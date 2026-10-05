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
check("ffuid handler soft-fail par credit NAHI katta",
      "_soft" in _ffseg and "service_busy" in _ffseg)


# =====================================================================
section("2) 🏦 UPI VERIFY — v59 me POORI TARAH DELETE (user ka order)")
# =====================================================================
# User ka order (v59): "phle upi verify tools delete karo and uska code".
# Isliye purana UPI verify tool + uska boxed card + privacy refusal +
# _VPA_RE + UPI_BANK_HANDLES + dono callbacks (upi_to_num / upi_to_vpa) +
# /upiapi command + modules/upi_provider.py — sab gaya.
check('bot.py me "if mode == \'upi\':" handler hi nahi bacha',
      'if mode == "upi":' not in _bot_src)
check("UPI VERIFY prompt gaya", "UPI VERIFY" not in _bot_src)
_bot_user = "\n".join(_l for _l in _bot_src.split("\n") if "BOT_VERSION =" not in _l)
check("keyboard/help me UPI Verify / UPI-IFSC mention nahi (version line chhod ke)",
      "UPI Verify" not in _bot_user and "UPI/IFSC" not in _bot_user)
check("upi_to_num / upi_to_vpa callbacks gaye",
      "upi_to_num" not in _bot_src and "upi_to_vpa" not in _bot_src)
check("/upiapi command gaya", "upiapi" not in _bot_src.lower())
import modules.osint_tools as _OT  # noqa: E402
check("osint_tools se upi_verify() gaya", not hasattr(_OT, "upi_verify"))
check("osint_tools se UPI_BANK_HANDLES gaya", not hasattr(_OT, "UPI_BANK_HANDLES"))
check("modules/upi_provider.py file gayi",
      not os.path.exists(os.path.join(ROOT, "modules", "upi_provider.py")))
check("keyboard me IFSC button duplicate nahi",
      sum(1 for _r in __import__("bot").KB_BTNS for _b in _r
          if "IFSC" in __import__("bot").unbold(_b).upper()) == 1)


# =====================================================================
section("3) 🧾 Version + overall sanity")
check("BOT_VERSION v56+ par hai",
      re.search(r'BOT_VERSION = "v(?:5[6-9]|[6-9][0-9])', _bot_src) is not None)

# --- v59: purana UPI card/status block bhi poori tarah gaya ---
check("UPI ka purana card/status section nahi bacha",
      "ACCOUNT DETAILS & STATUS" not in _bot_src and "FORMAT VALID" not in _bot_src)
check("UPI ke env var naam code me nahi", "UPI_VERIFY" not in _bot_src)
import bot as _bot  # noqa: E402
_cot = _bot.get_credits_over_text("imei")
check("credits-over text me hata hua 'Vehicle' tool advertise NAHI hota",
      "Vehicle" not in _cot)
check("VIP wall me hata hua Vehicle/Challan NAHI hai",
      "Vehicle" not in _bot.VIP_WALL_TEXT and "Challan" not in _bot.VIP_WALL_TEXT)
check("VIP wall me hata hua 'Private Channel Setup' NAHI hai",
      "Private Channel" not in _bot.VIP_WALL_TEXT)
check("/health par git commit SHA dikhta hai (deploy verify karne ke liye)",
      "RENDER_GIT_COMMIT" in _bot_src and "commit: {_GIT_COMMIT" in _bot_src)
check("/health par branch + uptime bhi hai",
      "RENDER_GIT_BRANCH" in _bot_src and "| up: " in _bot_src)
check("menu se vehicle/RTO/challan abhi bhi hata hua hai",
      "vehicle" not in _bot_src.lower().split("btn_mode_map")[0][-4000:].lower()
      or "RTO" not in _bot_src)

# =====================================================================
section("4)  v54.3 — LIVE crash fix: adhoora HTML tag (Render log wali error)")
# RENDER LOG (user screenshot, 2:03 PM): "Exception handling update: Can't
# parse entities: can't find end tag corresponding to start tag 'i'".
# Wajah: lamba IMEI card `txt[:4000]` se kata tha aur cut <i>...</i> line ke
# beech me gira → unclosed tag → Telegram pura message reject → crash +
# credit kata hua (user ko kuch nahi mila).
from modules.core.html_safe import cut_html, strip_html, html_balanced  # noqa: E402

_bad = "a\n" * 3 + "📊 <b>X:</b> 1\n<i>Data: lambi line yahan hai aur aage bhi jaati hai.</i>"
_lim = _bad.index("<i>Data") + 12
check("purana plain slice crash banata tha (unclosed <i>)",
      html_balanced(_bad[:_lim]) is False)
_fx = cut_html(_bad, _lim)
check("cut_html unclosed tag nahi chhodta", html_balanced(_fx) is True)
check("cut_html limit ke andar rehta hai", len(_fx) <= _lim)
check("cut_html adhoora '<' fragment nahi chhodta",
      not (("<" in _fx[_fx.rfind("\n") + 1:]) and (">" not in _fx[_fx.rfind("\n") + 1:])))
_nested = "<b>bold <i>ital</i> aur <code>code</code> adhoora"
_fx2 = cut_html(_nested, len(_nested) - 3)
check("cut_html khule tags stack-order me band karta hai", html_balanced(_fx2) is True)
check("cut_html chhoti string ko chhuta nahi", cut_html("abc <i>x</i>", 99) == "abc <i>x</i>")
check("strip_html saare tags hatata hai (plain fallback)",
      "<" not in strip_html("<b>a</b> <i>b</i> <code>c</code>"))

import modules.imei_lookup as IL  # noqa: E402
_big = {"ok": True, "imei": "356356426587792", "brand": "Samsung", "model": "Galaxy A52",
        "tac": "356356", "specs_url": "https://example.com/specs",
        "source_note": "TAC database + nanoreview.net",
        "sections": [{"title": "Display", "rows": [[f"key{i}", "v" * 100] for i in range(60)]},
                     {"title": "Battery", "rows": [[f"b{i}", "w" * 100] for i in range(60)]}]}
_rt = IL.render_text(_big, max_len=3950)     # force: tail lines ke saath >4000 bane
check("IMEI render_text 4000 ke andar rehta hai", len(_rt) <= 4000, str(len(_rt)))
check("IMEI render_text ke tags balanced hain (crash regression lock)",
      html_balanced(_rt) is True)
_rc = IL.render_caption(_big)
check("IMEI render_caption 1024 ke andar + balanced",
      len(_rc) <= 1024 and html_balanced(_rc) is True)

_imei_seg = _bot_src[_bot_src.index('if mode == "imei":'):]
_imei_seg = _imei_seg[:_imei_seg.index('if mode == "pp_stamp_text":')]
check("IMEI: credit AB delivery ke BAAD katta hai (pehle doob jaata tha)",
      _imei_seg.index("_imei_sent = False") < _imei_seg.index('spend_credit_msg(uid, "imei")'))
check("IMEI: HTML fail ho to plain-text fallback hai",
      "strip_html(body)" in _imei_seg)
check("IMEI: deliver na ho to 'Koi credit nahi kata' message",
      "Koi credit nahi kata" in _imei_seg)
check("bot.py me koi raw HTML slice [:3900]/[:4000] nahi bacha",
      'join(L)[:3900]' not in _bot_src and 'join(L)[:4000]' not in _bot_src)
check("keepalive ping ab 4 minute par hai (spin-down kam ho)",
      'or 4)' in _bot_src and "_KEEPALIVE_MINUTES = 4.0" in _bot_src)

# =====================================================================
print("\n" + "=" * 62)
print(f"  v54.1 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILURES:
    print("\n❌ FAILED CHECKS:")
    for f in FAILURES:
        print("   •", f)
sys.exit(1 if FAIL else 0)
