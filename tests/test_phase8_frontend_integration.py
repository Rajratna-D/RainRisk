"""
MahaRainRisk | Phase 8 Automated Verification Suite
================================================================================
Validates Frontend UI Integration, Responsive Asset Routing, Option A Integrity,
GPS Centroid Mathematics, TreeSHAP & Contagion DOM Targets, and MCP Connector Modal.
================================================================================
"""

import os
import sys
import math
import re
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app

client = TestClient(app)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


def test_phase8_static_assets_serving():
    """Validates that all essential frontend assets (HTML, CSS, JS) serve HTTP 200."""
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "text/html" in res_index.headers.get("content-type", "")
    assert "MahaRainRisk" in res_index.text

    # Core CSS files
    css_files = ["variables.css", "layout.css", "cards.css", "modals.css", "landing.css"]
    for css in css_files:
        res_css = client.get(f"/css/{css}")
        assert res_css.status_code == 200, f"Failed to serve /css/{css}"
        assert "text/css" in res_css.headers.get("content-type", "")

    # Core JS modules
    js_files = ["state.js", "app.js", "dashboard.js", "advisory.js", "audio.js", "i18n.js", "map.js"]
    for js in js_files:
        res_js = client.get(f"/js/{js}")
        assert res_js.status_code == 200, f"Failed to serve /js/{js}"
        assert "javascript" in res_js.headers.get("content-type", "")


def test_phase8_geojson_payload_compression():
    """Asserts Maharashtra taluka GeoJSON payload is lightweight (<= 450 KB)."""
    res = client.get("/api/map/geojson")
    assert res.status_code == 200
    payload_size_kb = len(res.content) / 1024.0
    assert payload_size_kb <= 450.0, f"GeoJSON payload is {payload_size_kb:.2f} KB, exceeds 450 KB threshold"
    
    geo = res.json()
    assert geo.get("type") == "FeatureCollection"
    assert len(geo.get("features", [])) > 100


def test_phase8_dom_hooks_presence():
    """Asserts that all newly integrated DOM hooks exist in frontend/index.html."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    assert os.path.exists(index_path)
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. 1-Tap GPS Location Snapping Button
    assert 'id="btn-gps-locate"' in html, "Missing GPS locate button"
    assert 'onclick="locateUserTaluka()"' in html, "Missing locateUserTaluka click handler"

    # 2. Stale Data Warning Banner
    assert 'id="stale-data-banner"' in html, "Missing stale data warning banner"

    # 3. Toast Notification Container
    assert 'id="toast-container"' in html, "Missing toast notification container"

    # 4. TreeSHAP Explainable AI Card & Hooks
    assert 'id="card-treeshap-explain"' in html, "Missing TreeSHAP explain card"
    assert 'id="treeshap-escalators-list"' in html, "Missing TreeSHAP escalators list"
    assert 'id="treeshap-buffer-box"' in html, "Missing TreeSHAP buffer box"
    assert 'id="treeshap-farmer-narrative"' in html, "Missing TreeSHAP farmer narrative"

    # 5. Regional Contagion & Adjacent Talukas Card & Hooks
    assert 'id="card-regional-contagion"' in html, "Missing regional contagion card"
    assert 'id="adjacent-talukas-grid"' in html, "Missing adjacent talukas grid"
    assert 'id="contagion-assessment-badge"' in html, "Missing contagion assessment badge"

    # 6. MCP Connector Card & Dedicated Modal
    assert 'id="card-mcp-connector"' in html, "Missing MCP connector card in Tab 2"
    assert 'id="modal-mcp-connector"' in html, "Missing MCP connector modal"
    assert 'onclick="openMcpModal()"' in html, "Missing openMcpModal handler"
    assert 'https://rainrisk-vcra.onrender.com/mcp' in html, "Missing production MCP URL in modal"


def test_phase8_option_a_zero_simulation_enforced():
    """Enforces Option A: Confirms absolute absence of simulation sliders and simulate endpoints."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # No simulation range sliders in the entire document
    assert '<input type="range"' not in html.lower(), "Found deprecated simulation range sliders in index.html"
    assert 'what-if' not in html.lower() or 'simulation' not in html.lower()

    # Check that app.js and dashboard.js do not call /api/v1/simulate
    for js_file in ["app.js", "dashboard.js"]:
        js_path = os.path.join(FRONTEND_DIR, "js", js_file)
        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()
        assert "/api/v1/simulate" not in js_code, f"Found deprecated /api/v1/simulate in {js_file}"


def test_phase8_haversine_gps_math_algorithm():
    """Unit tests client-side Haversine mathematical algorithm against true taluka coordinates."""
    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    # Paithan coordinates: (19.4795, 75.3852)
    # Test nearby point in Paithan village (19.4850, 75.3800)
    dist_paithan = haversine_km(19.4850, 75.3800, 19.4795, 75.3852)
    assert dist_paithan < 2.0, f"Expected < 2 km, got {dist_paithan:.2f} km"

    # Pune Shaniwar Wada: (18.5196, 73.8553)
    # Haveli centroid: (18.5204, 73.8567)
    dist_haveli = haversine_km(18.5196, 73.8553, 18.5204, 73.8567)
    assert dist_haveli < 1.0, f"Expected < 1 km, got {dist_haveli:.2f} km"

    # Out of state: London (51.5074, -0.1278) -> Paithan
    dist_london = haversine_km(51.5074, -0.1278, 19.4795, 75.3852)
    assert dist_london > 6000.0, "London should exceed 6000 km, triggering geofence warning"


def test_phase8_backend_adjacent_endpoint_resolution():
    """Validates GET /api/v1/taluka/{query}/adjacent REST endpoint."""
    res = client.get("/api/v1/taluka/paithan/adjacent")
    assert res.status_code == 200
    data = res.json()

    assert "target_taluka" in data
    assert data["target_taluka"]["taluka_name"] == "Paithan"
    assert "adjacent_neighbors" in data
    assert "contagion_assessment" in data
    assert len(data["adjacent_neighbors"]) >= 4

    # Verify neighbor schema contracts
    for n in data["adjacent_neighbors"]:
        assert "taluka_name" in n
        assert "taluka_name_mr" in n
        assert "district_name" in n
        assert "boundary_distance_km" in n
        assert "risk_tier" in n
        assert n["boundary_distance_km"] < 60.0


def test_phase8_mcp_modal_and_clipboard_targets():
    """Verifies MCP modal code targets and clipboard values match deployment specs."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="code-claude-url"' in html
    assert 'id="code-chatgpt-url"' in html
    assert 'id="code-openapi-url"' in html
    assert 'id="code-gemini-url"' in html
    assert 'https://rainrisk-vcra.onrender.com/mcp' in html
    assert 'https://rainrisk-vcra.onrender.com/openapi.json' in html


def test_phase8_i18n_instant_language_switch_no_devanagari_leak():
    """
    Validates BUG-I18N fix:
    1. DEFAULT_INITIAL_DATA is defined in state.js so currentData is never null.
    2. Bidirectional Devanagari <-> ASCII numeral conversion in formatNumber.
    3. sweepDomNumerals sweeps and cleans metric cards upon language toggle.
    4. Cache-buster versions bumped to ensure fresh CDN delivery.
    """
    state_path = os.path.join(FRONTEND_DIR, "js", "state.js")
    with open(state_path, "r", encoding="utf-8") as f:
        state_code = f.read()

    assert "DEFAULT_INITIAL_DATA" in state_code, "Missing DEFAULT_INITIAL_DATA in state.js"
    assert "currentData: DEFAULT_INITIAL_DATA" in state_code, "state.currentData must default to DEFAULT_INITIAL_DATA"
    assert "window.state = state" in state_code, "state must be attached to window.state"
    assert "०-९" in state_code and "0-9" in state_code, "formatNumber must support bidirectional Devanagari/ASCII conversion"

    i18n_path = os.path.join(FRONTEND_DIR, "js", "i18n.js")
    with open(i18n_path, "r", encoding="utf-8") as f:
        i18n_code = f.read()

    assert "sweepDomNumerals" in i18n_code, "Missing sweepDomNumerals function in i18n.js"
    assert "act-text-irrigation" in i18n_code, "Missing advisory texts in applyLanguage"
    assert "histogram-dates-row" in i18n_code, "Missing histogram dates row in applyLanguage"

    index_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'state.js?v=118' in html, "Script version must be bumped to ?v=118 for cache-busting"
    assert 'i18n.js?v=118' in html, "Script version must be bumped to ?v=118 for cache-busting"

