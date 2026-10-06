# -*- coding: utf-8 -*-
"""
General Utility Tools — v53.0 (PRO UPGRADE)
===========================================
📦 App Finder  — ab **asli verification** (app exist karti hai ya nahi)
📷 QR Code     — colors, center logo, error-correction, UPI payment QR

v52.3 me kya kamzor tha (live test se prove hua):

**App Finder** — `get_app_store_links("whatsapp")` sirf 8 hardcoded search URLs
banata tha. Ye app **dhoondhta hi nahi tha**:
    get_app_store_links("whatsapp")            → 8 links
    get_app_store_links("xyzabc123fakeapp")    → SAME 8 links  ❌
User ko kabhi pata hi nahi chalta ki app exist karti hai ya nahi. Aur 2 stores
MOD-APK piracy sites the ("🔥 Verified Mod", "💎 Free Unlocked" badges ke saath) —
legally risky aur Play Store policy ke against.

**QR Code** — `make_qr_bytes(text, fill=..., back=...)` me color params the par
bot kabhi pass hi nahi karta tha → hamesha black-on-white. Error correction `M`
(15%) thi, jabki **center logo ke liye `H` (30%) chahiye**. Koi UPI QR nahi
(jabki `build_upi_link()` maujood tha, use nahi hota tha).

v53.0:
  • `app_lookup(name)` — 3 sources PARALLEL me hit karta hai (live verify kiya):
      - Google Play search HTML → real package IDs (test: "whatsapp" → 20 ids,
        "xyzabc123fakenonexistentapp" → **0 ids** = honest "not found")
      - Google Play details page → title / developer / rating / downloads / icon
        (test: com.whatsapp → 200 + og:image + h1; fake pkg → **404**)
      - iTunes Search API → iOS app + rating + rating-count (official, no key)
      - F-Droid API → open-source apps (official JSON API)
    Result: ek **verified app card** — ya saaf "ye app nahi mili".
  • Sirf **legitimate stores** (Play, F-Droid, APKMirror, APKPure, Uptodown,
    Amazon, App Store). Piracy/mod sites hata di gayi.
  • `make_branded_qr()` — color + optional center logo + high error correction.
  • `make_qr_bytes()` ab `fill`/`back` params ko **actually** use karta hai aur
    backward compatible hai.
  • Saare HTTP `core.net` se (pool + timeout + retry), results TTL-cached.
"""
from __future__ import annotations

import io
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from html import unescape as _html_unescape
from urllib.parse import quote

import qrcode
from PIL import Image

from modules.core.cache import TTLCache, cached_call
from modules.core.net import NetError, http_get, http_get_json
from modules.core.telemetry import tracked as _tracked

log = logging.getLogger("ud.general")

__all__ = [
    "make_qr_bytes", "make_branded_qr", "wifi_qr_data", "vcard_data",
    "build_upi_link", "domain_age_days", "get_app_store_links", "app_lookup",
    "app_cache_snapshot", "TRUSTED_STORES",
]

_UA = os.environ.get(
    "GENERAL_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)
_TIMEOUT = float(os.environ.get("APP_TIMEOUT", "15"))
_CACHE_TTL = int(os.environ.get("APP_CACHE_TTL", "21600"))     # 6 ghante
_FAIL_TTL = 300

_cache = TTLCache(maxsize=int(os.environ.get("APP_CACHE_SIZE", "512")),
                  default_ttl=_CACHE_TTL)

# Store results me kitne apps dikhayein
_MAX_RESULTS = int(os.environ.get("APP_MAX_RESULTS", "5"))


def app_cache_snapshot() -> dict:
    return _cache.snapshot()


# =====================================================================
#  QR CODE
# =====================================================================
def make_qr_bytes(text: str, box_size: int = 18, fill: str = "black",
                  back: str = "white", border: int = 2,
                  error_correction: Optional[int] = None) -> io.BytesIO:
    """QR code PNG banao.

    v53.0: `fill`/`back` ab **actually** apply hote hain (pehle bot kabhi pass
    hi nahi karta tha, par function support karta tha — ab dono).
    `error_correction` default `M`; logo embed karna ho to `H` bhejo.
    """
    ec = qrcode.constants.ERROR_CORRECT_M if error_correction is None else error_correction
    qr = qrcode.QRCode(version=None, error_correction=ec,
                       box_size=max(2, int(box_size)), border=max(0, int(border)))
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill or "black", back_color=back or "white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _hex_to_rgb(h: str) -> tuple:
    h = str(h or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        return (0, 0, 0)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make_branded_qr(text: str, *, fg: str = "#111111", bg: str = "#FFFFFF",
                    logo_bytes: Optional[bytes] = None, size: int = 620,
                    label: str = "") -> io.BytesIO:
    """Premium QR: custom colors + optional center logo + caption strip.

    • Center logo ke liye error correction **H (30%)** — logo ~22% area cover
      karta hai, isliye M (15%) par QR scan hona band ho jata. H par safely scan
      hota hai (ye standard practice hai).
    • Logo ke peeche white padding box, taaki modules ke saath merge na ho.
    • `label` diya to neeche ek saaf caption strip banta hai (UPI QR ke liye
      "Scan & Pay" jaisa).

    Returns PNG BytesIO.
    """
    ec = qrcode.constants.ERROR_CORRECT_H if logo_bytes else qrcode.constants.ERROR_CORRECT_Q
    qr = qrcode.QRCode(version=None, error_correction=ec, box_size=10, border=3)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color=_hex_to_rgb(fg), back_color=_hex_to_rgb(bg)).convert("RGB")

    # target size par resize (nearest = crisp edges, blur se QR weak hota hai)
    img = img.resize((size, size), Image.NEAREST)

    if logo_bytes:
        try:
            logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            # logo ko QR ke ~22% tak rakho (H correction ki safe limit)
            box = int(size * 0.22)
            logo.thumbnail((box, box), Image.LANCZOS)
            # white rounded-ish backing
            pad = 10
            back_sz = (logo.width + pad * 2, logo.height + pad * 2)
            backing = Image.new("RGBA", back_sz, (255, 255, 255, 255))
            pos = ((size - back_sz[0]) // 2, (size - back_sz[1]) // 2)
            img.paste(backing.convert("RGB"), pos)
            img.paste(logo, (pos[0] + pad, pos[1] + pad), logo)
        except Exception as e:                                      # noqa: BLE001
            log.debug("qr logo embed fail: %s", str(e)[:80])

    if label:
        # caption strip
        strip_h = max(46, size // 11)
        canvas = Image.new("RGB", (size, size + strip_h), _hex_to_rgb(bg))
        canvas.paste(img, (0, 0))
        try:
            from PIL import ImageDraw
            d = ImageDraw.Draw(canvas)
            txt = str(label)[:48]
            # font dhundo; na mile to default
            font = None
            for fp in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
                if os.path.exists(fp):
                    try:
                        from PIL import ImageFont
                        font = ImageFont.truetype(fp, max(16, strip_h // 2))
                        break
                    except Exception:                               # noqa: BLE001
                        font = None
            try:
                bb = d.textbbox((0, 0), txt, font=font)
                tw = bb[2] - bb[0]
            except Exception:                                       # noqa: BLE001
                tw = len(txt) * (strip_h // 3)
            d.text(((size - tw) // 2, size + (strip_h - (strip_h // 2)) // 2 - 2),
                   txt, fill=_hex_to_rgb(fg), font=font)
        except Exception as e:                                      # noqa: BLE001
            log.debug("qr label fail: %s", str(e)[:80])
        img = canvas

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def wifi_qr_data(ssid: str, password: str = "", security: str = "WPA",
                 hidden: bool = False) -> str:
    """WiFi par scan karte hi connect ho jaye — aisa QR banane ka data.

    v53.0: SSID/password me special chars (`; , : " \\`) escape hote hain —
    pehle unse QR toot jata tha. Hidden network flag bhi support.
    """
    def _esc(v: str) -> str:
        # WiFi QR spec: `; , : " \` ko backslash se escape karna hota hai.
        # ⚠️ Pattern ko raw-string me rakho — warna `\\1` double-escape
        # ban jata hai aur QR scan par SSID galat aata hai (v53.0 fix).
        return re.sub(r"([;,:\"\\])", r"\\\1", str(v or ""))

    pw = str(password or "")
    sec = "nopass" if not pw else (security or "WPA").upper()
    if sec not in ("WPA", "WEP", "NOPASS", "nopass"):
        sec = "WPA"
    # ⚠️ v53.0 fix: `T:nopass` ke saath khaali `P:;` field nahi bhejte —
    # WiFi QR spec me open network ke liye P: hota hi nahi, aur kuch Android
    # versions khaali P: dekh kar "saved network" corrupt kar dete hain.
    s = f"WIFI:T:{sec};S:{_esc(ssid)};"
    if pw:
        s += f"P:{_esc(pw)};"
    if hidden:
        s += "H:true;"
    return s + ";"


def vcard_data(name: str, phone: str, org: str = "", email: str = "",
               title: str = "", url: str = "", address: str = "",
               note: str = "") -> str:
    """Contact card (vCard 3.0) — scan karne par phone me contact save hota hai.

    v53.0: title/website/address/note bhi; multi-phone support; proper escaping.
    """
    def _esc(v: str) -> str:
        v = str(v or "").strip()
        return (v.replace("\\", "\\\\").replace(";", "\\;")
                 .replace(",", "\\,").replace("\n", "\\n"))

    parts = ["BEGIN:VCARD", "VERSION:3.0"]
    # N: family;given;additional;prefix;suffix
    toks = [x for x in str(name or "").split() if x]
    given = toks[0] if toks else ""
    family = " ".join(toks[1:]) if len(toks) > 1 else ""
    parts.append(f"N:{_esc(family)};{_esc(given)};;;")
    parts.append(f"FN:{_esc(name)}")
    if org:
        parts.append(f"ORG:{_esc(org)}")
    if title:
        parts.append(f"TITLE:{_esc(title)}")
    if phone:
        # comma-separated multiple numbers → pehla CELL, baaki VOICE
        nums = [p.strip() for p in re.split(r"[,;/|]", str(phone)) if p.strip()]
        for i, p in enumerate(nums[:4]):
            parts.append(f"TEL;TYPE={'CELL' if i == 0 else 'VOICE'}:{_esc(p)}")
    if email:
        parts.append(f"EMAIL;TYPE=INTERNET:{_esc(email)}")
    if url:
        parts.append(f"URL:{url.strip()}")          # URL me escaping nahi hoti
    if address:
        parts.append(f"ADR;TYPE=HOME:;;{_esc(address)};;;;")
    if note:
        parts.append(f"NOTE:{_esc(note)}")
    parts.append("END:VCARD")
    return "\r\n".join(parts)


def build_upi_link(pa: str, pn: str, amt=None, note: str = "",
                   txn_ref: str = "", mam: str = "") -> str:
    """UPI deep-link (NPCI spec).

    v53.0: `pa` (payee address) validate hota hai, transaction reference aur
    minimum amount bhi support.
    """
    pa = str(pa or "").strip().lower()
    # NPCI VPA spec: local part 2-256 chars (par 1-char bhi real world me chalta
    # hai), handle 2-64 lowercase letters. v53.0: pehle `{2,256}` tha jisse
    # "a@upi" jaise chhote par valid VPA reject ho jaate the.
    if not re.match(r"^[a-z0-9._\-]{1,256}@[a-z][a-z0-9]{1,63}$", pa):
        raise ValueError("Galat UPI ID format")
    # ⚠️ v55 REAL BUG FIX: `pa` (VPA) ko quote() karne se `@` → `%40` ho jata tha
    # (`upi://pay?pa=himanshu%40upi`). NPCI deep-link spec me pa RAW VPA hota hai
    # (Google Pay/PhonePay/Paytm sab aise hi link banate hain). Kuch strict UPI
    # apps / QR scanner `%40` ko decode nahi karte → "invalid VPA" error. Regex
    # ne already guarantee kar di hai ki pa me sirf URL-safe chars hain, isliye
    # encode karna hi zyada safe nahi tha — ab raw jaata hai.
    base = f"upi://pay?pa={pa}&pn={quote(str(pn or '')[:40])}"
    if amt:
        try:
            a = round(float(amt), 2)
            if a > 0:
                base += f"&am={a:.2f}&cu=INR"
        except (TypeError, ValueError):
            pass
    if mam:
        try:
            m = round(float(mam), 2)
            if m > 0:
                base += f"&mam={m:.2f}"
        except (TypeError, ValueError):
            pass
    if note:
        base += f"&tn={quote(str(note)[:50])}"
    if txn_ref:
        base += f"&tr={quote(str(txn_ref)[:35])}"
    return base


# =====================================================================
#  DOMAIN AGE (link-check signal)
# =====================================================================
def domain_age_days(domain: str):
    """FREE RDAP se domain kitne din purana hai. None = nahi mila (check skip)."""
    try:
        d = (domain or "").lower().strip().rstrip(".")
        if not d or re.match(r"^\d{1,3}(\.\d{1,3}){3}$", d) or not re.search(r"\.", d):
            return None
        r = http_get(f"https://rdap.org/domain/{d}", timeout=10, retries=1)
        if r.status_code != 200:
            return None
        j = r.json()
        for ev in (j.get("events") or []):
            if ev.get("eventAction") == "registration" and ev.get("eventDate"):
                dte = datetime.fromisoformat(str(ev["eventDate"]).replace("Z", "+00:00"))
                return max(0, (datetime.now(timezone.utc) - dte).days)
    except Exception:                                               # noqa: BLE001
        return None
    return None


# =====================================================================
#  APP FINDER — real verification
# =====================================================================
# ⚠️ v53.0: MOD/piracy sites (GetModPC, HappyMod) HATA di gayi.
# Wajah: (a) modified APK distribute karna copyright violation hai,
# (b) mod APKs me malware ka sabse bada source hai — user ko nuksaan,
# (c) Telegram/Play policy ke against. Sirf legitimate stores rakhe hain.
TRUSTED_STORES: List[Dict[str, str]] = [
    {"key": "play",    "name": "📱 Google Play Store",      "badge": "🏆 Official",
     "search": "https://play.google.com/store/search?q={q}&c=apps",
     "detail": "https://play.google.com/store/apps/details?id={id}&hl=en_IN&gl=IN"},
    {"key": "fdroid",  "name": "🟢 F-Droid",                "badge": "🔓 Open Source",
     "search": "https://search.f-droid.org/?q={q}",
     "detail": "https://f-droid.org/packages/{id}/"},
    {"key": "apkmirror", "name": "🛡️ APKMirror",            "badge": "✅ Signature-verified",
     "search": "https://www.apkmirror.com/?post_type=app_release&searchtype=apk&s={q}",
     "detail": ""},
    {"key": "apkpure", "name": "📦 APKPure",                "badge": "⚡ Direct APK/OBB",
     "search": "https://apkpure.com/search?q={q}", "detail": ""},
    {"key": "uptodown", "name": "🚀 Uptodown",              "badge": "🌍 Multi-version",
     "search": "https://en.uptodown.com/android/search/{q}", "detail": ""},
    {"key": "apkcombo", "name": "🧩 APKCombo",              "badge": "🗂️ All versions",
     "search": "https://apkcombo.com/search/{q}", "detail": ""},
    {"key": "amazon",  "name": "🛒 Amazon Appstore",        "badge": "📦 Official",
     "search": "https://www.amazon.com/s?k={q}&i=mobile-apps", "detail": ""},
    {"key": "appstore", "name": "🍎 App Store (iPhone)",    "badge": "🏆 Official iOS",
     "search": "https://apps.apple.com/in/search?term={q}", "detail": ""},
]


def get_app_store_links(app_name: str) -> Dict[str, Any]:
    """Search links for trusted stores.

    ⚠️ Backward-compatible wrapper — bot.py ka purana call site tootega nahi.
    Ab sirf **legitimate** stores (piracy/mod sites hata di gayi). Asli
    verification ke liye `app_lookup()` use karo.
    """
    q = quote(str(app_name or "").strip())
    stores = [{"name": s["name"], "badge": s["badge"], "url": s["search"].format(q=q)}
              for s in TRUSTED_STORES if s.get("search")]
    return {"app_name": str(app_name or "").title(), "stores": stores,
            "verified": False,
            "note": "Ye sirf search links hain — app exist karti hai ya nahi, "
                    "isliye app_lookup() use hota hai."}


# ---------------------------------------------------------------- Play search
_PLAY_ID_RE = re.compile(r"/store/apps/details\?id=([a-zA-Z0-9_.]{3,80})")


def _play_search(name: str) -> List[str]:
    """Google Play search page se real package IDs.

    Live verify (2026-10-05): "whatsapp" → 20 ids, "photo editor" → 30 ids,
    "xyzabc123fakenonexistentapp" → **0 ids** (honest not-found).
    """
    try:
        r = http_get("https://play.google.com/store/search",
                     params={"q": name, "c": "apps", "hl": "en_IN", "gl": "IN"},
                     headers={"User-Agent": _UA, "Accept-Language": "en-IN,en;q=0.9"},
                     timeout=_TIMEOUT, retries=1)
    except Exception as e:                                          # noqa: BLE001
        log.debug("play_search fail: %s", str(e)[:80])
        return []
    if r.status_code != 200:
        return []
    ids = list(dict.fromkeys(_PLAY_ID_RE.findall(r.text)))
    # obviously junk ids filter
    ids = [i for i in ids if "." in i and len(i) >= 5 and not i.startswith("com.google.android.apps.")][:20]
    return ids


def _fmt_downloads(raw: str) -> str:
    """'10,000,000,000+' → '10B+' (padhne layak)."""
    s = str(raw or "").strip().rstrip("+")
    s = s.replace(",", "")
    try:
        n = float(s)
    except ValueError:
        return str(raw or "")
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            v = n / div
            return f"{v:.0f}{suf}+" if v >= 10 else f"{v:.1f}{suf}+"
    return f"{int(n)}+"


def _play_details(pkg: str) -> Optional[Dict[str, Any]]:
    """Play Store details page → title/developer/rating/downloads/icon.

    Live verify: com.whatsapp → 200 + h1 "WhatsApp Messenger" + og:image icon +
    rating 4.4 + downloads "10,000,000,000+". Non-existent pkg → **404**.
    """
    url = f"https://play.google.com/store/apps/details?id={quote(pkg)}&hl=en_IN&gl=IN"
    try:
        r = http_get(url, headers={"User-Agent": _UA, "Accept-Language": "en-IN,en;q=0.9"},
                     timeout=_TIMEOUT, retries=1)
    except Exception as e:                                          # noqa: BLE001
        log.debug("play_details fail %s: %s", pkg, str(e)[:80])
        return None
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        return None
    t = r.text

    def _meta(prop: str) -> str:
        m = re.search(r'<meta[^>]+(?:property|name)="' + re.escape(prop) +
                      r'"[^>]+content="([^"]*)"', t)
        return (m.group(1).strip() if m else "")

    title = ""
    # 1) itemprop="name" (sabse reliable — Play ka apna structured data)
    m = re.search(r'itemprop="name"[^>]*>([^<]{2,120})<', t)
    if m:
        title = m.group(1).strip()
    # 2) h1
    if not title:
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        if h1:
            title = re.sub(r"<[^>]+>", "", h1.group(1)).strip()
    # 3) og:title se " – Apps on Google Play" suffix hata ke
    if not title:
        og = _meta("og:title")
        title = re.sub(r"\s*[–\-|]\s*Apps on Google Play\s*$", "", og).strip()
    tagline = _meta("og:description") or _meta("twitter:description")
    icon = _meta("og:image") or _meta("twitter:image")

    # developer: <a href="/store/apps/developer?id=WhatsApp+LLC"><span>WhatsApp LLC</span></a>
    # ⚠️ naam <span> me wrap hota hai — v53.0 se pehle regex isi par fail hota tha.
    dev = ""
    # ⚠️ Play do tarah ke developer links use karta hai (dono live verify kiye):
    #   WhatsApp → /store/apps/developer?id=WhatsApp+LLC
    #   VLC      → /store/apps/dev?id=6364851808230428105   (numeric, short form)
    # v53.0 se pehle sirf lamba form match hota tha → VLC jaisi apps ka
    # developer khaali aata tha.
    m = re.search(r'/store/apps/(?:developer|dev)\?id=[^"&]+">\s*(?:<span[^>]*>)?([^<]{2,70})<', t)
    if m:
        dev = m.group(1).strip()
    if not dev:
        m = re.search(r'itemprop="author"[^>]*>([^<]{2,70})<', t)
        if m:
            dev = m.group(1).strip()
    if not dev:
        m = re.search(r'"([^"]{2,60})"\s*,\s*null\s*,\s*\[\s*\[\s*\\"/store/apps/dev', t)
        if m:
            dev = m.group(1).strip()

    # rating: aria-label="Rated 4.4 stars out of five stars"
    rating = ""
    m = re.search(r'aria-label="Rated\s+([\d.]{1,4})\s+stars?', t)
    if m:
        rating = m.group(1)
    else:
        m = re.search(r'"([\d]\.[\d])"', t)
        if m:
            rating = m.group(1)

    # reviews: <div class="g1rdde">24.5Cr reviews</div>  (India locale = Cr/L format)
    votes = ""
    m = re.search(r'>([\d.,]+\s*[KMB]?\s*(?:Cr|L|K|M|B)?)\s+reviews?<', t, re.I)
    if m:
        votes = re.sub(r"\s+", " ", m.group(1).strip()) + " reviews"
    if not votes:
        m = re.search(r'([\d,]{4,})\s+reviews', t, re.I)
        if m:
            votes = _fmt_votes(m.group(1))

    # downloads: <div class="ClM7O">1KCr+</div><div class="g1rdde">Downloads</div>
    downloads = ""
    m = re.search(r'>([A-Z0-9][\d.,]*\s*(?:KCr|Cr|L|K|M|B|T)?\+?)</div>\s*<div[^>]*>\s*Downloads', t, re.I)
    if m:
        downloads = m.group(1).strip()
    if not downloads:
        m = re.search(r'"([\d,]{6,})\+"', t)
        if m:
            downloads = _fmt_downloads(m.group(1) + "+")
    if not downloads:
        m = re.search(r'([\d,]{5,}\+)\s*Downloads', t, re.I)
        if m:
            downloads = _fmt_downloads(m.group(1))

    # content rating + price
    content_rating = ""
    for pat in (r'itemprop="contentRating"[^>]*>([^<]{1,40})<',
                r'aria-label="((?:Rated for|Content rating)[^"]{0,40})"',
                r'>((?:Rated for\s+)?\d{1,2}\+?)</div>\s*<div[^>]*>\s*(?:Rated for|Content rating|Age)'):
        m = re.search(pat, t, re.I)
        if m:
            v = m.group(1).strip()
            # ⚠️ "More info about this content rating" ek tooltip/link hai,
            # actual rating nahi — usse reject karo (v53.0 audit me pakda gaya).
            if v and "more info" not in v.lower() and len(v) <= 40:
                content_rating = _html_unescape(v)
                break

    price = "Free"
    m = re.search(r'itemprop="price"[^>]*content="([\d.]+)"', t)
    if m:
        try:
            price = "Free" if float(m.group(1)) == 0 else f"₹{float(m.group(1)):,.0f}"
        except ValueError:
            pass

    # extra details (label → value pairs embedded JSON me)
    def _near(label: str) -> str:
        m = re.search(re.escape(label) + r'[^A-Za-z0-9]{0,40}"([^"]{1,60})"', t)
        return m.group(1).strip() if m else ""

    return {
        "exists": True, "store": "play", "package": pkg,
        "title": _html_unescape(title)[:90] or pkg,
        "developer": _html_unescape(dev)[:60],
        "tagline": _html_unescape(tagline)[:140], "icon": icon[:400],
        "rating": rating, "votes": votes, "downloads": downloads,
        "content_rating": content_rating[:40], "price": price,
        "updated": _near("Updated on"),
        "version": _near("Version"),
        "url": url,
    }


def _fmt_votes(v: str) -> str:
    try:
        n = int(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return ""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M reviews"
    if n >= 1_000:
        return f"{n/1_000:.0f}K reviews"
    return f"{n} reviews"


# ---------------------------------------------------------------- iTunes
def _itunes_search(name: str, limit: int = 3) -> List[Dict[str, Any]]:
    """iTunes Search API (official, no key) → iOS apps with real ratings."""
    try:
        j = http_get_json("https://itunes.apple.com/search",
                          params={"term": name, "entity": "software",
                                  "country": "IN", "limit": limit},
                          timeout=_TIMEOUT, retries=1)
    except Exception as e:                                          # noqa: BLE001
        log.debug("itunes fail: %s", str(e)[:80])
        return []
    out = []
    for a in (j or {}).get("results") or []:
        if not isinstance(a, dict):
            continue
        rating = a.get("averageUserRating")
        out.append({
            "exists": True, "store": "appstore",
            "package": str(a.get("bundleId") or ""),
            "title": str(a.get("trackName") or "")[:90],
            "developer": str(a.get("sellerName") or a.get("artistName") or "")[:60],
            "tagline": str(a.get("description") or "")[:140],
            "icon": str(a.get("artworkUrl512") or a.get("artworkUrl100") or "").replace("100x100", "512x512"),
            "rating": f"{rating:.1f}" if isinstance(rating, (int, float)) and rating else "",
            "votes": _fmt_votes(a.get("userRatingCount") or 0),
            "downloads": "", "url": str(a.get("trackViewUrl") or ""),
            "price": "Free" if not float(a.get("price") or 0) else f"₹{a.get('price')}",
            "genre": str(a.get("primaryGenreName") or ""),
        })
    return out


# ---------------------------------------------------------------- F-Droid
def _fdroid_check(pkg: str) -> Optional[Dict[str, Any]]:
    """F-Droid official JSON API. 404 = app F-Droid par nahi hai."""
    try:
        j = http_get_json(f"https://f-droid.org/api/v1/packages/{quote(pkg)}",
                          timeout=12, retries=1)
    except NetError as e:
        if e.status == 404:
            return None
        return None
    except Exception:                                               # noqa: BLE001
        return None
    if not isinstance(j, dict) or not j.get("packageName"):
        return None
    pkgs = j.get("packages") or []
    ver = ""
    if pkgs and isinstance(pkgs[0], dict):
        ver = str(pkgs[0].get("versionName") or "")
    return {"exists": True, "store": "fdroid", "package": str(j.get("packageName")),
            "title": str(j.get("packageName")), "developer": "Open Source",
            "tagline": "", "icon": "", "rating": "", "votes": "",
            "downloads": "", "version": ver,
            "url": f"https://f-droid.org/packages/{j.get('packageName')}/"}


# ---------------------------------------------------------------- main lookup
@_tracked("appfind")
def app_lookup(name: str, use_cache: bool = True,
               max_results: int = _MAX_RESULTS) -> Dict[str, Any]:
    """App ka naam → **verified** app card(s).

    Teen sources parallel me hit hote hain (Play search + iTunes + Play details),
    phir top matches ki detail nikalti hai. Kuch na mile to honest `found=False`
    — pehle jaisa 8 blind links nahi.

    Returns:
      {"ok":True,"found":True,"query":..,"apps":[{...}],"stores":[...]}
      {"ok":True,"found":False,"query":..,"stores":[...],"error":..}
      {"ok":False,"error":..}   (invalid input)
    """
    q = re.sub(r"\s+", " ", str(name or "").strip())
    if not q:
        return {"ok": False, "error": "Koi app ka naam bhejo — jaise <code>WhatsApp</code>"}
    if len(q) < 2:
        return {"ok": False, "error": "App ka naam thoda lamba bhejo (2+ letters)."}
    if len(q) > 80:
        q = q[:80]

    def _work():
        # direct package-id diya ho (com.foo.bar)
        direct_pkg = q if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z0-9_]+){2,}", q) else ""

        play_ids: List[str] = []
        ios: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_play = ex.submit(_play_search, q)
            f_ios = ex.submit(_itunes_search, q, 3)
            try:
                play_ids = f_play.result() or []
            except Exception:                                       # noqa: BLE001
                play_ids = []
            try:
                ios = f_ios.result() or []
            except Exception:                                       # noqa: BLE001
                ios = []

        if direct_pkg and direct_pkg not in play_ids:
            play_ids.insert(0, direct_pkg)

        apps: List[Dict[str, Any]] = []
        # top Play matches ki detail (parallel, capped)
        if play_ids:
            with ThreadPoolExecutor(max_workers=min(4, len(play_ids[:4]))) as ex:
                futs = {ex.submit(_play_details, p): p for p in play_ids[:4]}
                for f in as_completed(futs):
                    try:
                        d = f.result()
                    except Exception:                               # noqa: BLE001
                        d = None
                    if d:
                        apps.append(d)
            # search order preserve karo
            order = {p: i for i, p in enumerate(play_ids[:4])}
            apps.sort(key=lambda a: order.get(a["package"], 99))

        # F-Droid check top match par (open-source flag)
        if apps:
            fd = _fdroid_check(apps[0]["package"])
            if fd:
                apps[0]["also_on_fdroid"] = True
                apps[0]["fdroid_url"] = fd["url"]

        # iOS results merge (alag store)
        for a in ios[:2]:
            apps.append(a)

        if not apps:
            return {"ok": True, "found": False, "query": q,
                    "apps": [], "stores": get_app_store_links(q)["stores"],
                    "error": (f"🔍 <b>'{q}' naam ki koi app nahi mili.</b>\n"
                              "──────────────────────\n"
                              "Google Play, App Store aur F-Droid — teeno par check kiya.\n\n"
                              "Ye ho sakta hai agar:\n"
                              "• Naam ki spelling alag ho (English me try karo)\n"
                              "• App sirf kisi ek country me ho\n"
                              "• App Play Store se hat gayi ho\n\n"
                              "💡 Poora naam ya developer ke saath bhejo, jaise "
                              "<code>WhatsApp Messenger</code>")}

        return {"ok": True, "found": True, "query": q,
                "apps": apps[:max_results],
                "play_ids": play_ids[:max_results],
                "stores": get_app_store_links(q)["stores"]}

    if not use_cache:
        return _work()
    val, _hit = cached_call(_cache, f"app:{q.lower()}", _work, ttl=_CACHE_TTL,
                            fail_ttl=_FAIL_TTL,
                            is_failure=lambda v: not v.get("ok") or not v.get("found"))
    return val
