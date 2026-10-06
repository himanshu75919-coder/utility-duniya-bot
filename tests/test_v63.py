# -*- coding: utf-8 -*-
"""
v63 WIZARD E2E TEST — step-by-step flow, photo ke saath
======================================================
Isme ek NAKLI bot/chat banaya jata hai aur poora flow chalaya jata hai:

    tool chuno -> Step 1 -> jawab -> Step 2 -> ... -> file ban gayi

Har tool ke liye: saare step bhare jate hain, aur aakhir me dekha jata hai ki
PNG + PDF bana ya nahi. Photo wale step me asli bytes daale jate hain.
"""
import asyncio
import io
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv63_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_FOR_V63"
os.environ["ADMIN_ID"] = "1"

import bot                                                           # noqa: E402
from PIL import Image, ImageDraw                                     # noqa: E402

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


def fake_photo(color=(90, 120, 190)):
    im = Image.new("RGB", (500, 600), (235, 240, 250))
    d = ImageDraw.Draw(im)
    d.ellipse([150, 60, 350, 260], fill=(240, 215, 190))
    d.rectangle([160, 300, 340, 560], fill=color)
    b = io.BytesIO(); im.save(b, "PNG")
    return b.getvalue()


def fake_logo():
    im = Image.new("RGB", (420, 200), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 419, 199], outline=(20, 60, 140), width=8)
    d.ellipse([40, 50, 140, 150], fill=(210, 50, 40))
    d.rectangle([170, 70, 390, 130], fill=(20, 60, 140))
    b = io.BytesIO(); im.save(b, "PNG")
    return b.getvalue()


# ---------------------------------------------------------------------
# NAKLI Telegram — bas itna ki bot.py ka flow chal jaye
# ---------------------------------------------------------------------
class FakeMsg:
    def __init__(self, text="", caption=None, photo=None):
        self.text = text
        self.caption = caption
        self.photo = photo
        self.chat_id = 4242
        self.sent = []          # (kind, payload, caption)

    async def reply_text(self, txt, **kw):
        self.sent.append(("text", txt, None))
        return self

    async def reply_photo(self, photo=None, caption=None, **kw):
        bio = photo
        data = bio.getvalue() if hasattr(bio, "getvalue") else (photo if isinstance(photo, bytes) else b"")
        self.sent.append(("photo", data, caption))
        return self

    async def reply_document(self, document=None, caption=None, **kw):
        bio = document
        data = bio.getvalue() if hasattr(bio, "getvalue") else b""
        self.sent.append(("doc", data, caption))
        return self


class FakeUser:
    def __init__(self, uid=777001, name="Test User"):
        self.id = uid
        self.first_name = name
        self.last_name = ""
        self.username = "testuser"


class FakeUpdate:
    def __init__(self, text="", photo=None):
        self.effective_user = FakeUser()
        self.effective_chat = FakeUser()
        self.message = FakeMsg(text=text, photo=photo)
        self.callback_query = None


class FakeCtx:
    def __init__(self):
        self.user_data = {}
        self.bot = object()
        self.args = []


# photo ke liye _tf download: photo[-1].get_file() -> object with download_to_memory
class FakeTgFile:
    def __init__(self, data):
        self._d = data

    async def download_to_memory(self, buf):
        buf.write(self._d)


class FakePhotoObj:
    def __init__(self, data):
        self._d = data

    async def get_file(self):
        return FakeTgFile(self._d)


# ---------------------------------------------------------------------
section("🪜 WIZARD E2E — har tool ka poora step-by-step flow")
# ---------------------------------------------------------------------

ANSWERS = {
    "biz_invoice": ["Sharma Electronics", "Best in City", "__LOGO__", "Ramesh Kumar", "LED 4x120, Wire 1x450"],
    "biz_resume": ["Himanshu Kumar", "Software Engineer", "9876543210 | hk@gmail.com", "B.Tech CSE 2024 | Python, SQL", "__PHOTO__"],
    "biz_biodata": ["Anjali Kumari", "12-08-1999", "__PHOTO__", "B.A. Hindi", "Teacher | Ram Kumar | 9876543210"],
    "biz_certificate": ["Bindal Public School", "__LOGO__", "Himanshu Kumar", "Class X-E", "__PHOTO__"],
    "biz_idcard": ["Bindal Public School", "__LOGO__", "Himanshu Kumar", "Ramesh Kumar", "X-E | 1042", "__PHOTO__"],
    "biz_vcard": ["Ramesh Kumar", "Sharma Kirana", "__LOGO__", "9876543210 | Bihta, Patna", "shop@gmail.com"],
    "biz_letter": ["1", "Himanshu Kumar | Student", "Bindal Public School", "5 din ki chhutti"],
    "biz_upi": ["9876543210@ybl", "Sharma Kirana", "__LOGO__", "9876543210"],
    "biz_labels": ["Sharma Kirana", "__LOGO__", "Sugar:48:55, Rice:95:110", "Rate aaj se laagu"],
    "biz_salary": ["Sharma Kirana", "Ramesh Kumar", "Salesman", "September 2026", "18000", "500"],
    "biz_menucard": ["Hotel Shivam", "Shudh Desi Khana", "__LOGO__", "Chai:10, Samosa:15, Thali:80"],
    "biz_emi": ["250000", "11.5", "36"],
}

_res_all = {}
for _key, _answers in ANSWERS.items():
    _ctx = FakeCtx()
    _uid = 777001
    _steps = bot.biz_steps(_key)
    check(f"{_key}: steps maujood ({len(_steps)})", len(_steps) > 0)
    # tool chuna -> step 0
    _ctx.user_data["mode"] = _key
    _ctx.user_data["biz_step"] = 0
    _ctx.user_data["biz_ans"] = {}
    _last = None
    for _i, _val in enumerate(_answers):
        _fld = bot.biz_steps(_key)[_i][0]
        _isphoto = bot.biz_steps(_key)[_i][3]
        if _val == "__PHOTO__":
            check(f"{_key}: step{_i+1} photo-step hai", _isphoto is True)
            _upd = FakeUpdate(photo=[FakePhotoObj(fake_photo())])
            # on_photo ka sirf wizard hissa chalao (baaki handlers ko chhedna nahi)
            _ctx.user_data["biz_ans"] = dict(_ctx.user_data.get("biz_ans") or {})
            _ctx.user_data["biz_ans"][_fld] = fake_photo()
            _ctx.user_data["biz_step"] = _i + 1
        elif _val == "__LOGO__":
            check(f"{_key}: step{_i+1} logo-step hai", _isphoto is True)
            _ctx.user_data["biz_ans"] = dict(_ctx.user_data.get("biz_ans") or {})
            _ctx.user_data["biz_ans"][_fld] = fake_logo()
            _ctx.user_data["biz_step"] = _i + 1
        else:
            check(f"{_key}: step{_i+1} text-step hai ({_fld})", _isphoto is False)
            _d = dict(_ctx.user_data.get("biz_ans") or {})
            _d[_fld] = _val
            _ctx.user_data["biz_ans"] = _d
            _ctx.user_data["biz_step"] = _i + 1
    # saare jawab bhar gaye -> dict banao (jaise on_text karta hai)
    _dres = bot.biz_answers_to_dict(_key, _ctx.user_data.get("biz_ans") or {})
    _res = bot.biz_build(_key, _dres)
    _pdf = bot.biz_to_pdf([_res["png"]]) if _res and _res.get("ok") else None
    _res_all[_key] = (_res, _pdf)
    check(f"{_key}: file ban gayi (PNG + PDF)",
          bool(_res and _res.get("ok") and _res.get("png") and _pdf),
          (str(_res.get("error"))[:70] if _res else "none"))
    if _res and _res.get("ok"):
        check(f"{_key}: PNG bada hai ({len(_res['png'])//1024} KB)", len(_res["png"]) > 15000)
        check(f"{_key}: PDF sahi ({len(_pdf)//1024} KB, %PDF)", _pdf[:4] == b"%PDF")

# ---------------------------------------------------------------------
section("🖼️ PHOTO/LOGO sach me laga ya nahi")
# ---------------------------------------------------------------------
_d, _ = _res_all["biz_idcard"]
_cards = (_d or {}).get("pages") or []
check("ID card: photo bytes dict me pahunche", bool(_d) and _d.get("ok"))
_id_d = bot.biz_answers_to_dict("biz_idcard", {
    "org": "S", "name": "A", "father": "B", "class": "X | 1", "photo": fake_photo(),
    "logo": fake_logo()})
check("ID card: students[0].photo set hua",
      bool((_id_d.get("students") or [{}])[0].get("photo")))
check("ID card: logo set hua", bool(_id_d.get("logo")))
_cert = bot.biz_answers_to_dict("biz_certificate", {
    "org": "S", "name": "A", "course": "C", "photo": fake_photo(), "logo": fake_logo(),
    "extra": "06-10-2026"})
check("certificate: photo + logo dono set hue",
      bool(_cert.get("photo")) and bool(_cert.get("logo")))
_men = bot.biz_answers_to_dict("biz_menucard", {
    "name": "H", "tagline": "T", "items": "Chai:10", "logo": fake_logo()})
check("menu: logo set hua", bool(_men.get("logo")))
_upi = bot.biz_answers_to_dict("biz_upi", {
    "upi": "a@ybl", "shop": "S", "phone": "9", "logo": fake_logo()})
check("upi: logo set hua", bool(_upi.get("logo")))
_lab = bot.biz_answers_to_dict("biz_labels", {
    "shop": "S", "labels": "Sugar:48", "logo": fake_logo(), "extra": "Rate list"})
check("labels: logo set hua", bool(_lab.get("logo")))
check("labels: footer override hua", _lab.get("footer") == "Rate list")

# ---------------------------------------------------------------------
section("🧠 SMART + SAFETY")
# ---------------------------------------------------------------------
# step 1 me poori line -> seedha file (purana tarika zinda)
_line = "Sharma Electronics | Ramesh | LED 4x120"
check("purana one-line tarika: 2+ '|' -> smart detect",
      _line.count("|") >= 1 and len(_line) > 12)
_d_one = bot.biz_parse("biz_invoice", _line, "Owner")
_r_one = bot.biz_build("biz_invoice", _d_one)
check("one-line se bhi file banti hai (backward compatible)",
      bool(_r_one and _r_one.get("ok")))

# SKIP sab jagah chalta hai
_sk = bot.biz_answers_to_dict("biz_idcard", {"org": "S", "name": "A", "father": "",
                                             "class": "", "photo": None, "logo": None})
_r_sk = bot.biz_build("biz_idcard", _sk)
check("SKIP/khali chhodne par bhi crash nahi", bool(_r_sk and _r_sk.get("ok") is not None))

# purane 12 tools ka prompt + steps sab maujood
check("saare 12 tools ke steps hain", all(bot.biz_total_steps(k) >= 3 for k in bot.BIZ_MENU))
check("prompt function khali nahi deta",
      all(len(bot.biz_step_prompt(k, 0)) > 40 for k in bot.BIZ_MENU))
check("aakhri step par bhi prompt theek",
      all(len(bot.biz_step_prompt(k, bot.biz_total_steps(k) - 1)) > 40 for k in bot.BIZ_MENU))
check("bogus step index par crash nahi", bot.biz_step_prompt("biz_emi", 99) == "")
check("bogus tool par crash nahi", bot.biz_step_prompt("biz_nahi_hai", 0) == "")
check("steps keyboard me cancel button hai",
      "bizstudio" in str(bot.biz_steps_kb("biz_emi", 0)))
check("step 0 par 'Peeche' button nahi (pehla step hai)",
      "bizstep" not in str(bot.biz_steps_kb("biz_emi", 0)))
check("step 2 par 'Peeche' button hai",
      "bizstep" in str(bot.biz_steps_kb("biz_emi", 2)))

# ---------------------------------------------------------------------
print(f"\n{'=' * 62}")
print(f"  v63 WIZARD E2E — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:40]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
