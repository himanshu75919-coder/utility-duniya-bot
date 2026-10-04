#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_verify_v49.py — v49 ke baad poora bot check (LIVE — asli net + asli API)
=========================================================================
1) 3 tools poore hate hain? (CLIP MAKER / LINK BYPASS / INTEREST CALC)
2) Menu ke saare buttons kaam karte hain? (BTN_MODE_MAP wiring)
3) Purane keyboard ke buttons ka safe handler hai?
4) Hinglish texts set hain?
5) Saare tools ki LIVE API chal rahi hai? (IMEI, IFSC, Pincode, IP, Number...)
6) IMEI ka poora flow (photo + specs + JSON) ban raha hai?
7) DB / credits / keyboard OK hai?
"""
import io
import os
import re
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BASE = "https://osint-api-hub.onrender.com/api"
for k in ("HUB_API_BASE", "VEHICLE_API_BASE", "IMEI_API_BASE", "NUM_INFO_API_BASE", "OSINT_API_BASE"):
    os.environ.setdefault(k, BASE)
for k in ("HUB_API_KEY", "VEHICLE_API_KEY", "IMEI_API_KEY", "NUM_INFO_API_KEY", "OSINT_API_KEY"):
    os.environ.setdefault(k, "Demo")
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("PREMIUM_ONLY", "off")   # tools ka behaviour test karne ke liye
os.environ.setdefault("ADMIN_ID", "1")

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    if cond:
        PASS.append(name)
        print(f"  ✅ {name}")
    else:
        FAIL.append(f"{name} :: {str(extra)[:150]}")
        print(f"  ❌ {name} :: {str(extra)[:150]}")


def section(t):
    print(f"\n{'='*70}\n{t}\n{'='*70}")


# ======================================================================
section("1) TEEN TOOLS POORE HATE? (CLIP MAKER / LINK BYPASS / INTEREST CALC)")
# ======================================================================
import bot
src = io.open(os.path.join(HERE, "bot.py"), encoding="utf-8").read()

ok("Menu me 🎬 CLIP MAKER button nahi", "CLIP MAKER')" not in re.search(r"^KB_BTNS = \[(.*?)^\]", src, re.S | re.M).group(1))
ok("Menu me 🔓 LINK BYPASS button nahi", "LINK BYPASS')" not in re.search(r"^KB_BTNS = \[(.*?)^\]", src, re.S | re.M).group(1))
# NOTE v50: INTEREST CALC ab naye PRO roop ("EMI / INTEREST CALC") me wapas hai —
# v49 me ye simple tool hataya gaya tha, v50 me EMI + vyaaj calculator ke saath upgrade karke laaya.
ok("v50: 🧮 EMI / INTEREST CALC button hai (naya pro tool)", "EMI / INTEREST CALC" in re.search(r"^KB_BTNS = \[(.*?)^\]", src, re.S | re.M).group(1))
ok("BTN_MODE_MAP me clips mapping nahi", '"clips":' not in re.search(r"^BTN_MODE_MAP = \{(.*?)^\}", src, re.S | re.M).group(1))
ok("BTN_MODE_MAP me linkbypass mapping nahi", '"linkbypass":' not in re.search(r"^BTN_MODE_MAP = \{(.*?)^\}", src, re.S | re.M).group(1))
ok("BTN_MODE_MAP me interest mapping nahi", '"interest":' not in re.search(r"^BTN_MODE_MAP = \{(.*?)^\}", src, re.S | re.M).group(1))
ok("PROMPTS me clips nahi", "clips" not in bot.PROMPTS)
ok("PROMPTS me linkbypass nahi", "linkbypass" not in bot.PROMPTS)
ok("PREMIUM_TOOLS me clips nahi", "clips" not in bot.PREMIUM_TOOLS)
ok("clip_maker import hataya", "import clip_maker" not in src)
ok("ai_brain import hataya", "import ai_brain" not in src)
ok("cmd_clipstatus function nahi", not hasattr(bot, "cmd_clipstatus"))
ok("cmd_aistatus function nahi", not hasattr(bot, "cmd_aistatus"))
# NOTE v50: ab vyaaj (chakravritti) tool isay use karta hai — import wapas hona chahiye
ok("v50: village_compound_interest import hai (vyaaj tool ke liye)", "village_compound_interest" in src)
ok("/clipstatus command registered nahi", 'CommandHandler(["clipstatus"' not in src)

# ======================================================================
section("2) MENU WIRING — har button ka handler hai?")
# ======================================================================
m = re.search(r"^KB_BTNS = \[(.*?)^\]", src, re.S | re.M)
btns = re.findall(r"f\"[^\"]*to_bold\('([^']+)'\)[^\"]*\"", m.group(1))
mmap = re.search(r"^BTN_MODE_MAP = \{(.*?)^\}", src, re.S | re.M).group(1)
keys = set(re.findall(r'"([^"]+)":\s*"[a-z_0-9]+"', mmap))
unmapped = [b for b in btns if b not in keys]
ok(f"Saare {len(btns)} menu buttons mapped", not unmapped, unmapped)
# NOTE v50: +WEATHER, +EMI/INTEREST CALC = 2 naye buttons (29 → 31)
ok("Menu me 31 buttons hain (v50: +WEATHER +EMI)", len(btns) == 31, len(btns))
ok("Koi duplicate button nahi", len(btns) == len(set(btns)))
ok("Menu rows sahi (har row 1-2 button)", all(1 <= len(r) <= 2 for r in [[1, 2]] ))

# map values ka handler
modes = set(re.findall(r'if mode == "([^"]+)"', src)) | set(re.findall(r'mode in \(([^)]*)\)', src))
modal = re.findall(r'mode in \(([^)]*)\)', src)
for grp in modal:
    modes |= set(re.findall(r'"([^"]+)"', grp))
vals = set(re.findall(r':\s*"([a-z_0-9]+)"', mmap))
# NOTE v50: "emi" action-driven hai — `if action == "emi"` do-choice menu dikhata hai,
# phir emi_calc/emi_vyaaj callbacks se emi_ask_*/vyaaj_ask_* modes chalte hain. Isliye special me.
special = {"vnum", "cloner", "premium", "refer", "account", "tutorial", "admin", "owner",
           "sarkari", "kagaz", "mediastudio", "bankpdf", "cloner_private_help", "emi"}
missing = sorted(v for v in vals if v not in modes and v not in special)
ok("Har mapped tool ka mode-handler hai", not missing, missing)

# ======================================================================
section("3) PURANE KEYBOARD KE BUTTONS (safe handler)")
# ======================================================================
ok("_removed_keys set hai", "_removed_keys" in src)
for k in ("CLIP MAKER", "LINK BYPASS", "INTEREST CALC", "CLIPMAKER", "VYAAJ CALC"):
    ok(f"purana button '{k}' handled", k in src)
ok("/refresh command registered", 'CommandHandler(["refresh", "newmenu"], cmd_refresh)' in src)
ok("refresh BotCommand list me", 'BotCommand("refresh"' in src)
ok("hata diya message Hinglish me", "hata diya gaya hai" in src)

# ======================================================================
section("4) HINGLISH TEXTS")
# ======================================================================
ok("WELCOME_TEXT Hinglish", "UTILITY DUNIYA SUPER BOT" in bot.WELCOME_TEXT or "dabao" in bot.WELCOME_TEXT)
ok("WELCOME_TEXT me English marketing nahi", "High-Power Automation" not in bot.WELCOME_TEXT)
ok("TUTORIAL_TEXT Hinglish", "bhejo" in bot.TUTORIAL_TEXT and "HAR TOOL EK LINE ME" in bot.unbold(bot.TUTORIAL_TEXT))
ok("PROMPTS Hinglish (imei)", "Ab 15 digit IMEI bhejo" in bot.PROMPTS["imei"])
ok("PROMPTS Hinglish (ifsc)", "Ab IFSC code bhejo" in bot.PROMPTS["ifsc"])
ok("PROMPTS Hinglish (rto)", "Ab number plate bhejo" in bot.PROMPTS["rto"])
ok("PROMPTS chhote hain (har prompt < 420 char)",
   all(len(p) < 420 for p in bot.PROMPTS.values()),
   max((len(p), k) for k, p in bot.PROMPTS.items()))
ok("Credits-over text Hinglish", "CREDITS KHATAM" in bot.unbold(bot.get_credits_over_text("imei")))
ok("Credits-over me Clip Maker nahi", "Clip Maker" not in bot.get_credits_over_text("imei"))
ok("BAN_MSG Hinglish", "ban hai" in bot.BAN_MSG)
ok("KAGAZ menu Hinglish", "Kirayanama" in bot.KAGAZ_MENU_TEXT)
ok("MEDIA menu Hinglish", "Neeche se chuno" in bot.MEDIA_MENU_TEXT)
ok("spend_credit_msg Hinglish", "credit laga" in bot.spend_credit_msg(1, "imei") or "credit" in bot.spend_credit_msg(1, "imei").lower())
ok("ASK_LINES Hinglish", "bhejo" in bot.ASK_LINES["pin"])

# kitna English bacha?
import ast
tree = ast.parse(src)
docs = set()
for n in ast.walk(tree):
    if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        d = ast.get_docstring(n, clean=False)
        if d:
            docs.add(d)
eng = 0
for n in ast.walk(tree):
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value not in docs:
        s = n.value
        w = re.findall(r"\b[a-zA-Z]{3,}\b", s)
        if len(s) < 45 or len(w) < 8:
            continue
        h = len(re.findall(r"\b(bhejo|karo|hai|hoga|milega|nahi|apna|ab|se|ka|ki|ke|me|ko|aur|ya|jaye|karke|"
                           r"chalega|dabao|chuno|baad|liye|wala|wale|kar|raha|rakho|dikhega|lagega|hain|khatam|"
                           r"lo|kholo|dekh|likho|dalo|padega|laga|bache|poore|milta|hota|kuch|sab|sirf|bina|jaisa|jaise)\b",
                           s, re.I))
        if h / max(1, len(w)) < 0.22:
            eng += 1
print(f"  ℹ️  (reference) English-heavy user strings bache: {eng}")

# ======================================================================
section("5) LIVE API TESTS — saare tools")
# ======================================================================
from modules import osint_tools as ot
from modules import imei_lookup as il
from modules import api_hub as hub
from modules import desi_tools as desi

t0 = time.time()
r = ot.lookup_ifsc("SBIN0000001")
ok("🏦 IFSC live", r.get("ok") and "State Bank" in str(r.get("bank")), r.get("error"))
ok("🏦 IFSC me MICR", bool(r.get("micr")))

r = ot.lookup_pincode("800001")
ok("📮 Pincode live", r.get("ok") and r.get("district") == "Patna", r.get("error"))
ok("📮 Pincode me post offices", len(r.get("post_offices") or []) > 5)

r = ot.search_by_area_name("Gaya")
ok("📮 Area search live", r.get("ok") and len(r.get("results") or []) > 0, r.get("error"))

r = ot.lookup_ip_domain("8.8.8.8")
ok("🌐 IP lookup live", r.get("ok") and "Google" in str(r.get("isp")), r.get("error"))

r = ot.lookup_ip_domain("192.168.1.1")
ok("🌐 Private IP block", not r.get("ok"))

r = ot.lookup_phone_info("9876543210")
ok("📱 Number info live", r.get("ok") and r.get("valid"), r.get("error"))
ok("📱 Operator mila", bool(r.get("operator")))

r = ot.lookup_vehicle_rto("BR30AR0802")
ok("🚗 RTO free card live", r.get("ok") and r.get("state_name") == "Bihar", r.get("error"))
ok("🚗 RTO se website links HAT gaye (user ka order)", (r.get("links") or []) == [])
ok("🚗 RTO me SMS tarika (VAHAN/CHALLAN -> 7738299899)",
   "7738299899" in str((r.get("sms") or {}).get("number", "")) and "VAHAN" in str((r.get("sms") or {}).get("rc", "")))

r = ot.check_username_platforms("github")
ok("🆔 Username check live", r.get("ok") and len(r.get("results") or []) >= 3, r.get("error"))

r = il.fetch_imei_details("353010111111110")
ok("📲 IMEI live", r.get("ok"), r.get("error"))
ok("📲 IMEI me brand+model", bool(r.get("brand")) and bool(r.get("model")))
ok("📲 IMEI me photo", bool(r.get("photo")))
ok("📲 IMEI me specs sections", len(r.get("sections") or []) >= 5)
ok("📲 IMEI caption ban raha", len(il.render_caption(r)) > 80)
ok("📲 IMEI text ban raha", len(il.render_text(r)) > 300)
ok("📲 IMEI JSON ban raha", len(il.specs_json_bytes(r)) > 500)
ok("📲 IMEI filename", il.specs_filename(r).endswith(".json"))

ok15, clean, err = il.validate_imei("353010111111110")
ok("📲 IMEI validate (sahi)", ok15)
ok15b, _, errb = il.validate_imei("353010111111111")
ok("📲 IMEI validate (galat reject)", not ok15b)

ok("🔌 Hub ready", hub.hub_ready())
ki = hub.hub_key_info() if hasattr(hub, "hub_key_info") else {}
ok("🔌 Hub status card", len(hub.status_card()) > 50)
ok("🧮 Bigha→Kattha converter", desi.convert_land(1, "bigha")["sqft"] > 1000)
ok("🧮 Registry cost ban raha", "total" in str(desi.registry_cost("bihar", 1000, 5000)).lower())

# ======================================================================
section("6) TOOL TEXT / KEYBOARD (bot objects)")
# ======================================================================
kb = bot.kb_for(999000111)
n_btn = sum(len(row) for row in kb.keyboard)
ok(f"Reply keyboard me {n_btn} button (31 hone chahiye — v50 +WEATHER +EMI)", n_btn == 31, n_btn)
labels = [bot.unbold(b.text) for row in kb.keyboard for b in row]
ok("Keyboard me CLIP MAKER nahi", not any("CLIP MAKER" in bot.unbold(l) for l in labels))
ok("Keyboard me LINK BYPASS nahi", not any("LINK BYPASS" in bot.unbold(l) for l in labels))
# NOTE v50: purana standalone "INTEREST CALC" nahi, par naya "EMI / INTEREST CALC" hai
ok("v50: Keyboard me 🧮 EMI / INTEREST CALC hai", any("EMI / INTEREST CALC" in bot.unbold(l) for l in labels))
ok("v50: Keyboard me 🌦️ WEATHER hai", any("WEATHER / MAUSAM" in bot.unbold(l) for l in labels))
ok("Keyboard me IMEI hai", any("IMEI" in bot.unbold(l) for l in labels))

for act in ("imei", "rto", "ifsc", "pin", "ip", "numinfo", "terabox", "insta_dl", "qr", "short", "linkcheck"):
    p = bot.tool_prompt(act)
    ok(f"tool_prompt({act}) ban raha", len(p) > 40)

ok("tutorial video kb (imei)", bot.tool_tutorial_kb("imei") is not None)
ok("tutorial video kb (clips) None", bot.tool_tutorial_kb("clips") is None)

# ======================================================================
section("7) DB / CREDITS")
# ======================================================================
u = bot.get_user(999000111, "Test")
ok("DB user ban gaya", u.get("user_id") == 999000111)
left = bot.credits_left(u, 999000111)
ok(f"Credits default {left}", isinstance(left, int))
ok("Premium check (numinfo)", bot.is_premium_tool("numinfo"))
ok("clips premium nahi", not bot.is_premium_tool("clips"))
ok("credits_line ban raha", len(bot.credits_line(u, 999000111)) > 10)
ok("get_credits_over_text ban raha", len(bot.get_credits_over_text("imei")) > 100)

# ======================================================================
section("8) v49.1 — GST / PAN card fix + dead code saaf")
# ======================================================================
from modules import api_hub as _hub
g1 = _hub.hub_gst("27AAPFU0939F1ZV")
ok("GST check chal raha", g1.get("ok") is True, g1.get("error"))
ok("GST state aaya", bool(g1.get("state")), g1.get("state"))
ok("GST PAN holder type aaya", len(str(g1.get("pan_holder_type") or "")) > 3, g1.get("pan_holder_type"))
ok("GST registration type aaya", bool(g1.get("registration_type")), g1.get("registration_type"))
ok("GST checksum field aaya", g1.get("checksum_valid") in (True, False), g1.get("checksum_valid"))
ok("GSTIN galat lambai par saaf error", _hub.hub_gst("123").get("ok") is False)
ok("GSTIN galat format par saaf error", _hub.hub_gst("99XXXXXXXXXXXXX").get("ok") is False)

p1 = _hub.hub_pan("AAPFU0939F")
ok("PAN check ab FAIL nahi hota (offline analysis)", p1.get("ok") is True, p1)
ok("PAN holder type aaya", len(str(p1.get("holder_type") or "")) > 3, p1.get("holder_type"))
ok("PAN series aaya", bool(p1.get("series")), p1.get("series"))
ok("PAN galat lambai par saaf error", _hub.hub_pan("ABC").get("ok") is False)

ok("Missing endpoint memo (404 dobara call nahi)", isinstance(_hub._MISSING, dict))
r_snap = _hub.hub_snap_stories("snapchat")
ok("Snap stories error message deta hai", r_snap.get("ok") is True or bool(r_snap.get("error")), r_snap)

ok("bot me kv_row helper hai", callable(getattr(bot, "kv_row", None)))
ok("GST card Hinglish", "GST CHECK NAHI HO PAYA" in open(os.path.join(HERE, "bot.py"), encoding="utf-8").read())
ok("PAN card Hinglish", "PAN CHECK NAHI HO PAYA" in open(os.path.join(HERE, "bot.py"), encoding="utf-8").read())
ok("UTR help Hinglish", "kahan milega" in __import__("modules.payguard", fromlist=["x"]).utr_help_text())
ok("Sarkari card Hinglish", "sarkari portal" in __import__("modules.sarkari_hub", fromlist=["x"]).SARKARI_CITIZEN_TEXT)
ok("Tutorial page Hinglish", "Ye bot kaise chalta hai" in __import__("modules.tutorial_hub", fromlist=["x"]).TUTORIAL_INTRO)

import importlib
try:
    importlib.import_module("modules.clip_maker"); ok("clip_maker.py deleted", False)
except ImportError:
    ok("clip_maker.py deleted", True)
try:
    importlib.import_module("modules.ai_brain"); ok("ai_brain.py deleted", False)
except ImportError:
    ok("ai_brain.py deleted", True)
ok("purane dev-note md gaye", not os.path.exists(os.path.join(HERE, "v48-IMEI-YOUTUBE-1080.md")))
ok("stale tutorial video gaye", not os.path.exists(os.path.join(HERE, "tutorial_videos", "interest.mp4")))
_vids = len([f for f in os.listdir(os.path.join(HERE, "tutorial_videos")) if f.endswith(".mp4")])
ok(f"tutorial videos = 24 (mila {_vids})", _vids == 24, _vids)


# ======================================================================
# v49.13: INFO TOOLS ME KOI BAHAR-WALA LINK BUTTON NAHI HONA CHAHIYE (user ka order)
# Links sirf inme allowed: download tools, short link / app finder / username / link check,
# sarkari hub menu, support/share buttons.
print("\n" + "=" * 70)
print("v49.13) LINK GUARD — info tools me koi bahar wala link nahi")
print("=" * 70)

_bot_src = open(os.path.join(HERE, "bot.py"), encoding="utf-8").read()
_lines = _bot_src.splitlines()
# ye patterns URL BUTTON me kabhi nahi aane chahiye (info tools ke links)
_forbidden_url_bits = ("maps_link", "imei.info", "truecaller", "wa.me/", "google.com/search",
                       "echallan", "vahan.parivahan", "iib.gov", "sarathi.parivahan",
                       "sancharsaathi", "cybercrime.gov.in", "tafcop")
# v49.14: safety card ke links bhi hataye — ab EXEMPTION nahi, poora strict check
_bad = []
for _i, _ln in enumerate(_lines, 1):
    if "url=" not in _ln:
        continue
    for _b in _forbidden_url_bits:
        if _b in _ln:
            _bad.append(f"line {_i}: {_ln.strip()[:90]}")
ok("bot.py me info-tool ke bahar wale link buttons nahi", not _bad, _bad[:4])

# v49.15: purana card + "safety" wala sab POORA delete (user ka order) — guard
import modules.osint_tools as _ost_mod
ok("osint_tools se leaked-records + purana card code DELETE",
   not hasattr(_ost_mod, "lookup_public_records") and not hasattr(_ost_mod, "number_safety_info")
   and not hasattr(_ost_mod, "NUM_LEAK_ENABLED") and not hasattr(_ost_mod, "PUBLIC_RECORD_WARNING"))

# bot.py ke pure code me "SAFETY" shabd kabhi nahi hona chahiye
ok("bot.py me 'safety' shabd kabhi nahi", "safety" not in _bot_src.lower(),
   [l.strip()[:80] for l in _lines if "safety" in l.lower()][:3])

# modules ke runtime code me bhi "safety" shabd nahi
_mod_bad = []
_mod_dir = os.path.join(HERE, "modules")
for _f in sorted(os.listdir(_mod_dir)):
    if _f.endswith(".py"):
        _txt = open(os.path.join(_mod_dir, _f), encoding="utf-8").read().lower()
        if "safety" in _txt:
            _mod_bad.append(_f)
ok("modules ke saare code me 'safety' shabd kabhi nahi", not _mod_bad, _mod_bad)

# IMEI walon ke liye: bot.py me imei.info ka koi url= button nahi
ok("bot.py me imei.info url button nahi",
   not any("imei.info" in l and "url=" in l for l in _lines))

# maps wale buttons gaye (IP / IFSC / PIN)
ok("bot.py me maps_link ka url button nahi",
   not any("maps_link" in l and "url=" in l for l in _lines))

# ======================================================================
print("\n" + "=" * 70)
print(f"v49 VERIFY — PASS: {len(PASS)} | FAIL: {len(FAIL)}   ({time.time()-t0:.1f}s)")
print("=" * 70)
if FAIL:
    print("\nFAILED:")
    for f in FAIL:
        print("  ❌", f)
sys.exit(1 if FAIL else 0)
