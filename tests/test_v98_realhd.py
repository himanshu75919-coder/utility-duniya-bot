#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v98 SELFTEST — 🎞️ REAL-HD (loader-1080 master + ffmpeg + background tap)
============================================================================
  A. PROBE/PICK — ffprobe-parse + single-shot height (junk-safe).
  B. DISK-DL + TRANSCODE — stream-to-disk + asli ffmpeg HD (skip agar no-ffmpeg).
  C. HD PIPELINE — nakli-master reject, lambi-video fatal, junk → None.
  D. HONESTY — ladder echo me sach ("720" → 360p, ffprobe-verified).
  E. REGRESSION — wiring, version v98 + history, prompts 43.

Chalane ka tarika:  python3 tests/test_v98_realhd.py
"""
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v98_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("PREMIUM_ONLY", "off")
os.environ.setdefault("ALL_FREE", "1")
for _k in ("FORCE_CHANNEL", "FORCE_CHANNEL_LINK", "WEBHOOK_URL"):
    os.environ.pop(_k, None)

PASS, FAIL, SKIP = [], [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name} {extra if not cond and extra else ''}")


def skip(name, why):
    SKIP.append(name)
    print(f"  ⏭️ {name} ({why})")


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


_real_get = MD.httpio.get
_FF = MD._FFMPEG_LOC if MD._HAS_FFMPEG else ""


def _mk_testsrc(path, w, h, dur=1):
    cp = subprocess.run(
        [_FF, "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", f"testsrc=size={w}x{h}:rate=10:duration={dur}",
         "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast", path],
        capture_output=True, timeout=60)
    return cp.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 1000


print("\n[A] Probe + pick")
_T1 = os.path.join(_TMP, "t1.mp4")
if _FF and _mk_testsrc(_T1, 640, 360, 2):
    _d, _w, _h = MD._ff_probe(_T1)
    ok("probe asli file (640x360, ~2s)", _w == 640 and _h == 360 and 1.5 <= _d <= 2.5,
       f"dur={_d} w={_w} h={_h}")
else:
    skip("probe asli file", "no-ffmpeg")
ok("probe garbage → zeros", MD._ff_probe("/no/such/file.mp4") == (0, 0, 0)
   and MD._ff_probe("") == (0, 0, 0) and MD._ff_probe(None) == (0, 0, 0))
ok("pick: 55MB/1080 → req720=720, req1080=1080",
   MD._hd_pick(55, 1080, 720) == 720 and MD._hd_pick(55, 1080, 1080) == 1080)
ok("pick: 330MB/1080 → 480 (720 samaaye nahi)",
   MD._hd_pick(330, 1080, 720) == 480 and MD._hd_pick(330, 1080, 1080) == 480)
ok("pick: 700MB/1080 → 360 (last resort)", MD._hd_pick(700, 1080, 720) == 360)
ok("pick junk → 360", MD._hd_pick("x", 1080, 720) == 360 and MD._hd_pick(0, 1080, 720) == 360
   and MD._hd_pick(55, 0, 720) == 360 and MD._hd_pick(None, None, None) == 360)

print("\n[B] Disk-dl + transcode")


def _dl_ok(url, **kw):
    return _FakeResp(200, b"V" * 5000, "video/mp4")


try:
    MD.httpio.get = _dl_ok
    _p = os.path.join(_TMP, "d.mp4")
    ok("dl_to_path likhta hai", MD._dl_to_path("http://cdn/v.mp4", _p, 48) is True
       and os.path.getsize(_p) == 5000)
    ok("dl cap/html/junk → False",
       MD._dl_to_path("http://cdn/v.mp4", _p, 0) is False
       and MD._dl_to_path("notaurl", _p, 48) is False
       and MD._dl_to_path("", _p, 48) is False)
    MD.httpio.get = lambda url, **kw: _FakeResp(200, b"<html>", "text/html")
    ok("dl html-captcha → False", MD._dl_to_path("http://cdn/v.mp4", _p, 48) is False)
finally:
    MD.httpio.get = _real_get

_TM = os.path.join(_TMP, "master720.mp4")
_TO = os.path.join(_TMP, "hd480.mp4")
if _FF and _mk_testsrc(_TM, 1280, 720, 2):
    _t0 = time.time()
    _ok = MD._hd_transcode(_TM, _TO, 480, 2)
    _d2, _w2, _h2 = MD._ff_probe(_TO) if _ok else (0, 0, 0)
    ok("transcode 720→480 asli HD (probe-verified)", bool(_ok) and _h2 == 480,
       f"took={time.time()-_t0:.0f}s h={_h2}")
else:
    skip("transcode asli", "no-ffmpeg")

print("\n[C] HD pipeline guards")
ok("HD junk-URL → None", MD._yt_loader_hd("https://fb.com/x", 720) is None
   and MD._yt_loader_hd("", 720) is None and MD._yt_loader_hd(None) is None)
_real_ff = MD._HAS_FFMPEG
try:
    MD._HAS_FFMPEG = False
    ok("no-ffmpeg → None (legacy try karo)",
       MD._yt_loader_hd("https://www.youtube.com/watch?v=VIDHD001", 720) is None)
finally:
    MD._HAS_FFMPEG = _real_ff

# nakli master (360x640 jaisa) → None, kabhi fake-HD nahi
_TS = os.path.join(_TMP, "small360.mp4")
if _FF and _mk_testsrc(_TS, 360, 640, 1):
    _rlr, _rdl = MD._loader_run, MD._dl_to_path

    def _fake_run(url, height, wait):
        return "http://cdn/master.mp4", "FX", "1080"

    def _fake_dl(url, path, max_mb, **kw):
        with open(_TS, "rb") as f, open(path, "wb") as o:
            o.write(f.read())
        return True

    try:
        MD._loader_run, MD._dl_to_path = _fake_run, _fake_dl
        ok("nakli-master (640h) → None", MD._yt_loader_hd(
            "https://www.youtube.com/watch?v=VIDHD002", 720, wait=10) is None)
    finally:
        MD._loader_run, MD._dl_to_path = _rlr, _rdl
else:
    skip("nakli-master reject", "no-ffmpeg")

# lambi video → fatal (honest message)
_rlr2, _rdl2, _rpr = MD._loader_run, MD._dl_to_path, MD._ff_probe
try:
    MD._loader_run = lambda url, height, wait: ("http://cdn/m.mp4", "LONG", "1080")
    MD._dl_to_path = lambda url, path, max_mb, **kw: (open(path, "wb").write(b"V" * 2000), True)[1]
    MD._ff_probe = lambda path: (1000.0, 608, 1080)
    _rf = MD._yt_loader_hd("https://www.youtube.com/watch?v=VIDHD003", 720, wait=10)
    ok("20-min video → fatal + Hindi wajah", bool(_rf) and _rf.get("fatal") is True
       and "lambi" in str(_rf.get("error")), str((_rf or {}).get("error"))[:40])
finally:
    MD._loader_run, MD._dl_to_path, MD._ff_probe = _rlr2, _rdl2, _rpr

print("\n[D] Honesty — ladder echo me sach")
_TV = os.path.join(_TMP, "v‐tiny.mp4")
if _FF and _mk_testsrc(_TV, 320, 240, 1):
    with open(_TV, "rb") as f:
        _VB = f.read()

    def _hon(url, **kw):
        if "loader.to/ajax" in url:
            return _FakeResp(200, b"{}", "application/json",
                              {"success": True, "progress_url": "http://p/hon"})
        if url == "http://p/hon":
            return _FakeResp(200, b"{}", "application/json",
                              {"success": 1, "download_url": "http://cdn/hon.mp4",
                               "title": "HON", "format": "720"})
        if url == "http://cdn/hon.mp4":
            return _FakeResp(200, _VB, "video/mp4")
        return _FakeResp(404, b"", "text/plain")

    try:
        MD.httpio.get = _hon
        _rh = MD._yt_loader("https://www.youtube.com/watch?v=VIDHON01", 720,
                            wait=15, max_mb=48)
        ok("'720'-ladder → quality 360p (sach)", bool(_rh and _rh.get("ok"))
           and (_rh or {}).get("quality") == "360p", str((_rh or {}).get("quality")))
    finally:
        MD.httpio.get = _real_get
else:
    skip("ladder honesty", "no-ffmpeg")

print("\n[E] Regression — wiring + version + prompts")
ok("quality-pipe me HD (1080 + asli-h)", "_yt_loader_hd(url, 1080" in MD_SRC
   and "_yt_loader_hd(url, h" in MD_SRC)
ok("picker par 1080-master prewarm", "MD.yt_loader_prewarm(raw_text, 1080)" in BOT_SRC)
ok("background tap task", "_yt_hd_bg" in BOT_SRC and "_YT_HD_RUNNING" in BOT_SRC
   and "taiyaar ho raha hai" in BOT_SRC)
ok("hub caps 6/12 intact", "_call_capped(_hub_youtube_download, 6" in MD_SRC
   and "_call_capped(_hub_youtube_download, 12" in MD_SRC)
_vm = re.match(r"v(\d+)", B.BOT_VERSION)
ok("version v85+ (v98) + poori history",
   bool(_vm) and int(_vm.group(1)) >= 85 and "v98.0" in B.BOT_VERSION
   and "v97.0" in B.BOT_VERSION and "v96.0" in B.BOT_VERSION
   and "v95.0" in B.BOT_VERSION and "v94.0" in B.BOT_VERSION
   and "v93.0" in B.BOT_VERSION and "v86.0" in B.BOT_VERSION
   and "v85.0" in B.BOT_VERSION and "v84.0" in B.BOT_VERSION
   and "v83.0" in B.BOT_VERSION and "v77" in B.BOT_VERSION
   and "FREE4ALL" in B.BOT_VERSION, B.BOT_VERSION[:16])
ok("PROMPT_DATA 43 (koi prompt change nahi)", len(B.PROMPT_DATA) == 43,
   f"count={len(B.PROMPT_DATA)}")

print(f"\nv98 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)} | SKIP: {len(SKIP)}")
if FAIL:
    print("FAILED:")
    for _f in FAIL:
        print(f"  ❌ {_f}")
    sys.exit(1)
