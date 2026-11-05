# 🔌 MahaRainRisk: Universal AI Agent Connection & Deployment Guide

> **Deploying and Connecting Model Context Protocol (MCP) Across Claude, Cursor, ChatGPT, and Web Users**

---

## 📌 Executive Summary

MahaRainRisk is equipped with a **Dual-Protocol Agent Engine**:
1. **Model Context Protocol (FastMCP 2.x):** Served over Server-Sent Events (SSE) at `/mcp/sse` and `stdio`.
2. **OpenAPI 3.1 REST Specification:** Served at `/openapi.json`.

This architecture enables **100% of major AI clients** (Claude, Cursor, ChatGPT, Antigravity, LibreChat) and ordinary web users to interact with Maharashtra's drought telemetry without cloning code or running local scripts.

---

## 🚀 Universal Connection Methods

### 1. 1-Click Installation via Smithery.ai (Claude Desktop & Cursor)

[Smithery.ai](https://smithery.ai) is the global registry for MCP servers. MahaRainRisk includes a pre-configured [`smithery.yaml`](file:///d:/PBL_selfmade/MahaRainRisk/smithery.yaml).

* **User Experience:**
  1. Open [smithery.ai/server/maharainrisk](https://smithery.ai).
  2. Click **"Install in 1-Click"** (or click the badge on our web dashboard).
  3. Claude Desktop or Cursor launches and adds the server automatically.
* **Result:** Zero terminal commands, zero git clones, and zero manual JSON edits.

---

### 2. Remote Cloud Connection over HTTPS / SSE (Any MCP Client)

Our production FastAPI backend hosts the MCP SSE app directly on Render:
```
https://rainrisk-vcra.onrender.com/mcp
```
*(Automatically resolves to `/mcp/sse` via HTTP 307 redirect)*

---

### 3. Connecting via Web-Based AI Connectors (Claude Web, ChatGPT Web & Gemini Web)

If you are using the web interfaces in Google Chrome, Microsoft Edge, or Brave, all three major AI platforms offer an in-browser **Custom MCP Server / Connector** dialog. Below are the exact input fields and values to enter for each platform based on their official web modals:

#### A. Claude Web (`claude.ai` $\rightarrow$ Settings $\rightarrow$ Connectors $\rightarrow$ "Add custom connector")
* **Dialog Title:** `Add custom connector`
* **Name:** `MahaRainRisk` *(displayed in your Claude connectors list)*
* **MCP server URL:**
  ```
  https://rainrisk-vcra.onrender.com/mcp
  ```
  *(Accepts remote HTTPS; automatically handles SSE handshake and tool discovery)*
* **Action:** Click **Continue**.
* Claude establishes the secure handshake, discovers all 6 enterprise tools, and enables the connector across your conversations.

#### B. ChatGPT Web (`chatgpt.com/plugins` $\rightarrow$ "Add custom MCP server")
* **Dialog Title:** `Add custom MCP server`
* **Icon (optional):** Leave blank or upload your icon (max 10 KB, 256x256 px).
* **Name:** `MahaRainRisk`
* **Description (optional):** `Maharashtra Drought Early Warning, TreeSHAP Explainability, and Agrometeorological Advisory Engine`
* **Connection:** Select the toggle **Server URL** (highlighted pill).
* **URL Input:**
  ```
  https://rainrisk-vcra.onrender.com/mcp
  ```
* **Authentication:** Select **None** from the dropdown.
  *(Note: The modal defaults to `OAuth`. Change it to `None` because MahaRainRisk is a public agricultural early-warning system that requires no client credentials).*
* **Advanced OAuth settings:** Leave collapsed / empty.
* **Action:** Click **Save / Add**.

#### C. Google Gemini Web (`gemini.google.com/customize/connectors` $\rightarrow$ "Connect to an MCP server")
* **Dialog Title:** `Connect to an MCP server`
* **MCP server URL:**
  ```
  https://rainrisk-vcra.onrender.com/mcp
  ```
  *(Must start with `https://`)*
* **Additional settings:** Click **Show more** $\rightarrow$ Verify Authentication is set to **None**.
* **Action:** Click **Next**.
* Gemini binds the 6 drought intelligence tools directly into your Gemini session.

---

### 4. Testing Locally Before Cloud Deployment (Instant HTTPS Tunnel)

Because Claude Web, ChatGPT Web, and Gemini Web run in cloud data centers, they cannot reach `http://localhost:8000`. To test these exact three web modals on your local machine before pushing to Render:

1. Start your local backend:
   ```powershell
   python d:\PBL_selfmade\MahaRainRisk\backend\main.py
   ```
2. In a second PowerShell window, launch a free HTTPS tunnel using `localtunnel` (zero account required):
   ```powershell
   npx localtunnel --port 8000
   ```
   *Example Output:* `https://quick-farm-42.loca.lt`
3. Enter your tunnel URL with `/mcp` in Claude, ChatGPT, or Gemini:
   ```
   https://quick-farm-42.loca.lt/mcp
   ```
   All three web platforms will immediately connect to your local code in real time!

---

### 5. Desktop Clients & IDEs (Claude Desktop, Cursor & Windsurf)

#### Connecting in Claude Desktop:
Add this entry to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "maharainrisk_cloud": {
      "url": "https://rainrisk-vcra.onrender.com/mcp/sse"
    }
  }
}
```

#### Connecting in Cursor / Windsurf:
1. Go to **Settings** $\rightarrow$ **Features** $\rightarrow$ **MCP** $\rightarrow$ **Add New Server**.
2. Select **Type:** `SSE`.
3. Enter **URL:** `https://rainrisk-vcra.onrender.com/mcp/sse`.

#### Connecting in LibreChat / Open-WebUI:
Add the remote SSE URL directly into the MCP Plugin Settings.

---

### 6. OpenAI ChatGPT Custom GPTs (OpenAPI Action Route)

OpenAI Custom GPTs connect through REST OpenAPI contracts:

1. Open **ChatGPT** $\rightarrow$ **Explore GPTs** $\rightarrow$ **Create**.
2. Under **Configure**, scroll down and click **Create new action**.
3. In **Import from URL**, enter:
   ```
   https://rainrisk-vcra.onrender.com/openapi.json
   ```
4. Click **Import**.
5. All 6 endpoints (`/api/v1/taluka/.../risk`, `/explain`, etc.) are automatically converted into ChatGPT Actions.
6. Users on the **ChatGPT Mobile App or Web** can now ask:
   - *"What is the drought situation in Paithan?"*
   - *"Give me the farmer advisory in Marathi."*

---

### 7. Direct Web Dashboard (For Farmers & Public)

No AI software is required for agricultural stakeholders:

1. Visit `https://maharainrisk.vercel.app`.
2. Tap the floating **"🤖 कृषी सल्लागार / Agro-Advisor"** button.
3. Select any taluka or speak a query in Marathi.
4. The dashboard queries the backend in real time and renders:
   - Live risk tier badge (Safe / Watch / Alert / Severe).
   - Vernacular Marathi advisory from MPKV/VNMKV.
   - Top 3 physical drivers from TreeSHAP.

---

## 🛠️ The 6 Available Agent Tools

| Tool Name | Parameters | Capabilities |
|:---|:---|:---|
| `get_taluka_risk` | `taluka: str`, `year: Optional[int]`, `month: Optional[int]` | Returns live diagnosis, 30-day forecaster, and 4 physical gauges (SPI-3, soil moisture %, dam storage %, dry spell days). |
| `explain_drought_prediction` | `taluka: str`, `as_of_date: Optional[str]` | Returns TreeSHAP top 3 escalators, mitigating buffer, and plain Marathi/English narratives. |
| `get_bilingual_advisory` | `taluka: str`, `language: str = "both"` | Prescriptive irrigation and crop practices from Maharashtra's 4 State Agricultural Universities. |
| `get_state_drought_summary` | None | Macro distribution across 194 talukas, state averages, and top 5 critical hotspots. |
| `get_adjacent_talukas` | `taluka: str`, `max_neighbors: int = 6` | Topological spatial neighbors, boundary distances (km), and regional drought corridor contagion check. |
| `get_district_summary` | `district: str` | District-level rollup (taluka roster, average soil moisture, assigned reservoir storage %). |

---

## 🔒 Production Security Guarantees
- **UTF-8 Stream Enforcement:** Prevents Windows `cp1252` encoding crashes on Marathi Devanagari script (`\u0900-\u097F`).
- **Stderr Logging Isolation:** Protects JSON-RPC 2.0 stdio pipes from unhandled print statements or library warnings.
- **Lazy Service Singleton:** Exposes tool definitions in $< 30\text{ ms}$, eliminating client handshake timeouts.
- **Context Guarding:** High-density 200–350 token JSON payloads prevent LLM context window flooding.

