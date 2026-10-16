#!/usr/bin/env python3
"""
RainRisk: Deployment Health & Endpoint Verification Utility

Validates that a live or local deployment is completely operational:
1. Health probe (/health)
2. API overview & aggregate metrics (/api/overview)
3. Subdivisions directory (/api/subdivisions)
4. Detail drill-down (/api/subdivision/Vidarbha)
5. Geospatial map intelligence (/api/map)
6. Model inference & agronomic advisory pipeline (/api/predict)
7. SPA frontend static serving (/)
8. Safe 404 API handling (/api/unknown)

Usage:
    python scripts/verify_deployment.py --url http://localhost:8008
    python scripts/verify_deployment.py --url https://rainrisk.onrender.com
"""

import sys
import time
import argparse
import urllib.request
import json
import ssl

def check_endpoint(name: str, url: str, method: str = "GET", data: dict = None, expected_status: int = 200, validator=None):
    start = time.perf_counter()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, method=method)
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        req.data = payload

    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000
            status = resp.status
            body = resp.read().decode("utf-8")
            parsed = None
            if resp.headers.get_content_type() == "application/json":
                try:
                    parsed = json.loads(body)
                except Exception:
                    pass

            if status != expected_status:
                print(f"  [FAIL] {name:<35} Status {status} != {expected_status} ({elapsed_ms:.1f}ms)")
                return False

            if validator and not validator(parsed, body):
                print(f"  [FAIL] {name:<35} Validation criteria not met ({elapsed_ms:.1f}ms)")
                return False

            print(f"  [PASS] {name:<35} Status {status} OK ({elapsed_ms:.1f}ms)")
            return True

    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        if e.code == expected_status:
            print(f"  [PASS] {name:<35} Status {e.code} OK ({elapsed_ms:.1f}ms)")
            return True
        print(f"  [FAIL] {name:<35} HTTPError {e.code}: {e.reason} ({elapsed_ms:.1f}ms)")
        return False
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  [FAIL] {name:<35} Connection Error: {e} ({elapsed_ms:.1f}ms)")
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify RainRisk deployment health")
    parser.add_argument("--url", default="http://localhost:8008", help="Target base URL (default: http://localhost:8008)")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    print("=" * 70)
    print(f"  RainRisk Deployment Verifier")
    print(f"  Target: {base}")
    print("=" * 70)

    checks = [
        (
            "1. Health Probe (/health)",
            f"{base}/health",
            "GET",
            None,
            200,
            lambda data, _: data and data.get("status") == "healthy" and data.get("model_loaded") is True,
        ),
        (
            "2. Overview Metrics (/api/overview)",
            f"{base}/api/overview",
            "GET",
            None,
            200,
            lambda data, _: data and data.get("total_subdivisions") == 36 and "national_lpa" in data,
        ),
        (
            "3. Subdivisions List (/api/subdivisions)",
            f"{base}/api/subdivisions",
            "GET",
            None,
            200,
            lambda data, _: isinstance(data, list) and len(data) == 36,
        ),
        (
            "4. Sub. Detail (/api/subdivision/Vidarbha)",
            f"{base}/api/subdivision/Vidarbha",
            "GET",
            None,
            200,
            lambda data, _: data and "timeline" in data and len(data["timeline"]) > 50,
        ),
        (
            "5. Geospatial Map (/api/map)",
            f"{base}/api/map?year=2015&region=All%20India&mode=actual",
            "GET",
            None,
            200,
            lambda data, _: data and "records" in data and len(data["records"]) == 36,
        ),
        (
            "6. ML Inference (/api/predict)",
            f"{base}/api/predict",
            "POST",
            {
                "subdivision": "Vidarbha",
                "prev_jjas": 850.0,
                "prev_change": -5.0,
                "rolling_3yr": 870.0,
                "rolling_5yr": 890.0,
                "cv_5yr": 18.5,
                "prev_jun": 150.0,
                "prev_jul": 300.0,
                "prev_aug": 250.0,
                "prev_sep": 150.0,
                "prev_jf": 10.0,
                "prev_mam": 20.0,
                "prev_ond": 50.0,
                "enso_djf": -0.4,
                "enso_mam": -0.2,
                "iod_mam": 0.1,
            },
            200,
            lambda data, _: data and "predicted_category" in data and "probabilities" in data and "advisory" in data,
        ),
        (
            "7. Frontend SPA Shell (/)",
            f"{base}/",
            "GET",
            None,
            200,
            lambda _, text: "<!doctype html>" in text.lower() or "rainrisk" in text.lower(),
        ),
        (
            "8. API 404 Guard (/api/nonexistent)",
            f"{base}/api/nonexistent",
            "GET",
            None,
            404,
            None,
        ),
    ]

    passed = 0
    total = len(checks)

    for name, url, method, data, status, val in checks:
        if check_endpoint(name, url, method=method, data=data, expected_status=status, validator=val):
            passed += 1

    print("=" * 70)
    if passed == total:
        print(f"  [SUCCESS] All {total}/{total} deployment verification checks passed!")
        print("  RainRisk is fully operational and production ready.")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"  [WARNING] {passed}/{total} checks passed. Please inspect failing endpoints above.")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
