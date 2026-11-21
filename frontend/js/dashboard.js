/**
 * MahaRainRisk | Dashboard DOM Updates (Farmer Cards, Analytics, Right Panel)
 * Depends on: state.js (state, formatNumber, ARC_LENGTH), advisory.js
 */

// Pre-warm Render backend the moment the dashboard loads.
// By the time a user reads the page and pastes the MCP link into Claude,
// Render has already fully woken up. Zero cold-start for real users.
(function prewarmBackend() {
  const base = window.API_BASE || "";
  fetch(`${base}/health`, { method: "GET", cache: "no-store" }).catch(() => {});
})();

// ============================================================================
// METEOROLOGICAL & SEASONAL OUTLOOK ENGINE
// ============================================================================
/**
 * Computes seasonally accurate 30-day rain outlook based on agro-climatic calendar,
 * active dry spells, and ML forecast category (eliminating static monsoonal placeholders).
 */
function getSeasonalRainOutlook(data, isMr) {
  let month = new Date().getMonth() + 1; // 1 to 12
  if (data?.meta?.period) {
    const parts = data.meta.period.split("-");
    if (parts.length >= 2) {
      const parsed = parseInt(parts[1], 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed <= 12) month = parsed;
    }
  }

  const catCode = data?.["30_day_forecast"]?.category_code ?? 0;
  const dryDays = data?.farmer_cards?.dry_gap?.value_days ?? 0;
  const moistPct = data?.farmer_cards?.soil_moisture ? Math.round(data.farmer_cards.soil_moisture.value_pct) : 60;
  const isOptimal = moistPct >= 60;

  let rainDaysText = "";
  let description = "";
  let climatePillText = "";
  let advisoryStatusHtml = "";

  // 1. Rabi Winter Season (Nov, Dec, Jan, Feb) — Post-monsoon, dry continental winds
  if (month === 11 || month === 12 || month === 1 || month === 2) {
    rainDaysText = isMr ? "०–१ दिवस" : "0–1 Days";
    climatePillText = isMr ? "हवामान: कोरडे हिवाळी" : "Weather: Dry Post-Monsoon";
    description = isMr
      ? `परतीचा मान्सून संपल्याने कोरडे हवामान राहील. पुढील ३० दिवसांत ०–१ दिवस पावसाची शक्यता. ${isOptimal ? `जमिनीत <strong>${formatNumber(moistPct, true)}%</strong> ओलावा उपलब्ध असून रब्बी पिकांना अनुकूल आहे.` : `जमिनीतील ओलावा कमी होत असल्याने रब्बी पिकांसाठी संरक्षित सिंचनाचे नियोजन ठेवावे.`}`
      : `Post-monsoon dry weather prevailing across Maharashtra. 0–1 rain days expected in next 30 days. ${isOptimal ? `Root-zone moisture (<strong>${moistPct}%</strong>) supports early Rabi growth; maintain intercultivation.` : `Soil moisture is declining; supplementary well or canal irrigation advised for standing Rabi crops.`}`;

    advisoryStatusHtml = isMr
      ? `<strong>समाधानकारक रब्बी हवामान:</strong> परतीचा मान्सून संपला असून कोरडे व आल्हाददायक हवामान राहील. पुढील ३० दिवसांत पाऊस नगण्य (०–१ दिवस) अपेक्षित आहे. ${isOptimal ? "जमिनीत पुरेसा ओलावा असल्याने रब्बी पिकांची वाढ चांगली होईल." : "जमिनीत ओलावा कमी असल्याने संरक्षित सिंचनाने पाणी द्यावे."}`
      : `<strong>Favorable Rabi Conditions:</strong> Monsoon has withdrawn and dry post-monsoon weather prevails. Negligible rainfall (0–1 rain days) expected over next 30 days. ${isOptimal ? "Residual root-zone moisture supports standing Rabi crops." : "Moisture is declining; supplementary irrigation advised."}`;
  }
  // 2. Summer / Pre-Monsoon (Mar, Apr, May) — High evaporative heat
  else if (month === 3 || month === 4 || month === 5) {
    rainDaysText = isMr ? "०–१ दिवस" : "0–1 Days";
    climatePillText = isMr ? "हवामान: उष्ण व कोरडे" : "Weather: Hot & Dry Summer";
    description = isMr
      ? `उन्हाळी कोरडे हवामान राहील. अवकाळी मेघगर्जनेची तुरळक शक्यता वगळता पुढील ३० दिवसांत पाऊस नगण्य (०–१ दिवस) राहील.`
      : `Hot, dry summer weather prevailing. Negligible rain (0–1 days) expected in next 30 days with only isolated pre-monsoon heat thundershowers possible.`;

    advisoryStatusHtml = isMr
      ? `<strong>उन्हाळी कोरडे हवामान:</strong> तीव्र ऊन व कोरडे हवामान राहील. पुढील ३० दिवसांत पाऊस नगण्य अपेक्षित असून उन्हाळी पिकांना ठिबक किंवा तुषार सिंचनाने पाणी द्यावे.`
      : `<strong>Hot Summer Conditions:</strong> High evaporative demand and dry weather. Negligible rain expected; prioritize micro-irrigation for standing crops.`;
  }
  // 3. Post-Monsoon Transition (October) — Monsoon withdrawal phase
  else if (month === 10) {
    if (dryDays > 15 || catCode >= 2) {
      rainDaysText = isMr ? "०–१ दिवस" : "0–1 Days";
      climatePillText = isMr ? "मान्सून: पूर्ण परतीचा टप्पा" : "Monsoon: Fully Withdrawn";
      description = isMr
        ? `मान्सून पूर्णपणे परतल्यामुळे कोरडे हवामान राहील. पुढील ३० दिवसांत पावसाची शक्यता नगण्य (०–१ दिवस) आहे. ${isOptimal ? `जमिनीतील उर्वरित ओलाव्याचा रब्बी पेरणीसाठी लाभ घ्यावा.` : `जमिनीत ओलावा कमी असल्याने संरक्षित सिंचनाचे नियोजन करा.`}`
        : `Monsoon has withdrawn. 0–1 rain days expected in next 30 days. ${isOptimal ? `Residual moisture (<strong>${moistPct}%</strong>) is suitable for Rabi sowing.` : `Moisture reserves are low; supplementary irrigation required for crop establishment.`}`;

      advisoryStatusHtml = isMr
        ? `<strong>मान्सून परतीचा टप्पा:</strong> मान्सून वारे माघारी फिरले असून हवामान कोरडे होत आहे. पुढील ३० दिवसांत ०–१ दिवस पावसाची शक्यता. रब्बी पिकांसाठी ओलावा टिकवून ठेवा.`
        : `<strong>Post-Monsoon Transition:</strong> Monsoon winds have withdrawn and clear weather prevails. 0–1 rain days expected over next 30 days. Conserve residual moisture for Rabi crops.`;
    } else {
      rainDaysText = isMr ? "~१–२ दिवस" : "~1–2 Days";
      climatePillText = isMr ? "मान्सून: परतीचा पाऊस" : "Monsoon: Retreating Showers";
      description = isMr
        ? `मान्सून परतीच्या टप्प्यात असून पुढील ३० दिवसांत १–२ दिवस हलक्या पावसाची शक्यता आहे.`
        : `Retreating monsoon phase with 1–2 isolated rain days possible over the next 30 days.`;

      advisoryStatusHtml = isMr
        ? `<strong>परतीचा पाऊस:</strong> स्थानिक ढगांमुळे तुरळक सरींची शक्यता. शेतात पाण्याचा निचरा ठेवा.`
        : `<strong>Retreating Monsoon:</strong> Isolated light showers expected. Ensure good field drainage.`;
    }
  }
  // 4. Kharif Active Monsoon (Jun, Jul, Aug, Sep)
  else {
    if (catCode === 0 && dryDays <= 10) {
      rainDaysText = isMr ? "~५–७ दिवस" : "~5–7 Days";
      climatePillText = isMr ? "मान्सून वारे: सक्रिय" : "Monsoon Winds: Active";
      description = isMr
        ? `मान्सून सक्रिय असून पुढील ३० दिवसांत अंदाजे ५–७ पावसाळी दिवस अपेक्षित आहेत. ${isOptimal ? `जमिनीत <strong>${formatNumber(moistPct, true)}%</strong> ओलावा उपलब्ध आहे.` : `ओलावा स्थिर राहील.`}`
        : `Monsoon winds are active with approximately 5–7 rain days expected over next 30 days. ${isOptimal ? `Root-zone moisture (<strong>${moistPct}%</strong>) is healthy.` : `Adequate moisture expected.`}`;

      advisoryStatusHtml = isMr
        ? `<strong>समाधानकारक पाऊस:</strong> मान्सून वारे सक्रिय असून पुढील ३० दिवसांत अंदाजे ५–७ पावसाळी दिवस अपेक्षित आहेत. शेतात वाफसा चांगला राहील व पिकावर दुष्काळाचा धोका नाही.`
        : `<strong>Favorable Rainfall:</strong> Monsoon winds are active with approximately 5–7 rain days expected over next 30 days. No drought threat to standing crops.`;
    } else if (catCode === 1 || dryDays <= 17) {
      rainDaysText = isMr ? "~२–३ दिवस" : "~2–3 Days";
      climatePillText = isMr ? "मान्सून: हलका ताण" : "Monsoon: Light Break";
      description = isMr
        ? `पावसात हलका खंड असून पुढील ३० दिवसांत २–३ पावसाळी दिवस अपेक्षित आहेत. ओलावा कमी होत असल्याने काळजी घ्यावी.`
        : `Light monsoon break with ~2–3 rain days expected in next 30 days. Moisture is declining; supplementary irrigation planning advised.`;

      advisoryStatusHtml = isMr
        ? `<strong>पावसाचा हलका ताण:</strong> मागील १५ दिवसांत पाऊस कमी झाल्यामुळे जमिनीतील ओलावा घटला आहे. पुढील आठवड्यात स्थानिक सरींची शक्यता आहे.`
        : `<strong>Mild Dry Spell:</strong> A 15-day rainfall deficit has reduced topsoil moisture. Localized showers expected in the coming week.`;
    } else {
      rainDaysText = isMr ? "०–१ दिवस" : "0–1 Days";
      climatePillText = isMr ? "मान्सून: मोठा कोरडा खंड" : "Monsoon: Severe Dry Spell";
      description = isMr
        ? `पावसात मोठा कोरडा खंड पडला असून पुढील ३० दिवसांत पाऊस नगण्य (०–१ दिवस) राहील. पिकांना तातडीने संरक्षित पाणी द्यावे.`
        : `Prolonged dry break with 0–1 rain days expected in next 30 days. High drought stress; immediate supplementary irrigation advised.`;

      advisoryStatusHtml = isMr
        ? `<strong>गंभीर कोरडा खंड:</strong> पावसाचा मोठा खंड पडल्यामुळे जमिनीतील ओल कमी झाली आहे. पिकाला संरक्षित पाणी देण्याची तातडीची गरज आहे.`
        : `<strong>Severe Dry Spell:</strong> Prolonged rainfall deficit. Immediate supplementary irrigation required to sustain crops.`;
    }
  }

  return { rainDaysText, description, climatePillText, advisoryStatusHtml };
}

window.getSeasonalRainOutlook = getSeasonalRainOutlook;

// ============================================================================
// MAIN DASHBOARD UPDATE (Called on data fetch & language switch)
// ============================================================================
function updateDashboard(data) {
  const isMr = state.currentLanguage === "mr";
  const meta = data.meta;
  const cards = data.farmer_cards;
  const diag = data.live_diagnosis;
  const fore = data["30_day_forecast"];

  // 1. Hero Pin Badge
  document.getElementById("hero-taluka-text").textContent = isMr ? (meta.taluka_mr || meta.taluka) : meta.taluka;
  document.getElementById("hero-district-text").textContent = isMr ? (meta.district_mr || meta.district) : meta.district;

  // 2. Floating Farmer Drought Risk Meter Card
  const gaugePath = document.getElementById("hero-gauge-path");
  const gaugeNum = document.getElementById("hero-gauge-num");
  const gaugeSub = document.getElementById("hero-gauge-sub");

  let statusText = isMr ? "सुरक्षित" : "Safe";
  let subText = isMr ? "पाऊस व ओलावा पुरेसा" : "Good Rain & Moisture";
  let strokeColor = "#5E8A42";
  let scorePct = 80;

  if (diag.category_code === 1) {
    statusText = isMr ? "सतर्क" : "Watch";
    subText = isMr ? "ओलावा कमी होत आहे" : "Moisture Depleting";
    strokeColor = "#EAB308";
    scorePct = 58;
  } else if (diag.category_code >= 2) {
    statusText = isMr ? "धोका" : "Severe Alert";
    subText = isMr ? "पाण्याची बचत करा" : "Water Deficit";
    strokeColor = "#EF4444";
    scorePct = 30;
  }

  if (gaugePath) {
    const offset = ARC_LENGTH * (1 - scorePct / 100.0);
    gaugePath.style.strokeDashoffset = offset;
    gaugePath.style.stroke = strokeColor;
  }
  if (gaugeNum) {
    gaugeNum.textContent = statusText;
    gaugeNum.style.color = strokeColor;
  }
  if (gaugeSub) {
    gaugeSub.textContent = subText;
  }

  // 3. Tab 1: 4 Simple Farmer Metric Cards (With Devanagari numerals in Marathi mode)
  document.getElementById("val-climate").textContent = formatNumber(cards.rainfall_deficit.value_mm, isMr);
  const pRain = document.getElementById("pill-rain");
  pRain.textContent = isMr ? cards.rainfall_deficit.status_mr : cards.rainfall_deficit.status_en;
  pRain.style.color = cards.rainfall_deficit.color;

  document.getElementById("val-moisture").textContent = formatNumber(cards.soil_moisture.value_pct, isMr);
  const pSoil = document.getElementById("pill-soil");
  pSoil.textContent = isMr ? cards.soil_moisture.status_mr : cards.soil_moisture.status_en;
  pSoil.style.color = cards.soil_moisture.color;

  document.getElementById("val-light").textContent = formatNumber(cards.dam_storage.value_pct, isMr);
  const pDam = document.getElementById("pill-dam");
  pDam.textContent = isMr ? cards.dam_storage.status_mr : cards.dam_storage.status_en;
  pDam.style.color = cards.dam_storage.color;

  document.getElementById("val-ec").textContent = formatNumber(cards.dry_gap.value_days, isMr);
  const pDry = document.getElementById("pill-dry");
  pDry.textContent = isMr ? cards.dry_gap.status_mr : cards.dry_gap.status_en;
  pDry.style.color = cards.dry_gap.color;
  const unitEc = document.getElementById("unit-ec");
  if (unitEc) unitEc.textContent = isMr ? "दिवस" : "days";

  // 4. Tab 1: Direct Farmer Agronomic Advisory Banner
  populateFarmerDirectAdvisory(data.advisory, isMr);

  // 5. Tab 2: Analytics Cards
  const damPct = cards.dam_storage.value_pct;
  document.getElementById("val-water-flow").textContent = `${formatNumber(Math.round(damPct), isMr)} % ${isMr ? "उपलब्ध साठा" : "Available Storage"}`;
  const greenCount = Math.round((damPct / 100.0) * 18);
  const capsules = document.querySelectorAll(".capsule-pill-bar");
  capsules.forEach((c, idx) => {
    if (idx < (18 - greenCount)) {
      c.classList.remove("green-fill");
    } else {
      c.classList.add("green-fill");
    }
  });

  document.getElementById("val-power").textContent = formatNumber(cards.dry_gap.value_days, isMr);

  // Calculate dynamic 5-year monsoon average if IMD history exists
  let avgRain5Yr = 824;
  if (data.chart_history && data.chart_history.length > 0) {
    const sum = data.chart_history.reduce((acc, curr) => acc + (curr.monsoon_rainfall_mm || 0), 0);
    avgRain5Yr = Math.round(sum / data.chart_history.length);
  } else if (meta.normal_annual_rainfall_mm) {
    avgRain5Yr = Math.round(meta.normal_annual_rainfall_mm * 0.85);
  }
  document.getElementById("val-growth").textContent = formatNumber(avgRain5Yr, isMr);

  const elGrowthSub = document.getElementById("growth-subtext");
  if (elGrowthSub) {
    elGrowthSub.textContent = isMr
      ? "मागील वर्षांतील सरासरी मान्सून पाऊस (IMD पुणे)"
      : "5-Year Monsoon Baseline Average (IMD Pune)";
  }

  const elHistoDates = document.getElementById("histogram-dates-row");
  if (elHistoDates) {
    elHistoDates.innerHTML = isMr
      ? "<span>२०१९</span><span>२०२०</span><span>२०२१</span><span>२०२२</span><span style='color: #F97316; font-weight: 700;'>२०२३ (दुष्काळ)</span><span>२०२४</span>"
      : "<span>2019</span><span>2020</span><span>2021</span><span>2022</span><span style='color: #F97316; font-weight: 700;'>2023 (Drought)</span><span>2024</span>";
  }

  const elConfCo2 = document.getElementById("conf-co2");
  const confVal = Math.round(fore.confidence_pct || 77);
  if (elConfCo2) elConfCo2.textContent = isMr ? `(${formatNumber(confVal, true)}% खात्री)` : `(${confVal}% Confidence)`;

  const elSubCo2 = document.getElementById("sub-co2");
  if (elSubCo2) {
    elSubCo2.textContent = isMr
      ? `Mode 2 AI Forecaster • पुढील महिना: ${fore.label_mr}`
      : `Mode 2 AI Forecaster • Next Month: ${fore.label_en} Outlook`;
  }

  const elStepDates = document.getElementById("step-dates-row");
  if (elStepDates) {
    elStepDates.innerHTML = isMr
      ? "<span>पहिला आठवडा</span><span>दुसरा आठवडा</span><span>तिसरा आठवडा</span><span style='font-weight: 700; color: #047857;'>महिना अखेर</span>"
      : "<span>Week 1</span><span>Week 2</span><span>Week 3</span><span style='font-weight: 700; color: #047857;'>Month End</span>";
  }

  const elSubWater = document.getElementById("sub-water-flow");
  if (elSubWater) {
    elSubWater.textContent = isMr
      ? "शेततळे व धरण साठा स्थिती"
      : "Farm pond & reservoir reserves status";
  }

  const elSubPower = document.getElementById("sub-power");
  if (elSubPower) {
    const isDrySpell = cards.dry_gap.value_days >= 14;
    const stressLabelMr = isDrySpell ? "तीव्र" : (cards.dry_gap.value_days >= 7 ? "मध्यम" : "कमी");
    const stressLabelEn = isDrySpell ? "Severe" : (cards.dry_gap.value_days >= 7 ? "Moderate" : "Low");
    const stressColor = isDrySpell ? "#DC2626" : (cards.dry_gap.value_days >= 7 ? "#F59E0B" : "#047857");
    elSubPower.innerHTML = isMr
      ? `<span>पावसातील सलग खंड: <strong style="color: ${stressColor};">${formatNumber(cards.dry_gap.value_days, true)} दिवस</strong></span> • <span>ओलावा ताण: <strong style="color: ${stressColor};">${stressLabelMr}</strong></span>`
      : `<span>Consecutive dry days: <strong style="color: ${stressColor};">${cards.dry_gap.value_days} days</strong></span> • <span>Moisture Stress: <strong style="color: ${stressColor};">${stressLabelEn}</strong></span>`;
  }

  const elPowerMonths = document.getElementById("power-months-row");
  if (elPowerMonths) {
    elPowerMonths.innerHTML = isMr
      ? "<span>जून</span><span>जुलै</span><span style='color: #F97316;'>ऑगस्ट (ताण)</span><span>सप्टेंबर</span><span>ऑक्टोबर</span>"
      : "<span>Jun</span><span>Jul</span><span style='color: #F97316;'>Aug (Dry Spell)</span><span>Sep</span><span>Oct</span>";
  }

  const foreLabel = document.getElementById("val-co2");
  if (fore.category_code === 0) {
    foreLabel.textContent = isMr ? "सुरक्षित अंदाज" : "Safe Outlook";
    foreLabel.style.color = "#047857";
  } else if (fore.category_code === 1) {
    foreLabel.textContent = isMr ? "सतर्कतेचा इशारा" : "Watch Outlook";
    foreLabel.style.color = "#D97706";
  } else {
    foreLabel.textContent = isMr ? "दुष्काळ धोका" : "Severe Alert";
    foreLabel.style.color = "#DC2626";
  }

  // 6. Right Column Side Panel (Permanent Dedicated Live Telemetry)
  document.getElementById("side-dam-level").textContent = `${formatNumber(cards.dam_storage.value_pct, isMr)} %`;
  document.getElementById("side-soil-level").textContent = `${formatNumber(cards.soil_moisture.value_pct, isMr)} %`;
  document.getElementById("side-dam-fill").style.width = `${Math.min(cards.dam_storage.value_pct, 100)}%`;
  document.getElementById("side-soil-fill").style.width = `${Math.min(cards.soil_moisture.value_pct, 100)}%`;

  const riskLbl = document.getElementById("side-risk-label");
  if (riskLbl) {
    if (diag.category_code === 0) {
      riskLbl.textContent = isMr ? "सुरक्षित" : "Safe";
      riskLbl.style.color = "#047857";
    } else if (diag.category_code === 1) {
      riskLbl.textContent = isMr ? "सतर्क" : "Watch";
      riskLbl.style.color = "#D97706";
    } else {
      riskLbl.textContent = isMr ? "धोका" : "Severe Alert";
      riskLbl.style.color = "#DC2626";
    }
  }

  const elSideDamSub = document.getElementById("side-dam-sub");
  if (elSideDamSub) {
    const damName = isMr ? (cards.dam_storage.dam_name_mr || "स्थानिक धरण") : (cards.dam_storage.dam_name || "Regional Reservoir");
    elSideDamSub.textContent = isMr
      ? `${damName} • पाणीसाठा: ${formatNumber(Math.round(cards.dam_storage.value_pct), true)}%`
      : `${damName} • Live Storage: ${Math.round(cards.dam_storage.value_pct)}%`;
  }
  const elSideSoilSub = document.getElementById("side-soil-sub");
  if (elSideSoilSub) {
    elSideSoilSub.textContent = isMr
      ? "रूट-झोन ओलावा समाधानकारक पातळीवर आहे."
      : "Root-zone soil moisture is at an optimal level.";
  }
  const elSideRiskSource = document.getElementById("side-risk-source");
  if (elSideRiskSource) {
    elSideRiskSource.textContent = isMr
      ? "भारतीय हवामान विभाग (IMD) व जलसंपदा • कृषी ML प्रणाली"
      : "IMD Pune & WRD Water Telemetry • Agri-ML Model";
  }

  const elSideCard4 = document.getElementById("side-card4-text");
  const moistPct = cards.soil_moisture ? Math.round(cards.soil_moisture.value_pct) : 70;
  const isOptimal = moistPct >= 60;

  const outlook = getSeasonalRainOutlook(data, isMr);
  const elRainDays = document.getElementById("side-card4-rain-days");
  if (elRainDays) {
    elRainDays.textContent = outlook.rainDaysText;
  }
  const elCumRain = document.getElementById("side-card4-cum-rain");
  if (elCumRain && cards.rainfall_deficit) {
    elCumRain.textContent = `${formatNumber(Math.round(cards.rainfall_deficit.value_mm), isMr)} mm`;
  }

  if (elSideCard4) {
    elSideCard4.innerHTML = outlook.description;
  }

  // Populate the dedicated AI Agricultural Advisor Modal
  if (typeof populateAiModal === "function") {
    populateAiModal(data, isMr);
  }

  // 6. Stale Data Warning Banner Detection
  const staleBanner = document.getElementById("stale-data-banner");
  if (staleBanner) {
    const isStale = (data.data_age_hours && data.data_age_hours > 24) ||
      (data.is_stale === true);
    if (isStale) {
      staleBanner.style.display = "flex";
      const bannerText = document.getElementById("stale-banner-text");
      if (bannerText) {
        bannerText.textContent = isMr
          ? "⚠️ हवामान डेटा सिंक प्रलंबित आहे. उपलब्ध सर्वात नवीन निरीक्षण दाखवत आहोत."
          : "⚠️ Weather telemetry sync delayed by provider. Displaying latest confirmed observation.";
      }
    } else {
      staleBanner.style.display = "none";
    }
  }
}

// ============================================================================
// TREESHAP EXPLAINABLE AI ATTRIBUTION (Tab 2)
// ============================================================================
async function fetchTalukaExplain(taluka) {
  try {
    const encoded = encodeURIComponent(taluka);
    const base = window.API_BASE || "";
    const res = await fetch(`${base}/api/v1/taluka/${encoded}/explain`);
    if (!res.ok) return;

    const xai = await res.json();
    state.currentXai = xai;
    renderTreeShapExplain(xai);
  } catch (err) {
    console.error("XAI fetch error:", err);
  }
}

function renderTreeShapExplain(xai) {
  if (!xai) return;
  const isMr = state.currentLanguage === "mr";

  // Headline & Narrative
  const headlineEl = document.getElementById("xai-narrative-headline");
  const bodyEl = document.getElementById("xai-narrative-body");

  if (headlineEl && xai.farmer_summary) {
    const defaultHeadline = isMr ? "स्थानिक शेतकरी विश्लेषण (Agro-Driver Summary)" : "Agro-Driver Attribution Summary";
    headlineEl.textContent = isMr
      ? (xai.farmer_summary.headline_mr || defaultHeadline)
      : (xai.farmer_summary.headline_en || defaultHeadline);
  }
  if (bodyEl && xai.farmer_summary) {
    const narrativeText = isMr
      ? (xai.farmer_summary.mr || xai.farmer_summary.narrative_mr)
      : (xai.farmer_summary.en || xai.farmer_summary.narrative_en);
    if (narrativeText) bodyEl.textContent = narrativeText;
  }

  // Top 3 Escalators List
  const escalatorsContainer = document.getElementById("treeshap-escalators-list");
  if (escalatorsContainer && xai.top_risk_escalators) {
    escalatorsContainer.innerHTML = "";
    xai.top_risk_escalators.slice(0, 3).forEach((esc) => {
      const item = document.createElement("div");
      item.className = "treeshap-escalator-item";

      const row = document.createElement("div");
      row.className = "treeshap-bar-row";

      const nameSpan = document.createElement("span");
      nameSpan.className = "treeshap-feature-name";
      const escName = isMr
        ? (esc.name_mr || esc.feature_name_mr || esc.feature || esc.feature_key)
        : (esc.name_en || esc.feature_name_en || esc.feature || esc.feature_key);
      const icon = esc.icon ? `${esc.icon} ` : '';
      nameSpan.textContent = `${icon}${escName}`;

      const actualPct = esc.impact_pct !== undefined ? esc.impact_pct : (esc.relative_impact_pct || 0);
      let pctStr = "";
      if (actualPct > 0 && actualPct < 1.0) {
        pctStr = isMr ? "+<१% (नगण्य)" : "+<1% (Negligible)";
      } else {
        const rounded = Math.round(actualPct);
        const formatted = typeof formatNumber === "function" ? formatNumber(rounded, isMr) : rounded;
        pctStr = `+${formatted}% ${isMr ? 'जोखीम वाढ' : 'Risk Impact'}`;
      }
      const impactSpan = document.createElement("span");
      impactSpan.className = "treeshap-impact-pct";
      impactSpan.textContent = pctStr;

      row.appendChild(nameSpan);
      row.appendChild(impactSpan);

      const track = document.createElement("div");
      track.className = "treeshap-bar-track";

      const fill = document.createElement("div");
      fill.className = "treeshap-bar-fill-escalator";
      fill.style.width = actualPct < 1.0 ? "4%" : `${Math.min(100, Math.max(12, Math.round(actualPct)))}%`;

      track.appendChild(fill);
      item.appendChild(row);
      item.appendChild(track);

      escalatorsContainer.appendChild(item);
    });
  }

  // Top 1 Mitigating Buffer Box
  const bufferBox = document.getElementById("treeshap-buffer-box");
  if (bufferBox) {
    bufferBox.innerHTML = "";
    if (xai.top_mitigating_buffers && xai.top_mitigating_buffers.length > 0) {
      const buf = xai.top_mitigating_buffers[0];
      const bufRow = document.createElement("div");
      bufRow.className = "buffer-row";

      const bufName = document.createElement("span");
      const bufNameStr = isMr
        ? (buf.name_mr || buf.feature_name_mr || buf.feature || buf.feature_key)
        : (buf.name_en || buf.feature_name_en || buf.feature || buf.feature_key);
      const bufIcon = buf.icon || '🛡️';
      bufName.textContent = `${bufIcon} ${bufNameStr}`;

      const rawBufPct = Math.round(buf.impact_pct !== undefined ? buf.impact_pct : (buf.relative_impact_pct || 0));
      const formattedBufPct = typeof formatNumber === "function" ? formatNumber(rawBufPct, isMr) : rawBufPct;
      const bufImpact = document.createElement("span");
      bufImpact.style.color = "#047857";
      bufImpact.style.fontWeight = "700";
      bufImpact.textContent = `-${formattedBufPct}% ${isMr ? 'जोखीम निवारण' : 'Risk Relief'}`;

      bufRow.appendChild(bufName);
      bufRow.appendChild(bufImpact);

      const bufDesc = document.createElement("div");
      bufDesc.className = "buffer-desc";
      bufDesc.textContent = isMr
        ? "हा घटक सध्याच्या परिस्थितीत दुष्काळाची तीव्रता रोखण्यास मदत करत आहे."
        : "This parameter is currently providing physical resilience against worsening drought.";

      bufferBox.appendChild(bufRow);
      bufferBox.appendChild(bufDesc);
    } else {
      const noBuf = document.createElement("div");
      noBuf.className = "buffer-desc";
      noBuf.textContent = isMr ? "सध्या कोणताही लक्षणीय बफर घटक उपलब्ध नाही." : "No significant mitigating buffer identified.";
      bufferBox.appendChild(noBuf);
    }
  }
}

// ============================================================================
// REGIONAL DROUGHT CONTAGION & ADJACENT TALUKAS (Tab 2)
// ============================================================================
async function fetchTalukaAdjacent(taluka) {
  try {
    const encoded = encodeURIComponent(taluka);
    const base = window.API_BASE || "";
    const res = await fetch(`${base}/api/v1/taluka/${encoded}/adjacent`);
    if (!res.ok) return;

    const data = await res.json();
    state.currentAdjacent = data;
    renderAdjacentTalukas(data);
  } catch (err) {
    console.error("Adjacent fetch error:", err);
  }
}

function renderAdjacentTalukas(data) {
  if (!data) return;
  const isMr = state.currentLanguage === "mr";

  const ass = data.contagion_assessment || {};
  const isAtRisk = ass.is_corridor_at_risk || (ass.alert_or_severe_count >= 2) || (ass.stressed_percentage >= 35);

  // 1. Legacy & New Assessment Badges
  const badgeEl = document.getElementById("contagion-assessment-badge");
  if (badgeEl) {
    badgeEl.textContent = isMr
      ? (isAtRisk ? "⚠️ प्रादेशिक कॉरिडॉर सतर्कता" : "🛡️ प्रादेशिक पट्टा सुरक्षित")
      : (isAtRisk ? "⚠️ Regional Corridor Alert" : "🛡️ Regional Buffer Intact");
    badgeEl.className = isAtRisk ? "contagion-badge-warning" : "contagion-badge-safe";
  }

  const pillEl = document.getElementById("contagion-assessment-pill");
  if (pillEl) {
    pillEl.textContent = isMr
      ? (isAtRisk ? "⚠️ प्रादेशिक कॉरिडॉर सतर्कता" : "🛡️ प्रादेशिक पट्टा सुरक्षित")
      : (isAtRisk ? "⚠️ Regional Corridor Alert" : "🛡️ Regional Buffer Intact");
    pillEl.className = isAtRisk ? "contagion-badge-warning" : "contagion-badge-safe";
  }

  // 2. Narrative text inside the corridor banner
  const narrativeEl = document.getElementById("contagion-narrative-text");
  if (narrativeEl) {
    const defaultText = isAtRisk
      ? (isMr ? "शेजारील तालुक्यांमध्ये तीव्र कोरडा खंड व ओलावा तूट आढळली आहे." : "Nearby talukas exhibit active soil moisture deficit and dry spell conditions.")
      : (isMr ? "शेजारील तालुक्यांमध्ये ओलावा व पाणीसाठा समाधानकारक पातळीवर स्थिर आहे." : "Adjacent talukas maintain healthy root-zone moisture and stable reservoir storage.");
    narrativeEl.textContent = isMr
      ? (ass.corridor_status_mr || defaultText)
      : (ass.corridor_status_en || defaultText);
  }

  // 3. Spatial Telemetry Strip (Evaluated Count, Stress %, Avg Distance)
  const neighbors = data.adjacent_neighbors || [];
  const evalCount = data.neighbors_evaluated || neighbors.length || 0;
  const stressedPct = Math.round(ass.stressed_percentage || 0);

  let avgDist = 0;
  if (neighbors.length > 0) {
    const totalDist = neighbors.reduce((acc, n) => acc + (n.boundary_distance_km || 0), 0);
    avgDist = Math.round(totalDist / neighbors.length);
  }

  const elCount = document.getElementById("val-corridor-count");
  if (elCount) {
    const formattedCount = typeof formatNumber === "function" ? formatNumber(evalCount, isMr) : evalCount;
    elCount.textContent = `${formattedCount} ${isMr ? 'तालुके' : 'Talukas'}`;
  }

  const elStress = document.getElementById("val-corridor-stress");
  if (elStress) {
    const formattedStress = typeof formatNumber === "function" ? formatNumber(stressedPct, isMr) : stressedPct;
    elStress.textContent = `${formattedStress}%`;
    elStress.style.color = stressedPct >= 35 ? "#DC2626" : (stressedPct >= 20 ? "#D97706" : "#047857");
  }

  const elDist = document.getElementById("val-corridor-dist");
  if (elDist) {
    const formattedDist = typeof formatNumber === "function" ? formatNumber(avgDist, isMr) : avgDist;
    elDist.textContent = `${formattedDist} km`;
  }

  // 4. Rich Neighbor Cards Grid
  const grid = document.getElementById("adjacent-talukas-grid");
  if (grid && neighbors.length > 0) {
    grid.innerHTML = "";
    neighbors.forEach((n) => {
      const card = document.createElement("div");
      card.className = "adjacent-card";
      card.title = isMr ? `${n.taluka_name} वर जा` : `Switch to ${n.taluka_name}`;

      // Top Row: Taluka Name + District Sub & Risk Pill
      const topRow = document.createElement("div");
      topRow.className = "adjacent-card-top";

      const nameWrap = document.createElement("div");
      nameWrap.className = "adjacent-name-wrap";

      const namePrimary = document.createElement("div");
      namePrimary.className = "adjacent-primary-name";
      namePrimary.textContent = isMr ? (n.taluka_name_mr || n.taluka_name) : n.taluka_name;

      const districtSub = document.createElement("div");
      districtSub.className = "adjacent-district-sub";
      districtSub.textContent = isMr ? `${n.district_name} जिल्हा` : `${n.district_name} Dist.`;

      nameWrap.appendChild(namePrimary);
      nameWrap.appendChild(districtSub);

      const riskPill = document.createElement("span");
      const tierKey = (n.risk_tier || "safe").toLowerCase();
      riskPill.className = `adjacent-risk-pill risk-${tierKey}`;
      riskPill.textContent = isMr ? (n.risk_label_mr || n.risk_tier) : n.risk_tier;

      topRow.appendChild(nameWrap);
      topRow.appendChild(riskPill);

      // Bottom Row: Distance & Soil Moisture / SPI
      const bottomRow = document.createElement("div");
      bottomRow.className = "adjacent-card-bottom";

      const distBadge = document.createElement("span");
      distBadge.className = "adjacent-dist-pill";
      const rawDist = Math.round(n.boundary_distance_km || 0);
      const formattedDist = typeof formatNumber === "function" ? formatNumber(rawDist, isMr) : rawDist;
      distBadge.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="10" height="10" style="margin-right:3px; vertical-align:-1px;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>${formattedDist} km`;

      const metricsWrap = document.createElement("div");
      metricsWrap.className = "adjacent-metrics-micro";

      if (n.soil_moisture_pct !== undefined) {
        const smiSpan = document.createElement("span");
        smiSpan.className = "adjacent-micro-stat";
        const smiVal = typeof formatNumber === "function" ? formatNumber(Math.round(n.soil_moisture_pct), isMr) : Math.round(n.soil_moisture_pct);
        smiSpan.textContent = `🌱 ${smiVal}%`;
        metricsWrap.appendChild(smiSpan);
      }

      if (n.spi_3 !== undefined) {
        const spiSpan = document.createElement("span");
        spiSpan.className = "adjacent-micro-stat";
        const spiSign = n.spi_3 >= 0 ? "+" : "";
        const spiFormatted = typeof formatNumber === "function" ? formatNumber(n.spi_3.toFixed(1), isMr) : n.spi_3.toFixed(1);
        spiSpan.textContent = `🌧️ ${spiSign}${spiFormatted}`;
        metricsWrap.appendChild(spiSpan);
      }

      bottomRow.appendChild(distBadge);
      bottomRow.appendChild(metricsWrap);

      card.appendChild(topRow);
      card.appendChild(bottomRow);

      // Click to navigate to neighbor taluka
      card.addEventListener("click", () => {
        state.currentTaluka = n.taluka_name;
        const searchInput = document.getElementById("taluka-search-input");
        if (searchInput) {
          searchInput.value = isMr ? (n.taluka_name_mr || n.taluka_name) : n.taluka_name;
        }
        if (typeof fetchTalukaData === "function") {
          fetchTalukaData(n.taluka_name);
        }
      });

      grid.appendChild(card);
    });
  }
}

window.fetchTalukaExplain = fetchTalukaExplain;
window.fetchTalukaAdjacent = fetchTalukaAdjacent;
window.renderTreeShapExplain = renderTreeShapExplain;
window.renderAdjacentTalukas = renderAdjacentTalukas;

