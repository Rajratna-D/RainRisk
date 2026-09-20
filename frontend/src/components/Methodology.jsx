import React, { useState, useEffect } from 'react';
import { fetchMethodology } from '../api/client';
import { BookOpen, Shield, Layers, Search } from 'lucide-react';

export default function Methodology() {
  const [data, setData] = useState(null);
  const [filterGroup, setFilterGroup] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchMethodology().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div className="skeleton" style={{ height: '160px' }} />
        <div className="skeleton" style={{ height: '240px' }} />
      </div>
    );
  }

  const { features = [] } = data;
  const groups = ['All', ...new Set(features.map((f) => f.group))];

  const filteredFeatures = features.filter((f) => {
    const matchesGroup = filterGroup === 'All' || f.group === filterGroup;
    const matchesSearch =
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.desc.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesGroup && matchesSearch;
  });

  return (
    <div>
      {/* IMD Operational Classification Standard */}
      <div className="bento-card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.05rem', marginBottom: '0.85rem' }}>IMD Operational Classification Standard</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.1rem' }}>
          Drought risk labels follow the India Meteorological Department's operational standard, evaluating June-September (JJAS) rainfall percentage departure from the 1971-2020 Long Period Average (LPA).
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.85rem' }}>
          {[
            { tier: 'Large Excess', range: '>= +60%', desc: 'Extreme flood / deluge risk', color: '#a78bfa' },
            { tier: 'Excess', range: '+20% to +59%', desc: 'Monsoon surplus', color: '#60a5fa' },
            { tier: 'Normal', range: '-19% to +19%', desc: 'Climatologically optimal', color: '#34d399' },
            { tier: 'Deficient', range: '-59% to -20%', desc: 'Moderate drought risk', color: '#fbbf24' },
            { tier: 'Large Deficient', range: '-99% to -60%', desc: 'Severe drought emergency', color: '#fb7185' },
            { tier: 'No Rainfall', range: '= -100%', desc: 'Complete monsoon failure', color: '#94a3b8' },
          ].map((item) => (
            <div
              key={item.tier}
              style={{
                background: 'var(--bg-inner)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                padding: '0.85rem',
                borderLeft: `3px solid ${item.color}`,
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#f4f4f6', marginBottom: '0.2rem' }}>
                {item.tier}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: item.color, fontWeight: 700 }}>
                {item.range}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                {item.desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Methodological Guardrails Grid */}
      <div className="grid-2">
        <div className="bento-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem' }}>
            <Shield size={16} color="var(--accent-blue)" />
            <h4 style={{ fontSize: '0.95rem' }}>Methodological Integrity Guardrails</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>1. 1971-2020 LPA Baseline:</strong> Fixed climatological baseline computed across the official IMD operational 50-year standard window.
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>2. Calendar-Gap Reindexing:</strong> Lags and rolling aggregates are evaluated after reindexing subdivisions to continuous year grids, preventing silent lookahead bridging.
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>3. SMOTENC Categorical Purity:</strong> Synthetic minority sampling occurs strictly inside training folds on raw features prior to one-hot encoding.
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>4. Expanding-Window CV:</strong> Temporal cross-validation ensures the model is never evaluated on historical past data using future knowledge.
            </div>
          </div>
        </div>

        <div className="bento-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.75rem' }}>
            <Layers size={16} color="var(--accent-teal)" />
            <h4 style={{ fontSize: '0.95rem' }}>Planetary Teleconnections & Ordinal Framework</h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>• Pacific ENSO (Niño 3.4):</strong> Ingests NOAA PSL spring SST anomalies capturing Walker circulation disruptions prior to monsoon onset.
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>• Indian Ocean Dipole (DMI):</strong> Ingests equatorial Indian Ocean SST gradient, identifying positive DMI events that buffer against El Niño drought.
            </div>
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>• True Ordinal Decomposition (Frank & Hall 2001):</strong> Translates multi-class loss into 5 cumulative binary threshold models (P(Y &gt; k)), aligning gradient steps with physical drought severity.
            </div>
          </div>
        </div>
      </div>

      {/* Feature Dictionary */}
      <div className="bento-card" style={{ marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem' }}>Engineered Feature Dictionary (23 Features + 1 Categorical)</h3>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              All features strictly adhere to zero-leakage prior-year (.shift(1)) or pre-monsoon spring time horizons.
            </p>
          </div>

          <div style={{ position: 'relative', width: '240px' }}>
            <input
              type="text"
              placeholder="Search feature identifier..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="custom-select"
              style={{ paddingLeft: '2rem', height: '36px' }}
            />
            <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '11px' }} />
          </div>
        </div>

        <div className="preset-chips">
          {groups.map((grp) => (
            <button
              key={grp}
              className={`preset-chip ${filterGroup === grp ? 'active' : ''}`}
              onClick={() => setFilterGroup(grp)}
            >
              {grp}
            </button>
          ))}
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', textAlign: 'left' }}>
                <th style={{ padding: '0.65rem' }}>Feature Identifier</th>
                <th style={{ padding: '0.65rem' }}>Category Group</th>
                <th style={{ padding: '0.65rem' }}>Climatological Description & Purpose</th>
              </tr>
            </thead>
            <tbody>
              {filteredFeatures.map((f) => (
                <tr key={f.name} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-teal)', fontWeight: 600 }}>
                    {f.name}
                  </td>
                  <td style={{ padding: '0.65rem' }}>
                    <span className="preset-chip" style={{ padding: '0.15rem 0.55rem', fontSize: '0.68rem' }}>
                      {f.group}
                    </span>
                  </td>
                  <td style={{ padding: '0.65rem', color: 'var(--text-secondary)' }}>
                    {f.desc}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
