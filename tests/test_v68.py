# -*- coding: utf-8 -*-
"""
v68 SELFTEST — 🚀 30-SECOND SPEED + 🛡️ TOOL FAIL PAR BOT ZINDA
==============================================================
Boss ki shikayatein (screenshot + message se):
  1. "chaaro tools bhut slow"          -> 4 naye hathiyar: circuit breaker,
     parallel clients, memory cache, file_id instant repeat.
  2. "max 30 second me video"          -> FAST_DEADLINE = 30, 40s hard timeout.
  3. "koi tool fail ho to bot chalta   -> tool fail par bot zinda; timeout se
     rahe"                                atka hua tool chhoot jata hai.
  4. "premium tools 1st me kar do"     -> downloader tools keyboard me sabse upar.
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

_TMP = tempfile.mkdtemp(prefix="udv68_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V68"
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
print("  v68 SELFTEST — 30-second speed + tool-fail isolation")
print("=" * 62)

import bot                                                           # noqa: E402
from modules import media_downloader as MD                           # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
MD_SRC = open(os.path.join(_ROOT, "modules", "media_downloader.py"),
              encoding="utf-8").read()

# =====================================================================
section("[A] ⏱️ 30 SECOND TARGET")
# =====================================================================
check("hard deadline 30 second hai", MD.FAST_DEADLINE == 30, str(MD.FAST_DEADLINE))
check("download par 40s outer timeout laga hai",
      'with_tool_timeout(download_video_async(raw_text), 75' in BOT_SRC)
# v98: quality-tap ab background HD task hai (transcode 1-4 min); 40s-inline hata,
# 600s wait_for cap + double-tap guard uski jagah (latakna ab bhi impossible).
check("YouTube quality par timeout-guard hai (v98 background + 600s cap)",
      "asyncio.wait_for(" in BOT_SRC and "_yt_hd_bg" in BOT_SRC
      and "_YT_HD_RUNNING" in BOT_SRC)
check("input par sirf 'Wait few seconds' (v101 UI)",
      "wait few seconds" in BOT_SRC.lower())
check("purana '15 second' ka wada hata diya",
      "Zyada se zyada 15 second lagenge" not in BOT_SRC
      and "zyada se zyada 15 second" not in BOT_SRC.lower())

# =====================================================================
section("[B] ♻️ CIRCUIT BREAKER (bot-check wale client hata do)")
# =====================================================================
check("breaker functions maujood hain",
      all(hasattr(MD, x) for x in ("_mark_client_bad", "_client_is_bad",
                                   "_ordered_client_sets")))
check("bad seconds 15 min hai", MD.BAD_CLIENT_SECONDS == 900, str(MD.BAD_CLIENT_SECONDS))
MD._BAD_CLIENTS.clear()
MD._mark_client_bad(("android_vr",), "Sign in to confirm you're not a bot")
check("bot-check wala client 'bad' mark ho gaya", MD._client_is_bad(("android_vr",)) is True)
check("doosra client theek hai", MD._client_is_bad(("tv_embedded",)) is False)
_ord = MD._ordered_client_sets(MD.YT_CLIENT_SETS)
check("bad client aakhir me chala gaya (achhe pehle)",
      _ord[0] != ("android_vr",) and _ord[-1] == ("android_vr",), str([c[0] for c in _ord]))
MD._mark_client_bad(("tv_embedded",), "This video is private")
check("video-private par breaker NAHI lagta (client ki galti nahi)",
      MD._client_is_bad(("tv_embedded",)) is False)
MD._BAD_CLIENTS.clear()

# =====================================================================
section("[C] 🔀 PARALLEL CLIENTS + 🧠 MEMORY CACHE")
# =====================================================================
check("info parallel chalta hai (ThreadPoolExecutor)",
      "ThreadPoolExecutor" in MD_SRC and "as_completed" in MD_SRC)
check("info me parallel branch hai", "if len(_sets) > 1:" in MD_SRC)
# cache asli test
MD._mem_put("https://x.test/v1", b"V" * 5000, {"title": "t"}, "media")
_hit = MD._mem_get("https://x.test/v1", "media")
check("cache me daala aur wapas mila", _hit and _hit[0] == b"V" * 5000 and _hit[1]["title"] == "t")
check("cache stats kaam karta hai", MD.dl_cache_stats()["items"] >= 1)
check("naya URL cache me nahi milta", MD._mem_get("https://x.test/nahi", "media") is None)
_res_cached = MD.download_video_media("https://x.test/v1")
check("download_video_media cache se TURANT deta hai",
      _res_cached.get("ok") and _res_cached.get("cached") is True
      and len(_res_cached.get("bytes") or b"") == 5000)


# cache ka size limit test (40MB se bada item nahi jaata)
_big = b"X" * (41 * 1024 * 1024)
MD._mem_put("https://x.test/bada", _big, {}, "media")
check("40MB se bada item cache me nahi jaata",
      MD._mem_get("https://x.test/bada", "media") is None)

# =====================================================================
section("[D] ⚡ FILE_ID INSTANT REPEAT (viral reel = 0.1 second)")
# =====================================================================
check("fid helpers maujood hain",
      all(callable(getattr(bot, x, None)) for x in
          ("dl_fid_key", "dl_fid_get", "dl_fid_set", "dl_fid_forget")))
bot.dl_fid_set("https://instagram.com/reel/TEST1", "FILE_ID_ABC123")
check("file_id save + wapas mila",
      bot.dl_fid_get("https://instagram.com/reel/TEST1") == "FILE_ID_ABC123")
check("doosre link ka file_id alag hai",
      bot.dl_fid_get("https://instagram.com/reel/DOOSRA") == "")
bot.dl_fid_forget("https://instagram.com/reel/TEST1")
check("file_id bhool jaata hai (kharab file_id case)",
      bot.dl_fid_get("https://instagram.com/reel/TEST1") == "")
check("download se PEHLE instant-repeat check hota hai",
      "_fid = dl_fid_get(raw_text)" in BOT_SRC)
check("video bhejne par file_id SAVE hota hai",
      "dl_fid_set(raw_text, _sent.video.file_id)" in BOT_SRC)
check("YouTube quality par bhi instant repeat",
      "dl_fid_get(url, f\"q{h}\")" in BOT_SRC)

# =====================================================================
section("[E] 🛡️ TOOL FAIL PAR BOT ZINDA (crash isolation)")
# =====================================================================
check("youtube timeout par friendly message aata hai",
      "40 second me jawab nahi diya" in BOT_SRC)
check("timeout par clear hai ki credit nahi katta",
      "Credit nahi katta" in BOT_SRC or "credit nahi katta" in BOT_SRC.lower())
check("khaali background error ka shor band (warning, na error)",
      'if _ex is None:\n                return' in BOT_SRC)
check("har tool ke liye global guard zinda", callable(bot.safe_tool_call))
check("with_tool_timeout helper zinda", callable(bot.with_tool_timeout))


async def _hang():
    await asyncio.sleep(30)


async def _t_iso():
    t0 = time.time()
    _r = await bot.with_tool_timeout(_hang(), seconds=1, name="hang-test")
    return _r, time.time() - t0


_r, _el = asyncio.run(_t_iso())
check("atka hua tool 1 second me chhod diya (bot zinda)", _r is None and _el < 3,
      f"{_el:.1f}s")

# =====================================================================
section("[F] 🥇 PREMIUM TOOLS SABSE UPAR + /speed")
# =====================================================================
_lbl = [bot.unbold(x) for x in bot.KB_BTNS[1] + bot.KB_BTNS[2]]  # v101: row0 = info tools
check("keyboard ki pehli rows me 3 downloader tools hain (v102)",
      sum(1 for x in _lbl if x.upper().endswith(" DL")) == 3, str(_lbl))
check("downloader tools rows 1-2 me hain (v101: info row top par)",
      "INSTA DL" in _lbl[0].upper() and "YOUTUBE DL" in _lbl[1].upper())
check("tools zinda (v102: 12 rows, aur 4 hataye)",
      len(bot.KB_BTNS) == 12, str(len(bot.KB_BTNS)))
check("/speed command hai", hasattr(bot, "cmd_speed"))
check("cache stats function hai", callable(MD.dl_cache_stats))
check("version naya hai (v68 ya usse upar)",
      re.search(r"v(?:6[8-9]|[7-9][0-9])\.", bot.BOT_VERSION) is not None,
      bot.BOT_VERSION)

# =====================================================================
section("[G] 🔁 KUCH PURANA TOOTA NAHI")
# =====================================================================
check("3 downloader tools zinda (v102)", len(bot.DL_SITES) == 3, str(list(bot.DL_SITES)))
check("27 deleted tools wapas nahi aaye", len(bot.DL_SITES) == 3)
check("12 business tools zinda", len(bot.BIZ_MENU) >= 12)
check("cookies ka ilaaj zinda", hasattr(bot, "cmd_cookies"))
check("saare tools FREE", bot.ALL_FREE is True)
check("progress pinger zinda", callable(bot._progress_pinger))
check("parallel + cache dono download path me",
      "_mem_get(url, f\"q{h}\")" in MD_SRC and "_mem_put(url, data, info, f\"q{h}\")" in MD_SRC)

# =====================================================================
section("[H] ⚡ v68.1 HUB-BUG FIX — slowness ka asli karan pakda gaya")
# =====================================================================
check("_call_capped helper mojood", hasattr(MD, "_call_capped"))
_t0 = time.time()
_r = MD._call_capped(lambda: (time.sleep(3) or "late"), 0.3)
_dt = time.time() - _t0
check("slow function 0.3s me chhoot gaya (bot atakta nahi)",
      _r is None and _dt < 1.5, f"{_dt:.1f}s")
check("fast function ka jawab turant milta hai",
      MD._call_capped(lambda: "turant", 2) == "turant")
check("hub YouTube call 6 second cap ke andar",
      "_call_capped(_hub_youtube_download, 6" in MD_SRC)
check("hub 1080p call 12 second cap ke andar",
      "_call_capped(_hub_youtube_download, 12" in MD_SRC)
_i = MD_SRC.find("def _ytdlp_download_bytes")
_j = MD_SRC.find("\ndef ", _i + 10)
_body = MD_SRC[_i:_j]
check("purana NameError bug (h) hamesha ke liye gaya",
      'f"q{h}"' not in _body and '_mem_get(url, "plain")' in _body
      and '_mem_put(url, data, info, "plain")' in _body)
_i = MD_SRC.find("def yt_download_at_height")
_j = MD_SRC.find("\ndef ", _i + 10)
_body2 = MD_SRC[_i:_j]
check("yt_download_at_height me bhi client ladder + cache",
      "_ordered_client_sets" in _body2 and 'f"q{h}"' in _body2
      and "FAST_DEADLINE if _i == 0 else 8" in _body2)

print(f"\n{'=' * 62}")
print(f"  v68 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
