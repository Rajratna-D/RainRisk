"""
MahaRainRisk: Resilient Open-Meteo Ingestion Pipeline
Downloads with rate-limit compliance:
- Batch size: 6 talukas per request
- Adaptive sleep: 4 seconds between requests
- Exponential backoff on HTTP 429 (waits 10s, 20s)
- Resume capability: skips batches already saved to disk in data/raw/open_meteo/
"""

import os
import sys
import time
import json
import requests
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_PATH = os.path.join(BASE_DIR, "data", "geo", "lgd_maharashtra_master.csv")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "open_meteo")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(INTERIM_DIR, exist_ok=True)

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2020-01-01"  # Full multi-year timespan
END_DATE = "2026-10-15"    # Covers 2020 through October 2026
BATCH_SIZE = 6

def run_resilient_ingestion():
    print("=" * 70)
    print("   MahaRainRisk: Resilient Open-Meteo ERA5-Land Ingestion")
    print(f"   Period: {START_DATE} to {END_DATE} | Batch Size: {BATCH_SIZE}")
    print("=" * 70)

    talukas_df = pd.read_csv(GEO_PATH)
    total_talukas = len(talukas_df)
    num_batches = (total_talukas + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"[*] Ingesting {total_talukas} talukas in {num_batches} batches...")

    for batch_idx in range(num_batches):
        raw_batch_file = os.path.join(RAW_DIR, f"resilient_batch_{batch_idx:03d}.json")
        if os.path.exists(raw_batch_file):
            print(f"[Batch {batch_idx + 1}/{num_batches}] Already on disk. Skipping.")
            continue

        start_i = batch_idx * BATCH_SIZE
        end_i = min(start_i + BATCH_SIZE, total_talukas)
        batch_slice = talukas_df.iloc[start_i:end_i]

        lats = batch_slice["latitude"].tolist()
        lons = batch_slice["longitude"].tolist()
        names = batch_slice["taluka_name"].tolist()

        print(f"[Batch {batch_idx + 1}/{num_batches}] Fetching {len(lats)} talukas ({names[0]} to {names[-1]})...")

        params = {
            "latitude": lats,
            "longitude": lons,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "daily": [
                "precipitation_sum",
                "temperature_2m_max",
                "temperature_2m_min",
                "et0_fao_evapotranspiration",
                "soil_moisture_28_to_100cm_mean"
            ],
            "timezone": "Asia/Kolkata"
        }

        # Backoff loop
        backoff = 4
        success = False
        for attempt in range(4):
            try:
                r = requests.get(OPEN_METEO_URL, params=params, timeout=25)
                if r.status_code == 200:
                    data = r.json()
                    with open(raw_batch_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                    print(f"  [OK] Batch {batch_idx + 1} saved successfully.")
                    success = True
                    break
                elif r.status_code == 429:
                    print(f"  [!] HTTP 429 (rate-limited). Backing off for {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    print(f"  [!] HTTP {r.status_code}. Backing off {backoff}s...")
                    time.sleep(backoff)
                    backoff += 2
            except Exception as e:
                print(f"  [!] Network error: {e}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff += 2

        if not success:
            print(f"  [WARN] Skipping batch {batch_idx + 1} for now.")
        
        # Polite pause between calls
        time.sleep(3.5)

    # Compile all downloaded batches into clean datasets
    compile_all_batches(talukas_df)

def compile_all_batches(talukas_df):
    print("\n[*] Compiling all downloaded batch JSON files into master interim parquet...")
    all_files = sorted([f for f in os.listdir(RAW_DIR) if f.startswith("resilient_batch_") and f.endswith(".json")])
    if not all_files:
        print("[!] No resilient batch files found to compile.")
        return

    records = []
    total_locs = 0

    for f_name in all_files:
        f_path = os.path.join(RAW_DIR, f_name)
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        batch_idx = int(f_name.replace("resilient_batch_", "").replace(".json", ""))
        start_i = batch_idx * BATCH_SIZE
        end_i = min(start_i + BATCH_SIZE, len(talukas_df))
        batch_slice = talukas_df.iloc[start_i:end_i]

        for loc_idx, loc_data in enumerate(data):
            if loc_idx >= len(batch_slice):
                continue
            t_meta = batch_slice.iloc[loc_idx]
            total_locs += 1
            daily = loc_data.get("daily", {})
            dates = daily.get("time", [])
            rain = daily.get("precipitation_sum", [])
            tmax = daily.get("temperature_2m_max", [])
            tmin = daily.get("temperature_2m_min", [])
            et0 = daily.get("et0_fao_evapotranspiration", [])
            sm_root = daily.get("soil_moisture_28_to_100cm_mean", [])

            for k, dt in enumerate(dates):
                p_val = rain[k] if k < len(rain) else 0.0
                records.append({
                    "taluka_lgd_code": t_meta["taluka_lgd_code"],
                    "taluka_name": t_meta["taluka_name"],
                    "taluka_name_mr": t_meta["taluka_name_mr"],
                    "district_name": t_meta["district_name"],
                    "district_name_mr": t_meta["district_name_mr"],
                    "division_name": t_meta["division_name"],
                    "agro_climatic_zone": t_meta["agro_climatic_zone"],
                    "date": dt,
                    "rainfall_mm": p_val if p_val is not None else 0.0,
                    "temp_max_c": tmax[k] if k < len(tmax) else np.nan,
                    "temp_min_c": tmin[k] if k < len(tmin) else np.nan,
                    "et0_evapotranspiration_mm": et0[k] if k < len(et0) else np.nan,
                    "soil_moisture_root_zone": sm_root[k] if k < len(sm_root) else np.nan,
                    "is_rainy_day": int(p_val is not None and p_val >= 2.5)
                })

    df = pd.DataFrame(records)
    print(f"[OK] Total daily observations compiled: {len(df):,} across {total_locs} taluka locations.")
    
    out_parquet = os.path.join(INTERIM_DIR, "openmeteo_daily.parquet")
    out_csv = os.path.join(INTERIM_DIR, "openmeteo_daily.csv")
    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False)
    print(f"[OK] Master Open-Meteo dataset saved to: {out_parquet}")

    # Monthly aggregation
    df["year"] = pd.to_datetime(df["date"]).dt.year
    df["month"] = pd.to_datetime(df["date"]).dt.month
    df["year_month"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

    monthly = df.groupby([
        "taluka_lgd_code", "taluka_name", "taluka_name_mr",
        "district_name", "district_name_mr", "division_name", "agro_climatic_zone",
        "year", "month", "year_month"
    ]).agg(
        total_rainfall_mm=("rainfall_mm", "sum"),
        total_et0_mm=("et0_evapotranspiration_mm", "sum"),
        mean_tmax_c=("temp_max_c", "mean"),
        mean_tmin_c=("temp_min_c", "mean"),
        mean_soil_moisture_root=("soil_moisture_root_zone", "mean"),
        rainy_days=("is_rainy_day", "sum"),
        peak_daily_rain_mm=("rainfall_mm", "max")
    ).reset_index()

    monthly["water_deficit_p_minus_pet_mm"] = (monthly["total_rainfall_mm"] - monthly["total_et0_mm"]).round(1)
    monthly_out = os.path.join(INTERIM_DIR, "openmeteo_monthly.parquet")
    monthly.to_parquet(monthly_out, index=False)
    print(f"[OK] Monthly Open-Meteo aggregation saved to: {monthly_out}")

if __name__ == "__main__":
    run_resilient_ingestion()
