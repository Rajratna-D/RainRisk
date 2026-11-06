const fs = require('fs');
const vm = require('vm');

// Mock window and document
const elements = {};
function getEl(id) {
  if (!elements[id]) {
    elements[id] = { 
      id,
      textContent: '', 
      innerHTML: '', 
      style: {}, 
      classList: { add(){}, remove(){}, contains(){ return false; } }, 
      setAttribute(){},
      value: ''
    };
  }
  return elements[id];
}
const documentMock = {
  getElementById: getEl,
  querySelectorAll: () => [],
  title: ''
};
const windowMock = {
  location: { hostname: 'localhost' },
  document: documentMock,
  speechSynthesis: null
};

// Populate initial mock elements matching index.html
getEl("val-climate").textContent = "१८६.८";
getEl("val-moisture").textContent = "६६.९";
getEl("val-light").textContent = "७२.५";
getEl("val-ec").textContent = "४";
getEl("val-growth").textContent = "८२४";
getEl("val-power").textContent = "४";
getEl("val-water-flow").textContent = "७८% उपलब्ध";
getEl("side-dam-level").textContent = "७२.५ %";
getEl("side-soil-level").textContent = "६६.९ %";
getEl("hero-taluka-text").textContent = "पैठण";
getEl("hero-district-text").textContent = "छत्रपती संभाजीनगर";
getEl("act-text-irrigation").textContent = "जमिनीत ओलावा चांगला असल्याने पुढील ४ दिवस पाणी देण्याची गरज नाही. हलके पाणी द्यावे.";
getEl("act-text-conservation").textContent = "पिकाच्या ओळींत पाचट किंवा भुसा आच्छादन (Mulching) केल्यास बाष्पीभवन रोखले जाईल.";
getEl("act-text-nutrients").textContent = "पावसात खंड पडल्यास १% पोटॅशियम नायट्रेट (१०० ग्रॅम प्रति १० लिटर पाणी) फवारावे.";

const sandbox = {
  window: windowMock,
  document: documentMock,
  console: console,
  setTimeout: setTimeout,
  clearTimeout: clearTimeout,
  Math: Math,
  String: String,
  parseInt: parseInt
};
sandbox.global = sandbox;
sandbox.window.window = sandbox.window;
vm.createContext(sandbox);

// Load files in the exact order as index.html
const stateCode = fs.readFileSync('frontend/js/state.js', 'utf8');
const advCode = fs.readFileSync('frontend/js/advisory.js', 'utf8');
const dashCode = fs.readFileSync('frontend/js/dashboard.js', 'utf8');
const i18nCode = fs.readFileSync('frontend/js/i18n.js', 'utf8');

vm.runInContext(stateCode, sandbox);
vm.runInContext(advCode, sandbox);
vm.runInContext(dashCode, sandbox);
vm.runInContext(i18nCode, sandbox);

console.log("=== Testing Numeral Formatting ===");
console.log("186.8 -> mr:", sandbox.formatNumber(186.8, true));
console.log("१८६.८ -> en:", sandbox.formatNumber("१८६.८", false));
console.log("४ -> en:", sandbox.formatNumber("४", false));
console.log("७२.५ % -> en:", sandbox.formatNumber("७२.५ %", false));
console.log("824 -> mr:", sandbox.formatNumber("824", true));

if (sandbox.formatNumber("१८६.८", false) !== "186.8") throw new Error("formatNumber en failed");
if (sandbox.formatNumber(186.8, true) !== "१८६.८") throw new Error("formatNumber mr failed");

console.log("\n=== Testing Initial Boot State ===");
const appState = sandbox.window.state;
console.log("state.currentData exists?", !!appState.currentData);
console.log("state.currentLanguage:", appState.currentLanguage);

console.log("\n=== Testing Immediate Switch to English (Race Condition Simulation) ===");
sandbox.window.toggleLanguage(); // Switch to "en"
console.log("After toggle, state.currentLanguage:", appState.currentLanguage);
console.log("hero-taluka-text:", getEl("hero-taluka-text").textContent);
console.log("val-climate:", getEl("val-climate").textContent);
console.log("val-moisture:", getEl("val-moisture").textContent);
console.log("val-light:", getEl("val-light").textContent);
console.log("val-ec:", getEl("val-ec").textContent);
console.log("val-growth:", getEl("val-growth").textContent);
console.log("val-power:", getEl("val-power").textContent);
console.log("val-water-flow:", getEl("val-water-flow").textContent);
console.log("side-dam-level:", getEl("side-dam-level").textContent);
console.log("side-soil-level:", getEl("side-soil-level").textContent);
console.log("act-text-irrigation:", getEl("act-text-irrigation").textContent);

// Verify NO Devanagari numerals remain in metric cards
const checkIds = [
  "val-climate", "val-moisture", "val-light", "val-ec",
  "val-growth", "val-power", "val-water-flow", "side-dam-level", "side-soil-level"
];
const mrRegex = /[\u0966-\u096F]/;

for (const id of checkIds) {
  const val = getEl(id).textContent;
  if (mrRegex.test(val)) {
    throw new Error(`Metric element #${id} still contains Devanagari numerals: ${val}`);
  }
}
console.log("[PASS] All 9 metric elements are 100% clean English numerals!");

// Verify text converted to English
if (getEl("hero-taluka-text").textContent !== "Paithan") {
  throw new Error(`Hero taluka text expected 'Paithan', got '${getEl("hero-taluka-text").textContent}'`);
}
if (/[\u0900-\u097F]/.test(getEl("act-text-irrigation").textContent)) {
  throw new Error(`Advisory irrigation text still contains Marathi: ${getEl("act-text-irrigation").textContent}`);
}
console.log("[PASS] Text converted cleanly to English!");

console.log("\n=== Testing Toggle Back to Marathi ===");
sandbox.window.toggleLanguage(); // Switch back to "mr"
console.log("After toggle back, state.currentLanguage:", appState.currentLanguage);
console.log("hero-taluka-text:", getEl("hero-taluka-text").textContent);
console.log("val-climate:", getEl("val-climate").textContent);
console.log("val-moisture:", getEl("val-moisture").textContent);

if (getEl("val-climate").textContent !== "१८६.८") {
  throw new Error(`Expected Marathi numerals '१८६.८', got '${getEl("val-climate").textContent}'`);
}
if (getEl("hero-taluka-text").textContent !== "पैठण") {
  throw new Error(`Hero taluka text expected 'पैठण', got '${getEl("hero-taluka-text").textContent}'`);
}
console.log("[PASS] Toggle back to Marathi restored Devanagari numerals and Marathi text perfectly!");

console.log("\n>>> ALL CLIENT-SIDE i18n VERIFICATIONS PASSED 100% <<<");
