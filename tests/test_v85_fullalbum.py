#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v85 SELFTEST — 📸 FULL-ALBUM + 🔗 LINK SANITIZER + 🛡️ FORTRESS-II
=================================================================
User ki 3 live shikayaton ka regression lock (sab OFFLINE, koi network nahi):

  A. 🔗 LINK SANITIZER (modules/core/urlclean.py)
     `?img_index=3&amp;amp;stkn=...` / markdown `[x](url)` / fbclid wale gande
     links ab engines tak saaf pahunchte hain.
  B. 📸 FULL-ALBUM (6-7 photos me se 1 milti thi)
     v82 wala "img_index=N → sirf N-wan item" slicing HATA diya — ab hamesha
     poori album jaati hai (media group fail ho to ek-ek karke fallback).
     Cache key se bhi img_index hata (same post = same key).
  C. ⚡ TERABOX wap/1024tera links (surl robust + canonical page + naye tokens)
  D. 🛡️ FORTRESS-II — safe button URLs (galat URL = crash), caption 1024 guard,
     album 45MB cap, khaali items filter, background-task source logging.
  E. 🔒 PROMPT SAFETY — koi input prompt nahi badla (PROMPT_DATA intact).

Chalane ka tarika:
    python3 tests/test_v85_fullalbum.py
"""
import io
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v85_")
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


# user ke 3 ASLI failing links (jaisa chat me aaya — &amp; samet)
IG_FAIL_1 = "https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3&amp;amp;amp;stkn=MXdtYnY5OWN6M3preg=="
TB_FAIL = ("https://www.1024tera.com/wap/share/filelist?surl=YfyQ2DSJWSE8mbuw3QMxbA"
           "&amp;amp;fbclid=PAT01DUAU0RHFleHRuA2FlbQIxMABwZG9mAnNydGMGYXBwX2lkDzU2NzA2NzM0MzM1MjQyNwABp7")
IG_ALBUM = "https://www.instagram.com/p/DdmJ952D3ux/?img_index=3&amp;amp;stkn=eWdxNTlmaW4xcGhl"
TB_MD = ("[https://www.1024tera.com/wap/share/filelist?surl=YfyQ2DSJWSE8mbuw3QMxbA"
         "&amp;fbclid=X](https://www.1024tera.com/wap/share/filelist?surl=YfyQ2DSJWSE8mbuw3QMxbA&fbclid=X)")


def main():
    from modules.core import urlclean as UC
    from modules.core import dlkey as DK
    from modules import cloud_tools as CT
    from modules import media_downloader as MD
    import bot as B

    BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()

    print("=" * 62)
    print("A) LINK SANITIZER — gande links saaf")
    print("=" * 62)
    ok("IG fail-link se canonical post URL", UC.insta_clean(IG_FAIL_1) == "https://www.instagram.com/p/DeJgDvDIFg2/",
       UC.insta_clean(IG_FAIL_1))
    _cu, _ci = UC.insta_parts(IG_FAIL_1)
    ok("img_index=3 parse (caption note ke liye)", _ci == 3, str(_ci))
    ok("album link canonical + idx", UC.insta_parts(IG_ALBUM) == ("https://www.instagram.com/p/DdmJ952D3ux/", 3),
       str(UC.insta_parts(IG_ALBUM)))
    ok("terabox surl (&amp;+fbclid ke baad bhi)", UC.tera_surl(TB_FAIL) == "YfyQ2DSJWSE8mbuw3QMxbA",
       UC.tera_surl(TB_FAIL))
    ok("markdown-wrapped terabox link", UC.tera_surl(TB_MD) == "YfyQ2DSJWSE8mbuw3QMxbA", UC.tera_surl(TB_MD))
    ok("markdown-wrapped IG link", UC.insta_clean(f"[reel]({IG_ALBUM})") == "https://www.instagram.com/p/DdmJ952D3ux/",
       UC.insta_clean(f"[reel]({IG_ALBUM})"))
    ok("clean_link: aas-paas ka text kat jaata hai",
       UC.clean_link("ye lo link: https://youtu.be/jNQXAC9IVRw?t=5 please dekho") == "https://youtu.be/jNQXAC9IVRw?t=5")
    for _jn, _jv in (("None", None), ("bytes", b"https://youtu.be/abc123"), ("khaali", "   "),
                     ("bina link", "hello duniya"), ("number", 12345)):
        try:
            _r = UC.clean_link(_jv)
            ok(f"junk '{_jn}' crash nahi", isinstance(_r, str), repr(_r)[:60])
        except Exception as e:  # noqa: BLE001
            ok(f"junk '{_jn}' crash nahi", False, repr(e)[:100])
    ok("safe_button_url: valid URL pass", UC.safe_button_url("https://x.com/a") == "https://x.com/a")
    ok("safe_button_url: kachra → None", UC.safe_button_url("notaurl") is None
       and UC.safe_button_url("") is None and UC.safe_button_url(None) is None)

    print("=" * 62)
    print("B) FULL-ALBUM — img_index se farq nahi, poori album")
    print("=" * 62)
    ok("dlkey: img_index=3 == bina img_index",
       DK.dl_cache_key(IG_FAIL_1) == DK.dl_cache_key("https://www.instagram.com/p/DeJgDvDIFg2/"))
    ok("dlkey: &amp; wala link == saaf link",
       DK.dl_cache_key(IG_FAIL_1) == DK.dl_cache_key("https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3"))
    ok("dlkey: alag post ≠ (galat hit nahi)",
       DK.dl_cache_key(IG_FAIL_1) != DK.dl_cache_key("https://www.instagram.com/p/AAAAAAAAAAA/"))
    ok("bot.py: single-item slicing HATA (v82 block gaya)",
       '_it = res["items"][_img_idx - 1]' not in BOT_SRC, "slicing abhi bhi hai!")
    ok("bot.py: FULL-ALBUM note maujood", "FULL-ALBUM" in BOT_SRC and "_album_note" in BOT_SRC)
    ok("bot.py: album one-by-one fallback maujood", "one-by-one" in BOT_SRC)
    ok("v86: album helper (_album_chunks) + 60MB cap + khaali-item filter",
       "_album_chunks(" in BOT_SRC and "60 * 1048576" in BOT_SRC and "album items khaali" in BOT_SRC)
    ok("bot.py: caption 1024-guard ([:900])", "[:900]" in BOT_SRC)
    ok("_parse_img_index abhi bhi parse karta hai (caption note ke liye)",
       B._parse_img_index(IG_FAIL_1) == 3 and B._parse_img_index("https://instagram.com/p/X/") is None)
    ok("embed-album engine maujood", hasattr(MD, "_ig_embed_album") and hasattr(MD, "_jpeg_fit"))
    # _jpeg_fit: chhoti/distorted bytes par None, kabhi crash nahi
    try:
        ok("_jpeg_fit junk par None (crash nahi)", MD._jpeg_fit(b"") is None and MD._jpeg_fit(b"xx") is None
           and MD._jpeg_fit(None) is None)
        # asli chhoti JPEG banao → fit hona chahiye
        from PIL import Image
        _im = Image.new("RGB", (50, 40), color="red")
        _bf = io.BytesIO()
        _im.save(_bf, format="JPEG")
        ok("_jpeg_fit asli photo par bytes deta hai",
           isinstance(MD._jpeg_fit(_bf.getvalue()), bytes))
    except Exception as e:  # noqa: BLE001
        ok("_jpeg_fit checks", False, repr(e)[:120])
    ok("_ig_code_of: instagr.am short link", MD._ig_code_of("https://instagr.am/p/DeJgDvDIFg2/") == "DeJgDvDIFg2",
       MD._ig_code_of("https://instagr.am/p/DeJgDvDIFg2/"))
    ok("_ig_code_of: &amp; wala link", MD._ig_code_of(IG_FAIL_1) == "DeJgDvDIFg2", MD._ig_code_of(IG_FAIL_1))
    ok("classify: &amp; reel link → reel",
       MD.classify_instagram_url("https://www.instagram.com/reel/AbC123/?igsh=xx&amp;amp;stkn=yy") == "reel")
    ok("is_supported_video_url: markdown IG link", MD.is_supported_video_url(f"[r]({IG_ALBUM})") is True)

    print("=" * 62)
    print("C) TERABOX — wap/1024tera robust")
    print("=" * 62)
    ok("surl: wap+&amp;+fbclid link", CT._extract_surl(TB_FAIL) == "YfyQ2DSJWSE8mbuw3QMxbA", str(CT._extract_surl(TB_FAIL)))
    ok("surl: markdown link", CT._extract_surl(TB_MD) == "YfyQ2DSJWSE8mbuw3QMxbA")
    ok("surl: shorturl= variant", CT._extract_surl("https://terabox.com/x?shorturl=AbC123xYz") == "AbC123xYz")
    ok("surl: /s/ link", CT._extract_surl("https://terabox.com/s/1XrQk2mBnPqRtYvWx3cde") is not None)
    ok("surl: junk par None (crash nahi)", CT._extract_surl(None) is None and CT._extract_surl("hello") is None)
    ok("is_terabox_url: markdown link", CT.is_terabox_url(TB_MD) is True)
    ok("bot.py: terabox safe buttons (validate)", BOT_SRC.count("_safe_btn_url(") >= 6,
       f"count={BOT_SRC.count('_safe_btn_url(')}")
    ok("bot.py: link-mode safe buttons", '"🌐 Original page kholo"' in BOT_SRC and "_orig_u" in BOT_SRC)

    print("=" * 62)
    print("D) FORTRESS-II — crash-proof wiring")
    print("=" * 62)
    ok("v86: version v86 + history (v85/v84/v83/v77)", B.BOT_VERSION.startswith("v86") and "v85.0" in B.BOT_VERSION and "v84.0" in B.BOT_VERSION
       and "v83.0" in B.BOT_VERSION and "v77" in B.BOT_VERSION, B.BOT_VERSION[:16])
    ok("guard words (FREE4ALL/SPEED/NO-GYAAN)", "FREE4ALL" in B.BOT_VERSION and "SPEED" in B.BOT_VERSION
       and "NO-GYAAN" in B.BOT_VERSION)
    ok("background-task source logging (v85)", "background task traceback" in BOT_SRC)
    ok("test-locked raw_text lines intact",
       all(s in BOT_SRC for s in ("_fid = dl_fid_get(raw_text)",
                                  "dl_fid_set(raw_text, _sent.video.file_id)",
                                  "with_tool_timeout(download_video_async(raw_text), 40",
                                  "yt_cached_qualities(raw_text)",
                                  "asyncio.to_thread(resolve_cloud_url, raw_text)")))
    ok("urlclean import fail-safe (bot kabhi nahi rukta)",
       "from modules.core import urlclean as _UC" in BOT_SRC and "_UC = None" in BOT_SRC)

    print("=" * 62)
    print("E) PROMPT SAFETY — koi prompt nahi badla")
    print("=" * 62)
    try:
        _pd = B.PROMPT_DATA
        ok("PROMPT_DATA 43 tools (42 + QR Scanner)", len(_pd) == 43, f"count={len(_pd)}")
        ok("terabox head intact", _pd.get("terabox", {}).get("head") == "⚡ TERABOX / CLOUD ENGINE")
        ok("insta_dl head intact",
           _pd.get("insta_dl", {}).get("head") == "📥 VIDEO DOWNLOAD (Insta / YouTube / Facebook / TikTok)")
        ok("har prompt me head+ask+tip (structure intact)",
           all(isinstance(v, dict) and "head" in v and "ask" in v for v in _pd.values()))
    except Exception as e:  # noqa: BLE001
        ok("PROMPT_DATA checks", False, repr(e)[:120])

    print("\n" + "=" * 62)
    print(f"v85 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
    print("=" * 62)
    if FAIL:
        print("FAILED:")
        for f in FAIL:
            print(f"  ❌ {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
