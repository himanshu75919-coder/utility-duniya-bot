# -*- coding: utf-8 -*-
"""
Instagram Reels, Posts, Photos, Carousels & Stories Downloader
Accurately distinguishes between Reels (Videos), Stories, and Posts (Photos/Carousels).
Never returns a photo thumbnail when a Reel/Video was requested.
"""

import io
import os
import re
import asyncio
import requests
from PIL import Image
from bs4 import BeautifulSoup
from urllib.parse import quote

UA_HEADER = {
    "User-Agent": "TelegramBot (like TwitterBot)"
}
DESKTOP_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def is_instagram_url(url: str) -> bool:
    domains = ["instagram.com", "instagr.am"]
    u = url.lower()
    return any(d in u for d in domains)


def classify_instagram_url(url: str) -> str:
    """Classifies Instagram URL into 'reel', 'story', or 'post'"""
    u = url.lower().split("?")[0]
    if "/reel/" in u or "/reels/" in u or "/tv/" in u:
        return "reel"
    if "/stories/" in u:
        return "story"
    if "/p/" in u:
        return "post"
    return "general"


def download_instagram_media(url: str) -> dict:
    """
    Downloads Instagram media accurately according to type:
    - Reel/Video: Extracts MP4 video with full sound. Never returns photo thumbnail.
    - Post: Extracts HD photo (or carousel image) and converts to standard JPEG.
    - Story: Extracts video or photo.
    """
    clean = url.split("?")[0].rstrip("/")
    if not clean.startswith("http"):
        clean = "https://" + clean.lstrip("/")

    media_type_category = classify_instagram_url(clean)

    # Scraper sources
    mirrors = ["kkinstagram.com", "eeinstagram.com", "ddinstagram.com"]

    for mirror in mirrors:
        try:
            m_url = clean.replace("instagram.com", mirror).replace("instagr.am", mirror)
            r = requests.get(m_url, headers=UA_HEADER, timeout=8, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 1000:
                c_type = r.headers.get("content-type", "")

                # 1. Direct raw MP4 video stream
                if "video" in c_type or r.content[:4] == b"\x00\x00\x00\x18" or b"ftyp" in r.content[:20]:
                    return {
                        "ok": True,
                        "type": "video",
                        "category": media_type_category,
                        "bytes": r.content,
                        "size_mb": round(len(r.content) / (1024 * 1024), 2),
                    }

                # 2. HTML parsing
                if "text/html" in c_type or b"<html" in r.content[:200]:
                    soup = BeautifulSoup(r.text, "html.parser")
                    og_video = (
                        soup.find("meta", {"property": "og:video"})
                        or soup.find("meta", {"property": "og:video:secure_url"})
                        or soup.find("meta", {"name": "twitter:player:stream"})
                    )
                    og_image = soup.find("meta", {"property": "og:image"}) or soup.find("meta", {"name": "twitter:image"})

                    # If it's a Reel or Video Post and video meta is found:
                    if og_video and og_video.get("content"):
                        v_url = og_video["content"]
                        r_v = requests.get(v_url, headers=DESKTOP_UA, timeout=10)
                        if r_v.status_code == 200 and len(r_v.content) > 1000:
                            return {
                                "ok": True,
                                "type": "video",
                                "category": "reel",
                                "bytes": r_v.content,
                                "size_mb": round(len(r_v.content) / (1024 * 1024), 2),
                            }

                    # If it is a Post (Photo / Carousel) and NOT a Reel:
                    if media_type_category == "post" and og_image and og_image.get("content"):
                        img_url = og_image["content"]
                        r_img = requests.get(img_url, headers=DESKTOP_UA, timeout=10)
                        if r_img.status_code == 200 and len(r_img.content) > 1000:
                            im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                            buf = io.BytesIO()
                            im.save(buf, format="JPEG", quality=95)
                            buf_bytes = buf.getvalue()
                            return {
                                "ok": True,
                                "type": "photo",
                                "category": "post",
                                "bytes": buf_bytes,
                                "size_mb": round(len(buf_bytes) / (1024 * 1024), 2),
                            }

                    # If it is a Story:
                    if media_type_category == "story":
                        if og_video and og_video.get("content"):
                            r_v = requests.get(og_video["content"], headers=DESKTOP_UA, timeout=10)
                            if r_v.status_code == 200:
                                return {
                                    "ok": True,
                                    "type": "video",
                                    "category": "story",
                                    "bytes": r_v.content,
                                    "size_mb": round(len(r_v.content) / (1024 * 1024), 2),
                                }
                        elif og_image and og_image.get("content"):
                            r_img = requests.get(og_image["content"], headers=DESKTOP_UA, timeout=10)
                            if r_img.status_code == 200:
                                im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                                buf = io.BytesIO()
                                im.save(buf, format="JPEG", quality=95)
                                return {
                                    "ok": True,
                                    "type": "photo",
                                    "category": "story",
                                    "bytes": buf.getvalue(),
                                    "size_mb": round(len(buf.getvalue()) / (1024 * 1024), 2),
                                }

                # 3. Direct raw image bytes (Only accept if url is NOT a Reel)
                if "image" in c_type and media_type_category != "reel":
                    try:
                        im = Image.open(io.BytesIO(r.content)).convert("RGB")
                        buf = io.BytesIO()
                        im.save(buf, format="JPEG", quality=95)
                        buf_bytes = buf.getvalue()
                        return {
                            "ok": True,
                            "type": "photo",
                            "category": "post",
                            "bytes": buf_bytes,
                            "size_mb": round(len(buf_bytes) / (1024 * 1024), 2),
                        }
                    except Exception:
                        pass
        except Exception:
            continue

    # If it was a Reel/Video but stream wasn't retrieved:
    if media_type_category == "reel":
        return {
            "ok": False,
            "category": "reel",
            "error": "Instagram ne is Reel ke video stream ko login/geoblock restrict kiya hua hai (Private ya age-gated post).",
        }

    return {
        "ok": False,
        "category": media_type_category,
        "error": "Media download nahi ho saki. Kripya check karein ki post public hai ya nahi.",
    }


async def download_instagram_async(url: str) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_instagram_media, url)
