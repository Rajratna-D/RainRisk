"""
RainRisk: Time-aware cross-validation.

Constructs expanding-window cross-validation folds. Chronological forward chaining
prevents lookahead data leakage by ensuring training periods strictly precede validation windows.
"""
import numpy as np
import pandas as pd


def expanding_window_folds(df, year_col="YEAR", n_folds=4,
                             min_train_years=40, fold_test_years=15):
    """
    Builds n_folds expanding-window (train, test) DataFrame pairs ordered chronologically.
    Returns a list of (fold_index, train_df, test_df) tuples.
    """
    years = sorted(df[year_col].unique())
    y0 = years[0]

    folds = []
    for i in range(n_folds):
        train_end = y0 + min_train_years + i * fold_test_years
        test_end = train_end + fold_test_years
        train_df = df[df[year_col] < train_end]
        test_df = df[(df[year_col] >= train_end) & (df[year_col] < test_end)]
        if len(test_df) == 0:
            break
        folds.append((i + 1, train_df, test_df))
    return folds


def verify_no_temporal_overlap(folds, year_col="YEAR"):
    """
    Validates that max(train year) < min(test year) across all folds to verify temporal separation.
    """
    violations = []
    for fold_idx, train_df, test_df in folds:
        if len(train_df) == 0 or len(test_df) == 0:
            continue
        max_train_year = train_df[year_col].max()
        min_test_year = test_df[year_col].min()
        if max_train_year >= min_test_year:
            violations.append(
                f"Fold {fold_idx}: max train year {max_train_year} >= "
                f"min test year {min_test_year} : TEMPORAL LEAKAGE"
            )
    return violations
