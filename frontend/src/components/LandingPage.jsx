import React, { useState, useEffect, useRef } from 'react';
import { 
  ArrowRight, 
  ChevronDown, 
  History, 
  Waves, 
  AlertTriangle, 
  Cpu, 
  GitBranch
} from 'lucide-react';

export default function LandingPage({ onLaunchDashboard, isExiting = false }) {
  const [progress, setProgress] = useState(0);
  const [heroOpacity, setHeroOpacity] = useState(1);
  const [heroTranslate, setHeroTranslate] = useState(0);
  const panelsRef = useRef(null);

  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const scrollY = window.scrollY;
          const vh = window.innerHeight;

          // Hero parallax fade & lift
          const hOpacity = Math.max(0, 1 - scrollY / (vh * 0.6));
          const hTranslate = -scrollY * 0.25;
          setHeroOpacity(hOpacity);
          setHeroTranslate(hTranslate);

          // Panels convergence animation:
          // Triggers as panels scroll into the user's viewport!
          if (panelsRef.current) {
            const rect = panelsRef.current.getBoundingClientRect();
            // rect.top is vh * 0.9 when top of panels enters near bottom of viewport
            // rect.top is vh * 0.2 when panels reach upper-middle of viewport
            const start = vh * 0.88;
            const end = vh * 0.18;
            const p = Math.min(1, Math.max(0, (start - rect.top) / (start - end)));
            setProgress(p);
          }

          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToPanels = () => {
    panelsRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 4 corners convergence (subtle vertical lift on mobile, 4-corner convergence on desktop)
  const xOffset = isMobile ? 0 : 90;
  const yOffset = isMobile ? 25 : 40;
  const card1Transform = `translate3d(${(1 - progress) * -xOffset}px, ${(1 - progress) * -yOffset}px, 0)`;
  const card2Transform = `translate3d(${(1 - progress) * xOffset}px, ${(1 - progress) * -yOffset}px, 0)`;
  const card3Transform = `translate3d(${(1 - progress) * -xOffset}px, ${(1 - progress) * yOffset}px, 0)`;
  const card4Transform = `translate3d(${(1 - progress) * xOffset}px, ${(1 - progress) * yOffset}px, 0)`;
  const centerTransform = `translate3d(0, ${(1 - progress) * (isMobile ? 20 : 50)}px, 0) scale(${isMobile ? 1 : 0.86 + progress * 0.14})`;


  return (
    <div className={`lp ${isExiting ? 'lp-exit' : ''}`}>
      {/* FIXED FULL-VIEWPORT VIDEO BACKGROUND */}
      <div className="lp-video-bg">
        <video autoPlay loop muted playsInline poster="/hero-poster.jpg">
          <source src="/hero-monsoon.mp4" type="video/mp4" />
        </video>
        <div className="lp-video-dim" />
      </div>

      <div className="lp-content">
        {/* ========== HERO SECTION ========== */}
        <section className="lp-hero">
          <div 
            className="lp-hero-inner"
            style={{
              opacity: heroOpacity,
              transform: `translate3d(0, ${heroTranslate}px, 0)`,
              pointerEvents: heroOpacity < 0.15 ? 'none' : 'auto'
            }}
          >
            <h1 className="lp-title">RAIN RISK</h1>
            <p className="lp-subtitle">
              Regional monsoon and drought risk intelligence across India's 36 meteorological units.
            </p>

            {/* LIQUID GLASS STATS */}
            <div className="lp-glass">
              <div className="lp-glass-sheen" />
              <div className="lp-glass-row">
                <div className="lp-stat">
                  <span className="lp-stat-num">93.0%</span>
                  <span className="lp-stat-label">Within ±1 Class</span>
                </div>
                <div className="lp-stat-div" />
                <div className="lp-stat">
                  <span className="lp-stat-num">117 Yrs</span>
                  <span className="lp-stat-label">Historical Records</span>
                </div>
                <div className="lp-stat-div" />
                <div className="lp-stat">
                  <span className="lp-stat-num">23 Features</span>
                  <span className="lp-stat-label">Rain + Ocean SST</span>
                </div>
                <div className="lp-stat-div" />
                <div className="lp-stat">
                  <span className="lp-stat-num">36</span>
                  <span className="lp-stat-label">Meteorological Units</span>
                </div>
              </div>
            </div>

            <button onClick={scrollToPanels} className="lp-scroll-cue" aria-label="Scroll down">
              <span>Explore Architecture</span>
              <ChevronDown size={18} />
            </button>
          </div>
        </section>

        {/* ========== 4 PANELS + CENTER LAUNCH BUTTON (SCROLL-ANIMATED LIQUID GLASS) ========== */}
        <section className="lp-panels" ref={panelsRef}>
          <div className="lp-panels-grid">

            {/* BOX 1: TOP LEFT */}
            <div 
              className="lp-card card-tl"
              style={{
                transform: card1Transform,
                opacity: progress
              }}
            >
              <div className="lp-card-accent" style={{ '--accent': 'var(--accent-amber)' }} />
              <div className="lp-card-icon" style={{ color: 'var(--accent-amber)' }}>
                <AlertTriangle size={20} />
              </div>
              <h3 className="lp-card-title">Pre-Monsoon Intelligence</h3>
              <p className="lp-card-body">
                Over 55% of Indian agriculture relies entirely on monsoon rains. Early subdivisional forecasts
                empower farmers and policymakers to adjust cropping cycles and conserve water before sowing begins.
              </p>
              <span className="lp-card-tag">600M People Dependent</span>
            </div>

            {/* BOX 2: TOP RIGHT */}
            <div 
              className="lp-card card-tr"
              style={{
                transform: card2Transform,
                opacity: progress
              }}
            >
              <div className="lp-card-accent" style={{ '--accent': 'var(--accent-teal)' }} />
              <div className="lp-card-icon" style={{ color: 'var(--accent-teal)' }}>
                <Cpu size={20} />
              </div>
              <h3 className="lp-card-title">Ordinal Precision</h3>
              <p className="lp-card-body">
                Frank-Hall ordinal classification respects the physical severity order of drought,
                delivering 93.0% adjacent class reliability and bounding catastrophic errors to 3.3%.
              </p>
              <span className="lp-card-tag">93.0% Within ±1 Class</span>
            </div>

            {/* LAUNCH BUTTON CENTERPIECE */}
            <div 
              className="lp-center"
              style={{
                transform: centerTransform,
                opacity: progress
              }}
            >
              <button
                onClick={onLaunchDashboard}
                className={`lp-launch ${isExiting ? 'launching' : ''}`}
                id="launch-dashboard-cta"
                disabled={isExiting}
              >
                <span>{isExiting ? 'Entering Dashboard...' : 'Launch Dashboard'}</span>
                <ArrowRight size={18} />
              </button>
              <a
                href="https://github.com/Rajratna-D/RainRisk"
                target="_blank"
                rel="noopener noreferrer"
                className="lp-github"
              >
                <GitBranch size={13} />
                <span>View Code on GitHub</span>
              </a>
            </div>

            {/* BOX 3: BOTTOM LEFT */}
            <div 
              className="lp-card card-bl"
              style={{
                transform: card3Transform,
                opacity: progress
              }}
            >
              <div className="lp-card-accent" style={{ '--accent': 'var(--accent-cyan)' }} />
              <div className="lp-card-icon" style={{ color: 'var(--accent-cyan)' }}>
                <Waves size={20} />
              </div>
              <h3 className="lp-card-title">Pacific + Indian Oceans</h3>
              <p className="lp-card-body">
                Incorporating Pacific Niño 3.4 SST momentum and Indian Ocean Dipole anomalies boosts
                rare drought and flood detection accuracy by 8.5%, from 34.7% to 43.2%.
              </p>
              <span className="lp-card-tag">+8.5% Balanced Accuracy Boost</span>
            </div>

            {/* BOX 4: BOTTOM RIGHT */}
            <div 
              className="lp-card card-br"
              style={{
                transform: card4Transform,
                opacity: progress
              }}
            >
              <div className="lp-card-accent" style={{ '--accent': 'var(--accent-sky)' }} />
              <div className="lp-card-icon" style={{ color: 'var(--accent-sky)' }}>
                <History size={20} />
              </div>
              <h3 className="lp-card-title">Century-Scale Climate Memory</h3>
              <p className="lp-card-body">
                Trained on 117 uninterrupted years of India Meteorological Department records (1901–2017),
                learning from over a century of historic droughts, famines, and planetary teleconnection cycles.
              </p>
              <span className="lp-card-tag">117-Year Historical Depth</span>
            </div>

          </div>
        </section>
      </div>
    </div>
  );
}
