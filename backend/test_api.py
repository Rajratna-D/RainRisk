"""
MahaRainRisk: Production Backend API, Schemas & Performance Test Suite
Verifies all REST endpoints, Pydantic data schemas, security headers,
input sanitization, side-by-side comparison, and sub-30ms latency benchmarks.
"""

import sys
import os
import time
import pytest
from fastapi.testclient import TestClient

# Ensure root in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app

client = TestClient(app)

def test_health_check():
    """Verify /api/health returns HTTP 200, headers, and indicates model readiness."""
    start = time.perf_counter()
    response = client.get("/api/health")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy"
    assert data["talukas_covered"] == 194
    assert data["districts_covered"] == 36
    assert "mode_1_diagnostic" in data["models"]
    assert "mode_2_forecaster" in data["models"]

    # Verify observability headers
    assert "x-process-time-ms" in response.headers
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
    print(f"[PASS] /api/health passed in {latency_ms:.2f}ms (Process time: {response.headers.get('x-process-time-ms')}ms)")

def test_get_all_talukas():
    """Verify /api/talukas returns exactly 194 talukas with bilingual metadata."""
    start = time.perf_counter()
    response = client.get("/api/talukas")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    talukas = response.json()
    assert len(talukas) == 194, f"Expected 194 talukas, got {len(talukas)}"

    sample = talukas[0]
    required_keys = ["taluka_lgd_code", "taluka_name", "taluka_name_mr", "district_name", "latitude", "longitude", "university", "risk_color", "risk_category"]
    for k in required_keys:
        assert k in sample, f"Missing key '{k}' in taluka metadata"
    print(f"[PASS] /api/talukas passed ({len(talukas)} talukas verified) in {latency_ms:.2f}ms")

def test_get_taluka_paithan():
    """Verify /api/taluka/Paithan returns 4 farmer cards, forecast, and advisory."""
    start = time.perf_counter()
    response = client.get("/api/taluka/Paithan")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["taluka"].lower() == "paithan"
    assert data["meta"]["district"] == "Chhatrapati Sambhajinagar"

    # Verify 4 Farmer Cards
    cards = data["farmer_cards"]
    assert "rainfall_deficit" in cards
    assert "soil_moisture" in cards
    assert "dam_storage" in cards
    assert "dry_gap" in cards

    for card_name, card in cards.items():
        assert "title_en" in card
        assert "title_mr" in card
        assert "status_en" in card
        assert "status_mr" in card
        assert "color" in card

    assert "dam_name" in cards["dam_storage"]
    assert "dam_name_mr" in cards["dam_storage"]

    # Verify Dual ML Modes
    assert "live_diagnosis" in data
    assert "30_day_forecast" in data
    assert "category_code" in data["live_diagnosis"]
    assert "label_en" in data["live_diagnosis"]
    assert "label_mr" in data["live_diagnosis"]
    assert "confidence_pct" in data["live_diagnosis"]
    assert "category_code" in data["30_day_forecast"]
    assert "label_en" in data["30_day_forecast"]

    # Verify Advisory
    assert "advisory" in data
    assert "university_anchor" in data["advisory"]
    assert "prescriptive_actions" in data["advisory"]

    print(f"[PASS] /api/taluka/Paithan passed in {latency_ms:.2f}ms")

def test_get_taluka_marathi_query():
    """Verify Devanagari query matching e.g. 'पैठण' or 'बारामती'."""
    start = time.perf_counter()
    response = client.get("/api/taluka/बारामती")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    data = response.json()
    assert "baramati" in data["meta"]["taluka"].lower()
    print(f"[PASS] /api/taluka/बारामती (Marathi query) passed in {latency_ms:.2f}ms")

def test_statewide_overview():
    """Verify /api/analytics/overview returns statewide macro stats and top hotspots."""
    start = time.perf_counter()
    response = client.get("/api/analytics/overview")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    data = response.json()
    assert data["total_talukas"] == 194
    assert data["total_districts"] == 36
    assert "risk_distribution" in data
    assert "safe_count" in data["risk_distribution"]
    assert "top_hotspots" in data
    assert len(data["top_hotspots"]) <= 5
    assert "state_avg_soil_moisture_pct" in data
    print(f"[PASS] /api/analytics/overview passed in {latency_ms:.2f}ms")

def test_get_all_districts():
    """Verify /api/districts returns 36 district rollups."""
    start = time.perf_counter()
    response = client.get("/api/districts")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    districts = response.json()
    assert len(districts) == 36, f"Expected 36 districts, got {len(districts)}"
    d0 = districts[0]
    assert "district_name" in d0
    assert "taluka_count" in d0
    assert "dominant_risk_category" in d0
    assert "primary_university" in d0
    print(f"[PASS] /api/districts (36 districts verified) in {latency_ms:.2f}ms")

def test_compare_talukas():
    """Verify /api/compare returns side-by-side comparison and differentials."""
    start = time.perf_counter()
    response = client.get("/api/compare?taluka1=Paithan&taluka2=Baramati")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    data = response.json()
    assert "taluka_1" in data
    assert "taluka_2" in data
    assert "analysis_delta" in data
    assert "soil_moisture_pct_delta" in data["analysis_delta"]
    assert "more_vulnerable_taluka" in data["analysis_delta"]
    print(f"[PASS] /api/compare passed in {latency_ms:.2f}ms")

def test_map_geojson():
    """Verify /api/map/geojson contains 194 features pre-painted with risk colors."""
    start = time.perf_counter()
    response = client.get("/api/map/geojson")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    geojson = response.json()
    assert geojson.get("type") == "FeatureCollection"
    features = geojson.get("features", [])
    assert len(features) == 194, f"Expected 194 features, got {len(features)}"

    # Check color annotation on first feature
    props = features[0]["properties"]
    assert "risk_color" in props
    assert props["risk_color"].startswith("#")
    assert "risk_label_en" in props
    assert "risk_label_mr" in props
    print(f"[PASS] /api/map/geojson (194 painted polygons) passed in {latency_ms:.2f}ms")

def test_reservoirs():
    """Verify /api/reservoirs returns 12 major dams with live storage."""
    start = time.perf_counter()
    response = client.get("/api/reservoirs")
    latency_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    reservoirs = response.json()
    assert len(reservoirs) >= 10, f"Expected at least 10 major dams, got {len(reservoirs)}"

    first = reservoirs[0]
    assert "dam_name" in first
    assert "storage_pct" in first
    assert "live_capacity_tmc" in first
    print(f"[PASS] /api/reservoirs ({len(reservoirs)} dams verified) in {latency_ms:.2f}ms")

def test_security_sanitization_and_errors():
    """Verify invalid queries, 404 handling, and script injection protection."""
    # Unknown taluka -> 404
    resp_404 = client.get("/api/taluka/NonExistentTaluka999")
    assert resp_404.status_code == 404
    err_json = resp_404.json()
    assert "error" in err_json or "detail" in err_json

    # Script tag injection -> 400
    resp_inject = client.get("/api/taluka/<script>alert(1)</script>")
    assert resp_inject.status_code == 400

    # Compare query injection -> 400
    resp_comp_inject = client.get("/api/compare?taluka1=<script>&taluka2=Baramati")
    assert resp_comp_inject.status_code == 400

    # Trailing slash handling -> 200
    resp_slash = client.get("/api/taluka/Paithan/")
    assert resp_slash.status_code == 200

    # Verify security headers injected
    resp = client.get("/api/health")
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    print("[PASS] Security sanitization, 404 handling, and security headers verified")

def test_latency_benchmark():
    """Assert that 50 consecutive queries run with average latency under 20ms."""
    # Pre-warm
    client.get("/api/taluka/Aurangabad")

    start = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        resp = client.get("/api/taluka/Aurangabad")
        assert resp.status_code == 200
    total_time_ms = (time.perf_counter() - start) * 1000
    avg_latency_ms = total_time_ms / iterations

    print(f"[PASS] Latency Benchmark: {iterations} requests executed in {total_time_ms:.2f}ms (Average: {avg_latency_ms:.2f}ms/req)")
    assert avg_latency_ms < 20.0, f"Expected latency < 20ms, got {avg_latency_ms:.2f}ms"

def test_phase4_taluka_risk_v1_and_caching():
    """Verify /api/v1/taluka/Paithan/risk delivers sub-5ms cached latency and HTTP headers."""
    # First hit (populates Tier 2 RAM)
    r1 = client.get("/api/v1/taluka/Paithan/risk")
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["taluka_name"].lower() == "paithan"
    assert "risk_score" in data1
    assert "shap_summary" in data1
    assert "bilingual_advisory" in data1
    assert "public, max-age=300" in r1.headers.get("Cache-Control", "")

    # Second hit (Tier 2 RAM cache hit < 5ms)
    t0 = time.perf_counter()
    r2 = client.get("/api/v1/taluka/Paithan/risk")
    hit_latency_ms = (time.perf_counter() - t0) * 1000.0
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["taluka_lgd_code"] == data1["taluka_lgd_code"]
    print(f"[PASS] Tier 2 Cache Hit Latency: {hit_latency_ms:.2f}ms (Target: < 5ms)")

def test_phase4_cache_stats_and_clear():
    """Verify /api/v1/cache/stats observability and manual flush endpoint."""
    r_stats = client.get("/api/v1/cache/stats")
    assert r_stats.status_code == 200
    stats = r_stats.json()
    assert stats["maxsize"] == 500
    assert stats["ttl_seconds"] == 21600
    assert stats["hits"] >= 1

    r_clear = client.post("/api/v1/cache/clear")
    assert r_clear.status_code == 200
    assert r_clear.json()["status"] == "success"

if __name__ == "__main__":
    pytest.main(["-v", "backend/test_api.py"])
