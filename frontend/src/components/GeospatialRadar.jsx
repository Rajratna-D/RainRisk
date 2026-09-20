import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Play, Pause, Compass, MapPin, Maximize2, AlertTriangle, Droplets, Layers } from 'lucide-react';
import { fetchMapData } from '../api/client';

const CATEGORY_COLORS = {
  'No Rainfall': '#64748b',
  'Large Deficient': '#f43f5e',
  'Deficient': '#f59e0b',
  'Normal': '#10b981',
  'Excess': '#06b6d4',
  'Large Excess': '#3b82f6',
};

const REGIONS = ['All India', 'Northwest India', 'Central India', 'South Peninsula', 'East & Northeast India'];

const REGION_BOUNDS = {
  'All India': [[8.0, 68.0], [37.0, 97.5]],
  'Northwest India': [[23.5, 68.0], [37.0, 84.5]],
  'Central India': [[17.5, 68.5], [26.5, 87.5]],
  'South Peninsula': [[8.0, 71.5], [20.0, 85.0]],
  'East & Northeast India': [[21.5, 83.5], [29.5, 97.5]],
};

const CATEGORY_FILTERS = ['ALL', 'DROUGHT', 'NORMAL', 'SURPLUS'];

export default function GeospatialRadar({ initialYear = 2015, onSelectSubdivision }) {
  const [year, setYear] = useState(initialYear);
  const [region, setRegion] = useState('All India');
  const [mode, setMode] = useState('actual');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [isPlaying, setIsPlaying] = useState(false);
  const [mapData, setMapData] = useState(null);

  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const playRef = useRef(null);

  useEffect(() => {
    if (initialYear) setYear(initialYear);
  }, [initialYear]);

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [22.8, 82.5],
      zoom: 4.8,
      minZoom: 4,
      maxZoom: 9,
      zoomControl: false,
      attributionControl: false,
    });

    L.tileLayer(
      'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 16 }
    ).addTo(map);

    L.tileLayer(
      'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 16, opacity: 0.6 }
    ).addTo(map);

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    markersLayerRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    fetchMapData(year, region, mode)
      .then(setMapData)
      .catch((err) => console.error('Map fetch error:', err));
  }, [year, region, mode]);

  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const bounds = REGION_BOUNDS[region] || REGION_BOUNDS['All India'];
    mapInstanceRef.current.flyToBounds(bounds, { padding: [25, 25], duration: 1.0, easeLinearity: 0.25 });
  }, [region]);

  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current || !mapData) return;

    const layerGroup = markersLayerRef.current;
    layerGroup.clearLayers();

    const filteredRecords = mapData.records.filter((rec) => {
      if (categoryFilter === 'ALL') return true;
      if (categoryFilter === 'DROUGHT') return rec.category.includes('Deficient') || rec.category === 'No Rainfall';
      if (categoryFilter === 'NORMAL') return rec.category === 'Normal';
      if (categoryFilter === 'SURPLUS') return rec.category.includes('Excess');
      return true;
    });

    filteredRecords.forEach((sub) => {
      const color = CATEGORY_COLORS[sub.category] || '#94a3b8';
      const isDrought = sub.category.includes('Deficient');

      const marker = L.circleMarker([sub.lat, sub.lon], {
        radius: isDrought ? 9 : 7,
        fillColor: color,
        color: '#ffffff',
        weight: 1.2,
        opacity: 0.9,
        fillOpacity: 0.85,
      });

      marker.bindTooltip(
        `<div style="font-family: Inter, sans-serif; font-size: 11px;">
           <strong style="color: var(--text-primary);">${sub.subdivision}</strong><br/>
           <span style="color:${color}; font-weight:600;">${sub.category} (${sub.departure > 0 ? '+' : ''}${sub.departure}%)</span>
         </div>`,
        { direction: 'top', offset: [0, -6], className: 'custom-map-tooltip' }
      );

      const popupHtml = `
        <div style="font-family: Inter, sans-serif; min-width: 190px;">
          <div style="font-size: 13px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; font-family: Outfit, sans-serif;">
            ${sub.subdivision}
          </div>
          <div style="display: inline-block; background: ${color}22; border: 1px solid ${color}66; color: ${color}; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 9999px; margin-bottom: 8px;">
            ${sub.category.toUpperCase()}
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px; margin-bottom: 10px; font-family: 'JetBrains Mono', monospace;">
            <div style="background: var(--bg-stat); padding: 5px 8px; border-radius: 4px;">
              <span style="color: var(--text-muted); display: block; font-size: 9px;">JJAS RAIN</span>
              <strong style="color: var(--text-primary);">${sub.jjas} mm</strong>
            </div>
            <div style="background: var(--bg-stat); padding: 5px 8px; border-radius: 4px;">
              <span style="color: var(--text-muted); display: block; font-size: 9px;">DEPARTURE</span>
              <strong style="color: ${color};">${sub.departure > 0 ? '+' : ''}${sub.departure}%</strong>
            </div>
          </div>
          <button id="inspect-sub-${sub.subdivision.replace(/\s+/g, '-')}" style="width: 100%; background: var(--bg-stat); border: 1px solid var(--border-hover); color: var(--text-primary); font-size: 10px; font-weight: 600; padding: 5px 0; border-radius: 6px; cursor: pointer; transition: all 0.15s ease;">
            Inspect in Regional Explorer
          </button>
        </div>
      `;

      marker.bindPopup(popupHtml);
      // Retaining subdivisionName on marker instance enables fly-to focus and popup triggering from leaderboard clicks
      marker.subdivisionName = sub.subdivision;

      marker.on('popupopen', () => {
        const btnId = `inspect-sub-${sub.subdivision.replace(/\s+/g, '-')}`;
        setTimeout(() => {
          const btn = document.getElementById(btnId);
          if (btn) btn.onclick = () => onSelectSubdivision?.(sub.subdivision);
        }, 10);
      });

      marker.addTo(layerGroup);
    });
  }, [mapData, categoryFilter, onSelectSubdivision]);

  useEffect(() => {
    if (isPlaying) {
      playRef.current = setInterval(() => {
        setYear((prev) => (prev >= 2017 ? 1901 : prev + 1));
      }, 700);
    } else {
      clearInterval(playRef.current);
    }
    return () => clearInterval(playRef.current);
  }, [isPlaying]);

  const handleResetView = () => {
    if (!mapInstanceRef.current) return;
    setRegion('All India');
    mapInstanceRef.current.flyToBounds(REGION_BOUNDS['All India'], { padding: [25, 25], duration: 0.8 });
  };

  const handleFlyToSub = (subName) => {
    if (!mapInstanceRef.current || !mapData) return;
    const match = mapData.records.find((r) => r.subdivision === subName);
    if (match) {
      mapInstanceRef.current.flyTo([match.lat, match.lon], 7, { duration: 0.8 });
      markersLayerRef.current.eachLayer((layer) => {
        if (layer.subdivisionName === subName) {
          layer.openPopup();
        }
      });
    }
  };

  const normalCount = mapData ? mapData.records.filter((r) => r.category === 'Normal').length : 0;
  const surplusCount = mapData ? mapData.records.filter((r) => r.category.includes('Excess')).length : 0;

  return (
    <div>
      <div className="bento-card" style={{ marginBottom: '1.25rem', padding: '1.1rem 1.35rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr 1fr', gap: '1.5rem', alignItems: 'center' }}>
          <div>
            <div className="slider-header">
              <span className="slider-label" style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <Compass size={15} color="var(--accent-teal)" /> Historical Monsoon Timeline
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  style={{
                    background: isPlaying ? 'rgba(251,113,133,0.15)' : 'rgba(255,255,255,0.06)',
                    border: `1px solid ${isPlaying ? 'var(--risk-danger)' : 'var(--border-subtle)'}`,
                    color: isPlaying ? 'var(--risk-danger)' : 'var(--text-secondary)',
                    borderRadius: '50%',
                    width: 26, height: 26,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    cursor: 'pointer', transition: 'all 0.15s ease',
                  }}
                  title={isPlaying ? 'Pause Timeline' : 'Play Timeline (1901-2017)'}
                >
                  {isPlaying ? <Pause size={12} /> : <Play size={12} style={{ marginLeft: 1 }} />}
                </button>
                <span className="slider-value" style={{ fontSize: '1.15rem', minWidth: '4ch', letterSpacing: '0.02em' }}>
                  {year}
                </span>
              </div>
            </div>
            <input
              type="range"
              min={1901}
              max={2017}
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-teal)' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.66rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono', marginTop: '0.2rem' }}>
              <span>1901</span>
              <span>1930</span>
              <span>1960</span>
              <span>1990</span>
              <span>2017</span>
            </div>
          </div>

          <div>
            <div className="slider-header">
              <span className="slider-label" style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <MapPin size={15} color="var(--accent-blue)" /> Macro-Region Focus
              </span>
            </div>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="select-input"
              style={{ width: '100%', padding: '0.45rem 0.65rem', fontSize: '0.78rem' }}
            >
              {REGIONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <div>
            <div className="slider-header">
              <span className="slider-label" style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <Layers size={15} color="var(--accent-amber)" /> Data Layer
              </span>
            </div>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <button
                className={`preset-chip ${mode === 'actual' ? 'active' : ''}`}
                style={{ flex: 1, padding: '0.45rem 0', justifyContent: 'center' }}
                onClick={() => setMode('actual')}
              >Observed IMD</button>
              <button
                className={`preset-chip ${mode === 'prediction' ? 'active' : ''}`}
                style={{ flex: 1, padding: '0.45rem 0', justifyContent: 'center' }}
                onClick={() => setMode('prediction')}
              >RF Forecast</button>
            </div>
          </div>
        </div>
      </div>

      {mapData && (
        <div className="status-strip">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '0.04em' }}>
              {year} ALL-INDIA PROFILE:
            </span>
            <span style={{ color: 'var(--text-secondary)' }}>
              {mapData.deficient_percentage}% Area Drought Stress
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', fontSize: '0.75rem' }}>
            <span style={{ color: 'var(--accent-rose)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <span className="status-dot" style={{ background: 'var(--accent-rose)' }}></span>
              Deficit {mapData.deficient_count}
            </span>
            <span style={{ color: 'var(--text-muted)' }}>-</span>
            <span style={{ color: 'var(--risk-safe)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <span className="status-dot" style={{ background: 'var(--risk-safe)' }}></span>
              Normal {normalCount}
            </span>
            <span style={{ color: 'var(--text-muted)' }}>-</span>
            <span style={{ color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <span className="status-dot" style={{ background: 'var(--accent-blue)' }}></span>
              Surplus {surplusCount}
            </span>
          </div>
        </div>
      )}

      <div className="grid-split">
        <div className="bento-card" style={{ padding: '0.75rem', position: 'relative' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem', padding: '0.35rem 0.6rem' }}>
            <div>
              <h3 className="section-title">
                <Layers size={16} color="var(--accent-teal)" />
                Sub-Continental Drought Radar: India
              </h3>
              <span className="section-subtitle">Esri Dark Cartography - 36 Meteorological Subdivisions</span>
            </div>

            <div style={{ display: 'flex', gap: '0.3rem' }}>
              {CATEGORY_FILTERS.map((f) => (
                <button
                  key={f}
                  onClick={() => setCategoryFilter(f)}
                  className={`preset-chip ${categoryFilter === f ? 'active' : ''}`}
                  style={{ fontSize: '0.66rem', padding: '0.2rem 0.55rem' }}
                >{f}</button>
              ))}
            </div>
          </div>

          <div className="india-map-wrapper">
            <div ref={mapContainerRef} className="india-map-container" />

            <div className="map-floating-panel">
              <button
                onClick={handleResetView}
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.35rem 0.65rem',
                  fontSize: '0.68rem', fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '0.35rem',
                  transition: 'var(--transition)',
                }}
                title="Fit full bounds of India"
              >
                <Maximize2 size={11} /> Reset India Framing
              </button>
            </div>

            <div className="map-floating-legend">
              <span style={{ fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', fontSize: '0.64rem' }}>IMD Tiers:</span>
              {Object.entries(CATEGORY_COLORS).map(([cat, col]) => (
                <div key={cat} className="legend-item" title={cat}>
                  <span className="legend-dot" style={{ background: col, color: col }}></span>
                  <span style={{ color: 'var(--text-secondary)' }}>{cat}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="bento-card" style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <AlertTriangle size={15} color="var(--accent-rose)" />
                <h4 style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>Most Deficient Subdivisions ({year})</h4>
              </div>
              <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Click to zoom</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              {mapData && mapData.top_deficient && mapData.top_deficient.length > 0 ? (
                mapData.top_deficient.map((item, i) => (
                  <div
                    key={item.subdivision}
                    className="extreme-row"
                    style={{ borderLeftColor: 'var(--accent-rose)' }}
                    onClick={() => handleFlyToSub(item.subdivision)}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(251,113,133,0.08)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--bg-inner)')}
                    title="Click to focus on map"
                  >
                    <div>
                      <span className="extreme-row-name">{i + 1}. {item.subdivision}</span>
                      <span className="extreme-row-detail">{item.jjas} mm rainfall</span>
                    </div>
                    <span className="extreme-row-departure" style={{ color: 'var(--accent-rose)' }}>
                      {item.departure}%
                    </span>
                  </div>
                ))
              ) : (
                <div style={{ padding: '0.85rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.78rem', textAlign: 'center', fontStyle: 'italic' }}>
                  No subdivisions in drought/deficit for {year}
                </div>
              )}
            </div>
          </div>

          <div className="bento-card" style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <Droplets size={15} color="var(--accent-blue)" />
                <h4 style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>Most Surplus Subdivisions ({year})</h4>
              </div>
              <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Click to zoom</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              {mapData && mapData.top_excess && mapData.top_excess.length > 0 ? (
                mapData.top_excess.map((item, i) => (
                  <div
                    key={item.subdivision}
                    className="extreme-row"
                    style={{ borderLeftColor: 'var(--accent-blue)' }}
                    onClick={() => handleFlyToSub(item.subdivision)}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(96,165,250,0.08)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--bg-inner)')}
                    title="Click to focus on map"
                  >
                    <div>
                      <span className="extreme-row-name">{i + 1}. {item.subdivision}</span>
                      <span className="extreme-row-detail">{item.jjas} mm rainfall</span>
                    </div>
                    <span className="extreme-row-departure" style={{ color: 'var(--accent-blue)' }}>
                      +{item.departure}%
                    </span>
                  </div>
                ))
              ) : (
                <div style={{ padding: '0.85rem 0.5rem', color: 'var(--text-muted)', fontSize: '0.78rem', textAlign: 'center', fontStyle: 'italic' }}>
                  No subdivisions in surplus for {year}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
