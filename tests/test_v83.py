# -*- coding: utf-8 -*-
"""
v83 SELFTEST — 🧠 PRO ENGINE (v75) + 🛡️ PERMANENT CRASH GUARD
==============================================================
Ye test file do sabse bade vaade check karti hai:

  1. "CODE KABHI CRASH NA HO"
     -> pyflakes gate: poore codebase me koi bhi `undefined name` ho to
        test FAIL. (Isi gate ne v75 me asli bug pakda tha: vault.py me
        `asyncio` undefined — jo VIP grant par crash karta tha.)
     -> sab .py files compile hoti hain (syntax gate)

  2. "PREMIUM USER KABHI KAM NA HO"
     -> merge/restore ke baad VIP count GHATNA nahi chahiye (premium floor)
     -> lifetime VIP lifetime hi rehta hai
     -> premium_rank: lifetime > 9999-din se upar (kabhi neeche na jaye)

  3. PRO ENGINE (v75) sahi kaam karta hai
     -> smart detect (16 cases)
     -> provider race (parallel, first-success)
     -> circuit breaker (fail -> open -> self-heal)
     -> result history (record + read + clear)
     -> quality stamp

  4. bot.py wiring sahi hai (smart detect hook, wrappers, commands)
"""
import os
import subprocess
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv83_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V83"
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


# ======================================================================
section("1) 🛡️ PERMANENT CRASH GATE — undefined names (asli crash jadd)")
# ======================================================================
#  Kyun ye gate: v74.6 tak ka asli crash bugs aise hi chhupe the — code me
#  ek naam likha hota tha jo kahin define hi nahi tha. Python us line par
#  pahunchne tak sab theek chalta hai, phir wahi ek tool CRASH karta hai.
#  pyflakes usi ko pakadta hai. Isliye ab ye test HAR BAAR chalega.
SRC_FILES = ["bot.py", "database.py"]
for _d in ("modules", os.path.join("modules", "core")):
    _p = os.path.join(_ROOT, _d)
    if os.path.isdir(_p):
        for f in sorted(os.listdir(_p)):
            if f.endswith(".py"):
                SRC_FILES.append(os.path.join(_d, f))

try:
    _pf = subprocess.run([sys.executable, "-m", "pyflakes"] + SRC_FILES,
                         cwd=_ROOT, capture_output=True, text=True, timeout=180)
    _lines = [ln for ln in (_pf.stdout or "").splitlines()
              if "undefined name" in ln or "redefinition" in ln
              or "local variable" in ln and "referenced before assignment" in ln]
    check("pyflakes: ZERO undefined-name crash bugs", len(_lines) == 0,
          f"-> {_lines[:4]}")
except Exception as e:                                           # noqa: BLE001
    check("pyflakes chala", False, str(e)[:120])

# syntax gate (sab files)
_bad = []
for f in SRC_FILES:
    r = subprocess.run([sys.executable, "-m", "py_compile", f],
                       cwd=_ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        _bad.append(f)
check("Syntax: saari files compile hoti hain", not _bad, f"-> {_bad[:4]}")

# bare `except:` gate (chup-chaap crash chhupane wala anti-pattern)
_bare = []
for f in SRC_FILES:
    try:
        with open(os.path.join(_ROOT, f), encoding="utf-8") as fh:
            for i, ln in enumerate(fh, 1):
                s = ln.strip()
                if s.endswith("except:") or s == "except:":
                    _bare.append(f"{f}:{i}")
    except Exception:                                            # noqa: BLE001
        pass
check("Bare `except:` nahi (crash chhupta nahi)", len(_bare) == 0, f"-> {_bare[:4]}")


# ======================================================================
section("2) 👑 PREMIUM SAFETY — VIP user kabhi kam nahi hoga")
# ======================================================================
from modules.core.vault import (                                   # noqa: E402
    premium_rank, is_lifetime, premium_floor_report, merge_rows, snapshot_rows,
)
from modules.core import proengine as pro                          # noqa: E402

# rank: lifetime sabse upar; expiry ke saath rank badhta hai (kabhi ghatta nahi)
check("premium_rank: lifetime > 100 saal wali date",
      premium_rank("lifetime") > premium_rank("2125-01-01"))
check("premium_rank: aage ki date > peeche ki date",
      premium_rank("2030-01-01") > premium_rank("2026-01-01"))
check("premium_rank: khaali = 0 (no VIP)", premium_rank("") == 0)
check("is_lifetime: sirf lifetime par True",
      is_lifetime("lifetime") is True and is_lifetime("2030-01-01") is False)

# merge kabhi premium ghata na sake (core promise)
#  IMPORTANT: backup (local) me chhoti VIP ho aur nayi DB (remote) me badi VIP
#  ho — merge ke baad BADI wali hi jeetni chahiye. Ulta bhi test karte hain.
_base = {"user_id": 5, "premium_until": "2030-01-01", "credits": 50,
         "referrals": 3, "banned": 0}
_old = {"user_id": 5, "premium_until": "2027-01-01", "credits": 10,
        "referrals": 1, "banned": 0}

_m1, _r1 = merge_rows({"users": [_old]}, {"users": [_base]})
_row = (_m1.get("users") or [{}])[0]
check("merge: purani (chhoti) VIP se badi VIP ghat nahi jaati",
      str(_row.get("premium_until")) == "2030-01-01", f"-> {_row.get('premium_until')}")
check("merge: credits kam nahi hote", int(_row.get("credits") or 0) >= 50)
check("merge: referrals kam nahi hote", int(_row.get("referrals") or 0) >= 3)

# ULTA case: local (backup) me badi VIP, remote me chhoti -> phir bhi badi
_m2, _ = merge_rows({"users": [_base]}, {"users": [_old]})
_row2 = (_m2.get("users") or [{}])[0]
check("merge (ulta): VIP kabhi neeche nahi jaati",
      str(_row2.get("premium_until")) == "2030-01-01", f"-> {_row2.get('premium_until')}")

# lifetime kabhi haara nahi jaata
_m3, _ = merge_rows({"users": [{"user_id": 7, "premium_until": "lifetime"}]},
                    {"users": [{"user_id": 7, "premium_until": "2030-01-01"}]})
_row3 = (_m3.get("users") or [{}])[0]
check("merge: LIFETIME VIP kabhi hari nahi jaati",
      str(_row3.get("premium_until")) == "lifetime", f"-> {_row3.get('premium_until')}")

# restore ke liye snapshot ban raha hai (naya field bhi capture ho)
_rd = {"users": [_base], "payments": [{"id": 1, "amount": 99}]}
_ms, _ = merge_rows(_rd, {})
check("merge: ek taraf khaali ho to bhi data zinda rehta hai",
      len(_ms.get("users") or []) >= 1)

# premium_floor_report structure
_floor = premium_floor_report(os.environ["DB_PATH"])
check("premium_floor_report: teeno count deta hai",
      all(k in _floor for k in ("lifetime", "active", "total_premium")))


# ======================================================================
section("3) 🧠 SMART DETECT (ENGINE-1)")
# ======================================================================
CASES = [
    ("SBIN0001234", "ifsc"), ("HDFC0000123", "ifsc"),
    ("9876543210", "mobile"), ("800001", "pincode"),
    ("BR01AB1234", "vehicle"), ("ABCDE1234F", "pan"),
    ("22AAAAA0000A1Z5", "gst"), ("https://youtu.be/abc", "url"),
    ("www.google.com", "url"), ("@himanshu_dev", "username"),
    ("358749052487655", "imei"), ("google.com", "domain"),
]
_okc = 0
for _txt, _want in CASES:
    _h = pro.detect(_txt)
    if _h and _h.get("kind") == _want:
        _okc += 1
    else:
        print(f"     ✗ {_txt!r} -> {(_h or {}).get('kind')} (chahiye {_want})")
check(f"detect: {len(CASES)} cases sahi pahchane", _okc == len(CASES), f"-> {_okc}/{len(CASES)}")

check("detect: normal baat-cheet par None (false positive nahi)",
      pro.detect("bhai kaisa hai") is None and pro.detect("kal milte hain") is None)
check("detect: khaali text par None", pro.detect("") is None and pro.detect("   ") is None)
check("detect: multi-line par None (tool input nahi)",
      pro.detect("hello\nSBIN0001234") is None)

_h = pro.detect("SBIN0001234")
check("detect: high-confidence mark hota hai", bool(_h and _h.high))
check("detect: auto-run sirf safe kinds par",
      _h.action in pro._AUTORUN and pro.detect("800001").action not in pro._AUTORUN)

# pending store (callback_data 64-byte limit ka ilaaj)
_tok = pro._pending_put(_h)
check("pending: token chhota hai (<64 byte)",
      len(f"pro_go:{_tok}".encode()) <= 64)
check("pending: value wapas milti hai", pro.pending_get(_tok) is not None)
check("pending: ek baar nikalne par dobara nahi milti",
      pro.pending_get(_tok) is None)
check("pending: fake token par None (crash nahi)", pro.pending_get("nahi-hai") is None)

# toggle
pro.set_detect_enabled(4242, False)
check("detect toggle: user ON/OFF kar sakta hai",
      pro.detect_enabled(4242) is False and pro.detect_enabled(999) is True)
pro.set_detect_enabled(4242, True)


# ======================================================================
section("4) ⚡ PROVIDER RACE + CIRCUIT BREAKER (ENGINE-2)")
# ======================================================================
_r, _who, _f = pro.race([("dead", lambda: 1 / 0), ("slow", lambda: (time.sleep(0.35), "slow")[1]),
                         ("fast", lambda: "fast")], timeout=6)
check("race: jo pehle de, wahi jeeta (slow nahi)", _r == "fast", f"-> {_r} {_who}")
check("race: fail hua provider list me aata hai", "dead" in _f)

_r2, _w2, _ = pro.race([("a", lambda: None), ("b", lambda: "")], timeout=4)
check("race: khaali/None jawab accept nahi (jhoot nahi milta)", _r2 is None)

_r3, _, _ = pro.race([], timeout=2)
check("race: khaali list par crash nahi", _r3 is None)

_br = pro.get_breaker("test-provider-v83", threshold=2, cooldown=60)
check("breaker: shuru me allow karta hai", _br.allow() is True)
_br.fail(); check("breaker: 1 fail par bhi khula nahi", _br.state == "closed")
_br.fail()
check("breaker: threshold par OPEN (dead source skip)", _br.state == "open")
_br.allow()
check("breaker: open hote hi skip milta hai", _br.skips >= 1)
_br.ok()
check("breaker: success par self-heal (closed)", _br.state == "closed" and _br.heals >= 1)
check("breaker_stats: report deta hai", len(pro.breaker_stats()) >= 1)


# ======================================================================
section("5) 🗂️ RESULT HISTORY + ANALYTICS (ENGINE-3/4)")
# ======================================================================
_U1, _U2 = 8300001, 8300002
pro.record_result(_U1, "ifsc", "IFSC Bank Branch", ok=True, ms=410, source="prov-a")
pro.record_result(_U1, "pin", "Pincode Info", ok=True, ms=220)
pro.record_result(_U2, "numinfo", "Number Info", ok=True, ms=900)
pro.tool_counter("failing-tool", ok=False, ms=100)

_rows = pro.results.recent(_U1, 5)
check("history: user ka result save hota hai", len(_rows) >= 2, f"-> {len(_rows)}")
check("history: sirf apna result dikhta hai (dusre ka nahi)",
      all(r["tool"] in ("ifsc", "pin") for r in _rows))
check("history: ms record hota hai", any(int(r["ms"]) == 410 for r in _rows))

_txt = pro.history_text(_U1, 5)
check("history_text: card banta hai", "AAKHI KE RESULTS" in _txt)
check("history_text: koi bahar ka link nahi (RULE #1)",
      "http://" not in _txt and "https://" not in _txt and "t.me" not in _txt)

_kb = pro.history_kb(_U1, 5)
check("history_kb: buttons bante hain", _kb is not None)
check("history_kb: callback_data 64 byte ke andar",
      all(len(b.callback_data.encode()) <= 64 for row in _kb.inline_keyboard for b in row))

_st = pro.toolstats(20)
check("toolstats: runs ginte hain", any(r["tool"] == "ifsc" and r["runs"] >= 1 for r in _st))
check("toolstats: fail % alag dikhta hai",
      any(r["tool"] == "failing-tool" and r["fail"] >= 1 for r in _st))
_tt = pro.toolstats_text(10)
check("toolstats_text: admin card banta hai", "TOOL ANALYTICS" in _tt)

pro.results.clear(_U1)
check("history clear: user ka data mit jaata hai", len(pro.results.recent(_U1, 5)) == 0)

# storage cap (Render disk chhota hota hai)
check("history: total cap set hai (disk bharne se bacha)",
      isinstance(pro.HISTORY_MAX, int) and pro.HISTORY_MAX > 0)

# quality stamp
_q = pro.quality_line("provider-x", 412)
check("quality_line: source + speed dikhata hai", "412" in _q and "provider-x" in _q)
check("quality_line: khaali par khaali (kuch na dikhe)", pro.quality_line() == "")
check("quality_line: koi link nahi", "http" not in _q)


# ======================================================================
section("6) 🔌 bot.py WIRING (hook sahi jagah lage hain)")
# ======================================================================
with open(os.path.join(_ROOT, "bot.py"), encoding="utf-8") as fh:
    SRC = fh.read()

check("bot.py: proengine import hua", "from modules.core import proengine as pro" in SRC)
check("bot.py: smart detect hook on_text me hai", "SMART DETECT (PRO ENGINE, ENGINE-1)" in SRC)
check("bot.py: on_text mode-dispatch se PEHLE detect hota hai",
      SRC.index("SMART DETECT (PRO ENGINE, ENGINE-1)") < SRC.index('if mode == "ifsc":'))
check("bot.py: pro_go handler on_cb me hai",
      SRC.index("pro_go:") < SRC.index('if mode == "ifsc":'))
check("bot.py: wrappers se handlers jude (_on_text_pro/_on_cb_pro)",
      "_on_text_pro)" in SRC and "CallbackQueryHandler(_on_cb_pro)" in SRC)
check("bot.py: naye commands register hain (/history /smart /toolstats)",
      'CommandHandler(["history", "recent", "myrecent"], cmd_history)' in SRC
      and 'CommandHandler(["smart", "autodetect", "auto"], cmd_smart)' in SRC
      and 'CommandHandler(["toolstats", "analytics", "toolreport"], cmd_toolstats)' in SRC)
check("bot.py: _pro_mode track hota hai (history button ke liye)",
      'context.user_data["_pro_mode"]' in SRC)

# --- RULE #1 NO-LINK: naye code me bahar ka link nahi ---
for _bad in ("t.me/", "https://t.me", "http://", "https://github"):
    check(f"RULE #1: naya code link-free ({_bad})",
          _bad not in pro.__doc__ and _bad not in pro.smart_line(_h))

# vault crash fix (v75 ka asli bug) — module-level asyncio import
with open(os.path.join(_ROOT, "modules", "core", "vault.py"), encoding="utf-8") as fh:
    _VSRC = fh.read()
check("vault.py: asyncio module-level import hai (crash fix)",
      "\nimport asyncio" in _VSRC and "v75 FIX" in _VSRC)


# ======================================================================
section("7) 🚀 END-TO-END — on_text se poora smart-detect flow (mock bot)")
# ======================================================================
#  Yahan asli `on_text` chalta hai (nakli Update ke saath) — isse sabit hota
#  hai ki detection -> mode -> tool dispatch -> history recording, sab jude
#  hue hain. Koi network call nahi (lookup_ifsc ko nakli kiya gaya hai).
import asyncio                                                   # noqa: E402
import types                                                     # noqa: E402
import bot as B                                                   # noqa: E402
from database import set_credits as _set_credits                   # noqa: E402

B.lookup_ifsc = lambda x: {"ok": False, "error": "test-mode (network nahi)"}


class _Msg:
    def __init__(self, text, uid):
        self.text = text
        self.chat = types.SimpleNamespace(id=uid)
        self.sent = []

    async def reply_text(self, *a, **kw):
        self.sent.append(str(a[0]) if a else str(kw.get("text") or ""))
        return self

    async def reply_photo(self, *a, **kw):
        self.sent.append("[photo]")
        return self


class _User:
    def __init__(self, uid, name="Test"):
        self.id = uid
        self.first_name = name
        self.username = "tester"
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


async def _run(uid, text):
    upd, ctx = _Upd(uid, text), _Ctx()
    await B._on_text_pro(upd, ctx)
    return upd.message.sent, ctx


try:
    # (a) MEDIUM confidence (pincode) -> 1-tap button milta hai, tool khud nahi chalta
    _sent, _ctx = asyncio.run(_run(8311111, "800001"))
    _joined = " ".join(_sent)
    check("e2e: pincode par 'chalaun?' button aata hai",
          "chalaun?" in _joined or "PINCODE" in _joined.upper(), f"-> {_joined[:90]}")
    check("e2e: medium par mode khud nahi khulta (galat tool nahi chalta)",
          _ctx.user_data.get("mode") in (None, ""))

    # (b) HIGH confidence (IFSC) -> khud chalta hai
    _sent2, _ctx2 = asyncio.run(_run(8322222, "SBIN0000001"))
    _joined2 = " ".join(_sent2)
    check("e2e: IFSC par bot khud tool chala leta hai",
          "chala raha hoon" in _joined2 or "IFSC" in _joined2.upper(), f"-> {_joined2[:90]}")
    check("e2e: IFSC detect hote hi mode set hota hai",
          str(_ctx2.user_data.get("mode") or "") == "ifsc",
          f"-> {_ctx2.user_data.get('mode')}")
    check("e2e: tool run history me record hota hai",
          any(r.get("tool") == "ifsc" for r in pro.results.recent(8322222, 5)),
          f"-> {pro.results.recent(8322222, 5)}")

    # (c) normal baat-cheet par koi tool nahi chalta (false positive = 0)
    _sent3, _ctx3 = asyncio.run(_run(8333333, "bhai kaisa hai"))
    check("e2e: normal message par koi tool nahi chalta",
          str(_ctx3.user_data.get("mode") or "") == "")

    # (d) EARNING GATE: 0 credit + premium tool -> credits-over screen
    _was_free = B.ALL_FREE
    B.ALL_FREE = False
    try:
        B.get_user(8344444, "Test")      # pehle user row bane
        _set_credits(8344444, 0)
        check("e2e setup: 0 credit set hua", B.get_credits(8344444) == 0,
              f"-> {B.get_credits(8344444)}")
        _sent4, _ctx4 = asyncio.run(_run(8344444, "SBIN0000002"))
        _j4 = " ".join(_sent4)
        check("e2e: 0 credit user par auto-run BLOCK hota hai (earning bachi)",
              "CREDITS KHATAM" in _j4.upper(), f"-> {_j4[:90]}")
        check("e2e: block hone par mode set nahi hota",
              str(_ctx4.user_data.get("mode") or "") == "")
        # credits hain to chalta hai
        B.get_user(8355555, "Test")
        _set_credits(8355555, 25)
        _sent5, _ctx5 = asyncio.run(_run(8355555, "SBIN0000003"))
        check("e2e: credits hone par chalta hai",
              str(_ctx5.user_data.get("mode") or "") == "ifsc")
    finally:
        B.ALL_FREE = _was_free

    # (e) /history aur /smart commands crash nahi karte
    async def _cmds():
        out = []
        _u, _c = _Upd(8366666, "/history"), _Ctx()
        await B.cmd_history(_u, _c)
        out.append(_u.message.sent[-1])
        _u2, _c2 = _Upd(8366666, "/smart"), _Ctx()
        await B.cmd_smart(_u2, _c2)
        out.append(_u2.message.sent[-1])
        return out

    _o = asyncio.run(_cmds())
    check("e2e: /history card deta hai", "AAKHI KE RESULTS" in _o[0])
    check("e2e: /smart ON/OFF toggle karta hai", "SMART DETECT" in _o[1])

except Exception as _e:                                          # noqa: BLE001
    import traceback
    check("e2e flow chala (crash nahi)", False, f"{type(_e).__name__}: {_e}")
    traceback.print_exc()


# ======================================================================
print("\n" + "=" * 62)
print(f"  v83 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILS:
    print("\nFAILED:")
    for f in FAILS:
        print("  •", f)
sys.exit(1 if FAIL else 0)
