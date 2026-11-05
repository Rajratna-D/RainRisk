# 🚀 MahaRainRisk: Cloud Deployment Guide (Render & PaaS)

> **Live Deployment Blueprint:** Deploy the unified MahaRainRisk Agritech Platform (FastAPI + Liquid Glass Landing Page + Taluka Dashboard + Neural Audio) on **Render.com** with automated zero-downtime CI/CD.

---

## 📌 Architecture Overview

MahaRainRisk is packaged as a **single unified high-performance ASGI service**:
* **Frontend:** Single-Page Application (`frontend/index.html`) featuring the Liquid Glass Landing Page with scroll convergence and the Obsidian-Emerald Taluka Dashboard.
* **Backend:** FastAPI asynchronous REST API engine (`backend/main.py`) serving live telemetry, dual-mode ML predictions, and static assets.
* **ML Inference Engine:** Pre-trained Random Forest diagnostic (`ml/drought_model.joblib`) and 30-day early warning forecaster (`ml/drought_forecaster.joblib`) loaded into memory at startup.
* **Audio Engine:** Microsoft Edge neural speech synthesis (`mr-IN-ManoharNeural` / `en-IN-PrabhatNeural`) with disk caching.

---

## 🛠️ Deployment Configuration Files

| File | Purpose | Target Environment |
| :--- | :--- | :--- |
| **`render.yaml`** | Declarative Infrastructure-as-Code Blueprint | Render.com |
| **`Procfile`** | PaaS web process definition | Render, Railway, Heroku |
| **`runtime.txt`** | Pins Python interpreter version (`python-3.11.9`) | PaaS buildpacks |
| **`requirements.txt`** | Lean production runtime dependencies (under 150 MB build footprint) | Render (512 MB RAM safe) |
| **`requirements-dev.txt`** | Full development dependencies including Jupyter, Geopandas & Matplotlib | Local development |
| **`.gitignore`** | Excludes 254 MB raw `.grd` binary files, audio cache, and temp docs | GitHub repository |

---

## 🚀 1-Click Deployment on Render.com

### Step 1: Push Code to GitHub
Ensure all production files are committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "Deploy: Unified MahaRainRisk platform"
git push origin main
```

### Step 2: Connect Render to Repository
1. Log into your dashboard at [https://dashboard.render.com](https://dashboard.render.com).
2. Click **New +** in the top right and select **Blueprint** (or **Web Service**).
3. Connect your GitHub repository: `https://github.com/Rajratna-D/RainRisk`.
4. Render automatically detects `render.yaml` and sets up:
   * **Service Type:** Web Service
   * **Runtime:** Python 3.11.9
   * **Region:** Singapore (or closest to India for minimal latency)
   * **Plan:** Free
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   * **Health Check Path:** `/health`

### Step 3: Verify Live Multi-Tier Architecture
Once deployed, verify the three integrated cloud tiers:
1. **Frontend (Cloudflare Pages):** Open `https://maharainrisk.pages.dev/` to view the ultra-fast landing page and taluka dashboard.
2. **Backend Health (Render):** Open `https://rainrisk-vcra.onrender.com/health` in your browser. It returns:
   ```json
   {
     "status": "healthy",
     "platform": "MahaRainRisk Agritech",
     "talukas_covered": 194,
     "districts_covered": 36,
     "models": {
       "mode_1_diagnostic": "250-Tree Random Forest (98% accuracy)",
       "mode_2_forecaster": "30-Day Early Warning Forecaster (77% accuracy)"
     }
   }
   ```
3. **Interactive Swagger Documentation:** Accessible at `https://rainrisk-vcra.onrender.com/docs`.
4. **FastMCP Agent Endpoint:** Accessible at `https://rainrisk-vcra.onrender.com/mcp`.

---

## ⚙️ Manual Deployment Settings (If Not Using Blueprint)

If creating a Web Service manually on Render:
* **Name:** `rainrisk` (or `maharainrisk`)
* **Environment:** `Python 3`
* **Region:** `Singapore`
* **Branch:** `main`
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
* **Health Check Path:** `/health`

### Environment Variables:
| Variable | Value | Description |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Pins Python 3.11 runtime |
| `PORT` | `10000` | Default listening port (Render sets this dynamically) |
| `ENVIRONMENT` | `production` | Enables production security headers and cache headers |

---

## ⚡ Memory Optimization for Free Tier (512 MB RAM)

Render's Free Web Service provides 512 MB of RAM. MahaRainRisk is optimized specifically to operate comfortably within this limit:
1. **Lean Dependencies:** Offline packages (`geopandas`, `jupyter`, `matplotlib`) are removed from production `requirements.txt`, preventing build memory spikes.
2. **Compact Feature Store:** Telemetry is stored in `data/processed/master_panel.parquet` (only 904 KB) and read using `pyarrow` with zero memory waste.
3. **Lazy Audio Generation:** Neural audio MP3s are synthesized and cached on-demand rather than pre-generating thousands of files.
4. **Memory Footprint:** At runtime, the server typically consumes **~160 MB to 210 MB RAM**, well below the 512 MB ceiling.

---

## 🔍 Post-Deployment Health Check Checklist

- [ ] `GET /health` returns HTTP 200 with `status: "healthy"`.
- [ ] `GET /` loads the Liquid Glass Landing Page with background video / poster.
- [ ] Clicking "Launch Platform" transitions to the dashboard without console errors.
- [ ] Taluka search and map click load telemetry cards and university advisories.
- [ ] Audio advisory button plays Marathi/English TTS audio.
- [ ] `GET /api/reservoirs` returns storage data for all 12 major Maharashtra dams.
