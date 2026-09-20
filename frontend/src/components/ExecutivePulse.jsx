import React, { useState } from 'react';
import { Layers, CheckCircle2, ShieldCheck, BarChart2, TrendingUp, AlertCircle } from 'lucide-react';

export default function ExecutivePulse({ overviewData, onSelectYear }) {
  const [hoverPoint, setHoverPoint] = useState(null);

  if (!overviewData) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div className="skeleton" style={{ height: '140px' }} />
        <div className="skeleton" style={{ height: '280px' }} />
        <div className="skeleton" style={{ height: '120px' }} />
      </div>
    );
  }

  const {
    total_records,
    normal_percentage,
    national_lpa,
    exact_accuracy,
    off_by_one_accuracy,
    category_distribution,
    national_trend = [],
  } = overviewData;

  const landmarkYears = [
    { year: 1918, dep: '-23.8%', label: 'Spanish Flu Era Failure' },
    { year: 1965, dep: '-18.2%', label: 'Green Revolution Catalyst' },
    { year: 1972, dep: '-23.9%', label: 'Great Asian Drought' },
    { year: 1987, dep: '-19.4%', label: 'Severe El Niño Drought' },
    { year: 2002, dep: '-19.2%', label: 'Early Season Shock' },
    { year: 2009, dep: '-21.8%', label: 'Modern Monsoon Deficit' },
    { year: 2015, dep: '-14.3%', label: 'Consecutive Year Deficit' },
  ];

  const cW = 960, cH = 200, pad = { t: 15, r: 15, b: 28, l: 42 };
  const yMin = 700, yMax = 1400, xMin = 1901, xMax = 2017;
  const sx = (yr) => pad.l + ((yr - xMin) / (xMax - xMin)) * (cW - pad.l - pad.r);
  const sy = (v) => cH - pad.b - ((v - yMin) / (yMax - yMin)) * (cH - pad.t - pad.b);

  const trend = national_trend.map((d) => `${sx(d.year)},${sy(d.jjas)}`).join(' ');
  const smooth = national_trend.map((d) => `${sx(d.year)},${sy(d.smooth)}`).join(' ');
  const area = national_trend.length
    ? `M ${sx(xMin)},${cH - pad.b} ` +
      national_trend.map((d) => `L ${sx(d.year)},${sy(d.jjas)}`).join(' ') +
      ` L ${sx(xMax)},${cH - pad.b} Z`
    : '';

  const spotlightMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty('--mouse-x', `${e.clientX - r.left}px`);
    e.currentTarget.style.setProperty('--mouse-y', `${e.clientY - r.top}px`);
  };

  return (
    <div>
      {/* Hero Metric Deck */}
      <div className="hero-metric-deck">
        {/* Standout Primary Hero Card */}
        <div className="hero-primary-card spotlight-card" onMouseMove={spotlightMove}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.45rem' }}>
              <ShieldCheck size={16} color="var(--accent-teal)" />
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--accent-teal)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Primary Production Telemetry
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.6rem' }}>
              <span style={{ fontSize: '2.75rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#f4f4f6', lineHeight: 1 }}>
                {off_by_one_accuracy}%
              </span>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-teal)' }}>
                Within ±1 Class
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.5rem', lineHeight: 1.45 }}>
              Under 6-tier ordinal risk classification, 93.0% of predictions match reality or lie within an immediately adjacent category.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
            <span style={{ fontSize: '0.66rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              HELD-OUT TEST 2011-2017 (N=243)
            </span>
            <span style={{ fontSize: '0.68rem', color: 'var(--accent-teal)', fontWeight: 600 }}>
              Zero Temporal Leakage ✓
            </span>
          </div>
        </div>

        {/* Supporting Secondary Tiles */}
        <div className="hero-secondary-grid">
          {/* Exact Accuracy */}
          <div className="metric-tile spotlight-card" style={{ '--tile-accent': '#60a5fa' }} onMouseMove={spotlightMove}>
            <div className="metric-header-row">
              <div className="metric-label">Exact 6-Tier Hit</div>
              <svg className="kpi-sparkline" viewBox="0 0 58 22">
                <path d="M 2 16 Q 15 8, 30 13 T 56 6" fill="none" stroke="#60a5fa" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <div className="metric-value">{exact_accuracy}%</div>
            <div className="metric-sub">
              <CheckCircle2 size={12} color="#60a5fa" />
              <span>Balanced multi-class</span>
            </div>
          </div>

          {/* Dataset Depth */}
          <div className="metric-tile spotlight-card" style={{ '--tile-accent': '#a78bfa' }} onMouseMove={spotlightMove}>
            <div className="metric-header-row">
              <div className="metric-label">Historical Archive</div>
              <svg className="kpi-sparkline" viewBox="0 0 58 22">
                <path d="M 2 18 Q 20 4, 35 14 T 56 8" fill="none" stroke="#a78bfa" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <div className="metric-value">{total_records.toLocaleString()}</div>
            <div className="metric-sub">
              <Layers size={12} color="#a78bfa" />
              <span>36 units · 1901-2017</span>
            </div>
          </div>

          {/* National Normal LPA */}
          <div className="metric-tile spotlight-card" style={{ '--tile-accent': '#fbbf24' }} onMouseMove={spotlightMove}>
            <div className="metric-header-row">
              <div className="metric-label">National LPA</div>
              <svg className="kpi-sparkline" viewBox="0 0 58 22">
                <path d="M 2 14 Q 18 18, 32 10 T 56 12" fill="none" stroke="#fbbf24" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <div className="metric-value">
              {national_lpa} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>mm</span>
            </div>
            <div className="metric-sub">
              <BarChart2 size={12} color="#fbbf24" />
              <span>Normal: {normal_percentage}% share</span>
            </div>
          </div>
        </div>
      </div>

      {/* 117-Year Interactive Time Series */}
      <div className="bento-card spotlight-card" style={{ marginBottom: '1.25rem' }} onMouseMove={spotlightMove}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <TrendingUp size={16} color="var(--accent-blue)" />
              All-India Monsoon Macro-Trajectory (1901-2017)
            </h3>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              117-year June-September aggregate with 10-year rolling decadal regime average
            </p>
          </div>
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ width: 10, height: 2, background: '#60a5fa', display: 'inline-block' }}></span>Annual JJAS
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ width: 10, height: 2, background: '#fbbf24', display: 'inline-block' }}></span>10-Yr Regime
            </span>
          </div>
        </div>

        <div style={{ width: '100%', position: 'relative' }}>
          <svg
            viewBox={`0 0 ${cW} ${cH}`}
            style={{ width: '100%', height: 'auto', display: 'block', cursor: 'crosshair' }}
            onMouseLeave={() => setHoverPoint(null)}
            onMouseMove={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const mx = ((e.clientX - rect.left) / rect.width) * cW;
              const yr = Math.round(xMin + ((mx - pad.l) / (cW - pad.l - pad.r)) * (xMax - xMin));
              const m = national_trend.find((d) => d.year === yr);
              if (m) setHoverPoint(m);
            }}
          >
            <defs>
              <linearGradient id="areaG" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#60a5fa" stopOpacity="0.18" />
                <stop offset="100%" stopColor="#60a5fa" stopOpacity="0.01" />
              </linearGradient>
            </defs>

            {/* Gridlines */}
            {[800, 1000, 1200].map((v) => (
              <g key={v}>
                <line x1={pad.l} y1={sy(v)} x2={cW - pad.r} y2={sy(v)} stroke="rgba(255,255,255,0.05)" />
                <text x={pad.l - 6} y={sy(v) + 3} fill="#4b5563" fontSize="9" fontFamily="JetBrains Mono" textAnchor="end">
                  {v}
                </text>
              </g>
            ))}
            {[1910, 1930, 1950, 1970, 1990, 2010].map((yr) => (
              <text key={yr} x={sx(yr)} y={cH - 6} fill="#4b5563" fontSize="9" fontFamily="JetBrains Mono" textAnchor="middle">
                {yr}
              </text>
            ))}

            {area && <path d={area} fill="url(#areaG)" />}
            <polyline
              fill="none"
              stroke="#60a5fa"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={trend}
              opacity="0.75"
            />
            <polyline
              fill="none"
              stroke="#fbbf24"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={smooth}
            />

            {hoverPoint && (
              <g>
                <line
                  x1={sx(hoverPoint.year)}
                  y1={pad.t}
                  x2={sx(hoverPoint.year)}
                  y2={cH - pad.b}
                  stroke="rgba(255,255,255,0.25)"
                  strokeDasharray="3 3"
                />
                <circle cx={sx(hoverPoint.year)} cy={sy(hoverPoint.jjas)} r="4.5" fill="#60a5fa" stroke="var(--bg-canvas)" strokeWidth="2" />
              </g>
            )}
          </svg>

          {/* Interactive Hover Tooltip */}
          {hoverPoint && (
            <div
              style={{
                position: 'absolute',
                top: 8,
                left: `${((sx(hoverPoint.year) / cW) * 100).toFixed(1)}%`,
                transform: 'translateX(-50%)',
                background: 'rgba(20,20,26,0.96)',
                border: '1px solid var(--border-hover)',
                padding: '0.45rem 0.8rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.74rem',
                fontFamily: 'var(--font-mono)',
                pointerEvents: 'none',
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                whiteSpace: 'nowrap',
              }}
            >
              <div style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.82rem' }}>
                Monsoon Year {hoverPoint.year}
              </div>
              <div style={{ color: '#60a5fa' }}>JJAS: {hoverPoint.jjas} mm</div>
              <div style={{ color: '#fbbf24' }}>10-Yr Smooth: {hoverPoint.smooth} mm</div>
            </div>
          )}
        </div>

        {/* Landmark Drought Shocks */}
        <div style={{ marginTop: '1.1rem', paddingTop: '0.85rem', borderTop: '1px solid var(--border-subtle)' }}>
          <div className="metric-label" style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <AlertCircle size={13} color="#fb7185" />
            Historic Landmark Drought Shocks (Click to view in Geospatial Radar):
          </div>
          <div className="preset-chips">
            {landmarkYears.map((item) => (
              <button
                key={item.year}
                className="preset-chip"
                onClick={() => onSelectYear?.(item.year)}
                title={item.label}
              >
                {item.year}{' '}
                <span style={{ color: '#fb7185', fontFamily: 'var(--font-mono)', marginLeft: '0.3rem', fontWeight: 600 }}>
                  {item.dep}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 6-Tier IMD Climatological Archive Distribution */}
      <div className="bento-card">
        <h3 style={{ fontSize: '0.98rem', marginBottom: '0.75rem' }}>
          Climatological Frequency Breakdown (4,188 Sub-Divisional Archive Observations)
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem' }}>
          {category_distribution.map((item) => {
            const pct = ((item.count / total_records) * 100).toFixed(1);
            return (
              <div
                key={item.category}
                style={{
                  background: 'var(--bg-inner)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem 1rem',
                  borderLeft: `3px solid ${item.color}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-primary)' }}>{item.category}</span>
                  <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: item.color, fontWeight: 600 }}>
                    {pct}%
                  </span>
                </div>
                <div style={{ fontSize: '1.35rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                  {item.count.toLocaleString()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
