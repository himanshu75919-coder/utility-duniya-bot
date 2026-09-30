# -*- coding: utf-8 -*-
"""
Universal Social Media & Viral Reels Downloader
Fast YouTube Shorts, Instagram Reels, Pinterest, Twitter/X, and TikTok Downloader.
"""

import os
import tempfile
import yt_dlp
import asyncio


def is_supported_media_url(url: str) -> bool:
    domains = [
        "instagram.com", "instagr.am", "youtube.com", "youtu.be",
        , "x.com", , ,
        "tiktok.com", "facebook.com", "fb.watch"
    ]
    u = url.lower()
    return any(d in u for d in domains)


def extract_media_info(url: str) -> dict:
    """
    Extracts title, thumbnail, direct video URL, and formats from URL.
    """
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
                return {"ok": False, "error": "Could not extract media info"}
            
            title = info.get("title", "Social Video")
            duration = info.get("duration", 0)
            thumbnail = info.get("thumbnail")
            direct_url = info.get("url")
            
            # Find best MP4 video stream if direct_url is not set
            if not direct_url and "formats" in info:
                # Prefer mp4 with video+audio or highest quality
                formats = [f for f in info["formats"] if f.get("ext") == "mp4" and f.get("vcodec") != "none"]
                if formats:
                    best = formats[-1]
                    direct_url = best.get("url")
            
            return {
                "ok": True,
                "title": title[:60],
                "duration": duration,
                "thumbnail": thumbnail,
                "direct_url": direct_url or url,
                "source": info.get("extractor_key", "Social Media"),
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def download_media_file(url: str, extract_audio: bool = False) -> tuple[str, str]:
    """
    Downloads media file (under 50MB) to temp location and returns (filepath, title).
    """
    fd, out_tmpl = tempfile.mkstemp(suffix=".%(ext)s")
    os.close(fd)
    
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
        ydl_opts = {
            "format": "best[ext=mp4][filesize<50M]/best[filesize<50M]/best",
            "outtmpl": out_tmpl,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }
        
    def _run_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if extract_audio:
                base, _ = os.path.splitext(filename)
                filename = base + ".mp3"
            return filename, info.get("title", "Media")
            
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_download)
