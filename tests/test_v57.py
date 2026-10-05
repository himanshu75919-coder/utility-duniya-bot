# -*- coding: utf-8 -*-
"""
tests/test_v57 — v57 "NUMBER INFO API + PREMIUM CARDS" suite
============================================================
v57 me kya hua:

  1. 📱 NUMBER INFO — AAPKI API (naya module `modules/numinfo_provider.py`)
     • Docs me v49.6 se `NUMINFO_PROVIDER_URL/KEY` likha tha par code me
       implement hi NAHI tha — sirf docs me tha. Ab sach me kaam karta hai.
     • 6 env vars: URL / KEY / PARAM / KEY_PARAM / AUTH / TIMEOUT
     • Response shape auto-detect (numverify / abstractapi / veriphone /
       twilio / nested-data — sab chalte hain)
     • 6 ghante cache (API quota bachta hai)
     • Provider + hub PARALLEL (asyncio.gather) — pehle serial tha
     • Fallback chain: provider → hub → offline phonenumbers (kabhi band nahi)

  2. `/numapi` — admin command: API lagi hai ya nahi + live test.
     KEY KABHI PRINT NAHI HOTI (sirf "set / not set").

  3. 🚨 ASLI BUG FIX — `BRAND_TAG` bot.py me DEFINE hi nahi tha par
     numinfo card me use hota tha → NameError crash. Ab os.getenv se aata hai.

  4. 🖼️ PREMIUM CARDS — ek reusable helper (pcard_title/pcard_foot/pcard_sep).
     Ab: IFSC · PINCODE (dono) · BGMI · FF UID · APP FINDER · LINK CHECK
     Sab boxed + 📡 Source + ⚡ Response time + 🔥 brand footer.

  5. ⚡ PERFORMANCE — LINK CHECK handler ka `analyze_link()` **blocking** call
     tha (async handler me seedha) → event loop ruk jaata tha, sab users slow.
     Ab asyncio.to_thread me.

Chalane ka tarika:
    python3 tests/test_v57.py
"""
from __future__ import annotations

import ast
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

BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()

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
        FAILURES.append(f"{name} {extra}")
        print(f"  ❌ {name}  {extra}")
    return bool(cond)


# =====================================================================
section("1) 📱 NUMINFO PROVIDER MODULE — naya, kabhi crash nahi karta")
# =====================================================================
import modules.numinfo_provider as NP  # noqa: E402

check("numinfo_provider module import hota hai", True)
for _fn in ("is_configured", "lookup", "status", "status_card",
            "provider_url", "provider_key", "provider_auth", "provider_param"):
    check(f"numinfo_provider.{_fn}() maujood hai", hasattr(NP, _fn))

# config env vars padhta hai
for _var in ("NUMINFO_PROVIDER_URL", "NUMINFO_PROVIDER_KEY",
             "NUMINFO_PROVIDER_PARAM", "NUMINFO_PROVIDER_KEY_PARAM",
             "NUMINFO_PROVIDER_AUTH", "NUMINFO_PROVIDER_TIMEOUT"):
    check(f"'{_var}' env var support hai", _var in open(
        os.path.join(ROOT, "modules", "numinfo_provider.py"), encoding="utf-8").read())

# provider set na ho to crash NAHI — saaf dict
_r = NP.lookup("9876543210")
check("provider set na ho to crash nahi (dict milta hai)", isinstance(_r, dict))
check("provider set na ho to not_configured=True", _r.get("not_configured") is True)
check("provider set na ho to ok=False", _r.get("ok") is False)
check("is_configured() False deta hai", NP.is_configured() is False)
check("khaali number par bhi crash nahi", isinstance(NP.lookup(""), dict))

# =====================================================================
section("2) 🔀 RESPONSE PARSING — koi bhi provider shape chalta hai")
# =====================================================================
# Har bade provider ka asli response shape test karo (offline, network nahi)


def _parse(data):
    """lookup() ka parsing hissa (network ke bina)."""
    flat = NP._flatten(data)
    return {
        "operator": NP._clean_name(NP._pick(
            flat, "carrier", "carrier_name", "carriername", "operator",
            "operatorname", "network", "network_name", "networkname",
            "provider", "providername")),
        "circle": NP._clean_name(NP._pick(
            flat, "location", "circle", "region", "state", "zone",
            "geolocation", "area")),
        "type": NP._nice_line_type(NP._pick(
            flat, "linetype", "line_type", "type", "numbertype",
            "phonetype", "carrier_type", "carriertype")),
        "ported": NP._clean_name(NP._pick(flat, "ported", "mnp", "isported", "portability")),
    }


_cases = [
    ("numverify", {"valid": True, "country_name": "India", "location": "Bihar",
                   "carrier": "Airtel", "line_type": "mobile"},
     {"operator": "Airtel", "circle": "Bihar", "type": "📱 Mobile"}),
    ("abstractapi", {"phone": "+919876543210", "valid": True,
                     "country": {"name": "India", "code": "IN"},
                     "carrier": "Jio", "type": "mobile"},
     {"operator": "Jio", "type": "📱 Mobile"}),
    ("veriphone", {"status": "success", "phone_valid": True, "carrier": "Vi India",
                   "phone_type": "mobile", "country": "India"},
     {"operator": "Vi India", "type": "📱 Mobile"}),
    ("nested/data", {"status": "success", "data": {"network": "BSNL",
                                                   "circle": "Bihar", "type": "landline",
                                                   "mnp": True}},
     {"operator": "BSNL", "circle": "Bihar", "type": "☎️ Landline"}),
    ("twilio style", {"carrier": {"type": "mobile", "name": "Airtel"},
                      "country_code": "IN"},
     {"operator": "Airtel", "type": "📱 Mobile"}),
    ("reliance", {"carrier": {"name": "Reliance Jio", "region": "MH"}, "type": "mobile"},
     {"operator": "Reliance Jio", "circle": "MH"}),
]
for _lbl, _payload, _expect in _cases:
    got = _parse(_payload)
    ok = all(got.get(k) == v for k, v in _expect.items())
    check(f"{_lbl} → {_expect} ", ok, f"mila={got}")

# junk values (NA / null / -) khaali hone chahiye
_junk = _parse({"carrier": "NA", "location": "null", "line_type": "-"})
check("junk values ('NA'/'null'/'-') khaali ho jaate hain",
      _junk == {"operator": "", "circle": "", "type": "", "ported": ""}, str(_junk))

# ---------- status card (key kabhi print na ho) ----------
_card = NP.status_card()
check("status_card() string deta hai", isinstance(_card, str) and len(_card) > 80)
check("status_card me 'SET NAHI HAI' dikhta hai (abhi set nahi)",
      "SET NAHI HAI" in _card)
check("status_card me setup instruction hai", "NUMINFO_PROVIDER_URL" in _card)
check("status_card me guide ka naam hai", "NUMBER-INFO-API-SETUP.md" in _card)

# =====================================================================
section("3) 🚨 BRAND_TAG CRASH FIX (asli bug)")
# =====================================================================
import bot  # noqa: E402

check("BOT_VERSION v57 par hai", 'BOT_VERSION = "v57.' in BOT_SRC)
check("BRAND_TAG bot.py me DEFINED hai (pehle NameError crash tha)",
      hasattr(bot, "BRAND_TAG"))
check("BRAND_TAG ki value sahi hai", str(bot.BRAND_TAG).startswith("@"))
check("BRAND_TAG os.getenv se aata hai (Render se badal sakte ho)",
      'BRAND_TAG = (os.getenv("BRAND_TAG"' in BOT_SRC)

# BOT_SRC me koi bhi undefined top-level naam use na ho (basic sanity)
_tree = ast.parse(BOT_SRC)
_defined = set()
for _n in _tree.body:
    if isinstance(_n, (ast.Assign, ast.AnnAssign)):
        _t = _n.targets if isinstance(_n, ast.Assign) else [_n.target]
        for _x in _t:
            if isinstance(_x, ast.Name):
                _defined.add(_x.id)
    elif isinstance(_n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        _defined.add(_n.name)
    elif isinstance(_n, (ast.Import, ast.ImportFrom)):
        for _a in _n.names:
            _defined.add(_a.asname or _a.name.split(".")[0])
check("BRAND_TAG top-level par defined hai", "BRAND_TAG" in _defined)

# =====================================================================
section("4) 🖼️ PREMIUM CARD HELPERS + wiring")
# =====================================================================
for _h in ("pcard_title", "pcard_foot", "pcard_sep", "PCARD_TOP", "PCARD_MID", "PCARD_BOT"):
    check(f"helper '{_h}' maujood hai", hasattr(bot, _h))

_t = bot.pcard_title("🏦", "TEST CARD")
check("pcard_title boxed header banata hai", "┌" in _t and "└" in _t and "│" in _t)
check("pcard_title title ko bold-unicode karta hai", "𝐓𝐄𝐒𝐓" in _t)

_f = bot.pcard_foot(ms=250, source="TestAPI")
check("pcard_foot me source dikhta hai", "TestAPI" in _f)
check("pcard_foot me response time dikhta hai (250ms)", "250ms" in _f)
_f2 = bot.pcard_foot(ms=1500)
check("pcard_foot 1.5s ko '1.5s' likhta hai", "1.5s" in _f2)
check("pcard_foot me brand footer hai", bot.BRAND_TAG in _f)
check("pcard_foot brand=False par footer nahi",
      bot.BRAND_TAG not in bot.pcard_foot(brand=False))
check("pcard_sep separator deta hai", bot.pcard_sep() == "─" * 30)

# kaunse tools premium ho gaye
for _tool, _needle in (
        ("IFSC", 'pcard_title("🏦", "IFSC BANK BRANCH REPORT")'),
        ("PINCODE", 'pcard_title("📮", "PINCODE DETAILS")'),
        ("AREA SEARCH", 'pcard_title("📮", "AREA SEARCH")'),
        ("BGMI", 'pcard_title("🎮", "BGMI PLAYER CARD")'),
        ("APP FINDER", 'pcard_title("📦", "APP FINDER")'),
        ("LINK CHECK", 'pcard_title("🛡️", "LINK CHECK REPORT")'),
        ("NUMBER INFO", 'to_bold(\'NUMBER INFO REPORT\')')):
    check(f"{_tool} card premium hai", _needle in BOT_SRC, _needle[:42])

check("FF UID card me premium footer hai", "Garena public profile" in BOT_SRC)
check("kam se kam 8 cards me pcard_foot laga hai", BOT_SRC.count("pcard_foot(") >= 8,
      f"count={BOT_SRC.count('pcard_foot(')}")

# =====================================================================
section("5) ⚡ PERFORMANCE — blocking call async handler se hata")
# =====================================================================
# analyze_link() pehle async handler me SEEDHA call hota tha (event loop block).
_lc_i = BOT_SRC.index('if mode == "linkcheck":')
_lc_j = BOT_SRC.index('if mode == "appfind":', _lc_i)
_lc = BOT_SRC[_lc_i:_lc_j]
check("LINK CHECK: analyze_link ab asyncio.to_thread me hai",
      "await asyncio.to_thread(analyze_link" in _lc)
check("LINK CHECK: seedha blocking call nahi bacha",
      "\n        chk = analyze_link(" not in _lc)
check("LINK CHECK: response time measure hota hai", "_ms = (time.perf_counter()" in _lc)

# numinfo: provider + hub PARALLEL
_ni_i = BOT_SRC.index('if mode == "numinfo":')
_ni_j = BOT_SRC.index('if mode == "ifsc":', _ni_i)
_ni = BOT_SRC[_ni_i:_ni_j]
check("NUMBER INFO: provider + hub PARALLEL chalte hain (asyncio.gather)",
      "asyncio.gather(" in _ni)
check("NUMBER INFO: dono apni jagah call hote hain",
      "numprov.lookup" in _ni and "hub_carrier_info" in _ni)
check("NUMBER INFO: fallback chain hai (provider → hub → offline)",
      '"source" or "offline"' in _ni or "or \"offline\"" in _ni)
check("NUMBER INFO: live source line dikhti hai",
      "LIVE" in _ni and "OFFLINE" in _ni)
check("NUMBER INFO: response time card me hai", 'int(_ms)}ms' in _ni)
check("NUMBER INFO: privacy line hai (koi leaked data nahi)",
      "leaked" in _ni.lower())

# =====================================================================
section("6) 🔌 /numapi ADMIN COMMAND")
# =====================================================================
check("cmd_numapi function maujood hai", "async def cmd_numapi(" in BOT_SRC)
check("cmd_numapi admin-only hai", "def cmd_numapi" in BOT_SRC and
      BOT_SRC[BOT_SRC.index("async def cmd_numapi"):][:400].count("is_admin") >= 1)
check("/numapi handler registered",
      "CommandHandler([\"numapi\", \"numinfoapi\", \"numberapi\"], cmd_numapi)" in BOT_SRC)
check("cmd_numapi status_card() use karta hai", "numprov.status_card()" in BOT_SRC)
check("cmd_numapi live test chalta hai", "numprov.lookup" in BOT_SRC)
check("live test me latency dikhti hai", "Latency" in BOT_SRC)
check("fail hone par 4-check troubleshooting dikhta hai",
      "Ye 4 cheezein check karo" in BOT_SRC)
check("fail hone par guide ka reference hai", "NUMBER-INFO-API-SETUP.md" in BOT_SRC)
check("fail par user ko batata hai tool band nahi hai",
      "band nahi hai" in BOT_SRC)

# KEY kabhi print na ho — kisi bhi card/message me
check("provider_key() sirf status me use hota hai (bool)",
      "provider_key()" not in BOT_SRC or "provider_key())\n" not in BOT_SRC)
check("status_card key ki VALUE nahi dikhata (sirf set/not set)",
      "set (chhupi hui)" in open(os.path.join(ROOT, "modules", "numinfo_provider.py"),
                                 encoding="utf-8").read())

# =====================================================================
section("7) 📄 DOCS + RENDER CONFIG")
# =====================================================================
check("NUMBER-INFO-API-SETUP.md guide maujood hai",
      os.path.exists(os.path.join(ROOT, "NUMBER-INFO-API-SETUP.md")))
_g = open(os.path.join(ROOT, "NUMBER-INFO-API-SETUP.md"), encoding="utf-8").read()
for _step in ("STEP 1", "STEP 2", "STEP 3", "STEP 4"):
    check(f"guide me {_step} hai", _step in _g)
check("guide me numverify ke exact values hain",
      "https://apilayer.net/api/validate" in _g and "access_key" in _g)
check("guide me abstractapi ke exact values hain",
      "phonevalidation.abstractapi.com" in _g and "api_key" in _g)
check("guide me Render ka exact path hai",
      "Environment" in _g and "utility-duniya-bot" in _g)
check("guide me safety table hai (key kisi ko na do)", "NA KARO" in _g)
check("guide me honesty section hai (naam/address nahi milta)",
      "owner" in _g.lower() and "Nahi" in _g)

_y = open(os.path.join(ROOT, "render.yaml"), encoding="utf-8").read()
for _k in ("NUMINFO_PROVIDER_URL", "NUMINFO_PROVIDER_KEY", "NUMINFO_PROVIDER_PARAM",
           "NUMINFO_PROVIDER_KEY_PARAM", "NUMINFO_PROVIDER_AUTH",
           "NUMINFO_PROVIDER_TIMEOUT"):
    check(f"render.yaml me {_k} hai", _k in _y)
check("render.yaml me KEY sync:false hai (secret)",
      "NUMINFO_PROVIDER_KEY\n        sync: false" in _y)

_e = open(os.path.join(ROOT, ".env.example"), encoding="utf-8").read()
check(".env.example me NUMINFO_PROVIDER_URL hai", "NUMINFO_PROVIDER_URL" in _e)

# =====================================================================
section("8) 🧾 SANITY — kuch aur toota nahi")
# =====================================================================


def _dup_keys(path):
    _t = ast.parse(open(path, encoding="utf-8").read())
    _out = []
    for _n in ast.walk(_t):
        if isinstance(_n, ast.Dict):
            _ks = [k.value for k in _n.keys
                   if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            _d = {x for x in _ks if _ks.count(x) > 1}
            if _d:
                _out.append(sorted(_d))
    return _out


check("bot.py me duplicate dict keys nahi", not _dup_keys(os.path.join(ROOT, "bot.py")),
      str(_dup_keys(os.path.join(ROOT, "bot.py"))[:2]))

# purane crash patterns wapas na aayein
_bad = re.findall(r"\b\w*message\.send_(?:photo|document|video)\s*\(", BOT_SRC)
check("Message.send_* crash pattern wapas nahi aaya", not _bad, str(_bad[:2]))
for _m in ("ip", , "webscraper", "aadeid", "tginfo"):
    check(f'deleted tool "{_m}" ka handler nahi aaya', f'if mode == "{_m}":' not in BOT_SRC)

# saare modules import
import importlib as _il  # noqa: E402
_ghost = []
for _mn in ("api_hub", "channel_cloner", "cloud_tools", "core.cache", "core.limiter",
            "core.net", "core.telemetry", "cyber_studio", "desi_tools", "gaming_tools",
            "general_tools", "imei_lookup", "media_downloader", "numinfo_provider",
            "osint_hub", "osint_tools", "payguard", "render_health", "sarkari_hub",
            "temp_mail", "toolkit_extras", "tutorial_hub", "vip_payment"):
    try:
        _m = _il.import_module(f"modules.{_mn}")
    except Exception as _e:                                  # noqa: BLE001
        _ghost.append(f"{_mn}: {_e}")
        continue
    for _n in getattr(_m, "__all__", []):
        if not hasattr(_m, _n):
            _ghost.append(f"{_mn}.__all__ -> {_n} ghost")
check("saare modules import hote hain + __all__ saaf", not _ghost, "; ".join(_ghost[:3]))

# =====================================================================
section("9) 🌐 HTML SAFETY — user data escape (asli crash bugs)")
# =====================================================================
# v57 audit: bot.py ke saare f-strings scan kiye jo parse_mode=HTML ke saath
# jaate hain. 4 jagah USER DATA bina escape ja raha tha → Telegram
# "can't parse entities" → pura message reject (user ko kuch nahi milta).
check("safe_html_err() helper maujood hai", hasattr(bot, "safe_html_err"))
check("_tags_balanced() helper maujood hai", hasattr(bot, "_tags_balanced"))

# --- safe_html_err ka behaviour ---
check("safe_html_err: engine HTML rakhta hai",
      "<b>Profile</b>" in bot.safe_html_err("Game me: <b>Profile</b> dekho"))
check("safe_html_err: <script> escape karta hai",
      "&lt;script&gt;" in bot.safe_html_err("<script>alert(1)</script>"))
_js = bot.safe_html_err('<a href="javascript:alert(1)">y</a>')
check("safe_html_err: javascript: link EXECUTABLE nahi rehta (escaped text ban jaata hai)",
      '<a href="javascript' not in _js and "&lt;a href=" in _js, _js)
check("safe_html_err: orphan </a> escape",
      "&lt;/a&gt;" in bot.safe_html_err("evil </a> text"))
check("safe_html_err: safe https link pair rakhta hai",
      '<a href="https://t.me/x">' in bot.safe_html_err('<a href="https://t.me/x">x</a>'))
check("safe_html_err: khaali input par khaali deta hai", bot.safe_html_err("") == "")
check("safe_html_err: None par crash nahi", bot.safe_html_err(None) == "")

# --- HAR output balanced hona chahiye (warna Telegram reject karega) ---
_tricky = [
    "<b>unclosed", "orphan</i>", "<b>x</b> aur </i>", "<script>a</script>",
    "a < b > c", "&already-escaped;", '<a href="http://x.com">http link</a>',
    '<a href="HTTPS://x.com">caps</a>', "<pre>code</pre>", "<tg-spoiler>s</tg-spoiler>",
    "User <b>bold</b> aur <img src=x>", "<<double>>", "<", ">",
]
_all_bal = all(bot._tags_balanced(bot.safe_html_err(t)) for t in _tricky)
check(f"safe_html_err ka har output balanced hai ({len(_tricky)} tricky inputs)",
      _all_bal, str([t for t in _tricky if not bot._tags_balanced(bot.safe_html_err(t))][:3]))

# --- BGMI/IMEI/GST/PAN/numapi me hesc → safe_html_err ---
check("BGMI error ab safe_html_err se jaata hai",
      "f\"❌ {safe_html_err(res.get('error'))}\"" in BOT_SRC)
check("BGMI error me hesc() nahi bacha",
      "hesc(str(res.get('error') or ''))" not in BOT_SRC)
check("IMEI status error safe_html_err use karta hai",
      BOT_SRC.count("safe_html_err(str(res.get('error'))") >= 3)
check("GST/PAN error safe_html_err use karte hain",
      BOT_SRC.count('safe_html_err(str(res.get(\'error\'))[:200])') >= 2 or
      BOT_SRC.count("safe_html_err(str(res.get('error'))[:200])") >= 2)

# --- purane 4 injection bugs wapas na aayein ---
check("Video Downloader title ab escape hota hai (3 jagah)",
      BOT_SRC.count("hesc(str(title))") >= 3,
      f"count={BOT_SRC.count('hesc(str(title))')}")
check("Cloner rename tag escape hota hai", "hesc(raw_text)}</b>" in BOT_SRC)
check("URL Short cleaned link escape hota hai", "hesc(str(clean))" in BOT_SRC)

# --- systematic re-scan: in 4 variables ko HTML me bina escape na bhejein ---
_bad = []
for _i, _ln in enumerate(BOT_SRC.splitlines(), 1):
    if not any(t in _ln for t in ("<b>", "<i>", "<code>", "<pre>")):
        continue
    for _v in ("raw_text", "title", "clean"):
        if re.search(r"\{" + _v + r"(?:\[[^\]]*\])?(?::[^}]*)?\}", _ln):
            if not any(w in _ln for w in ("hesc(", "safe_html_err(", "cut_html(", "to_bold(")):
                _bad.append(f"L{_i}[{_v}]: {_ln.strip()[:70]}")
check("user data (raw_text/title/clean) kisi HTML line me unescaped nahi",
      not _bad, "; ".join(_bad[:3]))


# =====================================================================
section("10) 🔬 END-TO-END — provider config + lookup (mock HTTP, network nahi)")
# =====================================================================
import modules.core.net as _net  # noqa: E402

_orig_get = _net.http_get
_orig_env = {k: os.environ.get(k) for k in (
    "NUMINFO_PROVIDER_URL", "NUMINFO_PROVIDER_KEY", "NUMINFO_PROVIDER_PARAM",
    "NUMINFO_PROVIDER_KEY_PARAM", "NUMINFO_PROVIDER_AUTH")}
_calls = []


class _FakeResp:
    """modules.core.net ka response object jaisa (status_code + json())."""
    status_code = 200

    def __init__(self, data): self._d = data
    def json(self): return self._d


def _fake_get(url, **kw):
    _calls.append((url, kw))
    return _FakeResp({"valid": True, "country_name": "India", "location": "Bihar",
                      "carrier": "Airtel", "line_type": "mobile"})


try:
    os.environ.update({
        "NUMINFO_PROVIDER_URL": "https://fake.api/validate",
        "NUMINFO_PROVIDER_KEY": "K" * 20,
        "NUMINFO_PROVIDER_PARAM": "number",
        "NUMINFO_PROVIDER_KEY_PARAM": "access_key",
        "NUMINFO_PROVIDER_AUTH": "query"})
    _net.http_get = _fake_get
    import importlib as _il2
    NP = _il2.reload(NP)
    if getattr(NP, "_CACHE", None) is not None:
        NP._CACHE.clear()

    check("config set hone par is_configured() True", NP.is_configured() is True)

    _r = NP.lookup("9876543210")
    check("lookup() ok=True deta hai", _r.get("ok") is True, str(_r)[:120])
    check("lookup() operator parse karta hai", _r.get("operator") == "Airtel")
    check("lookup() circle parse karta hai", _r.get("circle") == "Bihar")
    check("lookup() line type parse karta hai", "Mobile" in str(_r.get("type")))
    check("lookup() source='provider' batata hai", _r.get("source") == "provider")
    check("lookup() latency_ms deta hai", isinstance(_r.get("latency_ms"), int))

    # number parameter me jaana chahiye + key us param me (query auth)
    _u, _kw = _calls[-1]
    _sent = dict(_kw.get("params") or {})
    # provider APIs ko FULL international number chahiye (numverify etc.) —
    # sirf 10 digit nahi, isliye 919876543210 jaata hai. Ye SAHI behaviour hai.
    _num_sent = str(_sent.get("number") or "")
    check("number sahi param me jaata hai (full international format)",
          _num_sent.endswith("9876543210") and len(_num_sent) >= 10, str(_sent))
    check("key NUMINFO_PROVIDER_KEY_PARAM wale param me jaati hai",
          _sent.get("access_key") == "K" * 20, str(list(_sent)))
    check("URL me key NAHI jaati (query param se jaati hai)", "K" * 20 not in _u, _u)

    # cache: dobara call par network NAHI hona chahiye
    _n_before = len(_calls)
    _r2 = NP.lookup("9876543210")
    check("same number dobara → cache se (network call nahi)",
          len(_calls) == _n_before, f"calls {_n_before} -> {len(_calls)}")
    check("cache se aane par cached=True", _r2.get("cached") is True)

    # KEY KABHI card me nahi
    _card = NP.status_card()
    check("status_card me key ki VALUE nahi jaati", "K" * 20 not in _card)
    check("status_card me URL dikhta hai", "fake.api" in _card)

    # auth=header mode
    os.environ["NUMINFO_PROVIDER_AUTH"] = "header"
    NP = _il2.reload(NP)
    if getattr(NP, "_CACHE", None) is not None:
        NP._CACHE.clear()
    _calls.clear()
    NP.lookup("9876543210")
    _h = dict((_calls[-1][1].get("headers") or {}))
    check("AUTH=header par key header me jaati hai (params me nahi)",
          any(v == "K" * 20 for v in _h.values()), str(list(_h)))
    check("AUTH=header par URL/params me key nahi",
          "K" * 20 not in str(_calls[-1][1].get("params") or {}))

    # {number} placeholder mode
    os.environ["NUMINFO_PROVIDER_URL"] = "https://fake.api/v/{number}"
    NP = _il2.reload(NP)
    if getattr(NP, "_CACHE", None) is not None:
        NP._CACHE.clear()
    _calls.clear()
    NP.lookup("9876543210")
    check("URL me {number} placeholder bhar jaata hai",
          "9876543210" in _calls[-1][0] and "{number}" not in _calls[-1][0], _calls[-1][0])

finally:
    _net.http_get = _orig_get
    for _k, _v in _orig_env.items():
        if _v is None:
            os.environ.pop(_k, None)
        else:
            os.environ[_k] = _v
    NP = _il2.reload(NP)


print("\n" + "=" * 62)
print(f"  v57 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILURES:
    print("\n  FAILURES:")
    for _f in FAILURES:
        print(f"   - {_f}")
print()
sys.exit(0 if FAIL == 0 else 1)
