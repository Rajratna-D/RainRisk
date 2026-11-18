# MahaRainRisk: Future Development Roadmap

**Document Type:** Strategic Feature Planning & Engineering Roadmap  
**Last Updated:** November 19, 2026  
**Coverage:** 194 Monitored Rainfed Talukas, 36 Districts, Maharashtra  
**Author:** Rajratna Dhiwar  
**Status:** Active Planning Document — Not Yet Implemented

---

## Overview

This document records all planned features, data integrations, infrastructure upgrades, and product expansions for MahaRainRisk. Each idea is backed by research, comparative analysis against institutional systems (IIT Gandhinagar, IWMI SukhaRakshak AI, AgriStack), and engineering feasibility assessment.

Items are grouped by impact tier and ordered within each tier by implementation effort (lowest first).

---

## Priority Tiers

| Tier | Label | Description |
|---|---|---|
| 🟥 | CRITICAL UPGRADE | Closes the biggest gap vs institutional systems |
| 🟧 | HIGH IMPACT | Directly improves farmer outcomes or ML accuracy |
| 🟨 | MEDIUM IMPACT | Strengthens the platform competitively |
| 🟩 | STRATEGIC | Long-term product expansion |
| 🔵 | RESEARCH TRACK | Experimental / academic-grade improvements |

---

## 🟥 TIER 1 — CRITICAL UPGRADES

---

### PLAN-01 | NDVI + VCI Satellite Integration via Google Earth Engine

**Category:** Data Science / New Data Source  
**Estimated Effort:** 2 weeks  
**Cost:** Free (GEE free tier for researchers)  
**Priority:** Critical — This is the single feature that separates MahaRainRisk from IIT Gandhinagar's India Drought Monitor

#### What It Is
The **Vegetation Condition Index (VCI)** is a satellite-derived metric that measures whether crops and vegetation in a taluka are actually green and healthy *right now*, as seen from space by NASA MODIS (MOD13Q1 — 250m resolution, 16-day composite). It is calculated as:

$$\text{VCI} = \frac{\text{NDVI}_{current} - \text{NDVI}_{min}}{\text{NDVI}_{max} - \text{NDVI}_{min}} \times 100$$

Where NDVI min/max are computed from the historical baseline (2000–2025) for that specific taluka at that specific time of year.

- **VCI = 0–20**: Extreme vegetation stress (crop failure zone)
- **VCI = 20–40**: Severe stress (drought confirmed)
- **VCI = 40–60**: Moderate stress (watch zone)
- **VCI = 60–80**: Good crop health
- **VCI = 80–100**: Optimal condition

#### Why It Matters
Currently, MahaRainRisk predicts drought risk from weather API data alone (rainfall, temperature, soil moisture). VCI adds **empirical ground truth from space** — it directly confirms whether crops are stressed regardless of what the weather forecast says. This eliminates sensor errors, IMD data gaps, and model assumptions.

IWMI SukhaRakshak AI and IIT Gandhinagar India Drought Monitor both use VCI. MahaRainRisk needs this to be considered a peer system.

#### How to Implement
1. Register for Google Earth Engine (GEE) free academic access at `earthengine.google.com`.
2. `pip install earthengine-api geemap` in `requirements.txt`.
3. Create `etl/satellite_ingestion.py` that:
   - Loads the GEE MODIS collection: `ee.ImageCollection("MODIS/061/MOD13Q1")`
   - Computes 2000–2025 baseline NDVI min/max for each of the 194 taluka centroids
   - Calculates VCI for the most recent 16-day composite
   - Stores VCI per taluka in a new PostgreSQL column: `ALTER TABLE daily_weather ADD COLUMN vci NUMERIC(5,2);`
4. Add a new GitHub Actions cron at `every 16 days` (MODIS composite frequency): `.github/workflows/satellite_ingest.yml`
5. Add `vci` as a feature column in `ml/train.py` → retrain → expect model accuracy improvement of 2–5%.

#### New API Endpoint
```
GET /api/v1/taluka/{code}/satellite
→ { "taluka_code": 4120, "vci": 42.3, "ndvi": 0.38, "vegetation_status": "Moderate Stress", "as_of_date": "2026-11-01" }
```

#### Database Change
```sql
ALTER TABLE daily_weather ADD COLUMN vci NUMERIC(5,2) DEFAULT NULL;
ALTER TABLE taluka_risk_latest ADD COLUMN vci NUMERIC(5,2) DEFAULT NULL;
CREATE INDEX idx_daily_weather_vci ON daily_weather(vci) WHERE vci IS NOT NULL;
```

---

### PLAN-02 | IMD Gridded Rainfall Integration via `imdlib`

**Category:** Data Source Upgrade  
**Estimated Effort:** 2 weeks  
**Cost:** Free (IMD open data)  
**Priority:** Critical — IMD data is the official Government of India standard

#### What It Is
The India Meteorological Department (IMD) publishes official high-resolution gridded daily rainfall datasets at **0.25° × 0.25° resolution** dating back to **1901**. This is the same data used by the NDMA (National Disaster Management Authority) to officially declare droughts under the Government of India's Drought Manual.

Currently MahaRainRisk ingests weather data from Open-Meteo, which is a European numerical weather model (ERA5-based). While accurate, it is not the official Indian government standard.

#### Why It Matters
- **Legal/Policy alignment**: NDMA drought declarations are based on IMD data. If MahaRainRisk SPI calculations match IMD data, our risk scores will align with government drought declarations.
- **117+ years of historical depth**: Open-Meteo gives 2020–present. IMD gives 1901–present. With 117 years of data, our SPI calculations become statistically far more robust.
- **PMFBY integration prerequisite**: Crop insurance claims under PMFBY are validated against IMD gridded data. This makes MahaRainRisk legally defensible for insurance verification.

#### How to Implement
1. `pip install imdlib` — a community Python library to download IMD binary datasets.
2. Create `etl/imd_historical_sync.py`:
   - Downloads IMD daily gridded rainfall NetCDF for all years 1901–present
   - Clips to Maharashtra bounding box (`lat: 15.6–22.1°N, lon: 72.6–80.9°E`)
   - Spatially averages grid cells falling within each of 194 taluka boundaries using `geopandas` spatial join
   - Backfills `daily_weather.rainfall_mm` with IMD values where available
3. Create `etl/imd_daily_update.py`:
   - After IMD publishes yesterday's gridded data (usually 24–48 hr delay), auto-ingest to supplement Open-Meteo
4. Add data-source provenance column: `ALTER TABLE daily_weather ADD COLUMN rainfall_source VARCHAR(10) DEFAULT 'openmeteo';`

---

## 🟧 TIER 2 — HIGH IMPACT

---

### PLAN-03 | Historical Time-Series API Endpoint

**Category:** Backend / API  
**Estimated Effort:** 1 day  
**Cost:** Free  
**Priority:** High — Enables trend analysis, the most requested feature by agricultural officers

#### What It Is
Add a new API endpoint that returns a complete time-series of a taluka's drought risk scores, rainfall, SPI, and soil moisture for a specified date range. The `taluka_risk_history` table is **already being populated daily** but is never exposed via API.

#### Why It Matters
A single risk score today ("Alert") means nothing without context. A 30-day trend showing a taluka sliding from "Safe → Watch → Alert → Severe" over three weeks tells a complete, actionable story. This is what agricultural journalists, Collectorate officers, and NGO workers specifically need.

#### How to Implement
Add to `backend/main.py`:
```python
@app.get("/api/v1/taluka/{code}/history")
async def get_taluka_history(
    code: int,
    days: int = Query(default=30, ge=7, le=365)
):
    # Query taluka_risk_history for last N days
    # Return sorted list of {date, risk_category, risk_score, spi_3, soil_moisture}
```

#### New API Endpoint
```
GET /api/v1/taluka/4120/history?days=30
→ [
    { "date": "2026-10-20", "risk_category": "Safe", "risk_score": 0.12, "spi_3": 0.4 },
    { "date": "2026-10-21", "risk_category": "Watch", "risk_score": 0.31, "spi_3": -0.2 },
    ...
    { "date": "2026-11-19", "risk_category": "Alert", "risk_score": 0.68, "spi_3": -1.1 }
  ]
```

---

### PLAN-04 | Automated Monthly Model Retraining Cron

**Category:** MLOps / DevOps  
**Estimated Effort:** 0.5 days  
**Cost:** Free (GitHub Actions free tier)  
**Priority:** High — Prevents model drift as new 2026/2027 climate data accumulates

#### What It Is
A second GitHub Actions workflow that fires on the **1st of every month at 02:00 UTC**, appends the last 30 days of freshly ingested weather data to the master training panel, runs `ml/train.py`, and validates the new model's OOB accuracy before deploying it.

#### Why It Matters
Currently, `ml/train.py` exists but must be run manually. The model was trained once on data through early 2026 and has not seen the increasingly unusual climate patterns of late 2026. Without retraining, within 6–12 months the model's accuracy could decline significantly as Maharashtra's rainfall patterns continue to shift from climate change.

#### How to Implement
Create `.github/workflows/monthly_retrain.yml`:
```yaml
name: Monthly Model Retraining Pipeline
on:
  schedule:
    - cron: '0 2 1 * *'   # 2:00 AM UTC, 1st of every month
  workflow_dispatch:

jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - name: Rebuild Master Panel
        run: python ml/build_master_panel.py
      - name: Retrain Models with OOB Gate
        run: python ml/train.py --validate-oob-threshold 0.98
      - name: Retrain Forecaster
        run: python ml/train_forecaster.py --validate-oob-threshold 0.80
      - name: Commit Updated Model Artifacts
        run: |
          git config user.email "bot@maharainrisk.in"
          git config user.name "MahaRainRisk Bot"
          git add ml/drought_model.joblib ml/drought_forecaster.joblib
          git commit -m "chore(ml): monthly model retrain $(date +%Y-%m)"
          git push
```

---

### PLAN-05 | SPEI (Standardized Precipitation Evapotranspiration Index) Addition

**Category:** Data Science / Model Feature  
**Estimated Effort:** 1 day  
**Cost:** Free  
**Priority:** High — International standard for drought science; more accurate than SPI in hot climates

#### What It Is
The **SPEI** extends SPI by incorporating the effect of temperature-driven water loss (evapotranspiration). In Maharashtra's increasingly hot summers, 50 mm of rainfall at 40°C evaporates significantly faster than the same rainfall at 32°C — the land becomes drought-stressed even with "normal" rainfall amounts.

Formula:
$$\text{SPEI} = \text{SPI}(\text{Precipitation} - \text{PET})$$

Where PET (Potential Evapotranspiration) is computed using the **Hargreaves-Samani equation** using `temp_max_c` and `temp_min_c` already present in `daily_weather`.

CGIAR, IWMI, and IIT Gandhinagar use SPEI as their primary drought index in research publications.

#### How to Implement
1. `pip install climate-indices` — includes both SPI and SPEI calculators.
2. Add `spei_3` and `spei_6` to the `daily_weather` table.
3. Compute SPEI in `etl/daily_cron_ingestion.py` after each day's ingestion using the 90-day and 180-day rolling windows of `(rainfall_mm - PET)`.
4. Add `spei_3` as a feature in `ml/train.py` FEATURE_COLS.

#### PET Calculation (Already Have the Data)
```python
# Hargreaves-Samani equation — no extra data source needed
PET = 0.0023 * (temp_max_c - temp_min_c)**0.5 * (temp_max_c + temp_min_c + 17.8) * Ra
```
where `Ra` (extraterrestrial radiation) is a function of latitude and day-of-year — computable from taluka coordinates in `lgd_maharashtra_master.csv`.

---

### PLAN-06 | El Niño / La Niña (ENSO) Auto-Ingestion

**Category:** Data Source / Model Feature  
**Estimated Effort:** 1 day  
**Cost:** Free (NOAA CPC publishes data openly)  
**Priority:** High — ENSO is the dominant driver of Maharashtra drought; feature columns already exist in model

#### What It Is
The **Oceanic Niño Index (ONI)** is published monthly by NOAA's Climate Prediction Center. It measures sea surface temperature anomalies in the Pacific Ocean, which is the primary cause of India's monsoon variability:

- **El Niño (ONI > +0.5)**: Weak Indian monsoon → drought risk in Maharashtra increases 60–80%
- **La Niña (ONI < −0.5)**: Strong Indian monsoon → flood risk
- **Neutral**: Normal monsoon

The feature columns `nino34_anomaly` and `oni` already exist in `ml/train.py`'s `FEATURE_COLS`. They were included in model design but are currently filled with static historical values, not live-updated.

#### How to Implement
1. Add a monthly NOAA ingestion to `.github/workflows/daily_ingest.yml` that runs on the 15th of each month:
   ```python
   # NOAA CPC ONI data — free, open, machine-readable
   url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
   ```
2. Parse the latest ONI value and store it in a new `climate_indices` table.
3. Join ONI to `daily_weather` monthly records during ML feature engineering.
4. The model immediately gains a **seasonal lead signal** — it can warn "this Kharif season has elevated drought probability because ONI = +1.4 (El Niño active)."

---

### PLAN-07 | WhatsApp + SMS Push Alert System

**Category:** Farmer Outreach / Delivery Layer  
**Estimated Effort:** 3 days  
**Cost:** ~₹500–₹2,000/month (MSG91 or Twilio WhatsApp Business API)  
**Priority:** High — Makes MahaRainRisk proactively life-saving instead of reactively informative

#### What It Is
An automated alert system that sends a WhatsApp message in Marathi to enrolled farmers whenever their taluka's risk score crosses a danger threshold. Alert triggers:

| Transition | Alert Level | Message |
|---|---|---|
| Safe → Watch | ⚠️ Watch | "तुमच्या तालुक्यात पुढील ७ दिवस पाऊस कमी राहण्याची शक्यता आहे. पाणी जपून वापरा." |
| Watch → Alert | 🔴 Alert | "दुष्काळाचा धोका: तुमच्या तालुक्यात पीक जतनासाठी ठिबक सिंचन सुरू करा." |
| Alert → Severe | 🚨 Severe | "URGENT: तीव्र दुष्काळाचा इशारा. PMFBY विमा दावा नोंदवा." |

#### How to Implement
1. Add `farmer_subscriptions` table to PostgreSQL:
   ```sql
   CREATE TABLE farmer_subscriptions (
       id SERIAL PRIMARY KEY,
       phone_number VARCHAR(15) NOT NULL,
       taluka_lgd_code INTEGER REFERENCES talukas(taluka_lgd_code),
       language VARCHAR(5) DEFAULT 'mr',  -- 'mr' or 'en'
       subscribed_at TIMESTAMP DEFAULT NOW(),
       is_active BOOLEAN DEFAULT TRUE
   );
   ```
2. Add `POST /api/v1/subscribe` endpoint for farmer registration.
3. In `etl/daily_cron_ingestion.py`, after risk upsert, compare new vs. previous risk category for each taluka. If category worsened, query subscriptions and dispatch via MSG91 WhatsApp API.
4. Add SMS fallback for feature-phone users (DLT-registered template via TRAI framework).

---

### PLAN-08 | PMFBY Crop Insurance Verification Endpoint

**Category:** Commercial API / Business  
**Estimated Effort:** 3 days  
**Cost:** Free (revenue opportunity)  
**Priority:** High — Direct commercial application; ₹25,000+ crore insurance industry

#### What It Is
A dedicated API endpoint that allows insurance companies (AIC, Bajaj Allianz, HDFC ERGO), bank officials, and state agriculture departments to query MahaRainRisk's historical drought risk record for a specific taluka and date range to support or contest PMFBY crop insurance claims.

The endpoint answers the question: *"Was Osmanabad taluka in drought during the Kharif 2026 sowing season (June 15 – September 15)?"*

#### How to Implement
Add to `backend/main.py`:
```python
@app.get("/api/v1/insurance/drought-verification")
async def drought_verification(
    taluka_code: int,
    from_date: date,
    to_date: date,
    x_api_key: str = Header(None, alias="X-Insurance-API-Key")
):
    # Validate institutional API key (separate key tier from admin key)
    # Query taluka_risk_history for the date range
    # Return: daily risk scores, drought days count, peak severity, SPI summary
    # Include: "drought_declared": True/False based on NDMA criteria
    # (>= 7 consecutive days of Alert/Severe = drought declared)
```

#### Response Schema
```json
{
  "taluka_code": 4120,
  "taluka_name": "Osmanabad",
  "district": "Dharashiv",
  "query_period": { "from": "2026-06-15", "to": "2026-09-15" },
  "drought_summary": {
    "drought_declared": true,
    "peak_severity": "Severe",
    "drought_days": 42,
    "max_consecutive_dry_days": 29,
    "average_spi_3": -1.47,
    "average_risk_score": 0.74
  },
  "daily_records": [ ... ],
  "certified_by": "MahaRainRisk v2.0 | Data: Open-Meteo + IMD"
}
```

---

## 🟨 TIER 3 — MEDIUM IMPACT

---

### PLAN-09 | GeoJSON Live Drought Map Endpoint

**Category:** Visualization / API  
**Estimated Effort:** 3–5 days  
**Cost:** Free  
**Priority:** Medium — Enables visual drought dashboards; equivalent to IIT Gandhinagar's map layer

#### What It Is
An API endpoint that returns a valid **GeoJSON FeatureCollection** where each of the 194 Maharashtra taluka polygons is enriched with its current drought risk score, category, and SPI. This can be directly consumed by any Leaflet.js or Mapbox map to render a live color-coded drought heat-map of Maharashtra.

#### Why It Matters
IIT Gandhinagar's India Drought Monitor is widely cited precisely because of its visual map. MahaRainRisk has richer taluka-level ML data but zero visual layer accessible via API. This single endpoint would let any journalist, NGO, or government officer embed a live MahaRainRisk drought map on their website in 10 lines of JavaScript.

#### How to Implement
1. Load `lgd_maharashtra_master.csv` taluka boundaries as GeoJSON polygons (or fetch from GADM/Datameet Maharashtra shapefile).
2. Store taluka polygon GeoJSON in a `taluka_boundaries` PostgreSQL table with PostGIS `GEOMETRY` column.
3. Add endpoint:
   ```python
   @app.get("/api/v1/map/drought.geojson")
   async def drought_geojson():
       # JOIN taluka_risk_latest WITH taluka_boundaries
       # Return GeoJSON FeatureCollection
       # Each feature: polygon + { risk_category, risk_score, spi_3, district_name }
   ```
4. Frontend: Any consumer can render the map with 10 lines of Leaflet.js:
   ```javascript
   fetch("https://maharainrisk-api.onrender.com/api/v1/map/drought.geojson")
     .then(r => r.json())
     .then(data => L.geoJSON(data, { style: riskColorStyle }).addTo(map));
   ```

#### Risk Color Scale
```
Risk Score 0.0–0.2  → #2ecc71 (Green  — Safe)
Risk Score 0.2–0.4  → #f1c40f (Yellow — Watch)
Risk Score 0.4–0.6  → #e67e22 (Orange — Alert)
Risk Score 0.6–0.8  → #e74c3c (Red    — Severe)
Risk Score 0.8–1.0  → #8e44ad (Purple — Extreme)
```

---

### PLAN-10 | Real-Time Maharashtra Reservoir Storage Integration

**Category:** Data Source  
**Estimated Effort:** 4 days  
**Cost:** Free (Maharashtra WRD open data)  
**Priority:** Medium — Groundwater and dam storage are key drought indicators missing from current model

#### What It Is
Maharashtra's Water Resources Department (WRD) publishes **daily reservoir storage percentages** for all major dams (Jayakwadi, Majalgaon, Koyna, Bhandardara, etc.) through the `wrd.maharashtra.gov.in` portal and the **Pravah-AI** dashboard. This includes:
- Live storage volume (million cubic metres)
- Percentage of capacity filled
- Daily inflow and outflow

Currently, our model uses a **static** `district_dam_storage_pct` from historical averages. Live dam storage data would make this feature dynamic and dramatically improve prediction accuracy during drawdown periods.

#### How to Implement
1. Write `etl/reservoir_ingestion.py` that scrapes/parses the WRD Maharashtra daily water storage portal.
2. Map each dam to the talukas in its command area (Jayakwadi → Marathwada talukas).
3. Update `taluka_risk_latest.district_dam_storage_pct` dynamically in the daily cron.
4. The ML model will immediately use live dam storage for inference.

---

### PLAN-11 | CGWB Groundwater Level Integration

**Category:** Data Source  
**Estimated Effort:** 5 days  
**Cost:** Free (NWIC API — requires registration)  
**Priority:** Medium — Groundwater depletion is Maharashtra's most visible drought indicator

#### What It Is
The **Central Ground Water Board (CGWB)** publishes seasonal groundwater depth measurements (pre-monsoon/post-monsoon, in meters below ground level) through the **National Water Data Portal (NWIC)** at `nwdp.nwic.gov.in`. Maharashtra has hundreds of monitoring wells, and declining water tables are the most visible sign of chronic drought in the Deccan Plateau.

#### How to Implement
1. Register for a free NWIC API key at `nwdp.nwic.gov.in`.
2. Create `etl/groundwater_ingestion.py` that queries quarterly CGWB well measurements for Maharashtra wells.
3. Spatially average well readings within each taluka using `geopandas`.
4. Store in `daily_weather.groundwater_depth_mbgl` column (already in schema) with dynamic values replacing static estimates.

---

### PLAN-12 | Crop-Specific Risk Scores

**Category:** ML Model Enhancement  
**Estimated Effort:** 2 weeks  
**Cost:** Free  
**Priority:** Medium — Different crops have different drought tolerances

#### What It Is
Currently, MahaRainRisk issues one risk score per taluka. But a taluka growing Jowar (drought-tolerant) faces very different consequences than the same taluka growing Sugarcane (water-intensive). Add **crop-specific risk layers** using Maharashtra's crop sowing data.

#### Crop Drought Tolerance Matrix (Maharashtra Major Crops)
| Crop | Water Need | Drought Risk Multiplier |
|---|---|---|
| Jowar (Sorghum) | Low | 0.6× |
| Bajra (Pearl Millet) | Low | 0.5× |
| Cotton | Medium | 1.0× |
| Soybean | Medium-Low | 0.8× |
| Sugarcane | Very High | 2.0× |
| Tur (Pigeonpea) | Low-Medium | 0.7× |

#### How to Implement
1. Load Maharashtra crop sown area data from Agriculture Department / ICAR (available via `data.gov.in`).
2. Add `crop_risk_adjustments` table: `(taluka_code, crop_name, risk_multiplier, kharif_or_rabi)`.
3. Add endpoint: `GET /api/v1/taluka/{code}/risk?crop=sugarcane` → returns crop-adjusted risk.

---

## 🟩 TIER 4 — STRATEGIC (LONG-TERM)

---

### PLAN-13 | Offline-First Progressive Web App (PWA)

**Category:** Product / Mobile  
**Estimated Effort:** 4 weeks  
**Cost:** Free (Service Worker + IndexedDB)  
**Priority:** Strategic — Reaches farmers with no reliable internet

#### What It Is
A Progressive Web App that caches the last 7 days of risk data for all 194 talukas locally on the farmer's phone using **Service Workers** and **IndexedDB**. When internet is unavailable — which is common in rural Maharashtra — the app still shows the most recently cached risk scores, bilingual advisories, and rainfall alerts.

#### Key Features
- Installable from browser (no App Store)
- Works offline (cached data via Service Worker)
- Marathi-first interface
- Receives push notifications even when app is closed (Web Push API)
- Total app size < 2 MB
- Works on Android phones with 1 GB RAM and 2G connectivity

#### Technical Architecture
```
Frontend: Vite + React (or plain HTML + Vanilla JS for minimum size)
Caching: Service Worker (Workbox) + IndexedDB (Dexie.js)
Sync: Background Sync API — queues data refresh when connectivity returns
Notifications: Web Push API → connected to MahaRainRisk backend alert system
Offline Map: Pre-cached static Maharashtra SVG district map (not Leaflet)
```

---

### PLAN-14 | LLM-Powered Vernacular Chatbot (Kisan Sahayak)

**Category:** AI / Product  
**Estimated Effort:** 3 weeks  
**Cost:** Free (Gemini API free tier) or ~₹2,000/month at scale  
**Priority:** Strategic — Bridges the literacy and technology gap for farmers

#### What It Is
A conversational AI chatbot accessible via the MahaRainRisk web app and WhatsApp that answers farmer questions in **natural spoken Marathi** about their taluka's drought situation, what crops to plant, what emergency measures to take, and how to file PMFBY claims.

Example conversation:
> **Farmer (Marathi)**: "माझ्या तालुक्यात पाऊस कमी आहे, काय करू?"  
> **Kisan Sahayak**: "तुमच्या सोलापूर तालुक्यात SPI-3 = -1.4 आहे, म्हणजे तीव्र दुष्काळाचा धोका आहे. आत्ता ठिबक सिंचन सुरू करा, ज्वारी किंवा बाजरी यासारखी दुष्काळ-सहनशील पिके निवडा, आणि PMFBY विमा दावा नोंदवण्यास विलंब करू नका."

#### How to Implement
1. Use **Google Gemini API** (`gemini-1.5-flash` for cost efficiency) with a system prompt grounding it in MahaRainRisk's real-time data.
2. Create MCP tool call: `get_taluka_risk(taluka_name)` → Gemini calls this to get real-time data before answering.
3. Use **AI4Bharat IndicTrans** for Marathi ↔ English translation if needed.
4. Deploy as a FastAPI `/api/v1/chat` endpoint with streaming response.
5. Connect to WhatsApp Business API for farmers who prefer voice/text messaging.

---

### PLAN-15 | Crop Disease Detection via Smartphone Camera

**Category:** AI / Product Extension  
**Estimated Effort:** 6 weeks  
**Cost:** Free (PlantVillage open dataset + TensorFlow Lite)  
**Priority:** Strategic — Extends MahaRainRisk beyond drought into full agri-decision support

#### What It Is
An image recognition endpoint where a farmer photographs a diseased crop leaf and receives:
1. Disease name (in Marathi and English)
2. Confidence percentage
3. Recommended treatment (organic or chemical, available in Maharashtra markets)
4. Urgency level (days before irreversible crop loss)

#### Technical Architecture
- **Model**: EfficientNetB0 fine-tuned on PlantVillage (54,000 images, 38 disease classes) + Indian crop extension dataset (cotton, sugarcane, tur, soybean)
- **Explainability**: Grad-CAM heatmap showing which part of the leaf the model flagged
- **On-Device Option**: TensorFlow Lite model (~8 MB) for offline inference on Android
- **API**: `POST /api/v1/crop/diagnose` accepts multipart image upload

#### Maharashtra-Specific Crops to Cover
Cotton (bollworm, leaf curl), Soybean (yellow mosaic, rust), Sugarcane (red rot, smut), Tur/Pigeonpea (Fusarium wilt, sterility mosaic), Jowar (charcoal rot, downy mildew)

---

### PLAN-16 | Pan-India Expansion (Phase 2 Scaling)

**Category:** Infrastructure / Product  
**Estimated Effort:** 3–6 months  
**Cost:** Moderate (larger DB, Redis cache, parallel workers)  
**Priority:** Strategic — The long-term national vision

#### What It Is
Expand MahaRainRisk from 194 Maharashtra talukas to **all 6,000+ talukas / blocks across India**.

#### Scaling Requirements
| Component | Current (194 talukas) | Pan-India (6,000 talukas) |
|---|---|---|
| Daily API calls to Open-Meteo | 97 | ~3,000 |
| DB rows/year | ~70,800 | ~2.19 million |
| Cache memory | 232 KB | ~7.2 MB |
| GitHub Actions runtime | ~90 seconds | ~30 minutes (sharded into 4 workers) |
| DB storage/year | ~15 MB | ~450 MB |

#### Architecture Changes Required
1. Replace `cachetools.TTLCache` with **Redis** (Upstash free tier handles 6,000 entries)
2. Shard GitHub Actions into regional workers: North, South, East, West (parallel execution)
3. Add PostgreSQL table partitioning: `PARTITION BY RANGE (record_date)` by year
4. Expand `lgd_maharashtra_master.csv` → `lgd_india_master.csv` (LGD codes for all talukas)
5. Build state-selector UI layer on the frontend

---

## 🔵 RESEARCH TRACK

---

### PLAN-17 | LSTM Temporal Sequence Model (Experimental)

**Category:** ML Research  
**Estimated Effort:** 4–6 weeks  
**Cost:** Free (GPU via Google Colab)  
**Priority:** Research — May improve long-range forecast accuracy

#### What It Is
Replace or supplement the current Random Forest Forecaster with a **Long Short-Term Memory (LSTM)** neural network trained on 7-year sequences of daily weather data per taluka. LSTMs are designed to learn temporal dependencies — the kind of "last 60 days of drying trend" pattern that Random Forest sees as independent features but LSTM processes as a connected narrative.

#### Research Hypothesis
An LSTM trained on the last 90 days of `(rainfall, temperature, SPI-3, soil_moisture)` sequences per taluka may outperform the current 30-day Random Forest forecaster (81.12% OOB) for predicting drought 30 days ahead.

#### Implementation Plan
1. Build sequence dataset: `X = (taluka_code, 90-day rolling window), y = drought_category_30_days_ahead`
2. Train on Google Colab (T4 GPU, free tier) using PyTorch or TensorFlow
3. A/B test against current Random Forest: deploy LSTM only if F1-score exceeds 0.84 on 2026 holdout set
4. Keep Random Forest as fallback (interpretable, fast, production-proven)

---

### PLAN-18 | Federated Learning for Privacy-Preserving Farm Data

**Category:** Research / Privacy  
**Estimated Effort:** 8–12 weeks  
**Cost:** Free (research project)  
**Priority:** Research / Future-proof

#### What It Is
If MahaRainRisk ever collects individual farmer field data (soil sensors, micro-weather stations), **Federated Learning** allows the ML model to improve using that private farm data without the data ever leaving the farmer's device — only model gradients are shared.

This is the same technology used by Google's Gboard keyboard for on-device learning and is gaining traction in Indian agritech for protecting farmer data sovereignty under India's Digital Personal Data Protection Act, 2023.

---

## Implementation Timeline (Suggested)

```
Month 1 (December 2026)
  ├── PLAN-03: History endpoint           → 1 day
  ├── PLAN-04: Monthly retrain cron       → 0.5 days
  ├── PLAN-05: SPEI index                 → 1 day
  └── PLAN-06: ONI ENSO auto-ingest       → 1 day

Month 2 (January 2027)
  ├── PLAN-01: GEE VCI satellite          → 2 weeks
  └── PLAN-09: GeoJSON drought map        → 1 week

Month 3 (February 2027)
  ├── PLAN-07: WhatsApp/SMS alerts        → 1 week
  ├── PLAN-08: PMFBY insurance endpoint   → 1 week
  └── PLAN-02: IMD imdlib integration     → 2 weeks

Month 4–6 (March–May 2027)
  ├── PLAN-10: Reservoir live data        → 1 week
  ├── PLAN-11: CGWB groundwater          → 1 week
  ├── PLAN-12: Crop-specific risk         → 2 weeks
  └── PLAN-13: Offline PWA               → 1 month

Month 7–12 (June–December 2027)
  ├── PLAN-14: LLM Vernacular Chatbot     → 1 month
  ├── PLAN-15: Crop Disease Detection     → 2 months
  └── PLAN-16: Pan-India expansion        → 3-6 months

Research Track (Ongoing)
  ├── PLAN-17: LSTM model experiment
  └── PLAN-18: Federated Learning study
```

---

## Ideas Quick Reference

| ID | Feature | Tier | Effort | Cost | Status |
|---|---|---|---|---|---|
| PLAN-01 | NDVI + VCI from Google Earth Engine | 🟥 Critical | 2 weeks | ₹0 | Planned |
| PLAN-02 | IMD Gridded Rainfall via imdlib | 🟥 Critical | 2 weeks | ₹0 | Planned |
| PLAN-03 | Historical Time-Series API | 🟧 High | 1 day | ₹0 | Planned |
| PLAN-04 | Monthly Model Retraining Cron | 🟧 High | 0.5 days | ₹0 | Planned |
| PLAN-05 | SPEI Index Addition | 🟧 High | 1 day | ₹0 | Planned |
| PLAN-06 | El Niño ONI Auto-Ingestion | 🟧 High | 1 day | ₹0 | Planned |
| PLAN-07 | WhatsApp + SMS Push Alerts | 🟧 High | 3 days | ₹500/mo | Planned |
| PLAN-08 | PMFBY Insurance Verification | 🟧 High | 3 days | ₹0 | Planned |
| PLAN-09 | GeoJSON Live Drought Map | 🟨 Medium | 3–5 days | ₹0 | Planned |
| PLAN-10 | Maharashtra Reservoir Live Data | 🟨 Medium | 4 days | ₹0 | Planned |
| PLAN-11 | CGWB Groundwater Integration | 🟨 Medium | 5 days | ₹0 | Planned |
| PLAN-12 | Crop-Specific Risk Scores | 🟨 Medium | 2 weeks | ₹0 | Planned |
| PLAN-13 | Offline PWA Mobile App | 🟩 Strategic | 4 weeks | ₹0 | Planned |
| PLAN-14 | LLM Vernacular Chatbot (Kisan Sahayak) | 🟩 Strategic | 3 weeks | ₹2k/mo | Planned |
| PLAN-15 | Crop Disease Detection via Camera | 🟩 Strategic | 6 weeks | ₹0 | Planned |
| PLAN-16 | Pan-India Expansion | 🟩 Strategic | 3–6 months | Moderate | Planned |
| PLAN-17 | LSTM Temporal Sequence Model | 🔵 Research | 4–6 weeks | ₹0 | Research |
| PLAN-18 | Federated Learning for Farm Data | 🔵 Research | 8–12 weeks | ₹0 | Research |

---

*Future Plan Document — MahaRainRisk v2.0 and Beyond*  
*All timelines are estimates. Actual implementation depends on data access, testing results, and project priority.*
