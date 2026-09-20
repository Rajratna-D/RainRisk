"""
RainRisk: Rainfall categorization based on IMD operational classification standards.

Categories:
    Large Excess     >= +60%
    Excess           >= +20% and <= +59%
    Normal           >= -19% and <= +19%
    Deficient        >= -59% and <= -20%
    Large Deficient  >= -99% and <= -60%
    No Rainfall      = -100% (zero rainfall against a non-zero normal)
"""

import numpy as np

CATEGORY_ORDER = ["No Rainfall", "Large Deficient", "Deficient", "Normal", "Excess", "Large Excess"]

# IMD standard 50-year operational climatological baseline
LPA_BASELINE_START = 1971
LPA_BASELINE_END = 2020

# IMD operational standards treat No Rain as total absence of rain (-100%), whereas -99% to -60% is Large Deficient.
NO_RAINFALL_THRESHOLD = -100.0


def classify(pct_departure):
    """
    Classify percentage departure from LPA into an IMD operational category.
    Returns 'Unknown' for missing/NaN inputs to prevent silent misclassification.
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
    Compute Long Period Average (LPA) per subdivision over the reference period.
    A fixed baseline provides a uniform retrospective benchmark across all historical years.
    """
    baseline = df[(df[year_col] >= start) & (df[year_col] <= end)]
    return baseline.groupby(subdivision_col)[value_col].mean()


def compute_pct_departure(actual, lpa):
    return (actual - lpa) / lpa * 100
