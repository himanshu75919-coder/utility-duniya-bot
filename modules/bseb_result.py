# -*- coding: utf-8 -*-
"""
📋 BOARD RESULT CHECK — BSEB (Bihar School Examination Board)  [v73.1]
=====================================================================
User ka order (7 Oct 2026): "CBSE ke portal jaise result check tool — roll
number / roll code se result aa jaye. CBSE aur BSEB dono ka ho."

Sach (research ke baad — 7 Oct 2026):
  • BSEB (Bihar)  → ✅ HO SAKTA HAI. Bihar Board ki result website
    (result.biharboardonline.org) apni khud ki public API use karti hai:
        GET https://resultapi.biharboardonline.org/result
            ?roll_code=<code>&roll_no=<number>
    Isme NA login lagta hai, NA captcha. (Homepage JS bundle se endpoint
    nikala gaya — `Ei.create({baseURL:"https://resultapi.biharboardonline.org"})`
    aur Result page `te({roll_code, roll_no})`.)
  • CBSE          → ❌ NAHI ho sakta. CBSE ne apna result portal band kar
    diya hai — cbseresults.nic.in ab seedha results.digilocker.gov.in par
    bhej deta hai, aur DigiLocker me LOGIN (mobile OTP) zaroori hai.
    Login bypass karna allowed nahi. Isliye bot me CBSE ke liye saaf
    jaankari card hai (seedha fetch nahi).

Result SIRF tab milta hai jab board ne declare kiya ho:
  • Matric (10th)  → March-April
  • Inter (12th)   → March-April
  • Compartment    → May-August
Baaki time API "no result found" deta hai — bot wo bhi SAFA message me
batata hai (crash ya khaali card nahi).

Privacy: sirf roll code + roll number se public result milta hai (wahi jo
admit card par hota hai). Hum kuch save/log nahi karte.
"""

import re

API_URL = "https://resultapi.biharboardonline.org/result"
REFERER = "https://result.biharboardonline.org/"
TIMEOUT = 15

# Roll code: aam taur par 5 digit (kabhi 3-6). Roll number: 4-8 digit.
_RX_CODE = re.compile(r"^\d{3,6}$")
_RX_ROLL = re.compile(r"^\d{4,8}$")

MEDIA_NOTE = ("ℹ️ Ye result <b>Bihar Board ke official server</b> se seedha aata hai — "
              "jo chhap sakta ho, wahi dikhta hai.")


# ---------------------------------------------------------------- helpers
def clean_digits(s) -> str:
    """Text me se digits nikalo ('11,001' → '11001')."""
    return re.sub(r"[^\d]", "", str(s or ""))


def validate(roll_code, roll_no) -> tuple:
    """(ok, error_hinglish)."""
    rc = clean_digits(roll_code)
    rn = clean_digits(roll_no)
    if not rc and not rn:
        return False, "Roll Code aur Roll Number dono chahiye."
    if not rc:
        return False, "Roll Code nahi mila — jaise <code>11001</code>."
    if not rn:
        return False, "Roll Number nahi mila — jaise <code>100001</code>."
    if not _RX_CODE.match(rc):
        return False, "Roll Code 5 digit ka hota hai (jaise <code>11001</code>)."
    if not _RX_ROLL.match(rn):
        return False, "Roll Number 6 digit ka hota hai (jaise <code>100001</code>)."
    return True, ""


def split_input(text) -> tuple:
    """User ke message se (roll_code, roll_no) nikalo — '11001 100001',
    '11001/100001', 'roll code 11001 roll no 100001' — sab chalta hai."""
    t = re.sub(r"(?<=\d),(?=\d)", "", str(text or ""))   # '11,001' → '11001'
    nums = re.findall(r"\d{3,8}", t)
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return "", nums[0]
    return "", ""


def _find_student(obj):
    """Payload me kahin bhi student dict dhoondo (name/roll_no wali)."""
    if isinstance(obj, dict):
        keys = set(str(k).lower() for k in obj.keys())
        if {"roll_no"} & keys or {"name", "school_name"} <= keys:
            return obj
        for v in obj.values():
            hit = _find_student(v)
            if hit:
                return hit
    elif isinstance(obj, list):
        for v in obj:
            hit = _find_student(v)
            if hit:
                return hit
    return None


def _num(v):
    """'640' / 640 / '640.0' → float ya None."""
    try:
        if v is None or str(v).strip().upper() in ("ABS", "-", ""):
            return None
        return float(str(v).strip())
    except Exception:                                            # noqa: BLE001
        return None


def _sub_line(sub: dict) -> str:
    """Ek subject ki line: naam + marks + (C/F/#) note."""
    name = str(sub.get("sub_name") or sub.get("subject") or sub.get("name") or "-").strip()
    total = _num(sub.get("sub_total"))
    marks = sub.get("theory")
    marks_s = "-" if marks is None else str(marks).strip()
    if total is not None:
        marks_s = f"{marks_s} → <b>{int(total) if total == int(total) else total}</b>"
    flags = ""
    if sub.get("is_compartmental"):
        flags += " (C)"
    if str(sub.get("sub_result") or "").strip():
        if sub.get("sub_total") is not None and _num(sub.get("sub_total")) is not None:
            flags += " F"
    if sub.get("is_improved_sub"):
        flags += " #"
    if sub.get("regulation"):
        flags += " *"
    return f"{name} — {marks_s}{flags}"


def parse_payload(js) -> dict:
    """API ka JSON → saaf result dict. Kabhi crash nahi."""
    try:
        if not isinstance(js, dict):
            return {}
        if js.get("success") is False:
            return {}
        stu = _find_student(js)
        if not stu:
            return {}
        out = {
            "name": str(stu.get("name") or "").strip(),
            "father": str(stu.get("father_name") or "").strip(),
            "mother": str(stu.get("mother_name") or "").strip(),
            "school": str(stu.get("school_name") or "").strip(),
            "roll_code": str(stu.get("roll_code") or "").strip(),
            "roll_no": str(stu.get("roll_no") or "").strip(),
            "reg_no": str(stu.get("reg_no") or stu.get("registration_no") or "").strip(),
            "bseb_id": str(stu.get("bseb_id") or "").strip(),
            "division": str(stu.get("division") or "").strip(),
            "is_topper": bool(stu.get("is_topper")),
            "is_scrutiny": bool(stu.get("is_scrutiny")),
            "is_expelled": bool(stu.get("is_expelled")),
            "passed_under_regulation": bool(stu.get("passed_under_regulation")),
            "subjects": [],
        }
        subs = stu.get("subjects")
        if isinstance(subs, list):
            for s in subs[:20]:
                if isinstance(s, dict):
                    out["subjects"].append({
                        "sub_name": s.get("sub_name") or s.get("subject") or "",
                        "sub_code": str(s.get("sub_code") or ""),
                        "sub_total": s.get("sub_total"),
                        "theory": s.get("theory"),
                        "practical": s.get("practical"),
                        "regulation": s.get("regulation"),
                        "is_compartmental": bool(s.get("is_compartmental")),
                        "is_improved_sub": bool(s.get("is_improved_sub")),
                        "sub_result": s.get("sub_result"),
                    })
        tot = _num(stu.get("total") or stu.get("total_marks") or stu.get("grand_total"))
        if tot is None:
            _s = [_num(s.get("sub_total")) for s in out["subjects"]]
            _s = [x for x in _s if x is not None]
            if _s:
                tot = sum(_s)
        out["total"] = tot
        return out
    except Exception:                                            # noqa: BLE001
        return {}


# ---------------------------------------------------------------- fetch
def fetch(roll_code, roll_no) -> dict:
    """BSEB result lao. Returns:
       {"ok": True, "student": {...}}                → result mil gaya
       {"ok": False, "status": "not_live", ...}      → is roll ka result live nahi
       {"ok": False, "status": "server", ...}        → board ka server busy/down
    """
    rc, rn = clean_digits(roll_code), clean_digits(roll_no)
    ok, err = validate(rc, rn)
    if not ok:
        return {"ok": False, "status": "invalid", "error": err}
    try:
        from modules.core import httpio as _h
        js = _h.get_json(
            API_URL,
            params={"roll_code": rc, "roll_no": rn},
            headers={"Accept": "application/json", "Referer": REFERER},
            timeout=TIMEOUT,
            retry=False,                       # board server par halka rehna hai
        )
    except Exception as e:                                       # noqa: BLE001
        msg = str(e)[:120].lower()
        if "404" in msg or "not found" in msg:
            # API ne kaha "no result found" (off-season / galat roll)
            return {"ok": False, "status": "not_live",
                    "error": "is roll code + roll number ka result abhi live nahi hai"}
        return {"ok": False, "status": "server",
                "error": "Bihar Board ka server abhi jawab nahi de raha (busy ya band)"}
    if isinstance(js, dict) and js.get("success") is False:
        return {"ok": False, "status": "not_live",
                "error": str(js.get("message") or "result abhi live nahi hai")}
    stu = parse_payload(js)
    if not stu or not (stu.get("name") or stu.get("subjects")):
        return {"ok": False, "status": "not_live",
                "error": "is roll ka result abhi live nahi hai"}
    return {"ok": True, "student": stu, "raw_keys": sorted(list(js.keys()))[:8]
            if isinstance(js, dict) else []}
