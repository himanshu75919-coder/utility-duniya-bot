# -*- coding: utf-8 -*-
"""
IMEI / Phone Details (v41)
==========================
Ek IMEI number → poora device details: brand, model, photo + spec sections
(Network, Launch, Body, Display, Platform, Memory, Camera, Sound, Comms,
Features, Battery, Misc) + ek `.json` spec file (copy-code style).

Kahan se data aata hai:
  /api/imei?key=...&imei=15-digit     → { imei, result: { header:{brand,model,photo,imei},
                                                         items:[{role,title,content}] } }

Default base: https://osint-apis-hub.onrender.com/api   (key: Demo — apni key env me daal do)
ENV (Render → Environment):
  IMEI_API_BASE     = API host + /api   (khaali ho to VEHICLE_API_BASE / default)
  IMEI_API_KEY      = apni key          (khaali ho to VEHICLE_API_KEY / Demo)
  IMEI_TIMEOUT      = seconds (default 25)

IMEI check: 15 digit + Luhn. Galat IMEI par paisa/API call waste nahi hota.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime

import requests

DEFAULT_BASE = "https://osint-apis-hub.onrender.com/api"
TIMEOUT = int(os.environ.get("IMEI_TIMEOUT", "25"))
CACHE_TTL = 600          # 10 minute — same IMEI dobara check ho to API call na lage
_FAIL_TTL = 60

_CACHE: dict = {}
_LOCK = threading.Lock()

UA_HEADERS = {"User-Agent": "UtilityDuniyaBot/1.0", "Accept": "application/json"}

_EMPTY = ("", "-", "none", "na", "n/a", "null", "unknown", "not available")


# ---------------------------------------------------------------- config
def api_base() -> str:
    b = (os.environ.get("IMEI_API_BASE") or os.environ.get("VEHICLE_API_BASE") or "").strip()
    if b:
        return b.rstrip("/")
    return DEFAULT_BASE


def api_key() -> str:
    return (os.environ.get("IMEI_API_KEY") or os.environ.get("VEHICLE_API_KEY")
            or os.environ.get("IMEI_API_TOKEN") or "Demo").strip()


def is_configured() -> bool:
    return bool(api_base())


# ---------------------------------------------------------------- input
def clean_imei(text: str) -> str:
    """'IMEI: 35-301011-1111110' jaisa bhi chalega → sirf digits."""
    s = re.sub(r"\D", "", str(text or ""))
    if len(s) in (16, 17):        # IMEISV (16) ya IMEI+SV → pehle 15 = asli IMEI
        s = s[:15]
    return s


def luhn_ok(num: str) -> bool:
    d = [int(c) for c in str(num or "") if c.isdigit()]
    if len(d) < 2:
        return False
    total, alt = 0, False
    for n in reversed(d):
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        alt = not alt
    return total % 10 == 0


def validate_imei(text: str) -> tuple:
    """(ok, clean_imei, error_hindi_free_english)"""
    c = clean_imei(text)
    if len(c) != 15:
        return False, c, "IMEI must be exactly 15 digits."
    if not luhn_ok(c):
        return False, c, "This IMEI is not valid (check digit failed). Please re-check."
    return True, c, ""


def imei_of_device() -> str:
    """Jahan IMEI milta hai — user ko batane ke liye."""
    return "Dial *#06# on the phone — the IMEI shows on the screen."


# ---------------------------------------------------------------- http
def _get(url: str, params: dict, tmo: int = TIMEOUT):
    try:
        r = requests.get(url, params=params, headers=UA_HEADERS, timeout=tmo)
    except requests.Timeout:
        return None, "The API took too long to answer."
    except Exception as e:
        return None, f"Could not reach the API: {str(e)[:80]}"
    if r.status_code != 200:
        return None, f"The API returned HTTP {r.status_code}."
    try:
        return r.json(), None
    except Exception:
        return None, "The API did not send JSON."


def _err_of(payload) -> str:
    if not isinstance(payload, dict):
        return ""
    for k in ("error", "errorMsg", "message", "msg", "detail"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:120]
    return ""


# ---------------------------------------------------------------- parsing
def _clean_val(v) -> str:
    s = str(v if v is not None else "").strip()
    if s.lower() in _EMPTY:
        return ""
    if s == "True":
        return "✅"
    if s == "False":
        return "❌"
    return s


_SKIP_HEADERS = ("found an error", "help us and let us know")
_SKIP_LINKS = ("support team contact", "found an error")


def parse_imei_payload(payload, imei: str = "") -> dict:
    """API ka jawab → {ok, imei, brand, model, photo, sections, links}.

    sections = [ {"title": "Display", "rows": [("Display type", "OLED"), ...]}, ... ]
    links    = [ ("Tutorials", "https://..."), ... ]
    """
    if not isinstance(payload, dict):
        return {"ok": False, "error": "Bad API response.", "imei": imei}

    api_err = _err_of(payload)
    if api_err:
        low = api_err.lower()
        if "invalid" in low and "imei" in low:
            return {"ok": False, "error": "This IMEI is not in the database (not a valid device IMEI).",
                    "imei": imei, "not_found": True}
        return {"ok": False, "error": api_err, "imei": imei}

    res = payload.get("result")
    if isinstance(res, str):                       # {"result": "Invalid IMEI"}
        low = res.lower()
        if "invalid" in low:
            return {"ok": False, "error": "This IMEI is not in the database (not a valid device IMEI).",
                    "imei": imei, "not_found": True}
        return {"ok": False, "error": res[:120], "imei": imei}
    if not isinstance(res, dict):
        return {"ok": False, "error": "No device details found for this IMEI.", "imei": imei, "not_found": True}

    head = res.get("header") or {}
    items = res.get("items") or []
    if not isinstance(items, list):
        items = []

    sections: list = []
    links: list = []
    cur = None

    def _add_row(title, content):
        t, c = _clean_val(title), _clean_val(content)
        if not t or not c:
            return
        nonlocal cur
        if cur is None:
            cur = {"title": "General", "rows": []}
            sections.append(cur)
        cur["rows"].append((t, c))

    def _add_link(title, url):
        t, u = _clean_val(title), str(url or "").strip()
        if not u.lower().startswith(("http", "mailto:")):
            return
        if any(s in t.lower() for s in _SKIP_LINKS):
            return
        links.append((t or "Open", u))

    for it in items:
        if not isinstance(it, dict):
            continue
        role = str(it.get("role") or "").strip().lower()
        title = _clean_val(it.get("title"))
        content = it.get("content")
        if role == "header":
            if not title or any(s in title.lower() for s in _SKIP_HEADERS):
                cur = None if (title and any(s in title.lower() for s in _SKIP_HEADERS)) else cur
                continue
            cur = {"title": title, "rows": []}
            sections.append(cur)
        elif role == "item" or (not role and title and content is not None):
            _add_row(title, content)
        elif role == "button":
            _add_link(title, content)
        elif role == "group":
            for sub in (it.get("items") or []):
                if isinstance(sub, dict):
                    if str(sub.get("role")).lower() == "button":
                        _add_link(sub.get("title"), sub.get("content"))
                    else:
                        _add_row(sub.get("title"), sub.get("content"))

    sections = [s for s in sections if s["rows"]]

    brand = _clean_val(head.get("brand"))
    model = _clean_val(head.get("model"))
    photo = str(head.get("photo") or "").strip()
    clean = clean_imei(payload.get("imei") or imei)

    if not (brand or model) and not sections:
        return {"ok": False, "error": "No device details found for this IMEI.",
                "imei": clean, "not_found": True}

    return {
        "ok": True,
        "imei": clean,
        "brand": brand,
        "model": model,
        "photo": photo,
        "sections": sections,
        "links": links[:6],
        "checked_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "_source": "imei",
    }


# ---------------------------------------------------------------- fetch + cache
def fetch_imei_details(imei: str, use_cache: bool = True) -> dict:
    """IMEI → device details (cache ke saath). Wrong/unknown IMEI par clear error."""
    ok, clean, err = validate_imei(imei)
    if not ok:
        return {"ok": False, "error": err, "imei": clean}
    clean = clean or clean_imei(imei)

    now = time.time()
    if use_cache:
        with _LOCK:
            hit = _CACHE.get(clean)
        if hit and (now - hit[0]) < (CACHE_TTL if hit[1].get("ok") else _FAIL_TTL):
            out = dict(hit[1])
            out["cached"] = True
            return out

    payload, net_err = _get(f"{api_base()}/imei", {"key": api_key(), "imei": clean})
    if payload is None:
        out = {"ok": False, "error": net_err or "API is not reachable right now.", "imei": clean}
    else:
        out = parse_imei_payload(payload, clean)

    with _LOCK:
        _CACHE[clean] = (now, out)
        if len(_CACHE) > 300:
            for k in sorted(_CACHE, key=lambda x: _CACHE[x][0])[:100]:
                _CACHE.pop(k, None)
    return out


def clear_cache() -> None:
    with _LOCK:
        _CACHE.clear()


# ---------------------------------------------------------------- render
def device_title(res: dict) -> str:
    b = _clean_val(res.get("brand"))
    m = _clean_val(res.get("model"))
    if b and m and b.lower() not in m.lower():
        return f"{b.title()} {m}"
    return (m or b or "Unknown device")


def _sec_icon(title: str) -> str:
    t = str(title or "").lower()
    for keys, icon in (
        (("network", "comms", "connect"), "📶"),
        (("launch", "release", "date"), "📅"),
        (("body", "dimension", "weight"), "📐"),
        (("display", "screen"), "🖥️"),
        (("platform", "chipset", "cpu", "os", "processor"), "⚙️"),
        (("memory", "storage", "ram"), "💾"),
        (("camera", "selfie", "main"), "📷"),
        (("sound", "audio", "speaker"), "🔊"),
        (("feature", "sensor"), "✨"),
        (("battery", "power"), "🔋"),
        (("basic", "general", "info"), "📋"),
    ):
        if any(k in t for k in keys):
            return icon
    return "🔹"


def render_caption(res: dict, max_len: int = 1000) -> str:
    """Photo ke saath chhota caption (Telegram limit 1024 — isliye chhota)."""
    lines = [f"📲 <b>{device_title(res)}</b>"]
    if res.get("brand"):
        lines.append(f"🏷️ <b>Brand:</b> {res['brand']}")
    lines.append(f"🔢 <b>IMEI:</b> <code>{res.get('imei') or '—'}</code>")
    # top 5 sections ke 2-2 key points
    shown = 0
    for s in res.get("sections") or []:
        if shown >= 5:
            break
        head = f"{_sec_icon(s['title'])} <b>{s['title']}</b>"
        rows = []
        for k, v in s["rows"][:2]:
            txt = f"• {k}: {v}"
            if len(txt) > 70:
                txt = txt[:69] + "…"
            rows.append(txt)
        block = head + "\n" + "\n".join(rows)
        if len("\n".join(lines)) + len(block) + 60 > max_len:
            break
        lines.append(block)
        shown += 1
    lines.append("👇 <i>Full specification in the next message.</i>")
    out = "\n".join(lines)
    return out[:1024]


def render_text(res: dict, max_len: int = 3600) -> str:
    """Poora spec card (Telegram text message)."""
    if not res.get("ok"):
        return ""
    out = [
        f"📲 <b>{device_title(res)}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🏷️ <b>Brand:</b> {res.get('brand') or '—'}",
        f"🔢 <b>IMEI:</b> <code>{res.get('imei') or '—'}</code>",
    ]
    for s in res.get("sections") or []:
        out.append("━━━━━━━━━━━━━━━━━━━━━━")
        out.append(f"{_sec_icon(s['title'])} <b>{s['title']}</b>")
        for k, v in s["rows"]:
            txt = f"• <b>{k}:</b> {v}"
            if len(txt) > 120:
                txt = txt[:119] + "…"
            out.append(txt)
        if len("\n".join(out)) > max_len:
            out.append("<i>…spec list is long (full copy in the .json file below)</i>")
            break
    out.append("━━━━━━━━━━━━━━━━━━━━━━")
    out.append("<i>Data: imei.info device database · confirm on the official brand site before buying/selling.</i>")
    txt = "\n".join(out)
    return txt[:4000]


def render_report(res: dict) -> str:
    """Alias — bot isi naam se call karta hai."""
    return render_text(res)


def specs_dict(res: dict) -> dict:
    """Copy-code style JSON (bilkul spec sheet jaisa)."""
    specs = {}
    for s in res.get("sections") or []:
        specs[s["title"]] = {k: v for k, v in s["rows"]}
    return {
        "device": device_title(res),
        "brand": res.get("brand") or "",
        "model": res.get("model") or "",
        "imei": res.get("imei") or "",
        "checked_at": res.get("checked_at") or datetime.now().strftime("%d-%m-%Y %H:%M"),
        "specifications": specs,
        "source": "osint-apis-hub / imei.info",
    }


def specs_json_bytes(res: dict) -> bytes:
    return json.dumps(specs_dict(res), ensure_ascii=False, indent=2).encode("utf-8")


def specs_filename(res: dict) -> str:
    """Samsung_Galaxy_A9+_specs.json jaisa naam."""
    name = device_title(res)
    name = re.sub(r"[^\w+\-. ]", "", name).strip().replace(" ", "_")
    name = re.sub(r"_+", "_", name) or "device"
    return f"{name[:60]}_specs.json"


def fallback_links(imei: str = "") -> list:
    """API down ho to user khud check kar sake."""
    c = clean_imei(imei)
    return [
        ("🌐 Check on imei.info", f"https://www.imei.info/?imei={c}" if c else "https://www.imei.info/"),
        ("📱 How to find IMEI (dial *#06#)", "https://www.imei.info/faq-where-find-imei/"),
    ]


def help_card(error: str = "", imei: str = "") -> str:
    head = "📲 <b>IMEI / PHONE DETAILS</b>\n━━━━━━━━━━━━━━━━━━━━━━"
    if error:
        head += f"\n⚠️ <b>{error}</b>"
    return (
        head + "\n"
        "Send the <b>15 digit IMEI</b> of the phone.\n"
        "📍 Where to find it: dial <code>*#06#</code> on the phone, or see the box / bill.\n"
        "✅ You get: brand, model, device photo + full spec sheet (display, chipset, camera, "
        "battery, network) + a <code>.json</code> copy file.\n"
        "<i>Works for any phone/tablet. For legal use only (checking your own or a device you are buying).</i>"
    )
