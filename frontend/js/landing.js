/**
 * MahaRainRisk | Landing Page Interactive Controller
 * Exact scroll parallax & 4-corner convergence from LandingPage.jsx
 * View transitions between Landing Page and Dashboard
 */

(function () {
  const landingView = document.getElementById("landing-view");
  const appWindow = document.getElementById("app-window");
  const heroInner = document.getElementById("lp-hero-inner");
  const panelsRef = document.getElementById("lp-panels");
  const launchBtn = document.getElementById("launch-dashboard-cta");
  const scrollCue = document.getElementById("lp-scroll-cue");

  const cardTL = document.getElementById("card-tl");
  const cardTR = document.getElementById("card-tr");
  const cardBL = document.getElementById("card-bl");
  const cardBR = document.getElementById("card-br");
  const centerCTA = document.getElementById("lp-center-cta");

  let isTransitioning = false;

  // ==========================================================================
  // SCROLL PARALLAX & 4-CORNER CONVERGENCE (Exact from LandingPage.jsx)
  // ==========================================================================
  let ticking = false;

  function updateScrollParallax() {
    if (!landingView || landingView.style.display === "none") return;

    const scrollY = window.scrollY || window.pageYOffset;
    const vh = window.innerHeight;
    const isMobile = window.innerWidth < 768;

    // Hero parallax fade & lift
    if (heroInner) {
      const hOpacity = Math.max(0, 1 - scrollY / (vh * 0.6));
      const hTranslate = -scrollY * 0.25;
      heroInner.style.opacity = hOpacity;
      heroInner.style.transform = `translate3d(0, ${hTranslate}px, 0)`;
      heroInner.style.pointerEvents = hOpacity < 0.15 ? "none" : "auto";
    }

    // Panels convergence animation
    if (panelsRef) {
      const rect = panelsRef.getBoundingClientRect();
      const start = vh * 0.88;
      const end = vh * 0.18;
      const progress = Math.min(1, Math.max(0, (start - rect.top) / (start - end)));

      const xOffset = isMobile ? 0 : 90;
      const yOffset = isMobile ? 25 : 40;

      if (cardTL) {
        cardTL.style.transform = `translate3d(${(1 - progress) * -xOffset}px, ${(1 - progress) * -yOffset}px, 0)`;
        cardTL.style.opacity = progress;
      }
      if (cardTR) {
        cardTR.style.transform = `translate3d(${(1 - progress) * xOffset}px, ${(1 - progress) * -yOffset}px, 0)`;
        cardTR.style.opacity = progress;
      }
      if (cardBL) {
        cardBL.style.transform = `translate3d(${(1 - progress) * -xOffset}px, ${(1 - progress) * yOffset}px, 0)`;
        cardBL.style.opacity = progress;
      }
      if (cardBR) {
        cardBR.style.transform = `translate3d(${(1 - progress) * xOffset}px, ${(1 - progress) * yOffset}px, 0)`;
        cardBR.style.opacity = progress;
      }
      if (centerCTA) {
        const centerLift = (1 - progress) * (isMobile ? 20 : 50);
        const centerScale = isMobile ? 1 : 0.86 + progress * 0.14;
        centerCTA.style.transform = `translate3d(0, ${centerLift}px, 0) scale(${centerScale})`;
        centerCTA.style.opacity = progress;
      }
    }
  }

  function onScroll() {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        updateScrollParallax();
        ticking = false;
      });
      ticking = true;
    }
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", () => {
    updateScrollParallax();
  });

  if (scrollCue && panelsRef) {
    scrollCue.addEventListener("click", () => {
      panelsRef.scrollIntoView({ behavior: "smooth" });
    });
  }

  // ==========================================================================
  // VIEW TRANSITIONS: LANDING <-> DASHBOARD
  // ==========================================================================
  window.launchDashboard = function () {
    if (isTransitioning) return;
    isTransitioning = true;

    if (launchBtn) {
      launchBtn.classList.add("launching");
      launchBtn.innerHTML = `<span>Entering Dashboard...</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
    }

    if (landingView) {
      landingView.classList.add("lp-exit");
    }

    setTimeout(() => {
      // 1. Hide landing view
      if (landingView) landingView.style.display = "none";
      document.body.classList.remove("landing-active");

      // 2. Show dashboard app window
      if (appWindow) {
        appWindow.style.display = "flex";
        appWindow.classList.remove("dashboard-exit");
        appWindow.classList.add("dashboard-enter");
      }

      window.scrollTo(0, 0);

      // 3. Update URL hash
      if (window.location.hash !== "#dashboard") {
        window.location.hash = "dashboard";
      }

      // 4. Invalidate Leaflet map size
      setTimeout(() => {
        if (window.state && window.state.mapInstance) {
          window.state.mapInstance.invalidateSize();
        }
      }, 150);

      isTransitioning = false;
      if (launchBtn) {
        launchBtn.classList.remove("launching");
        launchBtn.innerHTML = `<span>Launch Dashboard</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`;
      }
    }, 380);
  };

  window.returnToLanding = function () {
    if (isTransitioning) return;
    isTransitioning = true;

    if (appWindow) {
      appWindow.classList.remove("dashboard-enter");
      appWindow.classList.add("dashboard-exit");
    }

    setTimeout(() => {
      // 1. Hide dashboard app window
      if (appWindow) appWindow.style.display = "none";

      // 2. Activate landing page on body
      document.body.classList.add("landing-active");
      if (landingView) {
        landingView.style.display = "block";
        landingView.classList.remove("lp-exit");
      }

      window.scrollTo(0, 0);

      // 3. Clear URL hash
      if (window.location.hash) {
        history.pushState(null, "", window.location.pathname + window.location.search);
      }

      updateScrollParallax();
      isTransitioning = false;
    }, 350);
  };

  // ==========================================================================
  // INITIAL ROUTE / HASH DETECTION
  // ==========================================================================
  function initRoute() {
    const hash = window.location.hash.replace(/^#\/?/, "").toLowerCase();
    if (hash === "dashboard") {
      // Directly open dashboard
      if (landingView) landingView.style.display = "none";
      document.body.classList.remove("landing-active");
      if (appWindow) {
        appWindow.style.display = "flex";
        appWindow.classList.add("dashboard-enter");
      }
      setTimeout(() => {
        if (window.state && window.state.mapInstance) {
          window.state.mapInstance.invalidateSize();
        }
      }, 200);
    } else {
      // Default: Display landing page
      document.body.classList.add("landing-active");
      if (landingView) landingView.style.display = "block";
      if (appWindow) appWindow.style.display = "none";
      setTimeout(updateScrollParallax, 50);
    }
  }

  // Handle browser back/forward buttons
  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace(/^#\/?/, "").toLowerCase();
    if (hash === "dashboard") {
      window.launchDashboard();
    } else {
      window.returnToLanding();
    }
  });

  // Attach Launch CTA click listener
  if (launchBtn) {
    launchBtn.addEventListener("click", window.launchDashboard);
  }

  // Initialize on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRoute);
  } else {
    initRoute();
  }
})();
