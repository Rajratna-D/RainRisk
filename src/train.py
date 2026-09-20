"""
RainRisk: training (ENHANCED). SMOTE is fit ONLY on the training fold
via imblearn.pipeline.Pipeline (not sklearn's own Pipeline) so it is never
fit on validation/test data.

METHODOLOGY FIX (SMOTE + categorical leakage): the original version applied
standard SMOTE AFTER one-hot encoding SUBDIVISION. Standard SMOTE interpolates
linearly between feature vectors of nearest neighbors, when applied to
one-hot columns, this can produce synthetic rows with fractional/impossible
category memberships (e.g. SUBDIVISION_Kerala=0.4, SUBDIVISION_Punjab=0.6),
which does not correspond to any real geographic subdivision.

Fix: use SMOTENC (SMOTE for Nominal and Continuous features), which is
designed specifically for mixed numeric/categorical data. It resamples
numeric features by interpolation as usual, but assigns the categorical
value of a synthetic sample by majority vote among the nearest neighbors
used to generate it, so SUBDIVISION is always one real, existing
subdivision, never a fractional blend. This requires SMOTENC to run on the
RAW categorical column (before one-hot encoding), so the pipeline order is:
  1. SMOTENC on [numeric columns + raw SUBDIVISION column] (train fold only)
  2. THEN encode: StandardScaler on numeric, OneHotEncoder on SUBDIVISION
This is the opposite order from the original pipeline (which encoded first,
then oversampled), and is the methodologically correct order for mixed data.

ENHANCEMENT: expanded numeric features from 5 (JJAS-only) to 18 (monthly +
seasonal + derived), and added GradientBoosting + HistGradientBoosting to
the model comparison.
"""
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTENC
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (RandomForestClassifier,
                               GradientBoostingClassifier,
                               HistGradientBoostingClassifier)
from sklearn.svm import SVC
from ordinal import FrankHallClassifier
from features import TELECONNECTION_FEATURES

# --- Original features (5, JJAS-only) ---
ORIGINAL_NUMERIC_FEATURES = [
    "prev_year_jjas", "prev_annual_change",
    "rolling_3yr_jjas", "rolling_5yr_jjas", "cv_5yr_jjas"
]

# --- Enhanced features (original + monthly + seasonal + derived) ---
ENHANCED_NUMERIC_FEATURES = ORIGINAL_NUMERIC_FEATURES + [
    # Individual monsoon month lags
    "prev_jun", "prev_jul", "prev_aug", "prev_sep",
    # Seasonal lags
    "prev_jf", "prev_mam", "prev_ond",
    # Annual lag and rolling
    "prev_annual", "rolling_3yr_annual", "rolling_5yr_annual",
    # Derived ratios
    "monsoon_concentration", "jjas_to_annual_ratio", "prev_premonsoon_signal",
]

# --- Teleconnection features imported from features.py ---
# (TELECONNECTION_FEATURES is imported at the top of this file)

# Teleconnections + enhanced features (23 numeric features total)
TELECONNECTION_NUMERIC_FEATURES = ENHANCED_NUMERIC_FEATURES + TELECONNECTION_FEATURES

CATEGORICAL_FEATURES = ["SUBDIVISION"]

# Use teleconnection-enhanced features by default (23 numeric + 1 categorical = 24 features)
NUMERIC_FEATURES = TELECONNECTION_NUMERIC_FEATURES
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Backward-compatible feature sets for rigorous ablation comparison
ORIGINAL_ALL_FEATURES = ORIGINAL_NUMERIC_FEATURES + CATEGORICAL_FEATURES
ENHANCED_ALL_FEATURES = ENHANCED_NUMERIC_FEATURES + CATEGORICAL_FEATURES
TELECONNECTION_ALL_FEATURES = TELECONNECTION_NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Index of the categorical column(s) WITHIN ALL_FEATURES (i.e. within the
# raw X passed to SMOTENC, before any encoding). SMOTENC needs this to know
# which columns to treat categorically vs numerically.
CATEGORICAL_FEATURE_INDICES = [ALL_FEATURES.index(c) for c in CATEGORICAL_FEATURES]


def build_postprocessor(numeric_features=None):
    """Encoding step applied AFTER SMOTENC has already resampled the raw
    (numeric + categorical) data. Operates on the same ALL_FEATURES column
    order that SMOTENC output preserves.
    
    sparse_output=False ensures compatibility with all classifiers including
    HistGradientBoostingClassifier which cannot handle sparse matrices."""
    if numeric_features is None:
        numeric_features = NUMERIC_FEATURES
    return ColumnTransformer([
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
    ])


def build_pipeline(model, smote_k_neighbors=5, numeric_features=None,
                   all_features=None):
    """
    Pipeline order (methodologically corrected):
      1. SMOTENC: resamples raw numeric+categorical data (train fold only,
         fit only ever called with training data since this sits inside a
         Pipeline whose .fit() is only ever invoked on X_train/y_train).
         Categorical column assigned by majority vote -> always a real
         subdivision, never a fractional blend.
      2. ColumnTransformer: scales numeric columns, one-hot encodes the
         (now-resampled, still-real) SUBDIVISION column.
      3. Classifier.
    """
    if all_features is None:
        all_features = ALL_FEATURES
    if numeric_features is None:
        numeric_features = NUMERIC_FEATURES

    cat_indices = [all_features.index(c) for c in CATEGORICAL_FEATURES]

    return ImbPipeline([
        ("smotenc", SMOTENC(categorical_features=cat_indices,
                             random_state=42, k_neighbors=smote_k_neighbors)),
        ("postprocess", build_postprocessor(numeric_features)),
        ("clf", model),
    ])


def get_models(include_ordinal=False):
    """
    NOTE on class_weight: an explicit ablation (see
    results/model/imbalance_strategy_comparison_all_models.json and
    docs/05_methodology_fixes.md Fix 5) showed that class_weight='balanced'
    has ZERO additional effect once SMOTENC has already balanced the
    training data; 'smotenc_only' and 'both' produce byte-identical
    predictions across every CV fold, for all three models. This makes
    sense: class_weight is computed from the (now-balanced) resampled
    class counts, which come out close to equal, so the weighting term
    becomes a near-no-op. class_weight='balanced' is therefore NOT set
    here: SMOTENC alone is used, based on evidence, not assumption.

    ENHANCEMENT: added GradientBoosting and HistGradientBoosting (sklearn's
    native gradient boosting implementations) for broader model comparison.
    HistGradientBoosting natively handles NaN and is faster on larger data.
    """
    models = {
        "LogisticRegression": LogisticRegression(max_iter=2000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
        "SVM": SVC(kernel="rbf", random_state=42, probability=False),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=300, max_depth=5, learning_rate=0.1, random_state=42
        ),
    }
    if include_ordinal:
        models.update(get_ordinal_models())
    return models


def get_ordinal_models():
    """Returns Frank & Hall (2001) ordinal decomposition variants."""
    return {
        "OrdinalRandomForest": FrankHallClassifier(
            base_estimator=RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_split=5, random_state=42, n_jobs=-1)
        ),
        "OrdinalLogisticRegression": FrankHallClassifier(
            base_estimator=LogisticRegression(max_iter=2000, random_state=42)
        ),
    }

