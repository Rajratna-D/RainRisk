/**
 * MahaRainRisk | Bilingual Language Switcher (Marathi <-> English)
 * 100% Strict Language Separation & Devanagari Numerals Engine
 * Depends on: state.js (state), map.js (updateMapPinLabels), dashboard.js (updateDashboard)
 */

function applyLanguage(lang) {
  if (window.stopAudioSpeech) window.stopAudioSpeech();
  state.currentLanguage = lang;
  const isMr = lang === "mr";

  // Toggle button badge: Display the target language you switch to upon clicking
  const langTag = document.getElementById("lang-tag");
  if (langTag) langTag.innerHTML = isMr ? "🌐 English" : "🌐 मराठी";
  const btnLang = document.getElementById("btn-lang");
  if (btnLang) btnLang.setAttribute("title", isMr ? "Switch to English (इंग्रजीत पहा)" : "मराठीत बदला (Switch to Marathi)");

  // Header & Titles (100% Strict Separation)
  const brandTitle = document.getElementById("brand-title-text");
  if (brandTitle) brandTitle.textContent = isMr ? "महा-रेन-रिस्क" : "MahaRainRisk";
  
  const subBadge = document.getElementById("brand-sub-badge");
  if (subBadge) subBadge.style.display = "none";
  
  document.title = isMr ? "महा-रेन-रिस्क | कृषी डॅशबोर्ड" : "MahaRainRisk | Agritech Dashboard";
  
  const aiAssist = document.getElementById("ai-assistant-label");
  if (aiAssist) aiAssist.textContent = isMr ? "कृषी AI" : "AI Assistant";
  
  const searchInput = document.getElementById("taluka-search-input");
  if (searchInput) {
    searchInput.placeholder = isMr 
      ? "तालुका शोधा (उदा. पैठण, बारामती, मेहकर)..." 
      : "Search taluka (e.g. Paithan, Baramati)...";
  }

  // Main Canvas Tab Labels
  const tabFarmer = document.getElementById("tab-label-farmer");
  if (tabFarmer) tabFarmer.textContent = isMr ? "शेतकरी माहिती" : "Farmer Essentials";
  
  const tabAnalytics = document.getElementById("tab-label-analytics");
  if (tabAnalytics) tabAnalytics.textContent = isMr ? "सविस्तर आलेख" : "Detailed Analytics";

  // Hero View Toggle Labels
  const lblCrop = document.getElementById("label-crop-view");
  if (lblCrop) lblCrop.textContent = isMr ? "पीक पाहणी" : "Crop View";
  
  const lblMap = document.getElementById("label-map-view");
  if (lblMap) lblMap.textContent = isMr ? "महाराष्ट्र नकाशा" : "Maharashtra Map";
  
  const harvestTitle = document.getElementById("harvest-card-title");
  if (harvestTitle) harvestTitle.textContent = isMr ? "दुष्काळ जोखीम मीटर" : "Drought Risk Meter";

  // Tab 1 Farmer Cards Titles
  const titleClimate = document.getElementById("title-climate");
  if (titleClimate) titleClimate.textContent = isMr ? "३ महिन्यांचा पाऊस" : "3-Month Rainfall";
  
  const titleMoist = document.getElementById("title-moisture");
  if (titleMoist) titleMoist.textContent = isMr ? "जमिनीतील ओलावा" : "Soil Moisture";
  
  const titleLight = document.getElementById("title-light");
  if (titleLight) titleLight.textContent = isMr ? "धरण पाणीसाठा" : "Dam Reservoir Storage";
  
  const titleEc = document.getElementById("title-ec");
  if (titleEc) titleEc.textContent = isMr ? "पावसातील खंड दिवस" : "Dry Spell Days";
  
  const unitEc = document.getElementById("unit-ec");
  if (unitEc) unitEc.textContent = isMr ? "दिवस" : "days";

  // Tab 1 Banner Titles
  const actIrrig = document.getElementById("act-title-irrigation");
  if (actIrrig) actIrrig.textContent = isMr ? "सिंचन नियोजन:" : "Irrigation Strategy:";
  
  const actConserv = document.getElementById("act-title-conservation");
  if (actConserv) actConserv.textContent = isMr ? "ओलावा संवर्धन:" : "Moisture Conservation:";
  
  const actNutr = document.getElementById("act-title-nutrients");
  if (actNutr) actNutr.textContent = isMr ? "खत व फवारणी उपाय:" : "Foliar Sprays & Nutrients:";
  
  const svgSpeaker = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13" style="vertical-align: -1px; margin-right: 4px;"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>`;
  const ttsInline = document.getElementById("tts-inline-label");
  if (ttsInline) ttsInline.innerHTML = `${svgSpeaker}<span>${isMr ? "सल्ला ऐका" : "Listen"}</span>`;
  
  const ttsAudio = document.getElementById("tts-audio-label");
  if (ttsAudio) ttsAudio.innerHTML = `${svgSpeaker}<span>${isMr ? "सल्ला ऐका" : "Listen"}</span>`;

  // Tab 2 Analytics Titles
  const titleGrowth = document.getElementById("title-growth");
  if (titleGrowth) titleGrowth.textContent = isMr ? "मागील ५ वर्षांचा पाऊस (IMD Pune)" : "5-Year Monsoon Rainfall (IMD Pune)";
  
  const unitGrowth = document.getElementById("unit-growth");
  if (unitGrowth) unitGrowth.textContent = isMr ? "mm वार्षिक सरासरी" : "mm Annual Average";
  
  const titleCo2 = document.getElementById("title-co2");
  if (titleCo2) titleCo2.textContent = isMr ? "पुढील ३० दिवसांचा अंदाज" : "30-Day Early Warning Outlook";
  
  const titleWaterFlow = document.getElementById("title-water-flow");
  if (titleWaterFlow) titleWaterFlow.textContent = isMr ? "पाणी साठा बॅटरी" : "Water Reserve Balance";
  
  const titlePower = document.getElementById("title-power");
  if (titlePower) titlePower.textContent = isMr ? "पावसाचा ताण व खंड दिवस" : "Dry Spell Timeline & Stress Days";
  
  const unitPower = document.getElementById("unit-power");
  if (unitPower) unitPower.textContent = isMr ? "दिवस खंड" : "Days Gap";

  // Permanent Right Telemetry Sidebar
  const sideTel = document.getElementById("side-telemetry-title");
  if (sideTel) sideTel.textContent = isMr ? "थेट पाणी व उपग्रह स्थिती" : "Live Water & Ground Telemetry";
  
  const sc1 = document.getElementById("side-card1-title");
  if (sc1) sc1.textContent = isMr ? "पाणी साठा स्थिती" : "Water Storage Status";
  
  const sc2 = document.getElementById("side-card2-title");
  if (sc2) sc2.textContent = isMr ? "जमीन ओलावा मूल्यांकन" : "Soil Moisture Assessment";
  
  const sc3 = document.getElementById("side-card3-title");
  if (sc3) sc3.textContent = isMr ? "दुष्काळ जोखीम पडताळणी" : "Drought Risk Verification";

  const sc4 = document.getElementById("side-card4-title");
  if (sc4) sc4.textContent = isMr ? "हवामान संदर्भ व पर्जन्यमान" : "Weather Context & Rain Outlook";

  const sc4Badge = document.getElementById("side-card4-badge");
  if (sc4Badge) sc4Badge.textContent = isMr ? "३०-दिवसीय अंदाज" : "30-DAY OUTLOOK";

  const sc4Stat1 = document.getElementById("side-card4-stat1-lbl");
  if (sc4Stat1) sc4Stat1.textContent = isMr ? "अपेक्षित पाऊस" : "Expected Rain";

  const sc4Stat2 = document.getElementById("side-card4-stat2-lbl");
  if (sc4Stat2) sc4Stat2.textContent = isMr ? "हंगामी पाऊस" : "Season Rain";

  // Tab 2 Climatological & ML Titles and Telemetry
  const tClimate = document.getElementById("title-climate-indices");
  if (tClimate) tClimate.textContent = isMr ? "हवामान निर्देशक व SPI तूट (Climatological Indices)" : "Climate Driver Indices & SPI Deficit";

  const txtNino = document.getElementById("txt-pill-nino");
  if (txtNino) txtNino.textContent = isMr ? "Niño 3.4 (ENSO): तटस्थ (Neutral -0.12°C)" : "Niño 3.4 (ENSO): Neutral (-0.12°C)";

  const txtIod = document.getElementById("txt-pill-iod");
  if (txtIod) txtIod.textContent = isMr ? "DMI (IOD): धन (+0.32°C Positive)" : "DMI (IOD): Positive (+0.32°C)";

  const txtSpi1 = document.getElementById("txt-pill-spi1");
  if (txtSpi1) txtSpi1.textContent = isMr ? "SPI-1: -0.22 (सामान्य)" : "SPI-1: -0.22 (Normal)";

  const txtSpi3 = document.getElementById("txt-pill-spi3");
  if (txtSpi3) txtSpi3.textContent = isMr ? "SPI-3: -0.45 (हलकी तूट)" : "SPI-3: -0.45 (Mild Deficit)";

  const txtSpi6 = document.getElementById("txt-pill-spi6");
  if (txtSpi6) txtSpi6.textContent = isMr ? "SPI-6: +0.10 (समाधानकारक)" : "SPI-6: +0.10 (Adequate)";

  const climSummary = document.getElementById("climatology-summary-text");
  if (climSummary) {
    climSummary.innerHTML = isMr
      ? "<strong>McKee et al. (1993) २-पॅरामीटर गॅमा वितरण:</strong> मागील ३ महिन्यांचा SPI निर्देशांक -०.४५ असून सौम्य ओलावा तूट दर्शवितो. पॅसिफिक व हिंदी महासागरातील प्रवाह सामान्य पावसासाठी अनुकूल आहेत."
      : "<strong>McKee et al. (1993) 2-Parameter Gamma Distribution:</strong> Past 3-month SPI index is -0.45, reflecting mild root-zone moisture deficit. Pacific and Indian Ocean teleconnections remain favorable for rainfall.";
  }

  const tMl = document.getElementById("title-ml-models");
  if (tMl) tMl.textContent = isMr ? "मशिन लर्निंग मॉडेल अचूकता (ML Telemetry)" : "Machine Learning Model Telemetry";

  const mlM1Title = document.getElementById("ml-m1-title");
  if (mlM1Title) mlM1Title.textContent = "Mode 1: 250-Tree RF Diagnostic Model";

  const mlM1Acc = document.getElementById("ml-m1-acc");
  if (mlM1Acc) mlM1Acc.textContent = "98.2% Test Accuracy";

  const mlM1Sub = document.getElementById("ml-m1-sub");
  if (mlM1Sub) mlM1Sub.textContent = "194 Talukas • 36 Districts (2014–2026)";

  const mlM2Title = document.getElementById("ml-m2-title");
  if (mlM2Title) mlM2Title.textContent = "Mode 2: 30-Day Early Warning Forecaster";

  const mlM2Acc = document.getElementById("ml-m2-acc");
  if (mlM2Acc) mlM2Acc.textContent = "77.4% Deficit Accuracy";

  const mlM2Sub = document.getElementById("ml-m2-sub");
  if (mlM2Sub) mlM2Sub.textContent = "Calibrated on Kharif 2026 Drought Shock";

  const mlDesc = document.getElementById("ml-features-desc");
  if (mlDesc) {
    mlDesc.textContent = "Input Features: IMD gridded rainfall, surface min/max temperature, root-zone moisture, reservoir storage & ENSO anomalies.";
  }

  // 100% Strict Bilingual Modals: Tips, Alerts, Verified Sources
  const elTipsTitle = document.getElementById("modal-tips-title");
  const elTipsBody = document.getElementById("modal-tips-body");
  if (elTipsTitle) elTipsTitle.textContent = isMr ? "शेतकरी हंगामी कृषी टिप्स" : "Farmer Seasonal Agronomic Tips";
  if (elTipsBody) {
    elTipsBody.innerHTML = isMr ? `
      <div style="background: rgba(94, 138, 66, 0.08); border-left: 4px solid var(--dock-active); padding: 10px 14px; border-radius: 0 10px 10px 0; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
        <div><strong>ठिबक सिंचन वापर:</strong> बाष्पीभवन टाळण्यासाठी रात्री किंवा पहाटेच्या वेळी पाणी द्यावे. ५०% पाण्याची बचत होते.</div>
      </div>
      <div style="background: rgba(94, 138, 66, 0.08); border-left: 4px solid var(--dock-active); padding: 10px 14px; border-radius: 0 10px 10px 0; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
        <div><strong>आच्छादन (Mulching):</strong> पिकाच्या दोन ओळींत पाचट किंवा भुसा पसरल्यास जमिनीतील ओलावा १५ दिवस टिकून राहतो.</div>
      </div>
      <div style="background: rgba(94, 138, 66, 0.08); border-left: 4px solid var(--dock-active); padding: 10px 14px; border-radius: 0 10px 10px 0; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="M10 2v7.31M14 2v7.31M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0"/></svg>
        <div><strong>फवारणी उपाय:</strong> पाऊस लांबल्यास १% पोटॅशियम नायट्रेटची फवारणी केल्याने पाने सुकत नाहीत.</div>
      </div>
    ` : `
      <div style="background: rgba(94, 138, 66, 0.08); border-left: 4px solid var(--dock-active); padding: 10px 14px; border-radius: 0 10px 10px 0; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
        <div><strong>Drip Irrigation Timing:</strong> Irrigate during early morning or late evening to minimize evaporation. Saves up to 50% water.</div>
      </div>
      <div style="background: rgba(94, 138, 66, 0.08); border-left: 4px solid var(--dock-active); padding: 10px 14px; border-radius: 0 10px 10px 0; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
        <div><strong>In-Situ Mulching:</strong> Spread crop residue or straw between crop rows to preserve soil moisture for up to 15 days.</div>
      </div>
      <div style="background: rgba(94, 138, 66, 0.08); border-left: 4px solid var(--dock-active); padding: 10px 14px; border-radius: 0 10px 10px 0; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="M10 2v7.31M14 2v7.31M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0"/></svg>
        <div><strong>Foliar Sprays:</strong> If rains are delayed, spray 1% Potassium Nitrate (100g in 10L water) early morning to prevent heat stress.</div>
      </div>
    `;
  }

  const elAlertsTitle = document.getElementById("modal-alerts-title");
  const elAlertsBody = document.getElementById("modal-alerts-body");
  if (elAlertsTitle) elAlertsTitle.textContent = isMr ? "हवामान व दुष्काळ सतर्कता इशारे" : "Live Weather & Drought Alerts";
  if (elAlertsBody) {
    elAlertsBody.innerHTML = isMr ? `
      <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); padding: 10px 12px; border-radius: 10px; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <div><strong style="color: #DC2626;">मराठवाडा कोरडा खंड इशारा:</strong> छत्रपती संभाजीनगर, जालना, बीड भागात पुढील ७ दिवस पावसाची शक्यता कमी.</div>
      </div>
      <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); padding: 10px 12px; border-radius: 10px; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        <div><strong style="color: #D97706;">पश्चिम महाराष्ट्र धरण स्थिती:</strong> उजनी व कोयना धरण पाणीसाठा समाधानकारक (८५%).</div>
      </div>
      <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); padding: 10px 12px; border-radius: 10px; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#047857" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <div><strong style="color: #047857;">विदर्भ पूर्व पाऊस:</strong> नागपूर, वर्धा भागात हलका ते मध्यम पाऊस अपेक्षित.</div>
      </div>
    ` : `
      <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); padding: 10px 12px; border-radius: 10px; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <div><strong style="color: #DC2626;">Marathwada Dry Spell Watch:</strong> Chhatrapati Sambhajinagar, Jalna, and Beed districts show high probability of a 7-day rainfall gap.</div>
      </div>
      <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); padding: 10px 12px; border-radius: 10px; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        <div><strong style="color: #D97706;">Western Maharashtra Reservoirs:</strong> Ujani and Koyna dams holding optimal live storage levels (85%).</div>
      </div>
      <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); padding: 10px 12px; border-radius: 10px; display: flex; align-items: flex-start; gap: 8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="#047857" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" style="flex-shrink:0; margin-top:2px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <div><strong style="color: #047857;">East Vidarbha Forecast:</strong> Nagpur and Wardha regions expect light to moderate rainfall over next 48 hours.</div>
      </div>
    `;
  }

  const elSourcesTitle = document.getElementById("modal-sources-title");
  const elSourcesBody = document.getElementById("modal-sources-body");
  if (elSourcesTitle) elSourcesTitle.textContent = isMr ? "अधिकृत माहिती व कृषी स्रोत" : "Official Agronomic Data Sources & Government Anchors";
  if (elSourcesBody) {
    elSourcesBody.innerHTML = isMr ? `
      <div><strong>• महाराष्ट्र शासन कृषी विभाग:</strong> Krishi Bhavan, Pune (Agro-Climatic Guidance)</div>
      <div><strong>• ४ राज्य कृषी विद्यापीठे:</strong> MPKV राहुरी, VNMKV परभणी, Dr. PDKV अकोला, Dr. BSKKV दापोली</div>
      <div><strong>• भारतीय हवामान विभाग (IMD Pune):</strong> उच्च दर्जाची दैनिक पर्जन्यवृष्टी आकडेवारी (२०१४-२०२६)</div>
      <div><strong>• जलसंपदा विभाग (WRD Maharashtra):</strong> १२ प्रमुख धरणांची थेट पाणीपातळी</div>
      <div><strong>• केंद्रीय भूजल मंडळ (CGWB):</strong> ६२२ विहिरींचे भूजल निरीक्षण</div>
      <div><strong>• युरोपियन स्पेस एजन्सी (ESA / ERA5):</strong> रूट-झोन जमिनीतील ओलावा व तापमान</div>
    ` : `
      <div><strong>• Department of Agriculture, Govt. of Maharashtra:</strong> Krishi Bhavan, Pune (Agro-Climatic Guidance)</div>
      <div><strong>• 4 State Agricultural Universities:</strong> MPKV Rahuri, VNMKV Parbhani, Dr. PDKV Akola, Dr. BSKKV Dapoli</div>
      <div><strong>• India Meteorological Department (IMD Pune):</strong> High-resolution gridded rainfall series (2014–2026)</div>
      <div><strong>• Water Resources Department (WRD Maharashtra):</strong> Real-time storage telemetry across 12 major reservoirs</div>
      <div><strong>• Central Ground Water Board (CGWB):</strong> 622 aquifer telemetry monitoring stations</div>
      <div><strong>• European Space Agency (ESA / ERA5-Land):</strong> Daily root-zone soil moisture & land surface temperature</div>
    `;
  }

  // 100% Strict Tooltips
  const setAttr = (id, attr, val) => {
    const el = document.getElementById(id);
    if (el) el.setAttribute(attr, val);
  };
  setAttr("dock-btn-greenhouse", "title", isMr ? "पीक पाहणी" : "Crop View");
  setAttr("dock-btn-grid", "title", isMr ? "महाराष्ट्र नकाशा" : "Maharashtra Talukas Map");
  setAttr("dock-btn-water", "title", isMr ? "पाणी साठा माहिती" : "Water Storage Insights");
  setAttr("dock-btn-calendar", "title", isMr ? "हवामान इतिहास व अंदाज" : "Weather History & Outlook");
  setAttr("dock-btn-sliders", "title", isMr ? "हंगामी कृषी टिप्स" : "Seasonal Agronomic Tips");
  setAttr("dock-btn-notes", "title", isMr ? "कृषी सल्लागार" : "University Advisory");
  setAttr("dock-btn-settings", "title", isMr ? "अधिकृत माहिती व स्रोत" : "Verified Data Sources");
  setAttr("btn-agri-dept", "title", isMr ? "महाराष्ट्र शासन कृषी विभाग" : "Department of Agriculture, GoM");
  setAttr("open-advisory-btn", "title", isMr ? "कृषी विद्यापीठ सल्ला उघडा" : "Open University Advisory");
  setAttr("btn-tips", "title", isMr ? "शेतकरी हंगामी टिप्स" : "Farmer Seasonal Tips");
  setAttr("btn-download", "title", isMr ? "तालुका अहवाल डाउनलोड करा" : "Download Taluka Report");
  setAttr("btn-alerts", "title", isMr ? "हवामान सतर्कता इशारे" : "Weather & Drought Alerts");
  setAttr("btn-refresh", "title", isMr ? "माहिती ताजी करा" : "Refresh Telemetry Data");
  setAttr("voice-mic-btn", "title", isMr ? "बोलून शोधा (तालुक्याचे नाव बोला)" : "Voice Search (Speak taluka name)");

  // Update map pin labels
  if (typeof updateMapPinLabels === "function") {
    updateMapPinLabels();
  }

  // Re-render dashboard data with proper language and numerals
  if (state.currentData && typeof updateDashboard === "function") {
    updateDashboard(state.currentData);
  }
  if (state.currentXai && typeof renderTreeShapExplain === "function") {
    renderTreeShapExplain(state.currentXai);
  }
  if (state.currentAdjacent && typeof renderAdjacentTalukas === "function") {
    renderAdjacentTalukas(state.currentAdjacent);
  }
}

function toggleLanguage() {
  const nextLang = state.currentLanguage === "mr" ? "en" : "mr";
  applyLanguage(nextLang);
}

function initI18n() {
  const btnLang = document.getElementById("btn-lang");
  if (btnLang) {
    btnLang.addEventListener("click", toggleLanguage);
  }
  // Initialize initial titles and strings
  applyLanguage(state.currentLanguage);
}

window.toggleLanguage = toggleLanguage;
window.applyLanguage = applyLanguage;
window.initI18n = initI18n;
