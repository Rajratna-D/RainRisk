"""
Unit tests for src/labeling.py: written BEFORE running classify() on the
full dataset, per project verification policy.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from labeling import classify, compute_pct_departure


def test_well_within_normal():
    assert classify(0) == "Normal"
    assert classify(10) == "Normal"
    assert classify(-10) == "Normal"


def test_well_within_deficient():
    assert classify(-30) == "Deficient"
    assert classify(-59) == "Deficient"


def test_well_within_large_deficient():
    assert classify(-70) == "Large Deficient"
    assert classify(-80) == "Large Deficient"


def test_well_within_no_rainfall():
    assert classify(-100) == "No Rainfall"


def test_well_within_excess():
    assert classify(30) == "Excess"
    assert classify(59) == "Excess"


def test_well_within_large_excess():
    assert classify(70) == "Large Excess"
    assert classify(200) == "Large Excess"


def test_boundary_normal_deficient():
    # -20 is the boundary: spec says -20 < x <= 19 is Normal, so -20 itself -> Deficient
    assert classify(-20) == "Deficient"
    assert classify(-19.99) == "Normal"
    assert classify(-19) == "Normal"


def test_boundary_normal_excess():
    # 19 is the boundary: -20 < x <= 19 is Normal, so 19 itself -> Normal, 19.01 -> Excess
    assert classify(19) == "Normal"
    assert classify(19.01) == "Excess"
    assert classify(20) == "Excess"


def test_boundary_deficient_large_deficient():
    # -60 is the boundary: -60 < x <= -20 is Deficient, so -60 itself -> Large Deficient
    assert classify(-60) == "Large Deficient"
    assert classify(-59.99) == "Deficient"


def test_boundary_large_deficient_no_rainfall():
    # CONFIRMED against IMD's own legend: No Rain is the exact value -100%,
    # not a range. Everything from -99% to -60% is Large Deficient.
    assert classify(-100) == "No Rainfall"
    assert classify(-99.99) == "Large Deficient"
    assert classify(-99) == "Large Deficient"
    assert classify(-95) == "Large Deficient"


def test_boundary_excess_large_excess():
    # 59 is the boundary: 19 < x <= 59 is Excess, so 59 itself -> Excess, 59.01 -> Large Excess
    assert classify(59) == "Excess"
    assert classify(59.01) == "Large Excess"
    assert classify(60) == "Large Excess"


def test_nan_input():
    assert classify(np.nan) == "Unknown"
    assert classify(None) == "Unknown"


def test_extreme_values():
    assert classify(-100) == "No Rainfall"
    assert classify(-150) == "No Rainfall"  # physically impossible but must not crash
    assert classify(500) == "Large Excess"


def test_compute_pct_departure():
    # actual = LPA -> 0% departure
    assert compute_pct_departure(1000, 1000) == 0
    # actual = 800, LPA = 1000 -> -20%
    assert abs(compute_pct_departure(800, 1000) - (-20)) < 1e-9
    # actual = 1200, LPA = 1000 -> +20%
    assert abs(compute_pct_departure(1200, 1000) - 20) < 1e-9


def test_ordinal_distance_rejects_unknown_label():
    """Regression test: ordinal_distance() must fail loudly (ValueError) on
    an out-of-scheme label like 'Unknown', not crash with a bare KeyError
    or silently mis-score. Found during a deep-analysis bug sweep."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from evaluate import ordinal_distance
    try:
        ordinal_distance(['Normal', 'Unknown'], ['Normal', 'Normal'])
        assert False, "expected ValueError, no exception was raised"
    except ValueError:
        pass
    except KeyError:
        assert False, "regression: raised bare KeyError instead of clear ValueError"


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
    print(f"\n{passed} passed, {failed} failed out of {len(test_fns)} tests")
    if failed > 0:
        sys.exit(1)
