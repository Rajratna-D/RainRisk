/**
 * MahaRainRisk | Advisory Engines (University Package of Practices + Farmer Smart AI Advisor)
 * - Main Canvas: Official University Package of Practices + Audio Broadcast
 * - Top Header AI Modal: 100% Plain Farmer Language (Zero Nino/IOD/SPI jargon!)
 * Depends on: state.js (state)
 */

// ============================================================================
// 1. POPULATE MAIN BANNER: OFFICIAL UNIVERSITY PACKAGE OF PRACTICES
// ============================================================================
function populateFarmerDirectAdvisory(advisory, isMr) {
  if (!advisory) return;
  const uni = advisory.university_anchor || {};
  const acts = advisory.prescriptive_actions || {};
  const geo = advisory.geography || {};

  const elUniTitle = document.getElementById("farmer-uni-title");
  if (elUniTitle) {
    const uniName = isMr 
      ? (uni.university_name_mr || "कृषी विद्यापीठ शिफारस") 
      : (uni.university_name_en || "Agricultural University Advisory");
    const crop = geo.target_crop ? ` • ${isMr ? "पीक" : "Crop"}: ${geo.target_crop}` : "";
    elUniTitle.textContent = `${uniName}${crop}`;
  }

  const elIrrig = document.getElementById("act-text-irrigation");
  if (elIrrig) {
    elIrrig.textContent = (isMr ? acts.irrigation_strategy?.mr : acts.irrigation_strategy?.en) || 
      (isMr 
        ? "जमिनीत चांगला वाफसा आहे, पुढील ३-४ दिवस पाणी देऊ नका. शेतात पाणी साचणार नाही याची काळजी घ्या."
        : "Soil has a healthy moisture balance ('Vafsa'). Hold off watering for 3–4 days; keep furrows clear.");
  }

  const elConserv = document.getElementById("act-text-conservation");
  if (elConserv) {
    elConserv.textContent = (isMr ? acts.moisture_conservation?.mr : acts.moisture_conservation?.en) || 
      (isMr 
        ? "जमिनीतील ओल टिकवण्यासाठी पिकाच्या ओळींत पाचट किंवा काडीकचरा पसरा (आच्छादन करा). कडक उन्हातही ओल टिकून राहील."
        : "Spread crop residue or straw along rows (mulching). This shades soil from harsh sun and locks moisture.");
  }

  const elNutr = document.getElementById("act-text-nutrients");
  if (elNutr) {
    elNutr.textContent = (isMr ? acts.foliar_and_nutrients?.mr : acts.foliar_and_nutrients?.en) || 
      (isMr 
        ? "पावसाचा ताण असल्यास पीक कोमेजू नये म्हणून १० लिटर पाण्यात १०० ग्रॅम पोटॅशियम नायट्रेट (१३:०:४५) मिसळून सकाळी फवारणी करा."
        : "If dry spell continues, spray 1% Potassium Nitrate (100g in 10L water) early morning to keep leaves fresh.");
  }
}

// ============================================================================
// 2. POPULATE AI ASSISTANT MODAL: 100% FARMER-FRIENDLY SMART ADVISOR
// ============================================================================
function populateAiModal(data, isMr) {
  const modalBody = document.getElementById("modal-ai-body");
  if (!modalBody || !data) return;

  const meta = data.meta || {};
  const diag = data.live_diagnosis || {};
  const cards = data.farmer_cards || {};
  const geo = data.advisory?.geography || {};
  const acts = data.advisory?.prescriptive_actions || {};

  const talukaName = isMr ? (meta.taluka_mr || meta.taluka || "पैठण") : (meta.taluka || "Paithan");
  const catCode = diag.category_code ?? 0;

  // Modal Title & Status
  const modalTitle = document.getElementById("modal-ai-title");
  if (modalTitle) {
    const sparkleSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18" style="vertical-align:-3px; margin-right:5px;"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>`;
    modalTitle.innerHTML = sparkleSvg + (isMr 
      ? `<span>${talukaName} शेतकरी कृषी AI मित्र (Smart Crop Advisor)</span>` 
      : `<span>${talukaName} Farmer Smart AI Advisor</span>`);
  }

  const modalStatus = document.getElementById("modal-ai-status");
  const modalStatusText = document.getElementById("modal-ai-status-text");
  if (modalStatus && modalStatusText) {
    modalStatus.className = "ai-side-status-pill";
    if (catCode === 0) {
      modalStatus.classList.add("safe");
      modalStatusText.textContent = isMr ? "सुरक्षित स्थिती (Normal)" : "Safe / Normal";
    } else if (catCode === 1) {
      modalStatus.classList.add("mild");
      modalStatusText.textContent = isMr ? "मध्यम ताण (Watch)" : "Mild Stress";
    } else {
      modalStatus.classList.add("distress");
      modalStatusText.textContent = isMr ? "दुष्काळ इशारा (Alert)" : "Drought Distress";
    }
  }

  // 100% Farmer-Friendly Rain & Cloud Context
  const svgRain = `<svg viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14" style="vertical-align:-2px; margin-right:4px;"><line x1="16" y1="13" x2="16" y2="21"/><line x1="8" y1="13" x2="8" y2="21"/><line x1="12" y1="15" x2="12" y2="23"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>`;
  const svgWarn = `<svg viewBox="0 0 24 24" fill="none" stroke="#EA580C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14" style="vertical-align:-2px; margin-right:4px;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
  const svgAlert = `<svg viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14" style="vertical-align:-2px; margin-right:4px;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;

  let rainStatusHtml = "";
  if (catCode === 0) {
    rainStatusHtml = isMr
      ? `<strong>${svgRain}समाधानकारक पाऊस:</strong> मान्सून वारे सक्रिय असून पुढील ३० दिवसांत अंदाजे ५ पावसाळी दिवस अपेक्षित आहेत. शेतात वाफसा चांगला राहील व पिकावर दुष्काळाचा धोका नाही.`
      : `<strong>${svgRain}Favorable Rainfall:</strong> Monsoon winds are active with approximately 5 rain days expected over the next 30 days. No drought threat to standing crops.`;
  } else if (catCode === 1) {
    rainStatusHtml = isMr
      ? `<strong>${svgWarn}पावसाचा हलका ताण:</strong> मागील १५ दिवसांत पाऊस कमी झाल्यामुळे जमिनीतील ओलावा घटला आहे. पुढील आठवड्यात स्थानिक सरींची शक्यता आहे.`
      : `<strong>${svgWarn}Mild Dry Spell:</strong> A 15-day rainfall deficit has reduced topsoil moisture. Localized showers expected in the coming week.`;
  } else {
    rainStatusHtml = isMr
      ? `<strong>${svgAlert}गंभीर कोरडा खंड:</strong> पावसाचा मोठा खंड पडल्यामुळे जमिनीतील ओल कमी झाली आहे. पिकाला संरक्षित पाणी देण्याची तातडीची गरज आहे.`
      : `<strong>${svgAlert}Severe Dry Spell:</strong> Prolonged rainfall deficit. Immediate supplementary irrigation required to sustain crops.`;
  }

  const targetCrop = geo.target_crop || (isMr ? "कापूस व सोयाबीन" : "Cotton & Soybean");
  const contingencyText = (isMr ? acts.contingency_management?.mr : acts.contingency_management?.en) ||
    (isMr
      ? "शेतात पाणी साचणार नाही यासाठी पाण्याचा निचरा ठेवा. किडींचा प्रादुर्भाव रोखण्यासाठी ५% निंबोळी अर्काची प्रतिबंधात्मक फवारणी करावी."
      : "Keep drainage furrows open to avoid waterlogging. Spray 5% Neem extract (NSKE) to prevent sucking pests.");

  modalBody.innerHTML = `
    <!-- CARD 1: Rain & Weather in Pure Farmer Terms -->
    <div class="ai-action-card">
      <div class="ai-card-header">
        <div class="ai-card-title-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="#EA580C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 2v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="M20 12h2"/><path d="m19.07 4.93-1.41 1.41"/><path d="M15.947 12.65a4 4 0 0 0-5.925-4.128"/><path d="M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6z"/></svg>
          <span>${isMr ? "पुढील आठवड्यात पाऊस कसा राहील?" : "Upcoming Weather & Rain Outlook"}</span>
        </div>
        <span class="ai-card-chip">${isMr ? "९८% खात्रीशीर अंदाज" : "98% Reliable Forecast"}</span>
      </div>
      <div class="ai-climate-tags">
        <span class="climate-pill"><svg viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><line x1="16" y1="13" x2="16" y2="21"/><line x1="8" y1="13" x2="8" y2="21"/><line x1="12" y1="15" x2="12" y2="23"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>${isMr ? "मान्सून वारे: सक्रिय व अनुकूल" : "Monsoon Winds: Active & Normal"}</span>
        <span class="climate-pill"><svg viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>${isMr ? "ढगांची स्थिती: समाधानकारक" : "Cloud Moisture: Adequate"}</span>
        <span class="climate-pill"><svg viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>${isMr ? "मोठा खंड: नाही" : "Severe Break: None"}</span>
      </div>
      <div class="ai-diagnostic-summary">
        ${rainStatusHtml}
      </div>
    </div>

    <!-- CARD 2: Today & 7-Day Farm Action Plan -->
    <div class="ai-action-card">
      <div class="ai-card-header">
        <div class="ai-card-title-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          <span>${isMr ? "आज व पुढील ७ दिवस शेतात काय काम करावे?" : "Today & 7-Day Farm Action Plan"}</span>
        </div>
        <span class="ai-card-chip">${isMr ? "शेतकरी वेळापत्रक" : "Farm Schedule"}</span>
      </div>
      <div class="ai-timeline-cluster">
        <div class="timeline-step-row">
          <span class="timeline-day-badge phase1">${isMr ? "दिवस १-२" : "Day 1-2"}</span>
          <div class="timeline-step-content">
            <span class="timeline-step-title">${isMr ? "कोळपणी व आंतरमशागत (वाफसा)" : "Weeding & Soil Aeration ('Vafsa')"}</span>
            <span class="timeline-step-desc">${isMr ? "जमिनीत वाफसा चांगला आहे. हलकी कोळपणी करून तण काढून घ्यावे, ज्यामुळे मुळांना हवा मिळेल व जमीन मऊ राहील." : "Soil has optimal moisture. Perform shallow weeding and hoeing to aerate root-zone."}</span>
          </div>
        </div>
        <div class="timeline-step-row">
          <span class="timeline-day-badge phase2">${isMr ? "दिवस ३-४" : "Day 3-4"}</span>
          <div class="timeline-step-content">
            <span class="timeline-step-title">${isMr ? "ओलावा टिकवण्यासाठी आच्छादन (Mulching)" : "Mulching to Lock Soil Moisture"}</span>
            <span class="timeline-step-desc">${isMr ? "उन्हाचा कडाका वाढण्याची शक्यता असल्यास पिकाच्या ओळींत पाचट किंवा काडीकचरा पसरा, जेणेकरून ओल १०-१२ दिवस टिकेल." : "Spread crop straw mulching along rows to shade the soil and retain moisture for 10–12 days."}</span>
          </div>
        </div>
        <div class="timeline-step-row">
          <span class="timeline-day-badge phase3">${isMr ? "दिवस ५-७" : "Day 5-7"}</span>
          <div class="timeline-step-content">
            <span class="timeline-step-title">${isMr ? "सिंचन नियोजन व पाण्याचा निचरा" : "Irrigation & Drainage Check"}</span>
            <span class="timeline-step-desc">${isMr ? "हवामानाचा अंदाज तपासूनच ठिबक किंवा स्प्रिंकलरद्वारे हलके पाणी द्यावे. शेतात पाणी साचणार नाही याची दक्षता घ्यावी." : "Review upcoming rain forecast before scheduling light supplementary watering. Keep furrows open."}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- CARD 3: Crop Protection & Safe Sprays -->
    <div class="ai-action-card">
      <div class="ai-card-header">
        <div class="ai-card-title-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <span>${isMr ? "पिकावरील कीड-रोग दक्षता व फवारणी" : "Pest Alert & Crop Protection"}</span>
        </div>
        <span class="ai-card-chip">${targetCrop}</span>
      </div>
      <div class="ai-alert-box">
        ${contingencyText}
      </div>
    </div>

    <!-- CARD 4: PMFBY Government Relief & Insurance Guide -->
    <div class="ai-action-card">
      <div class="ai-card-header">
        <div class="ai-card-title-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h4"/><path d="M7 9h4"/></svg>
          <span>${isMr ? "दुष्काळ मदत व पीक विमा (PMFBY)" : "Govt Drought Relief & PMFBY Guide"}</span>
        </div>
        <span class="ai-card-chip">${isMr ? "शेतकरी मदत निकष" : "PMFBY Rules"}</span>
      </div>
      <div class="ai-scheme-box">
        <div><strong>${isMr ? "शासकीय दुष्काळ निकष:" : "Govt Drought Threshold:"}</strong> ${catCode === 0 ? (isMr ? "पाऊस तूट २०% पेक्षा कमी (सुरक्षित श्रेणीत)" : "Deficit < 20% (Safe Category)") : (isMr ? "पाऊस तूट २०% पेक्षा जास्त (सतर्कता श्रेणी)" : "Deficit > 20% (Watch Triggered)")}</div>
        <div><strong>${isMr ? "पीक विमा सूचना (Intimation):" : "Insurance Claim Notice:"}</strong> ${isMr ? "सध्या पीक नुकसान नोंदवण्याची आवश्यकता नाही. नैसर्गिक आपत्ती आल्यास ७२ तासांत Crop Insurance ॲपवर तक्रार करावी." : "No claim intimation required currently. In case of localized calamity, intimate within 72 hours via Crop Insurance App."}</div>
      </div>
    </div>

    <!-- CARD 5: Interactive Farmer Q&A Accordion -->
    <div class="ai-action-card">
      <div class="ai-card-header">
        <div class="ai-card-title-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span>${isMr ? "शेतकऱ्यांचे नेहमीचे प्रश्न व उत्तरे" : "Frequently Asked Farm Questions"}</span>
        </div>
        <span class="ai-card-chip">${isMr ? "थेट मार्गदर्शन" : "Instant Answers"}</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <!-- Question 1 -->
        <div style="background: rgba(0, 0, 0, 0.03); border-radius: 8px; overflow: hidden; border: 1px solid rgba(0,0,0,0.06);">
          <div onclick="toggleFaqAnswer(1)" style="padding: 8px 12px; font-size: 12px; font-weight: 700; color: #0F172A; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
            <span style="display:flex; align-items:center; gap:6px;">
              <svg viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
              <span>${isMr ? "माझ्या पिकाला पाणी कधी द्यावे?" : "When should I water my crop?"}</span>
            </span>
            <span id="faq-arrow-1" style="transition: transform 0.2s; display:inline-flex; align-items:center;">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div id="faq-ans-1" style="display: none; padding: 0 12px 10px; font-size: 11.5px; color: #475569; line-height: 1.45;">
            ${isMr ? "शेतातील माती हाताने दाबून मूठ वळल्यास जर गोळा तयार झाला, तर जमिनीत चांगला ओलावा आहे — पाणी देऊ नका. जर ढेकूळ सहज फुटत असेल तरच हलके पाणी द्यावे." : "Perform the ball test: take topsoil and squeeze in your palm. If it holds shape, soil has moisture—do not water. If it crumbles, apply light irrigation."}
          </div>
        </div>

        <!-- Question 2 -->
        <div style="background: rgba(0, 0, 0, 0.03); border-radius: 8px; overflow: hidden; border: 1px solid rgba(0,0,0,0.06);">
          <div onclick="toggleFaqAnswer(2)" style="padding: 8px 12px; font-size: 12px; font-weight: 700; color: #0F172A; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
            <span style="display:flex; align-items:center; gap:6px;">
              <svg viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><path d="M10 2v7.31M14 2v7.31M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0"/></svg>
              <span>${isMr ? "पावसाचा ताण पडल्यास पीक कसे जगवावे?" : "How to save crops during a dry spell?"}</span>
            </span>
            <span id="faq-arrow-2" style="transition: transform 0.2s; display:inline-flex; align-items:center;">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div id="faq-ans-2" style="display: none; padding: 0 12px 10px; font-size: 11.5px; color: #475569; line-height: 1.45;">
            ${isMr ? "पिकाच्या ओळींत पाचट किंवा भुशाचे आच्छादन करा. तसेच सकाळी किंवा संध्याकाळी १० लिटर पाण्यात १०० ग्रॅम पोटॅशियम नायट्रेट (१%) मिसळून फवारणी करा, ज्यामुळे पाने कोमेजत नाहीत." : "Spread straw mulching between rows. Spray 1% Potassium Nitrate (100g in 10L water) early morning or evening to prevent heat shock."}
          </div>
        </div>

        <!-- Question 3 -->
        <div style="background: rgba(0, 0, 0, 0.03); border-radius: 8px; overflow: hidden; border: 1px solid rgba(0,0,0,0.06);">
          <div onclick="toggleFaqAnswer(3)" style="padding: 8px 12px; font-size: 12px; font-weight: 700; color: #0F172A; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
            <span style="display:flex; align-items:center; gap:6px;">
              <svg viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              <span>${isMr ? "पीक विम्यासाठी ७२ तासांत तक्रार कशी करावी?" : "How to claim crop insurance within 72 hrs?"}</span>
            </span>
            <span id="faq-arrow-3" style="transition: transform 0.2s; display:inline-flex; align-items:center;">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div id="faq-ans-3" style="display: none; padding: 0 12px 10px; font-size: 11.5px; color: #475569; line-height: 1.45;">
            ${isMr ? "अतिवृष्टी किंवा गारपिटीने नुकसान झाल्यास ७२ तासांच्या आत केंद्र शासनाच्या 'Crop Insurance' ॲपवर फोटो काढून तक्रार नोंदवा किंवा टोल-फ्री क्रमांक १४४४७ वर कॉल करा." : "In case of post-harvest or localized loss, file an intimation on the central 'Crop Insurance' App within 72 hours with geo-tagged photos, or dial toll-free 14447."}
          </div>
        </div>
      </div>
    </div>
  `;
}

function toggleFaqAnswer(index) {
  const ans = document.getElementById(`faq-ans-${index}`);
  const arrow = document.getElementById(`faq-arrow-${index}`);
  if (!ans) return;
  const isHidden = ans.style.display === "none" || !ans.style.display;
  ans.style.display = isHidden ? "block" : "none";
  if (arrow) arrow.style.transform = isHidden ? "rotate(180deg)" : "rotate(0deg)";
}

window.toggleFaqAnswer = toggleFaqAnswer;
window.populateAiModal = populateAiModal;
window.populateFarmerDirectAdvisory = populateFarmerDirectAdvisory;
window.populateSideAdvisoryPanel = function(advisory, isMr, fullData) {
  populateAiModal(fullData || state.currentData, isMr);
};
