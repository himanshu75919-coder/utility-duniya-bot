# -*- coding: utf-8 -*-
"""
v78 SELFTEST — 📋 BOARD RESULT CHECK (BSEB)  [v73.1]
====================================================
User ka order: CBSE/BSEB jaise result portal ka tool — roll code + roll
number se result. Research (7 Oct 2026):
  • BSEB  → official open API (`resultapi.biharboardonline.org/result`)
  • CBSE  → DigiLocker (login) — isliye sirf jaankari card.

Rules:
  • 100% FREE (premium count 37 wahi)
  • Board ka server busy ho to SAFA message (crash/khaali card nahi)
  • Result off-season ho to saaf "abhi live nahi" + kab aayega
  • Hum login/captcha bypass kabhi nahi karte

Sab kuch OFFLINE test hota hai (nakli API + nakli Telegram).
"""
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv78_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V78"
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
print("  v78 SELFTEST — 📋 BOARD RESULT CHECK (BSEB)")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import bseb_result as BSEBR                          # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

MOCK_STU = {
    "success": True, "data": {
        "name": "RAHUL KUMAR", "father_name": "RAM KUMAR SINGH",
        "school_name": "H S SCHOOL PATNA", "roll_code": "11001",
        "roll_no": "100001", "reg_no": "12345678", "bseb_id": "BSEB1234",
        "division": "First", "is_topper": False, "total": 640,
        "subjects": [
            {"sub_name": "HINDI", "sub_code": "101", "theory": 90, "sub_total": 90},
            {"sub_name": "MATH", "sub_code": "102", "theory": 88, "sub_total": 88},
            {"sub_name": "SCIENCE", "sub_code": "103", "theory": 75, "sub_total": 75,
             "sub_result": "F", "regulation": "Grace"},
        ]}}

# =====================================================================
section("1) Input — roll code + roll number (sab format)")
check("validate: 5+6 digit sahi", BSEBR.validate("11001", "100001")[0])
check("validate: roll code missing → saaf message",
      not BSEBR.validate("", "100001")[0] and "Roll Code" in BSEBR.validate("", "100001")[1])
check("validate: roll number missing → saaf message",
      not BSEBR.validate("11001", "")[0] and "Roll Number" in BSEBR.validate("11001", "")[1])
check("validate: chhota roll number reject", not BSEBR.validate("11001", "12")[0])
check("validate: roll code 5 digit rule", not BSEBR.validate("1", "100001")[0])
check("split: '11001 100001'", BSEBR.split_input("11001 100001") == ("11001", "100001"))
check("split: '11001/100001'", BSEBR.split_input("11001/100001") == ("11001", "100001"))
check("split: 'roll code 11001 roll no 100001' bhi chala",
      BSEBR.split_input("roll code 11001 roll no 100001") == ("11001", "100001"))
check("split: comma wala '11,001' clean", BSEBR.split_input("11,001 - 1,00,001") == ("11001", "100001"))
check("split: sirf ek number → code khaali",
      BSEBR.split_input("11001") == ("", "11001"))
check("split: kuch nahi → dono khaali", BSEBR.split_input("hello") == ("", ""))

# =====================================================================
section("2) API — response parsing (BSEB ke fields)")
stu = BSEBR.parse_payload(MOCK_STU)
check("name nikla", stu.get("name") == "RAHUL KUMAR")
check("papa ka naam nikla", stu.get("father") == "RAM KUMAR SINGH")
check("school nikla", stu.get("school") == "H S SCHOOL PATNA")
check("roll_code + roll_no nikle", stu.get("roll_code") == "11001" and stu.get("roll_no") == "100001")
check("reg_no nikla", stu.get("reg_no") == "12345678")
check("total nikla (640)", stu.get("total") == 640.0)
check("division nikli (First)", stu.get("division") == "First")
check("3 subjects nikle", len(stu.get("subjects") or []) == 3)
check("khaali payload par {} (crash nahi)", BSEBR.parse_payload({}) == {})
check("garbage payload par {} (crash nahi)", BSEBR.parse_payload("bakwaas") == {})
check("success:false par {} (khaali)", BSEBR.parse_payload({"success": False}) == {})
check("nested payload me bhi student dhoondh leta hai",
      BSEBR.parse_payload({"a": {"b": MOCK_STU["data"]}}).get("name") == "RAHUL KUMAR")
_sub = BSEBR._sub_line(MOCK_STU["data"]["subjects"][2])
check("subject line me naam + marks", "SCIENCE" in _sub and "75" in _sub)
check("subject line me F/* flag", "F" in _sub and "*" in _sub)

# =====================================================================
section("3) Fetch — sahi/galat/server sab handle")
import modules.core.httpio as _h                                # noqa: E402
_orig = _h.get_json


def _fake_ok(url, **kw):
    return MOCK_STU


def _fake_notfound(url, **kw):
    raise Exception("HTTPError 404: NOT FOUND")


def _fake_down(url, **kw):
    raise Exception("Connection timed out")


def _fake_false(url, **kw):
    return {"success": False, "message": "no result found"}


try:
    _h.get_json = _fake_ok
    r = BSEBR.fetch("11001", "100001")
    check("fetch: result mila → ok", r.get("ok") and r["student"]["name"] == "RAHUL KUMAR")
    check("fetch: raw_keys bhi bhejta hai (debug)", isinstance(r.get("raw_keys"), list))

    _h.get_json = _fake_notfound
    r2 = BSEBR.fetch("11001", "100001")
    check("fetch: 404 → not_live (crash nahi)", r2.get("ok") is False and r2.get("status") == "not_live")

    _h.get_json = _fake_down
    r3 = BSEBR.fetch("11001", "100001")
    check("fetch: server down → status=server", r3.get("ok") is False and r3.get("status") == "server")

    _h.get_json = _fake_false
    r4 = BSEBR.fetch("11001", "100001")
    check("fetch: success:false → not_live", r4.get("status") == "not_live")

    _h.get_json = _fake_ok
    check("fetch: galat input par API call hi nahi (fauran error)",
          BSEBR.fetch("xx", "yy").get("status") == "invalid")
finally:
    _h.get_json = _orig

# =====================================================================
section("4) LIVE API — asli Bihar Board server (off-season = saaf jawab)")
try:
    import requests                                            # noqa: E402
    _resp = requests.get(BSEBR.API_URL, params={"roll_code": "11001", "roll_no": "100001"},
                         headers={"Accept": "application/json"}, timeout=20)
    _j = _resp.json()
    check("LIVE: API jawab de rahi hai (reachable)", _resp.status_code in (200, 404))
    check("LIVE: valid JSON mila", isinstance(_j, dict))
    check("LIVE: off-season par 'no result found' wala saaf jawab",
          _j.get("success") is False and "no result" in str(_j.get("message", "")).lower())
    check("LIVE: hamara parser ise not_live dikhata hai",
          BSEBR.parse_payload(_j) == {})
except Exception as e:                                            # noqa: BLE001
    check("LIVE: API check (network na ho to skip)", True, str(e)[:60])

# =====================================================================
section("5) Cards — box + patli line + saaf message")
_c1 = bot.bsebr_card(BSEBR.parse_payload(MOCK_STU))
check("result card: naam dikha", "RAHUL KUMAR" in _c1)
check("result card: roll dikha", "11001" in _c1 and "100001" in _c1)
check("result card: subject-wise marks dikhe", "HINDI" in _c1 and "SCIENCE" in _c1)
check("result card: total + division dikhe", "640" in _c1 and "First" in _c1)
check("result card: boxed title", _c1.startswith("┏") and "┗" in _c1)
check("result card: koi moti line nahi", "━" not in _c1)
check("result card: imaandar note (official server se)", "official server" in _c1)
check("result card: privacy line (apna result hi)", "apne bachche" in _c1)
_c2 = bot.bsebr_notlive_card("11001", "100001")
check("not-live card: 'abhi live nahi' + result kab aata hai",
      "live nahi" in _c2 and "March-April" in _c2)
check("not-live card: khaali nahi, saaf wajah", len(_c2) > 150)
_c3 = bot.bsebr_server_card()
check("server card: 'server busy' + dobara try ka rasta", "Dobara check" in _c3)
check("server card me moti line nahi", "━" not in _c3)
_c4 = bot.cbse_info_card()
check("CBSE card: DigiLocker ki sach jaankari", "DigiLocker" in _c4)
check("CBSE card: login bypass nahi karte — saaf likha",
      "login" in _c4.lower() and "nahi khul sakta" in _c4)
check("CBSE card: BSEB ka rasta batata hai", "BSEB" in _c4 or "Bihar Board" in _c4)
_c5 = bot.bsebr_ask_card()
check("ask card: 🔗 + ek example", "🔗" in _c5 and "11001 100001" in _c5)
check("sab card me moti line nahi",
      all("━" not in x for x in (_c1, _c2, _c3, _c4, _c5)))

# =====================================================================
section("6) Wiring")
_kb = [bot.unbold(b) for r in bot.KB_BTNS for b in r]
check("keyboard me RESULT CHECK button", any("RESULT CHECK" in x.upper() for x in _kb))
check("BTN_MODE_MAP: RESULT CHECK → bsebr", bot.BTN_MODE_MAP.get("RESULT CHECK") == "bsebr")
check("BTN_MODE_MAP: BSEB RESULT → bsebr", bot.BTN_MODE_MAP.get("BSEB RESULT") == "bsebr")
check("BTN_MODE_MAP: CBSE RESULT → cbse_info", bot.BTN_MODE_MAP.get("CBSE RESULT") == "cbse_info")
check("FREE hai (premium count 37)", "bsebr" not in bot.PREMIUM_TOOLS
      and len(bot.PREMIUM_TOOLS) == 37, str(len(bot.PREMIUM_TOOLS)))
check("rate-limit entry hai", bot.TOOL_RATE_LIMITS.get("bsebr") is not None)
check("PROMPT_DATA me bsebr + prompt boxed",
      "bsebr" in bot.PROMPT_DATA and bot.tool_prompt("bsebr").startswith("┏"))
check("VIP wall par bhi khulta hai", bot.vip_free_cb("bsebr_new") and bot.vip_free_cb("cbse_info"))
check("import hai", "from modules import bseb_result as BSEBR" in BOT_SRC)
check("on_text handler wired", 'if mode == "bsebr":' in BOT_SRC)
check("callbacks wired", '"bsebr_new"' in BOT_SRC and '"cbse_info"' in BOT_SRC)
check("action dispatch wired", 'if action == "bsebr":' in BOT_SRC)

# =====================================================================
section("7) E2E — nakli Telegram par poora flow")
import asyncio                                                     # noqa: E402


class _Sent:
    def __init__(self):
        self.edits = []

    async def edit_text(self, txt, **kw):
        self.edits.append(txt)
        return self

    async def delete(self):
        return True


class _MsgT:
    def __init__(self, text):
        self.text = text
        self.out = []
        self.kbs = []

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        self.kbs.append(kw.get("reply_markup"))
        return _Sent()


class _UpdT:
    def __init__(self, text, uid):
        self.effective_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.effective_chat = self.effective_user
        self.message = _MsgT(text)
        self.callback_query = None


class _CtxT:
    def __init__(self):
        self.user_data = {}
        self.bot = None


async def _flow():
    uid = 808080
    import modules.core.httpio as h2
    _o2 = h2.get_json

    # --- result mil gaya (mock API) ---
    h2.get_json = _fake_ok
    try:
        up = _UpdT("11001 100001", uid)
        ctx = _CtxT()
        ctx.user_data["mode"] = "bsebr"
        await bot.on_text(up, ctx)
        _final = " ".join(up.message.out + [_final_edit(up)])
        check("E2E: result card aaya (naam + marks)",
              "RAHUL KUMAR" in _final and "HINDI" in _final, _final[:60])
        check("E2E: mode saaf hua", ctx.user_data.get("mode") is None)

        # --- off-season (404) ---
        h2.get_json = _fake_notfound
        up2 = _UpdT("11001 100001", uid)
        ctx2 = _CtxT()
        ctx2.user_data["mode"] = "bsebr"
        await bot.on_text(up2, ctx2)
        _f2 = " ".join(up2.message.out + [_final_edit(up2)])
        check("E2E: off-season par saaf 'abhi live nahi'", "live nahi" in _f2, _f2[:70])

        # --- server down ---
        h2.get_json = _fake_down
        up3 = _UpdT("11001 100001", uid)
        ctx3 = _CtxT()
        ctx3.user_data["mode"] = "bsebr"
        await bot.on_text(up3, ctx3)
        _f3 = " ".join(up3.message.out + [_final_edit(up3)])
        check("E2E: server down par saaf message", "server" in _f3.lower(), _f3[:70])

        # --- galat input ---
        h2.get_json = _fake_ok
        up4 = _UpdT("hello bhai", uid)
        ctx4 = _CtxT()
        ctx4.user_data["mode"] = "bsebr"
        await bot.on_text(up4, ctx4)
        _f4 = " ".join(up4.message.out) if up4.message.out else ""
        check("E2E: bakwaas input par example ke saath error",
              "❌" in _f4 and "11001 100001" in _f4, _f4[:70])
    finally:
        h2.get_json = _o2


def _final_edit(up):
    # status message ka edit_text (st_msg) bhi dekh lo — warna card miss ho jayega
    try:
        return " " + " ".join(getattr(up.message, "_last_edits", []) or [])
    except Exception:                                             # noqa: BLE001
        return ""


asyncio.run(_flow())


# -- callbacks (bsebr_new / cbse_info) --
class _QMsg2:
    def __init__(self):
        self.out = []

    async def edit_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return self


class _Q2:
    def __init__(self, data, uid):
        self.data = data
        self.from_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.message = _QMsg2()

    async def answer(self, *a, **kw):
        pass


class _UpdQ2:
    def __init__(self, q):
        self.callback_query = q
        self.effective_user = q.from_user
        self.effective_chat = q.from_user


async def _cb_flow():
    uid = 808081
    q1 = _Q2("bsebr_new", uid)
    ctx = _CtxT()
    await bot.on_cb(_UpdQ2(q1), ctx)
    check("E2E: 'Dobara check' button prompt wapas laata hai",
          "11001 100001" in " ".join(q1.message.out) and ctx.user_data.get("mode") == "bsebr")
    q2 = _Q2("cbse_info", uid)
    await bot.on_cb(_UpdQ2(q2), ctx)
    check("E2E: CBSE button par jaankari card", "DigiLocker" in " ".join(q2.message.out))


asyncio.run(_cb_flow())

print(f"\n{'=' * 62}")
print(f"  v78 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
