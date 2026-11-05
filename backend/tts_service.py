"""
backend/tts_service.py: High-fidelity natural Marathi & English neural audio generator.
Uses Microsoft Edge Neural voices (mr-IN-ManoharNeural / en-IN-PrabhatNeural) with automatic
fallback to gTTS, task deduplication, atomic file writes, and disk caching for instant low-latency playback.
"""

import os
import re
import hashlib
import asyncio
from typing import Optional, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "frontend", "assets", "audio", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

class TTSService:
    def __init__(self):
        self.mr_voice = "mr-IN-ManoharNeural"
        self.en_voice = "en-IN-PrabhatNeural"
        self._in_flight: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def _build_script(self, taluka_data: dict, lang: str = "mr") -> str:
        meta = taluka_data.get("meta", {})
        adv = taluka_data.get("advisory", {})
        acts = adv.get("prescriptive_actions", {})
        
        taluka_mr = meta.get("taluka_mr") or meta.get("taluka") or "आपल्या"
        taluka_en = meta.get("taluka") or "your"
        
        if lang == "mr":
            uni_anchor = adv.get("university_anchor", {})
            uni_name = uni_anchor.get("university_name_mr", "कृषी विद्यापीठ")
            
            irrigation = (acts.get("irrigation_strategy", {}).get("mr") or 
                          "जमिनीत चांगला वाफसा आहे, पुढील तीन ते चार दिवस पिकाला पाणी देऊ नका. शेतात पाणी साचणार नाही याची काळजी घ्या.")
            moisture = (acts.get("moisture_conservation", {}).get("mr") or 
                        "जमिनीतील ओल टिकवण्यासाठी पिकाच्या ओळींत पाचट किंवा काडीकचरा पसरा. कडक उन्हातही ओल दहा ते बारा दिवस टिकून राहील.")
            foliar = (acts.get("foliar_and_nutrients", {}).get("mr") or 
                      "पावसाचा ताण असल्यास पीक ताजेतवाने राहण्यासाठी दहा लिटर पाण्यात शंभर ग्रॅम पोटॅशियम नायट्रेट मिसळून सकाळी फवारणी करा.")
            
            script = f"""
            नमस्कार शेतकरी मित्रांनो. {taluka_mr} तालुक्यासाठी {uni_name} यांचा आजचा अधिकृत कृषी सल्ला ऐका.
            पहिली गोष्ट, सिंचन नियोजन: {irrigation}
            दुसरी गोष्ट, ओलावा टिकवण्यासाठी: {moisture}
            तिसरी गोष्ट, खत व फवारणी: {foliar}
            धन्यवाद, आणि आपली व पिकांची काळजी घ्या!
            """
        else:
            uni_anchor = adv.get("university_anchor", {})
            uni_name = uni_anchor.get("university_name_en", "Agricultural University")
            
            irrigation = (acts.get("irrigation_strategy", {}).get("en") or 
                          "Soil has a healthy moisture balance. Please hold off watering for the next 3 to 4 days, and keep field drainage clear.")
            moisture = (acts.get("moisture_conservation", {}).get("en") or 
                        "Spread straw or crop residue along crop rows as mulching to shade the soil and retain moisture for 10 to 12 days.")
            foliar = (acts.get("foliar_and_nutrients", {}).get("en") or 
                      "If dry weather persists, spray 1 percent Potassium Nitrate, which is 100 grams in 10 liters of water, in the early morning to prevent heat stress.")
            
            script = f"""
            Hello farmer friends. Here is today's official crop advisory for {taluka_en} taluka from {uni_name}.
            First, regarding irrigation: {irrigation}
            Second, for moisture conservation: {moisture}
            Third, foliar nutrition and fertilizers: {foliar}
            Thank you, and take good care of your crops!
            """
        
        # Clean extra whitespace
        return re.sub(r"\s+", " ", script).strip()

    async def generate_advisory_audio(self, taluka_data: dict, lang: str = "mr") -> str:
        """
        Generates or retrieves cached MP3 audio file.
        Deduplicates concurrent in-flight requests and writes atomically.
        Returns the absolute filepath to the MP3.
        """
        if lang not in {"mr", "en"}:
            raise ValueError("Invalid audio language code. Only 'mr' and 'en' are permitted.")

        meta = taluka_data.get("meta", {})
        raw_name = meta.get("taluka", "general").lower()
        taluka_name = re.sub(r"[^a-zA-Z0-9_-]", "", raw_name)
        diag = taluka_data.get("live_diagnosis", {})
        cat_code = diag.get("category_code", 0)
        
        cache_key = f"{taluka_name}_{lang}_{cat_code}"
        filename = f"{cache_key}.mp3"
        filepath = os.path.join(CACHE_DIR, filename)

        resolved_path = os.path.abspath(filepath)
        cache_root = os.path.abspath(CACHE_DIR)
        if os.path.commonpath([resolved_path, cache_root]) != cache_root:
            raise ValueError("Illegal path traversal sequence detected.")

        # Return cached file if valid and complete
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            return filepath

        # Concurrency deduplication: if already generating, await that exact task
        async with self._lock:
            if cache_key in self._in_flight:
                task = self._in_flight[cache_key]
            else:
                task = asyncio.create_task(self._generate_file(taluka_data, lang, filepath, cache_key))
                self._in_flight[cache_key] = task

        try:
            return await task
        finally:
            async with self._lock:
                self._in_flight.pop(cache_key, None)

    async def _generate_file(self, taluka_data: dict, lang: str, filepath: str, cache_key: str) -> str:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            return filepath

        script_text = self._build_script(taluka_data, lang=lang)
        temp_filepath = f"{filepath}.{os.getpid()}_{id(asyncio.current_task())}.tmp"

        try:
            # 1. Try Neural Edge-TTS (Natural Broadcast Quality)
            try:
                import edge_tts
                voice = self.mr_voice if lang == "mr" else self.en_voice
                rate = "-4%"
                communicate = edge_tts.Communicate(script_text, voice, rate=rate)
                await communicate.save(temp_filepath)
                if os.path.exists(temp_filepath) and os.path.getsize(temp_filepath) > 1000:
                    os.replace(temp_filepath, filepath)
                    return filepath
            except Exception as e:
                print(f"[TTS] Edge-TTS notice for {cache_key}: {e}, falling back to gTTS...")

            # 2. Fallback to gTTS (Google Marathi/English)
            try:
                from gtts import gTTS
                tts_lang = "mr" if lang == "mr" else "en"
                tts = gTTS(text=script_text, lang=tts_lang, slow=False)
                await asyncio.to_thread(tts.save, temp_filepath)
                if os.path.exists(temp_filepath) and os.path.getsize(temp_filepath) > 1000:
                    os.replace(temp_filepath, filepath)
                    return filepath
            except Exception as e:
                print(f"[TTS] gTTS fallback error for {cache_key}: {e}")

            raise RuntimeError("Failed to generate audio via both primary and fallback engines.")
        finally:
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass

tts_service = TTSService()
