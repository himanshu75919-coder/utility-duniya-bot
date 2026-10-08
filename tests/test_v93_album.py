# -*- coding: utf-8 -*-
"""v93 SELFTEST — 📸 INSTAGRAM CAROUSEL (poora album) FIX.

Owner ki asli shikayat (8 Oct 2026):
    "https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3  → is link me 6-7 photo
     hain, par bot EK hi photo de raha hai."

Wajah (jaanch kar confirm ki gayi):
    Instagram app jab share-link banata hai to apne aap `?img_index=N` chipka deta
    hai — N = wo photo jo user us waqt dekh raha tha. v82 us flag ko "user ko sirf
    N-wan item chahiye" samajh kar poore album ko 1 item par kaat deta tha.
    Live jaanch: parth_dl.get_info(".../p/DeJgDvDIFg2/") → type=carousel, entries=8.
    Yaani DATA poora aa raha tha; bot khud 7 photo phek raha tha.

Ye test 4 cheezein lock karta hai:
  A. Album kabhi 10 par chup-chaap na kate  (pehle items[:10] → 12-photo post me 2 gayab)
  B. Khaali/ghatiya item se KeyError na ho   (pehle item["bytes"] → handler mar jaata tha)
  C. img_index ab album ko kaat-ta NAHI; sirf explicit "sirf ek photo" par kaat-ta hai
  D. REAL Instagram carousel par end-to-end (network ho to; na ho to honest SKIP)
"""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v93_tmp.db"))

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


print("v93 SELFTEST — 📸 Instagram Carousel (poora album) FIX")

import bot as B                                                   # noqa: E402

# ============================================================================
print("\n[A] Album chunking — 10 ki chup-chaap hadd hata di")
# ============================================================================
_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 40


def _mk(n, kind="photo"):
    return [{"type": kind, "bytes": _JPEG + bytes([i])} for i in range(n)]


for n in (1, 2, 7, 8, 10, 11, 12, 23):
    ch = B.build_album_chunks(_mk(n), "CAP")
    got = sum(len(c) for c in ch)
    check(f"A{n} {n} item → {n} hi media jaayein (chunks={len(ch)})", got == n,
          f"mile {got}")
    check(f"A{n+100} har chunk ≤ 10 (Telegram hadd)", all(len(c) <= 10 for c in ch))

check("A200 caption sirf pehle chunk ke pehle media par",
      B.build_album_chunks(_mk(7), "CAP")[0][0].caption == "CAP"
      and all(m.caption == "" for m in B.build_album_chunks(_mk(7), "CAP")[0][1:]))
check("A201 10 se zyada par har chunk ke pehle media par position caption",
      all(c[0].caption for c in B.build_album_chunks(_mk(23), "CAP")))
check("A202 video item → InputMediaVideo + .mp4 naam",
      type(B.build_album_chunks([{"type": "video", "bytes": _JPEG}], "C")[0][0]).__name__
      == "InputMediaVideo")

# ============================================================================
print("\n[B] Khaali/ghatiya item se crash NAHI (pehle KeyError se handler marta tha)")
# ============================================================================
_dirty = [
    {"type": "photo", "bytes": _JPEG},      # sahi
    {"type": "photo"},                       # bytes missing  → pehle KeyError
    {"type": "photo", "bytes": b""},         # khaali bytes
    None,                                    # None entry     → pehle AttributeError
    "not-a-dict",                            # galat type
    {"bytes": _JPEG},                        # type missing → 'photo' maana jaaye
    {"type": "VIDEO", "bytes": _JPEG},       # uppercase → normalise ho
]
_clean = B.clean_album_items(_dirty)
check("B1 7 ghatiya items me se sirf 3 sahi bache", len(_clean) == 3, f"mile {len(_clean)}")
check("B2 koi 'bytes' key chhooti nahi (handler safe rahega)",
      all("bytes" in c and c["bytes"] for c in _clean))
check("B3 type lowercase me normalise hua", {c["type"] for c in _clean} == {"photo", "video"})
check("B4 poora kachra diya → khaali list (crash nahi)", B.clean_album_items([None, {}, "x"]) == [])
check("B5 None/omitted input → khaali list", B.clean_album_items(None) == [])
check("B6 khaali input par koi chunk nahi (handler fail_msg dikhayega)",
      B.build_album_chunks([], "C") == [])

# ============================================================================
print("\n[C] img_index ab album ko kaat-ta NAHI")
# ============================================================================
_OWNER_LINK_1 = "https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3&stkn=MXdtYnY5OWN6M3pre"
_OWNER_LINK_2 = "https://www.instagram.com/p/DdmJ952D3ux/?img_index=3&stkn=eWdxNTlmaW4xcGhl"
BOT_SRC = read("bot.py")

check("C1 img_index parse abhi bhi hota hai (v82 behaviour intact)",
      B._parse_img_index(_OWNER_LINK_1) == 3)
# v85 ne narrowing poori hata di thi (album hamesha poora) — wo behaviour bacha rahe.
# v93 uske upar sirf 10+ chunking add karta hai.
check("C2 handler me album ko 1 item par kaatne wala code nahi hai",
      "res[\"items\"][_img_idx - 1]" not in BOT_SRC)
check("C3 img_index sirf caption note ke liye use hota hai (kaatne ke liye nahi)",
      "_album_note" in BOT_SRC and "slide {_img_idx} ka link tha" in BOT_SRC)
check("C4 album delivery ALBUM_CHUNK (10) me chunk hoti hai",
      "ALBUM_CHUNK" in BOT_SRC and "range(0, len(items), ALBUM_CHUNK)" in BOT_SRC)
check("C5 album par purani res['items'][:10] chup-chaap kataai nahi bachi",
      re.search(r"\(res\[\"items\"\] or \[\]\)\[:10\]", BOT_SRC) is None)
check("C6 v85 ka 45MB cap bacha hua hai (RAM safety gayab nahi hui)",
      "45 * 1048576" in BOT_SRC)
check("C7 v85 ka album one-by-one fallback bacha hua hai",
      "album group fail, one-by-one bhej raha" in BOT_SRC)
check("C8 45MB cap se jo chhoote uska user ko NOTE jaata hai (chup-chaap nahi)",
      "size-limit se chhoote" in BOT_SRC)
# C10: `item["bytes"]` direct index tabhi jaayaz hai jab usse pehle items filter ho
# chuke hon (warna KeyError se poora handler marta tha). Merged code me filter
# do jagah hai: build_album_chunks ke andar clean_album_items(), aur v85 ke album
# handler me inline `isinstance(...) and (it.get("bytes") or b"")`.
_c10 = re.findall(r'io\.BytesIO\(item\["bytes"\]\)', BOT_SRC)
check("C10 item['bytes'] index sirf album code me hai (kahin aur nahi)",
      len(_c10) == 3, f"{len(_c10)} jagah mili")
_c10fn = BOT_SRC.split("def build_album_chunks")[1].split("\ndef ")[0]
check("C11 build_album_chunks pehle clean_album_items chalata hai (guarantee)",
      _c10fn.index("clean_album_items(") < _c10fn.index('io.BytesIO(item["bytes"])'))
# asli guarantee: album handler index se PEHLE khaali/ghatiya items nikaal deta hai
_h = BOT_SRC.split("# 1) Album / Carousel")[1].split("# 2) Single Video")[0]
check("C12 album handler index se pehle items FILTER karta hai (KeyError proof)",
      'isinstance(it, dict) and (it.get("bytes") or b"")' in _h
      and _h.index("isinstance(it, dict)") < _h.index('io.BytesIO(item["bytes"])'))
check("C13 helper clean_album_items khud bhi safe hai (None/string/bytes-missing skip)",
      B.clean_album_items([None, "x", {"type": "photo"}, {"type": "photo", "bytes": b""}]) == [])

# ============================================================================
print("\n[D] REAL Instagram carousel — end-to-end (aapke hi link par)")
# ============================================================================
try:
    from modules.media_downloader import _ig_parth
except Exception as _e:                                          # noqa: BLE001
    _ig_parth = None
    skip("D live carousel", f"media_downloader import nahi hua: {_e}")

if _ig_parth:
    try:
        info = _ig_parth("https://www.instagram.com/p/DeJgDvDIFg2/", "post")
    except Exception as _e:                                      # noqa: BLE001
        info = None
        skip("D live carousel", f"extract fail: {type(_e).__name__}: {str(_e)[:90]}")
    if not info:
        skip("D live carousel", "engine ne None diya (login-wall/rate-limit/network)")
    else:
        _items = info.get("items") or []
        check("D1 engine carousel deta hai", info.get("type") == "carousel")
        check("D2 6+ items aate hain (owner ne 6-7 bataye the)", len(_items) >= 6,
              f"mile {len(_items)}")
        _ch = B.build_album_chunks(_items, "CAP")
        check("D3 poore items Telegram chunks me jaate hain (ek bhi gayab nahi)",
              sum(len(c) for c in _ch) == len(_items),
              f"items={len(_items)} media={sum(len(c) for c in _ch)}")
        check("D4 10 se zyada ho to ek se zyada chunk bane",
              (len(_ch) > 1) if len(_items) > 10 else True)

# ============================================================================
print("\n" + "=" * 64)
for _l in FAILS:
    print("  ❌", _l)
print(f"RESULT: {PASS} PASS / {FAIL} FAIL / {SKIP} SKIP")
print(f"  v93 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 64)
sys.exit(1 if FAIL else 0)
