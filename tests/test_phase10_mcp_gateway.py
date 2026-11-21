# -*- coding: utf-8 -*-
"""
Phase 10 Test Suite: Universal Model Context Protocol (MCP) Gateway
Validates single-link endpoint /mcp across Claude, Gemini, ChatGPT, and Cursor:
- Elimination of HTTP 307 redirect failure for Claude SSE
- Direct 200 OK SSE stream handshake and messages path routing
- Streamable HTTP JSON-RPC 2.0 initialize & tools/list execution
- Universal CORS OPTIONS preflight response with max-age
- Host header validation & DNS rebinding hardening
- Per-IP TTLCache rate limiting (60 req/min)
- Diagnostic JSON status page for human browsers
"""

import sys
import os
import json
import pytest
from starlette.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app, MCP_RATE_LIMIT_CACHE


@pytest.fixture(autouse=True)
def clean_rate_limit():
    MCP_RATE_LIMIT_CACHE.clear()
    yield
    MCP_RATE_LIMIT_CACHE.clear()


def test_t06_single_link_exists_at_mcp_path():
    """T-06: Root /mcp exists, is reachable, and returns 200 (not 404 or 307)."""
    with TestClient(app) as client:
        res = client.get("/mcp")
        assert res.status_code == 200
        assert res.headers.get("content-type", "").startswith("application/json")


def test_t07_no_307_redirect_on_sse_accept():
    """T-07: BUG-FIX: GET /mcp with text/event-stream does NOT return HTTP 307."""
    import asyncio
    from starlette.requests import Request
    from starlette.responses import RedirectResponse
    from backend.main import handle_mcp_unified_gateway, ASGIAppResponse

    async def _run():
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/mcp",
            "headers": [(b"accept", b"text/event-stream")],
            "client": ("127.0.0.1", 12345),
            "server": ("localhost", 80),
        }
        req = Request(scope)
        res = await handle_mcp_unified_gateway(req)
        assert not isinstance(res, RedirectResponse), "Must not return 307/308 redirect for SSE!"
        assert isinstance(res, ASGIAppResponse), f"Expected ASGIAppResponse, got {type(res)}"
        assert res.path_override == "/sse"
        assert res.root_path == "/mcp"

    asyncio.run(_run())


def test_t08_post_json_rpc_initialize():
    """T-08: POST /mcp handles JSON-RPC 2.0 initialize without redirect or error."""
    with TestClient(app) as client:
        res = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 101,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-suite", "version": "1.0"}
                }
            }
        )
        assert res.status_code == 200
        assert "jsonrpc" in res.text or "event: message" in res.text


def test_t09_post_json_rpc_tools_list():
    """T-09: POST /mcp with tools/list discovers the 6 MahaRainRisk drought tools."""
    with TestClient(app) as client:
        # Step 1: Initialize session
        r_init = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 101,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-agent", "version": "1.0"}
                }
            }
        )
        assert r_init.status_code == 200
        session_id = r_init.headers.get("mcp-session-id")

        # Step 2: List tools using established session ID
        headers = {"mcp-session-id": session_id} if session_id else {}
        res = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 102,
                "method": "tools/list",
                "params": {}
            }
        )
        assert res.status_code == 200
        # Text contains tool definitions in Streamable HTTP event format
        assert "get_taluka_risk" in res.text
        assert "explain_drought_prediction" in res.text


def test_t10_options_response_max_age():
    """T-10: OPTIONS /mcp sets Access-Control-Max-Age to 86400 (24-hour preflight cache)."""
    with TestClient(app) as client:
        res = client.options("/mcp")
        assert res.status_code == 204
        assert res.headers.get("access-control-max-age") == "86400"
        assert res.headers.get("access-control-allow-origin") == "*"


def test_t11_host_allowlist_valid_host_passes():
    """T-11: SEC-FIX: Production Render host rainrisk-vcra.onrender.com passes host validation."""
    with TestClient(app) as client:
        res = client.get("/mcp", headers={"Host": "rainrisk-vcra.onrender.com"})
        assert res.status_code == 200


def test_t12_host_allowlist_invalid_host_blocked():
    """T-12: SEC-FIX: Unauthorized Host header is blocked by FastMCP TransportSecuritySettings."""
    with TestClient(app, base_url="http://untrusted-external-domain.net") as client:
        res = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        )
        # Transport security must reject with 421 Misdirected Request, 403 Forbidden, or 400
        assert res.status_code in [421, 403, 400]


def test_t13_rate_limit_resets_after_ttl():
    """T-13: Rate limit state clears when cache resets, allowing new requests."""
    with TestClient(app) as client:
        # Send 60 requests to fill quota
        for _ in range(60):
            res = client.get("/mcp")
            assert res.status_code == 200
        # 61st must be blocked
        blocked = client.get("/mcp")
        assert blocked.status_code == 429

        # Simulate TTL expiration by clearing cache
        MCP_RATE_LIMIT_CACHE.clear()

        # Should be allowed again
        res_after = client.get("/mcp")
        assert res_after.status_code == 200


def test_t14_tools_discoverable_via_diagnostic_page():
    """T-14: GET /mcp diagnostic page lists all 6 enterprise tools and connector guides."""
    with TestClient(app) as client:
        res = client.get("/mcp")
        data = res.json()
        assert data["tools_count"] == 6
        expected_tools = [
            "get_taluka_risk",
            "explain_drought_prediction",
            "get_bilingual_advisory",
            "get_state_drought_summary",
            "get_adjacent_talukas",
            "get_district_summary"
        ]
        for t in expected_tools:
            assert t in data["tools"]
        assert "claude" in data["connect_instructions"]
        assert "gemini" in data["connect_instructions"]
        assert "chatgpt" in data["connect_instructions"]


def test_t15_mcp_diagnostic_json_has_universal_link():
    """T-15: Diagnostic JSON payload advertises canonical universal link."""
    with TestClient(app) as client:
        res = client.get("/mcp")
        data = res.json()
        assert data["universal_link"] == "https://rainrisk-vcra.onrender.com/mcp"
        assert "None" in data["authentication"]


def test_t16_get_with_session_id_routes_to_streamable_http():
    """T-16: GET with Accept: text/event-stream and Mcp-Session-Id routes to Streamable HTTP, not legacy SSE."""
    import asyncio
    from starlette.requests import Request
    from backend.main import handle_mcp_unified_gateway, ASGIAppResponse, get_mcp_sse_app, get_mcp_streamable_app

    async def _run():
        # Case 1: Without Mcp-Session-Id -> routes to legacy SSE (/sse)
        scope_sse = {
            "type": "http",
            "method": "GET",
            "path": "/mcp",
            "headers": [(b"accept", b"text/event-stream")],
            "client": ("127.0.0.1", 12345),
            "server": ("localhost", 80),
        }
        res_sse = await handle_mcp_unified_gateway(Request(scope_sse))
        assert isinstance(res_sse, ASGIAppResponse)
        assert res_sse.path_override == "/sse"
        assert res_sse.asgi_app is get_mcp_sse_app()

        # Case 2: With Mcp-Session-Id -> routes to Streamable HTTP session manager (/)
        scope_streamable = {
            "type": "http",
            "method": "GET",
            "path": "/mcp",
            "headers": [
                (b"accept", b"text/event-stream"),
                (b"mcp-session-id", b"test-streamable-session-12345")
            ],
            "client": ("127.0.0.1", 12345),
            "server": ("localhost", 80),
        }
        res_streamable = await handle_mcp_unified_gateway(Request(scope_streamable))
        assert isinstance(res_streamable, ASGIAppResponse)
        assert res_streamable.path_override == "/"
        assert res_streamable.asgi_app is get_mcp_streamable_app()

    asyncio.run(_run())


def test_t17_sse_messages_trailing_slash_preservation():
    """T-17: /mcp/messages sub-path uses /messages/ with trailing slash to prevent Starlette 307 redirect."""
    import asyncio
    from starlette.requests import Request
    from backend.main import handle_mcp_unified_gateway, ASGIAppResponse, get_mcp_sse_app

    async def _run():
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp/messages",
            "raw_path": b"/mcp/messages",
            "query_string": b"session_id=test-session",
            "headers": [(b"host", b"localhost")],
            "client": ("127.0.0.1", 12345),
            "server": ("localhost", 80),
        }
        res = await handle_mcp_unified_gateway(Request(scope), rest="messages")
        assert isinstance(res, ASGIAppResponse)
        assert res.path_override == "/messages/"
        assert res.asgi_app is get_mcp_sse_app()

        # Execute the ASGI response to verify no 307/308 redirect occurs
        sent_messages = []
        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}
        async def send(message):
            sent_messages.append(message)

        await res(scope, receive, send)

        status_code = None
        for msg in sent_messages:
            if msg.get("type") == "http.response.start":
                status_code = msg.get("status")
                break

        assert status_code not in [307, 308], f"Mount unexpectedly returned redirect {status_code}!"
        # Calling /messages/ directly reaches the mounted session handler (returns 400 for invalid session, not 307 redirect)
        assert status_code == 400

    asyncio.run(_run())


def test_t18_cors_expose_headers_includes_mcp_session_id():
    """T-18: CORS preflight and responses expose Mcp-Session-Id so browser fetch clients can read it."""
    with TestClient(app) as client:
        # Check OPTIONS preflight
        res_opt = client.options("/mcp")
        assert res_opt.status_code == 204
        expose_opt = res_opt.headers.get("access-control-expose-headers", "").lower()
        assert "mcp-session-id" in expose_opt

        # Check POST response
        res_post = client.post(
            "/mcp",
            headers={"accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }
        )
        assert res_post.status_code == 200
        expose_post = res_post.headers.get("access-control-expose-headers", "").lower()
        assert "mcp-session-id" in expose_post


def test_t19_localtunnel_host_allowed():
    """T-19: Localtunnel hosts (*.loca.lt) are permitted by TransportSecuritySettings."""
    with TestClient(app, base_url="https://quick-farm-42.loca.lt") as client:
        res = client.get("/mcp")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "operational"


def test_t20_byte_safe_cloudflare_tunnel_host_allowed():
    """T-20: Cloudflare quick tunnel hosts (*.trycloudflare.com) are permitted by TransportSecuritySettings."""
    with TestClient(app, base_url="https://subdomain.trycloudflare.com") as client:
        res = client.get("/mcp")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "operational"
