/**
 * MahaRainRisk | Global Application State & UI View Switchers
 */

// ============================================================================
// API BASE URL CONFIGURATION
// Automatically connects to Render API when deployed on Cloudflare Pages or Vercel;
// uses local relative paths when running locally.
// ============================================================================
const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? (window.location.port === "8000" || !window.location.port ? "" : "http://127.0.0.1:8000")
  : (window.location.hostname.includes("pages.dev") || window.location.hostname.includes("vercel.app") || !window.location.hostname
      ? "https://rainrisk-vcra.onrender.com"
      : "");
window.API_BASE = API_BASE;

// ============================================================================
// DEFAULT INITIAL TELEMETRY & ADVISORY SNAPSHOT (Paithan baseline)
// Prevents race conditions when switching language immediately upon boot.
// ============================================================================
const DEFAULT_INITIAL_DATA = {
  meta: {
    taluka: "Paithan",
    district: "Chhatrapati Sambhajinagar",
    period: "2026-10",
    taluka_mr: "पैठण",
    district_mr: "छत्रपती संभाजीनगर",
    normal_annual_rainfall_mm: 734
  },
  live_diagnosis: {
    category_code: 0,
    label_en: "Safe",
    label_mr: "सुरक्षित",
    confidence_pct: 95.7
  },
  "30_day_forecast": {
    category_code: 0,
    label_en: "Safe Outlook",
    label_mr: "सुरक्षित अंदाज",
    confidence_pct: 84.0
  },
  farmer_cards: {
    rainfall_deficit: {
      title_en: "3-Month Rainfall",
      title_mr: "३ महिन्यांचा पाऊस",
      value_mm: 186.8,
      status_en: "Normal Rainfall",
      status_mr: "पाऊस समाधानकारक",
      color: "#047857"
    },
    soil_moisture: {
      title_en: "Root-Zone Soil Moisture",
      title_mr: "जमिनीतील ओलावा",
      value_pct: 66.9,
      status_en: "Adequate Soil Moisture",
      status_mr: "ओलावा पुरेसा आहे",
      color: "#047857"
    },
    dam_storage: {
      title_en: "Dam Reservoir Storage",
      title_mr: "धरण पाणीसाठा",
      value_pct: 72.5,
      status_en: "Jayakwadi Reservoir (Optimal)",
      status_mr: "जायकवाडी धरण (मुबलक)",
      color: "#047857",
      dam_name: "Jayakwadi Reservoir",
      dam_name_mr: "जायकवाडी धरण"
    },
    dry_gap: {
      title_en: "Dry Spell Days",
      title_mr: "पावसातील खंड दिवस",
      value_days: 4,
      status_en: "No Significant Dry Spell",
      status_mr: "पावसात मोठा खंड नाही",
      color: "#047857"
    }
  },
  chart_history: [
    { year: 2019, monsoon_rainfall_mm: 530.4 },
    { year: 2020, monsoon_rainfall_mm: 923.2 },
    { year: 2021, monsoon_rainfall_mm: 1200.3 },
    { year: 2022, monsoon_rainfall_mm: 734.0 },
    { year: 2023, monsoon_rainfall_mm: 429.9 },
    { year: 2024, monsoon_rainfall_mm: 824.0 }
  ],
  advisory: {
    geography: {
      taluka_name: "Paithan",
      district_name: "Chhatrapati Sambhajinagar",
      target_crop: "Soybean & Cotton"
    },
    university_anchor: {
      university_key: "VNMKV Parbhani",
      university_name_en: "Vasantrao Naik Marathwada Krishi Vidyapeeth, Parbhani",
      university_name_mr: "वसंतराव नाईक मराठवाडा कृषी विद्यापीठ, परभणी",
      regional_focus: "Deep Black Vertisols (काळी जमीन) & Rain-Shadow Drought Stress"
    },
    risk_level: {
      category_code: 0,
      status_en: "Safe / Normal Condition",
      status_mr: "सुरक्षित / सामान्य स्थिती",
      badge_color: "#10B981"
    },
    telemetry_context: {
      soil_moisture_index_pct: 66.9,
      dam_storage_pct: 72.5
    },
    prescriptive_actions: {
      irrigation_strategy: {
        en: "Soil moisture is optimal; no irrigation required for the next 4 days. Maintain light watering if needed.",
        mr: "जमिनीत ओलावा चांगला असल्याने पुढील ४ दिवस पाणी देण्याची गरज नाही. हलके पाणी द्यावे."
      },
      moisture_conservation: {
        en: "Spread crop residue or straw mulching between crop rows to preserve root-zone moisture.",
        mr: "पिकाच्या ओळींत पाचट किंवा भुसा आच्छादन (Mulching) केल्यास बाष्पीभवन रोखले जाईल."
      },
      foliar_and_nutrients: {
        en: "If dry spell extends, spray 1% Potassium Nitrate (100g in 10L water) early morning to relieve heat stress.",
        mr: "पावसात खंड पडल्यास १% पोटॅशियम नायट्रेट (१०० ग्रॅम प्रति १० लिटर पाणी) फवारावे."
      },
      contingency_management: {
        en: "Keep drainage furrows clear to avoid waterlogging. Spray 5% Neem seed kernel extract (NSKE) to prevent sucking pests.",
        mr: "शेतात पाणी साचणार नाही यासाठी पाण्याचा निचरा ठेवा. किडींचा प्रादुर्भाव रोखण्यासाठी ५% निंबोळी अर्काची प्रतिबंधात्मक फवारणी करावी."
      }
    },
    source_citation: "Official Agro-Advisory aligned with VNMKV Parbhani Package of Practices"
  }
};
window.DEFAULT_INITIAL_DATA = DEFAULT_INITIAL_DATA;

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
  currentAdvisory: DEFAULT_INITIAL_DATA.advisory,
  currentData: DEFAULT_INITIAL_DATA,
  currentXai: null,
  currentAdjacent: null,
  currentView: "crop", // "crop" or "map"
  currentMainTab: "farmer", // "farmer" or "analytics"
  currentRightPanel: "telemetry" // "telemetry" or "advisory"
};
window.state = state;

const ARC_LENGTH = 204.2;

// ============================================================================
// NUMERAL FORMATTER: BIDIRECTIONAL DEVANAGARI <-> ASCII NUMERAL ENGINE
// ============================================================================
function formatNumber(num, isMr) {
  if (num === null || num === undefined) return "";
  const mrDigits = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'];
  let str = String(num);
  if (isMr) {
    return str.replace(/[0-9]/g, d => mrDigits[parseInt(d)]);
  } else {
    return str.replace(/[०-९]/g, d => mrDigits.indexOf(d).toString());
  }
}
window.formatNumber = formatNumber;

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
