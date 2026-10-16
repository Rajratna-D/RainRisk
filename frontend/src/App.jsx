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

const VALID_TABS = ['pulse', 'radar', 'explorer', 'leaderboard', 'cockpit', 'methodology'];

function getInitialNavState() {
  if (typeof window === 'undefined') {
    return { viewMode: 'landing', activeTab: 'pulse' };
  }
  const hash = window.location.hash.replace(/^#\/?/, '').toLowerCase();
  if (VALID_TABS.includes(hash)) {
    return { viewMode: 'dashboard', activeTab: hash };
  }
  return { viewMode: 'landing', activeTab: 'pulse' };
}

export default function App() {
  const initial = useRef(getInitialNavState()).current;
  const [viewMode, setViewMode] = useState(initial.viewMode); // 'landing' | 'dashboard'
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [activeTab, setActiveTab] = useState(initial.activeTab);
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

  // Listen to browser Back / Forward buttons and URL hash changes
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '').toLowerCase();
      if (VALID_TABS.includes(hash)) {
        setViewMode('dashboard');
        setActiveTab(hash);
      } else if (!hash || hash === 'landing' || hash === 'home') {
        setViewMode('landing');
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    const el = pageRef.current;
    if (!el) return;
    el.classList.remove('page-enter');
    void el.offsetWidth;
    el.classList.add('page-enter');
  }, [activeTab]);

  const handleTabChange = (tabId) => {
    if (tabId === activeTab) return;
    setActiveTab(tabId);
    if (window.location.hash !== `#${tabId}`) {
      window.location.hash = tabId;
    }
  };

  const handleLaunchDashboard = () => {
    if (isTransitioning) return;
    setIsTransitioning(true);

    setTimeout(() => {
      setViewMode('dashboard');
      window.scrollTo(0, 0);
      setIsTransitioning(false);
      const targetTab = VALID_TABS.includes(activeTab) ? activeTab : 'pulse';
      if (window.location.hash !== `#${targetTab}`) {
        window.location.hash = targetTab;
      }
    }, 380);
  };

  const handleExitToLanding = () => {
    if (isTransitioning) return;
    setIsTransitioning(true);

    setTimeout(() => {
      setViewMode('landing');
      window.scrollTo(0, 0);
      setIsTransitioning(false);
      if (window.location.hash) {
        history.pushState(null, '', window.location.pathname + window.location.search);
      }
    }, 380);
  };

  const handleSelectYear = (yr) => {
    setActiveYear(yr);
    setActiveTab('radar');
    window.location.hash = 'radar';
  };

  const handleSelectSubdivision = (subName) => {
    setActiveSubdivision(subName);
    setActiveTab('explorer');
    window.location.hash = 'explorer';
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
        setActiveTab={handleTabChange}
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
