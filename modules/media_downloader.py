# -*- coding: utf-8 -*-
"""
Instagram Reels, Posts, Photos, Carousels & Stories Downloader
Downloads Instagram media with 100% full original audio and converts webp/heic to crisp JPEG.
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


def download_instagram_media(url: str) -> dict:
    """
    Downloads Instagram Reel, Video, Photo, Carousel, or Story.
    Handles HTML responses by extracting og:image / og:video and converting to standard JPEG/MP4.
    """
    clean = url.split("?")[0].rstrip("/")
    if not clean.startswith("http"):
        clean = "https://" + clean.lstrip("/")

    # Method 1: KKInstagram CDN Bypass
    try:
        kk_url = clean.replace("instagram.com", "kkinstagram.com").replace("instagr.am", "kkinstagram.com")
        r = requests.get(kk_url, headers=UA_HEADER, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            c_type = r.headers.get("content-type", "")

            # Case A: KKInstagram returned direct raw MP4 video
            if "video" in c_type or r.content[:4] == b"\x00\x00\x00\x18" or b"ftyp" in r.content[:20]:
                return {
                    "ok": True,
                    "type": "video",
                    "bytes": r.content,
                    "size_mb": round(len(r.content) / (1024 * 1024), 2),
                }

            # Case B: KKInstagram returned direct raw image bytes (JPEG/PNG/WEBP)
            if "image" in c_type:
                try:
                    im = Image.open(io.BytesIO(r.content)).convert("RGB")
                    buf = io.BytesIO()
                    im.save(buf, format="JPEG", quality=95)
                    buf_bytes = buf.getvalue()
                    return {
                        "ok": True,
                        "type": "photo",
                        "bytes": buf_bytes,
                        "size_mb": round(len(buf_bytes) / (1024 * 1024), 2),
                    }
                except Exception:
                    pass

            # Case C: KKInstagram returned HTML page (Carousel / Multi-Photo / Post)
            if "text/html" in c_type or b"<html" in r.content[:200]:
                soup = BeautifulSoup(r.text, "html.parser")
                og_video = soup.find("meta", {"property": "og:video"}) or soup.find("meta", {"name": "twitter:player:stream"})
                og_image = soup.find("meta", {"property": "og:image"}) or soup.find("meta", {"name": "twitter:image"})

                # If post has a video
                if og_video and og_video.get("content"):
                    v_url = og_video["content"]
                    r_v = requests.get(v_url, headers=DESKTOP_UA, timeout=10)
                    if r_v.status_code == 200 and len(r_v.content) > 1000:
                        return {
                            "ok": True,
                            "type": "video",
                            "bytes": r_v.content,
                            "size_mb": round(len(r_v.content) / (1024 * 1024), 2),
                        }

                # If post has photo/carousel
                if og_image and og_image.get("content"):
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
                            "bytes": buf_bytes,
                            "size_mb": round(len(buf_bytes) / (1024 * 1024), 2),
                        }
    except Exception:
        pass

    # Method 2: Fallback direct embed scraper
    try:
        shortcode_match = re.findall(r"/(?:p|reel|tv)/([a-zA-Z0-9_-]+)", clean)
        if shortcode_match:
            shortcode = shortcode_match[0]
            embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
            r_embed = requests.get(embed_url, headers=DESKTOP_UA, timeout=6)
            if r_embed.status_code == 200:
                cdn_matches = re.findall(r"(https://[^\s\"\'<>]+\.cdninstagram\.com/[^\s\"\'<>]+)", r_embed.text)
                for cdn_u in cdn_matches:
                    clean_cdn = cdn_u.replace("\\u0026", "&").replace("\\/", "/")
                    if "webp" not in clean_cdn and "rsrc.php" not in clean_cdn:
                        r_c = requests.get(clean_cdn, headers=DESKTOP_UA, timeout=8)
                        if r_c.status_code == 200 and len(r_c.content) > 5000:
                            im = Image.open(io.BytesIO(r_c.content)).convert("RGB")
                            buf = io.BytesIO()
                            im.save(buf, format="JPEG", quality=95)
                            return {
                                "ok": True,
                                "type": "photo",
                                "bytes": buf.getvalue(),
                                "size_mb": round(len(buf.getvalue()) / (1024 * 1024), 2),
                            }
    except Exception:
        pass

    return {"ok": False, "error": "Could not download Instagram media. Make sure link is from a public post/reel/story."}


async def download_instagram_async(url: str) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_instagram_media, url)
