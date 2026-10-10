#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v95 SELFTEST — 📸 IG-CAROUSEL-FIX (poori carousel wapas)
========================================================
  A. DEEP-UNESCAPE — triple-escaped embed JSON khulta hai.
  B. ALBUM-CANDIDATES (naya display_resources format) — max-width src,
     sidecar-window (related-post junk bahar), order + dedupe.
  C. PURANA FORMAT — display_url / image_versions2 / <img> ab bhi chalte.
  D. YTDLP PHOTO RESCUE — photo entry direct CDN (No-video-formats fix).
  E. CAPTION ENTITY FIX — &quot;/&amp; saaf, double-escape nahi.
  F. REGRESSION — version v95 + history, prompts 43 intact, junk-safe.

Chalane ka tarika:
    python3 tests/test_v95_igcarousel.py
"""
import html as _html
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v95_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("PREMIUM_ONLY", "off")
os.environ.setdefault("ALL_FREE", "1")
for _k in ("FORCE_CHANNEL", "FORCE_CHANNEL_LINK", "WEBHOOK_URL"):
    os.environ.pop(_k, None)

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name} {extra if not cond and extra else ''}")


import bot as B  # noqa: E402
from modules import media_downloader as MD  # noqa: E402

BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
MD_SRC = open(os.path.join(ROOT, "modules", "media_downloader.py"), encoding="utf-8").read()

print("\n[A] Deep-unescape (triple-escaped JSON)")
_bs = chr(92)
ok("helpers maujood", all(hasattr(MD, _f) for _f in
   ("_deep_unescape", "_ig_album_candidates", "_ytdlp_direct_image_bytes",
    "_ig_embed_album", "_jpeg_fit")))
ok("3x-escaped khulta hai",
   MD._deep_unescape("X" + _bs * 3 + '"Y' + _bs + "/Z" + _bs + "u0026W") == 'X"Y/Z&W')
ok("2x-escaped khulta hai",
   MD._deep_unescape('a' + _bs + '"b' + _bs + _bs + '/c') == 'a"b/c')
ok("saaf text waisa hi", MD._deep_unescape("plain https://a/b.jpg") == "plain https://a/b.jpg")
ok("junk-safe (None/int/list)",
   MD._deep_unescape(None) == "" and MD._deep_unescape(12345) == ""
   and MD._deep_unescape(["x"]) == "")

print("\n[B] Album candidates — NAYA display_resources format")
# fixture: owner profile block (window se PEHLE = bahar) + sidecar 4 nodes
# (3 asli + 1 tiny-thumb) + related block (window ke 100KB BAAD = bahar)
_FX = (
    "<html><head><title>x</title></head><body>" + "h" * 600
    + '{\\"display_resources\\":[{\\"src\\":\\"https:\\/\\/scontent-a.cdninstagram.com\\/prof_1_n.jpg\\",'
      '\\"config_width\\":150,\\"config_height\\":150}]}'          # profile (bahar)
    + '\\"edge_sidecar_to_children\\":{\\"edges\\":['
    + '{\\"node\\":{\\"display_resources\\":['
      '{\\"src\\":\\"https:\\/\\/scontent-a.cdninstagram.com\\/v\\/t51\\/p1_100_n.jpg?big\\",\\"config_width\\":1080,\\"config_height\\":1350},'
      '{\\"src\\":\\"https:\\/\\/scontent-a.cdninstagram.com\\/v\\/t51\\/p1_100_n.jpg?small\\",\\"config_width\\":640,\\"config_height\\":800}]}},'
    + '{\\"node\\":{\\"display_resources\\":['
      '{\\"src\\":\\"https:\\/\\/scontent-a.cdninstagram.com\\/v\\/t51\\/p2_200_n.jpg?big\\",\\"config_width\\":1080,\\"config_height\\":1080},'
      '{\\"src\\":\\"https:\\/\\/scontent-a.cdninstagram.com\\/v\\/t51\\/p2_200_n.jpg?small\\",\\"config_width\\":320,\\"config_height\\":320}]}},'
    + '{\\"node\\":{\\"display_resources\\":['
      '{\\"src\\":\\"https:\\/\\/scontent-a.cdninstagram.com\\/v\\/t51\\/p3_300_n.jpg?mid\\",\\"config_width\\":750,\\"config_height\\":1334}]}},'
    + '{\\"node\\":{\\"display_resources\\":['
      '{\\"src\\":\\"https:\\/\\/scontent-a.cdninstagram.com\\/v\\/t51\\/tiny_1_n.jpg?t\\",\\"config_width\\":150,\\"config_height\\":150}]}}'
    + "]}"
    + "z" * 100005
    + '{\\"display_resources\\":[{\\"src\\":\\"https:\\/\\/scontent-a.cdninstagram.com\\/v\\/t51\\/other_9_n.jpg?r\\",'
      '\\"config_width\\":1080,\\"config_height\\":1080}]}'        # related (bahar)
)
_c = MD._ig_album_candidates(_FX)
ok("3 asli photos (tiny/profile/related bahar)", len(_c) == 3, f"mile={len(_c)}")
ok("har photo ka SABSE BADA size", all("?big" in _u or "?mid" in _u for _u in _c), str(_c)[:120])
ok("carousel order barkarar",
   [re.sub(r"[?#].*$", "", _u.rsplit("/", 1)[-1]) for _u in _c]
   == ["p1_100_n.jpg", "p2_200_n.jpg", "p3_300_n.jpg"], str(_c)[:150])
ok("junk-safe (None/int/short)", MD._ig_album_candidates(None) == []
   and MD._ig_album_candidates(123) == [] and MD._ig_album_candidates("short") == [])

print("\n[C] Purana format ab bhi chalta hai")
_FX_OLD = ("<html>" + "q" * 500
           + '"display_url":"https://scontent-b.cdninstagram.com/v/o1_n.jpg?x=1"'
           + '"display_url":"https://scontent-b.cdninstagram.com/v/o2_n.jpg?x=2"')
ok("display_url x2", len(MD._ig_album_candidates(_FX_OLD)) == 2)
_FX_IV2 = ("<html>" + "q" * 500
           + '"url":"https://scontent-c.cdninstagram.com/v/iv1_n.jpg?y=1"'
           + '"url":"https://scontent-c.cdninstagram.com/v/iv2_n.png?y=2"')
ok("image_versions2 (fixed pattern, backslash nahi)", len(MD._ig_album_candidates(_FX_IV2)) == 2)
_FX_IMG = '<html>' + "q" * 500 + '<img src="https://scontent-d.cdninstagram.com/v/cover_n.jpg?w=1">'
ok("<img> cover", MD._ig_album_candidates(_FX_IMG) == ["https://scontent-d.cdninstagram.com/v/cover_n.jpg?w=1"])
ok("profile/150x150 filter",
   MD._ig_album_candidates("<html>" + "q" * 500
                           + '"display_url":"https://scontent-e.cdninstagram.com/profile_pic_1.jpg"'
                           + '"display_url":"https://scontent-e.cdninstagram.com/a150x150_b.jpg"') == [])

print("\n[D] yt-dlp photo rescue (direct CDN)")


class _FakeResp:
    def __init__(self, code, body):
        self.status_code = code
        self.content = body
        self.headers = {"content-type": "image/jpeg"}
    def iter_content(self, chunk_size):
        yield self.content
    def close(self):
        pass


_real_get = MD.httpio.get
try:
    MD.httpio.get = lambda *a, **k: _FakeResp(200, b"z" * 5000)
    ok("info['url'] se bytes", MD._ytdlp_direct_image_bytes({"url": "http://x/y.jpg"}) == b"z" * 5000)
    ok("formats fallback", MD._ytdlp_direct_image_bytes(
        {"formats": [{"url": ""}, {"url": "http://x/v.mp4"}]}) == b"z" * 5000)
    ok("thumbnails fallback", MD._ytdlp_direct_image_bytes(
        {"thumbnails": [{"url": "http://x/t.jpg"}]}) == b"z" * 5000)
    ok("None/garbage → None", MD._ytdlp_direct_image_bytes(None) is None
       and MD._ytdlp_direct_image_bytes("xx") is None
       and MD._ytdlp_direct_image_bytes({}) is None
       and MD._ytdlp_direct_image_bytes({"url": "notaurl"}) is None)
    MD.httpio.get = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("net down"))
    ok("network fail → None (crash nahi)",
       MD._ytdlp_direct_image_bytes({"url": "http://x/y.jpg"}) is None)
finally:
    MD.httpio.get = _real_get

ok("v86 video literal barkarar", "_ytdlp_download_bytes(u, max_mb=15)" in MD_SRC)
ok("carousel photo branch direct-CDN", "_ytdlp_direct_image_bytes(e)" in MD_SRC)
ok("single rescue branch", "_ytdlp_direct_image_bytes(info)" in MD_SRC)
ok("embed-album FB_UA pehle", "for _ua in (FB_UA, DESKTOP_UA)" in MD_SRC)

print("\n[E] Caption entity fix (&quot;)")
_dirty = "Sanjana kurmi on Instagram: &quot;Virushka&quot; &amp; Tabaahi"
_clean = _html.unescape(_html.unescape(_dirty))
ok("double-unescape saaf karta hai",
   "&quot;" not in _clean and "&amp;" not in _clean and '"Virushka"' in _clean)
ok("bot.py title line fixed",
   'title = html.unescape(html.unescape(str(res.get("title") or "")))[:60]' in BOT_SRC)
ok("usage par single hesc (double-escape nahi)",
   BOT_SRC.count("hesc(str(title))") >= 2)
ok("import html maujood", "\nimport html" in BOT_SRC)

print("\n[F] Regression — version + prompts + engine wiring")
_vm = re.match(r"v(\d+)", B.BOT_VERSION)
ok("version v85+ (v95) + poori history",
   bool(_vm) and int(_vm.group(1)) >= 85 and "v95.0" in B.BOT_VERSION
   and "v94.0" in B.BOT_VERSION and "v93.0" in B.BOT_VERSION
   and "v86.0" in B.BOT_VERSION and "v85.0" in B.BOT_VERSION
   and "v84.0" in B.BOT_VERSION and "v83.0" in B.BOT_VERSION
   and "v77" in B.BOT_VERSION and "FREE4ALL" in B.BOT_VERSION, B.BOT_VERSION[:16])
ok("PROMPT_DATA 34 (v102: 3 tools ke prompt gaye)", len(B.PROMPT_DATA) == 34,
   f"count={len(B.PROMPT_DATA)}")
ok("race me album engine + retry barkarar",
   "_ig_embed_album(clean, media_cat)" in MD_SRC and "embed-album" in MD_SRC)
ok("c-code ke bina album None (network nahi)",
   MD._ig_embed_album("not a url", "post") is None
   and MD._ig_embed_album("", "post") is None)
ok("kind referee intact",
   MD._ig_kind_ok({"ok": True, "type": "photo"}, True) is False
   and MD._ig_kind_ok({"ok": True, "type": "carousel"}, False) is True)

print(f"\nv95 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
if FAIL:
    print("FAILED:")
    for _f in FAIL:
        print(f"  ❌ {_f}")
    sys.exit(1)
