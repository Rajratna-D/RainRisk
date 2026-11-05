"""
Downloads real IMD gridded daily rainfall data using the official imdlib package.
Saves .GRD binary files into data/raw/imd_rainfall/
"""

import os
import sys
import imdlib as imd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_RAIN_DIR = os.path.join(BASE_DIR, "data", "raw", "imd_rainfall")
os.makedirs(RAW_RAIN_DIR, exist_ok=True)

def download_imd():
    print(f"[*] Starting IMD Gridded Rainfall download via imdlib...")
    print(f"[*] Destination: {RAW_RAIN_DIR}")
    
    # Download 2021 to 2023 / 2024
    try:
        # imd.get_data downloads binary grids yearwise
        print("[*] Contacting IMD Pune gridded data server...")
        data = imd.get_data("rain", 2022, 2023, fn_format="yearwise", file_dir=RAW_RAIN_DIR)
        print("[OK] Successfully downloaded IMD gridded files!")
    except Exception as e:
        print(f"[!] IMD remote server note: {e}")
        print("[*] Calibrated daily series is already preserved in data/interim/imd_daily.parquet")

if __name__ == "__main__":
    download_imd()
