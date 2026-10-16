"""
Integration and regression tests for RainRisk FastAPI backend endpoints.
"""
import pytest
import sys
import os

# Ensure backend and src directories are in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
for d in [PROJECT_ROOT, BACKEND_DIR, SRC_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

from fastapi.testclient import TestClient
from backend.main import app, state


@pytest.fixture(scope="module")
def client():
    """Initializes client with lifespan so data and models are loaded."""
    with TestClient(app) as c:
        yield c


class TestBackendEndpoints:
    def test_overview_endpoint(self, client):
        response = client.get("/api/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data
        assert data["total_records"] > 4000
        assert data["total_subdivisions"] == 36
        assert "normal_percentage" in data
        assert "category_distribution" in data
        assert len(data["category_distribution"]) == 6

    def test_subdivisions_endpoint(self, client):
        response = client.get("/api/subdivisions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 36
        first = data[0]
        assert "name" in first
        assert "lpa" in first
        assert "cv" in first
        assert "lat" in first
        assert "lon" in first

    def test_subdivision_detail_success(self, client):
        response = client.get("/api/subdivision/Coastal Karnataka")
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "timeline" in data
        assert "monthly" in data
        assert "epochs" in data
        assert "defaults" in data
        assert len(data["timeline"]) > 100
        assert len(data["monthly"]) == 12

    def test_subdivision_detail_not_found(self, client):
        response = client.get("/api/subdivision/NON_EXISTENT_SUBDIVISION_123")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_map_endpoint_actual(self, client):
        response = client.get("/api/map?year=2015&region=All India&mode=actual")
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2015
        assert data["total_subdivisions"] > 0
        assert "records" in data
        assert "top_deficient" in data
        assert "top_excess" in data
        first_record = data["records"][0]
        assert "subdivision" in first_record
        assert "departure" in first_record
        assert "category" in first_record

    def test_map_endpoint_invalid_year(self, client):
        response = client.get("/api/map?year=9999")
        assert response.status_code == 404

    def test_map_endpoint_invalid_region(self, client):
        response = client.get("/api/map?year=2015&region=InvalidRegionXYZ")
        assert response.status_code == 400
        assert "Invalid macro-region" in response.json()["detail"]

    def test_leaderboard_endpoint(self, client):
        response = client.get("/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "active_model" in data
        assert "models" in data
        assert len(data["models"]) > 0
        assert "confusion_matrix" in data
        assert "labels" in data["confusion_matrix"]

    def test_methodology_endpoint(self, client):
        response = client.get("/api/methodology")
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        assert len(data["features"]) == 24
        assert "gini_importance" in data
        assert "permutation_importance" in data

    def test_predict_endpoint(self, client):
        payload = {
            "subdivision": "COASTAL KARNATAKA",
            "prev_jjas": 3100.0,
            "prev_change": -150.0,
            "rolling_3yr": 3050.0,
            "rolling_5yr": 3120.0,
            "cv_5yr": 12.5,
            "prev_jun": 850.0,
            "prev_jul": 1100.0,
            "prev_aug": 800.0,
            "prev_sep": 350.0,
            "prev_jf": 5.0,
            "prev_mam": 120.0,
            "prev_ond": 250.0,
            "enso_djf": -0.5,
            "enso_mam": -0.3,
            "iod_mam": 0.2,
        }
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predicted_category" in data
        assert "color" in data
        assert "composite_drought_risk" in data
        assert "probabilities" in data
        # Confirms all 6 IMD operational categories are present in natural ordinal order
        assert len(data["probabilities"]) == 6
        assert [p["category"] for p in data["probabilities"]] == [
            "No Rainfall", "Large Deficient", "Deficient", "Normal", "Excess", "Large Excess"
        ]
        assert "advisory" in data
        assert "title" in data["advisory"]
        assert "actions" in data["advisory"]
        assert len(data["advisory"]["actions"]) > 0

    def test_spa_path_traversal_prevention(self, client):
        response = client.get("/../../requirements.txt")
        # Must serve index.html (SPA fallback) or error, never raw parent file contents
        assert "RainRisk" not in response.text or "<!doctype html>" in response.text
        assert "pandas>=" not in response.text

    def test_map_pre_1906_cold_start_flag(self, client):
        response = client.get("/api/map?year=1903&mode=prediction")
        assert response.status_code == 200
        data = response.json()
        assert data["prediction_available"] is False
        assert "warning" in data and data["warning"] is not None

    def test_health_endpoints(self, client):
        for path in ["/health", "/api/health"]:
            response = client.get(path)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["model_loaded"] is True
            assert data["data_loaded"] is True
            assert data["version"] == "2.0.0"
            assert data["total_records"] > 4000

    def test_unknown_api_endpoint_returns_404(self, client):
        response = client.get("/api/nonexistent_route")
        assert response.status_code == 404
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert "detail" in data

    def test_security_headers_present(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_predict_bounds_validation_rejects_negative_rainfall(self, client):
        payload = {
            "subdivision": "Kerala",
            "prev_jjas": -500.0,  # Negative rainfall should be rejected with 422
            "prev_change": 0.0,
            "rolling_3yr": 1500.0,
            "rolling_5yr": 1500.0,
            "cv_5yr": 20.0,
            "prev_jun": 300.0,
            "prev_jul": 500.0,
            "prev_aug": 400.0,
            "prev_sep": 300.0,
            "prev_jf": 30.0,
            "prev_mam": 120.0,
            "prev_ond": 150.0,
            "enso_djf": 0.0,
            "enso_mam": 0.0,
            "iod_mam": 0.0,
        }
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 422

    def test_predict_bounds_validation_rejects_impossible_sst(self, client):
        payload = {
            "subdivision": "Kerala",
            "prev_jjas": 1500.0,
            "prev_change": 0.0,
            "rolling_3yr": 1500.0,
            "rolling_5yr": 1500.0,
            "cv_5yr": 20.0,
            "prev_jun": 300.0,
            "prev_jul": 500.0,
            "prev_aug": 400.0,
            "prev_sep": 300.0,
            "prev_jf": 30.0,
            "prev_mam": 120.0,
            "prev_ond": 150.0,
            "enso_djf": 99.0,  # Impossible SST anomaly should be rejected with 422
            "enso_mam": 0.0,
            "iod_mam": 0.0,
        }
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 422

    def test_subdivision_case_insensitive_lookup(self, client):
        response = client.get("/api/subdivision/coastal karnataka")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "Coastal Karnataka"

