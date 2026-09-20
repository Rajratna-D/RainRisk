# RainRisk: Modeling and Evaluation Specification

## 1. Problem Formulation

Multi-class, **ordinal**, imbalanced classification. Given engineered spatiotemporal features for a (subdivision, year) observation, the model predicts the official IMD `drought_category` using only information available prior to the monsoon season (strictly zero future data leakage).

---

## 2. Chronological Split Strategy

We use a **chronological split**, never random shuffling. Because our features include multi-year moving averages and historical lags, random cross-validation would leak future rainfall numbers into the training set.

| Split Name | Historical Years | Purpose |
|---|---|---|
| **Train** | 1901 to 2000 | Core model fitting and pipeline transformations |
| **Validation** | 2001 to 2010 | Hyperparameter tuning and model selection |
| **Test** | 2011 to 2017 | Final evaluation on untouched historical records (N=243) |

---

## 3. Leakage Prevention Checklist

Every step in our pipeline is protected against data leakage:

* **Strict Temporal Shift:** Every lag and rolling feature uses `.shift(1)` before calculating rolling averages.
* **Fixed Climatological Baseline:** The 1971 to 2020 LPA is computed per subdivision once and applied as a fixed standard.
* **SMOTENC Purity:** `SMOTENC` is applied **only** on the training fold inside an `imblearn.pipeline.Pipeline`. It is never applied to the validation or test splits.
* **Categorical Integrity:** The categorical column (`SUBDIVISION`) is handled by `SMOTENC` using nearest-neighbor majority voting *before* one-hot encoding. This guarantees that synthetic samples are always 100% real geographical regions, never fractional blends like 0.4 Kerala and 0.6 Punjab.
* **Train-Only Scaling:** `StandardScaler` and `OneHotEncoder` calculate their parameters exclusively on the training fold.
* **Calendar-Gap Reindexing:** Each subdivision is reindexed onto an unbroken integer calendar grid before computing rolling statistics, preventing the code from bridging across missing historical years in island and mountain subdivisions.

---

## 4. Models Evaluated and Compared

1. **Logistic Regression:** Linear multi-class baseline with L2 regularization.
2. **Random Forest:** Ensemble bagging baseline; provides impurity and permutation feature importances.
3. **Support Vector Machine (SVM):** Support Vector Classifier with a Radial Basis Function (RBF) kernel.
4. **Gradient Boosting:** Sequential gradient-boosted decision tree classifier.
5. **HistGradientBoosting:** Histogram-binned gradient boosting that natively handles missing values and provides fast multi-class training.
6. **Frank and Hall (2001) Ordinal Classifiers:** Cumulative threshold meta-estimators that decompose the 6-class problem into cumulative binary models (`src/ordinal.py`).

---

## 5. Comprehensive Benchmark Results (Three-Tier Feature Ablation)

Evaluated on the held-out historical test set (2011 to 2017, N=243 observations across India's 36 subdivisions):

| Model Algorithm | Feature Set | Test Accuracy | Balanced Accuracy | Macro-F1 | Off-by-One Accuracy (+-1 Class) | Mean Ordinal Distance | Training Time |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **RandomForest** *(Active Best)* | **Teleconnections (23 features)** | **56.0%** | **43.2%** | **0.261** | **93.0%** | **0.52** | **1.68s** |
| RandomForest | Enhanced Rainfall (18 features) | 52.7% | 34.7% | 0.213 | 91.4% | 0.58 | 1.30s |
| RandomForest | Baseline (5 features) | 48.4% | 34.4% | 0.215 | 87.5% | 0.67 | 0.85s |
| **GradientBoosting** | **Teleconnections (23 features)** | **47.3%** | **39.6%** | **0.230** | **90.5%** | **0.63** | **203.0s** |
| GradientBoosting | Enhanced Rainfall (18 features) | 46.5% | 33.6% | 0.205 | 91.4% | 0.64 | 169.25s |
| GradientBoosting | Baseline (5 features) | 45.6% | 32.4% | 0.202 | 86.7% | 0.71 | 56.22s |
| **SVM** | **Teleconnections (23 features)** | **43.6%** | **38.7%** | **0.218** | **88.5%** | **0.70** | **2.50s** |
| SVM | Baseline (5 features) | 38.7% | 31.0% | 0.197 | 78.2% | 0.89 | 2.59s |
| SVM | Enhanced Rainfall (18 features) | 35.4% | 29.1% | 0.179 | 77.8% | 0.90 | 2.55s |
| **HistGradientBoosting** | **Teleconnections (23 features)** | **42.0%** | **38.9%** | **0.214** | **90.5%** | **0.69** | **3.36s** |
| HistGradientBoosting | Enhanced Rainfall (18 features) | 51.0% | 37.4% | 0.225 | 89.7% | 0.60 | 2.87s |
| HistGradientBoosting | Baseline (5 features) | 42.7% | 32.0% | 0.197 | 86.7% | 0.73 | 3.54s |
| **LogisticRegression** | **Teleconnections (23 features)** | **33.7%** | **34.0%** | **0.194** | **83.1%** | **0.86** | **0.74s** |
| LogisticRegression | Enhanced Rainfall (18 features) | 34.2% | 28.9% | 0.182 | 76.5% | 0.94 | 0.70s |
| LogisticRegression | Baseline (5 features) | 33.1% | 25.7% | 0.165 | 75.0% | 0.98 | 0.43s |

---

## 6. Ordinal Evaluation Metrics

Because drought categories have an inherent ordering (Normal is closer to Deficient than it is to Large Excess), standard raw accuracy does not tell the full story. We evaluate models using two key ordinal metrics:

```python
CATEGORY_ORDER = ["No Rainfall", "Large Deficient", "Deficient", "Normal", "Excess", "Large Excess"]

def ordinal_distance(y_true, y_pred, order=CATEGORY_ORDER):
    idx = {cat: i for i, cat in enumerate(order)}
    return abs(idx[y_true] - idx[y_pred])

def off_by_one_accuracy(y_true_list, y_pred_list):
    distances = [ordinal_distance(t, p) for t, p in zip(y_true_list, y_pred_list)]
    return sum(d <= 1 for d in distances) / len(distances)
```

* **Off-by-One Accuracy:** The percentage of predictions where the error is at most one category step ($|y_{\text{true}} - y_{\text{pred}}| \le 1$). Random Forest with teleconnections achieves **93.0%**.
* **Mean Ordinal Distance:** The average category step difference across all predictions. Random Forest achieves **0.523**, meaning that more than 9 out of 10 times, the model predicts the exact or immediately neighboring category.
