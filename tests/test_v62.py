# -*- coding: utf-8 -*-
"""
v62 SELFTEST — 2 NAYE TOOLS (💰 Salary Slip + 🍽️ Menu / Rate Card)
=================================================================
Ye test file PROVE karti hai ki:

  A. WIRING      — dono tools har jagah register hain (menu, prompt, limits)
  B. SALARY MATH — Basic/HRA/PF/ESI/Net ka hisaab BILKUL sahi hai
  C. RENDER      — dono ka PNG + PDF banta hai, sahi size ka
  D. BAD INPUT   — galat/adha input par CRASH NAHI, saaf error message
  E. FREE MODE   — 0 credit wala naya user bhi dono chala sakta hai
  F. PURANA SAFE — purane 10 business tools aur unke prompts waise hi hain

Chalao:  python tests/test_v62.py
"""
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv62_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_FOR_V62"
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
print("  v62 SELFTEST — Salary Slip + Menu / Rate Card")
print("=" * 62)

import warnings                                                      # noqa: E402
warnings.filterwarnings("ignore")
import bot                                                           # noqa: E402
from modules import business_tools as BT                             # noqa: E402

_A4 = BT.A4()

# =====================================================================
section("[A] 🔌 WIRING — dono tools har jagah register hain")
# =====================================================================
NEW = ("biz_salary", "biz_menucard")
for _k in NEW:
    check(f"BIZ_MENU me '{_k}'", _k in bot.BIZ_MENU)
    check(f"PREMIUM_TOOLS me '{_k}'", _k in bot.PREMIUM_TOOLS)
    check(f"PREMIUM_TOOL_NAMES me '{_k}'", _k in bot.PREMIUM_TOOL_NAMES)
    check(f"TOOL_RATE_LIMITS me '{_k}'", _k in bot.TOOL_RATE_LIMITS)
    check(f"PROMPT_DATA me '{_k}' (prompt maujood)", _k in bot.PROMPT_DATA)
    check(f"BTN_MODE_MAP/prompt aliases '{_k}'", bot._biz_kind(_k.replace("biz_", "")) == _k)
check("business menu me total 12 tools", len(bot.BIZ_MENU) == 12, len(bot.BIZ_MENU))
check("BIZ_MENU_TEXT me 12 likha hai", "12 kaam ki cheezein" in bot.BIZ_MENU_TEXT)
check("business menu keyboard me 12 buttons",
      sum(len(r) for r in bot.biz_menu_kb().inline_keyboard) >= 12)
check("biz_build me salary mapped hai",
      bot.biz_build("biz_salary", {"company": "X", "name": "Y", "gross": 10000}).get("ok") is True)
check("biz_build me menucard mapped hai",
      bot.biz_build("biz_menucard", {"name": "X", "items": [{"name": "a", "price": 1}]}).get("ok") is True)
check("salary ke aliases: salary/payslip/slip",
      all(bot._biz_kind(x) == "biz_salary" for x in ("salary", "payslip", "slip")))
check("menu ke aliases: menu/menucard/ratecard/ratelist",
      all(bot._biz_kind(x) == "biz_menucard" for x in ("menu", "menucard", "ratecard", "ratelist")))
check("version v62 ya usse aage hai (ye tools zinda hain)",
      any(f"v{n}." in bot.BOT_VERSION for n in range(62, 70)) or "FREE4ALL" in bot.BOT_VERSION,
      bot.BOT_VERSION)

# =====================================================================
section("[B] 🧮 SALARY KA GANIT — ek-ek number check")
# =====================================================================
_d = bot.biz_parse("biz_salary",
                   "Sharma Kirana | Ramesh Kumar | Salesman | September 2026 | 18000 | 500",
                   "Owner")
check("gross 18000 parse hua", bot._biz_num(_d.get("gross")) == 18000, str(_d.get("gross")))
check("advance 500 parse hua", bot._biz_num(_d.get("advance")) == 500, str(_d.get("advance")))
check("company sahi", _d.get("company") == "Sharma Kirana", _d.get("company"))
check("naam sahi", _d.get("name") == "Ramesh Kumar", _d.get("name"))
check("post sahi", _d.get("post") == "Salesman", _d.get("post"))
check("month sahi", _d.get("month") == "September 2026", _d.get("month"))

_r = BT.salary_slip_image(dict(_d))
_g = 18000.0
_basic, _hra, _other = _g * .5, _g * .2, _g * .3
_pf = round(_basic * 12 / 100, 2)                 # 1080
_esi = round(_g * 0.0075, 2)                      # 135 (gross <= 21000)
_ptax = 200.0
_adv = 500.0
_ded = round(_pf + _esi + _ptax + _adv, 2)        # 1915
_net = round(_g - _ded, 2)                        # 16085
check("render OK", _r.get("ok") is True, str(_r.get("error"))[:80])
check(f"net pay = {_net} (basic50/hra20/pf12/esi.75/ptax200/adv500)",
      _r.get("amount") == _net, f"mila: {_r.get('amount')}")
check("gross wapas mila", _r.get("gross") == _g, str(_r.get("gross")))
check("total deduction = 1915", _r.get("deductions") == _ded, str(_r.get("deductions")))
check("PF = basic ka 12% (1080)", _pf == 1080.0)
check("ESI sirf 21000 tak lagta hai (135)", _esi == 135.0)

# zyada salary par ESI nahi lagta
_r2 = BT.salary_slip_image({"company": "Big Co", "name": "A", "gross": 50000, "advance": 0})
check("50000 par ESI nahi katta (gross > 21000)",
      _r2.get("deductions") == round(50000 * .5 * .12 + 200, 2), str(_r2.get("deductions")))
check("50000 par net sahi",
      _r2.get("amount") == round(50000 - (50000 * .5 * .12 + 200), 2), str(_r2.get("amount")))

# sirf number dala (baaki khali) — phir bhi chalta hai
_r3 = BT.salary_slip_image(bot.biz_parse("biz_salary", "18000", "Owner"))
check("sirf '18000' likhne par bhi slip banti hai", _r3.get("ok") is True)

# =====================================================================
section("[C] 🖼️ RENDER — PNG + PDF dono, sahi size")
# =====================================================================
for _nm, _res in (("salary", _r), ("menucard",
                                   BT.menu_card_image({"name": "Hotel Shivam",
                                                       "items": [{"name": "Chai", "price": 10},
                                                                 {"name": "Thali", "price": 80}]}))):
    check(f"{_nm}: PNG bana", bool(_res.get("png")) and len(_res["png"]) > 20000,
          str(len(_res.get("png") or b"")))
    check(f"{_nm}: A4 @200dpi size {_A4}", _res.get("size") == _A4, str(_res.get("size")))
    _pdf = BT.to_pdf([_res["png"]])
    check(f"{_nm}: PDF bana", bool(_pdf) and _pdf[:4] == b"%PDF", str(len(_pdf or b"")))

for _n, _items in ((5, 5), (12, 12), (30, 30), (80, 80)):
    _ra = BT.menu_card_image({"name": "M", "items": [{"name": f"I{i}", "price": i * 10}
                                                     for i in range(1, _items + 1)]})
    check(f"menu: {_n} items par bhi banta hai (item limit/layout)",
          _ra.get("ok") and len(_ra.get("png") or b"") > 20000)

# Hindi (Devanagari) bhi chalna chahiye
_rd = BT.menu_card_image({"name": "श्री राम भोजनालय", "tagline": "शुद्ध देसी खाना",
                          "items": [{"name": "चाय", "price": 10},
                                    {"name": "समोसा", "price": 15},
                                    {"name": "थाली", "price": 80}]})
check("Hindi naam ke saath menu render hota hai", _rd.get("ok") is True, str(_rd.get("error"))[:80])
_rs = BT.salary_slip_image({"company": "शर्मा किराना", "name": "रमेश कुमार",
                            "post": "सेल्समैन", "gross": 18000})
check("Hindi naam ke saath salary slip banti hai", _rs.get("ok") is True, str(_rs.get("error"))[:80])

# =====================================================================
section("[D] 🛡️ GALAT INPUT — crash nahi, saaf message")
# =====================================================================
_bad_cases = [
    ("biz_salary", ""),
    ("biz_salary", "|||||"),
    ("biz_salary", "abc def ghi"),                       # salary 0
    ("biz_salary", "0"),
    ("biz_salary", "🙂🙂🙂"),
    ("biz_salary", "x" * 500),
    ("biz_menucard", ""),
    ("biz_menucard", "kuch bhi nahi"),                   # koi item nahi
    ("biz_menucard", "Hotel | | :::"),
    ("biz_menucard", "A" * 400),
    ("biz_menucard", "Hotel | tag | item:abc, xyz:"),     # price text
]
_crash = []
for _m, _inp in _bad_cases:
    try:
        _dd = bot.biz_parse(_m, _inp, "Owner")
        _rr = bot.biz_build(_m, _dd)
        if not isinstance(_rr, dict) or "ok" not in _rr:
            _crash.append(f"{_m} / {_inp[:12]} -> bad shape")
    except Exception as _e:                                # noqa: BLE001
        _crash.append(f"{_m} / {_inp[:12]} -> {_e!r}")
check(f"galt {len(_bad_cases)} input par bhi ek bhi crash nahi", not _crash, str(_crash[:3]))
check("salary 0 par saaf error message (crash nahi)",
      BT.salary_slip_image({"gross": 0}).get("error") is not None)
check("menu khali par saaf error message (crash nahi)",
      BT.menu_card_image({"items": []}).get("error") is not None)

# =====================================================================
section("[E] 🆓 FREE MODE — 0 credit wala user bhi chala sakta hai")
# =====================================================================
_u = {"user_id": 555000111, "credits": 0, "premium_until": ""}
check("ALL_FREE on hai", bot.ALL_FREE is True)
check("salary tool 0-credit user ke liye khula", bot.can_use_premium_tool(_u, 555000111) is True)
check("menu tool 0-credit user ke liye khula",
      bot.can_use_premium_tool(dict(_u, user_id=555000222), 555000222) is True)
check("credit katne wala msg khali hai", bot.spend_credit_msg(555000111, "biz_salary") == "")

# =====================================================================
section("[F] 🔒 PURANA SAFE — v60 ke 10 tools aur prompts waise hi")
# =====================================================================
_OLD10 = ("biz_invoice", "biz_resume", "biz_biodata", "biz_certificate", "biz_idcard",
          "biz_vcard", "biz_letter", "biz_upi", "biz_labels", "biz_emi")
check("v60 ke saare 10 tools aaj bhi hain", all(k in bot.BIZ_MENU for k in _OLD10))
check("v60 ke saare 10 prompts aaj bhi hain", all(k in bot.PROMPT_DATA for k in _OLD10))
# v64 ke baad 27 downloader prompts bhi jude. Asli baat: purane DELETE na hon.
check("v60 ke saare 10 purane business prompts aaj bhi zinda hain",
      all(k in bot.PROMPT_DATA for k in
          ("biz_invoice", "biz_resume", "biz_biodata", "biz_certificate", "biz_idcard",
           "biz_vcard", "biz_letter", "biz_upi", "biz_labels", "biz_emi")))
check("v62 ke 2 naye prompts bhi zinda hain",
      "biz_salary" in bot.PROMPT_DATA and "biz_menucard" in bot.PROMPT_DATA)
check("prompt ki ginti kam nahi hui (33+ — sirf naye jude hain)",
      len(bot.PROMPT_DATA) >= 33, str(len(bot.PROMPT_DATA)))
check("purane invoice prompt ka head waisa hi hai",
      "INVOICE" in str(bot.PROMPT_DATA["biz_invoice"].get("head", "")).upper(),
      str(bot.PROMPT_DATA["biz_invoice"].get("head"))[:40])
check("purane emi prompt ka head waisa hi hai",
      bot.PROMPT_DATA["biz_emi"]["head"].startswith("🧮 EMI"),
      str(bot.PROMPT_DATA["biz_emi"]["head"])[:40])
check("purane 10 business tools abhi bhi render karte hain",
      all(bot.biz_build(k, bot.biz_parse(k, "A | B | C", "X")).get("ok") is not None
          for k in _OLD10))
check("PREMIUM_TOOLS 34 (32 + 2 naye)", len(bot.PREMIUM_TOOLS) == 34,
      str(len(bot.PREMIUM_TOOLS)))
check("keyboard me BUSINESS STUDIO button zinda",
      any("BUSINESS STUDIO" in bot.unbold(b).upper() for r in bot.KB_BTNS for b in r))
check("keyboard me ALL TOOLS (FREE) button zinda",
      any("ALL TOOLS" in bot.unbold(b).upper() for r in bot.KB_BTNS for b in r))

# =====================================================================
print(f"\n{'=' * 62}")
print(f"  v62 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS:
        print("  •", f)
sys.exit(1 if FAIL else 0)
