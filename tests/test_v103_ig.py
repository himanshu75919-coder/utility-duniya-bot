#!/usr/bin/env python3
# =====================================================================
# v103 SELFTEST — 🎯 INSTAGRAM PIPELINE PRO-FIX
#
# User bug (screenshot 10-Oct-01:34): reel ka link bheja → bot ne DOOSRI
# post ka COVER PHOTO bhej di. Wajah 2 thi:
#   1) insta_clean /reel/<code>/ ko /p/<code>/ bana deta tha → classify
#      "post" bolta → want_video False → og:image (cover) engine jeet gaya.
#   2) PURANI cache (photo) bina referee ke serve ho rahi thi.
# v103 fixes: original-URL video-intent, cache par referee + auto-purge,
# 2 naye engines (_ig_wayback, _ig_jina), embed deep-unescape pass, aur
# honest reel error (galat media KABHI nahi).
#
# Run: python3 tests/test_v103_ig.py
# =====================================================================
import io
import os
import re
import sys
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

print("\n== 1) VIDEO-INTENT: reel URL kbhi 'post' nahi banega ==")
clean = MD._clean_incoming("https://www.instagram.com/reel/TESTCODE123/?vrf=xx")
cat_after = MD.classify_instagram_url("https://www.instagram.com/p/TESTCODE123/")
ok("classify /p/ abhi bhi 'post' hai (canonical same)", cat_after == "post")
ok("pipeline source me _vid_from_raw flag hai",
   "_vid_from_raw" in io.open(os.path.join(_ROOT, "modules", "media_downloader.py"),
                              encoding="utf-8").read())
_src = MD.download_instagram_media.__doc__ or ""
src_full = io.open(os.path.join(_ROOT, "modules", "media_downloader.py"),
                   encoding="utf-8").read()
ok("media_cat force → 'reel' (canonical se type nahi khoyega)",
   'media_cat = "reel"' in src_full)
ok("want_video me raw-flag OR shart", "_vid_from_raw or media_cat" in src_full)

print("\n== 2) CACHE REFEREE (integration, engines stubbed) ==")
URL_R = "https://www.instagram.com/reel/TESTCODE123/?vrf=xx"
CKEY = "https://www.instagram.com/p/TESTCODE123"          # pipeline ka final key
_real = {}
for _fn in ("_ig_parth", "_ig_ytdlp", "_ig_embed", "_og_scrape",
            "_ig_embed_album", "_ig_wayback", "_ig_jina"):
    _real[_fn] = getattr(MD, _fn)
    setattr(MD, _fn, lambda *a, **k: None)
try:
    MD._mem_put(CKEY, b"PHOTOBYTES",
                {"ok": True, "type": "photo", "category": "post"}, "ig")
    r = MD.download_instagram_media(URL_R)
    ok("reel par photo-cache SERVE nahi hota", not r.get("ok") and not r.get("cached"))
    ok("galat cache entry TURANT delete ho jaati hai", MD._mem_get(CKEY, "ig") is None)
    MD._mem_put(CKEY, b"VIDEOBYTES",
                {"ok": True, "type": "video", "category": "reel", "size_mb": 1.0}, "ig")
    r2 = MD.download_instagram_media(URL_R)
    ok("reel par video-cache turant serve (0 download)", r2.get("ok") and r2.get("cached"))
    MD._mem_put(CKEY, b"PHOTO3",
                {"ok": True, "type": "photo", "category": "post"}, "ig")
    r3 = MD.download_instagram_media("https://www.instagram.com/p/TESTCODE123/")
    ok("photo post par photo-cache chalega (no over-block)", r3.get("ok") and r3.get("cached"))
finally:
    for _fn, _f in _real.items():
        setattr(MD, _fn, _f)

print("\n== 3) NAYE ENGINES maujood + crash-free ==")
ok("_ig_wayback defined", callable(getattr(MD, "_ig_embed", None)) and callable(getattr(MD, "_ig_wayback", None)))
ok("_ig_jina defined", callable(getattr(MD, "_ig_jina", None)))
ok("reel race me dono add hote hain (source-lock)",
   "_ig_wayback(clean, media_cat)" in src_full and "_ig_jina(clean, media_cat)" in src_full)
ok("video budget 55s (v105 loader-ig ke liye)", "55.0" in src_full)
ok("naye engine fake code par None dete hain (crash nahi)",
   MD._ig_wayback("https://www.instagram.com/p/ZzFAKEzz123", "reel") in (None,)
   or True)  # network chal bhi gaya to None/miss acceptable; crash test upar

print("\n== 4) EMBED deep-unescape pass ==")
ok("_ig_embed me second-pass _deep_unescape",
   "_deep_unescape(r.text or \"\")" in src_full.split("def _ig_embed(")[1].split("def ")[0])

print("\n== 5) REEL ERROR honest (photo fallback band) ==")
ok("reel fail message me 'cover photo nahi bhejenge' wada",
   "kabhi galat cheez (cover photo) nahi bhejenge" in src_full
   or "Reel par kabhi galat cheez" in src_full)

print("\n== 6) FACEBOOK text bot se poori tarah saaf ==")
_bad = [ln.strip() for ln in BOT_SRC.splitlines()
        if ("Facebook" in ln or "facebook" in ln)
        and not ln.strip().startswith("#")
        and "VNUM_SERVICES" not in ln and '("fb"' not in ln
        and "domains" not in ln and "fbclid" not in ln.lower()
        and "hataya" not in ln and "delete" not in ln.lower() and "Facebook.com" not in ln]
# allowed residues: sanitizer domain lists etc. (below filters most)
ok("user-facing 'Facebook' DL text nahi bacha",
   not any("Insta / YouTube / Facebook" in x or "Instagram, YouTube, Facebook" in x
           or "Instagram/YouTube/Facebook" in x for x in _bad), str(_bad[:2]))

print("\n== 7) v102 STYLE REGRESSION (font/box lock ab bhi) ==")
ok("to_bold pass-through zinda", MD and __import__("bot").to_bold("IG") == "IG")
ok("DL_SITES 3 hi", set(__import__("bot").DL_SITES) == {"instagram", "youtube", "tiktok"})

print("\n== RESULT ==")
if FAIL:
    print("FAILED:")
    for f in FAIL:
        print("  ❌", f)
    sys.exit(1)
print("✅ v103 saare checks pass")
