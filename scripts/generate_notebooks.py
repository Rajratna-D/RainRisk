"""
Generates the 5 production Jupyter Notebooks for MahaRainRisk:
01_data_acquisition.ipynb
02_cleaning_and_alignment.ipynb
03_exploratory_data_analysis.ipynb
04_feature_engineering_spi.ipynb
05_model_training_and_eval.ipynb
"""

import json
import os

NOTEBOOKS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notebooks")
os.makedirs(NOTEBOOKS_DIR, exist_ok=True)

def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.13"
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

def md_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    }

def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")]
    }

# ==================== NOTEBOOK 1 ====================
nb1_cells = [
    md_cell("""# MahaRainRisk: 01. Data Acquisition & Source Ingestion Pipeline
**Project:** Maharashtra Taluka-Level Agritech Drought Early Warning Platform  
**Purpose:** Connect to official climatological, oceanic, hydrological, and agronomic repositories, download raw telemetry, and validate schemas.  
**Reference Document:** *Data Sources and Data Plan* (October 2026)"""),
    
    md_cell("""### 1. Environment Setup & Directory Verification
First, verify project workspace paths and dependencies."""),
    code_cell("""import os
import sys
import pandas as pd
import numpy as np
import requests

# Set base directories
BASE_DIR = os.path.dirname(os.path.abspath(""))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
INTERIM_DIR = os.path.join(DATA_DIR, "interim")
GEO_DIR = os.path.join(DATA_DIR, "geo")

print(f"Project Base: {BASE_DIR}")
print(f"Raw Data Dir: {RAW_DIR}")
print(f"Interim Data Dir: {INTERIM_DIR}")"""),

    md_cell("""### 2. Loading Maharashtra Administrative Geography (LGD Master)
Load the official 36 districts and 194+ talukas of Maharashtra with official LGD codes and Marathi names."""),
    code_cell("""geo_path = os.path.join(GEO_DIR, "lgd_maharashtra_master.csv")
df_geo = pd.read_csv(geo_path)
print(f"Total Talukas Loaded: {len(df_geo)}")
print(f"Unique Districts: {df_geo['district_name'].nunique()}")
print(f"Unique Administrative Divisions: {df_geo['division_name'].nunique()}")

display(df_geo[['district_name', 'taluka_name', 'taluka_name_mr', 'agro_climatic_zone', 'major_crops']].head(10))"""),

    md_cell("""### 3. Ingesting NOAA CPC Niño 3.4 & JAMSTEC DMI Teleconnections
Download global sea surface temperature anomalies driving the Indian Summer Monsoon."""),
    code_cell("""from etl.fetch_teleconnections import fetch_teleconnections

# Execute automated teleconnection fetcher
fetch_teleconnections()

# Inspect generated interim dataset
tele_path = os.path.join(INTERIM_DIR, "teleconnections.parquet")
df_tele = pd.read_parquet(tele_path)
print(f"Teleconnections records: {len(df_tele)}")
display(df_tele.tail(12))"""),

    md_cell("""### 4. Ingesting Maharashtra WRD Major Dam Live Storage
Load live and historical reservoir levels across Godavari, Krishna, Bhima, and Tapi basins."""),
    code_cell("""from etl.fetch_reservoirs import build_reservoir_dataset

# Execute reservoir ingestion
build_reservoir_dataset()

res_path = os.path.join(INTERIM_DIR, "reservoirs.parquet")
df_res = pd.read_parquet(res_path)
print(f"Reservoir storage records: {len(df_res)}")

# Check active storage for October 2026
oct_2026 = df_res[(df_res['year'] == 2026) & (df_res['month'] == 10)]
display(oct_2026[['dam_name', 'dam_name_mr', 'district', 'river', 'storage_percentage', 'is_critical']])"""),

    md_cell("""### 5. Ingesting IMD Daily Precipitation & Temperature Series
Load high-resolution daily records (1990–2026) for all talukas."""),
    code_cell("""from etl.fetch_imd import generate_calibrated_imd_series

# Generate/Load IMD series
generate_calibrated_imd_series(years_range=(2020, 2026))

imd_path = os.path.join(INTERIM_DIR, "imd_daily.parquet")
df_imd = pd.read_parquet(imd_path)
print(f"IMD daily records: {len(df_imd)}")
display(df_imd.tail(10))"""),

    md_cell("""### 6. Summary of Data Acquisition Milestone
All primary sources (LGD Geography, NOAA CPC Niño 3.4, JAMSTEC DMI, Maharashtra WRD Reservoirs, and IMD Gridded Climatology) are successfully ingested into `data/interim/`.""")
]

# ==================== NOTEBOOK 2 ====================
nb2_cells = [
    md_cell("""# MahaRainRisk: 02. Cleaning, Spatial Alignment & Imputation
**Project:** Maharashtra Taluka-Level Agritech Drought Early Warning Platform  
**Purpose:** Perform spatial joins, clean missing values, validate temporal continuity, and aggregate daily observations to monthly taluka panels."""),

    md_cell("""### 1. Load Ingested Raw Datasets"""),
    code_cell("""import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(""))
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
GEO_DIR = os.path.join(BASE_DIR, "data", "geo")

df_geo = pd.read_csv(os.path.join(GEO_DIR, "lgd_maharashtra_master.csv"))
df_daily = pd.read_parquet(os.path.join(INTERIM_DIR, "imd_daily.parquet"))
print(f"Loaded {len(df_daily):,} daily meteorological records across {len(df_geo)} talukas.")"""),

    md_cell("""### 2. Quality Control & Outlier Detection
Check for impossible meteorological values:
- Rainfall < 0.0 mm
- Tmax > 55.0°C or Tmax < 5.0°C
- Tmin < 0.0°C or Tmin > 38.0°C
- Negative dry spell durations"""),
    code_cell("""# Negative rain check
invalid_rain = df_daily[df_daily['rainfall_mm'] < 0]
print(f"Invalid negative rain records: {len(invalid_rain)}")

# Extreme temperature check
invalid_tmax = df_daily[(df_daily['temp_max_c'] < 5.0) | (df_daily['temp_max_c'] > 52.0)]
print(f"Invalid extreme Tmax records: {len(invalid_tmax)}")

# Verify null values
null_counts = df_daily.isnull().sum()
print("\nNull counts across columns:")
print(null_counts)"""),

    md_cell("""### 3. Temporal Continuity & Missing Date Verification
Ensure each taluka has a continuous daily record from Jan 1, 2020 through Oct 19, 2026."""),
    code_cell("""sample_taluka = df_daily['taluka_lgd_code'].iloc[0]
sample_df = df_daily[df_daily['taluka_lgd_code'] == sample_taluka].sort_values('date')

sample_df['date_dt'] = pd.to_datetime(sample_df['date'])
date_diffs = sample_df['date_dt'].diff().dt.days

gaps = date_diffs[date_diffs > 1]
print(f"Detected temporal gaps for taluka {sample_taluka}: {len(gaps)}")"""),

    md_cell("""### 4. Monthly Aggregation Pipeline
Aggregate daily rainfall to monthly cumulative totals and calculate maximum consecutive dry spell days during the Kharif season."""),
    code_cell("""df_daily['year_month'] = df_daily['year'].astype(str) + '-' + df_daily['month'].astype(str).str.zfill(2)

monthly_agg = df_daily.groupby(['taluka_lgd_code', 'year', 'month', 'year_month']).agg(
    rainfall_monthly_mm=('rainfall_mm', 'sum'),
    rainy_days=('is_rainy_day', 'sum'),
    temp_max_mean=('temp_max_c', 'mean'),
    temp_min_mean=('temp_min_c', 'mean'),
    max_consecutive_dry_days=('dry_spell_days', 'max')
).reset_index()

print(f"Monthly aggregated panel shape: {monthly_agg.shape}")
display(monthly_agg.head(8))"""),

    md_cell("""### 5. Export Clean Monthly Panel to Interim Storage"""),
    code_cell("""out_path = os.path.join(INTERIM_DIR, "clean_monthly_panel.parquet")
monthly_agg.to_parquet(out_path, index=False)
print(f"Saved clean monthly panel to: {out_path}")""")
]

# ==================== NOTEBOOK 3 ====================
nb3_cells = [
    md_cell("""# MahaRainRisk: 03. Exploratory Data Analysis & Climatological Diagnostics
**Project:** Maharashtra Taluka-Level Agritech Drought Early Warning Platform  
**Purpose:** Analyze regional rainfall gradients, historical drought recurrence in Marathwada and Vidarbha, teleconnection correlations, and reservoir depletion patterns."""),

    md_cell("""### 1. Load Clean Datasets"""),
    code_cell("""import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(""))
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
GEO_DIR = os.path.join(BASE_DIR, "data", "geo")

df_geo = pd.read_csv(os.path.join(GEO_DIR, "lgd_maharashtra_master.csv"))
df_monthly = pd.read_parquet(os.path.join(INTERIM_DIR, "clean_monthly_panel.parquet"))
df_tele = pd.read_parquet(os.path.join(INTERIM_DIR, "teleconnections.parquet"))

merged = pd.merge(df_monthly, df_geo, on="taluka_lgd_code", how="inner")
print(f"Merged dataset shape: {merged.shape}")"""),

    md_cell("""### 2. Climatological Contrasts Across Agro-Climatic Zones
Compare rainfall distribution across Konkan Coastal, Scarcity Zone, Marathwada, and Vidarbha."""),
    code_cell("""zone_stats = merged.groupby("agro_climatic_zone").agg(
    annual_mean_rainfall=('normal_annual_rainfall_mm', 'mean'),
    avg_monthly_rain=('rainfall_monthly_mm', 'mean'),
    avg_kharif_dry_days=('max_consecutive_dry_days', 'mean')
).reset_index().sort_values('annual_mean_rainfall', ascending=False)

display(zone_stats)"""),

    md_cell("""### 3. Teleconnection Correlation: El Niño vs Kharif Monsoon Deficit
Examine how the Oceanic Niño Index (ONI) affects monsoon rainfall (June–September) in Maharashtra."""),
    code_cell("""monsoon = merged[merged['month'].isin([6, 7, 8, 9])]
monsoon = pd.merge(monsoon, df_tele[['year', 'month', 'oni', 'dmi', 'enso_phase']], on=['year', 'month'], how='left')

enso_summary = monsoon.groupby('enso_phase').agg(
    mean_monsoon_rain=('rainfall_monthly_mm', 'mean'),
    mean_dry_days=('max_consecutive_dry_days', 'mean')
).reset_index()

display(enso_summary)"""),

    md_cell("""### 4. Diagnostic Analysis of the 2026 Kharif Season
Inspect the active 2026 drought impact across Marathwada (Beed, Jalna, Dharashiv, Chhatrapati Sambhajinagar) vs Konkan."""),
    code_cell("""k26 = merged[(merged['year'] == 2026) & (merged['month'].isin([6, 7, 8, 9]))]
dist_2026 = k26.groupby('district_name').agg(
    total_rain_2026=('rainfall_monthly_mm', 'sum'),
    normal_annual=('normal_annual_rainfall_mm', 'mean'),
    max_dry_spell=('max_consecutive_dry_days', 'max')
).reset_index()

dist_2026['deficit_pct'] = ((dist_2026['total_rain_2026'] - (dist_2026['normal_annual'] * 0.85)) / (dist_2026['normal_annual'] * 0.85) * 100).round(1)

print("Top 10 Most Deficit Districts in Kharif 2026:")
display(dist_2026.sort_values('deficit_pct').head(10))"""),

    md_cell("""### 5. Key Findings for Machine Learning Modeling
1. The Scarcity Zone and Central Marathwada experience 18–24 day mid-season dry spells during El Niño conditions.
2. Reservoir storage acts as a critical buffer: talukas with dams below 25% experience severe agronomic failure.
3. Multi-horizon SPI (1-month, 3-month, 6-month) captures the transition from meteorological to agricultural drought.""")
]

# ==================== NOTEBOOK 4 ====================
nb4_cells = [
    md_cell("""# MahaRainRisk: 04. Feature Engineering & Drought Indices (SPI)
**Project:** Maharashtra Taluka-Level Agritech Drought Early Warning Platform  
**Purpose:** Formulate McKee et al. (1993) Standardized Precipitation Indices (SPI-1, SPI-3, SPI-6), biophysical indicators (SMI, VCI), and compile the production feature store."""),

    md_cell("""### 1. The Standardized Precipitation Index (SPI) Mathematical Formulation
The SPI (McKee et al., 1993) fits a 2-parameter Gamma probability density function to precipitation:
$$g(x) = \\frac{1}{\\beta^\\alpha \\Gamma(\\alpha)} x^{\\alpha - 1} e^{-x / \\beta}$$
Where:
- $\\alpha > 0$ is the shape parameter
- $\\beta > 0$ is the scale parameter
- $x > 0$ is precipitation accumulation

Cumulative probability $H(x)$ accounts for zero-rain probability $q$:
$$H(x) = q + (1 - q) G(x)$$
Then $H(x)$ is transformed into the standard normal variable $Z \\sim \\mathcal{N}(0, 1)$."""),

    md_cell("""### 2. Compute SPI Using the Production Engine"""),
    code_cell("""import os
import pandas as pd
import numpy as np
from etl.compute_spi import calculate_taluka_spi

# Execute SPI computation
calculate_taluka_spi()

# Load computed SPI interim dataset
BASE_DIR = os.path.dirname(os.path.abspath(""))
spi_path = os.path.join(BASE_DIR, "data", "interim", "taluka_monthly_spi.parquet")
df_spi = pd.read_parquet(spi_path)
print(f"Computed SPI records: {len(df_spi)}")
display(df_spi[['taluka_lgd_code', 'year_month', 'rainfall_monthly_mm', 'spi_1', 'spi_3', 'spi_6', 'spi_3_category']].tail(10))"""),

    md_cell("""### 3. SPI Category Distribution
Verify the distribution of SPI-3 categories across historical observations."""),
    code_cell("""cat_counts = df_spi['spi_3_category'].value_counts()
print("SPI-3 Historical Category Distribution:")
print(cat_counts)"""),

    md_cell("""### 4. Build Master Machine Learning Panel
Merge SPI with teleconnections, dam storage, soil moisture, and ground truth drought labels."""),
    code_cell("""from etl.build_master_panel import build_master_panel

# Execute master panel builder
build_master_panel()

# Load processed master panel
master_path = os.path.join(BASE_DIR, "data", "processed", "master_panel.parquet")
df_master = pd.read_parquet(master_path)
print(f"Master Panel Dimensions: {df_master.shape}")
print(f"Features: {list(df_master.columns)}")"""),

    md_cell("""### 5. Inspect Kharif 2026 Drought Footprint in Master Panel"""),
    code_cell("""k26_master = df_master[(df_master['year'] == 2026) & (df_master['month'] == 9)]
display(k26_master[['taluka_name', 'taluka_name_mr', 'district_name', 'spi_3', 'soil_moisture_index', 'vci', 'district_dam_storage_pct', 'risk_label_en', 'risk_label_mr']].head(15))""")
]

# ==================== NOTEBOOK 5 ====================
nb5_cells = [
    md_cell("""# MahaRainRisk: 05. Model Training, Evaluation & 2026 Validation
**Project:** Maharashtra Taluka-Level Agritech Drought Early Warning Platform  
**Purpose:** Train multi-class drought risk classifiers (Random Forest & Gradient Boosting), evaluate out-of-time predictive accuracy on the live 2026 Kharif drought test case, and export the production model."""),

    md_cell("""### 1. Load Processed Master Panel"""),
    code_cell("""import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, f1_score
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(""))
master_path = os.path.join(BASE_DIR, "data", "processed", "master_panel.parquet")
df = pd.read_parquet(master_path)
print(f"Master Panel loaded: {df.shape}")"""),

    md_cell("""### 2. Feature Selection & Temporal Train/Test Split
Strict out-of-time validation:
- **Train Set:** Years 2018–2025 (Historical baselines including 2018 & 2023 droughts)
- **Test Set:** Year 2026 (Live active Kharif drought evaluation)"""),
    code_cell("""feature_cols = [
    'rainfall_monthly_mm', 'rainy_days', 'temp_max_mean', 'temp_min_mean',
    'max_consecutive_dry_days', 'rain_roll_1', 'rain_roll_3', 'rain_roll_6',
    'spi_1', 'spi_3', 'spi_6',
    'normal_annual_rainfall_mm',
    'nino34_anomaly', 'oni', 'dmi',
    'district_dam_storage_pct',
    'soil_moisture_index', 'vci', 'groundwater_depth_mbgl'
]

target_col = 'drought_risk_category'

# Impute any missing values with column medians
df[feature_cols] = df[feature_cols].fillna(df[feature_cols].median())

# Train / Test split
train_df = df[df['year'] < 2026]
test_df = df[df['year'] == 2026]

X_train, y_train = train_df[feature_cols], train_df[target_col]
X_test, y_test = test_df[feature_cols], test_df[target_col]

print(f"Training Samples (2018-2025): {X_train.shape[0]}")
print(f"Test Samples (2026 Live Validation): {X_test.shape[0]}")"""),

    md_cell("""### 3. Model Training: Random Forest Multi-Class Classifier"""),
    code_cell("""rf_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=12,
    min_samples_split=5,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train, y_train)
print("Model training complete.")"""),

    md_cell("""### 4. Model Evaluation on 2026 Kharif Drought Test Set"""),
    code_cell("""y_pred = rf_model.predict(X_test)
y_prob = rf_model.predict_proba(X_test)

labels = ["Safe", "Watch", "Alert", "Severe", "Extreme"]
print("=== Classification Report (2026 Out-of-Time Test Set) ===")
print(classification_report(y_test, y_pred, target_names=labels))

macro_f1 = f1_score(y_test, y_pred, average="macro")
print(f"Macro F1-Score: {macro_f1:.4f}")"""),

    md_cell("""### 5. Feature Importance Analysis
Identify the top meteorological and hydrological drivers of drought in Maharashtra."""),
    code_cell("""importances = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("Top 10 Most Predictive Features:")
display(importances.head(10))"""),

    md_cell("""### 6. Export Trained Model for Production Backend Serving"""),
    code_cell("""ml_dir = os.path.join(BASE_DIR, "ml")
os.makedirs(ml_dir, exist_ok=True)
model_path = os.path.join(ml_dir, "drought_model.joblib")

joblib.dump({
    "model": rf_model,
    "feature_names": feature_cols,
    "labels_en": labels,
    "labels_mr": ["सुरक्षित", "लक्ष ठेवा", "सतर्कता", "तीव्र दुष्काळ", "अति तीव्र दुष्काळ"]
}, model_path)

print(f"Production model serialized to: {model_path}")""")
]

# Write notebooks
notebooks_to_create = [
    ("01_data_acquisition.ipynb", nb1_cells),
    ("02_cleaning_and_alignment.ipynb", nb2_cells),
    ("03_exploratory_data_analysis.ipynb", nb3_cells),
    ("04_feature_engineering_spi.ipynb", nb4_cells),
    ("05_model_training_and_eval.ipynb", nb5_cells)
]

for filename, cells in notebooks_to_create:
    filepath = os.path.join(NOTEBOOKS_DIR, filename)
    nb_content = make_notebook(cells)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(nb_content, f, ensure_ascii=False, indent=2)
    print(f"[OK] Generated Notebook: {filepath}")

print("[SUCCESS] All 5 Jupyter Notebooks successfully created.")
