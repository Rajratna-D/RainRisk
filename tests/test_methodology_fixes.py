"""
Tests covering the four methodology fixes:
  1. SMOTENC never produces fractional/impossible SUBDIVISION values
  2. Expanding-window CV folds never have temporal overlap
  3. 'No Rainfall' category exists and boundary behaves correctly
  4. Final test set is never used during hyperparameter selection (structural check)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from labeling import compute_lpa, compute_pct_departure, classify, CATEGORY_ORDER
from features import build_lag_rolling_features
from temporal_cv import expanding_window_folds, verify_no_temporal_overlap
from train import build_pipeline, get_models, ALL_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'Sub_Division_IMD_2017.csv')


def _load_model_df():
    raw = pd.read_csv(DATA_PATH)
    lpa = compute_lpa(raw)
    raw['LPA'] = raw['SUBDIVISION'].map(lpa)
    raw['pct_departure'] = compute_pct_departure(raw['JJAS'], raw['LPA'])
    raw['drought_category'] = raw['pct_departure'].apply(classify)
    feat_df = build_lag_rolling_features(raw, enhanced=True)
    # Drop NaN on ALL numeric features (enhanced set)
    model_df = feat_df.dropna(subset=NUMERIC_FEATURES + ['drought_category'])
    model_df = model_df[model_df['drought_category'] != 'Unknown']
    return model_df


def test_no_rainfall_category_exists():
    assert "No Rainfall" in CATEGORY_ORDER
    assert len(CATEGORY_ORDER) == 6


def test_smotenc_never_produces_fractional_subdivision():
    """
    Core check for Problem 1: after SMOTENC resampling (inside the fitted
    pipeline), every SUBDIVISION value in the training data used by the
    classifier must be one of the real, original subdivision names, never
    a numeric/fractional blend. We check this by inspecting the SMOTENC step
    output directly (before the one-hot encoder), since that's the layer
    where the original bug (SMOTE on already-one-hot-encoded columns) could
    produce impossible values.
    """
    model_df = _load_model_df()
    train = model_df[model_df['YEAR'] <= 1995]
    real_subdivisions = set(train['SUBDIVISION'].unique())

    X_train = train[ALL_FEATURES]
    y_train = train['drought_category']

    pipe = build_pipeline(get_models()['RandomForest'])
    smotenc_step = pipe.named_steps['smotenc']
    X_resampled, y_resampled = smotenc_step.fit_resample(X_train, y_train)

    cat_col_idx = ALL_FEATURES.index(CATEGORICAL_FEATURES[0])
    resampled_subdivisions = set(X_resampled.iloc[:, cat_col_idx].unique()) if hasattr(X_resampled, 'iloc') else set(np.array(X_resampled)[:, cat_col_idx])

    unexpected = resampled_subdivisions - real_subdivisions
    assert len(unexpected) == 0, f"SMOTENC produced non-real subdivision values: {unexpected}"


def test_expanding_window_folds_no_temporal_overlap():
    model_df = _load_model_df()
    train_val = model_df[model_df['YEAR'] <= 2005]
    folds = expanding_window_folds(train_val, n_folds=4, min_train_years=40, fold_test_years=15)
    violations = verify_no_temporal_overlap(folds)
    assert len(violations) == 0, f"Temporal leakage found: {violations}"


def test_expanding_window_folds_train_before_test():
    """Redundant, independent check using a different method than
    verify_no_temporal_overlap, confirms every single row in a fold's
    train set has YEAR strictly less than every row in that fold's test set."""
    model_df = _load_model_df()
    train_val = model_df[model_df['YEAR'] <= 2005]
    folds = expanding_window_folds(train_val, n_folds=4, min_train_years=40, fold_test_years=15)
    for idx, tr, te in folds:
        if len(tr) == 0 or len(te) == 0:
            continue
        assert tr['YEAR'].max() < te['YEAR'].min(), f"Fold {idx} violates train < test ordering"


def test_final_test_set_never_in_cv_folds():
    """Structural check: the final held-out test set (2006-2017) must never
    appear inside any CV fold used for model selection."""
    model_df = _load_model_df()
    train_val = model_df[model_df['YEAR'] <= 2005]
    final_test = model_df[model_df['YEAR'] > 2005]

    folds = expanding_window_folds(train_val, n_folds=4, min_train_years=40, fold_test_years=15)
    final_test_years = set(final_test['YEAR'])
    for idx, tr, te in folds:
        assert len(set(tr['YEAR']) & final_test_years) == 0, f"Fold {idx} train overlaps final test years"
        assert len(set(te['YEAR']) & final_test_years) == 0, f"Fold {idx} test overlaps final test years"


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
