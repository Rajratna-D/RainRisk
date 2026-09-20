"""
RainRisk: Model training and pipeline assembly.

Pipeline order uses SMOTENC before OneHotEncoder so synthetic samples are generated
using nearest-neighbor voting on raw categorical identifiers, preventing impossible
fractional category interpolations.
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

ORIGINAL_NUMERIC_FEATURES = [
    "prev_year_jjas", "prev_annual_change",
    "rolling_3yr_jjas", "rolling_5yr_jjas", "cv_5yr_jjas"
]

ENHANCED_NUMERIC_FEATURES = ORIGINAL_NUMERIC_FEATURES + [
    "prev_jun", "prev_jul", "prev_aug", "prev_sep",
    "prev_jf", "prev_mam", "prev_ond",
    "prev_annual", "rolling_3yr_annual", "rolling_5yr_annual",
    "monsoon_concentration", "jjas_to_annual_ratio", "prev_premonsoon_signal",
]

TELECONNECTION_NUMERIC_FEATURES = ENHANCED_NUMERIC_FEATURES + TELECONNECTION_FEATURES

CATEGORICAL_FEATURES = ["SUBDIVISION"]

NUMERIC_FEATURES = TELECONNECTION_NUMERIC_FEATURES
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

ORIGINAL_ALL_FEATURES = ORIGINAL_NUMERIC_FEATURES + CATEGORICAL_FEATURES
ENHANCED_ALL_FEATURES = ENHANCED_NUMERIC_FEATURES + CATEGORICAL_FEATURES
TELECONNECTION_ALL_FEATURES = TELECONNECTION_NUMERIC_FEATURES + CATEGORICAL_FEATURES

# SMOTENC requires positional indices of categorical columns in the un-encoded feature matrix
CATEGORICAL_FEATURE_INDICES = [ALL_FEATURES.index(c) for c in CATEGORICAL_FEATURES]


def build_postprocessor(numeric_features=None):
    """
    Standardizes continuous features and one-hot encodes categorical subdivisions.
    sparse_output=False ensures compatibility with estimators requiring dense arrays.
    """
    if numeric_features is None:
        numeric_features = NUMERIC_FEATURES
    return ColumnTransformer([
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
    ])


def build_pipeline(model, smote_k_neighbors=5, numeric_features=None,
                   all_features=None):
    """
    Builds imbalanced-learn pipeline:
      1. SMOTENC on raw continuous and categorical features (training folds only)
      2. Postprocessing (StandardScaler + OneHotEncoder)
      3. Classifier
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
    Candidate model zoo.
    class_weight is omitted as SMOTENC already balances class distributions in training folds.
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
    return {
        "OrdinalRandomForest": FrankHallClassifier(
            base_estimator=RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_split=5, random_state=42, n_jobs=-1)
        ),
        "OrdinalLogisticRegression": FrankHallClassifier(
            base_estimator=LogisticRegression(max_iter=2000, random_state=42)
        ),
    }
