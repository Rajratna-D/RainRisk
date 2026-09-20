# RainRisk: Literature Review Traceability Matrix

This document maps all 25 research papers we surveyed directly to decisions in our code, our experimental setup, or our project scope. We built this matrix so that every paper in our literature review has a clear, practical purpose in the project rather than just sitting in a bibliography.

---

## Part 1: Indian Climatological Studies (Papers 1 to 13)

| # | Paper | Where and How We Used It |
|---|---|---|
| **1** | Pandey et al., Rainfall Forecast & Drought Analysis (LSTM + SPI) | **Scope Boundary:** We cited this as a deep learning sequence benchmark. We chose classical ML with engineered domain features instead because it is much more interpretable and faster to train. |
| **2** | Guhathakurta & Rajeevan (2008), Trends in Rainfall Across 36 Subdivisions | **Data Validation:** Used during early data exploration to verify that our historical 1901-2017 dataset accurately reproduced documented drying trends in Kerala, Jharkhand, and East MP. |
| **3** | Parthasarathy et al. (1994), All India Monthly/Seasonal Rainfall Series | **Spatial Unit Justification:** Justifies treating each of India's 36 meteorological subdivisions as consistent geographic units for regional policy planning. |
| **4** | Kumar et al. (2017), Mann-Kendall Trend Test, Gujarat | **Trend Check:** Methodological reference for evaluating non-parametric climate trends across semi-arid Indian subdivisions. |
| **5** | Pai et al. (2014), IMD High-Resolution Gridded Daily Rainfall Dataset | **Dataset Scope Choice:** Explains why we chose 36 official subdivisions over high-resolution gridded rasters to match operational IMD administrative alerts. |
| **6** | Guhathakurta et al. (2017), IMD Operational Rainfall Statistics | **Directly in Code (`src/labeling.py`):** The official source defining the 6 operational drought categories via percentage departure from the 1971-2020 LPA baseline. |
| **7** | Tamrakar et al. (2024), ML for Drought Forecasting, Bundelkhand | **Model Comparison:** Precedent for benchmarking Support Vector Machines directly against tree ensembles for regional rainfall tasks. |
| **8** | Dell'Acqua et al. (2025), Satellite Drought Detection | **Scope Boundary:** Cited as a remote sensing benchmark; our project focuses strictly on meteorological drought from weather and ocean signals. |
| **9** | Tandon et al. (2025), Efficacy of ML in Simulating Precipitation Extremes | **Performance Reference:** External comparison for Random Forest and Gradient Boosting accuracy on Indian rainfall records. |
| **10** | Naresh Kumar et al. (2009), SPI for Drought Intensity, Andhra Pradesh | **Index Comparison:** Context for understanding how Standardized Precipitation Index compares to percentage departure from normal. |
| **11** | Saha et al. (2021), Spatial Drought Vulnerability Index, Karnataka | **Scope Boundary:** Contrasts multi-criteria socioeconomic vulnerability maps with our pure meteorological hazard classification. |
| **12** | Singh et al. (2021), Drought Risk Assessment & Crop Yield | **Downstream Impact:** Connects rainfall deficits to agricultural crop yield shocks in Western Maharashtra, which guided our advisory rules. |
| **13** | Pandi et al. (2025), Multi-View Hierarchical Drought Severity, Tamil Nadu | **Architecture Reference:** Precedent for discrete multi-class drought severity tiers rather than simple binary wet/dry toggles. |

---

## Part 2: International Studies and Foundational ML Methods (Papers 14 to 19)

| # | Paper | Where and How We Used It |
|---|---|---|
| **14** | Hatami Bahman Beiglou et al. (2021), US Drought Monitor Classification | **Evaluation Framing:** Supported treating drought classification as an ordinal problem, directly justifying our Off-by-One Accuracy (+-1 class) metric. |
| **15** | Poudel et al. (2024), ANN vs SVM vs RF Comparison, Ohio Watershed | **Benchmark Methodology:** Guided our comparative setup testing linear, kernel, and tree models under identical cross-validation splits. |
| **16** | Gepreel (2025), ML Classification for Meteorological Drought, Pakistan | **Candidate Model Set:** Supported including Logistic Regression, SVM, Random Forest, and Gradient Boosting under tuned hyperparameters. |
| **17** | Melese et al. (2025), ML Drought Prediction with SMOTE, Ethiopia | **Imbalance Benchmark:** Demonstrated that tree ensembles consistently outperform linear baselines when oversampling minority drought classes. |
| **18** | Breiman (2001), Random Forest | **Directly in Code (`src/train.py`):** Foundational paper for our primary production classifier, out-of-bag validation, and feature importances. |
| **19** | Chawla et al. (2002), SMOTE and SMOTENC | **Directly in Code (`src/train.py`):** Foundation for using SMOTENC to oversample rare drought classes on raw categorical columns without creating fake fractional regions. |

---

## Part 3: Teleconnections, Ordinal Mechanics and Validation (Papers 20 to 25)

| # | Paper | Where and How We Used It |
|---|---|---|
| **20** | Ashok, Guan, & Yamagata (2001), Impact of IOD on ISMR-ENSO Relationship | **Directly in Code (`src/features.py`):** Proves a positive Indian Ocean Dipole can buffer against El Niño drought. Justified our `iod_mam_lag` and interaction features. |
| **21** | Kumar et al. (2006), Unraveling Indian Monsoon Failure During El Niño | **Directly in Code (`src/features.py`):** Proves Pacific ocean warming suppresses Indian monsoon air circulation, justifying our pre-monsoon Niño 3.4 features. |
| **22** | Saji et al. (1999), A Dipole Mode in the Tropical Indian Ocean | **Directly in Code (`src/features.py`):** The seminal paper defining the Dipole Mode Index (DMI), which we ingest directly from NOAA and JAMSTEC. |
| **23** | Frank & Hall (2001), A Simple Approach to Ordinal Classification | **Directly in Code (`src/ordinal.py`):** Decomposes the 6 severity tiers into cumulative binary threshold models to penalize distant prediction errors during training. |
| **24** | Bergmeir, Hyndman, & Koo (2018), Validity of Cross-Validation for Time Series | **Directly in Code (`src/temporal_cv.py`):** Shows that random K-fold cross-validation leaks time-series data, providing the mathematical reason for our expanding-window folds. |
| **25** | Hao & Singh (2015), Drought Characterization from a Multivariate Perspective | **Directly in Code (`src/features.py`):** Hydrological justification for our multi-year lag and rolling features (`rolling_3yr`, `rolling_5yr`, `cv_5yr`) to track multi-year dry spells. |

---

## Quick Summary

* **Directly Implemented in Our Code:** Papers 6, 18, 19, 20, 21, 22, 23, 24, and 25.
* **Informed Our Models and Evaluation Metrics:** Papers 7, 14, 15, 16, and 17.
* **Used to Check Trends During Data Exploration:** Papers 2, 3, 4, 10, and 12.
* **Defined Clear Boundaries for What We Did Not Build:** Papers 1, 5, 8, 9, 11, and 13.
