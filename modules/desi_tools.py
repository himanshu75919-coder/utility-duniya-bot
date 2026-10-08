"""
Utility Duniya — v38 "MARU-TOAD PACK" (chhupe hue tagra tools)
================================================================
4 naye tools, sab 100% apne server pe (koi AI nahi, koi paid API nahi):

  1) 🏦 BANK STATEMENT PDF → EXCEL/CSV   (lock khole, table nikale, hisaab bana de)
  2) 📜 SARKARI KAGAZ SUITE              (kirayanama, affidavit, 138 notice, bayana, registry kharcha, bigha/kattha)
  3) 🕵️ PHOTO INFO + FAKE DETECTOR       (EXIF, GPS, camera, ELA se edit ke nishaan)
  4) ⚡ MEDIA STUDIO                     (YouTube→MP3, status video, karaoke, 8D, bass, voice change, trim/compress)

Sab functions yahan pure-Python / ffmpeg se chalte hain — bot.py inhe import karke use karta hai.
"""
from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime

# ============================================================
#  FFMPEG (system ka, warna imageio-ffmpeg ka bundled binary)
# ============================================================
_FFMPEG = shutil.which("ffmpeg")
if not _FFMPEG:
    try:
        import imageio_ffmpeg  # type: ignore

        _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        _FFMPEG = None
HAS_FFMPEG = bool(_FFMPEG)


def ffmpeg_path() -> str:
    return _FFMPEG or "ffmpeg"


def _run(cmd: list, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


def _tmp(suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


def ffprobe_duration(path: str) -> float:
    """ffprobe na ho to ffmpeg -i ke stderr se duration nikalta hai."""
    probe = shutil.which("ffprobe")
    if probe:
        r = _run([probe, "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=nw=1:nk=1", path], timeout=60)
        try:
            return float((r.stdout or b"0").decode().strip() or 0)
        except Exception:
            pass
    r = _run([ffmpeg_path(), "-i", path], timeout=60)
    txt = (r.stderr or b"").decode(errors="ignore")
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", txt)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return 0.0


# ============================================================
#  1) 🏦 BANK STATEMENT PDF → EXCEL / CSV
# ============================================================
_BANK_SIGNS = {
    "SBI": ["state bank of india", "sbi", "onlinesbi"],
    "HDFC": ["hdfc bank"],
    "ICICI": ["icici bank"],
    "PNB": ["punjab national bank", "pnb"],
    "BOB": ["bank of baroda"],
    "CANARA": ["canara bank"],
    "UNION": ["union bank of india"],
    "KOTAK": ["kotak mahindra"],
    "AXIS": ["axis bank"],
    "YES": ["yes bank"],
    "IDBI": ["idbi bank"],
    "BOI": ["bank of india"],
    "CENTRAL": ["central bank of india"],
    "INDIAN": ["indian bank"],
    "UCO": ["uco bank"],
    "IPPB": ["india post payments bank", "ippb"],
    "PAYTM": ["paytm payments bank"],
    "AIRTEL": ["airtel payments bank"],
    "JIO": ["jio payments bank"],
    "FINO": ["fino payments bank"],
    "BANDHAN": ["bandhan bank"],
}

_MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
_DATE_RE = re.compile(
    r"^(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2}\b|"
    r"\d{1,2}\s*[A-Za-z]{3}\s*\d{2,4}|\d{4}-\d{2}-\d{2})$"
)
_AMT_RE = re.compile(r"^[\d,]+\.?\d{0,2}$")
# line-by-line fallback ke liye sakht (warna cheque number/phone amount lagega)
_AMT_STRICT = re.compile(r"^(?:\d{1,3}(?:,\d{2,3})+(?:\.\d{1,2})?|\d+\.\d{1,2}|\d{1,3}(?:\.\d{3})+)$")


def _txt_in(v):
    """Kachra input (None/bool/dict) -> str. v78: `(x or '')` True/5 jaisa
    truthy non-str pass kar deta tha -> re.compile TypeError = tool crash."""
    if isinstance(v, str):
        return v
    if v is None:
        return ""
    try:
        return v.decode("utf-8", "ignore") if isinstance(v, (bytes, bytearray)) else str(v)
    except Exception:                                       # noqa: BLE001
        return ""


def detect_bank(text: str) -> str:
    low = _txt_in(text).lower()[:6000]
    for name, keys in _BANK_SIGNS.items():
        for k in keys:
            if k in low:
                return name
    return "UNKNOWN"


def statement_passwords(account_hint: str = "", dob_hint: str = "", name_hint: str = "") -> list:
    """Bank PDF lock kholne ke liye aam patterns (log ye hi password rakhte hain)."""
    out = []
    acc = re.sub(r"\D", "", account_hint or "")
    name = re.sub(r"[^A-Za-z]", "", (name_hint or "").split(" ")[0]).lower()
    name4 = name[:4]
    years = []
    if dob_hint:
        for y in re.findall(r"(19|20)\d{2}", dob_hint or ""):
            pass
        m = re.findall(r"\b(19\d{2}|20\d{2})\b", dob_hint or "")
        years += m
    if acc:
        out += [acc, acc[-4:], acc[:4], "0" + acc if len(acc) == 10 else acc]
    if name4:
        for y in years:
            out += [name4 + y, name4.upper() + y, name4 + y[-2:]]
        out += [name4, name4 + "123", name4.upper()]
    # aam default koshish
    out += ["1234", "123456", "0000", "1111", "12345678"]
    # duplicate hata ke lambe pehle
    seen, res = set(), []
    for p in out:
        p = (p or "").strip()
        if p and p not in seen:
            seen.add(p)
            res.append(p)
    return res


def _norm_date(s: str) -> str:
    s = s.strip().replace(".", "/").replace("-", "/")
    for f in ("%d/%m/%Y", "%d/%m/%y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, f).strftime("%d-%m-%Y")
        except Exception:
            continue
    if re.match(r"^\d{4}/\d{1,2}/\d{1,2}$", s):
        try:
            return datetime.strptime(s, "%Y/%m/%d").strftime("%d-%m-%Y")
        except Exception:
            return s
    return s


def _f(x) -> float:
    try:
        return float(str(x).replace(",", "").replace("Cr", "-").replace("Dr", "").strip() or 0)
    except Exception:
        return 0.0


def _decide_amounts(nums: list, detail: str, prev_bal: float) -> tuple:
    """nums me se (debit, credit, balance) nikaalo — balance delta + keyword hints se."""
    amts = [_f(x) for x in nums]
    d = (detail or "").lower()
    if len(amts) >= 3:
        dr, cr, bal = amts[-3], amts[-2], amts[-1]
        if prev_bal:
            delta = bal - prev_bal
            if cr and abs(delta - cr) < 0.5:
                return 0.0, cr, bal
            if dr and abs(delta + dr) < 0.5:
                return dr, 0.0, bal
        if dr and not cr:
            return dr, 0.0, bal
        if cr and not dr:
            return 0.0, cr, bal
        if "cr" in d and "dr" not in d:
            return 0.0, max(dr, cr), bal
        if "dr" in d and "cr" not in d:
            return max(dr, cr), 0.0, bal
        return dr, cr, bal
    if len(amts) == 2:
        amt, bal = amts[0], amts[1]
        # 1) keyword hint
        if re.search(r"\bcr\b|upi/cr|imps/cr|neft/cr|by transfer|deposit|salary|interest|refund|credit", d):
            return 0.0, amt, bal
        if re.search(r"\bdr\b|upi/dr|imps/dr|neft/dr|wdl|withdraw|atm|purchase|cheque|chq|paid|debit|emi|bill", d):
            return amt, 0.0, bal
        # 2) balance delta
        if prev_bal:
            if abs(bal - (prev_bal + amt)) < 0.5:
                return 0.0, amt, bal
            if abs(bal - (prev_bal - amt)) < 0.5:
                return amt, 0.0, bal
        return 0.0, amt, bal
    if len(amts) == 1:
        return 0.0, 0.0, amts[0]
    return 0.0, 0.0, 0.0

def parse_bank_statement(pdf_bytes: bytes, password: str = "") -> dict:
    """
    PDF bytes → {"ok":True,"rows":[{date,detail,debit,credit,balance}],"summary":{...},"csv":bytes,"bank":str}
    Lock tha aur password sahi nahi → {"ok":False,"locked":True,"error":...}
    """
    try:
        import pdfplumber  # noqa
    except Exception:
        return {"ok": False, "error": "pdfplumber is not installed (check requirements)"}

    rows, bank, raw_text = [], "UNKNOWN", ""
    open_kw = {"password": password} if password else {}
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes), **open_kw) as pdf:
            pages = pdf.pages[:60]  # itne page kaafi hain (60 mahine se zyada nahi)
            for pg in pages:
                t = pg.extract_text() or ""
                raw_text += t + "\n"
                for tbl in (pg.extract_tables() or []):
                    for r in tbl:
                        if not r:
                            continue
                        cells = [(c or "").strip() for c in r]
                        vals = [c for c in cells if c]
                        if len(vals) < 3:
                            continue
                        if not _DATE_RE.match(vals[0].replace("  ", " ")):
                            continue
                        nums = [c for c in vals[1:] if _AMT_RE.match(c.replace(" ", ""))]
                        if not nums:
                            continue
                        detail = vals[1] if len(vals) > 2 else ""
                        date_v = _norm_date(vals[0])
                        prev_bal = rows[-1]["balance"] if rows else 0.0
                        dr, cr, bal = _decide_amounts(nums, detail, prev_bal)
                        rows.append({"date": date_v, "detail": detail[:90],
                                     "debit": round(dr, 2), "credit": round(cr, 2), "balance": round(bal, 2)})
    except Exception as e:
        msg = str(e).strip()
        if (not msg) or ("password" in msg.lower()) or ("encrypt" in msg.lower()) or ("decrypt" in msg.lower()):
            if password:
                return {"ok": False, "locked": True, "wrong_password": True,
                        "error": "This password is wrong"}
            return {"ok": False, "locked": True, "error": "The PDF is locked (password) — password needed"}
        return {"ok": False, "error": f"PDF kholne me dikkat: {msg[:120]}"}

    bank = detect_bank(raw_text)

    # Backup plan: table nahi mila → line by line regex
    if not rows:
        for line in raw_text.splitlines():
            parts = line.strip().split()
            if len(parts) < 4:
                continue
            if not re.match(r"^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$", parts[0]):
                continue
            nums = []
            for tok in reversed(parts):
                if _AMT_STRICT.match(tok.replace(" ", "")):
                    nums.append(tok)
                elif _AMT_RE.match(tok.replace(" ", "")) and "," in tok and any(ch.isdigit() for ch in tok):
                    nums.append(tok)
                else:
                    break
            nums = nums[::-1]
            if not nums:
                continue
            detail = " ".join(parts[1:len(parts) - len(nums)]) or "—"
            prev_bal = rows[-1]["balance"] if rows else 0.0
            dr, cr, bal = _decide_amounts(nums, detail, prev_bal)
            rows.append({"date": _norm_date(parts[0]), "detail": detail[:90],
                         "debit": round(dr, 2), "credit": round(cr, 2), "balance": round(bal, 2)})

    if not rows:
        return {"ok": False, "bank": bank,
                "error": "No transaction table found in this PDF. (Is it a scanned photo-PDF? Those have no text.)"}

    tot_dr = round(sum(r["debit"] for r in rows), 2)
    tot_cr = round(sum(r["credit"] for r in rows), 2)
    opening = rows[0]["balance"] - rows[0]["credit"] + rows[0]["debit"] if rows else 0
    closing = rows[-1]["balance"] if rows[-1]["balance"] else round(opening + tot_cr - tot_dr, 2)
    months = sorted({r["date"][3:] for r in rows if len(r["date"]) == 10})
    summary = {
        "count": len(rows), "total_debit": tot_dr, "total_credit": tot_cr,
        "opening": round(opening, 2), "closing": round(closing, 2),
        "months": len(months), "period": f"{rows[0]['date']} to {rows[-1]['date']}",
    }

    # CSV
    buf = io.StringIO()
    buf.write("Date,Detail,Debit (out),Credit (in),Balance\n")
    for r in rows:
        d = (r["detail"] or "").replace('"', "'").replace(",", " ")
        buf.write(f'{r["date"]},"{d}",{r["debit"] or ""},{r["credit"] or ""},{r["balance"] or ""}\n')
    buf.write(f"\nTOTAL,,{tot_dr},{tot_cr},{closing}\n")
    return {"ok": True, "rows": rows, "summary": summary, "bank": bank,
            "csv": buf.getvalue().encode("utf-8-sig")}


def statement_summary_text(res: dict) -> str:
    # v78: parse fail hone par 'summary' key hoti hi nahi -> KeyError -> tool
    # crash. Ab saaf dict-bharosa wala path.
    if not isinstance(res, dict):
        return "❌ <b>Statement parse nahi ho paya</b> (file khaali ya galat format)."
    summ = res.get("summary") or {}
    if not isinstance(summ, dict):
        summ = {}
    def _num(v):
        # v78: parser har field hamesha bharta hi nahi (aadha-pora statement) —
        # `s['total_debit']:,.2f` par KeyError/ValueError se tool crash hota tha.
        try:
            return f"{float(v):,.2f}"
        except Exception:                                          # noqa: BLE001
            return "—"

    return (
        "🏦 <b>BANK STATEMENT READY ✅</b>\n"
        "──────────────────────\n"
        f"🏛️ <b>Bank:</b> {res.get('bank', 'UNKNOWN')}\n"
        f"📅 <b>Period:</b> {summ.get('period', '—')}\n"
        f"🧾 <b>Transactions:</b> {summ.get('count', '—')}  ({summ.get('months', '—')} months)\n"
        f"🔴 <b>Total debit:</b> ₹{_num(summ.get('total_debit'))}\n"
        f"🟢 <b>Total credit (in):</b> ₹{_num(summ.get('total_credit'))}\n"
        f"📂 <b>Opening:</b> ₹{_num(summ.get('opening'))}   →   <b>Closing:</b> ₹{_num(summ.get('closing'))}\n"
        "──────────────────────\n"
        "⬇️ Excel/CSV file neeche hai — Google Sheets ya Excel me kholo, table ready hai."
    )


# ============================================================
#  2) 📜 SARKARI KAGAZ SUITE + STAMP DUTY + LAND UNITS
# ============================================================
STAMP_CONFIG = {
    "BIHAR": {"name": "Bihar", "stamp_pct": 6.5, "reg_pct": 3.0, "male_slab": [(20, 0), (50, 2.0), (100, 3.0), (200, 4.0), (500, 5.0), (1e9, 6.0)]},
    "UP": {"name": "Uttar Pradesh", "stamp_pct": 7.0, "reg_pct": 2.0, "male_slab": [(10, 1.0), (20, 2.0), (50, 3.0), (100, 4.0), (200, 5.0), (500, 6.0), (1e9, 7.0)]},
    "JHARKHAND": {"name": "Jharkhand", "stamp_pct": 4.0, "reg_pct": 2.0, "male_slab": [(0, 4.0)]},
    "DEFAULT": {"name": "Other State", "stamp_pct": 6.0, "reg_pct": 3.0, "male_slab": [(0, 6.0)]},
}

LAND_UNITS = {
    # 1 unit = kitne square feet (Bihar/UP deshi naap)
    "sqft": 1.0, "sqm": 10.7639, "decimal": 435.6, "katha_bihar": 1361.25,
    "dhur_bihar": 68.0625, "bigha_bihar": 27225.0,
    "katha_up": 1361.25, "bigha_up": 27225.0, "biswa_up": 1361.25 / 20,
    "guntha": 1089.0, "acre": 43560.0, "hectare": 107639.0, "gaj": 9.0,
}
LAND_ALIASES = {
    "sq ft": "sqft", "square feet": "sqft", "square foot": "sqft", "फीट": "sqft", "feet": "sqft", "foot": "sqft",
    "square meter": "sqm", "sqm": "sqm", "meter": "sqm",
    "decimal": "decimal", "dismil": "decimal", "dismal": "decimal",
    "katha": "katha_bihar", "kattha": "katha_bihar", "katta": "katha_bihar",
    "dhur": "dhur_bihar", "dhoor": "dhur_bihar",
    "bigha": "bigha_bihar", "bighah": "bigha_bihar",
    "biswa": "biswa_up", "guntha": "guntha",
    "acre": "acre", "ekad": "acre", "hectare": "hectare",
    "gaj": "gaj", "gaz": "gaj", "yard": "gaj",
}


def convert_land(value: float, from_unit: str, region: str = "bihar") -> dict:
    """Bigha/Kattha/Dhur/Decimal/Acre/SqFt — sab me convert + deshi jhalak."""
    f = LAND_ALIASES.get(from_unit.strip().lower(), from_unit.strip().lower())
    if f not in LAND_UNITS:
        return {"ok": False, "error": f"'{from_unit}' not understood. Type: bigha, katha, dhur, decimal, acre, sqft, gaj, hectare"}
    region = (region or "bihar").lower()
    if region.startswith("up") or region.startswith("u."):
        LAND_UNITS["katha_bihar"], LAND_UNITS["bigha_bihar"] = 1361.25, 27225.0
    sqft = value * LAND_UNITS[f]
    out = {
        "ok": True, "input": f"{value} {from_unit}", "sqft": round(sqft, 2),
        "sqm": round(sqft / 10.7639, 2), "decimal": round(sqft / 435.6, 4),
        "katha": round(sqft / 1361.25, 4), "dhur": round(sqft / 68.0625, 3),
        "bigha": round(sqft / 27225.0, 5), "acre": round(sqft / 43560.0, 5),
        "hectare": round(sqft / 107639.0, 5), "gaj": round(sqft / 9.0, 2),
        "guntha": round(sqft / 1089.0, 4),
    }
    return out


def land_text(res: dict) -> str:
    if not res.get("ok"):
        return f"❌ {res.get('error', 'Error')}"
    return (
        f"📐 <b>{res['input']}</b> = \n"
        "──────────────────────\n"
        f"🟩 <b>Sq Feet:</b> {res['sqft']}  |  <b>Sq Meter:</b> {res['sqm']}\n"
        f"🌾 <b>Bigha:</b> {res['bigha']}  |  <b>Kattha:</b> {res['katha']}  |  <b>Dhur:</b> {res['dhur']}\n"
        f"🧮 <b>Decimal (Dismil):</b> {res['decimal']}  |  <b>Gaj:</b> {res['gaj']}\n"
        f"🏞️ <b>Acre:</b> {res['acre']}  |  <b>Hectare:</b> {res['hectare']}  |  <b>Guntha:</b> {res['guntha']}\n"
        "──────────────────────\n"
        "<i>Bihar local units: 1 Bigha = 20 Kattha = 1361.25 Sq Ft per Kattha · 1 Dhur = 68.06 Sq Ft</i>\n"
        "<b>Use for:</b> buying/selling land, registry, all land measurement work."
    )


def registry_cost(state: str, area_sqft: float, circle_rate_per_sqft: float,
                  buyer: str = "male", panchayat_pct: float = 0.0) -> dict:
    """
    Registry ka poora kharcha: stamp duty (khareedar ke hisaab se) + registration + panchayat (Bihar 2% upar)...
    circle_rate_per_sqft = MVR (govt minimum value) — Bihar: bhumijankari.bihar.gov.in par milega.
    """
    st = STAMP_CONFIG.get((state or "DEFAULT").upper(), STAMP_CONFIG["DEFAULT"])
    value = max(area_sqft, 0) * max(circle_rate_per_sqft, 0)
    b = (buyer or "male").lower()
    pct = st["stamp_pct"]
    slab_note = ""
    if b.startswith("f"):
        pct = max(st["stamp_pct"] - 1.0, 0.5)      # mahila ko 1% kam (Bihar/Haryana style)
        slab_note = "Woman buyer — 1% less stamp duty"
    elif b.startswith("j") or "joint" in b:
        pct = max(st["stamp_pct"] - 1.0, 0.5)
        slab_note = "Joint (with a woman owner) — 1% less stamp duty"
    # v50: purana slab-loop theek kiya — wo kabhi use hi nahi ho raha tha (p variable
    # kabhi apply nahi hua). Ab slab note saaf dikhaya jata hai.
    slab_note = slab_note or (f"{st['name']} male slab rates applied")
    stamp = round(value * pct / 100, 2)
    reg = round(value * st["reg_pct"] / 100, 2)
    panch = round(value * panchayat_pct / 100, 2)
    total = round(stamp + reg + panch, 2)
    return {
        "ok": True, "state": st["name"], "value": round(value, 2),
        "area_sqft": area_sqft, "rate": circle_rate_per_sqft,
        "stamp_pct": pct, "stamp": stamp, "reg_pct": st["reg_pct"], "reg": reg,
        "panchayat_pct": panchayat_pct, "panchayat": panch, "total": total,
        "note": slab_note or "Purush (male) khareedar",
    }


def registry_text(r: dict) -> str:
    if not r.get("ok"):
        return "❌ Could not prepare the statement."
    extra = ""
    if r.get("panchayat"):
        extra = f"🏘️ <b>Panchayat/Anchal (extra {r['panchayat_pct']}%):</b> ₹{r['panchayat']:,.0f}\n"
    return (
        f"🏛️ <b>REGISTRY TOTAL COST ({r['state']})</b>\n"
        "──────────────────────\n"
        f"📐 <b>Zameen:</b> {r['area_sqft']:,.0f} Sq Ft  ×  <b>MVR ₹{r['rate']:,.0f}/SqFt</b>\n"
        f"💰 <b>Kul Value:</b> ₹{r['value']:,.0f}\n"
        f"👤 <b>Khareedar:</b> {r['note']}\n"
        "──────────────────────\n"
        f"🧾 <b>Stamp Duty ({r['stamp_pct']}%):</b> ₹{r['stamp']:,.0f}\n"
        f"📝 <b>Registration ({r['reg_pct']}%):</b> ₹{r['reg']:,.0f}\n"
        f"{extra}"
        "──────────────────────\n"
        f"💵 <b>Total government cost: ₹{r['total']:,.0f}</b>\n\n"
        "➕ <b>Extra (not included):</b> notary/advocate fee, e-stamp, witness, broker — as per local practice.\n"
        "<i>⚠️ This is an estimate (based on the MVR you gave) — confirm the final amount at the sub-registrar office.</i>"
    )


# ---------- Kagaz templates (PDF) ----------
def _pdf_doc(title: str, lines: list, footer: str = "") -> bytes:
    """Simple, saaf sarkari-style PDF (reportlab). Sanskrit/Hindi ke liye English text rakha hai."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm, title=title)
    ss = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=ss["Title"], fontSize=17, spaceAfter=10)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=12, leading=20, alignment=4)
    small = ParagraphStyle("s", parent=ss["BodyText"], fontSize=9.5, leading=14, textColor=colors.grey)
    story = [Paragraph(title, h), Spacer(1, 6)]
    for ln in lines:
        if not ln:
            story += [Spacer(1, 6)]
        elif ln.startswith("##"):
            story += [Paragraph(f"<b>{ln[2:].strip()}</b>", body)]
        elif ln.startswith("::"):
            story += [Paragraph(f"<i>{ln[2:].strip()}</i>", small)]
        else:
            story += [Paragraph(ln, body)]
    if footer:
        story += [Spacer(1, 14), Paragraph(footer, small)]
    doc.build(story)
    return buf.getvalue()


def _today_long() -> str:
    return datetime.now().strftime("%d %B %Y")


def kagaz_kirayanama(d: dict) -> bytes:
    lines = [
        "<b>RENT AGREEMENT / KIRAYANAMA</b>",
        f"::Date: {d.get('date') or _today_long()}",
        "",
        f"<b>1. Landlord (Makan Malik):</b> {d.get('landlord') or '________'}  ",
        f"   Address: {d.get('landlord_addr') or '________'}",
        "",
        f"<b>2. Tenant (Kirayedar):</b> {d.get('tenant') or '________'}  ",
        f"   Address: {d.get('tenant_addr') or '________'}",
        "",
        f"<b>3. Property (Makan):</b> {d.get('property') or '________'}  ",
        f"   Situated at: {d.get('place') or '________'}",
        "",
        f"<b>4. Rent (Kiraya):</b> Rs. {d.get('rent') or '________'} per month  ",
        f"<b>5. Deposit (Advance):</b> Rs. {d.get('deposit') or '0'}  ",
        f"<b>6. Period:</b> {d.get('months') or '11'} months, from {d.get('start') or '________'} to {d.get('end') or '________'}  ",
        f"<b>7. Electricity / Water bill:</b> {d.get('bill') or 'Tenant will pay as per actual consumption'}  ",
        "",
        "## TERMS & CONDITIONS",
        "1. The Tenant shall pay the monthly rent on or before the 5th day of every English month.",
        "2. The Tenant shall not sub-let the premises or any part of it without written consent of the Landlord.",
        "3. The Tenant shall use the premises only for residential/commercial purpose as agreed and shall not do any illegal activity.",
        "4. The monthly rent may be increased by 10% after completion of every 11 months, by mutual consent.",
        "5. The Landlord shall be responsible for major structural repairs; the Tenant shall keep the premises clean and pay for minor daily maintenance.",
        "6. This agreement shall be terminated after the agreed period or earlier by one month's written notice by either party.",
        "7. The security deposit shall be refunded by the Landlord at the time of vacating, after deducting dues (if any).",
        "",
        "## SIGNATURES",
        "Landlord: ______________________          Tenant: ______________________",
        "Witness 1: ______________________          Witness 2: ______________________",
    ]
    return _pdf_doc("RENT AGREEMENT (KIRAYANAMA)", lines,
                    "NOTE: This is a computer-generated draft. For legal registration, print on stamp paper of the "
                    "applicable value and get it notarised / registered with the Sub-Registrar. Draft format as per Indian "
                    "rent practice; get it verified by a local advocate for court use.")


def kagaz_affidavit(d: dict) -> bytes:
    lines = [
        "<b>AFFIDAVIT</b>",
        f"::Affidavit No.: {d.get('no') or '________'}   Sworn before Executive Magistrate / Notary",
        "",
        f"<b>I, {d.get('name') or '________'}</b>, son/daughter of <b>{d.get('father') or '________'}</b>,",
        f"aged about <b>{d.get('age') or '____'} years</b>, resident of {d.get('address') or '________'},",
        "do hereby solemnly affirm and declare on oath as under:",
        "## PURPOSE OF THIS AFFIDAVIT",
        f"{d.get('purpose') or 'That the facts stated herein are true and correct, and are being declared for the purpose of submission before the concerned authority.'}",
        "",
        f"{d.get('body') or 'That I am a Citizen of India and the particulars given above are true to the best of my knowledge and belief.'}",
        "",
        "## DECLARATION",
        "1. That the contents of this affidavit are true and correct to the best of my knowledge and belief and nothing material has been concealed.",
        "2. That this affidavit is being sworn in my full senses free from any pressure, threat or coercion.",
        f"3. That the facts stated above pertain to me / my family and are required for {d.get('reason') or 'official records'}.",
        "",
        f"::Place: {d.get('place') or '________'}                                Dated: {d.get('date') or _today_long()}",
        "",
        "## DEPONENT",
        "Name and Signature: _______________________________",
        "",
        "## VERIFICATION",
        "Verified at ______________ on this ____ day of ____________, 20____ that the contents of the above affidavit "
        "are true and correct to my knowledge and belief.",
        "",
        "Before me: ____________________________  (Notary / Executive Magistrate / Oath Commissioner)",
    ]
    return _pdf_doc("AFFIDAVIT", lines,
                    "NOTE: Affidavit must be sworn before a Notary Public / Executive Magistrate. Stamp paper value depends "
                    "on the purpose — ask the Notary. This is only a computer-generated draft.")


def kagaz_notice138(d: dict) -> bytes:
    amt = d.get("amount") or "________"
    lines = [
        "<b>LEGAL NOTICE UNDER SECTION 138</b>",
        "<b>Negotiable Instruments Act, 1881</b>",
        "::Through Registered Post / Speed Post (A.D.)",
        "",
        f"<b>To,</b><br/>{d.get('to_name') or '________'}<br/>{d.get('to_addr') or '________'}",
        "",
        f"<b>From,</b><br/>{d.get('from_name') or '________'}<br/>{d.get('from_addr') or '________'}",
        "",
        f"<b>Date:</b> {d.get('date') or _today_long()}",
        "",
        "## SUBJECT: Legal notice regarding dishonour of cheque No. ______ dated ______ for Rs. " + str(amt) + "/-",
        "",
        f"1. That you, the addressee, issued a Cheque bearing No. <b>{d.get('cheque_no') or '______'}</b> dated "
        f"<b>{d.get('cheque_date') or '______'}</b> for Rs. <b>{amt}/-</b> drawn on <b>{d.get('bank') or '______'}</b> in favour of my client, "
        f"towards discharge of your legally enforceable liability (Bill No. <b>{d.get('bill_no') or '______'}</b>).",
        f"2. That the said cheque was presented for encashment on <b>{d.get('present_date') or '______'}</b> and the same was "
        f"dishonoured/returned unpaid with the remark <b>“{d.get('reason') or 'Funds Insufficient'}”</b>, as per bank return memo.",
        "3. That your bank has returned the said cheque vide its Memo, thereby you have committed an offence punishable "
        "under Section 138 of the Negotiable Instruments Act, 1881.",
        "4. That despite repeated requests and reminders, you have failed to pay the cheque amount.",
        "",
        "## NOTICE",
        f"You are hereby called upon to pay the due amount of Rs. <b>{amt}/-</b> (along with any bank charges) within "
        "<b>15 (fifteen) days</b> from the receipt of this notice, failing which my client shall be constrained to initiate "
        "criminal proceedings against you under Section 138/142 of the Negotiable Instruments Act, 1881, at your cost, "
        "risk and responsibility.",
        "This notice is given without prejudice to the other rights and remedies available to my client.",
        "",
        "Yours faithfully,",
        "____________________________________",
        f"{d.get('advocate') or 'Advocate for the Complainant'}",
        "::Copy retained. Send by registered post and keep the postal receipt — it is the proof of service.",
    ]
    return _pdf_doc("LEGAL NOTICE (SECTION 138 N.I. ACT)", lines,
                    "NOTE: This is a computer-generated draft for guidance. Get it printed on the letterhead of an "
                    "advocate and verified by him before dispatch. Court format varies by jurisdiction.")


def kagaz_bayana(d: dict) -> bytes:
    lines = [
        "<b>BAYANA / PAKKI RASID (TOKEN RECEIPT FOR PROPERTY DEAL)</b>",
        f"::Date: {d.get('date') or _today_long()}",
        "",
        f"<b>1. Seller (Vikreta):</b> {d.get('seller') or '________'}",
        f"   S/o {d.get('seller_father') or '________'}, Address: {d.get('seller_addr') or '________'}",
        "",
        f"<b>2. Buyer (Kreta):</b> {d.get('buyer') or '________'}",
        f"   S/o {d.get('buyer_father') or '________'}, Address: {d.get('buyer_addr') or '________'}",
        "",
        f"<b>3. Property (Zameen/Makan):</b> {d.get('property') or '________'}",
        f"   Khata No.: <b>{d.get('khata') or '______'}</b>   Khasra/Plot No.: <b>{d.get('khasra') or '______'}</b>",
        f"   Mouza/Village: {d.get('mouza') or '________'}   Thana: {d.get('thana') or '________'}   Anchal: {d.get('anchal') or '________'}",
        f"   District: {d.get('district') or '________'}",
        f"   Area: <b>{d.get('area') or '________'}</b>",
        "",
        f"<b>4. Total Deal Amount:</b> Rs. {d.get('total') or '______'}/-",
        f"<b>5. Bayana (Token) Received Today:</b> Rs. {d.get('token') or '______'}/-",
        f"<b>6. Balance to be paid at registration:</b> Rs. {d.get('balance') or '______'}/-",
        f"<b>7. Registry/Agreement date fixed:</b> {d.get('reg_date') or '________'}",
        "",
        "## SHARTEN (CONDITIONS)",
        "1. The Seller has received the Bayana amount in cash/UPI/Cheque today in the presence of both parties and witnesses.",
        "2. If the <b>Seller</b> backs out, he shall return double the Bayana amount to the Buyer.",
        "3. If the <b>Buyer</b> backs out, the Bayana amount shall stand forfeited in favour of the Seller.",
        "4. The Seller assures that the said land/property is free from all disputes, mortgage, lien, bank loan, court case and is his self-acquired ancestral property as declared.",
        "5. All documents (jamabandi, khatiyan, tax receipt, mutation, sale deed chain) of the property shall be handed over to the Buyer at the time of registry.",
        "6. Stamp duty, registration charges and other legal expenses shall be borne as per the agreement between the parties.",
        "7. This receipt holds legal value as an agreement to sell between the parties and witnesses signing below.",
        "",
        "## SIGNATURES (with Aadhaar/PAN mention)",
        "Seller: ______________________   (ID: __________)",
        "Buyer:  ______________________   (ID: __________)",
        "Witness 1: ___________________   (ID: __________)",
        "Witness 2: ___________________   (ID: __________)",
    ]
    return _pdf_doc("BAYANA / TOKEN RECEIPT", lines,
                    "NOTE: Computer-generated draft. For a legally enforceable agreement, print on stamp paper of proper "
                    "value, mention full IDs and get it notarised. Keep both witnesses with ID.")


def kagaz_loan_receipt(d: dict) -> bytes:
    lines = [
        "<b>PROMISSORY NOTE / RIN SHODH (LOAN PAPER)</b>",
        f"::Place: {d.get('place') or '________'}          Date: {d.get('date') or _today_long()}",
        "",
        f"<b>Amount borrowed (Rin):</b> Rs. {d.get('amount') or '______'}/-",
        f"<b>In words:</b> {d.get('words') or '____________________'} Rupees only.<br/>",
        f"<b>I, {d.get('borrower') or '________'}</b>, S/o {d.get('father') or '________'},",
        f"resident of {d.get('address') or '________'}, acknowledge that I have today received "
        f"Rs. {d.get('amount') or '______'}/- as a loan from <b>{d.get('lender') or '________'}</b> "
        f"of {d.get('lender_addr') or '________'}.",
        f"<b>Receiving mode:</b> {d.get('mode') or 'Cash / UPI'}  ",
        f"<b>Repayment promise:</b> I promise to repay the said amount as agreed: {d.get('terms') or 'with interest as mutually agreed, within the agreed period'}.",
        f"<b>Promised repayment date:</b> {d.get('due') or '________'}",
        "",
        "## TERMS",
        f"1. Rate of interest (if any): <b>{d.get('rate') or '—'}</b> per {d.get('basis') or 'month'}. Interest will be calculated on the outstanding amount only.",
        "2. The borrower shall not raise any dispute about the receipt of the amount, and this document is the borrower's written acknowledgement of debt.",
        "3. In case of default, the lender is entitled to recover the amount with interest and lawful charges through lawful proceedings.",
        "4. Both parties declare that this transaction is lawful and not against public policy; the borrower is not a minor.",
        "",
        "## SIGNATURES",
        "Borrower: ______________________  (Aadhaar: __________  Mobile: __________)",
        "Lender:   ______________________  (Aadhaar: __________  Mobile: __________)",
        "Witness 1: ____________________  Witness 2: ____________________",
    ]
    return _pdf_doc("LOAN / PROMISSORY NOTE", lines,
                    "NOTE: Computer-generated draft. Print on proper stamp paper and take signatures + witnesses. "
                    "This helps in court as an acknowledgement of debt — but final legal value depends on stamp and proof.")


def kagaz_money_affidavit(d: dict) -> bytes:
    """Sarkari kaam ke liye aam affidavit: naam me sudhar, ghar ka pata, income, gap year."""
    kind = (d.get("kind") or "GENERAL").upper()
    presets = {
        "NAME": "That my correct name is <b>{new}</b> and in my educational/identity records it has been wrongly written as <b>{old}</b>. Both names refer to one and the same person.",
        "ADDRESS": "That I have been residing at <b>{new}</b> and my earlier recorded address was <b>{old}</b>. Both addresses relate to me.",
        "INCOME": "That my annual family income from all sources is Rs. <b>{new}</b> and the said declaration is true, required for the benefit of a government scheme.",
        "GAP": "That after passing my examination in <b>{old}</b>, I remained engaged in personal/family work till <b>{new}</b> and could not continue studies in between.",
        "DOB": "That my correct date of birth is <b>{new}</b>, whereas my earlier record shows <b>{old}</b>. Both refer to the same person, i.e., myself.",
    }
    body = presets.get(kind, "That the following facts stated by me are true: <b>{new}</b> (earlier: <b>{old}</b>).")
    body = body.replace("{new}", d.get("new") or "________").replace("{old}", d.get("old") or "________")
    d2 = dict(d)
    d2["purpose"] = f"<b>{kind} CORRECTION / DECLARATION AFFIDAVIT</b><br/>{body}"
    d2["body"] = "That the above facts are true and correct, and I execute this affidavit for official records / submission before the concerned authority."
    d2["reason"] = d.get("reason") or "official record correction"
    return kagaz_affidavit(d2)


KAGAZ_MAKERS = {
    "kirayanama": kagaz_kirayanama,
    "affidavit": kagaz_affidavit,
    "notice138": kagaz_notice138,
    "bayana": kagaz_bayana,
    "loan": kagaz_loan_receipt,
    "nameaff": kagaz_money_affidavit,
}

KAGAZ_FIELDS = {
    "kirayanama": [("landlord", "House owner name", "example: Ramesh Kumar"),
                   ("landlord_addr", "Owner address", "village/area, district"),
                   ("tenant", "Tenant name", "example: Suresh Sharma"),
                   ("tenant_addr", "Tenant address", "village/area, district"),
                   ("property", "House/shop details", "example: 2 rooms, 1 kitchen, roof"),
                   ("place", "Place (where it is)", "example: Boring Road, Patna"),
                   ("rent", "Rent (₹ per month)", "example: 6000"),
                   ("deposit", "Advance / Deposit ₹", "example: 12000"),
                   ("months", "Agreement for how many months", "example: 11"),
                   ("start", "From date", "example: 01-11-2026"),
                   ("end", "To date", "example: 30-09-2027")],
    "affidavit": [("name", "Your name", "example: Ravi Kumar"),
                  ("father", "Father\'s name", "example: Ram Kumar"),
                  ("age", "Age", "example: 32"),
                  ("address", "Full address", "example: Ward 5, Sitamarhi"),
                  ("purpose", "Purpose of affidavit", "example: name correction / address / income"),
                  ("body", "What to write (full statement)", "example: my correct name is Ravi Kumar..."),
                  ("place", "Place", "example: Patna"),
                  ("date", "Date", "example: 15-11-2026")],
    "notice138": [("from_name", "Your name (sender)", "example: Suresh Kumar"),
                  ("from_addr", "Your address", "village/area"),
                  ("to_name", "Notice kis ko bhejna hai (naam)", "jaise: Mahesh Yadav"),
                  ("to_addr", "His/her address", "village/area"),
                  ("amount", "Cheque amount ₹", "example: 50000"),
                  ("cheque_no", "Cheque number", "example: 456789"),
                  ("cheque_date", "Cheque date", "example: 10-08-2026"),
                  ("bank", "Bank name", "example: SBI"),
                  ("present_date", "Date presented in bank", "example: 12-09-2026"),
                  ("reason", "What the bank wrote", "example: Fund Insufficient"),
                  ("advocate", "Advocate name (or leave empty)", "example: Adv. A.K. Singh")],
    "bayana": [("seller", "Seller name", "example: Ram Singh"),
               ("seller_father", "His father\'s name", "example: Shyam Singh"),
               ("seller_addr", "Seller address", "village/area"),
               ("buyer", "Buyer name", "example: Ajay Kumar"),
               ("buyer_father", "His father\'s name", "example: Vijay Kumar"),
               ("buyer_addr", "Buyer address", "village/area"),
               ("property", "Land/House details", "example: 2 katha land, paddy"),
               ("khata", "Khata number", "example: 342"),
               ("khasra", "Khasra/Plot number", "example: 1125"),
               ("mouza", "Mouza / gaon", "example: Bishunpura"),
               ("thana", "Thana", "example: Runnisaidpur"),
               ("anchal", "Anchal/Block", "example: Belsand"),
               ("district", "Jila", "example: Sitamarhi"),
               ("area", "Kitni zameen (bigha/kattha)", "example: 2 katha 5 dhur"),
               ("total", "Kul sauda ₹", "example: 800000"),
               ("token", "Token money today ₹", "example: 100000"),
               ("balance", "Balance amount ₹", "example: 700000"),
               ("reg_date", "Registry date", "example: 20-12-2026")],
    "loan": [("borrower", "Borrower name", "example: Rahul Kumar"),
             ("father", "His father\'s name", "example: Suresh Kumar"),
             ("address", "His/her address", "village/area"),
             ("lender", "Lender name", "example: Mahesh Kumar"),
             ("lender_addr", "Lender address", "village/area"),
             ("amount", "Amount ₹", "example: 50000"),
             ("words", "Amount shabdon me", "example: Fifty Thousand"),
             ("mode", "How the money was given", "example: Cash / UPI"),
             ("rate", "Interest (rate)", "example: 3% per month"),
             ("basis", "interest basis", "month / year"),
             ("due", "Repayment date", "example: 31-03-2027"),
             ("place", "Place", "example: Sitamarhi"),
             ("date", "Date", "example: 15-11-2026")],
    "nameaff": [("name", "Your name", "example: Ravi Kumar"),
                ("father", "Father\'s name", "example: Ram Kumar"),
                ("age", "Age", "example: 28"),
                ("address", "Full address", "village/area"),
                ("kind", "Type of affidavit", "NAME / ADDRESS / INCOME / GAP / DOB"),
                ("new", "Correct / new detail", "example: Ravi Kumar"),
                ("old", "Old / as per record", "example: Rabi Kumar"),
                ("place", "Place", "example: Patna"),
                ("date", "Date", "example: 15-11-2026")],
}


# ============================================================
#  3) 🕵️ PHOTO INFO + FAKE / EDIT DETECTOR
# ============================================================


# ============================================================
#  4) ⚡ MEDIA STUDIO (ffmpeg jadoo — koi API nahi)
# ============================================================
def _ff(args: list, timeout: int = 600) -> subprocess.CompletedProcess:
    """v77: har ffmpeg encode ab HEAVY GATE se guzarta hai.

    Render free = 512 MB. 3-4 log ek saath "video compress"/"ringtone"
    dabayein to 4 ffmpeg process milkar box ko OOM-kill kar dete the
    (bot mar jata, user ko "crash" dikhta). Ab ek saath sirf
    HEAVY_MAX_SLOTS (default 2) encode chalte hain; bheed ho to ye
    returncode=124 deta hai aur upar wala caller user ko saaf message de
    deta hai — process KABHI marta nahi.
    """
    cmd = [ffmpeg_path(), "-hide_banner", "-y"] + list(args)
    try:
        from modules.core import heavy as _hg
    except Exception:                                          # noqa: BLE001
        _hg = None                                             # gate na mila -> jaisa tha waisa
    if _hg is None:
        return subprocess.run(cmd, capture_output=True, timeout=timeout)
    try:
        with _hg.gate("ffmpeg"):
            return subprocess.run(cmd, capture_output=True, timeout=timeout)
    except _hg.HeavyBusy as e:
        return subprocess.CompletedProcess(cmd, 124, b"", str(e.user_msg).encode())


def _out(cp: subprocess.CompletedProcess, path: str, extra: dict = None) -> dict:
    if cp.returncode != 0 or not os.path.exists(path) or os.path.getsize(path) == 0:
        err = (cp.stderr or b"").decode(errors="ignore").strip().splitlines()
        msg = err[-1] if err else "ffmpeg fail"
        return {"ok": False, "error": msg[:180]}
    with open(path, "rb") as fh:
        data = fh.read()
    res = {"ok": True, "bytes": data, "size_mb": round(len(data) / 1048576, 2)}
    if extra:
        res.update(extra)
    return res


def audio_cut(data: bytes, start: str, end: str = "", fmt: str = "mp3") -> dict:
    """Audio ka hissa kaato (ringtone). start/end = 'mm:ss' ya seconds."""
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    pin, pout = _tmp("." + fmt), _tmp("." + fmt)
    try:
        _write_media(pin, data)
        args = ["-i", pin, "-ss", str(start)]
        if end:
            args += ["-to", str(end)]
        args += ["-vn"]
        if fmt == "mp3":
            args += ["-codec:a", "libmp3lame", "-q:a", "2"]
        cp = _ff(args + [pout])
        extra = {"duration": round(ffprobe_duration(pout), 1)}
        return _out(cp, pout, extra)
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


def _write_media(path: str, data) -> int:
    """Media input ko temp file me utaro. Badi file (MappedFile) RAM se guzarti
    hi nahi — copy ho jati hai disk se disk (v79, 150MB support ke liye)."""
    _p = getattr(data, "path", "") or ""
    if _p:
        try:
            import shutil
            shutil.copyfile(_p, path)
            return os.path.getsize(path)
        except Exception:                                       # noqa: BLE001
            pass
    b = _as_bytes(data)
    with open(path, "wb") as fh:
        fh.write(b)
    return len(b)


def _as_bytes(data) -> bytes:
    """Jo bhi aaye (bytes / BytesIO / str / None) -> likhne-yogy bytes.

    v78: download fail hone par callers kabhi str ya None bhej dete the, aur
    `open(pin,'wb').write(data)` par `TypeError: a bytes-like object is
    required, not 'str'` seedha tool crash kar deta tha. Ab khaali bytes
    chale jaate hain -> ffmpeg apni saaf error deta hai, crash nahi.
    """
    try:
        if data is None:
            return b""
        if hasattr(data, "getvalue"):                     # io.BytesIO
            data = data.getvalue()
        if isinstance(data, (bytes, bytearray, memoryview)):
            return bytes(data)
    except Exception:                                      # noqa: BLE001
        pass
    return b""


def make_ringtone(data: bytes, start: str = "0", dur: int = 30) -> dict:
    res = audio_cut(data, start, str(int(float(start)) + int(dur)) if str(start).replace(".", "").isdigit() else "", "mp3")
    return res


def eff_8d(data: bytes) -> dict:
    """8D audio — gaana kaan me ghumta hua feel."""
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    pin, pout = _tmp(".mp3"), _tmp(".mp3")
    try:
        _write_media(pin, data)
        filt = ("apulsator=hz=0.09,"
                "aecho=0.8:0.88:60:0.4,"
                "aformat=channel_layouts=stereo")
        cp = _ff(["-i", pin, "-af", filt, "-codec:a", "libmp3lame", "-q:a", "2", pout], timeout=900)
        return _out(cp, pout, {"effect": "8D"})
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


def bass_boost(data: bytes, gain_db: int = 8) -> dict:
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    pin, pout = _tmp(".mp3"), _tmp(".mp3")
    try:
        _write_media(pin, data)
        filt = f"bass=g={gain_db},loudnorm=I=-16:TP=-1.5:LRA=11"
        cp = _ff(["-i", pin, "-af", filt, "-codec:a", "libmp3lame", "-q:a", "2", pout], timeout=900)
        return _out(cp, pout, {"effect": f"Bass +{gain_db}dB"})
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


def make_karaoke(data: bytes) -> dict:
    """Gaana hata ke sirf music (center channel cancel) — karaoke style."""
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    pin, pout = _tmp(".mp3"), _tmp(".mp3")
    try:
        _write_media(pin, data)
        filt = ("pan=stereo|c0=c0-0.9*c1|c1=c1-0.9*c0,"
                "highpass=f=120,alimiter=limit=0.95")
        cp = _ff(["-i", pin, "-af", filt, "-codec:a", "libmp3lame", "-q:a", "2", pout], timeout=900)
        res = _out(cp, pout, {"effect": "Karaoke (vocal cut)"})
        if res.get("ok"):
            res["note"] = "Vocals are reduced by 80-90% (studio mixing may vary)."
        return res
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


VOICE_PRESETS = {
    "bachcha": ("Girl/Child voice (thin)", "asetrate=44100*1.35,aresample=44100,atempo=1/1.35"),
    "motu": ("Deep/Heavy voice", "asetrate=44100*0.78,aresample=44100,atempo=1/0.78"),
    "robot": ("Robot voice", "afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)',acrusher=bits=6:mode=log:aa=1"),
    "bhoot": ("Ghost/Scary voice", "asetrate=44100*0.82,aresample=44100,atempo=1/0.82,aecho=0.8:0.85:500:0.45"),
    "gadget": ("Radio/Gadget voice", "highpass=f=700,lowpass=f=3000,acrusher=bits=8:mode=log:aa=1"),
    "pahad": ("Echo voice", "aecho=0.85:0.9:700:0.5"),
}


def voice_change(data: bytes, preset: str) -> dict:
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    if preset not in VOICE_PRESETS:
        return {"ok": False, "error": "preset not understood"}
    pin, pout = _tmp(".mp3"), _tmp(".mp3")
    try:
        _write_media(pin, data)
        lbl, filt = VOICE_PRESETS[preset]
        cp = _ff(["-i", pin, "-af", filt, "-codec:a", "libmp3lame", "-q:a", "3", pout], timeout=900)
        return _out(cp, pout, {"effect": lbl})
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


_VIDEO_EXT_OK = (".mp4", ".mkv", ".mov", ".webm", ".m4v", ".3gp", ".avi")


def video_trim(data: bytes, start: str, end: str, ext: str = ".mp4") -> dict:
    """Video ka hissa kaato aur WhatsApp-friendly chhota MP4 banao."""
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    pin, pout = _tmp(ext if ext in _VIDEO_EXT_OK else ".mp4"), _tmp(".mp4")
    try:
        _write_media(pin, data)
        cp = _ff(["-ss", str(start), "-to", str(end), "-i", pin,
                  "-vf", "scale='min(1280,iw)':-2",
                  "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26", "-maxrate", "1800k", "-bufsize", "3600k",
                  "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", pout], timeout=1500)
        return _out(cp, pout, {"duration": round(ffprobe_duration(pout), 1)})
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


def video_compress(data: bytes, target_mb: float = 18.0, ext: str = ".mp4", max_seconds: float = 150.0) -> dict:
    """Video ko target size ke andar laao (CRF iterate — size pakka target ke andar)."""
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    pin, pout = _tmp(ext if ext in _VIDEO_EXT_OK else ".mp4"), _tmp(".mp4")
    try:
        _write_media(pin, data)
        dur = ffprobe_duration(pin) or 30.0
        if dur > max_seconds:
            return {"ok": False, "too_long": True, "duration": round(dur, 1),
                    "error": f"Video is {int(dur)} seconds long — this is too big to compress fast. "
                             f"First use ✂️ TRIM to make it {int(max_seconds)} seconds short, then compress."}
        # agar pehle se hi target se chhoti hai to dobara kyun
        if len(data) <= target_mb * 1048576:
            return {"ok": True, "bytes": data, "size_mb": round(len(data) / 1048576, 2),
                    "note": "File pehle se hi target se chhoti thi — jaisi hai waisi bhej di.", "duration": round(dur, 1)}
        vf = "scale='min(1280,iw)':-2"
        for crf in (26, 30, 33, 36):
            cp = _ff(["-i", pin, "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast",
                      "-crf", str(crf), "-maxrate", "1600k", "-bufsize", "3200k",
                      "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", pout], timeout=1500)
            res = _out(cp, pout, {"duration": round(dur, 1), "crf": crf, "target_mb": target_mb})
            if not res.get("ok"):
                return res
            if res.get("size_mb", 99) <= target_mb:
                res["note"] = f"Quality level CRF {crf} reached the target size."
                return res
        return res  # sabse chhoti koshish (36) — jo bani
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


def video_to_mp3(data: bytes, ext: str = ".mp4") -> dict:
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    pin, pout = _tmp(ext if ext in _VIDEO_EXT_OK else ".mp4"), _tmp(".mp3")
    try:
        _write_media(pin, data)
        cp = _ff(["-i", pin, "-vn", "-codec:a", "libmp3lame", "-q:a", "2", pout], timeout=1200)
        return _out(cp, pout, {"duration": round(ffprobe_duration(pout), 1)})
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


def make_status_video(photo_bytes: bytes, audio_bytes: bytes, text: str = "",
                      seconds: float = 30.0, blur_bg: bool = True) -> dict:
    """
    Status video (9:16 = 1080x1920): photo + gaana + neeche apna likha text.
    WhatsApp / Instagram status me seedha daal sakte ho.
    """
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg not found"}
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        Image = None
    p_photo = _tmp(".jpg")
    p_audio = _tmp(".mp3")
    p_out = _tmp(".mp4")
    p_canvas = _tmp(".png")
    try:
        _write_media(p_photo, photo_bytes)
        _write_media(p_audio, audio_bytes)
        dur = min(max(ffprobe_duration(p_audio) or seconds, 3.0), max(seconds, 3.0))

        # ---- canvas 1080x1920 banao: photo upar, neeche text ----
        if Image:
            W, H = 1080, 1920
            base = Image.new("RGB", (W, H), (12, 12, 18))
            try:
                ph = Image.open(p_photo).convert("RGB")
                ph.load()
            except Exception:                                   # noqa: BLE001
                # v78: photo asli image nahi thi to PIL ka
                # UnidentifiedImageError seedha tool crash kar raha tha.
                return {"ok": False,
                        "error": "Photo padhi nahi ja saki — JPG/PNG bhejo."}
            ph.thumbnail((W, 1120))
            base.paste(ph, ((W - ph.width) // 2, 250))
            if text:
                dr = ImageDraw.Draw(base)
                f = None
                for cand in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                             "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
                    if os.path.exists(cand):
                        f = ImageFont.truetype(cand, 64)
                        break
                f = f or ImageFont.load_default()
                y = 250 + ph.height + 90
                for line in re.findall(r".{1,28}", text)[:5]:
                    w = dr.textlength(line, font=f)
                    dr.text(((W - int(w)) // 2, y), line, font=f, fill=(255, 255, 255))
                    y += 84
            base.save(p_canvas)
            vin = ["-loop", "1", "-framerate", "25", "-i", p_canvas]
        else:
            vin = ["-loop", "1", "-framerate", "25", "-i", p_photo]

        args = vin + ["-i", p_audio,
                      "-t", f"{dur:.1f}",
                      "-r", "25", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                      "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                      "-shortest", "-movflags", "+faststart",
                      "-af", "afade=t=in:st=0:d=0.4", "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x0c0c12,fade=t=in:st=0:d=0.5",
                      p_out]
        cp = _ff(args, timeout=1800)
        return _out(cp, p_out, {"duration": round(dur, 1)})
    finally:
        for p in (p_photo, p_audio, p_out, p_canvas):
            try:
                os.remove(p)
            except Exception:
                pass


# ---------- YouTube → MP3 (yt-dlp, jab user link de) ----------
def youtube_mp3(url: str, quality: str = "192") -> dict:
    try:
        import yt_dlp
    except Exception:
        return {"ok": False, "error": "yt-dlp is not installed"}
    out = _tmp(".mp3")
    opts = {
        "format": "bestaudio/best",
        "outtmpl": out[:-4] + ".%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                            "preferredquality": quality, "nopostoverwrites": True}],
        "retries": 2,
        "socket_timeout": 30,
    }
    if _FFMPEG:
        opts["ffmpeg_location"] = _FFMPEG
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        title = (info or {}).get("title") or "audio"
        uploader = (info or {}).get("uploader") or ""
        dur = (info or {}).get("duration") or 0
        real = out[:-4] + ".mp3"
        if not os.path.exists(real):
            return {"ok": False, "error": "Could not make the MP3 (the link may be private or age-restricted)"}
        with open(real, "rb") as fh:
            data = fh.read()
        os.remove(real)
        return {"ok": True, "bytes": data, "title": title, "uploader": uploader,
                "duration": dur, "size_mb": round(len(data) / 1048576, 2)}
    except Exception as e:
        return {"ok": False, "error": f"Not found on YouTube: {str(e)[:140]}"}


# ============================================================
#  4b) 🗣️ TEXT → HINDI VOICE (edge-tts, free neural voices)
# ============================================================
# Microsoft ke FREE neural Hindi voices — ekdum real/desi awaaz (robotic nahi).
# Koi API key nahi, koi paid service nahi. Text bhejo → MP3 audio aata hai.
TTS_HI_VOICES = {
    "male":   "hi-IN-MadhurNeural",   # mard awaaz (natural, desi)
    "female": "hi-IN-SwaraNeural",    # aurat awaaz (natural, desi)
}
TTS_MAX_CHARS = 1500


async def hindi_tts(text: str, voice: str = "male", rate: str = "+0%") -> dict:
    """Text → real Hindi MP3 (edge-tts neural). Returns {ok, bytes, size_mb}."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "Pehle text bhejo."}
    if len(text) > TTS_MAX_CHARS:
        text = text[:TTS_MAX_CHARS]
    voice_id = TTS_HI_VOICES.get(voice, TTS_HI_VOICES["male"])
    out = _tmp(".mp3")
    try:
        import edge_tts  # lazy — Render par pip se aata hai
        comm = edge_tts.Communicate(text, voice_id, rate=rate)
        await comm.save(out)
        if not os.path.exists(out) or os.path.getsize(out) < 500:
            return {"ok": False, "error": "Audio nahi bana (internet/voice issue). Thodi der baad dobara try karo."}
        with open(out, "rb") as fh:
            data = fh.read()
        return {"ok": True, "bytes": data, "size_mb": round(len(data) / 1048576, 2)}
    except Exception as e:
        return {"ok": False, "error": f"Voice nahi banna: {str(e)[:160]}"}
    finally:
        try:
            os.remove(out)
        except OSError:
            pass


# ============================================================
#  5) (BONUS) 🪔 RUHU KAAL + DIN SHUBH MUHURAT (offline hisaab)
# ============================================================
