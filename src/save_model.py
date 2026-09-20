"""
RainRisk: Train all models with teleconnection-enhanced features, compare, and save best.

Loads raw data, engineers features across three rigorous ablation tiers:
  Tier 1: Original baseline (5 JJAS-only features)
  Tier 2: Enhanced rainfall (18 features: monthly lags, seasonal, derived ratios)
  Tier 3: Planetary teleconnections (23 features: rainfall + ENSO & IOD)

Trains candidate classifiers (LogisticRegression, RandomForest, SVM,
GradientBoosting, HistGradientBoosting), evaluates on held-out test set (2011-2017),
and serializes:
  - results/model/best_pipeline.joblib: the fitted best pipeline
  - results/model/best_pipeline_metadata.json: features, categories, metrics
  - results/model/enhanced_comparison.json: three-tier ablation comparison

Usage:
    python src/save_model.py
"""
import os
import sys
import json
import time

import pandas as pd
import numpy as np
import joblib

# Add src/ to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from labeling import compute_lpa, compute_pct_departure, classify, CATEGORY_ORDER
from features import build_lag_rolling_features
from train import (build_pipeline, get_models,
                   ORIGINAL_ALL_FEATURES, ORIGINAL_NUMERIC_FEATURES,
                   ENHANCED_ALL_FEATURES, ENHANCED_NUMERIC_FEATURES,
                   TELECONNECTION_ALL_FEATURES, TELECONNECTION_NUMERIC_FEATURES,
                   ALL_FEATURES, NUMERIC_FEATURES, CATEGORICAL_FEATURES)
from evaluate import full_report

# --- Paths ---
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
RAW_DATA = os.path.join(PROJECT_ROOT, 'data', 'raw', 'Sub_Division_IMD_2017.csv')
MODEL_DIR = os.path.join(PROJECT_ROOT, 'results', 'model')
PIPELINE_PATH = os.path.join(MODEL_DIR, 'best_pipeline.joblib')
METADATA_PATH = os.path.join(MODEL_DIR, 'best_pipeline_metadata.json')
COMPARISON_PATH = os.path.join(MODEL_DIR, 'enhanced_comparison.json')


def load_and_prepare_data(tier="teleconnections"):
    """
    Full pipeline: raw CSV -> labeled -> feature-engineered -> model-ready.
    tier:
      - 'old': 5 JJAS-only features
      - 'enhanced_rainfall': 18 monthly/seasonal/derived features
      - 'teleconnections': 23 features (18 rainfall + 5 planetary teleconnections)
    """
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
    else:  # 'teleconnections'
        feat_df = build_lag_rolling_features(raw, enhanced=True, include_teleconnections=True)
        numeric_cols = TELECONNECTION_NUMERIC_FEATURES
        all_cols = TELECONNECTION_ALL_FEATURES

    model_df = feat_df.dropna(subset=numeric_cols + ['drought_category'])
    model_df = model_df[model_df['drought_category'] != 'Unknown']

    return model_df, all_cols, numeric_cols


def train_and_evaluate(model_df, features, numeric_features, model_name, model_instance):
    """Train a single model on train partition (<=2010) and evaluate on test partition (>2010)."""
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

    # Models to benchmark across tiers
    # We evaluate all 5 models for the active tier
    models_dict = get_models()

    # ---- Phase A: Original features (5 JJAS-only) ----
    print("=" * 65)
    print("PHASE A: Baseline (5 JJAS-only features)")
    print("=" * 65)
    model_df_old, old_all, old_num = load_and_prepare_data("old")
    print(f"  Rows: {len(model_df_old)} | Features: {len(old_num)}")

    for name, model in models_dict.items():
        # Quick run for baseline
        print(f"  Training {name} (old)...", end=" ", flush=True)
        try:
            _, metrics = train_and_evaluate(model_df_old, old_all, old_num, f"{name}_old", model)
            comparison["old_features"].append(metrics)
            print(f"Acc: {metrics['accuracy']:.3f} | BalAcc: {metrics['balanced_accuracy']:.3f} | Off-1: {metrics['off_by_one_accuracy']:.3f}")
        except Exception as e:
            print(f"FAILED: {e}")

    # ---- Phase B: Enhanced features (18 rainfall-only) ----
    print("\n" + "=" * 65)
    print("PHASE B: Enhanced (18 rainfall features)")
    print("=" * 65)
    model_df_enh, enh_all, enh_num = load_and_prepare_data("enhanced_rainfall")
    print(f"  Rows: {len(model_df_enh)} | Features: {len(enh_num)}")

    models_dict = get_models()
    for name, model in models_dict.items():
        print(f"  Training {name} (enhanced rainfall)...", end=" ", flush=True)
        try:
            _, metrics = train_and_evaluate(model_df_enh, enh_all, enh_num, f"{name}_enhanced", model)
            comparison["enhanced_features"].append(metrics)
            print(f"Acc: {metrics['accuracy']:.3f} | BalAcc: {metrics['balanced_accuracy']:.3f} | Off-1: {metrics['off_by_one_accuracy']:.3f}")
        except Exception as e:
            print(f"FAILED: {e}")

    # ---- Phase C: Planetary Teleconnections (23 features: rainfall + ENSO & IOD) ----
    print("\n" + "=" * 65)
    print("PHASE C: Planetary Teleconnections (23 features: rainfall + ENSO & IOD)")
    print("=" * 65)
    model_df_tele, tele_all, tele_num = load_and_prepare_data("teleconnections")
    print(f"  Rows: {len(model_df_tele)} | Features: {len(tele_num)}")

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
            print(f"Acc: {metrics['accuracy']:.3f} | BalAcc: {metrics['balanced_accuracy']:.3f} | Off-1: {metrics['off_by_one_accuracy']:.3f} ({metrics['train_time_seconds']:.1f}s)")

            # Select best based on balanced accuracy
            if metrics['balanced_accuracy'] > best_metric:
                best_metric = metrics['balanced_accuracy']
                best_pipeline = pipeline
                best_name = name
                best_metrics = metrics
        except Exception as e:
            print(f"FAILED: {e}")

    # ---- Save comparison results ----
    with open(COMPARISON_PATH, 'w') as f:
        json.dump(comparison, f, indent=2)
    print(f"\n  Comparison saved to: {COMPARISON_PATH}")

    # ---- Save best pipeline ----
    if best_pipeline is not None:
        print(f"\n  >>> BEST MODEL: {best_name} (Balanced Accuracy: {best_metric:.4f}, Exact Accuracy: {best_metrics['accuracy']:.4f}, Off-by-1: {best_metrics['off_by_one_accuracy']:.4f}) <<<")

        joblib.dump(best_pipeline, PIPELINE_PATH)
        print(f"  Pipeline saved to: {PIPELINE_PATH}")

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
        print(f"  Metadata saved to: {METADATA_PATH}")

    # ---- Print Summary Progression Table ----
    print("\n" + "=" * 80)
    print(f"{'Model':<22} {'Metric':<14} {'Old (5f)':>10} {'Enhanced (18f)':>15} {'Teleconn (23f)':>15} {'Total Gain':>10}")
    print("=" * 80)

    for old_m in comparison["old_features"]:
        name_base = old_m["model"].replace("_old", "")
        enh_m = next((m for m in comparison["enhanced_features"] if m["model"].replace("_enhanced", "") == name_base), None)
        tele_m = next((m for m in comparison["teleconnection_features"] if m["model"].replace("_tele", "") == name_base), None)

        if not enh_m or not tele_m:
            continue

        for m_key, m_label in [("accuracy", "Exact Acc"), ("balanced_accuracy", "Bal Acc"), ("off_by_one_accuracy", "Off-by-1"), ("mean_ordinal_distance", "Mean Dist")]:
            v_old = old_m[m_key]
            v_enh = enh_m[m_key]
            v_tele = tele_m[m_key]
            diff = v_tele - v_old

            if m_key == "mean_ordinal_distance":
                print(f"{name_base:<22} {m_label:<14} {v_old:>10.3f} {v_enh:>15.3f} {v_tele:>15.3f} {diff:>+10.3f}")
            else:
                print(f"{name_base:<22} {m_label:<14} {v_old:>9.1%} {v_enh:>14.1%} {v_tele:>14.1%} {diff:>+9.1%}")
        print("-" * 80)

    print("\nTraining and evaluation complete.")


if __name__ == "__main__":
    main()
