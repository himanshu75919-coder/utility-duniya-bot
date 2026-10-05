# -*- coding: utf-8 -*-
"""
OSINT HUB CLIENT (v45)
======================
Utility Duniya Bot → aapka apna OSINT API Hub (https://osint-api-hub.onrender.com)

Safe lookup scope:
  📱 NUMBER INFO       →  sirf non-sensitive carrier/circle metadata (personal records disabled)
  🚗 VEHICLE + CHALLAN →  official links by default; live data only with an authorized provider
  🆔 AADHAAR FAMILY    →  consent/authorized source required; koi leaked data query nahi hota

ENV (Render → Environment):
  OSINT_API_BASE   = https://osint-api-hub.onrender.com/api   (default)
  OSINT_API_KEY    = Demo                                     (default — apni key daal do)
  OSINT_TIMEOUT    = 70  (seconds; hub slow hone par bhi kaam kare)
  OSINT_CACHE_TTL  = 300                                      (seconds)

Design rules (professional):
  • Har call me timeout + retry + saaf error (kabhi traceback user ko nahi dikhta)
  • 5 min cache — same query par dobara API call nahi (Render free sleep na kare)
  • "credit nahi katta" wala faisla bot karta hai: yahan se hamesha
    {"ok": True/False, "has_data": True/False, ...} aata hai, bot has_data dekh kar charge kare
"""

from __future__ import annotations

import os
import re
import threading
import time

import requests

DEFAULT_BASE = "https://osint-api-hub.onrender.com/api"
# Hub kabhi-kabhi 30-60s leta hai (upstream sources slow hote hain).
# Bot ab user ko beech-beech me progress dikhata hai, isliye timeout bada rakhte hain.
TIMEOUT = int(os.environ.get("OSINT_TIMEOUT", "70"))
CACHE_TTL = int(os.environ.get("OSINT_CACHE_TTL", "300"))
_FAIL_TTL = 45          # fail wali query ko itni der dobara try nahi karenge

_CACHE: dict = {}
_LOCK = threading.Lock()

UA_HEADERS = {"User-Agent": "UtilityDuniyaBot/1.0", "Accept": "application/json"}


# ------------------------------------------------------------------ config
def api_base() -> str:
    b = (os.environ.get("OSINT_API_BASE") or "").strip().rstrip("/")
    return b or DEFAULT_BASE


def api_key() -> str:
    return (os.environ.get("OSINT_API_KEY") or "Demo").strip() or "Demo"


def vehicle_api_base() -> str:
    b = (os.environ.get("VEHICLE_API_BASE") or "").strip().rstrip("/")
    if not b:
        return ""
    if not b.lower().endswith("/api"):
        b += "/api"
    return b


def is_configured() -> bool:
    """Live vehicle data is off unless an authorized provider is explicitly configured."""
    authorized = os.environ.get("VEHICLE_PROVIDER_AUTHORIZED", "0").strip().lower()
    return authorized in ("1", "true", "yes") and bool(vehicle_api_base())


# ------------------------------------------------------------------ cache
def _cache_get(key: str):
    with _LOCK:
        hit = _CACHE.get(key)
    if not hit:
        return None
    val, ts, ttl = hit
    if time.time() - ts > ttl:
        return None
    return val


def _cache_put(key: str, val, ttl: int = CACHE_TTL):
    with _LOCK:
        _CACHE[key] = (val, time.time(), ttl)


def cache_clear():
    with _LOCK:
        _CACHE.clear()


# ------------------------------------------------------------------ http
def hub_get(path: str, params: dict, tmo: int | None = None, tries: int = 2,
            base_override: str | None = None, key_override: str | None = None):
    """Configured API ko call karo → (json|None, error|None)."""
    base = (base_override or api_base()).rstrip("/")
    url = f"{base}/{path.lstrip('/')}"
    p = dict(params or {})
    p.setdefault("key", key_override or api_key())
    last_err = "The API did not answer."
    for attempt in range(max(1, tries)):
        try:
            r = requests.get(url, params=p, headers=UA_HEADERS,
                             timeout=tmo or TIMEOUT)
        except requests.Timeout:
            last_err = "The API took too long to answer."
            time.sleep(0.4)
            continue
        except Exception as e:                                   # noqa: BLE001
            last_err = f"Could not reach the API: {str(e)[:80]}"
            time.sleep(0.4)
            continue
        if r.status_code == 429:
            last_err = "API rate limit — please try again in a minute."
            time.sleep(1.0)
            continue
        if r.status_code != 200:
            return None, f"API returned HTTP {r.status_code}."
        try:
            return r.json(), None
        except Exception:                                        # noqa: BLE001
            return None, "The API did not send JSON."
    return None, last_err


def _err_of(payload) -> str:
    """Hub ke jawab se saaf error line nikaalo (agar ho)."""
    if not isinstance(payload, dict):
        return ""
    for k in ("error", "detail", "message", "msg"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip() and v.strip().lower() not in ("none", "null"):
            return v.strip()[:160]
        if isinstance(v, dict):
            d = v.get("error") or v.get("message") or v.get("detail")
            if isinstance(d, str) and d.strip():
                return d.strip()[:160]
    return ""


def _clean(v) -> str:
    s = str(v if v is not None else "").strip()
    return "" if s.lower() in ("", "none", "null", "na", "n/a", "-", "nan") else s


# ===================================================================
#  1) NUMBER INFO
# ===================================================================
def num_info_report(number: str) -> dict:
    """Personal-record lookup band kar diya gaya hai; koi number OSINT hub par nahi jata."""
    return {
        "ok": False,
        "has_data": False,
        "disabled": True,
        "error": "Privacy ke liye leaked personal records retrieve nahi hote. Sirf safe phone metadata available hai.",
    }


# ===================================================================
#  2) VEHICLE INFO + CHALLAN
# ===================================================================
def _rc_from_hub(d: dict, plate: str) -> dict:
    """Hub ka naya /api/vehicle-report → vehicle_challan wala internal rc dict."""
    veh = d.get("vehicle") or {}
    own = d.get("owner") or {}
    rto = d.get("rto") or {}
    rc = d.get("rc") or {}
    ins = d.get("insurance") or {}
    puc = d.get("puc") or {}
    return {
        "plate": _clean(rc.get("registration_number")) or plate,
        "maker": _clean(veh.get("maker")),
        "model": _clean(veh.get("model")) or _clean(veh.get("maker_model")),
        "vehicle_class": _clean(veh.get("vehicle_class")),
        "fuel": _clean(veh.get("fuel")),
        "cc": _clean(veh.get("cubic_capacity")),
        "chassis": "",
        "engine": "",
        "emission": _clean(veh.get("fuel_norms")),
        "seating": _clean(veh.get("seating_capacity")),
        "owner": _clean(own.get("owner_name")),
        "owner_serial": "",
        "rto": _clean(rto.get("registered_rto")),
        "city": _clean(rto.get("city_name")),
        "rto_phone": _clean(rto.get("phone")),
        "rto_website": _clean(rto.get("website")),
        "rto_address": _clean(rto.get("address")),
        "reg_date": _clean(rc.get("registration_date")),
        "fitness_upto": _clean(rc.get("fitness_upto")),
        "tax_upto": _clean(rc.get("tax_upto")),
        "vehicle_age": _clean(rc.get("vehicle_age")),
        "ins_company": _clean(ins.get("company")),
        "ins_no": "",
        "ins_upto": _clean(ins.get("expiry")) or _clean(rc.get("insurance_upto")),
        "ins_status": _clean(ins.get("status")),
        "ins_remaining": _clean(ins.get("validity")) or _clean(rc.get("insurance_expiry_in")),
        "puc_no": "",
        "puc_upto": _clean(puc.get("upto")),
        "puc_remaining": _clean(puc.get("status")),
        "blacklist": _clean(own.get("blacklist_status")),
        "financer": _clean(own.get("financer")),
        "noc": _clean(own.get("noc")),
        "permit": _clean(own.get("permit_type")),
        "_source": "vehicle-report (hub v2)",
    }


def vehicle_report_v2(plate: str) -> dict:
    """
    Naya hub endpoint /api/vehicle-report → vehicle_challan wala shape:
    {"ok":True, "plate":…, "rc":{…}, "challans":[…], "summary":{…}, "sources":[…], "cached":bool}
    """
    plate_c = re.sub(r"[^A-Za-z0-9]", "", str(plate or "")).upper()
    if not plate_c:
        return {"ok": False, "error": "Number plate nahi mila.", "fallback": True}
    if not is_configured():
        return {"ok": False, "has_data": False, "fallback": True,
                "error": "Authorized vehicle/challan provider configured nahi hai. Official Parivahan/e-Challan portal use karein."}

    ck = f"veh2:{plate_c}"
    hit = _cache_get(ck)
    if hit is not None:
        return {**hit, "cached": True}

    payload, err = hub_get(
        "vehicle-report", {"q": plate_c, "format": "json"},
        base_override=vehicle_api_base(),
        key_override=(os.environ.get("VEHICLE_API_KEY") or "Demo").strip(),
    )
    if err:
        res = {"ok": False, "error": err, "fallback": True}
        _cache_put(ck, res, _FAIL_TTL)
        return res
    if not isinstance(payload, dict) or not payload.get("success", True):
        res = {"ok": False, "error": _err_of(payload) or "Is number ka koi record nahi mila.",
               "fallback": True}
        _cache_put(ck, res, _FAIL_TTL)
        return res

    rc = _rc_from_hub(payload, plate_c)
    ch = payload.get("challans") or {}
    challans = [c for c in (ch.get("list") or []) if isinstance(c, dict)]
    count = int(ch.get("count") or len(challans) or 0)
    pending = int(ch.get("pending_count") or 0)
    paid = int(ch.get("disposed_count") or 0)
    other = max(count - pending - paid, 0)

    def _n(v):
        try:
            return float(re.sub(r"[^\d.]", "", str(v)) or 0)
        except Exception:                                        # noqa: BLE001
            return 0.0

    summary = {
        "count": count, "pending": pending, "paid": paid, "other": other,
        "total_amount": _n(ch.get("total_amount")),
        "pending_amount": _n(ch.get("pending_amount")),
        "from_summary_api": True,
    }

    has_data = any(rc.get(k) for k in ("maker", "model", "owner", "reg_date", "ins_company")) \
        or bool(challans) or bool(count)
    res = {"ok": True, "plate": plate_c, "rc": rc, "challans": challans,
           "summary": summary, "has_data": has_data,
           "sources": [str(s) for s in (payload.get("sources_used") or [])] or ["vehicle-report"],
           "cached": False}
    _cache_put(ck, res)
    return res


# ===================================================================
#  3) AADHAAR FAMILY
# ===================================================================
def aadhaar_family_report(aadhaar: str) -> dict:
    """Retired: Aadhaar/family information is not queried from leaked datasets."""
    return {
        "ok": False,
        "has_data": False,
        "disabled": True,
        "error": "Aadhaar-family lookup yahan supported nahi. Apne records ke liye UIDAI/NFSA ke official, consent-based portal ka use karein.",
    }


# ===================================================================
#  ADMIN: /hubstatus — health endpoint only; no personal-ID test
# ===================================================================
def hub_status(sample_plate: str = "", sample_number: str = "") -> str:
    """Hub health check only; it never submits a phone, vehicle plate or Aadhaar."""
    from html import escape as _e

    base = api_base().rstrip("/")
    root = base[:-4] if base.lower().endswith("/api") else base
    health_url = f"{root}/health"
    status_line = "❌ Hub health endpoint se contact nahi ho paya."
    version = ""
    try:
        response = requests.get(health_url, headers=UA_HEADERS, timeout=min(TIMEOUT, 20))
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                data = {}
            status_line = "✅ Hub health: HTTP 200"
            version = str(data.get("version") or "")
        else:
            status_line = f"❌ Hub health: HTTP {response.status_code}"
    except Exception as exc:
        status_line = f"❌ {_e(str(exc)[:100])}"

    lines = [
        "🔌 <b>OSINT HUB STATUS</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🌐 <b>Health URL:</b> <code>{_e(health_url)}</code>",
        status_line,
    ]
    if version:
        lines.append(f"📦 <b>Version:</b> {_e(version)}")
    lines.extend([
        "",
        "📱 Number personal-record lookup: <b>disabled</b> (koi number query nahi hua)",
        "🚗 Vehicle/challan lookup: <b>not tested</b> (authorized provider zaroori)",
        "🆔 Aadhaar lookup: <b>not tested</b> (consent/authorized source zaroori)",
        "",
        f"⚡ <i>Powered by {_e(os.environ.get('BRAND_TAG', '@Supermannn_x'))}</i>",
    ])
    return "\n".join(lines)


# ⚠️ v55: yahan pehle ek `e()` helper tha (bot.py ke hesc() jaisa HTML-escape),
# par wo kahin use nahi hota tha — dead code hata diya. HTML escaping ke liye
# bot.py ka `hesc()` ya modules.api_hub ka `hesc()` use karo.
