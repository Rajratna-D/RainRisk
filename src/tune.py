"""
RainRisk: Time-series hyperparameter tuning.

Generates custom cross-validation index splits for scikit-learn GridSearchCV
from chronological expanding-window folds.
"""
import numpy as np
from sklearn.model_selection import GridSearchCV


def make_cv_splits(df, folds, feature_cols):
    df = df.reset_index(drop=True)
    df_keys = list(zip(df['YEAR'], df['SUBDIVISION']))
    splits = []
    for fold_idx, train_fold, test_fold in folds:
        # Matching on (YEAR, SUBDIVISION) pairs maps fold boundaries to target DataFrame row indices
        train_keys = set(zip(train_fold['YEAR'], train_fold['SUBDIVISION']))
        test_keys = set(zip(test_fold['YEAR'], test_fold['SUBDIVISION']))
        train_mask = np.array([k in train_keys for k in df_keys])
        test_mask = np.array([k in test_keys for k in df_keys])
        splits.append((np.where(train_mask)[0], np.where(test_mask)[0]))
    return splits


def tune_model(pipeline_builder, base_model, param_grid, df, folds, feature_cols,
                target_col="drought_category", scoring="balanced_accuracy"):
    """
    Runs GridSearchCV over expanding-window time splits using specified pipeline and scoring metric.
    """
    df = df.reset_index(drop=True)
    cv_splits = make_cv_splits(df, folds, feature_cols)

    X = df[feature_cols]
    y = df[target_col]

    pipe = pipeline_builder(base_model)
    gs = GridSearchCV(pipe, param_grid, cv=cv_splits, scoring=scoring, n_jobs=-1, refit=True)
    gs.fit(X, y)
    return gs
