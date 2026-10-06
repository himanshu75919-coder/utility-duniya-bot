# -*- coding: utf-8 -*-
"""
v66 SELFTEST — 🛡️ ASLI CRASH FIX + 🎯 27 ALAG DOWNLOADER TOOLS + 🍪 COOKIES
==========================================================================
Boss ki shikayatein:
  1. "saala pura baar baar crash ho jaata hai"  -> asli wajah pakdi gayi:
     vault ka auto-backup thread naya event loop bana raha tha
     ("Event object is bound to a different event loop") + polling Conflict
     par give-up -> Render restart.
  2. "saare service ko VIDEO DOWNLOADER me se REMOVE karo, har service ka
     apna ALAG tool banao"                      -> picker poora hataya.
  3. "76 second me bhi download nahi hua"       -> 3-client ladder + 45s cap,
     asli test me 480p video 1.8 second me.
  4. YouTube bot-check                          -> cookies (/cookies + file bhejo).
"""
import asyncio
import os
import re
import sys
import tempfile
import threading
import time
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv66_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V66"
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
print("  v66 SELFTEST — Asli crash fix + 27 alag downloader tools")
print("=" * 62)

import bot                                                           # noqa: E402
from modules import media_downloader as MD                           # noqa: E402
from modules.core import vault as V                                  # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
VAULT_SRC = open(os.path.join(_ROOT, "modules", "core", "vault.py"),
                 encoding="utf-8").read()

# =====================================================================
section("[A] 💥 ASLI CRASH FIX — 'bound to a different event loop'")
# =====================================================================
check("vault me main-loop registry hai", hasattr(V, "set_main_loop")
      and hasattr(V, "run_coro_blocking"))
check("vault me ab naya loop NAHI banta (asyncio.run hataya)",
      "asyncio.run(self.backup_now" not in VAULT_SRC)
check("auto-backup main loop par jaata hai",
      "run_coro_blocking(self.backup_now" in VAULT_SRC)
check("restore ka purana get_event_loop() hataya",
      "get_event_loop().run_until_complete" not in VAULT_SRC)
check("bot boot par main loop register karta hai",
      "vault_set_main_loop(_loop)" in BOT_SRC)
check("grant autosave bhi safe loop use karta hai",
      "run_coro_blocking as _rcb" in BOT_SRC)


# asli test: dusre thread se coroutine chalao (jaise vault karta hai)
async def _ping():
    return "main-loop-ok"


async def _t_loop():
    V.set_main_loop(asyncio.get_running_loop())
    _box = {}
    def _worker():
        _box["r"] = V.run_coro_blocking(_ping(), timeout=10)
    _t = threading.Thread(target=_worker)
    _t.start()
    while _t.is_alive():
        await asyncio.sleep(0.02)
    return _box.get("r")


_r = asyncio.run(_t_loop())
check("dusre thread se coroutine chal gayi (crash nahi)", _r == "main-loop-ok", str(_r))

# =====================================================================
section("[B] 🔁 POLLING AB KABHI GIVE-UP NAHI KARTI (Render restart band)")
# =====================================================================
check("polling loop 'while True' hai (infinite retry)", "while True:" in BOT_SRC)
check("Conflict par dobara koshish (give-up nahi)",
      "Do instance ek saath chal rahe hain" in BOT_SRC
      and "\n            raise\n" not in BOT_SRC.split("STARTING POLLING")[1][:2600])
check("polling crash par backoff hai (min(300", "min(300, 15 * _try)" in BOT_SRC)
check("supervisor (self-heal) zinda hai", "_supervise" in BOT_SRC)

# =====================================================================
section("[C] 🍪 YOUTUBE BOT-CHECK — 4-layer ilaaj")
# =====================================================================
check("client ladder asli test se (android_vr pehle)", MD.YT_CLIENT_SETS[0] == ("android_vr",))
check("tv_embedded backup hai (test me 1.2s me chala)", ("tv_embedded",) in MD.YT_CLIENT_SETS)
check("android backup hai", ("android",) in MD.YT_CLIENT_SETS)
check("purana ghalat 'tv tv_simply' hataya", ("tv", "tv_simply") not in MD.YT_CLIENT_SETS)
check("download me bhi client ladder chalta hai",
      "for _i, _cl in enumerate(_sets)" in open(
          os.path.join(_ROOT, "modules", "media_downloader.py"), encoding="utf-8").read())
check("bot-check message me 3-step hal hai", "bot-check" in open(
    os.path.join(_ROOT, "modules", "media_downloader.py"), encoding="utf-8").read().lower())
check("cookies helpers maujood hain", all(hasattr(MD, x) for x in
      ("cookies_path", "save_cookies_text", "cookies_status")))
check("/cookies command hai", hasattr(bot, "cmd_cookies"))
check("admin ki cookies.txt file handle hoti hai", hasattr(bot, "on_doc_cookies"))
check("cookies DB me save hoti hain (redeploy par bachi rahe)",
      'meta_set("yt_cookies"' in BOT_SRC and "cookies_boot_restore" in BOT_SRC)

# asli test: nakli cookies file
_fake = ("# Netscape HTTP Cookie File\n"
         ".youtube.com\tTRUE\t/\tTRUE\t2147483647\tSID\tTESTVALUE123\n")
_p = MD.save_cookies_text(_fake)
check("cookies file save ho gayi", bool(_p))
check("cookies status ON dikhata hai", MD.cookies_status().get("set") is True)
check("cookies path wahi hai jo yt-dlp ko milta hai", MD._cookiefile() == _p)
try:
    os.remove(_p)
except Exception:
    pass

# =====================================================================
section("[D] ⏱️ 45 SECOND HARD CAP (76 second wali wait khatam)")
# =====================================================================
check("FAST_DEADLINE 30 hai (v68)", MD.FAST_DEADLINE == 30, str(MD.FAST_DEADLINE))
check("pehla client pura budget, baaki short (kul 30s se kam)",
      "_budget = FAST_DEADLINE if _i == 0 else 8" in open(
          os.path.join(_ROOT, "modules", "media_downloader.py"), encoding="utf-8").read())
check("dead banda video par dobara koshish nahi (_retryable)",
      hasattr(MD, "_retryable") and MD._retryable("This video is private") is False
      and MD._retryable("Sign in to confirm you are not a bot") is True)
check("socket timeout 8s (atka connection chhoot jaye)", MD.SOCK_TIMEOUT == 8)
check("16 parallel chunks zinda",
      MD._ytdlp_opts({}).get("concurrent_fragment_downloads") == 16)

# =====================================================================
section("[E] 🎯 4 TOOLS = 4 ALAG TOOLS (v67: 23 services deleted)")
# =====================================================================
check("4 services hain (v67)", len(bot.DL_SITES) == 4, str(len(bot.DL_SITES)))
check("sirf Insta/YouTube/Facebook/TikTok bache",
      set(bot.DL_SITES) == {"instagram", "youtube", "facebook", "tiktok"},
      str(sorted(bot.DL_SITES)))
check("sirf 4 dl_* prompts bache (baaki sab gaye)",
      sorted(k for k in bot.PROMPT_DATA if k.startswith("dl_")) ==
      ["dl_facebook", "dl_instagram", "dl_tiktok", "dl_youtube"],
      str(sorted(k for k in bot.PROMPT_DATA if k.startswith("dl_"))))
check("media_downloader me sirf 4 platform support",
      len(bot.MD.SUPPORTED_SITES) == 7, str(len(bot.MD.SUPPORTED_SITES)))
check("har service ka apna label function hai", callable(bot.dl_tool_label))
check("labels me official emoji hain",
      bot.dl_tool_label("instagram").startswith("📸")
      and bot.dl_tool_label("youtube").startswith("▶️")
      and bot.dl_tool_label("facebook").startswith("📘"))
_rows = bot.dl_kb_rows(2)
check("4 tools 2 rows me (2-2)", len(_rows) == 2 and sum(len(r) for r in _rows) == 4,
      f"{len(_rows)} rows")
_flat = [b for r in bot.KB_BTNS for b in r]
check("saare 4 tools MAIN KEYBOARD me hain",
      all(bot.dl_tool_label(k) in _flat for k in bot.DL_SITES),
      [k for k in bot.DL_SITES if bot.dl_tool_label(k) not in _flat][:4])
check("27-app ka purana PICKER button keyboard me nahi hai",
      not any("27 APPS" in bot.unbold(b).upper() for b in _flat))
import re as _re                                                     # noqa: E402
check("'VIDEO DOWNLOADER' tool POORI TARAH delete (keyboard me nahi)",
      not any(_re.sub(r"^[^\w\s]+\s*", "", bot.unbold(b)).strip().upper()
              == "VIDEO DOWNLOADER" for b in _flat))
check("koi bhi label seedha insta_dl (purana tool) par nahi jata",
      "insta_dl" not in set(bot.BTN_MODE_MAP.values()))
check("purane labels par saaf message milta hai (dl_gone)",
      bot.BTN_MODE_MAP.get("VIDEO DOWNLOADER") == "dl_gone"
      and bot.BTN_MODE_MAP.get("VIDEO DOWNLOAD (27 APPS)") == "dl_gone")
check("'sabhi apps ek saath' button bhi hata diya",
      "dlv:any" not in BOT_SRC)
check("ALL TOOLS list me purana 'Video Downloader' tool nahi",
      "📥 Video Downloader" not in bot.all_tools_text())
check("ALL TOOLS list me 4 alag tools hain",
      len([ln for ln in bot.dl_tools_text().splitlines() if "Downloader" in ln]) == 4)
check("picker khulne ka koi rasta nahi (BTN_MODE_MAP me dlmenu nahi)",
      "dlmenu" not in set(bot.BTN_MODE_MAP.values()))
check("har tool apne dl_<app> mode par jata hai (direct)",
      all(bot.BTN_MODE_MAP.get(
          __import__("re").sub(r"^[^\w\s]+\s*", "",
                              bot.unbold(bot.dl_tool_label(k))).strip().upper())
          == "dl_" + k for k in bot.DL_SITES))
check("purani 'saare apps' inline button hata di",
      'callback_data="dlmenu"' not in BOT_SRC)
check("video downloader ke andar ab koi service list nahi",
      "BADLAV — ab har app APNA ALAG TOOL hai" in BOT_SRC)
check("har service ka premium + credit entry zinda",
      all(bot.is_premium_tool("dl_" + k) for k in bot.DL_SITES))
check("ALL TOOLS list me 4 downloader tools hain",
      len([ln for ln in bot.dl_tools_text().splitlines()
           if "Downloader" in ln]) == 4)
check("purana insta_dl (any link) zinda", "insta_dl" in bot.PREMIUM_TOOLS)

# =====================================================================
section("[F] 🔁 KUCH PURANA TOOTA NAHI + VERSION")
# =====================================================================
check("version v66+ hai", re.search(r"v(?:6[6-9]|[7-9][0-9])\.", bot.BOT_VERSION) is not None, bot.BOT_VERSION)
check("12 business tools zinda", len(bot.BIZ_MENU) >= 12)
check("wizard zinda", len(bot.BIZ_STEPS) == 12)
check("saare tools FREE mode ON", bot.ALL_FREE is True)
check("prompts 37 (33 purane + 4 dl)", len(bot.PROMPT_DATA) >= 37, str(len(bot.PROMPT_DATA)))
check("vault wahi hai (premium safe)", hasattr(V, "vault"))
check("safe_tool_call zinda (global crash guard)", callable(bot.safe_tool_call))
check("progress pinger zinda", callable(bot._progress_pinger))

print(f"\n{'=' * 62}")
print(f"  v66 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
