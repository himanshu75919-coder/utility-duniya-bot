# -*- coding: utf-8 -*-
"""
v106 — ⚡ IG FAST ENGINE — Instagram ka 1-5 second wala raasta
==============================================================

PROBLEM JO YE SOLVE KARTA HAI
-----------------------------
Pehle Instagram download ke liye 6-7 engines ki race chalti thi aur aksar
jeetne wala engine 20-55 second leta tha (loader.to 12-45s, jina render ~20s,
yt-dlp login-wall). Natija: user ko 2-3 minute wait, phir bhi kai baar fail.

Ye engine Instagram ke KHUD ke public JSON API par chalta hai — wahi jo
Instagram ka web/app khud use karta hai:

    https://i.instagram.com/api/v1/media/{media_id}/info/

• Post/Reel/IGTV/carousel — teeno ke HD mp4 + full-size photos milti hain.
• Login nahi chahiye (public posts ke liye). Koi third-party site nahi.
• 1 link = 1 chhoti JSON request + 1 file download ≈ **1-5 second**.

STORY SUPPORT
-------------
Story/highlight Instagram bina LOGIN ke kisi ko nahi deta (24h privacy).
Isliye: agar bot par Instagram ki cookie (IG_COOKIE env / cookies.txt) lagi
hai to story bhi isi engine se nikalti hai (reels_media API). Cookie na ho
to 30-55 second ki bekaar race ki jagah TURANT saaf message milta hai.

RATE-LIMIT SURAKSHA (429)
-------------------------
Datacenter IPs par Instagram kabhi-kabhi 429 deta hai. Ek 429 par ye engine
90-180 second ke COOLDOWN par chala jaata hai — us dauran ye request par
0.001s me None lautata hai aur baaki engines apna kaam karte hain. Isse
(a) waqt zaya nahi hota, (b) IP par aur hammer nahi padta.

CRASH-PROOF DESIGN (bot ke rules)
---------------------------------
• Har function kabhi exception nahi raise karta — hamesha None/{} lautata hai.
• Koi blocking call 15s se zyada nahi (socket timeout).
• media_downloader ko LAZY import karta hai (circular import se bachao).
"""
from __future__ import annotations

import json
import os
import re
import threading
import time

try:
    import requests
except Exception:                                                  # noqa: BLE001
    requests = None

# ---------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------
_API_BASE = "https://i.instagram.com/api/v1"
_APP_ID = "936619743392459"          # Instagram web ka public app id

# Desktop browser UA pool — ek hi UA se saari request na jaayein
_UAS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
)

_SC_ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
_SC_REV = {c: i for i, c in enumerate(_SC_ABC)}

STATS = {
    "hits": 0, "miss": 0, "cool429": 0, "private": 0,
    "stories": 0, "profiles": 0, "since": time.time(),
}
_LOCK = threading.RLock()
_COOL_UNTIL = 0.0        # 429 cooldown expiry (epoch)
_UA_IDX = 0
_SESSION = None

_CD = 90                 # 429 ke baad cooldown seconds (baad me dheere badhta hai)


# ---------------------------------------------------------------------
# SESSION (ek hi keep-alive pool — fast + kam TLS handshake)
# ---------------------------------------------------------------------
def _sess():
    global _SESSION, _UA_IDX
    if requests is None:
        return None
    with _LOCK:
        if _SESSION is None:
            s = requests.Session()
            a = requests.adapters.HTTPAdapter(pool_connections=8,
                                              pool_maxsize=16, max_retries=0)
            s.mount("https://", a)
            s.mount("http://", a)
            _SESSION = s
        _UA_IDX = (_UA_IDX + 1) % len(_UAS)
        return _SESSION


def _headers(extra: dict | None = None) -> dict:
    h = {
        "User-Agent": _UAS[_UA_IDX % len(_UAS)],
        "x-ig-app-id": _APP_ID,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.instagram.com/",
        "Origin": "https://www.instagram.com",
    }
    ck = _cookie_header()
    if ck:
        h["Cookie"] = ck
    if extra:
        h.update(extra)
    return h


def cool_active() -> bool:
    return time.time() < _COOL_UNTIL


def _cool_mark(seconds: int | None = None):
    """429 par cooldown lagao (dheere-dheere badhta hai)."""
    global _COOL_UNTIL, _CD
    with _LOCK:
        _CD = min(600, max(90, int(_CD * 1.5 if seconds is None else seconds)))
        _COOL_UNTIL = time.time() + _CD
        STATS["cool429"] += 1


def _api_get(path: str, params: dict | None = None, timeout: float = 12.0):
    """API GET → (json|None, status). Kabhi exception nahi.

    429 par cooldown set hota hai. Login-required/private par json me
    message milta hai — caller decide karta hai.
    """
    if requests is None or cool_active():
        return None, 0
    s = _sess()
    if s is None:
        return None, 0
    try:
        r = s.get(_API_BASE + path, params=params, headers=_headers(),
                  timeout=timeout, allow_redirects=True)
    except Exception:                                              # noqa: BLE001
        return None, 0
    st = r.status_code
    try:
        if st == 429:
            _cool_mark()
            return None, 429
        if st == 200:
            try:
                return r.json(), 200
            except Exception:                                      # noqa: BLE001
                return None, 200
        # 302→login, 400, 403, 404 sab yahan
        return None, st
    finally:
        try:
            r.close()
        except Exception:                                          # noqa: BLE001
            pass


# ---------------------------------------------------------------------
# COOKIE SUPPORT (story/highlight ke liye zaroori; post/reel ke liye bonus)
# ---------------------------------------------------------------------
def _cookie_header() -> str:
    """IG_COOKIE env / cookies.txt se sessionid cookie nikalo.

    Formats: 'sessionid=abc123', poori cookie line, ya Netscape cookies.txt.
    """
    try:
        raw = (os.getenv("IG_COOKIE") or os.getenv("YTDLP_COOKIES") or "").strip()
        if not raw:
            try:
                from modules import media_downloader as _MD      # lazy
                p = _MD._cookiefile()
                if p and os.path.isfile(p):
                    raw = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:                                      # noqa: BLE001
                raw = ""
        if not raw:
            return ""
        if "sessionid" not in raw:
            return ""
        out = set()
        for ln in raw.splitlines():
            ln = ln.strip()
            if ln.startswith("#") or not ln:
                continue
            parts = ln.split("\t")
            if len(parts) >= 7 and parts[5] in ("sessionid", "sessionid_ss", "ds_user_id"):
                out.add(f"{parts[5]}={parts[6]}")
            elif "=" in ln:
                for kv in re.split(r";\s*", ln):
                    k = kv.split("=", 1)[0].strip()
                    if k in ("sessionid", "sessionid_ss", "ds_user_id"):
                        out.add(kv.strip())
        return "; ".join(sorted(out))
    except Exception:                                              # noqa: BLE001
        return ""


def has_login_cookie() -> bool:
    return bool(_cookie_header())


# ---------------------------------------------------------------------
# URL PARSING + SHORTCODE ↔ MEDIA ID
# ---------------------------------------------------------------------
def shortcode_to_media_id(code: str) -> str:
    """Instagram shortcode → numeric media id (base64 jaisa)."""
    try:
        n = 0
        for ch in (code or "").strip():
            if ch not in _SC_REV:
                return ""
            n = n * 64 + _SC_REV[ch]
        return str(n) if n > 0 else ""
    except Exception:                                              # noqa: BLE001
        return ""


def parse_ig_url(url: str) -> dict:
    """Instagram link → {kind, code, user, story_id}. kind:
    reel | post | tv | story | highlight | profile | unknown
    """
    out = {"kind": "unknown", "code": "", "user": "", "story_id": ""}
    try:
        u = str(url or "").strip()
        if not u:
            return out
        u = re.sub(r"[\x00-\x20\x7f]+", "", u)
        u = u.split("#")[0]
        low = u.lower()
        m = re.search(r"(?:instagram\.com|instagr\.am)/stories/highlight(?:s)?/(\d+)", low)
        if m:
            out.update(kind="highlight", story_id=m.group(1))
            return out
        m = re.search(r"(?:instagram\.com|instagr\.am)/stories/([A-Za-z0-9._]{1,60})(?:/(\d+))?", low)
        if m:
            out.update(kind="story", user=m.group(1), story_id=m.group(2) or "")
            return out
        m = re.search(r"(?:instagram\.com|instagr\.am)/(?:[^/?#]+/)?(?:reel|reels)/([A-Za-z0-9_-]+)", u, re.I)
        if m:
            out.update(kind="reel", code=m.group(1))
            return out
        m = re.search(r"(?:instagram\.com|instagr\.am)/(?:[^/?#]+/)?tv/([A-Za-z0-9_-]+)", u, re.I)
        if m:
            out.update(kind="tv", code=m.group(1))
            return out
        m = re.search(r"(?:instagram\.com|instagr\.am)/(?:[^/?#]+/)?p/([A-Za-z0-9_-]+)", u, re.I)
        if m:
            out.update(kind="post", code=m.group(1))
            return out
        m = re.search(r"(?:instagram\.com|instagr\.am)/([A-Za-z0-9._]{1,40})(?:[/?#]|$)", u, re.I)
        if m:
            _u = m.group(1).strip(".").lower()
            reserved = {"p", "reel", "reels", "tv", "stories", "s", "highlight",
                        "explore", "accounts", "direct", "about", "developer",
                        "embed", "directory", "web", "graphql", "api", "static",
                        "support", "help", "terms", "www"}
            if _u and _u not in reserved:
                out.update(kind="profile", user=m.group(1).strip("."))
                return out
        return out
    except Exception:                                              # noqa: BLE001
        return {"kind": "unknown", "code": "", "user": "", "story_id": ""}


# ---------------------------------------------------------------------
# JSON → MEDIA (video bytes / photo bytes)
# ---------------------------------------------------------------------
def _best_video_url(item: dict) -> str:
    try:
        vs = item.get("video_versions") or []
        # type 101/102/103 — sabse upar wala best; width*height se double check
        vs = [v for v in vs if v.get("url")]
        if not vs:
            return ""
        vs.sort(key=lambda v: (int(v.get("width") or 0) * int(v.get("height") or 0),
                               int(v.get("type") or 999) == 101), reverse=True)
        return vs[0]["url"]
    except Exception:                                              # noqa: BLE001
        return ""


def _best_image_url(item: dict) -> str:
    try:
        cs = ((item.get("image_versions2") or {}).get("candidates")) or []
        cs = [c for c in cs if c.get("url")]
        if not cs:
            return ""
        cs.sort(key=lambda c: int(c.get("width") or 0) * int(c.get("height") or 0),
                reverse=True)
        return cs[0]["url"]
    except Exception:                                              # noqa: BLE001
        return ""


def _fetch_bytes(url: str, cap_mb: int, timeout: int = 30) -> bytes | None:
    """CDN se file uthao (cap + timeout ke saath)."""
    if not url:
        return None
    try:
        from modules import media_downloader as _MD                # lazy
        return _MD._http_get_capped(url, cap_mb, headers={"User-Agent": _UAS[0]},
                                    timeout=timeout, want="auto")
    except Exception:                                              # noqa: BLE001
        return None


def _item_title(item: dict) -> str:
    try:
        cap = (item.get("caption") or {}).get("text") or ""
        usr = (item.get("user") or {}).get("username") or ""
        t = cap.replace("\n", " ").strip()[:70]
        return (f"@{usr}" + (f" • {t}" if t else ""))[:90]
    except Exception:                                              # noqa: BLE001
        return ""


def _item_to_result(item: dict, media_cat: str):
    """API ka ek media item → media_downloader-format result dict."""
    try:
        from modules import media_downloader as _MD                # lazy
        mt = item.get("media_type")
        title = _item_title(item)
        # ---- CAROUSEL ----
        car = item.get("carousel_media") or []
        if mt == 8 or len(car) > 1:
            items = []
            for sub in car[:20]:
                if sub.get("media_type") == 2:
                    vb = _fetch_bytes(_best_video_url(sub), _MD.MAX_TG_MB, timeout=40)
                    if vb and len(vb) > 1000:
                        items.append({"type": "video", "bytes": vb})
                else:
                    ib = _fetch_bytes(_best_image_url(sub), 15, timeout=15)
                    jb = _MD._jpeg_fit(ib) if ib else None
                    if jb:
                        items.append({"type": "photo", "bytes": jb})
            if items:
                return {"ok": True, "type": "carousel", "category": media_cat or "post",
                        "title": title, "items": items, "count": len(items),
                        "platform": "Instagram", "engine": "ig-api"}
            return None
        # ---- VIDEO / REEL ----
        if mt == 2 or item.get("video_versions"):
            vb = _fetch_bytes(_best_video_url(item), _MD.MAX_TG_MB, timeout=45)
            if vb and len(vb) > 1000:
                _d, _w, _h = _MD._probe_data(vb)
                return {"ok": True, "type": "video",
                        "category": "reel" if media_cat in ("reel", "tv") else (media_cat or "video"),
                        "title": title, "bytes": vb, "size_mb": _MD._size_mb(vb),
                        "duration": int(_d or 0),
                        "quality": f"{_h}p" if _h else None,
                        "platform": "Instagram", "engine": "ig-api"}
            return None
        # ---- PHOTO ----
        ib = _fetch_bytes(_best_image_url(item), 15, timeout=15)
        jb = _MD._jpeg_fit(ib, max_px=2400, quality=94) if ib else None
        if jb:
            return {"ok": True, "type": "photo", "category": media_cat or "post",
                    "title": title, "bytes": jb, "size_mb": _MD._size_mb(jb),
                    "platform": "Instagram", "engine": "ig-api"}
        return None
    except Exception:                                              # noqa: BLE001
        return None


# ---------------------------------------------------------------------
# PUBLIC ENGINES
# ---------------------------------------------------------------------
def fetch_post(code: str, media_cat: str):
    """Post/Reel/IGTV shortcode → result (1 API call + file download)."""
    if not code or cool_active():
        return None
    mid = shortcode_to_media_id(code)
    if not mid:
        return None
    j, st = _api_get(f"/media/{mid}/info/")
    if st == 429:
        return None
    if not j:
        return None
    try:
        items = j.get("items") or []
        if not items:
            return None
        res = _item_to_result(items[0], media_cat)
        with _LOCK:
            STATS["hits" if res else "miss"] += 1
        return res
    except Exception:                                              # noqa: BLE001
        return None


def fetch_profile_pic(username: str):
    """Profile link → HD profile photo."""
    if not username or cool_active():
        return None
    j, st = _api_get("/users/web_profile_info/", params={"username": username})
    if st == 429 or not j:
        return None
    try:
        u = ((j.get("data") or {}).get("user")) or {}
        url = u.get("profile_pic_url_hd") or u.get("profile_pic_url") or ""
        if not url:
            return None
        from modules import media_downloader as _MD                # lazy
        ib = _fetch_bytes(url, 15, timeout=15)
        jb = _MD._jpeg_fit(ib, max_px=2400, quality=94) if ib else None
        with _LOCK:
            STATS["profiles"] += 1
        if jb:
            return {"ok": True, "type": "photo", "category": "profile",
                    "title": f"@{username} — profile photo",
                    "bytes": jb, "size_mb": _MD._size_mb(jb),
                    "platform": "Instagram", "engine": "ig-api-profile"}
        return None
    except Exception:                                              # noqa: BLE001
        return None


def _user_pk(username: str) -> str:
    try:
        j, st = _api_get("/users/web_profile_info/", params={"username": username})
        if st == 200 and j:
            return str(((j.get("data") or {}).get("user") or {}).get("id") or "")
    except Exception:                                              # noqa: BLE001
        pass
    return ""


def fetch_story(url: str):
    """Story/Highlight link → result. SIRF login-cookie ke saath kaam karta hai.

    Cookie na ho to {'ok': False, 'need_login': True, ...} — caller user ko
    saaf message dikha deta hai (30-55s ki bekaar race nahi hoti).
    """
    p = parse_ig_url(url)
    if p["kind"] not in ("story", "highlight"):
        return None
    if not has_login_cookie():
        return {"ok": False, "need_login": True, "category": p["kind"],
                "error": ("🔐 Instagram STORY bina login ke koi bhi service nahi de sakta "
                          "(Instagram ki apni privacy limit hai — story sirf logged-in "
                          "accounts ko dikhti hai).\n\n"
                          "✅ Bot par apni Instagram cookie lagao, story download ON ho "
                          "jayega — /cookies command se kaise karna hai wo bataya gaya hai.")}
    # highlight: story_id hi reel_id hai; story: username → pk → reels_media
    reel_id = p["story_id"] if p["kind"] == "highlight" else _user_pk(p["user"])
    if not reel_id:
        return {"ok": False, "category": "story",
                "error": ("❌ Ye username/story nahi mili — ya to story 24 ghante me "
                          "expire ho gayi, ya username galat/private hai.")}
    j, st = _api_get("/feed/reels_media/", params={"reel_ids": reel_id})
    if not j:
        return None
    try:
        reels = j.get("reels") or {}
        reel = reels.get(str(reel_id)) or (list(reels.values())[:1] or [None])[0]
        items = (reel or {}).get("items") or []
        if not items:
            return {"ok": False, "category": "story",
                    "error": ("❌ Is account ki koi active story nahi mili — story 24 "
                              "ghante baad apne aap delete ho jaati hai.")}
        # link me specific story id thi to wahi dhundo
        if p["kind"] == "story" and p["story_id"]:
            pick = next((it for it in items if str(it.get("id")) == str(p["story_id"])), None)
            if pick is None:
                pick = items[0]
        else:
            pick = items[0]
        with _LOCK:
            STATS["stories"] += 1
        if p["kind"] == "story" and len(items) > 1:
            # poori active story = saari items ek carousel ki tarah
            car = []
            for it in items[:15]:
                if it.get("media_type") == 2:
                    vb = _fetch_bytes(_best_video_url(it), 48, timeout=40)
                    if vb and len(vb) > 1000:
                        car.append({"type": "video", "bytes": vb})
                else:
                    ib = _fetch_bytes(_best_image_url(it), 15, timeout=15)
                    if ib:
                        car.append({"type": "photo", "bytes": ib})
            if len(car) >= 2:
                return {"ok": True, "type": "carousel", "category": "story",
                        "title": f"@{p['user']} — story ({len(car)} slides)",
                        "items": car, "count": len(car),
                        "platform": "Instagram", "engine": "ig-api-story"}
        return _item_to_result(pick, "story")
    except Exception:                                              # noqa: BLE001
        return None


def fetch_media(url: str, media_cat: str):
    """RACE ENTRY POINT — media_downloader isi ko engine ki tarah call karta hai."""
    try:
        p = parse_ig_url(url)
        if p["kind"] in ("post", "reel", "tv"):
            return fetch_post(p["code"], media_cat)
        if p["kind"] == "profile":
            return fetch_profile_pic(p["user"])
        if p["kind"] in ("story", "highlight"):
            r = fetch_story(url)
            # race me sirf ok results jeet-te hain; need_login/error alag se handle
            return r if (r and r.get("ok")) else None
        return None
    except Exception:                                              # noqa: BLE001
        return None


def diagnostics() -> dict:
    return {
        "enabled": requests is not None,
        "cooldown": cool_active(),
        "cookie": has_login_cookie(),
        **STATS,
    }
