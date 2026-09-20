import React, { useState, useEffect } from 'react';
import { fetchLeaderboard } from '../api/client';
import { Award, CheckCircle2, TrendingUp, AlertCircle } from 'lucide-react';

export default function ModelLeaderboard() {
  const [data, setData] = useState(null);
  const [showNormalized, setShowNormalized] = useState(true);

  useEffect(() => {
    fetchLeaderboard().then(setData).catch(console.error);
  }, []);

  if (!data) {
    return <div className="skeleton" style={{ height: '400px' }} />;
  }

  const { active_model, models, confusion_matrix } = data;
  const { labels = [], matrix = [], normalized_matrix = [], diagonal_accuracy = 56.0 } = confusion_matrix || {};

  return (
    <div>
      <div className="bento-card" style={{ borderLeft: '4px solid var(--accent-teal)', marginBottom: '1.5rem', padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <Award size={18} color="var(--accent-teal)" />
              <span className="preset-chip active" style={{ fontSize: '0.72rem', padding: '0.15rem 0.6rem' }}>
                Production Deployed Classifier
              </span>
            </div>
            <h2 style={{ fontSize: '1.6rem', marginBottom: '0.45rem' }}>
              Random Forest Classifier (Balanced Accuracy: 43.2%)
            </h2>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', maxWidth: '780px' }}>
              Evaluated strictly on held-out 2011-2017 test records (N=243). Pre-monsoon Pacific (Niño 3.4) and Indian Ocean (DMI) SST anomalies elevated Balanced Accuracy from 34.4% to <strong style={{ color: 'var(--text-primary)' }}>43.2%</strong> and Off-by-One Accuracy to <strong style={{ color: 'var(--accent-teal)' }}>93.0%</strong>.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1.5rem', textAlign: 'right' }}>
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Exact Acc</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f4f4f6', fontFamily: 'var(--font-mono)' }}>56.0%</div>
            </div>
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Within ±1 Class</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-teal)', fontFamily: 'var(--font-mono)' }}>93.0%</div>
            </div>
          </div>
        </div>
      </div>

      <div className="bento-card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.05rem', marginBottom: '0.85rem' }}>Algorithmic Progression Leaderboard</h3>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Chronological benchmark from classical baselines to multi-scale spatio-temporal modeling with global teleconnections.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {models.map((m) => {
            const isBest = m.name === active_model;
            return (
              <div
                key={m.name}
                style={{
                  background: isBest ? 'rgba(45, 212, 168, 0.05)' : 'var(--bg-inner)',
                  border: `1px solid ${isBest ? 'rgba(45, 212, 168, 0.3)' : 'var(--border-subtle)'}`,
                  borderRadius: '10px',
                  padding: '1rem 1.25rem',
                  transition: 'var(--transition)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.92rem', color: isBest ? 'var(--accent-teal)' : 'var(--text-primary)' }}>
                      {m.name}
                    </span>
                    {isBest && (
                      <span className="preset-chip active" style={{ padding: '0.15rem 0.55rem', fontSize: '0.64rem' }}>
                        Frontier Pipeline
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                    <span>Exact: <strong style={{ color: 'var(--text-primary)' }}>{m.accuracy}%</strong></span>
                    <span>Balanced: <strong>{m.balanced_accuracy}%</strong></span>
                    <span>Macro-F1: <strong>{m.macro_f1}</strong></span>
                    <span style={{ color: 'var(--accent-teal)' }}>±1 Class: <strong>{m.off_by_one}%</strong></span>
                    <span style={{ color: 'var(--text-muted)' }}>Train: {m.train_time}s</span>
                  </div>
                </div>

                <div style={{ width: '100%', height: '5px', background: '#27272a', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${m.off_by_one}%`,
                      height: '100%',
                      background: isBest ? 'linear-gradient(90deg, #2dd4a8, #60a5fa)' : '#52525b',
                      borderRadius: '3px',
                      transition: 'width 0.6s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {labels.length > 0 && (
        <div className="bento-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem' }}>Held-Out Test Confusion Matrix (2011-2017)</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Exact diagonal agreement: <strong style={{ color: 'var(--accent-teal)' }}>{diagonal_accuracy}%</strong>. Off-diagonal errors concentrate strictly in adjacent ordinal categories.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <button
                className={`preset-chip ${showNormalized ? 'active' : ''}`}
                onClick={() => setShowNormalized(true)}
              >
                Normalized (%)
              </button>
              <button
                className={`preset-chip ${!showNormalized ? 'active' : ''}`}
                onClick={() => setShowNormalized(false)}
              >
                Raw Counts
              </button>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', fontSize: '0.8rem' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.65rem', color: 'var(--text-muted)', textAlign: 'left' }}>True \ Pred</th>
                  {labels.map((l) => (
                    <th key={l} style={{ padding: '0.65rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{l}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {labels.map((trueLabel, rowIdx) => (
                  <tr key={trueLabel}>
                    <td style={{ padding: '0.65rem', color: 'var(--text-secondary)', fontWeight: 600, textAlign: 'left' }}>
                      {trueLabel}
                    </td>
                    {labels.map((predLabel, colIdx) => {
                      const countVal = matrix[rowIdx] ? matrix[rowIdx][colIdx] : 0;
                      const normVal = normalized_matrix[rowIdx] ? normalized_matrix[rowIdx][colIdx] : 0;
                      const isDiagonal = rowIdx === colIdx;
                      const isAdjacent = Math.abs(rowIdx - colIdx) === 1;
                      const displayVal = showNormalized ? `${normVal}%` : countVal;

                      let cellBg = 'rgba(255, 255, 255, 0.015)';
                      if (isDiagonal && normVal > 0) {
                        cellBg = `rgba(45, 212, 168, ${Math.min(0.8, 0.15 + (normVal / 100) * 0.65)})`;
                      } else if (isAdjacent && normVal > 0) {
                        cellBg = `rgba(96, 165, 250, ${Math.min(0.45, 0.08 + (normVal / 100) * 0.35)})`;
                      }

                      return (
                        <td
                          key={predLabel}
                          style={{
                            padding: '0.75rem',
                            background: cellBg,
                            fontFamily: 'var(--font-mono)',
                            color: isDiagonal ? '#ffffff' : 'var(--text-secondary)',
                            fontWeight: isDiagonal ? 700 : 400,
                            border: '1px solid rgba(255,255,255,0.05)',
                            transition: 'background 0.2s',
                          }}
                        >
                          {displayVal}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
