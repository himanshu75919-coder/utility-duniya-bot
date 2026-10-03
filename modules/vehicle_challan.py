# -*- coding: utf-8 -*-
"""
Vehicle Info + Challan Report (v41)
===================================
Ek number plate → poora RC record + saare challan (pending / paid / court).

Kahan se data aata hai (teen engine, sabse best merge hota hai):
  1) /api/vehicle-rc            → RC sections: dates, insurance, PUC, owner, RTO, vehicle
  2) /api/vehicle-challan       → challan list (ULIP e-Challan): number, amount, date, offence, court
  3) /api/vehicle-challan-v4    → summary: total challans + total amount (pending vs disposed)

Default base: https://osint-api-hub.onrender.com/api   (key: HUB_API_KEY / VEHICLE_API_KEY, default Demo)
ENV (Render → Environment):
  VEHICLE_API_BASE   = API host + /api   (default upar wala)
  VEHICLE_API_KEY    = apni key          (default: HUB_API_KEY, warna Demo — jo ab invalid hai)
  VEHICLE_API_URL    = (optional) purani single-endpoint API (ProPortalx style)
  VEHICLE_TIMEOUT    = seconds (default 25)

Privacy (default ON): owner naam, chassis/engine, insurance-PUC numbers **mask** hote hain.
Poora dikhana ho: VEHICLE_SHOW_MOBILE=1 · VEHICLE_SHOW_IDS=1 · VEHICLE_SHOW_OWNER=1
"""

from __future__ import annotations

import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html import escape

import requests

DEFAULT_BASE = "https://osint-api-hub.onrender.com/api"   # v49: naya LIVE hub (purana dead tha)
TIMEOUT = int(os.environ.get("VEHICLE_TIMEOUT", "25"))
CACHE_TTL = 300          # 5 minute — user dobara check kare to dobara paisa/API call na lage
_FAIL_TTL = 60

_CACHE: dict = {}
_LOCK = threading.Lock()

UA_HEADERS = {"User-Agent": "UtilityDuniyaBot/1.0", "Accept": "application/json"}


# ---------------------------------------------------------------- config
def api_base() -> str:
    b = (os.environ.get("VEHICLE_API_BASE") or "").strip()
    if b:
        return b.rstrip("/")
    # purana VEHICLE_API_URL (single endpoint) set ho aur base na ho → usi host ka /api nikaal lo
    old = (os.environ.get("VEHICLE_API_URL") or "").strip()
    if old:
        m = re.match(r"^(https?://[^/]+/api)", old)
        if m:
            return m.group(1)
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
    return (os.environ.get("VEHICLE_API_KEY") or os.environ.get("VEHICLE_API_TOKEN") or "Demo").strip()


def custom_url() -> str:
    """Purani single-endpoint API (ProPortalx jaisi) — optional."""
    u = (os.environ.get("VEHICLE_API_URL") or "").strip()
    return u if u and "/api/vehicle-" not in u else ""


def is_configured() -> bool:
    return bool(api_base() or custom_url())


def clean_plate(plate: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", plate or "").upper()


def valid_plate(plate: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{1,4}$", clean_plate(plate)))


# ---------------------------------------------------------------- masking
def mask_mobile(num: str) -> str:
    if os.environ.get("VEHICLE_SHOW_MOBILE") == "1":
        return str(num)
    d = re.sub(r"\D", "", str(num or ""))
    if len(d) < 4:
        return str(num or "-")
    return "•" * max(len(d) - 4, 0) + d[-4:]


def mask_id(val: str) -> str:
    if os.environ.get("VEHICLE_SHOW_IDS") == "1":
        return str(val)
    s = str(val or "").strip()
    if len(s) < 8:
        return s or "-"
    tail = 3 if s.upper().endswith("XXXXX") is False else 0   # API ne khud mask kiya ho to waisa hi rakho
    return f"{s[:6]}{'*' * max(len(s) - 9, 3)}{s[-tail:]}" if tail else f"{s[:6]}{'*' * min(max(len(s) - 6, 4), 12)}"


def mask_name(name: str) -> str:
    """R****T K***R style — jaise official portals dikhate hain."""
    if os.environ.get("VEHICLE_SHOW_OWNER") == "1":
        return str(name or "-")
    out = []
    for word in str(name or "").split():
        if len(word) <= 2:
            out.append(word)
        else:
            out.append(word[0] + "*" * (len(word) - 2) + word[-1])
    return " ".join(out) or "-"


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
    """API ke andar chhupa error message nikalta hai."""
    if not isinstance(payload, dict):
        return ""
    for k in ("error", "errorMsg", "message", "msg", "detail"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:120]
    if payload.get("success") is False and not payload.get("data"):
        return "Is number ka koi record nahi mila."
    return ""


# ---------------------------------------------------------------- hub sources
def _hub_rc(base: str, key: str, plate: str):
    return _get(f"{base}/vehicle-rc", {"key": key, "number": plate})


def _hub_challans(base: str, key: str, plate: str):
    return _get(f"{base}/vehicle-challan", {"key": key, "number": plate})


def _hub_summary(base: str, key: str, plate: str):
    return _get(f"{base}/vehicle-challan-v4", {"key": key, "number": plate})


# ---------------------------------------------------------------- normalizing
def _flat(d: dict) -> dict:
    """Nested dict ko nested-through flat kar deta hai (sections.vehicle_details.X)."""
    out = {}

    def walk(node, pre=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, dict):
                    walk(v, pre)
                elif isinstance(v, list):
                    continue
                else:
                    out[f"{pre}{k}".strip()] = v
        return out

    walk(d or {})
    return out


def _pick(flat: dict, *names, default="") -> str:
    nd = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in (flat or {}).items()}
    for n in names:
        k = re.sub(r"[^a-z0-9]", "", n.lower())
        if k in nd and str(nd[k]).strip() not in ("", "-", "None", "NA", "N/A"):
            return str(nd[k]).strip()
    for k, v in nd.items():
        for n in names:
            nn = re.sub(r"[^a-z0-9]", "", n.lower())
            if (nn and (nn in k or k in nn)) and str(v).strip() not in ("", "-", "None", "NA", "N/A"):
                return str(v).strip()
    return default


def normalize_hub_rc(payload) -> dict:
    """vehicle-rc ka jawab → ek flat, saaf dict (render isi par chalta hai)."""
    data = (payload or {}).get("data") or {}
    sec = data.get("sections") or {}
    vinfo = data.get("vehicle_info") or {}
    if not sec and not vinfo:
        return {}

    veh = _flat(sec.get("vehicle_details") or {})
    own = _flat(sec.get("ownership_details") or {})
    dates = _flat(sec.get("important_dates") or {})
    ins = _flat(sec.get("insurance_information") or {})
    other = _flat(sec.get("other_information") or {})

    return {
        "plate": (vinfo.get("vehicle_number") or own.get("Registration Number") or "").upper(),
        "maker": _pick(veh, "Model Name") or "",                 # hub me "Model Name" = company
        "model": _pick(veh, "Maker Model") or "",
        "vehicle_class": _pick(veh, "Vehicle Class"),
        "fuel": _pick(veh, "Fuel Type"),
        "cc": _pick(veh, "Cubic Capacity") or _pick(other, "Cubic Capacity"),
        "chassis": _pick(veh, "Chassis Number"),
        "engine": _pick(veh, "Engine Number"),
        "emission": _pick(veh, "Fuel Norms"),
        "seating": _pick(other, "Seating Capacity"),
        "owner": _pick(own, "Owner Name"),
        "owner_serial": _pick(own, "Owner Serial No"),
        "rto": _pick(own, "Registered RTO") or vinfo.get("rto") or "",
        "city": str(vinfo.get("city_name") or ""),
        "rto_phone": str(vinfo.get("phone") or ""),
        "rto_website": str(vinfo.get("website") or ""),
        "rto_address": str(vinfo.get("address") or ""),
        "reg_date": _pick(dates, "Registration Date"),
        "fitness_upto": _pick(dates, "Fitness Upto"),
        "tax_upto": _pick(dates, "Tax Upto"),
        "vehicle_age": _pick(dates, "Vehicle Age"),
        "ins_company": _pick(ins, "Insurance Company"),
        "ins_no": _pick(ins, "Insurance No"),
        "ins_upto": _pick(ins, "Insurance Upto", "Insurance Expiry"),
        "ins_status": _pick(ins, "Insurance Status"),
        "ins_remaining": _pick(ins, "Insurance Validity", "Insurance Expiry In"),
        "puc_no": _pick(dates, "PUC No"),
        "puc_upto": _pick(dates, "PUC Upto"),
        "puc_remaining": _pick(dates, "PUC Expiry In"),
        "blacklist": _pick(other, "Blacklist Status"),
        "financer": _pick(other, "Financer Name"),
        "noc": _pick(other, "NOC Details"),
        "permit": _pick(other, "Permit Type"),
        "_source": "vehicle-rc",
    }


def normalize_flat_rc(rc: dict, plate: str = "") -> dict:
    """Purani (ProPortalx jaisi) flat API → same saaf dict."""
    f = _flat(rc or {})
    maker = _pick(f, "maker name", "maker", "manufacturer", "make")
    model = _pick(f, "model name", "model")
    return {
        "plate": (plate or _pick(f, "registration number", "vehicle number")).upper(),
        "maker": maker, "model": model,
        "vehicle_class": _pick(f, "vehicle class"),
        "fuel": _pick(f, "fuel type", "fuel"),
        "cc": _pick(f, "cubic capacity"),
        "chassis": _pick(f, "chassis number", "chassis"),
        "engine": _pick(f, "engine number", "engine"),
        "emission": _pick(f, "emission norms", "emission"),
        "seating": _pick(f, "seating capacity"),
        "owner": _pick(f, "owner name", "owner"),
        "owner_serial": _pick(f, "owner serial", "owner sr"),
        "rto": _pick(f, "registration authority", "rto", "office code"),
        "city": "", "rto_phone": "", "rto_website": "", "rto_address": "",
        "reg_date": _pick(f, "registration date", "reg date"),
        "fitness_upto": _pick(f, "fitness upto", "fitness validity"),
        "tax_upto": _pick(f, "tax upto", "tax"),
        "vehicle_age": "",
        "ins_company": _pick(f, "insurance company", "insurer"),
        "ins_no": _pick(f, "insurance no", "policy no"),
        "ins_upto": _pick(f, "insurance validity", "insurance upto"),
        "ins_status": "", "ins_remaining": "",
        "puc_no": _pick(f, "pucc no", "puc no"),
        "puc_upto": _pick(f, "pucc upto", "puc upto"),
        "puc_remaining": "",
        "blacklist": "", "financer": _pick(f, "hypothecation bank", "financer"),
        "noc": "", "permit": "",
        "colour": _pick(f, "color", "colour"),
        "body": _pick(f, "body type"),
        "mfg_year": _pick(f, "manufacture year", "manufacturing year"),
        "mob": _pick(f, "owner mobile", "mobile", "phone"),
        "_source": "custom API",
    }


# ---------------------------------------------------------------- challans
CHALLAN_KEYS = {
    "number": ("challannumber", "challanno", "chalanumber", "challanid", "referenceno", "id"),
    "accused": ("accusedname", "accused", "name", "ownername", "driver"),
    "amount": ("amount", "fine", "fineamount", "penalty", "totalamount", "challanamount"),
    "date": ("challandate", "date", "offencedate", "issuedate"),
    "status": ("challanstatus", "status", "paymentstatus"),
    "offence": ("offensedetails", "offence", "offense", "offencename", "violation", "violationname"),
    "place": ("challanplace", "place", "location", "offenceplace", "rto", "district"),
    "court": ("courtname", "court"),
}
RC_ONLY_WORDS = ("registration", "engine", "chassis", "vehicle", "maker", "model", "fuel",
                 "insurance", "pucc", "tax", "seating", "hypothecation", "colour", "color", "fitness")


def _nk(d: dict) -> dict:
    return {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in (d or {}).items()}


def _challan_from_dict(d: dict, want: str):
    nd = _nk(d)
    for k in CHALLAN_KEYS[want]:
        if k in nd and str(nd[k]).strip() not in ("", "-", "None"):
            return nd[k]
    for k, v in nd.items():
        if isinstance(v, (dict, list)) or str(v).strip() in ("", "-", "None"):
            continue
        if any(w in k for w in RC_ONLY_WORDS) and want in ("number", "amount", "date"):
            continue
        for w in CHALLAN_KEYS[want]:
            if k.startswith(w) or (k.endswith(w) and len(w) > 5):
                return v
    return None


def _looks_like_challan(d) -> bool:
    if not isinstance(d, dict):
        return False
    nk = list(_nk(d).keys())
    if any(w in k for k in nk for w in RC_ONLY_WORDS):
        return False
    marks = 0
    for w in ("challannumber", "challanno", "challanid", "amount", "fine", "penalty",
              "challandate", "challanstatus", "offence", "offense", "violation", "accused"):
        if any(w in k for k in nk):
            marks += 1
    return marks >= 2


def find_challans(payload, key_hint: str = "challan") -> list:
    """Kisi bhi format se challan list nikal leta hai."""
    rows = []

    def walk(node):
        if isinstance(node, dict):
            nk = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in node.items()}
            if any(key_hint in k for k in nk) or any("challan" in k for k in nk):
                for k, v in nk.items():
                    if isinstance(v, list):
                        rows.extend([it for it in v if _looks_like_challan(it)])
                    elif isinstance(v, dict):
                        inner = [x for x in v.values() if isinstance(x, list)]
                        added = False
                        for lst in inner:
                            got = [it for it in lst if _looks_like_challan(it)]
                            if got:
                                rows.extend(got); added = True
                        if not added and _looks_like_challan(v):
                            rows.append(v)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(payload)
    seen, out = set(), []
    for r in rows:
        k = f"{_challan_from_dict(r, 'number')}|{_challan_from_dict(r, 'amount')}|{_challan_from_dict(r, 'date')}"
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def _num(v):
    try:
        return float(re.sub(r"[^\d.]", "", str(v)) or 0)
    except Exception:
        return 0.0


def challan_summary(challans: list) -> dict:
    total_amt = pend_amt = 0.0
    pend = paid = other = 0
    for c in challans:
        amt = _num(_challan_from_dict(c, "amount"))
        total_amt += amt
        st = str(_challan_from_dict(c, "status") or "").lower()
        if any(w in st for w in ("pending", "unpaid", "due", "not paid", "open")):
            pend += 1; pend_amt += amt
        elif any(w in st for w in ("paid", "disposed", "closed", "success")):
            paid += 1
        else:
            other += 1
    return {"count": len(challans), "pending": pend, "paid": paid, "other": other,
            "total_amount": total_amt, "pending_amount": pend_amt}


# ---------------------------------------------------------------- main fetch
def _cache_get(plate):
    with _LOCK:
        hit = _CACHE.get(plate)
    if not hit:
        return None
    res, ts, ttl = hit
    if time.time() - ts > ttl:
        return None
    return res


def _cache_put(plate, res, ttl=CACHE_TTL):
    with _LOCK:
        _CACHE[plate] = (res, time.time(), ttl)


def _report_from_hub_full(plate_c: str, vr: dict) -> dict:
    """Hub ka /vehicle-report (vehicle/owner/rto/rc/insurance/puc/challans) → hamara shape."""
    veh, own, rto = vr.get("vehicle") or {}, vr.get("owner") or {}, vr.get("rto") or {}
    rc, ins, puc = vr.get("rc") or {}, vr.get("insurance") or {}, vr.get("puc") or {}
    ch = vr.get("challans") or {}

    def g(d, *ks, default=""):
        for k in ks:
            if isinstance(d, dict) and d.get(k) not in (None, "", [], {}):
                return d[k]
        return default

    rc_norm = {
        "maker": str(g(veh, "maker", "maker_model", "makerModel")),
        "model": str(g(veh, "model", "maker_model", "makerModel")),
        "vehicle_class": str(g(veh, "class", "vehicle_class", "vehicleClass")),
        "fuel": str(g(veh, "fuel", "fuel_type", "fuelNorms")),
        "cc": str(g(veh, "cubic_capacity", "cc", "cubicCapacity", "engine_cc")),
        "seating": str(g(veh, "seating", "seating_capacity", "seatingCapacity")),
        "emission": str(g(veh, "emission", "emission_norms", "norms", "fuelNorms")),
        "owner": str(g(own, "name", "owner", "owner_name")),
        "owner_masked": bool(g(own, "masked", default=True)),
        "reg_date": str(g(rc, "registration", "reg_date", "registration_date", "regDate")),
        "fitness_upto": str(g(rc, "fitness", "fitness_upto", "fitnessUpto")),
        "tax_upto": str(g(rc, "tax", "tax_upto", "taxUpto")),
        "age": str(g(rc, "age", "vehicle_age")),
        "finance": str(g(rc, "finance", "financer", "hypothecation")),
        "insurance_company": str(g(ins, "company", "insurance_company", "insurer")),
        "insurance_upto": str(g(ins, "valid_upto", "upto", "insurance_upto")),
        "insurance_status": str(g(ins, "status", default="")),
        "puc_upto": str(g(puc, "valid_upto", "upto", "puc_upto")),
        "puc_status": str(g(puc, "status", default="")),
        "rto_code": str(g(rto, "code", "rto_code")),
        "rto_name": str(g(rto, "name", "rto", "rto_name")),
        "rto_city": str(g(rto, "city", default="")),
        "rto_state": str(g(rto, "state", default="")),
        "rto_phone": str(g(rto, "phone", default="")),
        "rto_site": str(g(rto, "site", "website", default="")),
    }
    lst = []
    for c in (ch.get("list") or [])[:20]:
        if isinstance(c, dict):
            lst.append({k: v for k, v in c.items()})
    challans = find_challans({"challans": lst}) if lst else []
    summary = {"count": int(g(ch, "count", default=len(challans)) or len(challans)),
               "pending_count": int(g(ch, "pending_count", default=0) or 0),
               "pending_amount": g(ch, "pending_amount", default=0),
               "total_amount": g(ch, "total_amount", default=0)}
    if not rc_norm.get("maker") and not rc_norm.get("model") and not challans:
        return {"ok": False, "error": "Hub report khaali thi", "fallback": True}
    return {"ok": True, "plate": plate_c, "rc": rc_norm, "challans": challans, "summary": summary,
            "sources": ["vehicle-report"], "cached": False, "raw": vr.get("raw")}


def fetch_vehicle_report(plate: str) -> dict:
    """
    Hub ke 3 engine + (agar set ho) custom API → sab merge karke ek report.
    {"ok":True, "plate":…, "rc":norm, "challans":[…], "summary":{…}, "sources":[…], "cached":bool}
    Fail: {"ok":False, "error":…, "fallback":True}
    """
    plate_c = clean_plate(plate)
    if not plate_c:
        return {"ok": False, "error": "No number plate given.", "fallback": True}

    hit = _cache_get(plate_c)
    if hit is not None:
        if hit.get("ok"):
            return {**hit, "cached": True}
        return hit

    # v46: pehle hub ka full report (ek hi call) — disabled mile to turant fallback
    try:
        from modules import api_hub as _hub
        vr = _hub.hub_vehicle_report_new(plate_c)
        if vr.get("ok"):
            rep = _report_from_hub_full(plate_c, vr)
            if rep.get("ok"):
                _cache_put(plate_c, rep)
                return rep
        elif vr.get("disabled_by_hub"):
            fast = {"ok": False, "fallback": True, "hub_disabled": True,
                    "error": vr.get("error") or "Live vehicle lookup is turned off on the data provider."}
            _cache_put(plate_c, fast)
            return fast
    except Exception:
        pass

    base, key = api_base(), api_key()
    rc_res = ch_res = sm_res = None
    errors = []

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_rc = ex.submit(_hub_rc, base, key, plate_c)
        f_ch = ex.submit(_hub_challans, base, key, plate_c)
        f_sm = ex.submit(_hub_summary, base, key, plate_c)
        rc_res = f_rc.result()
        ch_res = f_ch.result()
        sm_res = f_sm.result()

    rc_payload, rc_err = rc_res or (None, "no answer")
    ch_payload, ch_err = ch_res or (None, "no answer")
    sm_payload, sm_err = sm_res or (None, "no answer")
    for e in (rc_err, ch_err, sm_err):
        if e:
            errors.append(e)

    norm = normalize_hub_rc(rc_payload) if isinstance(rc_payload, dict) else {}
    challans = []
    if isinstance(ch_payload, dict):
        challans = find_challans(ch_payload)
    summary = {}
    if isinstance(sm_payload, dict):
        d = sm_payload.get("data") or {}
        cs = d.get("challan_summary") or {}
        if cs:
            summary = {"count": int(_num(cs.get("total_challans"))),
                       "total_amount": _num(cs.get("total_amount")),
                       "pending": int(_num((d.get("type_a") or {}).get("count"))),
                       "pending_amount": _num((d.get("type_a") or {}).get("amount")),
                       "paid": int(_num((d.get("type_b") or {}).get("count"))),
                       "paid_amount": _num((d.get("type_b") or {}).get("amount")),
                       "other": 0, "from_summary_api": True}

    # ---- optional: purani custom API (ProPortalx style) ----
    cu = custom_url()
    if cu:
        param = os.environ.get("VEHICLE_API_PARAM", "vehicle_number")
        method = (os.environ.get("VEHICLE_API_METHOD", "GET") or "GET").upper()
        keyname = os.environ.get("VEHICLE_API_KEYNAME", "key")
        try:
            if method == "POST":
                r = requests.post(cu, json={param: plate_c, keyname: key}, headers=UA_HEADERS, timeout=TIMEOUT)
            else:
                r = requests.get(cu, params={param: plate_c, keyname: key}, headers=UA_HEADERS, timeout=TIMEOUT)
            cj = r.json() if r.status_code == 200 else None
        except Exception as e:
            cj = None
            errors.append(f"Custom API: {str(e)[:60]}")
        if isinstance(cj, dict):
            cnorm = normalize_flat_rc(cj, plate_c)
            if cnorm.get("maker") or cnorm.get("model"):
                if not norm:
                    norm = cnorm
                else:                                   # hub me jo khaali ho, wahan custom se bharo
                    for k, v in cnorm.items():
                        if v and not norm.get(k):
                            norm[k] = v
            if not challans:
                challans = find_challans(cj)

    # ---- error / empty handling ----
    api_error = ""
    for payload in (rc_payload, ch_payload, sm_payload):
        if isinstance(payload, dict):
            api_error = api_error or _err_of(payload)

    if not norm and not challans and not summary:
        msg = api_error or (errors[0] if errors else "Is number ka koi record nahi mila.")
        res = {"ok": False, "error": msg, "fallback": True}
        _cache_put(plate_c, res, _FAIL_TTL)
        return res

    if not summary:
        s = challan_summary(challans)
        summary = {**s, "from_summary_api": False}

    res = {"ok": True, "plate": plate_c, "rc": norm, "challans": challans, "summary": summary,
           "sources": ["vehicle-rc", "vehicle-challan", "vehicle-challan-v4"] + (["custom API"] if cu else []),
           "api_error": api_error, "cached": False}
    _cache_put(plate_c, res)
    return res


# ---------------------------------------------------------------- rendering
def _inr(v: float) -> str:
    n = int(round(v))
    s = str(n)
    if len(s) <= 3:
        return "₹" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:]); head = head[:-2]
    if head:
        parts.insert(0, head)
    return "₹" + ",".join(parts) + "," + tail


def _cc_txt(v: str) -> str:
    m = re.search(r"([\d.]+)", str(v or ""))
    if not m:
        return ""
    try:
        f = float(m.group(1))
        return str(int(f)) if f == int(f) else str(f)
    except Exception:
        return m.group(1)


def _status_icon(status: str) -> str:
    s = str(status or "").lower()
    if any(w in s for w in ("pending", "unpaid", "due", "not paid", "open")):
        return "⏳ PENDING"
    if any(w in s for w in ("paid", "success", "disposed", "closed", "complete", "settled")):
        return "✅ PAID"
    if "court" in s:
        return "🏛️ IN COURT"
    return (str(status or "—")).upper()


def _e(v) -> str:
    """API ka text HTML-safe (warna & ya < par Telegram 'can't parse entities' deta hai)."""
    return escape(str(v if v is not None else ""), quote=False)


def render_report(res: dict, max_challans: int = 6) -> str:
    rc = res.get("rc") or {}
    challans = res.get("challans") or []
    summary = res.get("summary") or {}
    plate = res.get("plate") or rc.get("plate") or ""

    maker_model = " ".join([x for x in (rc.get("maker", ""), rc.get("model", "")) if x]).strip() or "—"
    out = [f"🚘 <b>VEHICLE REPORT — {_e(plate)}</b>", "━━━━━━━━━━━━━━━━━━━━━━"]

    # vehicle
    line = ["🚗 <b>VEHICLE</b>", f"• <b>Maker / Model:</b> {_e(maker_model)}"]
    if rc.get("vehicle_class"):
        line.append(f"• <b>Class:</b> {_e(rc['vehicle_class'])}")
    fuel = rc.get("fuel") or ""
    ccv = _cc_txt(rc.get("cc"))
    if fuel or ccv:
        line.append(f"• <b>Fuel:</b> {_e(fuel or '—')}" + (f" • {_e(ccv)} cc" if ccv else ""))
    if rc.get("seating"):
        line.append(f"• <b>Seating:</b> {_e(rc['seating'])}")
    if rc.get("colour"):
        line.append(f"• <b>Colour:</b> {_e(rc['colour'])}")
    if rc.get("emission"):
        line.append(f"• <b>Emission:</b> {_e(rc['emission'])}")
    if rc.get("mfg_year"):
        line.append(f"• <b>Manufacture Year:</b> {_e(rc['mfg_year'])}")
    if rc.get("chassis"):
        line.append(f"• <b>Chassis:</b> <code>{_e(mask_id(rc['chassis']))}</code>")
    if rc.get("engine"):
        line.append(f"• <b>Engine No:</b> <code>{_e(mask_id(rc['engine']))}</code>")
    out += line

    # owner + rto
    out.append("━━━━━━━━━━━━━━━━━━━━━━")
    line = ["👤 <b>OWNER &amp; RTO</b>"]
    if rc.get("owner"):
        line.append(f"• <b>Owner:</b> {_e(mask_name(rc['owner']))}"
                    + (f" ({_e(rc['owner_serial'])})" if rc.get("owner_serial") else ""))
    if rc.get("rto"):
        line.append(f"• <b>RTO:</b> {_e(rc['rto'])}" + (f" · {_e(rc['city'])}" if rc.get("city") else ""))
    if rc.get("rto_phone"):
        line.append(f"• <b>RTO Phone:</b> {_e(rc['rto_phone'])}")
    if rc.get("rto_website"):
        line.append(f"• <b>RTO Site:</b> {_e(rc['rto_website'])}")
    if rc.get("mob"):
        line.append(f"• <b>Owner Mobile:</b> <code>{_e(mask_mobile(rc['mob']))}</code>")
    if len(line) == 1:
        line.append("• not given by API")
    out += line

    # dates & papers
    out.append("━━━━━━━━━━━━━━━━━━━━━━")
    line = ["📅 <b>RC / PAPERS</b>"]
    if rc.get("reg_date"):
        line.append(f"• <b>Registration:</b> {_e(rc['reg_date'])}")
    if rc.get("fitness_upto"):
        line.append(f"• <b>Fitness upto:</b> {_e(rc['fitness_upto'])}")
    if rc.get("tax_upto"):
        line.append(f"• <b>Tax upto:</b> {_e(rc['tax_upto'])}")
    if rc.get("vehicle_age"):
        line.append(f"• <b>Vehicle Age:</b> {_e(rc['vehicle_age'])}")
    if rc.get("blacklist"):
        line.append(f"• <b>Blacklist:</b> {_e(rc['blacklist'])}")
    if rc.get("financer"):
        line.append(f"• <b>Finance / Bank:</b> {_e(rc['financer'])}")
    elif rc.get("financer") == "":
        line.append("• <b>Finance:</b> NA (no hypothecation)")
    if rc.get("noc"):
        line.append(f"• <b>NOC:</b> {_e(rc['noc'])}")
    if len(line) == 1:
        line.append("• not given by API")
    out += line

    # insurance + puc
    out.append("━━━━━━━━━━━━━━━━━━━━━━")
    line = ["🛡️ <b>INSURANCE &amp; PUC</b>"]
    if rc.get("ins_company"):
        line.append(f"• <b>Insurance:</b> {_e(rc['ins_company'])}")
    if rc.get("ins_no"):
        line.append(f"• <b>Policy No:</b> <code>{_e(mask_id(rc['ins_no']))}</code>")
    if rc.get("ins_upto"):
        line.append(f"• <b>Valid upto:</b> {_e(rc['ins_upto'])}"
                    + (f" ({_e(rc['ins_remaining'])})" if rc.get("ins_remaining") else ""))
    if rc.get("ins_status"):
        line.append(f"• <b>Status:</b> {_e(rc['ins_status'])}")
    if rc.get("puc_upto"):
        line.append(f"• <b>PUC:</b> {_e(rc['puc_upto'])}"
                    + (f" ({_e(rc['puc_remaining'])})" if rc.get("puc_remaining") else ""))
    elif rc.get("puc_remaining"):
        line.append(f"• <b>PUC:</b> {_e(rc['puc_remaining'])}")
    if rc.get("puc_no"):
        line.append(f"• <b>PUC No:</b> <code>{_e(mask_id(rc['puc_no']))}</code>")
    if len(line) == 1:
        line.append("• not given by API")
    out += line

    # challans
    cnt = int(summary.get("count") or len(challans))
    pend = int(summary.get("pending") or 0)
    paid = int(summary.get("paid") or 0)
    tot_amt = _num(summary.get("total_amount"))
    pend_amt = _num(summary.get("pending_amount"))

    out.append("━━━━━━━━━━━━━━━━━━━━━━")
    if cnt == 0 and not challans:
        out.append("🚨 <b>CHALLANS</b>")
        out.append("✅ Abhi is vehicle ka <b>koi challan nahi mila</b>.")
        out.append("<i>(Paid challan portal par 24-48 ghante tak dikh sakta hai.)</i>")
    else:
        head = [f"🚨 <b>CHALLANS — {cnt} mile</b>"]
        if pend or pend_amt:
            head.append(f"• ⏳ Pending: <b>{pend}</b>" + (f" — {_inr(pend_amt)}" if pend_amt else ""))
        if paid:
            head.append(f"• ✅ Paid / disposed: <b>{paid}</b>")
        other = int(summary.get("other") or 0)
        if other:
            head.append(f"• ⚪ Other: <b>{other}</b>")
        if tot_amt:
            head.append(f"• 💰 Total amount (all challans): <b>{_inr(tot_amt)}</b>")
        out += head
        for c in challans[:max_challans]:
            no = _challan_from_dict(c, "number") or "—"
            acc = _challan_from_dict(c, "accused")
            amt = _num(_challan_from_dict(c, "amount"))
            dt = _challan_from_dict(c, "date")
            stt = _status_icon(_challan_from_dict(c, "status"))
            off = _challan_from_dict(c, "offence")
            plc = _challan_from_dict(c, "place")
            court = _challan_from_dict(c, "court")
            blk = [f"\n🔹 <b>#{_e(no)}</b>"]
            if acc:
                blk.append(f"   👤 Accused: {_e(mask_name(str(acc)))}")
            if amt:
                blk.append(f"   💰 Amount: <b>{_inr(amt)}</b>")
            if dt:
                blk.append(f"   📅 Date: {_e(dt)}")
            blk.append(f"   ❌ Status: <b>{_e(stt)}</b>")
            if off:
                blk.append(f"   🛑 Offence: {_e(str(off)[:90])}")
            if plc:
                blk.append(f"   📍 Place: {_e(str(plc)[:70])}")
            if court:
                blk.append(f"   🏛️ Court: {_e(str(court)[:70])}")
            out.append("\n".join(blk))
        if len(challans) > max_challans:
            out.append(f"<i>…and {len(challans) - max_challans} more challans.</i>")

    # footer
    out.append("━━━━━━━━━━━━━━━━━━━━━━")
    src = ", ".join(res.get("sources") or []) or "API"
    foot = f"📶 <i>Live data · {_e(src)} · {datetime.now().strftime('%d-%m-%Y %H:%M')}"
    if res.get("cached"):
        foot += " · (saved copy, 5 min)"
    foot += "</i>"
    out.append(foot)
    if res.get("api_error"):
        out.append(f"⚠️ <i>Note: {_e(str(res['api_error'])[:110])}</i>")
    out.append("<i>Koi bhi paisa dene se pehle official e-Challan / Parivahan site par ek baar confirm kar lo.</i>")

    text = "\n".join(out)
    if len(text) > 3900:                      # Telegram limit
        text = text[:3850] + "\n<i>…report trimmed.</i>"
    return text


render_vehicle_report = render_report
