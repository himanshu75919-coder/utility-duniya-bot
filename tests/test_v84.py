# -*- coding: utf-8 -*-
"""
v84 SELFTEST — 📤 BULK MODE (v75.1) — earning tool
===================================================
Ye tool paisa banane ke liye hai (CA / bank agent / insurance agent /
transport wale ek file daal ke Excel maangte hain — ek banda = 500 users).

Ye test sabit karta hai:
  1. 🧠 List pahchan (IFSC / pincode / mobile / gaadi / link) — junk ignore
  2. 🔀 Excel/CSV paste clean hota hai (tab/comma/numbering/semicolon)
  3. ⚡ Parallel engine chalta hai (bounded workers — upstream safe)
  4. 📊 Asli .xlsx banti hai (openpyxl) — headers, colours, freeze pane
  5. 💰 Earning limit: free = 15, VIP = 500 (upsell ka base)
  6. 🛡️ Zero crash: khaali list / junk list / nakli kind — sab safe
  7. 🔌 bot.py wiring (menu button, BTN_MODE_MAP, /bulk, callbacks)
  8. RULE #1 — koi bahar ka link nahi
"""
import io
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv84_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V84"
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


from modules import bulk_mode as BM                                 # noqa: E402

# ======================================================================
section("1) 🧠 LIST PAHCHAN (detect) — 5 types + junk")
# ======================================================================
_paste = """1. SBIN0001234\tState Bank of India\tPatna
HDFC0000123
ICIC0000456
- UTIB0000001
2) KK BK0001234
bank list (heading)
khaali
"""
_e, _lines = BM.extract_entries(_paste)
_k, _m, _s = BM.detect_kind(_e)
check("IFSC list pahchani gayi", _k == "ifsc", f"-> {_k}")
#  4 asli IFSC: SBIN0001234, HDFC0000123, ICIC0000456, UTIB0000001
#  ("KK BK0001234" galat hai — beech me space, isliye skip hona chahiye)
check("Excel tab + numbering saaf hui (4 asli IFSC)",
      sum(1 for x in _e if BM.valid_entry("ifsc", x)) == 4,
      f"-> {_e}")
# extract() raw candidates deta hai (junk hataana filter_valid ka kaam hai).
# Yahan sabse zaroori: junk line TOOTI nahi (poori line rahe, tukde na banein)
check("junk line tooti nahi (KK / BK0001234 alag nahi hue)",
      "KK BK0001234" in _e and "KK" not in _e and "BK0001234" not in _e,
      f"-> {_e}")
_g0, _sk0 = BM.filter_valid("ifsc", _e)
check("filter_valid ke baad sirf asli IFSC bache (junk gaya)",
      len(_g0) == 4 and all(BM.valid_entry("ifsc", x) for x in _g0),
      f"-> {_g0}")
check("filter_valid: junk + galat format skip hui",
      _sk0 == 3 and not any("bank list" in x.lower() or x.lower() == "khaali" for x in _g0),
      f"-> skipped={_sk0}")
check("ek line me 2 entries split hoti hain (space-separated)",
      BM.extract_entries("9876543210 8765432109")[0] == ["9876543210", "8765432109"],
      f"-> {BM.extract_entries('9876543210 8765432109')[0]}")

_g, _sk = BM.filter_valid("ifsc", _e)
check("filter_valid: sirf sahi IFSC bache", all(BM.valid_entry("ifsc", x) for x in _g))
check("filter_valid: skip count milta hai", _sk >= 1, f"-> {_sk}")

# pincode
_e2, _ = BM.extract_entries("800001\n110001\n560001\n400001")
_k2, _, _s2 = BM.detect_kind(_e2)
check("pincode list pahchani gayi", _k2 == "pincode", f"-> {_k2}")
check("pincode sample sahi", "800001" in _s2)

# mobile
_e3, _ = BM.extract_entries("9876543210\n8765432109\n7654321098")
_k3, _, _ = BM.detect_kind(_e3)
check("mobile list pahchani gayi", _k3 == "mobile", f"-> {_k3}")

# gaadi
_e4, _ = BM.extract_entries("BR01AB1234\nDL8CAF5030\nMH12DE1433")
_k4, _, _ = BM.detect_kind(_e4)
check("gaadi number list pahchani gayi", _k4 == "vehicle", f"-> {_k4}")

# link
_e5, _ = BM.extract_entries("https://example.com/a\nhttps://test.in/b\nwww.foo.com")
_k5, _, _ = BM.detect_kind(_e5)
check("link list pahchani gayi", _k5 == "url", f"-> {_k5}")

# gibberish
_e6, _ = BM.extract_entries("hello bhai\nkaise ho\ntheek hai")
_k6, _, _ = BM.detect_kind(_e6)
check("bakwaas text par koi kind nahi (false positive zero)", _k6 == "", f"-> {_k6}")

# galat format ke saath mix (majority vote)
_e7, _ = BM.extract_entries("SBIN0001234\nHDFC0000123\n9876543210\n800001")
_k7, _, _ = BM.detect_kind(_e7)
check("mix list me majority (IFSC) jeeti", _k7 == "ifsc", f"-> {_k7}")


# ======================================================================
section("2) 🧹 PASTE CLEANING (Excel / CSV / numbering / semicolon)")
# ======================================================================
_t1 = "SBIN0001234\tState Bank\tPatna, Bihar"
check("Excel tab paste -> pehla column", BM.extract_entries(_t1)[0][0] == "SBIN0001234",
      f"-> {BM.extract_entries(_t1)[0]}")
check("CSV paste -> pehla column", BM.extract_entries("SBIN0001234,State Bank,Patna")[0][0] == "SBIN0001234")
check("numbering hatti hai (1. / 2) / - )",
      BM.extract_entries("1. SBIN0001234")[0][0] == "SBIN0001234"
      and BM.extract_entries("5) HDFC0000123")[0][0] == "HDFC0000123"
      and BM.extract_entries("- ICIC0000456")[0][0] == "ICIC0000456")
check("duplicate hatta hai (upstream par dobara call nahi)",
      BM.extract_entries("SBIN0001234\nsbin0001234")[0] == ["SBIN0001234"])
check("bullet • bhi saaf hota hai", BM.extract_entries("• UTIB0000001")[0][0] == "UTIB0000001")
check("quotes saaf hote hain", BM.extract_entries('"SBIN0001234"')[0][0] == "SBIN0001234")

_lim_ents, _ = BM.extract_entries("\n".join(f"SBIN000{i:04d}" for i in range(600)),
                                  limit=BM.VIP_LIMIT)
check(f"limit kaam karta hai (600 -> {BM.VIP_LIMIT})", len(_lim_ents) == BM.VIP_LIMIT,
      f"-> {len(_lim_ents)}")


# ======================================================================
section("3) ⚡ PARALLEL ENGINE (bounded workers, zero crash)")
# ======================================================================
import time as _t                                                  # noqa: E402

_ticks = {"n": 0}


def _prog(i, total):
    _ticks["n"] = i


_r = BM.run_bulk("pincode", ["800001", "110001"], on_progress=_prog, workers=2)
check("run_bulk: ok", bool(_r.get("ok")), f"-> {_r.get('error')}")
check("run_bulk: total sahi", _r["total"] == 2)
check("run_bulk: har entry ki row bani", len(_r["rows"]) == 2, f"-> {len(_r['rows'])}")
check("run_bulk: passed+failed = total",
      _r["passed"] + _r["failed"] == _r["total"])
check("run_bulk: progress callback chala", _ticks["n"] == 2, f"-> {_ticks['n']}")
check("run_bulk: time record hota hai", float(_r.get("seconds") or 0) >= 0)
check("run_bulk: input order maintain rehta hai",
      [str(x[0]) for x in _r["rows"]] == ["800001", "110001"])

# crash-proof cases
_r2 = BM.run_bulk("pincode", [])
check("khaali list par crash nahi", _r2.get("ok") is False and _r2["rows"] == [])
_r3 = BM.run_bulk("galat-kind", ["800001"])
check("nakli kind par crash nahi", _r3.get("ok") is False)
_r4 = BM.run_bulk("ifsc", ["SBIN0001234", "@@@junk@@@"])
check("junk entry par poora run nahi girta", _r4["total"] == 2 and len(_r4["rows"]) == 2)
check("junk entry FAIL mark hoti hai", _r4["rows"][1][-2] == "FAIL",
      f"-> {_r4['rows'][1][-2]}")

_workers = BM.MAX_WORKERS
check("workers bounded hain (upstream ko maar nahi dalte)", 1 <= _workers <= 8, f"-> {_workers}")


# ======================================================================
section("4) 📊 ASLI EXCEL (.xlsx) — openpyxl")
# ======================================================================
_blob = BM.to_xlsx(_r)
check("xlsx bytes bane", len(_blob) > 1000, f"-> {len(_blob)} bytes")
check("xlsx asli format hai (ZIP magic PK)", _blob[:2] == b"PK")

try:
    from openpyxl import load_workbook
    _wb = load_workbook(io.BytesIO(_blob))
    _ws = _wb.active
    check("sheet khulti hai", _ws.max_row >= 3 and _ws.max_column >= 5,
          f"-> {_ws.max_row}x{_ws.max_column}")
    check("header row sahi hai", str(_ws.cell(row=1, column=1).value) == "Input")
    check("data row me pincode", str(_ws.cell(row=2, column=1).value) == "800001")
    check("sheet title me forbidden character nahi (: \\ / ? * [ ])",
          not any(ch in _ws.title for ch in ':\\\\/?*[]'), f"-> {_ws.title}")
    check("freeze pane laga hai (badi file scroll me header dikhe)",
          str(_ws.freeze_panes) == "A2", f"-> {_ws.freeze_panes}")
    check("header par colour hai (premium feel)",
          _ws.cell(row=1, column=1).fill.fgColor.rgb not in (None, "00000000"))
except Exception as _e:                                            # noqa: BLE001
    check("xlsx padhi ja sake", False, str(_e)[:120])

# har kind ke liye headers hain
for _kd in BM.KINDS:
    check(f"kind '{_kd}' ke headers set hain", len(BM.KINDS[_kd]["cols"]) >= 6)

# csv fallback
_c = BM.to_csv(_r)
check("csv fallback bhi banta hai (openpyxl na ho to)",
      _c[:3] == b"\xef\xbb\xbf" and b"800001" in _c)


# ======================================================================
section("5) 💰 EARNING MODEL (free 15 vs VIP 500)")
# ======================================================================
check("free limit set hai", BM.FREE_LIMIT == 15, f"-> {BM.FREE_LIMIT}")
check("VIP limit zyada hai (upsell ka base)", BM.VIP_LIMIT > BM.FREE_LIMIT,
      f"-> {BM.VIP_LIMIT} vs {BM.FREE_LIMIT}")
_lim0, _vip0 = BM.limits_for(0)
check("naya user = free limit", _lim0 == BM.FREE_LIMIT and _vip0 is False)

import bot as B                                                    # noqa: E402
from database import grant_premium as _grant                       # noqa: E402
_vip_uid = 8499999
B.get_user(_vip_uid, "VipTest")
_grant(_vip_uid, 30)
_lim1, _vip1 = BM.limits_for(_vip_uid)
check("VIP user = VIP limit (500 entries)",
      _lim1 == BM.VIP_LIMIT and _vip1 is True, f"-> {_lim1} {_vip1}")
check("admin = unlimited", BM.limits_for(1)[0] == BM.VIP_LIMIT)

_txt_free = BM.bulk_intro_text(vip=False)
_txt_vip = BM.bulk_intro_text(vip=True)
check("intro card me free limit dikhti hai", str(BM.FREE_LIMIT) in _txt_free)
check("intro card me VIP ko 500 dikhta hai", str(BM.VIP_LIMIT) in _txt_vip)
check("result card VIP ko upsell nahi karta",
      "VIP me le lo" not in BM.bulk_result_text(_r, "pincode", vip=True))
check("result card free user ko upsell karta hai",
      "VIP" in BM.bulk_result_text(_r, "pincode", vip=False))


# ======================================================================
section("6) 🚫 v79: 3 TOOLS HATE — BULK MODE / REFER & EARN / HELP-TUTORIAL")
# ======================================================================
with open(os.path.join(_ROOT, "bot.py"), encoding="utf-8") as fh:
    SRC = fh.read()

# --- keyboard: teeno buttons gayab, SUPPORT aakhri row par akela ---
_labels = [B.unbold(x).upper() for r in B.KB_BTNS for x in r]
for gone in ("BULK MODE", "REFER & EARN", "HELP / TUTORIAL"):
    check(f"keyboard me '{gone}' NAHI hai", not any(gone in l for l in _labels),
          str([l for l in _labels if gone in l][:2]))
check("MY ACCOUNT button zinda hai (REFER wali row se hataya, delete nahi kiya)",
      any("MY ACCOUNT" in l for l in _labels))
check("SUPPORT / MADAD aakhri row par hai (v102: MY ACCOUNT ke saath)",
      any("SUPPORT" in B.unbold(x).upper() for x in B.KB_BTNS[-1]))
check("aakhri row me ab HELP/TUTORIAL saath me NAHI",
      not any("HELP" in B.unbold(x).upper() or "TUTORIAL" in B.unbold(x).upper() for x in B.KB_BTNS[-1]))

# --- text aliases (typing se tool na khule) ---
for alias in ("BULK MODE (EXCEL)", "BULK MODE", "BULK EXCEL", "BULK REPORT",
              "EXCEL REPORT", "REFER & EARN", "HELP / TUTORIAL"):
    check(f"BTN_MODE_MAP se '{alias}' hataya", alias not in B.BTN_MODE_MAP)
check("BTN_MODE_MAP me SUPPORT ab bhi hai", B.BTN_MODE_MAP.get("SUPPORT / MADAD") == "support")

# --- dead commands register NAHI hone chahiye ---
for cmd in ('CommandHandler(["bulk", "bulkexcel", "report"]',
            'CommandHandler("refer"',
            'CommandHandler(["tutorial", "madad", "guide"]'):
    check(f"command unregister: {cmd[:34]}…", cmd not in SRC)
check("cmd_bulk function code me thi (logic nahi badla, sirf wiring hati)",
      "async def cmd_bulk(" in SRC)

# --- SUPPORT branch me se tutorial card ka rasta band ---
check("SUPPORT branch ab sirf support_card() bhejta hai",
      "_txt, _kb = support_card()" in SRC)
check("SUPPORT branch me TUTORIAL_NOTICE ka use nahi raha",
      'if "SUPPORT" in norm_text else (TUTORIAL_NOTICE, tutorial_kb())' not in SRC)

# --- tutorial VIDEOS: repo + code se permanent delete ---
check("tutorial_videos/ folder repo me nahi hai",
      not os.path.isdir(os.path.join(_ROOT, "tutorial_videos")))
check("koi .mp4 tracked nahi (git ls-files)",
      ".mp4" not in __import__("subprocess").run(
          ["git", "-C", _ROOT, "ls-files"], capture_output=True, text=True).stdout)
from modules import tutorial_hub as TH                                  # noqa: E402
check("tutorial_hub.VIDEOS_REMOVED flag on", TH.VIDEOS_REMOVED is True)
check("has_video() har action par False",
      not any(TH.has_video(a) for a in ("video_dl", "qr", "terabox", "cloner", "refer")))
check("video_urls() khaali", TH.video_urls("qr") == [] and TH.video_urls("video_dl") == [])
check("tutorial_video_url() khaali",
      TH.tutorial_video_url("qr") == "" and TH.tutorial_video_url_fallback("qr") == "")
check("TUTORIAL_VIDEO_KEYS khali map (naye videos bhi auto-off)",
      TH.TUTORIAL_VIDEO_KEYS == {})
check("bulk_mode engine abhi bhi unit-testable hai (sirf tool hata, code nahi)",
      callable(getattr(BM, "bulk_intro_text", None)))

# RULE #1 NO-LINK
check("RULE #1: bulk module me document me koi link nahi",
      "http://" not in (BM.__doc__ or "") and "t.me/" not in (BM.__doc__ or ""))
check("RULE #1: intro card me koi link nahi", "http" not in _txt_free)
check("RULE #1: result card me koi link nahi",
      "http" not in BM.bulk_result_text(_r, "pincode", vip=False))


# ======================================================================
section("7) 🚀 END-TO-END — user list bhejta hai -> Excel milti hai (mock bot)")
# ======================================================================
import asyncio                                                     # noqa: E402
import types                                                       # noqa: E402


class _Msg:
    def __init__(self, text, uid):
        self.text = text
        self.chat = types.SimpleNamespace(id=uid)
        self.sent = []
        self.docs = []

    async def reply_text(self, *a, **kw):
        self.sent.append(str(a[0]) if a else str(kw.get("text") or ""))
        return self

    async def reply_document(self, *a, **kw):
        self.docs.append(kw)
        return self


class _User:
    def __init__(self, uid):
        self.id = uid
        self.first_name = "Bulk"
        self.username = "bulktester"
        self.is_bot = False


class _Upd:
    def __init__(self, uid, text):
        self.message = _Msg(text, uid)
        self.effective_user = _User(uid)
        self.effective_chat = types.SimpleNamespace(id=uid)
        self.effective_message = self.message
        self.update_id = 1


class _Ctx:
    def __init__(self):
        self.user_data = {}
        self.chat_data = {}
        self.bot = None


class _BotMock:
    """send_document ko capture karta hai (asli network nahi)."""
    def __init__(self):
        self.sent_docs = []

    async def send_document(self, *a, **kw):
        self.sent_docs.append(kw)
        return types.SimpleNamespace(message_id=1)

    async def get_file(self, *a, **kw):
        raise RuntimeError("no network in test")


async def _flow():
    _uid = 8488888
    B.get_user(_uid, "Bulk")
    _u, _c = _Upd(_uid, "📤 BULK MODE (EXCEL)"), _Ctx()
    _c.bot = _BotMock()
    await B._on_text_pro(_u, _c)
    intro = _u.message.sent[-1]
    mode_after_menu = _c.user_data.get("mode")

    # list paste
    _u2, _c2 = _Upd(_uid, "SBIN0001234\nHDFC0000123\nICIC0000456"), _Ctx()
    _c2.bot = _BotMock()
    _c2.user_data["mode"] = "bulk_wait"
    await B._on_text_pro(_u2, _c2)
    preview = _u2.message.sent[-1]
    kind_set = _c2.user_data.get("bulk_kind")
    ents = list(_c2.user_data.get("bulk_entries") or [])
    return intro, mode_after_menu, preview, kind_set, ents, _c2


try:
    _intro, _mode, _prev, _kind, _ents, _ctx2 = asyncio.run(_flow())
    # v79: tool hata diya gaya — "📤 BULK MODE (EXCEL)" type karne par ab
    # intake khulna NA chahiye (engine direct drive se niche test hota hai).
    check("e2e: BULK MODE type karne par ab intake NAHI khulta (tool hataya)",
          _mode != "bulk_wait", f"-> mode={_mode}")
    check("e2e: bulk card ka koi jhootha promise nahi gaya user ko",
          "list de" not in _intro and "BULK MODE" not in _intro, f"-> {_intro[:70]}")
    check("e2e: list paste par preview card aata hai",
          "list pahchan li" in _prev or "pahchan" in _prev, f"-> {_prev[:80]}")
    check("e2e: kind detect hoke save hui", _kind == "ifsc", f"-> {_kind}")
    check("e2e: entries save hui (3)", len(_ents) == 3, f"-> {_ents}")
    check("e2e: preview me confirm button ka zikr hai", "dabao" in _prev.lower() or "chalu" in _prev.lower())

    # junk list -> saaf message, crash nahi
    async def _junk():
        _u3, _c3 = _Upd(8488888, "hello bhai kaisa hai\ntheek hai"), _Ctx()
        _c3.bot = _BotMock()
        _c3.user_data["mode"] = "bulk_wait"
        await B._on_text_pro(_u3, _c3)
        return _u3.message.sent[-1]

    _j = asyncio.run(_junk())
    check("e2e: junk list par saaf message (crash nahi)", "pahchan nahi" in _j, f"-> {_j[:70]}")
except Exception as _e:                                            # noqa: BLE001
    import traceback
    check("e2e flow chala (crash nahi)", False, f"{type(_e).__name__}: {_e}")
    traceback.print_exc()


# ======================================================================
print("\n" + "=" * 62)
print(f"  v84 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILS:
    print("\nFAILED:")
    for f in FAILS:
        print("  •", f)
sys.exit(1 if FAIL else 0)
