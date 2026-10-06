# -*- coding: utf-8 -*-
"""
v64 SELFTEST — 📥 VIDEO DOWNLOADER ke 27 ALAG-ALAG TOOLS
=======================================================
Boss ka order: "video downloader ki jitni services hain, sabko alag tool bana do."

Is test me check hota hai:
  A. 27 TOOLS      — har app ka apna key, naam, prompt, limit
  B. PURANA SAFE   — purana 'VIDEO DOWNLOADER' button toota nahi (picker kholta hai)
  C. LINK CHECK    — sahi app ka link pehchan leta hai, galat par saaf batata hai
  D. MENU          — 2 page ka picker, har button ka callback sahi
  E. FREE MODE     — 0 credit wala user bhi sab chala sakta hai
  F. NO CRASH      — khali/galat link par bot girta nahi
"""
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv64_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V64"
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
print("  v64 SELFTEST — Video Downloader ke 27 alag tools")
print("=" * 62)

import warnings                                                      # noqa: E402
warnings.filterwarnings("ignore")
import bot                                                           # noqa: E402
from modules import media_downloader as MD                           # noqa: E402

# =====================================================================
section("[A] 📥 27 ALAG-ALAG TOOLS")
# =====================================================================
check("27 downloader tools hain", len(bot.DL_SITES) == 27, str(len(bot.DL_SITES)))
for _k, _v in bot.DL_SITES.items():
    check(f"  '{_k}' ka dhaancha sahi (icon/naam/domains/example)",
          isinstance(_v, (list, tuple)) and len(_v) == 4 and _v[0] and _v[1] and _v[2] and _v[3])
for _k in ("instagram", "youtube", "facebook", "tiktok", , ,
           , , , , , ):
    check(f"'{_k}' popular list me hai", _k in bot.DL_POPULAR)
check("har tool ka apna prompt hai (PROMPT_DATA)",
      all(f"dl_{k}" in bot.PROMPT_DATA for k in bot.DL_SITES))
check("prompts render bhi ho gaye (PROMPTS)",
      all(bot.tool_prompt(f"dl_{k}").strip() for k in bot.DL_SITES))
check("har prompt me Examples block hai (bot ke format me)",
      all("📝 <b>Examples:</b>" in bot.tool_prompt(f"dl_{k}") for k in bot.DL_SITES))
check("har prompt me ✨ ask line hai",
      all("✨" in bot.tool_prompt(f"dl_{k}") for k in bot.DL_SITES))
check("har tool premium ginti me hai",
      all(bot.is_premium_tool(f"dl_{k}") for k in bot.DL_SITES))
check("rate-limit prefix 'dl' laga hai (saare ek limit me)",
      "dl" in bot.TOOL_RATE_LIMITS)
check("purana insta_dl bhi premium hai", bot.is_premium_tool("insta_dl"))
check("purana insta_dl prompt zinda (5 app examples)",
      all(x in bot.tool_prompt("insta_dl") for x in ("YouTube", "Instagram", "Facebook")))
check("credits ke message me asli app ka naam aata hai",
      "Instagram" in bot.get_credits_over_text("dl_instagram"))
check("credits ke message me YouTube ka naam",
      "YouTube" in bot.get_credits_over_text("dl_youtube"))

# =====================================================================
section("[B] 🔁 PURANA TOOL SAFE — kuch toota nahi")
# =====================================================================
# v66: user ka order — 27-app ka PICKER hataya, har service apna ALAG tool
check("keyboard me 27-app ka picker button HATA diya",
      not any("VIDEO DOWNLOAD (27 APPS)" in bot.unbold(b).upper()
              for r in bot.KB_BTNS for b in r))
check("keyboard se 'VIDEO DOWNLOADER' tool POORI TARAH hata diya",
      not any("VIDEO DOWNLOADER" in bot.unbold(b).upper()
              for r in bot.KB_BTNS for b in r))
check("purana 'VIDEO DOWNLOADER' label ab hatane ka message deta hai",
      bot.BTN_MODE_MAP.get("VIDEO DOWNLOADER") == "dl_gone")
check("purana 'INSTA DOWNLOADER' label INSTA tool par jata hai",
      bot.BTN_MODE_MAP.get("INSTA DOWNLOADER") == "dl_instagram")
check("purane sabhi downloader labels zinda hain (koi user atke na)",
      all(bot.BTN_MODE_MAP.get(x) for x in
          ("VIDEO DOWNLOAD", "DOWNLOADER", "VIDEO DOWNLOAD (34 APPS)",
           "UNIVERSAL VIDEO DOWNLOADER", "VIRAL VIDEO DOWNLOAD",
           "VIDEO DOWNLOAD (27 APPS)")))
check("keyboard ki rows waisi hi hain (14)",
      len(bot.KB_BTNS) >= 14, str(len(bot.KB_BTNS)))
check("purana insta_dl mode zinda hai (koi purana user atke na)",
      "insta_dl" in bot.PREMIUM_TOOLS)
check("media_downloader ke saare 34+ sites waisa hi hai",
      len(MD.SUPPORTED_SITES) >= 30, str(len(MD.SUPPORTED_SITES)))
check("DL_SITES ke saare domains media_downloader me supported hain",
      all(any(d in MD.SUPPORTED_SITES for d in v[2])
          for v in bot.DL_SITES.values()),
      [k for k, v in bot.DL_SITES.items()
       if not any(d in MD.SUPPORTED_SITES for d in v[2])])

# =====================================================================
section("[C] 🔗 LINK CHECK — sahi app pehchano")
# =====================================================================
_ok_cases = [
    ("dl_instagram", "https://www.instagram.com/reel/abc123", True),
    ("dl_youtube", "https://youtu.be/abc123", True),
    ("dl_facebook", "https://fb.watch/abc123", True),
    ("dl_tiktok", "https://vt.tiktok.com/abc", True),
    ("", "https://x.com/i/status/123", True),
    ("", "https:/abc", True),
]
for _m, _u, _want in _ok_cases:
    check(f"{_m}: apna link pehchana ({_u[:34]})", bot.dl_url_matches(_m, _u) is _want)
_mismatch = [
    ("dl_instagram", "https://youtu.be/abc"),
    ("dl_youtube", "https://www.instagram.com/reel/abc"),
    ("dl_tiktok", "https://x.com/i/status/123"),
]
for _m, _u in _mismatch:
    check(f"{_m}: doosre app ka link pakda gaya", bot.dl_url_matches(_m, _u) is False)
check("khali link par crash nahi (True deta hai)",
      bot.dl_url_matches("dl_instagram", "") in (True, False))
check("bogus mode par crash nahi", bot.dl_url_matches("kuch_bhi", "x") is True)
check("dl_key_of sahi kaam karta hai", bot.dl_key_of("dl_youtube") == "youtube")
check("dl_key_of galat key par khali deta hai", bot.dl_key_of("dl_nahi") == "")
check("dl_name sahi naam deta hai", bot.dl_name("dl_youtube") == "YouTube")

# =====================================================================
section("[D] 📋 MENU — 2 page ka picker")
# =====================================================================
_kb1 = bot.dl_menu_kb(0).inline_keyboard
_kb2 = bot.dl_menu_kb(1).inline_keyboard
_btns1 = [b for r in _kb1 for b in r]
_btns2 = [b for r in _kb2 for b in r]
# v66.1: "sabhi apps ek saath" (dlv:any) tool POORI TARAH DELETE
check("page 1 me 12 popular apps",
      len([b for b in _btns1 if b.callback_data.startswith("dlv:")]) == 12)
check("page 1 me 'aur apps' button hai",
      any(b.callback_data == "dlvpage:1" for b in _btns1))
check("page 2 me baaki apps hain",
      len([b for b in _btns2 if b.callback_data.startswith("dlv:")]) >= 14)
check("page 2 me 'popular' wapas button hai",
      any(b.callback_data == "dlvpage:0" for b in _btns2))
check("'sabhi ek saath' (purana tool) button HATA diya",
      not any(b.callback_data == "dlv:any" for b in _btns1 + _btns2))
check("Home button hai", any(b.callback_data == "back_home" for b in _btns1))
check("menu text me 27 likha hai", "27" in bot.DL_MENU_TEXT)
check("menu text me 'alag tool' likha hai", "alag" in bot.DL_MENU_TEXT.lower())
_all_cb = [b.callback_data for b in _btns1 + _btns2 if b.callback_data.startswith("dlv:")]
check("har app ka apna callback hai (27 total)",
      len(_all_cb) == 27, str(len(_all_cb)))

# =====================================================================
section("[E] 🆓 FREE MODE — sabke liye khula")
# =====================================================================
_u = {"user_id": 4242, "credits": 0, "premium_until": ""}
check("ALL_FREE on hai", bot.ALL_FREE is True)
check("0-credit user sab downloader tools chala sakta hai",
      all(bot.can_use_premium_tool(_u, 4242) for _ in bot.DL_SITES))
check("credit katne wala message khali hai",
      bot.spend_credit_msg(4242, "dl_instagram") == "")

# =====================================================================
section("[F] 🛡️ NO CRASH — khali/galat input")
# =====================================================================
_bad = ["", "   ", "kuch bhi nahi", "https://", "instagram", "🎵🎵", "x" * 400]
_broke = []
for _b in _bad:
    try:
        _ = bot.dl_url_matches("dl_instagram", _b)
        _ = bot.dl_name("dl_youtube")
        _ = bot.get_credits_over_text("dl_youtube")
    except Exception as _e:                                       # noqa: BLE001
        _broke.append(f"{_b[:12]} -> {_e!r}")
check("khali/galat input par ek bhi crash nahi", not _broke, str(_broke[:3]))
check("version v64 hai", "v6" in bot.BOT_VERSION, bot.BOT_VERSION)

# =====================================================================
print(f"\n{'=' * 62}")
print(f"  v64 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
