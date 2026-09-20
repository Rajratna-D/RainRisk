"""
Regression guard tests. These exist specifically to catch a future edit
silently undoing one of the verified, evidence-based fixes made in this
project, e.g. someone "helpfully" re-adding class_weight='balanced'
without re-running the ablation that showed it's redundant, or the category
list drifting out of sync between src/labeling.py and src/evaluate.py.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import inspect
from train import get_models
from labeling import CATEGORY_ORDER as LABELING_CATEGORY_ORDER
from evaluate import CATEGORY_ORDER as EVALUATE_CATEGORY_ORDER


def test_class_weight_not_silently_reintroduced():
    """
    An explicit ablation (results/model/imbalance_strategy_comparison*.json)
    showed class_weight='balanced' has ZERO effect once SMOTENC has already
    balanced the training data (confirmed byte-identical predictions
    across every fold, every model. get_models() deliberately does NOT set
    class_weight for this reason.

    If a future edit re-adds class_weight='balanced' to any model without
    updating this test AND re-running/re-documenting the ablation, this
    test fails loudly rather than letting the redundancy silently return
    without anyone re-verifying it's still redundant (e.g. after a
    pipeline change that might make it NOT redundant anymore).
    """
    models = get_models()
    for name, model in models.items():
        cw = getattr(model, "class_weight", "NOT_APPLICABLE")
        assert cw in (None, "NOT_APPLICABLE"), (
            f"{name} has class_weight={cw!r}. If this is intentional, "
            f"re-run the imbalance-strategy ablation (see "
            f"docs/05_methodology_fixes.md Fix 5) to confirm it's not "
            f"redundant with SMOTENC before updating this test."
        )


def test_category_order_consistent_across_modules():
    """
    labeling.py and evaluate.py each define their own CATEGORY_ORDER
    (evaluate.py cannot import labeling.py's without creating a circular
    dependency risk in some usage patterns, so they're kept independent by
    design). This test guards against them silently drifting out of sync, e.g. someone adding a 7th category in one file and forgetting the other.
    """
    assert LABELING_CATEGORY_ORDER == EVALUATE_CATEGORY_ORDER, (
        f"CATEGORY_ORDER mismatch: labeling.py has {LABELING_CATEGORY_ORDER}, "
        f"evaluate.py has {EVALUATE_CATEGORY_ORDER}. These must be updated "
        f"together."
    )


def test_category_order_has_six_categories():
    """Guards against silently reverting to the pre-fix 5-category scheme
    (missing 'No Rainfall') without deliberately deciding to do so."""
    assert len(LABELING_CATEGORY_ORDER) == 6, (
        f"Expected 6 categories (including 'No Rainfall'), got "
        f"{len(LABELING_CATEGORY_ORDER)}: {LABELING_CATEGORY_ORDER}"
    )
    assert "No Rainfall" in LABELING_CATEGORY_ORDER


def test_smotenc_used_not_plain_smote():
    """
    Guards against silently reverting src/train.py to plain SMOTE (which
    caused the fractional-subdivision bug fixed in this project). Checks
    the actual pipeline's step name/class, not just an assumption.
    """
    from train import build_pipeline
    pipe = build_pipeline(get_models()["RandomForest"])
    step_names = [name for name, _ in pipe.steps]
    assert "smotenc" in step_names, (
        f"Expected a 'smotenc' step in the pipeline, found steps: {step_names}. "
        f"Plain SMOTE on one-hot-encoded categorical data was a confirmed bug "
        f"(see docs/05_methodology_fixes.md Fix 1); do not reintroduce it."
    )
    smotenc_step = pipe.named_steps["smotenc"]
    assert type(smotenc_step).__name__ == "SMOTENC", (
        f"Expected SMOTENC, found {type(smotenc_step).__name__}"
    )


def test_final_test_years_never_used_in_tuning_module_by_default():
    """
    src/tune.py's tune_model() takes a df parameter with no built-in
    restriction to train/val years; the caller is responsible for never
    passing the final test set. This test at least confirms the function
    signature still requires an explicit df/folds argument (i.e. it cannot
    silently default to "all data including test"), as a weak but real
    guard against a future refactor accidentally adding such a default.
    """
    from tune import tune_model
    sig = inspect.signature(tune_model)
    assert sig.parameters["df"].default is inspect.Parameter.empty, (
        "tune_model()'s df parameter must not have a default value, "
        "the caller must always explicitly pass the train/val-only "
        "DataFrame, never implicitly fall back to a dataset that could "
        "include the final held-out test set."
    )


def test_teleconnection_features_count_guard():
    """
    Guards against silently dropping teleconnection features (ENSO & IOD)
    or drifting feature counts. The active model must use 23 numeric features
    (18 rainfall + 5 teleconnections) and 1 categorical feature (24 total).
    """
    from train import (TELECONNECTION_FEATURES, NUMERIC_FEATURES,
                       ENHANCED_NUMERIC_FEATURES, ALL_FEATURES)
    assert len(TELECONNECTION_FEATURES) == 5, f"Expected 5 teleconnection features, got {len(TELECONNECTION_FEATURES)}"
    assert len(NUMERIC_FEATURES) == 23, f"Expected 23 numeric features, got {len(NUMERIC_FEATURES)}"
    assert len(ALL_FEATURES) == 24, f"Expected 24 total features, got {len(ALL_FEATURES)}"
    for f in TELECONNECTION_FEATURES:
        assert f in NUMERIC_FEATURES, f"Missing {f} in active NUMERIC_FEATURES"


if __name__ == "__main__":
    test_fns = [obj for name, obj in list(globals().items())
                if name.startswith("test_") and inspect.isfunction(obj)]
    passed, failed = 0, 0
    for fn in test_fns:
        try:
            fn()
            print(f"PASS: {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(test_fns)} tests")
    if failed > 0:
        sys.exit(1)
