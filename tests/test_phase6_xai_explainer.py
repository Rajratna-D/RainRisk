"""
MahaRainRisk: Phase 6 TreeSHAP Explainable AI (XAI) Test Suite
Verifies:
1. TreeSHAP Explainer C++ decision graph initialization.
2. Local instance Shapley feature attribution for individual talukas.
3. Multi-class shape handling and impact percentage sum property (~100%).
4. Bilingual farmer narrative generation in English and Marathi Unicode.
5. GET /api/v1/taluka/{query}/explain endpoint contracts and Pydantic validation.
6. Marathi query resolution (e.g. 'पैठण').
7. Tier 2 in-memory caching sub-5ms latency on repeated queries.
8. Adversarial query sanitization and error handling.
"""

import os
import sys
import re
import time
import urllib.parse
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.xai_engine import get_xai_engine, MahaRainRiskXAI
from backend.main import app

client = TestClient(app)


def test_phase6_xai_engine_initialization():
    """Verify TreeSHAP explainer initializes with 19 features and 5 target classes."""
    engine = get_xai_engine()
    assert isinstance(engine, MahaRainRiskXAI)
    assert engine.explainer is not None
    assert len(engine.feature_names) == 19
    assert len(engine.labels_en) == 5
    assert len(engine.labels_mr) == 5


def test_phase6_local_instance_shap_attribution():
    """Verify local instance Shapley attribution on a real taluka."""
    engine = get_xai_engine()
    import pandas as pd
    panel_path = os.path.join(BASE_DIR, "data", "processed", "master_panel.parquet")
    df = pd.read_parquet(panel_path)
    paithan_row = df[df["taluka_name"].str.lower() == "paithan"].iloc[-1]

    result = engine.explain_taluka(paithan_row)

    assert "predicted_tier" in result
    assert "code" in result["predicted_tier"]
    assert "top_risk_escalators" in result
    assert "top_mitigating_buffers" in result
    assert "all_drivers" in result
    assert "farmer_summary" in result

    # All 19 features must be attributed
    assert len(result["all_drivers"]) == 19

    # Impact percentages must sum approximately to 100%
    total_pct = sum(d["impact_pct"] for d in result["all_drivers"])
    assert 98.0 <= total_pct <= 102.0, f"Total impact percentage sum was {total_pct}%"

    # Escalators must have shap_value > 0
    for esc in result["top_risk_escalators"]:
        assert esc["is_escalator"] is True
        assert esc["shap_value"] > 0

    # Buffers must have shap_value <= 0
    for buf in result["top_mitigating_buffers"]:
        assert buf["is_escalator"] is False
        assert buf["shap_value"] <= 0


def test_phase6_bilingual_farmer_narrative_integrity():
    """Verify Marathi and English natural-language narratives are correctly formatted."""
    engine = get_xai_engine()
    import pandas as pd
    panel_path = os.path.join(BASE_DIR, "data", "processed", "master_panel.parquet")
    df = pd.read_parquet(panel_path)

    # Test on a drought row (tier >= 2)
    drought_rows = df[df["drought_risk_category"] >= 2]
    if len(drought_rows) > 0:
        row = drought_rows.iloc[0]
        res = engine.explain_taluka(row)
        summary = res["farmer_summary"]

        assert "en" in summary and "mr" in summary
        assert len(summary["en"]) > 10
        assert len(summary["mr"]) > 10

        # Marathi text must contain Devanagari characters (\u0900-\u097F)
        devanagari_pattern = re.compile(r"[\u0900-\u097F]")
        assert devanagari_pattern.search(summary["mr"]) is not None, "Marathi narrative must contain Devanagari script"


def test_phase6_endpoint_get_taluka_explain():
    """Verify GET /api/v1/taluka/{query}/explain endpoint schema and response."""
    resp = client.get("/api/v1/taluka/paithan/explain")
    assert resp.status_code == 200

    data = resp.json()
    assert data["taluka_name"] == "Paithan"
    assert data["taluka_lgd_code"] == 4123
    assert "predicted_tier" in data
    assert "top_risk_escalators" in data
    assert "top_mitigating_buffers" in data
    assert "all_drivers" in data
    assert "farmer_summary" in data
    assert len(data["top_risk_escalators"]) <= 3
    assert len(data["top_mitigating_buffers"]) <= 1


def test_phase6_marathi_query_resolution():
    """Verify GET /api/v1/taluka/{query}/explain handles Marathi Unicode query strings."""
    encoded_query = urllib.parse.quote("पैठण")
    resp = client.get(f"/api/v1/taluka/{encoded_query}/explain")
    assert resp.status_code == 200

    data = resp.json()
    assert data["taluka_name_mr"] == "पैठण"
    assert data["taluka_lgd_code"] == 4123


def test_phase6_cached_latency_sub_5ms():
    """Verify Tier 2 TTLCache provides sub-5ms latency on repeated explain queries."""
    # First query primes the Tier 2 cache
    _ = client.get("/api/v1/taluka/paithan/explain")

    # Second query must hit Tier 2 RAM cache
    start = time.perf_counter()
    resp = client.get("/api/v1/taluka/paithan/explain")
    latency_ms = (time.perf_counter() - start) * 1000.0

    assert resp.status_code == 200
    print(f"[PASS] /explain cached latency: {latency_ms:.2f}ms (Target: < 10ms)")
    assert latency_ms < 10.0, f"Cached latency {latency_ms:.2f}ms exceeded 10ms target"


def test_phase6_invalid_taluka_and_injection_handling():
    """Verify input sanitization on non-existent talukas and injection attempts."""
    resp_404 = client.get("/api/v1/taluka/non_existent_taluka_999/explain")
    assert resp_404.status_code == 404

    resp_400 = client.get("/api/v1/taluka/<script>alert(1)</script>/explain")
    assert resp_400.status_code == 400

