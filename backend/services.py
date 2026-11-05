"""
MahaRainRisk: Backend Data & ML Service Layer
Pre-loads in-memory caches, connects to the dual-mode ML engine,
annotates GeoJSON polygons with risk colors, and formats farmer-friendly cards.
"""

import os
import sys
import json
import time
import copy
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
GEO_DIR = os.path.join(BASE_DIR, "data", "geo")

from ml.predict import MahaRainRiskInference
from backend.cache import (
    cache_manager,
    risk_key,
    normalize_as_of_date
)

# Risk Color Palette & Labels
RISK_COLORS = {
    0: "#10B981", # Emerald Green (Safe)
    1: "#FBBF24", # Amber / Warm Yellow (Watch)
    2: "#F97316", # Orange (Alert)
    3: "#EF4444", # Red (Severe)
    4: "#7F1D1D"  # Deep Crimson (Extreme)
}

RISK_LABELS_EN = {
    0: "Safe",
    1: "Watch",
    2: "Alert",
    3: "Severe",
    4: "Extreme"
}

RISK_LABELS_MR = {
    0: "सुरक्षित",
    1: "लक्ष ठेवा (अल्प तूट)",
    2: "सतर्कता (मध्यम)",
    3: "तीव्र दुष्काळ",
    4: "अति तीव्र दुष्काळ"
}

class BackendDataService:
    def __init__(self):
        print("[*] Initializing MahaRainRisk High-Performance Backend Service...")
        self.inference_engine = MahaRainRiskInference()

        # Initialize TreeSHAP explainer once into memory for Phase 6 feature attribution
        try:
            import shap
            self.explainer = shap.TreeExplainer(self.inference_engine.diag_model)
            print("[OK] TreeSHAP Explainer pre-initialized in memory.")
        except Exception as e:
            print(f"[!] TreeSHAP Explainer initialization fallback: {e}")
            self.explainer = None

        self._districts_cache = None
        self._overview_cache = None

        # Load master panel
        panel_path = os.path.join(PROCESSED_DIR, "master_panel.parquet")
        self.master_df = pd.read_parquet(panel_path)
        self.master_df = self.master_df.sort_values(["taluka_lgd_code", "year", "month"]).reset_index(drop=True)

        # Load GeoJSON template
        geojson_path = os.path.join(GEO_DIR, "maharashtra_talukas.geojson")
        with open(geojson_path, "r", encoding="utf-8") as f:
            self.geojson_data = json.load(f)

        # Load spatial adjacency graph
        adj_path = os.path.join(GEO_DIR, "taluka_adjacency.json")
        if os.path.exists(adj_path):
            with open(adj_path, "r", encoding="utf-8") as f:
                self.adjacency_data = json.load(f)
        else:
            self.adjacency_data = {}

        # Pre-compute latest month per taluka (2024-08 or 2026-10)
        self.latest_df = self.master_df.groupby("taluka_lgd_code").last().reset_index()

        # Build fast O(1) indexed lookup tables for latest_df
        self._latest_by_code: Dict[int, pd.Series] = {}
        self._latest_by_name: Dict[str, pd.Series] = {}
        self._latest_by_name_mr: Dict[str, pd.Series] = {}

        for _, row in self.latest_df.iterrows():
            code = int(row["taluka_lgd_code"])
            self._latest_by_code[code] = row
            t_name = str(row["taluka_name"]).strip().lower()
            self._latest_by_name[t_name] = row
            if "taluka_name_mr" in row and pd.notna(row["taluka_name_mr"]):
                t_mr = str(row["taluka_name_mr"]).strip()
                if t_mr:
                    self._latest_by_name_mr[t_mr] = row

        # Pre-build annotated GeoJSON for ultra-fast instant map delivery
        self._annotated_geojson = self._build_annotated_geojson()

        # Load Reservoirs
        res_path = os.path.join(INTERIM_DIR, "reservoirs.parquet")
        if os.path.exists(res_path):
            self.reservoirs_df = pd.read_parquet(res_path)
        else:
            self.reservoirs_df = pd.DataFrame()

        # Build comprehensive district to nearest major reservoir mapping
        self.district_dam_map = {
            "Chhatrapati Sambhajinagar": ("Jayakwadi (Nathsagar)", "जायकवाडी (नाथसागर)"),
            "Jalna": ("Jayakwadi (Nathsagar)", "जायकवाडी (नाथसागर)"),
            "Beed": ("Majalgaon", "माजलगाव"),
            "Dharashiv": ("Ujjani (Bhima)", "उजनी (भीमा)"),
            "Latur": ("Majalgaon", "माजलगाव"),
            "Nanded": ("Yeldari", "येळदरी"),
            "Parbhani": ("Yeldari", "येळदरी"),
            "Hingoli": ("Yeldari", "येळदरी"),
            "Pune": ("Khadakwasla Complex (4 Dams)", "खडकवासला संकुल"),
            "Solapur": ("Ujjani (Bhima)", "उजनी (भीमा)"),
            "Satara": ("Koyna", "कोयना"),
            "Sangli": ("Koyna", "कोयना"),
            "Kolhapur": ("Radhanagari", "राधानगरी"),
            "Ahmednagar": ("Mula / Bhandardara", "मुळा / भंडारदरा"),
            "Nashik": ("Girna / Gangapur", "गिरणा / गंगापूर"),
            "Dhule": ("Girna", "गिरणा"),
            "Jalgaon": ("Girna / Hatnur", "गिरणा / हतनूर"),
            "Nandurbar": ("Sardar Sarovar", "सरदार सरोवर"),
            "Nagpur": ("Totladoh (Pench)", "तोतलाडोह (पेंच)"),
            "Wardha": ("Upper Wardha", "अपर वर्धा"),
            "Amravati": ("Upper Wardha (Nal Damyanti)", "अपर वर्धा"),
            "Buldhana": ("Khadakpurna / Upper Wardha", "खडकपूर्णा / अपर वर्धा"),
            "Akola": ("Katepurna", "काटेपूर्णा"),
            "Washim": ("Katepurna", "काटेपूर्णा"),
            "Yavatmal": ("Isapur / Upper Wardha", "ईसापूर / अपर वर्धा"),
            "Chandrapur": ("Asolamendha", "असोलामेंढा"),
            "Gadchiroli": ("Dina", "दिना"),
            "Bhandara": ("Ghosikhurd", "गोसीखुर्द"),
            "Gondia": ("Itiadoh", "इटियाडोह"),
            "Thane": ("Bhatsa", "भातसा"),
            "Palghar": ("Surya (Dhamani)", "सूर्या (धामणी)"),
            "Raigad": ("Bhatsa / Hetwane", "भातसा / हेतवणे"),
            "Ratnagiri": ("Koyna / Tillari", "कोयना / तिलारी"),
            "Sindhudurg": ("Tillari", "तिलारी"),
            "Mumbai City": ("Bhatsa / Vaitarna", "भातसा / वैतरणा"),
            "Mumbai Suburban": ("Bhatsa / Vaitarna", "भातसा / वैतरणा")
        }

        # Pre-Load and Index Historical 10-Year Monsoon Bar Chart Data (IMD Pune) into RAM
        imd_monthly_path = os.path.join(PROCESSED_DIR, "real_imd_taluka_monthly_2014_2023.parquet")
        self._imd_chart_cache: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        if os.path.exists(imd_monthly_path):
            df_imd = pd.read_parquet(imd_monthly_path)
            df_imd_monsoon = df_imd[(df_imd["year"] >= 2018) & (df_imd["month"].isin([6, 7, 8, 9]))]
            grouped = df_imd_monsoon.groupby(["taluka_lgd_code", "year"])["imd_monthly_rainfall_mm"].sum().reset_index()
            for _, r in grouped.iterrows():
                code = int(r["taluka_lgd_code"])
                self._imd_chart_cache[code].append({
                    "year": int(r["year"]),
                    "monsoon_rainfall_mm": round(float(r["imd_monthly_rainfall_mm"]), 1)
                })

        print(f"[OK] Backend Data Service initialized with {len(self.latest_df)} talukas & pre-cached IMD chart tables.")

    def _build_annotated_geojson(self) -> Dict[str, Any]:
        """Pre-colors GeoJSON features with their current risk status."""
        risk_lookup = {}
        for _, row in self.latest_df.iterrows():
            cat = int(row.get("drought_risk_category", 0))
            risk_lookup[int(row["taluka_lgd_code"])] = {
                "risk_category": cat,
                "risk_color": RISK_COLORS.get(cat, "#10B981"),
                "risk_label_en": row.get("risk_label_en", "Safe"),
                "risk_label_mr": row.get("risk_label_mr", "सुरक्षित"),
                "spi_3": round(float(row.get("spi_3", 0.0)), 2),
                "soil_moisture_index": round(float(row.get("soil_moisture_index", 50.0)), 1)
            }

        annotated = json.loads(json.dumps(self.geojson_data))
        for feat in annotated.get("features", []):
            props = feat.get("properties", {})
            code = int(props.get("taluka_lgd_code", 0))
            if code in risk_lookup:
                props.update(risk_lookup[code])
            else:
                props["risk_color"] = "#10B981"
                props["risk_label_en"] = "Safe"
                props["risk_label_mr"] = "सुरक्षित"
                props["risk_category"] = 0

        return annotated

    def get_talukas_list(self) -> List[Dict[str, Any]]:
        """Returns metadata for all 194 talukas for search autocomplete & map rendering."""
        talukas = []
        for _, row in self.latest_df.iterrows():
            cat = int(row.get("drought_risk_category", 0))
            talukas.append({
                "taluka_lgd_code": int(row["taluka_lgd_code"]),
                "taluka_name": row["taluka_name"],
                "taluka_name_mr": row.get("taluka_name_mr", ""),
                "district_name": row["district_name"],
                "district_name_mr": row.get("district_name_mr", ""),
                "division_name": row.get("division_name", ""),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "university": row.get("university_affiliation", "MPKV Rahuri"),
                "risk_category": cat,
                "risk_label_en": row.get("risk_label_en", "Safe"),
                "risk_label_mr": row.get("risk_label_mr", "सुरक्षित"),
                "risk_color": RISK_COLORS.get(cat, "#10B981")
            })
        return sorted(talukas, key=lambda x: x["taluka_name"])

    def get_annotated_geojson(self) -> Dict[str, Any]:
        """Returns pre-annotated GeoJSON with risk colors for Leaflet."""
        return self._annotated_geojson

    def get_taluka_detail(self, query: str) -> Dict[str, Any]:
        """Runs live analysis and formats the 4 simple farmer cards."""
        res = self.inference_engine.analyze_taluka(query)
        meta = res["meta"]
        t_name = meta["taluka"]
        d_name = meta["district"]

        # Fast O(1) indexed lookup from pre-cached latest_df
        row = self._latest_by_name.get(t_name.lower())
        if row is None:
            # Fallback to linear lookup if non-standard alias
            row_match = self.latest_df[self.latest_df["taluka_name"].str.lower() == t_name.lower()]
            row = row_match.iloc[0] if not row_match.empty else self.latest_df.iloc[0]

        meta["taluka_mr"] = str(row.get("taluka_name_mr", ""))
        meta["district_mr"] = str(row.get("district_name_mr", ""))

        # 1. Card 1: Rain Deficit
        spi3 = float(row.get("spi_3", 0.0))
        rain_sum = float(row.get("rain_roll_3", 100.0))
        annual_normal = float(row.get("normal_annual_rainfall_mm", 750.0))
        # Account for Maharashtra's monsoonal concentration (~85% in June-October)
        m_curr = int(row.get("month", 8))
        if 6 <= m_curr <= 10:
            normal_rain = annual_normal * 0.85 * (3.0 / 4.0)
        else:
            normal_rain = annual_normal * 0.15 * (3.0 / 8.0)
        pct_diff = round(((rain_sum - normal_rain) / (normal_rain + 1e-5)) * 100, 1)

        if spi3 <= -1.5 or pct_diff <= -40.0:
            pct_label = abs(pct_diff) if pct_diff < 0 else 45.0
            rain_status_en = f"Severe Rain Deficit ({pct_label:.0f}% below normal)"
            rain_status_mr = f"पावसात गंभीर तूट (सरासरीपेक्षा {pct_label:.0f}% कमी)"
            rain_color = "#EF4444"
        elif spi3 <= -0.5 or pct_diff <= -20.0:
            pct_label = abs(pct_diff) if pct_diff < 0 else 25.0
            rain_status_en = f"Below Normal Rain ({pct_label:.0f}% below normal)"
            rain_status_mr = f"पाऊस सरासरीपेक्षा कमी ({pct_label:.0f}% कमी)"
            rain_color = "#F97316"
        else:
            rain_status_en = "Normal Rainfall"
            rain_status_mr = "पाऊस सामान्य आहे"
            rain_color = "#10B981"

        # 2. Card 2: Soil Moisture Battery
        smi = float(row.get("soil_moisture_index", 50.0))
        if smi < 25.0:
            soil_status_en = "Critically Dry (Wilting Zone)"
            soil_status_mr = "अत्यंत कोरडी (तहानलेली जमीन)"
            soil_color = "#EF4444"
        elif smi < 42.0:
            soil_status_en = "Moisture Depleting"
            soil_status_mr = "ओलावा कमी होत आहे"
            soil_color = "#F97316"
        else:
            soil_status_en = "Adequate Soil Moisture"
            soil_status_mr = "जमिनीत ओलावा पुरेसा आहे"
            soil_color = "#10B981"

        # 3. Card 3: Nearest Dam Storage
        dam_pct = float(row.get("district_dam_storage_pct", 75.0))
        if dam_pct < 25.0:
            dam_status_en = f"Critical Dam Water ({dam_pct:.0f}% Storage)"
            dam_status_mr = f"धरण पाणीसाठा गंभीर ({dam_pct:.0f}% पाणी)"
            dam_color = "#EF4444"
        elif dam_pct < 50.0:
            dam_status_en = f"Moderate Dam Storage ({dam_pct:.0f}%)"
            dam_status_mr = f"मध्यम धरण पाणीसाठा ({dam_pct:.0f}%)"
            dam_color = "#FBBF24"
        else:
            dam_status_en = f"Healthy Dam Storage ({dam_pct:.0f}%)"
            dam_status_mr = f"धरण पाणीसाठा समाधानकारक ({dam_pct:.0f}%)"
            dam_color = "#10B981"

        # 4. Card 4: Dry Gap Days
        dry_days = int(row.get("max_consecutive_dry_days", 5))
        if dry_days > 17:
            dry_status_en = f"Dangerous Dry Spell ({dry_days} days without rain)"
            dry_status_mr = f"पावसात मोठा खंड ({dry_days} दिवस पाऊस नाही)"
            dry_color = "#EF4444"
        elif dry_days > 10:
            dry_status_en = f"Dry Gap ({dry_days} days)"
            dry_status_mr = f"पावसात खंड ({dry_days} दिवस)"
            dry_color = "#F97316"
        else:
            dry_status_en = f"Short Gap ({dry_days} days)"
            dry_status_mr = f"नियमित पाऊस ({dry_days} दिवस अंतर)"
            dry_color = "#10B981"

        # Assemble clean farmer cards
        farmer_cards = {
            "rainfall_deficit": {
                "title_en": "3-Month Rainfall",
                "title_mr": "३ महिन्यांचा पाऊस",
                "value_mm": round(rain_sum, 1),
                "status_en": rain_status_en,
                "status_mr": rain_status_mr,
                "color": rain_color
            },
            "soil_moisture": {
                "title_en": "Root-Zone Soil Moisture",
                "title_mr": "जमिनीतील ओलावा",
                "value_pct": round(smi, 1),
                "status_en": soil_status_en,
                "status_mr": soil_status_mr,
                "color": soil_color
            },
            "dam_storage": {
                "title_en": "Nearest Major Dam",
                "title_mr": "जवळचे मोठे धरण",
                "value_pct": round(dam_pct, 1),
                "status_en": dam_status_en,
                "status_mr": dam_status_mr,
                "color": dam_color,
                "dam_name": self.district_dam_map.get(d_name, ("Jayakwadi (Nathsagar)", "जायकवाडी (नाथसागर)"))[0],
                "dam_name_mr": self.district_dam_map.get(d_name, ("Jayakwadi (Nathsagar)", "जायकवाडी (नाथसागर)"))[1]
            },
            "dry_gap": {
                "title_en": "Dry Spell Gap",
                "title_mr": "पावसातील खंड",
                "value_days": dry_days,
                "status_en": dry_status_en,
                "status_mr": dry_status_mr,
                "color": dry_color
            }
        }

        # Retrieve Pre-Cached 10-Year Monsoon Bar Chart Data (Instant O(1) Memory Retrieval)
        t_code = int(row["taluka_lgd_code"])
        chart_data = self._imd_chart_cache.get(t_code, [])

        return {
            "meta": meta,
            "live_diagnosis": res["live_diagnosis"],
            "30_day_forecast": res["30_day_forecast"],
            "farmer_cards": farmer_cards,
            "chart_history": chart_data,
            "advisory": res["advisory"]
        }

    def get_statewide_overview(self) -> Dict[str, Any]:
        """
        Computes state-wide macro telemetry, risk tier distributions,
        and identifies top drought hotspots across all 194 talukas (cached in memory).
        """
        if self._overview_cache is not None:
            return self._overview_cache

        # 1. Risk Tier Counts
        cat_counts = self.latest_df["drought_risk_category"].value_counts().to_dict()
        risk_dist = {
            "safe_count": int(cat_counts.get(0, 0)),
            "watch_count": int(cat_counts.get(1, 0)),
            "alert_count": int(cat_counts.get(2, 0)),
            "severe_count": int(cat_counts.get(3, 0)),
            "extreme_count": int(cat_counts.get(4, 0))
        }

        # 2. State Averages (Season-adjusted 3-month climatological normal - BUG-09)
        rain_sum = self.latest_df["rain_roll_3"].fillna(100.0)
        annual_normal = self.latest_df["normal_annual_rainfall_mm"].fillna(750.0)
        curr_month = int(self.latest_df["month"].iloc[0]) if "month" in self.latest_df.columns and not self.latest_df.empty else 8
        if 6 <= curr_month <= 10:
            norm_rain = annual_normal * 0.85 * (3.0 / 4.0)
        else:
            norm_rain = annual_normal * 0.15 * (3.0 / 8.0)
        deficit_series = ((rain_sum - norm_rain) / (norm_rain + 1e-5)) * 100.0
        avg_deficit = round(float(deficit_series.mean()), 1)
        avg_smi = round(float(self.latest_df["soil_moisture_index"].mean()), 1)
        avg_dam = round(float(self.latest_df["district_dam_storage_pct"].mean()), 1)

        # 3. Top 5 Drought Hotspots (Highest risk category, lowest SMI, lowest SPI-3)
        sorted_hotspots = self.latest_df.sort_values(
            by=["drought_risk_category", "soil_moisture_index", "spi_3"],
            ascending=[False, True, True]
        ).head(5)

        hotspots = []
        for _, r in sorted_hotspots.iterrows():
            cat = int(r.get("drought_risk_category", 0))
            label = RISK_LABELS_EN.get(cat, "Safe")
            hotspots.append({
                "taluka_name": str(r["taluka_name"]),
                "taluka_name_mr": str(r.get("taluka_name_mr", "")),
                "district_name": str(r["district_name"]),
                "risk_tier": label,
                "category_code": cat,
                "spi_3": round(float(r.get("spi_3", 0.0)), 2),
                "soil_moisture_index": round(float(r.get("soil_moisture_index", 50.0)), 1),
                "dry_spell_days": int(r.get("max_consecutive_dry_days", 5))
            })

        self._overview_cache = {
            "total_talukas": len(self.latest_df),
            "total_districts": int(self.latest_df["district_name"].nunique()),
            "state_avg_rainfall_deficit_pct": avg_deficit,
            "state_avg_soil_moisture_pct": avg_smi,
            "state_avg_dam_storage_pct": avg_dam,
            "risk_distribution": risk_dist,
            "top_hotspots": hotspots
        }
        return self._overview_cache

    def get_districts_list(self) -> List[Dict[str, Any]]:
        """
        Aggregates all 194 talukas into their 36 parent administrative districts (cached in memory).
        """
        if self._districts_cache is not None:
            return self._districts_cache

        districts = []
        for d_name, g in self.latest_df.groupby("district_name"):
            r0 = g.iloc[0]
            avg_smi = round(float(g["soil_moisture_index"].mean()), 1)
            avg_dam = round(float(g["district_dam_storage_pct"].mean()), 1)
            dom_cat = int(g["drought_risk_category"].mode()[0])
            districts.append({
                "district_name": str(d_name),
                "district_name_mr": str(r0.get("district_name_mr", d_name)),
                "division_name": str(r0.get("division_name", "")),
                "taluka_count": len(g),
                "avg_soil_moisture": avg_smi,
                "avg_dam_storage": avg_dam,
                "dominant_risk_category": dom_cat,
                "dominant_risk_label": RISK_LABELS_EN.get(dom_cat, "Safe"),
                "primary_university": str(r0.get("university_affiliation", "MPKV Rahuri"))
            })
        self._districts_cache = sorted(districts, key=lambda x: x["district_name"])
        return self._districts_cache

    def compare_talukas(self, query1: str, query2: str) -> Dict[str, Any]:
        """
        Performs head-to-head agronomic comparison between two Maharashtra talukas.
        """
        t1 = self.get_taluka_detail(query1)
        t2 = self.get_taluka_detail(query2)

        # Compute analytical differentials (T1 vs T2)
        smi_diff = round(t1["farmer_cards"]["soil_moisture"]["value_pct"] - t2["farmer_cards"]["soil_moisture"]["value_pct"], 1)
        rain_diff = round(t1["farmer_cards"]["rainfall_deficit"]["value_mm"] - t2["farmer_cards"]["rainfall_deficit"]["value_mm"], 1)
        dam_diff = round(t1["farmer_cards"]["dam_storage"]["value_pct"] - t2["farmer_cards"]["dam_storage"]["value_pct"], 1)
        dry_diff = int(t1["farmer_cards"]["dry_gap"]["value_days"] - t2["farmer_cards"]["dry_gap"]["value_days"])

        vulnerable = t1["meta"]["taluka"] if t1["live_diagnosis"]["category_code"] > t2["live_diagnosis"]["category_code"] else t2["meta"]["taluka"]
        if t1["live_diagnosis"]["category_code"] == t2["live_diagnosis"]["category_code"]:
            vulnerable = t1["meta"]["taluka"] if t1["farmer_cards"]["soil_moisture"]["value_pct"] < t2["farmer_cards"]["soil_moisture"]["value_pct"] else t2["meta"]["taluka"]

        return {
            "taluka_1": t1,
            "taluka_2": t2,
            "analysis_delta": {
                "soil_moisture_pct_delta": smi_diff,
                "rainfall_mm_delta": rain_diff,
                "dam_storage_pct_delta": dam_diff,
                "dry_gap_days_delta": dry_diff,
                "more_vulnerable_taluka": vulnerable
            }
        }

    def get_reservoirs_list(self) -> List[Dict[str, Any]]:
        """Returns live status of all 12 major Maharashtra dams."""
        if self.reservoirs_df.empty:
            return []
        
        # Deduplicate to latest entry per dam
        latest_res = self.reservoirs_df.groupby("dam_name").last().reset_index()
        results = []
        for _, row in latest_res.iterrows():
            results.append({
                "dam_name": row.get("dam_name", ""),
                "dam_name_mr": row.get("dam_name_mr", ""),
                "district": row.get("district", ""),
                "river": row.get("river", ""),
                "storage_pct": round(float(row.get("storage_percentage", 75.0)), 1),
                "live_capacity_tmc": round(float(row.get("live_capacity_tmc", 50.0)), 1),
                "is_critical": bool(row.get("is_critical", False))
            })
        return sorted(results, key=lambda x: x["storage_pct"], reverse=True)

    # -------------------------------------------------------------------------
    # PHASE 4 & 5: MULTI-TIER RESOLUTION & INFERENCE WITH TREESHAP
    # -------------------------------------------------------------------------

    def resolve_taluka_row(self, query: str) -> pd.Series:
        """Fast O(1) resolution of a taluka from LGD code, English name, or Marathi name."""
        clean_q = query.strip().strip("/")
        if clean_q.isdigit():
            code = int(clean_q)
            if code in self._latest_by_code:
                return self._latest_by_code[code]
        q_lower = clean_q.lower()
        if q_lower in self._latest_by_name:
            return self._latest_by_name[q_lower]
        if clean_q in self._latest_by_name_mr:
            return self._latest_by_name_mr[clean_q]
        for name, row in self._latest_by_name.items():
            if q_lower in name:
                return row
        for name_mr, row in self._latest_by_name_mr.items():
            if clean_q in name_mr:
                return row
        raise ValueError(f"Taluka '{query}' not found in Maharashtra 194 monitored talukas.")

    def resolve_taluka_code(self, query: str) -> int:
        """Resolves official integer LGD code from query."""
        row = self.resolve_taluka_row(query)
        return int(row["taluka_lgd_code"])

    def get_taluka_risk_v1(self, query: str, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolves latest taluka risk via Tier 2 RAM TTLCache -> Tier 3 DB snapshot -> In-memory fallback.
        Delivers < 2ms response on cache hits.
        """
        code = self.resolve_taluka_code(query)
        return cache_manager.get_taluka_risk_multitier(code, as_of_date)

    def explain_taluka_v1(self, query: str, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes or retrieves cached local TreeSHAP attribution and vernacular farmer explanations.
        Protected by Tier 2 TTLCache and double-checked locking.
        """
        row = self.resolve_taluka_row(query)
        code = int(row["taluka_lgd_code"])
        from backend.cache import explain_key, normalize_as_of_date
        d_str = normalize_as_of_date(as_of_date)
        key = explain_key(code, d_str)

        def _compute():
            from ml.xai_engine import get_xai_engine
            xai = get_xai_engine()
            res = xai.explain_taluka(row)
            return {
                "taluka_lgd_code": code,
                "taluka_name": row["taluka_name"],
                "taluka_name_mr": row["taluka_name_mr"],
                "district_name": row["district_name"],
                "as_of_date": d_str,
                **res
            }

        return cache_manager.get_or_compute(key, _compute)

    def get_adjacent_talukas(self, query: str, max_neighbors: int = 6) -> Dict[str, Any]:
        """
        Retrieves topologically adjacent neighboring talukas and evaluates
        regional drought corridor / contagion status.
        """
        row = self.resolve_taluka_row(query)
        code = int(row["taluka_lgd_code"])
        target_cat = int(row.get("drought_risk_category", 0))

        raw_neighbors = self.adjacency_data.get(str(code), [])[:max_neighbors]
        neighbors_list = []
        alert_severe_count = 0

        for n in raw_neighbors:
            n_code = int(n["taluka_lgd_code"])
            n_row = self._latest_by_code.get(n_code)
            if n_row is not None:
                cat = int(n_row.get("drought_risk_category", 0))
                smi = round(float(n_row.get("soil_moisture_index", 50.0)), 1)
                spi3 = round(float(n_row.get("spi_3", 0.0)), 2)
            else:
                cat = 0
                smi = 50.0
                spi3 = 0.0

            if cat >= 2: # Alert, Severe, Extreme
                alert_severe_count += 1

            neighbors_list.append({
                "taluka_lgd_code": n_code,
                "taluka_name": n["taluka_name"],
                "taluka_name_mr": n.get("taluka_name_mr", ""),
                "district_name": n["district_name"],
                "boundary_distance_km": float(n.get("boundary_distance_km", 0.0)),
                "risk_category_code": cat,
                "risk_tier": RISK_LABELS_EN.get(cat, "Safe"),
                "risk_label_mr": RISK_LABELS_MR.get(cat, "सुरक्षित"),
                "soil_moisture_pct": smi,
                "spi_3": spi3
            })

        total_n = len(neighbors_list)
        pct_stressed = round((alert_severe_count / total_n * 100.0), 1) if total_n > 0 else 0.0

        if pct_stressed >= 50.0:
            corridor_status_en = "Active Regional Drought Corridor (Surrounding Talukas Stressed)"
            corridor_status_mr = "दुष्काळी पट्टा सक्रिय (शेजारील बहुतांश तालुक्यांमध्ये टंचाई)"
        elif pct_stressed >= 25.0:
            corridor_status_en = "Moderate Contagion Risk (Scattered Dry Pockets Nearby)"
            corridor_status_mr = "मध्यम धोका (जवळपास काही भागांत ओलावा कमी)"
        else:
            corridor_status_en = "Regional Buffer Intact (Surrounding Zones Stable)"
            corridor_status_mr = "शेजारील पट्टा सुरक्षित (ओलावा व पाणीसाठा समाधानकारक)"

        return {
            "target_taluka": {
                "taluka_lgd_code": code,
                "taluka_name": str(row["taluka_name"]),
                "taluka_name_mr": str(row.get("taluka_name_mr", "")),
                "district_name": str(row["district_name"]),
                "risk_category_code": target_cat,
                "risk_tier": RISK_LABELS_EN.get(target_cat, "Safe"),
                "risk_label_mr": RISK_LABELS_MR.get(target_cat, "सुरक्षित")
            },
            "neighbors_evaluated": total_n,
            "contagion_assessment": {
                "alert_or_severe_count": alert_severe_count,
                "stressed_percentage": pct_stressed,
                "corridor_status_en": corridor_status_en,
                "corridor_status_mr": corridor_status_mr
            },
            "adjacent_neighbors": neighbors_list
        }

    def get_district_summary(self, district_query: str) -> Dict[str, Any]:
        """
        Administrative aggregation of all talukas within a specified Maharashtra district.
        """
        d_clean = district_query.strip().lower()
        DISTRICT_ALIASES = {
            "aurangabad": "Chhatrapati Sambhajinagar",
            "औरंगाबाद": "Chhatrapati Sambhajinagar",
            "छत्रपती संभाजीनगर": "Chhatrapati Sambhajinagar",
            "osmanabad": "Dharashiv",
            "उस्मानाबाद": "Dharashiv",
            "धाराशिव": "Dharashiv",
            "poona": "Pune",
            "पुणे": "Pune",
            "nasik": "Nashik",
            "नाशिक": "Nashik",
            "सोलापूर": "Solapur",
            "अहमदनगर": "Ahmednagar",
            "जालना": "Jalna",
            "बीड": "Beed",
            "नांदेड": "Nanded",
            "लातूर": "Latur",
            "परभणी": "Parbhani",
            "हिंगोली": "Hingoli"
        }
        if d_clean in DISTRICT_ALIASES:
            canonical_district = DISTRICT_ALIASES[d_clean]
        else:
            canonical_district = district_query.strip()

        matches = self.latest_df[
            (self.latest_df["district_name"].str.lower() == canonical_district.lower()) |
            (self.latest_df["district_name_mr"] == canonical_district)
        ]
        if matches.empty:
            matches = self.latest_df[self.latest_df["district_name"].str.lower().str.contains(canonical_district.lower(), regex=False)]

        if matches.empty:
            raise ValueError(f"District '{district_query}' not found in Maharashtra 36 districts.")

        r0 = matches.iloc[0]
        d_name = str(r0["district_name"])
        d_name_mr = str(r0.get("district_name_mr", d_name))
        div_name = str(r0.get("division_name", ""))
        univ = str(r0.get("university_affiliation", "MPKV Rahuri"))

        cat_counts = matches["drought_risk_category"].value_counts().to_dict()
        risk_dist = {
            "safe_count": int(cat_counts.get(0, 0)),
            "watch_count": int(cat_counts.get(1, 0)),
            "alert_count": int(cat_counts.get(2, 0)),
            "severe_count": int(cat_counts.get(3, 0)),
            "extreme_count": int(cat_counts.get(4, 0))
        }

        avg_smi = round(float(matches["soil_moisture_index"].mean()), 1)
        avg_spi3 = round(float(matches["spi_3"].mean()), 2)
        dam_info = self.district_dam_map.get(d_name, ("Jayakwadi (Nathsagar)", "जायकवाडी (नाथसागर)"))
        avg_dam = round(float(matches["district_dam_storage_pct"].mean()), 1)

        vuln = matches.sort_values(
            by=["drought_risk_category", "soil_moisture_index", "spi_3"],
            ascending=[False, True, True]
        ).iloc[0]

        talukas_list = []
        for _, r in matches.sort_values(by=["drought_risk_category", "soil_moisture_index"], ascending=[False, True]).iterrows():
            cat = int(r.get("drought_risk_category", 0))
            talukas_list.append({
                "taluka_lgd_code": int(r["taluka_lgd_code"]),
                "taluka_name": str(r["taluka_name"]),
                "taluka_name_mr": str(r.get("taluka_name_mr", "")),
                "risk_category_code": cat,
                "risk_tier": RISK_LABELS_EN.get(cat, "Safe"),
                "risk_label_mr": RISK_LABELS_MR.get(cat, "सुरक्षित"),
                "soil_moisture_pct": round(float(r.get("soil_moisture_index", 50.0)), 1),
                "spi_3": round(float(r.get("spi_3", 0.0)), 2)
            })

        return {
            "district_name": d_name,
            "district_name_mr": d_name_mr,
            "division_name": div_name,
            "university_anchor": univ,
            "taluka_count": len(matches),
            "assigned_reservoir": {
                "name": dam_info[0],
                "name_mr": dam_info[1],
                "storage_pct": avg_dam
            },
            "risk_distribution": risk_dist,
            "district_averages": {
                "soil_moisture_pct": avg_smi,
                "spi_3": avg_spi3,
                "reservoir_storage_pct": avg_dam
            },
            "most_vulnerable_taluka": {
                "taluka_lgd_code": int(vuln["taluka_lgd_code"]),
                "taluka_name": str(vuln["taluka_name"]),
                "taluka_name_mr": str(vuln.get("taluka_name_mr", "")),
                "risk_tier": RISK_LABELS_EN.get(int(vuln.get("drought_risk_category", 0)), "Safe"),
                "soil_moisture_pct": round(float(vuln.get("soil_moisture_index", 50.0)), 1),
                "spi_3": round(float(vuln.get("spi_3", 0.0)), 2)
            },
            "talukas": talukas_list
        }

# Singleton Instance
backend_service = BackendDataService()
