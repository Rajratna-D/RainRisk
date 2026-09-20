# Model Results: Before vs After Methodology Fixes

See docs/05_methodology_fixes.md for full explanation.

| Model | Metric | OLD (leakage bug) | NEW (corrected) | Change |
|---|---|---|---|---|
| Logistic Regression | Accuracy | 32.9% | 34.0% | +1.1pp |
| Logistic Regression | Balanced Acc. | 18.6% | 22.0% | +3.4pp |
| Random Forest | Accuracy | 49.8% | 44.4% | -5.4pp |
| Random Forest | Balanced Acc. | 25.7% | 22.6% | -3.1pp |
| SVM | Accuracy | 34.7% | 35.4% | +0.7pp |
| SVM | Balanced Acc. | 21.1% | 20.4% | -0.7pp |

The Random Forest drop is interpreted as the corrected SMOTENC pipeline
removing an artificial performance inflation caused by the original SMOTE
bug (interpolating one-hot subdivision columns into fractional/impossible
category blends). See docs/05_methodology_fixes.md "Interpretation" for
full discussion.
