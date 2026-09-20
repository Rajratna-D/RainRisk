import React, { useState, useEffect, useRef } from 'react';
import { Layers, CheckCircle2, ShieldCheck, BarChart2, TrendingUp, AlertCircle } from 'lucide-react';

/* ── Animated Counter Hook ── */
function useAnimatedCounter(target, duration = 1200, decimals = 0) {
  const [value, setValue] = useState(0);
  const frameRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    if (target == null) return;
    const numTarget = parseFloat(target);
    if (isNaN(numTarget)) return;

    startRef.current = performance.now();

    const animate = (now) => {
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(eased * numTarget);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      } else {
        setValue(numTarget);
      }
    };

    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [target, duration]);

  if (decimals > 0) return value.toFixed(decimals);
  return Math.round(value);
}

/* ── Spotlight Mouse Tracker ── */
function useSpotlight() {
  return (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty('--mouse-x', `${e.clientX - r.left}px`);
    e.currentTarget.style.setProperty('--mouse-y', `${e.clientY - r.top}px`);
  };
}

/* ── Landmark Drought Years ── */
const LANDMARK_YEARS = [
  { year: 1918, dep: '-23.8%', label: 'Spanish Flu Era Failure' },
  { year: 1965, dep: '-18.2%', label: 'Green Revolution Catalyst' },
  { year: 1972, dep: '-23.9%', label: 'Great Asian Drought' },
  { year: 1987, dep: '-19.4%', label: 'Severe El Niño Drought' },
  { year: 2002, dep: '-19.2%', label: 'Early Season Shock' },
  { year: 2009, dep: '-21.8%', label: 'Modern Monsoon Deficit' },
  { year: 2015, dep: '-14.3%', label: 'Consecutive Year Deficit' },
];

export default function ExecutivePulse({ overviewData, onSelectYear }) {
  const [hoverPoint, setHoverPoint] = useState(null);
  const spotlightMove = useSpotlight();

  /* Animated hero counters */
  const animOBO   = useAnimatedCounter(overviewData?.off_by_one_accuracy, 1400, 1);
  const animExact = useAnimatedCounter(overviewData?.exact_accuracy, 1200, 1);
  const animRecs  = useAnimatedCounter(overviewData?.total_records, 1000, 0);
  const animLPA   = useAnimatedCounter(overviewData?.national_lpa, 1100, 0);

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
    category_distribution,
    national_trend = [],
  } = overviewData;

  /* SVG time-series chart dimensions */
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

  return (
    <div>
      {/* Hero Metric Deck */}
      <div className="hero-metric-deck">
        {/* Primary Hero Card */}
        <div className="hero-primary-card spotlight-card" onMouseMove={spotlightMove}>
          <div>
            <div className="hero-tag">
              <ShieldCheck size={16} color="var(--accent-teal)" />
              <span className="hero-tag-label">Primary Production Telemetry</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.6rem' }}>
              <span className="hero-number counter-animated">{animOBO}%</span>
              <span className="hero-unit">Within ±1 Class</span>
            </div>
            <p className="hero-description">
              Under 6-tier ordinal risk classification, 93.0% of predictions match reality or lie within an immediately adjacent category.
            </p>
          </div>

          <div className="hero-footer">
            <span className="hero-footer-mono">HELD-OUT TEST 2011-2017 (N=243)</span>
            <span style={{ fontSize: '0.68rem', color: 'var(--accent-teal)', fontWeight: 600 }}>
              Zero Temporal Leakage
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
            <div className="metric-value counter-animated">{animExact}%</div>
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
            <div className="metric-value counter-animated">{animRecs.toLocaleString()}</div>
            <div className="metric-sub">
              <Layers size={12} color="#a78bfa" />
              <span>36 units - 1901-2017</span>
            </div>
          </div>

          {/* National LPA */}
          <div className="metric-tile spotlight-card" style={{ '--tile-accent': '#fbbf24' }} onMouseMove={spotlightMove}>
            <div className="metric-header-row">
              <div className="metric-label">National LPA</div>
              <svg className="kpi-sparkline" viewBox="0 0 58 22">
                <path d="M 2 14 Q 18 18, 32 10 T 56 12" fill="none" stroke="#fbbf24" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <div className="metric-value">
              <span className="counter-animated">{animLPA}</span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}> mm</span>
            </div>
            <div className="metric-sub">
              <BarChart2 size={12} color="#fbbf24" />
              <span>Normal: {normal_percentage}% share</span>
            </div>
          </div>
        </div>
      </div>

      {/* 117-Year Time Series */}
      <div className="bento-card spotlight-card" style={{ marginBottom: '1.25rem' }} onMouseMove={spotlightMove}>
        <div className="section-header">
          <div>
            <h3 className="section-title">
              <TrendingUp size={16} color="var(--accent-blue)" />
              All-India Monsoon Macro-Trajectory (1901-2017)
            </h3>
            <p className="section-subtitle">
              117-year June-September aggregate with 10-year rolling decadal regime average
            </p>
          </div>
          <div className="chart-legend">
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span className="chart-legend-swatch" style={{ background: '#60a5fa' }}></span>Annual JJAS
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span className="chart-legend-swatch" style={{ background: '#fbbf24' }}></span>10-Yr Regime
            </span>
          </div>
        </div>

        <div className="chart-wrapper">
          <svg
            viewBox={`0 0 ${cW} ${cH}`}
            className="chart-svg"
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
                <line x1={pad.l} y1={sy(v)} x2={cW - pad.r} y2={sy(v)} stroke="var(--chart-gridline)" />
                <text x={pad.l - 6} y={sy(v) + 3} fill="var(--chart-label)" fontSize="9" fontFamily="JetBrains Mono" textAnchor="end">
                  {v}
                </text>
              </g>
            ))}
            {[1910, 1930, 1950, 1970, 1990, 2010].map((yr) => (
              <text key={yr} x={sx(yr)} y={cH - 6} fill="var(--chart-label)" fontSize="9" fontFamily="JetBrains Mono" textAnchor="middle">
                {yr}
              </text>
            ))}

            {area && <path d={area} fill="url(#areaG)" />}
            <polyline
              fill="none" stroke="#60a5fa" strokeWidth="1.4"
              strokeLinecap="round" strokeLinejoin="round"
              points={trend} opacity="0.75"
            />
            <polyline
              fill="none" stroke="#fbbf24" strokeWidth="2.2"
              strokeLinecap="round" strokeLinejoin="round"
              points={smooth}
            />

            {hoverPoint && (
              <g>
                <line
                  x1={sx(hoverPoint.year)} y1={pad.t}
                  x2={sx(hoverPoint.year)} y2={cH - pad.b}
                  stroke="rgba(255,255,255,0.25)" strokeDasharray="3 3"
                />
                <circle cx={sx(hoverPoint.year)} cy={sy(hoverPoint.jjas)} r="4.5" fill="#60a5fa" stroke="var(--bg-canvas)" strokeWidth="2" />
              </g>
            )}
          </svg>

          {/* Hover Tooltip */}
          {hoverPoint && (
            <div className="chart-tooltip" style={{ left: `${((sx(hoverPoint.year) / cW) * 100).toFixed(1)}%` }}>
              <div className="chart-tooltip-title">Monsoon Year {hoverPoint.year}</div>
              <div style={{ color: '#60a5fa' }}>JJAS: {hoverPoint.jjas} mm</div>
              <div style={{ color: '#fbbf24' }}>10-Yr Smooth: {hoverPoint.smooth} mm</div>
            </div>
          )}
        </div>

        {/* Landmark Drought Shocks */}
        <div className="landmark-section">
          <div className="metric-label" style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <AlertCircle size={13} color="var(--accent-rose)" />
            Historic Landmark Drought Shocks (Click to view in Geospatial Radar):
          </div>
          <div className="preset-chips">
            {LANDMARK_YEARS.map((item) => (
              <button
                key={item.year}
                className="preset-chip"
                onClick={() => onSelectYear?.(item.year)}
                title={item.label}
              >
                {item.year}
                <span className="landmark-chip-departure">{item.dep}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 6-Tier IMD Distribution with Hover Glow */}
      <div className="bento-card">
        <h3 style={{ fontSize: '0.98rem', marginBottom: '0.75rem' }}>
          Climatological Frequency Breakdown (4,188 Sub-Divisional Archive Observations)
        </h3>
        <div className="category-grid">
          {category_distribution.map((item) => {
            const pct = ((item.count / total_records) * 100).toFixed(1);
            return (
              <div
                key={item.category}
                className="category-card"
                style={{
                  borderLeftColor: item.color,
                  '--glow-color': `${item.color}22`,
                }}
              >
                <div className="category-card-header">
                  <span className="category-card-name">{item.category}</span>
                  <span className="category-card-pct" style={{ color: item.color }}>{pct}%</span>
                </div>
                <div className="category-card-count">{item.count.toLocaleString()}</div>
                <div className="category-bar">
                  <div className="category-bar-fill" style={{ width: `${pct}%`, background: item.color }}></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
