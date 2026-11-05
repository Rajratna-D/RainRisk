"""
MahaRainRisk: Unified Taluka Drought Inference & Advisory Service
Combines:
1. Mode 1: Live Multi-Source Drought Diagnostic Classifier
2. Mode 2: 30-Day Ahead Early Warning Forecaster
3. Bilingual Agricultural University Advisory Engine (MPKV, VNMKV, PDKV, BSKKV)
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
ML_DIR = os.path.join(BASE_DIR, "ml")

# Import Advisory Engine
from ml.advisory_engine import get_farmer_advisory

class MahaRainRiskInference:
    def __init__(self):
        # Load Mode 1: Diagnostic Model
        diag_path = os.path.join(ML_DIR, "drought_model.joblib")
        if not os.path.exists(diag_path):
            raise FileNotFoundError(f"Diagnostic model artifact not found at {diag_path}")
        self.diag_artifact = joblib.load(diag_path)
        self.diag_model = self.diag_artifact["model"]

        # Load Mode 2: Forecaster Model
        fore_path = os.path.join(ML_DIR, "drought_forecaster.joblib")
        if not os.path.exists(fore_path):
            raise FileNotFoundError(f"Forecaster model artifact not found at {fore_path}")
        self.fore_artifact = joblib.load(fore_path)
        self.fore_model = self.fore_artifact["model"]

        self.feature_names = self.diag_artifact["feature_names"]
        self.medians = self.diag_artifact.get("feature_medians", {})
        self.labels_en = self.diag_artifact["labels_en"]
        self.labels_mr = self.diag_artifact["labels_mr"]

        # Load Master Panel for telemetry lookup
        panel_path = os.path.join(PROCESSED_DIR, "master_panel.parquet")
        self.panel_df = pd.read_parquet(panel_path)
        self.panel_df = self.panel_df.sort_values(["taluka_name", "year", "month"]).reset_index(drop=True)

        # Pre-build fast O(1) indexed lookup dictionaries
        self._by_lgd: Dict[int, pd.DataFrame] = {}
        self._by_name: Dict[str, pd.DataFrame] = {}
        self._by_name_mr: Dict[str, pd.DataFrame] = {}
        self._inference_cache: Dict[tuple, Dict[str, Any]] = {}

        # Encoders for forecaster features
        self.zone_map = self.fore_artifact.get("zone_map", {})
        self.soil_map = self.fore_artifact.get("soil_map", {})
        if not self.zone_map:
            zones = sorted(self.panel_df["agro_climatic_zone"].dropna().unique())
            self.zone_map = {z: float(i) for i, z in enumerate(zones)}
        if not self.soil_map:
            soils = sorted(self.panel_df["soil_type"].dropna().unique())
            self.soil_map = {s: float(i) for i, s in enumerate(soils)}

        for code, group in self.panel_df.groupby("taluka_lgd_code"):
            sorted_g = group.sort_values(["year", "month"]).reset_index(drop=True)
            self._by_lgd[int(code)] = sorted_g
            t_name = str(sorted_g.iloc[0]["taluka_name"]).strip().lower()
            self._by_name[t_name] = sorted_g
            if "taluka_name_mr" in sorted_g.columns:
                t_mr = str(sorted_g.iloc[0]["taluka_name_mr"]).strip()
                if t_mr:
                    self._by_name_mr[t_mr] = sorted_g

    def analyze_taluka(self, taluka_query: str, year: int = 2026, month: int = 10):
        """
        Runs dual-mode evaluation and advisory lookup for any Maharashtra taluka.
        Fast O(1) indexed lookup with in-memory inference caching.
        """
        clean_q = taluka_query.strip().strip("/")
        cache_key = (clean_q.lower(), year, month)
        if cache_key in self._inference_cache:
            return self._inference_cache[cache_key]

        matches = None

        # 1. Exact numeric LGD code match (O(1))
        if clean_q.isdigit():
            matches = self._by_lgd.get(int(clean_q))
        else:
            # 2. Exact English name match (O(1))
            q_lower = clean_q.lower()
            matches = self._by_name.get(q_lower)

            # 3. Exact Marathi name match (O(1))
            if matches is None:
                matches = self._by_name_mr.get(clean_q)

            # 4. English substring fallback
            if matches is None:
                for name, df in self._by_name.items():
                    if q_lower in name:
                        matches = df
                        break

            # 5. Marathi substring fallback
            if matches is None:
                for name_mr, df in self._by_name_mr.items():
                    if clean_q in name_mr:
                        matches = df
                        break

        if matches is None or matches.empty:
            raise ValueError(f"Taluka '{taluka_query}' not found in Maharashtra 194-taluka master database.")

        # Find row for target year and month (or latest available)
        row_match = matches[(matches["year"] == year) & (matches["month"] == month)]
        if row_match.empty:
            row_match = matches.tail(1)

        row = row_match.iloc[0]
        taluka_name = row["taluka_name"]
        district_name = row["district_name"]

        # 1. Prepare Features for Model 1 (Diagnostic - 19 features)
        diag_features = self.diag_artifact["feature_names"]
        diag_medians = self.diag_artifact.get("feature_medians", {})
        X_diag_vals = [row.get(f, diag_medians.get(f, 0.0)) for f in diag_features]
        X_diag = pd.DataFrame([X_diag_vals], columns=diag_features).fillna(0.0)

        # Single predict_proba call gives both probability and argmax prediction (50% speedup)
        diag_proba = self.diag_model.predict_proba(X_diag)[0]
        diag_pred = int(np.argmax(diag_proba))

        # 2. Prepare Features for Model 2 (Forecaster - 31 features)
        fore_features = self.fore_artifact["feature_names"]
        fore_medians = self.fore_artifact.get("feature_medians", {})

        # Dynamic features calculation from taluka history if available
        t_history = matches.sort_values(["year", "month"])
        idx_list = t_history.index.tolist()
        curr_idx = row_match.index[0]
        pos = idx_list.index(curr_idx) if curr_idx in idx_list else -1
        prev_row = t_history.iloc[pos - 1] if pos > 0 else row

        dyn_dict = {
            "current_risk_tier": diag_pred,
            "delta_soil_moisture": float(row.get("soil_moisture_index", 50.0)) - float(prev_row.get("soil_moisture_index", 50.0)),
            "delta_spi3": float(row.get("spi_3", 0.0)) - float(prev_row.get("spi_3", 0.0)),
            "delta_temp_max": float(row.get("temp_max_mean", 30.0)) - float(prev_row.get("temp_max_mean", 30.0)),
            "delta_dam_storage": float(row.get("district_dam_storage_pct", 75.0)) - float(prev_row.get("district_dam_storage_pct", 75.0)),
            "month_sin": float(np.sin(2 * np.pi * row["month"] / 12.0)),
            "month_cos": float(np.cos(2 * np.pi * row["month"] / 12.0)),
            "is_monsoon": 1 if row["month"] in [6, 7, 8, 9] else 0,
            "is_kharif_peak": 1 if row["month"] in [7, 8] else 0,
            "zone_encoded": float(self.zone_map.get(str(row.get("agro_climatic_zone", "Unknown")), -1.0)),
            "soil_encoded": float(self.soil_map.get(str(row.get("soil_type", "Medium Black Soil")), -1.0))
        }

        X_fore_vals = []
        for f in fore_features:
            if f in dyn_dict:
                v = dyn_dict[f]
            elif f in row:
                v = row[f]
            else:
                v = fore_medians.get(f, 0.0)
            X_fore_vals.append(v if not pd.isna(v) else fore_medians.get(f, 0.0))

        X_fore = pd.DataFrame([X_fore_vals], columns=fore_features).fillna(0.0)
        fore_proba = self.fore_model.predict_proba(X_fore)[0]
        fore_pred = int(np.argmax(fore_proba))

        # 3. Advisory Lookup
        advisory = get_farmer_advisory(
            district_name=district_name,
            taluka_name=taluka_name,
            drought_risk_category=diag_pred,
            smi=float(row.get("soil_moisture_index", 50.0)),
            dam_pct=float(row.get("district_dam_storage_pct", 75.0))
        )

        result = {
            "meta": {
                "taluka": taluka_name,
                "district": district_name,
                "period": f"{row['year']}-{str(row['month']).zfill(2)}"
            },
            "live_diagnosis": {
                "category_code": diag_pred,
                "label_en": self.labels_en[diag_pred],
                "label_mr": self.labels_mr[diag_pred],
                "confidence_pct": round(float(diag_proba[diag_pred]) * 100, 1)
            },
            "30_day_forecast": {
                "category_code": fore_pred,
                "label_en": self.labels_en[fore_pred],
                "label_mr": self.labels_mr[fore_pred],
                "confidence_pct": round(float(fore_proba[fore_pred]) * 100, 1)
            },
            "telemetry_gauges": {
                "spi_3": round(float(row.get("spi_3", 0.0)), 2),
                "soil_moisture_index_pct": round(float(row.get("soil_moisture_index", 50.0)), 1),
                "dam_storage_pct": round(float(row.get("district_dam_storage_pct", 75.0)), 1),
                "groundwater_depth_mbgl": round(float(row.get("groundwater_depth_mbgl", 6.5)), 2)
            },
            "advisory": advisory
        }

        # Cache by query, taluka name, and LGD code
        self._inference_cache[cache_key] = result
        self._inference_cache[(taluka_name.lower(), year, month)] = result
        if "taluka_lgd_code" in row:
            self._inference_cache[(str(int(row["taluka_lgd_code"])), year, month)] = result

        return result

if __name__ == "__main__":
    engine = MahaRainRiskInference()

    test_talukas = ["Paithan", "Baramati", "Mehkar"]
    print("=" * 75)
    print(" MahaRainRisk: Dual-Mode Live Drought Inference & Farmer Advisory")
    print("=" * 75)

    for t_name in test_talukas:
        res = engine.analyze_taluka(t_name, year=2024, month=8)
        print(f"\n📍 Taluka: {res['meta']['taluka']} ({res['meta']['district']} District) | Period: {res['meta']['period']}")
        print(f"  🟢 Live Diagnosis: {res['live_diagnosis']['label_en']} ({res['live_diagnosis']['label_mr']}) - {res['live_diagnosis']['confidence_pct']}% conf")
        print(f"  🔮 30-Day Forecast: Next Month -> {res['30_day_forecast']['label_en']} ({res['30_day_forecast']['label_mr']})")
        print(f"  📊 Physical Gauges: SPI-3 = {res['telemetry_gauges']['spi_3']} | Root Soil Moisture = {res['telemetry_gauges']['soil_moisture_index_pct']}% | Dam = {res['telemetry_gauges']['dam_storage_pct']}%")
        print(f"  🏛️  University:     {res['advisory']['university_anchor']['university_name_en']}")
        print(f"  🌾 मराठी सल्ला:   {res['advisory']['prescriptive_actions']['foliar_and_nutrients']['mr']}")
