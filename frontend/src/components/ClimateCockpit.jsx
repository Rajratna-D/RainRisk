import React, { useState, useEffect, useCallback } from 'react';
import { runPrediction, fetchSubdivisions } from '../api/client';
import { Sliders, Zap, ShieldAlert, Waves, CloudRain } from 'lucide-react';

const CATEGORY_SHORT = {
  'No Rainfall': 'No Rain',
  'Large Deficient': 'Sev. Deficit',
  'Deficient': 'Deficit',
  'Normal': 'Normal',
  'Excess': 'Surplus',
  'Large Excess': 'Extreme Flood',
};

const PRESETS = [
  { key: 'baseline', label: 'Historical Neutral Baseline' },
  { key: 'elnino', label: 'Severe El Niño Drought (+1.8°C Pacific)' },
  { key: 'buffered', label: 'Buffered El Niño (+1.5°C Pacific, +0.7 IOD)' },
  { key: 'lanina', label: 'La Niña Monsoon Surge (-1.2°C Cooling)' },
  { key: 'deficit', label: 'Severe Precipitation Deficit (-30% JJAS)' },
];

export default function ClimateCockpit() {
  const [subdivisions, setSubdivisions] = useState([]);
  const [selectedSub, setSelectedSub] = useState('Kerala');

  const [prevJJAS, setPrevJJAS] = useState(1500);
  const [prevChange, setPrevChange] = useState(0);
  const [rolling3, setRolling3] = useState(1500);
  const [rolling5, setRolling5] = useState(1500);
  const [cv5, setCv5] = useState(20);
  const [ensoMam, setEnsoMam] = useState(0.0);
  const [ensoDjf, setEnsoDjf] = useState(0.0);
  const [iodMam, setIodMam] = useState(0.0);

  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activePreset, setActivePreset] = useState('baseline');

  useEffect(() => {
    fetchSubdivisions().then((list) => {
      setSubdivisions(list);
      if (list.length > 0) {
        const defaultSub = list.find((s) => s.name === 'Kerala') || list[0];
        setPrevJJAS(defaultSub.lpa);
        setRolling3(defaultSub.lpa);
        setRolling5(defaultSub.lpa);
        setCv5(defaultSub.cv);
      }
    });
  }, []);

  const handlePredict = useCallback(async () => {
    setLoading(true);
    try {
      const payload = {
        subdivision: selectedSub,
        prev_jjas: prevJJAS,
        prev_change: prevChange,
        rolling_3yr: rolling3,
        rolling_5yr: rolling5,
        cv_5yr: cv5,
        prev_jun: Math.round(prevJJAS * 0.22),
        prev_jul: Math.round(prevJJAS * 0.32),
        prev_aug: Math.round(prevJJAS * 0.28),
        prev_sep: Math.round(prevJJAS * 0.18),
        prev_jf: 30.0,
        prev_mam: 120.0,
        prev_ond: 150.0,
        enso_djf: ensoDjf,
        enso_mam: ensoMam,
        iod_mam: iodMam,
      };
      const result = await runPrediction(payload);
      setPrediction(result);
    } catch (err) {
      console.error('Prediction failed:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedSub, prevJJAS, prevChange, rolling3, rolling5, cv5, ensoMam, ensoDjf, iodMam]);

  useEffect(() => {
    handlePredict();
  }, [handlePredict]);

  const applyPreset = (presetKey) => {
    setActivePreset(presetKey);
    const subObj = subdivisions.find((s) => s.name === selectedSub);
    const baseLpa = subObj ? subObj.lpa : 1500;

    if (presetKey === 'elnino') {
      setEnsoMam(1.8); setEnsoDjf(1.2); setIodMam(0.0);
      setPrevJJAS(Math.round(baseLpa * 0.72)); setPrevChange(-350); setCv5(35);
    } else if (presetKey === 'buffered') {
      setEnsoMam(1.5); setEnsoDjf(1.0); setIodMam(0.75);
      setPrevJJAS(Math.round(baseLpa * 0.95)); setPrevChange(-50); setCv5(22);
    } else if (presetKey === 'lanina') {
      setEnsoMam(-1.2); setEnsoDjf(-0.9); setIodMam(0.1);
      setPrevJJAS(Math.round(baseLpa * 1.30)); setPrevChange(300); setCv5(16);
    } else if (presetKey === 'deficit') {
      setEnsoMam(1.4); setEnsoDjf(0.8); setIodMam(-0.2);
      setPrevJJAS(Math.round(baseLpa * 0.70)); setPrevChange(-400); setCv5(38);
    } else {
      setEnsoMam(0.0); setEnsoDjf(0.0); setIodMam(0.0);
      setPrevJJAS(baseLpa); setPrevChange(0);
      setCv5(subObj ? subObj.cv : 20);
    }
  };

  const radius = 68;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75;
  const droughtPct = prediction ? Math.min(100, Math.max(0, prediction.composite_drought_risk)) : 0;
  const arcOffset = arcLength - (droughtPct / 100) * arcLength;

  let arcColor = 'var(--accent-emerald)';
  if (droughtPct > 45) arcColor = 'var(--accent-red)';
  else if (droughtPct > 25) arcColor = 'var(--accent-amber)';

  let atmosphereBg = 'var(--bg-card)';
  if (ensoMam > 0.6) {
    atmosphereBg = 'linear-gradient(135deg, var(--hero-gradient-from) 0%, rgba(251, 191, 36, 0.06) 100%)';
  } else if (ensoMam < -0.6) {
    atmosphereBg = 'linear-gradient(135deg, var(--hero-gradient-from) 0%, rgba(96, 165, 250, 0.06) 100%)';
  }

  return (
    <div>
      <div className="bento-card" style={{ marginBottom: '1.25rem', padding: '1.1rem' }}>
        <div className="metric-label" style={{ marginBottom: '0.6rem' }}>
          Physical Climate Scenario Presets
        </div>
        <div className="preset-chips" style={{ marginBottom: 0 }}>
          {PRESETS.map((p) => (
            <button
              key={p.key}
              className={`preset-chip ${activePreset === p.key ? 'active' : ''}`}
              onClick={() => applyPreset(p.key)}
            >
              <Zap size={13} />
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid-split" style={{ alignItems: 'start' }}>
        <div className="bento-card" style={{ background: atmosphereBg, transition: 'background 0.4s ease' }}>
          <h3 className="section-title" style={{ marginBottom: '1.25rem' }}>
            <Sliders size={18} color="var(--accent-cyan)" />
            Meteorological & Ocean Teleconnection Inputs
          </h3>

          <div style={{ marginBottom: '1.25rem' }}>
            <label className="metric-label" style={{ marginBottom: '0.35rem', display: 'block' }}>
              Target Meteorological Subdivision
            </label>
            <select
              value={selectedSub}
              onChange={(e) => {
                setSelectedSub(e.target.value);
                const match = subdivisions.find((s) => s.name === e.target.value);
                if (match) {
                  setPrevJJAS(match.lpa); setRolling3(match.lpa); setRolling5(match.lpa); setCv5(match.cv);
                }
              }}
              className="custom-select"
            >
              {subdivisions.map((s) => (
                <option key={s.name} value={s.name}>{s.name} (LPA: {s.lpa} mm)</option>
              ))}
            </select>
          </div>

          <div className="cockpit-section" style={{ marginBottom: '1.25rem' }}>
            <div className="cockpit-section-label" style={{ color: 'var(--accent-sky)' }}>
              <Waves size={14} />
              Planetary Teleconnections (ENSO & IOD)
            </div>

            <div className="slider-group">
              <div className="slider-header">
                <span className="slider-label">Niño 3.4 Spring SST Anomaly</span>
                <span className="slider-value">{ensoMam > 0 ? `+${ensoMam}` : ensoMam}°C</span>
              </div>
              <input type="range" min="-3.0" max="3.0" step="0.1" value={ensoMam}
                onChange={(e) => setEnsoMam(parseFloat(e.target.value))} className="custom-range" />
              <span className="slider-hint">Values &gt; +0.5°C indicate El Niño drought forcing</span>
            </div>

            <div className="slider-group" style={{ marginBottom: 0 }}>
              <div className="slider-header">
                <span className="slider-label">Indian Ocean Dipole (DMI) Spring Anomaly</span>
                <span className="slider-value">{iodMam > 0 ? `+${iodMam}` : iodMam}</span>
              </div>
              <input type="range" min="-1.5" max="1.5" step="0.05" value={iodMam}
                onChange={(e) => setIodMam(parseFloat(e.target.value))} className="custom-range" />
              <span className="slider-hint">Positive DMI buffers against Pacific drought forcing</span>
            </div>
          </div>

          <div className="cockpit-section">
            <div className="cockpit-section-label" style={{ color: 'var(--accent-emerald)' }}>
              <CloudRain size={14} />
              Regional Precipitation Memory
            </div>

            <div className="slider-group">
              <div className="slider-header">
                <span className="slider-label">Prior-Year Monsoon JJAS Rainfall</span>
                <span className="slider-value">{prevJJAS} mm</span>
              </div>
              <input type="range" min="200" max="4000" step="10" value={prevJJAS}
                onChange={(e) => setPrevJJAS(parseInt(e.target.value))} className="custom-range" />
            </div>

            <div className="slider-group">
              <div className="slider-header">
                <span className="slider-label">Year-over-Year Momentum Delta</span>
                <span className="slider-value">{prevChange > 0 ? `+${prevChange}` : prevChange} mm</span>
              </div>
              <input type="range" min="-1000" max="1000" step="10" value={prevChange}
                onChange={(e) => setPrevChange(parseInt(e.target.value))} className="custom-range" />
            </div>

            <div className="slider-group" style={{ marginBottom: 0 }}>
              <div className="slider-header">
                <span className="slider-label">5-Year Volatility (CV%)</span>
                <span className="slider-value">{cv5}%</span>
              </div>
              <input type="range" min="5" max="60" step="1" value={cv5}
                onChange={(e) => setCv5(parseInt(e.target.value))} className="custom-range" />
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {prediction && (
            <div className="bento-card" style={{ borderLeft: `4px solid ${prediction.color}`, padding: '1.5rem' }}>
              <div className="metric-label">Predicted Anomaly Tier</div>
              <div style={{
                fontSize: '2.3rem', fontWeight: 800, color: prediction.color,
                fontFamily: 'var(--font-display)', letterSpacing: '-0.02em', margin: '0.2rem 0',
              }}>
                {prediction.predicted_category}
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Evaluated by Random Forest (23 Features + Teleconnections)
              </p>

              <div className="radial-dial-wrapper">
                <svg className="radial-dial-svg" viewBox="0 0 180 180">
                  <g transform="rotate(135 90 90)">
                    <circle cx="90" cy="90" r={radius} className="radial-track" strokeDasharray={`${arcLength} ${circumference}`} />
                    <circle cx="90" cy="90" r={radius} className="radial-fill" stroke={arcColor}
                      strokeDasharray={`${arcLength} ${circumference}`} strokeDashoffset={arcOffset} />
                  </g>
                </svg>
                <div className="radial-center-text">
                  <div className="radial-pct" style={{ color: arcColor }}>{prediction.composite_drought_risk}%</div>
                  <div className="radial-label">Composite Drought Risk</div>
                </div>
              </div>

              <div className="prob-spectrum">
                {prediction.probabilities.map((item) => (
                  <div key={item.category} className="prob-segment"
                    style={{ width: `${item.probability}%`, background: item.color }}
                    title={`${item.category}: ${item.probability}%`} />
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.71rem', fontFamily: 'var(--font-mono)', marginTop: '0.45rem' }}>
                {prediction.probabilities.map((p) => (
                  <div key={p.category} style={{ color: p.color, fontWeight: p.probability > 20 ? 700 : 400 }}>
                    {CATEGORY_SHORT[p.category] || p.category}: {p.probability}%
                  </div>
                ))}
              </div>
            </div>
          )}

          {prediction && (
            <div className="bento-card" style={{ borderLeft: `3px solid ${prediction.advisory.color}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.6rem' }}>
                <ShieldAlert size={16} color={prediction.advisory.color} />
                <h4 style={{ fontSize: '0.95rem', color: prediction.advisory.color, fontWeight: 700 }}>
                  {prediction.advisory.title}
                </h4>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem', fontSize: '0.81rem', color: 'var(--text-secondary)' }}>
                {prediction.advisory.actions.map((act, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                    <span style={{ color: prediction.advisory.color, fontWeight: 'bold' }}>•</span>
                    <span>{act}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
