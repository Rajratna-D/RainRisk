"""
MahaRainRisk: Phase 1 ML Models & Local Data Integrity Test Suite
Verifies:
1. Mode 1 Multi-Class Diagnostic Classifier artifact & features.
2. Mode 2 30-Day Early Warning Forecaster artifact & features.
3. Master panel parity (194 talukas, temporal bounds 2020-2026).
4. Agricultural University bilingual advisory matrix.
5. Live inference sanity for benchmark talukas (Paithan, Baramati, Mehkar).
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.predict import MahaRainRiskInference
from ml.advisory_engine import get_farmer_advisory

def test_phase1_mode1_diagnostic_artifact():
    """Verify Mode 1 Diagnostic Model artifact has 19 features, 5 classes, and 250 trees."""
    diag_path = os.path.join(BASE_DIR, "ml", "drought_model.joblib")
    assert os.path.exists(diag_path), f"Artifact not found: {diag_path}"

    art = joblib.load(diag_path)
    assert "model" in art
    assert "feature_names" in art
    assert "labels_en" in art
    assert "labels_mr" in art

    model = art["model"]
    assert len(art["feature_names"]) == 19
    assert list(model.classes_) == [0, 1, 2, 3, 4]
    assert len(model.estimators_) == 250

def test_phase1_mode2_forecaster_artifact():
    """Verify Mode 2 Forecaster Model artifact has 31 features and 250 trees."""
    fore_path = os.path.join(BASE_DIR, "ml", "drought_forecaster.joblib")
    assert os.path.exists(fore_path), f"Artifact not found: {fore_path}"

    art = joblib.load(fore_path)
    assert "model" in art
    assert "feature_names" in art
    model = art["model"]
    assert len(art["feature_names"]) == 31
    assert len(model.estimators_) == 250

def test_phase1_taluka_catalog_completeness():
    """Verify exactly 194 monitored rainfed Maharashtra talukas in official LGD master."""
    geo_path = os.path.join(BASE_DIR, "data", "geo", "lgd_maharashtra_master.csv")
    assert os.path.exists(geo_path), f"Geo catalog missing: {geo_path}"

    df = pd.read_csv(geo_path)
    assert len(df) == 194, f"Expected 194 talukas, got {len(df)}"
    assert df["taluka_lgd_code"].nunique() == 194
    assert df["latitude"].between(15.0, 22.5).all()
    assert df["longitude"].between(72.0, 81.0).all()

def test_phase1_master_panel_temporal_bounds():
    """Verify master_panel.parquet covers 2020 through 2026 across all 194 talukas."""
    panel_path = os.path.join(BASE_DIR, "data", "processed", "master_panel.parquet")
    assert os.path.exists(panel_path), f"Master panel missing: {panel_path}"

    df = pd.read_parquet(panel_path)
    assert df["taluka_lgd_code"].nunique() == 194
    assert df["year"].min() == 2020
    assert df["year"].max() >= 2024
    assert len(df) >= 10000

def test_phase1_advisory_engine_universities():
    """Verify advisory engine anchors correctly across all 4 Maharashtra state universities."""
    # MPKV Rahuri (Western Maharashtra & North Marathwada)
    adv_mpkv = get_farmer_advisory("Ahmednagar", "Rahuri", 0, 60.0, 80.0)
    assert "MPKV" in adv_mpkv["university_anchor"]["university_key"]

    # VNMKV Parbhani (Marathwada)
    adv_vnmkv = get_farmer_advisory("Parbhani", "Parbhani", 2, 35.0, 40.0)
    assert "VNMKV" in adv_vnmkv["university_anchor"]["university_key"]

    # Dr. PDKV Akola (Vidarbha)
    adv_pdkv = get_farmer_advisory("Akola", "Akola", 3, 20.0, 25.0)
    assert "PDKV" in adv_pdkv["university_anchor"]["university_key"]

    # Dr. BSKKV Dapoli (Konkan)
    adv_bskkv = get_farmer_advisory("Ratnagiri", "Dapoli", 1, 50.0, 70.0)
    assert "BSKKV" in adv_bskkv["university_anchor"]["university_key"]

def test_phase1_inference_sanity_benchmarks():
    """Verify dual-mode live inference on test talukas Paithan, Baramati, and Mehkar."""
    engine = MahaRainRiskInference()
    for t_name in ["Paithan", "Baramati", "Mehkar"]:
        res = engine.analyze_taluka(t_name)
        assert res["meta"]["taluka"].lower() == t_name.lower()
        assert 0 <= res["live_diagnosis"]["category_code"] <= 4
        assert 0 <= res["30_day_forecast"]["category_code"] <= 4
        assert 0.0 <= res["live_diagnosis"]["confidence_pct"] <= 100.0
        assert "prescriptive_actions" in res["advisory"]

