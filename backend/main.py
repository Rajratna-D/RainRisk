

import os
import sys
import json
from contextlib import asynccontextmanager
from typing import Dict, Any
import pandas as pd
import numpy as np
import joblib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Path Configuration
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
SRC_DIR = os.path.join(PROJECT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from labeling import compute_lpa, compute_pct_departure, classify, CATEGORY_ORDER
from features import build_lag_rolling_features
from train import ALL_FEATURES
from constants import CATEGORY_COLORS, COORDS, MACRO_REGIONS
from advisory import get_advisory_api


# Global State & Cache

state: Dict[str, Any] = {}

def initialize_data():
    """Load and preprocess datasets and model pipelines in memory."""
    print("Loading datasets and model artifacts...")
    csv_path = os.path.join(PROJECT_DIR, "data", "raw", "Sub_Division_IMD_2017.csv")
    raw = pd.read_csv(csv_path)
    lpa = compute_lpa(raw)
    raw["LPA"] = raw["SUBDIVISION"].map(lpa)
    raw["pct_departure"] = compute_pct_departure(raw["JJAS"], raw["LPA"])
    raw["drought_category"] = raw["pct_departure"].apply(classify)
    feat = build_lag_rolling_features(raw, enhanced=True)

    # Load models and results
    pipe_path = os.path.join(PROJECT_DIR, "results", "model", "best_pipeline.joblib")
    meta_path = os.path.join(PROJECT_DIR, "results", "model", "best_pipeline_metadata.json")
    comp_path = os.path.join(PROJECT_DIR, "results", "model", "enhanced_comparison.json")

    pipeline = joblib.load(pipe_path) if os.path.exists(pipe_path) else None

    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)

    comp = {}
    if os.path.exists(comp_path):
        with open(comp_path) as f:
            comp = json.load(f)

    # Feature importances
    imp_p = os.path.join(PROJECT_DIR, "results", "report_assets", "feature_importance.csv")
    perm_p = os.path.join(PROJECT_DIR, "results", "report_assets", "permutation_importance.csv")
    imp_df = pd.read_csv(imp_p) if os.path.exists(imp_p) else None
    perm_df = pd.read_csv(perm_p) if os.path.exists(perm_p) else None

    # Precalculate subdivision stats
    sub_stats = {}
    cv_series = (raw.groupby("SUBDIVISION")["JJAS"]
                 .agg(["mean", "std"])
                 .assign(cv=lambda d: d["std"] / d["mean"] * 100))
    national_median_cv = float(cv_series["cv"].median())

    drought_freq = (raw.assign(
        is_drought=raw["drought_category"].isin(["Deficient", "Large Deficient"]))
        .groupby("SUBDIVISION")["is_drought"].mean() * 100)

    for sub_name in sorted(raw["SUBDIVISION"].unique()):
        sub_lpa = float(lpa.get(sub_name, 0.0))
        sub_cv = float(cv_series.loc[sub_name, "cv"]) if sub_name in cv_series.index else 0.0
        sub_mean = float(cv_series.loc[sub_name, "mean"]) if sub_name in cv_series.index else 0.0
        sub_dfreq = float(drought_freq.get(sub_name, 0.0))
        lat, lon = COORDS.get(sub_name, (22.0, 80.0))

        # Find macro region
        m_region = "Other"
        for r_name, subs in MACRO_REGIONS.items():
            if sub_name in subs:
                m_region = r_name
                break

        sub_stats[sub_name] = {
            "name": sub_name,
            "lpa": round(sub_lpa, 1),
            "mean_jjas": round(sub_mean, 1),
            "cv": round(sub_cv, 1),
            "drought_frequency": round(sub_dfreq, 1),
            "lat": lat,
            "lon": lon,
            "macro_region": m_region,
        }

    # All-India mean annual JJAS series
    national = raw.groupby("YEAR")["JJAS"].mean().reset_index()
    national["smooth"] = national["JJAS"].rolling(10, min_periods=1).mean()
    national_trend = [
        {"year": int(row["YEAR"]), "jjas": round(float(row["JJAS"]), 1), "smooth": round(float(row["smooth"]), 1)}
        for _, row in national.iterrows()
    ]

    state["raw"] = raw
    state["feat"] = feat
    state["lpa"] = lpa
    state["pipeline"] = pipeline
    state["meta"] = meta
    state["comp"] = comp
    state["imp_df"] = imp_df
    state["perm_df"] = perm_df
    state["sub_stats"] = sub_stats
    state["national_trend"] = national_trend
    state["national_median_cv"] = national_median_cv
    print("Data initialization complete.")

# FastAPI App Definition (using modern lifespan pattern)
@asynccontextmanager
async def lifespan(app):
    """Startup: load data and model artifacts into memory."""
    initialize_data()
    yield

app = FastAPI(
    title="RainRisk API",
    description="REST API for Indian Monsoon Drought Risk Intelligence & Planetary Teleconnections",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints


@app.get("/api/overview")
def get_overview():
    """Returns high-level national summary, KPI metrics, and category distribution."""
    raw = state["raw"]
    n_obs = len(raw)
    n_subs = raw["SUBDIVISION"].nunique()
    counts = raw["drought_category"].value_counts().to_dict()
    ordered_counts = [{"category": cat, "count": int(counts.get(cat, 0)), "color": CATEGORY_COLORS.get(cat, "#64748b")}
                      for cat in CATEGORY_ORDER]

    normal_pct = (raw["drought_category"] == "Normal").mean() * 100
    meta = state.get("meta", {})
    test_met = meta.get("test_metrics", {})

    return {
        "total_records": n_obs,
        "total_subdivisions": n_subs,
        "normal_percentage": round(normal_pct, 1),
        "national_lpa": round(float(raw["JJAS"].mean()), 1),
        "national_median_cv": round(state["national_median_cv"], 1),
        "exact_accuracy": round(float(test_met.get("accuracy", 0.5597)) * 100, 1),
        "balanced_accuracy": round(float(test_met.get("balanced_accuracy", 0.4316)) * 100, 1),
        "off_by_one_accuracy": round(float(test_met.get("off_by_one_accuracy", 0.9300)) * 100, 1),
        "mean_ordinal_distance": round(float(test_met.get("mean_ordinal_distance", 0.5226)), 3),
        "category_distribution": ordered_counts,
        "national_trend": state["national_trend"],
    }

@app.get("/api/subdivisions")
def get_subdivisions():
    """Returns list of all 36 subdivisions with their metadata, LPA, CV%, and coords."""
    return list(state["sub_stats"].values())

@app.get("/api/subdivision/{name}")
def get_subdivision_detail(name: str):
    """Returns detailed climatology for a single subdivision."""
    raw = state["raw"]
    sub_data = raw[raw["SUBDIVISION"] == name].sort_values("YEAR")
    if sub_data.empty:
        raise HTTPException(status_code=404, detail=f"Subdivision '{name}' not found")

    stats = state["sub_stats"].get(name, {})
    lpa_val = stats.get("lpa", 0.0)

    # Historical timeline
    timeline = [
        {
            "year": int(row["YEAR"]),
            "jjas": round(float(row["JJAS"]), 1),
            "departure": round(float(row["pct_departure"]), 1),
            "category": row["drought_category"],
            "color": CATEGORY_COLORS.get(row["drought_category"], "#64748b"),
        }
        for _, row in sub_data.iterrows()
    ]

    # Monthly progression
    month_cols = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    monthly = []
    for m in month_cols:
        if m in sub_data.columns:
            monthly.append({"month": m, "rainfall": round(float(sub_data[m].mean()), 1)})

    # Decadal epochs
    sub_copy = sub_data.copy()
    sub_copy["epoch"] = pd.cut(sub_copy["YEAR"], bins=[1900, 1930, 1960, 1990, 2020],
                               labels=["1901-1930", "1931-1960", "1961-1990", "1991-2017"])
    epoch_summary = sub_copy.groupby("epoch", observed=False)["JJAS"].agg(["mean", "std"]).reset_index()
    epoch_summary["cv"] = (epoch_summary["std"] / epoch_summary["mean"] * 100).round(1)
    epochs = [
        {
            "epoch": str(row["epoch"]),
            "mean": round(float(row["mean"]), 1) if pd.notna(row["mean"]) else 0,
            "std": round(float(row["std"]), 1) if pd.notna(row["std"]) else 0,
            "cv": round(float(row["cv"]), 1) if pd.notna(row["cv"]) else 0,
        }
        for _, row in epoch_summary.iterrows()
    ]

    # Default monthly / seasonal averages for scenario inputs
    default_jf = float(sub_data["JF"].mean()) if "JF" in sub_data.columns else 30.0
    default_mam = float(sub_data["MAM"].mean()) if "MAM" in sub_data.columns else 120.0
    default_ond = float(sub_data["OND"].mean()) if "OND" in sub_data.columns else 150.0

    return {
        "metadata": stats,
        "timeline": timeline,
        "monthly": monthly,
        "epochs": epochs,
        "defaults": {
            "jf": round(default_jf, 1),
            "mam": round(default_mam, 1),
            "ond": round(default_ond, 1),
        },
    }

@app.get("/api/map")
def get_map_data(year: int = 2015, region: str = "All India", mode: str = "actual"):
    """Returns geospatial records for all subdivisions for a given year."""
    feat_df = state["feat"]
    pipeline = state["pipeline"]

    year_data = feat_df[feat_df["YEAR"] == year].copy()
    if year_data.empty:
        raise HTTPException(status_code=404, detail=f"Year {year} not found in database")

    if region != "All India" and region in MACRO_REGIONS:
        valid_subs = MACRO_REGIONS[region]
        year_data = year_data[year_data["SUBDIVISION"].isin(valid_subs)]

    # Telemetry prediction mode
    if mode == "prediction" and pipeline is not None:
        try:
            valid = year_data.dropna(subset=ALL_FEATURES)
            if len(valid):
                valid["drought_category"] = pipeline.predict(valid[ALL_FEATURES])
                year_data = valid
        except Exception as e:
            print(f"Prediction error in map: {e}")

    records = []
    for _, row in year_data.iterrows():
        sub_name = row["SUBDIVISION"]
        lat, lon = COORDS.get(sub_name, (22.0, 80.0))
        cat = row["drought_category"]
        dep = float(row["pct_departure"]) if pd.notna(row["pct_departure"]) else 0.0
        jjas = float(row["JJAS"]) if pd.notna(row["JJAS"]) else 0.0

        records.append({
            "subdivision": sub_name,
            "lat": lat,
            "lon": lon,
            "jjas": round(jjas, 1),
            "departure": round(dep, 1),
            "category": cat,
            "color": CATEGORY_COLORS.get(cat, "#64748b"),
            "bubble_size": min(55, max(14, abs(dep))),
        })

    # Summary
    n_total = len(records)
    n_def = sum(1 for r in records if r["category"] in ["Deficient", "Large Deficient", "No Rainfall"])
    pct_def = (n_def / n_total * 100) if n_total > 0 else 0.0

    # Extremes
    sorted_by_dep = sorted(records, key=lambda x: x["departure"])
    top_deficient = sorted_by_dep[:5]
    top_excess = sorted(records, key=lambda x: x["departure"], reverse=True)[:5]

    return {
        "year": year,
        "region": region,
        "mode": mode,
        "total_subdivisions": n_total,
        "deficient_count": n_def,
        "deficient_percentage": round(pct_def, 1),
        "records": records,
        "top_deficient": top_deficient,
        "top_excess": top_excess,
    }

@app.get("/api/leaderboard")
def get_leaderboard():
    """Returns model benchmark rankings and confusion matrix."""
    comp = state.get("comp", {})
    meta = state.get("meta", {})
    feat_df = state["feat"]
    pipeline = state["pipeline"]

    tier_key = "teleconnection_features" if "teleconnection_features" in comp else "enhanced_features"
    models_raw = comp.get(tier_key, [])
    models = []
    for m in models_raw:
        if "error" in m:
            continue
        clean_name = m["model"].replace("_tele", "").replace("_enhanced", "")
        models.append({
            "name": clean_name,
            "accuracy": round(float(m.get("accuracy", 0)) * 100, 1),
            "balanced_accuracy": round(float(m.get("balanced_accuracy", 0)) * 100, 1),
            "macro_f1": round(float(m.get("macro_f1", 0)), 3),
            "off_by_one": round(float(m.get("off_by_one_accuracy", 0)) * 100, 1),
            "train_time": round(float(m.get("train_time_seconds", 0)), 2),
            "is_best": "RandomForest" in clean_name,
        })

    # Confusion matrix on held-out test set
    cm_data = {"labels": [], "matrix": [], "normalized_matrix": [], "diagonal_accuracy": 56.0}
    if pipeline is not None:
        try:
            test = (feat_df[feat_df["YEAR"] > 2010]
                    .dropna(subset=ALL_FEATURES + ["drought_category"])
                    .query("drought_category != 'Unknown'"))
            if len(test):
                y_true = test["drought_category"]
                y_pred = pipeline.predict(test[ALL_FEATURES])

                from sklearn.metrics import confusion_matrix
                labels = [c for c in CATEGORY_ORDER if c in y_true.unique() or c in y_pred]
                cm = confusion_matrix(y_true, y_pred, labels=labels)
                row_sums = cm.sum(axis=1)[:, np.newaxis]
                cm_norm = np.divide(cm.astype('float'), row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums != 0)

                cm_data = {
                    "labels": labels,
                    "matrix": cm.tolist(),
                    "normalized_matrix": (cm_norm * 100).round(1).tolist(),
                    "diagonal_accuracy": round(float(np.trace(cm) / cm.sum() * 100), 1),
                }
        except Exception as e:
            print(f"Leaderboard matrix error: {e}")

    return {
        "active_model": meta.get("model", "RandomForest"),
        "features_count": 23,
        "models": models,
        "confusion_matrix": cm_data,
    }

@app.get("/api/methodology")
def get_methodology():
    """Returns feature dictionary and feature importances."""
    features_list = [
        {"name": "prev_year_jjas", "desc": "Prior year JJAS rainfall total", "group": "Monsoon Lag"},
        {"name": "prev_annual_change", "desc": "Year-on-year JJAS delta", "group": "Monsoon Momentum"},
        {"name": "rolling_3yr_jjas", "desc": "3-year rolling JJAS mean", "group": "Multi-Year Trend"},
        {"name": "rolling_5yr_jjas", "desc": "5-year rolling JJAS mean", "group": "Multi-Year Trend"},
        {"name": "cv_5yr_jjas", "desc": "5-year coefficient of variation", "group": "Volatility"},
        {"name": "prev_jun", "desc": "Prior June rainfall", "group": "Monthly Progression"},
        {"name": "prev_jul", "desc": "Prior July rainfall", "group": "Monthly Progression"},
        {"name": "prev_aug", "desc": "Prior August rainfall", "group": "Monthly Progression"},
        {"name": "prev_sep", "desc": "Prior September rainfall", "group": "Monthly Progression"},
        {"name": "prev_jf", "desc": "Prior Jan-Feb rainfall", "group": "Pre-Monsoon Lag"},
        {"name": "prev_mam", "desc": "Prior Mar-May rainfall", "group": "Pre-Monsoon Precursor"},
        {"name": "prev_ond", "desc": "Prior Oct-Dec rainfall", "group": "Post-Monsoon Memory"},
        {"name": "prev_annual", "desc": "Prior year total annual rainfall", "group": "Annual Total"},
        {"name": "rolling_3yr_annual", "desc": "3-year rolling annual mean", "group": "Multi-Year Trend"},
        {"name": "rolling_5yr_annual", "desc": "5-year rolling annual mean", "group": "Multi-Year Trend"},
        {"name": "monsoon_concentration", "desc": "max(Jun..Sep) / JJAS", "group": "Concentration Ratio"},
        {"name": "jjas_to_annual_ratio", "desc": "JJAS / annual total", "group": "Dependency Index"},
        {"name": "prev_premonsoon_signal", "desc": "MAM / annual total", "group": "Precursor Ratio"},
        {"name": "enso_djf_lag", "desc": "Antecedent winter (Dec-Feb) Niño 3.4 SST anomaly", "group": "Teleconnection"},
        {"name": "enso_mam_signal", "desc": "Pre-monsoon spring (Mar-May) Niño 3.4 anomaly", "group": "Teleconnection"},
        {"name": "enso_tendency", "desc": "Spring minus winter warming/cooling velocity", "group": "Teleconnection"},
        {"name": "iod_mam_lag", "desc": "Pre-monsoon spring (Mar-May) Dipole Mode Index", "group": "Teleconnection"},
        {"name": "enso_iod_interaction", "desc": "Coupled interaction (Niño 3.4 * IOD DMI)", "group": "Teleconnection"},
        {"name": "SUBDIVISION", "desc": "Geographic subdivision identifier", "group": "Spatial Identity"},
    ]

    imp_df = state.get("imp_df")
    perm_df = state.get("perm_df")

    gini_top = []
    if imp_df is not None:
        top_g = imp_df.nlargest(10, imp_df.columns[1])
        gini_top = [{"feature": str(r[0]), "score": round(float(r[1]), 4)} for r in top_g.itertuples(index=False)]

    perm_top = []
    if perm_df is not None:
        top_p = perm_df.head(10)
        perm_top = [{"feature": str(r[0]), "score": round(float(r[1]), 4)} for r in top_p.itertuples(index=False)]

    return {
        "features": features_list,
        "gini_importance": gini_top,
        "permutation_importance": perm_top,
    }

class PredictionRequest(BaseModel):
    subdivision: str
    prev_jjas: float
    prev_change: float
    rolling_3yr: float
    rolling_5yr: float
    cv_5yr: float
    prev_jun: float
    prev_jul: float
    prev_aug: float
    prev_sep: float
    prev_jf: float
    prev_mam: float
    prev_ond: float
    enso_djf: float
    enso_mam: float
    iod_mam: float

@app.post("/api/predict")
def predict_scenario(req: PredictionRequest):
    """Executes live model inference on simulated climate vector."""
    pipeline = state["pipeline"]
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Trained pipeline not loaded on server")

    p_annual = req.prev_jf + req.prev_mam + req.prev_jjas + req.prev_ond
    peak = max(req.prev_jun, req.prev_jul, req.prev_aug, req.prev_sep)
    conc = peak / req.prev_jjas if req.prev_jjas > 0 else 0.3
    ratio = req.prev_jjas / p_annual if p_annual > 0 else 0.8
    pre_sig = req.prev_mam / p_annual if p_annual > 0 else 0.08
    enso_tend = req.enso_mam - req.enso_djf
    enso_iod_inter = req.enso_mam * req.iod_mam

    row = {
        "prev_year_jjas": req.prev_jjas,
        "prev_annual_change": req.prev_change,
        "rolling_3yr_jjas": req.rolling_3yr,
        "rolling_5yr_jjas": req.rolling_5yr,
        "cv_5yr_jjas": req.cv_5yr,
        "prev_jun": req.prev_jun,
        "prev_jul": req.prev_jul,
        "prev_aug": req.prev_aug,
        "prev_sep": req.prev_sep,
        "prev_jf": req.prev_jf,
        "prev_mam": req.prev_mam,
        "prev_ond": req.prev_ond,
        "prev_annual": p_annual,
        "rolling_3yr_annual": req.rolling_3yr * 1.2,
        "rolling_5yr_annual": req.rolling_5yr * 1.2,
        "monsoon_concentration": conc,
        "jjas_to_annual_ratio": ratio,
        "prev_premonsoon_signal": pre_sig,
        "enso_djf_lag": req.enso_djf,
        "enso_mam_signal": req.enso_mam,
        "enso_tendency": enso_tend,
        "iod_mam_lag": req.iod_mam,
        "enso_iod_interaction": enso_iod_inter,
        "SUBDIVISION": req.subdivision,
    }

    inp = pd.DataFrame([row])[ALL_FEATURES]
    pred = pipeline.predict(inp)[0]

    probabilities = []
    drought_prob = 0.0
    if hasattr(pipeline, "predict_proba") and hasattr(pipeline, "classes_"):
        raw_probs = pipeline.predict_proba(inp)[0]
        for cat, pr in zip(pipeline.classes_, raw_probs):
            p_val = float(pr)
            probabilities.append({
                "category": cat,
                "probability": round(p_val * 100, 1),
                "color": CATEGORY_COLORS.get(cat, "#64748b"),
            })
            if cat in ["Deficient", "Large Deficient", "No Rainfall"]:
                drought_prob += p_val

    # Operational advisory (unified via src/advisory.py)
    advisory = get_advisory_api(pred)

    return {
        "predicted_category": pred,
        "color": CATEGORY_COLORS.get(pred, "#38bdf8"),
        "composite_drought_risk": round(drought_prob * 100, 1),
        "probabilities": probabilities,
        "advisory": advisory,
    }


# Static Frontend Serving

FRONTEND_DIST = os.path.join(PROJECT_DIR, "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
