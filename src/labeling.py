"""
RainRisk: Labeling module.

Implements IMD's operational rainfall classification scheme (district/state
spatial scale). Boundaries CONFIRMED against a primary IMD source document:
"District Rainfall Distribution" bulletin (India Meteorological Department,
Hydromet Division, New Delhi), which includes an explicit legend:

    Large Excess     >= +60%
    Excess           >= +20% and <= +59%
    Normal           >= -19% and <= +19%
    Deficient        >= -59% and <= -20%
    Large Deficient  >= -99% and <= -60%
    No Rain          = -100% exactly (not a range)

This resolves the previously PROVISIONAL "No Rainfall" boundary (an earlier
version of this module used <= -90% as an unverified placeholder). The
confirmed boundary is narrower than assumed: "No Rain" is the single exact
value -100% (actual rainfall = 0 against a nonzero normal), not a band.
Everything from -99% to -60% is "Large Deficient".

See docs/05_methodology_fixes.md Fix 12 for the full correction record.
"""

import numpy as np

CATEGORY_ORDER = ["No Rainfall", "Large Deficient", "Deficient", "Normal", "Excess", "Large Excess"]

LPA_BASELINE_START = 1971
LPA_BASELINE_END = 2020

# CONFIRMED against IMD's own "District Rainfall Distribution" bulletin legend.
NO_RAINFALL_THRESHOLD = -100.0


def classify(pct_departure):
    """
    Classify a single % departure from LPA into an IMD operational category.
    Boundaries confirmed against IMD's own published legend (see module
    docstring), not a placeholder.

    Bands (% departure from LPA):
        <= -100          -> No Rainfall     (exact value, not a range)
        -99 <= x <= -60  -> Large Deficient
        -59 <= x <= -20  -> Deficient
        -19 <= x <= +19  -> Normal
        +20 <= x <= +59  -> Excess
        >= +60           -> Large Excess

    Returns "Unknown" for NaN/None input (never silently misclassify).
    """
    if pct_departure is None or (isinstance(pct_departure, float) and np.isnan(pct_departure)):
        return "Unknown"

    if pct_departure <= NO_RAINFALL_THRESHOLD:
        return "No Rainfall"
    elif pct_departure <= -60:
        return "Large Deficient"
    elif pct_departure <= -20:
        return "Deficient"
    elif pct_departure <= 19:
        return "Normal"
    elif pct_departure <= 59:
        return "Excess"
    else:
        return "Large Excess"


def compute_lpa(df, subdivision_col="SUBDIVISION", year_col="YEAR",
                 value_col="JJAS", start=LPA_BASELINE_START, end=LPA_BASELINE_END):
    """
    Compute fixed LPA per subdivision using the 1971-2020 baseline period.
    Returns a Series indexed by subdivision.

    IMPORTANT FRAMING NOTE: this LPA is a single FIXED value computed once
    from a modern baseline period, then applied to EVERY row regardless of
    that row's own year, including rows from decades before the baseline
    period even starts (e.g. a 1920 row is classified using 1971-2020 data).

    This means the resulting drought_category label answers "how anomalous
    was this year relative to today's climatological normal", NOT "what
    could a forecaster classifying that year in real time have predicted."
    This is RETROSPECTIVE ANOMALY CLASSIFICATION, not real-time forecasting.
    See docs/02_labeling_spec.md Section "Task Framing" for full discussion,
    and src/features.py / notebooks/02_modeling.ipynb for the separate,
    genuinely leakage-free FEATURE construction used for the actual
    prediction task (features never use future years; only the fixed
    LPA baseline used to construct the LABEL does).
    """
    baseline = df[(df[year_col] >= start) & (df[year_col] <= end)]
    lpa = baseline.groupby(subdivision_col)[value_col].mean()
    return lpa


def compute_pct_departure(actual, lpa):
    """pct_departure = (actual - LPA) / LPA * 100"""
    return (actual - lpa) / lpa * 100
