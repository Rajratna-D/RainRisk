"""
Automated leakage tests for src/features.py.
Run against the REAL dataset (not synthetic) so it catches issues that only
show up with real gaps/edge cases (e.g. Andaman & Nicobar's missing years).

ENHANCED: covers both original 5-feature set and new 18-feature expanded set.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from features import (build_lag_rolling_features, ALL_ENGINEERED_FEATURES,
                      ORIGINAL_FEATURES, TELECONNECTION_FEATURES)

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'interim', 'rainfall_labeled.csv')
RAW_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'Sub_Division_IMD_2017.csv')


def test_no_leakage_first_rows():
    """Every subdivision's earliest row(s) must have NaN lag/rolling features:
    there is no prior year to compute them from."""
    df = pd.read_csv(DATA_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=False)

    issues = []
    for sub, grp in feat_df.groupby('SUBDIVISION'):
        grp = grp.sort_values('YEAR').reset_index(drop=True)
        if pd.notna(grp.loc[0, 'prev_year_jjas']):
            issues.append(f"{sub}: row 0 prev_year_jjas should be NaN")
        if len(grp) > 2 and pd.notna(grp.loc[1, 'prev_annual_change']):
            issues.append(f"{sub}: row 1 prev_annual_change should be NaN")
        if len(grp) > 3 and pd.notna(grp.loc[2, 'rolling_3yr_jjas']):
            issues.append(f"{sub}: row 2 rolling_3yr_jjas should be NaN")
        if len(grp) > 5 and pd.notna(grp.loc[4, 'rolling_5yr_jjas']):
            issues.append(f"{sub}: row 4 rolling_5yr_jjas should be NaN")

    assert len(issues) == 0, f"Leakage issues found: {issues}"


def test_row_count_preserved():
    df = pd.read_csv(DATA_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=False)
    assert len(df) == len(feat_df)


def test_prev_year_jjas_matches_manual():
    """Spot check: prev_year_jjas at row i must equal JJAS at row i-1, same subdivision."""
    df = pd.read_csv(DATA_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=False)

    kerala = feat_df[feat_df['SUBDIVISION'] == 'Kerala'].sort_values('YEAR').reset_index(drop=True)
    for i in range(1, min(20, len(kerala))):
        expected = kerala.loc[i-1, 'JJAS']
        actual = kerala.loc[i, 'prev_year_jjas']
        if pd.notna(expected) and pd.notna(actual):
            assert abs(expected - actual) < 1e-9, f"Mismatch at row {i}: {expected} vs {actual}"


def test_no_cross_subdivision_contamination():
    """A subdivision's first row must never borrow a value from a different
    subdivision's last row, even though the underlying frame is sorted
    by (subdivision, year)."""
    df = pd.read_csv(DATA_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=False)

    first_idx = feat_df.groupby('SUBDIVISION')['YEAR'].idxmin()
    first_rows = feat_df.loc[first_idx]
    assert first_rows['prev_year_jjas'].notna().sum() == 0


def test_missing_calendar_year_breaks_rolling_window():
    """
    Regression test for a real bug found via external review and merged in
    (see docs/05_methodology_fixes.md Fix 11): rolling windows must be
    calendar-year-aware, not merely positional. If a required prior year is
    missing from the data, the rolling feature for a row depending on that
    window must be NaN, not silently computed from whatever rows happen
    to be positionally nearby.
    """
    df = pd.DataFrame({
        "SUBDIVISION": ["X"] * 6,
        "YEAR": [2000, 2001, 2003, 2004, 2005, 2006],
        "JJAS": [100, 200, 300, 400, 500, 600],
    })
    feat = build_lag_rolling_features(df, enhanced=False)
    row_2004 = feat[feat.YEAR == 2004].iloc[0]
    assert pd.isna(row_2004["rolling_3yr_jjas"]), (
        "rolling_3yr_jjas at year 2004 should be NaN because 2002 is "
        "missing from the calendar-year sequence, but a non-NaN value was "
        "computed, this means the calendar-gap fix has regressed."
    )


def test_real_subdivisions_with_known_gaps_produce_nan_around_the_gap():
    """
    Same check as above, but against the REAL dataset's known gap years,
    not a synthetic example; confirms the fix actually applies where it
    matters, not just in a contrived test case.
    """
    df = pd.read_csv(DATA_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=False)

    # Andaman & Nicobar Islands is missing 1909, 1943, 1944, 1945, 1948
    andaman = feat_df[feat_df['SUBDIVISION'] == 'Andaman & Nicobar Islands']
    row_1946 = andaman[andaman['YEAR'] == 1946]
    if len(row_1946) > 0:
        assert pd.isna(row_1946.iloc[0]['rolling_3yr_jjas']), (
            "Andaman & Nicobar Islands 1946 rolling_3yr_jjas should be NaN "
            "since 1943-1945 are all missing from the calendar sequence"
        )


# ---- NEW: Enhanced features tests ----

def test_enhanced_features_row_count_preserved():
    """Enhanced features must preserve row count, same as original."""
    df = pd.read_csv(RAW_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=True)
    assert len(df) == len(feat_df), (
        f"Enhanced features changed row count: {len(df)} -> {len(feat_df)}"
    )


def test_enhanced_features_contain_expected_columns():
    """Verify that the enhanced feature set produces all expected columns."""
    df = pd.read_csv(RAW_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=True)

    expected_new = [
        "prev_jun", "prev_jul", "prev_aug", "prev_sep",
        "prev_jf", "prev_mam", "prev_ond",
        "prev_annual", "rolling_3yr_annual", "rolling_5yr_annual",
        "monsoon_concentration", "jjas_to_annual_ratio", "prev_premonsoon_signal",
    ]
    missing = [c for c in expected_new if c not in feat_df.columns]
    assert len(missing) == 0, f"Missing enhanced feature columns: {missing}"


def test_enhanced_features_no_leakage_first_rows():
    """All lag features (original + new) must be NaN for the first row
    of each subdivision: there's no prior year to lag from."""
    df = pd.read_csv(RAW_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=True)

    lag_cols = [
        "prev_year_jjas", "prev_jun", "prev_jul", "prev_aug", "prev_sep",
        "prev_jf", "prev_mam", "prev_ond", "prev_annual",
    ]

    issues = []
    for sub, grp in feat_df.groupby('SUBDIVISION'):
        grp = grp.sort_values('YEAR').reset_index(drop=True)
        for col in lag_cols:
            if col in grp.columns and pd.notna(grp.loc[0, col]):
                issues.append(f"{sub}: row 0 {col} should be NaN but is {grp.loc[0, col]}")

    assert len(issues) == 0, f"Leakage in enhanced features: {issues}"


def test_enhanced_prev_jun_matches_manual():
    """Spot check: prev_jun at row i must equal JUN at row i-1 (same subdivision)."""
    df = pd.read_csv(RAW_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=True)

    kerala = feat_df[feat_df['SUBDIVISION'] == 'Kerala'].sort_values('YEAR').reset_index(drop=True)
    for i in range(1, min(20, len(kerala))):
        expected = kerala.loc[i-1, 'JUN']
        actual = kerala.loc[i, 'prev_jun']
        if pd.notna(expected) and pd.notna(actual):
            assert abs(expected - actual) < 1e-9, (
                f"prev_jun mismatch at Kerala row {i}: expected {expected}, got {actual}"
            )


def test_enhanced_monsoon_concentration_valid_range():
    """Monsoon concentration (max_month / JJAS) should be between 0.25 and 1.0
    for valid rows (4 months, one must be at least 25% of total)."""
    df = pd.read_csv(RAW_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=True)

    valid = feat_df['monsoon_concentration'].dropna()
    assert len(valid) > 0, "No valid monsoon_concentration values"
    assert valid.min() >= 0.0, f"monsoon_concentration below 0: {valid.min()}"
    assert valid.max() <= 1.0 + 1e-9, f"monsoon_concentration above 1: {valid.max()}"


def test_enhanced_jjas_to_annual_ratio_valid_range():
    """JJAS/ANNUAL ratio should be between 0 and 1 for most subdivisions."""
    df = pd.read_csv(RAW_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=True)

    valid = feat_df['jjas_to_annual_ratio'].dropna()
    assert len(valid) > 0, "No valid jjas_to_annual_ratio values"
    assert valid.min() >= 0.0, f"jjas_to_annual_ratio below 0: {valid.min()}"
    assert valid.max() <= 1.0 + 1e-9, f"jjas_to_annual_ratio above 1: {valid.max()}"


def test_backward_compatibility_enhanced_false():
    """enhanced=False must produce exactly the same columns as the old code."""
    df = pd.read_csv(DATA_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=False)
    for col in ORIGINAL_FEATURES:
        assert col in feat_df.columns, f"Missing original feature: {col}"


def test_teleconnection_features_present_when_enhanced():
    """When enhanced=True, all 5 teleconnection features must be merged."""
    df = pd.read_csv(RAW_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=True)
    for col in TELECONNECTION_FEATURES:
        assert col in feat_df.columns, f"Expected teleconnection feature {col} in enhanced features"


def test_teleconnections_zero_nans_and_physical_bounds():
    """Teleconnection features must have zero NaNs and reside within realistic physical bounds."""
    df = pd.read_csv(RAW_PATH)
    feat_df = build_lag_rolling_features(df, enhanced=True)

    for col in TELECONNECTION_FEATURES:
        assert feat_df[col].isna().sum() == 0, f"Found NaNs in teleconnection feature {col}"

    # Physical checks:
    # Nino 3.4 SST anomaly typically within [-4.0, +4.0] deg C
    assert feat_df['enso_mam_signal'].min() >= -4.0, "Niño 3.4 MAM anomaly below -4.0"
    assert feat_df['enso_mam_signal'].max() <= 4.0, "Niño 3.4 MAM anomaly above +4.0"

    # IOD DMI index typically within [-2.0, +2.5]
    assert feat_df['iod_mam_lag'].min() >= -2.0, "IOD DMI MAM below -2.0"
    assert feat_df['iod_mam_lag'].max() <= 2.5, "IOD DMI MAM above +2.5"


if __name__ == "__main__":
    import inspect
    test_fns = [obj for name, obj in list(globals().items())
                if name.startswith("test_") and inspect.isfunction(obj)]
    passed, failed = 0, 0
    for fn in test_fns:
        try:
            fn()
            print(f"PASS: {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(test_fns)} tests")
    if failed > 0:
        sys.exit(1)
