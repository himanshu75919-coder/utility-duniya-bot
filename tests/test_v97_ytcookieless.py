#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v97 SELFTEST — ⬇️ YOUTUBE COOKIELESS (loader.to) + TikTok photo win
====================================================================
  A. LKEY/HEIGHT — video-id nikalna + format mapping (junk-safe).
  B. LOADER JOB — start/poll/run (fake network, asli flow).
  C. PREWARM + PICKUP — background job → cache → turant video.
  D. TIKTOK IMAGES-WIN — play+images ho to carousel (slideshow nahi).
  E. REGRESSION — wiring, version v97 + history, prompts 43.

Fixture-based (network nahi; chhote asli sleeps ~25s). Chalane ka tarika:
    python3 tests/test_v97_ytcookieless.py
"""
import os
import re
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v97_")
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
    def __init__(self, code=200, body=b"", ctype="video/mp4", json_data=None):
        self.status_code = code
        self.content = body
        self.headers = {"content-type": ctype}
        self._j = json_data

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


_MP4 = b"V" * 5000
_real_get = MD.httpio.get

print("\n[A] lkey + height")
ok("watch/shorts/youtu.be/embed/live/music → id",
   MD._lkey("https://www.youtube.com/watch?v=AXME_z0Dmvg") == "AXME_z0Dmvg"
   and MD._lkey("https://youtu.be/AXME_z0Dmvg?t=3") == "AXME_z0Dmvg"
   and MD._lkey("https://www.youtube.com/shorts/AXME_z0Dmvg") == "AXME_z0Dmvg"
   and MD._lkey("https://www.youtube.com/embed/AXME_z0Dmvg") == "AXME_z0Dmvg"
   and MD._lkey("https://www.youtube.com/live/AXME_z0Dmvg") == "AXME_z0Dmvg"
   and MD._lkey("https://music.youtube.com/watch?v=AXME_z0Dmvg") == "AXME_z0Dmvg")
ok("non-YT/junk → empty", MD._lkey("https://tiktok.com/@x/video/1") == ""
   and MD._lkey("") == "" and MD._lkey(None) == "" and MD._lkey(123) == "")
ok("height mapping", MD._loader_height(1080) == 1080 and MD._loader_height(900) == 720
   and MD._loader_height(720) == 720 and MD._loader_height(480) == 480
   and MD._loader_height(360) == 360 and MD._loader_height(0) == 360
   and MD._loader_height("xx") == 360 and MD._loader_height(None) == 360)

print("\n[B] Loader job flow (fake network)")
_calls = []


def _job_ok(url, **kw):
    _calls.append(url)
    if "loader.to/ajax/download.php" in url:
        return _FakeResp(200, b"{}", "application/json",
                          {"success": True, "progress_url": "http://p/prog"})
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _job_ok
    ok("start → progress_url",
       MD._loader_start("https://www.youtube.com/watch?v=VIDJOB01", 360) == "http://p/prog")
    _n0 = len(_calls)
    ok("non-YT start → None (network nahi)", MD._loader_start("https://x.com/y", 360) is None
       and len(_calls) == _n0)
finally:
    MD.httpio.get = _real_get


def _job_404(url, **kw):
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _job_404
    ok("start 404 → None", MD._loader_start("https://www.youtube.com/watch?v=VIDJOB02", 360) is None)
finally:
    MD.httpio.get = _real_get

try:
    MD.httpio.get = lambda url, **kw: _FakeResp(
        200, b"{}", "application/json",
        {"success": 1, "download_url": "http://cdn/v.mp4", "title": "FX", "format": "360"})
    _d, _dl, _t, _f = MD._loader_poll_once("http://p/prog")
    ok("poll done", _d is True and _dl == "http://cdn/v.mp4" and _t == "FX" and _f == "360")
    MD.httpio.get = lambda url, **kw: _FakeResp(
        200, b"{}", "application/json", {"success": 0, "progress": 50})
    _d2, _dl2, _t2, _f2 = MD._loader_poll_once("http://p/prog")
    ok("poll progress (done nahi)", _d2 is False and _dl2 == "")
finally:
    MD.httpio.get = _real_get


def _run_seq(url, **kw):
    if "loader.to/ajax" in url:
        return _FakeResp(200, b"{}", "application/json",
                          {"success": True, "progress_url": "http://p/s"})
    _run_seq.n += 1
    if _run_seq.n >= 2:
        return _FakeResp(200, b"{}", "application/json",
                          {"success": 1, "download_url": "http://cdn/seq.mp4",
                           "title": "SEQ", "format": "mp4 [720p]"})
    return _FakeResp(200, b"{}", "application/json", {"success": 0, "progress": 50})


_run_seq.n = 0
try:
    MD.httpio.get = _run_seq
    _dl3, _t3, _f3 = MD._loader_run("https://www.youtube.com/watch?v=VIDRUN01", 720, 25)
    ok("run: progress → done", _dl3 == "http://cdn/seq.mp4" and _t3 == "SEQ"
       and _f3 == "mp4 [720p]")
finally:
    MD.httpio.get = _real_get


def _run_hang(url, **kw):
    if "loader.to/ajax" in url:
        return _FakeResp(200, b"{}", "application/json",
                          {"success": True, "progress_url": "http://p/h"})
    return _FakeResp(200, b"{}", "application/json", {"success": 0, "progress": 50})


try:
    MD.httpio.get = _run_hang
    _t0 = time.time()
    _dl4, _t4, _f4 = MD._loader_run("https://www.youtube.com/watch?v=VIDRUN02", 360, 7)
    _el = time.time() - _t0
    ok("run timeout → None (latka nahi)", _dl4 is None and 5 <= _el <= 20, f"{_el:.0f}s")
finally:
    MD.httpio.get = _real_get

print("\n[C] Prewarm + pickup")
_MD_JOBS = MD._LOADER_JOBS


def _pw_seq(url, **kw):
    if "loader.to/ajax" in url:
        return _FakeResp(200, b"{}", "application/json",
                          {"success": True, "progress_url": "http://p/w"})
    if url == "http://p/w":
        return _FakeResp(200, b"{}", "application/json",
                          {"success": 1, "download_url": "http://cdn/warm.mp4",
                           "title": "WARM", "format": "360"})
    if url == "http://cdn/warm.mp4":
        return _FakeResp(200, _MP4, "video/mp4")
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _pw_seq
    _VID = "VIDWARM01"
    _U = f"https://www.youtube.com/watch?v={_VID}"
    ok("prewarm True (non-blocking)", MD.yt_loader_prewarm(_U, 360) is True)
    ok("prewarm junk → False", MD.yt_loader_prewarm("notaurl") is False
       and MD.yt_loader_prewarm("") is False)
    _st = None
    for _ in range(14):
        time.sleep(1)
        _st = _MD_JOBS.get((_VID, 360))
        if _st and _st[0] == "done":
            break
    ok("background job done hota hai", bool(_st and _st[0] == "done" and _st[1] == "http://cdn/warm.mp4"))
    _r = MD._yt_loader(_U, 360, wait=10, max_mb=48)
    ok("pickup → video (loader.to)", bool(_r and _r.get("ok")) and _r.get("engine") == "loader.to"
       and _r.get("title") == "WARM" and _r.get("quality") == "144p", str((_r or {}).get("quality")))  # v98: ladder-sach ("360"->144p ffprobe-verified)
    _MD_JOBS.pop((_VID, 360), None)
finally:
    MD.httpio.get = _real_get

# expired cache → inline run (job endpoint hit hona chahiye)
_calls2 = []


def _exp_seq(url, **kw):
    _calls2.append(url)
    if "loader.to/ajax" in url:
        return _FakeResp(200, b"{}", "application/json",
                          {"success": True, "progress_url": "http://p/e"})
    if url == "http://p/e":
        return _FakeResp(200, b"{}", "application/json",
                          {"success": 1, "download_url": "http://cdn/exp.mp4",
                           "title": "EXP", "format": "720"})
    if url == "http://cdn/exp.mp4":
        return _FakeResp(200, _MP4, "video/mp4")
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _exp_seq
    _VID2 = "VIDEXP001"
    _U2 = f"https://www.youtube.com/watch?v={_VID2}"
    _MD_JOBS[(_VID2, 360)] = ("done", "http://cdn/old.mp4", time.time() - 2000, "OLD", "360")
    _r2 = MD._yt_loader(_U2, 360, wait=20, max_mb=48)
    ok("expired cache → naya inline job", bool(_r2 and _r2.get("title") == "EXP")
       and any("loader.to/ajax" in c for c in _calls2))
    _MD_JOBS.pop((_VID2, 360), None)
finally:
    MD.httpio.get = _real_get

ok("loader junk-URL → None", MD._yt_loader("https://fb.com/x", 360) is None
   and MD._yt_loader("", 360) is None and MD._yt_loader(None) is None)

print("\n[D] TikTok images-win (photo-post = photos)")
from PIL import Image as _PIL  # noqa: E402


def _mkjpeg(color):
    im = _PIL.new("RGB", (400, 400), color)
    bf = __import__("io").BytesIO()
    im.save(bf, format="JPEG")
    return bf.getvalue()


_J1, _J2 = _mkjpeg((1, 2, 3)), _mkjpeg((9, 8, 7))


def _tt_both(url, **kw):
    if "tikwm.com/api" in url:
        return _FakeResp(200, b"{}", "application/json",
                          {"code": 0, "data": {"title": "FXP",
                                              "play": "http://cdn/slide.mp4",
                                              "images": ["http://cdn/p1.jpg", "http://cdn/p2.jpg"]}})
    if url == "http://cdn/p1.jpg":
        return _FakeResp(200, _J1, "image/jpeg")
    if url == "http://cdn/p2.jpg":
        return _FakeResp(200, _J2, "image/jpeg")
    return _FakeResp(404, b"", "text/plain")


try:
    MD.httpio.get = _tt_both
    _rp = MD._tt_tikwm("https://www.tiktok.com/@x/photo/789", 48)
    ok("play+images → carousel (IG jaisa)", bool(_rp and _rp.get("type") == "carousel")
       and len((_rp or {}).get("items") or []) == 2
       and (_rp or {}).get("engine") == "tikwm-photo", str((_rp or {}).get("type")))
finally:
    MD.httpio.get = _real_get

print("\n[E] Regression — wiring + version + prompts")
ok("quality-pipe me loader (1080 + 720)", "_yt_loader(url, 1080" in MD_SRC
   and "_yt_loader(url, 720" in MD_SRC)
ok("direct-chain me loader", "_lres = _yt_loader(url, 720, wait=30" in MD_SRC)
ok("picker par prewarm hook", "MD.yt_loader_prewarm(raw_text, 1080)" in BOT_SRC)  # v98: 1080-master
ok("hub caps 6/12 intact", "_call_capped(_hub_youtube_download, 6" in MD_SRC
   and "_call_capped(_hub_youtube_download, 12" in MD_SRC)
_vm = re.match(r"v(\d+)", B.BOT_VERSION)
ok("version v85+ (v97) + poori history",
   bool(_vm) and int(_vm.group(1)) >= 85 and "v97.0" in B.BOT_VERSION
   and "v96.0" in B.BOT_VERSION and "v95.0" in B.BOT_VERSION
   and "v94.0" in B.BOT_VERSION and "v93.0" in B.BOT_VERSION
   and "v86.0" in B.BOT_VERSION and "v85.0" in B.BOT_VERSION
   and "v84.0" in B.BOT_VERSION and "v83.0" in B.BOT_VERSION
   and "v77" in B.BOT_VERSION and "FREE4ALL" in B.BOT_VERSION, B.BOT_VERSION[:16])
ok("PROMPT_DATA 43 (koi prompt change nahi)", len(B.PROMPT_DATA) == 43,
   f"count={len(B.PROMPT_DATA)}")

print(f"\nv97 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
if FAIL:
    print("FAILED:")
    for _f in FAIL:
        print(f"  ❌ {_f}")
    sys.exit(1)
