import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ExecutivePulse from './components/ExecutivePulse';
import GeospatialRadar from './components/GeospatialRadar';
import RegionalExplorer from './components/RegionalExplorer';
import ModelLeaderboard from './components/ModelLeaderboard';
import ClimateCockpit from './components/ClimateCockpit';
import Methodology from './components/Methodology';
import { fetchOverview } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('pulse');
  const [overviewData, setOverviewData] = useState(null);
  const [activeYear, setActiveYear] = useState(2015);
  const [activeSubdivision, setActiveSubdivision] = useState('Kerala');

  useEffect(() => {
    fetchOverview()
      .then(setOverviewData)
      .catch((err) => console.error('Failed fetching overview:', err));
  }, []);

  const handleSelectYear = (yr) => {
    setActiveYear(yr);
    setActiveTab('radar');
  };

  const handleSelectSubdivision = (subName) => {
    setActiveSubdivision(subName);
    setActiveTab('explorer');
  };

  return (
    <div className="app-container">
      {/* Luxury Navbar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Tab Panels */}
      <main>
        {activeTab === 'pulse' && (
          <ExecutivePulse overviewData={overviewData} onSelectYear={handleSelectYear} />
        )}
        {activeTab === 'radar' && (
          <GeospatialRadar initialYear={activeYear} onSelectSubdivision={handleSelectSubdivision} />
        )}
        {activeTab === 'explorer' && (
          <RegionalExplorer selectedSub={activeSubdivision} />
        )}
        {activeTab === 'leaderboard' && (
          <ModelLeaderboard />
        )}
        {activeTab === 'cockpit' && (
          <ClimateCockpit />
        )}
        {activeTab === 'methodology' && (
          <Methodology />
        )}
      </main>

      {/* Executive Footer */}
      <footer style={{ marginTop: '3.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
        <div>
          <span style={{ color: '#f8fafc', fontWeight: 600 }}>RainRisk</span> · Production Climate Risk Intelligence Platform
        </div>
        <div className="mono">
          IMD SUBDIVISION SERIES 1901-2017 · ZERO LOOKAHEAD LEAKAGE · FASTAPI + REACT
        </div>
      </footer>
    </div>
  );
}
