#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v96 SELFTEST — 🎵 TikTok + 📘 Facebook FIX
==========================================
  A. TIKWM ENGINE — video (hdplay/play/wmplay), photo slideshow → carousel,
     API fail/junk → None (yt-dlp fallback ke liye).
  B. FB-NATIVE ENGINE — browser_native_hd/sd_url → mp4, title unescape.
  C. CAPPED GET — size cap + content-type guard (HTML kabhi media nahi).
  D. HUB GUARD + COOKIES CHAIN — savenow HTML reject, YT cookies wiring intact.
  E. REGRESSION — version v96 + history, prompts 43, caps 6/12 intact.

Sab fixture-based (network nahi). Chalane ka tarika:
    python3 tests/test_v96_socialfix.py
"""
import io as _io
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v96_")
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


class _FakeResp:
    def __init__(self, code=200, body=b"", ctype="video/mp4", json_data=None, text=""):
        self.status_code = code
        self.content = body
        self.headers = {"content-type": ctype}
        self._j = json_data
        self.text = text

    def json(self):
        if self._j is None:
            raise ValueError("no json")
        return self._j

    def iter_content(self, n):
        b = self.content or b""
        for i in range(0, len(b), n):
            yield b[i:i + n]

    def close(self):
        pass


def _mkjpeg(color):
    from PIL import Image as _PIL
    im = _PIL.new("RGB", (400, 400), color)
    bf = _io.BytesIO()
    im.save(bf, format="JPEG")
    return bf.getvalue()


_J1, _J2 = _mkjpeg((255, 0, 0)), _mkjpeg((0, 0, 255))
_MP4 = b"V" * 5000

print("\n[A] TikTok tikwm engine")
_real_get = MD.httpio.get


def _tt_video(url, **kw):
    if "tikwm.com/api" in url:
        return _FakeResp(200, b"{}", "application/json",
                          {"code": 0, "msg": "success",
                           "data": {"title": "FX video", "duration": 12,
                                   "play": "http://cdn/tt_play.mp4",
                                   "wmplay": "http://cdn/tt_wm.mp4"}})
    if url.startswith("http://cdn/"):
        return _FakeResp(200, _MP4, "video/mp4")
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _tt_video
    _r = MD._tt_tikwm("https://www.tiktok.com/@x/video/123", 48)
    ok("video milta hai (tikwm)", bool(_r and _r.get("ok") and _r.get("type") == "video")
       and _r.get("engine") == "tikwm" and _r.get("title") == "FX video"
       and _r.get("duration") == 12, str((_r or {}).get("engine")))
    ok("no-watermark quality tag", (_r or {}).get("quality") == "no-watermark")
finally:
    MD.httpio.get = _real_get


def _tt_photo(url, **kw):
    if "tikwm.com/api" in url:
        return _FakeResp(200, b"{}", "application/json",
                          {"code": 0,
                           "data": {"title": "FX slide",
                                   "images": ["http://cdn/s1.jpg", "http://cdn/s2.jpg"]}})
    if url == "http://cdn/s1.jpg":
        return _FakeResp(200, _J1, "image/jpeg")
    if url == "http://cdn/s2.jpg":
        return _FakeResp(200, _J2, "image/jpeg")
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _tt_photo
    _rp = MD._tt_tikwm("https://www.tiktok.com/@x/photo/456", 48)
    ok("slideshow → carousel (2 photos)", bool(_rp and _rp.get("type") == "carousel")
       and len((_rp or {}).get("items") or []) == 2
       and (_rp or {}).get("engine") == "tikwm-photo")
finally:
    MD.httpio.get = _real_get


def _tt_fail(url, **kw):
    if "tikwm.com/api" in url:
        return _FakeResp(200, b"{}", "application/json", {"code": -1, "msg": "bad"})
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _tt_fail
    ok("API error → None (fallback)", MD._tt_tikwm("https://www.tiktok.com/@x/video/1", 48) is None)
finally:
    MD.httpio.get = _real_get

ok("non-tiktok/junk → None", MD._tt_tikwm("https://youtube.com/watch?v=x", 48) is None
   and MD._tt_tikwm("", 48) is None and MD._tt_tikwm(None, 48) is None
   and MD._tt_tikwm(12345, 48) is None)

print("\n[B] FB native engine")
_FB_HTML = ("<html><head>"
            '<meta property="og:title" content="How to share &quot;Things&quot;">'
            "</head><body>" + "f" * 6000
            + '"browser_native_hd_url":"http://cdn/fb_hd.mp4",'
            + '"browser_native_sd_url":"http://cdn/fb_sd.mp4"'
            + "</body></html>")


def _fb_ok(url, **kw):
    if "facebook.com" in url:
        return _FakeResp(200, _FB_HTML.encode(), "text/html", None, _FB_HTML)
    if url.startswith("http://cdn/"):
        return _FakeResp(200, _MP4, "video/mp4")
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _fb_ok
    _f = MD._fb_native("https://www.facebook.com/watch/?v=123456789012345", 48)
    ok("FB video milta hai (fb-native)", bool(_f and _f.get("ok") and _f.get("type") == "video")
       and _f.get("engine") == "fb-native")
    ok("title entity saaf", "&quot;" not in ((_f or {}).get("title") or "x")
       and '"Things"' in ((_f or {}).get("title") or ""), ((_f or {}).get("title") or "")[:50])
finally:
    MD.httpio.get = _real_get


def _fb_none(url, **kw):
    return _FakeResp(200, ("<html>" + "n" * 6000 + "</html>").encode(), "text/html",
                     None, "<html>" + "n" * 6000 + "</html>")


try:
    MD.httpio.get = _fb_none
    ok("native URL nahi → None", MD._fb_native("https://www.facebook.com/watch/?v=1", 48) is None)
finally:
    MD.httpio.get = _real_get

ok("non-fb/short/junk → None", MD._fb_native("https://youtube.com/x", 48) is None
   and MD._fb_native("short", 48) is None and MD._fb_native(None, 48) is None
   and MD._fb_native(999, 48) is None)

print("\n[C] Capped GET (size + ctype guard)")
try:
    MD.httpio.get = lambda url, **kw: _FakeResp(200, b"<html>captcha</html>" * 500, "text/html; charset=utf8")
    ok("HTML kabhi media nahi", MD._http_get_capped("http://cdn/x.mp4", 48) is None)
    MD.httpio.get = lambda url, **kw: _FakeResp(200, b"V" * 3000, "video/mp4")
    ok("chhota video OK", MD._http_get_capped("http://cdn/x.mp4", 48) == b"V" * 3000)
    MD.httpio.get = lambda url, **kw: _FakeResp(200, b"V" * 2000, "video/mp4")
    ok("cap se bada → None", MD._http_get_capped("http://cdn/x.mp4", 0.001) is None)
    MD.httpio.get = lambda url, **kw: _FakeResp(404, b"", "text/plain")
    ok("404 → None", MD._http_get_capped("http://cdn/x.mp4", 48) is None)
    MD.httpio.get = lambda url, **kw: _FakeResp(200, b"tiny", "video/mp4")
    ok("tiny (<1000B) → None", MD._http_get_capped("http://cdn/x.mp4", 48) is None)
    ok("ganda URL → None", MD._http_get_capped("notaurl", 48) is None
       and MD._http_get_capped("", 48) is None and MD._http_get_capped(None, 48) is None)
finally:
    MD.httpio.get = _real_get

print("\n[D] Hub guard + cookies chain + wiring")
_hub_i = MD_SRC.find("def _hub_youtube_download")
_hub_body = MD_SRC[_hub_i:MD_SRC.find("\ndef ", _hub_i + 10)]
ok("hub me HTML guard", '"text/html" in _ct96' in _hub_body and "v96: loader backend" in _hub_body)
ok("chain me tiktok branch", '_tt_tikwm(url, max_mb)' in MD_SRC
   and '"tiktok.com" in url.lower()' in MD_SRC)
ok("chain me facebook branch", '_fb_native(url, max_mb)' in MD_SRC
   and '"fb.watch" in _lu96' in MD_SRC)
ok("hub caps 6/12 intact (v68)", "_call_capped(_hub_youtube_download, 6" in MD_SRC
   and "_call_capped(_hub_youtube_download, 12" in MD_SRC)
ok("cookies boot-restore wired", BOT_SRC.count("cookies_boot_restore()") >= 2)
ok("cookies save→DB meta", 'meta_set("yt_cookies"' in BOT_SRC)
ok("yt-dlp cookiefile use", 'opts["cookiefile"] = cf' in MD_SRC)
ok("/cookies command maujood", "COOKIES LAG GAYIN" in BOT_SRC and "COOKIES STATUS" in BOT_SRC)

print("\n[E] Regression — version + prompts")
_vm = re.match(r"v(\d+)", B.BOT_VERSION)
ok("version v85+ (v96) + poori history",
   bool(_vm) and int(_vm.group(1)) >= 85 and "v96.0" in B.BOT_VERSION
   and "v95.0" in B.BOT_VERSION and "v94.0" in B.BOT_VERSION
   and "v93.0" in B.BOT_VERSION and "v86.0" in B.BOT_VERSION
   and "v85.0" in B.BOT_VERSION and "v84.0" in B.BOT_VERSION
   and "v83.0" in B.BOT_VERSION and "v77" in B.BOT_VERSION
   and "FREE4ALL" in B.BOT_VERSION, B.BOT_VERSION[:16])
ok("PROMPT_DATA 44 (43 purane intact + familyinfo)", len(B.PROMPT_DATA) == 44,
   f"count={len(B.PROMPT_DATA)}")

print(f"\nv96 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
if FAIL:
    print("FAILED:")
    for _f in FAIL:
        print(f"  ❌ {_f}")
    sys.exit(1)
