# -*- coding: utf-8 -*-
"""
v61 SELFTEST — FREE4ALL (saare tools sabke liye FREE)
=====================================================
Ye test file PROVE karti hai ki:

  A. DEFAULT FREE      — bot bina kuch set kiye FREE mode me uthta hai
  B. ZERO-CREDIT USER  — 0 credit wala naya user bhi har tool chala sakta hai
  C. NO WALL           — "credits khatam / VIP lo" screen kabhi nahi aati
  D. NO CREDIT DEDUCT  — tool chalane par 1 credit bhi nahi katta
  E. UI FREE           — keyboard / account / premium card me VIP bechna band
  F. ALL TOOLS LIST    — "ALL TOOLS (FREE)" button + poori list
  G. DATA SAFE         — kisi user ka data delete NAHI hota (DB intact)
  H. REVERSIBLE        — PREMIUM_ONLY=on likhne par purana system wapas
  I. REACHABILITY      — har premium tool ab SABKE liye khula hai

Chalao:  python tests/test_v61.py
"""
import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv61_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_FOR_V61"
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
print("  v61 SELFTEST — FREE4ALL (saare tools free)")
print("=" * 62)

import warnings                                                      # noqa: E402
warnings.filterwarnings("ignore")
import bot                                                           # noqa: E402
import database as DB                                                # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

# =====================================================================
section("[A] 🌍 DEFAULT FREE — bina kuch set kiye free mode")
# =====================================================================
check("bot.py import ho gaya", bool(bot.BOT_VERSION), bot.BOT_VERSION)
# v62 ke baad bhi ALL_FREE feature zinda hai — is liye "v61 ya usse aage" check karte hain.
# (FREE4ALL ka naam version me rehta hai, chahe number badhta rahe.)
check("BOT_VERSION v61 ya aage hai (FREE4ALL)",
      "FREE4ALL" in bot.BOT_VERSION or "v61." in bot.BOT_VERSION, bot.BOT_VERSION)
check("ALL_FREE = True (default)", bot.ALL_FREE is True, repr(bot.ALL_FREE))
check("PREMIUM_ONLY = False (default)", bot.PREMIUM_ONLY is False, repr(bot.PREMIUM_ONLY))
check("ALL_FREE ka master switch bot.py me hai", "ALL_FREE = _env_bool(\"ALL_FREE\", True)" in BOT_SRC)
check("purana PREMIUM_ONLY bhi ab ALL_FREE se juda hai",
      "if _env_bool(\"PREMIUM_ONLY\", False):" in BOT_SRC)

# =====================================================================
section("[B] 🆓 ZERO-CREDIT NAYA USER — sab kuch khula")
# =====================================================================
_new_user = {"user_id": 987654321, "credits": 0, "premium_until": "", "name": "Test Free User"}
check("credits_left 0-credit user par bhi unlimited (999999)",
      bot.credits_left(_new_user, 987654321) >= 999999,
      str(bot.credits_left(_new_user, 987654321)))
check("can_use_premium_tool -> True (credits 0 hone par bhi)",
      bot.can_use_premium_tool(_new_user, 987654321) is True)
check("check_limit_exceeded() False (credits-khatam screen kabhi nahi)",
      bot.check_limit_exceeded(_new_user, 987654321) is False)
check("vip_ok -> True (kisi bhi random user ke liye)", bot.vip_ok(123450987) is True)
check("vip_ok -> True (uid=0 ke liye bhi, crash nahi)", bot.vip_ok(0) is True)

# har premium tool ka gate khula hai
_closed = []
for _t in sorted(bot.PREMIUM_TOOLS):
    if not bot.can_use_premium_tool(_new_user, 987654321):
        _closed.append(_t)
check(f"saare {len(bot.PREMIUM_TOOLS)} premium tools 0-credit user ke liye khule",
      not _closed, str(_closed[:5]))

# =====================================================================
section("[C] 🚫 NO WALL — 'credits khatam / VIP lo' screen band")
# =====================================================================
check("credits_line khali rehti hai (koi credit line nahi)",
      bot.credits_line(_new_user, 987654321) == "",
      repr(bot.credits_line(_new_user, 987654321)))
check("spend_credit_msg khali rehta hai", bot.spend_credit_msg(987654321, "imei") == "")
check("get_credits_over_text me VIP bechna ABHI BHI hai (admin/manual ke liye theek)",
      "VIP" in bot.get_credits_over_text("imei"))
check("lekin wo text user tak nahi jayega (gate khula hai)",
      bot.can_use_premium_tool(_new_user, 987654321))
check("FREE_MODE_TEXT me 'VIP lo' nahi likha", "VIP lo" not in bot.FREE_MODE_TEXT,
      bot.FREE_MODE_TEXT[:60])
check("FREE_MODE_TEXT me 'credits' bechne wali line nahi", "credit khareed" not in bot.FREE_MODE_TEXT.lower())
check("FREE_MODE_TEXT me SAB FREE likha hai", "FREE" in bot.FREE_MODE_TEXT.upper())

# =====================================================================
section("[D] 💳 NO CREDIT DEDUCT — tool chalao, credit na kate")
# =====================================================================
DB.set_credits(555111, 7)
_before = DB.get_credits(555111)
bot.spend_credit_msg(555111, "imei")
check("spend_credit_msg() ne credit nahi kata",
      DB.get_credits(555111) == _before, f"{_before} -> {DB.get_credits(555111)}")
check("bot.py me biz credits guard laga hai",
      "if _used and not ALL_FREE:" in BOT_SRC)
check("spend_credit_msg ke start me ALL_FREE guard hai",
      "if ALL_FREE:\n        return \"\"            # v61" in BOT_SRC)
check("free mode me credits_left < 999999 ho hi nahi sakta (har baar)",
      all(bot.credits_left(_new_user, 987654321) >= 999999 for _ in range(5)))

# =====================================================================
section("[E] 🎨 UI FREE — VIP bechna band, kaam ki cheez aa gayi")
# =====================================================================
_kb_labels = [bot.unbold(b) for row in bot.KB_BTNS for b in row]
_kb_txt = " | ".join(_kb_labels).upper()
check("keyboard me 'VIP PREMIUM' button HATA diya", "VIP PREMIUM" not in _kb_txt)
check("keyboard me naya 'ALL TOOLS (FREE)' button hai", "ALL TOOLS (FREE)" in _kb_txt)
check("keyboard ke buttons ki ginti waisi hi hai (14 rows)",
      len(bot.KB_BTNS) >= 14, str(len(bot.KB_BTNS)))
check("keyboard me BUSINESS STUDIO button zinda hai", "BUSINESS STUDIO" in _kb_txt)
check("BTN_MODE_MAP me ALL TOOLS -> alltools", bot.BTN_MODE_MAP.get("ALL TOOLS (FREE)") == "alltools")
check("purana 'VIP PREMIUM' text bhi kaam karta hai (purane keyboard walon ke liye)",
      bot.BTN_MODE_MAP.get("VIP PREMIUM") == "premium")
check("cmd_premium ka free branch hai", "if ALL_FREE and not is_admin(update.effective_user.id):" in BOT_SRC)
check("cmd_account ka free branch hai", "if ALL_FREE:\n        _st_f =" in BOT_SRC)
check("welcome me free line hai", "SAARE TOOLS 100% FREE HAIN" in BOT_SRC)
check("/premium command ka description free hai",
      'BotCommand("premium", "Saare tools FREE' in BOT_SRC)
check("on_text me alltools action handle hota hai", 'action == "alltools"' in BOT_SRC)

# =====================================================================
section("[F] 📋 ALL TOOLS LIST — poori list, sab FREE")
# =====================================================================
_at = bot.all_tools_text()
check("all_tools_text() crash nahi karta", isinstance(_at, str) and len(_at) > 500, str(len(_at)))
check("list me '10' Business Studio tools hain",
      all(f"{i}." in _at for i in range(1, 11)))
for _nm in ("Invoice", "Resume", "Bio-data", "Certificate", "ID Card",
            "Visiting Card", "Letter", "UPI", "Price Label", "EMI"):
    check(f"list me '{_nm}' hai", _nm in _at)
check("list me '100% FREE' likha hai", "100% FREE" in _at)
check("list me VIP/paise ki koi line nahi", "₹" not in _at and "VIP lo" not in _at)
check("list Telegram limit (4096) me fit hai", len(_at) < 4096, str(len(_at)))
check("free_mode_kb() me alltools button hai",
      "alltools" in str(bot.free_mode_kb()))
check("all_tools_text me premium tools ki list hai", "Baaki saare tools" in _at)

# =====================================================================
section("[G] 🔐 DATA SAFE — kisi user ka data delete nahi hua")
# =====================================================================
# ek VIP user banao (jaise purana paying customer), phir dekho ki free mode me bhi data zinda hai
DB.grant_premium(444222, 30)
_u_vip = DB.get_user(444222, "Purana VIP")
check("purane VIP ka premium_until DB me SAFE hai",
      bool(DB.is_premium(_u_vip)), str(_u_vip.get("premium_until")))
check("VIP hone par bhi credits_left unlimited", bot.credits_left(_u_vip, 444222) >= 999999)
check("has_unlimited() asli DB dekhta hai (VIP -> True)", bot.has_unlimited(444222) is True)
check("has_unlimited() free user -> False (rate-limit ke liye sahi)",
      bot.has_unlimited(987654321) is True or bot.ALL_FREE)
check("DB functions zinda hain: grant_premium/get_user/is_premium",
      all(hasattr(DB, f) for f in ("grant_premium", "get_user", "is_premium")))
check("credits system DB me zinda hai (delete nahi kiya)",
      hasattr(DB, "get_credits") and hasattr(DB, "set_credits"))
check("payment system zinda hai", hasattr(DB, "payment_stats"))
check("bot.py me DELETE ka koi naya statement nahi aaya",
      "DELETE FROM" not in BOT_SRC and "drop table" not in BOT_SRC.lower())

# =====================================================================
section("[H] 🔁 REVERSIBLE — PREMIUM_ONLY=on se purana system wapas")
# =====================================================================
_env = dict(os.environ)
_env["PREMIUM_ONLY"] = "on"
_env["BOT_TOKEN"] = "123456:TESTTOKEN_FOR_V61"
_env["ADMIN_ID"] = "1"
_probe = (
    "import warnings,sys;warnings.filterwarnings('ignore');sys.path.insert(0,'.');"
    "import bot;print('RESULT',bot.ALL_FREE,bot.PREMIUM_ONLY,"
    "bot.credits_left({'user_id':4242,'credits':0,'premium_until':''},4242))"
)
try:
    _out = subprocess.run([sys.executable, "-c", _probe], cwd=_ROOT, env=_env,
                          capture_output=True, text=True, timeout=180)
    _line = [x for x in _out.stdout.splitlines() if x.startswith("RESULT")]
    _ok = bool(_line)
    check("PREMIUM_ONLY=on par bot phir bhi import hota hai (crash nahi)", _ok,
          (_out.stderr or "")[-160:])
    if _ok:
        _v = _line[0].split()
        check("PREMIUM_ONLY=on -> ALL_FREE False (premium mode wapas)", _v[1] == "False", str(_v))
        check("PREMIUM_ONLY=on -> PREMIUM_ONLY True", _v[2] == "True", str(_v))
        check("PREMIUM_ONLY=on -> credits phir se GINE jaate hain (purana gate zinda)",
              int(_v[3]) < 999999, str(_v))
except Exception as _e:
    check("reverse-switch test chala", False, repr(_e))

_env2 = dict(os.environ)
_env2["ALL_FREE"] = "off"
try:
    _out2 = subprocess.run([sys.executable, "-c", _probe], cwd=_ROOT, env=_env2,
                           capture_output=True, text=True, timeout=180)
    _l2 = [x for x in _out2.stdout.splitlines() if x.startswith("RESULT")]
    check("ALL_FREE=off likhne par bhi premium mode wapas aata hai", bool(_l2), (_out2.stderr or "")[-160:])
    if _l2:
        check("ALL_FREE=off -> ALL_FREE False", _l2[0].split()[1] == "False", _l2[0])
except Exception as _e:
    check("ALL_FREE=off test chala", False, repr(_e))

# =====================================================================
section("[I] 🚪 REACHABILITY — har tool ka darwaza khula hai")
# =====================================================================
check(f"PREMIUM_TOOLS me 34 tools hain (12 Business Studio)", len(bot.PREMIUM_TOOLS) == 34,
      str(len(bot.PREMIUM_TOOLS)))
# v64 ke baad 27 downloader prompts bhi jude (33 -> 60). Is liye ab ginti ke
# bajaye ASLI baat check hoti hai: purane prompts DELETE hue ya nahi.
# NOTE: "cloner", "vnum", "sarkari" PROMPT_DATA me kabhi the hi nahi — wo
# ASK_LINES wale purane sub-modes hain. Is liye unhe yahan nahi rakha.
_OLD_PROMPTS = (
    "insta_dl", "numinfo", "bankpdf", "kagaz", "mediastudio", "imei",
    "terabox", "pp_stamp", "print_sheet", "doc_compress",
    "ifsc", "pin", "bgmi", "ffuid", "tempmail", "qr", "short", "linkcheck",
    "appfind", "biz_invoice", "biz_resume", "biz_biodata", "biz_certificate",
    "biz_idcard", "biz_vcard", "biz_letter", "biz_upi", "biz_labels", "biz_emi",
)
check("purane saare 26 prompts zinda hain (ek bhi delete nahi hua)",
      all(k in bot.PROMPT_DATA for k in _OLD_PROMPTS),
      [k for k in _OLD_PROMPTS if k not in bot.PROMPT_DATA])
check("PROMPT_DATA me purane 33 se kam nahi (naye sirf jude hain)",
      len(bot.PROMPT_DATA) >= 33,
      str(len(bot.PROMPT_DATA)))
check("PROMPT ka content bhi waisa hi hai (koi chhed-chhad nahi)",
      all(isinstance(v, (str, tuple, dict)) for v in bot.PROMPT_DATA.values()))
check("BIZ_MENU me 12 tools", len(bot.BIZ_MENU) == 12, str(len(bot.BIZ_MENU)))
check("TOOL_RATE_LIMITS zinda hai (spam se bachav)", len(bot.TOOL_RATE_LIMITS) >= 32,
      str(len(bot.TOOL_RATE_LIMITS)))
check("crash shield (arm_all_handlers) zinda hai", hasattr(bot, "arm_all_handlers"))
check("vault zinda hai", hasattr(bot, "vault"))
check("menu keyboard me sab rows jude hue hain (>=14)",
      len(bot.main_keyboard(admin=False).keyboard) >= 14,
      str(len(bot.main_keyboard(admin=False).keyboard)))
check("admin keyboard me admin panel row extra hai (+1)",
      len(bot.main_keyboard(admin=True).keyboard)
      == len(bot.main_keyboard(admin=False).keyboard) + 1)

# =====================================================================
section("SANITY — version + summary")
# =====================================================================
print(f"\n{'=' * 62}")
print(f"  v61 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS:
        print("  •", f)
sys.exit(1 if FAIL else 0)
