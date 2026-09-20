import React, { useState, useEffect } from 'react';
import { fetchSubdivisions, fetchSubdivisionDetail } from '../api/client';
import { GitCompare, Calendar, BarChart2 } from 'lucide-react';

export default function RegionalExplorer({ selectedSub = 'Kerala' }) {
  const [subdivisions, setSubdivisions] = useState([]);
  const [focusSub, setFocusSub] = useState(selectedSub);
  const [twinSub, setTwinSub] = useState('West Rajasthan');
  const [focusData, setFocusData] = useState(null);
  const [twinData, setTwinData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubdivisions().then((list) => {
      setSubdivisions(list);
    });
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

  return (
    <div>
      {/* Top Selectors Bar */}
      <div className="bento-card" style={{ marginBottom: '1.25rem', padding: '1.2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          <div>
            <label style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem', display: 'block' }}>
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
            <label style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem', display: 'block' }}>
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

      {/* Climate Twins Benchmark Cards */}
      <div className="grid-2">
        {focusData && (
          <div className="bento-card" style={{ borderTop: '3px solid #38bdf8' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.15rem' }}>{focusData.metadata.name}</h3>
              <span className="preset-chip active">{focusData.metadata.macro_region}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', textAlign: 'center' }}>
              <div style={{ background: 'rgba(8,12,20,0.6)', padding: '0.65rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>LPA Baseline</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {focusData.metadata.lpa} mm
                </div>
              </div>
              <div style={{ background: 'rgba(8,12,20,0.6)', padding: '0.65rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Mean JJAS</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {focusData.metadata.mean_jjas} mm
                </div>
              </div>
              <div style={{ background: 'rgba(8,12,20,0.6)', padding: '0.65rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Volatility</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                  {focusData.metadata.cv}%
                </div>
              </div>
              <div style={{ background: 'rgba(8,12,20,0.6)', padding: '0.65rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Drought Rate</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f43f5e', fontFamily: 'var(--font-mono)' }}>
                  {focusData.metadata.drought_frequency}%
                </div>
              </div>
            </div>
          </div>
        )}

        {twinData && (
          <div className="bento-card" style={{ borderTop: '3px solid #f59e0b' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.15rem' }}>{twinData.metadata.name}</h3>
              <span className="preset-chip">{twinData.metadata.macro_region}</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', textAlign: 'center' }}>
              <div style={{ background: 'rgba(8,12,20,0.6)', padding: '0.65rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>LPA Baseline</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {twinData.metadata.lpa} mm
                </div>
              </div>
              <div style={{ background: 'rgba(8,12,20,0.6)', padding: '0.65rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Mean JJAS</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                  {twinData.metadata.mean_jjas} mm
                </div>
              </div>
              <div style={{ background: 'rgba(8,12,20,0.6)', padding: '0.65rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Volatility</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                  {twinData.metadata.cv}%
                </div>
              </div>
              <div style={{ background: 'rgba(8,12,20,0.6)', padding: '0.65rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Drought Rate</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f43f5e', fontFamily: 'var(--font-mono)' }}>
                  {twinData.metadata.drought_frequency}%
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Historical Annual Timeline Bar Chart */}
      {focusData && (
        <div className="bento-card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem' }}>{focusData.metadata.name} Historical Monsoon Series (1901-2017)</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Annual JJAS rainfall records colored by IMD drought severity tier relative to LPA ({focusData.metadata.lpa} mm).
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
              <span style={{ color: '#f43f5e' }}>■ Large Deficit</span>
              <span style={{ color: '#f59e0b' }}>■ Deficit</span>
              <span style={{ color: '#10b981' }}>■ Normal</span>
              <span style={{ color: '#06b6d4' }}>■ Surplus</span>
            </div>
          </div>

          <div style={{ height: '180px', display: 'flex', alignItems: 'flex-end', gap: '2px', paddingBottom: '10px' }}>
            {focusData.timeline.map((d) => {
              const maxVal = Math.max(...focusData.timeline.map((x) => x.jjas), 1);
              const heightPct = Math.max(8, (d.jjas / maxVal) * 100);
              return (
                <div
                  key={d.year}
                  title={`${d.year}: ${d.jjas} mm (${d.category}, ${d.departure}%)`}
                  style={{
                    flex: 1,
                    height: `${heightPct}%`,
                    background: d.color,
                    borderRadius: '2px 2px 0 0',
                    transition: 'opacity 0.2s',
                    cursor: 'pointer',
                  }}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Monthly Progression & Decadal Regimes Grid */}
      {focusData && (
        <div className="grid-split">
          {/* Monthly Climatology */}
          <div className="bento-card">
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>12-Month Mean Precipitation Distribution</h4>
            <div style={{ display: 'flex', alignItems: 'flex-end', height: '140px', gap: '6px' }}>
              {focusData.monthly.map((m) => {
                const maxM = Math.max(...focusData.monthly.map((x) => x.rainfall), 1);
                const barH = Math.max(4, (m.rainfall / maxM) * 120);
                const isMonsoon = ['JUN', 'JUL', 'AUG', 'SEP'].includes(m.month);
                return (
                  <div key={m.month} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: '100%' }}>
                    <span style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '3px' }}>
                      {m.rainfall > 0 ? Math.round(m.rainfall) : ''}
                    </span>
                    <div
                      style={{
                        width: '100%',
                        height: `${barH}px`,
                        background: isMonsoon
                          ? 'linear-gradient(to top, #2dd4a8, #60a5fa)'
                          : 'rgba(255,255,255,0.08)',
                        borderRadius: '3px 3px 0 0',
                        transition: 'height 0.3s ease',
                      }}
                      title={`${m.month}: ${m.rainfall} mm`}
                    />
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', marginTop: '4px', color: isMonsoon ? 'var(--text-primary)' : 'var(--text-muted)', fontWeight: isMonsoon ? 600 : 400 }}>
                      {m.month}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Decadal Epochs */}
          <div className="bento-card">
            <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>Decadal Regime Shift Matrix</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              {focusData.epochs.map((ep) => (
                <div
                  key={ep.epoch}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'var(--bg-inner)',
                    padding: '0.5rem 0.85rem',
                    borderRadius: '8px',
                  }}
                >
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f8fafc' }}>{ep.epoch}</span>
                  <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}>
                    <span>Mean: <strong style={{ color: '#cbd5e1' }}>{ep.mean} mm</strong></span>
                    <span>CV: <strong style={{ color: '#38bdf8' }}>{ep.cv}%</strong></span>
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
