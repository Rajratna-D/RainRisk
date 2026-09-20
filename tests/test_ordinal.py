"""
Unit tests for Frank & Hall (2001) Ordinal Classification Decomposition.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from ordinal import FrankHallClassifier, DEFAULT_CATEGORY_ORDER


def test_frank_hall_sklearn_clone():
    """Confirms FrankHallClassifier implements standard scikit-learn cloning interface."""
    base = LogisticRegression(max_iter=100)
    fh = FrankHallClassifier(base_estimator=base)
    fh_cloned = clone(fh)
    assert fh_cloned.base_estimator.max_iter == 100


def test_frank_hall_probabilities_sum_to_one():
    """All predicted probability distributions must sum to 1.0 and remain non-negative."""
    np.random.seed(42)
    X = np.random.randn(60, 4)
    # 4 ordered classes
    classes = ["Large Deficient", "Deficient", "Normal", "Excess"]
    y = np.random.choice(classes, size=60)

    clf = FrankHallClassifier(base_estimator=LogisticRegression(max_iter=200), category_order=classes)
    clf.fit(X, y)

    probs = clf.predict_proba(X)
    assert probs.shape == (60, 4)
    assert np.all(probs >= 0.0), "Found negative probabilities"
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-6), "Probabilities do not sum to 1.0"


def test_frank_hall_monotonic_toy_ordering():
    """
    On a clear 1D ordinal step function (X < 1 -> Class 0, 1 <= X < 2 -> Class 1, X >= 2 -> Class 2),
    FrankHallClassifier must learn the correct monotonic sequence.
    """
    X = np.array([[-2.0], [-1.5], [-1.0], [0.0], [0.5], [1.0], [1.5], [2.0], [2.5], [3.0]])
    y = np.array(["Deficient", "Deficient", "Deficient",
                  "Normal", "Normal", "Normal", "Normal",
                  "Excess", "Excess", "Excess"])
    order = ["Deficient", "Normal", "Excess"]

    clf = FrankHallClassifier(base_estimator=LogisticRegression(C=10.0), category_order=order)
    clf.fit(X, y)

    # Test extreme negative point -> Deficient
    assert clf.predict(np.array([[-5.0]]))[0] == "Deficient"
    # Test extreme positive point -> Excess
    assert clf.predict(np.array([[+5.0]]))[0] == "Excess"


def test_frank_hall_expected_rank_bounds():
    """Expected rank must strictly lie within [0, K-1]."""
    np.random.seed(42)
    X = np.random.randn(30, 3)
    order = ["Large Deficient", "Deficient", "Normal", "Excess", "Large Excess"]
    y = np.random.choice(order, size=30)

    clf = FrankHallClassifier(base_estimator=RandomForestClassifier(n_estimators=10, random_state=42),
                              category_order=order)
    clf.fit(X, y)

    exp_ranks = clf.predict_expected_rank(X)
    assert len(exp_ranks) == 30
    assert np.all(exp_ranks >= 0.0)
    assert np.all(exp_ranks <= len(order) - 1.0 + 1e-6)


def test_get_models_with_ordinal_integration():
    """Confirms get_models(include_ordinal=True) integrates FrankHall models into the training catalog."""
    from train import get_models, get_ordinal_models
    std_models = get_models(include_ordinal=False)
    ord_models = get_ordinal_models()
    all_models = get_models(include_ordinal=True)

    assert len(std_models) == 5
    assert len(ord_models) == 2
    assert len(all_models) == 7
    assert "OrdinalRandomForest" in all_models
    assert "OrdinalLogisticRegression" in all_models



if __name__ == "__main__":
    import inspect
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
