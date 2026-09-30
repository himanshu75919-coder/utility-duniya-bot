# -*- coding: utf-8 -*-
"""
Text to Actors & Celebrity Voice Studio
Realistic Actor, Don, Superhero, and Character Voice Synthesizer powered by Neural Audio Engines.
"""

import os
import tempfile
import edge_tts

ACTOR_VOICE_PRESETS = {
    "don_amitabh": {
        "name": "👑 Amitabh Bachchan / Deep Don Style",
        "voice": "hi-IN-MadhurNeural",
        "rate": "-10%",
        "pitch": "-18Hz",
        "desc": "Heavy, deep authoritative baritone voice",
    },
    "modi_speech": {
        "name": "🎙️ Narendra Modi / Orator Speech Style",
        "voice": "hi-IN-MadhurNeural",
        "rate": "-8%",
        "pitch": "-5Hz",
        "desc": "Calm, deep cadence of official public speech",
    },
    "pushpa_rowdy": {
        "name": "🔥 Pushpa / South Action Rowdy Style",
        "voice": "hi-IN-MadhurNeural",
        "rate": "+5%",
        "pitch": "-12Hz",
        "desc": "Rough, aggressive gangster attitude voice",
    },
    "carry_rage": {
        "name": "⚡ CarryMinati / Aggressive Rant Style",
        "voice": "hi-IN-MadhurNeural",
        "rate": "+22%",
        "pitch": "+6Hz",
        "desc": "Fast, high-energy roast voice",
    },
    "srk_romantic": {
        "name": "🎬 Shah Rukh Khan / Smooth Hero Style",
        "voice": "hi-IN-MadhurNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "desc": "Warm, charming Bollywood hero voice",
    },
    "heroine_sweet": {
        "name": "🌸 Sweet Bollywood Heroine Voice",
        "voice": "hi-IN-SwaraNeural",
        "rate": "+5%",
        "pitch": "+6Hz",
        "desc": "Soft, melodic feminine expressive voice",
    },
    "epic_narrator": {
        "name": "🎙️ Hollywood Movie Trailer Epic Narrator",
        "voice": "en-US-ChristopherNeural",
        "rate": "-12%",
        "pitch": "-22Hz",
        "desc": "Morgan Freeman / Hollywood deep trailer voice",
    },
    "anime_cute": {
        "name": "🎭 Cute Anime / Cartoon Character Voice",
        "voice": "ja-JP-NanamiNeural",
        "rate": "+10%",
        "pitch": "+12Hz",
        "desc": "High-pitched energetic anime character voice",
    },
    "sports_commentary": {
        "name": "🏏 High-Energy Sports / Cricket Commentary",
        "voice": "hi-IN-MadhurNeural",
        "rate": "+18%",
        "pitch": "+4Hz",
        "desc": "Fast paced match commentary excitement",
    },
    "ind_eng_pro": {
        "name": "🇮🇳 Indian English Professional Speaker",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "desc": "Clear corporate Indian English voice",
    },
    "uk_gentleman": {
        "name": "🇬🇧 British Gentleman Royal Voice",
        "voice": "en-GB-RyanNeural",
        "rate": "-5%",
        "pitch": "-4Hz",
        "desc": "Refined British BBC accent",
    },
}


async def generate_actor_voice(text: str, preset_key: str = "don_amitabh", outpath: str = None) -> str:
    """
    Generates ultra-realistic actor/celebrity styled voice note from text in under 1 second.
    """
    preset = ACTOR_VOICE_PRESETS.get(preset_key, ACTOR_VOICE_PRESETS["don_amitabh"])
    if not outpath:
        fd, outpath = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

    communicate = edge_tts.Communicate(
        text=text[:1500],
        voice=preset["voice"],
        rate=preset["rate"],
        pitch=preset["pitch"],
    )
    await communicate.save(outpath)
    return outpath
