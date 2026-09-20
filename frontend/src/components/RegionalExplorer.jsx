import React, { useState, useEffect, useMemo } from 'react';
import { fetchSubdivisions, fetchSubdivisionDetail } from '../api/client';
import { GitCompare, Calendar, BarChart2 } from 'lucide-react';

function Sparkline({ data, color = '#60a5fa', width = 120, height = 28 }) {
  if (!data || data.length === 0) return null;

  const values = data.map((d) => d.jjas);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width;
    const y = height - 2 - ((v - min) / range) * (height - 4);
    return `${x},${y}`;
  }).join(' ');

  const areaPath = `M 0,${height} ` +
    values.map((v, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - 2 - ((v - min) / range) * (height - 4);
      return `L ${x},${y}`;
    }).join(' ') +
    ` L ${width},${height} Z`;

  return (
    <div className="sparkline-wrapper">
      <svg className="sparkline-svg" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id={`spark-fill-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.25" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill={`url(#spark-fill-${color.replace('#','')})`} />
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
      </svg>
    </div>
  );
}

export default function RegionalExplorer({ selectedSub = 'Kerala' }) {
  const [subdivisions, setSubdivisions] = useState([]);
  const [focusSub, setFocusSub] = useState(selectedSub);
  const [twinSub, setTwinSub] = useState('West Rajasthan');
  const [focusData, setFocusData] = useState(null);
  const [twinData, setTwinData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubdivisions().then(setSubdivisions);
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchSubdivisionDetail(focusSub),
      fetchSubdivisionDetail(twinSub),
    ])
      .then(([fData, tData]) => {
        setFocusData(fData);
        setTwinData(tData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed loading subdivision detail:', err);
        setLoading(false);
      });
  }, [focusSub, twinSub]);

  // Memoizing chart scale ceilings avoids scanning array extrema during state updates
  const focusMaxJJAS = useMemo(() => {
    if (!focusData?.timeline) return 1;
    return Math.max(...focusData.timeline.map((x) => x.jjas), 1);
  }, [focusData]);

  const focusMaxMonthly = useMemo(() => {
    if (!focusData?.monthly) return 1;
    return Math.max(...focusData.monthly.map((x) => x.rainfall), 1);
  }, [focusData]);

  return (
    <div>
      <div className="bento-card" style={{ marginBottom: '1.25rem', padding: '1.2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          <div>
            <label className="metric-label" style={{ marginBottom: '0.35rem', display: 'block' }}>
              Primary Target Subdivision
            </label>
            <select
              value={focusSub}
              onChange={(e) => setFocusSub(e.target.value)}
              className="custom-select"
            >
              {subdivisions.map((s) => (
                <option key={s.name} value={s.name}>{s.name} ({s.macro_region})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="metric-label" style={{ marginBottom: '0.35rem', display: 'block' }}>
              Comparative Climate Twin
            </label>
            <select
              value={twinSub}
              onChange={(e) => setTwinSub(e.target.value)}
              className="custom-select"
            >
              {subdivisions.map((s) => (
                <option key={s.name} value={s.name}>{s.name} ({s.macro_region})</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {focusData && (
          <SubdivisionCard
            data={focusData}
            accentColor="#38bdf8"
            chipActive
          />
        )}
        {twinData && (
          <SubdivisionCard
            data={twinData}
            accentColor="#f59e0b"
          />
        )}
      </div>

      {focusData && (
        <div className="bento-card" style={{ marginBottom: '1.5rem' }}>
          <div className="section-header">
            <div>
              <h3 className="section-title">{focusData.metadata.name} Historical Monsoon Series (1901-2017)</h3>
              <p className="section-subtitle">
                Annual JJAS rainfall records colored by IMD drought severity tier relative to LPA ({focusData.metadata.lpa} mm).
              </p>
            </div>
            <div className="chart-legend">
              <span style={{ color: 'var(--risk-danger)' }}>• Large Deficit</span>
              <span style={{ color: 'var(--risk-warning)' }}>• Deficit</span>
              <span style={{ color: 'var(--risk-safe)' }}>• Normal</span>
              <span style={{ color: 'var(--accent-teal)' }}>• Surplus</span>
            </div>
          </div>

          <div className="bar-chart-container">
            {focusData.timeline.map((d) => {
              const heightPct = Math.max(8, (d.jjas / focusMaxJJAS) * 100);
              return (
                <div
                  key={d.year}
                  className="bar-item"
                  title={`${d.year}: ${d.jjas} mm (${d.category}, ${d.departure}%)`}
                  style={{ height: `${heightPct}%`, background: d.color }}
                />
              );
            })}
          </div>
        </div>
      )}

      {focusData && (
        <div className="grid-split">
          <div className="bento-card">
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>12-Month Mean Precipitation Distribution</h4>
            <div className="monthly-chart">
              {focusData.monthly.map((m) => {
                const barH = Math.max(4, (m.rainfall / focusMaxMonthly) * 120);
                const isMonsoon = ['JUN', 'JUL', 'AUG', 'SEP'].includes(m.month);
                return (
                  <div key={m.month} className="monthly-bar-col">
                    <span className="monthly-bar-value">
                      {m.rainfall > 0 ? Math.round(m.rainfall) : ''}
                    </span>
                    <div
                      className="monthly-bar"
                      style={{
                        height: `${barH}px`,
                        background: isMonsoon
                          ? 'linear-gradient(to top, #2dd4a8, #60a5fa)'
                          : 'var(--bar-inactive)',
                      }}
                      title={`${m.month}: ${m.rainfall} mm`}
                    />
                    <span
                      className="monthly-bar-label"
                      style={{
                        color: isMonsoon ? 'var(--text-primary)' : 'var(--text-muted)',
                        fontWeight: isMonsoon ? 600 : 400,
                      }}
                    >
                      {m.month}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bento-card">
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>Decadal Regime Shift Matrix</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              {focusData.epochs.map((ep) => (
                <div key={ep.epoch} className="epoch-row">
                  <span className="epoch-label">{ep.epoch}</span>
                  <div className="epoch-stats">
                    <span>Mean: <strong style={{ color: 'var(--text-bright)' }}>{ep.mean} mm</strong></span>
                    <span>CV: <strong style={{ color: 'var(--accent-sky)' }}>{ep.cv}%</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SubdivisionCard({ data, accentColor, chipActive = false }) {
  const stats = [
    { label: 'LPA Baseline', value: `${data.metadata.lpa} mm` },
    { label: 'Mean JJAS', value: `${data.metadata.mean_jjas} mm` },
    { label: 'Volatility', value: `${data.metadata.cv}%`, color: accentColor },
    { label: 'Drought Rate', value: `${data.metadata.drought_frequency}%`, color: 'var(--accent-red)' },
  ];

  return (
    <div className="bento-card" style={{ borderTop: `3px solid ${accentColor}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '1.15rem' }}>{data.metadata.name}</h3>
        <span className={`preset-chip ${chipActive ? 'active' : ''}`}>{data.metadata.macro_region}</span>
      </div>

      {data.timeline && (
        <div style={{ marginBottom: '0.75rem' }}>
          <Sparkline data={data.timeline} color={accentColor} />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', padding: '0 0.15rem' }}>
            <span>1901</span>
            <span style={{ fontSize: '0.58rem', color: 'var(--text-muted)' }}>117-yr JJAS trend</span>
            <span>2017</span>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', textAlign: 'center' }}>
        {stats.map((s) => (
          <div key={s.label} className="stat-cell">
            <div className="stat-cell-label">{s.label}</div>
            <div className="stat-cell-value" style={s.color ? { color: s.color } : undefined}>
              {s.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
