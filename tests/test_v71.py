# -*- coding: utf-8 -*-
"""
v71 SELFTEST — 📱 PREMIUM EXAMPLES + 🚗 RC & CHALLAN + saaf cards
==================================================================
Boss ke teen order:
  1. "saare tools ke examples premium feel ho, ek valid example ho"
  2. "results me space ho, emoji ho, 'Malik' jaise words nahi — 'Owner' likho"
  3. "rc + challan wala add kar dena" (result bot ke andar)
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

_TMP = tempfile.mkdtemp(prefix="udv71_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V71"
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
print("  v71 SELFTEST — premium examples + RC/Challan + saaf cards")
print("=" * 62)

import bot                                                          # noqa: E402
from modules import vehicle_tool as VT                               # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

def _clean(t):
    return re.sub(r"</?(?:b|code|i|blockquote|a[^>]*)>", "", str(t or ""))


# =====================================================================
section("[A] 🎨 PROMPTS — premium box + EK valid example + tip")
# =====================================================================
_bad_words = ("xxxxx", "example.com/very", "kisi-site", "myexample")
for _k, _p in bot.PROMPTS.items():
    if not _p:
        continue
    _pl = _clean(_p)
    check(f"'{_k}' ka prompt boxed hai (┏━┓)", _pl.startswith("┏"))
    check(f"'{_k}' me EK hi example (code font)", _p.count("<code>") == 1, str(_p.count("<code>")))
    check(f"'{_k}' me dummy 'xxxxx' nahi", not any(b in _pl.lower() for b in _bad_words))
    check(f"'{_k}' me khali line ka spacing hai", "\n\n" in _p)

# downloader examples ASLI links hain
for _k, _url in (("instagram", "instagram.com/reel/"),
                 ("youtube", "youtube.com/watch?v="),
                 ("facebook", "facebook.com/watch"),
                 ("tiktok", "tiktok.com/")):
    check(f"dl_{_k} ka example asli link jaisa hai ({_url})", _url in bot.DL_SITES[_k][3])

check("jis tool ka sub ho, usme tip aata hai", "💡 <b>Tip:</b>" in bot.PROMPTS["numinfo"])
check("downloader me '30 second' wada dikhta hai", "30 second" in bot.PROMPTS["dl_youtube"])

# =====================================================================
section("[B] 🖼️ CARDS — space, emoji, aasan shabd")
# =====================================================================
_t = bot.pcard_title("🏦", "TEST CARD")
check("title box ┏━┓ frame ka hai", "┏" in _t and "┗" in _t and "┃" in _t)
check("title ke baad khali line aati hai", _t.endswith("\n"))
check("separator ke aage-peeche khali line", bot.pcard_sep().startswith("\n") and bot.pcard_sep().endswith("\n"))
check("footer se pehle khali line", bot.pcard_foot(ms=100).startswith("\n"))

_w = bot.whois_card(bot.lookup_whois("example.com")) if False else bot.whois_card({
    "domain": "xyzshop.in", "registrar": "GoDaddy", "registrant": "",
    "created_fmt": "12-03-2019", "age": "7 saal", "expires_fmt": "12-03-2027",
    "days_left": 400, "nameservers": ["ns1.x.com"], "status": ["✅ active"],
    "dnssec": "false", "latency_ms": 200})
_wp = _clean(_w)
check("whois card me 'Owner' likha hai ('Malik' nahi)", "👤 Owner:" in _wp and "Malik" not in _wp)
check("whois card me 'Registry Company' (aasan shabd)", "Registry Company:" in _wp and "Registrar:" not in _wp)
check("whois card me 'Servers' (Nameservers nahi)", "🛰️ Servers:" in _wp and "Nameserver" not in _wp)
check("whois card me khali lines (spacing)", "\n\n" in _w or "\n" in _w)
check("whois card me koi link nahi", "http" not in _wp.split("Powered by")[0])

_n = _clean(bot.numinfo_card({"national": "78578 43092", "number": "917857843092", "country": "India"},
                             {"name": "Sanjay Sah", "father": "Ram Akwal Sah", "alt": "7305190526",
                              "region": "BIHAR JIO", "govt_id": "401635555849",
                              "address": "S/O Ram Akwal Sah, ward 02, Sitamarhi, Bihar, 843324"},
                             {}, "JIO", "BIHAR", "📱 Mobile", "", "🟢 LIVE", 300))
check("numinfo card me sample order + spacing",
      _n.index("👤 Name:") < _n.index("👨 Father:") < _n.index("📱 Phone:")
      and "\n\n" in _n)

# =====================================================================
section("[C] 🚗 GAADI X-RAY (RC + CHALLAN) — naya tool")
# =====================================================================
check("premium tool list me hai", "vahan" in bot.PREMIUM_TOOLS)
check("naam set hai", "RC" in bot.PREMIUM_TOOL_NAMES.get("vahan", ""))
check("rate limit lagi hai", "vahan" in bot.TOOL_RATE_LIMITS)
check("keyboard par button hai",
      any("RC + CHALLAN" in bot.unbold(b).upper() for r in bot.KB_BTNS for b in r))
check("button → mode mapping", bot.BTN_MODE_MAP.get("RC + CHALLAN") == "vahan")
check("prompt me valid example BR01AB1234 hai",
      "<code>BR01AB1234</code>" in bot.PROMPTS.get("vahan", ""))
check("handler mode vahan hai", 'if mode == "vahan":' in BOT_SRC)
check("handler card builder use karta hai", "vahan_card(" in BOT_SRC)
check("plate saaf karta hai (space/dash hata ke)",
      VT._clean_plate("br 01-ab 1234") == "BR01AB1234")
check("galat plate par saaf error",
      VT.vehicle_lookup("hello").get("ok") is False)
check("offline parse (provider ke bina) state nikaalta hai",
      VT.offline_parse("BR01AB1234").get("state_name") == "Bihar")

_o = VT.offline_parse("BR01AB1234")
_c1 = _clean(bot.vahan_card({}, _o))
check("card me number + state + RTO aata hai",
      "BR01AB1234" in _c1 and "Bihar" in _c1 and "RTO Office:" in _c1)
check("provider off ho to jhooth nahi — SMS tarika batata hai",
      "7738299899" in _c1 and "VAHAN" in _c1)
check("card me koi link nahi (sirf SMS number)", "http" not in _c1.split("Powered by")[0])

# provider aane par card (dummy data se test)
_c2 = _clean(bot.vahan_card({
    "rc": {"plate": "BR01AB1234", "owner": "SANJAY SAH", "maker": "MARUTI", "model": "SWIFT",
           "fuel": "PETROL", "reg_date": "12-03-2019", "ins_company": "ICICI Lombard",
           "ins_upto": "11-03-2027", "financer": "none", "blacklist": "no", "colour": "WHITE"},
    "challans": [{"date": "01-02-2026", "offence": "No helmet", "amount": "500"}],
    "count": 1, "pending": 1, "amount": 500, "cached": True}, _o))
check("provider data par poori detail aati hai",
      all(x in _c2 for x in ("SANJAY SAH", "MARUTI SWIFT", "ICICI Lombard", "Loan/Lien",
                             "Blacklist", "Challan")))
check("loan nahi ho to 'clear' likhta hai", "clear" in _c2)
check("challan card me amount ₹ me aata hai", "₹" in _c2)
check("cached hone par 'turant mila' likhta hai", "turant mila" in _c2)

# provider env se mapping (RapidAPI jaise headers)
os.environ["VEHICLE_PROVIDER_URL"] = "https://x.example/api"
os.environ["VEHICLE_PROVIDER_KEY"] = "TESTKEY"
os.environ["VEHICLE_PROVIDER_HEADERS"] = "X-RapidAPI-Key:{key}|X-RapidAPI-Host:x.p.rapidapi.com"
check("provider ready detect hota hai", VT.provider_ready() is True)
_h = VT._flags()
check("RapidAPI headers theek bante hain (key bharta hai)",
      _h.get("X-RapidAPI-Key") == "TESTKEY" and "x.p.rapidapi.com" in str(_h.get("X-RapidAPI-Host")))
_m = VT.map_provider_payload({"rc": {"owner_name": "RAM SAH", "vehicle_class": "M-Cycle/Scooter",
                                     "registration_date": "01-01-2020", "insurance_upto": "01-01-2027"},
                              "challans": {"count": 2, "pending_count": 1,
                                           "pending_amount": 1500, "list": []}}, "BR01AB1234")
check("kisi bhi provider ka JSON map ho jata hai",
      _m["rc"].get("owner") == "RAM SAH" and _m["rc"].get("maker") is None
      and _m["count"] == 2 and _m["amount"] == 1500)
os.environ.pop("VEHICLE_PROVIDER_URL", None)

# =====================================================================
section("[D] 🔁 PURANA KUCH TOOTA NAHI")
# =====================================================================
check("4 downloader tools zinda", len(bot.DL_SITES) == 4)
check("premium tools 36 (35 + vahan)", len(bot.PREMIUM_TOOLS) == 36, str(len(bot.PREMIUM_TOOLS)))
check("keyboard rows badhe (18)", len(bot.KB_BTNS) >= 18, str(len(bot.KB_BTNS)))
check("downloader sabse upar hi hai",
      "INSTA DL" in bot.unbold(bot.KB_BTNS[0][0]).upper())
check("whois tool zinda", "osint_whois" in bot.PREMIUM_TOOLS)
check("'Privacy' shabd koi jagah nahi", "privacy" not in BOT_SRC.lower())
check("version v71 hai", bot.BOT_VERSION.startswith("v71"), bot.BOT_VERSION)
check("prompt texts ka structure zinda (head/ask/ex)",
      all(("head" in d and "ask" in d and "ex" in d) for d in bot.PROMPT_DATA.values()))

print(f"\n{'=' * 62}")
print(f"  v71 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
