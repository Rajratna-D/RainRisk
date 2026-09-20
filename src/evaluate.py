"""
RainRisk: evaluation utilities. Ordinal-aware metrics since drought
categories have a natural order (adjacent-category errors are less severe
than distant-category errors).
"""
import numpy as np
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                               f1_score, confusion_matrix, classification_report,
                               precision_recall_fscore_support)

from labeling import CATEGORY_ORDER

CAT_IDX = {c: i for i, c in enumerate(CATEGORY_ORDER)}


def ordinal_distance(y_true, y_pred):
    """
    Computes |index(true) - index(pred)| for each pair.

    Raises a clear ValueError (not a bare KeyError) if either list contains
    a label outside CATEGORY_ORDER, e.g. "Unknown" rows that should have
    been filtered out before modeling/evaluation. Failing loudly here is
    deliberate: this function must never silently mis-score or crash with
    an unhelpful traceback if unfiltered data reaches it.
    """
    bad_true = set(y_true) - set(CAT_IDX)
    bad_pred = set(y_pred) - set(CAT_IDX)
    if bad_true or bad_pred:
        raise ValueError(
            f"ordinal_distance received label(s) outside CATEGORY_ORDER "
            f"{CATEGORY_ORDER}: unexpected in y_true={bad_true}, "
            f"unexpected in y_pred={bad_pred}. "
            f"Filter out 'Unknown'/invalid rows before evaluation."
        )
    return np.array([abs(CAT_IDX[t] - CAT_IDX[p]) for t, p in zip(y_true, y_pred)])


def off_by_one_accuracy(y_true, y_pred):
    d = ordinal_distance(y_true, y_pred)
    return float(np.mean(d <= 1))


def full_report(y_true, y_pred, model_name=""):
    """Aggregate metrics only. For per-class breakdown use per_class_report()."""
    return {
        "model": model_name,
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "off_by_one_accuracy": off_by_one_accuracy(list(y_true), list(y_pred)),
        "mean_ordinal_distance": float(np.mean(ordinal_distance(list(y_true), list(y_pred)))),
    }


def per_class_report(y_true, y_pred, labels=None):
    """
    Returns per-class precision/recall/F1/support as a list of dicts.
    Classes with zero support in y_true are still included (with support=0)
    so the report is explicit about which categories were never tested,
    rather than silently omitting them.
    """
    labels = labels or CATEGORY_ORDER
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    rows = []
    for i, cat in enumerate(labels):
        rows.append({
            "category": cat,
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i]),
            "untested": int(support[i]) == 0,
        })
    return rows
