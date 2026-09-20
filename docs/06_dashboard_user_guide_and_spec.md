# RainRisk Web Platform: Technical Specification and User Guide

## 1. Executive Summary

The **RainRisk Climate Intelligence Platform** is an enterprise-grade web application built to analyze and predict meteorological drought risk across **36 meteorological subdivisions of India based on 117 years of historical records (1901 to 2017)** from the India Meteorological Department (IMD) coupled with **global ocean teleconnections** (NOAA PSL Niño 3.4 SST and JAMSTEC Indian Ocean Dipole).

The platform uses a decoupled architecture:
* **Backend:** A high-performance FastAPI REST API that loads data and serialized machine learning pipelines (`best_pipeline.joblib`) into memory for sub-20ms inference latency.
* **Frontend:** A responsive Single-Page Application (SPA) built with React 18 and Vite, featuring an interactive Leaflet map of India with Esri World Dark cartography and a custom obsidian Bento-grid interface.

*(Note on Streamlit: An early prototype was built in Streamlit (`app.py`) during Phases 5 and 6 for quick chart exploration. That prototype was superseded in Phase 8 by this modern FastAPI and React web platform).*

---

## 2. System Architecture and Data Flow

```
┌─────────────────────────────────────────────────────────┐
│              Raw IMD Data CSV (1901-2017)                │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
     ┌──────────────────────────────────────────────┐
     │ FastAPI Startup Lifespan                     │
     │ - Compute LPA (1971-2020 baseline)           │
     │ - Calculate % Departure & IMD 6 Categories   │
     │ - Precompute 23 Features & Hashmaps          │
     │ - Load best_pipeline.joblib in RAM           │
     └──────────────────────┬───────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│ REST API Endpoints            │ │ Static File Mounting          │
│ /api/overview, /map, /predict │ │ Serves compiled React bundle  │
│ Return JSON under 20ms        │ │ from frontend/dist/           │
└───────────────┬───────────────┘ └───────────────┬───────────────┘
                │                                 │
                └───────────────┬─────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      REACT 18 / VITE SPA                        │
│          ExecutivePulse, GeospatialRadar, RegionalExplorer      │
│          ModelLeaderboard, ClimateCockpit, Methodology          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. UI/UX Design System

The platform runs on a custom design system styled with pure Vanilla CSS (`frontend/src/index.css`):
* **Canvas:** Matte obsidian backdrop (`#05080f` to `#0a0e17`) with subtle ambient radial glow.
* **Bento Grid:** Modular cards with 16px border-radius, frosted glass backdrop (`backdrop-filter: blur(20px)`), and 1px micro-borders.
* **Typography:** Clean geometric headers (Outfit font) paired with crisp tabular numbers (JetBrains Mono) and readable body copy (Inter font).
* **Color Palette (IMD Categories):**
  * **Large Excess (>= +60%):** Sapphire Blue (`#3b82f6`)
  * **Excess (+20% to +59%):** Electric Aqua (`#06b6d4`)
  * **Normal (-19% to +19%):** Emerald Jade (`#10b981`)
  * **Deficient (-59% to -20%):** Warm Amber (`#f59e0b`)
  * **Large Deficient (-99% to -60%):** Coral Crimson (`#f43f5e`)
  * **No Rainfall (= -100%):** Steel Slate (`#64748b`)

---

## 4. Detailed Breakdown of the 6 Navigation Tabs

### Tab 1: Executive Pulse (`ExecutivePulse.jsx`)
* **Purpose:** High-level national dashboard displaying national KPIs and long-term rainfall trends.
* **Features:**
  * 4 sparkline metric cards: Total Records (4,116), Subdivisions (36), Normal Years (64.8%), and National LPA (887.5 mm).
  * 117-year interactive SVG area chart displaying annual all-India monsoon rainfall with a 10-year rolling trendline.
  * Interactive milestone year chips: Clicking a famous drought year (1918, 1965, 1972, 1987, 2002, 2009, 2014, 2015) instantly jumps to the geospatial map for that year.

### Tab 2: Geospatial Radar (`GeospatialRadar.jsx`)
* **Purpose:** Interactive spatial map of India displaying rainfall departures across all 36 subdivisions.
* **Features:**
  * Leaflet map powered by Esri World Dark Gray Base tiles with custom vector circle markers.
  * Bubble size dynamically scales with departure severity, colored by IMD category.
  * Historical timeline scrubber: Slider and play/pause button to animate year-by-year monsoon patterns from 1901 to 2017.
  * Macro-region filters: Filter by Northwest India, Central India, South Peninsula, or East and Northeast India.
  * Hover cards showing exact millimeter totals, departure percentages, and local coordinates.

### Tab 3: Regional Explorer (`RegionalExplorer.jsx`)
* **Purpose:** Deep-dive regional climatology for any selected subdivision.
* **Features:**
  * Historical annual monsoon bar chart colored by drought category relative to the subdivision's LPA baseline.
  * 12-month seasonal progression bar chart tracking average monthly rainfall from January to December.
  * Climate Twins: Side-by-side comparison cards matching the selected region with a subdivision having the most similar rainfall volume and volatility.

### Tab 4: Model Leaderboard (`ModelLeaderboard.jsx`)
* **Purpose:** Empirical machine learning benchmarks and performance evaluation.
* **Features:**
  * Comparative cards for all 5 candidate models across 3 feature tiers.
  * Visual progress bars for Test Accuracy, Balanced Accuracy, and Off-by-One Accuracy.
  * Interactive held-out test confusion matrix (2011 to 2017) with hover inspection showing exact true vs predicted counts.

### Tab 5: Climate Cockpit (`ClimateCockpit.jsx`)
* **Purpose:** Real-time *what-if* scenario simulator for climate risk planning.
* **Features:**
  * One-click historical presets: "2015 Super El Niño", "Buffered Positive IOD", "La Niña Surge", "Severe Deficit", and "Baseline Normal".
  * Interactive dark sliders for Niño 3.4 SST anomaly, IOD Dipole Mode Index, prior-year rainfall, and seasonal precursors.
  * Animated circular risk arc gauge displaying the composite probability of drought.
  * Horizontal probability distribution spectrum across all 6 IMD categories.
  * Dynamic Agro-Climatic Advisory: Generates operational farming recommendations based on predicted risk.

### Tab 6: Methodology (`Methodology.jsx`)
* **Purpose:** Reference manual and architectural documentation.
* **Features:**
  * Filterable 23-feature dictionary with group chips (Monsoon Lag, Pre-Monsoon Precursor, Teleconnection, Volatility).
  * Technical explanations for IMD wide-band standards, calendar-gap reindexing, and SMOTENC categorical purity.

---

## 5. REST API Endpoint Specification

The backend (`backend/main.py`) exposes these endpoints:

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/api/overview` | `GET` | None | Returns national summary metrics, category distribution counts, and the 117-year all-India trend series. |
| `/api/subdivisions` | `GET` | None | Returns metadata, coordinates, LPA baselines, and drought frequencies for all 36 subdivisions. |
| `/api/subdivision/{name}`| `GET` | `name` (path) | Returns detailed historical timeline, 12-month averages, and decadal volatility stats for one subdivision. |
| `/api/map` | `GET` | `year`, `region`, `mode` | Returns geographic coordinates, rainfall departures, and category colors for all subdivisions for the selected year. |
| `/api/leaderboard` | `GET` | None | Returns benchmark rankings for all models and held-out test confusion matrix data. |
| `/api/methodology` | `GET` | None | Returns the full 23-feature dictionary and feature importance rankings (Gini vs Permutation). |
| `/api/predict` | `POST` | JSON body | Receives a 16-parameter simulation vector, calculates derived features, runs model inference, and returns predicted category, class probabilities, and operational advisory. |

---

## 6. How to Launch the Platform

Run the single-command launcher:
```bash
python run_webapp.py
```
This starts the FastAPI server on port 8008 and opens your default browser at:
`http://localhost:8008`
