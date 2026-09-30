# -*- coding: utf-8 -*-
"""
Terabox & Multi-Cloud Direct Resolver
Extracts direct download & streaming links for Terabox, Mediafire, Google Drive, and cloud shares.
"""

import re
import requests
from urllib.parse import quote, unquote, urlparse

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def is_terabox_url(url: str) -> bool:
    domains = [
        "terabox.com", "teraboxapp.com", "1024tera.com", "mirrobox.com",
        "nephobox.com", "freeterabox.com", "teraboxlink.com", "terasharelink.com",
        "terabox.app", "tibibox.com", "4funbox.com"
    ]
    u = url.lower()
    return any(d in u for d in domains)


def is_mediafire_url(url: str) -> bool:
    return "mediafire.com" in url.lower()


def is_gdrive_url(url: str) -> bool:
    return "drive.google.com" in url.lower()


def resolve_gdrive_direct(url: str) -> dict:
    """Extracts direct download link from Google Drive URL"""
    file_id = None
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    if m:
        file_id = m.group(1)
    else:
        m2 = re.search(r"id=([a-zA-Z0-9_-]+)", url)
        if m2:
            file_id = m2.group(1)
            
    if file_id:
        direct = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
        return {
            "ok": True,
            "title": f"Google Drive File ({file_id[:8]}...)",
            "size": "Direct Stream",
            "direct_url": direct,
            "stream_url": direct,
            "provider": "Google Drive",
        }
    return {"ok": False, "error": "Invalid Google Drive link format"}


def resolve_mediafire_direct(url: str) -> dict:
    """Scrapes direct download link from Mediafire"""
    try:
        r = requests.get(url, headers=UA, timeout=8)
        if r.status_code == 200:
            m = re.search(r'aria-label="Download file"[^>]+href="([^"]+)"', r.text)
            if not m:
                m = re.search(r'href="((?:https?:)?//download\d+\.mediafire\.com/[^"]+)"', r.text)
            if m:
                direct = m.group(1)
                title = "Mediafire File"
                t_match = re.search(r'<div class="filename">([^<]+)</div>', r.text)
                if t_match:
                    title = t_match.group(1).strip()
                return {
                    "ok": True,
                    "title": title,
                    "size": "High Speed",
                    "direct_url": direct,
                    "stream_url": direct,
                    "provider": "Mediafire",
                }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "Direct download link not found on page"}


def resolve_terabox(url: str) -> dict:
    """
    Extracts high-speed direct download link & stream link for Terabox videos/files
    using multi-endpoint fallbacks.
    """
    clean_url = url.strip()
    
    # 1. Endpoint A: Public Fast API
    try:
        api_url = f"https://yt1s.click/api/terabox?url={quote(clean_url)}"
        r = requests.get(api_url, headers=UA, timeout=6)
        if r.status_code == 200 and "{" in r.text:
            data = r.json()
            if data.get("status") in (200, "success", True) or data.get("download_url"):
                return {
                    "ok": True,
                    "title": data.get("file_name") or data.get("title") or "Terabox Video/File",
                    "size": data.get("size") or "HD",
                    "direct_url": data.get("download_url") or data.get("direct_link") or clean_url,
                    "stream_url": data.get("stream_url") or data.get("download_url") or clean_url,
                    "provider": "Terabox Cloud",
                }
    except Exception:
        pass

    # 2. Endpoint B: Terabox Direct Downloader Helper
    try:
        api2 = "https://terabox-dl.qtcloud.workers.dev/api/get-info"
        surl = clean_url.split("/")[-1].replace("1", "", 1) if "/s/1" in clean_url else clean_url.split("/")[-1]
        r2 = requests.get(f"{api2}?shorturl={surl}", headers=UA, timeout=5)
        if r2.status_code == 200:
            data = r2.json()
            if data.get("ok") or data.get("list"):
                item = data.get("list", [{}])[0]
                return {
                    "ok": True,
                    "title": item.get("filename", "Terabox File"),
                    "size": f"{round(int(item.get('size', 0))/(1024*1024), 1)} MB" if item.get("size") else "HD",
                    "direct_url": item.get("dlink") or clean_url,
                    "stream_url": item.get("dlink") or clean_url,
                    "provider": "Terabox Cloud",
                }
    except Exception:
        pass

    # 3. Endpoint C: Fast Web Bypass URL generator
    # Many users use bypass mirror links that play instantly in browser/VLC
    surl_match = re.search(r"/s/([a-zA-Z0-9_-]+)", clean_url)
    if surl_match:
        s_id = surl_match.group(1)
        fast_stream = f"https://www.terabox.app/sharing/link?surl={s_id.lstrip('1')}"
        direct_player = f"https://playterabox.com/watch/{s_id}"
        return {
            "ok": True,
            "title": f"Terabox Media Stream ({s_id})",
            "size": "Full HD Stream",
            "direct_url": fast_stream,
            "stream_url": direct_player,
            "provider": "Terabox Fast Stream",
        }

    return {"ok": False, "error": "Could not bypass Terabox link. Please check if link is valid."}


def resolve_cloud_url(url: str) -> dict:
    if is_terabox_url(url):
        return resolve_terabox(url)
    elif is_mediafire_url(url):
        return resolve_mediafire_direct(url)
    elif is_gdrive_url(url):
        return resolve_gdrive_direct(url)
    else:
        return {"ok": False, "error": "Unsupported cloud domain. Send Terabox, Mediafire, or Google Drive link."}
