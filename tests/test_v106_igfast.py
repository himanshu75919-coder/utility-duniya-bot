# -*- coding: utf-8 -*-
"""v106 — IG FAST ENGINE offline tests (network nahi chahiye)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAIL = 0


def check(name, cond):
    global FAIL
    if cond:
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


from modules import ig_fast as IF  # noqa: E402

print("=" * 62)
print("1) URL PARSING — saare link types")
print("=" * 62)
cases = [
    ("https://www.instagram.com/reel/C8xYzAbCdEf/?igsh=abc", "reel", "code", "C8xYzAbCdEf"),
    ("https://www.instagram.com/reels/C8xYzAbCdEf/", "reel", "code", "C8xYzAbCdEf"),
    ("https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3", "post", "code", "DeJgDvDIFg2"),
    ("https://instagr.am/p/AbC123xyz45/", "post", "code", "AbC123xyz45"),
    ("https://www.instagram.com/tv/CxYz1234567/", "tv", "code", "CxYz1234567"),
    ("https://www.instagram.com/stories/someuser/3093939657949855636/", "story", "story_id", "3093939657949855636"),
    ("https://www.instagram.com/stories/someuser/", "story", "user", "someuser"),
    ("https://www.instagram.com/stories/highlight/17854360229135957/", "highlight", "story_id", "17854360229135957"),
    ("https://www.instagram.com/viralxreels/", "profile", "user", "viralxreels"),
    ("https://www.instagram.com/accounts/login/", "unknown", "user", ""),
    ("https://www.instagram.com/explore/tags/x/", "unknown", "code", ""),
    ("", "unknown", "code", ""),
]
for url, kind, field, want in cases:
    p = IF.parse_ig_url(url)
    check(f"{kind:9s} <- {url[:58] or '(empty)':58s}",
          p["kind"] == kind and str(p.get(field, "")) == str(want))

print("=" * 62)
print("2) SHORTCODE -> MEDIA ID (base64 math)")
print("=" * 62)
check("C8xYzAbCdEf -> 3400608251904643359",
      IF.shortcode_to_media_id("C8xYzAbCdEf") == "3400608251904643359")
check("khali/galad code par ''", IF.shortcode_to_media_id("") == "")
check("junk chars par ''", IF.shortcode_to_media_id("!!!") == "")
# roundtrip: known id ka shortcode wapas
_mid = "3400608251904643359"
n = int(_mid)
out = ""
ABC = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
while n:
    out = ABC[n % 64] + out
    n //= 64
check("id -> shortcode roundtrip", out == "C8xYzAbCdEf")

print("=" * 62)
print("3) CRASH-PROOF — junk input par kabhi exception nahi")
print("=" * 62)
for junk in (None, "", 12345, ["list"], {"a": 1}, b"bytes", "not a url at all",
             "https://example.com/p/abc"):
    try:
        r1 = IF.parse_ig_url(junk) if isinstance(junk, (str, bytes)) else IF.parse_ig_url(str(junk))
        r2 = IF.fetch_media(junk if isinstance(junk, str) else str(junk), "post")
        ok = isinstance(r1, dict) and (r2 is None or isinstance(r2, dict))
    except Exception:
        ok = False
    check(f"junk safe: {str(type(junk).__name__):5s}", ok)

print("=" * 62)
print("4) MOCK API — reel/post/carousel JSON se media extraction")
print("=" * 62)
# fake media item: reel with video_versions
FAKE_REEL = {
    "media_type": 2,
    "video_versions": [
        {"type": 101, "width": 720, "height": 1280, "url": "https://cdn.example/vid720.mp4"},
        {"type": 102, "width": 480, "height": 854, "url": "https://cdn.example/vid480.mp4"},
    ],
    "caption": {"text": "test caption"},
    "user": {"username": "tester"},
}
check("best video = highest res",
      IF._best_video_url(FAKE_REEL) == "https://cdn.example/vid720.mp4")
FAKE_PHOTO = {
    "media_type": 1,
    "image_versions2": {"candidates": [
        {"width": 640, "height": 640, "url": "https://cdn.example/p640.jpg"},
        {"width": 1080, "height": 1080, "url": "https://cdn.example/p1080.jpg"},
    ]},
}
check("best image = highest res",
      IF._best_image_url(FAKE_PHOTO) == "https://cdn.example/p1080.jpg")
check("khaali item par ''", IF._best_video_url({}) == "" and IF._best_image_url({}) == "")

print("=" * 62)
print("5) STORY FAST-FAIL — bina cookie ke turant need_login")
print("=" * 62)
os.environ.pop("IG_COOKIE", None)
os.environ.pop("YTDLP_COOKIES", None)
r = IF.fetch_story("https://www.instagram.com/stories/someuser/123456789/")
check("bina cookie -> need_login error", bool(r) and r.get("need_login") is True and not r.get("ok"))
check("error message me /cookies guide", "/cookies" in str(r.get("error", "")))

print("=" * 62)
print("6) 429 COOLDOWN — engine turant None (time waste nahi)")
print("=" * 62)
import time as _t
IF._COOL_UNTIL = _t.time() + 1.5        # 1.5 second ka test-cooldown
_t0 = _t.time()
r = IF.fetch_post("C8xYzAbCdEf", "reel")
_dt = _t.time() - _t0
check("cooldown me 0.05s se kam me None", r is None and _dt < 0.05)
check("cool_active() True", IF.cool_active())
_t.sleep(1.7)
check("cooldown ke baad False", not IF.cool_active())
check("429 par cooldown floor >= 90s", IF._cool_mark() or IF._CD >= 90)
IF._COOL_UNTIL = 0.0                    # aage ke tests ke liye reset

print("=" * 62)
print("7) MEDIA_DOWNLOADER INTEGRATION — engine race me IGF pehle hai")
print("=" * 62)
src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "modules", "media_downloader.py"), encoding="utf-8").read()
check("IGF import present", "from modules import ig_fast as IGF" in src)
check("race me IGF.fetch_media first", "IGF.fetch_media(clean, media_cat)" in src)
check("story fast-fail laga hai", "need_login" in src)
check("profile fast path laga hai", "IGF.fetch_profile_pic" in src)

print("=" * 62)
print("8) DIAGNOSTICS")
print("=" * 62)
d = IF.diagnostics()
check("diagnostics dict with keys", isinstance(d, dict) and "cooldown" in d and "cookie" in d)

print("=" * 62)
print(f"  {'PASS — sab green ✅' if FAIL == 0 else f'FAIL: {FAIL} checks'}")
print("=" * 62)
sys.exit(1 if FAIL else 0)
