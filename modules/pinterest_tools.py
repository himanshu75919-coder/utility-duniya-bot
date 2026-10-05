# -*- coding: utf-8 -*-
"""
Pinterest Tools — v53.0 (PRO REWRITE)
=====================================
📌 Pinterest HD image + video download + REAL search.

v52.3 me kya galat tha (live test se prove hua):
  • `pinterest_search()` Bing image scrape karta tha → **0 real Pinterest results**
    (test: "cat wallpaper" → 6 results, 0 ). Bot khud bolta tha
    "Pinterest par exact match nahi mila".
  • `pinterest_from_pin_link()` sirf og:image par fallback karta tha — par Pinterest
    ke page me **og:image hota hi nahi** (test: 1 MB HTML, og:image count = 0).
  • Video pins par kuch nahi milta tha → chup-chaap fail.
  • Koi metadata nahi (title/description/pinner/dimensions sab available the, use nahi ho rahe the).

v53.0 ab kya karta hai:
  • **Official Pinterest internal JSON APIs** (koi API key nahi chahiye):
      - `BaseSearchResource/get/` → REAL search results (test: 21 results, original-quality
        URLs, 3840x2400 tak, titles + dimensions ke saath)
      - `PinResource/get/`        → full pin detail (saare 9 sizes, pinner, description,
        repin/comment counts, video streams)
  • **Session warm-up**: pehle pinterest.com hit karke `csrftoken` / `_pinterest_sess`
    cookies lete hain — warna API 403 deta hai (ye bhi test se prove hua).
  • **Video pins** support — MP4 (720p/480p) ya HLS.
  • **3-layer fallback**: JSON API → HTML regex scrape → Bing image search.
    Ek layer fail ho to agla try hota hai; user ko kabhi khaali jawab nahi milta.
  • **TTL cache** (core.cache) — same keyword/pin dobara hit nahi hota.
  • Saare HTTP calls `core.net` se (connection pool + timeout + retry + size cap).

Legal: sirf PUBLIC pins. Koi login nahi, koi private board nahi, koi API key nahi.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from typing import Any, Dict, List, Optional

from modules.core.cache import TTLCache, cached_call
from modules.core.net import NetError, http_bytes, http_get, http_get_json, is_safe_url
from modules.core.telemetry import tracked as _tracked

log = logging.getLogger("ud.pinterest")

__all__ = [
    "pinterest_search", "pinterest_from_pin_link", "pinterest_pin_detail",
    "download_media", "PIN_SIZES", "cache_snapshot",
]

# --------------------------------------------------------------- config
_BROWSER_UA = os.environ.get(
    "PIN_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)
_APP_VERSION = os.environ.get("PIN_APP_VERSION", "e0e1a1c")
_TIMEOUT = float(os.environ.get("PIN_TIMEOUT", "20"))
_SEARCH_COUNT = int(os.environ.get("PIN_SEARCH_COUNT", "8"))
_CACHE_TTL = int(os.environ.get("PIN_CACHE_TTL", "900"))     # 15 min
_FAIL_TTL = 60                                                # fail: 1 min

# Sabse badi → sabse chhoti. `orig` = original upload quality.
PIN_SIZES = ["orig", "736x", "600x315", "564x", "474x", "236x", "170x", "136x136", "60x60"]

_cache = TTLCache(maxsize=int(os.environ.get("PIN_CACHE_SIZE", "512")),
                  default_ttl=_CACHE_TTL)

# Pinterest ki API bina session-cookie ke 403 deti hai. Ek hi shared session
# rakhte hain aur zaroorat par refresh karte hain.
_sess_lock = threading.Lock()
_session: Dict[str, Any] = {"cookies": {}, "ts": 0.0, "ok": False}
_SESSION_TTL = 1200.0   # 20 min baad cookies refresh


def cache_snapshot() -> dict:
    """Admin /sys card ke liye cache stats."""
    return _cache.snapshot()


# ============================================================ session warm-up
def _warm_session(force: bool = False) -> Dict[str, str]:
    """pinterest.com hit karke zaroori cookies nikalo.

    Returns cookie dict (khaali ho sakta hai — us case me bhi API kabhi-kabhi chalti hai).
    Fail-safe: exception kabhi bahar nahi jata.
    """
    import time as _t
    with _sess_lock:
        if not force and _session["ok"] and (_t.time() - _session["ts"]) < _SESSION_TTL:
            return dict(_session["cookies"])
        cookies: Dict[str, str] = {}
        try:
            r = http_get("https://www.pinterest.com/",
                         headers={"User-Agent": _BROWSER_UA,
                                  "Accept": "text/html,application/xhtml+xml"},
                         timeout=_TIMEOUT, retries=1)
            # requests ke CookieJar se naam→value nikaalo
            try:
                for c in r.cookies:
                    cookies[c.name] = c.value or ""
            except Exception:  # noqa: BLE001
                pass
            # session pool ki cookies bhi (redirects me set ho sakti hain)
            try:
                from modules.core.net import session as _net_session
                for c in _net_session().cookies:
                    if  in (c.domain or ""):
                        cookies.setdefault(c.name, c.value or "")
            except Exception:  # noqa: BLE001
                pass
            _session.update(cookies=cookies, ts=_t.time(), ok=bool(cookies))
        except Exception as e:  # noqa: BLE001
            log.debug("warm_session fail: %s", str(e)[:80])
            _session.update(ts=_t.time(), ok=False)
        return dict(cookies)


def _api_headers(handler: str, referer: str) -> Dict[str, str]:
    return {
        "User-Agent": _BROWSER_UA,
        "Accept": "application/json, text/javascript, */*, q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "X-APP-VERSION": _APP_VERSION,
        "X-Pinterest-PWS-Handler": handler,
        "Referer": referer,
    }


def _resource_get(resource: str, source_url: str, options: dict,
                  handler: str) -> Optional[dict]:
    """Pinterest internal resource API call → resource_response dict (ya None)."""
    cookies = _warm_session()
    payload = json.dumps({"options": options, "context": {}}, separators=(",", ":"))
    url = f"https://www.pinterest.com/resource/{resource}/get/"
    hdr = _api_headers(handler, "https://www.pinterest.com" + source_url.split("?")[0])
    try:
        j = http_get_json(url, params={"source_url": source_url, "data": payload},
                          headers={**hdr, **({"Cookie": _cookie_str(cookies)} if cookies else {})},
                          timeout=_TIMEOUT, retries=1)
    except NetError as e:
        # 403 = cookies stale → ek baar force-refresh karke retry
        if e.status in (401, 403):
            cookies = _warm_session(force=True)
            try:
                j = http_get_json(url, params={"source_url": source_url, "data": payload},
                                  headers={**hdr, **({"Cookie": _cookie_str(cookies)} if cookies else {})},
                                  timeout=_TIMEOUT, retries=0)
            except Exception:  # noqa: BLE001
                return None
        else:
            return None
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(j, dict):
        return None
    rr = j.get("resource_response")
    return rr if isinstance(rr, dict) else None


def _cookie_str(cookies: Dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookies.items() if v)


# ============================================================ pin id parsing
_PIN_URL_RE = re.compile(
    r"pinterest\.[a-z.]{2,10}/(?:[a-z]{2}/)?pin/(\d{6,25})", re.I)
_SHORT_RE = re.compile(r"pin\.it/([A-Za-z0-9]+)", re.I)


def extract_pin_id(target: str) -> Optional[str]:
    """Kisi bhi Pinterest link/number se pin ID nikalo.

    Handles: pinterest.com/pin/123/, pinterest.in/pin/123/, /XXXX (short link
    resolve karke), ya seedha 9+ digit number.
    """
    t = (target or "").strip()
    if not t:
        return None
    m = _PIN_URL_RE.search(t)
    if m:
        return m.group(1)
    if re.fullmatch(r"\d{9,25}", t):
        return t
    m = _SHORT_RE.search(t)
    if m:
        #  short link → redirect follow karke asli /pin/<id>/ nikalo
        try:
            r = http_get("https:/" + m.group(1),
                         headers={"User-Agent": _BROWSER_UA},
                         timeout=_TIMEOUT, retries=1)
            mm = _PIN_URL_RE.search(r.url or "") or _PIN_URL_RE.search(r.text[:4000])
            if mm:
                return mm.group(1)
        except Exception:  # noqa: BLE001
            pass
    # last resort: koi bhi lamba number jo URL me ho
    m2 = re.search(r"/(\d{9,25})(?:/|\?|$)", t)
    return m2.group(1) if m2 else None


# ============================================================ normalisation
def _best_image(images: dict) -> Dict[str, Any]:
    """images dict se sabse badi size wali URL chuno.

    Returns {"url","size","width","height"} — url khaali ho sakta hai.
    """
    if not isinstance(images, dict):
        return {"url": "", "size": "", "width": 0, "height": 0}
    for sz in PIN_SIZES:
        ent = images.get(sz)
        if isinstance(ent, dict) and ent.get("url"):
            return {"url": ent["url"], "size": sz,
                    "width": int(ent.get("width") or 0),
                    "height": int(ent.get("height") or 0)}
    # koi known size nahi — pehla available
    for sz, ent in images.items():
        if isinstance(ent, dict) and ent.get("url"):
            return {"url": ent["url"], "size": sz,
                    "width": int(ent.get("width") or 0),
                    "height": int(ent.get("height") or 0)}
    return {"url": "", "size": "", "width": 0, "height": 0}


def _best_video(videos: Any) -> Dict[str, Any]:
    """videos dict se best MP4 stream chuno (HLS se pehle — MP4 Telegram me chalta hai)."""
    if not isinstance(videos, dict):
        return {"url": "", "kind": ""}
    vl = videos.get("video_list") or {}
    if not isinstance(vl, dict):
        return {"url": "", "kind": ""}
    # MP4 variants (quality order), phir HLS
    mp4_keys = [k for k in vl if isinstance(vl.get(k), dict) and "MP4" in k.upper()]
    hls_keys = [k for k in vl if isinstance(vl.get(k), dict) and "HLS" in k.upper()]

    def _res_key(k: str) -> int:
        m = re.search(r"(\d{3,4})P?", k.upper())
        return int(m.group(1)) if m else 0

    for group, kind in ((sorted(mp4_keys, key=_res_key, reverse=True), "mp4"),
                        (sorted(hls_keys, key=_res_key, reverse=True), "hls")):
        for k in group:
            u = (vl.get(k) or {}).get("url")
            if u:
                if kind == "hls" and not u.startswith("http"):
                    continue
                return {"url": u, "kind": kind, "label": k}
    return {"url": "", "kind": ""}


def _s(v: Any, limit: int = 0) -> str:
    """Kisi bhi value ko safely str me badlo.

    Pinterest kabhi-kabhi text fields ko dict/list bhejta hai (jaise rich-text
    `title` = {"text": "..."}), aur kabhi None. `.strip()` seedha call karne par
    AttributeError aata tha — ye helper usse bachata hai.
    """
    if v is None:
        return ""
    if isinstance(v, str):
        s = v
    elif isinstance(v, dict):
        # rich-text format: {"text": "..."} ya {"story": "..."}
        s = ""
        for k in ("text", "story", "title", "value", "name"):
            if isinstance(v.get(k), str):
                s = v[k]
                break
        if not s:
            s = " ".join(_s(x) for x in v.values() if isinstance(x, str))
    elif isinstance(v, (int, float)):
        s = str(v)
    elif isinstance(v, (list, tuple)):
        s = " ".join(_s(x) for x in v if x)
    else:
        s = str(v)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit] if limit else s


def _pinner_of(d: dict) -> Dict[str, Any]:
    p = d.get("pinner") or {}
    if not isinstance(p, dict):
        p = {}
    return {
        "name": _s(p.get("full_name")) or _s(p.get("username")),
        "username": _s(p.get("username")),
        "followers": p.get("follower_count"),
    }


def _norm_pin(d: dict) -> Dict[str, Any]:
    """Pinterest ke raw pin object ko ek saaf dict me badlo."""
    if not isinstance(d, dict):
        return {}
    img = _best_image(d.get("images") if isinstance(d.get("images"), dict) else {})
    vid = _best_video(d.get("videos"))
    title = _s(d.get("grid_title")) or _s(d.get("title"))
    desc = (_s(d.get("description")) or _s(d.get("seo_description"))
            or _s(d.get("closeup_unified_description")) or _s(d.get("alt_text")))
    pin = _pinner_of(d)
    out = {
        "id": str(d.get("id") or d.get("node_id") or ""),
        "title": title,
        "description": desc,
        "image_url": img["url"],
        "image_size": img["size"],
        "width": img["width"],
        "height": img["height"],
        "video_url": vid["url"],
        "video_kind": vid["kind"],
        "video_label": vid.get("label", ""),
        "is_video": bool(vid["url"]) or d.get("video_status") == "available",
        "link": _s(d.get("link")),
        "domain": _s(d.get("domain")),
        "repins": d.get("repin_count"),
        "comments": d.get("comment_count"),
        "pinner_name": pin["name"],
        "pinner_username": pin["username"],
        "pinner_followers": pin["followers"],
        "all_sizes": {k: (v or {}).get("url")
                      for k, v in (d.get("images") or {}).items()
                      if isinstance(v, dict) and v.get("url")},
    }
    return out


# ============================================================ pin detail
_HTML_ORIG_RE = re.compile(
    r"https://i\.\.com/(?:originals|\d+x)/"
    r"[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{32}\.[a-z]{3,4}", re.I)


def _pin_detail_html(pin_id: str) -> Optional[Dict[str, Any]]:
    """Fallback: pin ka HTML page fetch karke image URLs nikalo."""
    try:
        r = http_get(f"https://www.pinterest.com/pin/{pin_id}/",
                     headers={"User-Agent": _BROWSER_UA,
                              "Accept": "text/html,application/xhtml+xml"},
                     timeout=_TIMEOUT, retries=1)
    except Exception:  # noqa: BLE001
        return None
    if r.status_code == 404:
        return {"notfound": True}
    if r.status_code != 200:
        return None
    urls = sorted(set(_HTML_ORIG_RE.findall(r.text)), key=lambda u: 0 if "/originals/" in u else 1)
    if not urls:
        return None
    # title meta se
    title = ""
    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', r.text)
    if m:
        title = m.group(1).strip()
    return {"id": pin_id, "title": title, "description": "",
            "image_url": urls[0], "image_size": "orig" if "/originals/" in urls[0] else "",
            "width": 0, "height": 0, "video_url": "", "video_kind": "", "video_label": "",
            "is_video": False, "link": "", "domain": "", "repins": None, "comments": None,
            "pinner_name": "", "pinner_username": "", "pinner_followers": None,
            "all_sizes": {}, "candidates": urls[:6], "source": "html"}


@_tracked("pinterest.pin_detail")
def pinterest_pin_detail(pin_id: str, use_cache: bool = True) -> Dict[str, Any]:
    """Ek pin ka poora public detail nikalo.

    Returns {"ok":bool, "pin":{...}} ya {"ok":False,"error":...}
    Layer 1: PinResource JSON API (full metadata)
    Layer 2: HTML page scrape (image URLs)
    """
    pid = re.sub(r"\D", "", str(pin_id or ""))
    if len(pid) < 6:
        return {"ok": False, "error": "Ye Pinterest PIN link/ID nahi lagta."}

    def _work():
        rr = _resource_get("PinResource", f"/pin/{pid}/",
                           {"id": pid, "field_set_key": "detailed"},
                           "www/pin/[id].js")
        data = (rr or {}).get("data")
        if isinstance(data, dict) and (data.get("images") or data.get("videos")):
            pin = _norm_pin(data)
            pin["source"] = "api"
            if pin["image_url"] or pin["video_url"]:
                return {"ok": True, "pin": pin}
        html = _pin_detail_html(pid)
        if html and html.get("notfound"):
            return {"ok": False, "notfound": True,
                    "error": ("Ye pin nahi mila — ya to <b>delete</b> ho gaya hai, "
                              "<b>private</b> hai, ya link galat hai.\n"
                              "📌 Koi doosra pin link bhejo.")}
        if html and html.get("image_url"):
            return {"ok": True, "pin": html}
        return {"ok": False,
                "error": ("Pin mila par uska image/video data nahi nikal paaya.\n"
                          "⚠️ Kabhi-kabhi Pinterest datacenter IPs ko block kar deta hai — "
                          "2-3 minute baad dobara try karo.")}

    if not use_cache:
        return _work()
    val, _hit = cached_call(_cache, f"pin:{pid}", _work, ttl=_CACHE_TTL,
                            fail_ttl=_FAIL_TTL,
                            is_failure=lambda v: not v.get("ok"))
    return val


# ============================================================ pin link → media
@_tracked("pinterest.pin_link")
def pinterest_from_pin_link(target: str) -> Dict[str, Any]:
    """Pinterest PIN link (ya  short link, ya seedha ID) → downloadable media.

    Returns:
      {"ok":True,"bytes":..,"ext":..,"kind":"image"|"video","pin":{...},"note":..}
      {"ok":False,"error":..}
    """
    t = (target or "").strip()
    if not t:
        return {"ok": False, "error": _PIN_HELP}

    pid = extract_pin_id(t)
    if not pid:
        return {"ok": False, "error": _PIN_HELP}

    res = pinterest_pin_detail(pid)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error", "Pin ka data nahi mila.")}
    pin = res["pin"]

    # video pin? → video bhejo (Telegram me MP4 chalta hai)
    if pin.get("is_video") and pin.get("video_url") and pin.get("video_kind") == "mp4":
        try:
            data = http_bytes(pin["video_url"], headers={"User-Agent": _BROWSER_UA},
                              timeout=60, max_bytes=80 * 1024 * 1024, retries=1)
            return {"ok": True, "bytes": data, "ext": ".mp4", "kind": "video",
                    "pin": pin, "note": "Pinterest video pin (MP4)"}
        except Exception as e:  # noqa: BLE001
            log.debug("video dl fail, image par wapas: %s", str(e)[:80])

    urls: List[str] = []
    if pin.get("image_url"):
        urls.append(pin["image_url"])
    urls += [u for u in (pin.get("candidates") or []) if u not in urls]
    urls += [u for u in (pin.get("all_sizes") or {}).values() if u not in urls]
    if not urls:
        if pin.get("is_video"):
            return {"ok": False,
                    "error": ("Ye ek <b>video pin</b> hai par uska direct MP4 stream "
                              "abhi nahi mila (Pinterest ne HLS-only bheja).\n"
                              "📌 Pin ka link browser me khol ke dekh sakte ho.")}
        return {"ok": False, "error": "Pin par koi downloadable image nahi mili."}

    # download — pehli URL fail ho to agli try karo
    last_err = ""
    for u in urls[:5]:
        safe, why = is_safe_url(u)
        if not safe:
            last_err = why or "unsafe url"
            continue
        try:
            data = http_bytes(u, headers={"User-Agent": _BROWSER_UA},
                              timeout=40, max_bytes=40 * 1024 * 1024, retries=1)
        except NetError as e:
            last_err = e.message
            continue
        except Exception as e:  # noqa: BLE001
            last_err = str(e)[:80]
            continue
        if len(data) < 1500:
            last_err = "file bahut chhoti thi"
            continue
        ext = _ext_from_url(u, data)
        return {"ok": True, "bytes": data, "ext": ext, "kind": "image", "pin": pin,
                "note": f"Pinterest original quality ({pin.get('image_size') or 'best'})"}
    return {"ok": False,
            "error": f"Image download fail ho gayi ({last_err[:60]}). Dobara try karo."}


def _ext_from_url(url: str, data: bytes) -> str:
    """File ke asli bytes se extension pata karo (content-type se zyada bharosemand)."""
    head = data[:12]
    if head.startswith(b"\x89PNG"):
        return ".png"
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if head.startswith(b"GIF8"):
        return ".gif"
    low = url.lower().split("?")[0]
    for e in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        if low.endswith(e):
            return ".jpeg" if e == ".jpeg" else e
    return ".jpg"


# ============================================================ search
def _search_api(keyword: str) -> List[Dict[str, Any]]:
    """Layer 1: official BaseSearchResource API."""
    from urllib.parse import quote
    src = f"/search/pins/?q={quote(keyword)}"
    rr = _resource_get("BaseSearchResource", src,
                       {"query": keyword, "scope": "pins",
                        "page_size": max(_SEARCH_COUNT * 3, 25),
                        "field_filter_key": "", "filters": None},
                       "www/search/[scope].js")
    data = (rr or {}).get("data")
    items: List[Any] = []
    if isinstance(data, dict):
        items = data.get("results") or []
    elif isinstance(data, list):
        items = data
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        p = _norm_pin(it)
        if p.get("image_url") or p.get("video_url"):
            p["source"] = "api"
            out.append(p)
        if len(out) >= _SEARCH_COUNT * 2:
            break
    return out


_BING_MURL_RE = re.compile(r'murl&quot;:&quot;(https?://[^&]+?)&quot;')


def _search_bing(keyword: str) -> List[Dict[str, Any]]:
    """Layer 3 fallback: Bing image search (Pinterest images ko priority)."""
    out: List[Dict[str, Any]] = []
    seen = set()
    for q in (f"{keyword} site:pinterest.com", f"{keyword} pinterest", keyword):
        try:
            r = http_get("https://www.bing.com/images/search",
                         params={"q": q, "form": "HDRSC2"},
                         headers={"User-Agent": _BROWSER_UA},
                         timeout=_TIMEOUT, retries=0)
        except Exception:  # noqa: BLE001
            continue
        for u in _BING_MURL_RE.findall(r.text):
            u = u.strip()
            m = _HTML_ORIG_RE.match(u)
            if m:
                u = m.group(0)
            if u in seen or not u.startswith("http"):
                continue
            seen.add(u)
            out.append({"id": "", "title": "", "description": "",
                        "image_url": u, "image_size": "", "width": 0, "height": 0,
                        "video_url": "", "video_kind": "", "video_label": "",
                        "is_video": False, "link": "", "domain": "",
                        "repins": None, "comments": None, "pinner_name": "",
                        "pinner_username": "", "pinner_followers": None,
                        "all_sizes": {}, "source": "bing"})
        if len(out) >= _SEARCH_COUNT:
            break
    return out


@_tracked("pinterest.search")
def pinterest_search(keyword: str, use_cache: bool = True) -> Dict[str, Any]:
    """Keyword se REAL Pinterest search.

    Returns {"ok":True,"results":[pin,...],"is_pinterest":[bool,...],"source":..}
    """
    kw = re.sub(r"\s+", " ", (keyword or "").strip())
    if len(kw) < 2:
        return {"ok": False,
                "error": ("Koi keyword bhejo — jaise <code>cat wallpaper</code>, "
                          "<code>logo design</code>, <code>girl dp</code>")}
    if len(kw) > 90:
        kw = kw[:90]

    def _work():
        results = _search_api(kw)
        source = 
        if len(results) < 3:
            # API ne kam diye → Bing se bharo (Pinterest images pehle)
            extra = _search_bing(kw)
            have = {r["image_url"] for r in results}
            for e in extra:
                if e["image_url"] not in have:
                    results.append(e)
                    have.add(e["image_url"])
            if source ==  and any(r["source"] == "bing" for r in results):
                source = "mixed" if any(r["source"] == "api" for r in results) else "web"
        if not results:
            return {"ok": False,
                    "error": (f"'{kw}' ke liye koi public image nahi mili.\n"
                              "📌 Doosra keyword try karo (English me zyada accha chalta hai), "
                              "ya seedha kisi pin ka link bhejo.")}
        # Pinterest (api) wale upar, phir , phir baaki
        def _rank(r: Dict[str, Any]) -> int:
            if r.get("source") == "api":
                return 0
            if ".com" in (r.get("image_url") or ""):
                return 1
            return 2
        results.sort(key=_rank)
        top = results[:_SEARCH_COUNT]
        return {"ok": True, "results": top, "keyword": kw,
                "is_pinterest": [r.get("source") == "api" or ".com" in (r.get("image_url") or "")
                                 for r in top],
                "source": source, "total_found": len(results)}

    if not use_cache:
        return _work()
    val, _hit = cached_call(_cache, f"search:{kw.lower()}", _work, ttl=_CACHE_TTL,
                            fail_ttl=_FAIL_TTL, is_failure=lambda v: not v.get("ok"))
    return val


# ============================================================ media download
@_tracked("pinterest.download")
def download_media(url: str, max_mb: int = 80) -> Dict[str, Any]:
    """Search result ki URL se media download karo (image ya video)."""
    u = (url or "").strip()
    if not u.startswith("http"):
        return {"ok": False, "error": "Galat URL."}
    safe, why = is_safe_url(u)
    if not safe:
        return {"ok": False, "error": f"Ye URL block hai — {why or 'unsafe'}"}
    try:
        data = http_bytes(u, headers={"User-Agent": _BROWSER_UA}, timeout=45,
                          max_bytes=max_mb * 1024 * 1024, retries=1)
    except NetError as e:
        return {"ok": False, "error": f"Download fail: {e.message[:70]}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"Download fail: {str(e)[:70]}"}
    if len(data) < 1500:
        return {"ok": False, "error": "File bahut chhoti/corrupt aayi. Dobara try karo."}
    ext = _ext_from_url(u, data)
    kind = "video" if ext == ".mp4" else "image"
    return {"ok": True, "bytes": data, "ext": ext, "kind": kind,
            "is_img": kind == "image", "size_kb": len(data) // 1024}


_PIN_HELP = (
    "Ye Pinterest PIN link nahi lagta.\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "📌 <b>Link kaise laayein:</b>\n"
    "1. Pinterest app kholo → koi pin dabao\n"
    "2. Upar-right <b>⋯</b> (3 dots) → <b>Copy link</b>\n"
    "3. Yahan paste kar do\n\n"
    "📌 <b>Jaise:</b> <code>https:/abc123</code>\n"
    "ya <code>https://in.pinterest.com/pin/576742296077249680/</code>\n\n"
    "💡 Sirf link nahi, <b>keyword</b> bhi bhej sakte ho — jaise "
    "<code>cat wallpaper</code> → 8 images dikhegi."
)
