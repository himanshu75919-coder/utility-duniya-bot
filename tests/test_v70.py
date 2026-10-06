# -*- coding: utf-8 -*-
"""
v70 SELFTEST — 🌐 WEBSITE OWNER X-RAY (result BOT KE ANDAR, koi link nahi)
=========================================================================
Boss ka order: "result mere bot me aana chahiye, links saaf mana hai."
Isliye ye tool: domain ka public record (RDAP) bot KHUD laata hai aur
card me dikhata hai — user ko koi link nahi kholna padta.

Real test (sandbox me chala tha):
    bihar.gov.in → Registrar: National Informatics Centre
                   Malik: Information Technology Department Government of Bihar
                   Banaya: 18-03-2008 (18 saal purana), 163 din bache
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

_TMP = tempfile.mkdtemp(prefix="udv70_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V70"
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
print("  v70 SELFTEST — WEBSITE OWNER X-RAY (in-bot result)")
print("=" * 62)

import bot                                                          # noqa: E402
from modules import osint_tools as OT                                # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
OT_SRC = open(os.path.join(_ROOT, "modules", "osint_tools.py"), encoding="utf-8").read()

# =====================================================================
section("[A] 🌐 ENGINE — domain saaf karna + RDAP parse")
# =====================================================================

check("lookup_whois maujood hai", callable(getattr(OT, "lookup_whois", None)))
check("parse_rdap alag hai (test ke liye)", callable(getattr(OT, "parse_rdap", None)))

check("link se sirf domain nikalta hai",
      OT._clean_domain("https://www.XyzShop.in/cart?x=1") == "xyzshop.in")
check("http:// bhi chalta hai",
      OT._clean_domain("http://kisi-site.com") == "kisi-site.com")
check("sirf domain waisa hi rehta hai",
      OT._clean_domain("amazon.in") == "amazon.in")
check("khaali input par crash nahi", OT._clean_domain("") == "")

_R = OT.lookup_whois("ye koi domain nahi hai")
check("galat input par saaf error (crash nahi)", _R.get("ok") is False and "domain" in str(_R.get("error")).lower())
check("error message me example hai", "xyzshop.in" in str(_R.get("error")))

# --- asli RDAP jaisa fixture (network ke bina test) ---
_FIX = {
    "ldhName": "XYZSHOP.IN",
    "status": ["active", "client transfer prohibited"],
    "events": [
        {"eventAction": "registration", "eventDate": "2019-03-12T05:09:21.699Z"},
        {"eventAction": "expiration", "eventDate": "2027-03-12T05:09:21.699Z"},
        {"eventAction": "last changed", "eventDate": "2026-02-01T06:22:50.743Z"},
    ],
    "entities": [
        {"roles": ["registrar"],
         "vcardArray": ["vcard", [["version", {}, "text", "4.0"],
                                  ["fn", {}, "text", "GoDaddy.com, LLC"]]]},
        {"roles": ["registrant"],
         "vcardArray": ["vcard", [["version", {}, "text", "4.0"],
                                  ["fn", {}, "text", "XYZ Traders Private Limited"]]]},
    ],
    "nameservers": [{"ldhName": "NS1.HOSTINGER.COM"}, {"ldhName": "NS2.HOSTINGER.COM"}],
    "secureDNS": {"delegationSigned": False},
}
_P = OT.parse_rdap(_FIX, "xyzshop.in", 250)
check("parse: domain aa gaya", _P.get("domain") == "xyzshop.in")
check("parse: registrar naam", _P.get("registrar") == "GoDaddy.com, LLC")
check("parse: malik (registrant) naam", _P.get("registrant") == "XYZ Traders Private Limited")
check("parse: banaya date DD-MM-YYYY me", _P.get("created_fmt") == "12-03-2019")
check("parse: umar nikalti hai", "saal" in str(_P.get("age")))
check("parse: khatam date + bache din",
      _P.get("expires_fmt") == "12-03-2027" and isinstance(_P.get("days_left"), int))
check("parse: last update", _P.get("changed_fmt") == "01-02-2026")
check("parse: nameserver list", _P.get("nameservers") == ["ns1.hostinger.com", "ns2.hostinger.com"])
check("parse: status Hinglish me samjhaya",
      any("active" in x for x in _P.get("status")) and
      any("transfer locked" in x for x in _P.get("status")))
check("parse: khaali dict par crash nahi", isinstance(OT.parse_rdap({}, "x.com"), dict))
check("parse: unknown TLD par bhi crash nahi", isinstance(OT.parse_rdap({"x": 1}, ""), dict))

# =====================================================================
section("[B] 📋 CARD — sab kuch bot ke andar, koi link nahi")
# =====================================================================
_CARD = bot.whois_card(_P)
_PLAIN = re.sub(r"</?(?:b|code|i)>", "", _CARD)
_PLAIN_NO_BRAND = "\n".join(l for l in _PLAIN.split("\n") if "Powered by" not in l)

check("card me domain hai", "xyzshop.in" in _PLAIN)
check("card me 'Banaya' line hai", "📅 Banaya: 12-03-2019" in _PLAIN)
check("card me umar likhi hai", "saal" in _PLAIN and "purana" in _PLAIN)
check("card me khatam date + bache din", "⌛ Khatam: 12-03-2027" in _PLAIN)
check("card me registrar", "🏢 Registrar: GoDaddy.com, LLC" in _PLAIN)
check("card me malik ka naam (public record)", "XYZ Traders Private Limited" in _PLAIN)
check("card me nameserver", "ns1.hostinger.com" in _PLAIN)
check("card me status", "📋 Status:" in _PLAIN)
check("card me aam aadmi ka matlab (verdict)", "💡 Matlab:" in _PLAIN)
check("purani site → 'bharosa karne layak' verdict",
      "bharosa" in _PLAIN or "theek hai" in _PLAIN)
check("card me koi link NAHI (user ka order)", "http" not in _PLAIN_NO_BRAND)

# naam chhupa ho to jhooth nahi bolna
_P2 = dict(_P); _P2["registrant"] = ""
_C2 = re.sub(r"</?(?:b|code|i)>", "", bot.whois_card(_P2))
check("malik chhupa ho to saaf likha aata hai (jhooth nahi)",
      "Registry me chhupa hua" in _C2)

# nayi site → warning
_P3 = dict(_P); _P3["age"] = "7 mahine"
_C3 = re.sub(r"</?(?:b|code|i)>", "", bot.whois_card(_P3))
check("nayi website par savdhan karta hai", "nayi hai" in _C3 or "soch lo" in _C3)

# =====================================================================
section("[C] 🔌 BOT ME WIRING — button, prompt, handler, credit")
# =====================================================================
check("premium tools list me hai", "osint_whois" in bot.PREMIUM_TOOLS)
check("tool ka naam set hai", "Website Owner" in bot.PREMIUM_TOOL_NAMES.get("osint_whois", ""))
check("rate limit lagi hai", "osint_whois" in bot.TOOL_RATE_LIMITS)
check("keyboard par button hai",
      any("WEBSITE OWNER X-RAY" in bot.unbold(b).upper()
          for r in bot.KB_BTNS for b in r))
check("button dabane par mode set hota hai",
      bot.BTN_MODE_MAP.get("WEBSITE OWNER X-RAY") == "osint_whois")
check("prompt (head/ask/ex) maujood hai",
      isinstance(bot.PROMPT_DATA.get("osint_whois"), dict)
      and bot.PROMPT_DATA["osint_whois"].get("ask"))
check("handler mode == osint_whois hai", 'if mode == "osint_whois":' in BOT_SRC)
check("handler card builder hi use karta hai", "whois_card(w_res)" in BOT_SRC)
check("credit message + add_use dono hain",
      'spend_credit_msg(uid, "osint_whois")' in BOT_SRC and
      BOT_SRC.count('add_use(uid)') >= 5)
check("fail par credit nahi katta (tel_note credit=True sirf ok me)",
      'tel_note("osint_whois", False, _msw' in BOT_SRC)
check("to_thread me chalta hai (bot atakta nahi)",
      "asyncio.to_thread(lookup_whois, raw_text)" in BOT_SRC)

# =====================================================================
section("[D] 🔁 PURANA KUCH TOOTA NAHI")
# =====================================================================
check("downloaders 4 hi hain", len(bot.DL_SITES) == 4)
check("downloader tools sabse upar (premium first)",
      "INSTA DL" in bot.unbold(bot.KB_BTNS[0][0]).upper())
check("keyboard me purane tools zinda", len(bot.KB_BTNS) >= 17)
check("IFSC/PINCODE/NUMBER INFO zinda",
      all(x in bot.PREMIUM_TOOLS for x in ("ifsc", "pin", "numinfo")))
check("numinfo card still sample format",
      "📱 <b>Phone:</b>" in BOT_SRC and "🏠 <b>Address:</b>" in BOT_SRC)
check("version v70+ hai", bot.BOT_VERSION.startswith("v70"), bot.BOT_VERSION)
check("koi bhi output me sirf-links wala tool add nahi hua",
      "link_only" not in BOT_SRC and "Direct link" not in BOT_SRC.split("whois_card")[1][:4000])

print(f"\n{'=' * 62}")
print(f"  v70 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
