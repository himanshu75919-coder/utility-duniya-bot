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


def _cfg(url: str = "", key: str = "") -> dict:
    g = lambda n, d="": (os.environ.get(f"VEHICLE_PROVIDER_{n}") or d).strip()   # noqa: E731
    return {
        "url": url or g("URL"),
        "key": key or g("KEY"),
        "param": g("PARAM", "number") or "number",
        "method": (g("METHOD", "GET") or "GET").upper(),
        "body": g("BODY"),
        "headers": g("HEADERS"),
        "auth": (g("AUTH", "bearer") or "bearer").lower(),
        "path": g("PATH"),
        "keyparam": g("KEY_PARAM", "key") or "key",
    }


def _cfg_all() -> list:
    """v71.7: VEHICLE_PROVIDER_URL me '|' se ALAG-ALAG providers.

    Misal:  https://host1|https://host2   aur   key1|key2
    Ek hi key ho to wo sab par chalegi. (RapidAPI BASIC = sirf 10 req/month —
    isliye 2-3 free API mila kar chalane ki sauvidha.)
    """
    raw = (os.environ.get("VEHICLE_PROVIDER_URL") or "").strip()
    keys = (os.environ.get("VEHICLE_PROVIDER_KEY") or "").strip()
    urls = [u.strip() for u in re.split(r"[|\n]+", raw) if u.strip()]
    klist = [k.strip() for k in re.split(r"[|\n]+", keys) if k.strip()]
    out = []
    for i, u in enumerate(urls):
        k = klist[i] if i < len(klist) else (klist[0] if klist else "")
        out.append({"url": u, "key": k})
    return out


def _exhausted(url: str) -> bool:
    """v71.7: jis provider ki monthly limit khatam — usko skip karo (quota bachao)."""
    return time.time() < (_EXHAUSTED.get(_rapidapi_host(url)) or 0)


def _mark_exhausted(url: str) -> None:
    _EXHAUSTED[_rapidapi_host(url)] = time.time() + 21600      # 6 ghante skip


def _rapidapi_host(url: str) -> str:
    """URL se RapidAPI host: https://xxx.p.rapidapi.com/api -> xxx.p.rapidapi.com"""
    u = re.sub(r"^https?://", "", str(url or "").strip())
    return u.split("/")[0].strip().lower()


def is_rapidapi(c: dict | None = None) -> bool:
    """User sirf URL+key daale — headers/method bot khud samajh le."""
    return "rapidapi.com" in (c or _cfg()).get("url", "").lower()


def provider_ready() -> bool:
    c = _cfg()
    return bool(c["url"])


def _flags(c: dict | None = None) -> dict:
    """RapidAPI jaise custom headers parse karo: A:{key}|B:value"""
    c = c or _cfg()
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
        "plate": _pick(f, "registrationnumber", "registrationno", "regnumber", "regno",
                       "vehiclenumber", "rcnumber", "number", "regnno") or plate,
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
        "unladen": _pick(f, "unladenweight", "unloadweight", "unladen", "unload"),
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
        "seating": _pick(f, "seatingcapacity", "seatcapacity", "seats"),
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
        "financer": _pick(f, "financer", "financername", "financiername",
                          "hypothecationbank", "hypothecation", "hypothecatedto"),
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
    # v71.5: "24-11-2017 00:00:00" jaisi dates se bekaar time hata do
    for _dk in ("reg_date", "ins_upto", "fitness_upto", "puc_upto", "tax_upto",
                "reg_validity"):
        if rc.get(_dk):
            rc[_dk] = re.sub(r"[ T]00:00:00(\.\d+)?Z?$", "", str(rc[_dk])).strip()
    return {"rc": {k: v for k, v in rc.items() if v}, "challans": ch_list,
            "count": count, "pending": pend, "amount": amt}


# v71.4: jo URL/body ek baar chal gaya, wo yaad rakho (agli baar turant)
_WORKING_URL: list = [""]
_EXHAUSTED: dict = {}      # v71.7: host -> skip-until timestamp
# RapidAPI par sirf host diya ho to ye aam paths try hote hain (vehicle RC wali API)
_PATH_CANDIDATES = ("VehicleInformation", "vehicle-information", "vehicle_information",
                    "vehicle", "rc", "v1/vehicle", "api/vehicle")


_QUOTA_MSG = ("<b>Is API ke free plan ki MONTHLY limit khatam ho gayi.</b> "
              "BASIC plan me sirf <b>10 requests/mahina</b> milti hain.\n"
              "Aage ke liye 2 rasta:\n"
              "1\ufe0f\u20e3 RapidAPI → is API ka <b>PRO plan</b> ($10/mo = 1000 requests) — ya\n"
              "2\ufe0f\u20e3 Ek aur <b>free</b> RC API subscribe karo aur <code>/rcsetup</code> ke hisaab se "
              "dono ko <code>|</code> se jod do — bot khud badal-badal kar chalayega.\n"
              "Agla mahina shuru hone par BASIC apne aap reset ho jayegi.")


def _vnf(r) -> bool:
    """404: 'gaadi nahi mili' ya 'endpoint galat'? (v71.6)"""
    if getattr(r, "status_code", 0) != 404:
        return False
    t = (getattr(r, "text", "") or "").lower()
    if "endpoint" in t or "does not exist" in t:
        return False        # path galat — aage try karo
    return ("not found" in t) or ("notfound" in t) or ("nahi mila" in t)


def _http_err(r) -> str:
    """HTTP code → saaf Hinglish baat (kya karna hai)."""
    if r.status_code in (401, 403):
        return ("Provider ne key nahi maani (401/403). RapidAPI → Manage Apps → apna app → "
                "Security → Application Key dobara copy karo (poori line).")
    if r.status_code == 429:
        return "Provider ka limit khatam (429) — thodi der baad try karo."
    if r.status_code == 404:
        return ("Provider ne 404 diya — endpoint ka pata galat hai. RapidAPI par API kholo → "
                "Endpoints tab → playground me 'Request' box se poora URL copy karo.")
    if r.status_code in (400, 422):
        return ("Provider ne body/param nahi maana (HTTP %d). Endpoint ka shape alag hai — "
                "ek baar /rcsetup dekho ya screenshot bhejo." % r.status_code)
    return f"Provider ne HTTP {r.status_code} diya."


def _key_error(raw) -> str:
    """RapidAPI kabhi 200 me hi 'not subscribed / invalid key' bhejta hai."""
    try:
        t = json.dumps(raw, ensure_ascii=False).lower()[:600]
    except Exception:                                         # noqa: BLE001
        return ""
    for _frag in ("not subscribed", "invalid api key", "missing api key",
                  "api key is not", "not authorized", "subscribe to a plan",
                  "you are not subscribed"):
        if _frag in t:
            return ("RapidAPI kehti hai: plan subscribe nahi hua / key galat. "
                    "API page par 'Subscribe to Test' (BASIC free) dobara karo, phir "
                    "Manage Apps → app → Security se Application Key copy karo.")
    return ""


def _provider_lookup(plate: str, pr: dict | None = None) -> dict:
    """Provider (authorized/licensed) se poora record — result bot ke ANDAR.

    v71.4 — RapidAPI ke liye "dimaag" laga diya:
      • Body ka key naam har API me alag hota hai (`VehicleNumber` / `vehicle_number`
        / `vehicleNumber`) — bot khud teeno try karta hai.
      • Playground wala poora URL paste karo, ya sirf host bhi — bot khud URL sahi
        karta hai aur (host-only ho to) aam path candidates bhi try karta hai.
      • Jo path ek baar chal gaya, wo yaad rakhta hai (agli baar seedha wahi).
      • Key/subscription ki galti ho to saaf Hinglish message deta hai.
    """
    c = _cfg((pr or {}).get("url", ""), (pr or {}).get("key", ""))
    base = (c["url"] or "").rstrip("/")
    params = {c["param"]: plate}
    if c.get("key") and c.get("auth") == "query":
        params[c.get("keyparam") or "key"] = c["key"]
    hdrs = {**_UA, **_flags(c)}

    def _bodies():
        """POST body — v71.7 QUOTA-SAFE: max 2 request (explicit body ho to sirf 1)."""
        if c.get("body"):
            return [c["body"].replace("{number}", plate).replace("{key}", c.get("key") or "")]
        return [json.dumps({k: plate}) for k in ("VehicleNumber", "vehicle_number")]

    def _post(url, body_txt):
        try:
            payload = json.loads(body_txt)
        except Exception:                                    # noqa: BLE001
            payload = {"VehicleNumber": plate}
        return requests.post(url, json=payload, headers=hdrs, timeout=TIMEOUT)

    def _get(url):
        return requests.get(url, params=params, headers=hdrs, timeout=TIMEOUT)

    def _urls():
        """Kaun-kaun se URL try karne hain — samajhdari se, ek-ek karke.

        v71.5: ROOT URL (base) pehle try hota hai — kuch RapidAPI endpoints
        (jaise "Vehicle RC Information") ROOT par hi POST lete hain; pehle
        unke liye 7 path-candidates bekaar 404 khaate the (~6s).
        """
        post = []
        if c.get("path"):
            post.append(base + "/" + c["path"].lstrip("/")
                        .replace("{number}", plate).replace("{key}", c.get("key") or ""))
        try:
            from urllib.parse import urlparse
            _has_path = bool(urlparse(base).path.strip("/"))
        except Exception:                                     # noqa: BLE001
            _has_path = base.count("/") > 2
        post.append(base)                                     # v71.5: root pehle
        if is_rapidapi(c) and not _has_path:
            post += [base + "/" + _pc.lstrip("/") for _pc in _PATH_CANDIDATES]
        out, seen = [], set()
        if _WORKING_URL[0] and _WORKING_URL[0].startswith(base):
            out.append(_WORKING_URL[0]); seen.add(_WORKING_URL[0])
        for _u in post:
            if _u not in seen:
                seen.add(_u); out.append(_u)
        return out

    def _try_all(url):
        """Ek URL par: POST (saare body shapes) phir GET — jo kaam kare."""
        _err = None
        for _m in ("POST", "GET"):
            if _m == "POST" and c["method"] == "GET" and not is_rapidapi(c):
                continue
            if _m == "GET" and c["method"] == "POST":
                continue
            if _m == "GET":
                try:
                    r = _get(url)
                except Exception as e:                        # noqa: BLE001
                    _err = f"Provider tak baat nahi pahunchi ({str(e)[:60]})."
                    continue
                if r.status_code < 400:
                    return r, None
                _err = _http_err(r)
                if r.status_code in (401, 403):
                    return None, "__AUTH__"
                if r.status_code == 429:
                    return None, "__QUOTA__"
                if _vnf(r):
                    return None, "__VNF__"   # v71.6: gaadi DB me hi nahi hai
        for _b in _bodies():
            try:
                r = _post(url, _b)
            except Exception as e:                            # noqa: BLE001
                _err = f"Provider tak baat nahi pahunchi ({str(e)[:60]})."
                continue
            if r.status_code < 400:
                return r, None
            _err = _http_err(r)
            if r.status_code in (401, 403):
                return None, "__AUTH__"
            if r.status_code == 429:
                return None, "__QUOTA__"
            if _vnf(r):
                return None, "__VNF__"   # v71.6: gaadi DB me hi nahi hai
            # v71.7: 404/400/422 → agli body try karo (max 2 bodies, quota-safe)
        return None, _err

    r, err = None, None
    for _u in _urls():
        r, err = _try_all(_u)
        if err == "__QUOTA__":
            return {"ok": False, "kind": "quota", "error": _QUOTA_MSG}
        if err == "__AUTH__":
            return {"ok": False, "kind": "auth",
                    "error": ("Provider ne key nahi maani (401/403). RapidAPI → Manage Apps → "
                              "apna app → Security → Application Key dobara copy karo "
                              "(poori line).")}
        if err == "__VNF__":
            return {"ok": False, "not_found": True, "kind": "not_found",
                    "error": ("Is gaadi ka record sarkari database me nahi mila "
                              f"(<code>{plate}</code>). Number ek baar phir check karo — "
                              "gaadi nayi hai / transfer ho rahi hai to record thodi der me "
                              "update hota hai.")}
        if r is not None:
            _WORKING_URL[0] = _u                            # agli baar seedha yehi
            break
    if r is None:
        return {"ok": False, "error": err or "Provider se data nahi mila."}
    if r.status_code != 200:
        return {"ok": False, "error": _http_err(r)}

    try:
        raw = r.json()
    except Exception:                                         # noqa: BLE001
        return {"ok": False, "error": "Provider ka jawab samajh nahi aaya."}

    _ke = _key_error(raw)
    if _ke:
        return {"ok": False, "error": _ke}
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
    provs = _cfg_all()
    _tried_provider = bool(provs) or provider_ready()
    _errs = []      # (kind, message) har provider se
    if _tried_provider:
        # v71.7: saare providers ek-ek karke — ek ki limit khatam to doosra
        for _pr in provs:
            _u = _pr.get("url") or ""
            if not _u:
                continue
            if _exhausted(_u):
                _errs.append(("quota", _QUOTA_MSG))
                continue
            _po = _provider_lookup(p, _pr)
            if _po.get("ok"):
                _po["provider"] = _rapidapi_host(_u) or "provider"
                out = _po
                break
            _k = _po.get("kind") or "other"
            if _k == "quota":
                _mark_exhausted(_u)          # agli baar isko chhodo (quota bachao)
            _errs.append((_k, str(_po.get("error") or "")))
    # koi provider na chala to hub dekho (uske apne env me provider ho sakta hai)
    if not out.get("ok"):
        h = _hub_lookup(p)
        if h.get("ok"):
            out = h
        elif h.get("hub_error") and not _tried_provider:
            out = {"ok": False, "hub_error": h.get("hub_error")}
        elif _errs:
            # sabse kaam ki baat pehle: quota > auth > gaadi-na-mili > baaki
            _pri = {"quota": 0, "auth": 1, "not_found": 2}
            _errs.sort(key=lambda x: _pri.get(x[0], 3))
            out = {"ok": False, "error": _errs[0][1], "kind": _errs[0][0]}
            if _errs[0][0] == "not_found":
                out["not_found"] = True
            if _errs[0][0] == "quota":
                _CACHE[ck] = (out, time.time(), 1800)   # 30 min tak wahi baat dikhao
            if len(provs) > 1:
                _tag = {"quota": "limit khatam", "auth": "key galat",
                        "not_found": "gaadi nahi mili", "other": "jawab nahi aaya"}
                _summ = []
                for _i, (_kk, _mm) in enumerate(_errs):
                    _host = _rapidapi_host((provs[_i].get("url") if _i < len(provs) else "") or "")
                    _summ.append(f"  • {_host or ('provider ' + str(_i + 1))}: "
                                 f"{_tag.get(_kk, 'fail')}")
                out["error"] = out["error"] + "\n\n<b>Providers:</b>\n" + "\n".join(_summ[:3])

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
