# MahaRainRisk MCP 2.0 — Model Context Protocol Upgrade Plan & Implementation Blueprint

**Project:** MahaRainRisk — Maharashtra Taluka-Level Agritech Drought Early Warning & Farmer Advisory Platform  
**Component:** Production Model Context Protocol (MCP) Server (`backend/mcp_server.py`)  
**Transport:** Streamable HTTP + Server-Sent Events (SSE) + stdio  
**Status:** Design / Planning  
**Grounded in:** `master_panel.parquet` (194 talukas × 58 cols, 2020–2026), `imd_taluka_monthly_2014_2023` (2014–2023), `reservoirs.parquet` (12 dams), `teleconnections.parquet` (ENSO/ONI/DMI/IOD to 2026-12), `taluka_adjacency.json`, 4-SAU advisory engine, TreeSHAP XAI, Marathi/English TTS, 3-tier cache, `talukas` / `taluka_risk_latest` / `daily_weather` DB tables.

---

## 1. Executive Summary

The current MCP server exposes **6 read-only tools** over a dual-transport gateway. It is functional but brittle: `year`/`month` parameters are silently ignored (ML-08), `str.contains(regex=True)` crashes on metacharacters (BUG-08), seasonal normals are hardcoded to monsoon year-round producing false dry-season deficits (BUG-09), TreeSHAP blocks the asyncio event loop (ML-09), idle RAM is ~380–420 MB with OOM risk on the 512 MB cloud tier (ML-10), DNS rebinding protection is disabled (SEC-07), there are no formal tool contracts (HIGH-07), and there is no auth, discovery, sampling, prompts, or resources surface.

**MCP 2.0** transforms the server from a demo of 6 JSON-RPC tools into a secure, correct, performant, discoverable, and extensible agent-context layer for operational drought early warning. It uses the **full MCP spec** — tools, resources, resource templates, prompts, sampling, elicitation, completions, progress/logging notifications, structured output, OAuth 2.1 auth, and per-tool contracts — rather than treating MCP as merely a remote function-calling transport.

This document specifies every upgrade, how it maps to real code and data in the repository, and how it will be implemented and validated.

---

## 2. Current State vs. MCP 2.0 Target Scorecard

| Dimension | Current (Baseline) | MCP 2.0 Target |
|---|---|---|
| Tool surface | 6 read-only lookups | 30+ tools across 9 domains + 8+ resources + 6+ prompts |
| Protocol surface | `tools/list`, `tools/call` only | Full MCP spec surface |
| Correctness | `year`/`month` ignored; regex crash; monsoon-normal bug | Every parameter honored or explicitly rejected; zero 500s on metacharacter input |
| Trust | Raw payloads, no provenance | Every response carries `data_as_of`, sources, model version/SHA-256, confidence, limitations, staleness flags |
| Safety | DNS rebinding disabled; no auth; no rate limits | DNS rebinding on; OAuth 2.1 scopes; per-tool rate limits; audit log |
| Performance | Event-loop blocking TreeSHAP; ~380–420 MB RAM idle | Threadpool/async offload; ONNX quantization; <300 MB idle; p95 <100 ms |
| DX & QA | 8 Phase 7 tests; no formal spec | Contract tests, property/fuzz, agent eval harness, typed SDK, formal spec |

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      External AI Agent                          │
│              Claude / Gemini / Cursor / Custom Agent            │
└──────────────────────────────┬──────────────────────────────────┘
                               │ JSON-RPC 2.0 (Streamable HTTP / SSE / stdio)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              MahaRainRisk MCP 2.0 Production Server             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐│
│  │ OAuth 2.1   │ │ Rate Limit  │ │ AuthZ Scopes│ │ Audit Log ││
│  │ Resource    │ │ & Quotas    │ │ (read/admin)│ │           ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘│
│                               │                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  MCP Router: tools | resources | prompts | completions    │  │
│  │  sampling | elicitation | notifications | structured out │  │
│  └───────────────────────────────────────────────────────────┘  │
│                               │                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Lazy Service Manager (singleton, <30 ms handshake)     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                               │                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐│
│  │   Tools     │  Resources    │   Prompts     │   Cache     ││
│  │   (30+)     │  (8+)         │   (6+)        │  (TTLCache) ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘│
│                               │                                   │
└──────────────────────────────┴──────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Underlying Domain Infrastructure (unchanged, now wrapped)      │
│  - master_panel.parquet (194 Talukas × 58 columns)              │
│  - IMD 10-year monthly rainfall (2014–2023)                     │
│  - reservoirs.parquet (12 dams, 3,408 dated rows)               │
│  - teleconnections.parquet (ENSO/ONI/DMI/IOD)                   │
│  - taluka_adjacency.json (topological graph)                    │
│  - ml/drought_model.joblib + drought_forecaster.joblib          │
│  - ml/xai_engine.py (TreeSHAP)                                  │
│  - ml/advisory_engine.py (4 State Agricultural Universities)    │
│  - backend/tts_service.py (Marathi/English neural audio)        │
│  - backend/db.py (PostgreSQL/Supabase pool + taluka_risk_latest)│
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Upgrade Pillars

### 4.1 Pillar A — Protocol & Transport Hardening

**What changes and why:**

| # | Upgrade | Implementation | Why it makes MCP better |
|---|---------|---------------|-------------------------|
| A1 | Enable DNS rebinding protection | In `backend/main.py`, flip `TransportSecuritySettings(enable_dns_rebinding_protection=False)` → `True` and pass an explicit allowlist `["rainrisk-vcra.onrender.com", "localhost", "127.0.0.1"]`. | Closes SEC-07: external pages cannot resolve attacker domains to `127.0.0.1` and invoke internal MCP tools. |
| A2 | Unified single transport | Deprecate the redirect-based dual route (`/mcp` → 307 → `/mcp/sse`). Expose one canonical `/mcp` Streamable HTTP endpoint; keep `/mcp/sse` as an optional legacy path without redirect hops. | Eliminates the 307 Temporary Redirect that caused Gemini HTTP 405 handshake failures and dropped POST bodies. |
| A3 | MCP authZ layer | Add optional Bearer-token / API-key middleware at the `/mcp` gateway. Scopes: `mcp:read` (all read tools), `mcp:advisory` (farmer advisory), `mcp:write` (subscriptions/observations), `mcp:admin` (refresh/usage stats). | Prevents unauthenticated remote agents from calling sensitive district-level aggregation or write operations. |
| A4 | Formal tool contracts | Publish per-tool JSON Schema (input + output), examples, error codes, rate limits, transport notes in `MCP_TOOLS_SPEC.md`. Addresses HIGH-07 missing interface contracts. | Agents validate calls before invoking; external auditors/viva boards can verify interface fidelity with file/line references. |
| A5 | Server instructions v2 | Rewrite `instructions` into a short decision tree: if unsure of a name → `search_locations`; full answer → `get_drought_briefing`; never guess coordinates → `resolve_coordinates`; read-only tools are safe to call freely. | Reduces agent hallucination and invalid-argument calls. |

### 4.2 Pillar B — Data Correctness & ML Integrity

**What changes and why:**

| # | Upgrade | Implementation | Root cause fixed |
|---|---------|---------------|------------------|
| B1 | Honor historical `year`/`month` | In `get_taluka_risk`, wire `year`/`month` through to `inference_engine.analyze_taluka(resolved_name, year=y, month=m)`; return the actual period in `meta.period`; reject unsupported periods (outside 2020–2026 / 2014–2023) with structured `UNSUPPORTED_PERIOD` error + suggestion of nearest available. | ML-08: tool accepted `year`/`month` but ignored them, returning 2026 telemetry while lying about `evaluated_period`. |
| B2 | Regex-safe lookups | Pass `regex=False` to every `str.contains()` in district/taluka matching (`backend/services.py:681` and any equivalents). | BUG-08: regex metacharacters (`[`, `(`, `*`, `+`) raised unhandled `re.error` → HTTP 500. |
| B3 | Season-aware climatology | Condition statewide/taluka normal-rainfall calculations on current month: monsoon (Jun–Oct) uses `0.85 × (3/4)`; non-monsoon uses `0.15 × (3/8)`. Apply to `get_statewide_overview` and any district rollup. | BUG-09: hardcoded monsoon formula year-round produced false -80% to -95% deficits Nov–May. |
| B4 | Structured error envelopes | Standardize every tool error as `{status: "ERROR", code, taluka_requested, message, suggested_alternatives, retry_allowed}`. Replace ad-hoc strings. | Agents can programmatically recover (e.g., "Did you mean Paithan?") instead of parsing free text. |
| B5 | Fuzzy resolution + suggestions | Levenshtein fuzzy matcher (cutoff 0.82) for taluka/district names; return closest valid options with scores instead of raw `ValueError`. NFC-normalize Devanagari input. | Trap 4 (entity disambiguation): agents submit historic names, typos, Devanagari variants. |

### 4.3 Pillar C — Tool Capability Expansion

The server grows from 6 tools to **30+ tools** across 9 domains, all grounded in real data files already present in the repo. Each tool gets: `title`, LLM-facing description with few-shot examples, `outputSchema` + `structuredContent`, annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`), pagination where lists are returned, and a `_meta` provenance block.

#### Domain A — Discovery & Geospatial

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `search_locations` | `query`, `type` (taluka/district/division), `language`, `limit`, `cursor` | Ranked matches: LGD code, en/mr names, district, match score, "did you mean" | GEO master CSV + alias map + fuzzy | P0 |
| `resolve_coordinates` | `lat`, `lon` | Nearest taluka(s), distance km, containing polygon, optional IDW estimate | GeoJSON + centroids | P1 |
| `get_taluka_profile` | `taluka` | Division, zone, soil, crops (en/mr), normal rainfall, university, lat/lon, assigned dam | DB `talukas` / GEO CSV | P0 |
| `list_districts` | `division`, `limit`, `cursor` | 36 districts, taluka counts, dominant risk, university | `services.get_districts_list` | P0 |
| `get_division_summary` | `division` | 6-division rollup: distribution, averages, top hotspots | MP aggregate | P1 |
| `get_server_capabilities` | — | Tools/resources/prompts list, version, limits, transports, instructions | Server metadata | P0 |

#### Domain B — Core Risk & Telemetry

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `get_taluka_risk` (enhanced) | `taluka`, `year`, `month`, `include_shap`, `language`, `detail` | Diagnosis + 30-day forecast + gauges + provenance; **honors year/month** | MP + ML + XAI | P0 |
| `get_taluka_telemetry` | `taluka`, `fields[]`, `as_of` | Selected subset of the 58 master_panel columns with units | MP | P0 |
| `batch_get_taluka_risk` | `talukas[]` / `codes[]`, `detail` | Compact risk array — one round trip for many talukas | MP + ML | P1 |
| `compare_talukas` | `taluka_a`, `taluka_b`, `metrics[]` | Head-to-head deltas + more-vulnerable verdict | `services.compare_talukas` | P0 |
| `rank_talukas` | `metric`, `order`, `filter`, `limit`, `cursor` | Ranked talukas with values | MP | P1 |
| `get_state_drought_summary` (enhanced) | `detail`, `include_trend` | Distribution, averages, month-over-month trend, division breakdown, hotspots | MP | P0 |

#### Domain C — Historical & Time-Series

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `get_taluka_history` | `taluka`, `start_year`, `end_year`, `metrics[]`, `granularity` | Monthly series: SPI-1/3/6, rainfall, soil, dam, groundwater, VCI | MP 2020–2026 + IMD10 2014–2023 | P0 |
| `get_spi_series` | `taluka`, `timescale` (1/3/6), `start`, `end` | SPI series + WMO drought category | MP / IMD10 | P1 |
| `get_drought_timeline` | `taluka`, `start_year`, `end_year` | Contiguous drought events (tier ≥2) with duration/peak tier | IMD10 + MP | P1 |
| `get_monsoon_chart` | `taluka` | 10-year monsoon totals (already cached in `_imd_chart_cache`) | IMD10 | P1 |
| `get_analog_years` | `taluka`, `year`, `month`, `top_k` | Most similar historical years by rainfall/SPI profile | MP + IMD10 | P2 |

#### Domain D — Spatial & Aggregation

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `get_adjacent_talukas` (enhanced) | `taluka`, `max_neighbors`, `include_telemetry` | Verified neighbors + contagion corridor + per-neighbor gauges | adjacency + MP | P0 |
| `get_spatial_contagion` | `taluka`, `hops` (1–3) | Multi-hop corridor, stressed clusters, expansion direction | adjacency + MP | P1 |
| `get_district_summary` (enhanced) | `district`, `include_roster`, `cursor` | Rollup + paginated roster + reservoir + most-vulnerable taluka | `services.get_district_summary` | P0 |
| `get_hotspots` | `threshold_tier`, `division`, `limit` | Ranked hotspots with drivers and recommended action | MP | P0 |
| `get_vulnerability_ranking` | `scope` (state/district), `limit` | Composite index (SPI, SMI, dam, groundwater, VCI) ranking | MP | P1 |

#### Domain E — Water & Hydro

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `list_reservoirs` | — | 12 dams: storage %, capacity, river, district, critical flag | `reservoirs.parquet` | P0 |
| `get_reservoir_status` | `dam` or `district` | Storage %, live capacity, trend, `is_critical`, days-to-threshold | RES | P0 |
| `get_reservoir_timeseries` | `dam`, `start`, `end` | Storage % over time | RES (3,408 rows) | P1 |
| `get_groundwater_status` | `taluka` or `district` | Depth mbgl, distress category (>10 m), trend | MP `groundwater_depth_mbgl` | P1 |
| `get_vegetation_condition` | `taluka` | VCI %, crop-vigor category | MP `vci` | P1 |

#### Domain F — Climate & Teleconnections

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `get_teleconnections` | `months` (lookback) | ENSO phase, ONI, Niño3.4 anomaly, DMI, IOD phase + monsoon implication | TC (to 2026-12) | P0 |
| `get_monsoon_outlook` | — | Seasonal outlook synthesized from TC + state averages | TC + MP | P1 |
| `get_climate_context` | `taluka` | Zone + teleconnection + normal-rainfall context | MP + TC | P2 |

#### Domain G — Advisory & Farmer Delivery

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `get_bilingual_advisory` (enhanced) | `taluka`, `crop`, `language`, `channel` | University-anchored 4-category actions + citation | `advisory_engine` | P0 |
| `get_advisory_bundle` | `taluka`, `language`, `channel` | Full bundle: actions + SMS text + audio URL + citation | ADV + TTS | P1 |
| `get_contingency_crop_plan` | `taluka` | Tier-4 contingency crops (Kulthi, Matki, fodder bajra) | ADV (derived) | P1 |
| `get_farmer_message` | `taluka`, `channel` (sms/ivr/voice/whatsapp), `language` | Channel-sized message + optional audio link | ADV + TTS | P1 |
| `get_audio_advisory` | `taluka`, `language` | MP3 path/URL via `tts_service` | TTS | P1 |
| `get_irrigation_water_budget` | `taluka`, `crop`, `area_ha` | ET0-based requirement vs dam/groundwater availability | MP + RES (derived) | P2 |
| `get_livestock_fodder_advisory` | `taluka` | Fodder/cattle-camp guidance by tier | ADV (derived) | P2 |

#### Domain H — XAI & What-If

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `explain_drought_prediction` (enhanced) | `taluka`, `as_of_date`, `detail` (top/all), `language` | Top escalators/buffers + narratives; optional all 19 drivers | XAI | P0 |
| `explain_counterfactual` | `taluka`, `target_tier` | Minimal feature changes to reach target tier | XAI + medians | P1 |
| `simulate_scenario` | `taluka`, `overrides` (rain/soil/dam/temp) | Recomputed tier — read-only what-if | ML | P1 |
| `get_model_metadata` | — | Model card: versions, SHA-256 hashes, 19/31 features, metrics, limitations | artifacts + `MODEL_CARD.md` | P0 |
| `get_global_feature_importance` | — | Global SHAP importance (precomputed offline/startup) | XAI | P2 |

#### Domain I — Governance, Ops & Data Quality

| Tool | Inputs | Returns | Source | Pri |
|---|---|---|---|---|
| `get_data_recency` | — | Per-source last update, coverage window, staleness flags | ETL checkpoints + files | P0 |
| `get_data_quality` | `scope` | Nulls, anomalies, drift flag, coverage gaps | MP + ETL | P1 |
| `get_health` | — | Readiness: DB/cache/model status, uptime, versions | Server | P0 |
| `get_usage_stats` | `window` | Per-tool latency, error rate, top callers (admin scope) | Telemetry | P2 |

#### Domain J — Guarded Actions (write, requires auth + new backend)

| Tool | Inputs | Returns | Pri |
|---|---|---|---|
| `subscribe_alerts` | `taluka`, `threshold_tier`, `channel`, `contact` | Subscription ID (PII-encrypted, consented) | P2 |
| `list_subscriptions` / `unsubscribe` | `subscription_id` | Status | P2 |
| `record_field_observation` | `taluka`, `observation`, `reporter` | Appended record (DB write, idempotency key) | P2 |
| `trigger_data_refresh` | `dataset`, `mode` | Job ID (admin, queued, progress-notified) | P2 |

---

### 4.4 Pillar D — Performance & Resource Efficiency

| # | Upgrade | Implementation | Target |
|---|---------|---------------|--------|
| D1 | Offload CPU-bound work | Wrap `explain_taluka_v1`, `analyze_taluka`, TreeSHAP calls in `run_in_threadpool` inside each MCP tool. | p95 tool latency < 100 ms; no event-loop starvation |
| D2 | Model quantization / ONNX | Export Random Forest + TreeSHAP graphs to ONNX Runtime; target <100 MB artifact. | Idle RAM < 300 MB; survives 512 MB tier; faster cold starts |
| D3 | Pin dependency versions | Pin `scikit-learn==1.4.2`, `joblib==1.4.0`, `shap==0.45.0`, `numpy==1.26.4`, `fastmcp==2.x`. | Eliminates unpickle crashes across sklearn minor versions |
| D4 | Per-tool response caching | TTLCache keyed by `(tool, normalized_args)` with short TTL (60 s) for read-heavy tools (`get_state_drought_summary`, `get_district_summary`). | Repeated agent queries hit cache |
| D5 | Connection pooling to Supabase | Reuse `psycopg2` ThreadedConnectionPool across MCP tool calls instead of opening per-call. | Lower DB latency and connection churn |
| D6 | Token-budget control | `detail_level` (`brief\|standard\|full`), `fields[]` column pruning, `max_items` list caps, cursor pagination on roster/list tools. | Brief responses ~200–300 tokens; no context flooding |

---

### 4.5 Pillar E — Observability, Testing & Developer Experience

| # | Upgrade | Implementation |
|---|---------|---------------|
| E1 | Formal MCP spec doc | `MCP_TOOLS_SPEC.md` with every tool: JSON Schema, aliases, example request/response, error codes, rate limits, transport notes. |
| E2 | Expanded test suite | Property-based tests for alias normalization, historical date handling, regex-safe inputs, concurrency (50 VU burst via k6), Marathi round-trip fidelity. |
| E3 | MCP telemetry | Per-tool latency, success/error rate, p95/p99, token count to Render logs or `/metrics`. |
| E4 | Data drift detection | Compare incoming telemetry distribution against training baseline; surface `drift_detected` flag in tool outputs. |
| E5 | CI gate for MCP | Run MCP test suite on every PR; block merge if tool count changes or handshake fails. |
| E6 | Agent eval harness | 50–100 natural-language questions → expected tool chains and grounded answers; score tool selection, argument accuracy, answer faithfulness; CI gate ≥ 90% correct selection / ≥ 85% grounded. |

---

### 4.6 Pillar F — Client & Ecosystem Integration

| # | Upgrade | Implementation |
|---|---------|---------------|
| F1 | Client SDK / connector package | Publish `@maharainrisk/mcp-client` (Python/TS) with pre-bound tool wrappers, retry logic, Devanagari input handling. |
| F2 | Discovery document | Serve `/.well-known/mcp-server` listing tools, capabilities, transports, auth requirements. |
| F3 | Offline / local-first mode | Ship an MCP stdio binary with embedded read-only Parquet snapshot for low-connectivity talukas. |
| F4 | Multi-language advisory | Expand beyond en/mr to Hindi (and sampling-based translation for other regional languages). |
| F5 | MCP sampling + completions | Server asks client LLM to translate/adapt advisories; autocomplete for taluka/district/division/dam/crop names (en + Devanagari). |

---

## 5. Response & Error Contract

Every tool returns a single envelope:

```json
{
  "status": "ok",
  "data": { "...": "..." },
  "meta": {
    "request_id": "uuid",
    "server_version": "2.0.0",
    "tool_version": "1.0",
    "data_as_of": "2026-10",
    "sources": ["IMD", "ERA5-Land", "WRD", "CGWB", "NOAA"],
    "model": {
      "diagnostic": { "version": "...", "sha256": "..." },
      "forecaster": { "version": "...", "sha256": "..." }
    },
    "cache": "hit|miss",
    "latency_ms": 12,
    "language": "en",
    "confidence": 0.87,
    "units": { "spi": "index", "soil": "%" },
    "disclaimer": "...",
    "degraded": false
  },
  "links": { "dashboard": "https://.../taluka/4123" },
  "pagination": { "next_cursor": null }
}
```

Error taxonomy (machine-actionable):

| Code | Meaning | Client action |
|---|---|---|
| `INVALID_ARGUMENT` | Bad type/range | Fix and retry |
| `NOT_FOUND` | Unknown entity | Try `suggestions` |
| `AMBIGUOUS_LOCATION` | Multiple matches | Elicit user choice |
| `UNSUPPORTED_PERIOD` | Outside data coverage | Use `get_data_recency` |
| `DATA_STALE` | Beyond freshness SLA | Show warning |
| `UPSTREAM_UNAVAILABLE` | DB/cache down | Retry with backoff |
| `MODEL_UNAVAILABLE` | Artifact missing/integrity fail | Fail closed |
| `RATE_LIMITED` | Quota exceeded | Honor `retry_after` |
| `UNAUTHORIZED` / `FORBIDDEN` | Auth/scope failure | Re-auth |
| `INTERNAL` | Unexpected | Report `request_id` |

**Token-budget control:** `detail_level=brief` returns ~200–300 tokens; `fields` prunes columns; `max_items` caps lists; heavy tools never dump raw arrays by default (Trap 5 — context flooding).

---

## 6. Agent Workflows to Design For

These composite intents must be servable in 1–3 calls:

1. **"Is Paithan heading into drought?"** → `search_locations` (if unsure) → `get_taluka_risk(include_shap)` → `explain_drought_prediction`.
2. **"Brief me on the drought situation in Marathwada."** → `get_division_summary` → `get_hotspots` → `get_teleconnections`.
3. **"What should farmers in Baramati do this week?"** → `get_bilingual_advisory` → `get_farmer_message` → `get_audio_advisory`.
4. **"Which district needs emergency relief?"** → `get_vulnerability_ranking` → `get_district_summary` → `get_reservoir_status`.
5. **"Has Paithan had droughts like this before?"** → `get_taluka_history` → `get_analog_years` → `get_drought_timeline`.
6. **"Explain why the model says Severe."** → `explain_drought_prediction(detail=all)` → `get_model_metadata`.
7. **"What if soil moisture drops 10 points?"** → `simulate_scenario` → `explain_counterfactual`.
8. **"Give me a viva-ready explanation."** → prompt `viva_explainer` → `get_model_metadata` + `get_data_recency`.

---

## 7. Reliability, Security & Performance (Implementation Detail)

### Reliability
- Idempotency keys + retry-safe reads; circuit breaker on DB; per-tool timeouts; cancellation support.
- Graceful degradation to in-memory fallback (already exists) with `meta.degraded: true` when PostgreSQL is offline.
- Input hardening: NFC Unicode normalization for Devanagari, length caps, `regex=False`, LGD whitelist from `db.py`, Levenshtein fuzzy (cutoff 0.82) with suggestions.
- Output guards: max payload bytes, max list items, recursive size check.

### Security
- OAuth 2.1 resource server + protected-resource metadata; scopes `mcp:read`, `mcp:advisory`, `mcp:write`, `mcp:admin`.
- DNS rebinding **on** with explicit allowed hosts/origins; legacy 307 redirect chain removed.
- Per-token/IP/tool rate limits + quotas with `retry_after`.
- Audit log: subject, tool, args hash, status, latency, `request_id`.
- Prompt-injection defense: inputs treated strictly as data; never interpolated into instructions; strip control characters.
- No arbitrary-URL tools (SSRF-safe); secrets redacted; PII encrypted for subscriptions.
- Supply chain: pinned deps, SHA-256 model verification (already in `predict.py`), SBOM.

### Performance
- Async DB pool (`psycopg2` ThreadedConnectionPool) reused across calls.
- `run_in_threadpool` for TreeSHAP/inference; gzip responses; request coalescing.
- Batch tools (`batch_get_taluka_risk`) to cut round trips; cursor pagination; precomputed snapshots.
- Concurrency limiter + backpressure; stateless Streamable HTTP for horizontal scaling.

---

## 8. Testing & Evaluation

| Layer | Coverage | Tooling |
|---|---|---|
| Contract | Every tool's `inputSchema`/`outputSchema` and envelope shape | Pydantic + JSON Schema validation |
| Property/fuzz | Aliases, Devanagari NFC, regex metacharacters, oversized strings, wrong types | Hypothesis / pytest |
| Transport matrix | stdio, SSE, Streamable HTTP | MCP Inspector + custom clients |
| Client matrix | Python SDK, TS SDK, Claude, Gemini, Cursor | End-to-end handshake tests |
| Chaos | DB down, model missing, cold cache, rate-limit hit | Fault injection |
| Security | Rebinding, injection, authz bypass, SSRF | Auth/z test suite |
| Load/soak | k6 50 VU burst + sustained | `tests/test_phase9_load_and_production.py` extended |
| Agent eval | NL → tool-chain + grounded answer scoring | Custom eval harness (CI gate) |
| Localization | Marathi/English round-trip, transliteration, audio generation | TTS round-trip tests |

---

## 9. Documentation & Developer Experience

- `MCP_TOOLS_SPEC.md` — formal contracts + examples + error codes.
- `MCP_CLIENT_GUIDE.md` — Claude/Gemini/Cursor/ChatGPT setup.
- `AGENT_COOKBOOK.md` — the 8 workflows above.
- Typed Python/TS SDK with retries and Devanagari helpers.
- `/.well-known/mcp-server` discovery document.
- OpenAPI mirror of tools for REST consumers.
- Changelog + semver + deprecation policy.

---

## 10. Phased Roadmap

| Phase | Theme | Key Deliverables | Exit Criteria |
|---|---|---|---|
| **0 — Contract & safety** | Fix trust basics | ML-08/BUG-08/BUG-09 fixes; envelope; error taxonomy; annotations; provenance; DNS on; contract tests | No 500s; params honored; spec v1 published |
| **1 — Discovery & context** | Make names/locations reliable | `search_locations`, `get_taluka_profile`, `list_districts`, `get_server_capabilities`, resources, completions, `get_taluka_history`, `get_taluka_telemetry` | Agent never guesses a location; context attachable via resources |
| **2 — Hydro-climate & spatial** | Operational breadth | reservoirs, groundwater, VCI, teleconnections, division/hotspots, vulnerability, multi-hop contagion | Full "state/district situation" workflows in ≤3 calls |
| **3 — XAI & what-if** | Explainability depth | counterfactual, simulate, model metadata, global importance | "Why" and "what-if" answerable with citations |
| **4 — Farmer delivery** | Last-mile value | advisory bundle, SMS, audio, contingency, Hindi, sampling | Farmer-ready message in en/mr/hi + audio |
| **5 — Ops & governance** | Production hardening | auth/scopes, rate limits, audit, OTel, data quality, drift, health | SLOs met; security checks pass |
| **6 — Actions & ecosystem** | Extend reach | subscriptions, field observations, admin refresh, SDK, discovery, offline snapshot, eval harness | External agent integrates in <15 lines; eval score gate |

**Quick wins (P0, low effort):** `search_locations`, `get_taluka_profile`, `list_districts`, `list_reservoirs`, `get_teleconnections`, `get_health`, `get_data_recency`, `get_model_metadata`, enhanced `get_taluka_risk`, resources + completions.

**Big bets (high effort, high differentiation):** agent eval harness, counterfactual/scenario engine, subscription/alert backend, ONNX quantization, OAuth multi-tenant auth.

---

## 11. Success Metrics

1. **Surface:** ≥ 30 tools (from 6), ≥ 8 resources, ≥ 6 prompts, completions + sampling + elicitation.
2. **Correctness:** 100% of `year`/`month` queries return the requested period; 0 regex-induced 500s; 0 false dry-season deficit reports.
3. **Trust:** 100% of responses carry provenance; model hashes exposed; staleness flags surfaced.
4. **Performance:** p95 < 100 ms; idle RAM < 300 MB; 50 VU burst clean.
5. **Safety:** DNS rebinding on; all writes scoped + audited; injection/fuzz suite green.
6. **Agent quality:** eval harness ≥ 90% correct tool selection and ≥ 85% grounded answers.
7. **Adoption:** one external client completes a multi-tool workflow end-to-end; integration < 15 lines via SDK.

---

## 12. Open Decisions to Steer Implementation

| Decision | Options | Impact |
|---|---|---|
| Purpose | Viva/demo polish vs. real production hardening | Determines whether Phase 5–6 auth/write work is in scope |
| Priority client | Claude / Gemini / Cursor / ChatGPT first | Drives transport and discovery prioritization |
| Write/admin tools | Include subscriptions + observations + admin refresh, or keep strictly read-only? | Affects auth scope and backend changes |
| Languages | en + mr only, or add Hindi + sampling-based translation? | Affects advisory engine and TTS scope |
| Infra ceiling | Stay on 512 MB Render tier (ONNX mandatory) vs. scale up? | Affects model optimization urgency |
| Eval harness | Build NL→tool-chain benchmark vs. focus on more tools? | Affects QA investment vs. feature breadth |

---

## Appendix A — Data Sources Already Present in the Repo (Ground Truth for MCP 2.0)

| File | Contents | Rows / Coverage | Used by |
|---|---|---|---|
| `data/processed/master_panel.parquet` | 194 talukas × 58 cols, SPI-1/3/6, soil, dam, groundwater, VCI, teleconnections, risk tier | 15,908 rows; 2020–2026; ~82 months/taluka | All risk/telemetry/history/spatial tools |
| `data/processed/real_imd_taluka_monthly_2014_2023.parquet` | IMD monthly rainfall by taluka | 2014–2023 | History, SPI series, drought timeline, analog years, monsoon chart |
| `data/interim/reservoirs.parquet` | 12 major dams with dated storage | 3,408 rows | Reservoir status/timeseries, water budget |
| `data/interim/teleconnections.parquet` | ENSO/ONI/DMI/IOD monthly | 924 rows to 2026-12 | Teleconnections, monsoon outlook |
| `data/geo/taluka_adjacency.json` | Topological neighbor graph | 194 talukas | Adjacent talukas, spatial contagion |
| `data/geo/lgd_maharashtra_master.csv` | Official LGD hierarchy with en/mr names, zone, soil, crops, normal rainfall | 194 talukas, 36 districts | Taluka profile, search locations |
| `ml/advisory_engine.py` | 4-SAU prescriptive matrix (tiers 0–4) en/mr | 4 universities, 36 districts | Bilingual advisory, contingency, farmer message |
| `ml/xai_engine.py` | TreeSHAP with `FEATURE_METADATA` en/mr | 19 diagnostic features | Explain, counterfactual, global importance |
| `backend/tts_service.py` | Edge-TTS/gTTS Marathi + English audio | `mr-IN-ManoharNeural`, `en-IN-PrabhatNeural` | Audio advisory |
| `backend/db.py` | PostgreSQL/Supabase pool; `talukas`, `taluka_risk_latest`, `daily_weather` tables | Parameterized, injection-safe | Profile, district summary, health |

---

## Appendix B — Files to Modify / Create (Implementation Map)

**Modify:**
- `MahaRainRisk/backend/mcp_server.py` — new tools, envelope, error taxonomy, annotations, provenance, ML-08/BUG-08 fixes, fuzzy resolution.
- `MahaRainRisk/backend/main.py` — DNS rebinding on, unified transport, auth middleware, rate limiting, `/well-known/mcp-server`.
- `MahaRainRisk/backend/services.py` — `regex=False`, season-aware normals, new service methods for reservoirs/groundwater/VCI/teleconnections/history.
- `MahaRainRisk/backend/cache.py` — per-tool TTLCache keys, drift/staleness flags.
- `MahaRainRisk/backend/schemas.py` — Pydantic models for new tool inputs/outputs.

**Create:**
- `MahaRainRisk/MCP_TOOLS_SPEC.md`
- `MahaRainRisk/MCP_CLIENT_GUIDE.md`
- `MahaRainRisk/AGENT_COOKBOOK.md`
- `MahaRainRisk/mcp_client_sdk/` (Python/TS)
- `MahaRainRisk/tests/test_mcp_v2_*.py` (expanded suite)
- `MahaRainRisk/evals/` (agent eval harness)

---

**End of plan.** This document is the authoritative blueprint for MCP 2.0. Implementation should begin with Phase 0 (correctness + safety + contract) before any capability expansion.