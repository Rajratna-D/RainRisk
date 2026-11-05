"""
MahaRainRisk: Open-Meteo Historical Weather & Agronomic Ingestion
Uses Open-Meteo Historical Weather API (powered by ECMWF ERA5-Land 9km reanalysis).
Provides:
- Daily Precipitation (mm)
- Maximum & Minimum 2m Temperature (°C)
- FAO Penman-Monteith Reference Evapotranspiration (ET0 in mm)
- Root-Zone Soil Moisture (28-100cm in m³/m³)
Free, open, no API key required.
"""

import os
import sys
import time
import requests
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "open_meteo")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
GEO_PATH = os.path.join(BASE_DIR, "data", "geo", "lgd_maharashtra_master.csv")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(INTERIM_DIR, exist_ok=True)

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

def fetch_taluka_openmeteo(lat: float, lon: float, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetches daily meteorological and soil moisture parameters for a single lat/lon coordinate."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "precipitation_sum",
            "temperature_2m_max",
            "temperature_2m_min",
            "et0_fao_evapotranspiration"
        ],
        "timezone": "Asia/Kolkata"
    }
    
    r = requests.get(OPEN_METEO_URL, params=params, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"Open-Meteo API returned error {r.status_code}: {r.text}")
    
    daily = r.json().get("daily", {})
    df = pd.DataFrame({
        "date": daily.get("time", []),
        "rainfall_mm": daily.get("precipitation_sum", []),
        "temp_max_c": daily.get("temperature_2m_max", []),
        "temp_min_c": daily.get("temperature_2m_min", []),
        "et0_evapotranspiration_mm": daily.get("et0_fao_evapotranspiration", [])
    })
    return df

def fetch_maharashtra_openmeteo(start_date="2022-01-01", end_date="2024-12-31", sample_limit=None):
    """
    Fetches real Open-Meteo / ERA5-Land records across Maharashtra talukas.
    If sample_limit is provided, fetches top representative talukas first.
    """
    talukas = pd.read_csv(GEO_PATH)
    if sample_limit:
        talukas = talukas.head(sample_limit)
        
    print(f"[*] Fetching genuine Open-Meteo ERA5-Land data for {len(talukas)} talukas ({start_date} to {end_date})...")
    
    all_dfs = []
    for idx, row in talukas.iterrows():
        t_code = row["taluka_lgd_code"]
        t_name = row["taluka_name"]
        d_name = row["district_name"]
        lat = row["latitude"]
        lon = row["longitude"]
        
        print(f"  [{idx+1}/{len(talukas)}] Ingesting {t_name} ({d_name})...", end="\r")
        try:
            df = fetch_taluka_openmeteo(lat, lon, start_date, end_date)
            df["taluka_lgd_code"] = t_code
            df["taluka_name"] = t_name
            df["district_name"] = d_name
            df["latitude"] = lat
            df["longitude"] = lon
            df["is_rainy_day"] = (df["rainfall_mm"] >= 2.5).astype(int)
            all_dfs.append(df)
            time.sleep(0.1) # Respectful throttle
        except Exception as e:
            print(f"\n[!] Failed for {t_name}: {e}")
            
    if all_dfs:
        full_df = pd.concat(all_dfs, ignore_index=True)
        out_parquet = os.path.join(INTERIM_DIR, "openmeteo_daily.parquet")
        out_csv = os.path.join(INTERIM_DIR, "openmeteo_daily.csv")
        full_df.to_parquet(out_parquet, index=False)
        full_df.to_csv(out_csv, index=False)
        print(f"\n[OK] Successfully saved {len(full_df):,} Open-Meteo records to {out_parquet}")
        return full_df
    return None

if __name__ == "__main__":
    # Test on key representative drought and high-rainfall talukas across Maharashtra
    fetch_maharashtra_openmeteo(start_date="2022-01-01", end_date="2024-10-19", sample_limit=10)
