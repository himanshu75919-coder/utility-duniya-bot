# -*- coding: utf-8 -*-
"""
v100 SELFTEST — 👪 FAMILY-INFO (Aadhaar → ration family card + sakht Aadhaar mask)
- NAYA premium tool: familyinfo (38th tool, 44th prompt) — purane 37 tools + 43 prompts intact
- Aadhaar KABHI poora nahi: na card, na error, na API ka 6-digit mask — sirf XXXX-XXXX-last4
- Live API test NAHI (slow/network) — captured fixtures + typo-gate timing se saboot
"""
import re
import sys
import time

sys.path.insert(0, ".")

import bot as B  # noqa: E402
from modules import familyinfo_api as F  # noqa: E402

PASS, FAIL = 0, 0


def ok(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label} {extra}")


def section(t):
    print(f"\n== {t} ==")


BOT_SRC = open("bot.py", encoding="utf-8").read()
FAM_SRC = open("modules/familyinfo_api.py", encoding="utf-8").read()

# Captured fixture (live API, 9 Oct 2026) — demo key ka record
HIT = {"success": True, "tool": "familyinfo",
       "data": {"card_number": "10040050016014100150", "card_type": "PHH",
               "aadhaar_mask": "401****849", "statedist": "BIHAR / SITAMARHI",
               "fps_id": "120600100966", "fps_name": "120600100966",
               "family_count": "5",
               "full_address": "0150,VILL-BELAKHURD,PS-PARIHAR,PAN-BELA,SITAMARHI",
               "name": "MONU KUMAR", "member_id": "10040011116014110006",
               "ekyc_status": "VERIFIED ✅",
               "name_": "SANJAY SAH", "member_id_": "10040011116014110007",
               "ekyc_status_": "VERIFIED ✅",
               "name__": "ADARSH RAJ", "member_id__": "10040011116014110008",
               "ekyc_status__": "VERIFIED ✅",
               "name___": "CHANCHALA DEVI", "member_id___": "10040011116014110009",
               "ekyc_status___": "VERIFIED ✅",
               "name____": "ANSHU KUMARI", "member_id____": "10040011116014110010",
               "ekyc_status____": "VERIFIED ✅",
               "generated": "09 Oct 2026, 04:06:12 PM"},
       "raw": "👪 Family Info Found Successfully ..."}
MISS = {"success": True, "tool": "familyinfo",
        "data": {"family_info_not_found_for": "123456789012"},
        "raw": "✖️ Family Info Not Found for: 123456789012"}
QUERY = "401635555849"   # fixture wala demo Aadhaar

section("1) module + unit helpers (no network)")
ok("familyinfo_api import + __all__", hasattr(F, "lookup") and "lookup" in F.__all__)
ok("is_configured() True (built-in)", F.is_configured() is True)
ok("mask XXXX-XXXX-5849", F.mask_aadhar12(QUERY) == "XXXX-XXXX-5849")
ok("mask junk → khali", F.mask_aadhar12("12345") == "" and F.mask_aadhar12(None) == "")
ok("Verhoeff: sahi Aadhaar pass", F.verhoeff_ok(QUERY) is True)
ok("Verhoeff: typo/galat fail",
   F.verhoeff_ok("401635555848") is False and F.verhoeff_ok("999999999999") is False
   and F.verhoeff_ok("12345") is False)
ok("space wala Aadhaar → 12 digit", F._digits12("4016 3555 5849") == QUERY)

section("2) parse fixtures (captured, no network)")
_hit = F.parse_payload(HIT, 9000, QUERY)
ok("HIT ok + source famapi", _hit.get("ok") is True and _hit.get("source") == "famapi")
ok("card + type + state + fps", _hit.get("card_number") == "10040050016014100150"
   and _hit.get("card_type") == "PHH" and _hit.get("state_dist") == "BIHAR / SITAMARHI"
   and _hit.get("fps") == "120600100966", str({k: _hit.get(k) for k in ("card_number", "card_type")}))
ok("5 members + eKYC normalized", len(_hit.get("members") or []) == 5
   and all(m.get("ekyc") == "✅ Verified" for m in _hit["members"])
   and _hit["members"][0]["name"] == "MONU KUMAR")
ok("MISS → not_found Hindi", F.parse_payload(MISS, 9000, "123456789012").get("not_found") is True)
ok("junk/empty → not_found", F.parse_payload({}, 0, QUERY).get("not_found") is True
   and F.parse_payload({"success": True, "data": {}}, 0, QUERY).get("not_found") is True
   and F.parse_payload(None, 0, QUERY).get("ok") is False)

section("3) 🔐 AADHAAR LEAK-LOCK (poora number kahin nahi)")
_card = B.familyinfo_card(_hit, "LIVE", 9000)
ok("parse-output me poora Aadhaar NAHI", QUERY not in str(_hit))
ok("API ka 6-digit mask bhi NAHI (401****849)", "401****849" not in str(_hit))
ok("card me poora Aadhaar NAHI", QUERY not in _card)
ok("card me 6-digit mask bhi NAHI", "401****849" not in _card)
ok("card me SAKHT mask HAI", "XXXX-XXXX-5849" in _card)
ok("typo/junk error me input ECHO nahi",
   "401635555848" not in str(F.lookup("401635555848"))
   and "12345" not in str(F.lookup("12345")))
ok("module me print() call nahi (key leak ka rasta hi nahi)",
   re.search(r"(?<![\w.])print\s*\(", FAM_SRC) is None)
ok("parse mask QUERY se bana (API wala ignore)", _hit.get("aadhaar_mask") == "XXXX-XXXX-5849")

section("4) typo-gate: API hit se PEHLE reject (timing proof)")
_t0 = time.time()
_typo = F.lookup("401635555848")
_typo_ms = (time.time() - _t0) * 1000
ok("typo turant reject (<3s = network gaya hi nahi)",
   _typo.get("ok") is False and _typo_ms < 3000, f"{_typo_ms:.0f}ms")
ok("typo error Hindi + masked-hint", "12-digit" in str(_typo.get("error")))

section("5) wiring: premium tool (v101: 30 tools)")
ok("PREMIUM_TOOLS 29 (v102: kagaz gaya)", len(B.PREMIUM_TOOLS) == 29, str(len(B.PREMIUM_TOOLS)))
ok("familyinfo member", "familyinfo" in B.PREMIUM_TOOLS)
ok("naam '👪 Family Info'", B.PREMIUM_TOOL_NAMES.get("familyinfo") == "👪 Family Info")
ok("rate-limit (10,60,'Family Info')",
   B.TOOL_RATE_LIMITS.get("familyinfo") == (10, 60, "Family Info"))
ok("BTN map FAMILY INFO → familyinfo", B.BTN_MODE_MAP.get("FAMILY INFO") == "familyinfo")
_labels = [[B.unbold(c).upper() for c in row] for row in B.KB_BTNS]
_flat = [c for row in _labels for c in row]
ok("keyboard me FAMILY INFO button", any("FAMILY INFO" in c for c in _flat))
ok("keyboard me FAMILY INFO sirf EK baar", sum(1 for c in _flat if "FAMILY INFO" in c) == 1)
_fam_row = next(i for i, row in enumerate(_labels) if any("FAMILY INFO" in c for c in row))
_num_row = next(i for i, row in enumerate(_labels) if any("NUMBER INFO" in c for c in row))
ok("FAMILY+NUMBER ek hi top row (v101)", _fam_row == _num_row == 0, f"num={_num_row} fam={_fam_row}")
ok("top row 2-button horizontal (v101)", len(_labels[_num_row]) == 2
   and "NUMBER INFO" in _labels[_num_row][0])
ok("mode handler maujood", 'if mode == "familyinfo":' in BOT_SRC)
ok("credit-gate + spend wiring",
   'get_credits_over_text("familyinfo")' in BOT_SRC
   and 'spend_credit_msg(uid, "familyinfo")' in BOT_SRC
   and 'tel_note("familyinfo"' in BOT_SRC)

section("6) prompt: 37 (36 purane + familyinfo; v101 me 7 gaye)")
ok("PROMPT_DATA 34 (v102)", len(B.PROMPT_DATA) == 34, str(len(B.PROMPT_DATA)))
_fe = B.PROMPT_DATA.get("familyinfo") or {}
ok("entry head/ask/ex", _fe.get("head") == "👪 FAMILY INFO"
   and "12-digit Aadhaar" in str(_fe.get("ask")) and bool(_fe.get("ex")))
ok("rendered prompt me ask + example",
   "12-digit Aadhaar number bhejein" in B.tool_prompt("familyinfo")
   and "401635555849" in B.tool_prompt("familyinfo"))
ok("rendered prompt me banned words NAHI",
   not [w for w in ("cancel", "Credits:", "💡", "Tip:", "credit") if w in B.PROMPTS["familyinfo"]])
ok("PROMPTS == PROMPT_DATA (34)", len(B.PROMPTS) == len(B.PROMPT_DATA) == 34)
ok("tutorial me FAMILY INFO line", "👪 FAMILY INFO → Aadhaar bhejo" in BOT_SRC)

section("7) 🛡️ purane tools GUARD (cher-chaar nahi)")
_ni = B.PROMPT_DATA.get("numinfo") or {}
ok("numinfo prompt EXACT (head/ask/ex/tip/foot)",
   _ni.get("head") == "📱 NUMBER INFO V2 ENGINE"
   and _ni.get("ask") == "10 Digit Number bhejein:"
   and _ni.get("ex") == [('7857843092', '10 digit ka mobile number')]
   and _ni.get("tip") == '+91 ya 0 pehle lagane ki zaroorat nahi — seedha 10 digit bhejo'
   and _ni.get("foot") == 'Circle · operator · owner card')
ok("numinfo wiring intact", 'if mode == "numinfo":' in BOT_SRC
   and "from modules import mynum_api as mynum" in BOT_SRC
   and "numinfo" in B.PREMIUM_TOOLS)
ok("purane heads intact (imei/ifsc/qr/vahan)",
   "IMEI V2" in B.PROMPT_DATA["imei"]["head"]
   and "IFSC" in B.PROMPT_DATA["ifsc"]["head"]
   and B.PROMPT_DATA["qr_scan"]["head"] == "📷 QR SCANNER"
   and "RC + CHALLAN" in B.PROMPT_DATA["vahan"]["head"])
ok("33 purane keys maujood (v102: 3 aur gaye)",
   len([k for k in B.PROMPT_DATA if k != "familyinfo"]) == 33)
ok("28 purane premium tools sab maujood (v102: kagaz gaya)",
   len([t for t in B.PREMIUM_TOOLS if t != "familyinfo"]) == 28)

section("8) version history")
ok("BOT_VERSION v103 head", B.BOT_VERSION.startswith("v103.0 IG-PRO"),
   B.BOT_VERSION[:40])
ok("v100 tag history me", "v100.0 FAMILY-INFO" in B.BOT_VERSION)
ok("v99 full-tag history me", "v99.0 MYNUM-API — 📱 purane number API delete" in B.BOT_VERSION)
ok("v98 ab bare (compress)", "| v98.0 |" in B.BOT_VERSION)

print(f"\nSELFTEST v100 familyinfo: {PASS} pass, {FAIL} fail")
sys.exit(1 if FAIL else 0)
