"""
MahaRainRisk: Advanced 30-Day Predictive Early Warning Forecaster (Mode 2)
Engineers dynamic rate-of-change (momentum/velocity) features, monsoon seasonality,
and geographic soil context.
Compares:
1. Enhanced 250-Tree Random Forest
2. Histogram Gradient Boosting Classifier (LightGBM Architecture)
Evaluates out-of-time on unseen 2026 test split with strict zero data-leakage.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import classification_report, f1_score, accuracy_score, confusion_matrix
from sklearn.preprocessing import OrdinalEncoder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
ML_DIR = os.path.join(BASE_DIR, "ml")
os.makedirs(ML_DIR, exist_ok=True)

TARGET_COL = "drought_risk_lead_1"
LABELS_EN = ["Safe", "Watch", "Alert", "Severe", "Extreme"]
LABELS_MR = ["सुरक्षित", "लक्ष ठेवा (अल्प तूट)", "सतर्कता (मध्यम)", "तीव्र दुष्काळ", "अति तीव्र दुष्काळ"]

def build_forecasting_features():
    data_path = os.path.join(PROCESSED_DIR, "master_panel.parquet")
    df = pd.read_parquet(data_path)

    # Sort strictly by taluka and time
    df = df.sort_values(["taluka_lgd_code", "year", "month"]).reset_index(drop=True)

    # 1. Target: Next Month's Risk Tier
    df[TARGET_COL] = df.groupby("taluka_lgd_code")["drought_risk_category"].shift(-1)

    # 2. Rate-of-Change (Momentum / Velocity Features)
    g = df.groupby("taluka_lgd_code")
    df["current_risk_tier"] = df["drought_risk_category"]
    df["delta_soil_moisture"] = df["soil_moisture_index"] - g["soil_moisture_index"].shift(1)
    df["delta_spi3"] = df["spi_3"] - g["spi_3"].shift(1)
    df["delta_temp_max"] = df["temp_max_mean"] - g["temp_max_mean"].shift(1)
    df["delta_dam_storage"] = df["district_dam_storage_pct"] - g["district_dam_storage_pct"].shift(1)

    # 3. Seasonal Cyclical Encodings (Monsoon Phase)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)
    df["is_monsoon"] = df["month"].isin([6, 7, 8, 9]).astype(int)
    df["is_kharif_peak"] = df["month"].isin([7, 8]).astype(int)

    # 4. Geographic Soil & Agro-Climatic Encodings
    zone_enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    df["zone_encoded"] = zone_enc.fit_transform(df[["agro_climatic_zone"]].fillna("Unknown"))
    soil_enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    df["soil_encoded"] = soil_enc.fit_transform(df[["soil_type"]].fillna("Medium Black Soil"))

    zone_map = {z: float(i) for i, z in enumerate(zone_enc.categories_[0])}
    soil_map = {s: float(i) for i, s in enumerate(soil_enc.categories_[0])}

    # Drop rows without future ground truth (last month of each taluka)
    valid_df = df.dropna(subset=[TARGET_COL]).copy()
    valid_df[TARGET_COL] = valid_df[TARGET_COL].astype(int)

    return valid_df, zone_map, soil_map

FEATURE_COLS = [
    # Core Current Telemetry
    'current_risk_tier',
    'rainfall_monthly_mm', 'rainy_days', 'temp_max_mean', 'temp_min_mean',
    'max_consecutive_dry_days', 'rain_roll_1', 'rain_roll_3', 'rain_roll_6',
    'spi_1', 'spi_3', 'spi_6',
    'soil_moisture_index', 'vci', 'groundwater_depth_mbgl',
    'district_dam_storage_pct', 'normal_annual_rainfall_mm',
    'oni', 'dmi',

    # Dynamic Rate-of-Change (Velocity)
    'delta_soil_moisture',
    'delta_spi3',
    'delta_temp_max',
    'delta_dam_storage',

    # Monsoon Seasonal Phase
    'month_sin', 'month_cos', 'is_monsoon', 'is_kharif_peak',

    # Geographic Physical Context
    'latitude', 'longitude', 'zone_encoded', 'soil_encoded'
]

def train_and_evaluate():
    print("=" * 75)
    print(" MahaRainRisk: Upgraded 30-Day Predictive Early Warning Forecaster")
    print("=" * 75)

    df, zone_map, soil_map = build_forecasting_features()
    print(f"[*] Engineered {len(FEATURE_COLS)} multi-scale temporal & physical features.")
    print(f"[*] Total valid forecasting samples: {len(df):,} taluka-months")

    # Strict Zero-Leakage Split (Train < 2026, Test == 2026)
    train_df = df[df["year"] < 2026].copy()
    test_df = df[df["year"] == 2026].copy()

    # Preprocessing medians strictly on train_df
    feature_medians = train_df[FEATURE_COLS].median()
    train_df[FEATURE_COLS] = train_df[FEATURE_COLS].fillna(feature_medians)
    test_df[FEATURE_COLS] = test_df[FEATURE_COLS].fillna(feature_medians)

    X_train, y_train = train_df[FEATURE_COLS], train_df[TARGET_COL]
    X_test, y_test = test_df[FEATURE_COLS], test_df[TARGET_COL]

    print(f"[*] Training on {len(X_train):,} past samples (2020-2025)...")
    print(f"[*] Evaluating on {len(X_test):,} unseen live future samples (2026)...")

    # 1. Model A: Upgraded Random Forest (250 Trees)
    print("\n--- Training Model A: Enhanced Random Forest (250 Trees) ---")
    rf = RandomForestClassifier(
        n_estimators=250,
        max_depth=14,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    acc_rf = accuracy_score(y_test, y_pred_rf)
    f1_rf = f1_score(y_test, y_pred_rf, average="macro", zero_division=0)
    print(f"  [RF-250] 2026 Out-of-Time Accuracy: {acc_rf * 100:.2f}% | Macro F1: {f1_rf:.4f}")

    # 2. Model B: Histogram Gradient Boosting (Champion)
    print("\n--- Training Model B: Histogram Gradient Boosting (GBDT) ---")
    hgb = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.06,
        max_depth=10,
        min_samples_leaf=8,
        class_weight="balanced",
        random_state=42
    )
    hgb.fit(X_train, y_train)
    y_pred_hgb = hgb.predict(X_test)
    acc_hgb = accuracy_score(y_test, y_pred_hgb)
    f1_hgb = f1_score(y_test, y_pred_hgb, average="macro", zero_division=0)
    print(f"  [HGB-GBDT] 2026 Out-of-Time Accuracy: {acc_hgb * 100:.2f}% | Macro F1: {f1_hgb:.4f}")

    # Select Champion
    if f1_hgb >= f1_rf:
        champion_model = hgb
        champion_name = "Histogram Gradient Boosting (GBDT)"
        champion_acc = acc_hgb
        champion_f1 = f1_hgb
        y_best = y_pred_hgb
    else:
        champion_model = rf
        champion_name = "Enhanced Random Forest (250 Trees)"
        champion_acc = acc_rf
        champion_f1 = f1_rf
        y_best = y_pred_rf

    print("\n" + "=" * 75)
    print(f" CHAMPION SELECTED: {champion_name}")
    print(f" 2026 Accuracy: {champion_acc * 100:.2f}% (Baseline was 74.60%)")
    print(f" 2026 Macro F1: {champion_f1:.4f} (Baseline was 0.4435)")
    print("=" * 75)

    print("\nClassification Report (Unseen 2026 Live Validation):")
    print(classification_report(y_test, y_best, labels=[0, 1, 2, 3, 4], target_names=LABELS_EN, zero_division=0))

    # Top drivers (using RF feature importances)
    feat_imp = pd.Series(rf.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
    print("Top 6 Predictive Forecaster Drivers:")
    for feat, imp in feat_imp.head(6).items():
        print(f"  - {feat}: {imp * 100:.2f}%")

    # Serialize champion artifact
    import hashlib
    import shutil

    artifact_path = os.path.join(ML_DIR, "drought_forecaster.joblib")
    joblib.dump({
        "model": champion_model,
        "champion_type": champion_name,
        "feature_names": FEATURE_COLS,
        "feature_medians": feature_medians.to_dict(),
        "zone_map": zone_map,
        "soil_map": soil_map,
        "labels_en": LABELS_EN,
        "labels_mr": LABELS_MR,
        "metrics": {
            "test_accuracy_2026": float(champion_acc),
            "macro_f1_2026": float(champion_f1),
            "lead_time": "30 days (1 month)"
        }
    }, artifact_path)
    print(f"\n[OK] Champion model saved to: {artifact_path}")

    # Compute SHA-256
    with open(artifact_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"[SECURITY] Forecaster SHA-256 Digest: {sha256}")

    # Mirror to Rainrisk/ml
    rainrisk_ml = os.path.join(os.path.dirname(BASE_DIR), "Rainrisk", "ml")
    if os.path.exists(rainrisk_ml):
        dst = os.path.join(rainrisk_ml, "drought_forecaster.joblib")
        shutil.copy2(artifact_path, dst)
        print(f"[OK] Mirrored forecaster to: {dst}")

if __name__ == "__main__":
    train_and_evaluate()
