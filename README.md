# RainRisk: AI-Powered Monsoon Drought and Rainfall Prediction for India

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Pytest](https://img.shields.io/badge/Tests-61%2F61%20Passing-44CC11?style=flat-square&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![IMD Dataset](https://img.shields.io/badge/IMD%20Records-117%20Years%20(1901--2017)-blue?style=flat-square)](https://mausam.imd.gov.in/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Report](https://img.shields.io/badge/Report-22--Page%20PDF-red?style=flat-square&logo=adobe-acrobat-reader&logoColor=white)](docs/RainRisk_Project_Report.pdf)

> **Predicting regional monsoon rainfall and drought risks across India before the rainy season begins - using 117 years of weather history, ocean temperatures, and machine learning.**

---

## What is RainRisk?

Every year between June and September, India receives over **70% of its annual rainfall** through the Southwest Monsoon. This rain feeds India's rivers, fills reservoirs, and powers the summer farming season (Kharif), which accounts for **half of India's food production** and supports **600 million people**.

Because more than **55% of India's farms have no canal or tube-well irrigation**, farmers depend entirely on timely rainfall. A bad monsoon can destroy a whole year's crop and wipe out a farming family's savings.

### Why National Forecasts Are Not Enough
Standard national forecasts give a single number for the whole country (like "India will receive 98% of normal rain"). But that hides reality:
- An overall "normal" year can still have a **killing drought in Rajasthan** while **Assam is flooded**.
- Farmers and local governments don't farm in "all of India" - they farm in specific states and districts.

**RainRisk solves this.** It predicts whether each of India's **36 meteorological regions** will face drought, normal rain, or excess rain, and delivers that prediction **before June 1st**, right when farmers are choosing their seeds and local officials are planning water budgets.

---

## Problem Statement

### 1. The Real-World Challenge
Farmers need answers before June 1st. Once the rains start, it is too late to change seed varieties, dig farm ponds, or store emergency cattle feed. But predicting rainfall months in advance for 36 different regions across India is notoriously difficult.

### 2. Why Standard Machine Learning Fails
Off-the-shelf AI models fail at this problem for three main reasons:

1. **Standard AI Treats All Mistakes the Same (Symmetric Loss):**
   - If the model predicts **Normal** when the truth is **Deficient** (a small 1-step error), that is a minor mistake.
   - But if the model predicts **Flood / Excess** when the truth is **Severe Drought** (a 4-step error), that is disastrous. If farmers believe the forecast and plant thirsty crops like paddy during a drought, they face complete ruin.
   - Standard AI models punish both mistakes equally. RainRisk uses **ordinal classification** to heavily punish opposite-category errors while being forgiving of near misses.

2. **Most Years Are Normal (Class Imbalance):**
   - In India's 117-year record, about **63% of years had normal rainfall**. Severe droughts make up less than 1% of the record.
   - A lazy AI model can simply guess "Normal" every single time and look 63% accurate on paper. But that model is useless because it will **never warn anyone about an incoming drought**.

3. **Models Cannot Peek into the Future (Data Leakage):**
   - A prediction made before June 1st cannot use June, July, or August rainfall data.
   - Many published models accidentally cheat by using moving averages that leak future data or by shuffling years randomly during testing. RainRisk strictly uses only past data and tests on forward-moving chronological blocks.

### The Project Goal
> **Build an AI model that predicts regional rainfall categories for all 36 Indian regions using only information available before June 1st. The model must catch rare droughts, avoid dangerous opposite-category errors, and give actionable farming advice before sowing starts.**

---

## Results at a Glance

We evaluated our models on an untouched test set of the most recent historical years (**2011 to 2017, covering 243 regional observations**):

| Model | What It Uses | Exact Hit Rate | Balanced Score (Across All Classes) | Off-by-One Accuracy (Within 1 Class) | Average Error Distance | Training Time |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Random Forest (Best)** | **23 Features (Rain + Ocean)** | **56.0%** | **43.2%** | **93.0%** | **0.52 steps** | **1.7 sec** |
| Ordinal RF (Frank-Hall) | 23 Features (Rain + Ocean) | 50.2% | 41.0% | 92.2% | 0.59 steps | 4.8 sec |
| Gradient Boosting | 23 Features (Rain + Ocean) | 47.3% | 39.6% | 90.5% | 0.63 steps | 3.4 min |
| HistGradientBoosting | 23 Features (Rain + Ocean) | 45.7% | 39.8% | 92.6% | 0.62 steps | 3.4 sec |
| Support Vector Machine (SVM) | 23 Features (Rain + Ocean) | 43.6% | 38.7% | 88.5% | 0.70 steps | 2.5 sec |
| Logistic Regression | 23 Features (Rain + Ocean) | 35.4% | 35.6% | 83.1% | 0.84 steps | 0.7 sec |

### 3 Big Takeaways:
1. **93% Practical Reliability:** In 93 out of 100 predictions, the model gets either the exact category right or is off by just one neighboring level. It almost never mistakes a drought for a flood (distant errors occur in only **3.3% of tests**).
2. **Ocean Temperatures Made the Difference (+8.5% Boost):** Using only past rainfall data hit a wall at 34.7% balanced accuracy. When we added Pacific and Indian Ocean temperatures, accuracy on rare droughts and floods jumped by **8.5%** up to **43.2%**.
3. **Pacific Ocean Warming Rate is the #1 Clue:** How fast the Pacific Ocean warms up between winter and spring (the El Nino tendency) is the single most important signal for predicting India's upcoming monsoon.

---

## Visual Charts and Data

### 1. 117 Years of Indian Monsoon Rainfall (1901-2017)
![National Monsoon Trend](results/figures/01_national_jjas_trend.png)
*National June-to-September rainfall over 117 years. The dashed line shows the long-term average of 1,064 mm. You can clearly see major drought years like 1965, 1972, 1987, 2002, 2009, and 2014-2015.*

### 2. Confusion Matrix: Where Does the Model Make Mistakes?
![Confusion Matrix](results/figures/05_confusion_matrices.png)
*This grid shows true categories vs predicted categories. Normal rainfall is correctly identified 68% of the time. When the model misses a drought, it almost always calls it "Normal" (1 step off), never "Flood" or "Excess".*

### 3. Which Clues Matter Most?
![Feature Importance](results/figures/07_permutation_vs_impurity_importance.png)
*This chart shows what happens when you shuffle each feature. Shuffling Pacific ocean warming (`enso_tendency`) causes the biggest drop in accuracy, proving that global ocean temperatures drive the monsoon.*

### 4. Rainfall Differences Across India
![Subdivision Variability](results/figures/03_variability_by_subdivision.png)
*Dry regions like Western Rajasthan have very low rainfall but huge year-to-year swings (volatility > 35%). Wet regions like Coastal Karnataka have high rainfall and steady yearly patterns.*

---

## How the AI Works

### 1. The 6 Official IMD Categories
The India Meteorological Department classifies regional monsoon rain into 6 bands based on percentage departure from the 50-year average (LPA):

| Category | Departure Range | What It Means |
|---|---|---|
| **No Rainfall** | Exactly -100% | Zero rain recorded all season |
| **Large Deficient** | -99% to -60% | Severe drought emergency |
| **Deficient** | -59% to -20% | Moderate drought |
| **Normal** | -19% to +19% | Healthy, normal monsoon |
| **Excess** | +20% to +59% | Surplus monsoon |
| **Large Excess** | +60% and above | Flood risk |

### 2. Ordinal Classification (Frank & Hall Method)
Instead of guessing among 6 random classes, RainRisk breaks the problem into 5 cumulative questions:
1. Is it wetter than "No Rain"?
2. Is it wetter than "Large Deficient"?
3. Is it wetter than "Deficient"?
4. Is it wetter than "Normal"?
5. Is it wetter than "Excess"?

By subtracting the probabilities between neighbors, the model calculates the exact chance for each category. This guarantees that errors stay small and adjacent.

### 3. SMOTENC: Fair Training Without Fake Data
Because droughts are rare, we need to balance the training data. Standard balancing tools create fake numbers between points, which would create impossible nonsense like "40% Kerala and 60% Punjab". We used **SMOTENC**, which only picks real regional names when creating synthetic examples.

### 4. Time-Aware Validation
We never shuffle years randomly like standard machine learning tutorials. We train on earlier blocks of years (like 1901 to 1980) and test on later blocks of years (like 1981 to 2000), making sure the model never learns by looking into the future.

---

## 12 Mistakes We Caught and Fixed

We documented every bug and scientific risk we found during development:

| # | What Was Wrong | Why It Mattered | How We Fixed It |
|---|---|---|---|
| **1** | Standard SMOTE made fake regions | Created impossible blended regions | Switched to `SMOTENC` to keep regional names 100% real |
| **2** | Baseline used modern 50-year average | Pre-1971 years used a future reference point | Documented this clearly as retrospective classification |
| **3** | Missing "No Rain" category | Early schema had only 5 categories | Added the official 6th IMD category ("No Rain") |
| **4** | Guessed "No Rain" cutoff at -90% | Made-up cutoff was scientifically inaccurate | Found official IMD bulletin confirming it is strictly -100% |
| **5** | Redundant class weights | Setting `class_weight='balanced'` after SMOTENC did nothing | Proved mathematical redundancy across 4 folds and cleaned it up |
| **6** | Tuning on just one train/test split | Made hyperparameters unstable across decades | Switched to 4-fold forward-moving time-series cross-validation |
| **7** | Gini importance favored region names | Fooled us into thinking region names were the #1 factor | Used permutation importance to prove ocean data is the real driver |
| **8** | Missing years in island regions | Positional rolling averages quietly bridged across missing years | Put every region on an unbroken calendar grid so missing years show as NaNs |
| **9** | Unpinned library versions | Package updates broke model loading | Locked all versions in `requirements.txt` |
| **10** | Risk of bugs returning | Easy to accidentally reintroduce fixed bugs | Added `tests/test_regression_guards.py` to test all fixes automatically |
| **11** | Only 5 features used initially | Models did not know about winter/spring rain | Added 13 monthly and seasonal features (jumped from 48.4% to 52.7%) |
| **12** | Ignored ocean temperatures | Models missed global climate drivers | Added 5 Pacific and Indian Ocean features (jumped to 56.0%) |

---

## The 23 Clues the Model Uses

All 23 features use only data from **before June 1st**:

- **Group 1: Past Monsoon Rainfall (5 features):** Previous year's monsoon total, change from two years ago, 3-year moving average, 5-year moving average, and 5-year volatility.
- **Group 2: Monthly and Winter/Spring Rain (13 features):** Rainfall from individual months (June, July, August, September), winter rain (Jan-Feb), spring rain (Mar-May), post-monsoon rain (Oct-Dec), and how concentrated the rain was in peak months.
- **Group 3: Pacific & Indian Ocean Temperatures (5 features):**
  - `enso_djf_lag`: Winter Pacific Ocean temperature (El Nino status).
  - `enso_mam_signal`: Spring Pacific Ocean temperature.
  - `enso_tendency`: How fast the Pacific warmed up from winter to spring.
  - `iod_mam_lag`: Spring Indian Ocean Dipole temperature difference.
  - `enso_iod_interaction`: Combined interaction (a warm Indian Ocean can cancel out an El Nino drought).

---

## Actionable Farming Advice (ICAR Guidelines)

RainRisk translates predictions into concrete farming advice based on official Indian Council of Agricultural Research (ICAR) contingency plans:

| Prediction | Advisory Level | What Farmers and Officials Should Do |
|---|---|---|
| **Large Deficient / No Rain** | **Emergency** | Switch to short-duration pulses (moong / urad); ration reservoir water; prepare cattle fodder camps; fast-track crop insurance paperwork. |
| **Deficient** | **Warning** | Delay sowing by 10 to 14 days; plant in ridges and furrows to catch moisture; split fertilizer applications; prepare drip and sprinkler systems. |
| **Normal** | **Standard** | Proceed with standard full-scale planting of rice, cotton, and soybean; use standard fertilizer; capture excess rain in farm ponds. |
| **Excess / Large Excess** | **Surplus** | Clean field drainage ditches to stop waterlogging; watch out for fungal crop diseases; get ready for early winter (Rabi) sowing. |

---

## The Web Application

RainRisk includes an interactive web platform with **6 easy-to-use tabs**:

```
+-------------------------------------------------------------------------------+
|                            REACT 18 SINGLE-PAGE APP                           |
|  Executive Pulse | Geospatial Radar | Climate Cockpit | Regional Explorer ... |
+---------------------------------------+---------------------------------------+
                                        | Clean REST API Calls
                                        v
+-------------------------------------------------------------------------------+
|                             FASTAPI BACKEND SERVER                            |
|        /api/overview   |   /api/predict   |   /api/map   |   /api/subdivisions    |
+-------------------------------------------------------------------------------+
```

1. **Executive Pulse:** Quick summary of all-India risk and current ocean conditions.
2. **Geospatial Radar (Interactive Map):** Full map of India divided into 36 regions, color-coded by predicted category. Click any region to see its drought history and farming advice.
3. **Climate Cockpit (Simulation Sandbox):** Move sliders for Pacific and Indian Ocean temperatures to see how the forecast changes in real time.
4. **Regional Explorer:** Browse 117 years of rainfall history for any individual region.
5. **Model Leaderboard:** Transparent view comparing all candidate models and accuracy scores.
6. **Methodology:** Complete in-app guide explaining the science and research papers.

---

## Quickstart: How to Run It

### 1. Set Up the Project
```bash
# Clone the repository
git clone https://github.com/Rajratna-D/RainRisk.git
cd RainRisk

# Create a virtual environment
python -m venv .venv

# Activate it:
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Launch the Web App (One Command)
```bash
python run_webapp.py
```
This automatically starts the backend, serves the interactive website, and opens **http://localhost:8008** in your browser.

### 3. Run the Automated Tests
```bash
pytest tests
```
All **61 tests pass** across labeling, features, models, API endpoints, and regression guards.

---

## Project Structure

```
RainRisk/
├── backend/                  # FastAPI REST API Backend
│   ├── main.py               # Routes for predictions, maps, and historical data
│   └── __init__.py
│
├── frontend/                 # React 18 + Vite Web App
│   ├── src/                  # React components (map, sliders, charts)
│   ├── dist/                 # Pre-built bundle (runs without needing Node.js)
│   └── package.json
│
├── data/
│   ├── raw/                  # 117 years of IMD rainfall data (1901-2017)
│   ├── interim/              # Cleaned rainfall and ocean index data
│   └── processed/            # Final 23-feature training table
│
├── src/                      # Core Machine Learning Code
│   ├── labeling.py           # IMD rainfall category rules
│   ├── features.py           # 23-feature engineering without data leaks
│   ├── train.py              # Model pipelines and SMOTENC
│   ├── ordinal.py            # Frank-Hall ordinal classification code
│   ├── evaluate.py           # Accuracy and error distance metrics
│   ├── temporal_cv.py        # Time-aware cross-validation folds
│   ├── tune.py               # Time-series hyperparameter search
│   ├── advisory.py           # ICAR farming recommendations
│   └── save_model.py         # Trains and evaluates all models
│
├── tests/                    # 61 automated tests (100% passing)
├── results/
│   ├── figures/              # Generated charts and confusion matrices
│   └── model/                # Benchmark metric files
│
├── scripts/
│   └── fetch_teleconnections.py # Downloads NOAA and JAMSTEC ocean data
│
├── docs/                     # Full Technical Documentation & 22-Page PDF Report
├── requirements.txt          # Python dependencies
└── run_webapp.py             # One-click startup script
```

---

## Documentation Index

All technical documents are organized in `docs/`:

| Document | What It Covers |
|---|---|
| [RainRisk Project Report (PDF)](docs/RainRisk_Project_Report.pdf) | Complete 22-page publication-grade report with all figures and data tables |
| [RainRisk Project Report (Markdown)](docs/RainRisk_Project_Report.md) | Exhaustive 14,399-word technical report covering all 12 chapters |
| [01: System Architecture](docs/01_architecture.md) | Full system design, data flow, and why we replaced Streamlit with FastAPI |
| [02: Labeling Specification](docs/02_labeling_spec.md) | Official IMD departure formulas and category definitions |
| [03: Modeling Specification](docs/03_modeling_spec.md) | Chronological splits, model setups, and evaluation rules |
| [04: Literature Traceability](docs/04_lit_review_traceability.md) | Survey of 25 research papers and how they were used |
| [05: Methodology Audit Trail](docs/05_methodology_fixes.md) | In-depth story of all 12 bugs caught and fixed |
| [06: Dashboard Guide](docs/06_dashboard_user_guide_and_spec.md) | User manual for all 6 web app tabs |
| [07: Teleconnections Plan](docs/07_teleconnections_implementation_plan.md) | Details on El Nino and Indian Ocean Dipole feature extraction |
| [08: Ordinal Decomposition](docs/08_frank_hall_ordinal_decomposition.md) | Math and code for Frank and Hall ordinal classification |
| [09: Data Sources Catalog](docs/09_data_sources_catalog.md) | Links and citations for all raw data sources |

---

## Citation

If you use RainRisk in your research or project, please cite:

```bibtex
@software{rainrisk2026,
  author    = {Dhiwar, Rajratna},
  title     = {RainRisk: AI-Powered Monsoon Drought and Rainfall Prediction for India},
  year      = {2026},
  publisher = {GitHub},
  url       = {https://github.com/Rajratna-D/RainRisk}
}
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
