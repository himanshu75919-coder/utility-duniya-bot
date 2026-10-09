# -*- coding: utf-8 -*-
"""
v75 SELFTEST — 🌐 SHARED HTTP ENGINE (v72.0 "saare tools ka upgrade")
======================================================================
User ka order: "mere saare tools ko upgrade karo" — Phase 1:

  PEHLE:  har module apna requests.get() → naya TLS handshake har call,
          ek hiccup = seedha fail, kuch calls bina timeout ke (hang risk)
  AB:     ek shared keep-alive session + auto-retry (2x) + default timeout
          + live stats (/health par) — SAB tools par lagoo

Test 100% OFFLINE (koi network call nahi — fake session se).
"""
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv75_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V75"
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
print("  v75 SELFTEST — 🌐 SHARED HTTP ENGINE (saare tools ka speed upgrade)")
print("=" * 62)

import bot                                                        # noqa: E402
from modules.core import httpio as H                              # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

# =====================================================================
section("1) Engine — shared session + auto-retry + default timeout")
_s1, _s2 = H.session(), H.session()
check("ek hi shared session (naya handshake nahi har call)", _s1 is _s2)
_ad = (_s1.adapters or {}).get("https://")
check("HTTPS adapter (retry engine) laga hua hai", _ad is not None)
_rt = getattr(_ad, "max_retries", None)
check("retry total = 2 set hai", getattr(_rt, "total", None) == H.RETRY_TOTAL,
      str(getattr(_rt, "total", None)))
check("5xx/429 par retry hota hai",
      500 in tuple(getattr(_rt, "status_forcelist", ()) or ())
      and 429 in tuple(getattr(_rt, "status_forcelist", ()) or ()))
check("connect/read errors par bhi retry", getattr(_rt, "connect", None) == 2
      and getattr(_rt, "read", None) == 2)
check("default timeout hai (hang khatam)", H.DEFAULT_TIMEOUT == 12)
check("common UA set hai (bot-block kam)", "Chrome" in str(_s1.headers.get("User-Agent")))


# =====================================================================
section("2) get / post / get_json — requests jaisa hi behaviour (fake session)")
class _Raw:
    def __init__(self, total=0):
        self.retries = type("R", (), {"total": total})()


class _Resp:
    def __init__(self, code=200, payload=None, rt=0, boom=False):
        self.status_code = code
        self._payload = payload or {}
        self.raw = _Raw(rt)
        self._boom = boom

    def json(self):
        if self._boom:
            raise ValueError("bad json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeSess:
    def __init__(self):
        self.calls = []

    def get(self, url, **kw):
        self.calls.append(("GET", url, kw))
        return _Resp(200, {"ok": 1, "url": url}, rt=kw.pop("_rt", 0))

    def post(self, url, **kw):
        self.calls.append(("POST", url, kw))
        return _Resp(200, {"posted": True})


_fs = _FakeSess()
_orig_session = H.session
H.session = lambda: _fs
_before = H.stats()
try:
    r = H.get("https://example.com/x")
    check("get() kaam karta hai", r.status_code == 200)
    _call = _fs.calls[-1]
    check("get() me default timeout apne aap lagta hai", _call[2].get("timeout") == 12,
          str(_call[2]))
    H.get("https://example.com/y", timeout=5)
    check("custom timeout respect hota hai", _fs.calls[-1][2].get("timeout") == 5)
    H.get("https://example.com/z", headers={"X-A": "1"})
    check("headers pass-through (modules ka apna UA chalta rahe)",
          _fs.calls[-1][2].get("headers") == {"X-A": "1"})
    rp = H.post("https://example.com/p", data={"a": 1})
    check("post() kaam karta hai", rp.status_code == 200 and _fs.calls[-1][0] == "POST")
    # retry=False → alag (0-retry) session, aur ye kwarg module tak nahi jaata
    _fsnr = _FakeSess()
    _orig_nr = H.session_noretry
    H.session_noretry = lambda: _fsnr
    try:
        H.get("https://example.com/r0", retry=False)
        check("retry=False → no-retry session use hota hai (quota-safe)",
              len(_fsnr.calls) == 1 and len(_fs.calls) >= 4)
        check("retry kwarg requests ko pass NAHI hota",
              "retry" not in _fsnr.calls[-1][2])
    finally:
        H.session_noretry = _orig_nr
    j = H.get_json("https://example.com/j")
    check("get_json() JSON parse karta hai", j.get("ok") == 1)
    _after = H.stats()
    check("stats: calls count badhe", _after["calls"] - _before["calls"] >= 5,
          f"{_before['calls']} -> {_after['calls']}")
    check("stats: avg_ms nikala jata hai", _after["avg_ms"] >= 0)

    # 500 par fail count
    _b2 = H.stats()["fails"]
    H.session = lambda: type("S", (), {"get": lambda s, u, **k: _Resp(503, {}, rt=2)})()
    H.get("https://example.com/down")
    _a2 = H.stats()
    check("5xx par fails badhta hai", _a2["fails"] - _b2 == 1, str(_a2["fails"]))
    check("retry count stats me aata hai (urllib3 .total)", _a2["retries"] >= 2, str(_a2["retries"]))

    # exception waisi hi bahar jaaye (modules ka try/except chalta rahe)
    H.session = lambda: type("S", (), {"get": lambda s, u, **k: (_ for _ in ()).throw(OSError("net down"))})()
    _b3 = H.stats()["fails"]
    _raised = False
    try:
        H.get("https://example.com/boom")
    except OSError:
        _raised = True
    check("network exception PEHLE JAISA hi bahar jaata hai (compat)", _raised)
    check("exception par bhi fails count sahi", H.stats()["fails"] - _b3 == 1)
finally:
    H.session = _orig_session

# =====================================================================
section("3) Crash-proofing — stats kharab response par bhi nahi tootta")
_check = H._count
try:
    H._count(None, 0.0)                       # response None
    H._count(object(), 0.0)                   # raw hi nahi
    H._count(_Resp(200, {}, rt=1), 0.0)
    check("_count kabhi exception nahi deta", True)
except Exception as e:                        # noqa: BLE001
    check("_count kabhi exception nahi deta", False, type(e).__name__)
_st = H.stats()
check("stats() me sab keys hain",
      all(k in _st for k in ("calls", "retries", "fails", "avg_ms", "uptime_min")))

# =====================================================================
section("4) Saare modules ab shared engine par (upgrade lagoo hua)")
import glob as _glob                                              # noqa: E402

_MIGRATED = ["modules/imei_lookup.py", "modules/vehicle_tool.py", "modules/osint_hub.py",
             "modules/tutorial_hub.py", "modules/api_hub.py", "modules/media_downloader.py",
             "modules/username_hunter.py"]
for _f in _MIGRATED:
    _src = open(os.path.join(_ROOT, _f), encoding="utf-8").read()
    _bare = (_src.count("requests.get(") + _src.count("requests.post(")
             + _src.count("requests.Session()"))
    check(f"{os.path.basename(_f)}: poori tarah httpio par", _bare == 0 and "httpio" in _src,
          str(_bare))

_left = []
for _f in _glob.glob(os.path.join(_ROOT, "modules", "*.py")):
    _src = open(_f, encoding="utf-8").read()
    if "requests.get(" in _src or "requests.post(" in _src:
        _left.append(os.path.basename(_f))
check("modules/ me koi bhi bare requests.get/post nahi bacha "
      "(temp_number ka apna throttled session jaan-boojh ke allowed)",
      not _left, str(_left))

# =====================================================================
section("5) Health page + version (upgrade dikhe)")
check("bot.py me http engine import hai", "httpio as http_engine" in BOT_SRC)
check("health page par http engine line hai", "_http_engine_line()" in BOT_SRC)
check("line me calls/retries/fails/avg dikhte hain",
      "session=shared+auto-retry" in BOT_SRC and "avg=" in BOT_SRC)
import re as _re75
_m75 = _re75.search(r"v(\d+)\.(\d+)", bot.BOT_VERSION or "")
check("v72.0 ya usse naya version set hai",
      bool(_m75) and (int(_m75.group(1)), int(_m75.group(2))) >= (72, 0), bot.BOT_VERSION)
check("version me upgrade ki baat hai (WAVE/UPGRADE/tez)",
      any(x in bot.BOT_VERSION.upper() for x in ("UPGRADE", "WAVE", "TEZ")))

_line = bot._http_engine_line()
check("_http_engine_line() chalta hai (crash nahi)", "calls=" in _line, _line)

# =====================================================================
section("6) Regression — purane tools jaise the waise hi (kuch nahi toota)")
check("premium tools count 38 (37 + familyinfo naya)", len(bot.PREMIUM_TOOLS) == 38, str(len(bot.PREMIUM_TOOLS)))
check("temp mail (number) tool zinda", bot.BTN_MODE_MAP.get("TEMP MAIL (NUMBER)") == "tnum")
check("temp number apna throttled session rakhta hai (jaan-boojh ke)",
      "requests.Session()" in open(os.path.join(_ROOT, "modules", "temp_number.py"),
                                   encoding="utf-8").read())
import modules.imei_lookup as _IL                                 # noqa: E402
import modules.vehicle_tool as _VT                                # noqa: E402
import modules.osint_hub as _OH                                   # noqa: E402
check("migrated modules import hote hain (crash nahi)",
      all(m is not None for m in (_IL, _VT, _OH)))
check("username_hunter ka hunt_username zinda", callable(bot.hunt_username))

print(f"\n{'=' * 62}")
print(f"  v75 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
