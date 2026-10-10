#!/usr/bin/env python3
# =====================================================================
# v105.2 SELFTEST — RENDER FREE RAM-SAVER (no paid plan required)
#
# Regression checks for the 512MB OOM email fix:
#   * yt-dlp/Telethon no longer eagerly imported at startup
#   * at most one heavy media job per 512MB process
#   * media race keeps at most two downloader engines active
#   * Instagram parth-dl downloads are capped/streamed before buffering
#   * downloader limit is 48MB on free, configurable on larger RAM
#   * watchdog scans every 15s and restart point stays below OOM ceiling
#
# Run: python3 tests/test_v1052_memory.py
# =====================================================================
import os
import re
import sys
import time
import threading
import subprocess
import inspect
import logging

logging.disable(logging.CRITICAL)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT)
sys.path.insert(0, _ROOT)
PASS = 0
FAIL = []


def ok(name, cond, extra=""):
    global PASS
    if cond:
        PASS += 1
        print("  ✅ " + name)
    else:
        FAIL.append(name)
        print("  ❌ " + name + ((" — " + str(extra)) if extra else ""))


import modules.media_downloader as MD
import modules.core.guard as G
import modules.core.heavy as H

BOT_SRC = open("bot.py", encoding="utf-8").read()
MD_SRC = open("modules/media_downloader.py", encoding="utf-8").read()
GUARD_SRC = open("modules/core/guard.py", encoding="utf-8").read()

print("\n== 1) Heavy libraries load only when actually needed ==")
ok("yt_dlp module is not imported during media module boot",
   MD.yt_dlp is None and MD._yt_dlp_tried is False)
_SC = BOT_SRC.split("def _startup_selfcheck", 1)[1].split("\ndef ", 1)[0]
ok("startup dependency self-check uses find_spec (not import_module)",
   "_find_spec(_dep)" in _SC and "_il.import_module(_dep)" not in _SC)
_PI = BOT_SRC.split("async def _post_init", 1)[1].split("\nasync def ", 1)[0]
ok("MTProto warm-up default OFF (large-file feature remains lazy)",
   '_env_bool("BIGFILE_WARM", False)' in _PI and "asyncio.create_task(BF.warm())" in _PI)
# If yt-dlp is installed, prove lazy first-use resolves to a module.
try:
    from importlib.util import find_spec
    _has_ytdlp = find_spec("yt_dlp") is not None
except Exception:
    _has_ytdlp = False
if _has_ytdlp:
    ok("first actual yt-dlp use imports successfully", MD._ytdlp() is not None)
else:
    ok("missing optional yt-dlp remains safe", MD._ytdlp() is None)

print("\n== 2) Heavy gate obeys 512MB safety despite old env value 2 ==")
_env = os.environ.copy()
_env.update({"MEMORY_LIMIT_MB": "512", "HEAVY_MAX_SLOTS": "2",
             "HEAVY_DENY_MB": "435", "HEAVY_THROTTLE_MB": "380"})
_code = "import modules.core.heavy as h; print(h._MAX_SLOTS_CFG, h._DENY, h._THROTTLE)"
_r = subprocess.run([sys.executable, "-c", _code], cwd=_ROOT, env=_env,
                    capture_output=True, text=True, timeout=10)
_nums = _r.stdout.strip().split()
ok("512MB + old HEAVY_MAX_SLOTS=2 → effective slot cap 1",
   _r.returncode == 0 and _nums and _nums[0] == "1", _r.stdout + _r.stderr)
ok("512MB deny line capped to 80% (~409MB)",
   _r.returncode == 0 and len(_nums) >= 2 and _nums[1] == "409", _r.stdout)
_env.update({"MEMORY_LIMIT_MB": "2048", "HEAVY_MAX_SLOTS": "2"})
_r2 = subprocess.run([sys.executable, "-c", _code], cwd=_ROOT, env=_env,
                     capture_output=True, text=True, timeout=10)
_nums2 = _r2.stdout.strip().split()
ok("larger-memory deployment may still use configured 2 slots",
   _r2.returncode == 0 and _nums2 and _nums2[0] == "2", _r2.stdout + _r2.stderr)

print("\n== 3) Media race / transfers bounded ==")
_src_race = inspect.getsource(MD._race)
ok("race has max two downloader workers", "workers = min(2, len(fns))" in _src_race)
ok("race cancels remaining work on return", "fut.cancel()" in _src_race and "cancel_futures=True" in _src_race)
_ig_src = inspect.getsource(MD.download_instagram_media)
ok("parth/embed fast paths run before yt-dlp heavy fallback",
   _ig_src.index("_ig_parth(clean") < _ig_src.index("_ig_ytdlp(clean")
   and _ig_src.index("_ig_embed(clean") < _ig_src.index("_ig_ytdlp(clean"))
# A rolling race should never run >2 callbacks at once; all fail => all tested.
_lk = threading.Lock(); _active = 0; _peak = 0; _count = 0

def _worker():
    global _active, _peak, _count
    with _lk:
        _active += 1; _count += 1; _peak = max(_peak, _active)
    time.sleep(0.025)
    with _lk:
        _active -= 1
    return None

_res = MD._race([_worker for _ in range(7)], timeout=2)
ok("runtime race never exceeds 2 simultaneous engines", _res is None and _peak <= 2, _peak)
ok("rolling fallback still reaches all engines on failure", _count == 7, _count)

_pt = inspect.getsource(MD._ig_parth)
ok("parth direct video now uses capped streaming fetch", "_http_get_capped(v_url, MAX_TG_MB" in _pt and "r_v.content" not in _pt)
ok("parth photo/carousel image fetches capped before decode",
   "_http_get_capped(img_url, 15" in _pt and "_http_get_capped(u, 15" in _pt)
_jf = inspect.getsource(MD._jpeg_fit)
ok("giant compressed photos are stopped before pixel decode",
   "w * h > 40_000_000" in _jf and _jf.index("w * h > 40_000_000") < _jf.index("im.convert(\"RGB\")"))
ok("stream buffer uses bytearray rather than repeated immutable concat",
   "_buf = bytearray()" in MD_SRC and "data += chunk" not in MD_SRC)

# Test env-dependent cap without changing the user's environment permanently.
_old = {k: os.environ.get(k) for k in ("MEMORY_LIMIT_MB", "MAX_TG_MB")}
try:
    os.environ["MEMORY_LIMIT_MB"] = "512"; os.environ["MAX_TG_MB"] = "96"
    _freecap = MD._tg_cap_mb()
    os.environ["MEMORY_LIMIT_MB"] = "2048"; os.environ["MAX_TG_MB"] = "96"
    _bigcap = MD._tg_cap_mb()
finally:
    for k, v in _old.items():
        if v is None: os.environ.pop(k, None)
        else: os.environ[k] = v
ok("512MB plan clamps any requested media cap to 48MB", _freecap == 48, _freecap)
ok("larger RAM still allows explicit MAX_TG_MB=96", _bigcap == 96, _bigcap)

print("\n== 4) Watchdog protects before the 512MB kill ==")
_default_interval = inspect.signature(G.start_memory_watchdog).parameters["interval"].default
ok("watchdog scans every 15 seconds", _default_interval == 15.0, _default_interval)
_old_restart = os.environ.get("MEM_RESTART_MB")
try:
    os.environ["MEM_RESTART_MB"] = "470"
    _rat = G._effective_restart_mb(512)
finally:
    if _old_restart is None: os.environ.pop("MEM_RESTART_MB", None)
    else: os.environ["MEM_RESTART_MB"] = _old_restart
ok("old 470MB env is clamped below OOM (~430MB)", 0 < _rat <= 430.1, _rat)
ok("guard has earlier soft/hard fractions", "soft = limit_mb * 0.76" in GUARD_SRC
   and "hard = limit_mb * 0.82" in GUARD_SRC)
ok("Render blueprint defaults to one heavy slot + 48MB media cap",
   'key: HEAVY_MAX_SLOTS\n        value: "1"' in open("render.yaml", encoding="utf-8").read()
   and 'key: MAX_TG_MB\n        value: "48"' in open("render.yaml", encoding="utf-8").read())
ok("version is v105.2 and preserves wall replacement history",
   re.search(r'BOT_VERSION\s*=\s*\(?\s*"v105\.2 RAM-SAVER', BOT_SRC) is not None
   and "v105.1 WALL-OSINT" in BOT_SRC)

print("\n" + (f"🎉 v105.2 MEMORY SELFTEST: PASS {PASS} | FAIL 0" if not FAIL
                else "❌ FAILURES: " + "; ".join(FAIL)))
sys.exit(1 if FAIL else 0)
