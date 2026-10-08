#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v84 SELFTEST — ⚡ DOWNLOAD CACHE KEY (instant repeat)
====================================================
Check karta hai:
  1) Same video ke alag share-links (tracking params) ek hi cache key par
  2) v85: Instagram img_index se farq NAHI (poori album ek hi key) /
     YouTube quality tag alag keys dete hain
  3) Case-sensitive IDs: alag ID kabhi same key nahi
  4) Unknown links: sirf utm_/fbclid/gclid hatte hain, baaki params safe
  5) Collision safety (random IDs par koi takraav nahi)
  6) bot.py integration: dl_fid_set/get tracking variants par kaam karta hai
  7) Import fail hone par purana fallback key chalta hai (bot kabhi nahi rukta)

Chalane ka tarika:
    python3 tests/test_v84_dlkey.py
"""
import os
import random
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v84_")
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
    from modules.core import dlkey as D

    K = D.dl_cache_key
    C = D.canonical_url_id

    print("=" * 62)
    print("1) Same video, alag share-links → ek hi key")
    print("=" * 62)
    ig_a = "https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3&stkn=abc"
    ig_b = "https://instagram.com/p/DeJgDvDIFg2/?img_index=3&igsh=xyz"
    ok("Instagram: stkn/igsh ka farq nahi", K(ig_a) == K(ig_b))
    yt_a = "https://youtu.be/jNQXAC9IVRw?si=abc"
    yt_b = "https://www.youtube.com/watch?v=jNQXAC9IVRw&t=10s"
    yt_c = "https://www.youtube.com/shorts/jNQXAC9IVRw"
    ok("YouTube: youtu.be / watch / shorts = ek key", K(yt_a) == K(yt_b) == K(yt_c))
    tt_a = "https://www.tiktok.com/@scout2015/video/6718335390845095173?is_from_webapp=1&sender_device=pc"
    tt_b = "https://www.tiktok.com/@scout2015/video/6718335390845095173"
    ok("TikTok: webapp params ka farq nahi", K(tt_a) == K(tt_b))
    fb_a = "https://www.facebook.com/watch/?v=10153231379946729&ref=sharing"
    fb_b = "https://www.facebook.com/PAGE/videos/10153231379946729/"
    ok("Facebook: watch?v= aur page/videos/ ek hi video", K(fb_a) == K(fb_b))
    ok("Facebook ID canonical 'fb:<id>'", C(fb_a) == "fb:10153231379946729", str(C(fb_a)))

    print("=" * 62)
    print("2) Alag content → alag key")
    print("=" * 62)
    ig_img2 = "https://www.instagram.com/p/DeJgDvDIFg2/?img_index=2"
    ok("v85: img_index=2 == img_index=3 (poori album ek hi key)", K(ig_a) == K(ig_img2))
    ok("v85: img_index nahi diya == img_index=3 (same post)", K("https://www.instagram.com/p/DeJgDvDIFg2/") == K(ig_a))
    ok("YouTube: quality tag alag ⇒ alag key", K(yt_a, "q360") != K(yt_a, "q720"))
    ok("YouTube: same tag ⇒ same key", K(yt_a, "q360") == K(yt_b, "q360"))
    ok("Instagram: case alag ⇒ alag key (ID case-sensitive)",
       K(ig_a) != K("https://www.instagram.com/p/dejgdvdifg2/?img_index=3"))
    ok("YouTube: ID case alag ⇒ alag key", K(yt_a) != K("https://youtu.be/JNQXAC9IVRW?si=abc"))
    ok("Facebook 'fb.watch' alag namespace (numeric id se takraav nahi)",
       C("https://fb.watch/10153231379946729/") != C("https://www.facebook.com/watch/?v=10153231379946729"))

    print("=" * 62)
    print("3) Unknown links: sirf universal tracking hata, baaki safe")
    print("=" * 62)
    ok("utm_ aur fbclid hat gaye", K("https://example.com/A?utm_source=x&fbclid=y&id=5") == K("https://example.com/A?id=5"))
    ok("path ka case preserve (A ≠ a)", K("https://example.com/A?id=5") != K("https://example.com/a?id=5"))
    ok("'source' param NAHI hataya (content badal sakta hai)",
       K("https://example.com/a?source=1") != K("https://example.com/a?source=2"))
    ok("'ref' param NAHI hataya", K("https://example.com/a?ref=1") != K("https://example.com/a?ref=2"))

    print("=" * 62)
    print("4) Edge inputs — crash nahi, hamesha 'dlfid:' key")
    print("=" * 62)
    for _name, _val in (("empty", ""), ("None", None), ("plain text", "hello there"),
                        ("url with punctuation", "https://youtu.be/jNQXAC9IVRw."), ("spaces", "   ")):
        try:
            _k = K(_val)
            ok(f"edge '{_name}' ok", _k.startswith("dlfid:") and len(_k) == 6 + 24, _k)
        except Exception as e:  # noqa: BLE001
            ok(f"edge '{_name}' ok", False, repr(e)[:120])
    ok("punctuation trim: '...jNQXAC9IVRw.' == clean",
       K("https://youtu.be/jNQXAC9IVRw.") == K("https://youtu.be/jNQXAC9IVRw"))
    long1 = "https://ex.com/" + "a" * 500 + "1"
    long2 = "https://ex.com/" + "a" * 500 + "2"
    ok("lambe links alag keys (truncation nahi)", K(long1) != K(long2))
    ok("deterministic (same input = same key)", K(ig_a) == K(ig_a))

    print("=" * 62)
    print("5) Collision safety (random IDs)")
    print("=" * 62)
    rnd = random.Random(84)
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
    codes = set()
    while len(codes) < 3000:
        codes.add("".join(rnd.choice(alpha) for _ in range(11)))
    codes = sorted(codes)
    ig_keys = {K(f"https://www.instagram.com/p/{c}/") for c in codes}
    ok("3000 random Instagram codes → 3000 unique keys", len(ig_keys) == len(codes), str(len(ig_keys)))
    yt_keys = {K(f"https://youtu.be/{c}") for c in codes}
    ok("3000 random YouTube IDs → 3000 unique keys", len(yt_keys) == len(codes), str(len(yt_keys)))
    case_pairs = [c for c in codes if c.lower() != c and c.upper() != c]
    ok("case-variant pairs ka koi takraav nahi",
       all(K(f"https://youtu.be/{c}") != K(f"https://youtu.be/{c.swapcase()}") for c in case_pairs[:500]))
    ok("key format: 'dlfid:' + 24 hex", bool(re.fullmatch(r"dlfid:[0-9a-f]{24}", K(ig_a))))

    print("=" * 62)
    print("6) bot.py integration — dl_fid_set/get tracking variants par")
    print("=" * 62)
    import bot as B
    ok("bot.dl_fid_key: tracking link == clean link", B.dl_fid_key(ig_a) == B.dl_fid_key(ig_b))
    B.dl_fid_set(ig_a, "FILE_ID_V84_A")
    ok("set (tracked) → get (doosra tracking) = file_id", B.dl_fid_get(ig_b) == "FILE_ID_V84_A")
    ok("get ek alag post par khaali (galat hit nahi)",
       B.dl_fid_get("https://www.instagram.com/p/AAAAAAAAAAA/") == "")
    ok("v85: get alag img_index par BHI file_id (same post)", B.dl_fid_get(ig_img2) == "FILE_ID_V84_A")
    B.dl_fid_forget(ig_a)
    ok("forget ke baad khaali", B.dl_fid_get(ig_b) == "")

    print("=" * 62)
    print("7) Fallback: module import fail ⇒ purana key, bot nahi rukta")
    print("=" * 62)
    _saved = sys.modules.get("modules.core.dlkey", "__absent__")
    sys.modules["modules.core.dlkey"] = None          # import ab ImportError dega
    try:
        _fb = B.dl_fid_key("https://www.instagram.com/p/DeJgDvDIFg2/?igsh=1")
        import hashlib as _h
        _legacy = "dlfid:" + _h.sha1(("|" + "https://www.instagram.com/p/dejgdvdifg2/?igsh=1".lower())
                                     .encode("utf-8", "ignore")).hexdigest()[:24]
        ok("fallback key chalu (purana formula)", _fb == _legacy, _fb)
    except Exception as e:  # noqa: BLE001
        ok("fallback key chalu (purana formula)", False, repr(e)[:120])
    finally:
        if _saved == "__absent__":
            sys.modules.pop("modules.core.dlkey", None)
        else:
            sys.modules["modules.core.dlkey"] = _saved

    print("\n" + "=" * 62)
    print(f"v84 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
    if FAIL:
        print("FAILED:", FAIL)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
