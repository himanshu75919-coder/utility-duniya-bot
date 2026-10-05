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

Default base: https://osint-api-hub.onrender.com/api   (key: HUB_API_KEY ya IMEI_API_KEY, default Demo)
ENV (Render → Environment):
  IMEI_API_BASE     = API host + /api   (khaali ho to VEHICLE_API_BASE / default)
  IMEI_API_KEY      = apni key          (khaali ho to HUB_API_KEY / VEHICLE_API_KEY)
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
from html import escape as _hesc

import requests

DEFAULT_BASE = "https://osint-api-hub.onrender.com/api"   # v49: naya LIVE hub (purana dead tha)
TIMEOUT = int(os.environ.get("IMEI_TIMEOUT", "25"))
# device-specs ka timeout chhota rakha: jab model ek CODE hota hai (T528) to hub
# ~22s tak ghoom kar fail hota hai — wo wait user ko na deni pade. Marketing naam
# par ye 0.3-0.6s me aa jata hai, to 8s kaafi hai.
SPEC_TIMEOUT = int(os.environ.get("IMEI_SPEC_TIMEOUT", "8"))
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
        b = b.rstrip("/")
        if b.lower().endswith("/imei"):
            b = b[:-5].rstrip("/")
        if not b.lower().endswith("/api"):
            b += "/api"
        return b
    try:
        from modules import api_hub as _hub
        if _hub.hub_key():
            return _hub.hub_base()
    except Exception:
        pass
    return DEFAULT_BASE


def api_key() -> str:
    try:
        from modules import api_hub as _hub
        if _hub.hub_ready():
            return _hub.hub_key()
    except Exception:
        pass
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
        return False, c, "IMEI poori 15 digit ka hona chahiye."
    if not luhn_ok(c):
        return False, c, "Ye IMEI sahi nahi hai (check digit fail). Dobara check karo."
    return True, c, ""


def imei_of_device() -> str:
    """Jahan IMEI milta hai — user ko batane ke liye."""
    return "Phone me *#06# dial karo — IMEI screen par dikh jayega."


# ---------------------------------------------------------------- http
def _get(url: str, params: dict, tmo: int = TIMEOUT):
    try:
        r = requests.get(url, params=params, headers=UA_HEADERS, timeout=tmo)
    except requests.Timeout:
        return None, "API ne jawab dene me zyada time liya."
    except Exception as e:
        return None, f"API tak nahi pahunch paye: {str(e)[:80]}"
    if r.status_code != 200:
        return None, f"API ne HTTP {r.status_code} bheja."
    try:
        return r.json(), None
    except Exception:
        return None, "API ne JSON nahi bheja."


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
        return {"ok": False, "error": "API ka jawab kharab aaya.", "imei": safe_tac, "tac": safe_tac}

    api_err = _err_of(payload)
    if api_err:
        low = api_err.lower()
        if "invalid" in low and "imei" in low:
            return {"ok": False, "error": "Ye IMEI database me nahi hai (valid device IMEI nahi hai).", "imei": safe_tac, "tac": safe_tac, "not_found": True}
        if "disabled" in low or "not supported" in low:
            return {"ok": False, "imei": safe_tac, "tac": safe_tac, "hub_disabled": True, "error": api_err}
        return {"ok": False, "error": api_err, "imei": safe_tac, "tac": safe_tac}

    # 🆕 v48: user ke hub v2.4/v2.5 ka POORA response (255k TAC database + nanoreview specs + photo):
    # {"success":true,"tac":"35635642","brand":"SAMSUNG","device":"SAMSUNG GALAXY TAB A9+",
    #  "extra":"","model_codes":[...],"released":"2023","image":"https://nanoreview.net/...",
    #  "specs":{"name":..., "url":..., "image":..., "row_count":122,
    #           "sections":[{"title":"Display","rows":[["Type","TFT LCD"], ...]}]},
    #  "links":{"gsmarena":..., "nanoreview":..., "imei_info":...},
    #  "source":"tac-db (248364 rows)","specs_source":"nanoreview.net"}
    _sp = payload.get("specs") if isinstance(payload.get("specs"), dict) else {}
    if payload.get("success") is not False and (
        payload.get("device") or _sp or payload.get("tac") or payload.get("brand") or payload.get("model")
    ) and "result" not in payload:
        brand = _clean_val(payload.get("brand"))
        model = _clean_val(payload.get("device") or payload.get("model"))
        tac = _clean_val(payload.get("tac")) or safe_tac
        extra = _clean_val(payload.get("extra"))
        released = _clean_val(payload.get("released"))
        codes = [str(c) for c in (payload.get("model_codes") or []) if str(c).strip()]
        photo = str(payload.get("image") or _sp.get("image") or "").strip()
        photo_hd = str(payload.get("image_hd") or "").strip()

        rows = []
        for k, v in (("Brand", brand), ("Model", model), ("TAC (first 8 digits)", tac),
                     ("Variant / extra", extra), ("Released", released)):
            if v:
                rows.append((k, v))
        if codes:
            rows.append(("Model codes", ", ".join(codes[:8])))
        sections = [{"title": "Device", "rows": rows}] if rows else []
        body = _clean_val(payload.get("reporting_body"))
        if body:
            sections.append({"title": "Reporting body", "rows": [("GSMA reporting body", body)]})
        note_txt = _clean_val(payload.get("note"))
        if note_txt:
            sections.append({"title": "Note", "rows": [("Info", note_txt)]})

        for sec in (_sp.get("sections") or []):
            if not isinstance(sec, dict):
                continue
            t = _clean_val(sec.get("title")) or "Specs"
            rr = []
            for kr in (sec.get("rows") or []):
                try:
                    k, v = kr[0], kr[1]
                except Exception:  # noqa: BLE001
                    continue
                k2, v2 = _clean_val(k), _clean_val(v)
                if k2 and v2:
                    rr.append((k2, v2))
            if rr:
                sections.append({"title": t, "rows": rr})

        links = []
        lk = payload.get("links") if isinstance(payload.get("links"), dict) else {}
        nr_url = str(_sp.get("url") or lk.get("nanoreview") or "").strip()
        if nr_url:
            links.append(("🔎 Full specs page (nanoreview)", nr_url))
        if lk.get("gsmarena"):
            links.append(("📱 Search on GSMArena", str(lk["gsmarena"])))
        if lk.get("imei_info"):
            links.append(("🌐 Check on imei.info", str(lk["imei_info"])))
        if not lk and (brand or model):
            q = "+".join(x for x in (brand, model) if x).replace(" ", "+")
            links.append(("📱 Full specs (GSMArena)", f"https://www.gsmarena.com/res.php3?sSearch={q}"))
            links.append(("🔎 Search this device", f"https://www.google.com/search?q={q}+specifications"))
            links.append(("📲 Check on imei.info", f"https://www.imei.info/?imei={tac or safe_tac}"))
        links.append(("📲 How to find IMEI (dial *#06#)", "https://www.imei.info/faq-where-find-imei/"))

        src_note = "TAC database"
        _src = _clean_val(payload.get("source"))
        _rows = re.search(r"(\d{3,7})", _src)
        if _rows:
            src_note += f" ({int(_rows.group(1)):,} TACs)"
        if payload.get("specs_source"):
            src_note += f" + {_clean_val(payload.get('specs_source'))}"
        got_specs = bool(_sp.get("sections"))
        return {
            "ok": True,
            "imei": clean_imei(payload.get("imei") or imei) or imei,
            "brand": brand,
            "model": model,
            "tac": tac,
            "photo": photo,
            "photo_hd": photo_hd,
            "specs_name": _clean_val(_sp.get("name")),
            "specs_url": nr_url,
            "url": nr_url,
            "specs_rows": int(_sp.get("row_count") or 0),
            "specs_pending": bool(payload.get("specs_pending") or not got_specs),
            "sections": sections,
            "links": links[:6],
            "checked_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "source_note": src_note,
            "basic": not got_specs,
            "_source": "hub v2.4",
        }

    # 🆕 v46: user ke hub ka TAC (local match) response:
    # {"success":true,"tac":"35301011","brand":"APPLE","model":"iPhone 12 mini","reporting_body":"BABT (UK)"}
    if payload.get("success") and (payload.get("brand") or payload.get("model") or payload.get("tac")):
        brand = _clean_val(payload.get("brand"))
        model = _clean_val(payload.get("model"))
        tac = _clean_val(payload.get("tac"))
        body = _clean_val(payload.get("reporting_body"))
        note = _clean_val(payload.get("note"))
        dev_rows = [(k, v) for k, v in (("Brand", brand), ("Model", model), ("TAC (first 8 digits)", tac)) if v]
        sections = [{"title": "Device (TAC match)", "rows": dev_rows}] if dev_rows else []
        if body:
            sections.append({"title": "Reporting body", "rows": [("GSMA reporting body", body)]})
        if note:
            sections.append({"title": "Note", "rows": [("Info", note)]})
        q = "+".join(x for x in (brand, model) if x).replace(" ", "+")
        links = []
        if q:
            links.append(("📱 Full specs (GSMArena)", f"https://www.gsmarena.com/res.php3?sSearch={q}"))
            links.append(("🔎 Search this device", f"https://www.google.com/search?q={q}+specifications"))
        links.append(("📲 Check on imei.info", f"https://www.imei.info/?imei={imei}"))
        return {"ok": True, "imei": imei, "brand": brand, "model": model, "tac": tac,
                "photo": "", "sections": sections, "links": links, "basic": True,
                "source": "hub (TAC)"}

    res = payload.get("result")
    if isinstance(res, str):                       # {"result": "Invalid IMEI"}
        low = res.lower()
        if "invalid" in low:
            return {"ok": False, "error": "Ye IMEI database me nahi hai (valid device IMEI nahi hai).", "imei": safe_tac, "tac": safe_tac, "not_found": True}

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
        if t.lower() in ("imei", "imei2", "serial", "serial number", "sn", "meid"):
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
    head_url = str(head.get("url") or "").strip()
    clean = clean_imei(payload.get("imei") or imei)
    tac_val = clean[:8] or safe_tac

    if not (brand or model) and not sections:
        return {"ok": False, "error": "No device details found for this IMEI.",
                "imei": safe_tac, "tac": safe_tac, "not_found": True}

    return {
        "ok": True,
        "imei": clean,
        "tac": tac_val,
        "brand": brand,
        "model": model,
        "photo": photo,
        "url": head_url,
        "specs_url": head_url,
        "sections": sections,
        "links": links[:6],
        "checked_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "_source": "imei",
    }


# ---------------------------------------------------------------- spec chain (v54)
# Pehle IMEI sirf TAC tak ruk jata tha: hub ka /api/imei brand+model deta hai par
# `specs_pending: true` (poora spec sheet NAHI). User ne kaha "IMEI se PURI detail
# nikal jaye". Ab ek chain hai:
#     IMEI → /api/imei (TAC db: brand+model)
#          → /api/device-specs?model=<naam>  (nanoreview: poora spec + photo)
# Agar model ek internal CODE hai (T528 / SM-A155F) to device-specs use nahi
# pehchanta — pehle DuckDuckGo se marketing naam resolve karte hain, phir specs.
# Sab fail ho to TAC result waisa hi wapas (graceful, koi crash nahi).
_SPEC_CACHE: dict = {}
_NAME_CACHE: dict = {}
_SPEC_TTL = 6 * 3600

# marketing-name ke hints: agar model me inme se kuch hai to wo marketing naam hai
# (device-specs seedha chala lega), warna wo model CODE hai (resolve karna padega)
_MKT_HINTS = ("galaxy", "redmi", "note", "spark", "camon", "poco", "iphone", "ipad",
              "pixel", "nord", "narzo", "realme", "honor", "mate", "nova", "tab",
              "watch", "band", "pro", "max", "plus", "lite", "ultra", "prime",
              "power", "magic", "smart", "play", "hot", "pop", "neo", "gt")

# DuckDuckGo ke liye browser-jaisa UA (bot-UA par HTML search block hota hai)
_DDG_UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/126.0 Safari/537.36"),
           "Accept-Language": "en-IN,en;q=0.9"}


def _looks_marketing(model: str) -> bool:
    m = (model or "").strip().lower()
    if not m:
        return False
    if " " in m:                       # "REDMI NOTE 6 PRO" → marketing naam
        return True
    return any(h in m for h in _MKT_HINTS)


def _ddg_marketing_name(brand: str, model: str) -> str:
    """Model CODE (T528 / SM-A155F / CPH2605) se marketing naam nikalna.

    GSMArena Cloudflare-Turnstile se blocked hai aur nanoreview ka search 404
    deta hai, isliye DuckDuckGo HTML ke result-titles se naam lete hain:
        "Tecno T528 Specifications and Price | DroidAfrica" → "Tecno T528"
    Fail ho to "" (chain gracefully TAC par ruk jayegi).
    """
    key = f"{brand}|{model}".lower()
    with _LOCK:
        if key in _NAME_CACHE:
            return _NAME_CACHE[key]
    name = ""
    try:
        r = requests.post("https://html.duckduckgo.com/html/",
                          data={"q": f'"{model}" {brand} phone specifications'},
                          headers=_DDG_UA, timeout=8)
        if r.status_code == 200:
            for t in re.findall(r"result__a[^>]*>(.*?)</a>", r.text, re.S):
                t = re.sub(r"<[^>]+>", "", t).strip()
                if model.lower() not in t.lower() or not (6 <= len(t) <= 80):
                    continue
                cand = re.split(r"\s+(?:specifications?|specs?|price|review|full|"
                                r"dual|features|questions|–|-|\|)", t, flags=re.I)[0].strip()
                if (brand.split()[0].lower() in cand.lower()
                        and model.lower() in cand.lower() and len(cand) >= 6):
                    name = cand
                    break
    except Exception:                                        # noqa: BLE001
        name = ""
    with _LOCK:
        _NAME_CACHE[key] = name
        if len(_NAME_CACHE) > 400:
            for k in list(_NAME_CACHE)[:100]:
                _NAME_CACHE.pop(k, None)
    return name


def fetch_device_specs(name: str) -> dict:
    """`/api/device-specs?model=<marketing naam>` → {ok,name,image,url,sections}.

    Marketing naam par 0.3-0.6s; galat/code naam par timeout SPEC_TIMEOUT par
    ruk jata hai (result cache hota hai to dobara wait nahi).
    """
    key = (name or "").strip().lower()
    if not key:
        return {"ok": False}
    with _LOCK:
        hit = _SPEC_CACHE.get(key)
    if hit and (time.time() - hit[0]) < _SPEC_TTL:
        return dict(hit[1])
    out = {"ok": False}
    payload, _err = _get(f"{api_base()}/device-specs",
                         {"key": api_key(), "model": name}, tmo=SPEC_TIMEOUT)
    if isinstance(payload, dict) and payload.get("success") is not False \
            and (payload.get("sections") or payload.get("image")):
        secs = []
        for sec in (payload.get("sections") or []):
            if not isinstance(sec, dict):
                continue
            rows = []
            for kr in (sec.get("rows") or []):
                try:
                    k2, v2 = _clean_val(kr[0]), _clean_val(kr[1])
                except Exception:                            # noqa: BLE001
                    continue
                if k2 and v2:
                    rows.append((k2, v2))
            if rows:
                secs.append({"title": _clean_val(sec.get("title")) or "Specs",
                             "rows": rows})
        out = {"ok": bool(secs), "name": _clean_val(payload.get("name")),
               "image": str(payload.get("image") or "").strip(),
               "url": str(payload.get("url") or "").strip(),
               "sections": secs}
    with _LOCK:
        _SPEC_CACHE[key] = (time.time(), out)
        if len(_SPEC_CACHE) > 200:
            for k in sorted(_SPEC_CACHE, key=lambda x: _SPEC_CACHE[x][0])[:60]:
                _SPEC_CACHE.pop(k, None)
    return out


def _enrich_with_specs(res: dict) -> dict:
    """TAC-only IMEI result ko full spec sheet + photo se upgrade karo (v54)."""
    if not res.get("ok") or not res.get("basic"):
        return res
    brand = res.get("brand") or ""
    model = res.get("model") or ""
    if not (brand or model):
        return res
    # brand+model me brand dobara na aaye: hub kai baar model me hi brand bhej
    # deta hai ("XIAOMI" + "XIAOMI REDMI NOTE 6 PRO") → "XIAOMI XIAOMI ..." banta
    # tha jo nanoreview match hi nahi karta. Pehla word match ho to sirf model lo.
    b0 = brand.split()[0].lower() if brand.split() else ""
    if b0 and model.lower().startswith(b0):
        name = model.strip()
    else:
        name = f"{brand} {model}".strip()
    sp = fetch_device_specs(name) if _looks_marketing(model) else {"ok": False}
    if not sp.get("ok"):
        resolved = _ddg_marketing_name(brand, model)
        if resolved and resolved.lower() != name.lower():
            sp = fetch_device_specs(resolved)
            if sp.get("ok"):
                name = resolved
    if not sp.get("ok"):
        return res
    if sp.get("image") and not res.get("photo"):
        res["photo"] = sp["image"]
        res["photo_hd"] = sp["image"]
    if sp.get("sections"):
        res["sections"] = (res.get("sections") or []) + sp["sections"]
        res["basic"] = False
        res["specs_pending"] = False
    if sp.get("name"):
        res["specs_name"] = sp["name"]
    if sp.get("url"):
        res["specs_url"] = sp["url"]
        res["url"] = sp["url"]
        res["links"] = ([("🔎 Full specs page (nanoreview)", sp["url"])]
                        + (res.get("links") or []))[:6]
    res["_source"] = "hub TAC + device-specs chain"
    return res


# ---------------------------------------------------------------- fetch + cache
def fetch_imei_details(imei: str, use_cache: bool = True) -> dict:
    """IMEI → device details (cache ke saath). Wrong/unknown IMEI par clear error."""
    ok, clean, err = validate_imei(imei)
    safe_tac = (clean or clean_imei(imei))[:8]
    if not ok:
        return {"ok": False, "error": err, "imei": safe_tac, "tac": safe_tac}
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
        out = {"ok": False, "error": net_err or "API is not reachable right now.",
               "imei": safe_tac, "tac": safe_tac}
    else:
        out = parse_imei_payload(payload, clean)
        # v54: TAC-only result ho to full spec sheet + photo chain karo
        if out.get("ok"):
            out = _enrich_with_specs(out)

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
_NAME_FIXES = (
    ("Iphone", "iPhone"), ("Ipad", "iPad"), ("Ipod", "iPod"), ("Macbook", "MacBook"),
    ("Samsung", "Samsung"), ("Redmi", "Redmi"), ("Oneplus", "OnePlus"), ("Realme", "Realme"),
    ("Htc", "HTC"), ("Lg", "LG"), ("Asus", "Asus"), ("Lenovo", "Lenovo"), ("Oppo", "OPPO"),
    ("Vivo", "Vivo"), ("Xiaomi", "Xiaomi"), ("Poco", "POCO"), ("Nokia", "Nokia"),
    ("Huawei", "Huawei"), ("Honor", "Honor"), ("Infinix", "Infinix"), ("Tecno", "Tecno"),
    ("Mi ", "Mi "), ("4g", "4G"), ("5g", "5G"), ("Lte", "LTE"), ("Nfc", "NFC"),
)


def pretty_name(name: str) -> str:
    """'SAMSUNG GALAXY TAB A9+' → 'Samsung Galaxy Tab A9+' (DB me naam capital me hota hai)."""
    n = re.sub(r"\s+", " ", str(name or "")).strip()
    if not n:
        return ""
    letters = [c for c in n if c.isalpha()]
    if letters and sum(1 for c in letters if c.isupper()) / max(1, len(letters)) > 0.7:
        n = n.title()
    for a, b in _NAME_FIXES:
        n = n.replace(a, b)
    return n


def device_title(res: dict) -> str:
    b = _clean_val(res.get("brand"))
    m = _clean_val(res.get("model"))
    if b and m and b.lower() not in m.lower():
        return f"{pretty_name(b)} {m}".strip()
    return pretty_name(m or b or res.get("specs_name") or "Unknown device")


def _sec_icon(title: str) -> str:
    t = str(title or "").lower()
    for keys, icon in (
        (("device",), "📋"),
        (("design", "build", "dimension"), "📐"),
        (("software", "os", "android", "ios"), "🤖"),
        (("other", "misc"), "✨"),
        (("performance", "benchmark"), "⚙️"),
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
    lines = [f"📲 <b>{_hesc(device_title(res))}</b>"]
    if res.get("brand"):
        lines.append(f"🏷️ <b>Brand:</b> {_hesc(str(res['brand']))}")
    lines.append(f"🔢 <b>IMEI:</b> <code>{_hesc(str(res.get('imei') or '—'))}</code>")
    # top 5 sections ke 2-2 key points
    shown = 0
    for s in res.get("sections") or []:
        if shown >= 5:
            break
        if str(s.get("title") or "").strip().lower() in ("device", "basic", "general") and res.get("brand"):
            continue                    # brand/model upar already dikh rahe hain
        head = f"{_sec_icon(s['title'])} <b>{_hesc(str(s['title']))}</b>"
        rows = []
        for k, v in s["rows"][:2]:
            txt = f"• {k}: {v}"
            if len(txt) > 70:
                txt = txt[:69] + "…"
            rows.append(_hesc(txt))
        block = head + "\n" + "\n".join(rows)
        if len("\n".join(lines)) + len(block) + 60 > max_len:
            break
        lines.append(block)
        shown += 1
    if res.get("specs_rows"):
        lines.append(f"📊 <b>{res['specs_rows']} specification points found</b>")
    lines.append("👇 <i>Poori specification agle message me hai.</i>")
    out = "\n".join(lines)
    return out[:1024]


def render_text(res: dict, max_len: int = 3600) -> str:
    """Poora spec card (Telegram text message)."""
    if not res.get("ok"):
        return ""
    out = [
        f"📲 <b>{_hesc(device_title(res))}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🏷️ <b>Brand:</b> {_hesc(str(res.get('brand') or '—'))}",
        f"🔢 <b>IMEI:</b> <code>{_hesc(str(res.get('imei') or '—'))}</code>",
    ]
    for s in res.get("sections") or []:
        out.append("━━━━━━━━━━━━━━━━━━━━━━")
        out.append(f"{_sec_icon(s['title'])} <b>{_hesc(str(s['title']))}</b>")
        for k, v in s["rows"]:
            vv = str(v)
            if len(str(k)) + len(vv) + 6 > 120:
                vv = vv[:max(20, 114 - len(str(k)))] + "…"
            out.append(f"• <b>{_hesc(str(k))}:</b> {_hesc(vv)}")
        if len("\n".join(out)) > max_len:
            out.append("<i>…spec list lambi hai (poori copy neeche .json file me hai)</i>")
            break
    out.append("━━━━━━━━━━━━━━━━━━━━━━")
    if res.get("tac"):
        out.append(f"🔢 <b>TAC:</b> <code>{_hesc(str(res['tac']))}</code>")
    if res.get("specs_url"):
        out.append(f"🔎 <b>Specs page:</b> {_hesc(str(res['specs_url']))}")
    out.append(f"<i>Data: {_hesc(str(res.get('source_note') or 'TAC database + nanoreview.net'))}"
               " · confirm on the official brand site before buying/selling.</i>")
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
    dev_name = res.get("specs_name") or device_title(res)
    spec_url = res.get("specs_url") or res.get("url") or ""
    out = {
        "device": dev_name,
        "device_name": dev_name,
        "brand": res.get("brand") or "",
        "model": res.get("model") or "",
        "imei": res.get("imei") or "",
        "tac": res.get("tac") or "",
        "url": spec_url,
        "checked_at": res.get("checked_at") or datetime.now().strftime("%d-%m-%Y %H:%M"),
        "specifications": specs,
        "source": res.get("source_note") or "TAC database + nanoreview.net",
        "powered_by": "@Supermannn_x",
    }
    if res.get("photo"):
        out["device_image"] = res["photo"]
    if spec_url:
        out["specs_page"] = spec_url
    if res.get("specs_rows"):
        out["total_specs"] = res["specs_rows"]
    return out


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
        "Phone ka <b>15 digit IMEI</b> bhejo.\n"
        "📍 Kahan milega: phone me <code>*#06#</code> dial karo, ya box/bill dekho.\n"
        "✅ Milega: brand, model, <b>phone ki photo</b> + <b>poori spec sheet</b> "
        "(display, chipset, camera, battery, network) + <b><code>.json</code> file</b>.\n"
        "<i>Kisi bhi phone/tablet par chalega. Sirf legal use ke liye (apna phone ya jo kharid rahe ho).</i>"
    )
