# -*- coding: utf-8 -*-
"""
_selftest_v541 — v54.1 "live bugs" suite
========================================
User ne Telegram ke **live screenshots** bheje the. Un screenshots se jo asli
bugs pakde gaye, ye suite unhe dobara aane se rokta hai:

  1. 🔥 FF UID  — HTTP 403 par bot "UID nahi mila" bolta tha (jhooth).
                  403 = API ne humare server ko block kiya hai → alag state
                  "blocked" + saaf Hinglish soft-fail + credit NAHI katta.
  2. 📌 Pinterest Download — live par "Chhota sa ghatna ho gaya" crash.
                  Wajah: bina `.name` wala BytesIO → PTB filename
                  "application.octet-stream" bana deta hai → Telegram 400 →
                  BadRequest exception unguarded send se bahar nikalta tha.
                  Ab: filename set + try/except + document fallback + credit
                  sirf delivery par.
  3. 🏦 UPI VERIFY — competitor-jaisa BOXED card (sirf public fields) aur
                  10-digit mobile par privacy-refusal (holder ka naam kabhi
                  nahi), bina credit kaate, legal alternatives ke buttons ke
                  saath.
  4. 📡 TG PUBLIC INFO — card me khali separator rows (double newline).

Chalane ka tarika:
    python3 tests/test_v541.py
"""
from __future__ import annotations

import io
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
        FAILURES.append(name + (f"  [{extra}]" if extra else ""))
        print(f"  ❌ {name}" + (f"  [{extra}]" if extra else ""))


# =====================================================================
section("1) 🔥 FF UID — HTTP 403 ab 'blocked' hai, 'UID nahi mila' nahi")
# SCREENSHOT: "⚠️ UID Lookup Failed — The API returned an HTTP 403 error."
# 403 ka matlab player absent NAHI hai — free API ne datacenter (Render) IP
# ko temporarily rok diya tha. Purana code 403 ko "other" state me daal kar
# "UID ... nahi mila" wala galat message bana deta tha (aur user ko lagta
# UID kharab hai).
import modules.gaming_tools as GT  # noqa: E402

_ALL_REGIONS = ["IND", "SAC", "BR", "EU", "NA", "TH", "SG", "VN", "ID",
                "ME", "PK", "BD", "CIS", "TW", "US"]


def _fake_status(force: bool = False) -> dict:
    return {"ok": True, "status": "online", "avg_ms": "300ms", "uptime": "99.8%",
            "daily_requests": "12000", "release": "OB55 - 1.132.8",
            "api_regions": list(_ALL_REGIONS),
            "regions": {r: {"total": 10, "available": 5, "banned": 0}
                        for r in _ALL_REGIONS},
            "dead_regions": [], "error": ""}


class _FakeResp:
    def __init__(self, code: int, payload: dict):
        self.status_code = code
        self._p = payload

    def json(self):
        return self._p


def _patch_http(code: int, payload: dict):
    def _fake_get(url, **kw):
        return _FakeResp(code, payload)
    return _fake_get


_orig_status, orig_http_get, orig_get_json = (GT.ff_service_status, GT.http_get,
                                              GT.http_get_json)
GT.ff_service_status = _fake_status

try:
    # --- (a) 403 par blocked soft-fail ---
    GT.http_get = _patch_http(403, {})
    r403 = GT.ff_player_info("123456789", "IND", use_cache=False)
    check("403 → ok=False", r403.get("ok") is False)
    check("403 → service_busy=True (isliye credit nahi katega)",
          r403.get("service_busy") is True)
    check("403 → blocked flag set", r403.get("blocked") is True)
    _e = str(r403.get("error") or "")
    check("403 message me 'HTTP 403' dikhta hai", "403" in _e, _e[:80])
    check("403 message Hinglish hai (English nahi)",
          ("credit NAHI kata" in _e) and ("server ko block" in _e), _e[:90])
    check("403 message jhootha 'nahi mila' NAHI bolta", "nahi mila" not in _e, _e[:90])
    check("403 message English 'Try again after some time' NAHI bolta",
          "Try again after" not in _e)

    # --- (b) 403 auto-scan (saare regions) par bhi blocked ---
    r403a = GT.ff_player_info("123456789", "", use_cache=False)
    check("auto-scan 403 → service_busy=True", r403a.get("service_busy") is True)
    check("auto-scan 403 → blocked_regions ginti hai",
          int(r403a.get("blocked_regions") or 0) >= 1, str(r403a.get("blocked_regions")))

    # --- (c) 404 ab bhi 'genuinely not found' (regression na ho) ---
    GT.http_get = _patch_http(404, {"success": False, "error": "PLAYER_NOT_FOUND"})
    r404 = GT.ff_player_info("123456789", "IND", use_cache=False)
    check("404 → notfound=True", r404.get("notfound") is True)
    check("404 → service_busy NAHI (ye asli 'nahi mila')",
          not r404.get("service_busy"))
    check("404 message me 'nahi mila' hai",
          "nahi mila" in str(r404.get("error") or ""))

    # --- (d) 429 rate-limit path abhi bhi kaam karta hai ---
    GT.http_get = _patch_http(429, {"success": False, "error": "RATE_LIMIT"})
    r429 = GT.ff_player_info("123456789", "IND", use_cache=False)
    check("429 → service_busy=True", r429.get("service_busy") is True)
    check("429 → 'rate-limit' message", "rate-limit" in str(r429.get("error") or ""))

    # --- (e) 500 → network/server error soft-fail ---
    GT.http_get = _patch_http(503, {})
    r503 = GT.ff_player_info("123456789", "IND", use_cache=False)
    check("503 → service_busy=True", r503.get("service_busy") is True)

    # --- (f) success path abhi bhi card banata hai ---
    GT.http_get = _patch_http(200, {"success": True, "result": {
        "basicInfo": {"nickname": {"text": "TestPlayer"}, "level": 62,
                      "region": "IND"},
        "socialInfo": {"friendsCount": {"text": "120"}},
        "inventory": {"characterName": "Alok",
                      "characterImage": "https://x/char.png"},
        "profileCard": {"png": "https://x/card.png"},
        "clothesUrl": {"png": "https://x/outfit.png"},
    }})
    rok = GT.ff_player_info("123456789", "IND", use_cache=False)
    check("200 → ok=True", rok.get("ok") is True)
    check("200 → nickname card me hai",
          "TestPlayer" in str(rok.get("lines") or rok.get("nickname") or rok))
finally:
    GT.ff_service_status = _orig_status
    GT.http_get = orig_http_get
    GT.http_get_json = orig_get_json

# bot.py side: soft-fail par credit nahi katta (wiring)
_bot_src = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
_ffseg = _bot_src[_bot_src.index('if mode == "ffuid":'):]
_ffseg = _ffseg[:_ffseg.index('if mode == "pinterest":')]
check("ffuid handler soft-fail par credit NAHI katta",
      "_soft" in _ffseg and "service_busy" in _ffseg)


# =====================================================================
section("2) 📌 Pinterest Download — nameless-BytesIO crash fix")
# SCREENSHOT: "⚠️ Chhota sa ghatna ho gaya..." (global error handler).
# Probe (2026-10-05): _pinpick_download() bilkul sahi JPEG deta tha
# (319,160 bytes, \xff\xd8\xff\xe0 JFIF) par uske BytesIO par `.name` NAHI
# tha. PTB 22.8 aise stream ka filename "application.octet-stream" bana deta
# hai → Telegram Bot API 400 deta hai → PTB BadRequest raise karta hai →
# exception seedha global handler tak jaata tha (aur credit bhi kat jaata tha).
from telegram import InputFile  # noqa: E402

_nameless = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01")
_if = InputFile(_nameless)
check("nameless stream ka filename image-jaisa NAHI hota (yahi crash ki jad thi)",
      str(getattr(_if, "filename", "")).endswith((".jpg", ".jpeg", ".png")) is False,
      str(getattr(_if, "filename", "")))

_named = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01")
_named.name = "pinterest.jpg"
_if2 = InputFile(_named)
check("filename set karne par InputFile ko .jpg milta hai",
      str(getattr(_if2, "filename", "")).endswith(".jpg"),
      str(getattr(_if2, "filename", "")))

check("bot.py pinpick stream par .name set karta hai",
      '_dl["stream"].name = f"pinterest' in _bot_src)
check("pinpick send-block try/except me hai",
      "_sent = False" in _bot_src and "if not _sent:" in _bot_src)
check("photo/video fail ho to send_document fallback hai",
      "document fallback" in _bot_src)
check("fallback me stream.seek(0) hai (warna khaali file jaati)",
      '_dl["stream"].seek(0)' in _bot_src)
check("credit SIRF delivery ke baad katta hai (order sahi)",
      _bot_src.index("_sent = False") <
      _bot_src.index('tel_note("pinterest.download", True, _ms, credit=True)'))
_pinseg = _bot_src[_bot_src.index('_dl = await asyncio.to_thread(_pinpick_download'):]
_pinseg = _pinseg[:_pinseg.index('tel_note("pinterest.download", True, _ms, credit=True)')]
check("failure message me 'Koi credit nahi kata' likha hai",
      "Koi credit nahi kata" in _pinseg)
check("failure par tel_note(..., False, ...) log hota hai",
      'tel_note("pinterest.download", False, _ms' in _pinseg)

# engine side abhi bhi theek hai (real call nahi — sirf contract)
check("_pinpick_download bot.py me defined hai",
      "def _pinpick_download(" in _bot_src)
check("_pin_meta_line bot.py me defined hai", "def _pin_meta_line(" in _bot_src)


# =====================================================================
section("3) 🏦 UPI VERIFY — boxed card (public only) + privacy refusal")
# SCREENSHOT (competitor "OSINT Lookup"): mobile number se account-holder ka
# NAAM. Wo NPCI/bank ka leaked private data hai — ye bot wo kabhi nahi karega.
# Humne sirf CARD KA FORMAT copy kiya hai, private fields nahi.
from modules.osint_tools import upi_verify  # noqa: E402

_u1 = upi_verify("rahul@sbi")
check("VPA verify chalta hai (rahul@sbi)", _u1.get("ok") is True)
check("bank handle map hota hai (@sbi → State Bank of India)",
      "State Bank of India" in str(_u1.get("bank") or ""))
check("local part nikalta hai", _u1.get("local") == "rahul")
_u2 = upi_verify("7260889792@ybl")
check("numeric-VPA (@ybl) bhi verify hota hai", _u2.get("ok") is True)
check("galat VPA par ok=False (crash nahi)", upi_verify("bad@@x").get("ok") is False)
check("khaali input par ok=False", upi_verify("").get("ok") is False)

_upiseg_start = _bot_src.index('if mode == "upi":')
_upiseg = _bot_src[_upiseg_start:_bot_src.index('if mode == "tginfo":', _upiseg_start)]

check("boxed card hai (┌ / └ box characters)", "┌──" in _upiseg and "└──" in _upiseg)
check("card ka title 'UPI VERIFY REPORT' hai", "UPI VERIFY REPORT" in _upiseg)
check("card me VPA / Format / Bank / Local fields hain",
      all(k in _upiseg for k in ("VPA / UPI ID", "Format Status",
                                 "Bank Handle", "Associated Bank", "Local Part")))
check("brand tag laga hai (@Supermannn_x)", "@Supermannn_x" in _upiseg)
check("card me privacy note hai", "Privacy (zaroori baat)" in _upiseg)
check("holder ka NAAM kisi field me nahi maanga jata (private data nahi)",
      "holder_name" not in _upiseg and "account_holder" not in _upiseg)

_mob = _upiseg[_upiseg.index("10-digit MOBILE number path"):]
_mob = _mob[:_mob.index("VPA verify (public format")]
check("10-digit mobile path hai", r're.fullmatch(r"\d{10}"' in _mob)
check("+91 wala mobile bhi pakda jata hai", r"(?:\+91)?[6-9]\d{9}" in _mob)
check("mobile path par credit NAHI katta (spend_credit_msg absent)",
      "spend_credit_msg" not in _mob)
check("mobile path par rate-limit counter phir bhi chalta hai (add_use)",
      "add_use(uid)" in _mob)
check("mobile path refusal me 'leaked private data' saaf bolta hai",
      "leaked private data" in _mob)
check("mobile path legal alternatives offer karta hai",
      "Number Info" in _mob and "VPA Verify" in _mob)
check("mobile path ke buttons wired hain",
      'callback_data="upi_to_num"' in _mob and 'callback_data="upi_to_vpa"' in _mob)

# on_cb me wo buttons actually mode set karte hain (warna dead buttons)
check("on_cb upi_to_num handle karta hai", 'if data == "upi_to_num":' in _bot_src)
check("on_cb upi_to_vpa handle karta hai", 'if data == "upi_to_vpa":' in _bot_src)
_n = _bot_src.index('if data == "upi_to_num":')
check("upi_to_num → mode 'numinfo' set hota hai",
      'context.user_data["mode"] = "numinfo"' in _bot_src[_n:_n + 400])
_v = _bot_src.index('if data == "upi_to_vpa":')
check("upi_to_vpa → mode 'upi' set hota hai",
      'context.user_data["mode"] = "upi"' in _bot_src[_v:_v + 400])


# =====================================================================
section("4) 📡 TG PUBLIC INFO — khali separator rows gayi")
# SCREENSHOT: card me har line ke baad ek khali "━━━" row dikhti thi.
# Wajah: har list-item ke end me "\n" tha AUR join bhi "\n" se hota tha →
# double newline. Ab item me newline nahi, sirf join ka.
_marker = 'L = [f"📡 <b>{to_bold(\'TG PUBLIC INFO\')}</b>"'
_idxs = []
_i = _bot_src.find(_marker)
while _i != -1:
    _idxs.append(_i)
    _i = _bot_src.find(_marker, _i + 1)
check("TG card ke dono branches mile (getChat + t.me fallback)", len(_idxs) == 2,
      f"blocks={len(_idxs)}")
for _n2, _i2 in enumerate(_idxs, 1):
    _j = _bot_src.index('card = "\\n".join(L)', _i2)
    _blk = _bot_src[_i2:_j]
    check(f"branch {_n2}: kisi item ke end me extra newline nahi",
          '\\n"' not in _blk, f"count={_blk.count(chr(92) + 'n' + chr(34))}")
    check(f"branch {_n2}: card single-newline join se banta hai",
          'card = "\\n".join(L)' in _bot_src[_j:_j + 40])
check("bio na ho to saaf fallback text hai",
      "(public page par nahi likha)" in _bot_src)


# =====================================================================
section("5) 🧾 Version + overall sanity")
check("BOT_VERSION v54.1 par hai", 'BOT_VERSION = "v54.1' in _bot_src)
check("prompts abhi bhi minimal one-liners hain (v54 feature zinda)",
      _bot_src.count("PROMPTS") >= 1 and "tool_prompt(" in _bot_src)
check("/health par git commit SHA dikhta hai (deploy verify karne ke liye)",
      "RENDER_GIT_COMMIT" in _bot_src and "commit: {_GIT_COMMIT" in _bot_src)
check("/health par branch + uptime bhi hai",
      "RENDER_GIT_BRANCH" in _bot_src and "| up: " in _bot_src)
check("menu se vehicle/RTO/challan abhi bhi hata hua hai",
      "vehicle" not in _bot_src.lower().split("btn_mode_map")[0][-4000:].lower()
      or "RTO" not in _bot_src)

# =====================================================================
print("\n" + "=" * 62)
print(f"  v54.1 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILURES:
    print("\n❌ FAILED CHECKS:")
    for f in FAILURES:
        print("   •", f)
sys.exit(1 if FAIL else 0)
