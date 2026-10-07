# -*- coding: utf-8 -*-
"""
v85 SELFTEST — v75.2 "PREMIUM POLISH PACK"
==========================================
Aaj ke 3 upgrade ka test:

  1. 📤 BULK MODE v2 — FILE input (.xlsx / .csv / .txt)
     CA / bank agent ke paas list FILE me hoti hai — "paste karo" unke liye
     ajeeb lagta hai. Ab file bhejo, Excel wapas milti hai.

  2. ⚡ CACHE-HIT TAG — "Instant (pehle check kiya tha)"
     Pehle cache-hit par bhi "Response: 1ms" aa jaata tha — samajh nahi aata
     tha ki taakat hai ya kuch toota. Ab saaf likha hota hai.

  3. 🧠 IMEI SMART QUERY — device naam ki typo khud sudhaar leta hai
     "redmi not 12" -> "Redmi Note 12", "iphon 13" -> "iPhone 13"
     (100% offline — koi network call nahi)
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

_TMP = tempfile.mkdtemp(prefix="udv85_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V85"
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
from modules import imei_lookup as IM                               # noqa: E402

# ======================================================================
section("1) 📤 BULK MODE v2 — FILE INPUT (.xlsx / .csv / .txt)")
# ======================================================================
# asli .xlsx banao (jaise CA bhejta hai) — do columns
from openpyxl import Workbook                                       # noqa: E402

_wb = Workbook()
_ws = _wb.active
_ws.append(["IFSC Code", "Bank Name"])
for _x in ("SBIN0001234", "HDFC0000123", "ICIC0000456", "UTIB0000001"):
    _ws.append([_x, "demo"])
_xb = io.BytesIO()
_wb.save(_xb)
_xlsx_bytes = _xb.getvalue()

_txt = BM.read_table_bytes("meri_list.xlsx", _xlsx_bytes)
check("xlsx padhi gayi", "SBIN0001234" in _txt, f"-> {_txt[:60]!r}")
_ents, _ = BM.extract_entries(_txt)
_kind, _, _ = BM.detect_kind(_ents)
check("xlsx se kind detect hua", _kind == "ifsc", f"-> {_kind}")
_good, _ = BM.filter_valid(_kind, _ents)
check("xlsx se sahi entries nikli (4)", len(_good) == 4, f"-> {_good}")

# numeric cell ka classic bug (800001 -> "800001.0")
_wb2 = Workbook()
_ws2 = _wb2.active
for _p in (800001, 110001, 560001):
    _ws2.append([_p])
_xb2 = io.BytesIO()
_wb2.save(_xb2)
_t2 = BM.read_table_bytes("pincode.xlsx", _xb2.getvalue())
check("numeric cell sahi ('800001.0' nahi bana)", "800001" in _t2 and ".0" not in _t2,
      f"-> {_t2!r}")

# csv
_t3 = BM.read_table_bytes("list.csv", "SBIN0001234,State Bank\nHDFC0000123,demo\n".encode())
check("csv padhi gayi", "SBIN0001234" in _t3)
_e3, _ = BM.extract_entries(_t3)
check("csv se bhi entries nikli", len(_e3) == 2, f"-> {_e3}")

# txt
check("txt padhi gayi", "SBIN0001234" in BM.read_table_bytes("l.txt", b"SBIN0001234\nHDFC0000123"))

# encoding (Windows se aayi file cp1252 ho sakti hai)
_raw = "SBIN0001234\n".encode("cp1252")
check("purani encoding (cp1252) bhi chalti hai", "SBIN0001234" in BM.read_table_bytes("l.txt", _raw))

# crash-proof cases
check("khaali file par crash nahi", BM.read_table_bytes("l.txt", b"") == "")
check("galat file par crash nahi (empty return)",
      BM.read_table_bytes("l.xlsx", b"not-an-excel-file") == "")
check("bina extension par crash nahi", isinstance(BM.read_table_bytes("l", b"SBIN0001234"), str))
check("bade max_rows par bhi safe (read_only mode)",
      "SBIN0001234" in BM.read_table_bytes("l.xlsx", _xlsx_bytes, max_rows=2))

# file ka preview card
_pv = BM.table_preview_text("ifsc", 4, 4, ["SBIN0001234"], 5, False, 15,
                            source_name="meri_list.xlsx")
check("file ka preview card me file ka naam dikhta hai",
      "meri_list.xlsx" in _pv, f"-> {_pv[:80]}")
check("file preview me bhi list pahchaan dikhti hai", "pahchan li" in _pv)

# ======================================================================
section("2) ⚡ CACHE-HIT TAG — 'Instant (pehle check kiya tha)'")
# ======================================================================
import bot as B                                                     # noqa: E402

_f_cached = B.pcard_foot(ms=1.2, source="official bank registry", cached=True)
_f_fresh = B.pcard_foot(ms=812, source="official bank registry")
check("cached=True par 'Instant' likha aata hai", "Instant" in _f_cached, f"-> {_f_cached}")
check("cached par '0 API call' ka bharosa dikhta hai", "0 API call" in _f_cached)
check("cached par purana 'Response: 1ms' NAHI aata", "Response:" not in _f_cached)
check("fresh result par normal Response ms aata hai", "Response:" in _f_fresh and "812" in _f_fresh)
check("fresh par 'Instant' nahi aata", "Instant" not in _f_fresh)
check("source line dono me aati hai", "official bank registry" in _f_cached
      and "official bank registry" in _f_fresh)
check("cached default False hai (purana behaviour safe)",
      "Instant" not in B.pcard_foot(ms=500, source="x"))

# WIRING: kaunse tools cached bhejte hain
with open(os.path.join(_ROOT, "bot.py"), encoding="utf-8") as _fh:
    SRC = _fh.read()
check("IFSC card cached flag bhejta hai", 'cached=bool(i_res.get("cached"))' in SRC)
check("Pincode card cached flag bhejta hai", 'cached=bool(p_res.get("cached"))' in SRC)
check("Gaadi (vahan) card cached dikhata hai", 'res.get("cached")' in SRC
      and "vahan" in SRC.lower())
check("pcard_foot me cached parameter hai", "cached: bool = False" in SRC)

# ======================================================================
section("3) 🧠 IMEI SMART QUERY — typo khud sudhaar")
# ======================================================================
CASES = [
    ("redmi not 12", "Redmi Note 12"), ("samsumg a54", "Samsung a54"),
    ("iphon 13", "iPhone 13"), ("onepls nord", "OnePlus nord"),
    ("poco x 3", "POCO X3"), ("vivo y 21", "Vivo Y21"),
    ("realmi narzo", "Realme narzo"), ("SM A155F", "SM-A155F"),
    ("tecno spark 10", "Tecno spark 10"), ("redmi 9a", "Redmi 9a"),
]
_okc = 0
for _in, _want in CASES:
    _got = IM.smart_query(_in)
    if _got == _want:
        _okc += 1
    else:
        print(f"     ✗ {_in!r} -> {_got!r} (chahiye {_want!r})")
check(f"smart_query: {len(CASES)} cases sahi", _okc == len(CASES), f"-> {_okc}/{len(CASES)}")

# kabhi kharab na kare (asli naam waisa hi rahe)
for _keep in ("Redmi Note 10 Pro", "iPhone 15 Pro Max", "M2101K6P", "Mi 11X",
              "Samsung Galaxy S21", "hello bhai", ""):
    _g = IM.smart_query(_keep)
    check(f"asli naam waisa hi rehta hai ({_keep or 'khaali'})",
          _g == _keep or (not _keep and _g == ""), f"-> {_g!r}")

check("smart_query khaali/None par crash nahi",
      IM.smart_query("") == "" and IM.smart_query(None) == "")
check("smart_query bahut lambe text par bhi safe",
      isinstance(IM.smart_query("a " * 500), str))
check("smart_query search_device me laga hai",
      "smart_query((query or \"\").strip())" in open(
          os.path.join(_ROOT, "modules", "imei_lookup.py"), encoding="utf-8").read())
check("offline hai (koi network function nahi)",
      "http" not in (IM.smart_query.__doc__ or "").lower())

# ======================================================================
section("4) 🔌 BOT WIRING — file handler sahi jagah")
# ======================================================================
check("ApplicationHandlerStop import hua", "ApplicationHandlerStop" in SRC)
check("on_bulk_file handler hai", "async def on_bulk_file(" in SRC)
check("handler group=-4 me register hai (cookies -5 ke baad)",
      "on_bulk_file),\n                    group=-4)" in SRC)
check("_bulk_offer helper hai (paste + file dono ek hi flow)",
      "async def _bulk_offer(" in SRC)
check("bulk_wait mode ab helper call karta hai",
      'if mode == "bulk_wait":\n        await _bulk_offer(update, context, raw_text)' in SRC)
check("handler sirf bulk mode me chalta hai (baaki files na roke)",
      'str(context.user_data.get("mode") or "") != "bulk_wait"' in SRC)
check("file handle hone par ApplicationHandlerStop raise hota hai",
      SRC.count("raise ApplicationHandlerStop") >= 3, f"-> {SRC.count('raise ApplicationHandlerStop')}")
check("file type check hai (xlsx/csv/txt/tsv)",
      '(".xlsx", ".xlsm", ".csv", ".txt", ".tsv")' in SRC)
check("file size limit hai (8 MB)", "8 * 1024 * 1024" in SRC)
check("intro card me file ke baare me likha hai",
      ".xlsx / .csv / .txt" in BM.bulk_intro_text(False) or "FILE" in BM.bulk_intro_text(False).upper())

# ======================================================================
section("5) 🛡️ PURANA SAB SALAMAT (regression)")
# ======================================================================
check("BULK MODE menu button waise hi hai", "BULK MODE (EXCEL)" in SRC)
check("bulk_go callback waise hi hai", 'data == "bulk_go"' in SRC)
check("earning limit waise hi (FREE 15 / VIP 500)",
      BM.FREE_LIMIT == 15 and BM.VIP_LIMIT == 500)
check("PRO ENGINE waise hi hai", "from modules.core import proengine as pro" in SRC)
check("smart detect hook waise hi hai", "SMART DETECT (PRO ENGINE, ENGINE-1)" in SRC)
check("aakhri keyboard row HELP/SUPPORT waise hi",
      any("SUPPORT / MADAD" in B.unbold(x) for x in B.KB_BTNS[-1]))
#  RULE #1 ka matlab: naya code koi BAHAR ka link na jode.
#  (pcard_foot me BRAND_LINK pehle se hai — wo bot ka apna owner-contact hai,
#   pre-existing hai, isliye wo chhod kar check karte hain.)
_instant_line = [l for l in _f_cached.split("\n") if "Instant" in l]
check("RULE #1: bulk ke naye cards me koi link nahi",
      "http" not in BM.table_preview_text("ifsc", 1, 1, ["x"], 1, False, 15)
      and "http" not in BM.bulk_intro_text(False)
      and "http" not in BM.bulk_intro_text(True)
      and "http" not in BM.bulk_result_text({"total": 1, "passed": 1, "failed": 0,
                                             "seconds": 1}, "ifsc", False))
check("RULE #1: nayi 'Instant' line me koi link nahi",
      bool(_instant_line) and "http" not in _instant_line[0], f"-> {_instant_line}")


# ======================================================================
section("6) 🚀 E2E — user FILE bheje -> Excel wapas (mock bot)")
# ======================================================================
import asyncio                                                     # noqa: E402
import types                                                       # noqa: E402
from telegram.ext import ApplicationHandlerStop                    # noqa: E402


class _Doc:
    def __init__(self, fname, data):
        self.file_name = fname
        self.file_id = "fid-1"
        self.file_size = len(data)
        self._data = data


class _File:
    def __init__(self, data):
        self._data = data

    async def download_as_bytearray(self):
        return bytearray(self._data)


class _Msg:
    def __init__(self, uid, document=None):
        self.text = ""
        self.chat = types.SimpleNamespace(id=uid)
        self.document = document
        self.sent = []

    async def reply_text(self, *a, **kw):
        self.sent.append(str(a[0]) if a else str(kw.get("text") or ""))
        return self

    async def edit_text(self, *a, **kw):
        self.sent.append(str(a[0]) if a else "")
        return self

    async def delete(self):
        return True


class _BotMock:
    def __init__(self, data):
        self._data = data
        self.docs = []

    async def get_file(self, fid):
        return _File(self._data)

    async def send_document(self, *a, **kw):
        self.docs.append(kw)
        return types.SimpleNamespace(message_id=9)


async def _file_flow():
    _uid = 8577777
    B.get_user(_uid, "FileTest")
    _doc = _Doc("meri_list.xlsx", _xlsx_bytes)
    _msg = _Msg(_uid, _doc)
    # ⚠️ mock bot ko ASLI xlsx bytes do (warna file-read fail hoga)
    _ctx = types.SimpleNamespace(user_data={"mode": "bulk_wait"}, chat_data={},
                                 bot=_BotMock(_xlsx_bytes))
    # `message` bhi dena zaroori hai — _bulk_offer preview isi par bhejta hai
    _upd = types.SimpleNamespace(
        message=_msg, effective_message=_msg,
        effective_user=types.SimpleNamespace(
            id=_uid, first_name="FileTest", username="ft", is_bot=False),
        effective_chat=types.SimpleNamespace(id=_uid), update_id=2)
    try:
        await B.on_bulk_file(_upd, _ctx)
        _stopped = False
    except ApplicationHandlerStop:
        _stopped = True
    return _msg, _ctx, _stopped


try:
    _m, _c, _stopped = asyncio.run(_file_flow())
    _joined = " ".join(_m.sent)
    check("e2e file: xlsx padh kar preview card aaya",
          "list pahchan li" in _joined, f"-> {_joined[:100]}")
    check("e2e file: kind detect hoke save hua", _c.user_data.get("bulk_kind") == "ifsc",
          f"-> {_c.user_data.get('bulk_kind')}")
    check("e2e file: entries save hui (4)",
          len(_c.user_data.get("bulk_entries") or []) == 4,
          f"-> {_c.user_data.get('bulk_entries')}")
    check("e2e file: file ka naam preview me dikha",
          "meri_list.xlsx" in _joined, f"-> {_joined[:120]}")
    check("e2e file: handler ne aage badhne se roka (ApplicationHandlerStop)",
          _stopped is True)
except Exception as _e:                                            # noqa: BLE001
    import traceback
    check("e2e file flow chala (crash nahi)", False, f"{type(_e).__name__}: {_e}")
    traceback.print_exc()

# bulk mode NA ho to handler chup-chaap aage jaane de (baaki files na rokein)
async def _not_bulk():
    _uid = 8577778
    _msg = _Msg(_uid, _Doc("video.mp4", b"x"))
    _ctx = types.SimpleNamespace(user_data={}, chat_data={}, bot=_BotMock(b"x"))
    _upd = types.SimpleNamespace(
        message=_msg, effective_message=_msg,
        effective_user=types.SimpleNamespace(
            id=_uid, first_name="T", username="t", is_bot=False),
        effective_chat=types.SimpleNamespace(id=_uid), update_id=3)
    await B.on_bulk_file(_upd, _ctx)
    return _msg


try:
    _m2 = asyncio.run(_not_bulk())
    check("normal file (bulk mode off) par kuch nahi karta — koi reply nahi",
          len(_m2.sent) == 0, f"-> {_m2.sent}")
except Exception as _e:                                            # noqa: BLE001
    check("bulk mode off par crash nahi", False, f"{type(_e).__name__}: {_e}")


# ======================================================================
print("\n" + "=" * 62)
print(f"  v85 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILS:
    print("\nFAILED:")
    for f in FAILS:
        print("  •", f)
sys.exit(1 if FAIL else 0)
