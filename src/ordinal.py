"""
RainRisk: Frank & Hall (2001) ordinal classification decomposition.

Decomposes a K-class ordinal classification problem into K-1 cumulative
binary threshold classifiers:
    M_k: P(Y > C_k | X)  for k in {0, 1, ..., K-2}

Individual class probabilities are recovered via:
    P(Y = C_0)     = 1 - P(Y > C_0)
    P(Y = C_k)     = P(Y > C_{k-1}) - P(Y > C_k)
    P(Y = C_{K-1}) = P(Y > C_{K-2})

Reference:
    Frank, E., & Hall, M. (2001). A simple approach to ordinal classification. ECML.
"""

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, clone

from labeling import CATEGORY_ORDER as DEFAULT_CATEGORY_ORDER


class FrankHallClassifier(BaseEstimator, ClassifierMixin):
    """
    Ordinal Classifier using Frank & Hall (2001) cumulative threshold decomposition.
    """

    def __init__(self, base_estimator=None, category_order=None):
        self.base_estimator = base_estimator
        self.category_order = category_order

    def fit(self, X, y):
        cat_order = self.category_order if self.category_order is not None else DEFAULT_CATEGORY_ORDER
        unique_in_y = set(y)
        self.active_categories_ = [c for c in cat_order if c in unique_in_y]
        
        if len(self.active_categories_) < 2:
            raise ValueError(f"At least 2 distinct classes must be present in y, found {len(self.active_categories_)}")

        self.classes_ = np.array(self.active_categories_)
        self.cat_to_rank_ = {cat: i for i, cat in enumerate(self.active_categories_)}
        self.rank_to_cat_ = {i: cat for i, cat in enumerate(self.active_categories_)}
        self.num_classes_ = len(self.active_categories_)

        y_ranks = np.array([self.cat_to_rank_[val] for val in y])

        self.classifiers_ = []
        for k in range(self.num_classes_ - 1):
            binary_y = (y_ranks > k).astype(int)
            clf = clone(self.base_estimator)
            clf.fit(X, binary_y)
            self.classifiers_.append(clf)

        return self

    def predict_proba(self, X):
        cum_probs = []
        for clf in self.classifiers_:
            if hasattr(clf, "predict_proba"):
                p = clf.predict_proba(X)[:, 1]
            elif hasattr(clf, "decision_function"):
                df = clf.decision_function(X)
                p = 1.0 / (1.0 + np.exp(-df))
            else:
                p = clf.predict(X).astype(float)
            cum_probs.append(p)

        cum_probs = np.column_stack(cum_probs)
        N = X.shape[0]
        K = self.num_classes_
        probs = np.zeros((N, K))

        probs[:, 0] = 1.0 - cum_probs[:, 0]
        for i in range(1, K - 1):
            probs[:, i] = cum_probs[:, i - 1] - cum_probs[:, i]
        probs[:, K - 1] = cum_probs[:, K - 2]

        # Clamping negative values handles non-monotonic threshold estimates across independently fit classifiers
        probs = np.clip(probs, 0.0, 1.0)
        row_sums = probs.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0.0] = 1.0
        return probs / row_sums

    def predict(self, X):
        probs = self.predict_proba(X)
        pred_ranks = np.argmax(probs, axis=1)
        return np.array([self.rank_to_cat_[r] for r in pred_ranks])

    def predict_expected_rank(self, X):
        """
        Computes continuous expected severity rank: E[r | X] = sum(k * P(Y = C_k | X)).
        """
        probs = self.predict_proba(X)
        ranks = np.arange(self.num_classes_)
        return np.sum(probs * ranks, axis=1)
