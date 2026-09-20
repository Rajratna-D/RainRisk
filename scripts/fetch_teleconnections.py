"""
RainRisk v2: Planetary Teleconnections Ingestion Engine.

Fetches historical monthly time series for:
1. El Niño-Southern Oscillation (ENSO): Niño 3.4 SST Anomalies (1870-present)
   Source: NOAA Physical Sciences Laboratory (HadISST1.1 reconstructed analysis)
   URL: https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.data

2. Indian Ocean Dipole (IOD): Dipole Mode Index (DMI) (1870-present)
   Source: NOAA Physical Sciences Laboratory / JAMSTEC (HadISST long series)
   URL: https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data

Extracts 5 strict, leakage-free pre-monsoon features per year (1901-2017):
- enso_djf_lag: Antecedent winter (Dec t-1, Jan t, Feb t) Niño 3.4 anomaly
- enso_mam_signal: Spring pre-monsoon (Mar t, Apr t, May t) Niño 3.4 anomaly
- enso_tendency: Spring minus Winter warming/cooling velocity (MAM - DJF)
- iod_mam_lag: Spring pre-monsoon (Mar t, Apr t, May t) Dipole Mode Index
- enso_iod_interaction: Product interaction (Niño3.4_MAM * DMI_MAM)

Usage:
    python scripts/fetch_teleconnections.py
"""

import os
import ssl
import urllib.request
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_TELE_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "teleconnections")
INTERIM_DIR = os.path.join(PROJECT_ROOT, "data", "interim")
OUTPUT_CSV = os.path.join(INTERIM_DIR, "teleconnections.csv")

NINO34_URL = "https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.data"
DMI_URL = "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data"

MONTH_COLS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _get_ssl_context():
    ctx = ssl.create_default_context()
    # In case of strict corporate or Windows SSL cert store issues
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def download_file(url, target_path):
    """Downloads a raw URL to target_path with fallback and User-Agent."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    print(f"Downloading {url} -> {target_path} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RainRisk/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
    except urllib.error.URLError:
        # Fallback with relaxed SSL context if needed
        with urllib.request.urlopen(req, context=_get_ssl_context(), timeout=30) as response:
            content = response.read()
    
    with open(target_path, "wb") as f:
        f.write(content)
    print(f"  Saved {len(content):,} bytes to {target_path}")


def parse_psl_matrix(filepath):
    """
    Parses standard NOAA Physical Sciences Laboratory (PSL) format:
    Header line (start_year end_year), followed by Year + 12 monthly values.
    Filters sentinel missing value flags (< -90.0).
    """
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f.readlines()]
    
    rows = []
    for line in lines:
        parts = line.split()
        if len(parts) == 13:
            try:
                yr = int(parts[0])
                vals = [float(p) for p in parts[1:]]
                # Replace PSL missing flags like -99.99, -999.0 with NaN
                vals = [np.nan if v < -90.0 else v for v in vals]
                rows.append([yr] + vals)
            except ValueError:
                continue
                
    df = pd.DataFrame(rows, columns=["YEAR"] + MONTH_COLS)
    return df.sort_values("YEAR").reset_index(drop=True)


def build_teleconnection_features(nino_df, dmi_df, start_year=1901, end_year=2017):
    """
    Builds the 5 leakage-free pre-monsoon features across [start_year, end_year].
    Every feature is strictly computed using data available PRIOR to June 1st of that year.
    """
    records = []
    for y in range(start_year, end_year + 1):
        # 1. Winter antecedent Niño 3.4 (Dec t-1, Jan t, Feb t)
        prev_dec_series = nino_df.loc[nino_df["YEAR"] == y - 1, "DEC"]
        jan_series = nino_df.loc[nino_df["YEAR"] == y, "JAN"]
        feb_series = nino_df.loc[nino_df["YEAR"] == y, "FEB"]
        
        if len(prev_dec_series) == 0 or len(jan_series) == 0 or len(feb_series) == 0:
            raise ValueError(f"Missing Niño 3.4 data for year {y} or {y-1}")
            
        enso_djf = (prev_dec_series.values[0] + jan_series.values[0] + feb_series.values[0]) / 3.0
        
        # 2. Spring pre-monsoon Niño 3.4 (Mar t, Apr t, May t)
        mar_series = nino_df.loc[nino_df["YEAR"] == y, "MAR"]
        apr_series = nino_df.loc[nino_df["YEAR"] == y, "APR"]
        may_series = nino_df.loc[nino_df["YEAR"] == y, "MAY"]
        enso_mam = (mar_series.values[0] + apr_series.values[0] + may_series.values[0]) / 3.0
        
        # 3. Warming/cooling tendency velocity (Spring minus Winter)
        enso_tendency = enso_mam - enso_djf
        
        # 4. Spring pre-monsoon IOD DMI (Mar t, Apr t, May t)
        d_mar = dmi_df.loc[dmi_df["YEAR"] == y, "MAR"]
        d_apr = dmi_df.loc[dmi_df["YEAR"] == y, "APR"]
        d_may = dmi_df.loc[dmi_df["YEAR"] == y, "MAY"]
        
        if len(d_mar) == 0 or len(d_apr) == 0 or len(d_may) == 0:
            raise ValueError(f"Missing DMI data for year {y}")
            
        iod_mam = (d_mar.values[0] + d_apr.values[0] + d_may.values[0]) / 3.0
        
        # 5. Non-linear coupled interaction
        enso_iod_inter = enso_mam * iod_mam
        
        records.append({
            "YEAR": y,
            "enso_djf_lag": round(float(enso_djf), 4),
            "enso_mam_signal": round(float(enso_mam), 4),
            "enso_tendency": round(float(enso_tendency), 4),
            "iod_mam_lag": round(float(iod_mam), 4),
            "enso_iod_interaction": round(float(enso_iod_inter), 4),
        })
        
    res_df = pd.DataFrame(records)
    # Verification assertions
    assert len(res_df) == (end_year - start_year + 1), f"Expected {end_year - start_year + 1} rows, got {len(res_df)}"
    assert res_df.isna().sum().sum() == 0, f"Found NaNs in teleconnection features:\n{res_df.isna().sum()}"
    return res_df


def main():
    os.makedirs(RAW_TELE_DIR, exist_ok=True)
    os.makedirs(INTERIM_DIR, exist_ok=True)
    
    nino_raw_path = os.path.join(RAW_TELE_DIR, "nino34.long.anom.data")
    dmi_raw_path = os.path.join(RAW_TELE_DIR, "dmi.had.long.data")
    
    # 1. Download if not present
    if not os.path.exists(nino_raw_path):
        download_file(NINO34_URL, nino_raw_path)
    else:
        print(f"Using cached raw Niño 3.4 file at {nino_raw_path}")
        
    if not os.path.exists(dmi_raw_path):
        download_file(DMI_URL, dmi_raw_path)
    else:
        print(f"Using cached raw DMI file at {dmi_raw_path}")
        
    # 2. Parse raw NOAA matrices
    nino_df = parse_psl_matrix(nino_raw_path)
    dmi_df = parse_psl_matrix(dmi_raw_path)
    print(f"Parsed Niño 3.4: {nino_df['YEAR'].min()} to {nino_df['YEAR'].max()} ({len(nino_df)} years)")
    print(f"Parsed DMI:      {dmi_df['YEAR'].min()} to {dmi_df['YEAR'].max()} ({len(dmi_df)} years)")
    
    # 3. Build features across 1901-2017
    tele_df = build_teleconnection_features(nino_df, dmi_df, start_year=1901, end_year=2017)
    tele_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Successfully generated {len(tele_df)} rows of teleconnection features.")
    print(f"Saved to: {OUTPUT_CSV}")
    print("\nSample records (head 3):")
    print(tele_df.head(3).to_string(index=False))
    print("\nSample records (tail 3):")
    print(tele_df.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
