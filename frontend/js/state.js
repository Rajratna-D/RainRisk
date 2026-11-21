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
  : "https://rainrisk-vcra.onrender.com";
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

const DEFAULT_FORECAST = {
  taluka_code: 4123,
  taluka_name: "Paithan",
  taluka_name_mr: "पैठण",
  district_name: "Chhatrapati Sambhajinagar",
  district_name_mr: "छत्रपती संभाजीनगर",
  latitude: 19.4795,
  longitude: 75.3854,
  as_of_date: new Date().toISOString().split("T")[0],
  forecast_7_day: [
    {
      date: new Date().toISOString().split("T")[0],
      day_name_en: "Today",
      day_name_mr: "आज",
      weather_code: 0,
      weather_desc_en: "Clear & Sunny",
      weather_desc_mr: "निरभ्र व स्वच्छ आकाश",
      icon: "sun",
      temp_max: 29.2,
      temp_min: 17.0,
      precip_mm: 0.0,
      precip_prob_pct: 0,
      wind_speed_max: 9.5,
      spray_condition_en: "Ideal for foliar spray",
      spray_condition_mr: "फवारणीसाठी उत्तम वेळ",
      field_action_en: "Optimal window for weeding, hoeing, and fertilizer application.",
      field_action_mr: "कोळपणी, आंतरमशागत व खत व्यवस्थापनासाठी उत्तम दिवस."
    },
    {
      date: new Date(Date.now() + 86400000).toISOString().split("T")[0],
      day_name_en: "Tomorrow",
      day_name_mr: "उद्या",
      weather_code: 0,
      weather_desc_en: "Clear & Sunny",
      weather_desc_mr: "निरभ्र व स्वच्छ आकाश",
      icon: "sun",
      temp_max: 29.5,
      temp_min: 17.2,
      precip_mm: 0.0,
      precip_prob_pct: 0,
      wind_speed_max: 10.0,
      spray_condition_en: "Ideal for foliar spray",
      spray_condition_mr: "फवारणीसाठी उत्तम वेळ",
      field_action_en: "Maintain good soil aeration with light hoeing.",
      field_action_mr: "जमिनीत हलकी कोळपणी करून हवा खेळती ठेवावी."
    },
    {
      date: new Date(Date.now() + 2 * 86400000).toISOString().split("T")[0],
      day_name_en: "Day 3",
      day_name_mr: "दिवस ३",
      weather_code: 1,
      weather_desc_en: "Mainly Clear",
      weather_desc_mr: "मुख्यतः स्वच्छ आकाश",
      icon: "cloud-sun",
      temp_max: 28.8,
      temp_min: 16.5,
      precip_mm: 0.0,
      precip_prob_pct: 0,
      wind_speed_max: 11.0,
      spray_condition_en: "Safe for spraying",
      spray_condition_mr: "फवारणीसाठी अनुकूल",
      field_action_en: "Soil retains good workable moisture.",
      field_action_mr: "जमिनीत वाफसा चांगला राहील."
    },
    {
      date: new Date(Date.now() + 3 * 86400000).toISOString().split("T")[0],
      day_name_en: "Day 4",
      day_name_mr: "दिवस ४",
      weather_code: 1,
      weather_desc_en: "Partly Cloudy",
      weather_desc_mr: "अंशतः ढगाळ",
      icon: "cloud-sun",
      temp_max: 28.5,
      temp_min: 16.2,
      precip_mm: 0.0,
      precip_prob_pct: 5,
      wind_speed_max: 10.5,
      spray_condition_en: "Safe for spraying",
      spray_condition_mr: "फवारणीसाठी अनुकूल",
      field_action_en: "Mulch crop rows to prevent moisture loss.",
      field_action_mr: "पिकाच्या ओळींत पाचट आच्छादन (Mulching) करावे."
    },
    {
      date: new Date(Date.now() + 4 * 86400000).toISOString().split("T")[0],
      day_name_en: "Day 5",
      day_name_mr: "दिवस ५",
      weather_code: 0,
      weather_desc_en: "Clear Sky",
      weather_desc_mr: "स्वच्छ आकाश",
      icon: "sun",
      temp_max: 29.0,
      temp_min: 16.0,
      precip_mm: 0.0,
      precip_prob_pct: 0,
      wind_speed_max: 9.8,
      spray_condition_en: "Ideal for foliar spray",
      spray_condition_mr: "फवारणीसाठी उत्तम वेळ",
      field_action_en: "Monitor standing crops for sucking pests.",
      field_action_mr: "रसशोषक किडींसाठी पिकाची पाहणी करावी."
    },
    {
      date: new Date(Date.now() + 5 * 86400000).toISOString().split("T")[0],
      day_name_en: "Day 6",
      day_name_mr: "दिवस ६",
      weather_code: 0,
      weather_desc_en: "Clear & Cool",
      weather_desc_mr: "निरभ्र व गारठा",
      icon: "sun",
      temp_max: 28.7,
      temp_min: 15.8,
      precip_mm: 0.0,
      precip_prob_pct: 0,
      wind_speed_max: 9.0,
      spray_condition_en: "Safe for spraying",
      spray_condition_mr: "फवारणीसाठी अनुकूल",
      field_action_en: "Schedule light drip irrigation if soil dry.",
      field_action_mr: "जमीन कोरडी असल्यास ठिबक सिंचनाने पाणी द्यावे."
    },
    {
      date: new Date(Date.now() + 6 * 86400000).toISOString().split("T")[0],
      day_name_en: "Day 7",
      day_name_mr: "दिवस ७",
      weather_code: 1,
      weather_desc_en: "Sunny & Dry",
      weather_desc_mr: "उबदार व कोरडे",
      icon: "sun",
      temp_max: 29.1,
      temp_min: 16.0,
      precip_mm: 0.0,
      precip_prob_pct: 0,
      wind_speed_max: 9.5,
      spray_condition_en: "Safe for spraying",
      spray_condition_mr: "फवारणीसाठी अनुकूल",
      field_action_en: "Prepare for upcoming week's nutrient management.",
      field_action_mr: "पुढील आठवड्याच्या खत नियोजनाची तयारी ठेवा."
    }
  ],
  forecast_30_day: {
    category_code: 0,
    risk_label_en: "Safe",
    risk_label_mr: "सुरक्षित",
    confidence_pct: 84.0,
    expected_rain_days: "0–1 Days",
    expected_rain_mm: 8.5,
    residual_moisture_pct: 74.0,
    summary_en: "Post-monsoon dry conditions. Residual root-zone soil moisture is 74%, favorable for Rabi crops.",
    summary_mr: "परतीचा मान्सून संपल्याने कोरडे हवामान राहील. जमिनीतील ओलावा ७४% असून रब्बी पिकांना अनुकूल आहे.",
    weeks: [
      {
        week_num: 1,
        title_en: "Week 1 (Days 1–7)",
        title_mr: "आठवडा १ (दिवस १–७)",
        moisture_pct: 74.0,
        moisture_status_en: "Adequate root-zone moisture (Vafsa condition)",
        moisture_status_mr: "जमिनीत वाफसा व पुरेसा ओलावा",
        rain_outlook_en: "Stable post-monsoon weather",
        rain_outlook_mr: "हवामान कोरडे व स्थिर",
        action_en: "Complete intercultural hoeing, weeding, and foliar nutrition while soil retains good moisture.",
        action_mr: "जमिनीत चांगला ओलावा असताना कोळपणी, तण नियंत्रण व विद्राव्य खतांची फवारणी पूर्ण करावी."
      },
      {
        week_num: 2,
        title_en: "Week 2 (Days 8–14)",
        title_mr: "आठवडा २ (दिवस ८–१४)",
        moisture_pct: 69.0,
        moisture_status_en: "Gradual moisture decline under sunny skies",
        moisture_status_mr: "उन्हामुळे ओलावा हळूहळू कमी होण्याचा अंदाज",
        rain_outlook_en: "Dry winds, negligible rainfall probability",
        rain_outlook_mr: "कोरडे वारे, पावसाची शक्यता अत्यल्प",
        action_en: "Apply crop residue mulching (straw/dry leaves) to shield root zone and preserve moisture for 10-12 days.",
        action_mr: "बाष्पीभवन रोखण्यासाठी पिकाच्या ओळींत पाचट किंवा भुसा आच्छादन (Mulching) करावे."
      },
      {
        week_num: 3,
        title_en: "Week 3 (Days 15–21)",
        title_mr: "आठवडा ३ (दिवस १५–२१)",
        moisture_pct: 62.0,
        moisture_status_en: "Irrigation threshold reached for critical crop stages",
        moisture_status_mr: "पिकाच्या संवेदनशील अवस्थेसाठी पाण्याची गरज",
        rain_outlook_en: "Passing high clouds, dry conditions",
        rain_outlook_mr: "ढगाळ हवामानाची शक्यता, पाऊस नाही",
        action_en: "Schedule supplementary drip/sprinkler irrigation from farm ponds or wells during morning/evening hours.",
        action_mr: "शेततळे किंवा विहिरीतून ठिबक सिंचनाद्वारे हलके संरक्षित पाणी द्यावे."
      },
      {
        week_num: 4,
        title_en: "Week 4 (Days 22–30)",
        title_mr: "आठवडा ४ (दिवस २२–३०)",
        moisture_pct: 56.0,
        moisture_status_en: "Month-end baseline established",
        moisture_status_mr: "महिना अखेर ओलावा पातळी",
        rain_outlook_en: "Cool night temperatures, dry days",
        rain_outlook_mr: "रात्री गारठा वाढेल, दिवस कोरडे",
        action_en: "Spray 1% potassium nitrate (100g in 10L water) if moisture stress is observed on leaves.",
        action_mr: "पानाचा ताण जाणवल्यास १% पोटॅशियम नायट्रेटची फवारणी करावी."
      }
    ]
  },
  source_attribution: "ECMWF / Open-Meteo & Mode 2 AI GBDT"
};
window.DEFAULT_FORECAST = DEFAULT_FORECAST;

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
  currentForecast: DEFAULT_FORECAST,
  forecastActiveTab: "7day", // "7day" or "30day"
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
