/**
 * MahaRainRisk | Global Application State & UI View Switchers
 */

// ============================================================================
// API BASE URL CONFIGURATION
// Automatically connects to Render API when deployed on Cloudflare Pages or Vercel;
// uses local relative paths when running locally.
// ============================================================================
const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? ""
  : (window.location.hostname.includes("pages.dev") || window.location.hostname.includes("vercel.app")
      ? "https://rainrisk-vcra.onrender.com"
      : "");
window.API_BASE = API_BASE;

// ============================================================================
// APPLICATION STATE
// ============================================================================
const state = {
  currentTaluka: "Paithan",
  currentLanguage: "mr", // Default: Marathi
  talukasDirectory: [],
  mapInstance: null,
  markerClusterLayer: null,
  activeMarker: null,
  markersList: [],
  speechSynth: window.speechSynthesis || null,
  activeSpeechRecognition: null,
  currentAdvisory: null,
  currentData: null,
  currentXai: null,
  currentAdjacent: null,
  currentView: "crop", // "crop" or "map"
  currentMainTab: "farmer", // "farmer" or "analytics"
  currentRightPanel: "telemetry" // "telemetry" or "advisory"
};

const ARC_LENGTH = 204.2;

// ============================================================================
// NUMERAL FORMATTER: DEVANAGARI NUMERALS FOR MARATHI MODE
// ============================================================================
function formatNumber(num, isMr) {
  if (num === null || num === undefined) return "";
  const str = String(num);
  if (!isMr) return str;
  const mrDigits = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'];
  return str.replace(/[0-9]/g, d => mrDigits[parseInt(d)]);
}

// ============================================================================
// GLOBAL VIEW & TAB SWITCHERS (Immediately available for inline onclicks)
// ============================================================================
window.switchMainTab = function(mode) {
  state.currentMainTab = mode;
  const tabFarmer = document.getElementById("tab-content-farmer");
  const tabAnalytics = document.getElementById("tab-content-analytics");
  const btnFarmer = document.getElementById("tab-btn-farmer");
  const btnAnalytics = document.getElementById("tab-btn-analytics");

  if (mode === "analytics") {
    tabFarmer?.classList.remove("active");
    tabAnalytics?.classList.add("active");
    btnFarmer?.classList.remove("active");
    btnAnalytics?.classList.add("active");
  } else {
    tabAnalytics?.classList.remove("active");
    tabFarmer?.classList.add("active");
    btnAnalytics?.classList.remove("active");
    btnFarmer?.classList.add("active");
    setTimeout(() => {
      if (state.mapInstance) state.mapInstance.invalidateSize();
    }, 120);
  }
};

window.openAiModal = function() {
  document.getElementById("modal-ai-advisory")?.classList.add("open");
};

window.closeAiModal = function() {
  document.getElementById("modal-ai-advisory")?.classList.remove("open");
};

window.switchRightPanel = function(mode) {
  // Directly opens the dedicated AI Decision Support Modal
  window.openAiModal();
};

window.openAdvisoryDrawer = function() {
  window.openAiModal();
};

window.toggleHeroView = function(mode) {
  const heroCard = document.getElementById("hero-card");
  const btnCrop = document.getElementById("switch-crop-view");
  const btnMap = document.getElementById("switch-map-view");
  if (!heroCard) return;

  if (mode === "map") {
    btnMap?.classList.add("active");
    btnCrop?.classList.remove("active");
    heroCard.classList.add("show-map");
    state.currentView = "map";
    if (typeof window.setActiveDockBtn === "function") {
      window.setActiveDockBtn("dock-btn-grid");
    }
    if (state.mapInstance) {
      setTimeout(() => {
        state.mapInstance.invalidateSize();
      }, 150);
      setTimeout(() => {
        state.mapInstance.invalidateSize();
        state.mapInstance.setView([19.65, 75.80], 7.2);
      }, 380);
    }
  } else {
    btnCrop?.classList.add("active");
    btnMap?.classList.remove("active");
    heroCard.classList.remove("show-map");
    state.currentView = "crop";
    if (typeof window.setActiveDockBtn === "function") {
      window.setActiveDockBtn("dock-btn-greenhouse");
    }
    if (state.mapInstance) {
      setTimeout(() => {
        state.mapInstance.invalidateSize();
      }, 380);
    }
  }
};

window.openTipsModal = function() {
  document.getElementById("modal-tips")?.classList.add("open");
};
window.closeTipsModal = function() {
  document.getElementById("modal-tips")?.classList.remove("open");
};
window.openAlertsModal = function() {
  document.getElementById("modal-alerts")?.classList.add("open");
};
window.closeAlertsModal = function() {
  document.getElementById("modal-alerts")?.classList.remove("open");
};
window.openSourcesModal = function() {
  document.getElementById("modal-sources")?.classList.add("open");
};
window.closeSourcesModal = function() {
  document.getElementById("modal-sources")?.classList.remove("open");
};
