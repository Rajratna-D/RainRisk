# RainRisk: The Methodology Audit Trail (12 Key Corrections)

This document is an honest engineering journal of the technical bugs, leakage risks, and methodological mistakes we caught and fixed during the development of RainRisk.

In academic and industry projects, people often hide when their accuracy drops. Here, we document every bug openly. In several cases, fixing a bug caused our reported accuracy to go down. We treat that as proof that the fix worked: the earlier higher number was measuring a bug, not real predictive skill.

---

## 1. Fixing the SMOTE Synthetic Region Leakage Bug

* **The Problem We Found:**
  In early versions of our training pipeline, we one-hot encoded the `SUBDIVISION` column *before* applying SMOTE oversampling. Standard SMOTE creates synthetic samples by drawing straight lines between nearest points in feature space. When applied to 0 and 1 columns, it created synthetic rows with numbers like `SUBDIVISION_Kerala = 0.4` and `SUBDIVISION_Punjab = 0.6`. This is a physical impossibility. A tree model could easily exploit these artificial fractional patterns.
* **How We Fixed It:**
  We switched to `SMOTENC` (SMOTE for Nominal and Continuous features). It interpolates continuous numbers (rainfall) while assigning the categorical label (`SUBDIVISION`) through nearest-neighbor majority voting. Every synthetic sample is guaranteed to be a 100% real Indian subdivision.
* **The Honest Result:**
  Random Forest test accuracy dropped from an artificial **49.8% to 44.4%**. We documented this drop rather than hiding it. The higher number was an artifact of the leakage bug.

---

## 2. Clarifying the Climatological Baseline (LPA)

* **The Problem We Found:**
  The IMD Long Period Average (LPA) baseline is calculated using the 1971 to 2020 window. Applying this fixed baseline to early historical years (like 1920) means the target label was built using numbers from 50 to 100 years into the future.
* **How We Clarified It:**
  The features themselves (the model inputs) use strictly prior-year data with zero leakage. However, because the target label uses the modern 1971-2020 baseline, our task is formally **retrospective climate anomaly classification** (evaluating past years relative to today's normal), not real-time forecasting. We updated our docstrings and documentation so we never make false claims.

---

## 3. Adding the Official 6th IMD Category ("No Rainfall")

* **The Problem We Found:**
  Early versions of this project only used 5 categories (*Large Deficient, Deficient, Normal, Excess, Large Excess*). However, official IMD statistics explicitly list 6 categories, including "No Rainfall".
* **How We Fixed It:**
  We updated `src/labeling.py` and `src/evaluate.py` to include "No Rainfall" in our `CATEGORY_ORDER` array.
* **The Honest Result:**
  In our 117-year historical dataset, no subdivision has ever recorded a seasonal monsoon departure below -82.67%. Therefore, zero historical rows changed labels, but our code now matches official IMD standards.

---

## 4. Confirming the Exact -100% "No Rainfall" Boundary

* **The Problem We Found:**
  When we first added "No Rainfall", we used an estimated -90% cutoff as an unverified placeholder.
* **How We Fixed It:**
  We obtained an official primary source document directly from the IMD Hydromet Division in New Delhi ("District Rainfall Distribution" bulletin). Its official legend explicitly states:
  * "No Rain" is the single exact value of **-100% departure** (zero recorded rain).
  * The entire range from **-99% down to -60%** belongs to "Large Deficient".
  We updated `NO_RAINFALL_THRESHOLD = -100.0` in `src/labeling.py` and saved the source PDF permanently in `docs/sources/`.

---

## 5. Proving Class Weights Were Redundant with SMOTENC

* **The Problem We Found:**
  We were using both `SMOTENC` oversampling and `class_weight='balanced'` in our classifiers without checking if using both actually helped.
* **How We Fixed It:**
  We ran a controlled 4-fold experiment testing all four combinations: none, class weights only, SMOTENC only, and both together.
* **The Finding:**
  `SMOTENC only` and `both` produced **byte-identical predictions across every fold for every model**. Once SMOTENC equalizes class frequencies, `class_weight='balanced'` becomes a mathematical no-op. We removed `class_weight` to keep the code clean and verified.

---

## 6. Time-Series Hyperparameter Tuning with Expanding Windows

* **The Problem We Found:**
  Early hyperparameter tuning used a single train/validation split, which was fragile and only tuned Random Forest.
* **How We Fixed It:**
  We wrote `src/tune.py` to convert our expanding-window folds into scikit-learn compatible index pairs. This enabled genuine 4-fold time-series `GridSearchCV` across all candidate models, strictly ensuring the final test set (2011 to 2017) was never touched during parameter tuning.

---

## 7. Exposing Gini Impurity Bias with Permutation Importance

* **The Problem We Found:**
  Random Forest's built-in feature importance (Mean Decrease in Impurity) ranked `rolling_3yr_jjas` as the top feature and highlighted individual subdivision flags. However, Gini impurity is known to artificially favor high-cardinality categorical features.
* **How We Fixed It:**
  We added held-out **Permutation Feature Importance** (20 repeats scored by balanced accuracy). Permutation importance revealed that individual subdivision flags were within noise of zero. The true predictive weight belonged to broad regional and pre-monsoon signals.

---

## 8. Fixing Hidden Calendar Gaps in Island Subdivisions

* **The Problem We Found:**
  Three subdivisions (Andaman and Nicobar Islands, Arunachal Pradesh, and Lakshadweep) have genuine missing years in IMD archives. Standard pandas `.rolling(3)` operated on row positions, meaning it silently averaged years 2000, 2001, and 2003 as if they were consecutive, skipping the missing year 2002.
* **How We Fixed It:**
  In `src/features.py`, we reindex each subdivision onto a continuous integer calendar range from 1901 to 2017. Missing years become explicit empty rows. Any rolling window touching a missing year correctly produces a NaN instead of a corrupt average.
* **The Result:**
  Usable training rows shifted from 3,960 to 3,952. Random Forest accuracy adjusted from 43.0% to 42.0%, representing the clean removal of an unhandled edge case.

---

## 9. Pinning Exact Package Versions

* **The Problem We Found:**
  The original `requirements.txt` used loose `>=` version bounds, which can cause subtle dependency breaks when libraries update.
* **How We Fixed It:**
  We pinned all packages to the exact tested versions and verified that the entire repository installs and runs in a completely fresh virtual environment.

---

## 10. Adding Regression Guard Tests

* **The Problem We Found:**
  Without automated regression tests, future code edits could accidentally bring back old bugs (like re-adding redundant class weights or drifting category names).
* **How We Fixed It:**
  We created `tests/test_regression_guards.py`. It inspects pipeline steps directly and fails loudly if redundant parameters return or if category arrays drift between modules.

---

## 11. Expanding Features from 5 to 18

* **The Problem We Found:**
  The baseline model used only 5 features derived entirely from total monsoon rain (JJAS). The raw IMD dataset contained 14 unused columns, including monthly rainfall and seasonal totals.
* **How We Fixed It:**
  We engineered 13 new prior-calendar features: individual monsoon month lags (June to September), seasonal lags (winter JF, spring MAM, post-monsoon OND), annual rolling totals, and the monsoon concentration ratio.
* **The Result:**
  Random Forest test accuracy jumped from **48.4% to 52.7%**, and balanced accuracy improved from **34.4% to 34.7%**.

---

## 12. Ingesting Planetary Ocean Teleconnections (ENSO & IOD)

* **The Problem We Found:**
  Past local rainfall alone hit a firm ceiling at ~52.7% accuracy because local memory decays over multi-year cycles. The Indian monsoon is physically driven by global ocean temperatures.
* **How We Fixed It:**
  We ingested continuous monthly records (1870 to present) from NOAA PSL and JAMSTEC for Niño 3.4 SST and the Indian Ocean Dipole. We extracted 5 pre-monsoon features strictly before June 1st (winter lag, spring signal, warming tendency, dipole index, and their product interaction).
* **The Empirical Result:**
  * Exact Test Accuracy reached **56.0%** (a 7.6% gain over baseline).
  * Balanced Accuracy jumped to **43.2%** (an 8.8% gain over baseline).
  * Off-by-One Accuracy reached **93.0%**.
  * Mean Ordinal Distance dropped to **0.523** (a 22.4% error reduction).
