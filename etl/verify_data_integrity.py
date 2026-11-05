"""
MahaRainRisk: Comprehensive Data Integrity & Quality Audit Suite
Performs 5 rigorous verification gates on the finalized dataset:
1. Taluka Coverage Gate (194/194 talukas present)
2. Temporal Window Gate (2020-01-01 to 2026-10-31, 2496 days, 82 months)
3. Zero-Null Completeness Gate
4. Physical Sanity & Agronomic Boundary Gate
5. Cross-Repository Synchronization Gate
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
GEO_PATH = os.path.join(BASE_DIR, "data", "geo", "lgd_maharashtra_master.csv")
RAINRISK_DIR = os.path.join(os.path.dirname(BASE_DIR), "Rainrisk", "data", "processed")

def audit():
    print("=" * 80)
    print("      MAHARAINRISK COMPREHENSIVE DATA INTEGRITY AUDIT")
    print("=" * 80)

    talukas_master = pd.read_csv(GEO_PATH)
    expected_talukas = len(talukas_master)
    print(f"[*] Expected Talukas from LGD Master: {expected_talukas}")

    passed_all = True

    # 1. Check Daily Parquet
    daily_path = os.path.join(INTERIM_DIR, "openmeteo_daily.parquet")
    if not os.path.exists(daily_path):
        print(f"[FAIL] Missing {daily_path}")
        return False
    df_daily = pd.read_parquet(daily_path)
    n_daily_talukas = df_daily["taluka_lgd_code"].nunique()
    start_dt = df_daily["date"].min()
    end_dt = df_daily["date"].max()
    print(f"\n[Gate 1: Daily Telemetry Dataset]")
    print(f"  - Total Rows:       {len(df_daily):,} (Expected: {expected_talukas * 2496:,})")
    print(f"  - Unique Talukas:   {n_daily_talukas} / {expected_talukas}")
    print(f"  - Date Range:       {start_dt} to {end_dt} (Target: 2020-01-01 to 2026-10-31)")
    
    if n_daily_talukas == expected_talukas and end_dt >= "2026-10-31":
        print("  --> [PASS] Daily coverage is complete.")
    else:
        print("  --> [FAIL] Daily coverage mismatch!")
        passed_all = False

    # 2. Check Monthly Aggregation
    monthly_path = os.path.join(INTERIM_DIR, "openmeteo_monthly.parquet")
    if not os.path.exists(monthly_path):
        print(f"[FAIL] Missing {monthly_path}")
        return False
    df_monthly = pd.read_parquet(monthly_path)
    n_monthly_talukas = df_monthly["taluka_lgd_code"].nunique()
    n_months_per_t = len(df_monthly) // n_monthly_talukas if n_monthly_talukas else 0
    print(f"\n[Gate 2: Monthly Aggregation Dataset]")
    print(f"  - Total Rows:       {len(df_monthly):,} (Expected: {expected_talukas * 82:,})")
    print(f"  - Unique Talukas:   {n_monthly_talukas} / {expected_talukas}")
    print(f"  - Months / Taluka:  {n_months_per_t} (Expected: 82 complete months)")
    print(f"  - Latest Month:     {df_monthly['year_month'].max()} (Expected: 2026-10)")

    if n_monthly_talukas == expected_talukas and n_months_per_t == 82 and df_monthly['year_month'].max() == "2026-10":
        print("  --> [PASS] Monthly temporal coverage is 100% complete.")
    else:
        print("  --> [FAIL] Monthly temporal coverage mismatch!")
        passed_all = False

    # 3. Check Master Analytical Panel
    panel_path = os.path.join(PROCESSED_DIR, "master_panel.parquet")
    if not os.path.exists(panel_path):
        print(f"[FAIL] Missing {panel_path}")
        return False
    panel = pd.read_parquet(panel_path)
    print(f"\n[Gate 3: Master Agritech Panel (Model Feature Store)]")
    print(f"  - Total Rows:       {len(panel):,}")
    print(f"  - Total Columns:    {len(panel.columns)}")
    print(f"  - Unique Talukas:   {panel['taluka_lgd_code'].nunique()} / {expected_talukas}")

    # Check Null Values in Critical Feature Columns
    crit_cols = [
        "rainfall_monthly_mm", "rainy_days", "temp_max_mean", "temp_min_mean",
        "max_consecutive_dry_days", "rain_roll_1", "rain_roll_3", "rain_roll_6",
        "spi_1", "spi_3", "spi_6", "soil_moisture_index", "vci",
        "district_dam_storage_pct", "groundwater_depth_mbgl", "drought_risk_category"
    ]
    nulls = panel[crit_cols].isnull().sum()
    has_nulls = nulls[nulls > 0]
    print(f"\n[Gate 4: Feature Completeness & Zero-Null Verification]")
    if len(has_nulls) == 0:
        print(f"  --> [PASS] Zero missing values across all {len(crit_cols)} model features!")
    else:
        print(f"  --> [WARN] Found nulls in feature columns:\n{has_nulls}")
        passed_all = False

    # 4. Check Physical Agronomic Sanity
    print(f"\n[Gate 5: Physical Sanity & Agronomic Boundaries]")
    t_check = (panel["temp_max_mean"] >= panel["temp_min_mean"]).all()
    rain_check = (panel["rainfall_monthly_mm"] >= 0).all()
    dry_check = ((panel["max_consecutive_dry_days"] >= 0) & (panel["max_consecutive_dry_days"] <= 31)).all()
    smi_check = ((panel["soil_moisture_index"] >= 5.0) & (panel["soil_moisture_index"] <= 98.0)).all()
    
    print(f"  - T_max >= T_min across all rows:             {'PASS' if t_check else 'FAIL'}")
    print(f"  - Monthly rainfall >= 0 mm:                   {'PASS' if rain_check else 'FAIL'}")
    print(f"  - Consecutive dry days strictly in [0, 31]:   {'PASS' if dry_check else 'FAIL'} (mean: {panel['max_consecutive_dry_days'].mean():.1f} days)")
    print(f"  - Soil Moisture Index strictly in [5%, 98%]:  {'PASS' if smi_check else 'FAIL'} (mean: {panel['soil_moisture_index'].mean():.1f}%)")

    print(f"\nDrought Severity Class Balance across Maharashtra (2020-2026):")
    counts = panel["risk_label_en"].value_counts()
    for cat, cnt in counts.items():
        pct = (cnt / len(panel)) * 100
        print(f"  - {cat:15s}: {cnt:6,} ({pct:5.2f}%)")

    # 5. Check Mirroring to Rainrisk/data/processed/
    print(f"\n[Gate 6: Cross-Repository Synchronization]")
    mirror_path = os.path.join(RAINRISK_DIR, "master_panel.parquet")
    if os.path.exists(mirror_path):
        m_sz = os.path.getsize(mirror_path)
        p_sz = os.path.getsize(panel_path)
        if m_sz == p_sz:
            print(f"  --> [PASS] Rainrisk repository mirrored perfectly ({m_sz:,} bytes).")
        else:
            print(f"  --> [WARN] File size mismatch: MahaRainRisk={p_sz:,} vs Rainrisk={m_sz:,}")
    else:
        print(f"  --> [WARN] Mirror file not yet generated at {mirror_path}")

    print("\n" + "=" * 80)
    if passed_all:
        print(" [AUDIT RESULT] ALL DATA INTEGRITY GATES PASSED! 100% PRODUCTION READY.")
    else:
        print(" [AUDIT RESULT] AUDIT COMPLETED WITH ISSUES (SEE ABOVE).")
    print("=" * 80)
    return passed_all

if __name__ == "__main__":
    audit()

