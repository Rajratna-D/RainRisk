import React from 'react';
import { CloudRain, BarChart3, Map, LineChart, Award, Sliders, BookOpen, ArrowLeft } from 'lucide-react';

const NAV_ITEMS = [
  { id: 'pulse', label: 'Executive Pulse', icon: BarChart3 },
  { id: 'radar', label: 'Geospatial Radar', icon: Map },
  { id: 'explorer', label: 'Regional Explorer', icon: LineChart },
  { id: 'leaderboard', label: 'Model Benchmark', icon: Award },
  { id: 'cockpit', label: 'Climate Cockpit', icon: Sliders },
  { id: 'methodology', label: 'Methodology', icon: BookOpen },
];

export default function Navbar({ activeTab, setActiveTab, onExitToLanding }) {
  return (
    <nav className="navbar">
      <div className="navbar-header-row">
        <div 
          className="brand" 
          onClick={onExitToLanding}
          style={{ cursor: 'pointer' }}
          title="Return to Landing Page"
        >
          <div className="brand-icon">
            <CloudRain size={20} strokeWidth={2.5} />
          </div>
          <div className="brand-text">
            <h1>RainRisk</h1>
            <span>Climate Risk Intelligence</span>
          </div>
        </div>

        <div className="nav-right">
          {onExitToLanding && (
            <button
              className="exit-to-landing-btn"
              onClick={onExitToLanding}
              title="Return to Landing Page"
            >
              <ArrowLeft size={13} />
              <span>Home</span>
            </button>
          )}

          <div className="status-capsule">
            <span className="pulse-dot"></span>
            <span>SYSTEM ONLINE</span>
          </div>
        </div>
      </div>

      <div className="nav-tabs" role="tablist">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              role="tab"
              aria-selected={isActive}
              className={`nav-tab ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={15} strokeWidth={isActive ? 2.5 : 2} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
