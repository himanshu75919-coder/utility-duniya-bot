# -*- coding: utf-8 -*-
"""
v84 — ⚡ DOWNLOAD CACHE KEY (instant repeat ka dimaag)
======================================================
Telegram ka file_id cache tabhi sahi kaam karta hai jab "same video" ki
pehchaan sahi ho. Pehle key = poora URL (lowercase) tha:
  • ?igsh= / ?si= / ?fbclid= jaise tracking params se alag key ban jaati thi,
    to same reel dobara download hoti thi (cache miss).
  • Poora URL lowercase hota tha, to Instagram / YouTube ki case-sensitive ID
    ka farq mit jaata tha (chhota lekin real wrong-video risk).

Ab:
  • Instagram  → shortcode (+ img_index agar diya ho, carousel slides ke liye)
  • YouTube    → video ID (watch / youtu.be / shorts / embed / live)
  • TikTok     → video ID
  • Facebook   → video ID (watch / reel / page videos — sab ek hi namespace)
  • fb.watch   → short code (alag namespace)
  • Baaki links → sirf universal tracking params hatakar (case-preserved)
Har key ke saath tag (jaise quality "q720") bhi judta hai.

Safety rule: ID hamesha case-sensitive hai aur har namespace alag hai, isliye
do alag videos ko same key nahi milti. Galat/ajeeb input par bhi key sirf
ek cache-miss deti hai (galat video nahi).
"""
import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

__all__ = ["dl_cache_key", "canonical_url_id", "strip_tracking_params", "first_url"]

_URL_RX = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

# Sirf wo params jo content ko kabhi identify nahi karte (universal tracking).
# Yahan "source", "ref", "si", "feature" jaise params jaan-boojh kar NAHI hain:
# kuch sites inse content badalti hain, to unhe hatane se galat video match ho sakta.
_TRACK_PREFIX = ("utm_",)
_TRACK_EXACT = frozenset({"fbclid", "gclid", "dclid", "msclkid", "igshid", "igsh"})

# (namespace, regex). Group(1) = content ID. Pehla match jeetega.
_PATTERNS = (
    ("ig", re.compile(r"instagram\.com/(?:[^/?#]+/)?(?:p|reels?|tv)/([A-Za-z0-9_-]+)", re.IGNORECASE)),
    ("yt", re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?(?:[^#]*&)?v=|shorts/|embed/|live/))"
                      r"([A-Za-z0-9_-]{6,20})", re.IGNORECASE)),
    ("tt", re.compile(r"tiktok\.com/@[^/?#]+/video/(\d+)", re.IGNORECASE)),
    ("fb", re.compile(r"facebook\.com/(?:watch/?\?(?:[^#]*&)?v=|reel/|[^/?#]+/videos/(?:[^/?#]+/)?)(\d+)",
                      re.IGNORECASE)),
    ("fbw", re.compile(r"fb\.watch/([A-Za-z0-9_-]+)", re.IGNORECASE)),
)


def first_url(text: str) -> str:
    """Text me pehla http(s) link. Na mile to trimmed text hi."""
    s = (text or "").strip()
    m = _URL_RX.search(s)
    if not m:
        return s
    return m.group(0).rstrip(".,;:!)")


def _query_map(url: str) -> dict:
    try:
        return {k.lower(): v for k, v in parse_qsl(urlsplit(url).query, keep_blank_values=True)}
    except Exception:  # noqa: BLE001
        return {}


def canonical_url_id(text: str):
    """Known platform ka content-ID → 'ns:id'. Unknown link par None."""
    url = first_url(text)
    for ns, rx in _PATTERNS:
        m = rx.search(url)
        if not m:
            continue
        cid = m.group(1)
        if ns == "ig":
            idx = _query_map(url).get("img_index", "")
            if idx.isdigit():
                cid = f"{cid}:{int(idx)}"
        return f"{ns}:{cid}"
    return None


def strip_tracking_params(url: str) -> str:
    """Universal tracking params hatao; baaki query aur path (case) waise hi rehne do."""
    try:
        p = urlsplit(url)
        if not p.query:
            return url
        kept = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                if not (k.lower().startswith(_TRACK_PREFIX) or k.lower() in _TRACK_EXACT)]
        return urlunsplit((p.scheme, p.netloc.lower(), p.path, urlencode(kept), ""))
    except Exception:  # noqa: BLE001
        return url


def dl_cache_key(text: str, tag: str = "") -> str:
    """Download file_id cache ki stable key. Same video = same key, alag tracking = bhi same."""
    ident = canonical_url_id(text)
    if ident is None:
        ident = "u:" + strip_tracking_params(first_url(text))
    # Truncation nahi: do alag lambe links ek hi key na banayein.
    raw = ident + "|" + str(tag or "")
    return "dlfid:" + hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:24]
