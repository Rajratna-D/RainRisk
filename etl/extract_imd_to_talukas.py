"""
MahaRainRisk: Real IMD Gridded Rainfall Extraction (10-Year Climatological Series)
Extracts genuine daily rainfall from downloaded IMD .grd binary files (2014-2023)
for all 194 Maharashtra talukas across 36 districts using spatial nearest-neighbor coordinate matching.
Zero synthetic values. 100% real IMD measurements.
"""

import os
import pandas as pd
import numpy as np
import xarray as xr
import imdlib as imd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_PATH = os.path.join(BASE_DIR, "data", "geo", "lgd_maharashtra_master.csv")
IMD_DIR = os.path.join(BASE_DIR, "data", "raw", "imd_rainfall")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def extract_real_imd_to_talukas(start_year=2014, end_year=2023):
    print("=" * 70)
    print(f"[*] Extracting genuine IMD binary grid files for {start_year}-{end_year}...")
    print("=" * 70)
    data = imd.open_data('rain', start_year, end_year, 'yearwise', IMD_DIR)
    ds = data.get_xarray()
    
    # Load taluka centroids
    talukas = pd.read_csv(GEO_PATH)
    print(f"[*] Mapping {len(talukas)} Maharashtra talukas to IMD 0.25° grid...")

    all_records = []
    
    # Pre-extract lat and lon coordinates
    grid_lats = ds.lat.values
    grid_lons = ds.lon.values
    time_series = ds.time.values
    time_strings = pd.to_datetime(time_series).strftime("%Y-%m-%d")

    for _, row in talukas.iterrows():
        t_code = row["taluka_lgd_code"]
        t_name = row["taluka_name"]
        t_mr = row.get("taluka_name_mr", "")
        d_code = row.get("district_lgd_code", "")
        d_name = row["district_name"]
        zone = row.get("agro_climatic_zone", "")
        lat = row["latitude"]
        lon = row["longitude"]

        # Find nearest IMD grid cell index
        nearest_lat_idx = np.abs(grid_lats - lat).argmin()
        nearest_lon_idx = np.abs(grid_lons - lon).argmin()

        # Extract daily time series at this grid cell
        rain_vals = ds.rain.values[:, nearest_lat_idx, nearest_lon_idx]
        
        # Replace negative missing flags (-999.0) with NaN
        rain_vals = np.where(rain_vals < 0, np.nan, rain_vals)

        for dt_str, rain_val in zip(time_strings, rain_vals):
            all_records.append({
                "taluka_lgd_code": t_code,
                "taluka_name": t_name,
                "taluka_name_mr": t_mr,
                "district_lgd_code": d_code,
                "district_name": d_name,
                "agro_climatic_zone": zone,
                "date": dt_str,
                "real_imd_rainfall_mm": round(float(rain_val), 2) if not np.isnan(rain_val) else None,
                "data_provenance": "IMD Pune 0.25 deg daily gridded binary archive"
            })

    df_real = pd.DataFrame(all_records)
    
    # Save outputs for full 10-year period (2014-2023)
    out_parquet_full = os.path.join(PROCESSED_DIR, "real_imd_taluka_rainfall_2014_2023.parquet")
    df_real.to_parquet(out_parquet_full, index=False)
    
    # Also save 2018-2023 and 2022-2023 slices for backwards compatibility
    df_2018_2023 = df_real[df_real["date"] >= "2018-01-01"]
    out_parquet_18_23 = os.path.join(PROCESSED_DIR, "real_imd_taluka_rainfall_2018_2023.parquet")
    df_2018_2023.to_parquet(out_parquet_18_23, index=False)

    df_2022_2023 = df_real[df_real["date"] >= "2022-01-01"]
    out_parquet_22_23 = os.path.join(PROCESSED_DIR, "real_imd_taluka_rainfall_2022_2023.parquet")
    df_2022_2023.to_parquet(out_parquet_22_23, index=False)
    
    print(f"[SUCCESS] Extracted {len(df_real):,} genuine IMD daily rainfall records (2014-2023).")
    print(f"[OK] Saved 10-year master dataset: {out_parquet_full}")

    # Monthly aggregation
    df_real["date"] = pd.to_datetime(df_real["date"])
    df_real["year"] = df_real["date"].dt.year
    df_real["month"] = df_real["date"].dt.month
    
    monthly_imd = df_real.groupby(
        ["taluka_lgd_code", "taluka_name", "taluka_name_mr", "district_name", "agro_climatic_zone", "year", "month"],
        as_index=False
    ).agg({"real_imd_rainfall_mm": "sum"})
    monthly_imd.rename(columns={"real_imd_rainfall_mm": "imd_monthly_rainfall_mm"}, inplace=True)
    
    monthly_out = os.path.join(PROCESSED_DIR, "real_imd_taluka_monthly_2014_2023.parquet")
    monthly_imd.to_parquet(monthly_out, index=False)
    print(f"[OK] Saved IMD 10-year monthly dataset ({len(monthly_imd):,} rows): {monthly_out}")

if __name__ == "__main__":
    extract_real_imd_to_talukas(2014, 2023)
