/**
 * MahaRainRisk | Application Controller & Bootstrap
 * Orchestrates modules: state.js, map.js, dashboard.js, advisory.js, audio.js, i18n.js
 */

// Global view functions and modals are initialized in state.js
window.downloadTalukaReport = downloadTalukaReport;
window.locateUserTaluka = locateUserTaluka;
window.openMcpModal = openMcpModal;
window.closeMcpModal = closeMcpModal;
window.copyMcpText = copyMcpText;
window.showToast = showToast;

// ============================================================================
// STATIC REPLICA VISUALS (Capsules, Histogram Bars, Power Bars)
// ============================================================================
function initStaticVisuals() {
  // 1. Water Flow 18 Capsule Bars
  const capsuleContainer = document.getElementById("water-capsule-bars");
  if (capsuleContainer) {
    let pillsHTML = "";
    for (let i = 0; i < 18; i++) {
      const isGreen = i >= 8;
      pillsHTML += `<div class="capsule-pill-bar ${isGreen ? 'green-fill' : ''}"></div>`;
    }
    capsuleContainer.innerHTML = pillsHTML;
  }

  // 2. Dry Spell Timeline Bars (June to October)
  const powerContainer = document.getElementById("power-bars-container");
  if (powerContainer) {
    const barsData = [
      { height: 28, colorClass: "gray" },
      { height: 35, colorClass: "gray" },
      { height: 50, colorClass: "orange" },
      { height: 85, colorClass: "orange" },
      { height: 95, colorClass: "orange" }, // August El Niño peak stress
      { height: 60, colorClass: "orange" },
      { height: 40, colorClass: "green" },
      { height: 75, colorClass: "green" },
      { height: 65, colorClass: "green" }
    ];

    powerContainer.innerHTML = barsData.map(b => 
      `<div class="power-bar ${b.colorClass}" style="height: ${b.height}%;"></div>`
    ).join("");
  }

  // 3. 5-Year Monsoon Rainfall History Bars (2019-2024)
  const histoContainer = document.getElementById("growth-histogram-bars");
  if (histoContainer) {
    const yearBars = [
      { h: 75, red: false },
      { h: 85, red: false },
      { h: 78, red: false },
      { h: 95, red: false },
      { h: 42, red: true },  // 2023 Drought Deficit
      { h: 72, red: false }
    ];
    histoContainer.innerHTML = yearBars.map(y => 
      `<div class="histo-bar-col ${y.red ? 'deficit-red' : 'active-green'}" style="height: ${y.h}%;"></div>`
    ).join("");
  }
}

// ============================================================================
// DATA FETCHING & SYNCHRONIZATION
// ============================================================================
async function loadTalukasDirectory() {
  try {
    const base = window.API_BASE || "";
    const res = await fetch(`${base}/api/talukas`);
    if (res.ok) {
      state.talukasDirectory = await res.json();
      renderTalukaPinsOnMap(state.talukasDirectory);
    }
  } catch (e) {
    console.error("Directory error:", e);
  }
}

// ============================================================================
// TOAST NOTIFICATION SYSTEM
// ============================================================================
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast-item ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-10px)";
    setTimeout(() => toast.remove(), 350);
  }, 4000);
}

// ============================================================================
// GPS 1-TAP LOCATION SERVICE (Client-Side Haversine Snapping)
// ============================================================================
function getHaversineDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius in kilometers
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function locateUserTaluka() {
  if (!navigator.geolocation) {
    const isMr = state.currentLanguage === "mr";
    showToast(isMr ? "तुमच्या ब्राउझरमध्ये GPS उपलब्ध नाही." : "Geolocation not supported by browser.", "warning");
    return;
  }

  const gpsBtn = document.getElementById("btn-gps-locate");
  if (gpsBtn) gpsBtn.classList.add("gps-locating-pulse");

  navigator.geolocation.getCurrentPosition(
    (position) => {
      if (gpsBtn) gpsBtn.classList.remove("gps-locating-pulse");
      const userLat = position.coords.latitude;
      const userLon = position.coords.longitude;

      if (!state.talukasDirectory || state.talukasDirectory.length === 0) {
        showToast(state.currentLanguage === "mr" ? "तालुका सूची लोड होत आहे, कृपया थांबा..." : "Talukas directory still loading...", "info");
        return;
      }

      let nearestTaluka = null;
      let minDistanceKm = Infinity;

      for (const t of state.talukasDirectory) {
        const dist = getHaversineDistanceKm(userLat, userLon, t.latitude, t.longitude);
        if (dist < minDistanceKm) {
          minDistanceKm = dist;
          nearestTaluka = t;
        }
      }

      if (nearestTaluka) {
        const isMr = state.currentLanguage === "mr";
        const talukaDisplayName = isMr ? (nearestTaluka.taluka_name_mr || nearestTaluka.taluka_name) : nearestTaluka.taluka_name;
        
        if (minDistanceKm > 100) {
          showToast(
            isMr 
              ? `तुम्ही महाराष्ट्राबाहेर आहात. सर्वात जवळचा सीमा तालुका: ${talukaDisplayName}`
              : `You are outside Maharashtra. Nearest border taluka: ${talukaDisplayName}`,
            "info"
          );
        } else {
          showToast(
            isMr 
              ? `📍 तालुका सापडला: ${talukaDisplayName} (${minDistanceKm.toFixed(1)} किमी)` 
              : `📍 Located: ${talukaDisplayName} (${minDistanceKm.toFixed(1)} km away)`,
            "success"
          );
        }

        state.currentTaluka = nearestTaluka.taluka_name;
        const inputEl = document.getElementById("taluka-search-input");
        if (inputEl) inputEl.value = talukaDisplayName;
        fetchTalukaData(nearestTaluka.taluka_name);
      }
    },
    (error) => {
      if (gpsBtn) gpsBtn.classList.remove("gps-locating-pulse");
      const isMr = state.currentLanguage === "mr";
      if (error.code === error.PERMISSION_DENIED) {
        showToast(
          isMr 
            ? "कृपया GPS परवानगी द्या किंवा शोधपेटीत नाव टाईप करा." 
            : "Location permission denied. Please search manually.",
          "warning"
        );
      } else {
        showToast(
          isMr 
            ? "GPS सिग्नल मिळाला नाही. कृपया पुन्हा प्रयत्न करा." 
            : "GPS signal unavailable. Please retry.",
          "warning"
        );
      }
    },
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 300000 }
  );
}

// ============================================================================
// MCP MODAL & CLIPBOARD COPY HANDLERS
// ============================================================================
function openMcpModal() {
  const modal = document.getElementById("modal-mcp-connector");
  if (modal) modal.classList.add("open");
}

function closeMcpModal() {
  const modal = document.getElementById("modal-mcp-connector");
  if (modal) modal.classList.remove("open");
}

function copyMcpText(text, btnElement) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showCopiedFeedback(btnElement);
    }).catch(() => {
      fallbackCopyText(text, btnElement);
    });
  } else {
    fallbackCopyText(text, btnElement);
  }
}

function fallbackCopyText(text, btnElement) {
  const tempInput = document.createElement("input");
  tempInput.value = text;
  document.body.appendChild(tempInput);
  tempInput.select();
  try {
    document.execCommand("copy");
    showCopiedFeedback(btnElement);
  } catch (e) {
    showToast("Copy failed: " + text, "warning");
  }
  document.body.removeChild(tempInput);
}

function showCopiedFeedback(btnElement) {
  if (!btnElement) return;
  const originalHtml = btnElement.innerHTML;
  btnElement.classList.add("copied");
  btnElement.innerHTML = "<span>✓ Copied!</span>";
  showToast("✓ Copied endpoint to clipboard!", "success");
  setTimeout(() => {
    btnElement.classList.remove("copied");
    btnElement.innerHTML = originalHtml;
  }, 2000);
}

// ============================================================================
// DATA FETCHING & SYNCHRONIZATION (With Offline-First Resilience)
// ============================================================================
async function fetchTalukaData(query) {
  const cleanQ = query.trim();
  const cacheKey = "mrr_taluka_" + cleanQ.toLowerCase();

  try {
    if (window.stopAudioSpeech) window.stopAudioSpeech();
    const encodedQ = encodeURIComponent(cleanQ);
    const base = window.API_BASE || "";
    const res = await fetch(`${base}/api/taluka/${encodedQ}`);

    if (res.ok) {
      const data = await res.json();
      state.currentData = data;
      state.currentTaluka = data.meta.taluka;
      state.currentAdvisory = data.advisory;

      // Cache snapshot for offline field resilience
      try {
        localStorage.setItem(cacheKey, JSON.stringify(data));
        localStorage.setItem("mrr_last_taluka", cleanQ);
      } catch (e) {
        // quota exceeded fallback
      }

      updateDashboard(data);

      // Trigger TreeSHAP Explainability & Regional Adjacency
      if (typeof fetchTalukaExplain === "function") {
        fetchTalukaExplain(cleanQ);
      }
      if (typeof fetchTalukaAdjacent === "function") {
        fetchTalukaAdjacent(cleanQ);
      }
      return;
    }
  } catch (err) {
    console.warn("Network fetch failed, attempting offline cache recovery:", err);
  }

  // Offline Fallback from LocalStorage
  try {
    const cachedStr = localStorage.getItem(cacheKey);
    if (cachedStr) {
      const cachedData = JSON.parse(cachedStr);
      state.currentData = cachedData;
      state.currentTaluka = cachedData.meta.taluka;
      state.currentAdvisory = cachedData.advisory;

      updateDashboard(cachedData);

      const isMr = state.currentLanguage === "mr";
      showToast(
        isMr 
          ? "📶 तुम्ही ऑफलाइन आहात. साठवलेली शेवटची माहिती दाखवत आहोत." 
          : "📶 Offline mode: Showing last cached telemetry.",
        "warning"
      );

      if (typeof fetchTalukaExplain === "function") {
        fetchTalukaExplain(cleanQ);
      }
      return;
    }
  } catch (e) {
    console.error("Local cache parse error:", e);
  }

  const isMr = state.currentLanguage === "mr";
  showToast(
    isMr 
      ? "डेटा लोड होऊ शकला नाही. इंटरनेट कनेक्शन तपासा." 
      : "Failed to load telemetry. Check internet connection.",
    "warning"
  );
}


// ============================================================================
// DOWNLOAD TALUKA REPORT
// ============================================================================
function downloadTalukaReport() {
  if (!state.currentData) {
    alert(state.currentLanguage === "mr" ? "कृपया प्रथम तालुका निवडा." : "Please select a taluka first.");
    return;
  }

  const d = state.currentData;
  const meta = d.meta;
  const cards = d.farmer_cards;
  const diag = d.live_diagnosis;
  const isMr = state.currentLanguage === "mr";

  const reportText = `
================================================================================
  ${isMr ? 'महाराष्ट्र शासन कृषी विभाग - महा-रेन-रिस्क तालुका दुष्काळ व पाणी अहवाल' : 'Government of Maharashtra - MahaRainRisk Agritech Drought Report'}
================================================================================
${isMr ? 'तालुका (Taluka)' : 'Taluka'}       : ${meta.taluka} (${meta.taluka_mr || ""})
${isMr ? 'जिल्हा (District)' : 'District'}     : ${meta.district}
${isMr ? 'कालावधी (Period)' : 'Period'}       : ${meta.period}
${isMr ? 'जोखीम पातळी (Risk)' : 'Risk Level'}   : ${diag.label_mr} (${diag.label_en}) - ${diag.confidence_pct}% Conf

${isMr ? 'भौतिक निर्देशांक:' : 'Physical Telemetry:'}
1. ${isMr ? '३ महिन्यांचा पाऊस' : '3-Month Rainfall'}   : ${cards.rainfall_deficit.value_mm} mm
2. ${isMr ? 'जमिनीतील ओलावा' : 'Soil Moisture'}     : ${cards.soil_moisture.value_pct}%
3. ${isMr ? 'धरण पाणीसाठा' : 'Dam Storage'}       : ${cards.dam_storage.value_pct}%
4. ${isMr ? 'पावसातील खंड' : 'Dry Gap Days'}       : ${cards.dry_gap.value_days} ${isMr ? 'दिवस' : 'days'}

${isMr ? 'विद्यापीठ शिफारस:' : 'University Recommendation:'}
${isMr ? (d.advisory?.university_anchor?.university_name_mr || "") : (d.advisory?.university_anchor?.university_name_en || "")}
${isMr ? (d.advisory?.prescriptive_actions?.irrigation_strategy?.mr || "") : (d.advisory?.prescriptive_actions?.irrigation_strategy?.en || "")}
================================================================================
  MahaRainRisk Agritech Platform • IMD Pune & WRD Telemetry
================================================================================
  `.trim();

  const blob = new Blob([reportText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `MahaRainRisk_${meta.taluka}_Report.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ============================================================================
// EVENT HANDLERS & MODALS
// ============================================================================
function bindEventHandlers() {
  // Autocomplete Search
  const searchInput = document.getElementById("taluka-search-input");
  const autoBox = document.getElementById("autocomplete-list");

  if (searchInput && autoBox) {
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.trim().toLowerCase();
      if (q.length < 1) {
        autoBox.style.display = "none";
        return;
      }
      const filtered = state.talukasDirectory.filter(t => 
        t.taluka_name.toLowerCase().includes(q) ||
        (t.taluka_name_mr && t.taluka_name_mr.includes(q))
      ).slice(0, 7);

      if (filtered.length === 0) {
        autoBox.style.display = "none";
        return;
      }

      autoBox.innerHTML = filtered.map(t => `
        <div class="autocomplete-row" data-name="${t.taluka_name}">
          <span class="autocomplete-row-name">${t.taluka_name} (${t.taluka_name_mr || ""})</span>
          <span class="autocomplete-row-sub">${t.district_name} • ${t.university}</span>
        </div>
      `).join("");

      autoBox.style.display = "block";
      autoBox.querySelectorAll(".autocomplete-row").forEach(r => {
        r.addEventListener("click", () => {
          const name = r.getAttribute("data-name");
          searchInput.value = name;
          autoBox.style.display = "none";
          searchInput.blur(); // Dismiss virtual keyboard on mobile
          findAndSelectTaluka(name);
        });
      });
    });

    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        autoBox.style.display = "none";
        searchInput.blur(); // Dismiss virtual keyboard on mobile
        findAndSelectTaluka(searchInput.value);
      }
    });

    document.addEventListener("click", (e) => {
      if (!e.target.closest(".search-center-group")) {
        autoBox.style.display = "none";
      }
    });
  }

  // Voice Search Button
  document.getElementById("voice-mic-btn")?.addEventListener("click", initVoiceSearch);

  // Audio Speech Advisor Buttons (Inline Banner & Side Panel)
  document.getElementById("tts-inline-btn")?.addEventListener("click", toggleAudioSpeech);
  document.getElementById("tts-audio-btn")?.addEventListener("click", toggleAudioSpeech);

  // Top Glowing AI Assistant Button -> Opens AI Decision Support Modal & Switches Right Panel
  document.getElementById("open-advisory-btn")?.addEventListener("click", () => {
    document.getElementById("modal-ai-advisory")?.classList.add("open");
    switchRightPanel('advisory');
  });

  // Download Report Button
  document.getElementById("btn-download")?.addEventListener("click", downloadTalukaReport);

  // Refresh Button
  const btnRefresh = document.getElementById("btn-refresh");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      btnRefresh.style.transform = "rotate(360deg)";
      btnRefresh.style.transition = "transform 0.5s ease";
      fetchTalukaData(state.currentTaluka);
      setTimeout(() => { btnRefresh.style.transform = "none"; }, 500);
    });
  }

  const setActiveDockBtn = (id) => {
    document.querySelectorAll(".dock-icon-btn").forEach(b => b.classList.remove("active"));
    document.getElementById(id)?.classList.add("active");
  };
  window.setActiveDockBtn = setActiveDockBtn;

  // Dock Shortcuts (Smooth Scroll to section on Mobile & Desktop)
  document.getElementById("dock-btn-greenhouse")?.addEventListener("click", () => {
    setActiveDockBtn("dock-btn-greenhouse");
    toggleHeroView("crop");
    switchMainTab("farmer");
    document.getElementById("hero-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  document.getElementById("dock-btn-grid")?.addEventListener("click", () => {
    setActiveDockBtn("dock-btn-grid");
    toggleHeroView("map");
    switchMainTab("farmer");
    document.getElementById("hero-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  document.getElementById("dock-btn-water")?.addEventListener("click", () => {
    setActiveDockBtn("dock-btn-water");
    switchMainTab("farmer");
    document.getElementById("card-air-moisture")?.scrollIntoView({ behavior: "smooth" });
  });
  document.getElementById("dock-btn-calendar")?.addEventListener("click", () => {
    setActiveDockBtn("dock-btn-calendar");
    switchMainTab("analytics");
    document.getElementById("card-power")?.scrollIntoView({ behavior: "smooth" });
  });
  document.getElementById("dock-btn-sliders")?.addEventListener("click", () => {
    setActiveDockBtn("dock-btn-sliders");
    openTipsModal();
  });
  document.getElementById("dock-btn-notes")?.addEventListener("click", () => {
    setActiveDockBtn("dock-btn-notes");
    document.getElementById("modal-ai-advisory")?.classList.add("open");
    switchRightPanel("advisory");
  });
}

function bindModalHandlers() {
  // Modal 1: Tips
  const modalTips = document.getElementById("modal-tips");
  document.getElementById("btn-tips")?.addEventListener("click", () => modalTips?.classList.add("open"));
  document.getElementById("close-modal-tips")?.addEventListener("click", () => modalTips?.classList.remove("open"));

  // Modal 2: Alerts
  const modalAlerts = document.getElementById("modal-alerts");
  document.getElementById("btn-alerts")?.addEventListener("click", () => modalAlerts?.classList.add("open"));
  document.getElementById("close-modal-alerts")?.addEventListener("click", () => modalAlerts?.classList.remove("open"));

  // Modal 3: Sources & Gov Emblem
  const modalSources = document.getElementById("modal-sources");
  document.getElementById("btn-agri-dept")?.addEventListener("click", () => modalSources?.classList.add("open"));
  document.getElementById("dock-btn-settings")?.addEventListener("click", () => modalSources?.classList.add("open"));
  document.getElementById("close-modal-sources")?.addEventListener("click", () => modalSources?.classList.remove("open"));

  // Modal 4: AI Decision Support & 7-Day Action Planner
  const modalAi = document.getElementById("modal-ai-advisory");
  document.getElementById("close-modal-ai-advisory")?.addEventListener("click", () => modalAi?.classList.remove("open"));
  window.closeAiModal = () => modalAi?.classList.remove("open");
  window.openAiModal = () => {
    modalAi?.classList.add("open");
    switchRightPanel("advisory");
  };

  // Close modals on clicking overlay background or pressing Escape
  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.remove("open");
    });
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay.open").forEach(m => m.classList.remove("open"));
    }
  });
}

// ============================================================================
// BOOTSTRAP
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  console.log("[*] Booting MahaRainRisk Farmer Dashboard...");
  initStaticVisuals();
  initMap();
  bindEventHandlers();
  bindModalHandlers();
  initI18n();
  loadTalukasDirectory();
  fetchTalukaData(state.currentTaluka);
});
