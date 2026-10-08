# -*- coding: utf-8 -*-
"""
v85 — 🔗 LINK SANITIZER (gande links ka permanent ilaaj)
========================================================
User aksar aise link bhejta hai (copy-paste me gandagi aa jaati hai):

  • https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3&amp;amp;stkn=MXdt...
    (HTML-escaped `&amp;` — 2-3 baar escape hua)
  • [link text](https://www.1024tera.com/wap/share/filelist?surl=XXX&fbclid=...)
    (markdown wrapper)
  • aage-peechhe space / nayi line / \"link: ...\" jaisa text

Pehle `raw_text` seedha engines ko jaata tha. Zyada tar engine `?` ke baad ka
hissa kaat dete the, isliye kaam chal jaata tha — par kuch case me (YouTube
query, terabox wap links, markdown wrapper, button URLs) gandagi andar tak
pahunch jaati thi aur tool FAIL ho jaata tha.

Ab har downloader/cloud tool ka input yahan se dhul kar jaata hai:
  clean_link()  → pehla saaf http(s) URL (ya khaali string)
  insta_parts() → (canonical_post_url, img_index|None)
  tera_surl()   → Terabox surl (1024tera/wap/markdown sab chalega)
  safe_button_url() → InlineKeyboardButton me daalne layak URL ya None

100% offline, koi network call nahi, kabhi exception nahi (junk par khaali).
"""
from __future__ import annotations

import re
from html import unescape
from urllib.parse import parse_qsl, urlsplit, urlunsplit

__all__ = [
    "clean_link", "first_url", "insta_parts", "insta_clean", "tera_surl",
    "strip_tracking", "safe_button_url", "TRACK_PARAMS",
]

_URL_RX = re.compile(r"https?://[^\s<>\"'`\]]+", re.IGNORECASE)

# Download ke liye bekaar params — engines ko saaf URL milta hai.
# (dlkey.py ke TRACK list se alag: yahan `stkn`/`img_index` bhi hatate hain
# kyunki download ke liye post ka shortcode hi kaafi hai.)
TRACK_PARAMS = frozenset({
    "fbclid", "gclid", "dclid", "msclkid", "igshid", "igsh", "stkn",
    "img_index", "si", "feature", "pp", "utm_source", "utm_medium",
    "utm_campaign", "utm_term", "utm_content",
})
_TRACK_PREFIX = ("utm_",)


def _unescape_deep(s: str, rounds: int = 4) -> str:
    """`&amp;amp;amp;` → `&` (jitni baar escape hua ho)."""
    try:
        out = s
        for _ in range(rounds):
            nxt = unescape(out)
            if nxt == out:
                break
            out = nxt
        # bachaa-khuchaa literal `&amp;` (adhura escape) bhi saaf karo
        out = re.sub(r"&amp;+;?", "&", out)
        return out
    except Exception:  # noqa: BLE001
        return s


def first_url(text) -> str:
    """Text me se pehla http(s) link. Na mile to ''."""
    try:
        if text is None:
            return ""
        if isinstance(text, bytes):
            try:
                text = text.decode("utf-8", "ignore")
            except Exception:  # noqa: BLE001
                return ""
        s = _unescape_deep(str(text)).strip()
        if not s:
            return ""
        m = _URL_RX.search(s)
        if not m:
            return ""
        # markdown [text](url) ke andar ka URL ho to trailing ')' kaato
        return m.group(0).rstrip(".,;:!)]}>\"'")
    except Exception:  # noqa: BLE001
        return ""


def clean_link(text, default_scheme: str = "https") -> str:
    """Downloader/cloud tools ke liye saaf URL. Na mile to ''."""
    try:
        u = first_url(text)
        if not u:
            # bina scheme ka link? (\"instagram.com/p/xxx\") — jod do
            try:
                s = _unescape_deep(str(text or "")).strip().split()[0]
            except Exception:  # noqa: BLE001
                return ""
            if re.match(r"(?i)^(?:www\.)?(instagram|instagr|youtu|youtube|facebook|fb|tiktok|terabox|1024tera|mirrobox)[\w.-]*\.[a-z]{2,}/", s):
                u = default_scheme + "://" + s.lstrip("/")
            else:
                return ""
        # control chars / spaces andar ho to kaato
        u = re.sub(r"[\x00-\x20\x7f]+", "", u)
        if len(u) > 2000:
            u = u[:2000]
        return u
    except Exception:  # noqa: BLE001
        return ""


def strip_tracking(url: str) -> str:
    """Tracking/query params hatao — download ke liye saaf URL."""
    try:
        u = clean_link(url)
        if not u or "?" not in u:
            return u.split("#")[0].rstrip("?&")
        p = urlsplit(u)
        kept = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                if k.lower() not in TRACK_PARAMS
                and not k.lower().startswith(_TRACK_PREFIX)]
        from urllib.parse import urlencode
        return urlunsplit((p.scheme, p.netloc.lower(), p.path, urlencode(kept), ""))
    except Exception:  # noqa: BLE001
        try:
            return str(url or "").split("?")[0].split("#")[0]
        except Exception:  # noqa: BLE001
            return ""


_IG_RX = re.compile(
    r"instagr(?:am\.com|am?\.am)/(?:[^/?#]+/)?(?:p|reels?|tv)/([A-Za-z0-9_-]+)",
    re.IGNORECASE)


def insta_parts(text) -> tuple:
    """Instagram link → (canonical_url, img_index|None). Na mile to ('', None)."""
    try:
        u = clean_link(text)
        if not u:
            return "", None
        m = _IG_RX.search(u)
        if not m:
            return strip_tracking(u), None
        code = m.group(1)
        idx = None
        try:
            q = dict(parse_qsl(urlsplit(u).query, keep_blank_values=True))
            raw_idx = q.get("img_index", "")
            if str(raw_idx).isdigit() and int(raw_idx) >= 1:
                idx = int(raw_idx)
        except Exception:  # noqa: BLE001
            idx = None
        return f"https://www.instagram.com/p/{code}/", idx
    except Exception:  # noqa: BLE001
        return "", None


def insta_clean(text) -> str:
    """Instagram download ke liye canonical post URL (query-free)."""
    try:
        url, _ = insta_parts(text)
        return url
    except Exception:  # noqa: BLE001
        return ""


def tera_surl(text) -> str:
    """Terabox link se surl — wap/markdown/&amp;/shorturl sab chalega."""
    try:
        u = clean_link(text)
        if not u:
            return ""
        m = re.search(r"/s/1?([A-Za-z0-9_-]+)", u)
        if m:
            code = m.group(1)
            return code if code.startswith("1") else code
        m = re.search(r"[?&](?:surl|shorturl)=([A-Za-z0-9_-]+)", u)
        if m:
            return m.group(1)
        return ""
    except Exception:  # noqa: BLE001
        return ""


def safe_button_url(url, fallback: str = "") -> str:
    """InlineKeyboardButton(url=...) kabhi crash na kare — valid http URL ya fallback/None.

    Telegram button me galat URL = handler exception = user ko \"ghatna\".
    Isliye dlink/\"original page\" buttons hamesha yahan se guzarte hain.
    """
    try:
        u = clean_link(url)
        if u.startswith("http://") or u.startswith("https://"):
            if len(u) <= 1000 and " " not in u:
                return u
    except Exception:  # noqa: BLE001
        pass
    try:
        f = (fallback or "").strip()
        if f.startswith("http://") or f.startswith("https://"):
            return f[:1000]
    except Exception:  # noqa: BLE001
        pass
    return None
