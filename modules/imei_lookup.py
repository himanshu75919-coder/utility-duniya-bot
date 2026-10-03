# -*- coding: utf-8 -*-
"""
IMEI / Phone Details (v41)
==========================
IMEI locally validate hota hai; network par sirf pehle 8 digits (TAC) bheje jate hain.
Hub ke local catalog se limited brand/model hint aa sakta hai; full specifications,
photo ya har model ki coverage guaranteed nahi. Serial, owner, blacklist ya tracking lookup nahi hota.

Kahan se data aata hai:
  /api/imei?key=...&imei=8-digit-TAC → TAC-based local device hint (flat ya safe legacy response)

Default base: https://osint-api-hub.onrender.com/api (canonical hub)
ENV (Render → Environment):
  IMEI_API_BASE     = API host + /api   (default upar wala)
  IMEI_API_KEY      = apni key          (default: Demo)
  IMEI_TIMEOUT      = seconds (default 25)

Privacy: bot IMEI ko locally validate karta hai; response me sirf device/TAC details dikhata hai.
Full serial/blacklist/owner data is endpoint se nahi liya jata.

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

DEFAULT_BASE = "https://osint-api-hub.onrender.com/api"
TIMEOUT = int(os.environ.get("IMEI_TIMEOUT", "25"))
CACHE_TTL = 600          # 10 minute — same TAC dobara check ho to API call na lage
_FAIL_TTL = 60

_CACHE: dict = {}
_LOCK = threading.Lock()

UA_HEADERS = {"User-Agent": "UtilityDuniyaBot/1.0", "Accept": "application/json"}

_EMPTY = ("", "-", "none", "na", "n/a", "null", "unknown", "not available")


# ---------------------------------------------------------------- config
def api_base() -> str:
    """IMEI config ko canonical hub par rakho; Vehicle credentials alag rehte hain."""
    b = (os.environ.get("IMEI_API_BASE") or os.environ.get("OSINT_API_BASE") or DEFAULT_BASE).strip()
    b = b.rstrip("/")
    if b.lower().endswith("/imei"):
        b = b[:-5].rstrip("/")
    if not b.lower().endswith("/api"):
        b += "/api"
    return b


def api_key() -> str:
    # IMEI key alag rakhein; Vehicle API ki key galti se bhejne se HTTP 401 aa sakta hai.
    return (os.environ.get("IMEI_API_KEY") or os.environ.get("OSINT_API_KEY")
            or os.environ.get("IMEI_API_TOKEN") or "Demo").strip() or "Demo"


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
    safe_tac = clean_imei(imei)[:8]
    if not isinstance(payload, dict):
        return {"ok": False, "error": "Bad API response.", "imei": safe_tac, "tac": safe_tac}

    api_err = _err_of(payload)
    if api_err:
        low = api_err.lower()
        if "invalid" in low and "imei" in low:
            return {"ok": False, "error": "This IMEI is not in the device catalog.",
                    "imei": safe_tac, "tac": safe_tac, "not_found": True}
        return {"ok": False, "error": api_err, "imei": safe_tac, "tac": safe_tac}

    res = payload.get("result")
    if isinstance(res, str):                       # {"result": "Invalid IMEI"}
        low = res.lower()
        if "invalid" in low:
            return {"ok": False, "error": "Yeh IMEI device catalog me nahi mila.",
                    "imei": clean_imei(imei)[:8], "not_found": True}
        return {"ok": False, "error": res[:120], "imei": clean_imei(imei)[:8]}

    # Canonical ToolVault hub ka native jawab flat hota hai: brand/model/tac.
    # Purana provider `result.header/items` bhejta tha; dono formats accept hote hain.
    if not isinstance(res, dict):
        flat = payload.get("local_analysis") if isinstance(payload.get("local_analysis"), dict) else payload
        brand = _clean_val(flat.get("brand"))
        model = _clean_val(flat.get("model"))
        tac = clean_imei(flat.get("tac") or imei)[:8]
        if not (brand or model):
            return {"ok": False, "error": "Is TAC ke liye device model catalog me nahi mila.",
                    "imei": tac, "tac": tac, "not_found": True}
        rows = [("TAC (first 8 digits)", tac)]
        if brand:
            rows.append(("Brand", brand))
        if model:
            rows.append(("Model", model))
        if flat.get("reporting_body"):
            rows.append(("Reporting body", _clean_val(flat.get("reporting_body"))))
        if flat.get("luhn_check"):
            rows.append(("Check", "Valid format; device identity matched by TAC"))
        if flat.get("note"):
            rows.append(("Catalog note", _clean_val(flat.get("note"))))
        meta = payload.get("_meta") if isinstance(payload.get("_meta"), dict) else {}
        return {
            "ok": True, "imei": tac, "tac": tac,
            "brand": brand, "model": model, "photo": "", "url": "",
            "sections": [{"title": "Device match (TAC)", "rows": rows}],
            "links": [], "checked_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "_source": str(meta.get("source") or "local TAC catalog"),
            "spec_level": "model-match-only",
        }

    head = res.get("header") or {}
    items = res.get("items") or []
    if not isinstance(items, list):
        items = []

    sections: list = []
    links: list = []
    cur = None

    def _add_row(title, content):
        t, c = _clean_val(title), _clean_val(content)
        low_title = t.lower().replace("_", " ").strip()
        # IMEI serial, SNR aur IMEI2 ko report/JSON me repeat nahi karte.
        if (not t or not c or low_title in {"imei", "imei number", "imei2", "serial", "serial number", "snr"}
                or "serial number" in low_title):
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

    brand = _clean_val(head.get("brand") or res.get("brand"))
    model = _clean_val(head.get("model") or res.get("model"))
    photo = str(head.get("photo") or res.get("photo") or "").strip()
    if not photo.lower().startswith(("https://", "http://")):
        photo = ""
    page_url = str(head.get("url") or res.get("url") or "").strip()
    if not page_url.lower().startswith(("https://", "http://")):
        page_url = ""
    tac = clean_imei(payload.get("tac") or imei)[:8]

    if not (brand or model) and not sections:
        return {"ok": False, "error": "Is TAC ke liye device details catalog me nahi mile.",
                "imei": tac, "tac": tac, "not_found": True}

    meta = payload.get("_meta") if isinstance(payload.get("_meta"), dict) else {}
    return {
        "ok": True,
        "imei": tac,             # backward-compatible field; ab isme sirf TAC rahega
        "tac": tac,
        "brand": brand,
        "model": model,
        "photo": photo,
        "url": page_url,
        "sections": sections,
        "links": links[:6],
        "checked_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "_source": str(meta.get("source") or "device catalog"),
    }


# ---------------------------------------------------------------- fetch + cache
def fetch_imei_details(imei: str, use_cache: bool = True) -> dict:
    """IMEI → device details (cache ke saath). Wrong/unknown IMEI par clear error."""
    ok, clean, err = validate_imei(imei)
    if not ok:
        return {"ok": False, "error": err, "tac": clean[:8]}
    clean = clean or clean_imei(imei)
    tac = clean[:8]

    now = time.time()
    if use_cache:
        with _LOCK:
            hit = _CACHE.get(tac)
        if hit and (now - hit[0]) < (CACHE_TTL if hit[1].get("ok") else _FAIL_TTL):
            out = dict(hit[1])
            out["cached"] = True
            return out

    # Full IMEI locally validate hota hai; network par sirf TAC (first 8 digits) jata hai.
    payload, net_err = _get(f"{api_base()}/imei", {"key": api_key(), "imei": tac})
    if payload is None:
        out = {"ok": False, "error": net_err or "API is not reachable right now.", "imei": tac, "tac": tac}
    else:
        out = parse_imei_payload(payload, tac)

    with _LOCK:
        _CACHE[tac] = (now, out)
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
    lines.append(f"🔎 <b>TAC:</b> <code>{res.get('tac') or res.get('imei') or '—'}</code>")
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
    lines.append("👇 <i>Catalog me available device details neeche hain; full spec har model ke liye guaranteed nahi.</i>")
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
        f"🔎 <b>TAC:</b> <code>{res.get('tac') or res.get('imei') or '—'}</code>",
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
    out.append("<i>Source: local TAC/device catalog. Serial number, owner, blacklist ya live-network status check nahi hota.</i>")
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
        "device_name": device_title(res),
        "image_url": res.get("photo") or "",
        "url": res.get("url") or "",
        "brand": res.get("brand") or "",
        "model": res.get("model") or "",
        "tac": res.get("tac") or res.get("imei") or "",
        "checked_at": res.get("checked_at") or datetime.now().strftime("%d-%m-%Y %H:%M"),
        "specifications": specs,
        "source": res.get("_source") or "local TAC catalog",
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
    """Generic help links only; full IMEI ko kisi third-party URL me nahi bhejte."""
    return [
        ("📱 Device specifications (GSMArena)", "https://www.gsmarena.com/"),
        ("ℹ️ IMEI/TAC kya hota hai?", "https://en.wikipedia.org/wiki/Type_Allocation_Code"),
    ]


def help_card(error: str = "", imei: str = "") -> str:
    head = "📲 <b>IMEI / PHONE DETAILS</b>\n━━━━━━━━━━━━━━━━━━━━━━"
    if error:
        head += f"\n⚠️ <b>{error}</b>"
    return (
        head + "\n"
        "Apne ya authorized device ka <b>15 digit IMEI</b> bhejein.\n"
        "📍 IMEI dekhne ke liye phone par <code>*#06#</code> dial karein.\n"
        "🔒 IMEI yahin locally validate hota hai; API ko sirf pehle 8 digit TAC bheja jata hai.\n"
        "✅ Catalog me available brand/model aur specifications + <code>.json</code> copy file milegi.\n"
        "ℹ️ Har model ki full specs/photo catalog me guaranteed nahi; owner, blacklist ya tracking data nahi liya jata."
    )
