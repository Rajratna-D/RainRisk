# Frank and Hall Ordinal Classification Decomposition

## 1. Executive Summary

In operational meteorology, drought risk is not an unordered set of labels. It is a **strictly ordered severity hierarchy**:

$$\text{No Rainfall} \prec \text{Large Deficient} \prec \text{Deficient} \prec \text{Normal} \prec \text{Excess} \prec \text{Large Excess}$$

Standard multi-class classification algorithms (such as plain Random Forest or Logistic Regression) treat target labels as **nominal (unordered)**. Under standard cross-entropy or Gini impurity loss, confusing *Normal* with *Deficient* (a minor 1-step error) incurs the exact same training penalty as confusing *Normal* with *Large Excess* (a catastrophic blunder predicting floods during a drought).

The **Frank and Hall (2001)** ordinal decomposition solves this fundamental limitation. It reformulates the $K$-class ordinal problem into $K-1$ **cumulative binary threshold classifiers** ($P(Y > k)$). This embeds the natural sequence of drought severity directly into the model training process without requiring complex custom loss solvers.

---

## 2. What Is Frank and Hall Decomposition?

Introduced by Eibe Frank and Mark Hall (ECML 2001), this method bridges the gap between standard binary machine learning algorithms and ordered multi-class outcomes.

### 2.1 The Cumulative Checkpoint Concept
Given $K$ ordered classes $C_0 \prec C_1 \prec C_2 \dots \prec C_{K-1}$ with integer ranks $r \in \{0, 1, \dots, K-1\}$, standard One-vs-Rest (OvR) trains $K$ models asking:
$$M_k: \text{Is } Y = C_k?$$
This completely ignores whether an observation was close or far from class $C_k$.

In contrast, **Frank and Hall trains $K-1$ cumulative threshold models**:
$$M_k: \text{Is } Y > C_k? \quad \text{for } k \in \{0, 1, \dots, K-2\}$$

```
                           Frank and Hall Cumulative Hierarchy
                           
  [Rank 0: Large Deficient] ──┐
                              ├─► Checkpoint 0: Is Y > Large Deficient?  [P(Y > 0)]
  [Rank 1: Deficient]       ──┤
                              ├─► Checkpoint 1: Is Y > Deficient?        [P(Y > 1)]
  [Rank 2: Normal]          ──┤
                              ├─► Checkpoint 2: Is Y > Normal? (Surplus) [P(Y > 2)]
  [Rank 3: Excess]          ──┤
                              ├─► Checkpoint 3: Is Y > Excess? (Flood)   [P(Y > 3)]
  [Rank 4: Large Excess]    ──┘
```

### 2.2 Mathematical Training Formulation
For each threshold $k \in \{0, \dots, K-2\}$, we create a binary indicator target $y^{(k)}$ from the full training dataset:

$$
y_i^{(k)} = 
\begin{cases} 
1 & \text{if } \text{rank}(y_i) > k \\
0 & \text{if } \text{rank}(y_i) \le k 
\end{cases}
$$

A base binary classifier $M_k$ (such as a decision tree ensemble) is fitted on $(X, y^{(k)})$. Every model $M_k$ trains on **100% of the training records**, learning the exact boundary dividing lower severity levels from higher ones.

---

## 3. Probability Recovery and Inference

During prediction, each trained binary model $M_k$ outputs an estimated probability:
$$\hat{p}_k(X) = \hat{P}(Y > C_k \mid X)$$

By the laws of cumulative probability distributions:
$$P(Y = C_k) = P(Y > C_{k-1}) - P(Y > C_k)$$

We recover the exact probability distribution across all $K$ individual categories:

$$
\begin{aligned}
\hat{P}(Y = C_0 \mid X) &= 1 - \hat{P}(Y > C_0 \mid X) \\
\hat{P}(Y = C_1 \mid X) &= \hat{P}(Y > C_0 \mid X) - \hat{P}(Y > C_1 \mid X) \\
\hat{P}(Y = C_2 \mid X) &= \hat{P}(Y > C_1 \mid X) - \hat{P}(Y > C_2 \mid X) \\
&\;\;\vdots \\
\hat{P}(Y = C_{K-1} \mid X) &= \hat{P}(Y > C_{K-2} \mid X)
\end{aligned}
$$

### 3.1 Monotonicity Regularization
Because independently fitted binary models may occasionally produce small numerical inconsistencies (for example, if $\hat{P}(Y > k) < \hat{P}(Y > k+1)$ on extreme outliers), the recovered probabilities are clamped and normalized:

$$\tilde{P}(Y = C_k) = \max\left(0, \hat{P}(Y = C_k)\right)$$
$$P(Y = C_k) = \frac{\tilde{P}(Y = C_k)}{\sum_{j=0}^{K-1} \tilde{P}(Y = C_j)}$$

### 3.2 Decision Rules
The final predicted category is selected by picking the class with the highest recovered probability:
$$\hat{y} = \arg\max_{k \in \{0, \dots, K-1\}} P(Y = C_k \mid X)$$

Alternatively, the continuous expected severity rank can be calculated:
$$\mathbb{E}[r \mid X] = \sum_{k=0}^{K-1} k \cdot P(Y = C_k \mid X)$$

---

## 4. Why We Use It in RainRisk

1. **Solves the Nominal Fallacy:** Standard cross-entropy penalizes all errors equally. Frank and Hall directly structures training so that distant errors receive higher cumulative penalties.
2. **Scikit-Learn Compatibility:** Implemented as a reusable estimator in `src/ordinal.py` inheriting from `BaseEstimator` and `ClassifierMixin`, allowing standard `.fit()`, `.predict()`, and `.predict_proba()` method calls.
3. **Monotonic Risk Gauges:** Provides clean, calibrated probabilities for our web application's circular risk gauge in `ClimateCockpit.jsx`.
