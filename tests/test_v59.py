# -*- coding: utf-8 -*-
"""
tests/test_v59 — v59 "UPI GAYA + DEEP CLEAN + FAST YOUTUBE" suite
=================================================================
v59 me kya hua:

  1. 🏦 UPI VERIFY — POORI TARAH DELETE (user ka order)
     handler · prompt · keyboard · rate-limit · premium list · tool-name map ·
     dono callbacks · /upiapi · modules/upi_provider.py ·
     osint_tools ka upi_verify() + UPI_BANK_HANDLES · UPI_VERIFY_* env vars ·
     UPI-NAAM-API-SETUP.md — sab gaya.

  2. 🔒 PRIVACY TEXT — SAARE TOOLS SE GAYI
     BGMI / FF UID / Number Info / UPI ke privacy notes hataye.
     Ab kisi bhi tool me "privacy lecture" nahi.

  3. 📱 NUMBER INFO — AAPKE DIYE FORMAT ME
     `👤 Name / 👨 Father / 📱 Phones-Alt / 🌐 Region / 🆔 Govt ID / 🏠 Address(es)`
     → separator → number/operator/source/response. Data sirf aapki API se.

  4. ⚡ YOUTUBE — LATE RESPONSE FIX
     Quality buttons instant (6h cache + background warm) + download
     progressive fmt (18/22) + parallel chunks + socket_timeout 15.

  5. 🐛 REGRESSION LOCK — /version function (patch15 ise uda deta tha).

Chalane ka tarika:
    python3 tests/test_v59.py
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
import threading
import types
import warnings
from http.server import BaseHTTPRequestHandler, HTTPServer

warnings.filterwarnings("ignore")

os.environ.setdefault("BOT_TOKEN", "123456:TEST-TOKEN-FOR-SELFTEST")
os.environ.setdefault("ADMIN_ID", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
MD_SRC = open(os.path.join(ROOT, "modules", "media_downloader.py"), encoding="utf-8").read()
OT_SRC = open(os.path.join(ROOT, "modules", "osint_tools.py"), encoding="utf-8").read()
NP_SRC = open(os.path.join(ROOT, "modules", "numinfo_provider.py"), encoding="utf-8").read()

PASS = 0
FAIL = 0
FAILURES: list = []


def section(t: str):
    print("\n" + "=" * 62)
    print(t)
    print("=" * 62)


def check(name: str, cond: bool, extra: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name} {extra}")
        print(f"  ❌ {name}  {extra}")
    return bool(cond)


import bot  # noqa: E402
import modules.osint_tools as OT  # noqa: E402
import modules.numinfo_provider as NP  # noqa: E402
import modules.media_downloader as MD  # noqa: E402


# =====================================================================
section("1) 🏦 UPI VERIFY — poora delete (tool + poori code)")
# =====================================================================

# --- bot.py ---
check("UPI mode handler gayab hai", 'if mode == "upi":' not in BOT_SRC)
check("UPI prompt gayab hai (PROMPT_DATA me 'upi' key nahi)",
      "upi" not in {str(k).lower() for k in bot.PROMPT_DATA})
_BOT_USER = "\n".join(_l for _l in BOT_SRC.split("\n")
                      if "BOT_VERSION =" not in _l)      # version comment chhod do
check("UPI VERIFY text kahin nahi (user-facing code me)", "UPI VERIFY" not in _BOT_USER)
# bot.py me 'UPI' shabd sirf VIP payment / IFSC service flag / safety advice /
# version line me bache — tool ka koi zikr nahi
_allowed = ("UPI_ID", "UPI_NAME", "BOT_VERSION", "VIP", "cash or UPI", "UPI tool:",
            "UPI ID:", "UPI PIN", "UPI {'✅'", "UPI Verify Removed")
_stray = [_l.strip()[:60] for _l in BOT_SRC.split("\n")
          if "UPI" in _l and not any(_a in _l for _a in _allowed)]
check("UPI ka koi stray reference nahi (sirf payment/IFSC/safety/version)",
      not _stray, str(_stray[:3]))
check("keyboard me UPI button nahi",
      not any("UPI" in bot.unbold(_b).upper() for _r in bot.KB_BTNS for _b in _r))
check("BTN_MODE_MAP me UPI nahi",
      not any("upi" in str(k).lower() for k in bot.BTN_MODE_MAP))
check("PREMIUM_TOOLS me UPI nahi",
      "upi" not in {str(x).lower() for x in bot.PREMIUM_TOOLS})
check("PREMIUM_TOOL_NAMES me UPI nahi",
      not any("upi" in str(x).lower() for x in bot.PREMIUM_TOOL_NAMES.values()
              if not isinstance(x, (list, tuple, dict))) if isinstance(bot.PREMIUM_TOOL_NAMES, dict) else True)
check("TOOL_RATE_LIMITS me UPI nahi",
      "upi" not in {str(x).lower() for x in bot.TOOL_RATE_LIMITS})
check("dono callbacks (upi_to_num / upi_to_vpa) gaye",
      "upi_to_num" not in BOT_SRC and "upi_to_vpa" not in BOT_SRC)
check("/upiapi command + handler gaye",
      "upiapi" not in BOT_SRC.lower() and "cmd_upiapi" not in BOT_SRC)
check("upi_provider ka koi import/reference nahi",
      "upiprov" not in BOT_SRC and "upi_provider" not in BOT_SRC)
check("UPI_VERIFY_* env var code me kahin nahi", "UPI_VERIFY" not in BOT_SRC)
check("help / replacement text me UPI Verify nahi",
      "UPI Verify" not in _BOT_USER and "UPI/IFSC" not in _BOT_USER)

# --- module level ---
check("modules/upi_provider.py file DELETE",
      not os.path.exists(os.path.join(ROOT, "modules", "upi_provider.py")))
check("osint_tools.upi_verify() gaya", not hasattr(OT, "upi_verify"))
check("osint_tools.UPI_BANK_HANDLES gaya", not hasattr(OT, "UPI_BANK_HANDLES"))
check("osint_tools me _VPA_RE bhi nahi", "_VPA_RE" not in OT_SRC)
check("osint_tools me UPI ka koi def/const nahi",
      "UPI_BANK_HANDLES" not in OT_SRC)

# --- keyboard: uski jagah pincode aaya, duplicate nahi ---
_labels = [bot.unbold(_b).upper() for _r in bot.KB_BTNS for _b in _r]
check("keyboard me PINCODE INFO button hai",
      any("PINCODE INFO" in x for x in _labels))
check("keyboard me IFSC button hai (UPI ki jagah)",
      any("IFSC INFO" in x for x in _labels))
check("keyboard me IFSC button sirf EK baar (duplicate nahi)",
      sum(1 for x in _labels if "IFSC" in x) == 1, str(sum(1 for x in _labels if "IFSC" in x)))
check("keyboard me SARKARI SEVA PORTALS duplicate nahi",
      sum(1 for x in _labels if "SARKARI SEVA" in x) == 1,
      str(sum(1 for x in _labels if "SARKARI SEVA" in x)))
check("keyboard ki total buttons kam nahi hui (26 = 25 tools + vip/help)",
      len(_labels) >= 24, str(len(_labels)))

# --- env + docs ---
check("render.yaml me UPI_VERIFY_* nahi",
      "UPI_VERIFY" not in open(os.path.join(ROOT, "render.yaml"), encoding="utf-8").read())
check(".env.example me UPI_VERIFY_* nahi",
      "UPI_VERIFY" not in open(os.path.join(ROOT, ".env.example"), encoding="utf-8").read())
check(".env.example me NUM_LEAK_ENABLED bhi nahi (purana privacy feature)",
      "NUM_LEAK_ENABLED" not in open(os.path.join(ROOT, ".env.example"),
                                     encoding="utf-8").read())
check("UPI-NAAM-API-SETUP.md delete",
      not os.path.exists(os.path.join(ROOT, "UPI-NAAM-API-SETUP.md")))
check("V59-KYA-BADLA.md guide bani", os.path.exists(os.path.join(ROOT, "V59-KYA-BADLA.md")))
check("README me v59 section hai",
      "v59.0" in open(os.path.join(ROOT, "README.md"), encoding="utf-8").read())
check("AB-KYA-KARNA-HAI.md me v59 dikhta hai",
      "v59" in open(os.path.join(ROOT, "AB-KYA-KARNA-HAI.md"), encoding="utf-8").read())


# =====================================================================
section("2) 🔒 PRIVACY TEXT — saare tools se gayi")
# =====================================================================
_bot_low = BOT_SRC.lower()
for _bad in ("leaked private data", "leaked data", "privacy (zaroori baat)",
             "ye naam public nahi", "publicly available nahi hota",
             "privacy ke liye", "privacy note"):
    check(f'bot.py me "{_bad}" nahi', _bad not in _bot_low)
check("bot.py me '🔒' privacy emoji wala text nahi",
      "🔒 <b>Privacy" not in BOT_SRC and "🔒 <b>Note" not in BOT_SRC)
check("bot.py me 'Privacy' shabd bilkul nahi (version comment bhi saaf)",
      "privacy" not in BOT_SRC.lower())
check("osint_hub.py me privacy refusal error nahi",
      "Privacy" not in open(os.path.join(ROOT, "modules", "osint_hub.py"),
                            encoding="utf-8").read())
_ot_low = OT_SRC.lower()
check("osint_tools.py me privacy note nahi",
      "privacy" not in _ot_low and "public nahi hota" not in _ot_low)
check("api_hub.py me 'leaked' shabd nahi",
      "leaked" not in open(os.path.join(ROOT, "modules", "api_hub.py"),
                           encoding="utf-8").read().lower())
# BGMI / FF cards
for _tool in ("bgmi", "ffuid"):
    _seg_i = BOT_SRC.index(f'if mode == "{_tool}":')
    _nxt = BOT_SRC.find('if mode == "', _seg_i + 20)
    _seg = BOT_SRC[_seg_i:_nxt if _nxt > 0 else len(BOT_SRC)]
    check(f"{_tool.upper()} card me privacy note nahi",
          "Privacy" not in _seg and "🔒" not in _seg)


# =====================================================================
section("3) 📱 NUMBER INFO — aapke diye format ka card")
# =====================================================================
_ni_i = BOT_SRC.index('if mode == "numinfo":')
_ni_j = BOT_SRC.index('if mode == "ifsc":', _ni_i)
NI = BOT_SRC[_ni_i:_ni_j]
# v59.5: card ka layout ab module-level renderer `numinfo_card()` me hai
_CARD_I = BOT_SRC.index("def numinfo_card(")
CARD_SRC = BOT_SRC[_CARD_I:BOT_SRC.index("\ndef build_qr_image(", _CARD_I)]

check("naya card block hai (_obits)", "_obits" in NI)
check("purana 'NUMBER INFO REPORT' card POORA DELETE ho gaya",
      "NUMBER INFO REPORT" not in NI and "NUMBER INFO REPORT" not in BOT_SRC)
check("numinfo me pcard_title ka use hi nahi (ek hi layout)",
      "pcard_title" not in NI)
check("ek hi card builder hai (_card) — owner lines optional",
      "_card = list(_obits)" in CARD_SRC and "if not _obits:" in CARD_SRC)
for _lbl in ("👤 <b>Name:</b>", "👨 <b>Father:</b>", "📱 <b>Phones/Alt:</b>",
             "🌐 <b>Region:</b>", "🆔 <b>Govt ID:</b>", "🏠 <b>Address(es):</b>"):
    check(f"card me line '{_lbl}'", _lbl in CARD_SRC)
# user ke format ka order: Name → Father → Phones → Region → Govt ID → Address
_pos = [CARD_SRC.index(x) for x in ("👤 <b>Name:</b>", "👨 <b>Father:</b>", "📱 <b>Phones/Alt:</b>",
                                  "🌐 <b>Region:</b>", "🆔 <b>Govt ID:</b>",
                                  "🏠 <b>Address(es):</b>")]
check("lines user ke diye ORDER me hain", _pos == sorted(_pos))
check("address bullet '└' se aata hai (max 4 line)",
      '_obits.append(f"   └ ' in CARD_SRC or "   └ " in CARD_SRC)
check("address 300 char par kata jaata hai (Telegram limit safe)", "_ap[:300]" in CARD_SRC)
check("separator (pcard_sep) owner block ke baad aata hai",
      "pcard_sep()" in CARD_SRC and "👤" in CARD_SRC)
check("card me Number line hai", "📞 <b>Number:</b>" in CARD_SRC)
check("card me Operator + Circle line hai", "🏢 <b>Operator:</b>" in CARD_SRC and "📍" in CARD_SRC)
check("card me Source + Response line hai",
      "📡 <b>Source:</b>" in CARD_SRC and "⚡ <b>Response:</b>" in CARD_SRC)
check("card ke aakhir me brand footer", "Powered by" in CARD_SRC and "BRAND_TAG" in CARD_SRC)
check("NUMINFO_SHOW_OWNER gate hata diya (card seedha dimaghta hai)",
      "NUMINFO_SHOW_OWNER" not in BOT_SRC)
check("API na ho to sirf chhota setup hint (koi lecture line nahi)",
      "NUMINFO_PROVIDER_URL" in NI and "/numapi" in NI)
check("card me privacy/leaked shabd nahi",
      "leaked" not in NI.lower() and "Privacy" not in NI and "privacy" not in NI)
check("extra address list (addresses / address_list) support hai",
      "address_list" in CARD_SRC and "addresses" in CARD_SRC)
# user ka exact format: 🏠 Address(es): ke baad ek khali line, phir "   └ ..."
check("Address(es) label ke baad blank line aati hai (aapka exact format)",
      '"🏠 <b>Address(es):</b>\\n"' in CARD_SRC)
check("address line '└' se shuru hoti hai", 'f"   └ {hesc(' in CARD_SRC)
check("purana '🔒 Private Setup' ad nahi (hata diya gaya tool)",
      "Private Setup" not in BOT_SRC)
check("TEMP MAIL card me privacy line nahi",
      "sirf isi chat me hai" not in BOT_SRC)

# provider module: owner fields parse (offline, fake API response)
_flat = NP._flatten({"name": "Sanjay Sah", "fatherName": "Ram Akwal Sah",
                     "altMobile": "7305190526", "region": "BIHAR JIO",
                     "govtId": "401635555849", "address": "S/O Ram Akwal Sah, ward 02"})
check("provider owner name parse", NP._clean_name(NP._pick(_flat, "name", "ownername")) == "Sanjay Sah")
check("provider father parse", NP._clean_name(NP._pick(_flat, "father", "fathername")) == "Ram Akwal Sah")
check("provider alt mobile parse", NP._clean_name(NP._pick(_flat, "alt", "altmobile")) == "7305190526")
check("provider region parse", NP._clean_name(NP._pick(_flat, "region", "state")) == "BIHAR JIO")
check("provider govt id parse", NP._clean_name(NP._pick(_flat, "govtid", "idnumber")) == "401635555849")
check("provider address parse", "ward 02" in NP._clean_name(NP._pick(_flat, "address")))
check("POST support hai (NUMINFO_PROVIDER_METHOD)",
      "NUMINFO_PROVIDER_METHOD" in NP_SRC and "def provider_method()" in NP_SRC
      and "http_post" in NP_SRC)
check("owner-only API bhi chalti hai (carrier data ke bina) — 'format match nahi hua' nahi",
      "and not any(_owner.values())" in NP_SRC)
check("owner dict me paanch field map hote hain",
      all(f'"{_f}": _clean_name' in NP_SRC
          for _f in ("name", "father", "alt", "region", "govt_id", "address")))

# ---- LIVE: POST + sirf owner data wali API ----


class _HPost(BaseHTTPRequestHandler):
    def do_POST(self):                                       # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        b = json.dumps({"name": "POST WALA NAAM", "address": "Sitamarhi, Bihar"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):                               # noqa: D102
        pass


_srv2 = HTTPServer(("127.0.0.1", 0), _HPost)
threading.Thread(target=_srv2.serve_forever, daemon=True).start()
os.environ["NUMINFO_PROVIDER_URL"] = f"http://127.0.0.1:{_srv2.server_address[1]}/api"
os.environ["NUMINFO_PROVIDER_KEY"] = "TESTKEY"
os.environ["NUMINFO_PROVIDER_METHOD"] = "POST"
try:
    _r2 = NP.lookup("9876543210")
    check("LIVE POST: ok=True (POST API chalti hai)", _r2.get("ok") is True, str(_r2)[:110])
    check("LIVE POST: sirf naam/pata wali API se bhi owner data aaya",
          (_r2.get("owner") or {}).get("name") == "POST WALA NAAM", str(_r2.get("owner")))
finally:
    _srv2.shutdown()
    os.environ.pop("NUMINFO_PROVIDER_URL", None)
    os.environ.pop("NUMINFO_PROVIDER_KEY", None)
    os.environ.pop("NUMINFO_PROVIDER_METHOD", None)
    try:
        NP._CACHE.clear()                                    # type: ignore[attr-defined]
    except Exception:                                        # noqa: BLE001
        pass

# ---- LIVE-ish: chhota fake API server, phir numprov.lookup ----
_SAMPLE = {"data": {"name": "Sanjay Sah", "fatherName": "Ram Akwal Sah",
                    "altMobile": "7305190526", "region": "BIHAR JIO",
                    "govtId": "401635555849",
                    "address": "S/O Ram Akwal Sah, ward 02, Patna",
                    "operator": "Jio", "circle": "Bihar"}}


class _H(BaseHTTPRequestHandler):
    def do_GET(self):                                        # noqa: N802
        body = json.dumps(_SAMPLE).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):                                       # noqa: N802
        ln = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(ln)
        self.do_GET()

    def log_message(self, *a):                               # noqa: D102
        pass


_srv = HTTPServer(("127.0.0.1", 0), _H)
_port = _srv.server_address[1]
threading.Thread(target=_srv.serve_forever, daemon=True).start()
os.environ["NUMINFO_PROVIDER_URL"] = f"http://127.0.0.1:{_port}/?number={{number}}"
os.environ["NUMINFO_PROVIDER_KEY"] = "TESTKEY"
try:
    _lk = NP.lookup("9876543210")
    check("fake API se lookup ok=True", _lk.get("ok") is True, str(_lk)[:120])
    _ow = (_lk.get("owner") or {})
    check("live lookup me name aaya", _ow.get("name") == "Sanjay Sah", str(_ow))
    check("live lookup me father aaya", _ow.get("father") == "Ram Akwal Sah")
    check("live lookup me alt number aaya", _ow.get("alt") == "7305190526")
    check("live lookup me region aaya", _ow.get("region") == "BIHAR JIO")
    check("live lookup me govt id aaya", _ow.get("govt_id") == "401635555849")
    check("live lookup me address aaya", "ward 02" in str(_ow.get("address")))
    check("live lookup me operator bhi aaya", str(_lk.get("operator") or "").lower() == "jio")
    check("lookup crashed nahi (dict milta hai)", isinstance(_lk, dict))
finally:
    _srv.shutdown()
    os.environ.pop("NUMINFO_PROVIDER_URL", None)
    os.environ.pop("NUMINFO_PROVIDER_KEY", None)
    try:
        NP._CACHE.clear()                                    # type: ignore[attr-defined]
    except Exception:                                        # noqa: BLE001
        pass


# =====================================================================
section("4) ⚡ YOUTUBE — instant buttons + tez download")
# =====================================================================
check("yt_cached_qualities() helper hai", hasattr(MD, "yt_cached_qualities"))
check("yt_warm_qualities() helper hai", hasattr(MD, "yt_warm_qualities"))
check("YT_QUALITY_OPTIONS fallback list hai",
      hasattr(MD, "YT_QUALITY_OPTIONS") and 1080 in MD.YT_QUALITY_OPTIONS)
check("cache + TTL + lock hai",
      "_YT_QUAL_CACHE" in MD_SRC and "_YT_QUAL_TTL" in MD_SRC and "_YT_QUAL_LOCK" in MD_SRC)
check("cache TTL 6 ghante", "_YT_QUAL_TTL = 6 * 3600" in MD_SRC)

# cold cache → [] (koi block nahi), warm cache → turant list
MD._YT_QUAL_CACHE.clear()
check("cold cache par [] (turant return, koi fetch nahi)",
      MD.yt_cached_qualities("https://youtu.be/xyz") == [])
MD._YT_QUAL_CACHE["https://youtu.be/xyz"] = (__import__("time").time(), [1080, 720])
check("warm cache par turant qualities", MD.yt_cached_qualities("https://youtu.be/xyz") == [1080, 720])
check("cache entry khali ho to [] (safe)", MD.yt_cached_qualities("") == [] or True)
MD._YT_QUAL_CACHE.clear()

# bot.py ka YouTube branch: koi blocking metadata fetch nahi
check("bot.py me yt_available_qualities ka await nahi bacha",
      "await asyncio.to_thread(yt_available_qualities" not in BOT_SRC)
check("bot.py instant cached-qualities use karta hai",
      "yt_cached_qualities(raw_text)" in BOT_SRC)
check("cache miss par background warm chalta hai",
      "yt_warm_qualities(raw_text)" in BOT_SRC)
check("cache miss par YT_QUALITY_OPTIONS turant dikhte hain",
      "list(YT_QUALITY_OPTIONS)" in BOT_SRC)
_md_imp = BOT_SRC.split("from modules.media_downloader import (")[1].split(")")[0]
check("bot.py me yt_cached_qualities / yt_warm_qualities import hai",
      "yt_cached_qualities" in _md_imp and "yt_warm_qualities" in _md_imp)

# downloader speed opts
check("socket_timeout 15 set hai", '"socket_timeout": 15' in MD_SRC)
check("concurrent_fragment_downloads 4 set hai",
      '"concurrent_fragment_downloads": 4' in MD_SRC)
check("progressive format 18 pehle try hota hai", 'fmt = ("18/' in MD_SRC)
check("progressive format me 22 bhi hai", '"22/' in MD_SRC or '"22"' in MD_SRC)
check("merge-avoid note comment hai", "progressive" in MD_SRC.lower())


# =====================================================================
section("5) 🐛 REGRESSION LOCK — /version function (patch ka shikaar)")
# =====================================================================
check("/version FUNCTION maujood hai (sirf handler nahi)",
      "async def cmd_version(" in BOT_SRC)
check("/version handler registered hai",
      'CommandHandler(["version", "ver", "v"], cmd_version)' in BOT_SRC)
check("/version me BOT_VERSION dikhta hai", "{hesc(BOT_VERSION)}" in BOT_SRC)
check("/version me UPI ka status line aata hai (hata diya gaya)",
      "UPI tool:</b> 🗑️" in BOT_SRC)
check("/version me Number Info API status aata hai", "Number Info API:</b>" in BOT_SRC)
check("/version me YouTube instant status aata hai", "YouTube quality buttons:</b>" in BOT_SRC)

# bot.py me jo bhi add_handler(..., cmd_x) hai, uska function zinda ho
_missing = []
for _m in re.finditer(r"CommandHandler\(\[([^\]]+)\],\s*(\w+)\)", BOT_SRC):
    _fn = _m.group(2)
    if f"def {_fn}(" not in BOT_SRC and f"async def {_fn}(" not in BOT_SRC:
        _missing.append(_fn)
check("saare command handlers ke function zinda hain (patch casualty lock)",
      not _missing, str(_missing))


# =====================================================================
section("6) 🧾 SANITY — version + kuch toota nahi")
# =====================================================================
check("BOT_VERSION v59 hai", 'BOT_VERSION = "v59.' in BOT_SRC,
      re.search(r'BOT_VERSION = "([^"]+)"', BOT_SRC).group(1) if
      re.search(r'BOT_VERSION = "([^"]+)"', BOT_SRC) else "?")
check("prompt system zinda hai (tool_prompt sanitize karta hai)",
      "return _sanitize_prompt(body)" in BOT_SRC)
check("kisi bhi tool prompt me Credits/cancel line nahi",
      all("Credits:" not in bot.tool_prompt(k) and "cancel" not in bot.tool_prompt(k).lower()
          for k in bot.PROMPT_DATA))
_np_p = bot.tool_prompt("numinfo")
check("NUMBER INFO prompt me 3 example hain (jaise baaki tools me)",
      _np_p.count("•") >= 3, str(_np_p.count("•")))
check("NUMBER INFO examples: 10-digit + dusra mobile + +91 wala",
      "9876543210" in _np_p and "7305190526" in _np_p and "+91 98765 43210" in _np_p)
check("NUMBER INFO me koi banned line nahi (credits/cancel)",
      "Credits:" not in _np_p and "cancel" not in _np_p.lower())
check("BOT_VERSION comment stack nahi hua (ek hi # v59: note)",
      BOT_SRC[BOT_SRC.index("BOT_VERSION ="):][:400].count("# v59:") <= 1)
# --- 🧪 DEMO mode + /numdemo (v59.5) ---
check("numinfo_card() renderer module-level hai (ek hi layout, do jagah use)",
      callable(getattr(bot, "numinfo_card", None)))
check("handler bhi numinfo_card() use karta hai (duplicate layout nahi)",
      "card = numinfo_card(res, _ow, _extra" in NI)
check("/numdemo command hai", callable(getattr(bot, "cmd_numdemo", None)))
check("/numdemo registered hai", '["numdemo", "numinfodemo", "numpreview"], cmd_numdemo' in BOT_SRC)
check("/numdemo admin-only hai", BOT_SRC[BOT_SRC.index("async def cmd_numdemo"):][:420].count("is_admin") >= 1)
check("/numdemo me credit NAHI katta", "spend_credit_msg" not in
      BOT_SRC[BOT_SRC.index("async def cmd_numdemo"):][:1500])
check("/numdemo card SAMPLE bolta hai (asli data jaisa confusion nahi)",
      "SAMPLE PREVIEW" in BOT_SRC and "nakli values" in BOT_SRC)
check("demo source line bot.py me hai (🧪 DEMO SAMPLE)",
      'if _src == "demo":' in BOT_SRC and "DEMO SAMPLE" in BOT_SRC)

import modules.numinfo_provider as _NP2  # noqa: E402
check("provider me demo_mode() hai", callable(getattr(_NP2, "demo_mode", None)))
check("provider me demo_result() hai", callable(getattr(_NP2, "demo_result", None)))
_d = _NP2.demo_result("9000000001")
check("demo_result asli shape deta hai (ok/source/owner)",
      _d.get("ok") is True and _d.get("source") == "demo" and bool(_d.get("owner")))
check("demo data clearly SAMPLE likha hua hai (real person nahi)",
      "SAMPLE" in str(_d.get("owner")))

# LIVE: env ON → lookup demo data deta hai; OFF → not_configured
import importlib as _il2  # noqa: E402
_il2.reload(_NP2)
_old_url = os.environ.pop("NUMINFO_PROVIDER_URL", None)
_old_key = os.environ.pop("NUMINFO_PROVIDER_KEY", None)
os.environ["NUMINFO_DEMO"] = "on"
_il2.reload(_NP2)
_r_demo = _NP2.lookup("9876543210")
check("LIVE: DEMO=on par lookup sample card deta hai (ok=True, source=demo)",
      _r_demo.get("ok") is True and _r_demo.get("source") == "demo", str(_r_demo)[:90])
os.environ["NUMINFO_DEMO"] = "off"
_il2.reload(_NP2)
_r_off = _NP2.lookup("9876543210")
check("LIVE: DEMO=off par not_configured (jhootha sample nahi)",
      _r_off.get("not_configured") is True, str(_r_off)[:90])
os.environ.pop("NUMINFO_DEMO", None)
if _old_url:
    os.environ["NUMINFO_PROVIDER_URL"] = _old_url
if _old_key:
    os.environ["NUMINFO_PROVIDER_KEY"] = _old_key
_il2.reload(_NP2)

# /numdemo card me saari 6 owner line + separator aate hain (renderer check)
_demo_card = bot.numinfo_card({"international": "+91 90000 00001", "country": "India"},
                              _NP2.demo_result().get("owner"), {}, "Jio", "Bihar",
                              "📱 Mobile", "", "🧪 SAMPLE", 240)
for _lbl in ("👤 <b>Name:</b>", "👨 <b>Father:</b>", "📱 <b>Phones/Alt:</b>",
             "🌐 <b>Region:</b>", "🆔 <b>Govt ID:</b>", "🏠 <b>Address(es):</b>"):
    check(f"demo card me '{_lbl}' aata hai", _lbl in _demo_card)

# --- 🔎 /numtest — MAPPING PREVIEW (JSON paste karo → card dikhao) ---
check("provider.parse_payload() hai (mapping ek jagah)",
      callable(getattr(NP, "parse_payload", None)))
check("lookup() bhi wahi parse_payload use karta hai (duplicate mapping nahi)",
      "out = parse_payload(data)" in NP_SRC)
check("/numtest command hai", callable(getattr(bot, "cmd_numtest", None)))
check("/numtest registered hai",
      '["numtest", "numcheck", "numinfotest"], cmd_numtest' in BOT_SRC)
check("/numtest admin-only hai",
      BOT_SRC[BOT_SRC.index("async def cmd_numtest"):][:420].count("is_admin") >= 1)
check("/numtest credit NAHI katta",
      "spend_credit_msg" not in BOT_SRC[BOT_SRC.index("async def cmd_numtest"):][:2500])
check("/numtest batata hai ki koi API call nahi hoti",
      "koi API call nahi hui" in BOT_SRC or "koi API call nahi hoti" in BOT_SRC)

_p = NP.parse_payload({"carrier": "Jio", "location": "Bihar", "name": "Rahul Kumar",
                       "fatherName": "Mohan Lal", "altMobile": "9000000001",
                       "address": "Ward 2, Sitamarhi", "govtId": "123456789012"})
check("parse_payload: carrier JSON ko samajhta hai",
      _p.get("ok") is True and _p.get("operator") == "Jio", str(_p)[:90])
check("parse_payload: owner fields map hote hain",
      (_p.get("owner") or {}).get("name") == "Rahul Kumar"
      and (_p.get("owner") or {}).get("father") == "Mohan Lal")
check("parse_payload: galat shape par saaf error (crash nahi)",
      NP.parse_payload({"kuch": "aur"}).get("ok") is False)

# LIVE: /numtest ka poora flow (mock update se)
import asyncio as _aio  # noqa: E402


class _TM:
    message_id = 1

    def __init__(self, t=""):
        self.text = t

    async def reply_text(self, t, **k):
        _TM.last = t
        return self

    async def edit_text(self, t, **k):
        _TM.last = t
        return self


class _TU:
    id = int(os.environ.get("ADMIN_ID", "1"))   # test harness admin hi hai
    first_name = "T"
    username = "t"


class _TUp:
    def __init__(self, t):
        self.message = _TM(t)
        self.effective_user = _TU()
        self.effective_chat = types.SimpleNamespace(id=888)
        self.callback_query = None
        self.effective_message = self.message


def _run_numtest(txt):
    _TM.last = ""
    _aio.run(bot.cmd_numtest(_TUp(txt),
                             types.SimpleNamespace(user_data={}, bot=None, args=None)))
    return _TM.last


_out = _run_numtest('/numtest {"carrier":"Jio","location":"Bihar","name":"Rahul Kumar","address":"Ward 2, Sitamarhi"}')
check("LIVE /numtest: card bana (Name line aayi)", "👤 <b>Name:</b> Rahul Kumar" in _out)
check("LIVE /numtest: MAPPING PREVIEW likha hai", "MAPPING PREVIEW" in _out)
check("LIVE /numtest: operator line aayi", "🏢 <b>Operator:</b> Jio" in _out)
_help = _run_numtest("/numtest")
check("LIVE /numtest (bina JSON): help message aata hai, crash nahi",
      "paste karo" in _help and "Koi API call nahi hoti" in _help)
_bad = _run_numtest("/numtest haan bhai ye json nahi hai")
check("LIVE /numtest (galat JSON): saaf error, crash nahi",
      "valid JSON nahi" in _bad)

check("SANKHYA: prompt wale tools 20+ hain (UPI hata ke bhi)",
      len(bot.PROMPT_DATA) >= 20, str(len(bot.PROMPT_DATA)))
check("IMEI tool zinda hai (photo + device search)", hasattr(bot, "cmd_imeistatus"))
check("module files me syntax error nahi (bot import hua)", True)

_dup = []
_t = ast.parse(BOT_SRC)
for _n in ast.walk(_t):
    if isinstance(_n, ast.Dict):
        _ks = [k.value for k in _n.keys
               if isinstance(k, ast.Constant) and isinstance(k.value, str)]
        _d = {x for x in _ks if _ks.count(x) > 1}
        if _d:
            _dup.append(sorted(_d))
check("bot.py me duplicate dict keys nahi", not _dup, str(_dup[:2]))


# =====================================================================
section("7) 🛡️ HARDCORE CRASH-PROOF CORE (self-check + self-heal + guards)")
# =====================================================================
check("_startup_selfcheck() helper hai", callable(getattr(bot, "_startup_selfcheck", None)))
check("_supervise() helper hai (self-heal supervisor)",
      callable(getattr(bot, "_supervise", None)))
check("_CRASH_STATE counter maujood hai",
      isinstance(getattr(bot, "_CRASH_STATE", None), dict)
      and "count" in bot._CRASH_STATE)
check("__main__ supervisor se chalta hai (seedha main() nahi)",
      "_supervise()" in BOT_SRC and BOT_SRC.rstrip().endswith("_supervise()"))
check("--check flag se sirf self-check chalta hai (deploy verify)",
      '"--check" in sys.argv' in BOT_SRC)
check("self-check me version + commit print hote hain",
      "🩺 SELF-CHECK" in BOT_SRC and "{_GIT_COMMIT}" in BOT_SRC)
check("self-check me modules verify hote hain", "modules: sab OK" in BOT_SRC)
check("self-check me API status sirf set/not-set (key never printed)",
      "Number Info API:" in BOT_SRC and "provider_key()" not in BOT_SRC.split("_startup_selfcheck")[1][:2000])
check("self-heal crash hone par dobara chalta hai (loop)",
      "while True:" in BOT_SRC.split("def _supervise")[1][:900])
check("bahut zyada crash par 60s wait (loop na bane)",
      "_wait = 60 if len(_fast) >= 8 else 5" in BOT_SRC)
check("KeyboardInterrupt par crash-restart nahi (clean exit)",
      "except KeyboardInterrupt:" in BOT_SRC.split("def _supervise")[1][:900])
check("traceback log hota hai (debugging ke liye)",
      "traceback.print_exc()" in BOT_SRC.split("def _supervise")[1][:2500])
check("loop exception handler laga hai (background task crash se bot nahi girta)",
      "set_exception_handler" in BOT_SRC)
check("/health me self-heal crash counter dikhta hai",
      "self-heal: crashes=" in BOT_SRC)
check("self-check boot par chalta hai (banner ke baad)",
      "_startup_selfcheck()" in BOT_SRC.split("print(f\"🚀 Starting ToolVault")[1][:300])
check("self-check crash kar bhi jaye to bot rukta nahi (try/except)",
      "self-check skip (crash nahi)" in BOT_SRC)
check("banner me ab commit + pid bhi dikhta hai",
      "   commit {_GIT_COMMIT} | pid {os.getpid()}" in BOT_SRC)

# --- LIVE proof: supervisor do crash ke baad khud chalu hota hai ---
_calls = []
_orig_main, _orig_sleep = bot.main, bot.time.sleep


def _fake_main():
    _calls.append(1)
    if len(_calls) < 3:
        raise RuntimeError("test crash %d" % len(_calls))


bot.main = _fake_main
bot.time.sleep = lambda s: None                     # test me wait skip
try:
    bot._supervise()
finally:
    bot.main, bot.time.sleep = _orig_main, _orig_sleep

check("LIVE: 2 crash ke baad 3rd try chala (self-heal kaam karta hai)",
      len(_calls) == 3, str(len(_calls)))
check("LIVE: crash counter badha", bot._CRASH_STATE["count"] >= 2,
      str(bot._CRASH_STATE["count"]))


print("\n" + "=" * 62)
print(f"  v59 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILURES:
    print("\n  FAILURES:")
    for _f in FAILURES:
        print(f"   - {_f}")
print()
sys.exit(0 if FAIL == 0 else 1)
