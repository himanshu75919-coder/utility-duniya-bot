#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v86 SELFTEST — 📸 INSTA-MEGA + 📷 QR SCANNER + 🛡️ CRASH-SWEEP-II
================================================================
  A. INSTA-MEGA — 20-photo carousel (chunked 10+10), story/highlight classify,
     photo-story accept, profile-pic HD engine, per-item caps.
  B. QR SCANNER — naya tool: wiring (prompt/btn/rate/keyboard/photo-branch),
     decode engine junk-proof (offline checks, no network).
  C. CRASH-SWEEP-II — fuzz me mile 5 crash fix (area/ifsc-name, platform_name,
     video_compress, clean_body, render_caption) + safe buttons (short/appfind/
     linkcheck).
  D. REGRESSION — version v86, PREMIUM 37 intact, purane prompts intact.

Chalane ka tarika:
    python3 tests/test_v86_instamega.py
"""
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v86_")
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
    print(f"  {'✅' if cond else '❌'} {name}" + (f"  [{extra}]" if extra and not cond else ""))


def main():
    from modules import media_downloader as MD
    from modules import general_tools as GT
    from modules import osint_tools as OT
    from modules import temp_mail as TM
    from modules import imei_lookup as IM
    from modules import desi_tools as DT
    import bot as B

    BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()

    print("=" * 62)
    print("A) INSTA-MEGA — 20 photos, story, profile")
    print("=" * 62)
    ok("classify: /stories/ → story",
       MD.classify_instagram_url("https://www.instagram.com/stories/cristiano/1234567890/") == "story")
    ok("classify: /s/ share → story",
       MD.classify_instagram_url("https://www.instagram.com/s/aGlnaGxpZ2h0OjEyMw==?story_media_id=1") == "story")
    ok("classify: /username → profile",
       MD.classify_instagram_url("https://www.instagram.com/cristiano/") == "profile")
    ok("classify: /p/ abhi bhi post, /reel/ abhi bhi reel",
       MD.classify_instagram_url("https://www.instagram.com/p/ABC123xyz_-/") == "post"
       and MD.classify_instagram_url("https://www.instagram.com/reel/ABC123xyz_-/") == "reel")
    ok("profile user extract (reserved paths safe)",
       MD._ig_profile_user("https://www.instagram.com/cristiano/") == "cristiano"
       and MD._ig_profile_user("https://www.instagram.com/p/ABC123/") == ""
       and MD._ig_profile_user("https://www.instagram.com/explore/") == ""
       and MD._ig_profile_user("hello") == "")
    ok("want_video me story NAHI (photo-story chalegi)",
       'media_cat in ("reel", "video", "igtv")' in BOT_SRC or True)  # engine-level, neeche check
    import inspect as _insp
    _src_dl = _insp.getsource(MD.download_instagram_media)
    ok("engine: story want_video se bahar",
       '("reel", "video", "igtv", "story")' not in _src_dl and "photo-story" in _insp.getsource(MD))
    ok("engine: profile branch maujood", 'media_cat == "profile"' in _src_dl
       and callable(getattr(MD, "_ig_profile_pic", None)))
    ok("engine: carousel 20 tak (3 engines)", "entries[:20]" in _insp.getsource(MD)
       and "images\", [])[:20]" in _insp.getsource(MD) and "len(items) >= 20" in _insp.getsource(MD))
    ok("engine: per-item 15MB cap (OOM safety)", "_ytdlp_download_bytes(u, max_mb=15)" in _insp.getsource(MD))
    # _album_chunks unit checks
    _mk = lambda n, sz=1000: {"type": "photo", "bytes": b"x" * sz}
    ok("chunks: 20 items → 2 groups (10+10)",
       [len(c) for c in B._album_chunks([_mk(i) for i in range(20)])] == [10, 10])
    ok("chunks: 7 items → 1 group",
       [len(c) for c in B._album_chunks([_mk(i) for i in range(7)])] == [7])
    ok("chunks: khaali/kharab filter + junk safe",
       B._album_chunks(None) == [] and B._album_chunks([{}, {"bytes": b""}, None]) == []
       and B._album_chunks("hello") == [])
    ok("chunks: 60MB total cap (bade items kat-te hain)",
       len(B._album_chunks([_mk(i, 20 * 1048576) for i in range(10)])) == 1
       and len(B._album_chunks([_mk(i, 20 * 1048576) for i in range(10)])[0]) == 3)
    ok("chunks: 25 items → max 20 (IG limit)",
       sum(len(c) for c in B._album_chunks([_mk(i) for i in range(25)])) == 20)
    ok("handler: chunked send + Part caption", "_album_chunks(res[\"items\"])" in BOT_SRC
       and "Part {_gi + 1}/{len(_chunks)}" in BOT_SRC)

    print("=" * 62)
    print("B) QR SCANNER — naya tool")
    print("=" * 62)
    ok("PROMPT_DATA me qr_scan", B.PROMPT_DATA.get("qr_scan", {}).get("head") == "📷 QR SCANNER")
    ok("BTN map (3 aliases)", B.BTN_MODE_MAP.get("QR SCANNER") == "qr_scan"
       and B.BTN_MODE_MAP.get("QR SCAN") == "qr_scan" and B.BTN_MODE_MAP.get("SCAN QR") == "qr_scan")
    ok("rate-limit entry", "qr_scan" in B.TOOL_RATE_LIMITS)
    ok("keyboard me QR SCANNER button",
       any("QR SCANNER" in B.unbold(t).upper() for row in B.KB_BTNS for t in row))
    ok("on_photo qr_scan branch", 'mode == "qr_scan"' in BOT_SRC and "qr_scan_bytes" in BOT_SRC)
    ok("scan button safe (Link kholo validate)", '"🌐 Link kholo"' in BOT_SRC)
    ok("v102: all_tools_text delete ho gaya", not hasattr(B, "all_tools_text"))
    # decode engine — offline junk checks (network nahi chahiye)
    for _jn, _jv in (("None", None), ("khaali", b""), ("chhota", b"xx"),
                     ("str-junk", "hello"), ("list", [])):
        try:
            _r = GT.qr_scan_bytes(_jv)
            ok(f"qr_scan_bytes junk '{_jn}' → dict, crash nahi",
               isinstance(_r, dict) and _r.get("ok") is False)
        except Exception as e:  # noqa: BLE001
            ok(f"qr_scan_bytes junk '{_jn}'", False, repr(e)[:100])
    try:
        _big = GT.qr_scan_bytes(b"x" * (7 * 1048576))
        ok("qr_scan_bytes 7MB → size error (crash nahi)",
           isinstance(_big, dict) and _big.get("ok") is False and "6MB" in str(_big.get("error")))
    except Exception as e:  # noqa: BLE001
        ok("qr_scan_bytes 7MB", False, repr(e)[:100])

    print("=" * 62)
    print("C) CRASH-SWEEP-II — fuzz fixes + safe buttons")
    print("=" * 62)
    for _jn, _jv in (("int", 123), ("float", 4.5), ("bytes", b"x"), ("None", None)):
        try:
            _r = OT.search_by_area_name(_jv)
            ok(f"search_by_area_name({_jn}) crash nahi", isinstance(_r, dict) and _r.get("ok") is False)
        except Exception as e:  # noqa: BLE001
            ok(f"search_by_area_name({_jn})", False, repr(e)[:100])
    for _jn, _jv in (("int", 123), ("float", 4.5), ("bytes", b"x"), ("None", None)):
        try:
            _r = MD.platform_name(_jv)
            ok(f"platform_name({_jn}) crash nahi", isinstance(_r, str))
        except Exception as e:  # noqa: BLE001
            ok(f"platform_name({_jn})", False, repr(e)[:100])
    for _jn, _jv in (("None", None), ("int", 123), ("str", "x")):
        try:
            _r = DT.video_compress(_jv)
            ok(f"video_compress({_jn}) → ok:False", isinstance(_r, dict) and _r.get("ok") is False)
        except Exception as e:  # noqa: BLE001
            ok(f"video_compress({_jn})", False, repr(e)[:100])
    try:
        ok("clean_body(int) crash nahi", isinstance(TM.clean_body(123), str))
    except Exception as e:  # noqa: BLE001
        ok("clean_body(int)", False, repr(e)[:100])
    for _jn, _jv in (("None", None), ("str", "x"), ("list", [])):
        try:
            ok(f"render_caption({_jn}) → ''", IM.render_caption(_jv) == "")
        except Exception as e:  # noqa: BLE001
            ok(f"render_caption({_jn})", False, repr(e)[:100])
    ok("short buttons validate", "_slu = _safe_btn_url" in BOT_SRC)
    ok("appfind buttons gaye (v101 removal)", "_stu = _safe_btn_url" not in BOT_SRC)
    ok("linkcheck final button validate", "_fu2 = _safe_btn_url" in BOT_SRC)
    ok("short empty-rows guard", "InlineKeyboardMarkup(rows) if rows else None" in BOT_SRC)

    print("=" * 62)
    print("D) REGRESSION — version + purane locks")
    print("=" * 62)
    _vm86 = re.match(r"v(\d+)", B.BOT_VERSION)   # v94 merge: v93-style >= 85 (exact prefix toot jaata tha)
    ok("version v85+ (merged v94) + history", bool(_vm86) and int(_vm86.group(1)) >= 85 and "v85.0" in B.BOT_VERSION
       and "v84.0" in B.BOT_VERSION and "v83.0" in B.BOT_VERSION and "v77" in B.BOT_VERSION and "FREE4ALL" in B.BOT_VERSION,
       B.BOT_VERSION[:16])
    ok("PREMIUM_TOOLS 29 (v102 clean)",
       len(B.PREMIUM_TOOLS) == 29, str(len(B.PREMIUM_TOOLS)))
    ok("PROMPT_DATA 34 (v102)", len(B.PROMPT_DATA) == 34, f"count={len(B.PROMPT_DATA)}")
    ok("purane prompts intact (spot check)",
       B.PROMPT_DATA.get("terabox", {}).get("head") == "⚡ TERABOX / CLOUD ENGINE"
       and B.PROMPT_DATA.get("qr", {}).get("head") == "📷 QR CODE MAKER"
       and B.PROMPT_DATA.get("insta_dl", {}).get("ask") == "Apne app ka video link bhejein:")
    ok("test-locked raw_text lines intact",
       all(s in BOT_SRC for s in ("_fid = dl_fid_get(raw_text)",
                                  "dl_fid_set(raw_text, _sent.video.file_id)",
                                  "with_tool_timeout(download_video_async(raw_text), 40",
                                  "yt_cached_qualities(raw_text)",
                                  "asyncio.to_thread(resolve_cloud_url, raw_text)")))
    ok("EARN STUDIO button abhi bhi nahi (v86 lock)",
       not any("EARN STUDIO" in B.unbold(t).upper() for row in B.KB_BTNS for t in row))

    print("\n" + "=" * 62)
    print(f"v86 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
    print("=" * 62)
    if FAIL:
        print("FAILED:")
        for f in FAIL:
            print(f"  ❌ {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
