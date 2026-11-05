import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

// ============================================================================
// MAHARAINRISK PRODUCTION LOAD TEST SUITE (PHASE 9)
// Architectural Policy: Option A (Zero Counterfactual Simulation)
// Real Endpoints: Telemetry (60%), TreeSHAP (20%), Spatial (10%), State (5%), MCP (5%)
// ============================================================================

const riskLatency = new Trend('risk_telemetry_latency');
const xaiLatency = new Trend('treeshap_xai_latency');
const spatialLatency = new Trend('spatial_adjacency_latency');
const failureRate = new Rate('failed_requests');

export const options = {
  stages: [
    { duration: '15s', target: 10 },  // Ramp-up: 1 to 10 Virtual Users (VUs)
    { duration: '30s', target: 50 },  // Sustained load: 50 concurrent users
    { duration: '20s', target: 100 }, // Peak stress spike: 100 concurrent users
    { duration: '15s', target: 0 },   // Graceful cool-down
  ],
  thresholds: {
    // 95% of all requests must complete within 200ms
    http_req_duration: ['p(95)<200'],
    // Error rate must remain under 1%
    failed_requests: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

const BENCHMARK_TALUKAS = [
  'haveli',
  'baramati',
  'solapur_north',
  'chhatrapati_sambhajinagar',
  'nashik',
  'amravati',
  'jalgaon',
  'nagpur_urban'
];

export default function () {
  const taluka = BENCHMARK_TALUKAS[Math.floor(Math.random() * BENCHMARK_TALUKAS.length)];
  const roll = Math.random();

  if (roll < 0.60) {
    // -----------------------------------------------------------------------
    // Scenario 1 (60%): High-Frequency Cached Taluka Risk Telemetry
    // -----------------------------------------------------------------------
    const res = http.get(`${BASE_URL}/api/v1/taluka/${taluka}/risk`);
    const isOk = check(res, {
      'risk status is 200': (r) => r.status === 200,
      'has risk_score': (r) => {
        try {
          return JSON.parse(r.body).risk_score !== undefined;
        } catch {
          return false;
        }
      },
    });

    if (!isOk) failureRate.add(1);
    riskLatency.add(res.timings.duration);

  } else if (roll < 0.80) {
    // -----------------------------------------------------------------------
    // Scenario 2 (20%): TreeSHAP Explainable AI Attributions & Vernacular Text
    // -----------------------------------------------------------------------
    const res = http.get(`${BASE_URL}/api/v1/taluka/${taluka}/explain`);
    const isOk = check(res, {
      'explain status is 200': (r) => r.status === 200,
      'has top_risk_escalators': (r) => {
        try {
          const body = JSON.parse(r.body);
          return Array.isArray(body.top_risk_escalators || body.top_escalators);
        } catch {
          return false;
        }
      },
    });

    if (!isOk) failureRate.add(1);
    xaiLatency.add(res.timings.duration);

  } else if (roll < 0.90) {
    // -----------------------------------------------------------------------
    // Scenario 3 (10%): Geospatial Adjacency & Boundary Contagion Radar
    // -----------------------------------------------------------------------
    const res = http.get(`${BASE_URL}/api/v1/taluka/${taluka}/adjacent`);
    const isOk = check(res, {
      'adjacent status is 200': (r) => r.status === 200,
      'has adjacent_neighbors': (r) => {
        try {
          const body = JSON.parse(r.body);
          return Array.isArray(body.adjacent_neighbors || body.neighbors);
        } catch {
          return false;
        }
      },
    });

    if (!isOk) failureRate.add(1);
    spatialLatency.add(res.timings.duration);

  } else if (roll < 0.95) {
    // -----------------------------------------------------------------------
    // Scenario 4 (5%): Statewide 194-Taluka High-Capacity Rollup
    // -----------------------------------------------------------------------
    const res = http.get(`${BASE_URL}/api/v1/state/summary`);
    const isOk = check(res, {
      'state summary status is 200': (r) => r.status === 200,
      'has total_talukas': (r) => {
        try {
          const body = JSON.parse(r.body);
          return (body.total_talukas_monitored === 194 || body.total_talukas === 194);
        } catch {
          return false;
        }
      },
    });

    if (!isOk) failureRate.add(1);

  } else {
    // -----------------------------------------------------------------------
    // Scenario 5 (5%): Model Context Protocol (MCP) Cloud Gateway Probe
    // -----------------------------------------------------------------------
    const res = http.get(`${BASE_URL}/mcp`);
    const isOk = check(res, {
      'mcp status is 200': (r) => r.status === 200,
      'mcp is operational': (r) => {
        try {
          return JSON.parse(r.body).status === 'operational';
        } catch {
          return false;
        }
      },
    });

    if (!isOk) failureRate.add(1);
  }

  // Realistic human / edge agent pause: 0.5s to 1.5s
  sleep(Math.random() * 1.0 + 0.5);
}
