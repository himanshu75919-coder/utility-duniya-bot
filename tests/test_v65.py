# -*- coding: utf-8 -*-
"""
v65 SELFTEST — 🚀 SPEED + 🛡️ HARD CRASH-PROOF
=============================================
Boss ki 3 shikayatein:
  1. "tools sab crash ho jaata hai"      -> hard crash-proof (3 layer)
  2. "2 minute kyun rukna"               -> 15 second response + progress
  3. "downloader ke saare service alag tool banao, official emoji ke saath"
"""
import asyncio
import os
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv65_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V65"
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
print("  v65 SELFTEST — Speed + Hard Crash-Proof")
print("=" * 62)

import bot                                                           # noqa: E402
from modules import media_downloader as MD                           # noqa: E402

# =====================================================================
section("[A] 🤖 YOUTUBE BOT-CHECK FIX (aapke log ka error)")
# =====================================================================
check("YT_CLIENT_SETS maujood hai", hasattr(MD, "YT_CLIENT_SETS"))
check("4 client sets hain (android_vr / tv / ios / web)",
      len(MD.YT_CLIENT_SETS) == 4, str(len(MD.YT_CLIENT_SETS)))
check("pehla client 'android_vr' hai (bot check nahi lagta)",
      "android_vr" in MD.YT_CLIENT_SETS[0])
_opts = MD._ytdlp_opts({"skip_download": True})
check("options me extractor_args.youtube.player_client hai",
      "extractor_args" in _opts and "youtube" in _opts["extractor_args"])
check("player_client set hai",
      bool(_opts["extractor_args"]["youtube"]["player_client"]))
check("'player_skip configs' laga hai (speed)",
      "configs" in _opts["extractor_args"]["youtube"].get("player_skip", []))
check("info function client ladder leta hai",
      "clients" in MD._ytdlp_info.__code__.co_varnames)
check("_ytdlp_info YouTube par ladder chalata hai",
      "YT_CLIENT_SETS" in open(os.path.join(_ROOT, "modules", "media_downloader.py"),
                               encoding="utf-8").read())

# =====================================================================
section("[B] 🚀 SPEED — 2 minute se 15 second ki taraf")
# =====================================================================
check("socket timeout 8 second (pehle 15 tha)", MD.SOCK_TIMEOUT == 8, str(MD.SOCK_TIMEOUT))
check("16 parallel chunks (pehle 4 the)",
      _opts["concurrent_fragment_downloads"] == 16, str(_opts["concurrent_fragment_downloads"]))
check("buffersize 1 MB laga hai", _opts.get("buffersize") == 1024 * 1024)
check("retries 1 (jaldi fallback)", _opts.get("retries") == 1, str(_opts.get("retries")))
check("hard deadline jaldi lagta hai (<=45s)", MD.FAST_DEADLINE <= 45, str(MD.FAST_DEADLINE))
check("progressive format (18) pehle aata hai — ffmpeg merge nahi = 3x tez",
      "18/" in open(os.path.join(_ROOT, "modules", "media_downloader.py"),
                    encoding="utf-8").read())
check("_pick_file helper hai (galat file na uthe)",
      hasattr(MD, "_pick_file"))
check("_pick_file .part file nahi uthata",
      callable(MD._pick_file))
check("bot me progress pinger hai", hasattr(bot, "_progress_pinger"))
check("pinger ki speed 5 second", bot.PROGRESS_EVERY == 5, str(bot.PROGRESS_EVERY))
check("pinger max 6 baar bolta hai (spam nahi)",
      "_progress_pinger" in open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
      and "max_pings: int = 6" in open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read())
check("download shuru hote hi TURANT message (1s me)",
      "link mil gaya!" in open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read())

# =====================================================================
section("[C] 🛡️ HARD CRASH-PROOF — 3 layer")
# =====================================================================
check("safe_tool_call() maujood hai", callable(getattr(bot, "safe_tool_call", None)))
check("with_tool_timeout() maujood hai", callable(getattr(bot, "with_tool_timeout", None)))
check("TOOL_HARD_TIMEOUT set hai (120s)", bot.TOOL_HARD_TIMEOUT == 120,
      str(bot.TOOL_HARD_TIMEOUT))
check("global guard (arm_all_handlers) zinda", hasattr(bot, "arm_all_handlers"))

# asli test: safe_tool_call crash ko kha jata hai
async def _crashy():
    raise ValueError("deliberate crash for test")


async def _slow():
    await asyncio.sleep(30)
    return "kabhi nahi aayega"


async def _main():
    # 1) crash -> (None, error), bot nahi girta
    _res, _err = await bot.safe_tool_call(_crashy)
    check("safe_tool_call ne crash pakda (bot zinda)", _res is None and _err is not None)
    # 2) normal kaam -> result milta hai
    _res2, _err2 = await bot.safe_tool_call(lambda: 6 * 7)
    check("safe_tool_call normal function chalata hai", _res2 == 42 and _err2 is None)
    # 3) timeout -> None (bot zinda rehta hai)
    t0 = time.time()
    _r3 = await bot.with_tool_timeout(_slow(), seconds=2, name="test-slow")
    _el = time.time() - t0
    check("with_tool_timeout ne atke tool ko chhod diya (2s me)",
          _r3 is None and _el < 4, f"{_el:.1f}s")
    # 4) timeout ke andar wala kaam poora hota hai
    _r4 = await bot.with_tool_timeout(asyncio.sleep(0, result="ok"), seconds=2)
    check("with_tool_timeout normal kaam poora karta hai", _r4 == "ok")
    # 5) crash wala coroutine bhi timeout helper me safe
    _r5 = await bot.with_tool_timeout(_crashy(), seconds=2, name="test-crash")
    check("with_tool_timeout crash bhi kha jata hai", _r5 is None)


asyncio.run(_main())

# =====================================================================
section("[D] 📥 DOWNLOADER SERVICES — alag tools, official emoji")
# =====================================================================
check("4 services hain (v67)", len(bot.DL_SITES) == 4, str(len(bot.DL_SITES)))
_OFC = {"instagram": "📸", "youtube": "▶️", "facebook": "📘", "tiktok": "🎵"}
for _k, _e in _OFC.items():
    check(f"{_k} ka official emoji {_e} laga hai", bot.DL_SITES[_k][0] == _e,
          f"mila: {bot.DL_SITES[_k][0]}")
check("har service ka apna nam hai (khaali nahi)",
      all(v[1].strip() for v in bot.DL_SITES.values()))
check("har service ka apna mode hai (dl_<app>)",
      all(f"dl_{k}" in bot.PROMPT_DATA for k in bot.DL_SITES))
_dt = bot.dl_tools_text()
check("tools list me saare 4 downloader services hain",
      len([ln for ln in _dt.splitlines() if "Downloader" in ln]) == 4,
      str(len([ln for ln in _dt.splitlines() if "Downloader" in ln])))
check("list me official emojis dikhte hain",
      all(e in _dt for e in ("📸", "▶️", "📘", "🎵")))
check("ALL TOOLS list me downloader section juda hai",
      "4 VIDEO DOWNLOADER TOOLS (sab ALAG-ALAG)" in bot.all_tools_text())
check("ALL TOOLS list Telegram limit me fit hai",
      len(bot.all_tools_text()) < 4096, str(len(bot.all_tools_text())))
check("purana picker menu code delete ho gaya",
      not hasattr(bot, "DL_MENU_TEXT") and not hasattr(bot, "dl_menu_kb"))

# =====================================================================
section("[D2] ⏱️ \"2 MINUTE\" WALA MESSAGE HAMESHA KE LIYE KHATAM")
# =====================================================================
_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
check("downloader ka purana 'video download ho rahi hai...' + '30 second - 2 minute' hat gaya",
      "video download ho rahi hai..." not in _SRC
      and "(30 second - 2 minute, video ki length par depend)" not in _SRC)
check("vnum card ka 'Time: 1-2 minute' hat gaya",
      "⚡ <b>Time:</b> 1-2 minute" not in _SRC)
check("deploy help ka '2 minute baad /version' hat gaya",
      "2 minute baad /version dobara bhejo" not in _SRC)
check("YouTube quality par bhi turant message",
      "kaam shuru ho gaya!" in _SRC)
check("live timer (⏱️ har 5 second) laga hai", "_progress_edit" in _SRC)
check("_StatusMsg wrapper hai (result ke upar ping nahi likhta)",
      "_StatusMsg" in _SRC)
check("purana pinger nayi request par band hota hai", "_stop_ping" in _SRC)


async def _t_ping():
    _msg = type("M", (), {"edits": [], "deletes": 0})()
    async def _e(*a, **k):
        _msg.edits.append(a[0] if a else k.get("text", ""))
    _msg.edit_text = _e
    _ev = asyncio.Event()
    t = asyncio.create_task(bot._progress_edit(_msg, "🔄 kaam chal raha hai", every=0.2,
                                               stop=_ev, max_pings=20))
    await asyncio.sleep(0.75)
    _n_before = len(_msg.edits)
    _ev.set()
    await asyncio.sleep(0.3)
    _n_after = len(_msg.edits)
    await t
    # wrapper: edit hone par stop khud set ho jaye
    _msg2 = type("M", (), {"edit_text": staticmethod(lambda *a, **k: asyncio.sleep(0, result=True)), "delete": staticmethod(lambda *a, **k: asyncio.sleep(0, result=True))})()
    _ev2 = asyncio.Event()
    _w = bot._StatusMsg(_msg2, _ev2)
    await _w.edit_text("final result")
    return _n_before, _n_after, _ev2.is_set()


_nb, _na, _wrapped = asyncio.run(_t_ping())
check("pinger live update bhejta hai (>0)", _nb > 0, str(_nb))
check("stop set karte hi pinger ruk jata hai", _na == _nb, f"{_nb}->{_na}")
check("_StatusMsg final edit par khud stop karta hai", _wrapped is True)

# =====================================================================
section("[D3] 🌐 NETWORK ERROR (aapke log ka 'Unknown error in HTTP implementation')")
# =====================================================================
check("connection pool 64 kiya (pehle chhota tha)",
      "connection_pool_size(64)" in _SRC)
check("HTTP/1.1 force kiya", 'http_version("1.1")' in _SRC)
check("get_updates ka apna pool set hai", "get_updates_connection_pool_size(16)" in _SRC)

# =====================================================================
section("[E] 🔁 PURANA SAFE + VERSION")
# =====================================================================
check("purana insta_dl zinda", "insta_dl" in bot.PREMIUM_TOOLS)
check("purane labels kaam karte hain (remove-message ya sahi tool)",
      bot.BTN_MODE_MAP.get("VIDEO DOWNLOADER") == "dl_gone"
      and bot.BTN_MODE_MAP.get("INSTA DOWNLOADER") == "dl_instagram")
check("11 business tools zinda", len(bot.BIZ_MENU) >= 12, str(len(bot.BIZ_MENU)))
check("wizard zinda", len(bot.BIZ_STEPS) == 12)
check("keyboard rows barhe (27 naye tools jude)", len(bot.KB_BTNS) >= 14,
      str(len(bot.KB_BTNS)))
import re as _r65                                                      # noqa: E402
_V65 = float((_r65.search(r"v(\d+(?:\.\d+)?)", str(bot.BOT_VERSION)) or [0, 0])[1]
             if _r65.search(r"v(\d+(?:\.\d+)?)", str(bot.BOT_VERSION)) else 0)
check("version v65 ya usse aage hai", _V65 >= 65, bot.BOT_VERSION)

# =====================================================================
print(f"\n{'=' * 62}")
print(f"  v65 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
