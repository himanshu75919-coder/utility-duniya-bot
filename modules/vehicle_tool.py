# -*- coding: utf-8 -*-
"""
🚗 GAADI X-RAY (RC + CHALLAN) — v71
====================================
User ka order: "rc+challan wala add kar dena" — aur RESULT bot ke andar aana
chahiye (koi link nahi).

Sach (honest) design:
  • VAHAN (sarkari) ka data CAPTCHA ke peeche hai — bot captcha nahi todta
    (wo illegal hai). Isliye live data ke liye ek AUTHORIZED provider chahiye.
  • Provider lagane par: RC + owner + insurance + PUC + loan + blacklist +
    challan — sab seedha bot ke andar card me dikhta hai.
  • Provider na ho to bot BILKUL khaali nahi lautta — plate ka poora sarkari
    matlab (state / RTO office / series), aur official **SMS tarika**
    (VAHAN <number> → 7738299899) batata hai. Jhootha data kabhi nahi.

Provider lagane ke 2 tarike (dono support hain):
  A) Bot ke Render env me:   VEHICLE_PROVIDER_URL + VEHICLE_PROVIDER_KEY
  B) Hub (ToolVault) ke env me:  wahi naam — bot khud hub se pooch leta hai

Env (saare optional — jo mile wahi use hota hai):
  VEHICLE_PROVIDER_URL    = provider ka poora URL (ya base + PATH)
  VEHICLE_PROVIDER_KEY    = provider key
  VEHICLE_PROVIDER_PARAM  = query param ka naam (default: number)
  VEHICLE_PROVIDER_METHOD = GET | POST      (default: GET)
  VEHICLE_PROVIDER_BODY   = POST body template, jaise {"vehicle_number":"{number}"}
  VEHICLE_PROVIDER_HEADERS= "X-RapidAPI-Key:{key}|X-RapidAPI-Host:xxx.p.rapidapi.com"
  VEHICLE_PROVIDER_AUTH   = bearer | key | header | query
  VEHICLE_PROVIDER_TIMEOUT= 25
"""
from __future__ import annotations

import json
import os
import re
import time

import requests

TIMEOUT = int(os.environ.get("VEHICLE_PROVIDER_TIMEOUT", "25") or 25)
_CACHE: dict = {}
_CACHE_TTL = 900          # 15 min — ek gaadi ka record itni der me nahi badalta
_FAIL_TTL = 60

_UA = {"User-Agent": "UtilityDuniyaBot/1.0", "Accept": "application/json"}


# ------------------------------------------------------------------ helpers
def _clean_plate(plate: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(plate or "")).upper()


def _cfg() -> dict:
    g = lambda n, d="": (os.environ.get(f"VEHICLE_PROVIDER_{n}") or d).strip()   # noqa: E731
    return {
        "url": g("URL"),
        "key": g("KEY"),
        "param": g("PARAM", "number") or "number",
        "method": (g("METHOD", "GET") or "GET").upper(),
        "body": g("BODY"),
        "headers": g("HEADERS"),
        "auth": (g("AUTH", "bearer") or "bearer").lower(),
        "path": g("PATH"),
        "keyparam": g("KEY_PARAM", "key") or "key",
    }


def _rapidapi_host(url: str) -> str:
    """URL se RapidAPI host: https://xxx.p.rapidapi.com/api -> xxx.p.rapidapi.com"""
    u = re.sub(r"^https?://", "", str(url or "").strip())
    return u.split("/")[0].strip().lower()


def is_rapidapi() -> bool:
    """User sirf URL+key daale — headers/method bot khud samajh le."""
    return "rapidapi.com" in _cfg().get("url", "").lower()


def provider_ready() -> bool:
    c = _cfg()
    return bool(c["url"])


def _flags() -> dict:
    """RapidAPI jaise custom headers parse karo: A:{key}|B:value"""
    c = _cfg()
    h = {}
    for part in (c.get("headers") or "").split("|"):
        if ":" in part:
            k, v = part.split(":", 1)
            h[k.strip()] = v.strip().replace("{key}", c.get("key") or "")
    if c.get("key") and not h:
        if is_rapidapi():
            # v71.2: RapidAPI par 2 line hi kaafi — headers apne aap
            h["X-RapidAPI-Key"] = c["key"]
            h["X-RapidAPI-Host"] = _rapidapi_host(c["url"])
        else:
            a = c.get("auth")
            if a == "bearer":
                h["Authorization"] = f"Bearer {c['key']}"
            elif a == "header":
                h["Authorization"] = c["key"]
    return h


def _flatten(d, out=None, depth=0):
    out = {} if out is None else out
    if depth > 6 or not isinstance(d, (dict, list)):
        return out
    if isinstance(d, list):
        for x in d[:3]:
            _flatten(x, out, depth + 1)
        return out
    for k, v in d.items():
        kk = re.sub(r"[^a-z0-9]", "", str(k).lower())
        if isinstance(v, (dict, list)):
            _flatten(v, out, depth + 1)
        elif v not in (None, "", [], {}):
            out.setdefault(kk, v)
    return out


def _pick(flat: dict, *names) -> str:
    for n in names:
        v = flat.get(re.sub(r"[^a-z0-9]", "", n.lower()))
        if v not in (None, "", "null", "NA", "N/A", "-"):
            return str(v).strip()
    return ""


def _int_safe(v):
    try:
        return int(float(re.sub(r"[^\d.]", "", str(v)) or 0))
    except Exception:                                        # noqa: BLE001
        return 0


def map_provider_payload(raw, plate: str) -> dict:
    """Kisi bhi provider ke JSON ko bot ke card shape me badlo (tolerant)."""
    f = _flatten(raw if isinstance(raw, (dict, list)) else {})
    rc = {
        "plate": _pick(f, "registrationnumber", "regnumber", "regno", "vehiclenumber",
                       "rcnumber", "number", "regnno") or plate,
        "owner": _pick(f, "ownername", "owner", "registeredowner", "name"),
        "owner_serial": _pick(f, "ownerserial", "ownernumber", "ownersr"),
        "father": _pick(f, "fathername", "fathersname", "sonof", "guardianname"),
        "mobile": _pick(f, "ownermobile", "mobile", "mobilenumber", "phone", "contactnumber"),
        "office_code": _pick(f, "officecode"),
        "authority": _pick(f, "registrationauthority", "authority"),
        "mfg_year": _pick(f, "manufactureyear", "mfgdate", "yearofmanufacture", "year"),
        "reg_validity": _pick(f, "registrationvalidity", "registrationvalidupto", "rcvalidupto"),
        "body_type": _pick(f, "bodytype"),
        "category": _pick(f, "vehiclecategory"),
        "unladen": _pick(f, "unladenweight", "unladen"),
        "sleeper": _pick(f, "sleepercapacity"),
        "data_source": _pick(f, "datasource"),
        "maker": _pick(f, "maker", "makername", "manufacturer"),
        "model": _pick(f, "model", "modelname", "makermodel", "vehiclemodel"),
        "vehicle_class": _pick(f, "vehicleclass", "class", "vehiclecategory", "vclass"),
        "fuel": _pick(f, "fuel", "fueltype", "fueldescription"),
        "cc": _pick(f, "cubiccapacity", "cc", "enginecapacity"),
        "chassis": _pick(f, "chassisnumber", "chassis", "chassisno"),
        "engine": _pick(f, "enginenumber", "engine", "engineno"),
        "colour": _pick(f, "color", "colour", "vehiclecolor"),
        "seating": _pick(f, "seatingcapacity", "seats"),
        "emission": _pick(f, "fuelnorms", "emissionnorms", "norms", "bsnorm"),
        "reg_date": _pick(f, "registrationdate", "regdate", "registeredon", "registrationvalidfrom"),
        "fitness_upto": _pick(f, "fitnessupto", "fitnesstill", "fitnessvalidupto"),
        "tax_upto": _pick(f, "taxupto", "roadtaxupto", "taxvalidupto"),
        "ins_company": _pick(f, "insurancecompany", "insurer", "insurancecompanyname"),
        "ins_no": _pick(f, "policynumber", "insuranceno", "insurancenumber"),
        "ins_upto": _pick(f, "insuranceupto", "insurancevalidupto", "insuranceexpiry",
                          "insurancevalidity"),
        "puc_no": _pick(f, "pucnumber", "pucno"),
        "puc_upto": _pick(f, "pucupto", "puccupto", "pucexpiry", "pollutionvalidupto"),
        "financer": _pick(f, "financer", "hypothecationbank", "hypothecation",
                          "hypothecatedto", "financername"),
        "blacklist": _pick(f, "blacklist", "blackliststatus", "isblacklisted"),
        "noc": _pick(f, "noc", "nocdetails", "nocstatus"),
        "permit": _pick(f, "permittype", "permit", "permitnumber"),
        "rto": _pick(f, "registeredrto", "rto", "rtocode"),
        "city": _pick(f, "cityname", "city", "district"),
        "status": _pick(f, "status", "rcstatus", "registrationstatus"),
    }
    # challan ka data kabhi seedha, kabhi {"challans": {...}} ke andar aata hai
    _ch_raw = raw.get("challans") if isinstance(raw, dict) else None
    _ch_d = _ch_raw if isinstance(_ch_raw, dict) else {}
    ch_list = []
    count = _int_safe(_pick(f, "challancount", "totalchallan", "challans", "count")) \
        or _int_safe(_ch_d.get("count") or _ch_d.get("total_challans") or 0)
    pend = _int_safe(_pick(f, "pendingchallan", "pendingchallans", "pendingcount", "pending")) \
        or _int_safe(_ch_d.get("pending_count") or 0)
    amt = _int_safe(_pick(f, "pendingamount", "totalamount", "challanamount", "amount")) \
        or _int_safe(_ch_d.get("pending_amount") or _ch_d.get("total_amount") or 0)
    for k in ("challans", "challanlist", "challandetails", "list"):
        _src = f.get(k)
        if isinstance(_ch_d, dict) and k in _ch_d:
            _src = _ch_d.get(k)
        _src = _src if isinstance(_src, list) else ([] if not isinstance(_src, list) else _src)
        for c in (_src or [])[:8]:
            if isinstance(c, dict):
                _fc = _flatten(c)
                ch_list.append({
                    "number": _pick(_fc, "challannumber", "number", "challanno"),
                    "date": _pick(_fc, "challandate", "date", "offensedate"),
                    "amount": _pick(_fc, "amount", "fineamount", "challanamount"),
                    "status": _pick(_fc, "status", "challanstatus", "paymentstatus"),
                    "offence": _pick(_fc, "offence", "offencename", "violation"),
                    "place": _pick(_fc, "place", "location", "offenceplace"),
                    "accused": _pick(_fc, "accused", "accusedname", "ownername", "name"),
                })
    if count == 0 and ch_list:
        count = len(ch_list)
    return {"rc": {k: v for k, v in rc.items() if v}, "challans": ch_list,
            "count": count, "pending": pend, "amount": amt}


def _provider_lookup(plate: str) -> dict:
    """Provider (authorized/licensed) se poora record — result bot ke andar."""
    c = _cfg()
    url = (c["url"] or "").rstrip("/")
    if c.get("path"):
        path = c["path"].replace("{number}", plate).replace("{key}", c.get("key") or "")
        url = url + "/" + path.lstrip("/")
        if "{number}" in c["path"]:
            url = (c["url"] if c["url"].startswith("http") else "https://" + c["url"]).rstrip("/") \
                  + "/" + c["path"].replace("{number}", plate).lstrip("/")
    params = {c["param"]: plate}
    if c.get("key") and c.get("auth") == "query":
        params[c.get("keyparam") or "key"] = c["key"]
    hdrs = {**_UA, **_flags()}

    def _try(method: str):
        if method == "POST":
            body = (c.get("body") or '{"vehicle_number": "{number}"}').replace(
                "{number}", plate).replace("{key}", c.get("key") or "")
            try:
                payload = json.loads(body)
            except Exception:                                # noqa: BLE001
                payload = {"vehicle_number": plate}
            return requests.post(url, json=payload, headers=hdrs, timeout=TIMEOUT)
        return requests.get(url, params=params, headers=hdrs, timeout=TIMEOUT)

    # v71.2: RapidAPI par GET/POST jo chale wahi — bot khud dono try karta hai
    _plan = ["POST"] if (c["method"] == "POST") else ["GET"]
    if is_rapidapi() and c["method"] != "POST" and not c.get("body"):
        _plan = ["GET", "POST"]
    r = None
    try:
        for _m in _plan:
            r = _try(_m)
            if r.status_code < 400:
                break
            if r.status_code in (401, 403, 429):
                break
    except Exception as e:                                    # noqa: BLE001
        return {"ok": False, "error": f"Provider tak baat nahi pahunchi ({str(e)[:60]})."}
    if r.status_code in (401, 403):
        return {"ok": False, "error": "Provider ne key nahi maani (401/403) — key check karo."}
    if r.status_code == 429:
        return {"ok": False, "error": "Provider ka limit khatam (429) — thodi der baad try karo."}
    if r.status_code != 200:
        return {"ok": False, "error": f"Provider ne HTTP {r.status_code} diya."}
    try:
        raw = r.json()
    except Exception:                                         # noqa: BLE001
        return {"ok": False, "error": "Provider ka jawab samajh nahi aaya."}
    out = map_provider_payload(raw, plate)
    out.update({"ok": True, "source": "provider"})
    return out


def _hub_lookup(plate: str) -> dict:
    """Hub (ToolVault) se — jab provider hub ke env me laga ho."""
    try:
        from modules import osint_hub as oh
    except Exception:                                         # noqa: BLE001
        return {"ok": False}
    try:
        res = oh.vehicle_report_v2(plate)
    except Exception:                                         # noqa: BLE001
        return {"ok": False}
    if not res.get("ok"):
        return {"ok": False, "hub_error": str(res.get("error") or "")[:120]}
    rc_full = res.get("rc") or {}
    ch = res.get("challans") or []
    summ = res.get("summary") or {}
    return {"ok": True, "source": "hub", "rc": rc_full, "challans": ch,
            "count": int(summ.get("count") or len(ch) or 0),
            "pending": int(summ.get("pending") or 0),
            "amount": int(summ.get("pending_amount") or summ.get("total_amount") or 0)}


def vehicle_lookup(plate: str) -> dict:
    """🚗 poora record — provider → hub → offline (kabhi raise nahi karta)."""
    p = _clean_plate(plate)
    m = re.match(r"^([A-Z]{2})(\d{1,2})([A-Z]{0,3})(\d{1,4})$", p)
    if len(p) < 6 or not m:
        return {"ok": False,
                "error": ("Number plate samajh nahi aaya. Aise bhejo: <code>BR01AB1234</code> "
                          "ya <code>DL8CAF5030</code>")}

    ck = "veh:" + p
    hit = _CACHE.get(ck)
    if hit and time.time() - hit[1] < hit[2]:
        return {**hit[0], "cached": True}

    out = {"ok": False}
    if provider_ready():
        out = _provider_lookup(p)
    if not out.get("ok"):
        h = _hub_lookup(p)
        if h.get("ok"):
            out = h
        elif h.get("hub_error"):
            out = {"ok": False, "hub_error": h.get("hub_error")}

    if out.get("ok"):
        _CACHE[ck] = (out, time.time(), _CACHE_TTL)
    return out


def offline_parse(plate: str) -> dict:
    """Provider na ho to bhi plate ka SARKARI matlab (state/RTO) — bot ke andar."""
    try:
        from modules.osint_tools import lookup_vehicle_rto
        return lookup_vehicle_rto(plate)
    except Exception:                                         # noqa: BLE001
        return {"ok": False, "error": "Plate parse nahi hua."}
