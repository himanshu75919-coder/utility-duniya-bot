# -*- coding: utf-8 -*-
"""
Actors & Celebrity Voice Studio — v32 REAL VOICES Edition
==========================================================
Pehle saare presets ek hi voice model (hi-IN-MadhurNeural) par rate/pitch badal ke banaye gaye the
— isliye sab ek jaise sunai dete the. Ab HAR preset ek ALAG REAL neural voice model use karta hai
(Hindi / Marathi / Telugu / Tamil / Bengali / Gujarati / Malayalam / Urdu / Indian-English / US / UK / Japanese...).

Ye asli alag voices hain — scripts nahi, alag trained neural speakers.

+ 🎚️ VOICE LAB: 26 asli voices ki list, user koi bhi chun kar apna text bolwa sakta hai
  + speed control (🐢 Slow / ▶️ Normal / ⚡ Fast / 🚀 Super Fast).
"""

import asyncio
import os
import tempfile

import edge_tts

# =====================================================================================
# SCRIPT RULES (bahut important — edge-tts ka real behaviour):
#   • Devanagari (हिंदी) text SIRF hi-IN / mr-IN voices me chalta hai
#   • Baaki saari 300+ voices Latin/English text me chalti hain
# Isliye code khud detect karta hai aur galat combo ho to Hindi voice par auto-switch karta hai,
# phir bhi wahi style (rate/pitch) lagata hai — user ko audio HAR BAAR milta hai.
# =====================================================================================
HINDI_CAPABLE_PREFIX = ("hi-IN", "mr-IN")


def text_script(text: str) -> str:
    """'devanagari' ya 'latin' detect karta hai."""
    for ch in (text or ""):
        if "\u0900" <= ch <= "\u097F":
            return "devanagari"
    return "latin"


def _gender_from_voice(voice_short: str) -> str:
    """Voice name se gender nikalta hai (Neural names me Female/Male hint hota hai)."""
    v = voice_short.lower()
    female = ("swara", "aarohi", "neerja", "dhwani", "sapna", "shruti", "pallavi", "sobhana", "gul",
              "aria", "jenny", "michelle", "ana", "ava", "emma", "sonia", "libby", "maisie", "nanami",
              "denise", "zariyah", "tanishaa", "svetlana", "elvira", "ximena", "katja", "vivienne")
    return "f" if any(f in v for f in female) else "m"


HINDI_FALLBACK = {"m": "hi-IN-MadhurNeural", "f": "hi-IN-SwaraNeural"}
LATIN_FALLBACK = {"m": "en-US-GuyNeural", "f": "en-US-AriaNeural"}


# =====================================================================================
# ACTOR / CHARACTER PRESETS — har ek ka ALAG REAL voice model
# =====================================================================================
ACTOR_VOICE_PRESETS = {
    # ---- INDIAN MALE ----
    "don_deep": {
        "name": "👑 Deep Don / Villain Baritone",
        "voice": "hi-IN-MadhurNeural",
        "rate": "-14%",
        "pitch": "-25Hz",
        "gender": "m",
        "desc": "Asli Hindi male voice — bahut gehri, dabbang villain style",
        "lang": "Hindi 🇮🇳",
    },
    "rowdy_marathi": {
        "name": "🔥 Rowdy Gangster (Marathi timbre)",
        "voice": "mr-IN-ManoharNeural",
        "rate": "+4%",
        "pitch": "-12Hz",
        "gender": "m",
        "desc": "Marathi male voice — desi rowdy/action attitude",
        "lang": "Marathi 🇮🇳",
    },
    "south_mass_hero": {
        "name": "💥 South Mass Hero (Telugu)",
        "voice": "te-IN-MohanNeural",
        "rate": "+2%",
        "pitch": "-8Hz",
        "gender": "m",
        "desc": "Telugu male voice — mass dialogue delivery",
        "lang": "Telugu 🇮🇳",
    },
    "tamil_action": {
        "name": "⚔️ Tamil Action Rowdy",
        "voice": "ta-IN-ValluvarNeural",
        "rate": "+6%",
        "pitch": "-10Hz",
        "gender": "m",
        "desc": "Tamil male voice — action/fight dialogue",
        "lang": "Tamil 🇮🇳",
    },
    "bengali_hero": {
        "name": "🎭 Bengali Hero / Emotional",
        "voice": "bn-IN-BashkarNeural",
        "rate": "+0%",
        "pitch": "-6Hz",
        "gender": "m",
        "desc": "Bengali male voice — emotional/bhaav wali delivery",
        "lang": "Bengali 🇮🇳",
    },
    "gujarati_anchor": {
        "name": "🗞️ News Anchor (Gujarati timbre)",
        "voice": "gu-IN-NiranjanNeural",
        "rate": "+14%",
        "pitch": "+3Hz",
        "gender": "m",
        "desc": "Gujarati male voice — energetic news reader",
        "lang": "Gujarati 🇮🇳",
    },
    "urdu_shayar": {
        "name": "🎙️ Urdu Shayari / Ghazal Mood",
        "voice": "ur-IN-SalmanNeural",
        "rate": "-12%",
        "pitch": "-5Hz",
        "gender": "m",
        "desc": "Urdu male voice — shaayari, dheemi aur asardaar",
        "lang": "Urdu 🇮🇳",
    },
    "malayalam_cool": {
        "name": "😎 Malayalam Cool Guy",
        "voice": "ml-IN-MidhunNeural",
        "rate": "+6%",
        "pitch": "-4Hz",
        "gender": "m",
        "desc": "Malayalam male voice — relax aur cool tone",
        "lang": "Malayalam 🇮🇳",
    },
    # ---- INDIAN FEMALE ----
    "sweet_girlfriend": {
        "name": "🌸 Sweet Girlfriend Voice (Hi)",
        "voice": "hi-IN-SwaraNeural",
        "rate": "+2%",
        "pitch": "+12Hz",
        "gender": "f",
        "desc": "Asli Hindi female voice — pyaar bhara soft tone",
        "lang": "Hindi 🇮🇳",
    },
    "kannada_didi": {
        "name": "💐 Didi / Caring Voice (Kannada)",
        "voice": "kn-IN-SapnaNeural",
        "rate": "-4%",
        "pitch": "+2Hz",
        "gender": "f",
        "desc": "Kannada female voice — warm, apnapan wali",
        "lang": "Kannada 🇮🇳",
    },
    "telegu_teacher": {
        "name": "👩‍🏫 Teacher Didi (Telugu)",
        "voice": "te-IN-ShrutiNeural",
        "rate": "+0%",
        "pitch": "+4Hz",
        "gender": "f",
        "desc": "Telugu female voice — clear padhaane wali tone",
        "lang": "Telugu 🇮🇳",
    },
    "tamil_amma": {
        "name": "🤱 Maa / Amma Voice (Tamil)",
        "voice": "ta-IN-PallaviNeural",
        "rate": "-4%",
        "pitch": "+0Hz",
        "gender": "f",
        "desc": "Tamil female voice — maa jaisi apnapan wali",
        "lang": "Tamil 🇮🇳",
    },
    "indian_english_madam": {
        "name": "🇮🇳 Indian English Madam",
        "voice": "en-IN-NeerjaExpressiveNeural",
        "rate": "+0%",
        "pitch": "+3Hz",
        "gender": "f",
        "desc": "Indian English female — study/corporate explanation",
        "lang": "Indian English",
    },
    # ---- INTERNATIONAL ----
    "hollywood_trailer": {
        "name": "🎬 Hollywood Trailer Narrator",
        "voice": "en-US-ChristopherNeural",
        "rate": "-16%",
        "pitch": "-20Hz",
        "gender": "m",
        "desc": "US male voice — blockbuster trailer jaisa",
        "lang": "English 🇺🇸",
    },
    "uk_documentary": {
        "name": "📽️ BBC Documentary Voice",
        "voice": "en-GB-RyanNeural",
        "rate": "-6%",
        "pitch": "-6Hz",
        "gender": "m",
        "desc": "British male voice — documentary narration",
        "lang": "English 🇬🇧",
    },
    "indian_english_pro": {
        "name": "💼 Indian English Professional",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "gender": "m",
        "desc": "Indian English male — interview/presentation",
        "lang": "Indian English",
    },
    "spooky_demon": {
        "name": "😈 Demon / Ghost Voice",
        "voice": "en-US-EricNeural",
        "rate": "-28%",
        "pitch": "-38Hz",
        "gender": "m",
        "desc": "US male voice — bhoot/daemon wala darawana tone",
        "lang": "English 🇺🇸",
    },
    "anime_girl": {
        "name": "🎀 Cute Anime Girl",
        "voice": "ja-JP-NanamiNeural",
        "rate": "+12%",
        "pitch": "+18Hz",
        "gender": "f",
        "desc": "Japanese female voice — anime character style",
        "lang": "Japanese 🇯🇵",
    },
    "cute_kid": {
        "name": "🧒 Bachche Jaisi Awaaz",
        "voice": "en-US-AnaNeural",
        "rate": "+6%",
        "pitch": "+12Hz",
        "gender": "f",
        "desc": "US kid voice (asli child neural model)",
        "lang": "English 🇺🇸",
    },
    "robot_ai": {
        "name": "🤖 Robot / AI Computer",
        "voice": "en-US-SteffanNeural",
        "rate": "-10%",
        "pitch": "-14Hz",
        "gender": "m",
        "desc": "US male voice — machine/AI jaisa flat tone",
        "lang": "English 🇺🇸",
    },
    "arabic_voice": {
        "name": "🕌 Arabic Voice",
        "voice": "ar-SA-HamedNeural",
        "rate": "-4%",
        "pitch": "-6Hz",
        "gender": "m",
        "desc": "Saudi male voice — Arabic script ke liye best",
        "lang": "Arabic 🇸🇦",
    },
    "french_voice": {
        "name": "🥐 French Voice",
        "voice": "fr-FR-HenriNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "gender": "m",
        "desc": "French male voice",
        "lang": "French 🇫🇷",
    },
    "spanish_voice": {
        "name": "💃 Spanish Voice",
        "voice": "es-ES-AlvaroNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "gender": "m",
        "desc": "Spanish male voice",
        "lang": "Spanish 🇪🇸",
    },
    "russian_voice": {
        "name": "❄️ Russian Voice",
        "voice": "ru-RU-DmitryNeural",
        "rate": "-2%",
        "pitch": "-4Hz",
        "gender": "m",
        "desc": "Russian male voice",
        "lang": "Russian 🇷🇺",
    },
}


# =====================================================================================
# VOICE LAB — 28 asli voices (user khud chunta hai)
# =====================================================================================
VOICE_LAB = [
    ("hi-m", "🇮🇳 Hindi Male (Madhur)", "hi-IN-MadhurNeural"),
    ("hi-f", "🇮🇳 Hindi Female (Swara)", "hi-IN-SwaraNeural"),
    ("enin-m", "🇮🇳 Indian English Male (Prabhat)", "en-IN-PrabhatNeural"),
    ("enin-f", "🇮🇳 Indian English Female (Neerja)", "en-IN-NeerjaExpressiveNeural"),
    ("bn-m", "🇧🇩 Bengali Male (Bashkar)", "bn-IN-BashkarNeural"),
    ("bn-f", "Bengali Female (Tanishaa)", "bn-IN-TanishaaNeural"),
    ("ta-m", "Tamil Male (Valluvar)", "ta-IN-ValluvarNeural"),
    ("ta-f", "Tamil Female (Pallavi)", "ta-IN-PallaviNeural"),
    ("te-m", "Telugu Male (Mohan)", "te-IN-MohanNeural"),
    ("te-f", "Telugu Female (Shruti)", "te-IN-ShrutiNeural"),
    ("mr-m", "Marathi Male (Manohar)", "mr-IN-ManoharNeural"),
    ("mr-f", "Marathi Female (Aarohi)", "mr-IN-AarohiNeural"),
    ("gu-m", "Gujarati Male (Niranjan)", "gu-IN-NiranjanNeural"),
    ("gu-f", "Gujarati Female (Dhwani)", "gu-IN-DhwaniNeural"),
    ("kn-m", "Kannada Male (Gagan)", "kn-IN-GaganNeural"),
    ("kn-f", "Kannada Female (Sapna)", "kn-IN-SapnaNeural"),
    ("ml-m", "Malayalam Male (Midhun)", "ml-IN-MidhunNeural"),
    ("ml-f", "Malayalam Female (Sobhana)", "ml-IN-SobhanaNeural"),
    ("ur-m", "Urdu Male (Salman)", "ur-IN-SalmanNeural"),
    ("ur-f", "Urdu Female (Gul)", "ur-IN-GulNeural"),
    ("us-m1", "US Male (Guy)", "en-US-GuyNeural"),
    ("us-m2", "US Male Deep (Christopher)", "en-US-ChristopherNeural"),
    ("us-f1", "US Female (Aria)", "en-US-AriaNeural"),
    ("uk-m", "UK Male (Ryan)", "en-GB-RyanNeural"),
    ("uk-f", "UK Female (Sonia)", "en-GB-SoniaNeural"),
    ("jp-f", "Japanese Female (Nanami)", "ja-JP-NanamiNeural"),
    ("ar-m", "Arabic Male (Hamed)", "ar-SA-HamedNeural"),
    ("fr-f", "French Female (Denise)", "fr-FR-DeniseNeural"),
    ("es-m", "Spanish Male (Alvaro)", "es-ES-AlvaroNeural"),
    ("de-m", "German Male (Conrad)", "de-DE-ConradNeural"),
]

VOICE_LAB_MAP = {k: (label, short) for k, label, short in VOICE_LAB}

# Agent-style rate (voice lab)
VOICE_SPEEDS = {
    "slow": ("🐢 Dheemi", "-25%"),
    "normal": ("▶️ Normal", "+0%"),
    "fast": ("⚡ Tez", "+25%"),
    "superfast": ("🚀 Bahut Tez", "+50%"),
}


def voice_label(preset_key: str) -> str:
    p = ACTOR_VOICE_PRESETS.get(preset_key)
    return p["name"] if p else "Voice"


# =====================================================================================
# GENERATORS
# =====================================================================================
def _outpath(outpath=None):
    if outpath:
        return outpath
    fd, path = tempfile.mkstemp(suffix=".mp3", prefix="voice_")
    os.close(fd)
    return path


def pick_voice_for_text(text: str, preset_key: str):
    """
    Text ka script dekh kar sahi voice chunta hai.
    Returns (voice, rate, pitch, note) — note me batate hain ki auto-switch hua ya nahi.
    """
    preset = ACTOR_VOICE_PRESETS.get(preset_key) or ACTOR_VOICE_PRESETS["don_deep"]
    voice, rate, pitch = preset["voice"], preset["rate"], preset["pitch"]
    gender = preset.get("gender") or _gender_from_voice(voice)

    if text_script(text) == "devanagari" and not voice.startswith(HINDI_CAPABLE_PREFIX):
        # Hindi text + non-Hindi voice = engine audio nahi deta (verified). Hindi voice par switch.
        fb = HINDI_FALLBACK[gender]
        note = (f"ℹ️ Aapka text Hindi (Devanagari) me tha, isliye <b>{fb.split('-')[2].replace('Neural','')}</b> "
                f"Hindi voice use ki — same style (rate/pitch) ke saath. English text bhejte to "
                f"<b>{preset['lang']}</b> voice lagti.")
        return fb, rate, pitch, note
    return voice, rate, pitch, ""


async def _synth(text, voice, rate, pitch, path, tries=3):
    last = None
    for i in range(tries):
        try:
            c = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
            await c.save(path)
            if os.path.exists(path) and os.path.getsize(path) > 2000:
                return True
            last = "empty audio"
        except Exception as e:
            last = str(e)[:80]
        await asyncio.sleep(1.2 * (i + 1))
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass
    raise RuntimeError(f"Voice engine ne audio nahi diya ({last}). 20-30 second baad dobara try karein.")


async def generate_actor_voice(text: str, preset_key: str = "don_deep", outpath: str = None):
    """
    Preset wali ASLI voice me audio banata hai.
    Returns (path, info_dict) — info me voice name, note (auto-switch), preset name.
    """
    text = (text or "").strip()[:1500]
    preset = ACTOR_VOICE_PRESETS.get(preset_key) or ACTOR_VOICE_PRESETS["don_deep"]
    voice, rate, pitch, note = pick_voice_for_text(text, preset_key)
    path = _outpath(outpath)

    try:
        await _synth(text, voice, rate, pitch, path)
    except Exception as first_err:
        # Fallback: script-compatible standard voice (audio HAR BAAR milega)
        gender = preset.get("gender") or _gender_from_voice(voice)
        fb = HINDI_FALLBACK[gender] if text_script(text) == "devanagari" else LATIN_FALLBACK[gender]
        if fb != voice:
            await _synth(text, fb, "+0%", "-4Hz", path)
            voice = fb
            note = (note + "\n" if note else "") + f"ℹ️ Pehli voice busy thi, backup voice use ki (<b>{fb}</b>)."
        else:
            raise first_err

    return path, {
        "preset": preset["name"],
        "voice": voice,
        "voice_short": voice.split("-")[-1].replace("Neural", ""),
        "lang": preset.get("lang", ""),
        "note": note,
    }


async def generate_voice(text: str, voice_short: str, rate: str = "+0%", pitch: str = "+0Hz",
                         outpath: str = None, label: str = ""):
    """
    Voice Lab: koi bhi asli voice model + speed.
    Devanagari text + non-Hindi voice ho to auto-switch (warna engine audio nahi deta).
    Returns (path, info_dict)
    """
    text = (text or "").strip()[:1500]
    note = ""
    voice = voice_short
    if text_script(text) == "devanagari" and not voice.startswith(HINDI_CAPABLE_PREFIX):
        gender = _gender_from_voice(voice)
        voice = HINDI_FALLBACK[gender]
        note = (f"ℹ️ Hindi text ke liye Hindi voice (<b>{voice.split('-')[2].replace('Neural','')}</b>) use ki — "
                f"English text bhejte to aapki chuni hui voice chalti.")
    path = _outpath(outpath)
    try:
        await _synth(text, voice, rate, pitch, path)
    except Exception as first_err:
        gender = _gender_from_voice(voice)
        fb = HINDI_FALLBACK[gender] if text_script(text) == "devanagari" else LATIN_FALLBACK[gender]
        if fb != voice:
            await _synth(text, fb, rate, pitch, path)
            voice = fb
            note += ("\n" if note else "") + f"ℹ️ Backup voice use ki (<b>{fb}</b>)."
        else:
            raise first_err
    return path, {"voice": voice, "label": label or voice, "note": note}
