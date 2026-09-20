# RainRisk: Climate Risk Intelligence Platform

RainRisk is a machine learning system designed to predict meteorological drought risk across all 36 meteorological subdivisions of India. It uses 117 years of historical rainfall data (1901 to 2017) from the India Meteorological Department (IMD) along with sea surface temperature anomalies from the Pacific Ocean (Niño 3.4) and Indian Ocean (Dipole Mode Index).

The platform includes a decoupled FastAPI backend and a modern React frontend with an interactive Leaflet map of India, historical timeline exploration, and real-time climate scenario simulations.

---

## Quickstart: How to Run the Platform

You can start the full web platform with a single command:

```bash
# Install dependencies
pip install -r requirements.txt

# Launch FastAPI and open the web app in your browser
python run_webapp.py
```

The application will start on **http://localhost:8008**.

To run the automated test suite (61 tests):
```bash
pytest tests
```

---

## Project Structure

```
RainRisk/
├── backend/                  # FastAPI REST API
│   ├── main.py               # API routes, in-memory caching, and static file serving
│   └── __init__.py
│
├── frontend/                 # React 18 + Vite Web Application
│   ├── src/
│   │   ├── components/       # UI components (ExecutivePulse, GeospatialRadar, etc.)
│   │   ├── api/client.js     # Unified API client connecting to FastAPI
│   │   ├── App.jsx           # Main application view manager
│   │   └── index.css         # Custom dark theme styling (no templates)
│   ├── dist/                 # Pre-built production bundle served by FastAPI
│   └── package.json          # Frontend dependencies (React, Leaflet, Lucide)
│
├── data/
│   ├── raw/                  # Original IMD 1901-2017 CSV and raw ocean index files
│   ├── interim/              # Labeled rainfall data and pre-monsoon ocean features
│   └── processed/            # Final 23-feature training matrix
│
├── src/                      # Core Machine Learning Code
│   ├── labeling.py           # 6 IMD operational categories & LPA baseline logic
│   ├── features.py           # 23-feature engineering with calendar-gap awareness
│   ├── split.py              # Chronological train, validation, and test split
│   ├── temporal_cv.py        # Expanding-window cross-validation harness
│   ├── train.py              # SMOTENC pipeline builder & model candidate setup
│   ├── ordinal.py            # Frank and Hall (2001) ordinal classifier
│   ├── evaluate.py           # Ordinal distance and off-by-one accuracy metrics
│   ├── tune.py               # Multi-fold time-series hyperparameter tuning
│   ├── save_model.py         # Trains all models, evaluates tiers, and saves pipeline
│   ├── constants.py          # Coordinates, colors, and macro-region mappings
│   └── advisory.py           # Farm and water management advisory rules
│
├── tests/                    # Automated Test Suite (61 tests passing)
│   ├── test_features.py      # Tests for calendar gaps and zero future data leakage
│   ├── test_labeling.py      # Tests for IMD classification cutoff boundaries
│   ├── test_methodology_fixes.py # Tests for SMOTENC purity and temporal CV
│   ├── test_ordinal.py       # Tests for ordinal probability consistency
│   ├── test_regression_guards.py # Guards against silent bugs or missing categories
│   ├── test_backend_api.py   # Integration tests for FastAPI endpoints
│   └── test_advisory.py      # Tests for advisory rules
│
├── results/
│   ├── model/                # Serialized model pipeline (best_pipeline.joblib)
│   └── figures/              # Output charts and feature importance plots
│
├── scripts/
│   └── fetch_teleconnections.py # Script to download NOAA and JAMSTEC ocean data
│
├── docs/                     # Technical documentation and specifications
├── requirements.txt          # Python packages needed to run the project
└── run_webapp.py             # One-click startup script
```

---

## Model Benchmark Results

We evaluated 5 machine learning models on an untouched test set of historical records (years 2011 to 2017, totaling 243 regional observations across India).

| Model | Feature Set | Exact Accuracy | Balanced Accuracy | Macro-F1 | Off-by-One Accuracy (+-1 Class) | Mean Ordinal Distance |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Random Forest** *(Best)* | **23 Features (Rain + Ocean)** | **56.0%** | **43.2%** | **0.261** | **93.0%** | **0.52** |
| Gradient Boosting | 23 Features (Rain + Ocean) | 47.3% | 39.6% | 0.230 | 90.5% | 0.63 |
| Support Vector Machine (SVM) | 23 Features (Rain + Ocean) | 43.6% | 38.7% | 0.218 | 88.5% | 0.70 |
| HistGradientBoosting | 23 Features (Rain + Ocean) | 42.0% | 38.9% | 0.214 | 90.5% | 0.69 |
| Logistic Regression | 23 Features (Rain + Ocean) | 33.7% | 34.0% | 0.194 | 83.1% | 0.86 |

### Key Findings
1. **Adding Ocean Temperatures Made a Huge Difference:** Relying on past local rainfall alone capped our accuracy at 52.7%. Adding Pacific and Indian Ocean temperatures pushed accuracy to 56.0% and boosted balanced accuracy from 34.7% to 43.2% (an 8.5% gain).
2. **High Practical Reliability:** The Random Forest achieved **93.0% Off-by-One Accuracy** with a **Mean Ordinal Distance of 0.52**. This means that over 9 times out of 10, the model is either completely correct or off by just a single adjacent severity band. It almost never mistakes a drought for a flood.

---

## Key Engineering Decisions We Defend

1. **SMOTENC Instead of Standard SMOTE:**
   Standard SMOTE creates synthetic samples by drawing straight lines between nearest points in feature space. When applied to one-hot encoded regions, it created impossible blends like 40% Kerala and 60% Punjab. We switched to `SMOTENC`, which uses nearest-neighbor voting for categories so that every synthetic region is 100% real.
2. **Fixing Hidden Calendar Gaps:**
   Three subdivisions (Andaman and Nicobar Islands, Arunachal Pradesh, and Lakshadweep) have missing years in historical records. Standard rolling averages silently averaged across these gaps as if they were consecutive years. We reindexed every subdivision onto a continuous integer calendar grid so that missing years produce clean NaNs instead of bad averages.
3. **Removing Redundant Class Weights:**
   We ran an explicit experiment testing all combinations of oversampling and class weights. We proved that setting `class_weight='balanced'` has zero effect once SMOTENC has already balanced the training data. We removed the extra setting to keep our pipeline simple and verified.
4. **Chronological Cross-Validation:**
   We never shuffle climate data randomly. We built an expanding-window cross-validation system where training years are strictly earlier than test years, ensuring our models never cheat by looking at the future.
