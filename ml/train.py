"""
MahaRainRisk: Production Model Training Pipeline
Trains multi-class Random Forest & Gradient Boosting early warning classifiers
on the historical feature store and saves the production model artifact.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
ML_DIR = os.path.join(BASE_DIR, "ml")
os.makedirs(ML_DIR, exist_ok=True)

FEATURE_COLS = [
    'rainfall_monthly_mm', 'rainy_days', 'temp_max_mean', 'temp_min_mean',
    'max_consecutive_dry_days', 'rain_roll_1', 'rain_roll_3', 'rain_roll_6',
    'spi_1', 'spi_3', 'spi_6',
    'normal_annual_rainfall_mm',
    'nino34_anomaly', 'oni', 'dmi',
    'district_dam_storage_pct',
    'soil_moisture_index', 'vci', 'groundwater_depth_mbgl'
]

TARGET_COL = 'drought_risk_category'
LABELS_EN = ["Safe", "Watch", "Alert", "Severe", "Extreme"]
LABELS_MR = ["सुरक्षित", "लक्ष ठेवा (अल्प तूट)", "सतर्कता (मध्यम)", "तीव्र दुष्काळ", "अति तीव्र दुष्काळ"]

def train_production_model():
    data_path = os.path.join(PROCESSED_DIR, "master_panel.parquet")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Master panel not found at {data_path}. Run build_master_panel.py first.")

    print(f"[*] Loading master panel from {data_path}...")
    df = pd.read_parquet(data_path)

    # 1. Temporal Split (Strict Zero-Leakage: Train < 2026, Test == 2026)
    train_df = df[df['year'] < 2026].copy()
    test_df = df[df['year'] == 2026].copy()

    # 2. Imputation Parameters (Computed STRICTLY on train_df only!)
    feature_medians = train_df[FEATURE_COLS].median()
    train_df[FEATURE_COLS] = train_df[FEATURE_COLS].fillna(feature_medians)
    test_df[FEATURE_COLS] = test_df[FEATURE_COLS].fillna(feature_medians)

    X_train, y_train = train_df[FEATURE_COLS], train_df[TARGET_COL]
    X_test, y_test = test_df[FEATURE_COLS], test_df[TARGET_COL]

    print(f"[*] Training Random Forest (250 Trees) on {len(X_train)} samples across {len(FEATURE_COLS)} features...")
    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=12,
        min_samples_split=5,
        class_weight="balanced",
        oob_score=True,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Test evaluation
    from sklearn.metrics import accuracy_score
    import hashlib
    import shutil

    y_pred = model.predict(X_test)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    test_acc = accuracy_score(y_test, y_pred)
    oob_acc = model.oob_score_
    print(f"[OK] Out-of-time 2026 Validation Macro F1-Score: {macro_f1:.4f}")
    print(f"[OK] Out-of-time 2026 Validation Accuracy:      {test_acc * 100:.2f}%")
    print(f"[OK] Out-of-Bag (OOB) Training Accuracy:        {oob_acc * 100:.2f}%")
    print("\nClassification Report (2026 Kharif Raw Evaluation):")
    print(classification_report(y_test, y_pred, labels=[0, 1, 2, 3, 4], target_names=LABELS_EN, zero_division=0))

    # Calibrated decision policy evaluation (ML-01)
    probs = model.predict_proba(X_test)
    y_calib = []
    for p in probs:
        if len(p) >= 5 and p[4] >= 0.20: y_calib.append(4)
        elif len(p) >= 4 and p[3] >= 0.35: y_calib.append(3)
        elif len(p) >= 3 and p[2] >= 0.40: y_calib.append(2)
        elif len(p) >= 2 and p[1] >= 0.45: y_calib.append(1)
        else: y_calib.append(int(np.argmax(p)))
    y_calib = np.array(y_calib)
    macro_f1_calib = f1_score(y_test, y_calib, average="macro")
    acc_calib = accuracy_score(y_test, y_calib)
    print(f"[OK] Calibrated 2026 Macro F1-Score: {macro_f1_calib:.4f} | Accuracy: {acc_calib * 100:.2f}%")
    print("\nClassification Report (2026 Kharif Calibrated Policy):")
    print(classification_report(y_test, y_calib, labels=[0, 1, 2, 3, 4], target_names=LABELS_EN, zero_division=0))

    # Feature importance
    feat_imp = pd.Series(model.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
    print("\nTop 5 Predictive Features:")
    for feat, imp in feat_imp.head(5).items():
        print(f"  - {feat}: {imp:.4f}")

    # Save artifact
    artifact_path = os.path.join(ML_DIR, "drought_model.joblib")
    joblib.dump({
        "model": model,
        "feature_names": FEATURE_COLS,
        "feature_medians": feature_medians.to_dict(),
        "labels_en": LABELS_EN,
        "labels_mr": LABELS_MR,
        "metrics": {
            "macro_f1_2026": float(macro_f1),
            "test_accuracy_2026": float(test_acc),
            "oob_score": float(oob_acc),
            "n_estimators": 250
        }
    }, artifact_path)
    print(f"[OK] Model successfully serialized to: {artifact_path}")

    # Compute SHA-256
    with open(artifact_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"[SECURITY] Model SHA-256 Digest: {sha256}")

    # Mirror to Rainrisk/ml
    rainrisk_ml = os.path.join(os.path.dirname(BASE_DIR), "Rainrisk", "ml")
    if os.path.exists(rainrisk_ml):
        dst = os.path.join(rainrisk_ml, "drought_model.joblib")
        shutil.copy2(artifact_path, dst)
        print(f"[OK] Mirrored model to: {dst}")

if __name__ == "__main__":
    train_production_model()
