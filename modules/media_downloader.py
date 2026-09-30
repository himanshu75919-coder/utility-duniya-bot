# -*- coding: utf-8 -*-
"""
Instagram Universal Media Engine (Reels, Posts, Full Carousels & Stories)
Uses parth-dl high-speed extractor with multi-layer fallbacks.
Downloads 100% full original audio reels and sends all 2-10 carousel photos/videos together.
"""

import io
import os
import re
import asyncio
import requests
from PIL import Image
from bs4 import BeautifulSoup
from urllib.parse import quote

try:
    import parth_dl
except ImportError:
    parth_dl = None

DESKTOP_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BOT_UA = {
    "User-Agent": "TelegramBot (like TwitterBot)"
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
    Downloads Instagram media:
    - Reel: Returns HD MP4 video with 100% original audio.
    - Carousel (Multi-photos): Returns ALL photos/videos (up to 10) in an album batch.
    - Single Post: Returns HD photo or video.
    - Story: Downloads story media if active/public.
    """
    clean = url.split("?")[0].rstrip("/")
    if not clean.startswith("http"):
        clean = "https://" + clean.lstrip("/")

    media_cat = classify_instagram_url(clean)

    # Strategy 1: Parth-DL Core Engine
    if parth_dl:
        try:
            info = parth_dl.get_info(clean)
            m_type = info.get("type", "")
            title = info.get("title", "")

            # 1. Carousel Multi-Item Post
            if m_type == "carousel" or len(info.get("images", [])) > 1 or len(info.get("entries", [])) > 1:
                items = []
                # Check entries first
                entries = info.get("entries", [])
                if entries:
                    for entry in entries[:10]:
                        e_kind = entry.get("kind", "")
                        e_formats = entry.get("formats", [])
                        if e_kind == "video" and e_formats:
                            v_u = e_formats[0].get("url")
                            r_v = requests.get(v_u, headers=DESKTOP_UA, timeout=12)
                            if r_v.status_code == 200:
                                items.append({"type": "video", "bytes": r_v.content})
                        elif e_formats:
                            img_u = e_formats[0].get("url")
                            r_img = requests.get(img_u, headers=DESKTOP_UA, timeout=10)
                            if r_img.status_code == 200:
                                try:
                                    im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                                    buf = io.BytesIO()
                                    im.save(buf, format="JPEG", quality=95)
                                    items.append({"type": "photo", "bytes": buf.getvalue()})
                                except Exception:
                                    pass
                # Fallback to images list if entries were empty
                if not items and info.get("images"):
                    for img_obj in info.get("images", [])[:10]:
                        img_u = img_obj.get("url")
                        if img_u:
                            r_img = requests.get(img_u, headers=DESKTOP_UA, timeout=10)
                            if r_img.status_code == 200:
                                try:
                                    im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                                    buf = io.BytesIO()
                                    im.save(buf, format="JPEG", quality=95)
                                    items.append({"type": "photo", "bytes": buf.getvalue()})
                                except Exception:
                                    pass

                if items:
                    return {
                        "ok": True,
                        "type": "carousel",
                        "category": media_cat,
                        "title": title,
                        "items": items,
                        "count": len(items),
                    }

            # 2. Reel or Video Post
            if m_type == "video" or (info.get("formats") and len(info["formats"]) > 0):
                formats = info.get("formats", [])
                v_url = formats[0].get("url") if formats else None
                if v_url:
                    r_v = requests.get(v_url, headers=DESKTOP_UA, timeout=15)
                    if r_v.status_code == 200 and len(r_v.content) > 1000:
                        return {
                            "ok": True,
                            "type": "video",
                            "category": "reel" if media_cat == "reel" else "video",
                            "title": title,
                            "bytes": r_v.content,
                            "size_mb": round(len(r_v.content) / (1024 * 1024), 2),
                        }

            # 3. Single Photo Post
            if m_type in ("image", "photo") or (info.get("images") and len(info["images"]) > 0):
                img_url = info["images"][0].get("url") if info.get("images") else None
                if img_url:
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
                            "title": title,
                            "bytes": buf_bytes,
                            "size_mb": round(len(buf_bytes) / (1024 * 1024), 2),
                        }
        except Exception:
            pass

    # Strategy 2: Multi-Mirror OpenGraph / CDN Scraper
    mirrors = ["kkinstagram.com", "eeinstagram.com"]
    for mirror in mirrors:
        try:
            m_url = clean.replace("instagram.com", mirror).replace("instagr.am", mirror)
            r = requests.get(m_url, headers=BOT_UA, timeout=8, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 1000:
                c_type = r.headers.get("content-type", "")

                # Raw MP4 stream
                if "video" in c_type or r.content[:4] == b"\x00\x00\x00\x18" or b"ftyp" in r.content[:20]:
                    return {
                        "ok": True,
                        "type": "video",
                        "category": media_cat,
                        "bytes": r.content,
                        "size_mb": round(len(r.content) / (1024 * 1024), 2),
                    }

                # HTML parser
                if "text/html" in c_type or b"<html" in r.content[:200]:
                    soup = BeautifulSoup(r.text, "html.parser")
                    og_video = soup.find("meta", {"property": "og:video"}) or soup.find("meta", {"name": "twitter:player:stream"})
                    og_image = soup.find("meta", {"property": "og:image"}) or soup.find("meta", {"name": "twitter:image"})

                    if og_video and og_video.get("content"):
                        v_url = og_video["content"]
                        r_v = requests.get(v_url, headers=DESKTOP_UA, timeout=10)
                        if r_v.status_code == 200 and len(r_v.content) > 1000:
                            return {
                                "ok": True,
                                "type": "video",
                                "category": "reel" if media_cat == "reel" else "video",
                                "bytes": r_v.content,
                                "size_mb": round(len(r_v.content) / (1024 * 1024), 2),
                            }

                    if media_cat == "post" and og_image and og_image.get("content"):
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
        except Exception:
            continue

    # Clean, specific failure message according to media category
    if media_cat == "story":
        return {
            "ok": False,
            "category": "story",
            "error": "Instagram Stories sirf 24 ghante ke liye live hoti hain aur expired/private stories ko Instagram bina login allow nahi karta.",
        }

    if media_cat == "reel":
        return {
            "ok": False,
            "category": "reel",
            "error": "Instagram ne is Reel ke video stream ko login/geoblock restrict kiya hua hai (Private ya age-gated post).",
        }

    return {
        "ok": False,
        "category": media_cat,
        "error": "Media stream extract nahi ho saka. Kripya check karein ki post public hai ya nahi.",
    }


async def download_instagram_async(url: str) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_instagram_media, url)
