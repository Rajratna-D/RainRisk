# 🧠 MahaRainRisk: Machine Learning Model Card

> **Dual-Mode Climatological & Agronomic Drought Intelligence Engine**

---

## 📌 Model Overview

MahaRainRisk utilizes a **Dual-Mode Architecture** designed to balance immediate diagnostic classification with forward-looking predictive risk mitigation:

```
[ Multi-Source Ingestion: IMD 0.25° Grid + NOAA ONI + JAMSTEC DMI + WRD Dams ]
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
     [ Mode 1: Diagnostic ]                       [ Mode 2: Forecaster ]
  250-Tree Random Forest Classifier           30-Day Early Warning Forecaster
  Acc: 98.0% | F1-Macro: 0.96                 Acc: 77.2% | F1-Macro: 0.74
  Identifies current drought state            Predicts risk trajectory for next 30 days
```

---

## 🔬 Training Data & Engineering

* **Spatial Coverage:** 194 Talukas across all 36 Districts of Maharashtra (LGD-aligned).
* **Temporal Coverage:** 10-Year historical daily records (2014–2023) + calibrated on the **2026 Kharif Shock Season**.
* **Data Sources:**
  * India Meteorological Department (IMD) 0.25° × 0.25° daily gridded rainfall.
  * Open-Meteo historical daily temperature and solar radiation.
  * NOAA Climate Prediction Center Oceanic Niño Index (ONI / Niño 3.4).
  * JAMSTEC Dipole Mode Index (DMI / Indian Ocean Dipole).
  * Maharashtra Water Resources Department (WRD) major reservoir storage telemetry.

---

## ⚙️ Feature Pipeline

1. **Standardized Precipitation Index (SPI):** Computed over 1-month, 3-month, and 6-month windows using McKee et al. (1993) 2-parameter Gamma distribution fitting.
2. **Monsoon Timing Dynamics:** Early onset failure indicators (June lag), mid-season dry spell duration (consecutive days with rain <2.5mm), and withdrawal strength.
3. **Soil & Zone Context:** Agro-climatic zone categorical encoding, soil holding capacity, and reservoir live storage percentage.
4. **Macro Teleconnections:** ENSO state (El Niño / La Niña) and IOD phase (Positive / Negative / Neutral).

---

## 🎯 Target Classification & Risk Tiers

| Code | Risk Label (EN) | Risk Label (MR) | Standard Deviation Departure (SPI-3) |
| :---: | :--- | :--- | :---: |
| **0** | **Safe** | **सुरक्षित** | $\text{SPI} \ge -0.5$ (Normal / Surplus) |
| **1** | **Watch** | **लक्ष ठेवा** | $-1.0 \le \text{SPI} < -0.5$ (Mild Deficit) |
| **2** | **Alert** | **सतर्कता** | $-1.5 \le \text{SPI} < -1.0$ (Moderate Deficit) |
| **3** | **Severe** | **तीव्र दुष्काळ** | $-2.0 \le \text{SPI} < -1.5$ (Severe Drought) |
| **4** | **Extreme** | **अति तीव्र दुष्काळ** | $\text{SPI} < -2.0$ (Extreme Agrarian Emergency) |

---

## 🏆 Model Performance Summary

| Metric | Mode 1 (Diagnostic) | Mode 2 (30-Day Forecaster) |
| :--- | :---: | :---: |
| **Algorithm** | Random Forest Classifier (250 Estimators) | Balanced Gradient Boosted Trees |
| **Test Accuracy** | **98.0%** | **77.2%** |
| **Precision (Macro)** | **0.97** | **0.75** |
| **Recall (Macro)** | **0.96** | **0.74** |
| **F1-Score (Macro)** | **0.96** | **0.74** |
| **Inference Latency** | **< 4.2 ms** | **< 6.8 ms** |
| **Artifact Size** | **12.2 MB** | **28.0 MB** |

---

## 🌾 University Advisory Mapping (Package of Practices)

Predictions are mapped deterministically to official agricultural university advisories:
* **MPKV Rahuri:** Western Maharashtra & Scarcity Zone (Ahmednagar, Pune, Solapur, Satara, Sangli, Kolhapur, Nashik, Dhule, Jalgaon, Nandurbar).
* **VNMKV Parbhani:** Marathwada Division (Chhatrapati Sambhajinagar, Jalna, Beed, Dharashiv, Latur, Nanded, Parbhani, Hingoli).
* **PDKV Akola:** Vidarbha Division (Akola, Amravati, Buldhana, Yavatmal, Washim, Nagpur, Wardha, Bhandara, Gondia, Chandrapur, Gadchiroli).
* **BSKKV Dapoli:** Konkan Coastal Division (Thane, Palghar, Raigad, Ratnagiri, Sindhudurg, Mumbai).
