#!/usr/bin/env python3
# =====================================================================
# v102 SELFTEST — 🎨 OSINT-style CLEAN LOOK + 🚫 4 TOOLS PERMANENT DELETE
#
# User ke 4 orders (v102):
#  1) Fonts waise hi jaise OSINT Lookup bot ke — plain clean, bold-unicode
#     band; saare tools + menus. Data/flows SAME.
#  2) Family info card: proper spacing + ━ separators, faaltu member-id
#     codes nahi — "best design".
#  3) "har tools use karne se phle support seedha message karo" — ye text
#     SAARE jagah se remove; username sirf RESULT ke end me (ek baar).
#  4) 4 tools PERMANENTLY delete: 📋 ALL TOOLS (FREE), 📜 SARKARI KAGAZ
#     SUITE, 📘 FACEBOOK DL, 💬 CHAT X-RAY (modules/chat_xray.py bhi gaya).
#
# Run:  python3 tests/test_v102_clean.py
# =====================================================================
import re
import sys
import os                                                      # noqa: E402
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
FAIL = []


def check(name, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + name + (("  " + str(extra)) if (not cond and extra) else ""))
    if not cond:
        FAIL.append(name)


import bot as B                                               # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

print("\n== 1) 🎨 FONT COPY — OSINT Lookup jaisa plain ==")
check("to_bold pass-through (bold-unicode NAHI banata)", B.to_bold("FAMILY INFO") == "FAMILY INFO")
check("unbold helper zinda (backward compat)", B.unbold("FAMILY") == "FAMILY")
_b = re.compile(r"[\U0001D400-\U0001D7FF]")
_cells = [c for r in B.KB_BTNS for c in r]
check("KB buttons me koi bold-unicode character nahi", not any(_b.search(c) for c in _cells))
check("saare KB buttons uppercase + emoji-prefix (OSINT style)",
      all(c.strip() and c == c.upper() for c in _cells))
check("PROMPTS me bold-unicode nahi (plain + HTML <b>)",
      not any(_b.search(v) for v in B.PROMPTS.values() if v))
check("PCARD_TOP/BOT box khatam (empty string)", B.PCARD_TOP == "" and B.PCARD_BOT == "")
check("PCARD_MID = ━ divider (OSINT rule style)", set(B.PCARD_MID) == {"━"} and len(B.PCARD_MID) >= 16)
_t = B.pcard_title("📱", "DEMO CARD")
check("card header = icon + <b>TITLE</b> + ━ (box nahi)",
      _t.startswith("📱 <b>DEMO CARD</b>") and "━" in _t and "┏" not in _t and "┃" not in _t)

print("\n== 2) 🚫 4 TOOLS PERMANENTLY DELETE (user order) ==")
_dead = {"kagaz": "SARKARI KAGAZ SUITE", "cxray": "CHAT X-RAY",
         "alltools": "ALL TOOLS (FREE)", "dl_facebook": "FACEBOOK DL"}
for k, label in _dead.items():
    check(f"{label}: PROMPTS se gaya", k not in B.PROMPTS)
    check(f"{label}: PROMPT_DATA se gaya", k not in B.PROMPT_DATA)
    check(f"{label}: PREMIUM_TOOLS se gaya", k not in B.PREMIUM_TOOLS)
    check(f"{label}: BTN_MODE_MAP se gaya", k not in set(B.BTN_MODE_MAP.values()))
check("keyboard me Kagaz/X-Ray/ALLTOOLS/Facebook-DL button nahi",
      not any(x in c.upper() for c in _cells for x in ("KAGAZ", "CHAT X-RAY", "ALL TOOLS", "FACEBOOK")))
check("FACEBOOK DOWNLOADER site delete (sirf 3 DL_SITES)",
      set(B.DL_SITES) == {"instagram", "youtube", "tiktok"})
check("DL_POPULAR me facebook nahi", "facebook" not in B.DL_POPULAR)
check("modules/chat_xray.py file bhi gayab",
      not os.path.exists(os.path.join(_ROOT, "modules", "chat_xray.py")))
check("bot.py me chat_xray import nahi bacha", "chat_xray" not in BOT_SRC.split("\n\n\n")[0] + BOT_SRC)
for fn in ("kagaz_menu_kb", "kagaz_ask_next", "all_tools_text", "free_mode_kb", "cxray_caption"):
    check(f"helper {fn}() bhi module se gaya", not hasattr(B, fn))

print("\n== 3) 📩 SUPPORT-NAG SAARE JAGAH SE HATA ==")
check("tool_support_kb() ab None deta hai", all(B.tool_support_kb(k) is None for k in B.PROMPT_DATA))
check("'support ko message karo' type line prompt me nahi",
      not any("seedha message" in v for v in B.PROMPTS.values() if v))
check("HELP_NOTICE compact — 'Poori list'/support-nag lines nahi",
      "Poori list" not in B.HELP_NOTICE and "ALL TOOLS" not in B.HELP_NOTICE
      and "seedha message" not in B.HELP_NOTICE)
check("tool prompt me username signature sirf RESULT footer (BRAND_LINK) ke through",
      "Powered" in B.BRAND_LINK or "t.me" in B.BRAND_LINK)

print("\n== 4) 👪 FAMILY INFO CARD — spacing + ━ + no id-junk ==")
_fake = {
    "aadhaar_mask": "1234****9012",
    "card_number": "1002223344556", "card_type": "PHH",
    "state_dist": "Bihar / Patna", "fps": "FPS 12345", "family_count": 2,
    "address": "123 Test Road, Sample Area, Patna, Bihar - 800001",
    "members": [
        {"name": "PARENT ONE", "ekyc": "✅ Verified"},
        {"name": "CHILD TWO", "ekyc": ""},
    ],
}
_card = B.familyinfo_card(_fake, "public pds record", 812)
check("card me ━ divider rows hain", _card.count("━") >= 6)
check("member lines clean: NAME — ✅ Verified (koi member-id code nahi)",
      "PARENT ONE" in _card and "✅ Verified" in _card
      and "member_id" not in _card and "#1" not in _card)
check("Aadhaar SAKHT masked (12 digits kabhi nahi)",
      "123456789012" not in _card and "987654321098" not in _card and "****" in _card)
check("card me blank-line spacing hai (.OSINT style)", "\n\n" in _card)
check("footer: Source + Speed + Lookup Status + brand line",
      "Source" in _card and "Speed" in _card and "Lookup Status" in _card and "t.me" in _card)
check("address ek line me wrap nahi hota 40+ chars ke bina comma-wrap", len(_card) > 100)
check("card box-free (┏/┗ nahi)", "┏" not in _card and "┗" not in _card)

print("\n== 5) ⚖️ COUNTS + SAB PURANA INTACT ==")
check("PREMIUM_TOOLS == 29 (v101 30 - kagaz)", len(B.PREMIUM_TOOLS) == 29, str(len(B.PREMIUM_TOOLS)))
check("PROMPT_DATA == 34 (v101 37 - kagaz/cxray/dl_facebook)", len(B.PROMPT_DATA) == 34, str(len(B.PROMPT_DATA)))
check("PROMPTS == PROMPT_DATA", len(B.PROMPTS) == len(B.PROMPT_DATA))
check("keyboard 12 rows, max 3 wide, sab non-empty",
      len(B.KB_BTNS) == 12 and max(len(r) for r in B.KB_BTNS) <= 3
      and all(any(c.strip() for c in r) for r in B.KB_BTNS))
check("NUMBER INFO + FAMILY INFO pehli row", "NUMBER INFO" in _cells[0] and "FAMILY INFO" in _cells[1])
check("DL row: INSTA+YOUTUBE+TIKTOK (3 buttons)",
      sum(1 for c in _cells if c.endswith("DL")) == 3)
check("koi duplicate button nahi", len(_cells) == len(set(_cells)))
for k in ("numinfo", "familyinfo", "terabox", "vahan", "imei",
           "ifsc", "pin", "bankpdf", "mediastudio"):
    check(f"zinda tool: {k} prompt intact", k in B.PROMPTS and "━" in B.PROMPTS[k])
check("cloner + vahan (RC/CHALLAN) premium list me zinda",
      "cloner" in B.PREMIUM_TOOLS and "vahan" in B.PREMIUM_TOOLS)
check("BOT_VERSION current head (v104+)", B.BOT_VERSION.startswith("v104.0 HD-TRUTH"), B.BOT_VERSION[:40])

print("\n== RESULT ==")
if FAIL:
    print("FAILED:")
    for f in FAIL:
        print("  ❌", f)
    sys.exit(1)
print("✅ v102 saare checks pass")
