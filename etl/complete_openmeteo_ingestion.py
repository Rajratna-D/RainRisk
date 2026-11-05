"""
MahaRainRisk: Complete Open-Meteo Ingestion for all 194 Talukas
Uses 2-taluka micro-chunking to ensure zero timeouts and maximum API speed.
Fetches 2020-01-01 to 2026-10-15 for any batches that currently stop at 2024.
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
SUB_CHUNK_SIZE = 2

def needs_update(batch_idx):
    raw_batch_file = os.path.join(RAW_DIR, f"resilient_batch_{batch_idx:03d}.json")
    if not os.path.exists(raw_batch_file):
        return True
    try:
        with open(raw_batch_file, "r", encoding="utf-8") as f:
            d = json.load(f)
        item = d[0] if isinstance(d, list) else d
        times = item.get("daily", {}).get("time", [])
        if len(times) >= 2480 and times[-1] >= "2026-10-15":
            return False
    except Exception:
        return True
    return True

def fetch_micro_chunk(lats, lons, attempt_max=5):
    params = {
        "latitude": lats if len(lats) > 1 else lats[0],
        "longitude": lons if len(lons) > 1 else lons[0],
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
    backoff = 5
    for attempt in range(1, attempt_max + 1):
        try:
            r = requests.get(OPEN_METEO_URL, params=params, timeout=45)
            if r.status_code == 200:
                data = r.json()
                if not isinstance(data, list):
                    data = [data]
                return data
            elif r.status_code == 429:
                print(f"    [!] HTTP 429 concurrency limit. Cooldown {backoff}s...", flush=True)
                time.sleep(backoff)
                backoff = min(backoff * 2, 45)
            else:
                print(f"    [!] HTTP {r.status_code}. Retrying in {backoff}s...", flush=True)
                time.sleep(backoff)
                backoff += 5
        except Exception as e:
            print(f"    [!] Network error: {e}. Retrying in {backoff}s...", flush=True)
            time.sleep(backoff)
            backoff += 5
    return None

def run():
    talukas_df = pd.read_csv(GEO_PATH)
    total_talukas = len(talukas_df)
    num_batches = (total_talukas + BATCH_SIZE - 1) // BATCH_SIZE

    print("=" * 75, flush=True)
    print("   MAHARAINRISK: COMPLETING OPEN-METEO INGESTION (2020-2026)", flush=True)
    print(f"   Total Talukas: {total_talukas} | Total Batches: {num_batches}", flush=True)
    print("=" * 75, flush=True)

    batches_to_fetch = [b for b in range(num_batches) if needs_update(b)]
    print(f"[*] Batches requiring full 2020-2026 fetch: {len(batches_to_fetch)} of {num_batches}", flush=True)

    for idx, batch_idx in enumerate(batches_to_fetch, 1):
        raw_batch_file = os.path.join(RAW_DIR, f"resilient_batch_{batch_idx:03d}.json")
        start_i = batch_idx * BATCH_SIZE
        end_i = min(start_i + BATCH_SIZE, total_talukas)
        batch_slice = talukas_df.iloc[start_i:end_i]

        names = batch_slice["taluka_name"].tolist()
        print(f"\n[{idx}/{len(batches_to_fetch)}] Processing Batch {batch_idx:02d} ({len(names)} talukas: {names[0]} .. {names[-1]})...", flush=True)

        batch_results = []
        batch_success = True

        # Fetch in micro-chunks of 2 talukas
        for sub_start in range(0, len(batch_slice), SUB_CHUNK_SIZE):
            sub_slice = batch_slice.iloc[sub_start : sub_start + SUB_CHUNK_SIZE]
            sub_lats = sub_slice["latitude"].tolist()
            sub_lons = sub_slice["longitude"].tolist()
            sub_names = sub_slice["taluka_name"].tolist()

            print(f"  -> Sub-chunk ({', '.join(sub_names)})...", end=" ", flush=True)
            res = fetch_micro_chunk(sub_lats, sub_lons)
            if res is not None and len(res) == len(sub_slice):
                batch_results.extend(res)
                print(f"[OK ({len(res[0]['daily']['time'])} days)]", flush=True)
            else:
                print("[FAILED]", flush=True)
                batch_success = False
                break
            
            # Polite pause between micro-chunks
            time.sleep(2.5)

        if batch_success and len(batch_results) == len(batch_slice):
            with open(raw_batch_file, "w", encoding="utf-8") as f:
                json.dump(batch_results, f)
            print(f"  [SUCCESS] Saved resilient_batch_{batch_idx:03d}.json with {len(batch_results)} talukas.", flush=True)
        else:
            print(f"  [ERROR] Could not complete batch {batch_idx}. Aborting to prevent incomplete files.", flush=True)
            return False

        # Courteous pause between batches
        time.sleep(3.0)

    print("\n[OK] All 33 batches successfully verified and stored on disk!", flush=True)
    
    # Compile all downloaded batches into master clean datasets
    sys.path.append(os.path.join(BASE_DIR, "etl"))
    from fetch_openmeteo_resilient import compile_all_batches
    compile_all_batches(talukas_df)
    return True

if __name__ == "__main__":
    run()
