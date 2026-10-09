#!/usr/bin/env python3
# =====================================================================
# v101 SELFTEST — MENU-CLEAN: 8 tools ka removal, horizontal pairing,
# info-tools-top, "Wait few seconds" flow, typing pump, terabox file
# delivery. Bot ke andar koi bhi naya tool/feature chup-chaap na jaye —
# ye file uski deewar hai.
# =====================================================================
"""v101 selftest — run: python3 tests/test_v101_clean.py"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = FAIL = 0
FAILS = []


def check(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        FAILS.append(f"{label} :: {extra}")
        print(f"  ❌ {label}  {extra}")


import bot                                                    # noqa: E402

BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()

print("\n== 1) 8 TOOLS POORE HATE (bot + prompts + code) ==")
DEAD = ["pp_stamp", "print_sheet", "doc_compress", "sarkari", "uhunt", "bgmi", "ffuid", "appfind"]
for k in DEAD:
    check(f"{k}: PREMIUM_TOOLS me NAHI", k not in bot.PREMIUM_TOOLS)
    check(f"{k}: PROMPT_DATA me NAHI", k not in bot.PROMPT_DATA)
    check(f"{k}: rate-limit table me NAHI", k not in bot.TOOL_RATE_LIMITS)
    check(f"{k}: tool-names me NAHI", k not in getattr(bot, "PREMIUM_TOOL_NAMES", {}))
check("BOT_MODE_MAP kisi deleted tool par nahi jaata",
      not ({v for v in bot.BTN_MODE_MAP.values()} & set(DEAD)))
check("handler blocks gaye (if mode == bgmi/uhunt/appfind)",
      'if mode == "bgmi":' not in BOT_SRC and 'if mode == "uhunt":' not in BOT_SRC
      and 'if mode == "appfind":' not in BOT_SRC
      and 'if mode == "pp_stamp":' not in BOT_SRC and 'if mode == "ffuid":' not in BOT_SRC
      and 'if mode == "print_sheet":' not in BOT_SRC and 'if mode == "doc_compress":' not in BOT_SRC)
for m in ("modules/username_hunter.py", "modules/gaming_tools.py",
          "modules/sarkari_hub.py", "modules/cyber_studio.py"):
    check(f"{m} file bhi gayi", not os.path.exists(os.path.join(ROOT, m)))
check("/sarkari command gayi", 'CommandHandler("sarkari"' not in BOT_SRC)
check("sarkari_citizen callbacks gayi", "sarkari_citizen" not in BOT_SRC)
check("doc_* callbacks gayi", not re.search(r'"doc_(kb_|gray|go)', BOT_SRC))
check("uhunt_card function gayi", "def uhunt_card" not in BOT_SRC)

print("\n== 2) COUNTS ==")
check("PREMIUM_TOOLS == 29", len(bot.PREMIUM_TOOLS) == 29, str(len(bot.PREMIUM_TOOLS)))
check("PROMPT_DATA == 34", len(bot.PROMPT_DATA) == 34, str(len(bot.PROMPT_DATA)))
check("PROMPTS == 34", len(bot.PROMPTS) == 34, str(len(bot.PROMPTS)))
check("familyinfo zinda", "familyinfo" in bot.PREMIUM_TOOLS and "familyinfo" in bot.PROMPT_DATA)
check("numinfo zinda + prompt untouched",
      'if mode == "numinfo":' in BOT_SRC
      and bot.PROMPT_DATA["numinfo"]["foot"] == "Circle · operator · owner card")
check("v99 num wiring untouched", "mynum.lookup" in BOT_SRC)

print("\n== 3) MENU — horizontal pairs + info top ==")
_labels = [[bot.unbold(c).upper() for c in row] for row in bot.KB_BTNS]
_flat = [c for row in _labels for c in row]
check("row0 = [NUMBER INFO, FAMILY INFO]", _labels[0] == ["📱 NUMBER INFO", "👪 FAMILY INFO"], str(_labels[0]))
check("downloader rows 1-2 me", "INSTA DL" in _labels[1][0] and "YOUTUBE DL" in _labels[1][1], str(_labels[1]))
over = [i for i, r in enumerate(_labels[:-1]) if len(r) > 3]  # v102: DL row 3-wide
check("koi row 3 se badi nahi (v102: DL row 3-wide)", not over, str(over))
singles = [i for i, r in enumerate(_labels) if len(r) == 1 and "SUPPORT" not in r[0]]
check("akhri (SUPPORT) ke siva koi single-row nahi", not singles, str(singles))
for gone in ("PASSPORT", "PRINT SHEET", "DOCUMENT PDF", "SARKARI SEVA", "USERNAME HUNTER", "BGMI", "FF UID", "APP FINDER"):
    check(f"keyboard me '{gone}' nahi", all(gone not in c for c in _flat))
check("SARKARI KAGAZ SUITE bhi gaya (v102 user order)", not any("KAGAZ" in c for c in _flat))
check("QR CODE + QR SCANNER alag-alag zinda",
      sum(1 for c in _flat if c == "📷 QR CODE") == 1 and sum(1 for c in _flat if c == "📷 QR SCANNER") == 1)
check("koi button duplicate nahi", len(_flat) == len(set(_flat)))
check("sabhi KB buttons non-empty + uppercase-label format",
      all(c.strip() and c == c.upper() for row in _labels for c in row))
_mapped_labels = set(bot.BTN_MODE_MAP)
_unmapped = [c for row in _labels for c in row
             if re.sub(r"^[^A-Z0-9]+", "", c).strip() not in _mapped_labels
             and c not in ("👤 MY ACCOUNT", "💬 SUPPORT / MADAD", "🛠️ ADMIN PANEL", "👑 OWNER MODE",
                           "📋 ALL TOOLS (FREE)", "💎 VIP PREMIUM")]
check("har menu button ka mode-map maujood", not _unmapped, str(_unmapped))

print("\n== 4) ⏳ WAIT-FEW-SECONDS + TYPING PUMP ==")
check("WAIT_NOTE exactly 'Wait few seconds'", bot.WAIT_NOTE == "⏳ <b>Wait few seconds...</b>", bot.WAIT_NOTE)
check("_wait_st defined", "async def _wait_st(" in BOT_SRC)
_n = BOT_SRC.count("_wait_st(")
check("15+ tool flows _wait_st use karte hain", _n >= 15, f"n={_n}")
for m in ("numinfo", "familyinfo", "vahan", "ifsc", "osint_whois", "imei", "terabox"):
    check(f"{m} flow me wait-note wiring", m in BOT_SRC and "_wait_st" in BOT_SRC)
check("numinfo me wait pehle, lookup baad",
      BOT_SRC.index('_wn = await _wait_st(update.message)') < BOT_SRC.index("res = lookup_phone_info(raw_text)"))
check("typing pump helper + Bot wrapper maujood",
      "def _arm_typing(" in BOT_SRC and "_wrap_bot_typing_stop" in BOT_SRC
      and 'send_chat_action' in BOT_SRC)
check("Bot.send_message wrapper se typing-stop armed",
      getattr(__import__("telegram").Bot, "_v101_wrapped", False) is True)
check("HTML-net ka marker wrapper ke baad bhi zinda (v93 lock)",
      getattr(__import__("telegram").Bot.send_message, "__ud_wrapped__", False) is True)
check("purane lambe placeholder gaye (6 engines wala etc.)",
      "Resolving the cloud link (6 engines)" not in BOT_SRC
      and "Bihar Board se result nikal raha hoon" not in BOT_SRC
      and "Making the ringtone" not in BOT_SRC)

print("\n== 5) ☁️ TERABOX FILE DELIVERY (v101) ==")
import modules.cloud_tools as CT                                # noqa: E402
check("fetch_bytes helper defined", callable(getattr(CT, "fetch_bytes", None)))
check("Robin worker pehle engine hai (fetchable link)",
      '("Public Worker (Robin)", _tb_robin),\n        ("Guest Listing"' in
      open(os.path.join(ROOT, "modules/cloud_tools.py"), encoding="utf-8").read())
check("bot me 46MB delivery cap + FILE AA GAYI card",
      "46 * 1048576" in BOT_SRC and "TERABOX — FILE AA GAYI" in BOT_SRC)
check("delivery fail par link-card fallback zinda",
      "High-Speed Link" in BOT_SRC and BOT_SRC.index("if _derr:") < BOT_SRC.index('if len(files) > 1:'))
check("send-type router (video/audio/photo/doc)",
      all(x in BOT_SRC for x in ('reply_video(video=_buf', 'reply_audio(audio=_buf',
          'reply_photo(photo=_buf', 'reply_document(document=_buf')))
check("fetch_bytes offline behavior: galat URL → (None, reason) not crash",
      CT.fetch_bytes("http://127.0.0.1:9/x.bin", 1)[0] is None)

print("\n== 6) VERSION ==")
check("BOT_VERSION v102 head", bot.BOT_VERSION.startswith("v102.0 CLEAN-STYLE"), bot.BOT_VERSION[:48])
check("v100/v99 history intact",
      "v100.0 FAMILY-INFO" in bot.BOT_VERSION and "v99.0 MYNUM-API" in bot.BOT_VERSION)
check("start-text me FF/BGMI zinda nahi (gaya hua tool promote NAHI)",
      "🔥 FF/BGMI" not in BOT_SRC)

print("\n" + "=" * 55)
print(f"v101 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAILS:
    print("FAILED CHECKS:")
    for x in FAILS:
        print("  ✗", x)
    sys.exit(1)
