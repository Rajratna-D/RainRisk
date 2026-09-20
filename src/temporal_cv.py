"""
RainRisk: time-aware cross-validation.

Standard k-fold CV shuffles rows randomly, which would leak future years
into training folds (rolling/lag features from a "test" fold row could
depend on a year sitting in a "train" fold). This module instead builds
EXPANDING-WINDOW folds: each fold's train set is always strictly earlier in
time than its test set. This is the time-series-safe analogue of k-fold CV,
letting every fold serve as an independent estimate of generalization
performance instead of relying on one single, possibly-unrepresentative
train/test split.

Only the TRAINING/VALIDATION period (years <= FINAL_TEST_START) is ever
divided into folds here. The final held-out test set is never touched by
this module: it must remain untouched until the very last evaluation
step, per the project's model-selection discipline (see docs).
"""
import numpy as np
import pandas as pd


def expanding_window_folds(df, year_col="YEAR", n_folds=4,
                             min_train_years=40, fold_test_years=15):
    """
    Builds n_folds expanding-window (train, test) DataFrame pairs from df,
    ordered chronologically. Each fold's test window is disjoint from the
    others where possible; train always precedes test within a fold.

    Example with min_train_years=40, fold_test_years=15, starting at the
    dataset's minimum year Y0:
        Fold 1: train [Y0, Y0+40)   test [Y0+40, Y0+55)
        Fold 2: train [Y0, Y0+55)   test [Y0+55, Y0+70)
        Fold 3: train [Y0, Y0+70)   test [Y0+70, Y0+85)
        ...

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
    Explicit check: for every fold, confirm max(train year) < min(test year).
    Returns a list of violation messages (empty list = all clear).
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
