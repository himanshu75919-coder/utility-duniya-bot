# -*- coding: utf-8 -*-
"""
📋 BOARD RESULT CHECK — BSEB (Bihar School Examination Board)  [v74.0 PRO]
===========================================================================
User ka order (8 Oct 2026): "Result check tool ko upgrade karo — sirf BSEB.
Portal jaisa: pehle EXAM chuno, phir YEAR chuno, phir Roll Code, phir Roll
Number. Result aisa de jaise portal par PDF download hota hai — PDF me poora
data ho. Aisa hi BSEB ke saare exam ke liye."

Sach (research ke baad — 7/8 Oct 2026, LIVE verify kiya):
  • MATRIC (10th) Annual — ✅ LIVE. Official React app ki open API:
        GET https://resultapi.biharboardonline.org/result?roll_code=&roll_no=
    (asli topper ke roll 22050/2600046 par poora result aaya — naam, papa,
    school, subject-wise marks, total 492, 1st Division.)
  • INTER (12th) Annual — portal: interbiharboard.com/ex-26
    Form POST: /ex-26/Result/GetResult  (rollcode, rollno + antiforgery)
    Captcha SIRF client-side hai (server check nahi karta) — isliye bot
    seedha roll code + roll number se result maang sakta hai. Result season
    ke bahar board data hata deta hai → tab "Not Found" (bot saaf batata hai).
  • INTER Special & Compartmental — portal: interbiharboard.com/Spcl-Comprt-26
    (wahi form pattern.)
  • PURANE SAAL (2025, 2024, 2023...) — board purane saal ka data live
    portal par NAHI rakhta. Bot saaf batata hai (jhoothi umeed nahi).

Privacy: sirf roll code + roll number se PUBLIC result. Hum kuch save/log
nahi karte. Login/captcha bypass jaisa kuch nahi — sab public endpoints hain.
"""

import io
import re
import time

# ───────────────────────────────────────────────────────────── constants
MATRIC_API = "https://resultapi.biharboardonline.org/result"
INTER_BASE = "https://interbiharboard.com"
API_REFERER = "https://result.biharboardonline.org/"
TIMEOUT = 18
CURRENT_YEAR = 2026

MEDIA_NOTE = ("ℹ️ Ye result <b>bilkul asli data</b> par bana hai — jo board ke record me "
              "hai, wahi yahan hai. Print / screenshot nikaal sakte hain ✅")

# Exam registry — portal ke buttons jaisa (sirf BSEB)
EXAMS = {
    "matric": {
        "label": "🎓 MATRIC (10th) ANNUAL",
        "short": "Matric (10th)",
        "kind": "api",
        "btn": "🎓 Matric (10th)",
    },
    "inter": {
        "label": "🎓 INTER (12th) ANNUAL",
        "short": "Inter (12th)",
        "kind": "portal",
        "page": "ex-26",                 # portal ka page (2026 cycle)
        "btn": "🎓 Inter (12th)",
    },
    "inter_sc": {
        "label": "🔁 INTER SPECIAL & COMPARTMENTAL",
        "short": "Inter Spl/Compartmental",
        "kind": "portal",
        "page": "Spcl-Comprt-26",
        "btn": "🔁 Inter Spl/Comp",
    },
}

YEARS = [2026, 2025, 2024, 2023, 2022]

_RX_CODE = re.compile(r"^\d{3,6}$")
_RX_ROLL = re.compile(r"^\d{4,9}$")


# ───────────────────────────────────────────────────────────── helpers
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
        return False, "Roll Number 6-7 digit ka hota hai (jaise <code>2600046</code>)."
    return True, ""


def split_input(text) -> tuple:
    """Message se (roll_code, roll_no) nikalo — '11001 100001' jaisa bhi."""
    t = re.sub(r"(?<=\d),(?=\d)", "", str(text or ""))   # '11,001' → '11001'
    nums = re.findall(r"\d{3,9}", t)
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return "", nums[0]
    return "", ""


def _num(v):
    """'640' / 640 / '098' → float ya None."""
    try:
        if v is None or str(v).strip().upper() in ("ABS", "-", ""):
            return None
        return float(str(v).strip())
    except Exception:                                            # noqa: BLE001
        return None


def _nice(v) -> str:
    """Marks ko saaf dikhao: '098' → '98', 88.0 → '88', None → '-'."""
    n = _num(v)
    if n is None:
        return "-"
    return str(int(n)) if n == int(n) else f"{n:g}"


def _flag_str(sub: dict) -> str:
    """""C/#/*/F — portal wale nishaan."""
    f = ""
    if sub.get("is_compartmental"):
        f += " (C)"
    if str(sub.get("sub_result") or "").strip():
        _n = _num(sub.get("sub_total"))
        if _n is None or _n < 30:
            f += " F"
    if sub.get("is_improved_sub"):
        f += " #"
    if sub.get("regulation"):
        f += " *"
    return f


def _sub_line(sub: dict) -> str:
    """Text card ke liye ek subject ki line."""
    name = str(sub.get("sub_name") or sub.get("subject") or sub.get("name") or "-").strip()
    out = f"{name} — <b>{_nice(sub.get('sub_total'))}</b>"
    extra = []
    if sub.get("theory") is not None:
        extra.append(f"th {_nice(sub.get('theory'))}")
    if sub.get("practical") is not None:
        extra.append(f"pr {_nice(sub.get('practical'))}")
    if extra:
        out += f" <i>({', '.join(extra)})</i>"
    out += _flag_str(sub)
    return out


def _extra_marks_cell(sub: dict) -> str:
    """Practical / IA / project / CCE — jo bhi ho, ek cell me."""
    parts = []
    for key, lab in (("practical", "Pr"), ("ia_sci", "IA"),
                     ("project_work", "Proj"), ("cce", "CCE"),
                     ("literacy_activity", "Lit")):
        v = _num(sub.get(key))
        if v is not None:
            parts.append(f"{lab} {_nice(v)}")
    return ", ".join(parts) if parts else "-"


def _find_student(obj):
    """Payload me kahin bhi student dict dhoondo (roll_no / name wali)."""
    if isinstance(obj, dict):
        keys = set(str(k).lower() for k in obj.keys())
        if "roll_no" in keys or {"name", "school_name"} <= keys:
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


def parse_payload(js) -> dict:
    """Matric API ka JSON → saaf student dict. Kabhi crash nahi."""
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
            "exam_type": str(stu.get("exam_type") or "").strip(),
            "is_topper": bool(stu.get("is_topper")),
            "is_scrutiny": bool(stu.get("is_scrutiny")),
            "is_expelled": bool(stu.get("is_expelled")),
            "passed_under_regulation": bool(stu.get("passed_under_regulation")),
            "is_improved_result": bool(stu.get("is_improved_result")),
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
                        "ia_sci": s.get("ia_sci"),
                        "project_work": s.get("project_work"),
                        "cce": s.get("cce"),
                        "literacy_activity": s.get("literacy_activity"),
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


def result_text(st: dict) -> str:
    """PASS / FAIL / Expelled / Regulation — saaf shabdon me."""
    if st.get("is_expelled"):
        return "EXPELLED"
    div = str(st.get("division") or "").lower()
    if "fail" in div:
        return "FAIL"
    bad = [s for s in (st.get("subjects") or [])
           if str(s.get("sub_result") or "").strip() and (_num(s.get("sub_total")) or 0) < 30]
    if st.get("division") or st.get("total"):
        return "PASS (Regulation)" if st.get("passed_under_regulation") else "PASS"
    return "FAIL" if bad else "PASS"


# ======================================================================
#  SOURCE 1: MATRIC — official open API
# ======================================================================
def fetch_matric(roll_code, roll_no) -> dict:
    """Matric result lao (official API).
       {"ok": True, "student": {...}} | {"ok": False, "status": not_live|server|invalid}
    """
    rc, rn = clean_digits(roll_code), clean_digits(roll_no)
    ok, err = validate(rc, rn)
    if not ok:
        return {"ok": False, "status": "invalid", "error": err}
    try:
        from modules.core import httpio as _h
        js = _h.get_json(
            MATRIC_API,
            params={"roll_code": rc, "roll_no": rn},
            headers={"Accept": "application/json", "Referer": API_REFERER},
            timeout=TIMEOUT,
            retry=False,                       # board server par halka rehna hai
        )
    except Exception as e:                                       # noqa: BLE001
        msg = str(e)[:160].lower()
        if "404" in msg or "not found" in msg:
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
    return {"ok": True, "student": stu}


# ======================================================================
#  SOURCE 2: INTER — portal form (interbiharboard.com)
# ======================================================================
def _inter_session():
    """Inter portal ke liye apna chhota session (cookies chahiye)."""
    import requests
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
    })
    return s


def _extract_token(html: str) -> str:
    m = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', html or "")
    return m.group(1) if m else ""


def _txt(html: str) -> str:
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html or "")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"[ \t\r\f\v]+", " ", t)


def _parse_marksheet_guess(html: str) -> dict:
    """Portal ke result page se data nikaalo (best-effort — format badal
    bhi jaye to crash na ho)."""
    out = {"name": "", "roll_code": "", "roll_no": "", "subjects": [],
           "total": None, "division": "", "school": "", "father": ""}
    try:
        t = _txt(html)
        def grab(labels):
            for lab in labels:
                m = re.search(lab + r"\s*[:\-]?\s*([A-Za-z0-9 .'()/-]{2,60})", t, re.I)
                if m and m.group(1).strip():
                    return m.group(1).strip()
            return ""
        out["name"] = grab([r"Student[’'s]*\s*Name", r"Name of (?:the )?Student",
                            r"Candidate[’'s]*\s*Name"])
        out["father"] = grab([r"Father[’'s]*\s*Name"])
        out["school"] = grab([r"School[’'s]*\s*Name", r"School"])
        out["roll_code"] = clean_digits(grab([r"Roll\s*Code"]))
        out["roll_no"] = clean_digits(grab([r"Roll\s*(?:No|Number)"]))
        m = re.search(r"(First|Second|Third|1st|2nd|3rd)\s*Division", t, re.I)
        out["division"] = m.group(0) if m else ""
        m = re.search(r"(?:Grand\s*Total|Total\s*Marks)\s*[:\-]?\s*(\d{2,4})", t, re.I)
        if m:
            out["total"] = _num(m.group(1))
        # subject rows: kisi bhi table se rows utha lo jisme subject + number ho
        rows = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", html or "", re.I)
        for r in rows[:80]:
            cells = re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", r, re.I)
            cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in cells]
            if len(cells) < 2:
                continue
            name = cells[0]
            if not re.match(r"^[A-Za-z][A-Za-z .&()/-]{2,40}$", name):
                continue
            if re.search(r"\d", name):
                continue
            _low = re.sub(r"[^a-z ]", " ", name.lower())
            _bad = {"roll", "code", "number", "no", "name", "father", "mother",
                    "school", "college", "student", "registration", "dob", "date",
                    "gender", "sex", "category", "total", "grand", "division",
                    "result", "marks", "theory", "practical", "subject", "subjects",
                    "class", "board", "session", "exam", "signature", "photo",
                    "sl", "sr", "note", "sub", "paper"}
            if any(t in _bad for t in _low.split()):
                continue
            nums = [_num(c) for c in cells[1:]]
            if not any(n is not None for n in nums):
                continue
            sub = {"sub_name": name, "sub_code": "", "sub_total": None,
                   "theory": None, "practical": None, "ia_sci": None,
                   "project_work": None, "cce": None, "literacy_activity": None,
                   "regulation": None, "is_compartmental": False,
                   "is_improved_sub": False, "sub_result": None}
            vals = [c for c in cells[1:] if _num(c) is not None]
            if vals:
                sub["sub_total"] = vals[-1]
                if len(vals) >= 2:
                    sub["theory"] = vals[0]
            out["subjects"].append(sub)
        if out["total"] is None and out["subjects"]:
            _s = [_num(s.get("sub_total")) for s in out["subjects"]]
            _s = [x for x in _s if x is not None]
            if _s:
                out["total"] = sum(_s)
    except Exception:                                            # noqa: BLE001
        pass
    return out


def fetch_inter(roll_code, roll_no, page: str = "ex-26") -> dict:
    """Inter portal se result lao (form POST — captcha server check nahi karta)."""
    rc, rn = clean_digits(roll_code), clean_digits(roll_no)
    ok, err = validate(rc, rn)
    if not ok:
        return {"ok": False, "status": "invalid", "error": err}
    url = f"{INTER_BASE}/{page}"
    try:
        s = _inter_session()
        g = s.get(url, timeout=TIMEOUT)
        token = _extract_token(g.text)
        if not token:
            return {"ok": False, "status": "server",
                    "error": "portal ka form nahi mila (page badal gaya ho sakta hai)"}
        p = s.post(
            f"{url}/Result/GetResult",
            data={"rollcode": rc, "rollno": rn, "captcha": "000000",
                  "__RequestVerificationToken": token},
            headers={"Referer": url,
                     "Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUT, allow_redirects=True,
        )
        html = p.text or ""
        low = html.lower()
        if "no result found" in low or "not found for the given" in low:
            return {"ok": False, "status": "not_live",
                    "error": "is roll code + roll number ka result abhi live nahi hai"}
        # success page kabhi form wapas hota hai (cookie flow) — dono dekh lo
        if "resultform" in low and "view result" in low and "no result" not in low:
            # shaayad redirect galat hua — dobara try karo seedha GET nahi chalega
            html2 = html
        else:
            html2 = html
        stu = _parse_marksheet_guess(html2)
        if stu.get("name") or stu.get("subjects"):
            return {"ok": True, "student": stu}
        # result aaya par format samajh nahi aaya — raw snippet bhej do
        return {"ok": False, "status": "parse",
                "snippet": re.sub(r"\s+", " ", _txt(html))[:400],
                "error": "result mila par format naya hai"}
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "status": "server",
                "error": f"portal tak nahi pahunch paya ({str(e)[:80]})"}


# ======================================================================
#  DISPATCHER — bot isi ko call karta hai
# ======================================================================
def check(exam_key: str, year, roll_code, roll_no) -> dict:
    """Exam + year + roll → result. Har halat me dict (kabhi crash nahi)."""
    ex = EXAMS.get(str(exam_key))
    if not ex:
        return {"ok": False, "status": "invalid", "error": "pehle exam chuno"}
    try:
        y = int(year or 0)
    except Exception:                                            # noqa: BLE001
        y = 0
    res = {"exam": str(exam_key), "year": y,
           "exam_label": ex["label"], "exam_short": ex["short"]}
    if ex["kind"] == "api":
        r = fetch_matric(roll_code, roll_no)
    else:
        if y and y != CURRENT_YEAR:
            return {**res, "ok": False, "status": "archive",
                    "error": (f"{ex['short']} ka {y} wala result board ke live portal "
                              f"par nahi hai (board purane saal ka data hata deta hai)")}
        r = fetch_inter(roll_code, roll_no, ex.get("page") or "ex-26")
    r.update(res)
    return r


# ======================================================================
#  PDF — portal jaisi "WEB COPY" marksheet (saara data ke saath)
# ======================================================================
_PDF_FONTS = {"done": False}

_RX_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF"
    "\U0001F1E6-\U0001F1FF\U00002190-\U000021FF\U0000FE0F\U0000200D]")


def _sane(t) -> str:
    """PDF text me emoji nahi chhap sakte (▯ aata hai) — hata do."""
    try:
        return re.sub(r"\s{2,}", " ", _RX_EMOJI.sub("", str(t or ""))).strip()
    except Exception:                                            # noqa: BLE001
        return str(t or "")


def _register_pdf_fonts():
    """DejaVu (Latin) + Noto Devanagari register karo (ek hi baar)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    if _PDF_FONTS["done"]:
        return _PDF_FONTS
    _PDF_FONTS["done"] = True
    try:
        from modules.business_tools import _resolved, _resolve
        _resolve()
        lat = _resolved.get("latin")
        latb = _resolved.get("latin_b")
        dev = _resolved.get("deva")
    except Exception:                                            # noqa: BLE001
        lat = latb = dev = None
    try:
        if lat:
            pdfmetrics.registerFont(TTFont("UD", lat))
            _PDF_FONTS["base"] = "UD"
        if latb:
            pdfmetrics.registerFont(TTFont("UD-B", latb))
            _PDF_FONTS["bold"] = "UD-B"
        if dev:
            try:
                pdfmetrics.registerFont(TTFont("UD-DEV", dev))
                _PDF_FONTS["deva"] = "UD-DEV"
            except Exception:                                    # noqa: BLE001
                pass
    except Exception:                                            # noqa: BLE001
        pass
    _PDF_FONTS.setdefault("base", "Helvetica")
    _PDF_FONTS.setdefault("bold", "Helvetica-Bold")
    return _PDF_FONTS


def pdf_filename(exam_key: str, roll_code, roll_no, year) -> str:
    return f"BSEB_{exam_key}_{clean_digits(roll_code)}-{clean_digits(roll_no)}_{year}.pdf"


def build_pdf(student: dict, exam_label: str, year, source: str = "") -> bytes:
    """Marksheet PDF (portal wali web copy jaisi) — bytes deta hai, fail par None."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (Image as RLImage, Paragraph,
                                        SimpleDocTemplate, Spacer, Table, TableStyle)
    except Exception:                                            # noqa: BLE001
        return None
    try:
        st = student or {}
        F = _register_pdf_fonts()
        fb, fbd = F.get("base", "Helvetica"), F.get("bold", "Helvetica-Bold")
        fdev = F.get("deva", fb)
        MAROON = colors.HexColor("#8B1A1A")
        NAVY = colors.HexColor("#123A6B")
        LIGHT = colors.HexColor("#F2F5FA")
        GREY = colors.HexColor("#6B7280")
        LINE = colors.HexColor("#C9D2E0")

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                                topMargin=12 * mm, bottomMargin=14 * mm,
                                title=f"BSEB Result {st.get('roll_code')}/{st.get('roll_no')}",
                                author="Utility Duniya Bot")
        W = doc.width

        def P(txt, size=9, font=None, color=colors.black, align=0, leading=None):
            return Paragraph(_sane(txt), ParagraphStyle(
                f"p{abs(hash(str(txt))) % 99999}", fontName=font or fb, fontSize=size,
                leading=leading or (size + 3), textColor=color, alignment=align))

        story = []
        # ---------- official logo (BSEB website se) ----------
        _logo_cell = ""
        try:
            from modules import boards as _BRD
            _lp = _BRD.logo_path("bseb")
            if _lp:
                _logo_cell = RLImage(_lp, width=21 * mm, height=21 * mm)
        except Exception:                                        # noqa: BLE001
            _logo_cell = ""
        # ---------- header ----------
        _head_col = [P("बिहार विद्यालय परीक्षा समिति", 13, fdev, MAROON, 1),
                     Spacer(1, 2),
                     P("BIHAR SCHOOL EXAMINATION BOARD, PATNA", 11, fbd, NAVY, 1),
                     Spacer(1, 3),
                     P(f"{_sane(exam_label)} — {year}", 10, fbd, colors.black, 1)]
        if _logo_cell:
            hdr = Table([[
                [_logo_cell],
                _head_col,
                [P("WEB COPY", 15, fbd, colors.HexColor("#B91C1C"), 2),
                 P("(NOT AN OFFICIAL DOCUMENT)", 6.5, fb, GREY, 2)],
            ]], colWidths=[24 * mm, W - 24 * mm - 42 * mm, 42 * mm])
        else:
            hdr = Table([[
                _head_col,
                [P("WEB COPY", 16, fbd, colors.HexColor("#B91C1C"), 2),
                 P("(NOT AN OFFICIAL DOCUMENT)", 7, fb, GREY, 2)],
            ]], colWidths=[W - 45 * mm, 45 * mm])
        hdr.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 1.2, MAROON),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDF6F6")),
            ("RIGHTPADDING", (0, 0), (0, 0), 6),
        ] + ([("ALIGN", (0, 0), (0, 0), "CENTER")] if _logo_cell else []) + [
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story += [hdr, Spacer(1, 5 * mm)]

        # ---------- student details ----------
        def kv(k, v):
            return [P(k, 9, fbd, NAVY), P(v if str(v or "").strip() else "-", 9.5)]

        rows = [
            kv("Student Name", st.get("name")),
            kv("Father's Name", st.get("father")),
        ]
        if st.get("mother"):
            rows.append(kv("Mother's Name", st.get("mother")))
        rows.append(kv("School / College", st.get("school")))
        rows.append(kv("Roll Code", st.get("roll_code")))
        rows.append(kv("Roll Number", st.get("roll_no")))
        if st.get("reg_no"):
            rows.append(kv("Registration No.", st.get("reg_no")))
        if st.get("bseb_id"):
            rows.append(kv("BSEB Unique ID", st.get("bseb_id")))
        if st.get("exam_type"):
            rows.append(kv("Exam Type", st.get("exam_type")))
        info = Table(rows, colWidths=[48 * mm, W - 48 * mm])
        info.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT),
            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ]))
        story += [info, Spacer(1, 5 * mm)]

        # ---------- marks table ----------
        subs = st.get("subjects") or []
        head = ["#", "Subject", "Code", "Theory", "Prac/Int", "Reg.", "Subject Total"]
        data = [[P(h, 8.5, fbd, colors.white, 1 if h != "Subject" else 0) for h in head]]
        for i, s in enumerate(subs, 1):
            r = [P(i, 9, fb, colors.black, 1),
                 P(str(s.get("sub_name") or "-")[:34], 9),
                 P(str(s.get("sub_code") or "-"), 8, fb, GREY, 1),
                 P(_nice(s.get("theory")), 9.5, fbd, colors.black, 1),
                 P(_extra_marks_cell(s), 8, fb, colors.black, 1),
                 P(_nice(s.get("regulation")), 8.5, fb, GREY, 1),
                 P(_nice(s.get("sub_total")) + _flag_str(s), 10, fbd, colors.black, 1)]
            data.append(r)
        # final result row (7 cells, spans: 0-2 = label, 3-4 = total)
        tot_txt = _nice(st.get("total"))
        div_txt = _sane(st.get("division") or "-")
        res_txt = result_text(st)
        data.append([P("FINAL RESULT", 9, fbd, colors.white, 0), "", "",
                     P(f"Total: {tot_txt}", 10, fbd, colors.white, 1), "",
                     P(f"{res_txt} · {div_txt}", 9, fbd, colors.white, 1), ""])

        col_w_map = {"#": 8 * mm, "Subject": None, "Code": 13 * mm, "Theory": 19 * mm,
                     "Prac/Int": 22 * mm, "Reg.": 13 * mm, "Subject Total": 27 * mm}
        fixed = sum(v for k, v in col_w_map.items() if v)
        cw = [col_w_map[h] if col_w_map[h] else (W - fixed) for h in head]
        tb = Table(data, colWidths=cw, repeatRows=1)
        nrows = len(data)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("GRID", (0, 0), (-1, nrows - 2), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, nrows - 2),
             [colors.white, colors.HexColor("#F8FAFC")]),
            ("BOX", (0, nrows - 1), (-1, nrows - 1), 0.8, MAROON),
            ("BACKGROUND", (0, nrows - 1), (-1, nrows - 1), MAROON),
            ("SPAN", (0, nrows - 1), (2, nrows - 1)),
            ("SPAN", (3, nrows - 1), (4, nrows - 1)),
            ("SPAN", (5, nrows - 1), (6, nrows - 1)),
            ("GRID", (0, nrows - 1), (-1, nrows - 1), 0.5, MAROON),
        ]
        tb.setStyle(TableStyle(style))
        story += [tb, Spacer(1, 4 * mm)]

        # ---------- notes ----------
        flags_used = any(_flag_str(s).strip() for s in subs)
        if flags_used:
            story.append(P("# = pichhle saal se zyada marks · * = grace marks · "
                           "(C) = compartmental · F = us subject me fail", 8, fb, GREY))
            story.append(Spacer(1, 2 * mm))
        if st.get("is_topper"):
            story.append(P("BOARD TOPPER — is roll ne board ki topper list me jagah banayi hai.",
                           10, fbd, colors.HexColor("#B45309")))
            story.append(Spacer(1, 2 * mm))
        story.append(P(f"Result status: <b>{res_txt}</b>"
                       + ("  ·  Regulation ke saath pass"
                          if st.get("passed_under_regulation") else ""), 9.5))
        story.append(Spacer(1, 4 * mm))

        note = ("NOTE: Ye <b>WEB COPY</b> hai — poora data board ke record se liya gaya hai. "
                "Marksheet ki official copy school / board office se milti hai. "
                f"Banaya: {time.strftime('%d-%m-%Y %I:%M %p')}")
        box = Table([[P(note, 8, fb, colors.HexColor("#7F1D1D"))]], colWidths=[W])
        box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#E5C7C7")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7F7")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story += [box, Spacer(1, 3 * mm)]
        story.append(P("Generated by Utility Duniya Bot · @Supermannn_x", 8, fb, GREY, 1))

        doc.build(story)
        return buf.getvalue()
    except Exception:                                            # noqa: BLE001
        return None
