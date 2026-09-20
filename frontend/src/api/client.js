/**
 * RainRisk API Client
 * Connects to FastAPI backend endpoints with fallback handling.
 */

const BASE_URL = ''; // Relative path leverages Vite proxy or FastAPI static serving

export async function fetchOverview() {
  const res = await fetch(`${BASE_URL}/api/overview`);
  if (!res.ok) throw new Error('Failed to fetch overview metrics');
  return res.json();
}

export async function fetchSubdivisions() {
  const res = await fetch(`${BASE_URL}/api/subdivisions`);
  if (!res.ok) throw new Error('Failed to fetch subdivisions list');
  return res.json();
}

export async function fetchSubdivisionDetail(name) {
  const res = await fetch(`${BASE_URL}/api/subdivision/${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error(`Failed to fetch details for ${name}`);
  return res.json();
}

export async function fetchMapData(year = 2015, region = 'All India', mode = 'actual') {
  const res = await fetch(`${BASE_URL}/api/map?year=${year}&region=${encodeURIComponent(region)}&mode=${mode}`);
  if (!res.ok) throw new Error('Failed to fetch map data');
  return res.json();
}

export async function fetchLeaderboard() {
  const res = await fetch(`${BASE_URL}/api/leaderboard`);
  if (!res.ok) throw new Error('Failed to fetch model leaderboard');
  return res.json();
}

export async function fetchMethodology() {
  const res = await fetch(`${BASE_URL}/api/methodology`);
  if (!res.ok) throw new Error('Failed to fetch methodology');
  return res.json();
}

export async function runPrediction(payload) {
  const res = await fetch(`${BASE_URL}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Inference request failed');
  return res.json();
}
