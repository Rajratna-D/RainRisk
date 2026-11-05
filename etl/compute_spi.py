"""
MahaRainRisk: Standardized Precipitation Index (SPI) Engine
Implements McKee et al. (1993) algorithm to compute SPI-1, SPI-3, and SPI-6
across Maharashtra talukas using 2-parameter Gamma distribution fit.
Outputs:
- data/interim/taluka_monthly_spi.parquet
- data/interim/taluka_monthly_spi.csv
"""

import os
import pandas as pd
import numpy as np
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")

def fit_gamma_spi(series: pd.Series) -> pd.Series:
    """
    Fits 2-parameter Gamma distribution to monthly precipitation series
    and transforms to standard normal variate (SPI).
    """
    vals = series.values.astype(float)
    spi_vals = np.full_like(vals, np.nan)

    valid_mask = ~np.isnan(vals)
    valid_vals = vals[valid_mask]

    if len(valid_vals) < 5:
        return pd.Series(spi_vals, index=series.index)

    # Separate zeros
    n = len(valid_vals)
    zeros = valid_vals == 0
    m = np.sum(zeros)
    q = m / n # probability of zero

    positive_vals = valid_vals[~zeros]

    if len(positive_vals) < 3:
        # Near zero rainfall throughout
        spi_vals[valid_mask] = -2.5
        return pd.Series(spi_vals, index=series.index)

    try:
        # Fit Gamma distribution (shape=alpha, scale=beta)
        alpha, loc, beta = stats.gamma.fit(positive_vals, floc=0)
        
        # Cumulative probability G(x)
        g_x = stats.gamma.cdf(valid_vals, alpha, loc=0, scale=beta)
        
        # Mixture cumulative probability H(x) = q + (1 - q) * G(x)
        h_x = q + (1.0 - q) * g_x
        
        # Bound probabilities to avoid +/- inf
        h_x = np.clip(h_x, 1e-6, 1.0 - 1e-6)
        
        # Standard normal inverse transformation Z
        z_vals = stats.norm.ppf(h_x)
        
        # Clip to realistic SPI bounds [-4.0, +4.0]
        z_vals = np.clip(z_vals, -4.0, 4.0)
        
        spi_vals[valid_mask] = np.round(z_vals, 2)
    except Exception:
        # Fallback to standard z-score if Gamma fitting fails
        mean = np.nanmean(valid_vals)
        std = np.nanstd(valid_vals) + 1e-5
        z_vals = (valid_vals - mean) / std
        spi_vals[valid_mask] = np.round(np.clip(z_vals, -4.0, 4.0), 2)

    return pd.Series(spi_vals, index=series.index)

def calculate_taluka_spi():
    daily_path = os.path.join(INTERIM_DIR, "imd_daily.parquet")
    if not os.path.exists(daily_path):
        raise FileNotFoundError(f"IMD daily dataset not found at {daily_path}. Run fetch_imd.py first.")

    print(f"[*] Loading daily IMD data from {daily_path}...")
    df_daily = pd.read_parquet(daily_path)

    # Aggregate to monthly rainfall and temperature
    df_daily["year_month"] = df_daily["year"].astype(str) + "-" + df_daily["month"].astype(str).str.zfill(2)
    
    monthly = df_daily.groupby(["taluka_lgd_code", "year", "month", "year_month"]).agg(
        rainfall_monthly_mm=("rainfall_mm", "sum"),
        rainy_days=("is_rainy_day", "sum"),
        temp_max_mean=("temp_max_c", "mean"),
        temp_min_mean=("temp_min_c", "mean"),
        max_consecutive_dry_days=("dry_spell_days", "max")
    ).reset_index()

    monthly = monthly.sort_values(["taluka_lgd_code", "year", "month"]).reset_index(drop=True)

    print("[*] Computing rolling accumulation windows (1-month, 3-month, 6-month)...")
    # Rolling sums per taluka (index-aligned transformation)
    grouped = monthly.groupby("taluka_lgd_code")
    monthly["rain_roll_1"] = monthly["rainfall_monthly_mm"]
    monthly["rain_roll_3"] = grouped["rainfall_monthly_mm"].transform(lambda s: s.rolling(window=3, min_periods=1).sum())
    monthly["rain_roll_6"] = grouped["rainfall_monthly_mm"].transform(lambda s: s.rolling(window=6, min_periods=1).sum())

    print("[*] Fitting Gamma distributions and calculating SPI-1, SPI-3, SPI-6...")
    # Compute SPI for each taluka and each month of the year separately (climatological standard)
    def compute_grouped_spi(group, roll_col):
        # Fit by month to account for monsoonal seasonality
        return group.groupby("month")[roll_col].transform(fit_gamma_spi)

    monthly["spi_1"] = monthly.groupby("taluka_lgd_code", group_keys=False).apply(
        lambda g: compute_grouped_spi(g, "rain_roll_1")
    )
    monthly["spi_3"] = monthly.groupby("taluka_lgd_code", group_keys=False).apply(
        lambda g: compute_grouped_spi(g, "rain_roll_3")
    )
    monthly["spi_6"] = monthly.groupby("taluka_lgd_code", group_keys=False).apply(
        lambda g: compute_grouped_spi(g, "rain_roll_6")
    )

    # Classify drought severity based on SPI-3
    def classify_spi(val):
        if np.isnan(val):
            return "Unknown"
        elif val >= 2.0:
            return "Extremely Wet"
        elif val >= 1.5:
            return "Very Wet"
        elif val >= 1.0:
            return "Moderately Wet"
        elif val > -1.0:
            return "Normal"
        elif val > -1.5:
            return "Moderate Drought (Watch)"
        elif val > -2.0:
            return "Severe Drought (Alert)"
        else:
            return "Extreme Drought"

    monthly["spi_3_category"] = monthly["spi_3"].apply(classify_spi)

    # Save results
    parquet_out = os.path.join(INTERIM_DIR, "taluka_monthly_spi.parquet")
    csv_out = os.path.join(INTERIM_DIR, "taluka_monthly_spi.csv")
    monthly.to_parquet(parquet_out, index=False)
    monthly.to_csv(csv_out, index=False)
    print(f"[OK] Saved taluka monthly SPI dataset: {parquet_out} ({len(monthly)} records)")

if __name__ == "__main__":
    calculate_taluka_spi()
