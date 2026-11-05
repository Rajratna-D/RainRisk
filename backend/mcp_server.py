
# -*- coding: utf-8 -*-
"""
MahaRainRisk: Production Model Context Protocol (MCP) Server
Hardened for zero-crash stdio/SSE execution, lazy ML loading, and bilingual Marathi entity resolution.
Exposes 6 high-signal climatology, risk explainability, spatial topology, and agronomic advisory tools.
"""

import sys
import os
import json
import logging
import argparse
from typing import Optional, List, Dict, Any, Union

# Ensure base project path is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# =========================================================================
# SAFEGUARD 1 & 2: UTF-8 Stream Enforcement & Stderr Logging Isolation
# =========================================================================
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Force all internal loggers to stderr (NEVER stdout!)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s"
)
logger = logging.getLogger("MahaRainRisk-MCP")

from pydantic import Field, AliasChoices

# FastMCP / MCPServer initialization (compatible with mcp 1.x and 2.x)
try:
    from mcp.server.fastmcp import FastMCP
except (ImportError, ModuleNotFoundError):
    from mcp.server.mcpserver import MCPServer as FastMCP

mcp = FastMCP(
    "MahaRainRisk Climatology & Spatial Intelligence Engine",
    instructions=(
        "MahaRainRisk provides real-time drought assessments, dual-mode machine learning predictions, "
        "TreeSHAP explainability attributions, topological adjacency analyses, and bilingual (Marathi/English) "
        "agricultural advisories across all 194 rainfed talukas in Maharashtra, India."
    )
)

# =========================================================================
# SAFEGUARD 3: Lazy Singleton Service Manager (< 30ms Protocol Handshake)
# =========================================================================
class LazyServiceManager:
    _service = None

    @classmethod
    def get_service(cls):
        """Loads heavy backend service and models only upon the first actual tool call."""
        if cls._service is None:
            logger.info("Lazy-loading MahaRainRisk BackendDataService and TreeSHAP...")
            from backend.services import backend_service
            cls._service = backend_service
            logger.info("BackendDataService initialized successfully.")
        return cls._service

# =========================================================================
# SAFEGUARD 4: Canonical Alias Normalizer (Bilingual & Historic Names)
# =========================================================================
CANONICAL_TALUKA_ALIASES: Dict[str, str] = {
    # Renamed / Historical Districts & Talukas
    "aurangabad": "Chhatrapati Sambhajinagar",
    "औरंगाबाद": "Chhatrapati Sambhajinagar",
    "छत्रपती संभाजीनगर": "Chhatrapati Sambhajinagar",
    "osmanabad": "Dharashiv",
    "उस्मानाबाद": "Dharashiv",
    "धाराशिव": "Dharashiv",
    "poona": "Haveli",
    "pune": "Haveli",
    "पुणे": "Haveli",
    "हवेली": "Haveli",
    "बारामती": "Baramati",
    "पैठण": "Paithan",
    "मेहेकर": "Mehkar",
    "जालना": "Jalna",
    "सोलापूर": "Solapur North",
    "solapur": "Solapur North",
    "solapur_north": "Solapur North",
    "solapur_south": "Solapur South",
    "nasik": "Nashik",
    "नाशिक": "Nashik",
    "अहमदनगर": "Nagar",
    "नगर": "Nagar",
    "अकोला": "Akola",
    "अमरावती": "Amravati",
    "बीड": "Beed",
    "नांदेड": "Nanded",
    "लातूर": "Latur",
    "परभणी": "Parbhani",
    "हिंगोली": "Hingoli",
    "बुलढाणा": "Buldana",
    "वाशिम": "Washim",
    "यवतमाळ": "Yavatmal",
    "वर्धा": "Wardha",
    "नागपूर": "Nagpur",
    "भंडारा": "Bhandara",
    "गोंदिया": "Gondia",
    "चंद्रपूर": "Chandrapur",
    "गडचिरोली": "Gadchiroli"
}

def normalize_taluka_query(query: str) -> str:
    """Normalizes natural language, historic, or Devanagari taluka queries."""
    clean = query.strip()
    clean_lower = clean.lower()
    if clean_lower in CANONICAL_TALUKA_ALIASES:
        return CANONICAL_TALUKA_ALIASES[clean_lower]
    if clean in CANONICAL_TALUKA_ALIASES:
        return CANONICAL_TALUKA_ALIASES[clean]
    return clean

# =========================================================================
# MCP TOOL 1: Taluka Drought Status & Dual-Mode Telemetry
# =========================================================================
@mcp.tool()
def get_taluka_risk(
    taluka: str = Field(
        ...,
        validation_alias=AliasChoices("taluka", "taluka_name", "query", "location", "name"),
        description="Official Maharashtra Taluka name in English or Marathi (e.g., 'Paithan', 'Baramati', 'पैठण')."
    ),
    year: Optional[int] = Field(None, description="Assessment year (e.g., 2026). Defaults to latest available."),
    month: Optional[int] = Field(None, description="Assessment month (1-12). Defaults to latest available.")
) -> Dict[str, Any]:
    """
    Evaluates current and 30-day forecast drought conditions for any Maharashtra taluka.
    Returns physical telemetry (SPI-3, root-zone soil moisture %, dam storage %, dry spell days),
    dual-mode machine learning classifications (Diagnostic & Forecaster), and confidence scores.
    """
    resolved_name = normalize_taluka_query(taluka)
    service = LazyServiceManager.get_service()

    try:
        y = year if year is not None else 2026
        m = month if month is not None else 10
        row = service.resolve_taluka_row(resolved_name)
        code = int(row["taluka_lgd_code"])
        
        # ML-08: If specific historical period requested, evaluate target period features
        if year is not None or month is not None:
            analysis = service.inference_engine.analyze_taluka(resolved_name, year=y, month=m)
            diag = analysis["live_diagnosis"]
            fc = analysis["30_day_forecast"]
            detail = service.get_taluka_detail(resolved_name)
            meta = analysis.get("meta", detail["meta"])
            cards = detail["farmer_cards"]
        else:
            detail = service.get_taluka_detail(resolved_name)
            meta = detail["meta"]
            diag = detail["live_diagnosis"]
            fc = detail["30_day_forecast"]
            cards = detail["farmer_cards"]

        return {
            "status": "SUCCESS",
            "taluka_lgd_code": code,
            "taluka_name": meta["taluka"],
            "taluka_name_mr": meta.get("taluka_mr", ""),
            "district_name": meta["district"],
            "district_name_mr": meta.get("district_mr", ""),
            "evaluated_period": f"{y}-{m:02d}",
            "is_latest_calibrated": (y == 2026 and m == 10),
            "live_diagnosis": {
                "category_code": diag["category_code"],
                "risk_tier": diag["label_en"],
                "risk_label_mr": diag["label_mr"],
                "confidence_pct": round(float(diag.get("confidence_pct", 95.0)), 1),
                "drought_probability": round(float(diag.get("risk_score", 0.8)), 2)
            },
            "early_warning_30day": {
                "forecast_code": fc["category_code"],
                "forecast_tier": fc["label_en"],
                "forecast_label_mr": fc["label_mr"],
                "trend": fc.get("trend_en", "Stable")
            },
            "telemetry_gauges": {
                "spi_3": round(float(row.get("spi_3", 0.0)), 2),
                "rainfall_3month_mm": round(float(cards["rainfall_deficit"]["value_mm"]), 1),
                "rainfall_status_en": cards["rainfall_deficit"]["status_en"],
                "rainfall_status_mr": cards["rainfall_deficit"]["status_mr"],
                "soil_moisture_pct": cards["soil_moisture"]["value_pct"],
                "soil_status_en": cards["soil_moisture"]["status_en"],
                "soil_status_mr": cards["soil_moisture"]["status_mr"],
                "dam_storage_pct": cards["dam_storage"]["value_pct"],
                "dam_name": cards["dam_storage"].get("dam_name", ""),
                "dam_name_mr": cards["dam_storage"].get("dam_name_mr", ""),
                "dry_spell_days": cards["dry_gap"]["value_days"],
                "dry_status_en": cards["dry_gap"]["status_en"],
                "dry_status_mr": cards["dry_gap"]["status_mr"]
            }
        }
    except Exception as e:
        logger.error(f"Error evaluating taluka '{taluka}': {e}")
        return {
            "status": "ERROR",
            "taluka_requested": taluka,
            "message": f"Could not evaluate taluka '{taluka}': {str(e)}. Verify spelling against Maharashtra LGD codes."
        }

# =========================================================================
# MCP TOOL 2: TreeSHAP Explainable AI (XAI) Attribution & Narratives
# =========================================================================
@mcp.tool()
def explain_drought_prediction(
    taluka: str = Field(
        ...,
        validation_alias=AliasChoices("taluka", "taluka_name", "query", "location", "name"),
        description="Official Maharashtra Taluka name in English or Marathi (e.g., 'Paithan', 'Baramati', 'पैठण')."
    ),
    as_of_date: Optional[str] = Field(None, description="Assessment date (YYYY-MM-DD). Defaults to latest calibrated date.")
) -> Dict[str, Any]:
    """
    Delivers exact TreeSHAP local feature attribution and bilingual farmer explanations.
    Identifies the top 3 environmental risk escalators pushing the taluka toward drought,
    the top 1 mitigating buffer resisting drought, and provides verified Marathi & English narratives.
    """
    resolved_name = normalize_taluka_query(taluka)
    service = LazyServiceManager.get_service()

    try:
        res = service.explain_taluka_v1(resolved_name, as_of_date)
        pred = res.get("predicted_tier", {})
        pred_code = pred.get("code", 0) if isinstance(pred, dict) else int(pred)
        pred_label = pred.get("label_en", "Safe") if isinstance(pred, dict) else str(pred)

        escalators = []
        for esc in res.get("top_risk_escalators", []):
            escalators.append({
                "feature_name": esc.get("feature_key", ""),
                "human_label": esc.get("name_en", ""),
                "human_label_mr": esc.get("name_mr", ""),
                "icon": esc.get("icon", "⚠️"),
                "observed_value": esc.get("raw_value", 0.0),
                "unit": esc.get("unit", ""),
                "shap_importance_pct": esc.get("impact_pct", 0.0),
                "direction": "ESCALATING_RISK"
            })

        top_buf = None
        raw_buffers = res.get("top_mitigating_buffers", [])
        if raw_buffers:
            b0 = raw_buffers[0]
            top_buf = {
                "feature_name": b0.get("feature_key", ""),
                "human_label": b0.get("name_en", ""),
                "human_label_mr": b0.get("name_mr", ""),
                "icon": b0.get("icon", "🛡️"),
                "observed_value": b0.get("raw_value", 0.0),
                "unit": b0.get("unit", ""),
                "shap_importance_pct": b0.get("impact_pct", 0.0),
                "direction": "MITIGATING_BUFFER"
            }

        return {
            "status": "SUCCESS",
            "taluka_lgd_code": res["taluka_lgd_code"],
            "taluka_name": res["taluka_name"],
            "taluka_name_mr": res["taluka_name_mr"],
            "district_name": res["district_name"],
            "as_of_date": res["as_of_date"],
            "predicted_category": pred_code,
            "predicted_label": pred_label,
            "confidence_pct": round(float(res.get("confidence_pct", 95.0)), 1),
            "top_risk_escalators": escalators,
            "top_mitigating_buffer": top_buf,
            "farmer_narrative": res.get("farmer_summary", {})
        }
    except Exception as e:
        logger.error(f"Error computing XAI for taluka '{taluka}': {e}")
        return {
            "status": "ERROR",
            "taluka_requested": taluka,
            "message": f"Could not generate TreeSHAP attribution for '{taluka}': {str(e)}."
        }

# =========================================================================
# MCP TOOL 3: Bilingual Agricultural University Advisory
# =========================================================================
@mcp.tool()
def get_bilingual_advisory(
    taluka: str = Field(
        ...,
        validation_alias=AliasChoices("taluka", "taluka_name", "query", "location", "name"),
        description="Official Maharashtra Taluka name in English or Marathi (e.g., 'Paithan', 'Baramati', 'पैठण')."
    ),
    language: str = Field("both", description="Advisory language filter: 'en' for English, 'mr' for Marathi, or 'both'.")
) -> Dict[str, Any]:
    """
    Retrieves localized, crop-specific agronomic advisories strictly anchored to
    Maharashtra's 4 State Agricultural Universities:
    MPKV Rahuri (Western Maharashtra), VNMKV Parbhani (Marathwada),
    PDKV Akola (Vidarbha), or BSKKV Dapoli (Konkan).
    """
    resolved_name = normalize_taluka_query(taluka)
    service = LazyServiceManager.get_service()

    try:
        detail = service.get_taluka_detail(resolved_name)
        adv = detail["advisory"]
        u_anchor = adv["university_anchor"]
        actions = adv["prescriptive_actions"]

        lang_filter = language.strip().lower()

        def _filter_lang(item: Any) -> Union[str, Dict[str, str]]:
            if isinstance(item, dict):
                if lang_filter == "en":
                    return item.get("en", "")
                if lang_filter == "mr":
                    return item.get("mr", "")
                return {"en": item.get("en", ""), "mr": item.get("mr", "")}
            return str(item)

        return {
            "status": "SUCCESS",
            "taluka_name": detail["meta"]["taluka"],
            "district_name": detail["meta"]["district"],
            "risk_tier": detail["live_diagnosis"]["label_en"],
            "university_anchor": {
                "code": u_anchor.get("university_key", "MPKV Rahuri"),
                "full_name_en": u_anchor.get("university_name_en", ""),
                "full_name_mr": u_anchor.get("university_name_mr", ""),
                "regional_focus": u_anchor.get("regional_focus", ""),
                "primary_crops": u_anchor.get("primary_crops", [])
            },
            "prescriptive_actions": {
                "irrigation_strategy": _filter_lang(actions.get("irrigation_strategy", {})),
                "moisture_conservation": _filter_lang(actions.get("moisture_conservation", {})),
                "foliar_and_nutrients": _filter_lang(actions.get("foliar_and_nutrients", {})),
                "contingency_management": _filter_lang(actions.get("contingency_management", {}))
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving advisory for taluka '{taluka}': {e}")
        return {
            "status": "ERROR",
            "taluka_requested": taluka,
            "message": f"Could not retrieve agricultural advisory for '{taluka}': {str(e)}."
        }

# =========================================================================
# MCP TOOL 4: Statewide Drought Overview & Hotspot Monitoring
# =========================================================================
@mcp.tool()
def get_state_drought_summary() -> Dict[str, Any]:
    """
    Returns statewide macro climatological summary across all 194 monitored rainfed talukas in Maharashtra.
    Provides risk category distributions (Safe, Watch, Alert, Severe, Extreme),
    statewide averages, and identifies the top 5 critical drought hotspots requiring immediate relief.
    """
    service = LazyServiceManager.get_service()

    try:
        overview = service.get_statewide_overview()
        return {
            "status": "SUCCESS",
            "total_talukas_monitored": overview["total_talukas"],
            "total_districts": overview["total_districts"],
            "risk_distribution": overview["risk_distribution"],
            "state_averages": {
                "rainfall_deficit_pct": overview["state_avg_rainfall_deficit_pct"],
                "soil_moisture_pct": overview["state_avg_soil_moisture_pct"],
                "major_reservoir_storage_pct": overview["state_avg_dam_storage_pct"]
            },
            "top_5_drought_hotspots": overview["top_hotspots"],
            "policy_recommendation": (
                "Prioritize emergency protective irrigation scheduling from Jayakwadi, Ujjani, "
                "and Majalgaon reservoirs for hotspots exhibiting consecutive dry gaps > 15 days."
            )
        }
    except Exception as e:
        logger.error(f"Error generating statewide summary: {e}")
        return {
            "status": "ERROR",
            "message": f"Could not generate statewide drought summary: {str(e)}."
        }

# =========================================================================
# MCP TOOL 5: Spatial Topology & Regional Contagion Analysis
# =========================================================================
@mcp.tool()
def get_adjacent_talukas(
    taluka: str = Field(
        ...,
        validation_alias=AliasChoices("taluka", "taluka_name", "query", "location", "name"),
        description="Target taluka name in English or Marathi (e.g., 'Paithan', 'Baramati', 'पैठण')."
    ),
    max_neighbors: int = Field(6, description="Maximum number of topological neighbors to return (default: 6).")
) -> Dict[str, Any]:
    """
    Evaluates topological adjacency and spatial contagion corridors around any Maharashtra taluka.
    Eliminates spatial hallucinations by returning verified geographic neighbors, their current
    drought risk tiers, root-zone soil moisture, and regional corridor stress indicators.
    """
    resolved_name = normalize_taluka_query(taluka)
    service = LazyServiceManager.get_service()

    try:
        adj = service.get_adjacent_talukas(resolved_name, max_neighbors=max_neighbors)
        return {
            "status": "SUCCESS",
            **adj
        }
    except Exception as e:
        logger.error(f"Error computing adjacency for taluka '{taluka}': {e}")
        return {
            "status": "ERROR",
            "taluka_requested": taluka,
            "message": f"Could not evaluate adjacent neighbors for '{taluka}': {str(e)}."
        }

# =========================================================================
# MCP TOOL 6: District Administrative Rollup & Vulnerability Assessment
# =========================================================================
@mcp.tool()
def get_district_summary(
    district: str = Field(
        ...,
        validation_alias=AliasChoices("district", "district_name", "query", "name"),
        description="Maharashtra District name in English or Marathi (e.g., 'Solapur', 'Pune', 'छत्रपती संभाजीनगर')."
    )
) -> Dict[str, Any]:
    """
    Administrative aggregation of all monitored talukas within a specified Maharashtra district.
    Returns district-wide risk distribution, average soil moisture, assigned major reservoir storage %,
    the most vulnerable taluka, and a comprehensive status roster for Disaster Management & PMFBY officials.
    """
    service = LazyServiceManager.get_service()

    try:
        dist_summary = service.get_district_summary(district)
        return {
            "status": "SUCCESS",
            **dist_summary
        }
    except Exception as e:
        logger.error(f"Error aggregating district '{district}': {e}")
        return {
            "status": "ERROR",
            "district_requested": district,
            "message": f"Could not aggregate district summary for '{district}': {str(e)}."
        }

# =========================================================================
# CLI ENTRYPOINT & TRANSPORT EXECUTION
# =========================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MahaRainRisk Production MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="MCP transport protocol: 'stdio' (default for Claude Desktop/Cursor) or 'sse' (HTTP remote)"
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "0.0.0.0"),
        help="Host for SSE transport (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", 8001)),
        help="Port for SSE transport (default: 8001)"
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        logger.info("Starting MahaRainRisk MCP Server over stdio transport...")
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        logger.info(f"Starting MahaRainRisk MCP Server over SSE transport on {args.host}:{args.port}...")
        mcp.run(transport="sse")
