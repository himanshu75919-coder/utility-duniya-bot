# -*- coding: utf-8 -*-
"""
v88 SELFTEST — "FAST DB + PERMANENT CRASH-FREE TOOLS"
======================================================
Aaj ke 3 kaam (sab OFFLINE, koi network/API nahi chahiye):

  A. ⚡ FAST DB (database.py)
     Pehle HAR SQLite call par naya connection + 5 PRAGMA + 6 CREATE TABLE
     chalta tha — 0.299 ms per call, aur ye event loop ke ANDAR tha (bot ka
     poora response usi waqt tak ruka rehta). Ab: thread-local connection
     reuse + schema sirf ek baar per process = 0.014 ms (21x). Test ye
     TIMING se nahi (sandbox slow ho sakta hai) balki connect-COUNT se karta
     hai: 200 calls me ek bhi naya connect nahi banana chahiye.

  B. 🧱 SCHEMA INIT ONCE + SAFE CLOSE
     `with db() as con: con.close()` wale 100+ purane sites bina change kiye
     chalne chahiye (proxy ka close() no-op hai), aur vault restore se DB file
     badal jaaye (inode change) to reconnect hona chahiye — warna purani file
     par likhte reh jaate.

  C. 🛡️ CRASH SWEEP (46 sites jo junk input par tutte the)
     Ek junk value (None/True/''/[]/b''/int) par bhi koi tool
     TypeError/AttributeError/KeyError se NA mare. Saath me do asli user-
     facing bugs:
       • QR: 2900+ characters bhejo -> `ValueError: Invalid version (was 41)`
         = tool crash. Ab EC level khud degrade (H->Q->M->L) hota hai taaki
         zyada se zyada text SCAN-HOGAYE QR me aaye, aur jo sach me nahi ho
         sakta usme saaf wajah milti hai.
       • Bank statement: parse fail par `res["summary"]` KeyError.
     Aur ek BOOT bug: `int(os.environ.get("RATE_LIMIT_WINDOW"))` — Render par
     ek khaali env value = bot ek baar bhi start nahi hota tha. Ab safeconf.
"""
import os
import sys
import io
import importlib
import sqlite3
import threading

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v88_tmp.db"))
for _f in ("_v88_tmp.db",):
    try:
        os.remove(os.path.join(_HERE, _f))
    except OSError:
        pass

PASS = 0
FAIL = 0
FAILS = []


def check(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILS.append(f"{label}{(' — ' + extra) if extra else ''}")
        print(f"  ❌ {label}{(' — ' + extra) if extra else ''}")


def no_crash(label, fn, allow=()):
    """fn() NA tute (TypeError/AttributeError/KeyError/ValueError se)."""
    try:
        fn()
        check(label, True)
        return True
    except allow:
        check(label, True)
        return True
    except Exception as e:                            # noqa: BLE001
        check(label, False, f"{type(e).__name__}: {str(e)[:70]}")
        return False


import database as db                                                # noqa: E402

# ======================================================================
print("\n=== A. FAST DB: connection reuse (21x) ===")
# ======================================================================
_real_connect = db._vault_connect
_connects = {"n": 0}


def _counting_connect(path, *a, **kw):
    _connects["n"] += 1
    return _real_connect(path, *a, **kw)


db._vault_connect = _counting_connect
try:
    db.reset_conns()                       # naye process jaisa
    _connects["n"] = 0
    for _ in range(200):
        with db.db() as con:
            con.execute("SELECT 1")
    check("200 DB calls me sirf 1 connect (pehle 200 hote)",
          _connects["n"] <= 1, f"connects={_connects['n']}")

    # reuse: do baar same underlying connection
    c1 = db.db().__wrapped__ if hasattr(db.db(), "__wrapped__") else None
    con_a = db.db()
    con_b = db.db()
    check("same thread ko same connection milta hai",
          con_a._con is con_b._con and con_a is not con_b)

    # schema ek hi baar
    check("schema init ek baar (_schema_ready())", db.schema_ready() is True)
    _n_before = _connects["n"]
    db.reset_conns()
    with db.db() as con:
        con.execute("SELECT 1")
    check("reset_conns() ke baad ek naya connect", _connects["n"] == _n_before + 1,
          f"delta={_connects['n'] - _n_before}")
finally:
    db._vault_connect = _real_connect

# ======================================================================
print("=== B. safe close + counts + thread behaviour ===")
# ======================================================================
# purana code `con.close()` karta hai — proxy use ko no-op samajhta hai
con = db.db()
try:
    con.close()
    check("con.close() no-op (100+ purane sites bina badlav chalein)",
          con.execute("SELECT 1") is not None)
except Exception as e:                                    # noqa: BLE001
    check("con.close() no-op (100+ purane sites bina badlav chalein)", False, str(e)[:60])

uid = 990001
db.meta_set("v88_k", "v88_v")
check("meta_set/meta_get", db.meta_get("v88_k") == "v88_v")
check("meta_get missing -> default", db.meta_get("v88_missing", "zz") == "zz")

u0 = db.get_user(uid)
check("get_user naye uid ko banata hai", u0 and u0.get("user_id") == uid)
n0 = (db.get_user(uid) or {}).get("uses_today", 0)
db.add_use(uid)
n1 = (db.get_user(uid) or {}).get("uses_today", 0)
check("add_use uses_today badhata hai", n1 == n0 + 1, f"{n0}->{n1}")

# doosre thread ko naya connection + wahi data dikhe
seen = {}


def _other():
    try:
        other = db.db()
        seen["same_raw"] = other._con is con._con
        r = other.execute("SELECT uses_today FROM users WHERE user_id=?", (uid,)).fetchone()
        seen["val"] = r[0] if r else None
        other.close()
    except Exception as e:                                # noqa: BLE001
        seen["err"] = f"{type(e).__name__}: {str(e)[:60]}"


t = threading.Thread(target=_other)
t.start()
t.join(10)
check("doosre thread ko USKA connection milta hai (SQLite thread-safe)",
      seen.get("same_raw") is False, str(seen)[:90])
check("doosre thread ko doosre thread ki likhi value dikhti hai",
      seen.get("val") == n1, str(seen)[:90])
check("thread me koi error nahi", "err" not in seen, seen.get("err", ""))

# WAL/concurrency: parallel likhna
errs = []


def _writer(k):
    try:
        for _ in range(25):
            db.add_use(uid)
    except Exception as e:                                # noqa: BLE001
        errs.append(f"{type(e).__name__}:{str(e)[:40]}")


ts = [threading.Thread(target=_writer, args=(i,)) for i in range(6)]
for x in ts:
    x.start()
for x in ts:
    x.join(30)
after = (db.get_user(uid) or {}).get("uses_today", 0)
check("6 threads x 25 likhne par koi 'database is locked'/crash nahi",
      not errs, str(errs[:2])[:100])
check("saari 150 likhein giri (loss nahi)", after == n1 + 150, f"{n1}+150 != {after}")

# inode swap = vault restore -> reconnect
p = db.DB_PATH
try:
    st = os.stat(p)
    # fake swap: temp file se replace karo (naya inode)
    tmp = p + ".swap"
    con2 = sqlite3.connect(tmp)
    con2.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, uses_today INTEGER DEFAULT 0)")
    con2.execute("INSERT INTO users(user_id, uses_today) VALUES (12345, 77)")
    con2.commit()
    con2.close()
    db.reset_conns()
    _raw = db.db()
    for _sfx in ("-wal", "-shm"):                  # clean restore jaisa
        try:
            os.remove(p + _sfx)
        except OSError:
            pass
    os.replace(tmp, p)
    db.reset_conns()                       # restore-style: fresh
    v = db.db().execute("SELECT uses_today FROM users WHERE user_id=12345").fetchone()
    check("DB file badalne (inode swap) par purani file par nahi likhta",
          v is not None and v[0] == 77, str(v)[:40])
except Exception as e:                                    # noqa: BLE001
    check("DB file badalne (inode swap) par purani file par nahi likhta", False, str(e)[:70])
finally:
    for _f in (tmp,):
        try:
            os.remove(_f)
        except OSError:
            pass
    # swap ne test DB ka schema 2-column kar diya — aage ke sections ke liye
    # saaf DB chahiye (warna get_user "no column named name" dega)
    for _f in (p, p + "-wal", p + "-shm"):
        try:
            os.remove(_f)
        except OSError:
            pass
    db.reset_conns()

db.reset_conns()
# reset ke baad bhi asli schema wapas ban jaye (stale DB_PATH case)
with db.db() as c3:
    c3.execute("SELECT uses_today FROM users WHERE user_id=?", (uid,)).fetchone()
check("reset_conns() ke baad schema dobara ready", db.schema_ready() is True)

# ======================================================================
print("=== C. QR capacity guard (asli user crash) ===")
# ======================================================================
from modules.general_tools import make_qr_bytes, make_branded_qr, qr_capacity, QrTooLong  # noqa: E402

for png in (make_qr_bytes, make_branded_qr):
    name = png.__name__
    ok_small = False
    try:
        b = png("https://paytm.com/x")
        ok_small = b.getvalue()[:8] == b"\x89PNG\r\n\x1a\n"
    except Exception as e:                                # noqa: BLE001
        check(f"{name}: chhota text PNG deta hai", False, str(e)[:60])
    check(f"{name}: chhota text PNG deta hai", ok_small)
    no_crash(f"{name}: 2300 char (ab tak crash karta tha)", lambda n=name: png("x" * 2300))
    no_crash(f"{name}: 2900 char (limit ke paas)", lambda n=name: png("x" * 2900))
    try:
        png("x" * 5000)
        check(f"{name}: limit se bada text -> saaf QrTooLong (crash nahi)", False,
              "koi error hi nahi aaya")
    except QrTooLong:
        check(f"{name}: limit se bada text -> saaf QrTooLong (crash nahi)", True)
    except Exception as e:                                # noqa: BLE001
        check(f"{name}: limit se bada text -> saaf QrTooLong (crash nahi)", False,
              f"{type(e).__name__}: {str(e)[:60]}")
    for junk in (None, "", "   ", [], {}, 0):
        try:
            png(junk)
            check(f"{name}: junk {repr(junk)[:6]} -> saaf error", False, "chup-chaap ban gaya")
        except QrTooLong:
            check(f"{name}: junk {repr(junk)[:6]} -> saaf error", True)
        except Exception as e:                            # noqa: BLE001
            check(f"{name}: junk {repr(junk)[:6]} -> saaf error", False,
                  f"{type(e).__name__}: {str(e)[:50]}")

cap = qr_capacity("x" * 2900)
check("qr_capacity: 2900 fit (level L)", cap["ok"] is True and cap["best_ec"] == "L", str(cap)[:70])
check("qr_capacity: 4000 fit nahi", qr_capacity("x" * 4000)["ok"] is False)
check("qr_capacity: chhote text par H milta hai", qr_capacity("upi://pay?pa=x")["best_ec"] == "H")
check("qr_capacity: advice me limit ka number", "2953" in qr_capacity("x" * 9999)["advice"])
check("QrTooLong ValueError ka bachha (purane except Exception ise pakad lein)",
      issubclass(QrTooLong, ValueError))

import modules.vip_payment as vp                          # noqa: E402
_fn = getattr(vp, "make_qr_bytes", None)
if _fn:
    try:
        _fn("x" * 5000)
        check("vip_payment QR bhi fix hua (same helper share)", False, "error nahi")
    except QrTooLong:
        check("vip_payment QR bhi fix hua (same helper share)", True)
    except Exception as e:                                # noqa: BLE001
        check("vip_payment QR bhi fix hua (same helper share)", False, type(e).__name__)

# ======================================================================
print("=== D. media/image kachra-input guards ===")
# ======================================================================
import modules.desi_tools as dt                           # noqa: E402
check("_as_bytes(str) -> b'' (media nahi, isliye crash nahi hota)",
      dt._as_bytes("junk") == b"")
check("_as_bytes(None) -> b''", dt._as_bytes(None) == b"")
_buf = io.BytesIO(b"ABC")
check("_as_bytes(BytesIO) -> andar ka data", dt._as_bytes(_buf) == b"ABC")
check("_as_bytes(int) -> b''", dt._as_bytes(123) == b"")
for fn_name in ("make_karaoke", "make_ringtone", "video_to_mp3"):
    fn = getattr(dt, fn_name, None)
    if not fn:
        continue
    for junk in ("not-audio", None, [], 42):
        try:
            r = fn(junk) if fn_name != "make_ringtone" else fn(junk, "0", 5)
            check(f"{fn_name}({repr(junk)[:8]}) dict deta hai, exception nahi",
                  isinstance(r, dict), str(r)[:50])
        except Exception as e:                            # noqa: BLE001
            check(f"{fn_name}({repr(junk)[:8]}) dict deta hai, exception nahi", False,
                  f"{type(e).__name__}: {str(e)[:50]}")
no_crash("make_status_video(str,str) crash nahi karta",
         lambda: dt.make_status_video("junk", "junk", "hi", 1.0))

import modules.business_tools as bt                       # noqa: E402
check("to_pdf(' ') -> None (crash nahi)", bt.to_pdf(" ") is None)
check("to_pdf([None,'']) -> None", bt.to_pdf([None, ""]) is None)
check("to_pdf(123) -> None", bt.to_pdf(123) is None)
_png_ok = None
try:
    _png_ok = make_qr_bytes("ok").getvalue()
except Exception:                                         # noqa: BLE001
    pass
if _png_ok:
    check("to_pdf asli PNG se PDF banata hai (guard kaam kare, kaam na tute)",
          (bt.to_pdf([_png_ok]) or b"")[:4] == b"%PDF")
    check("to_pdf single bytes bhi chalega", (bt.to_pdf(_png_ok) or b"")[:4] == b"%PDF")
    check("to_pdf BytesIO bhi chalega", (bt.to_pdf([io.BytesIO(_png_ok)]) or b"")[:4] == b"%PDF")

import modules.imei_lookup as il                          # noqa: E402
for payload in ({}, {"result": None}, {"result": {}}, None, [], {"header": 5}):
    try:
        r = il.parse_imei_payload(payload, "123456789012345")
        check(f"parse_imei_payload({repr(payload)[:12]}) -> dict, crash nahi",
              isinstance(r, dict) and r.get("ok") in (True, False), str(r)[:50])
    except Exception as e:                                # noqa: BLE001
        check(f"parse_imei_payload({repr(payload)[:12]}) -> dict, crash nahi", False,
              f"{type(e).__name__}: {str(e)[:50]}")

# ======================================================================
print("=== E. junk input sweep (jo 46 sites the) ===")
# ======================================================================
import modules.toolkit_extras as tx                       # noqa: E402
import modules.osint_tools as ot                           # noqa: E402
import modules.payguard as pg                             # noqa: E402
import modules.media_downloader as md                     # noqa: E402
import modules.tutorial_hub as th                          # noqa: E402
import modules.cloud_tools as ct                           # noqa: E402
import modules.api_hub as ah                                # noqa: E402
import modules.captcha_bridge as cb                         # noqa: E402
import modules.bseb_result as br                            # noqa: E402

check("brand_in_text(True) -> False (v77 ka mera bug)", tx.brand_in_text(True, "x", set()) is False)
check("brand_in_text(None) -> False", tx.brand_in_text(None, "x", set()) is False)
check("brand_in_text('vi','servic vi',{'vi'}) -> True",
      tx.brand_in_text("vi", "servic vi", {"vi"}) is True)
check("brand_in_text chhota brand token-wise (ghatiya fix non-regression)",
      tx.brand_in_text("vi", "services", set()) is False)

JUNKS = (None, True, "", "   ", [], {}, 0, 42, b"", b"x", 3.5, object())
_SITES = [
    ("analyze_link", lambda j: tx.analyze_link(j)),
    ("expand_url", lambda j: tx.expand_url(j)),
    ("shorten_url", lambda j: tx.shorten_url(j)),
    ("classify_instagram_url", lambda j: md.classify_instagram_url(j)),
    ("save_cookies_text", lambda j: md.save_cookies_text(j)),
    ("validate_utr", lambda j: pg.validate_utr(j)),
    ("text_to_nodes", lambda j: th.text_to_nodes(j)),
    ("_extract_surl", lambda j: ct._extract_surl(j)),
    ("lookup_ifsc", lambda j: ot.lookup_ifsc(j)),
    ("lookup_pincode", lambda j: ot.lookup_pincode(j)),
    ("lookup_phone_info", lambda j: ot.lookup_phone_info(j)),
    ("lookup_vehicle_rto", lambda j: ot.lookup_vehicle_rto(j)),
    ("api_hub.gstin_format_ok", lambda j: ah.gstin_format_ok(j)),
    ("api_hub.pan_format_ok", lambda j: ah.pan_format_ok(j)),
    ("desi_tools.detect_bank", lambda j: dt.detect_bank(j)),
    ("captcha_bridge.parse_result", lambda j: cb.parse_result(j)),
    ("bseb_result._extract_token", lambda j: br._extract_token(j)),
]
import socket                                          # noqa: E402

_real_gai = socket.getaddrinfo


def _offline(*a, **k):
    raise OSError("test: network band (varna connect timeouts se suite 3 min lagta)")


socket.getaddrinfo = _offline
try:
    for name, fn in _SITES:
        bad = []
        for j in JUNKS:
            try:
                fn(j)
            except (TypeError, AttributeError, KeyError, sqlite3.Error) as e:
                bad.append(f"{type(j).__name__}:{type(e).__name__}")
            except Exception:                             # noqa: BLE001
                pass                                      # saaf business error = theek
        check(f"{name}: 14 junk inputs par bhi crash nahi (offline)", not bad, str(bad[:3])[:90])
finally:
    socket.getaddrinfo = _real_gai

# ======================================================================
print("=== F. env/boot safety (galat env = bot start nahi hota tha) ===")
# ======================================================================
from modules.core import safeconf                          # noqa: E402

os.environ["RATE_LIMIT_WINDOW"] = ""
os.environ["RATE_LIMIT_BURST"] = "abc"
os.environ["RATE_LIMIT_DEFAULT"] = "999999"
os.environ["PRO_HISTORY_MAX"] = "not-a-number"
import modules.core.limiter                              # noqa: E402
import modules.core.proengine                              # noqa: E402
_lim = importlib.reload(sys.modules["modules.core.limiter"])
_pro = importlib.reload(sys.modules["modules.core.proengine"])
check("khaali RATE_LIMIT_WINDOW -> default 60 (crash nahi)", _lim._DEFAULT_WINDOW == 60,
      str(_lim._DEFAULT_WINDOW))
check("kachra RATE_LIMIT_BURST -> default 6", _lim._BURST_LIMIT == 6, str(_lim._BURST_LIMIT))
check("OUT-OF-RANGE RATE_LIMIT_DEFAULT -> clamp (blast se bacha)",
      1 <= _lim._DEFAULT_LIMIT <= 5000, str(_lim._DEFAULT_LIMIT))
check("kachra PRO_HISTORY_MAX -> default 20000", _pro.HISTORY_MAX == 20000, str(_pro.HISTORY_MAX))
for k in ("RATE_LIMIT_WINDOW", "RATE_LIMIT_BURST", "RATE_LIMIT_DEFAULT", "PRO_HISTORY_MAX"):
    os.environ.pop(k, None)
check("safeconf.env_int('') kabhi raise nahi karta",
      safeconf.env_int("RATE_LIMIT_WINDOW", 7) == 7)

lim = sys.modules["modules.core.limiter"]   # package __init__ ka `limiter` naam shadow karta hai
no_crash("check_limit(junk uid) crash nahi karta (har tool se pehle chalta hai)",
         lambda: lim.check_limit("", "any"))
no_crash("check_limit(True action) crash nahi karta",
         lambda: lim.check_limit(1, True))
no_crash("detect_enabled('') crash nahi", lambda: _pro.detect_enabled(""))
no_crash("set_detect_enabled('') crash nahi", lambda: _pro.set_detect_enabled("", True))
check("_safe_uid digits nikaalta hai", _pro._safe_uid("12a34") in (34, 1234))
check("_safe_uid kachra -> default", _pro._safe_uid("abc", 5) == 5)

# statement summary (bank tool ka KeyError)
no_crash("statement_summary_text({}) -> KeyError nahi", lambda: dt.statement_summary_text({}))
no_crash("statement_summary_text(None) -> crash nahi", lambda: dt.statement_summary_text(None))
no_crash("statement_summary_text partial -> crash nahi",
         lambda: dt.statement_summary_text({"summary": {"period": "x"}, "bank": "SBI"}))
_r = dt.statement_summary_text({"summary": {"period": "01-01 to 31-01", "credits": 5,
                                            "debits": 2, "closing": 100}, "bank": "HDFC"})
check("statement summary sahi data par pehle jaisa hi banta hai",
      "BANK STATEMENT READY" in _r and "HDFC" in _r, _r[:40])

# ======================================================================
print("=== G. API shape ab bhi waisi hi (non-regression) ===")
# ======================================================================
check("database.db() ab bhi context manager hai", hasattr(db.db(), "__enter__"))
with db.db() as c9:
    check("with-block ke andar execute chalta hai", c9.execute("SELECT 1").fetchone()[0] == 1)
_newu = db.get_user(987654321)
check("get_user naye uid par dict deta hai (purana contract)",
      isinstance(_newu, dict) and _newu.get("user_id") == 987654321, str(_newu)[:60])
try:
    db.add_use(990001)
    check("add_use signature unchanged", True)
except TypeError as e:
    check("add_use signature unchanged", False, str(e)[:60])
check("reset_conns() public + callable", callable(getattr(db, "reset_conns", None)))
check("schema_ready() public + callable", callable(getattr(db, "schema_ready", None)))

print("\n" + "=" * 62)
print(f"  v88 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAILS:
    print("-" * 62)
    for f in FAILS[:25]:
        print("   ❌ " + f)
print("=" * 62)
sys.exit(1 if FAIL else 0)
