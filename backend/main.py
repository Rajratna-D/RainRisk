"""
MahaRainRisk: Production FastAPI Backend
Serves real-time agrometeorological telemetry, dual-mode machine learning predictions,
annotated Leaflet GIS map boundaries, and official bilingual farmer advisories.
Equipped with IP rate-limiting, CORS protection, security headers, and static file mounting.
"""

import os
import sys
import time
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

# Ensure base directory in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services import backend_service
from backend.tts_service import tts_service
from backend.cache import cache_manager
from backend.schemas import (
    HealthResponse,
    TalukaSummaryItem,
    TalukaDetailResponse,
    OverviewResponse,
    DistrictRollupItem,
    TalukaComparisonResponse,
    ReservoirItem,
    ErrorEnvelope,
    TalukaRiskResponse,
    CacheStatsResponse,
    TalukaExplainResponse
)

# -------------------------------------------------------------------------
# FAST MCP / MODEL CONTEXT PROTOCOL APP INITIALIZATION
# -------------------------------------------------------------------------
mcp_sse_app = None
current_streamable_app = None

def get_mcp_streamable_app():
    try:
        from backend.mcp_server import mcp
        try:
            from mcp.server.transport_security import TransportSecuritySettings
            sec_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)
            return mcp.streamable_http_app(streamable_http_path="/", transport_security=sec_settings)
        except Exception:
            return mcp.streamable_http_app(streamable_http_path="/")
    except Exception as e:
        print(f"[!] Warning: Could not initialize Streamable HTTP app: {e}")
        return None

try:
    from backend.mcp_server import mcp
    try:
        from mcp.server.transport_security import TransportSecuritySettings
        sec_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)
        mcp_sse_app = mcp.sse_app(transport_security=sec_settings)
    except Exception:
        mcp_sse_app = mcp.sse_app()
    current_streamable_app = get_mcp_streamable_app()
    print("[OK] Remote MCP Server initialized (Streamable HTTP + SSE transport, DNS rebinding disabled for cloud).")
except Exception as e:
    print(f"[!] Warning: Could not initialize FastMCP sub-apps: {e}")

# -------------------------------------------------------------------------
# LIFESPAN CONTEXT MANAGER: STARTUP PRE-WARMING & CLEAN SHUTDOWN
# -------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Prewarm cache for all 194 talukas to eliminate cold-start stampedes
    print("[*] FastAPI Lifespan Startup: Pre-warming Tier 2 cache for all 194 talukas...")
    try:
        count = cache_manager.prewarm_all_talukas()
        print(f"[OK] Successfully pre-warmed {count} talukas into RAM. Cold-start latency eliminated.")
    except Exception as e:
        print(f"[!] Warning: Lifespan cache pre-warm encountered: {e}")

    # Startup: Pre-compile TreeSHAP Explainable AI decision graph
    print("[*] FastAPI Lifespan Startup: Pre-compiling TreeSHAP decision graph structure...")
    try:
        from ml.xai_engine import get_xai_engine
        get_xai_engine()
        print("[OK] TreeSHAP Explainability Engine warm in memory.")
    except Exception as e:
        print(f"[!] Warning: TreeSHAP engine pre-initialization encountered: {e}")

    # Startup: Initialize MCP Streamable HTTP session manager task group
    global current_streamable_app
    current_streamable_app = get_mcp_streamable_app()
    if current_streamable_app and hasattr(current_streamable_app, "router") and hasattr(current_streamable_app.router, "lifespan_context"):
        async with current_streamable_app.router.lifespan_context(current_streamable_app):
            yield
    else:
        yield

    # Shutdown: Clean in-memory caches
    print("[*] FastAPI Lifespan Shutdown: Purging in-memory cache...")
    cache_manager.clear()

app = FastAPI(
    title="MahaRainRisk API",
    description="Operational Maharashtra Taluka-Level Agritech Drought Early Warning & Advisory Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# -------------------------------------------------------------------------
# SECURITY: PRODUCTION-GRADE CORS MIDDLEWARE
# -------------------------------------------------------------------------
DEFAULT_ALLOWED_ORIGINS = [
    "https://maharainrisk.pages.dev",
    "https://maharainrisk.vercel.app",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000"
]
custom_origins_env = os.getenv("CORS_ORIGINS", "")
if custom_origins_env:
    ALLOWED_ORIGINS = [o.strip() for o in custom_origins_env.split(",") if o.strip()]
elif os.getenv("ENVIRONMENT") == "production":
    ALLOWED_ORIGINS = DEFAULT_ALLOWED_ORIGINS
else:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https:\/\/.*\.pages\.dev$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# PHASE 7: ENTERPRISE MODEL CONTEXT PROTOCOL (STREAMABLE HTTP + SSE + BROWSER)
# -------------------------------------------------------------------------
@app.api_route("/mcp", methods=["GET", "POST", "DELETE", "OPTIONS"], include_in_schema=False)
@app.api_route("/mcp/", methods=["GET", "POST", "DELETE", "OPTIONS"], include_in_schema=False)
async def handle_mcp_unified_gateway(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = request.headers.get("content-type", "")

    # 1. Human browser / developer GET diagnostics
    if request.method == "GET" and "text/event-stream" not in accept_header and "json" not in accept_header:
        return {
            "status": "operational",
            "protocol": "Model Context Protocol (FastMCP 2.x)",
            "transports": ["Streamable HTTP", "Server-Sent Events (SSE)"],
            "endpoints": {
                "streamable_http": "https://rainrisk-vcra.onrender.com/mcp",
                "sse": "https://rainrisk-vcra.onrender.com/mcp/sse"
            },
            "tools_count": 6,
            "tools": [
                "get_taluka_risk",
                "explain_drought_prediction",
                "get_bilingual_advisory",
                "get_state_drought_summary",
                "get_adjacent_talukas",
                "get_district_summary"
            ],
            "connectors": {
                "gemini_web": "Settings -> Add MCP Server -> https://rainrisk-vcra.onrender.com/mcp",
                "claude_web": "Settings -> Connectors -> Add custom connector: https://rainrisk-vcra.onrender.com/mcp",
                "chatgpt_web": "Plugins -> Add custom MCP server: https://rainrisk-vcra.onrender.com/mcp",
                "cursor_sse": "Cursor Settings -> MCP -> Add SSE: https://rainrisk-vcra.onrender.com/mcp/sse"
            }
        }

    # 2. Redirect legacy SSE requests querying root /mcp to /mcp/sse
    if request.method == "GET" and "text/event-stream" in accept_header and "json" not in content_type:
        return RedirectResponse(url="/mcp/sse", status_code=307)

    # 3. Forward to Streamable HTTP ASGI app (Gemini, Claude Web, modern clients)
    app_target = current_streamable_app or get_mcp_streamable_app()
    if app_target:
        scope = dict(request.scope)
        scope["path"] = "/"
        scope["raw_path"] = b"/"

        status_code = 200
        headers = []
        body_chunks = []

        async def receive():
            return await request.receive()

        async def send(message):
            nonlocal status_code, headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                body_chunks.append(message.get("body", b""))

        await app_target(scope, receive, send)

        res = Response(content=b"".join(body_chunks), status_code=status_code)
        for k, v in headers:
            res.headers[k.decode("latin-1")] = v.decode("latin-1")
        return res

    return JSONResponse(status_code=503, content={"error": "MCP Streamable HTTP not initialized"})

# Mount SSE sub-app for legacy SSE clients (Cursor, Claude Desktop at /mcp/sse and /mcp/messages)
if mcp_sse_app:
    app.mount("/mcp", mcp_sse_app)

# -------------------------------------------------------------------------
# SECURITY & OBSERVABILITY: RATE LIMITER & LATENCY TIMING MIDDLEWARE
# -------------------------------------------------------------------------
IP_REQUEST_TIMESTAMPS = defaultdict(list)
RATE_LIMIT_PER_MINUTE = 240 # Generous 240 req/min for real-time map tile and audio streaming
LAST_CLEANUP_TIME = time.time()

@app.middleware("http")
async def security_and_timing_middleware(request: Request, call_next):
    global LAST_CLEANUP_TIME
    start_time = time.perf_counter()
    now = time.time()

    # Periodic cleanup of inactive IPs (prevents unbounded memory growth)
    if now - LAST_CLEANUP_TIME > 60.0:
        stale_ips = [ip for ip, ts in IP_REQUEST_TIMESTAMPS.items() if not ts or (now - ts[-1] > 120.0)]
        for ip in stale_ips:
            del IP_REQUEST_TIMESTAMPS[ip]
        LAST_CLEANUP_TIME = now

    # 1. Rate Limiting Check (Respect X-Forwarded-For behind Render / Cloudflare reverse proxies)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"

    if client_ip != "testclient":
        timestamps = [t for t in IP_REQUEST_TIMESTAMPS[client_ip] if now - t < 60.0]
        IP_REQUEST_TIMESTAMPS[client_ip] = timestamps

        remaining_requests = max(0, RATE_LIMIT_PER_MINUTE - len(timestamps))
        if len(timestamps) >= RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "detail": "Rate limit exceeded. Please wait a moment.",
                    "timestamp": now
                },
                headers={
                    "X-RateLimit-Limit": str(RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60"
                }
            )
        IP_REQUEST_TIMESTAMPS[client_ip].append(now)
    else:
        remaining_requests = RATE_LIMIT_PER_MINUTE

    # 2. Process Request
    response = await call_next(request)

    # 3. Inject Observability & Security Headers
    process_time_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith(("/css", "/js")) or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    elif request.method == "GET" and request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"

    return response

# -------------------------------------------------------------------------
# CENTRALIZED EXCEPTION HANDLERS
# -------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "detail": str(exc.detail),
            "timestamp": time.time()
        }
    )

# -------------------------------------------------------------------------
# REST API ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System Health"])
@app.get("/api/health", response_model=HealthResponse, tags=["System Health"])
async def health_check():
    """Liveness probe confirming service, cache, and model health."""
    return {
        "status": "healthy",
        "platform": "MahaRainRisk Agritech",
        "talukas_covered": len(backend_service.get_talukas_list()),
        "districts_covered": 36,
        "models": {
            "mode_1_diagnostic": "250-Tree Random Forest (98% accuracy)",
            "mode_2_forecaster": "30-Day Early Warning Forecaster (77% accuracy)"
        }
    }

@app.get("/api/talukas", response_model=List[TalukaSummaryItem], tags=["Talukas"])
async def get_all_talukas():
    """Returns metadata for all 194 talukas for search & voice autocomplete."""
    return backend_service.get_talukas_list()

@app.get("/api/taluka/{query:path}", response_model=TalukaDetailResponse, tags=["Talukas"])
async def get_taluka_insights(query: str, background_tasks: BackgroundTasks):
    """
    Returns live diagnosis, 30-day forecast, 4 farmer cards,
    and official bilingual university advisory for any Maharashtra taluka.
    Pre-warms Marathi & English TTS neural audio in the background.
    """
    clean_query = query.strip().strip("/")
    if len(clean_query) > 50 or re.search(r"[<>{};]", clean_query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid taluka query characters."
        )

    try:
        data = backend_service.get_taluka_detail(clean_query)
        # Pre-generate Marathi & English advisory audio in the background for zero-latency clicks
        background_tasks.add_task(tts_service.generate_advisory_audio, data, "mr")
        background_tasks.add_task(tts_service.generate_advisory_audio, data, "en")
        return data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference error: {str(e)}")

@app.get("/api/analytics/overview", response_model=OverviewResponse, tags=["Analytics"])
async def get_statewide_overview():
    """
    Returns macro state-wide telemetry, risk tier distribution (Safe/Watch/Alert/Severe/Extreme),
    and top 5 drought hotspots across all 194 Maharashtra talukas.
    """
    return backend_service.get_statewide_overview()

@app.get("/api/districts", response_model=List[DistrictRollupItem], tags=["Analytics"])
async def get_all_districts():
    """
    Returns aggregated district-level statistics, taluka counts,
    and dominant risk tiers for all 36 Maharashtra districts.
    """
    return backend_service.get_districts_list()

@app.get("/api/compare", response_model=TalukaComparisonResponse, tags=["Analytics"])
async def compare_two_talukas(
    taluka1: str = Query(..., description="First taluka name, LGD code, or Marathi name"),
    taluka2: str = Query(..., description="Second taluka name, LGD code, or Marathi name")
):
    """
    Performs head-to-head agronomic comparison between two Maharashtra talukas,
    computing soil moisture, rainfall deficit, and dry spell differentials.
    """
    q1 = taluka1.strip().strip("/")
    q2 = taluka2.strip().strip("/")
    if not q1 or not q2 or len(q1) > 50 or len(q2) > 50 or re.search(r"[<>{};]", q1) or re.search(r"[<>{};]", q2):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid taluka query parameters.")

    try:
        return backend_service.compare_talukas(q1, q2)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Comparison error: {str(e)}")

@app.get("/api/map/geojson", tags=["GIS"])
async def get_map_geojson():
    """
    Returns Maharashtra taluka boundaries with live pre-computed
    risk colors for instant high-speed Leaflet choropleth rendering.
    """
    return backend_service.get_annotated_geojson()

@app.get("/api/reservoirs", response_model=List[ReservoirItem], tags=["Telemetry"])
async def get_major_reservoirs():
    """Returns live storage percentages and status for all 12 major Maharashtra dams."""
    return backend_service.get_reservoirs_list()

@app.get("/api/audio/advisory/{query:path}")
async def get_taluka_audio_advisory(query: str, lang: str = "mr"):
    """
    Returns natural high-quality Marathi or Indian English neural MP3 audio
    for the specified taluka's crop advisory.
    """
    clean_query = query.strip().strip("/")
    if len(clean_query) > 50 or re.search(r"[<>{};]", clean_query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid taluka query characters."
        )

    try:
        data = backend_service.get_taluka_detail(clean_query)
        audio_path = await tts_service.generate_advisory_audio(data, lang=lang)
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Audio file not found")
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename=os.path.basename(audio_path),
            content_disposition_type="inline",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"TTS generation error: {str(e)}")


# -------------------------------------------------------------------------
# PHASE 4 & 5 MULTI-TIER CACHING & INFERENCE ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/api/v1/talukas", response_model=List[TalukaSummaryItem], tags=["Talukas"])
async def get_all_talukas_v1():
    """Version 1 alias returning metadata for all 194 monitored rainfed talukas."""
    return backend_service.get_talukas_list()

@app.get("/api/v1/taluka/{query:path}/risk", response_model=TalukaRiskResponse, tags=["Talukas"])
@app.get("/api/risk/{query:path}", response_model=TalukaRiskResponse, tags=["Talukas"])
async def get_taluka_risk_latest(query: str, as_of_date: Optional[str] = Query(None, description="Optional baseline date YYYY-MM-DD")):
    """
    Tier 2 In-Memory TTLCache backed endpoint.
    Returns latest taluka risk snapshot, TreeSHAP drivers, and bilingual advisory in < 2ms.
    """
    clean_query = query.strip().strip("/")
    if len(clean_query) > 50 or re.search(r"[<>{};]", clean_query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid taluka query characters."
        )
    try:
        return backend_service.get_taluka_risk_v1(clean_query, as_of_date=as_of_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Risk resolution error: {str(e)}")

@app.get("/api/v1/taluka/{query:path}/explain", response_model=TalukaExplainResponse, tags=["Explainability"])
@app.get("/api/explain/{query:path}", response_model=TalukaExplainResponse, tags=["Explainability"])
async def explain_taluka_risk(query: str, as_of_date: Optional[str] = Query(None, description="Optional baseline date YYYY-MM-DD")):
    """
    Phase 6 TreeSHAP Explainable AI Endpoint.
    Computes local Shapley feature attribution, extracting top 3 drought escalators,
    top mitigating buffers, and natural-language Marathi & English farmer narratives.
    Backed by Tier 2 TTLCache (< 2ms on repeat queries).
    """
    clean_query = query.strip().strip("/")
    if len(clean_query) > 50 or re.search(r"[<>{};]", clean_query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid taluka query characters."
        )
    try:
        return backend_service.explain_taluka_v1(clean_query, as_of_date=as_of_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"XAI explanation error: {str(e)}")

@app.get("/api/v1/taluka/{query:path}/adjacent", tags=["Spatial"])
@app.get("/api/adjacent/{query:path}", tags=["Spatial"])
async def get_taluka_adjacent(query: str, max_neighbors: int = Query(6, ge=1, le=12)):
    """
    Returns topologically adjacent neighboring talukas and regional contagion status.
    Uses pre-computed spatial adjacency topology graph.
    """
    clean_query = query.strip().strip("/")
    if len(clean_query) > 50 or re.search(r"[<>{};]", clean_query):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid taluka query characters."
        )
    try:
        return backend_service.get_adjacent_talukas(clean_query, max_neighbors=max_neighbors)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Adjacency error: {str(e)}")

@app.get("/api/v1/cache/stats", response_model=CacheStatsResponse, tags=["Observability"])
async def get_cache_telemetry():
    """Returns real-time in-memory TTLCache performance stats, hit ratio, and Tier 3 DB metrics."""
    return cache_manager.stats()

@app.post("/api/v1/cache/clear", tags=["Observability"])
async def clear_cache_manually():
    """Manual in-memory cache purge hook (for admin or post-ingestion flush)."""
    cache_manager.clear()
    return {"status": "success", "message": "In-memory Tier 2 TTLCache cleared."}


# -------------------------------------------------------------------------
# STATIC FRONTEND MOUNTING
# -------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    # Mount subdirectories if they exist
    for sub in ["css", "js", "assets", "public"]:
        sub_path = os.path.join(FRONTEND_DIR, sub)
        if os.path.exists(sub_path):
            app.mount(f"/{sub}", StaticFiles(directory=sub_path), name=sub)

    # Serve index.html at root "/"
    @app.get("/")
    async def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(
                index_file,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        return {"message": "MahaRainRisk API operational. Frontend under active construction."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print("=" * 70)
    print(f" Starting MahaRainRisk Backend Server on http://{host}:{port}")
    print("=" * 70)
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)
