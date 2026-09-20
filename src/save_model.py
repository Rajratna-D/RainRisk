"""
RainRisk: Model comparison and serialization script.

Benchmarks candidates across ablation tiers:
  1. Baseline (5 JJAS lag/rolling features)
  2. Enhanced rainfall (18 monthly, seasonal, and derived features)
  3. Planetary teleconnections (23 features: rainfall + ENSO & IOD)

Fits candidate estimators on historical train folds (<=2010), validates on held-out test
partition (2011-2017), and serializes the leading pipeline and evaluation metadata.
"""
import os
import sys
import json
import time

import pandas as pd
import numpy as np
import joblib

sys.path.insert(0, os.path.dirname(__file__))

from labeling import compute_lpa, compute_pct_departure, classify, CATEGORY_ORDER
from features import build_lag_rolling_features
from train import (build_pipeline, get_models,
                   ORIGINAL_ALL_FEATURES, ORIGINAL_NUMERIC_FEATURES,
                   ENHANCED_ALL_FEATURES, ENHANCED_NUMERIC_FEATURES,
                   TELECONNECTION_ALL_FEATURES, TELECONNECTION_NUMERIC_FEATURES,
                   ALL_FEATURES, NUMERIC_FEATURES, CATEGORICAL_FEATURES)
from evaluate import full_report

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
RAW_DATA = os.path.join(PROJECT_ROOT, 'data', 'raw', 'Sub_Division_IMD_2017.csv')
MODEL_DIR = os.path.join(PROJECT_ROOT, 'results', 'model')
PIPELINE_PATH = os.path.join(MODEL_DIR, 'best_pipeline.joblib')
METADATA_PATH = os.path.join(MODEL_DIR, 'best_pipeline_metadata.json')
COMPARISON_PATH = os.path.join(MODEL_DIR, 'enhanced_comparison.json')


def load_and_prepare_data(tier="teleconnections"):
    raw = pd.read_csv(RAW_DATA)
    lpa = compute_lpa(raw)
    raw['LPA'] = raw['SUBDIVISION'].map(lpa)
    raw['pct_departure'] = compute_pct_departure(raw['JJAS'], raw['LPA'])
    raw['drought_category'] = raw['pct_departure'].apply(classify)

    if tier == "old":
        feat_df = build_lag_rolling_features(raw, enhanced=False)
        numeric_cols = ORIGINAL_NUMERIC_FEATURES
        all_cols = ORIGINAL_ALL_FEATURES
    elif tier == "enhanced_rainfall":
        feat_df = build_lag_rolling_features(raw, enhanced=True, include_teleconnections=False)
        numeric_cols = ENHANCED_NUMERIC_FEATURES
        all_cols = ENHANCED_ALL_FEATURES
    else:
        feat_df = build_lag_rolling_features(raw, enhanced=True, include_teleconnections=True)
        numeric_cols = TELECONNECTION_NUMERIC_FEATURES
        all_cols = TELECONNECTION_ALL_FEATURES

    model_df = feat_df.dropna(subset=numeric_cols + ['drought_category'])
    model_df = model_df[model_df['drought_category'] != 'Unknown']

    return model_df, all_cols, numeric_cols


def train_and_evaluate(model_df, features, numeric_features, model_name, model_instance):
    train_val = model_df[model_df['YEAR'] <= 2010].copy()
    test = model_df[model_df['YEAR'] > 2010].copy()

    X_train = train_val[features]
    y_train = train_val['drought_category']
    X_test = test[features]
    y_test = test['drought_category']

    pipeline = build_pipeline(model_instance, numeric_features=numeric_features,
                               all_features=features)
    start = time.time()
    pipeline.fit(X_train, y_train)
    train_time = time.time() - start

    y_pred = pipeline.predict(X_test)
    metrics = full_report(y_test, y_pred, model_name=model_name)
    metrics['train_time_seconds'] = round(train_time, 2)

    return pipeline, metrics


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    comparison = {
        "old_features": [],
        "enhanced_features": [],
        "teleconnection_features": []
    }

    models_dict = get_models()

    print("Phase 1: Baseline (5 JJAS features)")
    model_df_old, old_all, old_num = load_and_prepare_data("old")
    for name, model in models_dict.items():
        print(f"  Training {name} (old)...", end=" ", flush=True)
        try:
            _, metrics = train_and_evaluate(model_df_old, old_all, old_num, f"{name}_old", model)
            comparison["old_features"].append(metrics)
            print(f"Acc: {metrics['accuracy']:.3f} | BalAcc: {metrics['balanced_accuracy']:.3f}")
        except Exception as e:
            print(f"FAILED: {e}")

    print("\nPhase 2: Enhanced (18 rainfall features)")
    model_df_enh, enh_all, enh_num = load_and_prepare_data("enhanced_rainfall")
    models_dict = get_models()
    for name, model in models_dict.items():
        print(f"  Training {name} (enhanced rainfall)...", end=" ", flush=True)
        try:
            _, metrics = train_and_evaluate(model_df_enh, enh_all, enh_num, f"{name}_enhanced", model)
            comparison["enhanced_features"].append(metrics)
            print(f"Acc: {metrics['accuracy']:.3f} | BalAcc: {metrics['balanced_accuracy']:.3f}")
        except Exception as e:
            print(f"FAILED: {e}")

    print("\nPhase 3: Teleconnections (23 features: rainfall + ENSO & IOD)")
    model_df_tele, tele_all, tele_num = load_and_prepare_data("teleconnections")

    best_pipeline = None
    best_metric = -1
    best_name = None
    best_metrics = None

    models_dict = get_models()
    for name, model in models_dict.items():
        print(f"  Training {name} (teleconnections)...", end=" ", flush=True)
        try:
            pipeline, metrics = train_and_evaluate(model_df_tele, tele_all, tele_num, f"{name}_tele", model)
            comparison["teleconnection_features"].append(metrics)
            print(f"Acc: {metrics['accuracy']:.3f} | BalAcc: {metrics['balanced_accuracy']:.3f} ({metrics['train_time_seconds']:.1f}s)")

            # Balanced accuracy serves as the selection criterion to avoid majority-class bias toward Normal years
            if metrics['balanced_accuracy'] > best_metric:
                best_metric = metrics['balanced_accuracy']
                best_pipeline = pipeline
                best_name = name
                best_metrics = metrics
        except Exception as e:
            print(f"FAILED: {e}")

    with open(COMPARISON_PATH, 'w') as f:
        json.dump(comparison, f, indent=2)

    if best_pipeline is not None:
        print(f"\nLeading Model: {best_name} (Balanced Accuracy: {best_metric:.4f})")
        joblib.dump(best_pipeline, PIPELINE_PATH)

        train_val = model_df_tele[model_df_tele['YEAR'] <= 2010]
        test = model_df_tele[model_df_tele['YEAR'] > 2010]

        metadata = {
            "model": best_name,
            "pipeline_steps": [name for name, _ in best_pipeline.steps],
            "features_used": tele_all,
            "numeric_features": tele_num,
            "feature_count": len(tele_num),
            "numeric_feature_count": len(tele_num),
            "total_feature_count": len(tele_all),
            "category_order": CATEGORY_ORDER,
            "train_years": "1901-2010",
            "test_years": "2011-2017",
            "train_val_rows": len(train_val),
            "test_rows": len(test),
            "test_metrics": best_metrics,
            "usage": (
                "import joblib; "
                "pipe = joblib.load('best_pipeline.joblib'); "
                "predictions = pipe.predict(X[features])"
            ),
        }
        with open(METADATA_PATH, 'w') as f:
            json.dump(metadata, f, indent=2)

    print("\nTraining and evaluation complete.")


if __name__ == "__main__":
    main()
