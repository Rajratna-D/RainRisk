"""
RainRisk: Feature engineering module (ENHANCED).

CRITICAL: every feature must use ONLY data from years strictly before the
row's own year. See tests/test_features.py for an explicit leakage check
that verifies this on the real dataset before features are trusted.

CALENDAR-GAP FIX (merged from external review, see docs/05_methodology_fixes.md
Fix 11): the original implementation computed rolling windows using
POSITIONAL row offsets (pandas .rolling() over consecutive rows in the
group), not actual calendar-year continuity. For the 3 subdivisions with
real missing years (Andaman & Nicobar Islands, Arunachal Pradesh,
Lakshadweep (see docs/05_methodology_fixes.md Fix 11 for the concrete)
before/after demonstration), this silently bridged over gaps: e.g. a
rolling_3yr_jjas computed from years {2000, 2001, 2003} (with 2002 missing)
was treated as if those were 3 consecutive prior years, averaging real but
non-contiguous data without any indication a gap existed.

Fixed by reindexing each subdivision's data to a full contiguous calendar-
year range BEFORE computing shift/rolling. Missing years become explicit
NaN rows, so pandas' rolling window correctly returns NaN when the required
window of prior years is not fully calendar-contiguous, rather than
silently averaging across a gap.

ENHANCEMENT: expanded from 5 features (all derived from JJAS only) to 17+
features using the monthly/seasonal columns already present in the raw data.
This addresses the primary bottleneck of model performance: the original
feature set was too narrow to capture monsoon onset patterns, seasonal
interactions, and multi-variate trends.
"""

import os
import pandas as pd
import numpy as np


# ---- Original JJAS-only features (preserved for backward compatibility) ----

def _jjas_features_for_subdivision(group, year_col="YEAR", value_col="JJAS"):
    """
    Computes lag/rolling features for a single subdivision's data, reindexed
    to a full contiguous calendar-year range first so rolling windows are
    calendar-aware, not merely positional.
    """
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


# ---- Enhanced features using monthly/seasonal data ----

# Monthly columns for individual monsoon months
MONSOON_MONTHS = ["JUN", "JUL", "AUG", "SEP"]
# Seasonal columns already present in the raw data
SEASONAL_COLS = ["JF", "MAM", "OND"]
# Additional useful columns
EXTRA_COLS = ["ANNUAL"]

# All new lag features we'll create
NEW_LAG_FEATURES = (
    [f"prev_{m.lower()}" for m in MONSOON_MONTHS] +   # prev_jun, prev_jul, prev_aug, prev_sep
    [f"prev_{s.lower()}" for s in SEASONAL_COLS] +     # prev_jf, prev_mam, prev_ond
    ["prev_annual"]                                      # prev_annual
)

# New derived features (computed from current row's own prior-year data)
NEW_DERIVED_FEATURES = [
    "monsoon_concentration",   # max(JUN,JUL,AUG,SEP) / JJAS: how peaked the monsoon is
    "jjas_to_annual_ratio",    # JJAS / ANNUAL: monsoon dependency
    "rolling_3yr_annual",      # 3-year rolling mean of ANNUAL
    "rolling_5yr_annual",      # 5-year rolling mean of ANNUAL
    "prev_premonsoon_signal",  # prev MAM / prev ANNUAL: pre-monsoon as fraction of total
]

ALL_NEW_FEATURES = NEW_LAG_FEATURES + NEW_DERIVED_FEATURES

# Planetary teleconnection features (ENSO & IOD)
TELECONNECTION_FEATURES = [
    "enso_djf_lag",           # Preceding winter (Dec-Feb) Niño 3.4 anomaly
    "enso_mam_signal",        # Pre-monsoon spring (Mar-May) Niño 3.4 anomaly
    "enso_tendency",          # Spring minus Winter anomaly velocity
    "iod_mam_lag",            # Pre-monsoon spring (Mar-May) Dipole Mode Index
    "enso_iod_interaction",   # Niño 3.4 * IOD DMI interaction product
]

# Complete list of original features
ORIGINAL_FEATURES = [
    "prev_year_jjas", "prev_annual_change",
    "rolling_3yr_jjas", "rolling_5yr_jjas", "cv_5yr_jjas"
]

# Complete list of all features (original + new monthly/seasonal + teleconnections)
ALL_ENGINEERED_FEATURES = ORIGINAL_FEATURES + ALL_NEW_FEATURES + TELECONNECTION_FEATURES


def _enhanced_features_for_subdivision(group, year_col="YEAR"):
    """
    Computes ALL features (original JJAS + new monthly/seasonal) for a single
    subdivision, with calendar-gap-aware reindexing.
    """
    group = group.sort_values(year_col).copy()
    years = range(int(group[year_col].min()), int(group[year_col].max()) + 1)
    indexed = group.set_index(year_col).reindex(years)

    # --- Original JJAS features (preserved exactly) ---
    jjas_shifted = indexed["JJAS"].shift(1)
    indexed["prev_year_jjas"] = jjas_shifted
    indexed["prev_annual_change"] = jjas_shifted - indexed["JJAS"].shift(2)
    indexed["rolling_3yr_jjas"] = jjas_shifted.rolling(3, min_periods=3).mean()
    indexed["rolling_5yr_jjas"] = jjas_shifted.rolling(5, min_periods=5).mean()
    std5 = jjas_shifted.rolling(5, min_periods=5).std()
    indexed["cv_5yr_jjas"] = std5 / indexed["rolling_5yr_jjas"] * 100

    # --- New: individual monsoon month lags ---
    for month in MONSOON_MONTHS:
        if month in indexed.columns:
            indexed[f"prev_{month.lower()}"] = indexed[month].shift(1)

    # --- New: seasonal lags ---
    for season in SEASONAL_COLS:
        if season in indexed.columns:
            indexed[f"prev_{season.lower()}"] = indexed[season].shift(1)

    # --- New: annual lag ---
    if "ANNUAL" in indexed.columns:
        annual_shifted = indexed["ANNUAL"].shift(1)
        indexed["prev_annual"] = annual_shifted
        indexed["rolling_3yr_annual"] = annual_shifted.rolling(3, min_periods=3).mean()
        indexed["rolling_5yr_annual"] = annual_shifted.rolling(5, min_periods=5).mean()

    # --- New: monsoon concentration (from previous year) ---
    # How "peaked" was the monsoon? If one month dominates, concentration is high.
    if all(m in indexed.columns for m in MONSOON_MONTHS):
        prev_months = pd.DataFrame({
            m: indexed[m].shift(1) for m in MONSOON_MONTHS
        })
        prev_jjas = indexed["JJAS"].shift(1)
        max_month = prev_months.max(axis=1)
        indexed["monsoon_concentration"] = max_month / prev_jjas
        # Replace inf/nan from division by zero
        indexed["monsoon_concentration"] = indexed["monsoon_concentration"].replace(
            [np.inf, -np.inf], np.nan
        )

    # --- New: JJAS to annual ratio (from previous year) ---
    if "ANNUAL" in indexed.columns:
        prev_jjas_val = indexed["JJAS"].shift(1)
        prev_annual_val = indexed["ANNUAL"].shift(1)
        indexed["jjas_to_annual_ratio"] = prev_jjas_val / prev_annual_val
        indexed["jjas_to_annual_ratio"] = indexed["jjas_to_annual_ratio"].replace(
            [np.inf, -np.inf], np.nan
        )

    # --- New: pre-monsoon signal (MAM / ANNUAL from previous year) ---
    if "MAM" in indexed.columns and "ANNUAL" in indexed.columns:
        prev_mam_val = indexed["MAM"].shift(1)
        prev_annual_val = indexed["ANNUAL"].shift(1)
        indexed["prev_premonsoon_signal"] = prev_mam_val / prev_annual_val
        indexed["prev_premonsoon_signal"] = indexed["prev_premonsoon_signal"].replace(
            [np.inf, -np.inf], np.nan
        )

    # Collect all feature columns to return
    feature_cols = ORIGINAL_FEATURES + ALL_NEW_FEATURES
    available_cols = [c for c in feature_cols if c in indexed.columns]

    indexed = indexed.reset_index().rename(columns={"index": year_col})
    return indexed[[year_col] + available_cols]


def build_lag_rolling_features(df, subdivision_col="SUBDIVISION", year_col="YEAR",
                               value_col="JJAS", enhanced=True, include_teleconnections=None):
    """
    Builds lag and rolling features per subdivision, using only strictly
    prior CALENDAR years (not merely prior rows (see module docstring for)
    why this distinction matters and what bug it fixes).

    If enhanced=True (default), builds the full expanded feature set using
    monthly, seasonal, and planetary teleconnection columns. If enhanced=False,
    builds only the original 5 JJAS-derived features for backward compatibility.

    Returns a copy of df with new feature columns.

    Row count is preserved (a left-merge back onto the original df), even
    though internally each subdivision is temporarily reindexed to include
    placeholder rows for missing calendar years; those placeholder rows
    are used only to correctly compute neighboring rows' features, then
    discarded via the merge.
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
