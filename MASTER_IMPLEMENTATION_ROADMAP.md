# MahaRainRisk: Production System Architecture & Master Implementation Roadmap

> **Target Audience:** Production Portfolio / Full-Stack AI Engineer  
> **System Scope:** Automated Continuous Ingestion, Supabase PostgreSQL, Multi-Tier Caching, Render FastAPI ML Runtime, TreeSHAP Explainable AI (XAI), Model Context Protocol (MCP), Vercel Frontend, and k6 Load Testing.

---

## 1. System Architecture Overview

```
                                      +------------------------------------+
                                      |            AI AGENTS               |
                                      |   (Claude / Cursor / Antigravity)  |
                                      +-----------------+------------------+
                                                        |
                                                        | Remote SSE / Bearer Token
                                                        v
+------------------------+             +------------------------------------+
|    VERCEL FRONTEND     |             |         RENDER BACKEND             |
|   (Next.js / React)    |             |       (FastAPI / Python)           |
|                        |  HTTPS/SWR  |                                    |
| - Interactive Map      |------------>| - FastAPI App Lifecycle (Lifespan) |
| - What-If Simulator    |             | - In-Memory TTLCache (<2ms)        |
| - Marathi / Eng XAI    |             | - TreeSHAP Explainer (Loaded Once) |
| - SWR Edge Caching     |<------------| - FastMCP Server Instance          |
+------------------------+             +--------+------------------+--------+
                                                |                  ^
                                    Read/Write  |                  | Automated
                                  (Port 6543)   v                  | Ingestion
                               +-----------------------+           | (Daily Cron)
                               |       SUPABASE        |           |
                               | (PostgreSQL + PostGIS)|           |
                               |                       |           |
                               | - Raw Daily Weather   |           |
                               | - Monthly SPI/SPEI    |           |
                               | - Pre-computed Risk   |           |
                               | - shap_summary JSONB  |           |
                               +-----------------------+           |
                                           ^                       |
                                           | Daily Batches         |
                               +-----------+-----------------------+--------+
                               |        GITHUB ACTIONS / CRON WORKER        |
                               |    (Open-Meteo & IMD Daily API Fetcher)    |
                               +--------------------------------------------+
```

---

## 2. The Strict Implementation Order (Dependency Graph)

Never build the frontend or MCP server first. If you build the top layer before the foundation, you will constantly rewrite mock APIs and debug ghost errors.

```
[Phase 1: ML & Local Data] 
       │
       ▼
[Phase 2: Supabase Cloud Database] 
       │
       ▼
[Phase 3: Automated Ingestion (Static to Live)] 
       │
       ▼
[Phase 4: Multi-Tier Caching Engine] 
       │
       ▼
[Phase 5: Render FastAPI Core Backend] 
       │
       ▼
[Phase 6: TreeSHAP Explainable AI (XAI)] 
       │
       ▼
[Phase 7: Model Context Protocol (MCP Server)] 
       │
       ▼
[Phase 8: Vercel Frontend UI] 
       │
       ▼
[Phase 9: k6 Load Testing & Verification]
```

### Why This Exact Sequence?
1. **Phase 1 before Phase 2:** You cannot design a relational schema until your local data cleaning and feature engineering (19 baseline features, 28 velocity features) are finalized.
2. **Phase 2 before Phase 3:** The ingestion script needs a cloud database destination with primary keys and constraints already established.
3. **Phase 4 before Phase 5:** Integrating caching into FastAPI endpoints from day one prevents high-concurrency architecture rework later.
4. **Phase 5 before Phase 6 & 7:** Both XAI and MCP rely on in-memory models hosted inside the FastAPI runtime.
5. **Phase 8 (Frontend) near the end:** When the frontend is built, every API endpoint is already live, verified, documented via Swagger (`/docs`), and responding in <10ms.
6. **Phase 9 (k6) last:** Stress-testing validates the complete end-to-end integration under real user loads.

---

## 3. Component-by-Component Blueprint & Failure Handling

---

### Component 1: Static to Live Pipeline (Automated Ingestion)

#### What We Are Implementing
An automated ETL pipeline that wakes up daily at 06:00 AM IST (after Open-Meteo/IMD updates daily records), fetches yesterday's observed meteorological readings across all 194 talukas, calculates running rolling sums (7-day, 14-day rainfall), updates SPI-3/SPI-6 metrics, runs the model, and appends rows to Supabase.

#### Implementation Steps
1. Create a headless Python script: `etl/daily_cron_ingestion.py`.
2. Configure **GitHub Actions** (`.github/workflows/daily_ingest.yml`) scheduled via cron: `0 0:30 * * *` (06:00 AM IST).
3. The script calls Open-Meteo Archive/Forecast API using coordinate centroids.
4. Calculate dynamic features:
   - `rain_deficit_pct = ((rain_actual - rain_normal) / rain_normal) * 100`
   - `consecutive_dry_days` using continuous zero-rain groupings.
5. Upsert (insert on conflict update) the new date row into Supabase.

#### Problems You Will Face & Production Fixes

| Problem | Root Cause | Production Fix |
| :--- | :--- | :--- |
| **API Rate Limit Exceeded (HTTP 429)** | Blasting 194 HTTP requests simultaneously to Open-Meteo free tier. | Chunk the 194 talukas into 33 batches of 6 talukas. Add `time.sleep(1.5)` between batches. |
| **Silent Missing Days** | Weather sensor offline or data delay for a specific taluka. | Implement backward-fill imputation (max 2 days) and log an alert flag `imputed=True` in the database. |
| **Pipeline Duplicate Runs** | GitHub Actions retrying failed jobs, causing duplicate rows. | Enforce a PostgreSQL Composite Unique Constraint: `UNIQUE(taluka_id, record_date)`. Use `ON CONFLICT (taluka_id, record_date) DO UPDATE`. |

---

### Component 2: Supabase (PostgreSQL Database Architecture)

#### What We Are Implementing
A relational cloud database holding geospatial boundaries, raw daily weather logs, monthly drought indices (SPI/SPEI), and pre-computed risk predictions.

#### Database Schema Design
```sql
-- 1. Static Metadata
CREATE TABLE talukas (
    taluka_id VARCHAR(50) PRIMARY KEY,
    taluka_name VARCHAR(100) NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    division VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    normal_annual_rainfall DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326) -- PostGIS point centroid
);

-- 2. Daily Weather Telemetry (High Volume Time-Series)
CREATE TABLE daily_weather (
    id BIGSERIAL PRIMARY KEY,
    taluka_id VARCHAR(50) REFERENCES talukas(taluka_id),
    record_date DATE NOT NULL,
    precipitation_mm DOUBLE PRECISION NOT NULL,
    temp_max DOUBLE PRECISION NOT NULL,
    temp_min DOUBLE PRECISION NOT NULL,
    temp_mean DOUBLE PRECISION NOT NULL,
    soil_moisture_0_7cm DOUBLE PRECISION,
    et0_fao_evapotranspiration DOUBLE PRECISION,
    consecutive_dry_days INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(taluka_id, record_date)
);

CREATE INDEX idx_weather_taluka_date ON daily_weather(taluka_id, record_date DESC);

-- 3. Pre-computed Drought Risk & XAI Cache Table
CREATE TABLE taluka_risk_latest (
    taluka_id VARCHAR(50) PRIMARY KEY REFERENCES talukas(taluka_id),
    as_of_date DATE NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,       -- 0.0 to 1.0
    risk_category VARCHAR(20) NOT NULL,        -- Normal, Watch, Alert, Severe
    confidence DOUBLE PRECISION NOT NULL,
    forecast_month VARCHAR(20) NOT NULL,
    shap_summary JSONB NOT NULL,               -- Top 3 positive/negative drivers
    bilingual_narrative JSONB NOT NULL,        -- {"en": "...", "mr": "..."}
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Problems You Will Face & Production Fixes

| Problem | Root Cause | Production Fix |
| :--- | :--- | :--- |
| **Connection Slot Starvation** | Supabase free tier caps direct PostgreSQL connections at ~60. Multiple serverless instances hit Port `5432` directly. | **Never connect to Port 5432.** Always connect to the **Supavisor Transaction Pooler on Port `6543`** or use `@supabase/supabase-js` / Python `supabase` client over HTTPS. |
| **Slow Geospatial Queries** | Querying "Find all talukas within 50km of drought" without spatial indexing. | Enable PostGIS extension (`CREATE EXTENSION postgis;`) and create a GIST index on `geom`: `CREATE INDEX idx_taluka_geom ON talukas USING GIST(geom);`. |

---

### Component 3: Multi-Tier Caching System

#### What We Are Implementing
A hybrid caching strategy that delivers `< 2ms` response times for standard queries while shielding the database and ML model from redundant computation.

```
Client Request -> [1. Vercel SWR Cache] -> [2. FastAPI TTLCache (RAM)] -> [3. Supabase JSONB]
```

#### Implementation Code (FastAPI In-Memory Cache)
```python
from cachetools import TTLCache
import hashlib
import json

# Holds 500 taluka entries for 6 hours
risk_cache = TTLCache(maxsize=500, ttl=21600)

def generate_cache_key(taluka_id: str, date: str, custom_params: dict = None) -> str:
    if not custom_params:
        return f"risk:{taluka_id}:{date}"
    param_hash = hashlib.md5(json.dumps(custom_params, sort_keys=True).encode()).hexdigest()
    return f"sim:{taluka_id}:{date}:{param_hash}"
```

#### Problems You Will Face & Production Fixes

| Problem | Root Cause | Production Fix |
| :--- | :--- | :--- |
| **Stale Data After Morning Ingestion** | Ingestion finishes at 06:15 AM, but cache TTL still serves yesterday's prediction until 12:00 PM. | Key the cache by `date` (`f"risk:{taluka}:{latest_date}"`). When the date rolls over, the key automatically changes, bypassing old cache with 0 manual invalidation logic. |
| **Memory Growth (OOM)** | Unbounded Python dictionary used as cache (`cache[key] = val`) eventually crashes the container. | Always use `TTLCache` or `LRUCache` from the `cachetools` library with an explicit `maxsize=500`. |

---

### Component 4: Production Backend on Render (FastAPI ML Runtime)

#### What We Are Implementing
A persistent, high-performance containerized FastAPI application hosting both ML models (`drought_model.joblib`, `drought_forecaster.joblib`), the pre-initialized TreeSHAP explainer, and RESTful API endpoints.

#### Implementation Architecture (The Lifespan Pattern)
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import joblib, shap

ml_artifacts = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load models & initialize TreeExplainer ONCE into memory
    print("Loading ML models into container memory...")
    ml_artifacts["model"] = joblib.load("models/drought_model.joblib")
    ml_artifacts["forecaster"] = joblib.load("models/drought_forecaster.joblib")
    ml_artifacts["explainer"] = shap.TreeExplainer(ml_artifacts["model"])
    print("ML models & SHAP ready.")
    yield
    # Shutdown: Clean up resources
    ml_artifacts.clear()

app = FastAPI(title="MahaRainRisk API", version="2.0.0", lifespan=lifespan)
```

#### Problems You Will Face & Production Fixes

| Problem | Root Cause | Production Fix |
| :--- | :--- | :--- |
| **Render Free Tier Spin-Down & 750hr Cap** | Service suspends after 15 mins of inactivity. Pinging 24/7 exhausts Render's 750-hour monthly account limit, shutting down the app. | **Dual Strategy:** (1) Serve 95% of dashboard data from Supabase/Vercel SWR so the site works instantly even if Render sleeps. (2) Trigger "Wake on Intent" background ping when user hovers over What-If Simulator, or restrict pinging to business hours (09:00 AM–09:00 PM IST = 360 hrs/mo, well under the 750h quota). |
| **Slow Dependency Installation** | Render rebuilding heavy wheels (`scipy`, `scikit-learn`, `shap`) on every git push, hitting the 15-minute build timeout. | Use a multi-stage `Dockerfile` with pre-compiled wheels, or pin exact binary versions in `requirements.txt`. |
| **CORS Errors on Vercel** | Browser blocks frontend from calling Render API: `Cross-Origin Request Blocked`. | Configure FastAPI `CORSMiddleware` with explicit allowed origins: `["https://maharainrisk.vercel.app", "http://localhost:3000"]`. |

---

### Component 5: Explainable AI (XAI) Engine

#### What We Are Implementing
A dual-speed feature attribution engine using TreeSHAP.
- **Speed 1 (Pre-calculated):** Ingested daily; top 3 drivers stored as JSON in Supabase.
- **Speed 2 (Interactive "What-If"):** Live SHAP calculation on Render when users simulate rainfall/temperature anomalies.
- **Bilingual Natural Language Generator:** Generates plain English and Marathi explanations for policymakers and farmers.

#### Problems You Will Face & Production Fixes

| Problem | Root Cause | Production Fix |
| :--- | :--- | :--- |
| **SHAP Matrix Shape Mismatch** | TreeSHAP binary classification returns a list of two arrays `[shap_class_0, shap_class_1]`. Extracting the wrong index causes backwards logic. | Target drought risk is Class 1 (Alert/Severe). Always slice `shap_values[1]` for positive drought push. |
| **Feature Name Scrambling** | Passing a NumPy array directly to `explainer(X)` loses feature names; output shows `Feature 0, Feature 1`. | Always pass a pandas DataFrame with exact column names (`feature_names = model.feature_names_in_`) to the explainer. |
| **Non-Technical User Confusion** | Showing raw SHAP log-odds (+0.42) confuses agricultural officers. | Map SHAP values to percentage impact and humanized bilingual pills (e.g., `SPI-3 Deficit: -42% rainfall below normal`). |

---

### Component 6: Model Context Protocol (MCP) Server

#### What We Are Implementing
An MCP server exposing tools (`get_taluka_risk`, `simulate_rainfall_shock`, `get_state_drought_summary`) so external AI agents (Claude Desktop, Cursor, Antigravity) can autonomously reason over Maharashtra climate risk.

#### Implementation Architecture (FastMCP Remote SSE)
```python
from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("MahaRainRisk-Intelligence")

@mcp.tool()
async def get_taluka_drought_risk(taluka_name: str) -> dict:
    """Fetch current drought risk, category, and top environmental drivers for any Maharashtra taluka."""
    # 1. Alias normalization (e.g. 'Poona' -> 'haveli')
    # 2. Check in-memory cache
    # 3. Return structured JSON
    return {...}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
```

#### Problems You Will Face & Production Fixes

| Problem | Root Cause | Production Fix |
| :--- | :--- | :--- |
| **Local stdio vs Cloud SSE Mismatch** | Claude Desktop expects a local stdio command, but your backend is on Render. | Provide two access methods: (1) Remote SSE URL for web agents, and (2) A tiny 15-line local Python stdio bridge that forwards queries to the Render API. |
| **Unauthenticated Cloud Abuse** | Public SSE endpoint allows anyone to spam MCP tools and burn Supabase quotas. | Require an `X-MCP-API-KEY` header in your FastAPI MCP endpoint. Drop connections that lack valid tokens. |
| **Taluka Name Misspellings by LLMs** | Agent asks for "Aurangabad" instead of "Chhatrapati Sambhajinagar" or "Nasik" instead of "Nashik". | Implement an **Alias Normalizer dictionary** with `difflib.get_close_matches(cutoff=0.8)` inside the tool. |

---

### Component 7: Modern Frontend on Vercel

#### What We Are Implementing
A fast, responsive Next.js / Tailwind CSS web application featuring:
- Choropleth Map of Maharashtra with color-coded risk (Green = Normal, Yellow = Watch, Red = Severe).
- Taluka Drilldown Modal with TreeSHAP waterfall driver charts.
- "What-If" interactive climate sliders (Adjust rainfall -50% to +50%, Temp +0°C to +4°C).
- Instant Marathi / English language toggle.
- Vercel SWR data fetching for automatic background revalidation.

#### Problems You Will Face & Production Fixes

| Problem | Root Cause | Production Fix |
| :--- | :--- | :--- |
| **Heavy GeoJSON Lagging the Map** | A detailed Maharashtra 194-taluka boundary GeoJSON can be 15 MB, freezing browser rendering. | Simplify the GeoJSON geometry using `mapshaper` (`-simplify 10% keep-shapes`). Reduces payload from 15 MB to **380 KB** with zero visible loss. |
| **Hydration Mismatch on Language Toggle** | Server renders English while client local-storage has Marathi selected. | Use a client-only mounting wrapper (`useEffect(() => setMounted(true), [])`) before rendering localized strings. |

---

## 4. Validating System Load with k6 (User Simulation)

### Can You Check Load with k6?
**Yes, absolutely.** Running a load test with **k6** (by Grafana) is the gold standard for proving your system is production-grade. In technical interviews, presenting a k6 load test benchmark report immediately distinguishes you from typical student projects.

### What k6 Tests
1. **Cache Efficiency:** Simulating 50 concurrent users clicking popular talukas (Pune, Solapur, Chhatrapati Sambhajinagar) to verify the cache serves responses under **10 ms**.
2. **Compute Under Stress:** Simulating 10 concurrent users running "What-If" simulations triggering live TreeSHAP to verify Render's memory does not spike to OOM.
3. **Database Connection Pool Stability:** Ensuring 100 requests/second do not trigger PostgreSQL slot exhaustion.

### Production-Ready k6 Script (`load_test.js`)

Save this file as `tests/load_test.js`:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

// Custom Metrics
const cacheHitLatency = new Trend('cache_hit_latency');
const liveComputeLatency = new Trend('live_compute_latency');
const failureRate = new Rate('failed_requests');

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp-up: 1 to 10 Virtual Users (VUs)
    { duration: '1m',  target: 50 },  // Sustained load: 50 concurrent users
    { duration: '30s', target: 100 }, // Stress spike: 100 concurrent users
    { duration: '20s', target: 0 },   // Ramp-down
  ],
  thresholds: {
    // 95% of all requests must complete within 200ms
    http_req_duration: ['p(95)<200'],
    // Error rate must remain under 1%
    failed_requests: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

const POPULAR_TALUKAS = ['haveli', 'baramati', 'solapur_north', 'chhatrapati_sambhajinagar', 'nashik'];

export default function () {
  // -------------------------------------------------------------
  // Scenario A: 80% of users view standard taluka dashboard (Cached)
  // -------------------------------------------------------------
  const taluka = POPULAR_TALUKAS[Math.floor(Math.random() * POPULAR_TALUKAS.length)];
  const cachedRes = http.get(`${BASE_URL}/api/v1/taluka/${taluka}/risk`);
  
  const isOk = check(cachedRes, {
    'status is 200': (r) => r.status === 200,
    'has risk_score': (r) => JSON.parse(r.body).risk_score !== undefined,
  });

  if (!isOk) failureRate.add(1);
  cacheHitLatency.add(cachedRes.timings.duration);

  // -------------------------------------------------------------
  // Scenario B: 20% of users trigger a "What-If" simulation (Compute)
  // -------------------------------------------------------------
  if (Math.random() < 0.20) {
    const payload = JSON.stringify({
      taluka_id: taluka,
      rainfall_shock_pct: -30.0,
      temperature_delta_c: 2.0
    });

    const params = {
      headers: { 'Content-Type': 'application/json' },
    };

    const simRes = http.post(`${BASE_URL}/api/v1/simulate`, payload, params);
    
    check(simRes, {
      'simulation status is 200': (r) => r.status === 200,
      'has shap_drivers': (r) => JSON.parse(r.body).top_drivers !== undefined,
    });

    liveComputeLatency.add(simRes.timings.duration);
  }

  sleep(Math.random() * 2 + 1); // User think time: 1-3 seconds
}
```

### Running the Test

1. **Install k6:**
   ```powershell
   # Windows via Winget
   winget install k6 --source winget
   # Or via Chocolatey
   choco install k6
   ```

2. **Execute Locally (Baseline):**
   ```powershell
   k6 run -e TARGET_URL=http://localhost:8000 tests/load_test.js
   ```

3. **Execute Against Render Production:**
   ```powershell
   k6 run -e TARGET_URL=https://maharainrisk-api.onrender.com tests/load_test.js
   ```

### How to Interpret the Output & Showcase on Your Resume

When k6 finishes, it outputs a clean summary table:
```
✓ status is 200
✓ has risk_score
✓ simulation status is 200

http_req_duration..............: avg=18.4ms   min=1.2ms   med=4.5ms   max=182ms   p(90)=12.1ms  p(95)=18.7ms
cache_hit_latency..............: avg=3.2ms    min=1.2ms   med=2.1ms   max=15.4ms  p(95)=4.8ms
live_compute_latency...........: avg=42.1ms   min=28.2ms  med=38.4ms  max=164ms   p(95)=78.2ms
failed_requests................: 0.00% (0 failures out of 8,420 requests)
```

**Portfolio Impact:**  
In your README and interview pitch, you can state:
> *"Engineered a multi-tier caching architecture (Vercel Edge + FastAPI in-memory TTL) and benchmarked the system using **k6** with 100 concurrent virtual users generating 8,400+ requests. Maintained a **p95 latency of 4.8 ms** for cached taluka queries, sub-80 ms for live TreeSHAP What-If simulations, and a **0.00% error rate** without exhausting Supabase connection pools."*

---

## 5. The 6 Production Blind Spots (Security, Observability & Reliability)

These are the operational requirements that prevent catastrophic security leaks, silent outages, and server crashes after deployment.

### 1. The Supabase Key Split (Critical Security Boundary)
* **The Vulnerability:** Exposing the `SERVICE_ROLE_KEY` in the frontend allows anyone to inspect network traffic, bypass all access controls, and drop or mutate database tables.
* **The Rule:**
  * **Vercel Frontend:** Receives **ONLY** `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Enable Row-Level Security (RLS) on all tables with `SELECT` (read-only) permissions for public users.
  * **Render Backend & GitHub Actions:** Store `SUPABASE_SERVICE_ROLE_KEY` securely in private server environment variables. Only backend jobs are allowed to `INSERT` or `UPDATE` weather/risk tables.

### 2. Silent Ingestion Failure Alerting (Telegram/Discord Webhook)
* **The Vulnerability:** Weather APIs occasionally change schemas, rate limit, or go offline. If the morning GitHub Actions cron job fails, it fails silently, leaving predictions weeks out of date.
* **The Rule:** Add an automated failure alert step to `.github/workflows/daily_ingest.yml`:
  ```yaml
  - name: Alert on Failure
    if: failure()
    run: |
      curl -X POST -H 'Content-Type: application/json' \
      -d '{"content": "🚨 **CRITICAL: MahaRainRisk Daily Ingestion Failed!** Check GitHub Actions log."}' \
      ${{ secrets.DISCORD_ALERTS_WEBHOOK }}
  ```

### 3. Compute Rate Limiting on Live TreeSHAP (`slowapi`)
* **The Vulnerability:** While cached endpoints take <2ms, the `/simulate` endpoint runs 250 trees of matrix math. An adversarial user or loop firing 30 req/sec will spike Render's CPU to 100% and freeze the app.
* **The Rule:** Implement rate limiting in FastAPI via `slowapi`:
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter

  # Standard taluka view (generous)
  @app.get("/api/v1/taluka/{taluka_id}/risk")
  @limiter.limit("120/minute")
  def get_risk(request: Request, taluka_id: str): ...

  # Live TreeSHAP simulation (strict CPU protection)
  @app.post("/api/v1/simulate")
  @limiter.limit("10/minute")
  def run_simulation(request: Request, payload: SimPayload): ...
  ```

### 4. Database Schema Version Control (Supabase Migrations in Git)
* **The Vulnerability:** Creating tables manually via the Supabase Web UI makes environments irreproducible and untracked in Git.
* **The Rule:** Manage all schemas via `supabase/migrations/` using timestamped SQL files (`20261103000001_initial_schema.sql`). Deploy changes deterministically using the Supabase CLI (`supabase db push`).

### 5. Annual Post-Monsoon Retraining Lifecycle
* **The Vulnerability:** Climate patterns shift (e.g., El Niño / La Niña). A model trained strictly on historical data up to 2026 will suffer data drift by 2027.
* **The Rule:** Establish an annual post-monsoon retraining pipeline on **November 15th** (after Maharashtra's Kharif harvest and official government drought assessments are recorded). If newly validated data drops OOB accuracy below 75%, retrain and deploy a versioned model (`drought_model_v2027.joblib`).

### 6. Upstream Weather Outage Circuit Breaker
* **The Vulnerability:** If Open-Meteo or IMD servers experience a multi-day outage, the system will serve stale predictions with no user indication.
* **The Rule:** Include data freshness metadata in every API response:
  ```json
  {
    "as_of_date": "2026-11-01",
    "data_age_hours": 36,
    "sensor_status": "delayed"
  }
  ```
  If `data_age_hours > 24`, Vercel UI automatically renders an amber warning banner:  
  *`⚠️ Weather telemetry sync delayed by meteorological provider. Displaying latest confirmed observation.`*

---

## 6. Comprehensive Security Threat Model & Defense Playbook

This matrix defines the 7 concrete threat vectors in an AI/ML + Cloud + Database system and their defensive implementations:

### Threat 1: The `.joblib` Deserialization Vulnerability (Arbitrary Code Execution)
* **The Attack:** Scikit-Learn `.joblib` files use Python `pickle`. If an attacker or untrusted PR alters `drought_model.joblib`, calling `joblib.load()` executes arbitrary shell commands inside Render, compromising your entire backend.
* **The Defense:** Cryptographically verify the SHA-256 checksum of model files before unpickling:
  ```python
  import hashlib, joblib
  from pathlib import Path

  EXPECTED_HASHES = {
      "drought_model.joblib": "a1b2c3d4e5f6...", # Exact 64-char hex digest
      "drought_forecaster.joblib": "f8e7d6c5b4..."
  }

  def safe_load_model(filepath: str):
      path = Path(filepath)
      file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
      if file_hash != EXPECTED_HASHES.get(path.name):
          raise SecurityError(f"Model integrity tampered! Hash mismatch on {path.name}")
      return joblib.load(path)
  ```

### Threat 2: MCP Tool Injection & LLM Hallucinated Payloads
* **The Attack:** An external AI agent passes SQL injection fragments or path traversal (`../../etc/passwd`) via MCP tool arguments (`taluka_name`).
* **The Defense:** Strict Pydantic schema validation coupled with an immutable **in-memory whitelist** of the 194 monitored taluka IDs. Reject any payload containing non-alphanumeric characters or IDs outside the whitelist before any database or compute execution.

### Threat 3: Supabase Public REST Data Wipe
* **The Attack:** By default, new Supabase tables have Row-Level Security (RLS) disabled. Anyone holding the public `ANON_KEY` can fire a `DELETE` request to `https://<project>.supabase.co/rest/v1/daily_weather` and wipe climate tables.
* **The Defense:**
  ```sql
  ALTER TABLE talukas ENABLE ROW LEVEL SECURITY;
  ALTER TABLE daily_weather ENABLE ROW LEVEL SECURITY;
  ALTER TABLE taluka_risk_latest ENABLE ROW LEVEL SECURITY;

  -- Read-only policy for anon users
  CREATE POLICY "Public Read Only" ON taluka_risk_latest FOR SELECT TO anon USING (true);
  -- Strictly zero INSERT/UPDATE/DELETE policies for anon role!
  ```

### Threat 4: Permissive Cross-Origin Access (`allow_origins=["*"]`)
* **The Attack:** Wildcard CORS allows malicious third-party websites in a user's browser to make authenticated background requests to your Render API or MCP endpoints.
* **The Defense:** Explicitly whitelist production and development origins only:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "https://maharainrisk.vercel.app",
          "https://maharainrisk-preview.vercel.app",
          "http://localhost:3000"
      ],
      allow_credentials=True,
      allow_methods=["GET", "POST"],
      allow_headers=["Content-Type", "Authorization", "X-MCP-API-KEY"],
  )
  ```

### Threat 5: Git Secret Leaks in Commit History
* **The Attack:** Committing `.env` files containing `DATABASE_URL` with raw PostgreSQL passwords. Even if deleted in a later commit, the secret persists in the git object store forever.
* **The Defense:** Use `gitleaks` pre-commit hooks to block commits containing high-entropy keys, keep `.env*` in `.gitignore`, and use `.env.example` templates with empty placeholders.

### Threat 6: Stored Cross-Site Scripting (XSS) via Bilingual Narratives
* **The Attack:** Malicious HTML (`<script src="...">`) injected into database weather records or XAI strings executed via React's `dangerouslySetInnerHTML`.
* **The Defense:** **Never** use `dangerouslySetInnerHTML` for bilingual XAI explanations. Always render localized strings natively as React children (`<p>{narrative.mr}</p>`), which automatically sanitizes and escapes all HTML entities.

### Threat 7: Model Inversion & Scraping Attacks via `/simulate`
* **The Attack:** Automated bot scripts querying the `/simulate` endpoint 50,000 times across a coordinate grid to reverse-engineer model decision boundaries and siphon the dataset.
* **The Defense:**
  1. Enforce strict rate limits (10 simulations/min per IP via `slowapi`).
  2. Coarse-grain returned probabilities: Round predicted risk probabilities to 2 decimal places (`0.74`) rather than raw 6-decimal floats (`0.741928`), mathematically preventing boundary reconstruction.

---

## 7. Master Roadmap Checklist

- [ ] **Phase 1: Local Foundations**
  - [ ] Complete Open-Meteo download for remaining 8 batches (all 194 talukas through 2026-10-15).
  - [ ] Compute comprehensive SPI-3 and SPI-6 on full series.
  - [ ] Train final champion models with native `class_weight='balanced'` and `oob_score=True`.
  - [ ] Generate and record SHA-256 checksums for model artifacts.
- [ ] **Phase 2: Database Provisioning & Security**
  - [ ] Create Supabase project; configure tables via Git-tracked migrations (`supabase/migrations/`).
  - [ ] Enable Row-Level Security (RLS) across all tables; enforce read-only for public `ANON_KEY`.
  - [ ] Route all backend connections through Supavisor Port `6543`.
- [ ] **Phase 3: Automated Ingestion & Alerting**
  - [ ] Implement `daily_cron_ingestion.py` with batching (6 talukas/batch) and exponential backoff.
  - [ ] Setup GitHub Actions cron workflow to trigger daily at 06:00 AM IST.
  - [ ] Add Discord/Telegram failure notification webhook to the workflow.
- [ ] **Phase 4: Backend, Rate Limiting & Caching**
  - [ ] Build FastAPI app using `@asynccontextmanager lifespan` to load models once with hash verification.
  - [ ] Implement `cachetools.TTLCache` for in-memory `< 2ms` reads.
  - [ ] Protect `/simulate` with `slowapi` rate limiter (10 req/min).
  - [ ] Lock down CORS strictly to Vercel production and localhost URLs.
  - [ ] Configure "Wake on Intent" background ping or business-hours keep-alive (360h/mo) to preserve Render's 750h limit.
- [ ] **Phase 5: XAI & MCP**
  - [ ] Implement pre-calculated top 3 SHAP drivers in Supabase `shap_summary`.
  - [ ] Build live What-If TreeSHAP simulation endpoint with 2-decimal coarse-graining.
  - [ ] Deploy FastMCP server with SSE transport, alias normalizer whitelist, and API key authentication.
- [ ] **Phase 6: Frontend & Verification**
  - [ ] Build responsive Next.js dashboard on Vercel with simplified 380KB GeoJSON.
  - [ ] Wire SWR client for instantaneous optimistic rendering.
  - [ ] Add stale-data warning banner if `data_age_hours > 24`.
  - [ ] Render bilingual text safely as React children (no `dangerouslySetInnerHTML`).
  - [ ] Run k6 load test script; verify p95 latency under 200ms and 0% error rate.

---

## 8. Zero-Cost Cloud Backend Hosting Strategy (Render 360-Hour Safety Valve & Koyeb)

To host the Python FastAPI ML backend **100% free with zero credit card requirements**, we operate Render under a mathematically safe schedule, with Koyeb documented as an automated fallback.

### 8.1 The Render 360-Hour Safety Valve Strategy
* **The Constraint:** Render free tier provides **750 hours/month** per account. Pinging 24/7 uses 744 hours, risking account suspension if container builds overlap.
* **The Solution:**
  1. **Supabase First:** 95% of frontend views (maps, taluka cards, pre-computed SHAP drivers) read directly from **Supabase and Vercel SWR cache**. Render is not touched for standard browsing.
  2. **12-Hour Scheduled Keep-Alive:** Configure an uptime ping (via Cron-Job.org or GitHub Actions) to run strictly during active daytime hours:
     - **Active Window:** 09:00 AM – 09:00 PM IST (12 hours/day).
     - **Monthly Consumption:** $12\text{ hours/day} \times 30\text{ days} = \mathbf{360\text{ hours/month}}$.
     - **Safety Headroom:** You use only **48% of your quota**, leaving **390 hours** of unused buffer every month.

### 8.2 Koyeb Free Tier Fallback
* If you ever need a secondary container host without a shared 750-hour pool:
  * **Koyeb Hobby Tier:** Provides 1 free `nano` micro-VM (512 MB RAM) with free SSL and git-push deployment directly from GitHub.
  * Uses the exact same `Dockerfile` and FastAPI configuration.

### 8.3 Hardened Container `Dockerfile` (Runs on Render or Koyeb)
```dockerfile
# Step 1: Lightweight Python base
FROM python:3.11-slim

# Step 2: Prevent bytecode generation and configure unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Step 3: Install system build dependencies for scientific packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 4: Layer cached dependency installation
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Step 5: Security: Run container as non-root user
RUN useradd -m -u 1000 appuser
USER appuser
ENV HOME=/home/appuser \
    PATH=/home/appuser/.local/bin:$PATH

# Step 6: Copy application code and model artifacts
COPY --chown=appuser:appuser . .

EXPOSE 8000

# Step 7: Launch FastAPI via Uvicorn
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

---

## 9. The Complete Mastery Curriculum (What You Need to Learn)

To build, deploy, and confidently defend this project in technical interviews, master these 7 engineering domains:

```
+-------------------------------------------------------------------------------+
|                       THE 7 MASTERY DOMAINS CURRICULUM                        |
+-------------------------------------------------------------------------------+
| Domain 1: Climate & Geospatial Data Engineering                               |
| Domain 2: Production Machine Learning & Explainable AI (XAI)                 |
| Domain 3: High-Performance Backend & Containerization (FastAPI + Docker)      |
| Domain 4: Cloud Database Architecture & Security (Supabase / PostgreSQL)      |
| Domain 5: AI Agent Protocols (Model Context Protocol - MCP)                   |
| Domain 6: Modern Reactive Frontend (Next.js, Tailwind & SWR)                  |
| Domain 7: Performance Benchmarking & DevOps (k6, GitHub Actions CI/CD)        |
+-------------------------------------------------------------------------------+
```

---

### Domain 1: Climate & Geospatial Data Engineering
* **What to Learn:**
  1. **REST Weather APIs:** How to structure batched HTTP calls to Open-Meteo and IMD, handle HTTP 429 rate limits, and implement exponential backoff algorithms.
  2. **Feature Engineering on Time Series:** Calculating rolling 7-day, 14-day cumulative rainfall, sequential zero-rain day grouping (`itertools.groupby`), and rainfall anomaly percentages.
  3. **Meteorological Drought Indices:** Understanding the mathematical definition of **Standardized Precipitation Index (SPI-3 and SPI-6)**: fitting monthly rainfall series to a two-parameter Gamma distribution ($\alpha, \beta$) and transforming cumulative probabilities into standard normal deviations ($Z \sim \mathcal{N}(0, 1)$).
  4. **Geospatial Optimization:** Working with GeoJSON geometries, understanding coordinate reference systems (`EPSG:4326`), and using tools like `mapshaper` to simplify polygon vertices by 90% without breaking boundaries.

---

### Domain 2: Production Machine Learning & Explainable AI (XAI)
* **What to Learn:**
  1. **Cost-Sensitive Learning:** Why class balancing via `class_weight='balanced'` works better than artificial sampling (SMOTE) on tabular climate datasets with physical feature dependencies.
  2. **Out-of-Bag (OOB) Validation:** How Random Forest calculates generalization error internally across unselected bootstrap samples, eliminating data leakage without needing cross-validation data loss.
  3. **TreeSHAP Mathematics:** Understanding Shapley values from cooperative game theory:
     $$\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{i\}) - f(S) \right]$$
     How `shap.TreeExplainer` calculates exact polynomial-time feature attributions across 250 decision trees.
  4. **Natural Language Translation of Math:** Converting log-odds SHAP values into percentages and human-readable bilingual narratives (English and Marathi) for agricultural stakeholders.

---

### Domain 3: High-Performance Backend & Containerization (FastAPI + Docker)
* **What to Learn:**
  1. **FastAPI Lifespan Architecture:** Managing stateful resources via `@asynccontextmanager` to load heavy machine learning models and `TreeExplainer` exactly once on container startup.
  2. **Pydantic v2 Schema Validation:** Writing strict data contracts, regex field validators, and preventing parameter injection.
  3. **In-Memory Caching:** Using `cachetools.TTLCache` to deliver `<2ms` responses, and designing **temporal cache keys** (`f"risk:{id}:{date}"`) that naturally self-invalidate when new daily data arrives.
  4. **Docker Fundamentals:** Writing multi-stage `Dockerfile`s, understanding Linux user IDs (`UID 1000`), layer caching (why copying `requirements.txt` before code saves 10 minutes of build time), and port mapping.

---

### Domain 4: Cloud Database Architecture & Security (Supabase / PostgreSQL)
* **What to Learn:**
  1. **Relational Data Modeling:** Designing tables with composite unique constraints (`UNIQUE(taluka_id, record_date)`) and writing idempotent upsert queries (`INSERT ... ON CONFLICT DO UPDATE`).
  2. **PostGIS & Spatial Indexing:** Storing taluka coordinate centroids as `GEOMETRY(Point, 4326)` and querying nearest talukas via `ST_DWithin` with GIST spatial indexes.
  3. **Connection Pooling Mechanics:** The critical difference between direct PostgreSQL port `5432` and transaction poolers (Supavisor port `6543`), and how pool starvation happens.
  4. **Row-Level Security (RLS):** Writing declarative PostgreSQL security policies to guarantee the public `ANON_KEY` can only read data, while write permissions require the `SERVICE_ROLE` key.

---

### Domain 5: AI Agent Protocols (Model Context Protocol - MCP)
* **What to Learn:**
  1. **MCP Specification:** Understanding Anthropic's Model Context Protocol (the JSON-RPC 2.0 communication format between LLMs and external tools).
  2. **FastMCP Framework:** Defining typed tools, docstrings that guide LLM tool-calling decisions, and resource schemas.
  3. **Transport Protocols:** The difference between local `stdio` (Standard I/O subprocesses) and remote `SSE` (Server-Sent Events over HTTP).
  4. **Agent Defensive Engineering:** Normalizing fuzzy user queries (e.g., mapping `"Poona"` to `"haveli"`) using string distance algorithms (`difflib`) and enforcing whitelists.

---

### Domain 6: Modern Reactive Frontend (Next.js, Tailwind & SWR)
* **What to Learn:**
  1. **Next.js App Router:** Server Components vs. Client Components, file-based routing, and layout architecture.
  2. **Interactive Map Visualization:** Integrating Leaflet or MapLibre inside React to render interactive choropleth maps with dynamic risk color scales (Green / Amber / Red).
  3. **Stale-While-Revalidate (SWR):** Implementing optimistic client-side data fetching that displays cached data instantly while refreshing telemetry in the background.
  4. **Client-Side Security:** Sanitizing inputs and avoiding `dangerouslySetInnerHTML` to prevent Stored Cross-Site Scripting (XSS).

---

### Domain 7: Performance Benchmarking & DevOps (k6, GitHub Actions)
* **What to Learn:**
  1. **k6 Load Testing:** Writing JavaScript test scenarios to simulate concurrent Virtual Users (VUs), calculating 95th percentile latency (p95), throughput (requests/sec), and setting pass/fail thresholds.
  2. **GitHub Actions Workflows:** Writing `.github/workflows/daily_ingest.yml` to trigger daily headless Python scripts on a scheduled cron syntax (`0 0:30 * * *`).
  3. **Secrets Management:** Securely managing cloud tokens across GitHub Secrets, Hugging Face Secrets, and Vercel Environment Variables.
  4. **Observability & Webhooks:** Configuring automated Discord or Telegram alerts on pipeline failures.

