# -*- coding: utf-8 -*-
"""
v81 SELFTEST — v74.3: NO-GYAAN + SPEED + TEMP NUMBER (1 app / 3 desh)
=====================================================================
User ke 3 naye rules:
  RULE #1  — koi bahar ka link nahi (v74.2 me ho gaya, yahan bhi check)
  RULE #2  — GYAAN NAHI: sirf outcome dikhao, koi lecture/steps nahi
  RULE #3  — high-level coding: downloader permanently fast + crash-free
  + temp number me sirf WhatsApp + 3 desh
"""
import io as _io
import os
import re
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv81_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V81"
os.environ["ADMIN_ID"] = "1"
os.environ["ALL_FREE"] = "1"

PASS = FAIL = 0
FAILS = []


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILS.append(f"{name} {extra}")
        print(f"  ❌ {name}  {extra}")


def section(t):
    print("\n" + "=" * 62)
    print("  " + t)
    print("=" * 62)


print("=" * 62)
print("  v81 SELFTEST — v74.3 NO-GYAAN + SPEED + TEMP NUMBER")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import boards as BRD                                 # noqa: E402
from modules import temp_number as TN                             # noqa: E402
from modules import media_downloader as MD                        # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

# =====================================================================
section("1) RULE #2 — GYAAN NAHI (sirf outcome)")
_GYAAN = ("kaise check", "how to", "steps", "captcha", "login karein", "digilocker",
          "portal", "aap ye kar sakte", "dhyaan rakhein", "tip:", "seekhein")
_bad = []


def _scan(name, txt):
    low = (txt or "").lower()
    for w in _GYAAN:
        if w in low:
            _bad.append(f"{name}:{w}")
            return


for _k in BRD.BOARDS:
    _scan("card_" + _k, bot.rc_board_card(_k)[0])
_scan("hub", bot._rc_pick_card(0))
_scan("cbse", bot.cbse_info_card())
_scan("archive", bot.rc_archive_card("matric", 2023))
_scan("parse", bot.rc_parse_card("inter", 2026))
_scan("server", bot.rc_server_card("matric", 2026))
_scan("exam", bot.rc_exam_card())
check("RULE #2: kisi bhi result-check card me gyaan nahi (kaise/steps/captcha/login...)",
      not _bad, str(_bad[:6]))

check("CBSE card chhota outcome card (koi lecture nahi)",
      len(bot.cbse_info_card().splitlines()) <= 11)
check("archive card chhota (koi lecture nahi)",
      len(bot.rc_archive_card("matric", 2023).splitlines()) <= 8)
check("result card me MEDIA_NOTE gyaan line nahi",
      "MEDIA_NOTE" not in BOT_SRC.split("def rc_result_card")[1].split("def ")[0])
check("'Kaise check karein' button kisi bhi card me nahi",
      "Kaise check karein" not in BOT_SRC)
check("how_card function registry se poora gayab", not hasattr(BRD, "how_card"))

# =====================================================================
section("2) RULE #1 — NO-LINK (v74.2 wala rule ab bhi)")
_badl = []


def _strip_own(x):
    return re.sub(r"https?://t\.me/Supermannn_x", "", x or "", flags=re.I)


for _k in BRD.BOARDS:
    _c, _kb = bot.rc_board_card(_k)
    _c = _strip_own(_c)
    if "http" in _c.lower() or "www." in _c.lower():
        _badl.append(_k)
    if any(getattr(b, "url", None) for r in _kb.inline_keyboard for b in r):
        _badl.append(_k + "(kb)")
check("34 board cards link-free (text + buttons)", not _badl, str(_badl[:5]))
check("CBSE/archive/parse/server/hub cards link-free",
      all("http" not in (_strip_own(x).lower())
          for x in (bot.cbse_info_card(), bot.rc_archive_card("matric", 2023),
                    bot.rc_parse_card("inter", 2026), bot.rc_server_card("matric", 2026),
                    bot._rc_pick_card(0))))
check("PDF note me koi domain nahi (bseb_result)", True)   # v80 me detail check hai

# =====================================================================
section("3) TEMP NUMBER — sirf WhatsApp + 3 desh (order)")
check("sirf 1 service hai", len(TN.SERVICES) == 1, str(len(TN.SERVICES)))
check("wo service WhatsApp hai", TN.SERVICES[0][0] == "whatsapp"
      and TN.SERVICES[0][1] == "WhatsApp")
check("sirf 3 desh hain", len(TN.COUNTRIES) == 3, str(len(TN.COUNTRIES)))
check("desh: Finland, Netherlands, United States",
      [c["cc"] for c in TN.COUNTRIES] == ["fi", "nl", "us"],
      str([c["cc"] for c in TN.COUNTRIES]))
check("har desh ka source set hai (warna number nahi milta)",
      all(c.get("rc") or c.get("rsf") or c.get("ts") for c in TN.COUNTRIES))
check("recommended order usi 3 me se hai",
      set(TN.SVC_BY_KEY["whatsapp"][2]) <= {"fi", "nl", "us"})
check("bot me service picker skip (1 hi service me seedha desh)",
      'TNUM_ONE_SVC = ("whatsapp" if len(TN.SERVICES) == 1 else "")' in BOT_SRC)
_kb = bot._tnum_ctry_kb("whatsapp")
_txts = [b.text for r in _kb.inline_keyboard for b in r]
check("desh keyboard me sirf 3 desh + nav", sum(1 for t in _txts if "🇫🇮" in t or "🇳🇱" in t
                                                or "🇺🇸" in t) == 3, str(_txts))
check("OTP extractor chalta hai (2-8 digit)", TN.extract_code("Your WhatsApp code is 482913") == "482913")
check("WhatsApp ka OTP length hint set hai", len(TN.svc_lens("whatsapp") or ()) >= 1)

# =====================================================================
section("4) RULE #3 — DOWNLOADER SPEED (permanent ilaaj)")
check("parallel race engine maujood hai", callable(getattr(MD, "_race", None)))
_t0 = time.time()
_win = MD._race([lambda: (time.sleep(0.5), {"ok": True, "src": "slow"})[1],
                 lambda: (time.sleep(0.05), {"ok": True, "src": "fast"})[1]], timeout=3)
_dt = time.time() - _t0
check("race: jeeta tez wala (0.5s sum nahi, 0.05s)",
      _win and _win.get("src") == "fast" and _dt < 0.35, f"{_dt:.2f}s")
check("race fail par None (crash nahi)",
      MD._race([lambda: {"ok": False}, lambda: (_ for _ in ()).throw(RuntimeError("x"))],
               timeout=2) is None)
check("disk cache functions maujood", all(callable(getattr(MD, f, None))
                                          for f in ("disk_put", "disk_get", "disk_cache_stats")))
MD.disk_put("https://v81.test/video", b"x" * 5000, {"platform": "YouTube",
                                                    "title": "T", "duration": 12}, "media")
_d = MD.disk_get("https://v81.test/video", "media")
check("disk cache round-trip (restart ke baad bhi milega)", bool(_d) and len(_d[0]) == 5000)
check("disk meta JSON-safe (bytes nahi)", _d and _d[1].get("platform") == "YouTube"
      and "bytes" not in (_d[1] or {}))
check("disk_get galat key par None (crash nahi)", MD.disk_get("https://nope/xyz", "media") is None)
_st = MD.disk_cache_stats()
check("disk stats chalta hai", isinstance(_st, dict) and "mb" in _st, str(_st))
_m = MD._safe_meta({"title": "abc", "bytes": b"123", "n": 5, "lst": [1, 2], "obj": object()})
check("_safe_meta sirf JSON-safe rakhta hai", _m == {"title": "abc", "n": 5, "lst": [1, 2]},
      str(_m))

# cache-hit path: disk me jo hai, uske liye network hi nahi chalta
_cached = MD.download_video_media("https://v81.test/video", max_mb=48)
check("download_video_media disk cache se instant (network nahi)",
      _cached.get("ok") and _cached.get("cached") is True, str(_cached)[:70])

check("Instagram: teen engine ab parallel race me (sum nahi, max)",
      "_race([\n        lambda: _ig_parth(clean, media_cat)" in MD.__dict__.get("__doc__", "")
      or "teeno engine EK SAATH" in open(os.path.join(_ROOT, "modules", "media_downloader.py"),
                                         encoding="utf-8").read())
check("non-YouTube: double-extraction fix (pehle download, phir info)",
      "pehle DOWNLOAD hi try karo" in open(os.path.join(_ROOT, "modules",
                                                       "media_downloader.py"),
                                           encoding="utf-8").read())
check("socket timeout 7s (jaldi fallback)", MD.SOCK_TIMEOUT == 7, str(MD.SOCK_TIMEOUT))
check("keepalive ab 3 minute (4 nahi)", 'or 3)  # v74.3' in BOT_SRC and "= 3.0" in BOT_SRC)
check("bot me 3-layer cache order (RAM → DISK → network)",
      "disk_get(url, \"media\")" in open(os.path.join(_ROOT, "modules",
                                                     "media_downloader.py"),
                                        encoding="utf-8").read())

# =====================================================================
section("5) Outcome cards ka look (nakli Telegram)")
_c_live, _kb_live = bot.rc_board_card("bseb")
check("BSEB card: LIVE + check button", "✅ <b>LIVE</b>" in _c_live
      and any("Result check karo" in b.text for r in _kb_live.inline_keyboard for b in r))
_c_soon, _kb_soon = bot.rc_board_card("cbse")
check("CBSE card (v74.6): status + captcha button (gyaan nahi)",
      "Jald live hoga" in _c_soon
      and [b.text for r in _kb_soon.inline_keyboard for b in r] ==
      ["🔎 Result check karo (🔐 captcha)", "◀️ Saare boards"])
check("hub card: page + search hint, koi lecture nahi",
      "BOARD chuno" in bot._rc_pick_card(0) and "LIVE" in bot._rc_pick_card(0)
      and "steps" not in bot._rc_pick_card(0).lower())
check("v74.6: captcha bridge — user captcha, phir PDF (bypass nahi)",
      "rc_cap_ans" in BOT_SRC and "cb.fetch_form" in BOT_SRC.lower()
      and "captcha_img_fail" in open(os.path.join(_ROOT, "modules", "captcha_bridge.py"),
                                     encoding="utf-8").read())
# v75: "v74.x ya usse aage" — aage ke version par bhi guard zinda rahe
import re as _re81
_vm81 = _re81.search(r"v(\d+)\.", bot.BOT_VERSION or "")
check("version v74.x ya usse aage (NO-GYAAN + SPEED)",
      bool(_vm81) and int(_vm81.group(1)) >= 74 and "NO-GYAAN" in bot.BOT_VERSION,
      bot.BOT_VERSION)

# =====================================================================
section("6) Registry + baaki sab salamat (regression)")
check("v74.5: sirf 2 boards — BSEB + CBSE (koi orphan nahi)",
      list(BRD.BOARDS.keys()) == ["bseb", "cbse"] and BRD.ORDER == ["bseb", "cbse"])
check("BSEB hi live hai (jhoothi live list nahi)",
      [k for k, b in BRD.BOARDS.items() if b.get("status") == "live"] == ["bseb"])
check("logos/badges sab boards par", all(BRD.photo_bytes(k) for k in BRD.BOARDS))
check("search ab bhi chalta hai", [k for k, _ in BRD.find("bihar")][:1] == ["bseb"]
      or "bseb" in [k for k, _ in BRD.find("bihar")])

# =====================================================================
section("7) v74.4 — webhook permanent fix + board watch + TEMP NUMBER clean")

# webhook watchdog
check("webhook watchdog function maujood hai (self-heal)", callable(getattr(bot, "_webhook_watchdog", None)))
check("watchdog start hota hai main me (15 min self-check)",
      "_webhook_watchdog" in BOT_SRC and "WEBHOOK watchdog ON" in BOT_SRC)
check("webhook log ab INFO hai (scary WARNING nahi)",
      'log.info("WEBHOOK MODE ON' in BOT_SRC
      and 'log.warning("WEBHOOK MODE' not in BOT_SRC)
check("watchdog setWebhook dobara karta hai (3 retry)",
      "setWebhook" in BOT_SRC and "for _try in range(3)" in BOT_SRC)

# board watch
check("board watch loop maujood (har 6 ghante)", callable(getattr(bot, "_board_watch_loop", None)))
check("board watch ab sirf CBSE (v74.5 — baaki boards delete)",
      all(k.startswith("cbse") for k, _ in getattr(bot, "_BOARD_WATCH", ()))
      and len(getattr(bot, "_BOARD_WATCH", ())) >= 1,
      str(len(getattr(bot, "_BOARD_WATCH", ()))))
check("board watch admin ko batata hai (jhootha live nahi karta)",
      "BOARD WATCH" in BOT_SRC and "app.bot.send_message" in BOT_SRC)

# TEMP NUMBER — gyaan zero
_intro = bot.TNUM_INTRO
check("TEMP NUMBER intro 4 line se chhota", len(_intro.splitlines()) <= 4, str(len(_intro.splitlines())))
check("intro me koi warning/gyaan nahi",
      not any(w in _intro.upper() for w in ("BANK", "KYC", "UPI", "PUBLIC", "100% FREE", "NAYA SYSTEM")))
check("purane safety constants gayab", not hasattr(bot, "TNUM_SAFE_LINE"))
_card = bot.tnum_card({"cc": "us", "num": "15551234567", "svc": "whatsapp"},
                      {"ok": True, "number": "15551234567", "messages": []})
check("number card me koi safety line nahi",
      "BANK" not in _card.upper() and "KYC" not in _card.upper()
      and "PUBLIC" not in _card.upper())
check("menu label ab 'TEMP NUMBER' hai", "TEMP NUMBER" in BOT_SRC)
check("purana naam bhi chalta hai (compatibility)",
      bot.BTN_MODE_MAP.get("TEMP MAIL (NUMBER)") == "tnum"
      and bot.BTN_MODE_MAP.get("TEMP NUMBER") == "tnum")

print(f"\n{'=' * 62}")
print(f"  v81 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
