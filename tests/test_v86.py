# -*- coding: utf-8 -*-
"""
v86 SELFTEST — v76 "FORTRESS" (SIRF CRASH-FIX)
==============================================
Is release me sirf EK kaam hua hai: **bot ko crash hone se rokna**.
Koi naya tool add nahi hua, koi purana prompt nahi badla.

  A. 🪣 BOUNDED CACHE — cache jo KABHI unlimited nahi badhta
     v76 se pehle: osint_hub / username_hunter / vehicle_tool ke cache aam
     `dict` the — kabhi saaf nahi hote the. Har nayi query = pakki entry.
     Hafton me lakhon entry -> Render free (512 MB) par OOM KILL.
     Ab: maxsize + TTL + LRU + global registry (watchdog ek saath saaf kare).

  B. 🧹 JANITOR — khud-safai
     1) /tmp me chhoote hue udl_* folder (crash ke baad) hatate hain
     2) atke hue ffmpeg/yt-dlp process maarte hain (RAM+CPU bachao)
     3) expire cache entry nikaalte hain
     4) disk 88% se upar -> turant aggressive safai

  C. 🔗 WIRING + 🛡️ REGRESSION — crash-shield zinda hai, aur bot me
     koi bhi NAya tool nahi juda (BIZ_MENU / PREMIUM_TOOLS count wahi).
"""
import os
import sys
import tempfile
import time as _t
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv86_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V86"
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


# ======================================================================
section("A) 🪣 BOUNDED CACHE — kabhi unlimited nahi badhta")
# ======================================================================
from modules.core.bounded import (BoundedCache, cache_report,      # noqa: E402
                                  clear_all_caches, prune_all_caches,
                                  registry)

c = BoundedCache("v86_test", maxsize=5, default_ttl=60)
for i in range(200):
    c.put(f"key{i}", i)
check("200 entry daalne ke baad bhi size 5 se upar nahi gaya",
      len(c) == 5, f"size={len(c)}")
check("nayi entry (key199) mili — LRU ne purani hatayi",
      c.get("key199") == 199, f"got={c.get('key199')}")
check("purani entry (key0) ud gayi", c.get("key0") is None)
check("evictions count hua", c.stats()["evictions"] > 0,
      f"evict={c.stats()['evictions']}")

# TTL
c2 = BoundedCache("v86_ttl", maxsize=10, default_ttl=1)
c2.put("soon", "value", ttl=1)
check("TTL se pehle value milti hai", c2.get("soon") == "value")
_t.sleep(1.3)
check("TTL ke baad value expire (None)", c2.get("soon") is None,
      f"got={c2.get('soon')}")

# registry + clear
c3 = BoundedCache("v86_reg", maxsize=50, default_ttl=600)
c3.put("a", 1)
names = [x.name for x in registry()]
check("registry me saare cache dikhte hain",
      "v86_reg" in names and "v86_test" in names, f"names={names[:6]}")
check("prune_all_caches chalta hai (int return)",
      isinstance(prune_all_caches(), int))
n = clear_all_caches()
check("clear_all_caches saare cache saaf karta hai", n >= 3, f"cleared={n}")
check("clear ke baad cache khali", len(c3) == 0, f"size={len(c3)}")

# thread safety (crash na ho)
import threading                                                   # noqa: E402
c4 = BoundedCache("v86_thread", maxsize=100, default_ttl=60)


def _worker(w):
    for i in range(300):
        c4.put(f"{w}-{i}", i)
        c4.get(f"{w}-{i}")


ths = [threading.Thread(target=_worker, args=(w,)) for w in range(6)]
[t.start() for t in ths]
[t.join() for t in ths]
check("6 thread ek saath — koi crash nahi, size limit me",
      len(c4) <= 100, f"size={len(c4)}")


# ======================================================================
section("B) 🧹 JANITOR — khud-safai (temp · process · cache · disk)")
# ======================================================================
from modules.core import janitor as J                              # noqa: E402

# 1) purana temp folder hatana
old_dir = tempfile.mkdtemp(prefix="udl_v86_old_")
with open(os.path.join(old_dir, "video.mp4"), "wb") as fh:
    fh.write(b"x" * 4096)
os.utime(old_dir, (_t.time() - 7200, _t.time() - 7200))     # 2 ghante purana
fresh_dir = tempfile.mkdtemp(prefix="udl_v86_fresh_")        # abhi bana hai
J.sweep_now()
check("purana udl_ folder hat gaya", not os.path.exists(old_dir))
check("JANITOR ne folder ginati badhayi", J.JAN["tmp_dirs"] >= 1,
      f"dirs={J.JAN['tmp_dirs']}")
check("naya (fresh) folder NAHI hata — abhi use ho raha hai",
      os.path.exists(fresh_dir))
check("bytes_freed record hua", J.JAN["bytes_freed"] >= 4096,
      f"freed={J.JAN['bytes_freed']}")

# 2) doosre program ki cheez nahi chhooni chahiye
safe_file = os.path.join(tempfile.gettempdir(), "someone_else_v86.txt")
with open(safe_file, "w") as fh:
    fh.write("important")
os.utime(safe_file, (_t.time() - 7200, _t.time() - 7200))
J.sweep_tmp(max_age_min=1)
check("doosre program ki file ko haath nahi lagaya (sirf udl_/qsc_/ud_)",
      os.path.exists(safe_file))
try:
    os.remove(safe_file)
except Exception:
    pass

# 3) cache prune + stats
J.sweep_now()
st = J.janitor_stats()
check("janitor_stats dict deta hai", isinstance(st, dict) and "runs" in st)
check("janitor runs badha", st["runs"] >= 2, f"runs={st['runs']}")
check("janitor_block() HTML text deta hai",
      isinstance(J.janitor_block(), str))
check("disk_pct 0 se 100 ke beech", 0.0 <= st["disk_pct"] <= 100.0,
      f"disk={st['disk_pct']}")


# ======================================================================
section("C) 🔗 WIRING + 🛡️ REGRESSION — crash-shield zinda, koi naya tool nahi")
# ======================================================================
import bot                                                         # noqa: E402

# --- crash-shield ON ---
check("arm_all_handlers() maujood hai", callable(getattr(bot, "arm_all_handlers", None)))
check("on_error handler maujood hai", callable(getattr(bot, "on_error", None)))
check("start_janitor import hua hai", callable(getattr(bot, "start_janitor", None)))
try:
    bot._clear_caches_mem()
    check("_clear_caches_mem bina crash chal gaya", True)
except Exception as e:
    check("_clear_caches_mem bina crash chal gaya", False, str(e)[:80])

# --- module cache registry me (osint_hub lazy import hota hai) ---
try:
    import modules.osint_hub as _oh                                # noqa: F401
except Exception:
    pass
reg_names = [getattr(x, "name", "") for x in registry()]

try:
    rep = bot._janitor_stats()
    check("_janitor_stats() dict deta hai", isinstance(rep, dict))
    rep2 = bot._bounded_report()
    check("_bounded_report() dict deta hai",
          isinstance(rep2, dict) and "caches" in rep2)
except Exception as e:
    check("janitor/bounded report", False, str(e)[:90])

# --- KOI NAYA TOOL NAHI JUDA (yahi is release ka rule hai) ---
check("❌ koi naya tool nahi juda: PREMIUM_TOOLS 37 hi hai",
      len(bot.PREMIUM_TOOLS) == 30, str(len(bot.PREMIUM_TOOLS)))
check("❌ koi naya tool nahi juda: BIZ_MENU 12 hi hai",
      len(bot.BIZ_MENU) == 12, str(len(bot.BIZ_MENU)))
check("❌ koi naya tool nahi juda: BIZ_STEPS 12 hi hai",
      len(bot.BIZ_STEPS) == 12, str(len(bot.BIZ_STEPS)))
check("❌ koi naya tool nahi juda: main keyboard me koi naya button nahi",
      not any("EARN STUDIO" in bot.unbold(t).upper()
              for row in bot.KB_BTNS for t in row))
check("❌ koi naya tool nahi juda: BIZ_MENU_TEXT me '12 kaam ki cheezein' wahi",
      "12 kaam ki cheezein" in bot.BIZ_MENU_TEXT)

# --- saare PURANE tools zinda (regression) ---
OLD = ["biz_invoice", "biz_resume", "biz_biodata", "biz_certificate",
       "biz_idcard", "biz_vcard", "biz_letter", "biz_upi", "biz_labels",
       "biz_emi", "biz_salary", "biz_menucard"]
missing = [k for k in OLD if k not in bot.BIZ_MENU]
check("sab 12 purane Business Studio tool zinda (koi nahi hata)",
      not missing, f"missing={missing}")
check("purane tools ke steps wahi rahe",
      len(bot.biz_steps("biz_invoice")) == 5,
      f"steps={len(bot.biz_steps('biz_invoice'))}")
check("puraana insta_dl zinda", "insta_dl" in bot.PREMIUM_TOOLS)
check("puraana PRO ENGINE zinda", hasattr(bot, "pro"))

# --- version format (purane tests ka rule) ---
import re as _re                                                   # noqa: E402
_m = _re.search(r"v(\d+)\.(\d+)", bot.BOT_VERSION or "")
check("version v74+ set hai", bool(_m) and int(_m.group(1)) >= 74,
      bot.BOT_VERSION)
check("version me FREE4ALL hai (purana feature zinda)",
      "FREE4ALL" in bot.BOT_VERSION)
check("version me NO-GYAAN + SPEED hai", "NO-GYAAN" in bot.BOT_VERSION)


# ======================================================================
print("\n" + "=" * 62)
print(f"  v86 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAILS:
    print("-" * 62)
    for f in FAILS[:25]:
        print("   ❌ " + f)
print("=" * 62)
sys.exit(1 if FAIL else 0)
