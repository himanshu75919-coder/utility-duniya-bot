# -*- coding: utf-8 -*-
"""
🔌 API HUB (v45) — user ke apne OSINT API hub se baat karne ka ek hi darwaza.

Hub: https://osint-api-hub.onrender.com  (v2.5 · 100+ endpoints, Demo key = lifetime)

Env (Render → Environment):
  HUB_API_BASE  = https://osint-api-hub.onrender.com/api   (default)
  HUB_API_KEY   = aapki apni key      ← ye lagate hi saare tools hub par shift ho jaate hain
                  (khaali ho to VEHICLE_API_KEY / IMEI_API_KEY / NUM_INFO_API_KEY
                   me se jo mile wahi use hoti hai)

Key na hone par bot tootta nahi: purane free APIs (ip-api, razorpay-ifsc,
postalpincode, terabox workers, yt-dlp) **fallback** ki tarah chalte rehte hain.

Design rules:
  • Har function dict return karta hai, kabhi raise nahi karta.
  • Response shape hub badal de to bhi toot na jaye — `_pick()` keys ko
    case-insensitive + nested ("data"/"result"/"results"/"response") dhoondta hai.
"""
from __future__ import annotations

import os
import re
from typing import Any

import requests

UA = {"User-Agent": "UtilityDuniya-Bot/1.0 (+hub)"}

# khaali / dummy values — inhe "key nahi hai" maano (Demo ab VALID key hai)
PLACEHOLDER_KEYS = {"", "demo_key", "your_api_key", "key", "none", "null", "changeme",
                    "change_me", "apni_key"}

# ✅ user ka asli hub (59 endpoints, Demo key = lifetime, ALL ENDPOINTS plan)
DEFAULT_BASE = "https://osint-api-hub.onrender.com/api"
# purana hub (v2.0) — sirf tab jab env me khud set karo
LEGACY_BASE = "https://osint-apis-hub.onrender.com/api"


# =====================================================================
# config
# =====================================================================
def hub_base() -> str:
    for var in ("HUB_API_BASE", "VEHICLE_API_BASE", "IMEI_API_BASE", "NUM_INFO_API_BASE"):
        v = (os.environ.get(var) or "").strip()
        if v:
            v = v.rstrip("/")
            if not v.endswith("/api") and ("osint-api" in v or "osint-apis" in v):
                v += "/api"
            return v
    return DEFAULT_BASE


def hub_key() -> str:
    """Key: HUB_API_KEY → VEHICLE/IMEI/NUM keys → default 'Demo' (public demo key jo chalti hai)."""
    for var in ("HUB_API_KEY", "VEHICLE_API_KEY", "IMEI_API_KEY", "NUM_INFO_API_KEY"):
        v = (os.environ.get(var) or "").strip()
        if v and v.lower() not in PLACEHOLDER_KEYS:
            return v
    return "Demo"


def hub_ready() -> bool:
    """Hub chalu hai? (base + Demo/key set, aur HUB_ENABLED off na ho.)

    Demo key aapke hub par by-default chalti hai (lifetime, ALL ENDPOINTS).
    Kisi call par 401 aaye to hum use tool ke level par fallback de dete hain.
    """
    return bool(hub_key()) and not hub_disabled()


def hub_disabled() -> bool:
    return (os.environ.get("HUB_ENABLED") or "on").strip().lower() in ("off", "0", "false", "no")


def hub_key_name() -> str:
    for var in ("HUB_API_KEY", "VEHICLE_API_KEY", "IMEI_API_KEY", "NUM_INFO_API_KEY"):
        v = (os.environ.get(var) or "").strip()
        if v and v.lower() not in PLACEHOLDER_KEYS:
            return var
    return ""


# =====================================================================
# core request
# =====================================================================
def hub_get(path: str, params: dict | None = None, timeout: int = 45) -> dict:
    """Hub par ek GET. Returns {"ok","data","error","status","endpoint"}."""
    if hub_disabled():
        return {"ok": False, "disabled": True, "error": "Hub is off (HUB_ENABLED=off)"}
    if not hub_ready():
        return {"ok": False, "no_key": True,
                "error": "Hub API key is not set (HUB_API_KEY)"}
    p = dict(params or {})
    p["key"] = hub_key()
    url = hub_base().rstrip("/") + "/" + path.lstrip("/")
    try:
        r = requests.get(url, params=p, headers=UA, timeout=timeout)
        if r.status_code == 401:
            return {"ok": False, "auth": True, "status": 401,
                    "error": "Hub ne key reject kar di (401 Invalid API key)"}
        if r.status_code == 410:
            j = {}
            try:
                j = r.json()
            except Exception:
                pass
            return {"ok": False, "disabled_by_hub": True, "status": 410,
                    "error": _short(str(j.get("error") or "This endpoint is turned off on the hub")),
                    "hint": j.get("hint"), "official_links": j.get("official_links")}
        if r.status_code >= 400:
            return {"ok": False, "status": r.status_code,
                    "error": f"Hub HTTP {r.status_code}: {_short(r.text)}"}
        try:
            j = r.json()
        except Exception:
            return {"ok": False, "status": r.status_code, "error": "Hub ne JSON nahi bheja"}
        if isinstance(j, dict) and j.get("error"):
            return {"ok": False, "status": r.status_code, "error": _short(str(j["error"]))}
        return {"ok": True, "data": j, "status": r.status_code, "endpoint": path}
    except requests.Timeout:
        return {"ok": False, "timeout": True, "error": "Hub slow hai (timeout)"}
    except Exception as e:                                  # noqa: BLE001
        return {"ok": False, "error": _short(str(e))}


def hub_try(pairs: list, timeout: int = 45) -> dict:
    """Ek se zyada endpoint try karo — pehla jo chale wahi do.
    pairs = [("/ip-v2", {"ip": x}), ("/ip-v3", {"ip": x}), ...]
    """
    last = {"ok": False, "error": "Koi endpoint nahi chala"}
    for path, params in pairs:
        res = hub_get(path, params, timeout=timeout)
        if res.get("ok"):
            res["endpoint"] = path
            return res
        last = res
        if res.get("no_key") or res.get("disabled"):
            break                                   # key hi nahi — aage try karne ka matlab nahi
    return last


def _short(t: str, n: int = 140) -> str:
    return re.sub(r"\s+", " ", str(t or "")).strip()[:n]


def _pick(d: Any, *names, default=None):
    """Nested dict me case-insensitive key dhoondo (data/result/results/response me bhi)."""
    if not isinstance(d, dict):
        return default
    wanted = [n.lower().replace("_", "").replace("-", "") for n in names]
    scopes = [d]
    for k in ("data", "result", "results", "response", "info", "details"):
        v = d.get(k)
        if isinstance(v, dict):
            scopes.append(v)
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            scopes.append(v[0])
    for sc in scopes:
        for k, v in sc.items():
            kk = str(k).lower().replace("_", "").replace("-", "")
            if kk in wanted and v not in (None, "", [], {}):
                return v
    return default


def _find_list(d: Any, keys=("files", "items", "results", "data", "list", "links")):
    """Response me se list of dicts nikaalo (files/downloads ke liye)."""
    if isinstance(d, list):
        return d
    if not isinstance(d, dict):
        return []
    for k in keys:
        v = d.get(k)
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            for k2 in keys:
                v2 = v.get(k2)
                if isinstance(v2, list):
                    return v2
    # last try: koi bhi list jo dicts ki ho
    for v in d.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


def _b(x) -> bool:
    if isinstance(x, bool):
        return x
    return str(x or "").strip().lower() in ("1", "true", "yes", "y", "on", "up", "enabled")


# =====================================================================
# 🌐 IP / DOMAIN  →  /ip-v2 → /ip-v3 → /ip-v1
# =====================================================================
def hub_ip(target: str) -> dict:
    """IP/domain info — bot ke lookup_ip_domain() jaisa hi shape deta hai."""
    t = re.sub(r"^https?://", "", (target or "").strip()).split("/")[0].strip()
    if not t:
        return {"ok": False, "error": "Send a domain or IP"}
    res = hub_try([("/ip-v2", {"ip": t}), ("/ip-v3", {"ip": t}), ("/ip-v1", {"query": t})], timeout=40)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    ip = str(_pick(d, "ip", "query", "ipaddress", default=t))
    lat, lon = _pick(d, "lat", "latitude"), _pick(d, "lon", "lng", "longitude")
    try:
        lat = float(lat) if lat not in (None, "") else None
        lon = float(lon) if lon not in (None, "") else None
    except Exception:
        lat = lon = None
    return {
        "ok": True, "source": f"hub{res.get('endpoint')}",
        "query": t, "ip": ip,
        "isp": str(_pick(d, "isp", "org", default="N/A")),
        "org": str(_pick(d, "org", "isp", "asn", default="N/A")),
        "country": str(_pick(d, "country", "countryname", default="N/A")),
        "country_code": str(_pick(d, "countrycode", "country_code", "cc", default="")),
        "region": str(_pick(d, "region", "regionname", "state", default="N/A")),
        "city": str(_pick(d, "city", "town", default="N/A")),
        "zip": str(_pick(d, "zip", "postal", "pincode", default="")),
        "timezone": str(_pick(d, "timezone", "time_zone", default="N/A")),
        "as": str(_pick(d, "as", "asn", "asname", default="N/A")),
        "lat": lat, "lon": lon,
        "is_proxy": _b(_pick(d, "proxy", "isproxy", default=False)),
        "is_mobile": _b(_pick(d, "mobile", "ismobile", default=False)),
        "is_hosting": _b(_pick(d, "hosting", "ishosting", "datacenter", default=False)),
        "maps_link": f"https://maps.google.com/?q={lat},{lon}" if lat and lon else "",
    }


# =====================================================================
# 🏦 IFSC  →  /ifsc
# =====================================================================
def hub_ifsc(code: str) -> dict:
    clean = re.sub(r"[^A-Za-z0-9]", "", code or "").upper()
    if len(clean) != 11:
        return {"ok": False, "error": "IFSC is 11 characters (example SBIN0000001)"}
    res = hub_get("/ifsc", {"ifsc": clean}, timeout=40)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    bank = str(_pick(d, "bank", "bankname", "bank_name", default="Bank"))
    branch = str(_pick(d, "branch", "branchname", "branch_name", default="Branch"))
    address = str(_pick(d, "address", "addr", default=""))
    maps_q = requests.utils.quote(f"{bank} {branch} {address}")
    return {
        "ok": True, "source": "hub/ifsc", "ifsc": clean,
        "bank": bank, "branch": branch, "address": address,
        "city": str(_pick(d, "city", default="")),
        "district": str(_pick(d, "district", default="")),
        "state": str(_pick(d, "state", default="")),
        "contact": str(_pick(d, "contact", "phone", "tel", default="")),
        "micr": str(_pick(d, "micr", "micr_code", default="N/A")),
        "neft": _b(_pick(d, "neft", default=False)),
        "rtgs": _b(_pick(d, "rtgs", default=False)),
        "imps": _b(_pick(d, "imps", default=False)),
        "upi": _b(_pick(d, "upi", default=False)),
        "maps_link": f"https://maps.google.com/?q={maps_q}",
    }


# =====================================================================
# 📮 PINCODE  →  /pincode
# =====================================================================
def hub_pincode(pin: str) -> dict:
    clean = re.sub(r"[^\d]", "", pin or "")
    if len(clean) != 6:
        return {"ok": False, "error": "Pincode is 6 digits (example 800001)"}
    res = hub_get("/pincode", {"pincode": clean}, timeout=40)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    pos = _find_list(d, keys=("postoffice", "postoffices", "post_office", "offices", "results", "data"))
    names = []
    for p in pos[:12]:
        if isinstance(p, dict):
            nm = _pick(p, "name", "officename", "postoffice", "office", default="")
            if nm:
                names.append(str(nm))
        elif isinstance(p, str):
            names.append(p)
    district = str(_pick(d, "district", "dist", default=""))
    state = str(_pick(d, "state", default=""))
    return {
        "ok": True, "source": "hub/pincode", "pincode": clean,
        "district": district, "state": state,
        "taluk": str(_pick(d, "taluk", "taluka", "block", default="")),
        "division": str(_pick(d, "division", default="")),
        "region": str(_pick(d, "region", default="")),
        "circle": str(_pick(d, "circle", default="")),
        "branch_type": str(_pick(d, "branchtype", "branch_type", default="")),
        "delivery": str(_pick(d, "deliverystatus", "delivery", default="")),
        "post_offices": names,
        "total_offices": int(_pick(d, "total", "totaloffices", "count", default=len(names)) or len(names)),
        "maps_link": f"https://maps.google.com/?q={requests.utils.quote(district + ' ' + state)}",
    }


# =====================================================================
# ⚡ TERABOX  →  /terabox-file → /terabox-stream(-v3/v2)
# =====================================================================
def hub_terabox(url: str) -> dict:
    """TeraBox file list + direct links. cloud_tools.resolve_terabox() jaisa shape."""
    res = hub_try([("/terabox-file", {"url": url}),
                   ("/terabox-stream-v3", {"url": url})], timeout=20)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    raw = _find_list(d, keys=("files", "items", "list", "links", "data", "results"))
    files = []
    for f in raw[:20]:
        if not isinstance(f, dict):
            if isinstance(f, str) and f.startswith("http"):
                files.append({"name": "file", "size": 0, "size_h": "—", "link": f})
            continue
        link = str(_pick(f, "link", "url", "download", "downloadlink", "direct", "dlink", "stream", default="") or "")
        if not link:
            continue
        size = _pick(f, "size", "filesize", "length", default=0)
        try:
            size = int(float(size))
        except Exception:
            size = 0
        files.append({
            "name": str(_pick(f, "name", "filename", "file_name", "title", default="file")),
            "size": size, "size_h": _size_h(size) if size else str(_pick(f, "size_h", "sizehuman", default="—")),
            "link": link,
            "thumb": str(_pick(f, "thumb", "thumbnail", "thumbnails", "image", default="") or ""),
        })
    if not files:
        # shayad single file ka direct link bhi ho
        one = str(_pick(d, "link", "url", "download", "downloadlink", "stream", default="") or "")
        if one.startswith("http"):
            files = [{"name": str(_pick(d, "name", "filename", "title", default="file")),
                      "size": 0, "size_h": "—", "link": one, "thumb": ""}]
    if not files:
        return {"ok": False, "error": "Hub ne is link par koi file nahi di"}
    return {"ok": True, "source": f"hub{res.get('endpoint')}", "files": files, "count": len(files)}


def _size_h(n) -> str:
    try:
        n = float(n)
    except Exception:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024


# =====================================================================
# ▶️ YOUTUBE  →  /youtube-all → /youtube-info
# =====================================================================
def hub_yt_download(url: str, kind: str = "video", quality: str = "") -> dict:
    """v47: hub ka NAYA /youtube-download (hub v2.2) — asli video+audio links.

    Hub v2.2 me 2 bug fix hue the (NameError + galat yt-dlp clients) — ab hub 1-3s me
    links deta hai aur har link ke saath **proxy_url** (IP-lock free) aata hai.

    Returns {"ok", "title", "duration", "best_url", "direct_url", "audio_url", "links", "source"}.
    best_url = proxy link (jahan hub se stream hota hai) — pehle isi ko use karo, direct
    link sirf fallback (wo IP-locked ho sakta hai).
    """
    params = {"url": url}
    if kind == "audio":
        params["type"] = "audio"
    if quality:
        params["quality"] = str(quality)
    pairs = [("/youtube-download", dict(params)), ("/ytdl", dict(params))]
    if kind == "audio":
        pairs.append(("/youtube-mp3", {"url": url}))
    res = hub_try(pairs, timeout=75)
    if not res.get("ok"):
        out = {"ok": False, "error": res.get("error") or "Hub se download link nahi mila"}
        if res.get("disabled_by_hub"):
            out["disabled_by_hub"] = True
        return out
    d = res["data"] if isinstance(res.get("data"), dict) else {}
    links = [l for l in (d.get("links") or []) if isinstance(l, dict)]

    def _by_type(t: str) -> dict:
        for l in links:
            if str(l.get("type")) == t:
                return l
        return {}

    # v48: VIDEO links ko quality ke hisaab se sort karo — 1080p sabse pehle
    def _qnum(l: dict) -> int:
        m = re.search(r"(\d{3,4})", str(l.get("quality") or ""))
        try:
            return int(m.group(1)) if m else 0
        except Exception:  # noqa: BLE001
            return 0

    videos = sorted([l for l in links if str(l.get("type")) == "video"],
                    key=_qnum, reverse=True)
    audio = _by_type("audio")
    chosen = videos[0] if videos else (audio or (links[0] if links else {}))
    best = (chosen.get("proxy_url") or chosen.get("url")
            or d.get("proxy_download_url") or d.get("download_url") or "")
    # 480p/backup link — 1080p file Telegram limit se badi ho to ye kaam aayega
    backup = {}
    for l in videos[1:]:
        if l.get("url") and str(l.get("url")) != str(chosen.get("url")):
            backup = l
            break
    if not backup and chosen is audio and videos:
        backup = videos[-1]
    return {
        "ok": bool(best),
        "source": str(res.get("endpoint") or "hub"),
        "title": d.get("title") or "",
        "duration": d.get("duration") or 0,
        "best_url": str(best or ""),
        "quality": str(chosen.get("quality") or ""),
        "hd": bool(chosen.get("hd")) or _qnum(chosen) >= 1080,
        "backup_url": str(backup.get("url") or ""),
        "backup_quality": str(backup.get("quality") or ""),
        "direct_url": str(chosen.get("url") or d.get("download_url") or ""),
        "audio_url": str(audio.get("proxy_url") or audio.get("url")
                         or d.get("proxy_audio_url") or d.get("audio_url") or ""),
        "links": links,
        "endpoint": res.get("endpoint"),
    }


def hub_youtube(url: str) -> dict:
    """YouTube link → video ke direct mp4/audio links (clip maker + downloader ke liye)."""
    res = hub_try([("/youtube-all", {"url": url}), ("/youtube-info", {"url": url})], timeout=60)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]

    def _link_of(node) -> str:
        if isinstance(node, str):
            return node if node.startswith("http") else ""
        if isinstance(node, dict):
            return str(_pick(node, "url", "link", "download", "downloadurl", "src", default="") or "")
        return ""

    video = ""
    for key in ("hd", "hdurl", "video_hd", "720p", "1080p", "video", "videourl", "mp4", "url", "download"):
        v = d.get(key) if isinstance(d, dict) else None
        if isinstance(v, dict):
            for sub in ("url", "link", "download", "hd"):
                if isinstance(v.get(sub), str) and v[sub].startswith("http"):
                    video = v[sub]
                    break
        if not video and isinstance(v, str) and v.startswith("http") and not v.endswith(".m4a"):
            video = v
        if video:
            break
    fmts = _find_list(d, keys=("formats", "videos", "medias", "urls", "links", "downloads"))
    for f in fmts:
        if video:
            break
        if isinstance(f, dict):
            has_v = _b(_pick(f, "hasvideo", "video", "isvideo", default=True))
            ln = _link_of(f)
            if ln and has_v and ((".mp4" in ln) or "mime" in str(f).lower()):
                video = ln
    audio = ""
    for f in fmts:
        if audio:
            break
        if isinstance(f, dict) and _b(_pick(f, "hasaudio", "audio", "isaudio", default=False)):
            audio = _link_of(f)
    if not video:
        for key in ("audio", "mp3", "m4a"):
            v = d.get(key) if isinstance(d, dict) else None
            if isinstance(v, str) and v.startswith("http"):
                audio = audio or v
    return {
        "ok": bool(video or audio), "source": f"hub{res.get('endpoint')}",
        "video": video, "audio": audio,
        "title": str(_pick(d, "title", "name", default="") or ""),
        "duration": _pick(d, "duration", "length", default=0),
        "thumb": str(_pick(d, "thumb", "thumbnail", "image", default="") or ""),
        "error": "" if (video or audio) else "Hub ne is video ka direct link nahi diya",
    }


# =====================================================================
# 🐦 X / TWITTER VIDEO  →  /twitter-video-v6 → hd-video → v5 → v2
# =====================================================================
def hub_twitter_video(url: str) -> dict:
    res = hub_try([("/twitter-video-v6", {"url": url}), ("/twitter-hd-video", {"url": url}),
                   ("/twitter-video-v5", {"url": url}), ("/twitter-video-v2", {"url": url})], timeout=60)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    link = ""
    for key in ("hd", "url", "video", "videourl", "download", "link", "mp4", "sd"):
        v = d.get(key) if isinstance(d, dict) else None
        if isinstance(v, str) and v.startswith("http"):
            link = v
            break
        if isinstance(v, dict):
            for sub in ("url", "link", "hd", "download"):
                if isinstance(v.get(sub), str) and v[sub].startswith("http"):
                    link = v[sub]
                    break
        if link:
            break
    for f in _find_list(d, keys=("variants", "formats", "medias", "videos", "urls", "data")):
        if link:
            break
        if isinstance(f, dict):
            ln = str(_pick(f, "url", "link", "src", default="") or "")
            if ln.startswith("http") and (".mp4" in ln or "video" in ln):
                link = ln
    if not link:
        return {"ok": False, "error": "Hub ne video link nahi diya"}
    return {"ok": True, "source": f"hub{res.get('endpoint')}", "url": link,
            "title": str(_pick(d, "title", "text", "description", default="") or "")}


# =====================================================================
# 📸 SOCIAL PROFILES (ID finder upgrade)  →  instagram / snap / twitter
# =====================================================================
def hub_insta_profile(username: str) -> dict:
    res = hub_try([("/instagram-profile", {"username": username.lstrip("@")})], timeout=45)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    d = res["data"]
    return {"ok": True, "source": "hub/instagram-profile",
            "full_name": str(_pick(d, "fullname", "full_name", "name", default="") or ""),
            "bio": str(_pick(d, "biography", "bio", "description", default="") or "")[:180],
            "followers": _pick(d, "followers", "followercount", "followerscount", default=""),
            "following": _pick(d, "following", "followingcount", default=""),
            "posts": _pick(d, "posts", "postscount", "media_count", default=""),
            "private": _b(_pick(d, "private", "isprivate", default=False)),
            "verified": _b(_pick(d, "verified", "isverified", default=False)),
            "pic": str(_pick(d, "profilepic", "profile_pic_url", "profilepicurl", "pic", default="") or "")}


def hub_insta_posts(username: str) -> dict:
    res = hub_try([("/instagram-posts", {"username": username.lstrip("@")})], timeout=50)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    items = _find_list(res["data"], keys=("posts", "items", "data", "results", "medias"))
    out = []
    for p in items[:12]:
        if isinstance(p, dict):
            out.append({"caption": str(_pick(p, "caption", "text", "title", default="") or "")[:80],
                        "link": str(_pick(p, "link", "url", "posturl", default="") or ""),
                        "likes": _pick(p, "likes", "likecount", default="")})
    return {"ok": bool(out), "posts": out, "count": len(out)}


def hub_snap_stories(username: str) -> dict:
    res = hub_try([("/snap-stories", {"username": username.lstrip("@")}),
                   ("/snap-highlights", {"username": username.lstrip("@")})], timeout=45)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    items = _find_list(res["data"], keys=("stories", "highlights", "items", "data", "results"))
    urls = []
    for s in items[:15]:
        if isinstance(s, dict):
            u = str(_pick(s, "url", "link", "media", "mediaurl", "snap", default="") or "")
            if u.startswith("http"):
                urls.append(u)
        elif isinstance(s, str) and s.startswith("http"):
            urls.append(s)
    return {"ok": bool(urls), "urls": urls, "count": len(urls)}


def hub_twitter_profile(username: str) -> dict:
    res = hub_try([("/twitter-profile-v2", {"username": username.lstrip("@")}),
                   ("/twitter-profile", {"url": f"https://x.com/{username.lstrip('@')}"})], timeout=45)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    d = res["data"]
    return {"ok": True, "source": "hub/twitter-profile",
            "name": str(_pick(d, "name", "displayname", "fullname", default="") or ""),
            "handle": str(_pick(d, "username", "screenname", "handle", default=username) or username),
            "bio": str(_pick(d, "description", "bio", default="") or "")[:180],
            "followers": _pick(d, "followers", "followerscount", "followers_count", default=""),
            "tweets": _pick(d, "tweets", "statusescount", "tweetcount", default=""),
            "verified": _b(_pick(d, "verified", "isverified", "isblueverified", default=False)),
            "pic": str(_pick(d, "profileimage", "profile_image_url", "pic", "avatar", default="") or "")}


# =====================================================================
# 🧾 GST / PAN  →  kagaz suite upgrade
# =====================================================================
def hub_gst(gstin: str) -> dict:
    g = re.sub(r"\s+", "", (gstin or "")).upper()
    if len(g) != 15:
        return {"ok": False, "error": "GSTIN is 15 characters (example 19BOKPS7056D1ZI)"}
    res = hub_try([("/gst-search", {"gstin": g}), ("/gst-info", {"gst": g}),
                   ("/gst-direct", {"gstin": g}), ("/gst-info-v2", {"gst": g})], timeout=60)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    return {
        "ok": True, "source": f"hub{res.get('endpoint')}", "gstin": g,
        "legal_name": str(_pick(d, "legalname", "legal_name", "name", "lgnm", default="") or ""),
        "trade_name": str(_pick(d, "tradename", "trade_name", "tradenam", "trade_name_", default="") or ""),
        "status": str(_pick(d, "status", "gststatus", "sts", default="") or ""),
        "type": str(_pick(d, "gsttype", "taxpayertype", "dty", "type", default="") or ""),
        "state": str(_pick(d, "state", "pradr_state", default="") or ""),
        "address": str(_pick(d, "address", "pradr", "addr", default="") or "")[:220],
        "reg_date": str(_pick(d, "regdate", "registrationdate", "rgdt", default="") or ""),
        "pan": str(_pick(d, "pan", "pan_no", default="") or ""),
        "raw": {k: v for k, v in list(d.items())[:25]} if isinstance(d, dict) else {},
    }


def hub_pan(pan: str) -> dict:
    p = re.sub(r"[^A-Za-z0-9]", "", (pan or "")).upper()
    if len(p) != 10:
        return {"ok": False, "error": "PAN is 10 characters (example AAYFK4129N)"}
    res = hub_try([("/pan-to-gst-v4", {"pan": p}), ("/pan-to-gst-v3", {"pan": p}),
                   ("/pan-to-gst-v2", {"pan": p}), ("/pan-to-gst", {"pan": p}),
                   ("/pan-info", {"pan": p})], timeout=60)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    gsts = _find_list(d, keys=("gstin", "gstins", "results", "data", "items", "list"))
    out = []
    for g in gsts[:12]:
        if isinstance(g, dict):
            num = str(_pick(g, "gstin", "gst", "number", default="") or "")
            if num:
                out.append({"gstin": num, "status": str(_pick(g, "status", "sts", default="") or ""),
                            "name": str(_pick(g, "name", "legalname", "tradename", default="") or "")})
        elif isinstance(g, str) and len(g) == 15:
            out.append({"gstin": g, "status": "", "name": ""})
    single = str(_pick(d, "gstin", "gst", default="") or "")
    if single and not out:
        out.append({"gstin": single, "status": str(_pick(d, "status", default="") or ""),
                    "name": str(_pick(d, "name", "legalname", default="") or "")})
    return {"ok": bool(out) or bool(_pick(d, "status", "name")), "source": f"hub{res.get('endpoint')}",
            "pan": p, "gstins": out, "count": len(out),
            "status": str(_pick(d, "status", "panstatus", default="") or ""),
            "name": str(_pick(d, "name", "legalname", default="") or "")}


# =====================================================================
# 📱 NUMBER / LEAK (existing num-info ka hub version)
# =====================================================================
def hub_num_info(number_digits: str) -> dict:
    dg = re.sub(r"\D", "", number_digits or "")
    if len(dg) == 10:
        dg = "91" + dg
    if len(dg) != 12:
        return {"ok": False, "error": "10 digit number bhejo"}
    res = hub_try([("/num-info", {"q": dg}), ("/leak-v1", {"q": dg})], timeout=60)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "Hub ne jawab nahi diya"}
    return {"ok": True, "source": f"hub{res.get('endpoint')}", "data": res["data"]}


# =====================================================================
# 🧾 NUM REPORT (full)  →  /num-info   [hub par abhi OFF ho sakta hai]
# =====================================================================
def hub_num_report(number_digits: str) -> dict:
    """Number → poora report (naam/papa/address). Hub par ON ho to data aayega."""
    dg = re.sub(r"\D", "", number_digits or "")
    if len(dg) == 10:
        dg = "91" + dg
    if len(dg) != 12:
        return {"ok": False, "error": "10 digit number bhejo"}
    res = hub_try([("/num-info", {"q": dg}), ("/number-info", {"q": dg}), ("/num", {"q": dg})], timeout=70)
    if not res.get("ok"):
        return {"ok": False, "disabled_by_hub": res.get("disabled_by_hub", False),
                "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    people = []
    raw_people = d.get("people") if isinstance(d, dict) else None
    if not isinstance(raw_people, list):
        raw_people = _find_list(d, keys=("people", "records", "results", "data"))
    for p in (raw_people or [])[:5]:
        if not isinstance(p, dict):
            continue
        phones = p.get("phones") or p.get("alt_phones") or []
        people.append({
            "name": str(_pick(p, "name", "full_name", default="") or ""),
            "father": str(_pick(p, "father_name", "father", "guardian", default="") or ""),
            "phones": [str(x) for x in phones][:6] if isinstance(phones, list) else [],
            "alt_phones": [str(x) for x in (p.get("alt_phones") or [])][:6],
            "region": str(_pick(p, "region", "operator", "circle", default="") or ""),
            "govt_ids": [str(x) for x in (p.get("govt_ids") or [])][:4],
            "addresses": [str(x) for x in (p.get("addresses") or [])][:4]
                         if isinstance(p.get("addresses"), list) else ([str(p.get("address"))] if p.get("address") else []),
            "sources": p.get("sources") or [],
        })
    return {"ok": bool(people), "source": res.get("source") or f"hub{res.get('endpoint')}",
            "number": dg, "people": people, "count": len(people),
            "record_count": _pick(d, "record_count", "total", default=len(people)),
            "sources_used": d.get("sources_used") if isinstance(d, dict) else None,
            "formatted": (d.get("formatted") if isinstance(d, dict) else "") or "",
            "error": "" if people else "Is number ka koi record nahi mila."}


# =====================================================================
# 🚗 VEHICLE FULL REPORT  →  /vehicle-report   [hub par abhi OFF ho sakta hai]
# =====================================================================
def hub_vehicle_report_new(plate: str) -> dict:
    """Plate → RC + RTO + insurance + PUC + challans (ek hi call me)."""
    pl = re.sub(r"[^A-Za-z0-9]", "", plate or "").upper()
    if len(pl) < 8:
        return {"ok": False, "error": "Send a correct number plate (example BR30AR0802)"}
    res = hub_try([("/vehicle-report", {"number": pl}), ("/vehicle-full", {"number": pl}),
                   ("/rc-info", {"rc": pl})], timeout=70)
    if not res.get("ok"):
        return {"ok": False, "disabled_by_hub": res.get("disabled_by_hub", False),
                "status": res.get("status"),
                "error": res.get("error") or "Hub ne jawab nahi diya"}
    d = res["data"]
    if not isinstance(d, dict):
        return {"ok": False, "error": "Hub ka jawab samajh nahi aaya"}
    return {"ok": True, "source": res.get("source") or "hub/vehicle-report",
            "plate": pl, "raw": d,
            "vehicle": d.get("vehicle") if isinstance(d.get("vehicle"), dict) else {},
            "owner": d.get("owner") if isinstance(d.get("owner"), dict) else {},
            "rto": d.get("rto") if isinstance(d.get("rto"), dict) else {},
            "rc": d.get("rc") if isinstance(d.get("rc"), dict) else {},
            "insurance": d.get("insurance") if isinstance(d.get("insurance"), dict) else {},
            "puc": d.get("puc") if isinstance(d.get("puc"), dict) else {},
            "challans": d.get("challans") if isinstance(d.get("challans"), dict) else {},
            "formatted": str(d.get("formatted") or ""),
            "server_line": str(d.get("server_line") or "")}


# =====================================================================
# 🔑 KEY INFO  →  /key-info
# =====================================================================
def hub_key_info() -> dict:
    res = hub_get("/key-info", {}, timeout=40)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    d = res["data"]
    return {"ok": True, "plan": _pick(d, "plan", default=""), "status": _pick(d, "status", default=""),
            "expires": _pick(d, "expires_at_ist", "expires", default=""), "raw": d}


# =====================================================================
# 🎵 SONG SEARCH  →  /song  (iTunes preview + metadata)
# =====================================================================
def hub_song(query: str) -> dict:
    res = hub_get("/song", {"song": query}, timeout=50)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    items = _find_list(res["data"], keys=("results", "data", "songs"))
    out = []
    for it in items[:8]:
        if isinstance(it, dict):
            out.append({"title": str(_pick(it, "title", "name", default="") or ""),
                        "artist": str(_pick(it, "artists", "artist", default="") or ""),
                        "album": str(_pick(it, "album", default="") or ""),
                        "preview": str(_pick(it, "download_url", "preview_url", default="") or ""),
                        "art": str(_pick(it, "artwork", default="") or ""),
                        "applemusic": str(_pick(it, "apple_music_url", default="") or "")})
    return {"ok": bool(out), "songs": out, "count": len(out),
            "error": "" if out else "Koi gaana nahi mila"}


# =====================================================================
# admin status
# =====================================================================
def status_card() -> str:
    base = hub_base()
    key = hub_key()
    ready = hub_ready()
    lines = ["🔌 <b>API HUB — status</b>", "━━━━━━━━━━━━━━━━━━━━━━",
             f"• Base: <code>{base}</code>",
             f"• Key: {'✅ ' + hesc(key[:8]) + '…' if ready else '❌ <b>nahi lagi</b>'}",
             "• Plan: <b>Demo = ALL ENDPOINTS</b> (lifetime) · apni key Dashboard → API Keys se"]
    lines += ["",
              "✅ <b>Chalte hain:</b> 🏦 IFSC · 📮 PINCODE · 🌐 IP · 📲 IMEI (brand/model) ·",
              "▶️ YouTube info · 🧮 GST/PAN format check · 🎵 Song search · 🔑 Password breach check",
              "",
              "⛔ <b>Hub par abhi OFF:</b> 🚗 Vehicle RC/challan · 📱 Number records (naam/address)",
              "<i>Ye hub ke apne switch se band hain (safety). Chalu karne ke liye hub ke",
              "dashboard/settings me sensitive endpoints ON karo ya UPSTREAM_KEY set karo.</i>",
              "⛔ <b>Upstream key chahiye:</b> ⚡ TeraBox · 📸 Instagram · 👻 Snapchat"]
    if not ready:
        lines += ["", "Render → Environment: <code>HUB_API_KEY</code> = <code>Demo</code> (ya apni key)"]
    return "\n".join(lines)


def hesc(t) -> str:
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def live_test() -> dict:
    """Hub par live check — IP + key-info (kaun kaun se endpoint chalu hain bhi batata hai)."""
    if not hub_ready():
        return {"ok": False, "error": "Hub band hai (HUB_ENABLED=off)"}
    res = hub_get("/ip-v2", {"ip": "8.8.8.8"}, timeout=50)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    d = res["data"]
    ki = hub_key_info()
    plan = hesc(ki.get("plan") or "?") if ki.get("ok") else "?"
    return {"ok": True, "say": f"ip-v2 ✅ ({_pick(d, 'country', 'city', default='ok')}) · plan: {plan}"}
