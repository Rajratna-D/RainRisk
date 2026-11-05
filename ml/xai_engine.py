# -*- coding: utf-8 -*-
"""
MahaRainRisk: Production Explainable AI (XAI) Engine
Computes ultra-fast (< 15ms) local TreeSHAP attributions and converts mathematical
margin log-odds into vernacular farmer explanations in Marathi and English.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib
import shap

logger = logging.getLogger("MahaRainRisk-XAI")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
ML_DIR = os.path.join(BASE_DIR, "ml")

# Bilingual Feature Metadata & Icons for Vernacular Rendering
FEATURE_METADATA = {
    "rainfall_monthly_mm": {
        "name_en": "Monthly Rainfall Accumulation",
        "name_mr": "मासिक एकूण पाऊस",
        "icon": "🌧️",
        "unit": "mm"
    },
    "rainy_days": {
        "name_en": "Rainy Days Count",
        "name_mr": "पावसाचे दिवस",
        "icon": "🌦️",
        "unit": "days"
    },
    "temp_max_mean": {
        "name_en": "Maximum Surface Temperature",
        "name_mr": "कमाल तापमान व उष्णता",
        "icon": "🌡️",
        "unit": "°C"
    },
    "temp_min_mean": {
        "name_en": "Minimum Night Temperature",
        "name_mr": "किमान रात्रीचे तापमान",
        "icon": "🌡️",
        "unit": "°C"
    },
    "max_consecutive_dry_days": {
        "name_en": "Consecutive Rainless Spell",
        "name_mr": "पावसातील सलग खंड",
        "icon": "☀️",
        "unit": "days"
    },
    "rain_roll_1": {
        "name_en": "30-Day Rainfall Volume",
        "name_mr": "३० दिवसांचा पाऊस",
        "icon": "🌧️",
        "unit": "mm"
    },
    "rain_roll_3": {
        "name_en": "90-Day Seasonal Rainfall",
        "name_mr": "९० दिवसांचा मोसमी पाऊस",
        "icon": "🌧️",
        "unit": "mm"
    },
    "rain_roll_6": {
        "name_en": "180-Day Hydrological Rainfall",
        "name_mr": "१८० दिवसांचा एकूण पाऊस",
        "icon": "🌧️",
        "unit": "mm"
    },
    "spi_1": {
        "name_en": "1-Month Rainfall Deficit (SPI-1)",
        "name_mr": "१ महिन्याचा पाऊस निर्देशांक (SPI-1)",
        "icon": "📉",
        "unit": "index"
    },
    "spi_3": {
        "name_en": "3-Month Seasonal Rain Deficit (SPI-3)",
        "name_mr": "३ महिन्यांचा मोसमी पाऊस तुटवडा (SPI-3)",
        "icon": "📉",
        "unit": "index"
    },
    "spi_6": {
        "name_en": "6-Month Hydrological Index (SPI-6)",
        "name_mr": "६ महिन्यांचा जल निर्देशांक (SPI-6)",
        "icon": "📉",
        "unit": "index"
    },
    "normal_annual_rainfall_mm": {
        "name_en": "Long-Term Normal Annual Rainfall",
        "name_mr": "वार्षिक सरासरी पाऊस",
        "icon": "📊",
        "unit": "mm"
    },
    "nino34_anomaly": {
        "name_en": "Pacific Niño 3.4 SST Anomaly",
        "name_mr": "प्रशांत महासागरातील तापमान विसंगती",
        "icon": "🌊",
        "unit": "°C"
    },
    "oni": {
        "name_en": "Oceanic Niño Index (El Niño Phase)",
        "name_mr": "एल निनो महासागरी निर्देशांक",
        "icon": "🌊",
        "unit": "index"
    },
    "dmi": {
        "name_en": "Indian Ocean Dipole (IOD / DMI)",
        "name_mr": "हिंदी महासागरातील द्विध्रुव निर्देशांक",
        "icon": "🌊",
        "unit": "index"
    },
    "district_dam_storage_pct": {
        "name_en": "District Reservoir Live Storage",
        "name_mr": "जिल्ह्यातील धरणांमधील पाणीसाठा",
        "icon": "💧",
        "unit": "%"
    },
    "soil_moisture_index": {
        "name_en": "Root-Zone Soil Moisture Level",
        "name_mr": "जमिनीतील मुळांच्या थरातील ओलावा",
        "icon": "🌱",
        "unit": "%"
    },
    "vci": {
        "name_en": "Vegetation Condition Index (Crop Vigor)",
        "name_mr": "पिकांची हिरवळ व आरोग्य (VCI)",
        "icon": "🌾",
        "unit": "VCI"
    },
    "groundwater_depth_mbgl": {
        "name_en": "Groundwater Table Depth",
        "name_mr": "भूजल पातळी खोली",
        "icon": "🚰",
        "unit": "mbgl"
    }
}


class MahaRainRiskXAI:
    """
    Production-grade TreeSHAP Explainable AI Engine.
    Pre-compiles TreeSHAP C++ graph structures once into memory for sub-15ms inference.
    """

    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = os.path.join(ML_DIR, "drought_model.joblib")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model artifact for XAI missing at {model_path}")

        logger.info("[*] Loading Diagnostic ML model for XAI from %s...", model_path)
        from ml.predict import verify_and_load_artifact
        artifact = verify_and_load_artifact(model_path, "EXPECTED_HASH_DROUGHT_MODEL")
        self.model = artifact["model"]
        self.feature_names: List[str] = artifact["feature_names"]
        self.labels_en: List[str] = artifact.get("labels_en", ["Safe", "Watch", "Alert", "Severe", "Extreme"])
        self.labels_mr: List[str] = artifact.get("labels_mr", [
            "सुरक्षित",
            "लक्ष द्या (कमी धोका)",
            "सतर्क राहा (मध्यम)",
            "गंभीर दुष्काळ",
            "अति-गंभीर दुष्काळ"
        ])

        # Precompute feature medians from master panel for safe imputations
        panel_path = os.path.join(PROCESSED_DIR, "master_panel.parquet")
        if os.path.exists(panel_path):
            panel_df = pd.read_parquet(panel_path)
            self.medians = panel_df[self.feature_names].median().to_dict()
        else:
            self.medians = {f: 0.0 for f in self.feature_names}

        # Initialize and pre-compile TreeExplainer once into RAM
        logger.info("[*] Initializing TreeSHAP Explainer C++ decision graph...")
        t0 = time.perf_counter()
        self.explainer = shap.TreeExplainer(self.model)
        init_ms = (time.perf_counter() - t0) * 1000.0
        logger.info("[OK] TreeSHAP Explainer initialized in memory in %.2f ms.", init_ms)

    def explain_taluka(
        self,
        feature_row: pd.Series,
        predicted_class: Optional[int] = None,
        confidence_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Computes exact local TreeSHAP attribution for a single taluka evaluation.
        Returns top risk escalators and mitigating buffers in English and Marathi.
        """
        t_start = time.perf_counter()

        # Build feature dictionary aligned to training feature names
        raw_dict = {}
        for feat in self.feature_names:
            val = feature_row.get(feat, None)
            if val is None or pd.isna(val):
                val = self.medians.get(feat, 0.0)
            try:
                raw_dict[feat] = float(val)
            except (ValueError, TypeError):
                raw_dict[feat] = float(self.medians.get(feat, 0.0))

        # Create DataFrame with exact column names to prevent scikit-learn warnings
        X_df = pd.DataFrame([raw_dict], columns=self.feature_names)

        # Predict winning class & confidence if not provided
        if predicted_class is None:
            probs = self.model.predict_proba(X_df)[0]
            predicted_class = int(np.argmax(probs))
            calc_conf = round(float(probs[predicted_class]) * 100.0, 1)
        elif confidence_pct is None:
            probs = self.model.predict_proba(X_df)[0]
            calc_conf = round(float(probs[predicted_class]) * 100.0, 1)
        else:
            calc_conf = round(float(confidence_pct), 1)

        # Compute exact Shapley values
        shap_values = self.explainer.shap_values(X_df)

        # Robust multi-class shape extractor
        # Handles (1, n_features, n_classes), list of (1, n_features), or 2D arrays
        if isinstance(shap_values, list):
            class_shap = shap_values[predicted_class][0]
        elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
            class_shap = shap_values[0, :, predicted_class]
        elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 2:
            class_shap = shap_values[0]
        else:
            class_shap = np.array(shap_values).flatten()

        # Relative impact percentages
        abs_vals = np.abs(class_shap)
        total_impact = np.sum(abs_vals) + 1e-6
        relative_percentages = (abs_vals / total_impact) * 100.0

        # Build feature attribution records
        all_drivers = []
        for feat_name, sv, pct in zip(self.feature_names, class_shap, relative_percentages):
            meta = FEATURE_METADATA.get(feat_name, {
                "name_en": feat_name.replace("_", " ").title(),
                "name_mr": feat_name,
                "icon": "📊",
                "unit": ""
            })
            val = raw_dict.get(feat_name, None)

            # ML-05: For Class 0 (Safe), positive SHAP keeps it safe (protective buffer),
            # while negative SHAP pulls toward higher drought tiers (risk escalator).
            # For Classes 1-4 (Drought), positive SHAP escalates risk.
            if predicted_class == 0:
                is_escalator = bool(sv < 0)
            else:
                is_escalator = bool(sv > 0)

            all_drivers.append({
                "feature_key": feat_name,
                "name_en": meta["name_en"],
                "name_mr": meta["name_mr"],
                "icon": meta["icon"],
                "raw_value": round(float(val), 2) if val is not None else None,
                "unit": meta["unit"],
                "shap_value": round(float(sv), 4),
                "impact_pct": round(float(pct), 1),
                "is_escalator": is_escalator
            })

        # Categorize escalators (positive SHAP pushing towards predicted tier)
        # and buffers (negative SHAP mitigating against worsening drought)
        escalators = sorted(
            [d for d in all_drivers if d["is_escalator"]],
            key=lambda x: x["impact_pct"],
            reverse=True
        )
        buffers = sorted(
            [d for d in all_drivers if not d["is_escalator"]],
            key=lambda x: x["impact_pct"],
            reverse=True
        )

        compute_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        return {
            "predicted_tier": {
                "code": predicted_class,
                "label_en": self.labels_en[predicted_class],
                "label_mr": self.labels_mr[predicted_class]
            },
            "confidence_pct": calc_conf,
            "top_risk_escalators": escalators[:3],
            "top_mitigating_buffers": buffers[:1],
            "all_drivers": sorted(all_drivers, key=lambda x: x["impact_pct"], reverse=True),
            "farmer_summary": {
                "en": self._format_farmer_narrative(escalators, buffers, predicted_class, lang="en"),
                "mr": self._format_farmer_narrative(escalators, buffers, predicted_class, lang="mr")
            },
            "computation_time_ms": compute_ms,
            "source": "xai_engine"
        }

    def _format_farmer_narrative(
        self,
        escalators: List[dict],
        buffers: List[dict],
        predicted_class: int,
        lang: str = "en"
    ) -> str:
        """Formats natural-language driver sentence for vernacular dashboard display."""
        if predicted_class == 0:
            if lang == "mr":
                return "सर्व हवामान, पाऊस व ओलावा निर्देशांक सुरक्षित मर्यादेत आहेत."
            return "All agrometeorological and moisture indicators are within safe operational thresholds."

        if not escalators:
            if lang == "mr":
                return "सद्यस्थितीत कोणतेही तीव्र दुष्काळी घटक आढळलेले नाहीत."
            return "No acute drought risk triggers detected in current conditions."

        primary = escalators[0]
        if lang == "mr":
            msg = f"जोखमीचे मुख्य कारण {primary['icon']} {primary['name_mr']} ({primary['impact_pct']}% प्रभाव) आहे."
            if buffers:
                b = buffers[0]
                msg += f" {b['icon']} {b['name_mr']} मुळे पिकाला काहीसा आधार मिळत आहे."
            return msg
        else:
            msg = f"Primary drought trigger is {primary['icon']} {primary['name_en']} ({primary['impact_pct']}% impact)."
            if buffers:
                b = buffers[0]
                msg += f" Buffered partially by {b['icon']} {b['name_en']}."
            return msg


# Module-level singleton pattern
_XAI_ENGINE_INSTANCE: Optional[MahaRainRiskXAI] = None

def get_xai_engine() -> MahaRainRiskXAI:
    """Returns the pre-initialized singleton instance of the TreeSHAP XAI Engine."""
    global _XAI_ENGINE_INSTANCE
    if _XAI_ENGINE_INSTANCE is None:
        _XAI_ENGINE_INSTANCE = MahaRainRiskXAI()
    return _XAI_ENGINE_INSTANCE
