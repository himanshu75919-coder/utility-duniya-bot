#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v99 SELFTEST — 📱 NUMBER API (purane API delete + tumhara API live)
=====================================================================
  A. PARSE — asli API shape (live-captured fixtures), circle split, records.
  B. MASK — Aadhaar HAMESHA masked (poora kabhi nahi, kanoon).
  C. LOOKUP — 10-digit/91-strip/junk-safe + key route (mock HTTP).
  D. REMOVAL — purana kuch nahi bacha (provider/hub/demo/numtest/numdemo).
  E. REGRESSION — wiring, version v99 + history, prompts 43.

Chalane ka tarika:  python3 tests/test_v99_mynumapi.py
"""
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v99_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("PREMIUM_ONLY", "off")
os.environ.setdefault("ALL_FREE", "1")
for _k in ("FORCE_CHANNEL", "FORCE_CHANNEL_LINK", "WEBHOOK_URL"):
    os.environ.pop(_k, None)

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name} {extra if not cond and extra else ''}")


import bot as B  # noqa: E402
from modules import mynum_api as M  # noqa: E402

BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
HUB_SRC = open(os.path.join(ROOT, "modules", "api_hub.py"), encoding="utf-8").read()

# live-captured fixtures (8 Oct 2026)
_HIT = {"success": True, "tool": "num", "query": "9999400000",
        "data": {"owner_name": "MR  DEEPAK   MEHTA", "father_name": "C P MEHTA",
                 "mobile_no": "9999400000", "alt_mobile": "7827854931",
                 "aadhar_card_no": "886553666165", "circle": "VI DELHI",
                 "address": "S/O C P MEHTA 6A LIG FLATS VIKRANT ENCLAVE 110064",
                 "owner_name_": "MR DEEPAK  MEHTA", "circle_": "VI DELHI",
                 "owner_name__": "THIRD", "circle__": "VI DELHI"}}
_MISS = {"success": True, "tool": "num", "query": "12345", "data": {},
         "raw": "✖️ No result found"}

print("\n[A] Parse — asli API shape")
_p = M.parse_payload(_HIT, 1200)
_ow = _p.get("owner") or {}
ok("HIT ok + myapi", _p.get("ok") is True and _p.get("source") == "myapi")
ok("double-space naam saaf hota hai", _ow.get("name") == "MR DEEPAK MEHTA",
   str(_ow.get("name")))
ok("father/alt/phone", _ow.get("father") == "C P MEHTA"
   and _ow.get("alt") == "7827854931" and _ow.get("phone") == "9999400000")
ok("circle split VI/DELHI", _p.get("operator") == "VI" and _p.get("circle") == "DELHI")
ok("ulta order bhi split (DELHI VODA)", M.parse_payload(
    {"success": True, "data": {"owner_name": "X", "circle": "DELHI VODA"}}, 0).get("operator") == "VODA")
ok("3 records gine", (_p.get("extra") or {}).get("records") == 3)
ok("latency_ms aata hai", _p.get("latency_ms") == 1200)
_m = M.parse_payload(_MISS, 0)
ok("MISS → not_found + Hindi", _m.get("ok") is False and _m.get("not_found") is True
   and "nahi mila" in str(_m.get("error")))
ok("ajeeb shape → crash nahi", M.parse_payload({}, 0).get("ok") is False
   and M.parse_payload(None, 0).get("ok") is False
   and M.parse_payload({"data": []}, 0).get("ok") is False)
ok("NA/None junk saaf", M.parse_payload(
    {"success": True, "data": {"owner_name": "NA", "alt_mobile": "None",
                               "aadhar_card_no": "None", "circle": "NA"}}, 0).get("owner") == {})

print("\n[B] Mask — Aadhaar lock")
ok("12-digit → XXXX-XXXX-6165", M.mask_aadhar("886553666165") == "XXXX-XXXX-6165")
ok("parse me masked", _ow.get("govt_id") == "XXXX-XXXX-6165")
ok("poora Aadhaar kahin nahi", "886553666165" not in str(_p))
ok("junk/short → khaali", M.mask_aadhar("NA") == "" and M.mask_aadhar(None) == ""
   and M.mask_aadhar("123") == "" and M.mask_aadhar("") == "")
_card = B.numinfo_card({"international": "+91 99994 00000", "country": "India"},
                       _ow, {}, "VI", "DELHI", "", "", "🟢 LIVE", 240)
ok("card me masked ID", "XXXX-XXXX-6165" in _card)
ok("card me poora Aadhaar KABHI nahi", "886553666165" not in _card)

print("\n[C] Lookup — digits + key route (mock)")
ok("91/0 strip → 10 digit", M._digits10("919999400000") == "9999400000"
   and M._digits10("09999400000") == "9999400000"
   and M._digits10("99994 00000") == "9999400000")
ok("galat input → khaali", M._digits10("12345") == "" and M._digits10("") == ""
   and M._digits10(None) == "" and M._digits10("abcdefghij") == "")
ok("junk lookup → Hindi error (network nahi)", M.lookup("123").get("ok") is False
   and "10-digit" in str(M.lookup("123").get("error")))

import modules.core.net as _net  # noqa: E402


class _FR:
    status_code = 200

    def __init__(self, d): self._d = d
    def json(self): return self._d


_calls = []
_real = _net.http_get
_old = {k: os.environ.get(k) for k in ("MYNUM_API_URL", "MYNUM_API_KEY")}
try:
    os.environ["MYNUM_API_URL"] = "https://fake.num/x"
    os.environ["MYNUM_API_KEY"] = "KKK"
    _net.http_get = lambda url, **kw: (_calls.append((url, kw)), _FR(_HIT))[1]
    if M._CACHE is not None:
        M._CACHE.clear()
    _r = M.lookup("9999400000")
    _s = dict(_calls[-1][1].get("params") or {})
    ok("term/key/tool sahi jaate hain", _s.get("term") == "9999400000"
       and _s.get("key") == "KKK" and _s.get("tool") == "num", str(_s))
    ok("mock lookup ok", _r.get("ok") is True and _r.get("source") == "myapi")
    _n0 = len(_calls)
    _r2 = M.lookup("9999400000")
    ok("cache (dobara network nahi)", len(_calls) == _n0 and _r2.get("cached") is True)
    _sc = M.status_card()
    ok("card me key VALUE nahi", "KKK" not in _sc and "MYNUM_API_KEY" in _sc)
    _st = M.status()
    ok("status me configured + timeout", _st.get("configured") is True
       and _st.get("timeout_s") == 40 and _st.get("cache_hours") == 6)
finally:
    _net.http_get = _real
    for _k, _v in _old.items():
        if _v is None:
            os.environ.pop(_k, None)
        else:
            os.environ[_k] = _v
    try:
        M._CACHE.clear()
    except Exception:                                        # noqa: BLE001
        pass

print("\n[D] Removal — purana kuch nahi bacha")
_NI = BOT_SRC[BOT_SRC.index('if mode == "numinfo":'):BOT_SRC.index('if mode == "ifsc":')]
ok("purana module file GAYA", not os.path.exists(os.path.join(ROOT, "modules", "numinfo_provider.py")))
ok("bot.py me numprov/provider-gone", "numprov" not in BOT_SRC
   and "numinfo_provider" not in BOT_SRC and "NUMINFO_PROVIDER" not in BOT_SRC
   and "NUMINFO_DEMO" not in BOT_SRC and "NUMINFO_WAIT" not in BOT_SRC)
ok("hub carrier API GAYI", "hub_carrier_info" not in BOT_SRC and "hub_carrier_info" not in HUB_SRC)
ok("demo/numtest/numdemo commands GAYE", "cmd_numdemo" not in BOT_SRC
   and "cmd_numtest" not in BOT_SRC and '"numdemo"' not in BOT_SRC and '"numtest"' not in BOT_SRC)
ok("flow me mynum + guard", "mynum.lookup" in _NI and "wait_for(" in _NI
   and "TimeoutError" in _NI)
ok("/numapi zinda (repurposed)", "async def cmd_numapi(" in BOT_SRC
   and "mynum.status_card()" in BOT_SRC)
ok("bulk mobile naya API", "mynum_api" in open(
    os.path.join(ROOT, "modules", "bulk_mode.py"), encoding="utf-8").read())

print("\n[E] Regression — version + prompts")
_vm = re.match(r"v(\d+)", B.BOT_VERSION)
ok("version v85+ (v99) + poori history",
   bool(_vm) and int(_vm.group(1)) >= 85 and "v99.0" in B.BOT_VERSION
   and "v98.0" in B.BOT_VERSION and "v97.0" in B.BOT_VERSION
   and "v96.0" in B.BOT_VERSION and "v95.0" in B.BOT_VERSION
   and "v94.0" in B.BOT_VERSION and "v93.0" in B.BOT_VERSION
   and "v86.0" in B.BOT_VERSION and "v85.0" in B.BOT_VERSION
   and "v84.0" in B.BOT_VERSION and "v83.0" in B.BOT_VERSION
   and "v77" in B.BOT_VERSION and "FREE4ALL" in B.BOT_VERSION, B.BOT_VERSION[:16])
ok("PROMPT_DATA 34 (v102: 3 gaye)", len(B.PROMPT_DATA) == 34,
   f"count={len(B.PROMPT_DATA)}")
ok("numinfo tool + prompt zinda", "numinfo" in B.PREMIUM_TOOLS
   and "numinfo" in B.PROMPT_DATA)

print(f"\nv99 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
if FAIL:
    print("FAILED:")
    for _f in FAIL:
        print(f"  ❌ {_f}")
    sys.exit(1)
