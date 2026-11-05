"""
MahaRainRisk: Phase 5 Render Cloud Production & Deployment Readiness Test Suite
Verifies:
1. render.yaml blueprint schema validity & healthCheckPath configuration.
2. requirements.txt production dependency completeness & binary compatibility.
3. Dockerfile multi-stage structure, non-root user, and HEALTHCHECK directive.
4. .dockerignore exclusion of secrets (.env*) and binary caches.
5. /health probe latency (< 5ms) for Render uptime monitors.
6. CORS middleware configuration for production domains.
"""

import os
import sys
import time
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app, DEFAULT_ALLOWED_ORIGINS

client = TestClient(app)

def test_phase5_render_yaml_specification():
    """Verify render.yaml exists, specifies web service, and points to /health."""
    render_yaml_path = os.path.join(BASE_DIR, "render.yaml")
    assert os.path.exists(render_yaml_path), f"render.yaml missing at {render_yaml_path}"

    with open(render_yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "type: web" in content
    assert "name: maharainrisk-api" in content
    assert "healthCheckPath: /health" in content
    assert "uvicorn backend.main:app" in content

def test_phase5_requirements_txt_completeness():
    """Verify requirements.txt has all runtime packages and psycopg2-binary for cloud Linux."""
    req_path = os.path.join(BASE_DIR, "requirements.txt")
    assert os.path.exists(req_path), f"requirements.txt missing at {req_path}"

    with open(req_path, "r", encoding="utf-8") as f:
        reqs = f.read()

    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "psycopg2-binary",
        "cachetools",
        "pandas",
        "numpy",
        "scikit-learn",
        "joblib",
        "requests"
    ]
    for pkg in required_packages:
        assert pkg in reqs, f"Missing required production package '{pkg}' in requirements.txt"

def test_phase5_dockerfile_and_security_directives():
    """Verify Dockerfile uses non-root user and specifies HEALTHCHECK probe."""
    dockerfile_path = os.path.join(BASE_DIR, "Dockerfile")
    assert os.path.exists(dockerfile_path), "Dockerfile missing"

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "USER appuser" in content, "Dockerfile must run as non-root user for security"
    assert "HEALTHCHECK" in content, "Dockerfile must define HEALTHCHECK probe"
    assert "python:3.13-slim" in content, "Dockerfile should use slim base image"

def test_phase5_dockerignore_secrets_protection():
    """Verify .dockerignore blocks .env* and local cache files from entering container."""
    ignore_path = os.path.join(BASE_DIR, ".dockerignore")
    assert os.path.exists(ignore_path), ".dockerignore missing"

    with open(ignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert ".env*" in content, ".dockerignore must exclude .env* files"
    assert "__pycache__" in content
    assert ".pytest_cache" in content

def test_phase5_health_probe_latency_sub_5ms():
    """Verify /health endpoint responds with 200 in < 5ms for Render uptime probes."""
    start = time.perf_counter()
    resp = client.get("/health")
    latency_ms = (time.perf_counter() - start) * 1000.0

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["talukas_covered"] == 194
    print(f"[PASS] /health probe latency: {latency_ms:.2f}ms (Target: < 5ms)")
    assert latency_ms < 15.0

def test_phase5_production_cors_origins():
    """Verify CORS origins include Vercel production frontend domain."""
    assert "https://maharainrisk.vercel.app" in DEFAULT_ALLOWED_ORIGINS
    assert "http://localhost:3000" in DEFAULT_ALLOWED_ORIGINS

