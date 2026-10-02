# -*- coding: utf-8 -*-
"""
OSINT HUB CLIENT (v45)
======================
Utility Duniya Bot → aapka apna OSINT API Hub (https://osint-api-hub.onrender.com)

Ek hi jagah se 3 bade tools chalte hain:
  📱 NUMBER INFO       →  /api/num-info        (naam, father, address, alt numbers, IDs)
  🚗 VEHICLE + CHALLAN →  /api/vehicle-report  (RC + insurance + PUC + challan)
  🆔 AADHAAR FAMILY    →  /api/aadhaar-family  (family members + district, masked Aadhaar)

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
from html import escape

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


def is_configured() -> bool:
    return bool(api_base())


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
def hub_get(path: str, params: dict, tmo: int | None = None, tries: int = 2):
    """Hub ko call karo → (json|None, error|None). Kabhi exception nahi phenkta."""
    url = f"{api_base()}/{path.lstrip('/')}"
    p = dict(params or {})
    p.setdefault("key", api_key())
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
    """
    /api/num-info → saaf dict.
    {"ok":True, "has_data":True, "people":[{name, father_name, phones[], alt_phones[],
      govt_ids[], emails[], addresses[], region}], "record_count":n, "sources":[], "cached":bool}
    Fail: {"ok":False, "error":..., "has_data":False}
    """
    digits = re.sub(r"\D", "", str(number or ""))
    if len(digits) < 8:
        return {"ok": False, "has_data": False, "error": "Please send a valid 10 digit mobile number."}
    q = digits[-10:] if len(digits) >= 10 else digits

    ck = f"num:{q}"
    hit = _cache_get(ck)
    if hit is not None:
        return {**hit, "cached": True}

    payload, err = hub_get("num-info", {"q": q, "format": "json"})
    if err:
        res = {"ok": False, "has_data": False, "error": err}
        _cache_put(ck, res, _FAIL_TTL)
        return res
    if not isinstance(payload, dict) or not payload.get("success", True):
        res = {"ok": False, "has_data": False, "error": _err_of(payload) or "No record found."}
        _cache_put(ck, res, _FAIL_TTL)
        return res

    people = []
    for p in (payload.get("people") or []):
        if not isinstance(p, dict):
            continue
        phones = [x for x in (_clean(y) for y in (p.get("phones") or [])) if x]
        alts = [x for x in (_clean(y) for y in (p.get("alt_phones") or [])) if x]
        for a in alts:
            if a not in phones:
                phones.append(a)
        ids = [x for x in (_clean(y) for y in (p.get("govt_ids") or [])) if x]
        mails = [x for x in (_clean(y) for y in (p.get("emails") or [])) if x]
        addrs = [x for x in (_clean(y) for y in (p.get("addresses") or [])) if x]
        name = _clean(p.get("name"))
        father = _clean(p.get("father_name"))
        if not name and not father and not addrs and not phones:
            continue
        people.append({
            "name": name, "father_name": father,
            "phones": phones, "alt_phones": alts,
            "govt_ids": ids, "emails": mails, "addresses": addrs,
            "region": _clean(p.get("region")),
            "sources": [str(s) for s in (p.get("sources") or [])],
            "record_count": int(p.get("record_count") or 0),
        })

    has_data = any(p.get("name") or p.get("addresses") or len(p.get("phones") or []) > 1
                   or p.get("govt_ids") for p in people)
    res = {"ok": True, "has_data": has_data, "people": people,
           "record_count": int(payload.get("record_count") or len(people)),
           "query": q, "sources": [str(s) for s in (payload.get("sources_used") or [])],
           "cached": False, "error": ""}
    _cache_put(ck, res)
    return res


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
        return {"ok": False, "error": "No number plate given.", "fallback": True}

    ck = f"veh2:{plate_c}"
    hit = _cache_get(ck)
    if hit is not None:
        return {**hit, "cached": True}

    payload, err = hub_get("vehicle-report", {"q": plate_c, "format": "json"})
    if err:
        res = {"ok": False, "error": err, "fallback": True}
        _cache_put(ck, res, _FAIL_TTL)
        return res
    if not isinstance(payload, dict) or not payload.get("success", True):
        res = {"ok": False, "error": _err_of(payload) or "No record found for this number.",
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
    """
    /api/aadhaar-family → saaf dict.
    {"ok":True, "has_data":True, "aadhaar_masked":…, "valid":bool, "primary":{…},
     "members":[{name, aadhaar_masked, relation, father_name, phones[], address}],
     "member_count":n, "location":{district,state,pincode}, "ration_card":…, "fps_id":…}
    """
    digits = re.sub(r"\D", "", str(aadhaar or ""))
    if len(digits) != 12:
        return {"ok": False, "has_data": False,
                "error": "Aadhaar number must be exactly 12 digits."}

    ck = f"aadhaar:{digits}"
    hit = _cache_get(ck)
    if hit is not None:
        return {**hit, "cached": True}

    payload, err = hub_get("aadhaar-family", {"aadhaar": digits, "format": "json"})
    if err:
        res = {"ok": False, "has_data": False, "error": err}
        _cache_put(ck, res, _FAIL_TTL)
        return res
    if not isinstance(payload, dict) or not payload.get("success", True):
        res = {"ok": False, "has_data": False, "error": _err_of(payload) or "No record found."}
        _cache_put(ck, res, _FAIL_TTL)
        return res

    members = []
    for m in (payload.get("members") or []):
        if not isinstance(m, dict):
            continue
        phones = [x for x in (_clean(y) for y in (m.get("phones") or [])) if x]
        members.append({
            "name": _clean(m.get("name")),
            "aadhaar_masked": _clean(m.get("aadhaar_masked")),
            "relation": _clean(m.get("relation")),
            "father_name": _clean(m.get("father_name")),
            "phones": phones,
            "address": _clean(m.get("address")),
        })
    if not members:
        prim = payload.get("primary") or {}
        if isinstance(prim, dict) and _clean(prim.get("name")):
            members = [{
                "name": _clean(prim.get("name")),
                "aadhaar_masked": _clean(payload.get("aadhaar_masked")),
                "relation": "searched Aadhaar holder",
                "father_name": _clean(prim.get("father_name")),
                "phones": [x for x in (_clean(y) for y in (prim.get("phones") or [])) if x],
                "address": _clean((prim.get("addresses") or [""])[0]) if isinstance(prim.get("addresses"), list) else "",
            }]

    loc = payload.get("location") or {}
    res = {
        "ok": True,
        "has_data": bool(members),
        "aadhaar_masked": _clean(payload.get("aadhaar_masked")),
        "valid": bool(payload.get("aadhaar_valid_checksum")),
        "primary": payload.get("primary") or {},
        "members": members,
        "member_count": int(payload.get("member_count") or len(members)),
        "location": {
            "district": _clean(loc.get("district")),
            "state": _clean(loc.get("state")),
            "pincode": _clean(loc.get("pincode")),
        },
        "ration_card": _clean(payload.get("ration_card_number")),
        "fps_id": _clean(payload.get("fps_id")),
        "sources": [str(s) for s in (payload.get("sources_used") or [])],
        "note": _clean(payload.get("note")),
        "cached": False, "error": "",
    }
    _cache_put(ck, res)
    return res


# ===================================================================
#  ADMIN: /hubstatus — teeno API ka live test
# ===================================================================
def hub_status(sample_plate: str = "BR30AR0802", sample_number: str = "9058390341") -> str:
    from html import escape as _e
    lines = ["🔌 <b>OSINT HUB STATUS</b>", "━━━━━━━━━━━━━━━━━━━━━━",
             f"🌐 <b>Base:</b> <code>{_e(api_base())}</code>",
             f"🔑 <b>Key:</b> <code>{_e(api_key()[:6] + '…' + api_key()[-3:] if len(api_key()) > 10 else api_key())}</code>",
             f"⏱️ <b>Timeout:</b> {TIMEOUT}s", ""]
    t0 = time.time()
    p, err = hub_get("num-info", {"q": sample_number, "format": "json"}, tmo=min(TIMEOUT, 40))
    lines.append(f"📱 <b>num-info:</b> {'✅ OK' if p else '❌ ' + _e(err or 'fail')}"
                 + (f" — {len((p or {}).get('people') or [])} person" if p else ""))
    p2, err2 = hub_get("vehicle-report", {"q": sample_plate, "format": "json"}, tmo=min(TIMEOUT, 40))
    lines.append(f"🚗 <b>vehicle-report:</b> {'✅ OK' if p2 else '❌ ' + _e(err2 or 'fail')}"
                 + (f" — {(((p2 or {}).get('challans') or {}).get('count'))} challan" if p2 else ""))
    p3, err3 = hub_get("aadhaar-family", {"aadhaar": "861313813129", "format": "json"},
                       tmo=min(TIMEOUT, 40), tries=1)
    lines.append(f"🆔 <b>aadhaar-family:</b> {'✅ OK' if p3 else '❌ ' + _e(err3 or 'fail')}"
                 + (f" — {(p3 or {}).get('member_count')} members" if p3 else ""))
    lines.append("")
    lines.append(f"⏱️ <b>Total time:</b> {round(time.time() - t0, 1)}s")
    lines.append(f"⚡ <i>Powered by {_e(os.environ.get('BRAND_TAG', '@Supermannn_x'))}</i>")
    return "\n".join(lines)


def e(v) -> str:
    """bot.py ke hesc() jaisa — HTML safe."""
    return escape(str(v if v is not None else ""))
