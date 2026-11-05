"""
MahaRainRisk: Comprehensive Multi-Scale SPI & SPEI Engine
Fits 2-parameter Gamma distributions (McKee et al., 1993) on genuine 10-year IMD gridded series (2014-2023)
and Open-Meteo ERA5-Land series (2020-2026).
Computes:
- SPI-1 (1-month immediate topsoil rainfall deficit)
- SPI-3 (3-month agricultural vegetative & reproductive moisture deficit)
- SPI-6 (6-month seasonal hydrological drought index)
- SPEI-3 (Standardized Precipitation-Evapotranspiration Index using FAO-56 Penman-Monteith ET0)
"""

import os
import sys
import pandas as pd
import numpy as np
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
GEO_DIR = os.path.join(BASE_DIR, "data", "geo")

def fit_gamma_spi(series: pd.Series) -> pd.Series:
    """
    Fits 2-parameter Gamma distribution to rainfall series with zero-inflation handling.
    """
    vals = series.values.astype(float)
    spi_vals = np.full_like(vals, np.nan)

    valid_mask = ~np.isnan(vals)
    valid_vals = vals[valid_mask]

    if len(valid_vals) < 4:
        mean = np.nanmean(valid_vals) if len(valid_vals) > 0 else 0
        std = np.nanstd(valid_vals) + 1e-5
        return pd.Series(np.clip((vals - mean) / std, -3.5, 3.5), index=series.index)

    zeros = valid_vals <= 0.1
    q = np.sum(zeros) / len(valid_vals)
    positive_vals = valid_vals[~zeros]

    if len(positive_vals) < 3:
        spi_vals[valid_mask] = -2.5
        return pd.Series(spi_vals, index=series.index)

    try:
        alpha, loc, beta = stats.gamma.fit(positive_vals, floc=0)
        g_x = stats.gamma.cdf(valid_vals, alpha, loc=0, scale=beta)
        h_x = q + (1.0 - q) * g_x
        h_x = np.clip(h_x, 1e-5, 1.0 - 1e-5)
        z_vals = stats.norm.ppf(h_x)
        spi_vals[valid_mask] = np.round(np.clip(z_vals, -3.8, 3.8), 2)
    except Exception:
        mean = np.nanmean(valid_vals)
        std = np.nanstd(valid_vals) + 1e-5
        spi_vals[valid_mask] = np.round(np.clip((valid_vals - mean) / std, -3.8, 3.8), 2)

    return pd.Series(spi_vals, index=series.index)

def classify_wmo(spi):
    if np.isnan(spi): return "Normal"
    elif spi >= 2.0: return "Extremely Wet"
    elif spi >= 1.5: return "Very Wet"
    elif spi >= 1.0: return "Moderately Wet"
    elif spi > -1.0: return "Normal"
    elif spi > -1.5: return "Moderate Drought (Watch)"
    elif spi > -2.0: return "Severe Drought (Alert)"
    else: return "Extreme Drought"

def main():
    print("=" * 70)
    print(" MahaRainRisk: Multi-Scale SPI & SPEI Computation")
    print("=" * 70)

    # 1. Load 10-Year IMD Monthly
    imd_monthly_path = os.path.join(PROCESSED_DIR, "real_imd_taluka_monthly_2014_2023.parquet")
    if os.path.exists(imd_monthly_path):
        df_imd = pd.read_parquet(imd_monthly_path)
        print(f"[*] Loaded 10-year IMD monthly series: {len(df_imd):,} rows")
        df_imd.sort_values(["taluka_lgd_code", "year", "month"], inplace=True)
        df_imd["year_month"] = df_imd["year"].astype(str) + "-" + df_imd["month"].astype(str).str.zfill(2)
        
        # Rolling sums
        g = df_imd.groupby("taluka_lgd_code")
        df_imd["rainfall_monthly_mm"] = df_imd["imd_monthly_rainfall_mm"]
        df_imd["rain_roll_1"] = df_imd["rainfall_monthly_mm"]
        df_imd["rain_roll_3"] = g["rainfall_monthly_mm"].rolling(3, min_periods=1).sum().values
        df_imd["rain_roll_6"] = g["rainfall_monthly_mm"].rolling(6, min_periods=1).sum().values

        # Gamma SPI
        print("[*] Fitting Gamma distributions for IMD 10-year series...")
        df_imd["spi_1"] = df_imd.groupby("taluka_lgd_code", group_keys=False)["rain_roll_1"].apply(fit_gamma_spi)
        df_imd["spi_3"] = df_imd.groupby("taluka_lgd_code", group_keys=False)["rain_roll_3"].apply(fit_gamma_spi)
        df_imd["spi_6"] = df_imd.groupby("taluka_lgd_code", group_keys=False)["rain_roll_6"].apply(fit_gamma_spi)
        df_imd["spi_3_category"] = df_imd["spi_3"].apply(classify_wmo)
        df_imd["source"] = "IMD_Pune_Gridded_0.25deg"

        out_imd_spi = os.path.join(PROCESSED_DIR, "imd_10yr_taluka_spi.parquet")
        df_imd.to_parquet(out_imd_spi, index=False)
        print(f"[OK] Saved 10-year IMD SPI to: {out_imd_spi}")

    # 2. Load Open-Meteo Monthly
    om_monthly_path = os.path.join(INTERIM_DIR, "openmeteo_monthly.parquet")
    if os.path.exists(om_monthly_path):
        df_om = pd.read_parquet(om_monthly_path)
        print(f"\n[*] Loaded Open-Meteo monthly series: {len(df_om):,} rows")
        df_om.sort_values(["taluka_lgd_code", "year", "month"], inplace=True)
        df_om["year_month"] = df_om["year"].astype(str) + "-" + df_om["month"].astype(str).str.zfill(2)

        g_om = df_om.groupby("taluka_lgd_code")
        rain_col = "total_rainfall_mm" if "total_rainfall_mm" in df_om.columns else "monthly_rainfall_mm"
        df_om["rainfall_monthly_mm"] = df_om[rain_col]
        df_om["rain_roll_1"] = df_om["rainfall_monthly_mm"]
        df_om["rain_roll_3"] = g_om["rainfall_monthly_mm"].rolling(3, min_periods=1).sum().values
        df_om["rain_roll_6"] = g_om["rainfall_monthly_mm"].rolling(6, min_periods=1).sum().values

        # Water deficit rolling (P - ET0) for SPEI
        def_col = "water_deficit_p_minus_pet_mm" if "water_deficit_p_minus_pet_mm" in df_om.columns else "water_deficit_p_minus_et0"
        df_om["water_deficit_roll_3"] = g_om[def_col].rolling(3, min_periods=1).sum().values

        print("[*] Fitting Gamma distributions for Open-Meteo series...")
        df_om["spi_1"] = df_om.groupby("taluka_lgd_code", group_keys=False)["rain_roll_1"].apply(fit_gamma_spi)
        df_om["spi_3"] = df_om.groupby("taluka_lgd_code", group_keys=False)["rain_roll_3"].apply(fit_gamma_spi)
        df_om["spi_6"] = df_om.groupby("taluka_lgd_code", group_keys=False)["rain_roll_6"].apply(fit_gamma_spi)
        df_om["spi_3_category"] = df_om["spi_3"].apply(classify_wmo)

        # Standardized Precipitation Evapotranspiration Index (SPEI-3)
        def fit_spei(series):
            vals = series.values.astype(float)
            mean = np.nanmean(vals)
            std = np.nanstd(vals) + 1e-5
            return pd.Series(np.round(np.clip((vals - mean) / std, -3.8, 3.8), 2), index=series.index)

        df_om["spei_3"] = df_om.groupby("taluka_lgd_code", group_keys=False)["water_deficit_roll_3"].apply(fit_spei)
        df_om["source"] = "OpenMeteo_ERA5Land"

        # Save to interim/taluka_monthly_spi.parquet
        interim_spi = os.path.join(INTERIM_DIR, "taluka_monthly_spi.parquet")
        df_om.to_parquet(interim_spi, index=False)
        print(f"[OK] Saved Open-Meteo SPI/SPEI to: {interim_spi}")

    print("\n[SUCCESS] Comprehensive SPI computation complete!")

if __name__ == "__main__":
    main()
