# RainRisk: Labeling Specification

## 1. Purpose

This document defines exactly how the target variable (`drought_category`) is calculated. This is the single most important design decision in the project. If the labels are wrong, every model trained on them becomes invalid, regardless of its statistical accuracy.

---

## 2. Decision: Operational Wide-Band 6-Category Scheme

The India Meteorological Department (IMD) maintains two official classification systems:

1. **All-India Headline Scheme:** Uses very narrow bands (Normal is 96% to 104% of normal rainfall). This is only used for the single nationwide seasonal announcement for the entire country.
2. **Operational Scheme:** Uses wide bands (Normal is -19% to +19% departure). This is the operational standard applied below the national level, specifically for states, meteorological subdivisions, and districts.

**Decision:** We use the operational wide-band scheme with all six categories because our unit of analysis is India's 36 meteorological subdivisions.

### Primary Source Confirmation for the "No Rainfall" Boundary
Early versions of this project used an estimated -90% placeholder for the rarest category. We confirmed the exact definition using an official primary document from the IMD Hydromet Division ("District Rainfall Distribution" bulletin).

* **Confirmed Definition:** "No Rain" is the exact value of **-100% departure** (recorded zero rainfall against a normal baseline).
* The entire range from **-99% down to -60%** belongs to "Large Deficient".
* In our historical 117-year dataset (1901 to 2017), the lowest recorded seasonal departure is -82.67%. This means zero historical rows change classification, but our code now follows 100% authentic IMD operational standards.

---

## 3. Official IMD Category Table

| Category | % of LPA Baseline | % Departure Range | Official Meaning |
|---|---|---|---|
| **No Rainfall** | 0% (exact) | = -100% exactly | Zero rainfall recorded |
| **Large Deficient** | 1% to 40% | -99% to -60% | Severe drought emergency |
| **Deficient** | 41% to 80% | -59% to -20% | Moderate drought |
| **Normal** | 81% to 119% | -19% to +19% | Climatological optimum |
| **Excess** | 120% to 159% | +20% to +59% | Monsoon surplus |
| **Large Excess** | >= 160% | >= +60% | Flood surge |

---

## 4. Long Period Average (LPA) Baseline

The IMD updates its official 50-year climatological baseline roughly once per decade. The current operational baseline is **1971 to 2020** (evaluating to an all-India average of approximately 887.5 mm during the June to September monsoon).

For each subdivision, the fixed baseline is computed as:

$$\text{LPA}_i = \frac{1}{N_{1971-2020}} \sum_{t=1971}^{2020} \text{JJAS}_{i,t}$$

Percentage departure is then evaluated as:

$$\text{Departure \%}_{i,t} = \frac{\text{JJAS}_{i,t} - \text{LPA}_i}{\text{LPA}_i} \times 100$$

### Common Mistake to Avoid
Never compute a rolling average or all-years average as the baseline per row. Doing so causes the baseline to constantly shift, making departures inconsistent across historical decades. The LPA must remain a fixed reference period.

---

## 5. Python Implementation

The production logic lives in `src/labeling.py`:

```python
import numpy as np

CATEGORY_ORDER = [
    "No Rainfall",
    "Large Deficient",
    "Deficient",
    "Normal",
    "Excess",
    "Large Excess"
]

LPA_BASELINE_START = 1971
LPA_BASELINE_END = 2020
NO_RAINFALL_THRESHOLD = -100.0


def classify(pct_departure):
    """
    Classify a single percentage departure from LPA into an IMD category.
    Boundaries are verified against IMD official bulletin standards.
    """
    if pct_departure is None or (isinstance(pct_departure, float) and np.isnan(pct_departure)):
        return "Unknown"

    if pct_departure <= NO_RAINFALL_THRESHOLD:
        return "No Rainfall"
    elif pct_departure <= -60.0:
        return "Large Deficient"
    elif pct_departure <= -20.0:
        return "Deficient"
    elif pct_departure <= 19.0:
        return "Normal"
    elif pct_departure <= 59.0:
        return "Excess"
    else:
        return "Large Excess"
```

---

## 6. Testing Requirements

Our automated test suite (`tests/test_labeling.py`) explicitly validates:
1. Exact boundary values (e.g., confirming that -20.0% is Deficient and -19.99% is Normal).
2. The exact -100.0% boundary for "No Rainfall" and -99.99% for "Large Deficient".
3. Safe handling of invalid inputs (NaN or None returns "Unknown" rather than raising silent errors).
4. Full agreement between `src/labeling.py` and `src/evaluate.py`.
