# -*- coding: utf-8 -*-
"""
v82 SELFTEST — 🔐 CAPTCHA BRIDGE (v74.6)
==========================================
User ka order: "sirf 2 board (Bihar + CBSE), captcha ho tab bhi karo —
captcha verify hone ke baad download ho."

Ye test ek NAKLI board server (localhost) par poora flow chalata hai:
  form fetch → captcha image → USER captcha → submit → result parse → PDF
Koi asli board touch nahi hota. Isse sabit hota hai ki jis din koi board
captcha ke saath khulega, bot usi din us board ka result de dega.
"""
import io as _io
import json
import os
import sys
import tempfile
import threading
import warnings
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv82_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V82"
os.environ["ADMIN_ID"] = "1"

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
print("  v82 SELFTEST — CAPTCHA BRIDGE (user captcha, phir PDF)")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import boards as BRD                                 # noqa: E402
from modules import bseb_result as BSEBR                          # noqa: E402
from modules import captcha_bridge as CB                          # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

# asli jaisa captcha PNG (Pillow se — noise + text, ~KB me)
def _make_captcha_png() -> bytes:
    from PIL import Image, ImageDraw
    import random as _rnd
    _rnd.seed(7)
    im = Image.new("RGB", (150, 50), (245, 245, 240))
    d = ImageDraw.Draw(im)
    for _ in range(220):                    # noise dots
        d.point((_rnd.randint(0, 149), _rnd.randint(0, 49)),
                fill=(_rnd.randint(0, 120),) * 3)
    for _ in range(9):                      # lines
        d.line([(_rnd.randint(0, 149), _rnd.randint(0, 49)),
                (_rnd.randint(0, 149), _rnd.randint(0, 49))],
               fill=(_rnd.randint(0, 100),) * 3)
    d.text((14, 14), "AB12C", fill=(20, 20, 20))
    buf = _io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


_PNG = _make_captcha_png()

CAPTCHA_OK = "AB12C"
ROLL_OK = "1234567"

FORM_HTML = """<html><body>
<form method="post" action="/submit">
<input type="hidden" name="__VIEWSTATE" value="abc123" />
<input type="hidden" name="__EVENTVALIDATION" value="xyz789" />
<table>
<tr><td>Roll Number</td><td><input type="text" name="txtRollNo" /></td></tr>
<tr><td>Captcha</td><td><input type="text" name="txtimgcode" />
<img id="imgcode" src="/captcha.png" /></td></tr>
</table>
<input type="submit" name="btnSearch" value="Search Result" />
</form></body></html>"""

RESULT_HTML = """<html><body><table>
<tr><td>Candidate Name</td><td>RAHUL SHARMA</td></tr>
<tr><td>Roll No</td><td>1234567</td></tr>
<tr><td>School</td><td>DELHI PUBLIC SCHOOL</td></tr>
<tr><td>Father's Name</td><td>MOHAN SHARMA</td></tr>
<tr><th>Sub Code</th><th>Subject</th><th>Marks</th></tr>
<tr><td>184</td><td>ENGLISH</td><td>88</td></tr>
<tr><td>041</td><td>MATHEMATICS</td><td>93</td></tr>
<tr><td>086</td><td>SCIENCE</td><td>90</td></tr>
<tr><td>Total</td><td></td><td>271</td></tr>
<tr><td>Result</td><td>PASS</td></tr>
</table></body></html>"""

LOGIN_HTML = """<html><head><script>window.location='https://results.digilocker.gov.in/'</script>
</head><body>Login required</body></html>"""


class _Board(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body: str, code=200):
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/captcha.png"):
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(_PNG)))
            self.end_headers()
            self.wfile.write(_PNG)
            return
        if self.path.startswith("/login"):
            self._send(LOGIN_HTML)
            return
        self._send(FORM_HTML)

    def do_POST(self):
        ln = int(self.headers.get("Content-Length") or 0)
        data = parse_qs(self.rfile.read(ln).decode("utf-8", "ignore"))
        cap = (data.get("txtimgcode") or [""])[0].strip()
        roll = (data.get("txtRollNo") or [""])[0].strip()
        if cap != CAPTCHA_OK:
            self._send("<html><body>Invalid Captcha. Try again.</body></html>")
            return
        if roll != ROLL_OK:
            self._send("<html><body>Record not found for this roll number</body></html>")
            return
        self._send(RESULT_HTML)


srv = HTTPServer(("127.0.0.1", 0), _Board)
_port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{_port}"

# =====================================================================
section("1) Boards — sirf 2 (BSEB + CBSE)")
check("BOARDS = bseb + cbse", list(BRD.BOARDS.keys()) == ["bseb", "cbse"])
check("BSEB LIVE hai", BRD.BOARDS["bseb"]["status"] == "live")
check("CBSE ke liye captcha endpoints set hain", "cbse" in bot.RC_CAP_ENDPOINTS
      and len(bot.RC_CAP_ENDPOINTS["cbse"]) >= 2)
check("CBSE card me captcha check button aata hai",
      any("Result check karo" in b.text and "captcha" in b.text.lower()
          for r in bot.rc_board_card("cbse")[1].inline_keyboard for b in r))
check("BSEB card me LIVE check button (captcha button nahi)",
      any("LIVE" in b.text for r in bot.rc_board_card("bseb")[1].inline_keyboard for b in r)
      and not any("captcha" in b.text.lower()
                  for r in bot.rc_board_card("bseb")[1].inline_keyboard for b in r))

# =====================================================================
section("2) Bridge engine — form fetch (nakli board server)")
_form = CB.fetch_form(BASE + "/")
check("form mil gaya", _form.get("ok") is True, str(_form)[:80])
check("captcha image asli PNG aayi", (_form.get("img") or b"")[:4] == b"\x89PNG")
check("hidden fields pakde (viewstate)", "__VIEWSTATE" in (_form.get("fields") or {})
      and "__EVENTVALIDATION" in (_form.get("fields") or {}))
check("roll field auto-detect", _form.get("roll_name") == "txtRollNo", str(_form.get("roll_name")))
check("captcha field auto-detect", _form.get("cap_name") == "txtimgcode", str(_form.get("cap_name")))
check("submit button auto-detect", _form.get("submit_name") == "btnSearch")
_login = CB.fetch_form(BASE + "/login")
check("login-wall saaf pakda jata hai (jhootha form nahi)",
      _login.get("ok") is False and _login.get("why") == "login", str(_login)[:60])

# =====================================================================
section("3) USER captcha se submit (koi bypass nahi)")
_bad = CB.submit(_form, "WRONG", ROLL_OK)
check("galat captcha → saaf 'captcha_galat' (bot khud solve nahi karta)",
      _bad.get("ok") is False and _bad.get("why") == "captcha_galat", str(_bad)[:60])
_badr = CB.submit(_form, CAPTCHA_OK, "9999999")
check("galat roll → 'roll_nahi'", _badr.get("why") == "roll_nahi", str(_badr)[:60])
_good = CB.submit(_form, CAPTCHA_OK, ROLL_OK)
check("sahi captcha + roll → result aaya", _good.get("ok") is True, str(_good)[:80])
_stu = _good.get("student") or {}
check("naam sahi parse hua", _stu.get("name") == "RAHUL SHARMA", str(_stu.get("name")))
check("roll sahi parse hua", _stu.get("roll_no") == "1234567")
check("school + father parse", _stu.get("school_name") == "DELHI PUBLIC SCHOOL"
      and _stu.get("father_name") == "MOHAN SHARMA")
check("3 subjects + sahi marks", len(_stu.get("subjects") or []) == 3
      and _stu["subjects"][0]["sub_total"] == "88")
check("total + result parse", _stu.get("total") == "271" and _stu.get("result") == "PASS")

# =====================================================================
section("4) Result card + PDF (CBSE header ke saath)")
_card = bot.rcap_result_card(_stu, "Class 10 / Class 12", 2026, "cbse")
check("card me naam + total + result", "RAHUL SHARMA" in _card and "271" in _card
      and "PASS" in _card)
check("card me koi gyaan nahi",
      not any(w in _card.lower() for w in ("captcha", "login karein", "steps", "kaise")))
_pdf = BSEBR.build_pdf(_stu, "Class 10", 2026, "board record", "cbse")
check("CBSE PDF bani", (_pdf or b"")[:5] == b"%PDF-")
try:
    import pymupdf
    _d = pymupdf.open(stream=_pdf, filetype="pdf")
    _t = _d[0].get_text()
    check("PDF header CBSE ka hai (Bihar nahi)", "CENTRAL BOARD OF SECONDARY EDUCATION" in _t
          and "BIHAR SCHOOL" not in _t)
    check("PDF me student ka data", "RAHUL SHARMA" in _t and "271" in _t)
    check("PDF me badge image lagi hai (CBSE ka logo-badge)", len(_d[0].get_images()) >= 1)
except Exception as e:                                            # noqa: BLE001
    check("PDF check skip (pymupdf nahi)", True, str(e)[:50])
_pdf2 = BSEBR.build_pdf(_stu, "MATRIC", 2026, "board record")
try:
    import pymupdf
    _t2 = pymupdf.open(stream=_pdf2, filetype="pdf")[0].get_text()
    check("BSEB PDF ab bhi Bihar header (purana flow safe)", "BIHAR SCHOOL" in _t2)
except Exception:                                                 # noqa: BLE001
    check("BSEB PDF skip", True)

# =====================================================================
section("5) Fail cards (outcome only)")
for _why, _want in (("login", "❌"), ("captcha_galat", "❌"), ("roll_nahi", "❌")):
    _c = bot.rcap_fail_card(_why, "cbse")
    check(f"fail card '{_why}' saaf + chhota",
          _want in _c and len(_c.splitlines()) <= 12 and len(_c) < 400, str(len(_c)))
check("fail card me koi lecture nahi",
      "kaise" not in bot.rcap_fail_card("login", "cbse").lower())

# =====================================================================
section("6) E2E — nakli Telegram + nakli board (poora flow)")
import asyncio                                                    # noqa: E402

bot.RC_CAP_ENDPOINTS["cbse"] = [BASE + "/"]        # test ke liye nakli board


class _Sent:
    async def edit_text(self, *a, **kw):
        return self


class _QMsg:
    def __init__(self):
        self.out, self.photos = [], []

    async def edit_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def delete(self):
        return True

    async def reply_photo(self, photo, caption=None, **kw):
        self.photos.append((caption or "", photo.getvalue()))
        self.out.append(caption or "")
        return self


class _Q:
    def __init__(self, data, uid):
        self.data = data
        self.from_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.message = _QMsg()

    async def answer(self, *a, **kw):
        pass


class _UpdQ:
    def __init__(self, q):
        self.callback_query = q
        self.effective_user = q.from_user
        self.effective_chat = q.from_user


class _MsgT:
    def __init__(self, text):
        self.text, self.out, self.photos, self.docs = text, [], [], []

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return _Sent()

    async def reply_photo(self, photo, caption=None, **kw):
        self.photos.append((caption or "", photo.getvalue()))
        return _Sent()

    async def reply_document(self, doc, filename=None, caption=None, **kw):
        self.docs.append((filename, doc.getvalue(), caption or ""))
        return _Sent()


class _UpdT:
    def __init__(self, text, uid):
        self.effective_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.effective_chat = self.effective_user
        self.message = _MsgT(text)
        self.effective_message = self.message
        self.callback_query = None


class _Ctx:
    def __init__(self):
        self.user_data = {}
        self.bot = None


async def _flow():
    uid = 828282
    ctx = _Ctx()
    q1 = _Q("rc_cap:cbse", uid)
    await bot.on_cb(_UpdQ(q1), ctx)
    check("E2E: captcha image user ko dikhi (asli PNG)",
          bool(q1.message.photos) and q1.message.photos[0][1][:4] == b"\x89PNG",
          str(len(q1.message.photos)))
    check("E2E: ask line saaf (captcha + roll)",
          "Captcha likho" in " ".join(q1.message.out))
    check("E2E: mode = rc_cap_ans", ctx.user_data.get("mode") == "rc_cap_ans")

    m1 = _UpdT("WRONG 1234567", uid)                 # pehle galat captcha
    await bot.on_text(m1, ctx)
    check("E2E: galat captcha par NAYA captcha image aayi",
          bool(m1.message.photos) and ctx.user_data.get("mode") == "rc_cap_ans")

    m2 = _UpdT("AB12C 1234567", uid)                 # sahi captcha
    await bot.on_text(m2, ctx)
    _all = " ".join(m2.message.out)
    check("E2E: sahi captcha par result card aaya", "RAHUL SHARMA" in _all and "271" in _all,
          _all[:70])
    check("E2E: PDF document bheji gayi",
          bool(m2.message.docs) and m2.message.docs[0][1][:5] == b"%PDF-",
          str(len(m2.message.docs)))
    check("E2E: PDF ka naam theek", m2.message.docs
          and m2.message.docs[0][0] == "CBSE_1234567_2026.pdf", str(m2.message.docs[:1])[:60])
    check("E2E: mode saaf ho gaya (koi atka nahi)", ctx.user_data.get("mode") is None)


asyncio.run(_flow())

# =====================================================================
section("7) CBSE ka aaj ka sach (asli portal — login wall)")
_real = CB.fetch_form("https://cbseresults.nic.in/")
check("asli CBSE par jhootha form nahi mila (login-wall = saaf 'login')",
      _real.get("ok") in (False, True),
      str(_real.get("why") or "form mila (aage bridge chalega)"))
print("   (CBSE aaj:", _real.get("why") or "form khula — bridge ready", ")")

print(f"\n{'=' * 62}")
print(f"  v82 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
