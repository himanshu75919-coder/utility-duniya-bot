# -*- coding: utf-8 -*-
"""
Instagram Reels, Posts, Photos & Stories Downloader
Downloads Instagram Reels, Videos, Photos, and Public Stories with 100% Full Audio & Ultra-HD Quality.
"""

import io
import os
import re
import asyncio
import requests
import yt_dlp
from urllib.parse import quote

UA_HEADER = {"User-Agent": "TelegramBot (like TwitterBot)"}


def is_instagram_url(url: str) -> bool:
    domains = ["instagram.com", "instagr.am"]
    u = url.lower()
    return any(d in u for d in domains)


def download_instagram_media(url: str) -> dict:
    """
    Downloads Instagram Reel, Video, Photo, or Story using high-speed direct CDN bypass.
    Returns: {ok: True, type: 'video'|'photo', bytes: bytes, size_mb: float}
    """
    clean = url.split("?")[0].rstrip("/")
    if not clean.startswith("http"):
        clean = "https://" + clean.lstrip("/")

    # Method 1: KKInstagram Direct CDN Proxy (100% Full Audio & HD Media)
    try:
        kk_url = clean.replace("instagram.com", "kkinstagram.com").replace("instagr.am", "kkinstagram.com")
        r = requests.get(kk_url, headers=UA_HEADER, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            c_type = r.headers.get("content-type", "")
            # Check if video (mp4 / ftyp / moov)
            if "video" in c_type or r.content[:4] == b"\x00\x00\x00\x18" or b"ftyp" in r.content[:20]:
                return {
                    "ok": True,
                    "type": "video",
                    "bytes": r.content,
                    "size_mb": round(len(r.content) / (1024 * 1024), 2),
                }
            else:
                return {
                    "ok": True,
                    "type": "photo",
                    "bytes": r.content,
                    "size_mb": round(len(r.content) / (1024 * 1024), 2),
                }
    except Exception:
        pass

    # Method 2: yt-dlp fallback for video reels
    try:
        ydl_opts = {
            "format": "best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean, download=False)
            if info:
                direct_url = info.get("url")
                if direct_url:
                    r_dl = requests.get(direct_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    if r_dl.status_code == 200:
                        return {
                            "ok": True,
                            "type": "video",
                            "bytes": r_dl.content,
                            "size_mb": round(len(r_dl.content) / (1024 * 1024), 2),
                        }
    except Exception:
        pass

    return {"ok": False, "error": "Could not download media. Please ensure the post/story is public."}


async def download_instagram_async(url: str) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_instagram_media, url)
