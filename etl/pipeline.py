"""
MahaRainRisk: Unified Master Data & Machine Learning Pipeline Coordinator
Orchestrates end-to-end execution across 5 automated stages:
  Stage 1: Ingestion Audit & Data Integrity Verification
  Stage 2: Multi-Scale Climatological SPI & SPEI Engine
  Stage 3: Master Agritech Feature Panel Compilation (Parquet + CSV)
  Stage 4: Dual Machine Learning Training (Mode 1 Diagnostic + Mode 2 Forecaster)
  Stage 5: Live Inference & Advisory Smoke Test (Paithan & Baramati)

Usage:
  python etl/pipeline.py --all       # Run complete end-to-end pipeline
  python etl/pipeline.py --audit     # Run comprehensive data inventory audit
  python etl/pipeline.py --stage spi # Run specific stage (spi, panel, ml, test)
"""

import os
import sys
import time
import argparse
import subprocess
import pandas as pd
import numpy as np

# Ensure Windows terminal prints UTF-8 (Marathi text support)
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
GEO_DIR = os.path.join(DATA_DIR, "geo")
RAW_DIR = os.path.join(DATA_DIR, "raw")
INTERIM_DIR = os.path.join(DATA_DIR, "interim")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
ML_DIR = os.path.join(BASE_DIR, "ml")

def print_header(title: str):
    print("\n" + "=" * 75)
    print(f"  {title.upper()}")
    print("=" * 75, flush=True)

# -------------------------------------------------------------------------
# STAGE 1: INVENTORY & INTEGRITY AUDIT
# -------------------------------------------------------------------------
def stage_audit():
    print_header("Stage 1: Comprehensive Data Inventory & Integrity Audit")
    audit_script = os.path.join(BASE_DIR, "etl", "audit_inventory.py")
    res = subprocess.run([sys.executable, audit_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(res.stdout)
    if res.returncode != 0:
        print(f"[ERROR] Audit failed:\n{res.stderr}")
        return False
    return True

# -------------------------------------------------------------------------
# STAGE 2: MULTI-SCALE SPI & SPEI ENGINE
# -------------------------------------------------------------------------
def stage_spi():
    print_header("Stage 2: Multi-Scale McKee Gamma SPI & SPEI Engine")
    spi_script = os.path.join(BASE_DIR, "etl", "compute_comprehensive_spi.py")
    t0 = time.time()
    res = subprocess.run([sys.executable, spi_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(res.stdout)
    if res.returncode != 0:
        print(f"[ERROR] SPI computation failed:\n{res.stderr}")
        return False

    out_file = os.path.join(PROCESSED_DIR, "imd_10yr_taluka_spi.parquet")
    if os.path.exists(out_file):
        df = pd.read_parquet(out_file)
        print(f"[OK] IMD 10-Year SPI verified: {len(df):,} rows across {df['taluka_lgd_code'].nunique()} talukas ({time.time()-t0:.2f}s)")
    return True

# -------------------------------------------------------------------------
# STAGE 3: MASTER FEATURE PANEL BUILDER
# -------------------------------------------------------------------------
def stage_master_panel():
    print_header("Stage 3: Master Agritech Panel Compilation (Parquet + CSV)")
    panel_script = os.path.join(BASE_DIR, "etl", "build_master_panel.py")
    t0 = time.time()
    res = subprocess.run([sys.executable, panel_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(res.stdout)
    if res.returncode != 0:
        print(f"[ERROR] Master panel build failed:\n{res.stderr}")
        return False

    # Data Quality Contract Assertions
    pq_path = os.path.join(PROCESSED_DIR, "master_panel.parquet")
    csv_path = os.path.join(PROCESSED_DIR, "master_panel.csv")
    df = pd.read_parquet(pq_path)

    assert os.path.exists(csv_path), "Missing master_panel.csv backup!"
    assert df["taluka_lgd_code"].nunique() == 194, f"Expected 194 talukas, found {df['taluka_lgd_code'].nunique()}"
    assert df["district_name"].nunique() == 36, f"Expected 36 districts, found {df['district_name'].nunique()}"
    assert df["drought_risk_category"].isna().sum() == 0, "Found nulls in target drought_risk_category!"

    print(f"\n[DATA QUALITY PASSED] All 194 talukas & 36 districts verified in master panel!")
    print(f"  Parquet: {pq_path} ({os.path.getsize(pq_path)/1024/1024:.2f} MB)")
    print(f"  CSV:     {csv_path} ({os.path.getsize(csv_path)/1024/1024:.2f} MB)")
    print(f"  Execution Time: {time.time()-t0:.2f}s")
    return True

# -------------------------------------------------------------------------
# STAGE 4: DUAL MACHINE LEARNING TRAINING
# -------------------------------------------------------------------------
def stage_ml():
    print_header("Stage 4: Training Dual Machine Learning Models")

    # 4A: Mode 1 - Live Diagnostic Model
    print("[*] Training Mode 1: Diagnostic Classifier (250 Trees)...")
    diag_script = os.path.join(BASE_DIR, "ml", "train.py")
    res1 = subprocess.run([sys.executable, diag_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in res1.stdout.split("\n"):
        if "Out-of-time" in line or "Top 5" in line or line.startswith("  -"):
            print(f"  {line}")

    # 4B: Mode 2 - 30-Day Predictive Forecaster
    print("\n[*] Training Mode 2: 30-Day Early Warning Forecaster (31 Dynamic Features)...")
    fore_script = os.path.join(BASE_DIR, "ml", "train_forecaster.py")
    res2 = subprocess.run([sys.executable, fore_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in res2.stdout.split("\n"):
        if "Accuracy:" in line or "Macro F1:" in line or "CHAMPION" in line or "Top 6" in line or line.startswith("  -"):
            print(f"  {line}")

    assert os.path.exists(os.path.join(ML_DIR, "drought_model.joblib")), "Missing drought_model.joblib"
    assert os.path.exists(os.path.join(ML_DIR, "drought_forecaster.joblib")), "Missing drought_forecaster.joblib"
    print("\n[OK] Both machine learning artifacts serialized successfully!")
    return True

# -------------------------------------------------------------------------
# STAGE 5: SMOKE TEST INFERENCE & ADVISORY
# -------------------------------------------------------------------------
def stage_smoke_test():
    print_header("Stage 5: Live Inference & Bilingual Advisory Smoke Test")
    try:
        from ml.predict import MahaRainRiskInference
        engine = MahaRainRiskInference()

        for t_name in ["Paithan", "Baramati"]:
            res = engine.analyze_taluka(t_name, year=2024, month=8)
            print(f"\n📍 Taluka: {res['meta']['taluka']} ({res['meta']['district']})")
            print(f"   Mode 1 Diagnosis:  {res['live_diagnosis']['label_en']} ({res['live_diagnosis']['label_mr']})")
            print(f"   Mode 2 Forecast:   Next Month -> {res['30_day_forecast']['label_en']}")
            print(f"   University Anchor: {res['advisory']['university_anchor']['university_name_en']}")
            print(f"   मराठी कृषी सल्ला: {res['advisory']['prescriptive_actions']['foliar_and_nutrients']['mr']}")
        print("\n[SMOKE TEST PASSED] Full end-to-end pipeline operational!")
        return True
    except Exception as e:
        print(f"[ERROR] Smoke test failed: {e}")
        return False

# -------------------------------------------------------------------------
# CLI DISPATCHER
# -------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="MahaRainRisk Master Pipeline Coordinator")
    parser.add_argument("--all", action="store_true", help="Execute complete 5-stage pipeline")
    parser.add_argument("--audit", action="store_true", help="Run comprehensive data inventory audit")
    parser.add_argument("--stage", type=str, choices=["audit", "spi", "panel", "ml", "test"], help="Run specific stage")
    args = parser.parse_args()

    t_start = time.time()

    if args.audit or args.stage == "audit":
        stage_audit()
    elif args.stage == "spi":
        stage_spi()
    elif args.stage == "panel":
        stage_master_panel()
    elif args.stage == "ml":
        stage_ml()
    elif args.stage == "test":
        stage_smoke_test()
    elif args.all or len(sys.argv) == 1:
        print("=" * 75)
        print("   MAHARAINRISK: EXECUTING FULL AUTOMATED 5-STAGE PIPELINE")
        print("=" * 75)
        if not stage_audit(): return
        if not stage_spi(): return
        if not stage_master_panel(): return
        if not stage_ml(): return
        if not stage_smoke_test(): return

        elapsed = time.time() - t_start
        print("\n" + "=" * 75)
        print(f" [SUCCESS] FULL PIPELINE COMPLETED IN {elapsed:.1f} SECONDS!")
        print("=" * 75)

if __name__ == "__main__":
    main()
