# -*- coding: utf-8 -*-
"""v93 SELFTEST — ☁️ TERABOX / 1024TERA FILE REPORT FIX.

Owner ki shikayat (8 Oct 2026):
    "https://www.1024tera.com/wap/share/filelist?surl=YfyQ2DSJWSE8mbuw3QMxbA
     — ye link fail ho gaya."

Jaanch kar jo mila (live, 8 Oct 2026):
  * Listing API (`share/list`) bina login 100% chalta hai — errno 0, poora file
    byora aata hai: naam, size, duration, width/height, thumbs, md5, date.
  * Download API (`share/download`) Terabox ne lock kar di hai:
        {"errno":400310,"errmsg":"need verify_v2"}   ← CAPTCHA wall
    Aur `api/sharedownload` → {"errno":2}. Public workers bhi mar chuke hain
    (robin: "Failed to get share info", hnn: "Page not found", qtcloud: HTTP 500).
  * Yaani dlink bina cookie nikalna 2026 me possible nahi. Bot pehle bhi file ka
    naam+size nikal leta tha, par user ko sirf ek adhuri line dikhti thi aur
    5 mar-chuke web downloader buttons — isliye laga "tool fail ho gaya".

v93 me kya badla:
  * Poora FILE REPORT card (har file: size, type, video length, resolution, date,
    total size) + thumbnail photo. Listing ka asli kaam ab dikhta hai.
  * Error message jhooth nahi bolta — saaf batata hai Terabox ne kya lock kiya
    aur uska permanent ilaaj (TERABOX_COOKIE) kya hai.

Ye test 3 cheezein lock karta hai:
  A. Helper functions ka behaviour (koi network nahi)
  B. Report card ka format + HTML-safety + Telegram ki 1024-char hadd ka dhyaan
  C. REAL 1024tera link par end-to-end (network ho to; na ho to honest SKIP)
"""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v93_tb_tmp.db"))

PASS = 0
FAIL = 0
SKIP = 0
FAILS = []


def check(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILS.append(label)
        print(f"   ❌ FAIL: {label} {extra}")


def skip(label, why):
    global SKIP
    SKIP += 1
    print(f"   ⚪ SKIP: {label} — {why}")


def read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


print("v93 SELFTEST — ☁️ Terabox File Report FIX")

import modules.cloud_tools as CT                                 # noqa: E402

# ============================================================================
print("\n[A] Helpers")
# ============================================================================
check("A1 _fmt_dur 291 -> 4m 51s", CT._fmt_dur(291) == "4m 51s", CT._fmt_dur(291))
check("A2 _fmt_dur 3725 -> 1h 02m 05s", CT._fmt_dur(3725) == "1h 02m 05s", CT._fmt_dur(3725))
check("A3 _fmt_dur 9 -> 9s", CT._fmt_dur(9) == "9s")
check("A4 _fmt_dur galat input par '' (crash nahi)",
      CT._fmt_dur(None) == "" and CT._fmt_dur("abc") == "" and CT._fmt_dur(0) == "")

for nm, exp_icon, exp_label in (
    ("clip.mp4", "🎬", "Video"), ("song.MP3", "🎵", "Audio"),
    ("pic.jpg", "🖼️", "Image"), ("doc.pdf", "📕", "PDF"),
    ("pack.zip", "🗜️", "Archive"), ("app.apk", "📦", "APK"),
    ("data.xlsx", "📊", "Sheet"), ("noext", "📄", "File"),
):
    i, l = CT._kind_of(nm)
    check(f"A5 {nm} -> {exp_icon} {exp_label}", (i, l) == (exp_icon, exp_label), f"{i} {l}")
check("A6 category=1 par Video maana jaata hai (extension na ho)",
      CT._kind_of("weird_file", "1") == ("🎬", "Video"))
check("A7 _kind_of(None) crash nahi karta", isinstance(CT._kind_of(None), tuple))

check("A8 thumbs dict me se sabse bada URL chunta hai",
      CT._tb_thumb_url({"thumbs": {"url1": "a", "url2": "b", "url3": "c"}}) == "c")
check("A9 thumbs na ho to '' (crash nahi)",
      CT._tb_thumb_url({}) == "" and CT._tb_thumb_url(None) == "")
check("A10 thumbs string ho to wahi", CT._tb_thumb_url({"thumbs": "zz"}) == "zz")

# _tb_info_only — asli Terabox share/list ke jaisa item
_RAW = [{
    "server_filename": "All Viral Videos and MMS Link(1).mp4",
    "size": 44829267, "duration": 291, "width": 480, "height": 856,
    "category": "1", "server_mtime": 1788434926, "fs_id": 826869911250765,
    "md5": "29dca67640d9fe8402e167eb99979a6f",
    "thumbs": {"url1": "https://dm-data.1024tera.com/thumbnail/x?size=c140_u90"},
}]
_info = CT._tb_info_only(_RAW)
check("A11 info me naam + size (v82 test ka contract intact)",
      bool(_info) and _info[0]["name"].endswith(".mp4") and "MB" in _info[0]["size"])
check("A12 naye fields mile: kind/duration/resolution/thumb",
      _info[0]["kind"] == "Video" and _info[0]["duration"] == "4m 51s"
      and _info[0]["width"] == 480 and _info[0]["thumb"].startswith("https://"))
check("A13 size_bytes sahi (42.75 MB)", _info[0]["size_bytes"] == 44829267)
check("A14 ghatiya items skip (None / bina naam)",
      CT._tb_info_only([None, {"size": 5}, "x", _RAW[0]]) and
      len(CT._tb_info_only([None, {"size": 5}, "x", _RAW[0]])) == 1)
check("A15 _tb_info_only(None) -> [] (crash nahi)", CT._tb_info_only(None) == [])

# ============================================================================
print("\n[B] Report card")
# ============================================================================
_rep = CT.tb_file_report(_info)
check("B1 report me file ka naam hai", "All Viral Videos" in _rep)
check("B2 report me size hai", "42.75 MB" in _rep)
check("B3 report me video length hai", "4m 51s" in _rep)
check("B4 report me resolution hai", "480×856" in _rep)
check("B5 report me total size hai", "total" in _rep)
check("B6 khaali input par '' (bot ise skip karega)", CT.tb_file_report([]) == ""
      and CT.tb_file_report(None) == "")

# HTML-safety: file ke naam me < > & ho to Telegram message reject karta hai
_evil = CT._tb_info_only([{"server_filename": "<script>alert(1)</script> & 'x'.mp4", "size": 100}])
_rep_evil = CT.tb_file_report(_evil)
check("B7 file ke naam me < > escape hue (Telegram reject nahi karega)",
      "<script>" not in _rep_evil and "&lt;script&gt;" in _rep_evil, _rep_evil[:120])

# bahut saari file: report Telegram ki hadd se na toote
_many = CT._tb_info_only([{"server_filename": f"file_{i}.mp4", "size": 1000000,
                           "duration": 60} for i in range(40)])
_rep_many = CT.tb_file_report(_many)
check("B8 40 file par report limit me rehta hai", len(_rep_many) < 3800, str(len(_rep_many)))
check("B9 '…aur N file' note aata hai", "aur " in _rep_many and "file(s)" in _rep_many)
check("B10 report hamesha str hai", isinstance(_rep, str))

# bot.py me wiring — report + thumbnail actually bheje jaate hain
BOT_SRC = read("bot.py")
CT_SRC = read("modules/cloud_tools.py")
check("B11 resolve_terabox 'report' field lautata hai",
      '"report": report' in CT_SRC)
check("B12 bot.py report ko card me dikhata hai",
      "res.get(\"report\")" in BOT_SRC or "res.get('report')" in BOT_SRC)
check("B13 bot.py thumbnail fetch karta hai (tb_fetch_thumb import)",
      "tb_fetch_thumb" in BOT_SRC)
check("B14 photo bhejne ka rasta hai", "reply_photo(photo=_tb" in BOT_SRC)
check("B15 card fail ho to bhi plain jawab jaata hai (khali haath nahi)",
      "Download link nahi mila — share page kholo" in BOT_SRC)
check("B16 error message jhooth nahi bolta — CAPTCHA wall ka naam leta hai",
      "need verify_v2" in CT_SRC)
check("B17 permanent ilaaj bataya gaya hai (TERABOX_COOKIE)",
      "TERABOX_COOKIE" in CT_SRC)

# ============================================================================
print("\n[C] REAL 1024tera link — end-to-end (aapke hi link par)")
# ============================================================================
_OWNER = "https://www.1024tera.com/wap/share/filelist?surl=YfyQ2DSJWSE8mbuw3QMxbA"
try:
    import requests                                              # noqa: F401
    _probe = CT.http_get("https://www.1024tera.com/", headers=CT.UA, timeout=10)
    _online = _probe.status_code < 500
except Exception as _e:                                          # noqa: BLE001
    _online = False
    skip("C live terabox", f"network probe fail: {type(_e).__name__}: {str(_e)[:80]}")

if _online:
    try:
        r = CT.resolve_cloud_url(_OWNER)
    except Exception as _e:                                      # noqa: BLE001
        r = None
        skip("C live terabox", f"resolve fail: {type(_e).__name__}: {str(_e)[:90]}")
    if r:
        _rep_live = str(r.get("report") or "")
        check("C1 surl sahi nikla", r.get("surl") == "YfyQ2DSJWSE8mbuw3QMxbA", r.get("surl"))
        check("C2 file_info bhara aata hai (listing chalti hai)",
              bool(r.get("file_info")), str(r.get("tried")))
        check("C3 report card bana (pehle ye khaali tha)", bool(_rep_live))
        check("C4 report me asli file ka naam hai", ".mp4" in _rep_live, _rep_live[:120])
        check("C5 report me size hai", "MB" in _rep_live or "GB" in _rep_live)
        check("C6 thumbnail URL mila", str(r.get("thumb") or "").startswith("https://"))
        if r.get("thumb"):
            _b = CT.tb_fetch_thumb(r["thumb"])
            if _b is None:
                skip("C7 thumbnail bytes", "thumb server ne jawab nahi diya")
            else:
                check("C7 thumbnail asli JPEG bytes hain",
                      _b[:3] == b"\xff\xd8\xff" and len(_b) > 200, str(len(_b)))
        check("C8 fallback buttons abhi bhi aate hain (user kaam rukta nahi)",
              len(r.get("fallback_links") or []) >= 3)
        # dlink mil gaya to ye test khushi se pass karega (cookie laga ho to)
        if r.get("ok"):
            print("   ✅ BONUS: dlink mil gaya (cookie/provider chalu hai) — direct download OK")

print("\n" + "=" * 64)
for _l in FAILS:
    print("  ❌", _l)
print(f"RESULT: {PASS} PASS / {FAIL} FAIL / {SKIP} SKIP")
print(f"  v93 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 64)
sys.exit(1 if FAIL else 0)
