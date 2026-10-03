# -*- coding: utf-8 -*-
"""
Cloud Direct Resolver v31 PRO (Terabox + Mediafire + Google Drive)
==================================================================
2026 reality: Terabox ke purane public API endpoints (yt1s.click, qtcloud worker, playterabox)
band ho chuke hain. Isliye ab 6-layer ENGINE CHAIN banaya gaya hai — jo pehle chal jaye wahi use hota hai:

  Layer 1: Public Cloudflare Worker APIs (robinkumarshakya, hnn, qtcloud, ...)
  Layer 2: Guest share/list (bina cookie — listing/info nikalta hai)
  Layer 3: NDUS cookie method (agar TERABOX_COOKIE / TERABOX_NDUS env set ho — 100% reliable in 2026)
  Layer 4: Apna custom provider (TERABOX_API_BASE env — own deployment / RapidAPI key)
  Layer 5: Web-downloader fallback links (buttons) — user kaam kabhi rukta nahi
  Layer 6: Mediafire (scrambled-url decode) + Google Drive (large-file confirm token) upgrades

Env vars (optional, Render ke Environment me daal sakte hain):
  TERABOX_COOKIE   = apne throwaway Terabox account ka poora cookie ya sirf ndus value
  TERABOX_API_BASE = jaise https://my-teradl.onrender.com   (POST {base}/download {"url": ...})
  TERABOX_API_KEY  = agar provider API key maange (header me jaata hai)
"""

import base64
import json
import os
import re
from html import unescape
from urllib.parse import quote, unquote, urlparse, parse_qs

import requests

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
MOBILE_UA = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

TERABOX_DOMAINS = [
    "terabox.com", "teraboxapp.com", "1024tera.com", "1024terabox.com", "mirrobox.com",
    "nephobox.com", "freeterabox.com", "teraboxlink.com", "terasharelink.com", "terabox.app",
    "tibibox.com", "4funbox.com", "4funbox.co", "terasharefile.com", "momerybox.com",
    "terafileshare.com", "teraboxshare.com", "terabox1.com", "terabox2.com", "dubox.com",
]

TERABOX_WEB_FALLBACKS = [
    ("🅰️ TeraDownloader", "https://teradownloader.com/"),
    ("🅱️ Sechno (Turbo)", "https://sechno.com/"),
    ("🅾️ TeraBoxDL", "https://teraboxdl.site/"),
    ("🌀 TeraLoader", "https://teraloader.com/"),
    ("▶️ Flow Player", "https://flowvideoplayer.com/"),
]


# =====================================================================================
# DETECTORS
# =====================================================================================
def is_terabox_url(url: str) -> bool:
    u = (url or "").lower()
    return any(d in u for d in TERABOX_DOMAINS)


def is_mediafire_url(url: str) -> bool:
    return "mediafire.com" in (url or "").lower()


def is_gdrive_url(url: str) -> bool:
    return "drive.google.com" in (url or "").lower()


def _extract_surl(url: str):
    """Terabox share link se surl (short url id) nikalta hai."""
    url = (url or "").strip()
    m = re.search(r"/s/1?([A-Za-z0-9_\-]+)", url)
    if m:
        return "1" + m.group(1) if not m.group(0).startswith("/s/1") else m.group(1)
    m = re.search(r"[?&]surl=([A-Za-z0-9_\-]+)", url)
    if m:
        return m.group(1)
    return None


def _size_h(n):
    try:
        n = float(n)
    except Exception:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.2f} {unit}"
        n /= 1024.0
    return "N/A"


def _norm_files(items):
    files = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        name = it.get("server_filename") or it.get("filename") or it.get("file_name") or it.get("name") or "File"
        size_b = it.get("size") or it.get("size_bytes") or it.get("bytes") or 0
        dlink = it.get("dlink") or it.get("download_url") or it.get("downloadUrl") or it.get("direct_link") or it.get("direct_url")
        stream = it.get("stream_url") or it.get("streaming_url") or it.get("player_url") or dlink
        thumb = it.get("thumb") or it.get("thumbnail") or ""
        if isinstance(thumb, dict):
            thumb = thumb.get("url1") or thumb.get("url3") or thumb.get("icon") or ""
        try:
            size_b = int(size_b)
        except Exception:
            size_b = 0
        if name and (dlink or stream):
            files.append({
                "name": str(name)[:120],
                "size": _size_h(size_b) if size_b else "N/A",
                "size_bytes": size_b,
                "dlink": dlink or stream,
                "stream": stream or dlink,
                "thumb": thumb,
            })
    return files


# =====================================================================================
# LAYER 1 — PUBLIC WORKER APIs
# =====================================================================================
def _tb_robin(url):
    """Cloudflare worker: terabox-worker.robinkumarshakya103.workers.dev"""
    r = requests.get(f"https://terabox-worker.robinkumarshakya103.workers.dev/api?url={quote(url, safe='')}",
                     headers=UA, timeout=20)
    if r.status_code == 200:
        j = r.json()
        if j.get("success") and j.get("files"):
            files = _norm_files(j["files"])
            if files:
                return files, "Robin Worker"
    return None, None


def _tb_hnn(url):
    """Cloudflare worker: terabox.hnn.workers.dev (koi bhi endpoint jo chale)"""
    surl = _extract_surl(url)
    if not surl:
        return None, None
    for path, method in (("/api/get-info", "POST"), ("/api/get-info", "GET")):
        try:
            if method == "POST":
                r = requests.post(f"https://terabox.hnn.workers.dev{path}", data={"shorturl": surl, "pwd": ""},
                                  headers=UA, timeout=18)
            else:
                r = requests.get(f"https://terabox.hnn.workers.dev{path}", params={"shorturl": surl},
                                 headers=UA, timeout=18)
            if r.status_code == 200 and r.text.strip().startswith("{"):
                j = r.json()
                files = _norm_files(j.get("list") or j.get("files") or [])
                if not files and j.get("dlink"):
                    files = _norm_files([j])
                if files:
                    return files, "HNN Worker"
        except Exception:
            continue
    return None, None


def _tb_qtcloud(url):
    """worker: terabox-dl.qtcloud.workers.dev"""
    surl = _extract_surl(url)
    if not surl:
        return None, None
    for endpoint in ("api/get-info", "api/get-download"):
        try:
            r = requests.get(f"https://terabox-dl.qtcloud.workers.dev/{endpoint}",
                             params={"shorturl": surl, "url": url}, headers=UA, timeout=18)
            if r.status_code == 200 and r.text.strip().startswith("{"):
                j = r.json()
                files = _norm_files(j.get("list") or j.get("files") or [])
                if not files:
                    one = j.get("data") or j
                    files = _norm_files([one])
                if files:
                    return files, "QTCloud Worker"
        except Exception:
            continue
    return None, None


def _tb_surl_api(url):
    """surl-based public endpoints (naye domain variants)"""
    surl = _extract_surl(url)
    if not surl:
        return None, None
    cands = [
        f"https://terabox-api.vercel.app/api/terabox?url={quote(url, safe='')}",
        f"https://terabox.surl.workers.dev/api?shorturl={surl}",
        f"https://teraboxdl.vercel.app/api?url={quote(url, safe='')}",
    ]
    for c in cands:
        try:
            r = requests.get(c, headers=UA, timeout=12)
            if r.status_code == 200 and r.text.strip().startswith("{"):
                j = r.json()
                files = _norm_files(j.get("list") or j.get("files") or j.get("data") or [])
                if files:
                    return files, "Public API"
        except Exception:
            continue
    return None, None


# =====================================================================================
# LAYER 2 — GUEST share/list (bina cookie: infolist milti hai)
# =====================================================================================
def _tb_guest_list(url):
    """Bina cookie Terabox share/list — kuch public shares par chalti hai."""
    surl = _extract_surl(url)
    if not surl:
        return None, None
    try:
        s = requests.Session()
        page = f"https://www.terabox.com/sharing/link?surl={surl}"
        s.get(page, headers=UA, timeout=15)
        r = s.get("https://www.terabox.com/share/list",
                  params={"app_id": "250528", "web": "1", "shorturl": surl, "root": "1"},
                  headers={**UA, "Referer": page}, timeout=20)
        if r.status_code == 200 and r.text.strip().startswith("{"):
            j = r.json()
            if j.get("errno") == 0 and j.get("list"):
                files = _norm_files(j["list"])
                # Folder ho (isdir=1) to ek level andar bhi jhaankte hain
                if files and any(x.get("isdir") for x in j["list"]):
                    folder = next((x for x in j["list"] if x.get("isdir")), None)
                    if folder:
                        r2 = s.get("https://www.terabox.com/share/list",
                                   params={"app_id": "250528", "web": "1", "shorturl": surl,
                                           "root": "1", "dir": folder.get("path", "/")},
                                   headers={**UA, "Referer": page}, timeout=20)
                        if r2.status_code == 200 and r2.text.strip().startswith("{"):
                            j2 = r2.json()
                            more = _norm_files((j2.get("list") or [])[:30])
                            if more:
                                files = more
                if files:
                    return files, "Terabox Guest Listing"
    except Exception:
        pass
    return None, None


# =====================================================================================
# LAYER 3 — NDUS COOKIE (2026 ka 100% reliable tareeka; env se ON hota hai)
# =====================================================================================
def _tb_cookie_value():
    raw = (os.getenv("TERABOX_COOKIE") or os.getenv("TERABOX_NDUS") or "").strip()
    if not raw:
        return ""
    if "ndus=" in raw:
        m = re.search(r"ndus=([^;\s]+)", raw)
        return m.group(1) if m else raw
    return raw


def _tb_ndus(url):
    """Apne (throwaway) Terabox account ke ndus cookie se signed dlink nikalta hai."""
    ndus = _tb_cookie_value()
    if not ndus:
        return None, None
    surl = _extract_surl(url)
    if not surl:
        return None, None
    try:
        s = requests.Session()
        s.cookies.set("ndus", ndus, domain=".terabox.com")
        headers = {**MOBILE_UA, "Referer": f"https://www.terabox.com/sharing/link?surl={surl}"}

        # 1) WAP page me __INITIAL_STATE__ ke andar signed dlinks embedded hote hain
        for page_url in (
            f"https://www.terabox.com/wap?shorturl={surl}",
            f"https://www.terabox.com/main?shorturl={surl}&root=1",
            f"https://www.terabox.com/sharing/link?surl={surl}",
        ):
            try:
                r = s.get(page_url, headers=headers, timeout=20, allow_redirects=True)
                body = r.text
                m = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*</script>", body, re.S)
                if not m:
                    m = re.search(r"__INITIAL_STATE__\s*=\s*(\{.*?\});", body, re.S)
                if m:
                    try:
                        data = json.loads(m.group(1))
                    except Exception:
                        data = None
                    if data:
                        raw_list = []
                        def _walk(o):
                            if isinstance(o, dict):
                                if ("dlink" in o or "server_filename" in o):
                                    raw_list.append(o)
                                for v in o.values():
                                    _walk(v)
                            elif isinstance(o, list):
                                for v in o:
                                    _walk(v)
                        _walk(data)
                        files = _norm_files(raw_list)
                        if files:
                            return files, "Terabox Cookie (Direct)"
                # 2) HTML me direct dlink string
                dls = re.findall(r'"dlink"\s*:\s*"(https:[^"]+)"', body)
                names = re.findall(r'"server_filename"\s*:\s*"([^"]+)"', body)
                sizes = re.findall(r'"size"\s*:\s*(\d+)', body)
                if dls:
                    files = _norm_files([
                        {"server_filename": names[i] if i < len(names) else f"File {i+1}",
                         "size": sizes[i] if i < len(sizes) else 0,
                         "dlink": dls[i].replace("\\/", "/")}
                        for i in range(len(dls))
                    ])
                    if files:
                        return files, "Terabox Cookie (HTML)"
            except Exception:
                continue
    except Exception:
        pass
    return None, None


# =====================================================================================
# LAYER 4 — CUSTOM PROVIDER (apna TeraDL / RapidAPI)
# =====================================================================================
def _tb_custom_provider(url):
    base = (os.getenv("TERABOX_API_BASE") or "").strip().rstrip("/")
    if not base:
        return None, None
    key = (os.getenv("TERABOX_API_KEY") or "").strip()
    headers = {**UA, "Content-Type": "application/json"}
    if key:
        headers["X-API-Key"] = key
        headers["Authorization"] = f"Bearer {key}"
    tries = [
        ("post", f"{base}/download", {"url": url}),
        ("post", f"{base}/api/download", {"url": url}),
        ("get", f"{base}/api", None),
        ("get", f"{base}/download", None),
    ]
    for method, endpoint, payload in tries:
        try:
            if method == "post":
                r = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            else:
                r = requests.get(endpoint, params={"url": url}, headers=headers, timeout=30)
            if r.status_code == 200:
                try:
                    j = r.json()
                except Exception:
                    continue
                blob = j.get("data") or j
                raw = blob.get("files") or blob.get("list") or [blob]
                files = _norm_files(raw)
                if files:
                    return files, "Custom Provider"
        except Exception:
            continue
    return None, None


# =====================================================================================
# MAIN TERABOX RESOLVER — engine chain
# =====================================================================================
_TB_HUB_COOLDOWN = [0.0]          # hub fail hone par kuch der skip (live test slow na ho)


def _tb_hub(url):
    """v46: user ke API hub se terabox (primary engine) — fail par 5 min cooldown."""
    import time as _t
    if _t.time() < _TB_HUB_COOLDOWN[0]:
        return [], ""
    try:
        from modules import api_hub as hub
    except Exception:
        return [], ""
    if not hub.hub_ready():
        return [], ""
    res = hub.hub_terabox(url)
    if not res.get("ok"):
        _TB_HUB_COOLDOWN[0] = _t.time() + 300      # 5 min tak skip
        return [], ""
    if not res.get("ok"):
        return [], ""
    files = []
    for f in res.get("files", [])[:10]:
        link = f.get("link") or ""
        if not link:
            continue
        files.append({
            "name": f.get("name") or "file",
            "size": int(f.get("size") or 0),
            "size_h": f.get("size_h") or _size_h(f.get("size") or 0),
            "dlink": link, "stream": link,
            "thumb": f.get("thumb") or "",
        })
    return files, f"API Hub ({res.get('endpoint', 'terabox')})"


def resolve_terabox(url: str) -> dict:
    engines = [
        ("API Hub", _tb_hub),                       # v45: user ka hub pehle
        ("Public Worker (Robin)", _tb_robin),
        ("Public Worker (HNN)", _tb_hnn),
        ("Public Worker (QTCloud)", _tb_qtcloud),
        ("Public API (surl)", _tb_surl_api),
        ("Guest Listing", _tb_guest_list),
        ("Cookie Mode (NDUS)", _tb_ndus),
        ("Custom Provider", _tb_custom_provider),
    ]
    tried = []
    for name, fn in engines:
        try:
            files, engine = fn(url)
        except Exception as e:
            tried.append(f"{name}: {type(e).__name__}")
            continue
        tried.append(f"{name}: {'OK' if files else 'no'}")
        if files:
            main = files[0]
            return {
                "ok": True,
                "provider": f"Terabox • {engine}",
                "engine": engine,
                "title": main["name"],
                "size": main["size"],
                "direct_url": main["dlink"],
                "stream_url": main["stream"],
                "thumb": main.get("thumb", ""),
                "files": files,
                "total_files": len(files),
            }

    # Sab fail — kabhi bhi user ko khali haath nahi bhejte: fallback card
    surl = _extract_surl(url)
    hint = ("Direct link ke liye TERABOX_COOKIE (ndus) set karo — wo hamesha chalta hai. Ya neeche web downloader use karo."
            "Or use the web downloader below.")
    return {
        "ok": False,
        "provider": "Terabox",
        "error": "Direct link nahi mila (Terabox ne 2026 me public API band kar di).",
        "hint": hint,
        "fallback_links": TERABOX_WEB_FALLBACKS,
        "surl": surl,
        "tried": tried,
    }


# =====================================================================================
# MEDIAFIRE (scrambled-url decode + modern scrape)
# =====================================================================================
def resolve_mediafire_direct(url: str) -> dict:
    try:
        r = requests.get(url, headers=UA, timeout=12)
        if r.status_code != 200:
            return {"ok": False, "error": f"Mediafire page status {r.status_code}"}
        html = r.text

        direct = None
        # 1) Naya tareeka: data-scrambled-url (base64 encoded)
        m = re.search(r'data-scrambled-url="([^"]+)"', html)
        if m:
            try:
                direct = base64.b64decode(m.group(1)).decode("utf-8", "ignore")
            except Exception:
                direct = None
        # 2) aria-label / download button href
        if not direct:
            m = re.search(r'aria-label="Download file"[^>]+href="([^"]+)"', html)
            if m:
                direct = m.group(1)
        # 3) id="downloadButton"
        if not direct:
            m = re.search(r'id="downloadButton"[^>]+href="([^"]+)"', html)
            if m:
                direct = m.group(1)
        # 4) Purana pattern
        if not direct:
            m = re.search(r'href="((?:https?:)?//download\d*\.mediafire\.com/[^"]+)"', html)
            if m:
                direct = m.group(1)

        title = "Mediafire File"
        tm = re.search(r'<div class="filename">\s*([^<]+?)\s*</div>', html)
        if tm:
            title = unescape(tm.group(1)).strip()
        else:
            tm = re.search(r'<title>([^<]+)</title>', html)
            if tm:
                title = unescape(tm.group(1)).replace("MediaFire", "").strip(" -|") or title

        size = "N/A"
        sm = re.search(r'<span class="details">\s*\(([^)]+)\)', html) or re.search(r'\((\d+(?:\.\d+)?\s*(?:KB|MB|GB|TB))\)', html)
        if sm:
            size = sm.group(1)

        if direct:
            if direct.startswith("//"):
                direct = "https:" + direct
            return {
                "ok": True,
                "provider": "Mediafire Direct",
                "title": title[:120],
                "size": size,
                "direct_url": direct,
                "stream_url": direct,
                "files": [{"name": title[:120], "size": size, "size_bytes": 0, "dlink": direct, "stream": direct}],
            }
        return {"ok": False, "error": "Download button nahi mila (file private ya delete ho gayi ho sakti hai)."}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


# =====================================================================================
# GOOGLE DRIVE (large-file confirm + filename/size)
# =====================================================================================
def resolve_gdrive_direct(url: str) -> dict:
    file_id = None
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url) or re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if m:
        file_id = m.group(1)
    if not file_id:
        return {"ok": False, "error": "Invalid Google Drive link (file ID not found)."}

    direct = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
    title = f"Google Drive File ({file_id[:10]}...)"
    size = "N/A"
    confirm_note = ""
    try:
        s = requests.Session()
        r = s.get(direct, headers=UA, timeout=15, stream=True)
        cd = r.headers.get("Content-Disposition", "")
        fn = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', cd)
        if fn:
            title = unquote(fn.group(1))[:120]
        if r.headers.get("Content-Length"):
            size = _size_h(int(r.headers["Content-Length"]))
        # Bade files par Google confirm token wala page deta hai
        ctype = r.headers.get("Content-Type", "")
        if "text/html" in ctype:
            body = r.text[:8000]
            tok = re.search(r'name="confirm"\s+value="([^"]+)"', body) or re.search(r"confirm=([0-9A-Za-z_\-]+)", body)
            uuid = re.search(r'name="uuid"\s+value="([^"]+)"', body)
            if tok:
                direct = f"{direct}&confirm={tok.group(1)}"
                if uuid:
                    direct += f"&uuid={uuid.group(1)}"
                confirm_note = "Ye badi file hai — neeche wala link browser me kholo, download turant shuru ho jayega."
    except Exception:
        pass

    return {
        "ok": True,
        "provider": "Google Drive Direct",
        "title": title,
        "size": size,
        "direct_url": direct,
        "stream_url": direct,
        "note": confirm_note,
        "files": [{"name": title, "size": size, "size_bytes": 0, "dlink": direct, "stream": direct}],
    }


# =====================================================================================
# DISPATCHER (jaisa pehle tha — bot isi ko call karta hai)
# =====================================================================================
def resolve_cloud_url(url: str) -> dict:
    url = (url or "").strip()
    if is_terabox_url(url):
        return resolve_terabox(url)
    elif is_mediafire_url(url):
        return resolve_mediafire_direct(url)
    elif is_gdrive_url(url):
        return resolve_gdrive_direct(url)
    else:
        return {
            "ok": False,
            "error": ("Ye cloud domain support nahi hai. Abhi chalta hai: Terabox (20+ domain), Mediafire, Google Drive."
                      "Mediafire, Google Drive. For a direct URL of any other link, use the 'LINK BYPASS' tool."),
        }
