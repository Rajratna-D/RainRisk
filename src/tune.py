"""
RainRisk: time-series hyperparameter tuning.

Builds a scikit-learn-compatible cross-validator from the expanding-window
folds in temporal_cv.py, so GridSearchCV performs genuine multi-fold
time-series-aware tuning (not a single train/val split wrapped in
PredefinedSplit, which was the earlier, weaker version of this fix).

CRITICAL: this must only ever be run on the train/validation period. The
final held-out test set must never be passed to tune_model().
"""
import numpy as np
from sklearn.model_selection import GridSearchCV


def make_cv_splits(df, folds, feature_cols):
    """
    Converts (fold_idx, train_df, test_df) tuples from expanding_window_folds
    into the (train_indices, test_indices) format GridSearchCV's `cv` param
    expects, indexed against df.reset_index(drop=True).

    df must be the SAME DataFrame (same row order) that X/y passed to
    GridSearchCV.fit() are derived from.
    """
    df = df.reset_index(drop=True)
    # Pre-compute (YEAR, SUBDIVISION) tuples once for vectorized matching
    df_keys = list(zip(df['YEAR'], df['SUBDIVISION']))
    splits = []
    for fold_idx, train_fold, test_fold in folds:
        # Use precise (YEAR, SUBDIVISION) pair matching to avoid accidentally
        # including rows that share a year but weren't part of that fold.
        train_keys = set(zip(train_fold['YEAR'], train_fold['SUBDIVISION']))
        test_keys = set(zip(test_fold['YEAR'], test_fold['SUBDIVISION']))
        train_mask = np.array([k in train_keys for k in df_keys])
        test_mask = np.array([k in test_keys for k in df_keys])
        splits.append((np.where(train_mask)[0], np.where(test_mask)[0]))
    return splits


def tune_model(pipeline_builder, base_model, param_grid, df, folds, feature_cols,
                target_col="drought_category", scoring="balanced_accuracy"):
    """
    Runs GridSearchCV using genuine multi-fold expanding-window CV.

    pipeline_builder: function(model) -> sklearn/imblearn Pipeline (e.g. train.build_pipeline)
    base_model: unfitted estimator instance
    param_grid: dict of {"clf__param": [values]}
    df: the train/validation DataFrame (must NOT include the final test set)
    folds: output of temporal_cv.expanding_window_folds(df, ...)

    Returns the fitted GridSearchCV object.
    """
    df = df.reset_index(drop=True)
    cv_splits = make_cv_splits(df, folds, feature_cols)

    X = df[feature_cols]
    y = df[target_col]

    pipe = pipeline_builder(base_model)
    gs = GridSearchCV(pipe, param_grid, cv=cv_splits, scoring=scoring, n_jobs=-1, refit=True)
    gs.fit(X, y)
    return gs
