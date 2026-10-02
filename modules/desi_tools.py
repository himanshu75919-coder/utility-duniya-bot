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
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta

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


def detect_bank(text: str) -> str:
    low = (text or "").lower()[:6000]
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
        return {"ok": False, "error": "pdfplumber install nahi hai (requirements check karo)"}

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
                        "error": "Ye password sahi nahi hai"}
            return {"ok": False, "locked": True, "error": "PDF locked (password) hai — password chahiye"}
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
                "error": "Is PDF me transaction table nahi mili. (Scanned photo-PDF hai? Usme text nahi hota.)"}

    tot_dr = round(sum(r["debit"] for r in rows), 2)
    tot_cr = round(sum(r["credit"] for r in rows), 2)
    opening = rows[0]["balance"] - rows[0]["credit"] + rows[0]["debit"] if rows else 0
    closing = rows[-1]["balance"] if rows[-1]["balance"] else round(opening + tot_cr - tot_dr, 2)
    months = sorted({r["date"][3:] for r in rows if len(r["date"]) == 10})
    summary = {
        "count": len(rows), "total_debit": tot_dr, "total_credit": tot_cr,
        "opening": round(opening, 2), "closing": round(closing, 2),
        "months": len(months), "period": f"{rows[0]['date']} se {rows[-1]['date']}",
    }

    # CSV
    buf = io.StringIO()
    buf.write("Date,Detail,Debit (nikala),Credit (aaya),Balance\n")
    for r in rows:
        d = (r["detail"] or "").replace('"', "'").replace(",", " ")
        buf.write(f'{r["date"]},"{d}",{r["debit"] or ""},{r["credit"] or ""},{r["balance"] or ""}\n')
    buf.write(f"\nTOTAL,,{tot_dr},{tot_cr},{closing}\n")
    return {"ok": True, "rows": rows, "summary": summary, "bank": bank,
            "csv": buf.getvalue().encode("utf-8-sig")}


def statement_summary_text(res: dict) -> str:
    s = res["summary"]
    return (
        "🏦 <b>BANK STATEMENT READY ✅</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏛️ <b>Bank:</b> {res.get('bank', 'UNKNOWN')}\n"
        f"📅 <b>Period:</b> {s['period']}\n"
        f"🧾 <b>Transactions:</b> {s['count']}  ({s['months']} mahine)\n"
        f"🔴 <b>Total nikala (Debit):</b> ₹{s['total_debit']:,.2f}\n"
        f"🟢 <b>Total aaya (Credit):</b> ₹{s['total_credit']:,.2f}\n"
        f"📂 <b>Opening:</b> ₹{s['opening']:,.2f}   →   <b>Closing:</b> ₹{s['closing']:,.2f}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⬇️ Neeche Excel/CSV file — Google Sheets ya Excel me kholo, seedha table ban jayega."
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
        return {"ok": False, "error": f"'{from_unit}' samajh nahi aaya. Likho: bigha, katha, dhur, decimal, acre, sqft, gaj, hectare"}
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
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟩 <b>Sq Feet:</b> {res['sqft']}  |  <b>Sq Meter:</b> {res['sqm']}\n"
        f"🌾 <b>Bigha:</b> {res['bigha']}  |  <b>Kattha:</b> {res['katha']}  |  <b>Dhur:</b> {res['dhur']}\n"
        f"🧮 <b>Decimal (Dismil):</b> {res['decimal']}  |  <b>Gaj:</b> {res['gaj']}\n"
        f"🏞️ <b>Acre:</b> {res['acre']}  |  <b>Hectare:</b> {res['hectare']}  |  <b>Guntha:</b> {res['guntha']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Bihar ka deshi naap: 1 Bigha = 20 Kattha = 1361.25 Sq Ft har Kattha · 1 Dhur = 68.06 Sq Ft</i>\n"
        "<b>Kaam:</b> zameen kharidna/bechna, registry, naap-taul — sab me."
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
        slab_note = "Mahila khareedar — 1% kam stamp"
    elif b.startswith("j") or "joint" in b:
        pct = max(st["stamp_pct"] - 1.0, 0.5)
        slab_note = "Joint (mahila saath) — 1% kam stamp"
    for limit, p in st["male_slab"]:
        if value <= limit * 10000000 or (limit < 1e8):  # slab ₹ crore ke hisaab se (approx)
            break
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
        return "❌ Hishaab nahi bana."
    extra = ""
    if r.get("panchayat"):
        extra = f"🏘️ <b>Panchayat/Anchal (extra {r['panchayat_pct']}%):</b> ₹{r['panchayat']:,.0f}\n"
    return (
        f"🏛️ <b>REGISTRY TOTAL KHARCHA ({r['state']})</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📐 <b>Zameen:</b> {r['area_sqft']:,.0f} Sq Ft  ×  <b>MVR ₹{r['rate']:,.0f}/SqFt</b>\n"
        f"💰 <b>Kul Value:</b> ₹{r['value']:,.0f}\n"
        f"👤 <b>Khareedar:</b> {r['note']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Stamp Duty ({r['stamp_pct']}%):</b> ₹{r['stamp']:,.0f}\n"
        f"📝 <b>Registration ({r['reg_pct']}%):</b> ₹{r['reg']:,.0f}\n"
        f"{extra}"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Kul Kharcha (sarkari): ₹{r['total']:,.0f}</b>\n\n"
        "➕ <b>Alag se:</b> notary/advocate fee, e-stamp, gawah, dalali — ye riwaaj ke hisaab se.\n"
        "<i>⚠️ Ye andaaza hai (tumhare bataye MVR par) — final amount sub-registrar office me confirm karo.</i>"
    )


# ---------- Kagaz templates (PDF) ----------
def _pdf_doc(title: str, lines: list, footer: str = "") -> bytes:
    """Simple, saaf sarkari-style PDF (reportlab). Sanskrit/Hindi ke liye English text rakha hai."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as _canvas  # noqa

    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
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
    "kirayanama": [("landlord", "Makan malik ka naam", "jaise: Ramesh Kumar"),
                   ("landlord_addr", "Malik ka pata", "gaon/mohalla, jila"),
                   ("tenant", "Kirayedar ka naam", "jaise: Suresh Sharma"),
                   ("tenant_addr", "Kirayedar ka pata", "gaon/mohalla, jila"),
                   ("property", "Makan/dukaan ka details", "jaise: 2 kamra, 1x rasoi, chhat"),
                   ("place", "Jagah (kahan hai)", "jaise: Boring Road, Patna"),
                   ("rent", "Kiraya (mahine ka ₹)", "jaise: 6000"),
                   ("deposit", "Advance/Deposit ₹", "jaise: 12000"),
                   ("months", "Kitne mahine ka agreement", "jaise: 11"),
                   ("start", "Kab se", "jaise: 01-11-2026"),
                   ("end", "Kab tak", "jaise: 30-09-2027")],
    "affidavit": [("name", "Aapka naam", "jaise: Ravi Kumar"),
                  ("father", "Pita/Pat ka naam", "jaise: Ram Kumar"),
                  ("age", "Umar", "jaise: 32"),
                  ("address", "Pura pata", "jaise: Ward 5, Sitamarhi"),
                  ("purpose", "Affidavit kisliye", "jaise: naam sudhar / pata / income"),
                  ("body", "Kya likhna hai (poora bayan)", "jaise: mera sahi naam Ravi Kumar hai..."),
                  ("place", "Jagah", "jaise: Patna"),
                  ("date", "Tareekh", "jaise: 15-11-2026")],
    "notice138": [("from_name", "Aapka naam (bhejne wale)", "jaise: Suresh Kumar"),
                  ("from_addr", "Aapka pata", "gaon/mohalla"),
                  ("to_name", "Jisko notice bhejna hai", "jaise: Mahesh Yadav"),
                  ("to_addr", "Unka pata", "gaon/mohalla"),
                  ("amount", "Cheque ka amount ₹", "jaise: 50000"),
                  ("cheque_no", "Cheque number", "jaise: 456789"),
                  ("cheque_date", "Cheque ki tareekh", "jaise: 10-08-2026"),
                  ("bank", "Bank ka naam", "jaise: SBI"),
                  ("present_date", "Bank me lagane ki tareekh", "jaise: 12-09-2026"),
                  ("reason", "Bank ne kya likha", "jaise: Fund Insufficient"),
                  ("advocate", "Advocate ka naam (ya khali)", "jaise: Adv. A.K. Singh")],
    "bayana": [("seller", "Beche wale ka naam", "jaise: Ram Singh"),
               ("seller_father", "Uske pita ka naam", "jaise: Shyam Singh"),
               ("seller_addr", "Beche wale ka pata", "gaon/mohalla"),
               ("buyer", "Kharidne wale ka naam", "jaise: Ajay Kumar"),
               ("buyer_father", "Uske pita ka naam", "jaise: Vijay Kumar"),
               ("buyer_addr", "Kharidne wale ka pata", "gaon/mohalla"),
               ("property", "Zameen/Makan ki jankari", "jaise: 2 katha zameen, dhan"),
               ("khata", "Khata number", "jaise: 342"),
               ("khasra", "Khasra/Plot number", "jaise: 1125"),
               ("mouza", "Mouza / gaon", "jaise: Bishunpura"),
               ("thana", "Thana", "jaise: Runnisaidpur"),
               ("anchal", "Anchal/Block", "jaise: Belsand"),
               ("district", "Jila", "jaise: Sitamarhi"),
               ("area", "Kitni zameen (bigha/kattha)", "jaise: 2 katha 5 dhur"),
               ("total", "Kul sauda ₹", "jaise: 800000"),
               ("token", "Aaj ka bayana ₹", "jaise: 100000"),
               ("balance", "Baki paisa ₹", "jaise: 700000"),
               ("reg_date", "Registry ki tareekh", "jaise: 20-12-2026")],
    "loan": [("borrower", "Karz lene wale ka naam", "jaise: Rahul Kumar"),
             ("father", "Uske pita ka naam", "jaise: Suresh Kumar"),
             ("address", "Uska pata", "gaon/mohalla"),
             ("lender", "Paisa dene wale ka naam", "jaise: Mahesh Kumar"),
             ("lender_addr", "Dene wale ka pata", "gaon/mohalla"),
             ("amount", "Amount ₹", "jaise: 50000"),
             ("words", "Amount shabdon me", "jaise: Fifty Thousand"),
             ("mode", "Paisa kaise diya", "jaise: Cash / UPI"),
             ("rate", "Byaaj (rate)", "jaise: 3% per month"),
             ("basis", "byaaj ka aadhaar", "month / saal"),
             ("due", "Kab tak wapas karega", "jaise: 31-03-2027"),
             ("place", "Jagah", "jaise: Sitamarhi"),
             ("date", "Tareekh", "jaise: 15-11-2026")],
    "nameaff": [("name", "Aapka naam", "jaise: Ravi Kumar"),
                ("father", "Pita ka naam", "jaise: Ram Kumar"),
                ("age", "Umar", "jaise: 28"),
                ("address", "Pura pata", "gaon/mohalla"),
                ("kind", "Kis type ka affidavit", "NAME / ADDRESS / INCOME / GAP / DOB"),
                ("new", "Sahi/naya detail", "jaise: Ravi Kumar"),
                ("old", "Purana/record me likha", "jaise: Rabi Kumar"),
                ("place", "Jagah", "jaise: Patna"),
                ("date", "Tareekh", "jaise: 15-11-2026")],
}


# ============================================================
#  3) 🕵️ PHOTO INFO + FAKE / EDIT DETECTOR
# ============================================================
def _gps_decimal(gps, ref) -> float:
    def _to_deg(v):
        try:
            d, m, s = (float(x) for x in v)
            return d + m / 60 + s / 3600
        except Exception:
            return 0.0

    try:
        val = _to_deg(gps)
        if ref in ("S", "W"):
            val = -val
        return round(val, 6)
    except Exception:
        return 0.0


def photo_forensics(image_bytes: bytes) -> dict:
    """
    EXIF (camera, date, GPS) + ELA (edit ke nishaan) + quality check.
    Sab offline — koi API nahi.
    """
    out = {"ok": False, "exif": {}, "flags": [], "notes": []}
    try:
        from PIL import Image, ImageChops, ImageDraw
        import numpy as np
    except Exception as e:
        out["error"] = f"Pillow/numpy nahi mila: {e}"
        return out

    try:
        im = Image.open(io.BytesIO(image_bytes))
        im.load()
    except Exception as e:
        out["error"] = f"Photo kholne me dikkat: {e}"
        return out

    ex = {}
    try:
        raw = im.getexif() or {}
        for k, v in raw.items():
            tag = {271: "Make", 272: "Model", 305: "Software", 306: "DateTime", 36867: "DateTimeOriginal",
                   36868: "DateTimeDigitized", 274: "Orientation", 296: "ResolutionUnit", 34855: "ISO",
                   33437: "FNumber", 33434: "ExposureTime", 37386: "FocalLength", 42036: "LensModel"}.get(k)
            if tag:
                ex[tag] = str(v)
        gps_ifd = raw.get_ifd(0x8825) if hasattr(raw, "get_ifd") else {}
        if gps_ifd:
            lat = _gps_decimal(gps_ifd.get(2), gps_ifd.get(1, "N"))
            lon = _gps_decimal(gps_ifd.get(4), gps_ifd.get(3, "E"))
            if lat or lon:
                ex["GPS"] = f"{lat}, {lon}"
                ex["MapsLink"] = f"https://www.google.com/maps?q={lat},{lon}"
                if gps_ifd.get(1) or gps_ifd.get(3):
                    ex["GPSRef"] = f"{gps_ifd.get(1, '')}{gps_ifd.get(3, '')}"
    except Exception:
        pass

    out["exif"] = ex
    out["format"] = im.format or "?"
    out["size"] = f"{im.width} x {im.height}"
    out["mode"] = im.mode
    out["file_kb"] = round(len(image_bytes) / 1024, 1)

    # ---------- ELA + Noise-block analysis (edit ke nishaan) ----------
    ela_score, ela_verdict, ela_img, marked = 0.0, "—", None, None
    suspicious = 0
    try:
        rgb = im.convert("RGB")
        small = rgb.copy()
        small.thumbnail((720, 720))
        buf = io.BytesIO()
        small.save(buf, "JPEG", quality=90)
        buf.seek(0)
        recomp = Image.open(buf)
        diff = ImageChops.difference(small, recomp)
        arr = np.asarray(diff).astype("float32")
        ela_score = float(arr.mean())

        # block-wise ELA (16px) — median/MAD se bahar wale blocks = shak
        g = arr.mean(axis=2)
        h, w = g.shape
        bs = 16
        blocks = []
        for by in range(0, h - bs + 1, bs):
            for bx in range(0, w - bs + 1, bs):
                blocks.append((bx, by, float(g[by:by + bs, bx:bx + bs].mean())))
        vals = np.array([b[2] for b in blocks]) if blocks else np.array([0.0])
        med = float(np.median(vals))
        mad = max(float(np.median(np.abs(vals - med))), 0.30 * med, 0.25)
        hot = [b for b in blocks if b[2] > med + 6 * mad and b[2] > med * 1.7 + 0.8]

        # noise map (Laplacian std) — pasted/flat hisse alag noise dikhate hain
        gray = np.asarray(small.convert("L")).astype("float32")
        lap = np.abs(np.diff(gray, axis=0)[:, :-1]) + np.abs(np.diff(gray, axis=1)[:-1, :])
        nb = 32
        noises = []
        for by in range(0, lap.shape[0] - nb + 1, nb):
            for bx in range(0, lap.shape[1] - nb + 1, nb):
                noises.append((bx, by, float(lap[by:by + nb, bx:bx + nb].mean())))
        nvals = np.array([x[2] for x in noises]) if noises else np.array([0.0])
        nmed = float(np.median(nvals))
        flat = [n for n in noises if n[2] < max(nmed * 0.28, 1.0) and nmed > 6.0]
        flat_ratio = (len(flat) / max(len(noises), 1))
        if flat_ratio > 0.28:
            flat = []          # itni badi flat jagah = aakash/deewar (normal baat), shak nahi
        rough = [n for n in noises if n[2] > nmed * 3.2 and nmed > 4.0]

        suspicious = len(hot) + len(flat)
        std_all = float(g.std())

        if suspicious == 0:
            ela_verdict = "✅ Editing ke nishaan NAHI mile (photo asli lagti hai)"
        elif suspicious <= 4:
            ela_verdict = f"🟡 Halka shak — {suspicious} hisse alag lag rahe hain (filter/app ya halki editing ho sakti hai)"
        else:
            ela_verdict = f"🔴 Edit hone ka shak — {suspicious} hisse alag nikle (cut-paste/editing ke nishaan)"
        out["hot_blocks"] = len(hot)
        out["flat_blocks"] = len(flat)
        if rough:
            out["rough_blocks"] = len(rough)

        # ELA heatmap
        ela_img = Image.fromarray((np.clip(arr * 10, 0, 255)).astype("uint8"))

        # marked photo (shak wale block par laal dabba)
        marked = rgb.copy()
        md = ImageDraw.Draw(marked)
        scale_x = marked.width / max(small.width, 1)
        scale_y = marked.height / max(small.height, 1)
        for (bx, by, _v) in (hot[:12] + flat[:12]):
            x0, y0 = int(bx * scale_x), int(by * scale_y)
            x1 = int(min(bx + bs, small.width) * scale_x)
            y1 = int(min(by + bs, small.height) * scale_y)
            md.rectangle([x0, y0, x1, y1], outline=(255, 40, 40), width=max(2, int(3 * scale_x)))
        out["ela_std"] = round(std_all, 2)
        out["ela_score"] = round(ela_score, 2)
    except Exception as e:
        out["notes"].append(f"Edit-check fail: {e}")

    out["ela_verdict"] = ela_verdict
    out["ela_image"] = ela_img
    out["marked_image"] = marked
    out["suspicious_blocks"] = suspicious

    # ---------- Flags ----------
    if not ex:
        out["flags"].append("EXIF/meta data nahi mila — WhatsApp/Telegram/Instagram se aayi photo me company "
                            "meta hata deti hai (isliye asli-photo check ELA se hi ho raha hai).")
    sw = (ex.get("Software") or "").lower()
    if any(k in sw for k in ("photoshop", "lightroom", "snapseed", "picsart", "canva", "editor", "adobe", "pixlr", "meitu", "remaker")):
        out["flags"].append(f"⚠️ Photo '{ex.get('Software')}' me process hui hai (editing app ka nishaan).")
    if any(k in sw for k in ("whatsapp", "instagram", "telegram")):
        out["flags"].append(f"📲 Ye photo {ex.get('Software')} se bhejne par save hui hai (asli camera meta hat gaya).")
    if ex.get("DateTimeOriginal") and ex.get("DateTime") and ex["DateTimeOriginal"] != ex["DateTime"]:
        out["flags"].append("⚠️ Photo ki 'original date' aur 'save date' alag hain — baad me badli/save ki gayi hai.")
    if re.match(r"^Screenshot", str(im.format or ""), re.I) or (not ex and im.info.get("screenshot")):
        out["flags"].append("📱 Ye screenshot lagti hai (camera photo nahi).")

    out["ok"] = True
    return out


def photo_meta_text(res: dict) -> str:
    if not res.get("ok"):
        return f"❌ {res.get('error', 'Photo read nahi hui')}"
    ex = res.get("exif") or {}
    lines = [
        "🕵️ <b>PHOTO KI ASLI JANKARI</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📐 <b>Size:</b> {res['size']} px   |   <b>Format:</b> {res['format']}   |   <b>File:</b> {res['file_kb']} KB",
    ]
    if ex:
        if ex.get("Make") or ex.get("Model"):
            lines.append(f"📱 <b>Camera:</b> {ex.get('Make', '')} {ex.get('Model', '')}".strip())
        dt = ex.get("DateTimeOriginal") or ex.get("DateTime")
        if dt:
            lines.append(f"📅 <b>Kab kheechi (camera date):</b> {dt}")
        if ex.get("Software"):
            lines.append(f"⚙️ <b>Software/App:</b> {ex['Software']}")
        if ex.get("GPS"):
            lines.append(f"📍 <b>Jagah (GPS):</b> {ex['GPS']}\n🗺️ <a href=\"{ex.get('MapsLink')}\">Google Maps me kholo</a>")
        if ex.get("LensModel"):
            lines.append(f"🔭 <b>Lens:</b> {ex['LensModel']}")
        extra = []
        for k, lbl in (("FNumber", "F"), ("ExposureTime", "Shutter"), ("ISO", "ISO"), ("FocalLength", "Focal(mm)")):
            if ex.get(k):
                extra.append(f"{lbl} {ex[k]}")
        if extra:
            lines.append("🎛️ " + " · ".join(extra))
    else:
        lines.append("📭 <b>Camera meta:</b> Nahi mila (WhatsApp/Telegram ne hata diya, ya screenshot hai)")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🔍 <b>Edit Check (ELA):</b> {res.get('ela_verdict', '—')}",
        f"<i>(score {res.get('ela_score', 0)} · jitna kam utni asli)</i>",
    ]
    for f in res.get("flags", []):
        lines.append(f"• {f}")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "🖼️ Neeche <b>ELA</b> wali photo bhi bhej raha hoon — jahan white/chamakdar dhabbe hain, wahan edit ka shak hai.",
        "<i>⚠️ Ye court ka expert report nahi hai — sirf pakadne ka ishara. Bade maamle me forensic lab se verify karwao.</i>",
    ]
    return "\n".join(lines)


# ============================================================
#  4) ⚡ MEDIA STUDIO (ffmpeg jadoo — koi API nahi)
# ============================================================
def _ff(args: list, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run([ffmpeg_path(), "-hide_banner", "-y"] + args, capture_output=True, timeout=timeout)


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
        return {"ok": False, "error": "ffmpeg nahi mila"}
    pin, pout = _tmp("." + fmt), _tmp("." + fmt)
    try:
        open(pin, "wb").write(data)
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


def make_ringtone(data: bytes, start: str = "0", dur: int = 30) -> dict:
    res = audio_cut(data, start, str(int(float(start)) + int(dur)) if str(start).replace(".", "").isdigit() else "", "mp3")
    return res


def eff_8d(data: bytes) -> dict:
    """8D audio — gaana kaan me ghumta hua feel."""
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg nahi mila"}
    pin, pout = _tmp(".mp3"), _tmp(".mp3")
    try:
        open(pin, "wb").write(data)
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
        return {"ok": False, "error": "ffmpeg nahi mila"}
    pin, pout = _tmp(".mp3"), _tmp(".mp3")
    try:
        open(pin, "wb").write(data)
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
        return {"ok": False, "error": "ffmpeg nahi mila"}
    pin, pout = _tmp(".mp3"), _tmp(".mp3")
    try:
        open(pin, "wb").write(data)
        filt = ("pan=stereo|c0=c0-0.9*c1|c1=c1-0.9*c0,"
                "highpass=f=120,alimiter=limit=0.95")
        cp = _ff(["-i", pin, "-af", filt, "-codec:a", "libmp3lame", "-q:a", "2", pout], timeout=900)
        res = _out(cp, pout, {"effect": "Karaoke (vocal cut)"})
        if res.get("ok"):
            res["note"] = "Vocal 80-90% kam ho jata hai (studio mixing ke hisaab se farak hota hai)."
        return res
    finally:
        for p in (pin, pout):
            try:
                os.remove(p)
            except Exception:
                pass


VOICE_PRESETS = {
    "bachcha": ("Ladki/Bachcha awaaz (patli)", "asetrate=44100*1.35,aresample=44100,atempo=1/1.35"),
    "motu": ("Bhaari/Motu awaaz", "asetrate=44100*0.78,aresample=44100,atempo=1/0.78"),
    "robot": ("Robot awaaz", "afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)',acrusher=bits=6:mode=log:aa=1"),
    "bhoot": ("Bhoot/Dar wali awaaz", "asetrate=44100*0.82,aresample=44100,atempo=1/0.82,aecho=0.8:0.85:500:0.45"),
    "gadget": ("Gadget/Radio awaaz", "highpass=f=700,lowpass=f=3000,acrusher=bits=8:mode=log:aa=1"),
    "pahad": ("Pahad/Echo wali awaaz", "aecho=0.85:0.9:700:0.5"),
}


def voice_change(data: bytes, preset: str) -> dict:
    if not HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg nahi mila"}
    if preset not in VOICE_PRESETS:
        return {"ok": False, "error": "preset samajh nahi aaya"}
    pin, pout = _tmp(".mp3"), _tmp(".mp3")
    try:
        open(pin, "wb").write(data)
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
        return {"ok": False, "error": "ffmpeg nahi mila"}
    pin, pout = _tmp(ext if ext in _VIDEO_EXT_OK else ".mp4"), _tmp(".mp4")
    try:
        open(pin, "wb").write(data)
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
        return {"ok": False, "error": "ffmpeg nahi mila"}
    pin, pout = _tmp(ext if ext in _VIDEO_EXT_OK else ".mp4"), _tmp(".mp4")
    try:
        open(pin, "wb").write(data)
        dur = ffprobe_duration(pin) or 30.0
        if dur > max_seconds:
            return {"ok": False, "too_long": True, "duration": round(dur, 1),
                    "error": f"Video {int(dur)} second ki hai — itni badi compress karne me server zyada time lega. "
                             f"Pehle ✂️ TRIM se {int(max_seconds)} second se chhoti banao, phir compress karo."}
        # agar pehle se hi target se chhoti hai to dobara kyun
        if len(data) <= target_mb * 1048576:
            return {"ok": True, "bytes": data, "size_mb": round(len(data) / 1048576, 2),
                    "note": "File pehle se hi target se chhoti thi — waisi hi bhej di.", "duration": round(dur, 1)}
        vf = "scale='min(1280,iw)':-2"
        for crf in (26, 30, 33, 36):
            cp = _ff(["-i", pin, "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast",
                      "-crf", str(crf), "-maxrate", "1600k", "-bufsize", "3200k",
                      "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", pout], timeout=1500)
            res = _out(cp, pout, {"duration": round(dur, 1), "crf": crf, "target_mb": target_mb})
            if not res.get("ok"):
                return res
            if res.get("size_mb", 99) <= target_mb:
                res["note"] = f"Quality level CRF {crf} par target me aa gaya."
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
        return {"ok": False, "error": "ffmpeg nahi mila"}
    pin, pout = _tmp(ext if ext in _VIDEO_EXT_OK else ".mp4"), _tmp(".mp3")
    try:
        open(pin, "wb").write(data)
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
        return {"ok": False, "error": "ffmpeg nahi mila"}
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        Image = None
    p_photo = _tmp(".jpg")
    p_audio = _tmp(".mp3")
    p_out = _tmp(".mp4")
    p_canvas = _tmp(".png")
    try:
        open(p_photo, "wb").write(photo_bytes)
        open(p_audio, "wb").write(audio_bytes)
        dur = min(max(ffprobe_duration(p_audio) or seconds, 3.0), max(seconds, 3.0))

        # ---- canvas 1080x1920 banao: photo upar, neeche text ----
        if Image:
            W, H = 1080, 1920
            base = Image.new("RGB", (W, H), (12, 12, 18))
            ph = Image.open(p_photo).convert("RGB")
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
        return {"ok": False, "error": "yt-dlp install nahi hai"}
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
            return {"ok": False, "error": "MP3 ban nahi paya (link private/age-restricted ho sakta hai)"}
        with open(real, "rb") as fh:
            data = fh.read()
        os.remove(real)
        return {"ok": True, "bytes": data, "title": title, "uploader": uploader,
                "duration": dur, "size_mb": round(len(data) / 1048576, 2)}
    except Exception as e:
        return {"ok": False, "error": f"YouTube se nahi mila: {str(e)[:140]}"}


# ============================================================
#  5) (BONUS) 🪔 RUHU KAAL + DIN SHUBH MUHURAT (offline hisaab)
# ============================================================
def _sun_times(lat: float, lon: float, d: datetime) -> tuple:
    """Sunrise/sunset (NOAA simple formula) — 0.833° refraction ke saath."""
    import math
    n = d.timetuple().tm_yday
    lng_hour = lon / 15.0
    t = n + ((6 - lng_hour) / 24.0)
    M = (0.9856 * t) - 3.289
    L = M + (1.916 * math.sin(math.radians(M))) + (0.020 * math.sin(math.radians(2 * M))) + 282.634
    L %= 360
    RA = math.degrees(math.atan(0.91764 * math.tan(math.radians(L)))) % 360
    Lq = (math.floor(L / 90)) * 90
    RAq = (math.floor(RA / 90)) * 90
    RA = (RA + (Lq - RAq)) / 15.0
    sinDec = 0.39782 * math.sin(math.radians(L))
    cosDec = math.cos(math.asin(sinDec))
    cosH = (math.cos(math.radians(90.833)) - (sinDec * math.sin(math.radians(lat)))) / (cosDec * math.cos(math.radians(lat)))
    if cosH > 1 or cosH < -1:
        return (0.0, 0.0)
    H = 360 - math.degrees(math.acos(cosH))
    H /= 15.0
    T = H + RA - (0.06571 * t) - 6.622
    UT = (T - lng_hour) % 24
    sr = (UT + 5.5) % 24  # IST
    H2 = math.degrees(math.acos(cosH)) / 15.0
    T2 = H2 + RA - (0.06571 * t) - 6.622
    UT2 = (T2 - lng_hour) % 24
    ss = (UT2 + 5.5) % 24
    return (sr, ss)


def _h(hours: float) -> str:
    h = int(hours) % 24
    m = int(round((hours - int(hours)) * 60))
    if m == 60:
        h, m = h + 1, 0
    return f"{h:02d}:{m:02d}"


RAHU_SEG = {"Monday": 2, "Tuesday": 7, "Wednesday": 5, "Thursday": 6, "Friday": 4, "Saturday": 3, "Sunday": 8}
RAHU_HINDI = {"Monday": "Somvar", "Tuesday": "Mangalvar", "Wednesday": "Budhvar", "Thursday": "Guruvar",
              "Friday": "Shukravar", "Saturday": "Shanivar", "Sunday": "Ravivar"}


def rahu_kaal(d: datetime = None, lat: float = 25.5941, lon: float = 85.1376) -> dict:
    """
    Aaj ka Rahu Kaal + din ke 8 hisse (Choghadiya style) — Bihar (Patna) default, user apna jila daal sakta hai.
    """
    d = d or datetime.now()
    day = d.strftime("%A")
    sr, ss = _sun_times(lat, lon, d)
    if not sr and not ss:
        return {"ok": False, "error": "Is jagah ka sunrise/sunset nahi nikal paya"}
    day_len = (ss - sr) % 24
    part = day_len / 8.0
    idx = RAHU_SEG.get(day, 2)
    rahu_start = sr + (idx - 1) * part
    out = {
        "ok": True, "day": RAHU_HINDI.get(day, day), "sunrise": _h(sr), "sunset": _h(ss),
        "rahu": f"{_h(rahu_start)} – {_h(rahu_start + part)}",
        "daylight": f"{int(day_len)}h {int((day_len % 1) * 60)}m",
        "parts": [{"name": f"Part {i+1}", "time": f"{_h(sr + i*part)} – {_h(sr + (i+1)*part)}"} for i in range(8)],
        "advice": "Rahu Kaal me naya kaam/khareed/shaadi/registry/gaadi lena — sab avoid karo. Isme jo kaam "
                  "chal raha ho, use poora karna theek hai.",
    }
    return out


def rahu_text(r: dict) -> str:
    if not r.get("ok"):
        return f"❌ {r.get('error', 'Error')}"
    return (
        f"🪔 <b>AAJ KA RAHU KAAL ({r['day']})</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌅 <b>Sunrise:</b> {r['sunrise']}   |   🌇 <b>Sunset:</b> {r['sunset']}\n"
        f"🚫 <b>Rahu Kaal:</b> <b>{r['rahu']}</b>\n"
        f"⏳ <b>Din:</b> {r['daylight']} (8 hisse)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(f"• <b>{p['name']}:</b> {p['time']}" for p in r["parts"])
        + "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <i>{r['advice']}</i>"
    )
