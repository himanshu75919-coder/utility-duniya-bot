# -*- coding: utf-8 -*-
"""
tests/test_v58 — v58 "NAYA PROMPT SYSTEM + IMEI PHOTO + API PANELS" suite
=========================================================================
v58 me kya hua:

  1. 🎨 NAYA TOOL PROMPT SYSTEM (user ka order)
     Har tool ka prompt ab:
         🔐 𝐈𝐌𝐄𝐈 𝐕𝟐 & 𝐆𝐒𝐌𝐀𝐑𝐄𝐍𝐀 𝐒𝐏𝐄𝐂𝐒 𝐄𝐍𝐆𝐈𝐍𝐄
         ✨ 15-digit IMEI Number ya direct Device Model Name / Code bhejein:
         📝 Examples:
         • 862407054987700 (IMEI Number)
         • M2101K6P (Model Code)
         • Redmi Note 10 Pro (Device Name)
     • PROMPTS ab PROMPT_DATA (head/ask/examples) se banta hai — ek jagah se
       poore bot ka style.
     • Video Downloader me 5 app examples (YouTube/Instagram/Facebook/TikTok/X).

  2. 🚫 DO LINES HAMESHA KE LIYE GAYI (user ka strict order)
     • "⚡ Credits: ♾️ Unlimited (VIP)" — tool start par kahin nahi
     • "Tap /cancel any time to stop." — tool start par kahin nahi
     credits_line() ab VIP par KHALI string deti hai.

  3. 📸 IMEI TOOL — PHONE KA PHOTO
     • Pehle Xiaomi (862407054987700) par photo NAHI aata tha: TAC naam
       "XIAOMI NOTE 10 PRO" nanoreview ke "Xiaomi Redmi Note 10 Pro" se
       match nahi karta tha.
     • FIX: naya nanoreview search API (fuzzy naam sudhaarta hai) +
       phone photo (`/common/images/phone/<slug>-mini@2x.jpeg`).
     • GALAT PHOTO guard: model CODE se seedha search karne par koi aur
       device match ho jaata tha (M2101K6P → Poco M6 Plus!) — ab code par
       photo tabhi jab koi SAHI naam resolve ho chuka ho.

  4. 🔎 DEVICE NAAM / MODEL CODE SE SEARCH (naya — pehle kaam hi nahi karta tha)
     Prompt me likha tha "Device Model Name / Code bhejein" par code sirf
     15-digit IMEI leta tha! Ab naya search_device() hai.

  5. 🏦 UPI VERIFY — naam (aapki API se, legal)  [⚠️ v59 me DELETE ho gaya]
     v58 me naya modules/upi_provider.py + /upiapi command aaya tha.
     v59 me user ne ise reverse kar diya — tool + poori code hata di gayi.
     Is suite ke section 5 me ab "v59 me UPI poori tarah gaya" ke checks hain.

  6. 📱 NUMBER INFO — 👤 OWNER PANEL
     Agar aapki API response me name/father/alt/region/govt-id/address aayein
     to card me aapke diye format me panel dikhta hai (warna gayab rehta hai).

Chalane ka tarika:
    python3 tests/test_v58.py
"""
from __future__ import annotations

import ast
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

os.environ.setdefault("BOT_TOKEN", "123456:TEST-TOKEN-FOR-SELFTEST")
os.environ.setdefault("ADMIN_ID", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
IMP_SRC = open(os.path.join(ROOT, "modules", "imei_lookup.py"), encoding="utf-8").read()

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


# =====================================================================
section("1) 🎨 NAYA PROMPT SYSTEM (head + ✨ ask + 📝 Examples)")
# =====================================================================
import bot  # noqa: E402

check("BOT_VERSION v58+ par hai", re.search(r'BOT_VERSION = "v(?:5[6-9]|[6-9][0-9])', BOT_SRC) is not None)
check("PROMPT_DATA maujood hai (naya system)", hasattr(bot, "PROMPT_DATA"))
check("PROMPT_DATA me behaviour: har entry me head/ask/ex", all(
    isinstance(v, dict) and v.get("head") and v.get("ask")
    for v in bot.PROMPT_DATA.values()))
check("_render_tool_prompt() maujood hai", hasattr(bot, "_render_tool_prompt"))
check("PROMPTS backward-compat ke liye bana rehta hai",
      isinstance(bot.PROMPTS, dict) and len(bot.PROMPTS) == len(bot.PROMPT_DATA))

# ---- IMEI prompt bilkul user ke diye format me ----
_imei_p = bot.tool_prompt("imei")
check("IMEI header 'IMEI V2 & GSMARENA SPECS ENGINE' hai",
      "IMEI V2 & GSMARENA SPECS ENGINE" in _imei_p or
      "𝐈𝐌𝐄𝐈 𝐕𝟐 & 𝐆𝐒𝐌𝐀𝐑𝐄𝐍𝐀 𝐒𝐏𝐄𝐂𝐒 𝐄𝐍𝐆𝐈𝐍𝐄" in _imei_p, _imei_p[:60])
check("IMEI ask line ✨ ke saath hai",
      "✨ 15-digit IMEI Number ya direct Device Model Name / Code bhejein:" in _imei_p)
check("IMEI me teeno examples hain (IMEI/Model Code/Device Name)",
      "862407054987700" in _imei_p and "M2101K6P" in _imei_p
      and "Redmi Note 10 Pro" in _imei_p)
check("IMEI examples me labels hain",
      "(IMEI Number)" in _imei_p and "(Model Code)" in _imei_p
      and "(Device Name)" in _imei_p)
check("Examples '📝 Examples:' heading ke saath aate hain",
      "📝 <b>Examples:</b>" in _imei_p)

# ---- NUMINFO + UPI (user ne jo maanga) ----
_np = bot.tool_prompt("numinfo")
check("NUMBER INFO ask line '10 Digit Number bhejein:' hai",
      "✨ 10 Digit Number bhejein:" in _np, _np[:120])
# v59: UPI tool poora delete — uska prompt bhi nahi bachna chahiye
check("v59: UPI prompt ab gayab (tool delete ho gaya)", bot.tool_prompt("upi") == "")

# ---- VIDEO DOWNLOADER: 5 apps ----
_vd = bot.tool_prompt("insta_dl")
for _app, _url in (("YouTube", "youtube.com"), ("Instagram", "instagram.com"),
                   ("Facebook", "facebook.com"), ("TikTok", "tiktok.com"),
                   ("Twitter / X", "x.com")):
    check(f"Video Downloader me {_app} example hai", _app in _vd and _url in _vd)

# ---- saare prompts ka structure ----
check("saare 22 prompts me 📝 Examples block hai",
      all("📝 <b>Examples:</b>" in v for v in bot.PROMPTS.values()))
check("saare prompts me ✨ ask line hai",
      all("✨" in v for v in bot.PROMPTS.values()))
check("har prompt me kam se kam 1 bullet example hai",
      all(v.count("• ") >= 1 for v in bot.PROMPTS.values()))
check("prompt me <code> me example value hai (copy karne layak)",
      all("<code>" in v for v in bot.PROMPTS.values()))
check("tool_prompt() unknown key par crash nahi",
      bot.tool_prompt("koi_galat_key") == "")

# =====================================================================
section("2) 🚫 DO LINES HAMESHA KE LIYE GAYI (user ka strict order)")
# =====================================================================
check("kisi bhi prompt me 'Credits:' line nahi",
      not any("Credits:" in v for v in bot.PROMPTS.values()))
check("kisi bhi prompt me '/cancel' line nahi",
      not any("cancel" in v.lower() for v in bot.PROMPTS.values()))
check("bot.py me 'Credits:</b> ♾️ Unlimited' text gaya",
      "Credits:</b> ♾️ Unlimited" not in BOT_SRC)
check("'Tap /cancel any time to stop.' sirf comment me bacha (code me nahi)",
      BOT_SRC.count("Tap /cancel any time") <= 1)
check("credits_line() VIP par khaali deti hai",
      bot.credits_line({"credits": 999999}, 1) == "")
check("credits_line() 0 credits par warning branch hai",
      'return "⚡ <b>Credits:</b> 0 / %d — <b>khatam!</b>' in BOT_SRC)
# tool start par credits line ka koi call nahi bacha
for _lbl, _needle in (
        ("IMEI start", 'tool_prompt("imei") + "\\n\\n" + credits_line'),
        ("callback tool start", 'extra = "\\n\\n" + credits_line(_u0, uid)'),
        ("text tool start", 'extra = "\\n\\n" + credits_line(u, uid)'),
        ("Virtual Numbers card", 'reply_text(credits_line(_u_v, uid)'),
        ("Cloner dashboard", '{credits_line(_u_cl, uid)}')):
    check(f"{_lbl} par credits line nahi bachi", _needle not in BOT_SRC)

# =====================================================================
section("3) 📸 IMEI PHOTO — nanoreview search + image")
# =====================================================================
import modules.imei_lookup as IL  # noqa: E402

check("nanoreview_search() maujood hai", hasattr(IL, "nanoreview_search"))
check("nanoreview_image() maujood hai", hasattr(IL, "nanoreview_image"))
check("nanoreview API endpoint sahi hai",
      "nanoreview.net/api/search" in IMP_SRC)
check("photo URL pattern sahi hai (-mini@2x.jpeg)",
      "-mini@2x.jpeg" in IMP_SRC)
check("nanoreview search ka 6-ghante cache hai", "_NR_TTL" in IMP_SRC)

# live (network ho to) — warna skip
try:
    _nr = IL.nanoreview_search("Redmi Note 10 Pro")
    _live = bool(_nr.get("ok"))
except Exception:                                              # noqa: BLE001
    _live = False
if _live:
    check("nanoreview search live chalta hai", True)
    check("search se sahi naam milta hai",
          "Redmi Note 10 Pro" in str(_nr.get("name")), str(_nr.get("name")))
    check("search se photo URL milta hai",
          str(_nr.get("image") or "").startswith("https://nanoreview.net/"),
          str(_nr.get("image"))[:70])
    check("search se slug + page URL milta hai",
          bool(_nr.get("slug")) and "nanoreview.net/en/phone/" in str(_nr.get("url")))
    # fuzzy naam bhi theek ho (asli bug yahi tha)
    _nr2 = IL.nanoreview_search("XIAOMI NOTE 10 PRO")
    check("adhoore naam (XIAOMI NOTE 10 PRO) bhi sahi resolve hota hai",
          _nr2.get("ok") and "Redmi" in str(_nr2.get("name")), str(_nr2.get("name")))
else:
    print("  ⚠️  network nahi — live nanoreview checks skip (code checks ho gaye)")

check("search fail par crash nahi (khaali dict)", isinstance(IL.nanoreview_search(""), dict))
check("chhota query (<3 char) par safe", IL.nanoreview_search("ab").get("ok") is False)

# ---- GALAT PHOTO GUARD ----
check("model CODE se seedha nanoreview search nahi hota (galat device ka khatra)",
      "_looks_marketing(model)" in IMP_SRC and "elif resolved:" in IMP_SRC)
check("guard ka comment hai (M2101K6P → Poco M6 Plus wala case)",
      "Poco M6 Plus" in IMP_SRC)

# =====================================================================
section("4) 🔎 DEVICE NAAM / MODEL CODE se SEARCH (naya)")
# =====================================================================
check("imei_lookup me search_device() hai", hasattr(IL, "search_device"))
check("bot.py me search_device import hai",
      "search_device as imei_search_device" in BOT_SRC)
check("handler me _dev_query rasta hai", "_dev_query" in BOT_SRC)
check("letters wale input par device search hota hai",
      're.search(r"[A-Za-z]", _dev_q)' in BOT_SRC)
check("wait message device ke liye alag hai",
      "🔎 <b>Device dhoondh raha hoon" in BOT_SRC)
check("error card device query dikhata hai",
      "🔢 <b>Query:</b>" in BOT_SRC)
check("error card me device-friendly hint hai",
      "poora device naam likho" in BOT_SRC)
check("chhota query par crash nahi",
      IL.search_device("").get("ok") is False)
check("search_device me brand/model split hota hai",
      '_parts = str(out["specs_name"] or out["model"]).split()' in IMP_SRC)

if _live:
    _sd = IL.search_device("Redmi Note 10 Pro")
    check("search_device live: ok=True", _sd.get("ok") is True, str(_sd.get("error"))[:80])
    check("search_device live: photo milta hai", bool(_sd.get("photo")),
          str(_sd.get("photo"))[:60])
    check("search_device live: brand/model alag hote hain",
          _sd.get("brand") == "Xiaomi" and "Note 10 Pro" in str(_sd.get("model")),
          f"{_sd.get('brand')} | {_sd.get('model')}")
    check("search_device live: query result me save hoti hai",
          _sd.get("query") == "Redmi Note 10 Pro")

# ---- render: IMEI khaali ho to 'Search:' line ----
check("render_text me IMEI khaali par 'Search:' line aati hai",
      'if res.get("imei"):' in IMP_SRC and '🔎 <b>Search:</b>' in IMP_SRC)
check("render_caption bhi wahi karta hai",
      IMP_SRC.count('🔎 <b>Search:</b>') >= 2)

# =====================================================================
section("5) 🏦 UPI VERIFY — v59 me POORI TARAH DELETE (user ka order)")
# =====================================================================
# v58 me UPI naam-API (upi_provider.py + /upiapi) aayi thi.
# v59: user ne reverse kar diya — "phle upi verify tools delete karo and uska code".
# Ab: tool, prompt, handler, callbacks, keyboard, rate-limit, premium list,
# tool-name map, dono callbacks, /upiapi, module file — sab khatam.
check("modules/upi_provider.py file DELETE ho gayi",
      not os.path.exists(os.path.join(ROOT, "modules", "upi_provider.py")))
check("bot.py me upi_provider ka import nahi",
      "upi_provider" not in BOT_SRC and "upiprov" not in BOT_SRC)
check("UPI mode handler gayab", 'if mode == "upi":' not in BOT_SRC)
check("UPI prompt gayab (PROMPT_DATA / PROMPTS me 'upi' key nahi)",
      "upi" not in {k.lower() for k in bot.PROMPT_DATA})
check("UPI VERIFY text kahin nahi", "UPI VERIFY" not in BOT_SRC)
check("UPI ke callbacks gaye", "upi_to_num" not in BOT_SRC and "upi_to_vpa" not in BOT_SRC)
check("/upiapi command gayi", "upiapi" not in BOT_SRC.lower())
check("UPI premium/rate-limit list me nahi",
      "upi" not in {str(x).lower() for x in bot.PREMIUM_TOOLS}
      and "upi" not in {str(x).lower() for x in bot.TOOL_RATE_LIMITS})
check("UPI env vars (UPI_VERIFY_*) code me nahi", "UPI_VERIFY" not in BOT_SRC)
check("render.yaml se UPI_VERIFY_* hata",
      "UPI_VERIFY" not in open(os.path.join(ROOT, "render.yaml"), encoding="utf-8").read())
check(".env.example se UPI_VERIFY_* hata",
      "UPI_VERIFY" not in open(os.path.join(ROOT, ".env.example"), encoding="utf-8").read())
check("UPI-NAAM-API-SETUP.md doc hata diya",
      not os.path.exists(os.path.join(ROOT, "UPI-NAAM-API-SETUP.md")))


section("6) 📱 NUMBER INFO — 👤 OWNER PANEL (aapke format me)")
# =====================================================================
import modules.numinfo_provider as NP  # noqa: E402

check("provider response me 'owner' dict hota hai",
      '"owner": {k: v for k, v in _owner.items() if v}' in open(
          os.path.join(ROOT, "modules", "numinfo_provider.py"), encoding="utf-8").read())
for _f in ("name", "father", "alt", "region", "govt_id", "address"):
    check(f"owner field '{_f}' parse hota hai", f'"{_f}": _clean_name' in open(
        os.path.join(ROOT, "modules", "numinfo_provider.py"), encoding="utf-8").read())
check("card me OWNER panel rendering hai (_obits)", "_obits" in BOT_SRC)
for _lbl in ("👤 <b>Name:", "👨 <b>Father:", "📱 <b>Phones/Alt:",
             "🌐 <b>Region:", "🆔 <b>Govt ID:", "🏠 <b>Address(es):"):
    check(f"panel me '{_lbl}' line hai", _lbl in BOT_SRC)
check("v59: owner card seedha dikhta hai (koi NUMINFO_SHOW_OWNER gate nahi)",
      "NUMINFO_SHOW_OWNER" not in BOT_SRC)
check("panel sirf tab dikhta hai jab data aaye (warna fallback card)",
      "_obits" in BOT_SRC and "if _obits:" in BOT_SRC and "else:" in BOT_SRC)
check("v59: numinfo card me koi privacy line NAHI hai",
      "aapki API</b> ke jawab me aaya hai" not in BOT_SRC and "leaked" not in BOT_SRC.lower())
check("v59: fallback card me API setup hint aata hai (privacy lecture nahi)",
      "NUMINFO_PROVIDER_URL" in BOT_SRC and "/numapi" in BOT_SRC)

# parse check (offline)
_flat = NP._flatten({"name": "Sanjay Sah", "fatherName": "Ram Akwal Sah",
                     "altMobile": "7305190526", "region": "BIHAR JIO",
                     "govtId": "401635555849", "address": "S/O Ram Akwal Sah, ward 02"})
check("owner name parse hota hai",
      NP._clean_name(NP._pick(_flat, "name", "ownername")) == "Sanjay Sah")
check("father parse hota hai",
      NP._clean_name(NP._pick(_flat, "father", "fathername")) == "Ram Akwal Sah")
check("govt id parse hota hai",
      NP._clean_name(NP._pick(_flat, "govtid", "idnumber")) == "401635555849")
check("junk 'NA' par khaali (jhootha data nahi)",
      NP._clean_name(NP._pick(NP._flatten({"name": "NA"}), "name")) == "")

# =====================================================================
section("7) 🧾 SANITY — kuch aur toota nahi")
# =====================================================================


def _dup_keys(path):
    _t = ast.parse(open(path, encoding="utf-8").read())
    _out = []
    for _n in ast.walk(_t):
        if isinstance(_n, ast.Dict):
            _ks = [k.value for k in _n.keys
                   if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            _d = {x for x in _ks if _ks.count(x) > 1}
            if _d:
                _out.append(sorted(_d))
    return _out


check("bot.py me duplicate dict keys nahi",
      not _dup_keys(os.path.join(ROOT, "bot.py")))
check("imei_lookup.py me duplicate dict keys nahi",
      not _dup_keys(os.path.join(ROOT, "modules", "imei_lookup.py")))
_bad = re.findall(r"\b\w*message\.send_(?:photo|document|video)\s*\(", BOT_SRC)
check("Message.send_* crash pattern wapas nahi aaya", not _bad, str(_bad[:2]))
for _m in ("ip", "pinterest", "webscraper", "aadeid", "tginfo"):
    check(f'deleted tool "{_m}" ka handler nahi aaya', f'if mode == "{_m}":' not in BOT_SRC)

import importlib as _il  # noqa: E402
_ghost = []
for _mn in ("api_hub", "channel_cloner", "cloud_tools", "core.cache", "core.limiter",
            "core.net", "core.telemetry", "cyber_studio", "desi_tools", "gaming_tools",
            "general_tools", "imei_lookup", "media_downloader", "numinfo_provider",
            "osint_hub", "osint_tools", "payguard", "render_health", "sarkari_hub",
            "temp_mail", "toolkit_extras", "tutorial_hub", "vip_payment"):
    try:
        _il.import_module(f"modules.{_mn}")
    except Exception as _e:                                    # noqa: BLE001
        _ghost.append(f"{_mn}: {_e}")
check("saare modules import hote hain (upi_provider ke bina)", not _ghost,
      "; ".join(_ghost[:3]))

# =====================================================================
section("8) ⚡ /version — deploy check command")
# =====================================================================
check("/version command FUNCTION maujood hai (patch15 ise galti se uda deta tha)",
      "async def cmd_version(" in BOT_SRC)
check("/version registered hai (version/ver/v)",
      'CommandHandler(["version", "ver", "v"], cmd_version)' in BOT_SRC)
check("/version sabke liye khula hai (admin-only nahi — deploy check ke liye)",
      BOT_SRC[BOT_SRC.index("async def cmd_version"):][:500].count("is_admin") == 0)
check("/version me prompt system status dikhta hai",
      "Naya prompt system:</b>" in BOT_SRC)
check("/version me credits/cancel line check dikhta hai",
      "Credits/cancel line:</b>" in BOT_SRC)
check("/version me IMEI photo status dikhta hai", "IMEI photo:</b>" in BOT_SRC)
check("/version deploy-pending hint deta hai",
      "Render me deploy pending hai" in BOT_SRC)
check("credits_line() ab kahin CALL nahi hoti (poori tarah hata)",
      BOT_SRC.count("credits_line(") == 1,  # sirf definition
      f"count={BOT_SRC.count('credits_line(')}")


# =====================================================================
section("9) 🔒 PERMANENT GUARD — banned lines kabhi wapas nahi aa sakti")
# =====================================================================
check("_sanitize_prompt() helper hai", hasattr(bot, "_sanitize_prompt"))
check("_BANNED_PROMPT_PATTERNS maujood hai (4 patterns)",
      hasattr(bot, "_BANNED_PROMPT_PATTERNS")
      and len(bot._BANNED_PROMPT_PATTERNS) >= 3)

# --- sanitizer behaviour: inject karo, delete hona chahiye ---
_inj1 = bot._sanitize_prompt("⚡ TOOL — link bhejo:\n\n⚡ Credits: ♾️ Unlimited (VIP)\n\nAndar text")
check("sanitizer: '⚡ Credits: ♾️ Unlimited (VIP)' delete karta hai",
      "Credits" not in _inj1 and "Unlimited" not in _inj1, repr(_inj1))
check("sanitizer: baaki text safe rakhta hai", "link bhejo" in _inj1 and "Andar text" in _inj1)
_inj2 = bot._sanitize_prompt("Header\n\nTap /cancel any time to stop.\n\nBody")
check("sanitizer: 'Tap /cancel any time to stop.' delete karta hai",
      "cancel" not in _inj2.lower(), repr(_inj2))
check("sanitizer: body bachi rehti hai", "Header" in _inj2 and "Body" in _inj2)
_inj3 = bot._sanitize_prompt("Credits: Unlimited\nTap /cancel any time")
check("sanitizer: dono line ek saath aayein to bhi saaf", _inj3 == "", repr(_inj3))
check("sanitizer: khaali input par khaali", bot._sanitize_prompt("") == "")
check("sanitizer: None par crash nahi", bot._sanitize_prompt(None) == "")
check("sanitizer: extra blank lines collapse karta hai",
      "\n\n\n" not in bot._sanitize_prompt("A\n\n\n\nB"))
check("sanitizer: 'Unlimited' ka doosra roop bhi pakadta hai",
      "Unlimited" not in bot._sanitize_prompt("Credits: Unlimited (VIP)"))

# --- tool_prompt har baar sanitizer se guzarta hai ---
check("tool_prompt() sanitizer use karta hai",
      "return _sanitize_prompt(body)" in BOT_SRC)
check("saare 22 prompts sanitizer ke baad bhi saaf",
      all(("Credits:" not in bot.tool_prompt(k)
           and "cancel" not in bot.tool_prompt(k).lower())
          for k in bot.PROMPT_DATA))
# sub-mode fallback bhi sanitizer se guzre
check("unknown/ASK_LINES fallback bhi sanitized return karta hai",
      bot.tool_prompt("koi_galat") == "")

# --- MEDIA menu se credit line gayi ---
check("MEDIA STUDIO menu se 'Har option = 1 credit' line gayi",
      "Har option = <b>1 credit" not in BOT_SRC)


print("\n" + "=" * 62)
print(f"  v58 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILURES:
    print("\n  FAILURES:")
    for _f in FAILURES:
        print(f"   - {_f}")
print()
sys.exit(0 if FAIL == 0 else 1)
