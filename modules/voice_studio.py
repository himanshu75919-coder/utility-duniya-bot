# -*- coding: utf-8 -*-
"""
AI Voice Clone & Celebrity Voiceover Studio
Fast, realistic Text-to-Speech engine powered by edge-tts with rich presets.
"""

import os
import tempfile
import edge_tts

VOICE_PRESETS = {
    "modi": {
        "name": "🎙️ Deep Hindi Male (Modi / Narrator Style)",
        "voice": "hi-IN-MadhurNeural",
        "rate": "+0%",
        "pitch": "-3Hz",
    },
    "swara": {
        "name": "🌸 Sweet Hindi Female (Swara)",
        "voice": "hi-IN-SwaraNeural",
        "rate": "+4%",
        "pitch": "+0Hz",
    },
    "alpha": {
        "name": "⚡ Viral Deep Alpha Male (Hormozi / Sigma)",
        "voice": "en-US-ChristopherNeural",
        "rate": "+0%",
        "pitch": "-4Hz",
    },
    "sports": {
        "name": "🏏 High-Energy Sports Commentary",
        "voice": "hi-IN-MadhurNeural",
        "rate": "+15%",
        "pitch": "+4Hz",
    },
    "anime": {
        "name": "🎭 Cute Anime Girl Voice",
        "voice": "ja-JP-NanamiNeural",
        "rate": "+8%",
        "pitch": "+10Hz",
    },
    "ind_eng_m": {
        "name": "🇮🇳 Indian English (Prabhat Male)",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    },
    "ind_eng_f": {
        "name": "🇮🇳 Indian English (Neerja Female)",
        "voice": "en-IN-NeerjaNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    },
    "uk_male": {
        "name": "🇬🇧 British Accent (Ryan Male)",
        "voice": "en-GB-RyanNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    },
    "uk_female": {
        "name": "🇬🇧 British Accent (Sonia Female)",
        "voice": "en-GB-SoniaNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    },
}


async def generate_voice(text: str, preset_key: str = "modi", outpath: str = None) -> str:
    """
    Generates realistic speech audio file from text within 1-2 seconds.
    Returns the path of the generated .mp3 file.
    """
    preset = VOICE_PRESETS.get(preset_key, VOICE_PRESETS["modi"])
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
