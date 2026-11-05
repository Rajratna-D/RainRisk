"""
MahaRainRisk: Auto-Resume Open-Meteo Ingestion
Monitors Open-Meteo API availability (polls every 3 minutes with a lightweight single-coordinate check).
The moment the hourly quota resets (17:00 GMT / 22:30 IST), it immediately executes
etl/fetch_missing_batches.py to download the remaining 5 batches and compile the 100% complete master datasets.
"""

import os
import sys
import time
import requests
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK_URL = "https://archive-api.open-meteo.com/v1/archive"

def test_api():
    params = {
        "latitude": 19.6667,
        "longitude": 77.3333,
        "start_date": "2024-01-01",
        "end_date": "2024-01-05",
        "daily": "precipitation_sum",
        "timezone": "Asia/Kolkata"
    }
    try:
        r = requests.get(CHECK_URL, params=params, timeout=15)
        return r.status_code == 200
    except Exception:
        return False

def main():
    print("=" * 70)
    print(" MahaRainRisk: Background Quota Watcher for Batches [9, 10, 11, 21, 28]")
    print("=" * 70)
    
    while True:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Checking if Open-Meteo hourly quota has reset...", flush=True)
        if test_api():
            print(f"[{current_time}] >>> QUOTA UNLOCKED! Launching batch fetcher now! <<<", flush=True)
            script_path = os.path.join(BASE_DIR, "etl", "fetch_missing_batches.py")
            subprocess.run([sys.executable, script_path], check=True)
            print("[*] Completed all missing batches and compiled 100% master datasets!", flush=True)
            break
        else:
            print("  Still waiting for hourly quota reset. Checking again in 120 seconds...", flush=True)
            time.sleep(120)

if __name__ == "__main__":
    main()
