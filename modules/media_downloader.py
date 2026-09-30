# -*- coding: utf-8 -*-
"""
Universal Social Media & Video Downloader
Downloads Instagram Reels, YouTube Shorts & Videos, Twitter/X, Pinterest, and TikTok with 100% Full Audio & HD Video.
"""

import os
import tempfile
import yt_dlp
import asyncio
import requests
from urllib.parse import quote


def is_supported_media_url(url: str) -> bool:
    domains = [
        "instagram.com", "instagr.am", "youtube.com", "youtu.be",
        , "x.com", , ,
        "tiktok.com", "facebook.com", "fb.watch"
    ]
    u = url.lower()
    return any(d in u for d in domains)


async def download_media_file_fast(url: str, extract_audio: bool = False) -> dict:
    """
    Downloads media with full audio & video stream merged via yt-dlp.
    Returns dict with {ok: True, filepath: ..., title: ..., size_mb: ..., duration: ...}
    """
    fd, out_tmpl = tempfile.mkstemp(suffix=".%(ext)s")
    os.close(fd)

    clean_url = url.strip()

    if extract_audio:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_tmpl,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        # Merges best video + best audio stream to guarantee 100% sound
        ydl_opts = {
            "format": "best[ext=mp4][filesize<50M]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[filesize<50M]/best",
            "outtmpl": out_tmpl,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

    def _run():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=True)
                if not info:
                    return {"ok": False, "error": "Could not extract video stream."}
                
                filename = ydl.prepare_filename(info)
                if extract_audio:
                    base, _ = os.path.splitext(filename)
                    filename = base + ".mp3"

                if os.path.exists(filename):
                    size_mb = round(os.path.getsize(filename) / (1024 * 1024), 2)
                    return {
                        "ok": True,
                        "filepath": filename,
                        "title": info.get("title", "Video")[:60],
                        "duration": info.get("duration", 0),
                        "size_mb": size_mb,
                        "direct_url": info.get("url") or clean_url,
                        "source": info.get("extractor_key", "Social Media"),
                    }
                return {"ok": False, "error": "Downloaded file not found on disk."}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run)


def extract_media_info(url: str) -> dict:
    """Fast metadata extraction fallback"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return {"ok": False, "error": "Could not extract video information"}
            return {
                "ok": True,
                "title": info.get("title", "Social Video")[:60],
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail"),
                "direct_url": info.get("url") or url,
                "source": info.get("extractor_key", "Social Media"),
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}
