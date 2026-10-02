# -*- coding: utf-8 -*-
"""
Vehicle Info + Challan Report (v40)
===================================
Ek hi number plate se poora RC record + challan status (pending / paid / disposed).

Kaam kaise karta hai:
  1) Agar API configured hai (Render env me VEHICLE_API_URL + VEHICLE_API_KEY) →
     live report: RC details + insurance + PUC + finance + challan list.
  2) Agar API nahi hai / API fail hui → purana "RTO district + official links" wala card
     (kaam rukta nahi, user ko khaali haath nahi bhejta).

ENV (Render → Environment):
  VEHICLE_API_URL     = poora endpoint (jaise https://api.example.com/rc)
  VEHICLE_API_KEY     = API key / token
  VEHICLE_API_PARAM   = query/body me plate ka naam (default: vehicle_number)
  VEHICLE_API_KEYNAME = key ka naam (default: key)   [kuch APIs 'api_key' / 'token' maangti hain]
  VEHICLE_API_METHOD  = GET (default) ya POST
  VEHICLE_SHOW_MOBILE = 1 kar do to owner ka poora mobile dikhega (default: masked)
  VEHICLE_SHOW_IDS    = 1 kar do to chassis/engine poora dikhega (default: masked)

Safety (default): owner ka mobile aur chassis/engine number **mask** hote hain
(DPDP Act — kisi aur ki personal detail publicly na dikhe). Owner khud chaho to env se on kar sakta hai.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime

import requests

TIMEOUT = int(os.environ.get("VEHICLE_API_TIMEOUT", "25"))


# ---------------------------------------------------------------- config
def api_url() -> str:
    return (os.environ.get("VEHICLE_API_URL") or os.environ.get("VEHICLE_API_BASE") or "").strip()


def api_key() -> str:
    return (os.environ.get("VEHICLE_API_KEY") or os.environ.get("VEHICLE_API_TOKEN") or "").strip()


def is_configured() -> bool:
    return bool(api_url())


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
    s = str(val or "")
    if len(s) < 8:
        return s or "-"
    return f"{s[:6]}{'*' * (len(s) - 9)}{s[-3:]}"


def mask_name(name: str) -> str:
    """R****T K***R style — jaisa official challan portals dikhate hain."""
    out = []
    for word in str(name or "").split():
        if len(word) <= 2:
            out.append(word)
        else:
            out.append(word[0] + "*" * (len(word) - 2) + word[-1])
    return " ".join(out) or "-"


# ---------------------------------------------------------------- api call
def _dig(data, *keys):
    """Nested dict/list me key dhoondhta hai (kisi bhi level par, case/space ignore)."""
    want = [re.sub(r"[^a-z0-9]", "", k.lower()) for k in keys]
    found = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                nk = re.sub(r"[^a-z0-9]", "", str(k).lower())
                if nk in want and not isinstance(v, (dict, list)) and v not in (None, "", "-"):
                    found.append(v)
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(data)
    return found[0] if found else None


def _find_rc_block(payload) -> dict:
    """RC wala dict dhoondhta hai (jisem Registration Number / Maker / Model jaisi keys hon)."""
    best = {}

    def score(d):
        keys = {re.sub(r"[^a-z0-9]", "", str(k).lower()) for k in d.keys()}
        marks = 0
        for k in ("registrationnumber", "makername", "modelname", "chassisnumber", "enginenumber",
                  "registrationdate", "fueltype", "vehicleclass"):
            if k in keys:
                marks += 1
        return marks

    def walk(node):
        nonlocal best
        if isinstance(node, dict):
            s = score(node)
            if s >= 3 and s > score(best):
                best = node
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(payload)
    return best


CHALLAN_KEYS = {
    "number": ("challannumber", "challanno", "chalanumber", "number", "challanid", "id", "referenceno"),
    "accused": ("accusedname", "accused", "name", "ownername", "driver"),
    "amount": ("amount", "fine", "fineamount", "penalty", "totalamount", "challanamount"),
    "date": ("challandate", "date", "offencedate", "issuedate", "challandatetime"),
    "status": ("status", "challanstatus", "paymentstatus", "state"),
    "offence": ("offence", "offense", "offencename", "violation", "violationname", "offencedetails", "offense_details"),
    "place": ("place", "location", "offenceplace", "district", "rto"),
}


def _norm_keys(d: dict) -> dict:
    return {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in d.items()}


RC_ONLY_WORDS = ("registration", "engine", "chassis", "vehicle", "model", "maker", "fuel",
                "insurance", "pucc", "tax", "seating", "hypothecation", "colour", "color")


def _challan_from_dict(d: dict, want: str):
    """Challan field nikalta hai — RC wali keys ko chhodta hai (registration/engine/chassis number)."""
    nd = _norm_keys(d)
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
    """Sirf wahi dict challan maani jaye jisem 2+ challan wale field hon."""
    if not isinstance(d, dict):
        return False
    nk = list(_norm_keys(d).keys())
    marks = 0
    for w in ("challannumber", "challanno", "challanid", "amount", "fine", "penalty",
              "challandate", "challanstatus", "offence", "offense", "violation", "accused"):
        if any(w in k for k in nk):
            marks += 1
    if any(w in k for k in nk for w in RC_ONLY_WORDS):
        return False
    return marks >= 2


def find_challans(payload) -> list:
    """Challan list nikalta hai — API ka format kuch bhi ho, key ke naam se pakad leta hai."""
    rows = []

    def walk(node):
        if isinstance(node, dict):
            nk = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in node.items()}
            hit = any("challan" in k or "challan" in str(k).lower() for k in nk)
            if hit:
                for k, v in nk.items():
                    if isinstance(v, list):
                        for it in v:
                            if _looks_like_challan(it):
                                rows.append(it)
                    elif isinstance(v, dict):
                        inner = [x for x in v.values() if isinstance(x, list)]
                        added = False
                        for lst in inner:
                            for it in lst:
                                if _looks_like_challan(it):
                                    rows.append(it); added = True
                        if not added and _looks_like_challan(v):
                            rows.append(v)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(payload)

    # dedupe
    seen, out = set(), []
    for r in rows:
        k = str(_challan_from_dict(r, "number") or _challan_from_dict(r, "amount")) + "|" + str(_challan_from_dict(r, "date"))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def fetch_vehicle_report(plate: str) -> dict:
    """
    Live API call → {"ok":True, "plate":..., "rc":{...}, "challans":[...], "raw":payload}
    Fail: {"ok":False, "error":..., "fallback":True}
    """
    plate_c = clean_plate(plate)
    if not is_configured():
        return {"ok": False, "error": "Vehicle API is not configured", "not_configured": True}

    url, key = api_url(), api_key()
    param = os.environ.get("VEHICLE_API_PARAM", "vehicle_number")
    keyname = os.environ.get("VEHICLE_API_KEYNAME", "key")
    method = (os.environ.get("VEHICLE_API_METHOD", "GET") or "GET").upper()

    headers = {"User-Agent": "UtilityDuniyaBot/1.0", "Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
        headers["x-api-key"] = key

    try:
        if method == "POST":
            body = {param: plate_c}
            if key:
                body[keyname] = key
            r = requests.post(url, json=body, headers=headers, timeout=TIMEOUT)
        else:
            params = {param: plate_c}
            if key:
                params[keyname] = key
            r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    except requests.Timeout:
        return {"ok": False, "error": "The API took too long to answer. Try again.", "fallback": True}
    except Exception as e:
        return {"ok": False, "error": f"Could not reach the API: {str(e)[:90]}", "fallback": True}

    if r.status_code != 200:
        return {"ok": False, "error": f"The API returned HTTP {r.status_code}. Try again later.", "fallback": True}

    try:
        payload = r.json()
    except Exception:
        return {"ok": False, "error": "The API sent a reply that is not JSON.", "fallback": True}

    rc = _find_rc_block(payload)
    challans = find_challans(payload)

    # kuch APIs "result" ke andar hi sab rakhti hain aur rc block nahi milta
    if not rc:
        rc = {k: v for k, v in (payload.get("result") or {}).items() if not isinstance(v, (dict, list))}

    api_name = payload.get("API_Developer") or payload.get("developer") or payload.get("source") or "live API"
    used_today = payload.get("Today_Used") or payload.get("today_used")

    if not rc and not challans:
        msg = _dig(payload, "message", "msg", "error", "detail")
        return {"ok": False, "error": str(msg or "No record found for this number."), "fallback": True}

    return {"ok": True, "plate": plate_c, "rc": rc, "challans": challans,
            "api_name": str(api_name)[:40], "used_today": used_today, "raw": payload}


# ---------------------------------------------------------------- rendering
def _g(rc: dict, *names):
    nd = _norm_keys(rc or {})
    for n in names:
        k = re.sub(r"[^a-z0-9]", "", n.lower())
        if k in nd and str(nd[k]).strip() not in ("", "-", "None"):
            return str(nd[k]).strip()
    for k, v in nd.items():
        for n in names:
            nn = re.sub(r"[^a-z0-9]", "", n.lower())
            if (nn in k or k.startswith(nn)) and str(v).strip() not in ("", "-", "None"):
                return str(v).strip()
    return ""


def _status_icon(status: str) -> str:
    s = str(status or "").lower()
    if any(w in s for w in ("pending", "unpaid", "due", "not paid", "open")):
        return "⏳ PENDING"
    if any(w in s for w in ("paid", "success", "disposed", "closed", "complete", "settled")):
        return "✅ PAID"
    if any(w in s for w in ("court", "prosecut", "challan")) or s == "in court":
        return "🏛️ IN COURT"
    return (status or "—").upper()


def challan_summary(challans: list) -> dict:
    total_amt = pend_amt = 0.0
    pend = paid = other = 0
    for c in challans:
        amt = _num(_challan_from_dict(c, "amount"))
        total_amt += amt
        st = str(_challan_from_dict(c, "status") or "").lower()
        if any(w in st for w in ("pending", "unpaid", "due", "not paid")):
            pend += 1; pend_amt += amt
        elif any(w in st for w in ("paid", "disposed", "closed", "success")):
            paid += 1
        else:
            other += 1
    return {"count": len(challans), "pending": pend, "paid": paid, "other": other,
            "total_amount": total_amt, "pending_amount": pend_amt}


def _cc(v: str) -> str:
    """99.0 → 99 (numbers saaf dikhein)."""
    try:
        f = float(str(v).strip())
        return str(int(f)) if f == int(f) else str(f)
    except Exception:
        return str(v)


def _num(v):
    try:
        return float(re.sub(r"[^\d.]", "", str(v)) or 0)
    except Exception:
        return 0.0


def _inr(v: float) -> str:
    s = f"{v:,.0f}"
    if len(s) > 3 and s[-4] != ",":
        pass
    return "₹" + s


render_vehicle_report = None   # niche alias set hota hai (bot isi naam se import karta hai)


def render_report(res: dict, max_challans: int = 6) -> str:
    rc, challans = res.get("rc") or {}, res.get("challans") or []
    plate = res.get("plate") or ""

    maker = _g(rc, "maker name", "maker", "manufacturer", "make")
    model = _g(rc, "model name", "model")
    maker_model = f"{maker} {model}".strip() or "—"

    line1 = (
        f"🚘 <b>VEHICLE REPORT — {plate}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚗 <b>VEHICLE INFORMATION</b>\n"
        f"• <b>Number:</b> <code>{plate}</code>\n"
        f"• <b>Maker / Model:</b> {maker_model}\n"
        f"• <b>Class:</b> {_g(rc, 'vehicle class') or '—'}"
        f"{' (' + _g(rc, 'vehicle category') + ')' if _g(rc, 'vehicle category') else ''}\n"
        f"• <b>Fuel:</b> {_g(rc, 'fuel type', 'fuel') or '—'}"
        f"{' • ' + _cc(_g(rc, 'cubic capacity')) + ' cc' if _g(rc, 'cubic capacity') else ''}\n"
        f"• <b>Colour:</b> {_g(rc, 'color', 'colour') or '—'}\n"
        f"• <b>Body:</b> {_g(rc, 'body type') or '—'}"
        f"{' • seats ' + _g(rc, 'seating capacity') if _g(rc, 'seating capacity') else ''}\n"
        f"• <b>Emission:</b> {_g(rc, 'emission norms', 'emission') or '—'}\n"
    )
    chassis, engine = _g(rc, "chassis number", "chassis"), _g(rc, "engine number", "engine")
    if chassis:
        line1 += f"• <b>Chassis:</b> <code>{mask_id(chassis)}</code>\n"
    if engine:
        line1 += f"• <b>Engine No:</b> <code>{mask_id(engine)}</code>\n"
    if _g(rc, "unladen weight"):
        line1 += f"• <b>Unladen Weight:</b> {_g(rc, 'unladen weight')} kg\n"

    reg_office = _g(rc, "registration authority", "rto", "office code")
    insurance = _g(rc, "insurance company", "insurer")
    ins_valid = _g(rc, "insurance validity", "insurance upto", "insurance expiry")
    puc = _g(rc, "pucc upto", "puc upto", "pucc", "puc")
    tax = _g(rc, "tax upto", "tax")
    finance = _g(rc, "hypothecation bank", "financer", "hypothecation")
    rc_status = _g(rc, "rc status", "status")

    line2 = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>RC / PAPERS</b>\n"
        f"• <b>RTO Office:</b> {reg_office or '—'}\n"
        f"• <b>Registration:</b> {_g(rc, 'registration date', 'reg date') or '—'}"
        f"{'  →  valid till ' + _g(rc, 'registration validity', 'valid upto') if _g(rc, 'registration validity', 'valid upto') else ''}\n"
        f"• <b>Manufacture Year:</b> {_g(rc, 'manufacture year', 'manufacturing year', 'mfg year') or '—'}\n"
        f"• <b>RC Status:</b> {('✅ ' + rc_status) if rc_status else '⚠️ not given by API'}\n"
        f"• <b>Insurance:</b> {insurance or '—'}"
        f"{' (till ' + ins_valid + ')' if ins_valid else ''}\n"
        f"• <b>PUC:</b> "
        + (f"{'✅ till ' + puc}" if puc and puc.upper() not in ("N/A", "NA") else "⚠️ not given by API") + "\n"
        f"• <b>Tax:</b> {tax or '—'}\n"
        f"• <b>Finance / Bank:</b> {finance or '✅ none (no hypothecation)'}\n"
    )
    mob = _g(rc, "owner mobile", "mobile", "phone")
    if mob:
        line2 += f"• <b>Owner Mobile:</b> <code>{mask_mobile(mob)}</code>\n"

    s = challan_summary(challans)
    if s["count"] == 0:
        ch = ("━━━━━━━━━━━━━━━━━━━━━━\n"
              "🚨 <b>CHALLANS</b>\n"
              "✅ <b>No challan found</b> for this vehicle right now.\n"
              "<i>(Challan bharne ke baad bhi portal par 24-48 ghante purana record dikh sakta hai.)</i>\n")
    else:
        head = (f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚨 <b>CHALLANS — {s['count']} found</b>\n"
                f"• ⏳ Pending: <b>{s['pending']}</b>"
                + (f" ({_inr(s['pending_amount'])})" if s['pending'] else "") + "\n"
                f"• ✅ Paid / disposed: <b>{s['paid']}</b>\n"
                + (f"• ⚪ Other: <b>{s['other']}</b>\n" if s['other'] else "")
                + (f"• 💰 Total amount (all): <b>{_inr(s['total_amount'])}</b>\n" if s['total_amount'] else ""))
        rows = []
        for c in challans[:max_challans]:
            no = _challan_from_dict(c, "number") or "—"
            acc = _challan_from_dict(c, "accused")
            amt = _num(_challan_from_dict(c, "amount"))
            dt = _challan_from_dict(c, "date")
            stt = _status_icon(_challan_from_dict(c, "status"))
            off = _challan_from_dict(c, "offence")
            plc = _challan_from_dict(c, "place")
            rows.append(
                f"\n🔹 <b>#{no}</b>\n"
                + (f"   👤 Accused: {mask_name(acc)}\n" if acc else "")
                + (f"   💰 Amount: <b>{_inr(amt)}</b>\n" if amt else "")
                + (f"   📅 Date: {dt}\n" if dt else "")
                + f"   ❌ Status: <b>{stt}</b>\n"
                + (f"   🛑 Offence: {off}\n" if off else "")
                + (f"   📍 Place: {plc}\n" if plc else "")
            )
        ch = head + "".join(rows)
        if s["count"] > max_challans:
            ch += f"\n<i>…and {s['count'] - max_challans} more.</i>\n"

    tail = ("━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📶 <i>Live data — {res.get('api_name') or 'API'}"
            + (f" · queries today: {res['used_today']}" if res.get("used_today") else "")
            + f" · {datetime.now().strftime('%d-%m-%Y %H:%M')}</i>\n"
            "<i>Confirm once on the official Parivahan / e-Challan site before paying anything.</i>")

    return line1 + line2 + ch + tail


# bot.py isi naam se import karta hai
render_vehicle_report = render_report
