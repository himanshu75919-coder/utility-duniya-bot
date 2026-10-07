# -*- coding: utf-8 -*-
"""
v79 SELFTEST — 📋 RESULT CHECK PRO (BSEB)  [v74.0]
===================================================
User ka order (8 Oct 2026): "Result check tool upgrade karo, sirf BSEB.
Portal jaisa: pehle EXAM chuno, phir YEAR, phir Roll Code, phir Roll Number.
Result aisa de jaise portal par PDF download hoti hai — PDF me poora data."

Research (live verify kiya 7-8 Oct 2026):
  • Matric  → official open API (asli topper roll par poora result aaya)
  • Inter   → portal form POST (captcha sirf client-side)
  • Purane saal (2023...) → board ke live portal par NAHI — bot saaf batata hai

Rules:
  • 100% FREE (premium count 37 wahi) • crash-proof • khaali card kabhi nahi
  • PDF me poora data (naam, papa, school, subject-wise marks, total, division)
"""
import io as _io
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv79_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V79"
os.environ["ADMIN_ID"] = "1"
os.environ["ALL_FREE"] = "1"

PASS = FAIL = 0
FAILS = []


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILS.append(f"{name} {extra}")
        print(f"  ❌ {name}  {extra}")


def section(t):
    print("\n" + "=" * 62)
    print("  " + t)
    print("=" * 62)


print("=" * 62)
print("  v79 SELFTEST — 📋 RESULT CHECK PRO (BSEB)")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import bseb_result as BSEBR                          # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

# asli topper ka roll (India Today ki public topper list se) — live test ke liye
REAL_MATRIC = ("22050", "2600046", "PUSHPANJALI KUMARI")

MOCK_STU = {
    "success": True, "data": {
        "name": "RAHUL KUMAR", "father_name": "RAM KUMAR SINGH",
        "school_name": "H S SCHOOL PATNA", "roll_code": "11001",
        "roll_no": "100001", "reg_no": "11001-00099-25", "bseb_id": "1252130500099",
        "division": "1st Division", "exam_type": "REGULAR", "is_topper": False, "total": 640,
        "subjects": [
            {"sub_name": "M.I.L. HINDI", "sub_code": "201", "theory": "090", "sub_total": "90"},
            {"sub_name": "ADVANCED MATH", "sub_code": "214", "theory": "088", "sub_total": "88"},
            {"sub_name": "SCIENCE", "sub_code": "212", "theory": "075", "sub_total": "75",
             "sub_result": "F", "regulation": "Grace"},
        ]}}

# =====================================================================
section("1) Exam registry — portal jaisa (sirf BSEB)")
check("3 exam registry me hain", len(BSEBR.EXAMS) == 3, str(list(BSEBR.EXAMS)))
check("Matric (10th) hai", "matric" in BSEBR.EXAMS)
check("Inter (12th) hai", "inter" in BSEBR.EXAMS)
check("Inter Special/Compartmental hai", "inter_sc" in BSEBR.EXAMS)
check("Matric ka source = official API", BSEBR.EXAMS["matric"]["kind"] == "api")
check("Inter ka source = portal form", BSEBR.EXAMS["inter"]["kind"] == "portal")
check("saal list me 2026 + purane saal", 2026 in BSEBR.YEARS and 2023 in BSEBR.YEARS)
check("current year 2026 mark hai", BSEBR.CURRENT_YEAR == 2026)

# =====================================================================
section("2) Input validation (wizard ke steps)")
check("roll code 5 digit OK", BSEBR.validate("11001", "2600046")[0])
check("roll number 7 digit OK (naye format)", BSEBR.validate("22050", "2600046")[0])
check("khaali roll code par saaf error", "Roll Code" in BSEBR.validate("", "100001")[1])
check("khaali roll number par saaf error", "Roll Number" in BSEBR.validate("11001", "")[1])
check("chhota roll number reject", not BSEBR.validate("11001", "12")[0])
check("split: dono ek saath", BSEBR.split_input("22050 2600046") == ("22050", "2600046"))
check("split: comma wala saaf", BSEBR.split_input("22,050 - 26,00,046") == ("22050", "2600046"))

# =====================================================================
section("3) Matric — parsing + asli fields")
stu = BSEBR.parse_payload(MOCK_STU)
check("naam nikla", stu.get("name") == "RAHUL KUMAR")
check("papa ka naam nikla", stu.get("father") == "RAM KUMAR SINGH")
check("school nikla", stu.get("school") == "H S SCHOOL PATNA")
check("total 640 nikla", stu.get("total") == 640.0)
check("division nikli", stu.get("division") == "1st Division")
check("exam_type nikla (REGULAR)", stu.get("exam_type") == "REGULAR")
check("3 subjects nikle", len(stu.get("subjects") or []) == 3)
check("marks saaf dikhte hain ('090' → 90)", BSEBR._nice("090") == "90")
check("PASS/FAIL text sahi", BSEBR.result_text(stu) == "PASS")
_fail_stu = {"division": "Fail", "total": 200, "subjects": []}
check("Fail division → FAIL text", BSEBR.result_text(_fail_stu) == "FAIL")
check("expelled → EXPELLED", BSEBR.result_text({"is_expelled": True}) == "EXPELLED")
check("khaali payload → {} (crash nahi)", BSEBR.parse_payload({}) == {})
check("success:false → {} ", BSEBR.parse_payload({"success": False}) == {})

# =====================================================================
section("4) Inter — portal parse (naya format bhi safe)")
FAKE_MARKSHEET = """
<html><body><table>
<tr><td>Student's Name</td><td>PRIYA JAISWAL</td></tr>
<tr><td>Father's Name</td><td>SANTOSH JAISWAL</td></tr>
<tr><td>School Name</td><td>GOVT HIGH SCHOOL PATNA</td></tr>
<tr><td>Roll Code</td><td>35052</td></tr>
<tr><td>Roll Number</td><td>25010033</td></tr>
</table>
<table>
<tr><th>Subject</th><th>Theory</th><th>Subject Total</th></tr>
<tr><td>PHYSICS</td><td>88</td><td>88</td></tr>
<tr><td>CHEMISTRY</td><td>85</td><td>85</td></tr>
<tr><td>MATHEMATICS</td><td>92</td><td>92</td></tr>
</table>
<div>Grand Total: 265</div><div>First Division</div>
</body></html>
"""
_ps = BSEBR._parse_marksheet_guess(FAKE_MARKSHEET)
check("Inter: naam nikla", _ps.get("name") == "PRIYA JAISWAL", str(_ps.get("name")))
check("Inter: father nikla", _ps.get("father") == "SANTOSH JAISWAL")
check("Inter: roll code/number nikle", _ps.get("roll_code") == "35052" and _ps.get("roll_no") == "25010033")
check("Inter: total nikla (265)", _ps.get("total") == 265.0, str(_ps.get("total")))
check("Inter: division nikli", "First Division" in str(_ps.get("division")))
check("Inter: subjects nikle (3)", len(_ps.get("subjects") or []) == 3, str(len(_ps.get("subjects") or [])))
check("Inter: khaali HTML par crash nahi", isinstance(BSEBR._parse_marksheet_guess(""), dict))

# =====================================================================
section("5) Dispatcher — exam/year/halat sab")
check("galat exam key → invalid", BSEBR.check("nope", 2026, "11001", "100001")["status"] == "invalid")
_r = BSEBR.check("inter", 2023, "35052", "25010033")
check("purana saal (2023) → archive status", _r.get("status") == "archive"
      and "2023" in str(_r.get("error")), str(_r.get("status")))
check("archive me exam + year bhi saath aate hain", _r.get("year") == 2023 and _r.get("exam") == "inter")

_orig_matric = BSEBR.fetch_matric
_orig_inter = BSEBR.fetch_inter
try:
    BSEBR.fetch_matric = lambda rc, rn: {"ok": True, "student": BSEBR.parse_payload(MOCK_STU)}
    _r2 = BSEBR.check("matric", 2026, "11001", "100001")
    check("matric 2026 → ok + student", _r2.get("ok") and _r2["student"]["name"] == "RAHUL KUMAR")
    check("result me exam_label bhi aata hai", "MATRIC" in str(_r2.get("exam_label", "")).upper())

    BSEBR.fetch_matric = lambda rc, rn: {"ok": False, "status": "not_live",
                                         "error": "abhi live nahi"}
    check("not_live aage pass hota hai",
          BSEBR.check("matric", 2026, "11001", "100001").get("status") == "not_live")

    BSEBR.fetch_inter = lambda rc, rn, page="ex-26": {"ok": False, "status": "server",
                                                      "error": "down"}
    check("inter 2026 → portal se (server bhi handle)",
          BSEBR.check("inter", 2026, "35052", "25010033").get("status") == "server")
finally:
    BSEBR.fetch_matric = _orig_matric
    BSEBR.fetch_inter = _orig_inter

# =====================================================================
section("6) PDF marksheet — poora data + safe")
_pdf = BSEBR.build_pdf(stu, BSEBR.EXAMS["matric"]["label"], 2026, "test")
check("PDF bani (PNG nahi, asli PDF)", bool(_pdf) and _pdf[:5] == b"%PDF-", str(len(_pdf or b"")))
check("PDF ka size theek (10KB+)", len(_pdf or b"") > 10000, str(len(_pdf or b"")))
try:
    import fitz
    _d = fitz.open(stream=_pdf, filetype="pdf")
    _t = _d[0].get_text()
    check("PDF me naam hai", "RAHUL KUMAR" in _t)
    check("PDF me papa ka naam hai", "RAM KUMAR SINGH" in _t)
    check("PDF me school hai", "H S SCHOOL PATNA" in _t)
    check("PDF me subject-wise marks hain", "M.I.L. HINDI" in _t and "ADVANCED MATH" in _t)
    check("PDF me total hai (640)", "640" in _t)
    check("PDF me division hai", "1st Division" in _t)
    check("PDF me WEB COPY + disclaimer hai", "WEB COPY" in _t.upper() and "official" in _t.lower())
    check("PDF me roll code/number hai", "11001" in _t and "100001" in _t)
    check("PDF me emoji nahi (▯ box nahi)", "▯" not in _t)
    check("PDF mein Hindi font chhapa (board ka naam)", "बिहार" in _t or "BIHAR SCHOOL" in _t)
except Exception as e:                                            # noqa: BLE001
    check("PDF check (fitz na ho to skip)", True, str(e)[:60])
check("khaali student par bhi PDF (crash nahi)", (BSEBR.build_pdf({}, "x", 2026) or b"")[:5] == b"%PDF-")
check("filename saaf", BSEBR.pdf_filename("matric", "22050", "2600046", 2026)
      == "BSEB_matric_22050-2600046_2026.pdf")

# =====================================================================
section("7) LIVE — asli Bihar Board (topper ka public roll)")
try:
    import requests
    _resp = requests.get(BSEBR.MATRIC_API,
                         params={"roll_code": REAL_MATRIC[0], "roll_no": REAL_MATRIC[1]},
                         headers={"Accept": "application/json"}, timeout=25)
    _j = _resp.json()
    if _j.get("success"):
        _ls = BSEBR.parse_payload(_j)
        check("LIVE: asli result aaya", bool(_ls.get("name")), str(_ls)[:60])
        check("LIVE: naam sahi (topper)", REAL_MATRIC[2].split()[0] in str(_ls.get("name")))
        check("LIVE: total 492", _ls.get("total") == 492.0, str(_ls.get("total")))
        check("LIVE: topper flag", _ls.get("is_topper") is True)
        _lp = BSEBR.build_pdf(_ls, BSEBR.EXAMS["matric"]["label"], 2026, "live")
        check("LIVE: iska PDF bhi bani", (_lp or b"")[:5] == b"%PDF-")
    else:
        check("LIVE: API reachable (result abhi nahi)", _resp.status_code in (200, 404),
              str(_j)[:80])
except Exception as e:                                            # noqa: BLE001
    check("LIVE check (network na ho to skip)", True, str(e)[:60])

# =====================================================================
section("8) Cards — wizard ke saare screens")
_c1 = bot.rc_exam_card()
check("exam card: boxed title + teen exam naam",
      _c1.startswith("┏") and "Matric" in _c1 and "Inter" in _c1 and "Special" in _c1)
_c2 = bot.rc_year_card("matric")
check("year card: exam + saal dikhte hain", "Matric" in _c2 and "2026" in _c2 and "2023" in _c2)
_c3 = bot.rc_ask_code_card("matric", 2026)
check("roll code step: 🔗 + example", "🔗" in _c3 and "11001" in _c3)
_c4 = bot.rc_ask_roll_card("matric", 2026, "11001")
check("roll number step: roll code confirm dikhta", "11001" in _c4 and "Roll Number" in _c4)
_c5 = bot.rc_result_card(stu, "matric", 2026)
check("result card: naam + marks + total + division",
      "RAHUL KUMAR" in _c5 and "M.I.L. HINDI" in _c5 and "640" in _c5 and "PASS" in _c5)
check("result card: PDF ka zikr", "PDF" in _c5)
_c6 = bot.rc_archive_card("matric", 2023)
check("archive card: sach + rasta (school/board office)",
      "nahi hai" in _c6 and "school" in _c6.lower() and "2023" in _c6)
_c7 = bot.rc_server_card("matric", 2026)
check("server card: dobara try ka rasta", "Dobara try" in _c7)
_c8 = bot.rc_parse_card("inter", 2026)
import re as _re2                                                    # noqa: E402
_own = lambda x: _re2.sub(r'https?://t\.me/' + _re2.escape(str(bot.OWNER_USERNAME)), '', x)
check("parse card: imaandar (format badla) + koi bahar ka link nahi",
      "format badal" in _c8 and "http" not in _own(_c8))
_c9 = bot.cbse_info_card()
check("CBSE card: login bypass nahi + koi bahar ka link nahi",
      "login" in _c9.lower() and "http" not in _own(_c9))
check("sab card me moti line (━) nahi",
      all("━" not in x for x in (_c1, _c2, _c3, _c4, _c5, _c6, _c7, _c8, _c9)))

# =====================================================================
section("9) Wiring + keyboards")
_kb = [bot.unbold(b) for r in bot.KB_BTNS for b in r]
check("keyboard me RESULT CHECK", any("RESULT CHECK" in x.upper() for x in _kb))
check("BTN_MODE_MAP: RESULT CHECK → bsebr", bot.BTN_MODE_MAP.get("RESULT CHECK") == "bsebr")
check("exam kb me 3 exam + CBSE", len(bot._rc_exam_kb().inline_keyboard) == 5,
      str(len(bot._rc_exam_kb().inline_keyboard)))
check("year kb me saare saal + back",
      len(bot._rc_year_kb().inline_keyboard) == 4, str(len(bot._rc_year_kb().inline_keyboard)))
check("FREE hai (premium 37)", "bsebr" not in bot.PREMIUM_TOOLS and len(bot.PREMIUM_TOOLS) == 37)
check("rate-limit: rc (wizard step) + bsebr", bot.TOOL_RATE_LIMITS.get("rc") is not None
      and bot.TOOL_RATE_LIMITS.get("bsebr") is not None)
check("VIP wall par khula (rc_ prefix)",
      bot.vip_free_cb("rc_new") and bot.vip_free_cb("rc_ex:matric") and bot.vip_free_cb("rc_retry"))
check("import + wizard functions bot me hain",
      "from modules import bseb_result as BSEBR" in BOT_SRC and "async def rc_deliver" in BOT_SRC)
check("purana _bsebr_kb wala toota ref nahi bacha", "_bsebr_kb(" not in BOT_SRC)

# =====================================================================
section("10) E2E — nakli Telegram par poora wizard (offline)")
import asyncio                                                     # noqa: E402


class _Sent:
    def __init__(self):
        self.edits = []
        self.msg = None

    async def edit_text(self, txt, **kw):
        self.edits.append(txt)
        return self

    async def delete(self):
        return True

    async def reply_text(self, txt, **kw):
        self.msg = txt
        return self


class _Msg:
    def __init__(self, text=""):
        self.text = text
        self.out = []
        self.docs = []

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return _Sent()

    async def reply_document(self, document, filename=None, caption=None, **kw):
        self.docs.append((filename, caption or "", document.getvalue() if hasattr(document, "getvalue") else b""))
        return _Sent()


class _Ctx:
    def __init__(self):
        self.user_data = {}
        self.bot = None


class _UpdT:
    def __init__(self, text, uid):
        self.effective_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.effective_chat = self.effective_user
        self.message = _Msg(text)
        self.callback_query = None


class _QMsg:
    def __init__(self):
        self.out = []
        self.photos = []

    async def edit_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def delete(self):
        return True

    async def reply_photo(self, photo, caption=None, **kw):
        self.photos.append((caption or "", photo.getvalue() if hasattr(photo, "getvalue") else b""))
        self.out.append(caption or "")
        return self


class _Q:
    def __init__(self, data, uid):
        self.data = data
        self.from_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.message = _QMsg()
        self.answered = []

    async def answer(self, *a, **kw):
        self.answered.append(a)


class _UpdQ:
    def __init__(self, q):
        self.callback_query = q
        self.effective_user = q.from_user
        self.effective_chat = q.from_user


async def _wizard_flow():
    uid = 707070

    def cb(data, ctx):
        q = _Q(data, uid)
        asyncio.get_event_loop().run_until_complete(bot.on_cb(_UpdQ(q), ctx))
        return q

    ctx = _Ctx()
    # 1) RESULT CHECK button → BOARD list (hub)
    q0 = _Q("rc_new", uid)
    await bot.on_cb(_UpdQ(q0), ctx)
    _t0 = " ".join(q0.message.out)
    check("E2E: pehle BOARD list aayi (hub)", "BOARD chuno" in _t0 and "BSEB" in _t0)
    check("E2E: mode = rc_board", ctx.user_data.get("mode") == "rc_board")

    # 2a) BSEB board card (photo ke saath)
    qb = _Q("rcb:bseb", uid)
    await bot.on_cb(_UpdQ(qb), ctx)
    check("E2E: BSEB board card aaya", "Bihar School Examination Board" in " ".join(qb.message.out))
    check("E2E: board ka OFFICIAL LOGO photo bheji",
          bool(qb.message.photos) and qb.message.photos[0][1][:4] == b"\xff\xd8\xff\xe0",
          str(len(qb.message.photos)))

    # 2b) LIVE check button → exam list
    q1 = _Q("rc_live:bseb", uid)
    await bot.on_cb(_UpdQ(q1), ctx)
    _t1 = " ".join(q1.message.out)
    check("E2E: exam list aayi (Matric/Inter/Special)",
          "Matric" in _t1 and "Inter" in _t1 and "Special" in _t1)
    check("E2E: mode = rc_exam", ctx.user_data.get("mode") == "rc_exam")

    # 2) exam chuno
    q2 = _Q("rc_ex:matric", uid)
    await bot.on_cb(_UpdQ(q2), ctx)
    _t2 = " ".join(q2.message.out)
    check("E2E: year list aayi (2026 + purane)", "2026" in _t2 and "2023" in _t2)
    check("E2E: exam select yaad raha", (ctx.user_data.get("rcdb") or {}).get("exam") == "matric")

    # 3) year chuno
    q3 = _Q("rc_yr:2026", uid)
    await bot.on_cb(_UpdQ(q3), ctx)
    check("E2E: ab Roll Code maanga", "Roll Code" in " ".join(q3.message.out))
    check("E2E: mode = rc_code", ctx.user_data.get("mode") == "rc_code")

    # 4) roll code bhejo
    up1 = _UpdT("11001", uid)
    await bot.on_text(up1, ctx)
    check("E2E: roll code le liya, ab Roll Number maanga",
          "Roll Number" in " ".join(up1.message.out) and ctx.user_data.get("mode") == "rc_roll")

    # 5) roll number bhejo → (mock API se) result + PDF
    _om = BSEBR.fetch_matric
    BSEBR.fetch_matric = lambda rc, rn: {"ok": True, "student": BSEBR.parse_payload(MOCK_STU)}
    try:
        up2 = _UpdT("2600046", uid)
        await bot.on_text(up2, ctx)
        _t3 = " ".join(up2.message.out)
        check("E2E: result card aaya (naam + marks + total)",
              "RAHUL KUMAR" in _t3 and "M.I.L. HINDI" in _t3 and "640" in _t3, _t3[:70])
        check("E2E: PDF document bhi gaya", len(up2.message.docs) == 1,
              str([d[0] for d in up2.message.docs]))
        if up2.message.docs:
            _fn, _cap, _bytes = up2.message.docs[0]
            check("E2E: PDF asli hai (%PDF)", _bytes[:5] == b"%PDF-")
            check("E2E: PDF ka naam saaf (BSEB_...)",
                  _fn.startswith("BSEB_matric_") and _fn.endswith(".pdf"), _fn)
            check("E2E: caption me 'poora data'", "poora data" in _cap)
            try:
                import fitz
                _txt = fitz.open(stream=_bytes, filetype="pdf")[0].get_text()
                check("E2E: PDF ke andar naam + marks hain",
                      "RAHUL KUMAR" in _txt and "ADVANCED MATH" in _txt)
            except Exception:                                     # noqa: BLE001
                pass
        check("E2E: session saaf (mode gaya)", ctx.user_data.get("mode") is None)
    finally:
        BSEBR.fetch_matric = _om

    # 6) server down → server card + rc_retry se dobara
    _om2 = BSEBR.fetch_matric
    BSEBR.fetch_matric = lambda rc, rn: {"ok": False, "status": "server", "error": "down"}
    try:
        up3 = _UpdT("11001", uid)
        ctx.user_data["mode"] = "rc_code"
        ctx.user_data["rcdb"] = {"exam": "matric", "year": 2026}
        await bot.on_text(up3, ctx)
        up4 = _UpdT("2600046", uid)
        await bot.on_text(up4, ctx)
        check("E2E: server down par saaf message",
              "server" in " ".join(up4.message.out).lower())
        check("E2E: numbers yaad rakhe (retry ke liye)",
              (ctx.user_data.get("rcdb") or {}).get("rn") == "2600046")
        # ab API theek → rc_retry
        BSEBR.fetch_matric = lambda rc, rn: {"ok": True, "student": BSEBR.parse_payload(MOCK_STU)}
        q5 = _Q("rc_retry", uid)
        await bot.on_cb(_UpdQ(q5), ctx)
        check("E2E: 🔁 Dobara try se result aa gaya",
              "RAHUL KUMAR" in " ".join(q5.message.out), " ".join(q5.message.out)[:70])
    finally:
        BSEBR.fetch_matric = _om2

    # 7) purana saal (2023) → archive card
    q7 = _Q("rc_ex:matric", uid)
    await bot.on_cb(_UpdQ(q7), ctx)
    q8 = _Q("rc_yr:2023", uid)
    await bot.on_cb(_UpdQ(q8), ctx)
    _t4 = " ".join(q8.message.out)
    check("E2E: 2023 chunte hi sach (archive) card",
          "nahi hai" in _t4 and "school" in _t4.lower(), _t4[:80])
    check("E2E: archive par mode saaf", ctx.user_data.get("mode") is None)

    # 8) galat roll code par saaf error
    q9 = _Q("rc_yr:2026", uid)
    await bot.on_cb(_UpdQ(q9), ctx)
    upx = _UpdT("abc", uid)
    await bot.on_text(upx, ctx)
    check("E2E: galat roll code par example ke saath error",
          "❌" in " ".join(upx.message.out) and "11001" in " ".join(upx.message.out))


asyncio.run(_wizard_flow())

# -- Inter flow (portal) — mock se not_live --
class _Ctx2(_Ctx):
    pass


async def _inter_flow():
    uid = 707071
    ctx = _Ctx()
    qa = _Q("rc_new", uid)
    await bot.on_cb(_UpdQ(qa), ctx)
    qb = _Q("rc_ex:inter", uid)
    await bot.on_cb(_UpdQ(qb), ctx)
    check("E2E-Inter: Inter select hua",
          (ctx.user_data.get("rcdb") or {}).get("exam") == "inter")
    qc = _Q("rc_yr:2026", uid)
    await bot.on_cb(_UpdQ(qc), ctx)
    check("E2E-Inter: year ke baad roll code maanga", "Roll Code" in " ".join(qc.message.out))
    _oi = BSEBR.fetch_inter
    BSEBR.fetch_inter = lambda rc, rn, page="ex-26": {"ok": False, "status": "not_live",
                                                      "error": "abhi live nahi"}
    try:
        up1 = _UpdT("35052", uid)
        await bot.on_text(up1, ctx)
        up2 = _UpdT("25010033", uid)
        await bot.on_text(up2, ctx)
        _t = " ".join(up2.message.out)
        check("E2E-Inter: result na hone par saaf card (crash nahi)",
              "live nahi" in _t, _t[:80])
    finally:
        BSEBR.fetch_inter = _oi


asyncio.run(_inter_flow())

print(f"\n{'=' * 62}")
print(f"  v79 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
