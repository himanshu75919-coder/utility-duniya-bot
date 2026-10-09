#!/usr/bin/env python3
# =====================================================================
# v104 SELFTEST — 🏆 HD-TRUTH (YouTube quality + Instagram posts)
#
# User bug #1 (screenshot 10-Oct): "720 quality choose kiya — itna low
# quality video de rha, chhiiii." Root causes:
#   1) yt_download_at_height ka fmt "18/22/..." tha — itag 18 = 360p
#      HAMESHA jeet jaata tha, 720 maango ya 1080.
#   2) Hub fallback 360p file ko ffmpeg se 720 me stretch (upscale) karke
#      "720p" label chipka deta tha = blurry HD-jaisa file.
#   3) Loader.to v2 API ab ASLI 720/1080 deta hai (live naap 10-Oct:
#      1280x720 h264 @1.1Mbps) — par code me wo master-ladder ke baad
#      daba tha (156s) aur uska purana "720→360p" darr-map label galat
#      kar raha tha.
# v104: loader DIRECT-height pehle, ladder backup, fmt order fix, upscale
# par ROK, aur _yt_honest — jo file bheji jaaye uski height FFmpeg se NAAP
# kar hi label lagta hai. "Jo dabao, wahi milega — ya uska sach."
#
# User bug #2: "Instagram tools mein sirf reels ke links work kar rhe" —
# /p/ post par sirf 640px og:image (blurry, single) jaata tha. Private
# account ho to aur kuch milega hi nahi — ab 🔒 note ke saath sach bola
# jaata hai; public post/carousel par naya _ig_jina_hd engine poori album
# HD (1080-3072px) laata hai (r.jina.ai render se raw media URLs).
#
# Run: python3 tests/test_v104_hd.py
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
MD_SRC = open(os.path.join(_ROOT, "modules", "media_downloader.py"),
              encoding="utf-8").read()

print("\n== 1) yt_download_at_height — fmt ladder ka ORDER (18 ab pehle nahi) ==")
_f = inspect.getsource(MD.yt_download_at_height)
_fmt_block = _f[_f.index("if _HAS_FFMPEG:"): _f.index("else:")]
ok("purana f'18/22/' opener GAYAB (comment chhodo, code dekho)",
   'f"18/22/"' not in _fmt_block)
ok("22 (asli 720p progressive) shart ke saath pehle aata hai",
   'f"22/" if h >= 720' in _fmt_block)
ok("18 sirf aakhri fallback hai (b/best se pehle)",
   re.search(r"b\[height<=\{h\}\]/18/b/best", _fmt_block) is not None)

print("\n== 2) Loader label ka sach — purana 360p darr-map removed ==")
_l = inspect.getsource(MD._yt_loader)
ok('"720": "360p" wala fake-map nahi raha', '"720": "360p"' not in _l)
ok("loader result label seedha f\"{h}p\"", '"quality": f"{h}p"' in _l)

print("\n== 3) _yt_honest — FILE NAAP kar label (contract) ==")
ok("_yt_honest maujood", callable(getattr(MD, "_yt_honest", None)))
ok("_probe_data maujood", callable(getattr(MD, "_probe_data", None)))
_h = inspect.getsource(MD._yt_honest)
ok("non-video/link result ko haath nahi lagata", 'res.get("type") != "video"' in _h)
ok("asli height < request → relabel + note", 'res["quality"] = f"{_h}p"' in _h and "note_quality" in _h)
_q = inspect.getsource(MD._yt_quality_download)
ok("_yt_quality_download raw ko _yt_honest se guzarta hai", "_yt_honest(_yt_quality_download_raw" in _q)
ok("cache honest result ke BAAD banta hai", _q.index("_yt_honest") < _q.index("_mem_put"))

print("\n== 4) Chain ordering — loader-direct PEHLE, ladder backup ==")
_r = inspect.getsource(MD._yt_quality_download_raw)
ok("step1: _yt_loader(url, h) seedha maang par", re.search(r'_yt_loader\(url, h,', _r) is not None)
ok("step2: master-ladder sirf HD (720+) par backup", "_yt_loader_hd(url, 1080 if h >= 1080 else 720" in _r)
ok("step1 pehle aata hai, ladder baad me",
   _r.index("_yt_loader(url, h,") < _r.index("_yt_loader_hd("))
ok("hub branch: upscale guard (source<=target → transcode SKIP)",
   "_hh2 and _hh2 <= h" in _r and "nakli upscale nahi bheja" in _r)
ok("downscale sirf guard ke BAAD chalta hai",
   _r.index("_hh2 <= h") < _r.index('ds = downscale_video(hubres["bytes"]'))

print("\n== 5) IG — jina-HD engine + og ko HD-first wiring ==")
ok("_ig_jina_hd maujood", callable(getattr(MD, "_ig_jina_hd", None)))
ok("_ig_efg_res maujood", callable(getattr(MD, "_ig_efg_res", None)))
_j = inspect.getsource(MD._ig_jina_hd)
ok("private-account signal deta hai", '"private": True' in _j)
ok("suggested grid 'Discover something new' par kaatti hai", "Discover something new" in _j)
ok("profile picture/rsrc junk skip", "profile_pic" in _j and "rsrc.php" in _j)
ok("2+ photos = carousel contract (items list)", '"type": "carousel"' in _j and '"items": items' in _j)
_d = inspect.getsource(MD.download_instagram_media)
ok("og slot ab _hd_then_og (HD-first, phir og)", "_hd_then_og" in _d and "_ig_jina_hd" in _d)
ok("reel race me bhi _ig_jina_hd juda (wrapper + video engine = 2 jagah)",
   _d.count("_ig_jina_hd(clean") >= 2 and "_ig_jina(clean" in _d)
ok("photo budget 34s (jina cold render ke liye)", "34.0" in _d)
ok("private par honest 🔒 note lagta hai", "PRIVATE account" in _d)

print("\n== 6) _ig_efg_res live-verified URLs par ==")
U1 = ("https://scontent-sea5-1.cdninstagram.com/v/t51.82787-15/838893636_1864065743"
      "8011614_5395623996320912329_n.jpg?stp=dst-jpg_e35_tt6&_nc_cat=1&x=1"
      "&efg=eyJ2ZW5jb2RlX3RhZyI6IkNBUk9VU0VMX0lURU0ueHBpZHMuMzA3Mi5zZHIucmVndWxhcl9waG90by5DMyJ9")
ok("CAROUSEL_ITEM 3072 token → 3072", MD._ig_efg_res(U1) == 3072, MD._ig_efg_res(U1))
U2 = ("https://scontent-sea5-1.cdninstagram.com/v/t51.82787-15/1_2_3_n.webp"
      "?stp=c288.0.864.864a_dst-jpg_e35_s640x640_tt6&y=1")
ok("stp s640x640 → 640", MD._ig_efg_res(U2) == 640, MD._ig_efg_res(U2))
ok("anjaan URL → default 640 (safe)", MD._ig_efg_res("https://x.com/y.jpg") == 640)

print("\n== 7) bot.py — prewarm (v105: sirf 1080 — picker hi hata diya) ==")
ok("1080 prewarm maujood", "MD.yt_loader_prewarm(raw_text, 1080)" in BOT_SRC)

print("\n== 8) Version head ==")
ok("BOT_VERSION current head (v104+)",
   re.search(r'BOT_VERSION\s*=\s*\(?\s*"v10[4-9]\.', BOT_SRC) is not None)

print("\n" + ("🎉 v104 SELFTEST: SAB PASSED" if not FAIL
              else "❌ FAILURES: " + "; ".join(FAIL)))
sys.exit(1 if FAIL else 0)
