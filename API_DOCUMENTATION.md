# 📡 MahaRainRisk: REST API Documentation

> **FastAPI High-Performance Agritech Engine**  
> Interactive OpenAPI / Swagger Documentation available locally at `http://127.0.0.1:8008/docs` or in production at `https://<service-url>/docs`.

---

## 🔒 Security & Middleware Specifications

1. **IP Rate Limiter:**
   * **Limit:** 120 requests per minute per IP address.
   * **Headers Injected:**
     * `X-RateLimit-Limit: 120`
     * `X-RateLimit-Remaining: <count>`
     * `Retry-After: 60` (when exceeded with HTTP 429)
2. **Security Headers Injected:**
   * `X-Frame-Options: DENY`
   * `X-Content-Type-Options: nosniff`
   * `X-XSS-Protection: 1; mode=block`
   * `Referrer-Policy: strict-origin-when-cross-origin`
3. **Observability Header:**
   * `X-Process-Time-Ms: <latency_in_ms>`

---

## 📋 Endpoints Catalog

### 1. System Health
* **Route:** `GET /health` or `GET /api/health`
* **Description:** Liveness probe verifying server health, total talukas loaded, and ML models status.
* **Response (HTTP 200):**
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

---

### 2. Taluka Search Catalog
* **Route:** `GET /api/talukas`
* **Description:** Returns the complete directory of 194 monitored talukas for instant search autocomplete and voice recognition.
* **Sample Item:**
```json
[
  {
    "taluka_name": "Haveli",
    "taluka_name_mr": "हवेली",
    "district_name": "Pune",
    "district_name_mr": "पुणे",
    "lgd_code": 4983,
    "division": "Pune"
  }
]
```

---

### 3. Taluka Real-Time Insights & Farmer Advisory
* **Route:** `GET /api/taluka/{query}`
* **Parameters:** `query` (Taluka name in English, Marathi, or LGD numeric code)
* **Description:** Returns live agrometeorological telemetry, dual-mode ML predictions, 4 metric cards, and university-anchored advisory.
* **Sample Request:** `GET /api/taluka/haveli` or `GET /api/taluka/4983`
* **Response Structure:**
```json
{
  "meta": {
    "taluka": "Haveli",
    "taluka_mr": "हवेली",
    "district": "Pune",
    "division": "Pune",
    "lgd_code": 4983,
    "agro_climatic_zone": "Western Maharashtra Plain Zone",
    "soil_type": "Medium Black"
  },
  "metrics": {
    "rainfall_jjas_mm": 682.4,
    "departure_pct": -8.5,
    "spi_3": -0.42,
    "soil_moisture_index": 0.62,
    "consecutive_dry_days": 6,
    "reservoir_storage_pct": 74.2
  },
  "predictions": {
    "mode_1_diagnostic": {
      "risk_code": 0,
      "label_en": "Safe",
      "label_mr": "सुरक्षित",
      "confidence": 0.94
    },
    "mode_2_forecaster_30d": {
      "risk_code": 1,
      "label_en": "Watch",
      "label_mr": "लक्ष ठेवा (अल्प तूट)",
      "confidence": 0.79
    }
  },
  "advisory": {
    "university_anchor": {
      "university_name_en": "Mahatma Phule Krishi Vidyapeeth, Rahuri (MPKV)",
      "university_name_mr": "महात्मा फुले कृषी विद्यापीठ, राहुरी (राहुरी)",
      "zone": "Western Maharashtra & Scarcity Zone"
    },
    "prescriptive_actions": {
      "irrigation_strategy": {
        "en": "Soil has healthy moisture balance. Hold off watering for 3-4 days.",
        "mr": "जमिनीत चांगला वाफसा आहे, पुढील ३ ते ४ दिवस पाणी देऊ नका."
      },
      "moisture_conservation": {
        "en": "Spread crop residue as mulching to retain soil moisture.",
        "mr": "जमिनीतील ओल टिकवण्यासाठी पिकाच्या ओळींत पाचट पसरा."
      },
      "foliar_and_nutrients": {
        "en": "Spray 1% Potassium Nitrate in the early morning if heat stress rises.",
        "mr": "उन्हाचा ताण जाणवल्यास १० लिटर पाण्यात १०० ग्रॅम पोटॅशियम नायट्रेट मिसळून फवारणी करा."
      }
    }
  }
}
```

---

### 4. Statewide Macro Analytics
* **Route:** `GET /api/analytics/overview`
* **Description:** State-level macro summary, risk distribution breakdown, and top 5 vulnerable drought hotspots.

---

### 5. District Rollup Statistics
* **Route:** `GET /api/districts`
* **Description:** Aggregates telemetry and risk tiers across all 36 Maharashtra districts.

---

### 6. Head-to-Head Taluka Comparison
* **Route:** `GET /api/compare?taluka1=Haveli&taluka2=Baramati`
* **Description:** Computes agronomic and hydrological differentials between two talukas (rainfall, SPI, soil moisture, dry days).

---

### 7. Major Dam Reservoirs Telemetry
* **Route:** `GET /api/reservoirs`
* **Description:** Live storage percentage and operational alert level for all 12 major Maharashtra dams (Jayakwadi, Koyna, Ujani, Bhatsa, Totladoh, etc.).

---

### 8. Annotated GeoJSON Boundary Polygons
* **Route:** `GET /api/map/geojson`
* **Description:** Pre-computed GeoJSON polygon boundaries styled with real-time risk classification colors for Leaflet choropleth rendering.

---

### 9. Neural Speech Audio Advisory
* **Route:** `GET /api/audio/advisory/{query}?lang=mr` (or `lang=en`)
* **Description:** Generates and streams high-fidelity Marathi (`mr-IN-ManoharNeural`) or Indian English (`en-IN-PrabhatNeural`) voice advisory audio (MP3).
