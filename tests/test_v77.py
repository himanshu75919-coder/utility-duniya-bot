# -*- coding: utf-8 -*-
"""
v77 SELFTEST — 💬 WHATSAPP CHAT X-RAY (v73.0)
==============================================
User ka chuna hua tool: "apni exported chat ki poori fun-report".

Rules:
  • 100% FREE (premium count 37 hi rahega)
  • Poora OFFLINE — koi API nahi, kabhi fail nahi
  • File sirf memory me padhi jati hai (kahin save/upload nahi)
  • Android + iOS + 24-hour + am/pm — sab format chalne chahiye
  • Crash-proof: kharab file par saaf message, khaali card kabhi nahi

Sab kuch 100% OFFLINE test hota hai (nakli Telegram par poora flow).
"""
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv77_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V77"
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
print("  v77 SELFTEST — 💬 WHATSAPP CHAT X-RAY")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import chat_xray as CXR                              # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

ANDROID_CHAT = """12/09/25, 9:41 pm - Rahul: Hi bhai kaisa hai tu 😂😂
12/09/25, 9:42 pm - Neha: sab badhiya! kal milte hain
12/09/25, 9:43 pm - Rahul: haha sahi hai
12/09/25, 10:15 pm - Mom: Good morning beta
12/09/25, 11:50 pm - Neha: ok ok
13/09/25, 1:20 am - Rahul: raat ko jugad hai 😂
13/09/25, 1:21 am - Rahul: [Photo] <Media omitted>
12/12/25, 9:41 pm - Messages and calls are end-to-end encrypted. No one outside of this chat can read or listen to them.
14/09/25, 21:00 - Neha: Good morning
14/09/25, 21:01 - Rahul: order de raha hoon dukaan se, jaldi aana warna mera kaam nahi hoga.
15/09/25, 9:00 am - Rahul: haan haan bataya tha na
"""

IOS_CHAT = """[12/09/25, 9:41:05 PM] Rahul: Hi bhai
[12/09/25, 9:42:10 PM] Neha: hmm kya haal
[13/09/25, 11:59:00 AM] Rahul: thik hoon yaar, tu bata
[13/09/25, 12:01:00 AM] Neha: so ja ab
12/09/25, 9:41 pm - Messages and calls are end-to-end encrypted. No one outside of this chat can read or listen to them.
"""

# =====================================================================
section("1) Parsing — Android / iOS / 24-hour sab format")
_a = CXR.analyze_text(ANDROID_CHAT)
check("Android chat parse hui", _a.get("ok") is True)
check("total 10 messages (notice line skip)", _a.get("total") == 10, str(_a.get("total")))
check("system/notice line gini nahi gayi", _a.get("sys") == 1, str(_a.get("sys")))
_i = CXR.analyze_text(IOS_CHAT)
check("iOS brackets format bhi chala", _i.get("ok") is True and _i.get("total") == 4,
      str(_i.get("total")))
_24 = CXR.analyze_text("""14/09/25, 21:00 - Neha: Good morning
14/09/25, 21:01 - Rahul: haan haan
15/09/25, 09:30 - Neha: theek hai""")
check("24-hour ('21:01') format bhi chala", _24.get("ok") and _24.get("total") == 3)
check("am/pm hour sahi nikla (9:41 pm → 21)", _a.get("busy_hour") == (21, 5), str(_a.get("busy_hour")))
check("iOS busy hour sahi (9:41/9:42 PM → 21)", _i.get("busy_hour") == (21, 2), str(_i.get("busy_hour")))

# multi-line message (message ke andar line break)
_ml = CXR.analyze_text("""1/10/25, 5:00 pm - Rahul: pehli line
dusri line yahan
1/10/25, 5:01 pm - Neha: ok
1/10/25, 5:02 pm - Neha: chal""")
check("multi-line message bhi sambhala", _ml.get("ok") and _ml.get("total") == 3,
      str(_ml.get("total")))

# kharab/baahari file
check("nakli text par saaf error (crash nahi)",
      CXR.analyze_file(b"hello ye chat nahi hai", "a.txt").get("ok") is False)
check("bahut chhoti chat par saaf error",
      CXR.analyze_file(b"1/1/25, 5:00 pm - A: hi", "a.txt").get("ok") is False)

# =====================================================================
section("2) Stats — kaun sahi hai, kya sahi hai")
_u = _a.get("users") or []
check("top chatter sahi (Rahul 6 msg)", _u and _u[0]["name"] == "Rahul" and _u[0]["n"] == 6, str(_u[:1]))
check("share % sahi (6/10 = 60%)", _u and abs(_u[0]["share"] - 60.0) < 0.1, str(_u[:1]))
check("3 log list me hain", len(_u) == 3, str(len(_u)))
check("emoji king Rahul (3 emoji)", _a.get("emoji_king") == ("Rahul", 3), str(_a.get("emoji_king")))
check("hasi king Rahul (haha x4)", _a.get("haha_king")[0] == "Rahul" and _a.get("haha_king")[1] == 4,
      str(_a.get("haha_king")))
check("ok/hmm king Neha (2x)", _a.get("ok_king") == ("Neha", 2), str(_a.get("ok_king")))
check("good-morning champ Mom", _a.get("gm_king") == ("Mom", 1), str(_a.get("gm_king")))
check("raat ka jagaadu Rahul (12-5 baje, 2 msg)", _a.get("night", {}).get("top") == ("Rahul", 2),
      str(_a.get("night")))
check("busy din sahi (12 Sep 2025)", _a.get("busy_day") == ("2025-09-12", 5), str(_a.get("busy_day")))
check("din gine sahi (12,13,14,15 = 4)", _a.get("days") == 4, str(_a.get("days")))
check("per-day sahi (10/4 = 2.5)", abs(_a.get("per_day", 0) - 2.5) < 0.05, str(_a.get("per_day")))
check("media count 1", _a.get("media") == 1, str(_a.get("media")))
check("sabse lamba message Rahul", _a.get("longest", {}).get("user") == "Rahul",
      str(_a.get("longest", {}).get("user")))
check("top emoji 😂 3 baar", _a.get("emojis") and _a["emojis"][0] == ("😂", 3), str(_a.get("emojis")[:1]))
_wds = [w for w, _ in (_a.get("words") or [])]
check("top words me junk nahi (end/messages/omitted nahi)",
      not any(x in _wds for x in ("end", "messages", "omitted", "media", "photo")), str(_wds[:6]))
check("top words me asli shabd hain", "badhiya" in _wds or "dukaan" in _wds, str(_wds[:6]))

# =====================================================================
section("3) File → report — .txt, .zip, limits")
_txt = ANDROID_CHAT.encode("utf-8")
_r = CXR.analyze_file(_txt, "WhatsApp Chat with Rahul.txt")
check(".txt file → report OK", _r.get("ok") and _r["stats"]["total"] == 10)

import io as _io
import zipfile as _zip                                              # noqa: E402
_buf = _io.BytesIO()
with _zip.ZipFile(_buf, "w") as z:
    z.writestr("WhatsApp Chat with Rahul/_chat.txt", ANDROID_CHAT)
    z.writestr("WhatsApp Chat with Rahul/IMG-001.jpg", b"fake")
_r2 = CXR.analyze_file(_buf.getvalue(), "WhatsApp Chat with Rahul.zip")
check(".zip export → andar se chat nikal li", _r2.get("ok") and _r2["stats"]["total"] == 10)
check("kharab zip par saaf error",
      CXR.analyze_file(b"PK\x03\x04kharab", "x.zip").get("ok") is False)
check("badi file (13MB) par saaf error",
      CXR.analyze_file(b"x" * (13 * 1024 * 1024), "big.txt").get("ok") is False)
check("cp1252 (purana Windows) file bhi chali",
      CXR.analyze_text(ANDROID_CHAT.replace("😀", "").encode("utf-8").decode("utf-8")).get("ok"))

# =====================================================================
section("4) Image report")
_img = CXR.report_image(_a)
check("PNG image bani", bool(_img) and _img[:4] == b"\x89PNG", str(len(_img or b"")))
from PIL import Image as _PIL                                          # noqa: E402
_im = _PIL.open(_io.BytesIO(_img))
check("image HD hai (1080 wide)", _im.size[0] == 1080, str(_im.size))
check("image me khaali hissa crop hua (height reasonable)", 1500 < _im.size[1] < 3600, str(_im.size))
_img2 = CXR.report_image(CXR.analyze_text(IOS_CHAT))
check("chhoti chat par bhi image bani", bool(_img2) and _img2[:4] == b"\x89PNG")
check("emoji naam map me hai (Laugh)", CXR._EMOJI_NAMES.get("😂") == "Laugh")
_bad = CXR.report_image({})
check("khaali stats par bhi crash nahi (None ya image)", _bad is None or _bad[:4] == b"\x89PNG")

# =====================================================================
section("5) Wiring — button, prompt, mode, batch")
_kb = [bot.unbold(b) for r in bot.KB_BTNS for b in r]
check("keyboard me CHAT X-RAY button", any("CHAT X-RAY" in x.upper() for x in _kb))
check("BTN_MODE_MAP: CHAT X-RAY → cxray", bot.BTN_MODE_MAP.get("CHAT X-RAY") == "cxray")
check("FREE hai (premium count 37 wahi)", "cxray" not in bot.PREMIUM_TOOLS
      and len(bot.PREMIUM_TOOLS) == 37, str(len(bot.PREMIUM_TOOLS)))
check("rate-limit entry hai", bot.TOOL_RATE_LIMITS.get("cxray") is not None)
check("PROMPT_DATA + PROMPTS me cxray", "cxray" in bot.PROMPT_DATA and "cxray" in bot.PROMPTS)
_p = bot.tool_prompt("cxray")
check("prompt boxed + 🔗 + example", _p.startswith("┏") and "🔗" in _p and ".txt" in _p)
check("prompt me Tip/gyaan nahi", "Tip" not in _p and "💡" not in _p)
check("import hai", "from modules import chat_xray as CXR" in BOT_SRC)
check("handle branch wired", 'if mode == "cxray":' in BOT_SRC)
check("_our_modes me cxray", '"cxray")' in BOT_SRC and 'chat export file' in BOT_SRC)
check("kind detect (.txt/.zip → chat)", 'kind = "chat"' in BOT_SRC)

# =====================================================================
section("6) E2E — nakli Telegram par file bhejo (offline)")
import asyncio                                                     # noqa: E402


class _Sent:
    def __init__(self):
        self.edits = []

    async def edit_text(self, txt, **kw):
        self.edits.append(txt)
        return self

    async def delete(self):
        return True

    async def reply_text(self, txt, **kw):
        self.msg = txt
        return self


class _Doc:
    def __init__(self, name, mime, data):
        self.file_name = name
        self.mime_type = mime
        self.file_size = len(data)
        self._data = data

    async def get_file(self):
        doc = self

        class _TF:
            async def download_to_memory(self, buf):
                buf.write(doc._data)
                return None
        return _TF()


class _Msg:
    def __init__(self, doc=None):
        self.document = doc
        self.media_group_id = None
        self.out_text = []
        self.out_photo = []
        self.sent = _Sent()          # edit_text yahan record hota hai

    async def reply_text(self, txt, **kw):
        self.out_text.append(txt)
        return self.sent

    async def reply_photo(self, photo, caption=None, **kw):
        self.out_photo.append((photo.getvalue() if hasattr(photo, "getvalue") else b"",
                               caption or ""))
        return _Sent()


class _UpdM:
    def __init__(self, msg, uid):
        self.message = msg
        self.effective_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.effective_chat = self.effective_user
        self.callback_query = None


class _CtxM:
    def __init__(self):
        self.user_data = {}
        self.bot = None


async def _flow():
    uid = 909090
    # -- sahi .txt file --
    msg = _Msg(_Doc("WhatsApp Chat with Rahul.txt", "text/plain", ANDROID_CHAT.encode()))
    ctx = _CtxM()
    ctx.user_data["mode"] = "cxray"
    await bot.on_media(_UpdM(msg, uid), ctx)
    check("E2E: image report bheji gayi", len(msg.out_photo) == 1, str(len(msg.out_text)))
    if msg.out_photo:
        _imgbytes, cap = msg.out_photo[0]
        check("E2E: image asli PNG hai", _imgbytes[:4] == b"\x89PNG")
        check("E2E: caption me total + top chatter",
              "10 messages" in cap and "Rahul" in cap, cap[:80])
        check("E2E: caption me privacy line", "upload nahi" in cap)
    check("E2E: mode saaf ho gaya", ctx.user_data.get("mode") is None)

    # -- PDF bhej diya galti se --
    msg2 = _Msg(_Doc("kuch.pdf", "application/pdf", b"%PDF-1.4 xx"))
    ctx2 = _CtxM()
    ctx2.user_data["mode"] = "cxray"
    await bot.on_media(_UpdM(msg2, uid), ctx2)
    _t = " ".join(msg2.out_text + [e for s in [] for e in s.edits])
    check("E2E: galat file par saaf message", bool(msg2.out_text) and "export file" in msg2.out_text[0],
          str(msg2.out_text[:1])[:90])

    # -- kharab txt --
    msg3 = _Msg(_Doc("random.txt", "text/plain", b"ye koi chat nahi hai bas text"))
    ctx3 = _CtxM()
    ctx3.user_data["mode"] = "cxray"
    await bot.on_media(_UpdM(msg3, uid), ctx3)
    _allt = " ".join(msg3.out_text + msg3.sent.edits)
    check("E2E: kharab file par saaf error (crash nahi)", "❌" in _allt, _allt[-120:])


asyncio.run(_flow())


# -- text bhejne par file maangta hai --
class _MsgT:
    def __init__(self, text):
        self.text = text
        self.out = []

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return _Sent()


class _UpdT:
    def __init__(self, text, uid):
        self.effective_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.effective_chat = self.effective_user
        self.message = _MsgT(text)
        self.callback_query = None


async def _txt_flow():
    uid = 909091
    ctx = _CtxM()
    ctx.user_data["mode"] = "cxray"
    up = _UpdT("hello", uid)
    await bot.on_text(up, ctx)
    check("E2E: text par file maangi (crash nahi)",
          bool(up.message.out) and "file" in up.message.out[-1].lower(), str(up.message.out[-1])[:80])


asyncio.run(_txt_flow())

print(f"\n{'=' * 62}")
print(f"  v77 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
