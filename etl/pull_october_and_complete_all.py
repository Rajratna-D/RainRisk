"""
MahaRainRisk: Ingest Complete October 2026 & Finalize All 194 Talukas
Fetches full daily telemetry through 2026-10-31 (2,496 days, 82 complete months).
- Batches 0-23 & 28: extends from Oct 16 to Oct 31 (16 days).
- Batches 24-27 & 29-32: fetches full 2020-01-01 to 2026-10-31 taluka-by-taluka with persistent taluka cache.
- Auto-handles Open-Meteo Retry-After header.
- Compiles master interim daily (484,224 rows) and monthly (15,908 rows) datasets.
- Automatically executes compute_comprehensive_spi and build_master_panel upon completion.
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
TALUKA_CACHE_DIR = os.path.join(RAW_DIR, "taluka_cache")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(TALUKA_CACHE_DIR, exist_ok=True)
os.makedirs(INTERIM_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
FULL_START = "2020-01-01"
FULL_END = "2026-10-31"
OCT_EXT_START = "2026-10-16"
OCT_EXT_END = "2026-10-31"
BATCH_SIZE = 6

DAILY_VARS = [
    "precipitation_sum",
    "temperature_2m_max",
    "temperature_2m_min",
    "et0_fao_evapotranspiration",
    "soil_moisture_28_to_100cm_mean"
]

def fetch_with_retry(params, timeout=85, max_attempts=12):
    backoff = 6
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.get(OPEN_METEO_URL, params=params, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                if not isinstance(data, list):
                    data = [data]
                return data
            elif r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                if retry_after:
                    wait_s = int(retry_after) + 3
                    print(f"\n    [!] HTTP 429: Open-Meteo Retry-After header: {wait_s}s. Sleeping...", flush=True)
                    time.sleep(wait_s)
                    continue
                print(f"    [!] HTTP 429 rate limit. Cooling down {backoff}s...", flush=True)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
            else:
                print(f"    [!] HTTP {r.status_code}. Retrying in {backoff}s...", flush=True)
                time.sleep(backoff)
                backoff += 5
        except Exception as e:
            print(f"    [!] Request error: {e}. Retrying in {backoff}s...", flush=True)
            time.sleep(backoff)
            backoff += 5
    return None

def process_batch(batch_idx, batch_slice):
    raw_batch_file = os.path.join(RAW_DIR, f"resilient_batch_{batch_idx:03d}.json")
    n_talukas = len(batch_slice)
    names = batch_slice["taluka_name"].tolist()

    # Check disk state
    if os.path.exists(raw_batch_file):
        try:
            with open(raw_batch_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
            item = existing[0]
            times = item.get("daily", {}).get("time", [])
            
            # Case 1: Already complete through 2026-10-31
            if len(times) >= 2496 and times[-1] >= FULL_END:
                print(f"[*] Batch {batch_idx:02d} ({names[0]}..{names[-1]}): Complete through {FULL_END} ({len(times)} days). Skipping.", flush=True)
                return True

            # Case 2: Has 2020-01-01 to 2026-10-15 (2,480 days) -> Fetch only 16 days extension
            if len(times) >= 2480 and times[-1] >= "2026-10-15":
                print(f"[*] Batch {batch_idx:02d} ({names[0]}..{names[-1]}): Extending from Oct 16 to Oct 31 (16 days)...", end=" ", flush=True)
                params = {
                    "latitude": batch_slice["latitude"].tolist(),
                    "longitude": batch_slice["longitude"].tolist(),
                    "start_date": OCT_EXT_START,
                    "end_date": OCT_EXT_END,
                    "daily": DAILY_VARS,
                    "timezone": "Asia/Kolkata"
                }
                ext_data = fetch_with_retry(params, timeout=30)
                if ext_data and len(ext_data) == n_talukas:
                    for loc_i in range(n_talukas):
                        ext_daily = ext_data[loc_i].get("daily", {})
                        base_daily = existing[loc_i].get("daily", {})
                        for k in ["time"] + DAILY_VARS:
                            if k in ext_daily and k in base_daily:
                                base_daily[k].extend(ext_daily[k])
                    with open(raw_batch_file, "w", encoding="utf-8") as f:
                        json.dump(existing, f)
                    new_len = len(existing[0]["daily"]["time"])
                    print(f"[OK -> {new_len} days, ends {existing[0]['daily']['time'][-1]}]", flush=True)
                    time.sleep(2.0)
                    return True
                else:
                    print("[FAILED to extend]", flush=True)
                    return False
        except Exception as e:
            print(f"[!] Error reading batch {batch_idx}: {e}. Will refetch.", flush=True)

    # Case 3: Missing or old data -> Fetch full 2020-2026 taluka-by-taluka with persistent disk cache
    print(f"[*] Batch {batch_idx:02d} ({names[0]}..{names[-1]}): Full 2020-2026 fetch ({n_talukas} talukas)...", flush=True)
    batch_records = []
    for loc_i in range(n_talukas):
        t_row = batch_slice.iloc[loc_i]
        t_code = t_row["taluka_lgd_code"]
        t_name = t_row["taluka_name"]
        cache_file = os.path.join(TALUKA_CACHE_DIR, f"taluka_{t_code}.json")

        # Check single-taluka cache
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                c_times = c_data.get("daily", {}).get("time", [])
                if len(c_times) >= 2496 and c_times[-1] >= FULL_END:
                    print(f"    [{loc_i+1}/{n_talukas}] {t_name}: Loaded from cache ({len(c_times)} days).", flush=True)
                    batch_records.append(c_data)
                    continue
            except Exception:
                pass

        print(f"    [{loc_i+1}/{n_talukas}] {t_name} (lat: {t_row['latitude']:.4f}, lon: {t_row['longitude']:.4f})...", end=" ", flush=True)
        params = {
            "latitude": [t_row["latitude"]],
            "longitude": [t_row["longitude"]],
            "start_date": FULL_START,
            "end_date": FULL_END,
            "daily": DAILY_VARS,
            "timezone": "Asia/Kolkata"
        }
        loc_res = fetch_with_retry(params, timeout=85)
        if loc_res and len(loc_res) >= 1:
            item = loc_res[0]
            n_days = len(item.get("daily", {}).get("time", []))
            print(f"[OK: {n_days} days]", flush=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(item, f)
            batch_records.append(item)
        else:
            print("[FAILED]", flush=True)
            return False
        time.sleep(2.5)

    with open(raw_batch_file, "w", encoding="utf-8") as f:
        json.dump(batch_records, f)
    print(f"  [SUCCESS] Batch {batch_idx:02d} saved with {len(batch_records)} talukas ({FULL_START} to {FULL_END}).", flush=True)
    time.sleep(2.0)
    return True

def compile_all():
    print("\n" + "=" * 75, flush=True)
    print("   COMPILING MASTER DATASETS FOR ALL 194 TALUKAS THROUGH 2026-10-31", flush=True)
    print("=" * 75, flush=True)

    talukas_df = pd.read_csv(GEO_PATH)
    all_files = sorted([f for f in os.listdir(RAW_DIR) if f.startswith("resilient_batch_") and f.endswith(".json")])
    
    print(f"[*] Found {len(all_files)} batch files. Compiling daily observations...", flush=True)

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
    print(f"\n[OK] Daily Observations Compiled: {len(df):,} across {total_locs} talukas.", flush=True)
    print(f"     Date Range: {df['date'].min()} to {df['date'].max()}", flush=True)

    out_parquet = os.path.join(INTERIM_DIR, "openmeteo_daily.parquet")
    out_csv = os.path.join(INTERIM_DIR, "openmeteo_daily.csv")
    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False)
    print(f"[OK] Master Daily dataset saved: {out_parquet}", flush=True)

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
    print(f"[OK] Master Monthly dataset saved: {monthly_out} ({len(monthly):,} rows)", flush=True)
    print(f"     Total Months per Taluka: {len(monthly) // total_locs} complete calendar months (82 expected).", flush=True)

    # Trigger downstream feature engineering
    print("\n[*] Triggering Comprehensive SPI & SPEI Computation...", flush=True)
    sys.path.append(os.path.join(BASE_DIR, "etl"))
    import compute_comprehensive_spi
    compute_comprehensive_spi.main()

    print("\n[*] Triggering Master Agritech Panel Builder (Physical Ground Truth)...", flush=True)
    import build_master_panel
    build_master_panel.build_master_panel()

    # Also mirror master_panel.parquet to Rainrisk/data/processed/ if directory exists
    rainrisk_processed = os.path.join(os.path.dirname(BASE_DIR), "Rainrisk", "data", "processed")
    if os.path.exists(rainrisk_processed):
        import shutil
        src_panel = os.path.join(PROCESSED_DIR, "master_panel.parquet")
        dst_panel = os.path.join(rainrisk_processed, "master_panel.parquet")
        shutil.copy2(src_panel, dst_panel)
        print(f"[OK] Mirrored master_panel.parquet to {dst_panel}", flush=True)

def run():
    talukas_df = pd.read_csv(GEO_PATH)
    total_talukas = len(talukas_df)
    num_batches = (total_talukas + BATCH_SIZE - 1) // BATCH_SIZE

    print("=" * 75, flush=True)
    print("   MAHARAINRISK: INGESTING FULL OCTOBER 2026 FOR ALL 194 TALUKAS", flush=True)
    print(f"   Target Window: {FULL_START} to {FULL_END} | 194 Talukas ({num_batches} Batches)", flush=True)
    print("=" * 75, flush=True)

    for b_idx in range(num_batches):
        start_i = b_idx * BATCH_SIZE
        end_i = min(start_i + BATCH_SIZE, total_talukas)
        b_slice = talukas_df.iloc[start_i:end_i]
        
        ok = process_batch(b_idx, b_slice)
        if not ok:
            print(f"[!] Processing stopped at batch {b_idx}.", flush=True)
            return False

    print("\n[OK] All 33 batches are complete through 2026-10-31!", flush=True)
    compile_all()
    return True

if __name__ == "__main__":
    run()
