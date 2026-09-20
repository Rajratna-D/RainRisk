"""
RainRisk: Feature engineering module.

Constructs strictly antecedent lag, rolling, and teleconnection features.
Subdivision time-series are reindexed to continuous calendar years before computing rolling windows
to prevent non-contiguous gaps from silently distorting multi-year averages.
"""

import os
import pandas as pd
import numpy as np


def _jjas_features_for_subdivision(group, year_col="YEAR", value_col="JJAS"):
    # Reindexing to full year range ensures rolling windows return NaN across historical gaps
    group = group.sort_values(year_col).copy()
    years = range(int(group[year_col].min()), int(group[year_col].max()) + 1)
    indexed = group.set_index(year_col).reindex(years)

    shifted = indexed[value_col].shift(1)
    indexed["prev_year_jjas"] = shifted
    indexed["prev_annual_change"] = shifted - indexed[value_col].shift(2)
    indexed["rolling_3yr_jjas"] = shifted.rolling(3, min_periods=3).mean()
    indexed["rolling_5yr_jjas"] = shifted.rolling(5, min_periods=5).mean()
    std5 = shifted.rolling(5, min_periods=5).std()
    indexed["cv_5yr_jjas"] = std5 / indexed["rolling_5yr_jjas"] * 100

    indexed = indexed.reset_index().rename(columns={"index": year_col})
    return indexed[[year_col, "prev_year_jjas", "prev_annual_change",
                     "rolling_3yr_jjas", "rolling_5yr_jjas", "cv_5yr_jjas"]]


MONSOON_MONTHS = ["JUN", "JUL", "AUG", "SEP"]
SEASONAL_COLS = ["JF", "MAM", "OND"]
EXTRA_COLS = ["ANNUAL"]

NEW_LAG_FEATURES = (
    [f"prev_{m.lower()}" for m in MONSOON_MONTHS] +
    [f"prev_{s.lower()}" for s in SEASONAL_COLS] +
    ["prev_annual"]
)

NEW_DERIVED_FEATURES = [
    "monsoon_concentration",
    "jjas_to_annual_ratio",
    "rolling_3yr_annual",
    "rolling_5yr_annual",
    "prev_premonsoon_signal",
]

ALL_NEW_FEATURES = NEW_LAG_FEATURES + NEW_DERIVED_FEATURES

TELECONNECTION_FEATURES = [
    "enso_djf_lag",
    "enso_mam_signal",
    "enso_tendency",
    "iod_mam_lag",
    "enso_iod_interaction",
]

ORIGINAL_FEATURES = [
    "prev_year_jjas", "prev_annual_change",
    "rolling_3yr_jjas", "rolling_5yr_jjas", "cv_5yr_jjas"
]

ALL_ENGINEERED_FEATURES = ORIGINAL_FEATURES + ALL_NEW_FEATURES + TELECONNECTION_FEATURES


def _enhanced_features_for_subdivision(group, year_col="YEAR"):
    group = group.sort_values(year_col).copy()
    years = range(int(group[year_col].min()), int(group[year_col].max()) + 1)
    indexed = group.set_index(year_col).reindex(years)

    jjas_shifted = indexed["JJAS"].shift(1)
    indexed["prev_year_jjas"] = jjas_shifted
    indexed["prev_annual_change"] = jjas_shifted - indexed["JJAS"].shift(2)
    indexed["rolling_3yr_jjas"] = jjas_shifted.rolling(3, min_periods=3).mean()
    indexed["rolling_5yr_jjas"] = jjas_shifted.rolling(5, min_periods=5).mean()
    std5 = jjas_shifted.rolling(5, min_periods=5).std()
    indexed["cv_5yr_jjas"] = std5 / indexed["rolling_5yr_jjas"] * 100

    for month in MONSOON_MONTHS:
        if month in indexed.columns:
            indexed[f"prev_{month.lower()}"] = indexed[month].shift(1)

    for season in SEASONAL_COLS:
        if season in indexed.columns:
            indexed[f"prev_{season.lower()}"] = indexed[season].shift(1)

    if "ANNUAL" in indexed.columns:
        annual_shifted = indexed["ANNUAL"].shift(1)
        indexed["prev_annual"] = annual_shifted
        indexed["rolling_3yr_annual"] = annual_shifted.rolling(3, min_periods=3).mean()
        indexed["rolling_5yr_annual"] = annual_shifted.rolling(5, min_periods=5).mean()

    if all(m in indexed.columns for m in MONSOON_MONTHS):
        prev_months = pd.DataFrame({
            m: indexed[m].shift(1) for m in MONSOON_MONTHS
        })
        prev_jjas = indexed["JJAS"].shift(1)
        max_month = prev_months.max(axis=1)
        indexed["monsoon_concentration"] = max_month / prev_jjas
        # Guard against division by zero in arid years with zero rainfall
        indexed["monsoon_concentration"] = indexed["monsoon_concentration"].replace(
            [np.inf, -np.inf], np.nan
        )

    if "ANNUAL" in indexed.columns:
        prev_jjas_val = indexed["JJAS"].shift(1)
        prev_annual_val = indexed["ANNUAL"].shift(1)
        indexed["jjas_to_annual_ratio"] = prev_jjas_val / prev_annual_val
        indexed["jjas_to_annual_ratio"] = indexed["jjas_to_annual_ratio"].replace(
            [np.inf, -np.inf], np.nan
        )

    if "MAM" in indexed.columns and "ANNUAL" in indexed.columns:
        prev_mam_val = indexed["MAM"].shift(1)
        prev_annual_val = indexed["ANNUAL"].shift(1)
        indexed["prev_premonsoon_signal"] = prev_mam_val / prev_annual_val
        indexed["prev_premonsoon_signal"] = indexed["prev_premonsoon_signal"].replace(
            [np.inf, -np.inf], np.nan
        )

    feature_cols = ORIGINAL_FEATURES + ALL_NEW_FEATURES
    available_cols = [c for c in feature_cols if c in indexed.columns]

    indexed = indexed.reset_index().rename(columns={"index": year_col})
    return indexed[[year_col] + available_cols]


def build_lag_rolling_features(df, subdivision_col="SUBDIVISION", year_col="YEAR",
                               value_col="JJAS", enhanced=True, include_teleconnections=None):
    """
    Builds lag and rolling features per subdivision using strictly prior calendar years.
    Returns df merged with computed feature columns.
    """
    if include_teleconnections is None:
        include_teleconnections = enhanced

    base = df.copy().sort_values([subdivision_col, year_col])
    parts = []
    for sub, group in base.groupby(subdivision_col, sort=False):
        if enhanced:
            f = _enhanced_features_for_subdivision(group, year_col)
        else:
            f = _jjas_features_for_subdivision(group, year_col, value_col)
        f[subdivision_col] = sub
        parts.append(f)
    feat = pd.concat(parts, ignore_index=True)
    result = base.merge(feat, on=[subdivision_col, year_col], how="left", validate="one_to_one")

    if include_teleconnections:
        tele_path = os.path.join(os.path.dirname(__file__), "..", "data", "interim", "teleconnections.csv")
        if os.path.exists(tele_path):
            tele_df = pd.read_csv(tele_path)
            cols_to_merge = [c for c in tele_df.columns if c == year_col or c not in result.columns]
            result = result.merge(tele_df[cols_to_merge], on=year_col, how="left")

    return result.sort_values([subdivision_col, year_col]).reset_index(drop=True)
