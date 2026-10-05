# -*- coding: utf-8 -*-
"""
tests/test_v56 — v56 "CRASH-PROOF + 5-TOOL CLEANUP" suite
==========================================================
v56 me do bade kaam hue:

  A) 🚨 ASLI CRASH KI JADD mili aur fix hui
     Render log:  'Message' object has no attribute 'send_photo'
                  'Message' object has no attribute 'send_document'
     Wajah: python-telegram-bot me `send_photo` / `send_document` /
            `send_video` **Bot** par hote hain, **Message** par NAHI.
            Message par sirf `reply_photo` / `reply_document` / `reply_video`
            hote hain. Code 8 jagah `q.message.send_photo(...)` aur
            `update.message.send_document(...)` call kar raha tha → har baar
            AttributeError → user ko "Chhota sa ghatna ho gaya".
     Fix:  wo saare 8 call sites deleted tools ke saath hat gaye (ye suite
           unhe wapas aane se rokta hai).

  B) 🗑️ USER ORDER PAR 5 TOOLS PERMANENTLY DELETE
     1. 🌐 DOMAIN OSINT / IP   (mode "ip")
     2. 📌 PINTEREST           (mode )
     3. 📄 WEB SCRAPER         (mode "webscraper")
     4. 🪪 AADHAAR EID         (mode "aadeid")
     5. 📡 TG PUBLIC INFO      (mode "tginfo")
     Code (keyboard, BTN_MODE_MAP, PROMPTS, rate-limits, premium lists,
     handlers, helpers), modules (.py, web_tools.py,
     osint_tools ke domain/tg functions, desi_tools ka aadhaar helper),
     tests aur docs — sab se.

  C) 🛡️ Extra crash-proofing
     • q.message InaccessibleMessage guard (purane message par crash nahi)
     • yt-dlp "Sign in to confirm you're not a bot" → saaf Hindi message
     • dead-link detection (jo link khulta hi nahi use "SAFE" nahi bolta)
     • raw requests/urllib3 error leak fix

Chalane ka tarika:
    python3 tests/test_v56.py
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
section("1) 🚨 CRASH KI JADD — Message par send_photo/send_document NAHI hote")
# =====================================================================
# PTB ka asli contract: Message par sirf reply_* methods hain.
from telegram import Message  # noqa: E402

check("PTB: Message.send_photo EXIST NAHI karta (yahi crash ki jadd thi)",
      not hasattr(Message, "send_photo"))
check("PTB: Message.send_document EXIST NAHI karta",
      not hasattr(Message, "send_document"))
check("PTB: Message.send_video EXIST NAHI karta",
      not hasattr(Message, "send_video"))
check("PTB: Message.reply_photo EXIST karta hai (sahi tarika)",
      hasattr(Message, "reply_photo"))
check("PTB: Message.reply_document EXIST karta hai",
      hasattr(Message, "reply_document"))

# bot.py me koi bhi `*.message.send_photo(...)` jaisa call bacha ho to FAIL.
_bad_calls = re.findall(
    r"\b\w*message\.send_(?:photo|document|video|audio|animation|media_group|voice)\s*\(",
    BOT_SRC)
check("bot.py me koi `message.send_photo/document/video` call nahi bachi",
      not _bad_calls, f"mila: {_bad_calls[:3]}")

_bad_q = re.findall(r"\bq\.message\.send_(?:photo|document|video|audio|animation)\s*\(", BOT_SRC)
check("bot.py me koi `q.message.send_*` nahi bacha", not _bad_q, f"mila: {_bad_q[:3]}")

# module files me bhi check
for _mod in ("media_downloader", "imei_lookup", "general_tools", "cloud_tools"):
    _p = os.path.join(ROOT, "modules", f"{_mod}.py")
    if os.path.exists(_p):
        _src = open(_p, encoding="utf-8").read()
        _hits = re.findall(r"\bmessage\.send_(?:photo|document|video)\s*\(", _src)
        check(f"modules/{_mod}.py me broken Message.send_* nahi", not _hits,
              f"mila: {_hits[:2]}")

# =====================================================================
section("2) 🗑️ 5 TOOLS PERMANENTLY DELETE — code se poora saaf")
# =====================================================================
import bot  # noqa: E402

_DELETED_MODES = ("ip", , "webscraper", "aadeid", "tginfo")
_DELETED_WORDS = ("tginfo", "aadeid", "webscraper", "pinpick",
                  "scrape_public_text", , "domain_osint",
                  "tg_user_public", "lookup_ip_domain")

# 2a) bot.py me koi ACTIVE handler / import bacha na ho.
# NOTE: purane keyboard walon ke liye _removed_keys / _why / _alt me naam
# JAAN-BOOJH KAR hain (unhe match nahi karna hai) — isliye handler pattern
# check karte hain, plain substring nahi.
for _m in _DELETED_MODES:
    check(f'bot.py me `if mode == "{_m}":` handler nahi bacha',
          f'if mode == "{_m}":' not in BOT_SRC)
for _imp in ("lookup_ip_domain", "domain_osint", "tg_user_public",
             "scrape_public_text", "pinterest_search", "pinterest_from_pin_link",
             "pin_download_media", "_pinpick_download", "_pin_meta_line"):
    check(f"bot.py me '{_imp}' import/call nahi bacha",
          f"    {_imp},\n" not in BOT_SRC and f"{_imp}(" not in BOT_SRC)
# ACTIVE code me sirf removal-message block me hi ye naam ho sakte hain
_code_wo_labels = BOT_SRC
_i = _code_wo_labels.find("    _removed_keys = {")
_j = _code_wo_labels.find("    if action:", _i)
if _i != -1 and _j != -1:
    _code_wo_labels = _code_wo_labels[:_i] + _code_wo_labels[_j:]
for _w in ("tginfo", "aadeid", "webscraper", "pinpick", "scrape_public_text"):
    check(f"bot.py ke ACTIVE code me '{_w}' nahi (labels chhod kar)",
          _w not in _code_wo_labels)

# 2b) dicts / sets
for _m in _DELETED_MODES:
    check(f"PREMIUM_TOOLS me '{_m}' nahi", _m not in bot.PREMIUM_TOOLS)
    check(f"PREMIUM_TOOL_NAMES me '{_m}' nahi", _m not in bot.PREMIUM_TOOL_NAMES)
    check(f"TOOL_RATE_LIMITS me '{_m}' nahi", _m not in bot.TOOL_RATE_LIMITS)
    check(f"PROMPTS me '{_m}' nahi", _m not in bot.PROMPTS)

# 2c) keyboard me purane labels nahi
_kb_labels = [lab for row in bot.KB_BTNS for lab in row]
_kb_txt = " ".join(bot.unbold(x).upper() for x in _kb_labels)
for _label in ("DOMAIN OSINT", "TG PUBLIC INFO", "PINTEREST", "WEB SCRAPER", "AADHAAR"):
    check(f"keyboard me '{_label}' button nahi", _label not in _kb_txt)

# 2d) BTN_MODE_MAP
for _k in ("DOMAIN OSINT / IP", "TG PUBLIC INFO", "PINTEREST", "WEB SCRAPER", "AADHAAR EID"):
    check(f"BTN_MODE_MAP me '{_k}' nahi", _k not in bot.BTN_MODE_MAP)

# 2e) module files delete ho gayi
for _f in ("modules/.py", "modules/web_tools.py"):
    check(f"{_f} delete ho gayi", not os.path.exists(os.path.join(ROOT, _f)))

# 2f) osint_tools se domain/tg functions gaye, baaki zinda hain
import modules.osint_tools as OT  # noqa: E402
for _gone in ("domain_osint", "lookup_ip_domain", "tg_user_public", "_doh_query", "_DOMAIN_RE"):
    check(f"osint_tools.{_gone} hata diya gaya", not hasattr(OT, _gone))
for _alive in ("lookup_phone_info", "lookup_ifsc", "lookup_pincode",
               "search_by_area_name", "upi_verify", "lookup_vehicle_rto"):
    check(f"osint_tools.{_alive} abhi bhi hai (kaam karta rahe)", hasattr(OT, _alive))

# 2g) desi_tools se aadhaar helper gaya
import modules.desi_tools as DT  # noqa: E402
check("desi_tools.aadhaar_eid_helper hata diya gaya",
      not hasattr(DT, "aadhaar_eid_helper"))

# 2h) osint_hub se aadhaar family gaya, baaki zinda
import modules.osint_hub as OH  # noqa: E402
check("osint_hub.aadhaar_family_report hata diya gaya",
      not hasattr(OH, "aadhaar_family_report"))
check("osint_hub.num_info_report abhi bhi hai", hasattr(OH, "num_info_report"))
check("osint_hub.hub_status abhi bhi hai", hasattr(OH, "hub_status"))

# 2i) saare modules import hote hain + __all__ saaf
import importlib as _il  # noqa: E402
_ghost = []
for _mn in ("api_hub", "channel_cloner", "cloud_tools", "core.cache", "core.limiter",
            "core.net", "core.telemetry", "cyber_studio", "desi_tools", "gaming_tools",
            "general_tools", "imei_lookup", "media_downloader", "osint_hub",
            "osint_tools", "payguard", "render_health", "sarkari_hub", "temp_mail",
            "toolkit_extras", "tutorial_hub", "vip_payment"):
    try:
        _m = _il.import_module(f"modules.{_mn}")
    except Exception as _e:                                  # noqa: BLE001
        _ghost.append(f"{_mn}: {_e}")
        continue
    for _n in getattr(_m, "__all__", []):
        if not hasattr(_m, _n):
            _ghost.append(f"{_mn}.__all__ -> {_n} ghost")
check("saare modules import hote hain + __all__ saaf", not _ghost, "; ".join(_ghost[:3]))

# =====================================================================
section("3) 💬 PURANE KEYBOARD WALON KE LIYE FRIENDLY REMOVAL MESSAGE")
# =====================================================================
# _removed_keys (set) aur _why / _alt (dict) — teeno AST se nikalo
_tree = ast.parse(BOT_SRC)
_removed_keys, _why, _alt = set(), {}, {}
for _node in ast.walk(_tree):
    if isinstance(_node, ast.Assign) and isinstance(_node.targets[0], ast.Name):
        _n = _node.targets[0].id
        _v = _node.value
        _d = _v.func.value if isinstance(_v, ast.Call) and isinstance(_v.func, ast.Attribute) else _v
        if _n == "_removed_keys" and isinstance(_v, ast.Set):
            _removed_keys = {e.value for e in _v.elts}
        elif _n == "_why" and isinstance(_d, ast.Dict):
            _why = {k.value: val.value for k, val in zip(_d.keys, _d.values)}
        elif _n == "_alt" and isinstance(_d, ast.Dict):
            _alt = {k.value: val.value for k, val in zip(_d.keys, _d.values)}

_NEW_LABELS = ["DOMAIN OSINT / IP", "DOMAIN OSINT", "OSINT", "DOMAIN INFO",
               "IP INFO", "IP / DOMAIN INFO", "IP", "DOMAIN",
               "PINTEREST", "PINTEREST DOWNLOADER", "PINTEREST SEARCH",
               "WEB SCRAPER", "WEBSCRAPER", "SCRAPER", "WEB SCRAPE",
               "AADHAAR EID", "AADHAAR STATUS", "AADHAAR", "AADHAR", "EID",
               "TG PUBLIC INFO", "TG INFO", "TELEGRAM INFO", "TG PUBLIC"]

check("_removed_keys me v56 ke sabhi 24 labels hain",
      all(k in _removed_keys for k in _NEW_LABELS),
      f"missing={[k for k in _NEW_LABELS if k not in _removed_keys][:4]}")
check("_why me sabhi 24 labels ka friendly naam hai",
      all(k in _why for k in _NEW_LABELS),
      f"missing={[k for k in _NEW_LABELS if k not in _why][:4]}")
check("_alt me sabhi 24 labels ka 'kya use karo' suggestion hai",
      all(k in _alt for k in _NEW_LABELS),
      f"missing={[k for k in _NEW_LABELS if k not in _alt][:4]}")

# sabse zaroori: koi ZINDA tool galti se removed_keys me na aa jaye
_conflict = set(bot.BTN_MODE_MAP) & _removed_keys
check("koi bhi ZINDA button galti se 'removed' me nahi hai", not _conflict,
      f"conflict={sorted(_conflict)[:5]}")

# "PIN" jaisa generic label galti se Pincode tool ko na khaye
check("'PIN' standalone label removed_keys me nahi (Pincode tool zinda rahe)",
      "PIN" not in _removed_keys)

# _why = chhota label (jaise "📌 Pinterest"), _alt = "kya use karo" suggestion.
# Final user message:  "ℹ️ {_why} hata diya gaya hai.\n• {_alt}"
for _k in ("PINTEREST", "AADHAAR EID", "TG PUBLIC INFO", "WEB SCRAPER", "DOMAIN OSINT / IP"):
    check(f"'{_k}' ka label chhota hai (naam hi dikhe)",
          0 < len(str(_why[_k])) <= 24, str(_why[_k])[:50])
    check(f"'{_k}' ke liye alternative diya gaya hai",
          len(str(_alt[_k])) > 25, str(_alt[_k])[:50])
# har label ka real aur readable naam ho
check("_why labels me emoji + naam hai (yaise 'Ye tool' default nahi)",
      all(str(_why[_k]).strip() and _why[_k] != "Ye tool" for _k in _NEW_LABELS))

# =====================================================================
section("4) 🛡️ InaccessibleMessage GUARD (callback crash khatam)")
# =====================================================================
check("on_cb me cbmsg() safe helper hai", "async def cbmsg()" in BOT_SRC)
check("cbmsg() purane message ko detect karta hai",
      "is_accessible" in BOT_SRC)
check("cbmsg() chat fallback deta hai (naya message bhej sake)",
      "effective_chat" in BOT_SRC)
check("on_cb me guard comment hai (future dev samjhe)",
      "INACCESSIBLE MESSAGE GUARD" in BOT_SRC)

# =====================================================================
section("5) 🤖 yt-dlp ERRORS → SAFF HINDI MESSAGE (raw traceback nahi)")
# =====================================================================
import modules.media_downloader as MD  # noqa: E402

check("friendly_dl_error() maujood hai", hasattr(MD, "friendly_dl_error"))
check("last_dl_error() maujood hai", hasattr(MD, "last_dl_error"))

# asli Render log wala error
MD._remember(Exception(
    "ERROR: [youtube] yaQCKQMiLo: Sign in to confirm you're not a bot. "
    "Use --cookies-from-browser or --cookies for the authentication."))
_msg = MD.friendly_dl_error()
check("bot-check error pe saaf message aata hai (bina 'cookies' jargon)",
      "bot-check" in _msg and "--cookies" not in _msg, _msg[:70])
check("bot-check message me credit-safety line hai", "credit nahi kata" in _msg.lower())

_cases = [
    ("ERROR: Video unavailable", "available nahi"),
    ("ERROR: This video is private", "private"),
    ("ERROR: Sign in to confirm your age", "age"),
    ("HTTP Error 429: Too Many Requests", "rate-limit"),
    ("ERROR: Requested format is not available", "quality"),
    ("Connection timed out", "connection slow"),
    ("ERROR: This live event will begin in 3 hours", "live"),
]
for _raw, _expect in _cases:
    MD._remember(Exception(_raw))
    _m = MD.friendly_dl_error()
    check(f"'{_raw[:34]}…' → friendly ({_expect})",
          _expect in _m and "<b>" in _m, _m[:60])

MD._remember(Exception("kuch bilkul anjaan error zzz"))
_generic = MD.friendly_dl_error()
check("anjaan error par bhi friendly fallback (traceback nahi)",
      "download abhi nahi ho paya" in _generic and "Traceback" not in _generic)

# raw technical text kabhi leak na ho
for _t in ("HTTPSConnectionPool", "urllib3", "Traceback (most recent call last)"):
    check(f"output me '{_t}' leak nahi hota", _t not in _generic)

check("bot.py friendly_dl_error import karta hai", "friendly_dl_error," in BOT_SRC)
check("ytq handler friendly error use karta hai",
      "friendly_dl_error(platform=" in BOT_SRC)

# =====================================================================
section("6) 🔌 DEAD-LINK DETECTION (khulta hi nahi to 'SAFE' nahi)")
# =====================================================================
import modules.toolkit_extras as TE  # noqa: E402

check("friendly_net_error() maujood hai", hasattr(TE, "friendly_net_error"))
check("analyze_link me 'reachable' signal hai",
      "_reachable" not in TE.analyze_link.__doc__ and "reachable" in
      open(os.path.join(ROOT, "modules", "toolkit_extras.py"), encoding="utf-8").read())

_dead = TE.analyze_link("junk.nonexistent-xyz-qq-zz.com")
check("dead domain par reachable=False", _dead["signals"].get("reachable") is False)
check("dead domain par 'SAFE ✅' NAHI bolta",
      "SAFE" not in str(_dead.get("verdict")), str(_dead.get("verdict")))
check("dead domain ka saaf reason milta hai",
      any("khulta nahi" in r for r in _dead.get("reasons", [])))
check("dead link ka advice OTP-warning deta hai",
      "OTP" in str(_dead.get("advice")))

_live = TE.analyze_link("https://www.google.com")
check("zinda domain par reachable=True", _live["signals"].get("reachable") is True)
check("zinda clean domain par 'SAFE ✅' hi aata hai",
      "SAFE" in str(_live.get("verdict")), str(_live.get("verdict")))

# raw error leak check
_exp = TE.expand_url("http://junk.nonexistent-xyz-qq-zz.invalid")
check("expand_url dead host par ok=False", _exp.get("ok") is False)
check("expand_url ka error raw urllib3 text nahi hai",
      "HTTPSConnectionPool" not in str(_exp.get("error"))
      and "urllib3" not in str(_exp.get("error")), str(_exp.get("error"))[:80])

# =====================================================================
section("7) 🧾 VERSION + FILE HYGIENE")
# =====================================================================
check("BOT_VERSION v56+ par hai", 'BOT_VERSION = "v57.' in BOT_SRC)
# duplicate keys — asli check
def _dup_keys(path):
    _t = ast.parse(open(path, encoding="utf-8").read())
    _out = []
    for _node in ast.walk(_t):
        if isinstance(_node, ast.Dict):
            _ks = [k.value for k in _node.keys
                   if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            _dup = {x for x in _ks if _ks.count(x) > 1}
            if _dup:
                _out.append(sorted(_dup))
    return _out


check("bot.py me duplicate dict keys nahi", not _dup_keys(os.path.join(ROOT, "bot.py")),
      str(_dup_keys(os.path.join(ROOT, "bot.py"))[:2]))

# purane _selftest dev scripts hata diye (tests/ unki jagah hai)
for _old in ("_selftest_v50.py", "_selftest_v55_live.py", "_selftest_v45.py",
             "_verify_v49.py"):
    check(f"purana dev script {_old} hata diya gaya",
          not os.path.exists(os.path.join(ROOT, _old)))

print("\n" + "=" * 62)
print(f"  v56 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILURES:
    print("\n  FAILURES:")
    for _f in FAILURES:
        print(f"   - {_f}")
print()
sys.exit(0 if FAIL == 0 else 1)
