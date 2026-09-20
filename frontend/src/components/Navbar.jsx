import React from 'react';
import { CloudRain, BarChart3, Map, LineChart, Award, Sliders, BookOpen, Sun, Moon } from 'lucide-react';

const NAV_ITEMS = [
  { id: 'pulse', label: 'Executive Pulse', icon: BarChart3 },
  { id: 'radar', label: 'Geospatial Radar', icon: Map },
  { id: 'explorer', label: 'Regional Explorer', icon: LineChart },
  { id: 'leaderboard', label: 'Model Benchmark', icon: Award },
  { id: 'cockpit', label: 'Climate Cockpit', icon: Sliders },
  { id: 'methodology', label: 'Methodology', icon: BookOpen },
];

export default function Navbar({ activeTab, setActiveTab, theme, onToggleTheme }) {
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
        {NAV_ITEMS.map((item) => {
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

      <div className="nav-right">
        <button
          className="theme-toggle"
          onClick={onToggleTheme}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <div className="status-capsule">
          <span className="pulse-dot"></span>
          <span>SYSTEM ONLINE</span>
        </div>
      </div>
    </nav>
  );
}
