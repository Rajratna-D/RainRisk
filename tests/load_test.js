import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

// Custom Trend Metrics to track latency separately
const cacheHitLatency = new Trend('cache_hit_latency');
const liveComputeLatency = new Trend('live_compute_latency');
const failureRate = new Rate('failed_requests');

export const options = {
  stages: [
    { duration: '20s', target: 10 },  // Ramp-up: 1 to 10 Virtual Users (VUs)
    { duration: '40s', target: 50 },  // Sustained load: 50 concurrent users
    { duration: '30s', target: 100 }, // Stress spike: 100 concurrent users
    { duration: '20s', target: 0 },   // Cool-down
  ],
  thresholds: {
    // 95% of all requests must complete within 200ms
    http_req_duration: ['p(95)<200'],
    // Error rate must remain under 1%
    failed_requests: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

const POPULAR_TALUKAS = [
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
  // -------------------------------------------------------------
  // Scenario A: 80% of users view standard taluka dashboard (Cached)
  // -------------------------------------------------------------
  const taluka = POPULAR_TALUKAS[Math.floor(Math.random() * POPULAR_TALUKAS.length)];
  const cachedRes = http.get(`${BASE_URL}/api/v1/taluka/${taluka}/risk`);
  
  const isOk = check(cachedRes, {
    'status is 200': (r) => r.status === 200,
    'has risk_score': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.risk_score !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  if (!isOk) {
    failureRate.add(1);
  }
  cacheHitLatency.add(cachedRes.timings.duration);

  // -------------------------------------------------------------
  // Scenario B: 20% of users trigger a "What-If" simulation (Compute)
  // -------------------------------------------------------------
  if (Math.random() < 0.20) {
    const payload = JSON.stringify({
      taluka_id: taluka,
      rainfall_shock_pct: -25.0,
      temperature_delta_c: 1.8
    });

    const params = {
      headers: { 'Content-Type': 'application/json' },
    };

    const simRes = http.post(`${BASE_URL}/api/v1/simulate`, payload, params);
    
    const isSimOk = check(simRes, {
      'simulation status is 200': (r) => r.status === 200,
      'has shap_drivers': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.top_drivers !== undefined;
        } catch (e) {
          return false;
        }
      },
    });

    if (!isSimOk) {
      failureRate.add(1);
    }
    liveComputeLatency.add(simRes.timings.duration);
  }

  // Realistic user reading/pause time: 1 to 2.5 seconds
  sleep(Math.random() * 1.5 + 1.0);
}

