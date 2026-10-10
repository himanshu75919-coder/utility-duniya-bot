#!/usr/bin/env python3
# =====================================================================
# v105 SELFTEST — 🚀 BEST-ONLY (YouTube picker hatao) + 🎬 IG reels LIVE
#
# User order (11-Oct):
#  1) "YouTube me quality choose karne wala option hi hta do — link bhejo
#     to best quality extract kar do." → picker GAYAB, seedha _yt_hd_bg(1080).
#  2) "Instagram: reels/posts (7-8 photos wali)/stories ke saare links usi
#     quality me work karne chahiye." → reels ke liye NAYA engine: loader.to
#     IG-support (live proof 10 Oct: public reel → 12-19s me genuine MP4);
#     parth-dl wapas chalu (720×1280 reel, full albums) — dono par ASLI
#     quality ka naap (probe) lagta hai, aur bot ab 360p par "(FHD)" nahi
#     likhta. jina-hd photo cap 1600→2400px + q93 = practically original.
#
# Run: python3 tests/test_v105_best_only.py
# =====================================================================
import os
import re
import sys
import inspect
import logging

logging.disable(logging.CRITICAL)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
FAIL = []


def ok(name, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + name + (("  " + str(extra)) if not cond and extra else ""))
    if not cond:
        FAIL.append(name)


import modules.media_downloader as MD                                  # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

print("\n== 1) YouTube — PICKER PURI TARAH HATAA ==")
ok("ytq button build nahi hota", 'callback_data=f"ytq:{h}"' not in BOT_SRC)
ok("'YOUTUBE QUALITY CHUNO' text gayab", "QUALITY CHUNO" not in BOT_SRC)
ok("list(YT_QUALITY_OPTIONS) ka use khatam", "list(YT_QUALITY_OPTIONS)" not in BOT_SRC)
ok("message flow seedha _yt_hd_bg(1080) chalata hai",
   "uid, raw_text, 1080, _st105," in BOT_SRC)
ok("1080 prewarm shuru hote hi", "MD.yt_loader_prewarm(raw_text, 1080)" in BOT_SRC)
ok("file_id instant-hit (q1080) bacha hua", 'dl_fid_get(raw_text, "q1080")' in BOT_SRC)
ok("ytq handler purane buttons ke liye compat ke roop me zinda",
   'if data.startswith("ytq:")' in BOT_SRC)
ok("ytq handler ka dead inline-send block safai ho gaya",
   BOT_SRC.count("VIDEO READY NAHI HUI") == 1 and "YOUTUBE VIDEO — {h}p" not in BOT_SRC)
ok("pinger ka jhootha 'max 30s' wala label hataya", "({el}s / max 30s)" not in BOT_SRC)
ok("insta tool timeout 40→75s (reel engine ke liye)",
   'with_tool_timeout(download_video_async(raw_text), 75, "video-dl")' in BOT_SRC)

print("\n== 2) Caption — ab SIRF asli quality dikhti hai ==")
_fhd = re.findall(r".*\(FHD\).*", BOT_SRC)
ok("FHD har file par blind nahi chipakta (conditional bana)", len(_fhd) == 1)
ok("FHD sirf 1080p/1440p par", "'1080p','1440p'" in _fhd[0], _fhd)
ok("bina-label case me honest fallback line",
   "jo publicly available best thi" in BOT_SRC)
ok("_yt_hd_bg header bhi measured quality dikhata hai",
   "YOUTUBE VIDEO — {hesc(str(_q))}" in BOT_SRC)

print("\n== 3) IG reels — loader-ig engine (v105 ka naya raasta) ==")
ok("_ig_loader_reel maujood", callable(getattr(MD, "_ig_loader_reel", None)))
ok("_ig_ensure_playable maujood", callable(getattr(MD, "_ig_ensure_playable", None)))
_lr = inspect.getsource(MD._ig_loader_reel)
ok("loader.to ko IG link format=1080 ke saath bheja jaata hai",
   "download.php?format=1080" in _lr)
ok("job poll ke baad file size+type guard", "_http_get_capped(dl, MAX_TG_MB" in _lr
   and 'len(data) < 20000' in _lr)
ok("label FILE NAAP se (jhooth impossible)", "_probe_data(data)" in _lr and 'f"{_h}p"' in _lr)
_pl = inspect.getsource(MD._ig_ensure_playable)
ok("h264 ho to re-encode SKIP", "Video:\\s*h264" in _pl)
ok("VP9/HEVC → h264 re-encode (Telegram streaming)", "libx264" in _pl)
_d = inspect.getsource(MD.download_instagram_media)
ok("loader-ig race me wire hai", "_ig_loader_reel(clean" in _d)
ok("reel budget 55s (job 12-45s ke liye)", "55.0" in _d)

print("\n== 4) parth-dl — wapas zinda, ab meta ke saath ==")
_pt = inspect.getsource(MD._ig_parth)
ok("video return par duration+quality naap", "_probe_data(r_v.content)" in _pt
   and '"duration": int(_dv or 0)' in _pt)
ok("album 20 photos tak (v86 cap bacha)", "entries[:20]" in _pt)

print("\n== 5) Photos — ORIGINAL ke kareeb quality ==")
_jh = inspect.getsource(MD._ig_jina_hd)
ok("jina-hd photo cap 2400px q93", "max_px=2400, quality=93" in _jh)
ok("album 12 photos tak (user: '7-8 ya kitni bhi')", "[:12]" in _jh)
MD_SRC = open(os.path.join(_ROOT, "modules", "media_downloader.py"), encoding="utf-8").read()
_src_jf = MD_SRC
ok("_jpeg_fit signature q94 (real check)",
   "def _jpeg_fit(raw: bytes, max_px: int = 2160, quality: int = 94):" in MD_SRC)

print("\n== 6) Stories — abhi bhi honest (wall sach me hai) ==")
ok("story fail par wajah-bata error (v103) intact",
   "Instagram Story nahi mili" in _src_jf and "24 ghante" in _src_jf)
ok("story ke liye bhi _ig_jina_hd try hota hai (base list)",
   "_ig_jina_hd" in _src_jf and "_hd_then_og" in _src_jf)

print("\n== 7) Version head ==")
ok("BOT_VERSION v105.0 BEST-ONLY",
   re.search(r'BOT_VERSION\s*=\s*\(?\s*"v105\.[01]', BOT_SRC) is not None)

print("\n" + ("🎉 v105 SELFTEST: SAB PASSED" if not FAIL else "❌ FAILURES: " + "; ".join(FAIL)))
sys.exit(1 if FAIL else 0)
