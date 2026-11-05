# -*- coding: utf-8 -*-
"""
Phase 7 Verification Test Suite: Model Context Protocol (FastMCP) Server
Validates protocol handshakes, 6 enterprise MCP tools, bilingual Devanagari support,
TreeSHAP explainability delivery, spatial topology neighbors, and district rollups.
"""

import sys
import os
import json
import pytest
import asyncio

# Ensure project root is available
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.mcp_server import mcp, normalize_taluka_query, CANONICAL_TALUKA_ALIASES


def extract_tool_result(call_res) -> dict:
    """Helper to extract dictionary payload from MCP CallToolResult across MCP 1.x & 2.x."""
    if hasattr(call_res, "structured_content") and call_res.structured_content:
        if "result" in call_res.structured_content:
            return call_res.structured_content["result"]
        return call_res.structured_content
    if hasattr(call_res, "content") and call_res.content:
        return json.loads(call_res.content[0].text)
    raise ValueError(f"Could not parse MCP CallToolResult: {call_res}")


def test_mcp_server_initialization_and_tool_discovery():
    """Verifies that the MCP server initializes cleanly and exposes exactly 6 tools."""
    async def _run():
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        
        expected_tools = [
            "get_taluka_risk",
            "explain_drought_prediction",
            "get_bilingual_advisory",
            "get_state_drought_summary",
            "get_adjacent_talukas",
            "get_district_summary"
        ]
        
        assert len(tools) == 6, f"Expected 6 MCP tools, got {len(tools)}: {tool_names}"
        for exp in expected_tools:
            assert exp in tool_names, f"Tool '{exp}' missing from registered MCP tools!"

    asyncio.run(_run())


def test_tool_get_taluka_risk_english_and_marathi():
    """Verifies Tool 1 get_taluka_risk for both English and Marathi Devanagari input."""
    async def _run():
        # English query
        res_en = await mcp.call_tool("get_taluka_risk", {"taluka": "Paithan"})
        data_en = extract_tool_result(res_en)
        
        assert data_en["status"] == "SUCCESS"
        assert data_en["taluka_lgd_code"] == 4123
        assert data_en["taluka_name"] == "Paithan"
        assert data_en["district_name"] == "Chhatrapati Sambhajinagar"
        assert "live_diagnosis" in data_en
        assert "telemetry_gauges" in data_en
        assert data_en["telemetry_gauges"]["dam_name"] == "Jayakwadi (Nathsagar)"
        assert data_en["live_diagnosis"]["risk_tier"] in ["Safe", "Watch", "Alert", "Severe", "Extreme"]
        
        # Marathi Devanagari query
        res_mr = await mcp.call_tool("get_taluka_risk", {"taluka": "पैठण"})
        data_mr = extract_tool_result(res_mr)
        
        assert data_mr["status"] == "SUCCESS"
        assert data_mr["taluka_lgd_code"] == 4123
        assert data_mr["taluka_name"] == "Paithan"
        assert any('\u0900' <= char <= '\u097F' for char in data_mr["taluka_name_mr"])

    asyncio.run(_run())


def test_tool_explain_drought_prediction_treeshap():
    """Verifies Tool 2 explain_drought_prediction delivers TreeSHAP attributions and narratives."""
    async def _run():
        res = await mcp.call_tool("explain_drought_prediction", {"taluka": "Baramati"})
        data = extract_tool_result(res)
        
        assert data["status"] == "SUCCESS"
        assert data["taluka_name"] == "Baramati"
        assert data["predicted_category"] in [0, 1, 2, 3, 4]
        assert "top_risk_escalators" in data
        assert len(data["top_risk_escalators"]) > 0
        
        # Verify top escalator structure
        top1 = data["top_risk_escalators"][0]
        assert "feature_name" in top1
        assert "human_label" in top1
        assert "shap_importance_pct" in top1
        assert top1["direction"] == "ESCALATING_RISK"
        
        # Verify bilingual farmer narratives
        narrative = data["farmer_narrative"]
        assert "en" in narrative and len(narrative["en"]) > 10
        assert "mr" in narrative and len(narrative["mr"]) > 10
        assert any('\u0900' <= char <= '\u097F' for char in narrative["mr"]), "Narrative must contain Devanagari!"

    asyncio.run(_run())


def test_tool_get_bilingual_advisory():
    """Verifies Tool 3 get_bilingual_advisory with university anchoring and language filtering."""
    async def _run():
        # Test 'both' languages
        res_both = await mcp.call_tool("get_bilingual_advisory", {"taluka": "Baramati", "language": "both"})
        data_both = extract_tool_result(res_both)
        
        assert data_both["status"] == "SUCCESS"
        assert data_both["university_anchor"]["code"] == "MPKV Rahuri"
        assert "prescriptive_actions" in data_both
        assert "irrigation_strategy" in data_both["prescriptive_actions"]
        assert "en" in data_both["prescriptive_actions"]["irrigation_strategy"]
        assert "mr" in data_both["prescriptive_actions"]["irrigation_strategy"]
        
        # Test 'mr' language filter
        res_mr = await mcp.call_tool("get_bilingual_advisory", {"taluka": "Paithan", "language": "mr"})
        data_mr = extract_tool_result(res_mr)
        assert data_mr["status"] == "SUCCESS"
        assert data_mr["university_anchor"]["code"] == "VNMKV Parbhani"
        assert isinstance(data_mr["prescriptive_actions"]["irrigation_strategy"], str)
        assert any('\u0900' <= char <= '\u097F' for char in data_mr["prescriptive_actions"]["irrigation_strategy"])

    asyncio.run(_run())


def test_tool_get_state_drought_summary():
    """Verifies Tool 4 get_state_drought_summary across all 194 monitored talukas."""
    async def _run():
        res = await mcp.call_tool("get_state_drought_summary", {})
        data = extract_tool_result(res)
        
        assert data["status"] == "SUCCESS"
        assert data["total_talukas_monitored"] == 194
        assert data["total_districts"] == 36
        assert "risk_distribution" in data
        dist = data["risk_distribution"]
        assert sum(dist.values()) == 194
        
        assert "top_5_drought_hotspots" in data
        assert len(data["top_5_drought_hotspots"]) == 5
        for hs in data["top_5_drought_hotspots"]:
            assert "taluka_name" in hs
            assert "district_name" in hs
            assert "risk_tier" in hs

    asyncio.run(_run())


def test_tool_get_adjacent_talukas_spatial_topology():
    """Verifies Tool 5 get_adjacent_talukas resolves geographic neighbors without spatial hallucinations."""
    async def _run():
        res = await mcp.call_tool("get_adjacent_talukas", {"taluka": "Paithan", "max_neighbors": 6})
        data = extract_tool_result(res)
        
        assert data["status"] == "SUCCESS"
        assert data["target_taluka"]["taluka_name"] == "Paithan"
        assert "contagion_assessment" in data
        assert "adjacent_neighbors" in data
        assert len(data["adjacent_neighbors"]) <= 6
        assert len(data["adjacent_neighbors"]) >= 4
        
        neighbor_names = [n["taluka_name"] for n in data["adjacent_neighbors"]]
        assert any(valid in neighbor_names for valid in ["Pathardi", "Shevgaon", "Georai", "Gangapur"]), \
            f"Expected true spatial neighbors, got {neighbor_names}"
        
        for n in data["adjacent_neighbors"]:
            assert n["boundary_distance_km"] < 50.0, f"Neighbor {n['taluka_name']} has excessive distance: {n['boundary_distance_km']} km"

    asyncio.run(_run())


def test_tool_get_district_summary_administrative_rollup():
    """Verifies Tool 6 get_district_summary performs correct district aggregation."""
    async def _run():
        res = await mcp.call_tool("get_district_summary", {"district": "Solapur"})
        data = extract_tool_result(res)
        
        assert data["status"] == "SUCCESS"
        assert data["district_name"] == "Solapur"
        assert data["taluka_count"] > 0
        assert "assigned_reservoir" in data
        assert "Ujjani" in data["assigned_reservoir"]["name"]
        assert "most_vulnerable_taluka" in data
        assert "talukas" in data
        assert len(data["talukas"]) == data["taluka_count"]
        
        # Test Devanagari district query
        res_mr = await mcp.call_tool("get_district_summary", {"district": "सोलापूर"})
        data_mr = extract_tool_result(res_mr)
        assert data_mr["status"] == "SUCCESS"
        assert data_mr["district_name"] == "Solapur"

    asyncio.run(_run())


def test_mcp_alias_normalizer_and_error_handling():
    """Verifies historical name resolution and graceful error handling on non-existent regions."""
    async def _run():
        norm_aurangabad = normalize_taluka_query("Aurangabad")
        assert norm_aurangabad == "Chhatrapati Sambhajinagar"
        
        norm_osmanabad = normalize_taluka_query("Osmanabad")
        assert norm_osmanabad == "Dharashiv"
        
        res_err = await mcp.call_tool("get_taluka_risk", {"taluka": "Atlantis_Imaginary_Taluka"})
        data_err = extract_tool_result(res_err)
        assert data_err["status"] == "ERROR"
        assert "Atlantis_Imaginary_Taluka" in data_err["message"]

    asyncio.run(_run())
