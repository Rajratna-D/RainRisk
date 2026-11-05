"""
Fetch the remaining 5 missing batches from Open-Meteo and compile master datasets.
Missing batches: [9, 10, 11, 21, 28]
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
START_DATE = "2020-01-01"
END_DATE = "2026-10-15"
BATCH_SIZE = 6

def main():
    talukas_df = pd.read_csv(GEO_PATH)
    total_talukas = len(talukas_df)
    num_batches = (total_talukas + BATCH_SIZE - 1) // BATCH_SIZE

    # Find missing batches
    missing_batches = []
    for b_idx in range(num_batches):
        f = os.path.join(RAW_DIR, f"resilient_batch_{b_idx:03d}.json")
        if not os.path.exists(f):
            missing_batches.append(b_idx)

    print(f"Total batches required: {num_batches}", flush=True)
    print(f"Missing batches to fetch: {missing_batches}", flush=True)

    session = requests.Session()
    # Add standard User-Agent header
    session.headers.update({"User-Agent": "MahaRainRisk-Research/1.0 (Agriculture Drought Early Warning)"})

    for batch_idx in missing_batches:
        raw_batch_file = os.path.join(RAW_DIR, f"resilient_batch_{batch_idx:03d}.json")
        start_i = batch_idx * BATCH_SIZE
        end_i = min(start_i + BATCH_SIZE, total_talukas)
        batch_slice = talukas_df.iloc[start_i:end_i]

        lats = batch_slice["latitude"].tolist()
        lons = batch_slice["longitude"].tolist()
        names = batch_slice["taluka_name"].tolist()

        print(f"\n---> Fetching Batch {batch_idx} ({len(lats)} talukas: {names[0]} to {names[-1]})...", flush=True)

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

        success = False
        for attempt in range(1, 6):
            try:
                t0 = time.time()
                resp = session.get(OPEN_METEO_URL, params=params, timeout=45)
                elapsed = time.time() - t0

                if resp.status_code == 200:
                    data = resp.json()
                    with open(raw_batch_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                    print(f"  [SUCCESS] Batch {batch_idx} saved ({elapsed:.2f}s, {len(resp.content)} bytes).", flush=True)
                    success = True
                    break
                elif resp.status_code == 429:
                    wait_time = 10 * attempt
                    print(f"  [HTTP 429] Rate limit hit. Waiting {wait_time}s before retry {attempt}/5...", flush=True)
                    time.sleep(wait_time)
                else:
                    wait_time = 5 * attempt
                    print(f"  [HTTP {resp.status_code}] Unexpected status. Waiting {wait_time}s...", flush=True)
                    time.sleep(wait_time)
            except Exception as e:
                wait_time = 5 * attempt
                print(f"  [Error] {e}. Waiting {wait_time}s...", flush=True)
                time.sleep(wait_time)

        if not success:
            print(f"  [FAILED] Could not download batch {batch_idx}.", flush=True)

        # Respectful pause between batches to avoid 429
        time.sleep(6.0)

    # Re-check how many batches we have
    existing_files = sorted([f for f in os.listdir(RAW_DIR) if f.startswith("resilient_batch_") and f.endswith(".json")])
    print(f"\nTotal batches on disk: {len(existing_files)} / {num_batches}", flush=True)

    # Now compile master datasets
    compile_master_datasets(talukas_df)

def compile_master_datasets(talukas_df):
    print("\n" + "=" * 70, flush=True)
    print(" Compiling all Open-Meteo batches into master interim datasets...", flush=True)
    print("=" * 70, flush=True)

    all_files = sorted([f for f in os.listdir(RAW_DIR) if f.startswith("resilient_batch_") and f.endswith(".json")])
    total_talukas = len(talukas_df)
    records = []

    for f_name in all_files:
        b_idx = int(f_name.replace("resilient_batch_", "").replace(".json", ""))
        start_i = b_idx * BATCH_SIZE
        end_i = min(start_i + BATCH_SIZE, total_talukas)
        batch_slice = talukas_df.iloc[start_i:end_i]

        with open(os.path.join(RAW_DIR, f_name), "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        for loc_idx, loc_data in enumerate(data):
            if loc_idx >= len(batch_slice):
                continue
            meta = batch_slice.iloc[loc_idx]
            daily = loc_data.get("daily", {})
            dates = daily.get("time", [])
            rain = daily.get("precipitation_sum", [])
            tmax = daily.get("temperature_2m_max", [])
            tmin = daily.get("temperature_2m_min", [])
            et0 = daily.get("et0_fao_evapotranspiration", [])
            sm_root = daily.get("soil_moisture_28_to_100cm_mean", [])

            for k, dt in enumerate(dates):
                p_val = rain[k] if k < len(rain) else 0.0
                p_float = round(float(p_val) if p_val is not None else 0.0, 2)
                records.append({
                    "taluka_lgd_code": meta["taluka_lgd_code"],
                    "taluka_name": meta["taluka_name"],
                    "taluka_name_mr": meta.get("taluka_name_mr", ""),
                    "district_lgd_code": meta.get("district_lgd_code", ""),
                    "district_name": meta["district_name"],
                    "district_name_mr": meta.get("district_name_mr", ""),
                    "division_name": meta.get("division_name", ""),
                    "division_name_mr": meta.get("division_name_mr", ""),
                    "date": dt,
                    "rainfall_mm": p_float,
                    "temp_max_c": round(float(tmax[k]), 1) if (k < len(tmax) and tmax[k] is not None) else np.nan,
                    "temp_min_c": round(float(tmin[k]), 1) if (k < len(tmin) and tmin[k] is not None) else np.nan,
                    "et0_fao_evapotranspiration": round(float(et0[k]), 2) if (k < len(et0) and et0[k] is not None) else np.nan,
                    "et0_evapotranspiration_mm": round(float(et0[k]), 2) if (k < len(et0) and et0[k] is not None) else np.nan,
                    "soil_moisture_root_zone": round(float(sm_root[k]), 4) if (k < len(sm_root) and sm_root[k] is not None) else np.nan,
                    "is_rainy_day": 1 if p_float >= 2.5 else 0,
                    "latitude": meta["latitude"],
                    "longitude": meta["longitude"],
                    "agro_climatic_zone": meta.get("agro_climatic_zone", ""),
                    "university_affiliation": meta.get("university_affiliation", "")
                })

    print(f"Total compiled daily records: {len(records)} across {len(records) // 2480 if records else 0} talukas", flush=True)
    df_daily = pd.DataFrame(records)
    df_daily["date"] = pd.to_datetime(df_daily["date"])

    # Save daily master parquet & csv
    daily_parquet = os.path.join(INTERIM_DIR, "openmeteo_daily.parquet")
    daily_csv = os.path.join(INTERIM_DIR, "openmeteo_daily.csv")
    df_daily.to_parquet(daily_parquet, index=False)
    print(f"[OK] Saved daily master parquet: {daily_parquet} ({len(df_daily):,} rows)", flush=True)

    # Monthly aggregation
    df_daily["year"] = df_daily["date"].dt.year
    df_daily["month"] = df_daily["date"].dt.month
    df_daily["year_month"] = df_daily["year"].astype(str) + "-" + df_daily["month"].astype(str).str.zfill(2)

    monthly_df = df_daily.groupby([
        "taluka_lgd_code", "taluka_name", "taluka_name_mr",
        "district_lgd_code", "district_name", "district_name_mr",
        "division_name", "division_name_mr", "agro_climatic_zone", "university_affiliation",
        "latitude", "longitude", "year", "month", "year_month"
    ], as_index=False).agg({
        "rainfall_mm": ["sum", "max"],
        "temp_max_c": "mean",
        "temp_min_c": "mean",
        "et0_fao_evapotranspiration": "sum",
        "soil_moisture_root_zone": "mean",
        "is_rainy_day": "sum"
    })

    # Flatten MultiIndex columns
    monthly_df.columns = [
        "taluka_lgd_code", "taluka_name", "taluka_name_mr",
        "district_lgd_code", "district_name", "district_name_mr",
        "division_name", "division_name_mr", "agro_climatic_zone", "university_affiliation",
        "latitude", "longitude", "year", "month", "year_month",
        "total_rainfall_mm", "peak_daily_rain_mm",
        "mean_tmax_c", "mean_tmin_c",
        "total_et0_mm", "mean_soil_moisture_root", "rainy_days"
    ]

    # Provide all compatible aliases
    monthly_df["monthly_rainfall_mm"] = monthly_df["total_rainfall_mm"]
    monthly_df["monthly_et0_mm"] = monthly_df["total_et0_mm"]
    monthly_df["mean_soil_moisture_root_zone"] = monthly_df["mean_soil_moisture_root"]
    monthly_df["water_deficit_p_minus_pet_mm"] = (monthly_df["total_rainfall_mm"] - monthly_df["total_et0_mm"]).round(1)
    monthly_df["water_deficit_p_minus_et0"] = monthly_df["water_deficit_p_minus_pet_mm"]

    monthly_parquet = os.path.join(INTERIM_DIR, "openmeteo_monthly.parquet")
    monthly_csv = os.path.join(INTERIM_DIR, "openmeteo_monthly.csv")
    monthly_df.to_parquet(monthly_parquet, index=False)
    monthly_df.to_csv(monthly_csv, index=False)
    print(f"[OK] Saved monthly master parquet: {monthly_parquet} ({len(monthly_df):,} rows)", flush=True)
    print(f"[OK] Saved monthly master CSV: {monthly_csv}", flush=True)

    # Automatically execute downstream processing
    import subprocess
    print("\n" + "=" * 70, flush=True)
    print(" Triggering downstream SPI, Master Panel & Model Pipeline...", flush=True)
    print("=" * 70, flush=True)

    spi_script = os.path.join(BASE_DIR, "etl", "compute_comprehensive_spi.py")
    print(f"[*] Running {spi_script}...", flush=True)
    subprocess.run([sys.executable, spi_script], check=True)

    panel_script = os.path.join(BASE_DIR, "etl", "build_master_panel.py")
    print(f"[*] Running {panel_script}...", flush=True)
    subprocess.run([sys.executable, panel_script], check=True)

    train_script = os.path.join(BASE_DIR, "ml", "train.py")
    print(f"[*] Running {train_script}...", flush=True)
    subprocess.run([sys.executable, train_script], check=True)

    print("\n[COMPLETE] 100% End-to-End Pipeline Executed Successfully!", flush=True)

if __name__ == "__main__":
    main()

