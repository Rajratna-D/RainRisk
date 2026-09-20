# RainRisk: System and Architecture Guide

## 1. High-Level Overview

RainRisk is built around a simple principle: keep data processing, machine learning, and the web interface cleanly separated. 

Instead of writing one massive Python script that does everything, we split the project into three clear layers:
1. **The Machine Learning Pipeline (`src/`):** Reads raw meteorological data, cleans it, engineers features without lookahead leakage, trains our models, and saves the best trained pipeline to disk.
2. **The Backend REST API (`backend/`):** A FastAPI service that loads the saved model into memory once when the server boots up, exposes clean HTTP endpoints, and handles prediction requests in under 20 milliseconds.
3. **The Frontend User Interface (`frontend/`):** A single-page application built with React and Vite. It lets users explore an interactive map of India, view 117 years of rainfall history, compare model accuracy, and test custom climate scenarios using live sliders.

---

## 2. Directory Structure

```
RainRisk/
├── backend/                  # FastAPI REST API server
│   ├── main.py               # REST endpoints, in-memory cache, and static file serving
│   └── __init__.py
│
├── frontend/                 # React 18 + Vite frontend
│   ├── src/
│   │   ├── components/       # UI views (Map, Timeline, Simulator, Leaderboard)
│   │   ├── api/client.js     # Lightweight fetch wrapper for API calls
│   │   ├── App.jsx           # Main view switcher
│   │   └── index.css         # Clean dark theme styling
│   ├── dist/                 # Compiled production assets served by FastAPI
│   └── package.json          # Node dependencies (React, Leaflet, Lucide)
│
├── data/
│   ├── raw/                  # Original untouched IMD rainfall and ocean index files
│   ├── interim/              # Cleaned intermediate tables and pre-monsoon features
│   └── processed/            # Final 23-feature training matrix
│
├── src/                      # Core Python ML modules
│   ├── labeling.py           # IMD operational 6-category classification logic
│   ├── features.py           # 23-feature engineering with calendar-gap awareness
│   ├── split.py              # Chronological train, validation, and test split
│   ├── temporal_cv.py        # Expanding-window cross-validation
│   ├── train.py              # Pipeline construction with SMOTENC
│   ├── ordinal.py            # Frank and Hall ordinal decomposition classifier
│   ├── evaluate.py           # Accuracy, balanced accuracy, and ordinal distance metrics
│   ├── tune.py               # Multi-fold time-series hyperparameter tuning
│   ├── save_model.py         # Full training pipeline and artifact serializer
│   ├── constants.py          # Coordinates, color mappings, and macro-regions
│   └── advisory.py           # Agricultural contingency recommendations
│
├── tests/                    # 61 automated tests verifying every pipeline step
├── results/
│   ├── model/                # Serialized best model pipeline and benchmark JSON files
│   └── figures/              # Generated charts and feature importance plots
│
├── scripts/
│   └── fetch_teleconnections.py # Automated fetch script for NOAA and JAMSTEC ocean data
│
├── docs/                     # Technical specifications and guides
├── requirements.txt          # Pinned Python package dependencies
└── run_webapp.py             # Single-command launcher for the full application
```

---

## 3. How Data Moves Through the System

Data moves in a strict, single-direction path from raw records to the browser:

```
[Raw IMD Rainfall Records + NOAA Ocean Index Files]
                     │
                     ▼
[1. Labeling & Ingestion] (src/labeling.py, scripts/fetch_teleconnections.py)
   - Computes fixed 1971-2020 Long Period Average (LPA) per subdivision.
   - Calculates percentage departure and assigns the official IMD category.
   - Downloads monthly Niño 3.4 and IOD data, extracting pre-monsoon spring lags.
                     │
                     ▼
[2. Feature Engineering] (src/features.py)
   - Reindexes each subdivision onto a continuous integer calendar grid.
   - Computes 18 prior-year rainfall lags and rolling averages using .shift(1).
   - Merges 5 zero-leakage pre-monsoon ocean features (Niño 3.4 and IOD).
                     │
                     ▼
[3. Modeling & Oversampling] (src/train.py, src/save_model.py)
   - Chronological split: Train (1901-2000), Val (2001-2010), Test (2011-2017).
   - SMOTENC oversamples minority classes on raw columns within training folds.
   - Evaluates 5 model architectures across baseline, enhanced, and ocean tiers.
   - Saves the winning Random Forest pipeline to results/model/best_pipeline.joblib.
                     │
                     ▼
[4. FastAPI Backend] (backend/main.py)
   - Loads the 100MB model pipeline and historical dataframes into memory on boot.
   - Serves fast REST endpoints (/api/overview, /api/map, /api/predict).
   - Validates incoming simulation requests with Pydantic schemas.
                     │
                     ▼
[5. React Frontend] (frontend/src/)
   - Renders interactive Leaflet map showing all 36 subdivisions with dynamic bubbles.
   - Displays 117-year historical timeline with clickable milestone drought years.
   - Sends simulation vectors to /api/predict and renders instant risk probabilities.
```

---

## 4. Key Architectural Choices

### Why We Separated the Backend and Frontend
Early versions used Streamlit, but Streamlit re-runs the entire script on every user click. That made interactive maps and sliders feel sluggish. Decoupling into FastAPI and React gave us:
* **Immediate Response:** The model stays in memory, so predictions take under 20 milliseconds.
* **Full Design Control:** We built a custom dark theme without Streamlit's default templates or layout limits.
* **Production Standards:** This matches how real software teams build machine learning products.

### How We Prevent Future Data Leakage
Time-series data has an easy trap: looking ahead into the future. We enforce three strict rules:
1. Every lag feature uses `.shift(1)` so it only looks at years before the target year.
2. For ocean data, we only use winter (DJF) and spring (MAM) values before the June 1st monsoon onset.
3. Our cross-validation expands forward in time so training folds are always earlier than test folds.

### Why We Reindexed for Calendar Gaps
If an island region is missing the year 2002, a standard rolling average would take 2000, 2001, and 2003 as if they were consecutive. That is wrong. Reindexing forces missing years to be empty rows, so our rolling window properly produces an empty value instead of a fake average.
