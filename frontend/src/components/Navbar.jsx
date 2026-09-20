import React from 'react';
import { CloudRain, BarChart3, Map, LineChart, Award, Sliders, BookOpen } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'pulse', label: 'Executive Pulse', icon: BarChart3 },
    { id: 'radar', label: 'Geospatial Radar', icon: Map },
    { id: 'explorer', label: 'Regional Explorer', icon: LineChart },
    { id: 'leaderboard', label: 'Model Benchmark', icon: Award },
    { id: 'cockpit', label: 'Climate Cockpit', icon: Sliders },
    { id: 'methodology', label: 'Methodology', icon: BookOpen },
  ];

  return (
    <nav className="navbar">
      <div className="brand">
        <div className="brand-icon">
          <CloudRain size={20} strokeWidth={2.5} />
        </div>
        <div className="brand-text">
          <h1>RainRisk</h1>
          <span>Climate Risk Intelligence</span>
        </div>
      </div>

      <div className="nav-tabs">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-tab ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={15} strokeWidth={isActive ? 2.5 : 2} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="status-capsule">
        <span className="pulse-dot"></span>
        <span>SYSTEM ONLINE · 117-YR IMD ARCHIVE</span>
      </div>
    </nav>
  );
}
