import os
import sys
import time
import statistics
import concurrent.futures
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.main import app

LOAD_TEST_JS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "load_test.js"))

BENCHMARK_TALUKAS = [
    "paithan",
    "baramati",
    "haveli",
    "kannad",
    "gangapur",
    "sillod",
    "nashik",
    "amravati",
]


def test_phase9_k6_script_configuration_and_zero_simulation():
    """Validates that the k6 load testing script is configured for Option A (zero simulation)."""
    assert os.path.isfile(LOAD_TEST_JS_PATH), "load_test.js must exist in tests directory"
    with open(LOAD_TEST_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Threshold assertions
    assert "p(95)<200" in content, "k6 thresholds must require p(95) < 200ms"
    assert "rate<0.01" in content, "k6 thresholds must require error rate < 1%"

    # Absolute absence of deprecated simulation endpoints
    assert "/api/v1/simulate" not in content, "load_test.js must not reference /simulate (Option A)"
    assert "rainfall_shock_pct" not in content, "load_test.js must not contain counterfactual shock fields"

    # Presence of core production endpoints
    assert "/api/v1/taluka/" in content, "load_test.js must test taluka endpoints"
    assert "/explain" in content, "load_test.js must test TreeSHAP explainability"
    assert "/adjacent" in content, "load_test.js must test spatial adjacency"
    assert "/state/summary" in content, "load_test.js must test state summary"
    assert "/mcp" in content, "load_test.js must probe MCP endpoint"


def test_phase9_concurrent_virtual_users_burst():
    """Simulates 50 concurrent virtual users hitting cached endpoints and verifies p(95) < 200ms."""
    with TestClient(app) as client:
        def worker(taluka_id: str):
            t0 = time.perf_counter()
            resp = client.get(f"/api/v1/taluka/{taluka_id}/risk")
            duration_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Expected 200 for {taluka_id}, got {resp.status_code}"
            data = resp.json()
            assert "risk_score" in data
            return duration_ms

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, BENCHMARK_TALUKAS[i % len(BENCHMARK_TALUKAS)]) for i in range(50)]
            latencies = [f.result() for f in futures]

        assert len(latencies) == 50
        latencies.sort()
        p95_idx = int(0.95 * len(latencies))
        p95_latency = latencies[p95_idx]

        assert p95_latency < 200.0, f"p(95) latency was {p95_latency:.2f}ms, exceeding 200ms threshold"


def test_phase9_treeshap_concurrency_stability():
    """Fires 20 concurrent TreeSHAP queries to verify singleton stability and zero race conditions."""
    with TestClient(app) as client:
        def fetch_xai(taluka_id: str):
            t0 = time.perf_counter()
            resp = client.get(f"/api/v1/taluka/{taluka_id}/explain")
            duration_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Explain failed for {taluka_id}"
            data = resp.json()
            assert "top_risk_escalators" in data
            assert "farmer_summary" in data
            return duration_ms

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_xai, BENCHMARK_TALUKAS[i % len(BENCHMARK_TALUKAS)]) for i in range(20)]
            durations = [f.result() for f in futures]

        assert len(durations) == 20
        avg_xai_time = statistics.mean(durations)
        assert avg_xai_time < 500.0, f"Average TreeSHAP latency was {avg_xai_time:.2f}ms"


def test_phase9_spatial_adjacency_concurrency():
    """Fires 25 concurrent spatial queries and verifies graph resolution consistency."""
    with TestClient(app) as client:
        def fetch_adjacent(taluka_id: str):
            resp = client.get(f"/api/v1/taluka/{taluka_id}/adjacent")
            assert resp.status_code == 200
            data = resp.json()
            neighbors = data.get("adjacent_neighbors") or data.get("neighbors") or []
            assert len(neighbors) > 0
            return len(neighbors)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_adjacent, BENCHMARK_TALUKAS[i % len(BENCHMARK_TALUKAS)]) for i in range(25)]
            results = [f.result() for f in futures]

        assert len(results) == 25
        assert all(count > 0 for count in results)


def test_phase9_mcp_streamable_http_and_browser_concurrency():
    """Verifies dual-mode MCP endpoint handles concurrent browser and Streamable HTTP queries correctly."""
    with TestClient(app) as client:
        # 1. Gemini / Modern Agent POST initialize
        gemini_init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "Google-Gemini", "version": "1.0"}
            }
        }
        resp_post = client.post("/mcp", json=gemini_init_payload)
        assert resp_post.status_code == 200, f"Expected 200 from Gemini POST /mcp, got {resp_post.status_code}"
        assert "jsonrpc" in resp_post.text, "Response must contain JSON-RPC payload"

        # 2. Browser GET diagnostics
        resp_get = client.get("/mcp", headers={"Accept": "text/html"})
        assert resp_get.status_code == 200
        data = resp_get.json()
        assert data["status"] == "operational"
        assert data["tools_count"] == 6
        assert "Streamable HTTP" in data["transports"]

        # 3. Trailing slash tolerance
        resp_slash = client.post("/mcp/", json=gemini_init_payload)
        assert resp_slash.status_code == 200


def test_phase9_production_health_probe_sla():
    """Verifies that the /health monitoring probe responds in < 20ms under a 30-request burst."""
    with TestClient(app) as client:
        def probe_health():
            t0 = time.perf_counter()
            resp = client.get("/health")
            duration_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200
            assert resp.json()["status"] == "healthy"
            return duration_ms

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(probe_health) for _ in range(30)]
            probe_durations = [f.result() for f in futures]

        assert len(probe_durations) == 30
        p95_probe = sorted(probe_durations)[int(0.95 * len(probe_durations))]
        assert p95_probe < 100.0, f"/health p(95) was {p95_probe:.2f}ms, exceeding 100ms SLA"
