/**
 * MahaRainRisk | Text-to-Speech (TTS) Audio & Voice Search
 * Depends on: state.js (state)
 */

// ============================================================================
// TEXT-TO-SPEECH (TTS) AUDIO LOGIC (SERVER NEURAL VOICE MODEL + FALLBACK)
// ============================================================================
let activeAudioPlayer = null;
let isAudioLoading = false;
let lastAudioClickTime = 0;

const SVG_AUDIO_PLAY = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13" style="vertical-align: -1px; margin-right: 4px;"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>`;
const SVG_AUDIO_STOP = `<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" width="12" height="12" style="vertical-align: -1px; margin-right: 4px;"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>`;
const SVG_AUDIO_LOAD = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13" style="vertical-align: -1px; margin-right: 4px; animation: spin 1s linear infinite;"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg>`;

function setSpeakingUI(isSpeaking) {
  const isMr = state.currentLanguage === "mr";
  const btnSide = document.getElementById("tts-audio-btn");
  const labelSide = document.getElementById("tts-audio-label");
  const btnInline = document.getElementById("tts-inline-btn");
  const labelInline = document.getElementById("tts-inline-label");

  btnSide?.classList.remove("loading");
  btnInline?.classList.remove("loading");

  if (isSpeaking) {
    btnSide?.classList.add("speaking");
    btnInline?.classList.add("speaking");
    const stopHtml = `${SVG_AUDIO_STOP}<span>${isMr ? "थांबवा (Stop)" : "Stop"}</span>`;
    if (labelSide) labelSide.innerHTML = stopHtml;
    if (labelInline) labelInline.innerHTML = stopHtml;
  } else {
    btnSide?.classList.remove("speaking");
    btnInline?.classList.remove("speaking");
    const playHtml = `${SVG_AUDIO_PLAY}<span>${isMr ? "सल्ला ऐका" : "Listen"}</span>`;
    if (labelSide) labelSide.innerHTML = playHtml;
    if (labelInline) labelInline.innerHTML = playHtml;
  }
}

function setLoadingUI() {
  const isMr = state.currentLanguage === "mr";
  const btnSide = document.getElementById("tts-audio-btn");
  const labelSide = document.getElementById("tts-audio-label");
  const btnInline = document.getElementById("tts-inline-btn");
  const labelInline = document.getElementById("tts-inline-label");

  btnSide?.classList.remove("speaking");
  btnInline?.classList.remove("speaking");
  btnSide?.classList.add("loading");
  btnInline?.classList.add("loading");

  const loadHtml = `${SVG_AUDIO_LOAD}<span>${isMr ? "तयार होत आहे..." : "Generating..."}</span>`;
  if (labelSide) labelSide.innerHTML = loadHtml;
  if (labelInline) labelInline.innerHTML = loadHtml;
}

async function toggleAudioSpeech() {
  // Prevent rapid double-clicks / bounce
  const now = Date.now();
  if (now - lastAudioClickTime < 400) {
    return;
  }
  lastAudioClickTime = now;

  // If currently loading/generating, cancel immediately
  if (isAudioLoading) {
    stopAudioSpeech();
    return;
  }

  // If already playing audio, stop immediately
  if (activeAudioPlayer && !activeAudioPlayer.paused) {
    stopAudioSpeech();
    return;
  }

  // Also stop browser speech synthesis if active
  if (window.speechSynthesis && window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    stopAudioSpeech();
    return;
  }

  const taluka = state.currentData?.meta?.taluka || state.currentTaluka || "Paithan";
  const lang = state.currentLanguage || "mr";

  isAudioLoading = true;
  setLoadingUI();

  try {
    const base = window.API_BASE || "";
    const audioUrl = `${base}/api/audio/advisory/${encodeURIComponent(taluka)}?lang=${lang}`;
    const player = new Audio();
    activeAudioPlayer = player;

    player.onplaying = () => {
      if (activeAudioPlayer !== player) return;
      isAudioLoading = false;
      setSpeakingUI(true);
    };

    player.oncanplay = () => {
      if (activeAudioPlayer !== player) return;
      isAudioLoading = false;
    };

    player.onended = () => {
      if (activeAudioPlayer === player) {
        stopAudioSpeech();
      }
    };

    player.onerror = (e) => {
      if (activeAudioPlayer !== player) return;
      console.warn("Neural audio endpoint failed, checking fallback:", e);
      stopAudioSpeech();
      fallbackBrowserSpeech();
    };

    player.src = audioUrl;
    player.load();
    await player.play().catch((playErr) => {
      if (playErr.name === "AbortError") {
        return;
      }
      if (activeAudioPlayer === player) {
        console.warn("Audio play() promise rejected:", playErr);
        stopAudioSpeech();
        fallbackBrowserSpeech();
      }
    });
  } catch (err) {
    if (err.name !== "AbortError") {
      console.warn("Audio play exception:", err);
      stopAudioSpeech();
      fallbackBrowserSpeech();
    }
  }
}

function stopAudioSpeech() {
  isAudioLoading = false;
  if (activeAudioPlayer) {
    const player = activeAudioPlayer;
    activeAudioPlayer = null;
    try {
      player.pause();
      player.currentTime = 0;
    } catch (e) {}
    player.src = "";
  }
  if (window.speechSynthesis && window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
  }
  setSpeakingUI(false);
}

function fallbackBrowserSpeech() {
  const synth = window.speechSynthesis;
  if (!synth) return;
  const isMr = state.currentLanguage === "mr";
  const voices = synth.getVoices() || [];
  const marathiVoice = voices.find(v => v.lang.includes("mr") || v.name.toLowerCase().includes("marathi"));
  const englishVoice = voices.find(v => v.lang.includes("IN") || v.lang.startsWith("en"));

  // Only use browser speech synthesis if a real matching voice exists
  if (isMr && !marathiVoice) {
    console.info("No native Marathi voice in browser speech synthesis. Neural backend is primary.");
    if (typeof showToast === "function") {
      showToast(isMr ? "ऑडिओ सर्व्हर तयार होत आहे, कृपया १-२ सेकंद थांबा..." : "Audio server warming up, please wait a moment...", "info");
    }
    return;
  }

  const meta = state.currentData?.meta || {};
  const speechText = isMr ? `
    नमस्कार शेतकरी मित्रांनो. ${meta.taluka_mr || meta.taluka} तालुक्यासाठी आजचा कृषी सल्ला.
    पहिली गोष्ट, सिंचन नियोजन: जमिनीत चांगला वाफसा आहे, पुढील ३ ते ४ दिवस पाणी देऊ नका.
    दुसरी गोष्ट, ओलावा टिकवण्यासाठी: पिकाच्या बुडाशी पाचट पसरा, जेणेकरून ओल टिकून राहील.
    तिसरी गोष्ट, फवारणी सल्ला: पावसाचा ताण असल्यास पोटॅशियम नायट्रेटची सकाळी फवारणी करा. धन्यवाद!
  `.replace(/[*_#]/g, "").trim() : `
    Hello farmer friends. Here is today's crop advisory for ${meta.taluka} taluka.
    First, irrigation: Soil has healthy moisture, hold off watering for 3 to 4 days.
    Second, moisture conservation: Spread crop residue mulching to lock moisture.
    Third, foliar spray: Spray 1 percent Potassium Nitrate early morning. Thank you!
  `.replace(/[*_#]/g, "").trim();

  const utter = new SpeechSynthesisUtterance(speechText);
  utter.rate = 0.88;
  utter.pitch = 1.0;

  if (isMr && marathiVoice) {
    utter.voice = marathiVoice;
    utter.lang = "mr-IN";
  } else if (!isMr && englishVoice) {
    utter.voice = englishVoice;
  } else if (isMr) {
    return;
  }

  const btnSide = document.getElementById("tts-audio-btn");
  const labelSide = document.getElementById("tts-audio-label");
  const btnInline = document.getElementById("tts-inline-btn");
  const labelInline = document.getElementById("tts-inline-label");

  utter.onstart = () => {
    btnSide?.classList.add("speaking");
    btnInline?.classList.add("speaking");
    const stopHtml = `${SVG_AUDIO_STOP}<span>${isMr ? "थांबवा (Stop)" : "Stop"}</span>`;
    if (labelSide) labelSide.innerHTML = stopHtml;
    if (labelInline) labelInline.innerHTML = stopHtml;
  };

  utter.onend = utter.onerror = () => {
    btnSide?.classList.remove("speaking");
    btnInline?.classList.remove("speaking");
    const playHtml = `${SVG_AUDIO_PLAY}<span>${isMr ? "सल्ला ऐका" : "Listen"}</span>`;
    if (labelSide) labelSide.innerHTML = playHtml;
    if (labelInline) labelInline.innerHTML = playHtml;
  };

  synth.speak(utter);
}

window.toggleAudioSpeech = toggleAudioSpeech;
window.stopAudioSpeech = stopAudioSpeech;
window.openAdvisoryDrawer = function() {
  document.getElementById("modal-ai-advisory")?.classList.add("open");
  switchRightPanel('advisory');
};

// ============================================================================
// VOICE SEARCH WITH NATIVE SPEECH RECOGNITION
// ============================================================================
function initVoiceSearch() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    alert(state.currentLanguage === "mr" ? "व्हॉइस सर्च उपलब्ध नाही. क्रोम वापरा." : "Voice search not supported.");
    return;
  }

  if (state.activeSpeechRecognition) {
    try { state.activeSpeechRecognition.stop(); } catch(e){}
  }

  const rec = new SpeechRec();
  state.activeSpeechRecognition = rec;
  rec.lang = state.currentLanguage === "mr" ? "mr-IN" : "en-IN";
  rec.continuous = false;
  rec.interimResults = false;

  const micBtn = document.getElementById("voice-mic-btn");
  const searchInput = document.getElementById("taluka-search-input");

  micBtn.classList.add("listening");
  searchInput.placeholder = state.currentLanguage === "mr" 
    ? "ऐकत आहे... बोला (उदा. पैठण, बारामती)..." 
    : "Listening... speak taluka name...";

  rec.onresult = (e) => {
    const text = e.results[0][0].transcript.trim().replace(/[.,!?:;]/g, "");
    console.log("[Voice recognized]:", text);
    searchInput.value = text;
    micBtn.classList.remove("listening");
    searchInput.placeholder = state.currentLanguage === "mr"
      ? "तालुका शोधा (उदा. पैठण, बारामती, मेहकर)..."
      : "Search taluka (e.g. Paithan, Baramati)...";
    searchInput.blur();
    findAndSelectTaluka(text);
  };

  rec.onerror = () => {
    micBtn.classList.remove("listening");
    searchInput.placeholder = state.currentLanguage === "mr" ? "तालुका शोधा..." : "Search taluka...";
  };

  rec.onend = () => {
    micBtn.classList.remove("listening");
  };

  rec.start();
}

function findAndSelectTaluka(query) {
  if (!query) return;
  const searchInput = document.getElementById("taluka-search-input");
  if (searchInput) searchInput.blur();
  const autoBox = document.getElementById("autocomplete-list");
  if (autoBox) autoBox.style.display = "none";
  const clean = query.trim().toLowerCase();

  const match = state.talukasDirectory.find(t => 
    t.taluka_name.toLowerCase() === clean ||
    (t.taluka_name_mr && t.taluka_name_mr === clean) ||
    t.taluka_name.toLowerCase().includes(clean) ||
    (t.taluka_name_mr && t.taluka_name_mr.includes(clean))
  );

  if (match) {
    fetchTalukaData(match.taluka_name);
    if (state.mapInstance && match.latitude && match.longitude) {
      state.mapInstance.flyTo([match.latitude, match.longitude], 10);
    }
  } else {
    fetchTalukaData(query);
  }
}
