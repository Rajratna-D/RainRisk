import React, { useState, useEffect, useRef } from 'react';
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
  const [theme, setTheme] = useState(() => localStorage.getItem('rainrisk-theme') || 'dark');
  const pageRef = useRef(null);

  /* Apply theme to DOM */
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('rainrisk-theme', theme);
  }, [theme]);

  /* Fetch overview data on mount */
  useEffect(() => {
    fetchOverview()
      .then(setOverviewData)
      .catch((err) => console.error('Failed fetching overview:', err));
  }, []);

  /* Trigger page-enter animation on tab change */
  useEffect(() => {
    const el = pageRef.current;
    if (!el) return;
    el.classList.remove('page-enter');
    // Force reflow to restart animation
    void el.offsetWidth;
    el.classList.add('page-enter');
  }, [activeTab]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

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
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <main ref={pageRef} className="page-enter">
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

      <footer className="app-footer">
        <div>
          <span className="app-footer-brand">RainRisk</span> &middot; Production Climate Risk Intelligence Platform
        </div>
      </footer>
    </div>
  );
}
