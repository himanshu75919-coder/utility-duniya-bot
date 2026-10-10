# -*- coding: utf-8 -*-
"""v107 — PRO-SPEED upgrade offline tests (network nahi chahiye).

Check karta hai:
  1. RAM-SAVER-III: osint_tools import par phonenumbers LOAD NAHI hota
     (boot se ~112 MB kam), pehli lookup par load hota hai, output same.
  2. Emergency RAM valve: drop_geocoder() geocoder wapas chhodta hai.
  3. IG engine order + budget (live-audit wala order code me hai).
  4. user_safe_error: raw upstream kachra clean hota hai, saaf message safe.
  5. ig_fast login-wall backoff: 3 wall ke baad 10 min break.
  6. bot.py: gaming_tools ka zikr nahi (self-check FAIL hataya), version v107.
"""
import os
import sys
import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAIL = 0


def check(name, cond):
    global FAIL
    if cond:
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


print("=" * 62)
print("1) RAM-SAVER-III — phonenumbers lazy import")
print("=" * 62)
check("phonenumbers pehle se loaded nahi", "phonenumbers" not in sys.modules)
from modules import osint_tools as OSN  # noqa: E402

check("osint_tools import ke baad bhi phonenumbers lazy", OSN.PN_LOADED is False
      and "phonenumbers" not in sys.modules)
r = OSN.lookup_phone_info("9876543210")
check("lookup chalta hai (ok ya saaf error)", isinstance(r, dict))
check("lookup ke baad phonenumbers loaded", OSN.PN_LOADED is True
      and "phonenumbers" in sys.modules)
if r.get("ok"):
    check("carrier/timezone fields maujood",
          ("operator" in r) and ("timezones" in r) and ("country" in r))
check("drop_geocoder() True deta hai", OSN.drop_geocoder() is True)
check("drop ke baad geocoder None", OSN.geocoder is None)
r2 = OSN.lookup_phone_info("+919876543210")
check("drop ke baad bhi lookup chalta hai", isinstance(r2, dict) and r2.get("ok"))
check("geocoder dobara load ho gaya", OSN.geocoder is not None)

print("=" * 62)
print("2) IG ENGINE ORDER + BUDGET (live audit 10 Oct 2026)")
print("=" * 62)
from modules import media_downloader as MD  # noqa: E402

src = inspect.getsource(MD.download_instagram_media)
vid_part = src.split("if want_video:", 1)[1].split("else:", 1)[0]
post_part = src.split("else:", 1)[1].split("_budget", 1)[0]
check("video: parth sabse pehle", vid_part.find("_ig_parth") < vid_part.find("_ig_loader_reel"))
check("video: loader-ig rescue aakhir me",
      vid_part.find("_ig_loader_reel") < vid_part.find("_ig_wayback"))
check("video: budget 40s", "_budget = 40.0" in src)
check("post: embed_album parth ke turant baad",
      post_part.find("_ig_embed_album") < post_part.find("_hd_then_og"))
check("post: budget 26s", "_budget = 26.0" in src)
check("RAM cache 12 MB", MD._DL_MEM_MAX_BYTES == 12 * 1024 * 1024)

print("=" * 62)
print("3) USER-SAFE ERROR SANITIZER")
print("=" * 62)
bad = MD.user_safe_error("Media number out of range.", "Instagram")
check("raw upstream string clean hua", "out of range" not in bad.lower())
check("clean message me credit-note hai", "credit" in bad.lower())
good = "🔐 Instagram STORY bina login ke kisi ko nahi milti."
check("saaf Hinglish message unchanged", MD.user_safe_error(good, "Instagram") == good)
hindi = "ये पोस्ट प्राइवेट है — कुछ नहीं मिल सकता।"
check("Devanagari message unchanged", MD.user_safe_error(hindi, "Instagram") == hindi)
own = "📸 Media nahi nikal paya — dekho post public hai kya (private/age-restrict post nahi chalti)."
check("bot ka apna IG error unchanged", MD.user_safe_error(own, "Instagram") == own)
check("khaali reason par generic safe", "credit" in MD.user_safe_error("", "Instagram").lower())

print("=" * 62)
print("4) IG_FAST LOGIN-WALL BACKOFF")
print("=" * 62)
from modules import ig_fast as IF  # noqa: E402

IF._WALL_UNTIL = 0.0
IF._WALL_STREAK = 0
for _ in range(3):
    IF._wall_mark()
check("3 wall ke baad break ON", IF.wall_active() is True)
IF._WALL_UNTIL = 0.0
IF._WALL_STREAK = 0
check("reset ke baad break OFF", IF.wall_active() is False)
d = IF.diagnostics()
check("diagnostics me wall fields", "wall" in d and "wall_hits" in d)

print("=" * 62)
print("5) BOT.PY SELF-CHECK + VERSION")
print("=" * 62)
bot_src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "bot.py"), encoding="utf-8").read()
check("gaming_tools reference hataya", "gaming_tools" not in bot_src)
check("version v107", "v107.0 PRO-SPEED" in bot_src)
check("insta_dl fail path sanitizer use karta hai", "MD.user_safe_error" in bot_src)

print("=" * 62)
print("6) GUARD EMERGENCY VALVE HOOK")
print("=" * 62)
from modules.core import guard as GD  # noqa: E402

gsrc = inspect.getsource(GD.free_memory)
check("free_memory me geocoder valve", "drop_geocoder" in gsrc)
check("limit_mb_hint maujood", callable(getattr(GD, "limit_mb_hint", None)))

print("=" * 62)
if FAIL:
    print(f"❌ {FAIL} check FAIL")
else:
    print("✅ v107: saare checks PASS")
print("=" * 62)
sys.exit(1 if FAIL else 0)
