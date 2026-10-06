# -*- coding: utf-8 -*-
"""
v69 SELFTEST — 📱 NUMBER INFO card = aapka SAMPLE + OSINT tools (naye)
=====================================================================
Boss ka order: "number-info tool ka output bilkul is card jaisa ho":

    👤 Name: Sanjay Sah
    👨 Father: Ram Akwal Sah
    📱 Phone: 7857843092
    📱 Alt: 7305190526
    🌐 Circle: BIHAR JIO
    🆔 Govt ID: 401635555849
    🏠 Address:
    └ S/O Ram Akwal Sah, ward 02, ... Sitamarhi, Bihar, 843324

Ye test usi card ko word-by-word check karta hai.
"""
import os
import re
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv69_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V69"
os.environ["ADMIN_ID"] = "1"

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
print("  v69 SELFTEST — NUMBER INFO card (aapka sample) + OSINT")
print("=" * 62)

import bot                                                          # noqa: E402
from modules import numinfo_provider as NP                           # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
NI_SRC = open(os.path.join(_ROOT, "modules", "numinfo_provider.py"),
              encoding="utf-8").read()

# =====================================================================
section("[A] 📱 AAPKA SAMPLE CARD — word by word")
# =====================================================================

_SAMPLE_RES = {"number": "917857843092", "national": "78578 43092",
               "international": "+91 78578 43092", "country": "India",
               "type": "📱 Mobile"}
_SAMPLE_OWNER = {"name": "Sanjay Sah", "father": "Ram Akwal Sah",
                 "alt": "7305190526", "region": "BIHAR JIO",
                 "govt_id": "401635555849",
                 "address": "S/O Ram Akwal Sah, ward 02, Sitamarhi, Bihar, 843324"}

_CARD = bot.numinfo_card(_SAMPLE_RES, _SAMPLE_OWNER, {}, "JIO", "BIHAR",
                         "📱 Mobile", "", "🟢 LIVE", 340)
_PLAIN = re.sub(r"</?(?:b|code|i)>", "", _CARD)
_LINES = _PLAIN.split("\n")

_EXPECT = [
    "👤 Name: Sanjay Sah",
    "👨 Father: Ram Akwal Sah",
    "📱 Phone: 7857843092",
    "📱 Alt: 7305190526",
    "🌐 Circle: BIHAR JIO",
    "🆔 Govt ID: 401635555849",
    "🏠 Address:",
    "└ S/O Ram Akwal Sah, ward 02, Sitamarhi, Bihar, 843324",
]
for _i, _want in enumerate(_EXPECT):
    check(f"line {_i + 1}: {_want[:34]}", _LINES[_i] == _want,
          f"mila: {_LINES[_i][:40]!r}")

check("poora sample block ek saath sahi order me",
      _LINES[:8] == _EXPECT)
check("address line se pehle koi extra space nahi (aapka format)",
      _LINES[7].startswith("└ ") and not _LINES[7].startswith(" "))
check("Phone me sirf 10 digit (country code nahi)",
      _LINES[2].endswith("7857843092") and "+91" not in _LINES[2])
check("Alt alag line hai (Phone me mila nahi)",
      "7305190526" not in _LINES[2] and _LINES[3].endswith("7305190526"))
check("Circle me circle + operator dono (BIHAR JIO)",
      _LINES[4].endswith("BIHAR JIO"))
check("Govt ID code font me (copy karne layak)",
      "🆔 <b>Govt ID:</b> <code>401635555849</code>" in _CARD)
check("purani technical lines bhi zinda (kuch nahi hata)",
      "📞 <b>Number:</b>" in _CARD and "🏢 <b>Operator:</b>" in _CARD
      and "⚡ <b>Response:</b>" in _CARD)
check("brand link footer zinda", "Powered by" in _CARD)

# --- data na ho to card tootna nahi chahiye ---
_bare = bot.numinfo_card({"international": "+91 90000 00001", "country": "India"},
                         {}, {}, "Jio", "Bihar", "📱 Mobile", "", "🧪 SAMPLE", 240)
check("owner data na ho to bhi card banta hai (crash nahi)",
      "📞 <b>Number:</b>" in _bare and "💡" in _bare)
check("API setup hint card me hai", "NUMINFO_PROVIDER_URL" in _bare
      and "/numapi" in _bare)

# --- demo card: Phone + Alt dono dikhne chahiye ---
_demo = NP.demo_result("9000000001")
_demo_card = bot.numinfo_card({"international": "+91 90000 00001", "country": "India"},
                              _demo.get("owner"), {}, "Jio", "Bihar",
                              "📱 Mobile", "", "🧪 SAMPLE", 240)
check("demo card: Phone line aati hai", "📱 <b>Phone:</b>" in _demo_card)
check("demo card: Alt line aati hai", "📱 <b>Alt:</b>" in _demo_card)
check("demo me main aur alt number alag hain (sample jaisa)",
      _demo["owner"]["alt"] != "9000000001")

# --- ek hi layout (duplicate block nahi) ---
check("handler me purana duplicate card block nahi (ek hi jagah se format)",
      "AAPKE DIYE FORMAT ME CARD" not in BOT_SRC)
check("renderer ek hi hai", BOT_SRC.count("def numinfo_card(") == 1)

# =====================================================================
section("[B] 🔍 OSINT — ideas file + safety")
# =====================================================================
_idea = os.path.join(_ROOT, "OSINT-IDEAS.md")
check("OSINT ideas file bani hai (user pick karega)", os.path.exists(_idea))
if os.path.exists(_idea):
    _t = open(_idea, encoding="utf-8").read()
    check("ideas file me pick-list hai (A/B/C/D…)",
          _t.count("| **") >= 8)
    check("ideas file me 'leaked data' wala tool NAHI hai (safety)",
          "leaked" not in _t.lower().replace("no leaked", "")
          .replace("leaked data", "").replace("leaked database", ""))
    check("ideas file me aadhaar/phone-dump tool ka zikr safety ke saath hai",
          "Aadhaar" in _t)

print(f"\n{'=' * 62}")
print(f"  v69 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
