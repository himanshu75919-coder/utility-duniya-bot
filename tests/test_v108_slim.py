# -*- coding: utf-8 -*-
"""
v108 SLIM — test suite
======================================================================
Ye test file sirf 2 cheezein pakka karti hai:

  1. ✅ 📱 NUMBER INFO aur 👪 FAMILY INFO bilkul pehle jaise kaam karte
     hain (card, prompt, flow — kuch nahi badla).
  2. ❌ Delete kiye gaye 15 tools ka naam-o-nishan repo me nahi bacha —
     na code, na button, na module, na library.

Chalane ka tarika:
      python tests/test_v108_slim.py
"""
import ast
import asyncio
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("VAULT_ENABLED", "off")
os.environ.setdefault("FORCE_CHANNEL", "")

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name}" + (f"   {extra}" if extra and not cond else ""))


print("=" * 66)
print("  v108 SLIM — TEST SUITE")
print("=" * 66)

# ---------------------------------------------------------------- 1. boot
print("\n[1] BOT LOAD HOTA HAI?")
import bot  # noqa: E402

check("bot.py import ho gaya", True)
check("version v108 hai", bot.BOT_VERSION.startswith("v108"))

# ------------------------------------------------------------- 2. the menu
print("\n[2] MENU ME SIRF 2 TOOLS?")
flat = [bot.unbold(b) for row in bot.KB_BTNS for b in row]
check("menu me exactly 2 buttons", len(flat) == 2, f"mila: {flat}")
check("📱 NUMBER INFO hai", any("NUMBER INFO" in b for b in flat))
check("👪 FAMILY INFO hai", any("FAMILY INFO" in b for b in flat))
check("sirf 2 prompts hain", set(bot.PROMPTS) == {"numinfo", "familyinfo"},
      f"mila: {set(bot.PROMPTS)}")

# --------------------------------------------------------- 3. deleted tools
print("\n[3] DELETE KIYE GAYE TOOLS SACH ME GAYAB?")
GONE_LABELS = [
    "YOUTUBE DL", "TIKTOK DL", "CHANNEL CLONER", "TERABOX DOWNLOADER",
    "WEBSITE OWNER X-RAY", "TEMP MAIL", "TEMP NUMBER", "QR CODE",
    "LINK CHECK", "URL SHORT", "BUSINESS STUDIO", "BANK STATEMENT → EXCEL",
    "MEDIA STUDIO (MP3/STATUS)", "MY ACCOUNT", "SUPPORT / MADAD",
    "INSTA DL", "VIRTUAL NUMBERS", "RC + CHALLAN", "PINCODE INFO",
    "IFSC INFO", "RESULT CHECK", "QR SCANNER", "IMEI / PHONE DETAILS",
    "VIP PREMIUM",
]
for lab in GONE_LABELS:
    check(f"menu me nahi: {lab}", not any(lab in b.upper() for b in flat))
    check(f"mode map me nahi: {lab}", lab not in bot.BTN_MODE_MAP)

GONE_MODULES = [
    "api_hub", "boards", "bseb_result", "bulk_mode", "business_tools",
    "captcha_bridge", "channel_cloner", "cloud_tools", "desi_tools",
    "general_tools", "ig_fast", "imei_lookup", "media_downloader",
    "osint_hub", "payguard", "temp_mail", "temp_number", "toolkit_extras",
    "tutorial_hub", "vehicle_tool", "vip_payment",
    "core/bigfile", "core/dlkey", "core/heavy", "core/httpio",
    "core/proengine", "core/urlclean",
]
for m in GONE_MODULES:
    check(f"file delete: modules/{m}.py",
          not os.path.exists(os.path.join(ROOT, "modules", m + ".py")))

GONE_LIBS = ["yt-dlp", "parth-dl", "imageio-ffmpeg", "Pillow", "qrcode",
             "img2pdf", "reportlab", "pypdf", "pdfplumber", "openpyxl",
             "edge-tts", "gtts", "telethon", "numpy", "beautifulsoup4",
             "aiohttp"]
req = open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8").read()
req_pkgs = [ln.split(">=")[0].split("==")[0].split("[")[0].strip()
            for ln in req.splitlines()
            if ln.strip() and not ln.strip().startswith("#")]
for lib in GONE_LIBS:
    check(f"library hat gayi: {lib}",
          not any(lib.lower() == p.lower() for p in req_pkgs))
check("sirf 4 libraries bachi", len(req_pkgs) == 4, f"mila: {req_pkgs}")

# --------------------------------------------------- 4. cards unchanged
print("\n[4] DONO TOOLS KA CARD BILKUL PEHLE JAISA?")
num_res = {
    "ok": True, "national": "078578 43092", "international": "+91 78578 43092",
    "number": "917857843092", "e164": "+917857843092", "country": "India",
    "operator": "Reliance Jio", "circle": "India", "type": "📱 Mobile",
}
card = bot.numinfo_card(
    num_res,
    {"name": "Sanjay Sah", "father": "Ram Akwal Sah", "phone": "7857843092",
     "govt_id": "401635555849", "address": "S/O Ram Akwal Sah, ward 02, Sitamari, Bihar, 843324"},
    {}, "JIO", "BIHAR", "📱 Mobile", "", "🟢 <b>LIVE</b> — number API se", 412.0)
check("numinfo card bana", bool(card))
check("card me Name hai", "👤 <b>Name:</b> Sanjay Sah" in card)
check("card me Father hai", "👨 <b>Father:</b> Ram Akwal Sah" in card)
check("card me Circle hai", "🌐 <b>Circle:</b> BIHAR JIO" in card)
check("card me Govt ID hai", "401635555849" in card)
check("card me Address hai", "🏠 <b>Address:</b>" in card)
check("card me Response time", "⚡ <b>Response:</b> 412ms" in card)
check("card me brand line", "Powered by" in card)
check("card ka HTML valid hai", bot._tags_balanced(card))

fam = bot.familyinfo_card(
    {"ok": True, "aadhaar_mask": "XXXX-XXXX-5849", "card_number": "123456789012",
     "card_type": "PHH", "state_dist": "Bihar / Sitamarhi", "fps": "FPS-0098",
     "family_count": 5, "address": "Ward 02, Bathnaha, Sitamarhi, Bihar, 843324",
     "members": [{"name": "Sanjay Sah", "ekyc": "Done"},
                 {"name": "Sunita Devi", "ekyc": "Done"}]},
    "🟢 <b>LIVE</b> — family API se", 988.0)
check("familyinfo card bana", bool(fam))
check("header sahi", fam.startswith("👪 <b>FAMILY INFO — RATION CARD</b>"))
check("Aadhaar MASKED hai", "XXXX-XXXX-5849" in fam)
check("poora Aadhaar kahin nahi", "401635555849" not in fam)
check("ration card number hai", "123456789012" in fam)
check("members list hai", "FAMILY MEMBERS" in fam and "Sanjay Sah" in fam)
check("success line hai", "Lookup Status: SUCCESS" in fam)
check("card ka HTML valid hai", bot._tags_balanced(fam))

# -------------------------------------------- 5. offline number lookup
print("\n[5] NUMBER KA OFFLINE PARSER?")
r = bot.lookup_phone_info("7857843092")
check("10-digit number parse hua", r.get("ok") is True)
check("operator mila", bool(r.get("operator")))
check("+91 laga", r.get("e164") == "+917857843092")
check("mobile type", "Mobile" in str(r.get("type")))
bad = bot.lookup_phone_info("123")
check("galat number par saaf error", bad.get("ok") is False and bool(bad.get("error")))

# ------------------------------------------------ 6. prompts unchanged
print("\n[6] TOOL KA PROMPT PEHLE JAISA?")
p1 = bot.tool_prompt("numinfo")
check("numinfo prompt hai", "NUMBER INFO V2 ENGINE" in p1)
check("numinfo ask line", "10 Digit Number bhejein" in p1)
check("numinfo example", "7857843092" in p1)
p2 = bot.tool_prompt("familyinfo")
check("familyinfo prompt hai", "FAMILY INFO" in p2)
check("familyinfo ask line", "12-digit Aadhaar number bhejein" in p2)
check("koi credits/VIP line nahi", "credit" not in (p1 + p2).lower()
      and "vip" not in (p1 + p2).lower())

# ------------------------------------------------- 7. live flow (fake TG)
print("\n[7] ASLI FLOW — user button dabata hai, number bhejta hai")


class FakeMsg:
    def __init__(self, text="", chat_id=99):
        self.text = text
        self.chat_id = chat_id
        self.sent = []

    async def reply_text(self, text, **kw):
        self.sent.append(text)
        return FakeMsg("", self.chat_id)

    def get_bot(self):
        class _B:
            async def send_chat_action(self, **kw):
                return True
        return _B()


class FakeUser:
    id = 4242
    first_name = "Tester"
    username = "tester"


class FakeUpdate:
    def __init__(self, text):
        self.message = FakeMsg(text)
        self.effective_user = FakeUser()
        self.effective_chat = type("C", (), {"id": 99})()
        self.callback_query = None


class FakeCtx:
    def __init__(self):
        self.user_data = {}
        self.args = []


def run(text, ctx):
    u = FakeUpdate(text)
    asyncio.get_event_loop().run_until_complete(bot.on_text(u, ctx))
    return u.message.sent


asyncio.set_event_loop(asyncio.new_event_loop())
ctx = FakeCtx()

out = run("📱 NUMBER INFO", ctx)
check("button dabane par prompt aaya", out and "NUMBER INFO V2 ENGINE" in out[0])
check("mode set hua", ctx.user_data.get("mode") == "numinfo")

# number API mock (asli network call na ho)
bot.mynum.lookup = lambda n: {
    "ok": True, "source": "myapi", "latency_ms": 350,
    "operator": "Jio", "circle": "BIHAR", "type": "Mobile",
    "owner": {"name": "Sanjay Sah", "father": "Ram Akwal Sah",
              "govt_id": "401635555849", "address": "Ward 02, Sitamarhi, Bihar"},
    "extra": {"records": 1},
}
out = run("7857843092", ctx)
joined = "\n".join(out)
check("number bhejne par card aaya", "Sanjay Sah" in joined)
check("wait note dikha", any("Wait few seconds" in s for s in out))
check("LIVE source line", "LIVE" in joined)
# pehle jaisa behaviour: success ke baad tool khula rehta hai, taaki user
# doosra number bina button dabaye bhej sake.
check("tool khula raha (pehle jaisa)", ctx.user_data.get("mode") == "numinfo")
out = run("9123456780", ctx)
check("doosra number bina button ke chala", "Sanjay Sah" in "\n".join(out))

ctx2 = FakeCtx()
out = run("👪 FAMILY INFO", ctx2)
check("family button par prompt", out and "FAMILY INFO" in out[0])
bot.faminfo.lookup = lambda a: {
    "ok": True, "aadhaar_mask": "XXXX-XXXX-5849", "card_number": "123456789012",
    "card_type": "PHH", "state_dist": "Bihar / Sitamarhi", "family_count": 2,
    "members": [{"name": "Sanjay Sah", "ekyc": "Done"}],
}
out = run("401635555849", ctx2)
joined = "\n".join(out)
check("aadhaar bhejne par family card", "RATION CARD" in joined)
check("aadhaar masked hi raha", "XXXX-XXXX-5849" in joined and "401635555849" not in joined)

# bina button ke seedha number
ctx3 = FakeCtx()
out = run("9876543210", ctx3)
check("bina button ke bhi number chal gaya", "Number:" in "\n".join(out)
      or "Sanjay" in "\n".join(out))

# deleted tool ka purana button
ctx4 = FakeCtx()
out = run("▶️ YOUTUBE DL", ctx4)
joined = "\n".join(out)
check("purane tool par saaf message", "ab is bot me nahi hai" in joined)
check("us message me naye 2 tools", "NUMBER INFO" in joined and "FAMILY INFO" in joined)
check("purane tool par crash nahi", True)

for lab in ["⚡ TERABOX DOWNLOADER", "💼 BUSINESS STUDIO", "💬 SUPPORT / MADAD",
            "📷 QR CODE", "🏦 BANK STATEMENT → EXCEL", "👤 MY ACCOUNT"]:
    c = FakeCtx()
    o = "\n".join(run(lab, c))
    check(f"purana button safe: {lab}", "ab is bot me nahi hai" in o)

# --------------------------------------------- 8. no leftovers in source
print("\n[8] SOURCE ME PURANE TOOL KA KACHRA TO NAHI?")
src = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
tree = ast.parse(src)
imported = set()
for n in ast.walk(tree):
    if isinstance(n, ast.ImportFrom) and n.module:
        imported.add(n.module.split(".")[0] if not n.module.startswith("modules")
                     else n.module)
    elif isinstance(n, ast.Import):
        for a in n.names:
            imported.add(a.name)
bad_imports = [m for m in imported
               if any(g.replace("core/", "core.") in m for g in GONE_MODULES)]
check("deleted module ka import nahi", not bad_imports, f"mila: {bad_imports}")

# sirf ASLI import statements dekho (comment/version text me naam aana theek hai)
_real_imports = set()
for n in ast.walk(tree):
    if isinstance(n, ast.Import):
        _real_imports |= {a.name.split(".")[0] for a in n.names}
    elif isinstance(n, ast.ImportFrom) and n.module:
        _real_imports.add(n.module.split(".")[0])
for heavy in ("yt_dlp", "PIL", "telethon", "numpy", "reportlab", "pdfplumber",
              "openpyxl", "qrcode", "img2pdf", "pypdf", "bs4", "aiohttp",
              "edge_tts", "gtts", "imageio_ffmpeg"):
    check(f"{heavy} import nahi hota", heavy not in _real_imports)
check("bot.py 3000 line se chhoti", len(src.splitlines()) < 3000,
      f"{len(src.splitlines())} lines")

# ------------------------------------------------------------- summary
print("\n" + "=" * 66)
print(f"  RESULT:  ✅ {len(PASS)} pass   ❌ {len(FAIL)} fail")
print("=" * 66)
if FAIL:
    for f in FAIL:
        print("   ❌", f)
    sys.exit(1)
print("  🎉 SAB THEEK HAI — dono tools kaam kar rahe hain, baaki sab delete.")
sys.exit(0)
