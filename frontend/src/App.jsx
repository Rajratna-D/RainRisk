import React, { useState, useEffect, useRef } from 'react';
import LandingPage from './components/LandingPage';
import Navbar from './components/Navbar';
import ExecutivePulse from './components/ExecutivePulse';
import GeospatialRadar from './components/GeospatialRadar';
import RegionalExplorer from './components/RegionalExplorer';
import ModelLeaderboard from './components/ModelLeaderboard';
import ClimateCockpit from './components/ClimateCockpit';
import Methodology from './components/Methodology';
import { fetchOverview } from './api/client';

export default function App() {
  const [viewMode, setViewMode] = useState('landing'); // 'landing' | 'dashboard'
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [activeTab, setActiveTab] = useState('pulse');
  const [overviewData, setOverviewData] = useState(null);
  const [activeYear, setActiveYear] = useState(2015);
  const [activeSubdivision, setActiveSubdivision] = useState('Kerala');
  const pageRef = useRef(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
  }, []);

  useEffect(() => {
    fetchOverview()
      .then(setOverviewData)
      .catch((err) => console.error('Failed fetching overview:', err));
  }, []);

  useEffect(() => {
    const el = pageRef.current;
    if (!el) return;
    el.classList.remove('page-enter');
    void el.offsetWidth;
    el.classList.add('page-enter');
  }, [activeTab]);

  const handleLaunchDashboard = () => {
    if (isTransitioning) return;
    setIsTransitioning(true);

    setTimeout(() => {
      setViewMode('dashboard');
      window.scrollTo(0, 0);
      setIsTransitioning(false);
    }, 380);
  };

  const handleExitToLanding = () => {
    if (isTransitioning) return;
    setIsTransitioning(true);

    setTimeout(() => {
      setViewMode('landing');
      window.scrollTo(0, 0);
      setIsTransitioning(false);
    }, 380);
  };

  const handleSelectYear = (yr) => {
    setActiveYear(yr);
    setActiveTab('radar');
  };

  const handleSelectSubdivision = (subName) => {
    setActiveSubdivision(subName);
    setActiveTab('explorer');
  };

  if (viewMode === 'landing') {
    return (
      <LandingPage 
        onLaunchDashboard={handleLaunchDashboard} 
        isExiting={isTransitioning}
      />
    );
  }

  return (
    <div className={`app-container ${isTransitioning ? 'dashboard-exit' : 'dashboard-enter'}`}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onExitToLanding={handleExitToLanding}
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <span className="app-footer-brand">RainRisk</span> &middot; Production Climate Risk Intelligence Platform
          </div>
          <button 
            onClick={handleExitToLanding}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--accent-teal)',
              fontSize: '0.74rem',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            ← Return to Landing Page
          </button>
        </div>
      </footer>
    </div>
  );
}
