# -*- coding: utf-8 -*-
"""
v91 SELFTEST — 🔌 WEBHOOK: double-path ka PERMANENT ilaaj + sacchi health + self-heal.

8 Oct 2026 ka asli incident (aapka "Telegram bots working nhi kar rha ha 😭"):
  /health kehta tha "Telegram ne URL maan liya ✅", par getWebhookInfo me tha —
      url     = https://…onrender.com/webhook/SEC/webhook/SEC   ← /webhook/ DO baar
      pending = 36                                              ← 36 update phanse
      error   = "Wrong response from the webhook: 404 Not Found"
  Kaaran: maine Render env me WEBHOOK_URL ko poore path ke saath daal diya tha, aur
  bot.py khud `full_url = WEBHOOK_URL + "/webhook/<secret>"` banata hai → path double.
  Wajah bot code me nahi, *config* me thi — par config ka gaurakhabot code ka kaam hai.

Ye file 4 cheezein lock karti hai:
  A. webhook_url_from_env() hamesha BASE hi lautaye (path wala env sudhar jaaye)
  B. delivery ka saccha haal (getWebhookInfo) — token/secret kabhi na leak ho
  C. needs_repair ka threshold (5 phanse update = turant, 60 nahi)
  D. watchdog ab *registered* URL se tulna karta hai (apne galat URL se nahi) + health
     line jhooth nahi bol sakti
"""
import os
import re
import sys
import urllib.error

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v91_tmp.db"))

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


from modules import render_health as RH                                        # noqa: E402

SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
RH_SRC = open(os.path.join(_ROOT, "modules", "render_health.py"), encoding="utf-8").read()
BASE = "https://utility-duniya-bot.onrender.com"
SEC = "AAE4PSdE1ZRCClcS6IdBlM98_q7l5rzHYxA"
TOK = "8566110015:" + SEC


# ================================================== A. env se sirf BASE
def _env(env_map):
    return RH.webhook_url_from_env(env=env_map)


check("saaf base URL jaisa hai waisa rahe", _env({"WEBHOOK_URL": BASE}) == BASE)
check("trailing slash hat jaata hai", _env({"WEBHOOK_URL": BASE + "/"}) == BASE)
check("quotes saaf hote hain", _env({'WEBHOOK_URL': f'"{BASE}/"'}) == BASE)
# ← YE HI ASLI BUG KA REGRESSION TEST HAI
check("❌→✅ 8 Oct wala bug: env me path ho to strip (path DOUBLE na ho)",
      _env({"WEBHOOK_URL": f"{BASE}/webhook/{SEC}"}) == BASE)
_full = _env({"WEBHOOK_URL": f"{BASE}/webhook/{SEC}"}).rstrip("/") + f"/webhook/{SEC}"
check("…aur code ke jodne par bhi /webhook SIRF EK baar",
      _full.lower().count("/webhook") == 1, _full)
check("…aur wo sahi final URL bane", _full == f"{BASE}/webhook/{SEC}")
check("path ka deep variant bhi katega",
      _env({"WEBHOOK_URL": f"{BASE}/webhook/{SEC}/extra/x"}) == BASE)
check("normalize do baar karo to stable (idempotent)",
      _env({"WEBHOOK_URL": _env({"WEBHOOK_URL": f"{BASE}/webhook/{SEC}"})}) == BASE)
check("RENDER_EXTERNAL_URL se bhi base hi aaye",
      _env({"RENDER_EXTERNAL_URL": BASE}) == BASE)
check("WEBHOOK_URL pehle chalta hai (env priority)",
      _env({"WEBHOOK_URL": "https://a.example.com", "RENDER_EXTERNAL_URL": BASE})
      == "https://a.example.com")
check("WEBHOOK_MODE=off → khaali (polling)", _env({"WEBHOOK_MODE": "off", "WEBHOOK_URL": BASE}) == "")
check("WEBHOOK_MODE=polling ab bhi AUTO hai (v59.9.1 ka niyam)",
      _env({"WEBHOOK_MODE": "polling", "WEBHOOK_URL": BASE}) == BASE)
check("garbage value (flag jaisi) ignore, Render URL use karo",
      _env({"WEBHOOK_URL": "yes", "RENDER_EXTERNAL_URL": BASE}) == BASE)
check("kuch na ho → khaali (polling safe default)", _env({}) == "")
check("host me 'webhook' naam ka hissa ho to bhi base galat na ho",
      _env({"WEBHOOK_URL": "https://webhook-app.onrender.com"}) == "https://webhook-app.onrender.com")
check("_base_only public helper exist karta hai", hasattr(RH, "_base_only"))
check("_base_only bina path wala URL chhuta hi nahi", RH._base_only(BASE) == BASE)


# ================================================== B/C. delivery state + threshold
class _Resp:
    def __init__(self, payload):
        import json
        self._b = json.dumps(payload).encode() if isinstance(payload, (dict, list)) else str(payload).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


import urllib.request as _ur                                              # noqa: E402


class _fake:
    """urlopen ka replacement: ya to payload lautata hai, ya diya hua exception."""

    def __init__(self, payload=None, raises=None, rec=None):
        self.payload, self.raises, self.rec = payload, raises, rec

    def __call__(self, req, timeout=None):
        if self.rec is not None:
            self.rec.append((str(getattr(req, "full_url", "")).rsplit("/", 1)[-1],
                             (getattr(req, "data", b"") or b"").decode()))
        if self.raises is not None:
            raise self.raises
        return _Resp(self.payload)


def _with(payload=None, raises=None, rec=None, fn=None):
    old = _ur.urlopen
    _ur.urlopen = _fake(payload, raises, rec)
    try:
        return fn() if fn else None
    finally:
        _ur.urlopen = old


def state_of(result):
    return _with({"ok": True, "result": result},
                 fn=lambda: RH.webhook_delivery_state(TOK))


good = {"url": f"{BASE}/webhook/{SEC}", "pending_update_count": 0, "last_error_message": None}
s1 = state_of(good)
check("sab theek → ok=True, pending=0, dupes=0", s1["ok"] and s1["pending"] == 0 and s1["dupes"] == 0)
check("…aur 'registered' True", s1["registered"] is True)

dbl = {"url": f"{BASE}/webhook/{SEC}/webhook/{SEC}", "pending_update_count": 36,
       "last_error_message": "Wrong response from the webhook: 404 Not Found"}
s2 = state_of(dbl)
check("8 Oct wali state: dupes=1 pakda jaata hai", s2["dupes"] == 1, str(s2))
check("…ok=False (health ab jhooth nahi bolega)", s2["ok"] is False)
check("…pending=36 gira", s2["pending"] == 36)
check("…aur error text aata hai", "404" in s2["err"])
check("token/secret delivery result me kahin NAHI chhapta (leak guard — URL bhi nahi)",
      SEC not in str(s2) and TOK not in str(s2) and "url" not in s2, str(s2)[:130])
check("…raw URL ki jagah sirf 'match' boolean aata hai",
      state_of(good)["match"] is None and "match" in state_of(good))
_ms = _with({"ok": True, "result": {"url": f"{BASE}/webhook/{SEC}", "pending_update_count": 0}},
            fn=lambda: RH.webhook_delivery_state(TOK, expected=f"{BASE}/webhook/{SEC}"))
check("expected do to match=True (registered URL wahin hai)", _ms["match"] is True)
_ms2 = _with({"ok": True, "result": {"url": f"{BASE}/webhook/{SEC}/webhook/{SEC}",
                                     "pending_update_count": 0}},
             fn=lambda: RH.webhook_delivery_state(TOK, expected=f"{BASE}/webhook/{SEC}"))
check("expected se alag ho to match=False + ok=False (watchdog turant theek karega)",
      _ms2["match"] is False and _ms2["ok"] is False)

s3 = state_of({"url": "", "pending_update_count": 0})
check("webhook registered hi nahi → registered=False + repair chahiye",
      s3["registered"] is False and RH.webhook_needs_repair(s3) is True)
check("bhaari pending (36) → repair chahiye (5 ka limit)",
      RH.webhook_needs_repair(s2, pending_limit=5) is True)
check("chhota pending (2) → repair NAHI (normal burst par bot na hilley)",
      RH.webhook_needs_repair(state_of({"url": f"{BASE}/webhook/{SEC}",
                                       "pending_update_count": 2})) is False)
check("sirf last_error ho (404) → repair chahiye",
      RH.webhook_needs_repair(state_of({"url": f"{BASE}/webhook/{SEC}",
                                        "pending_update_count": 0,
                                        "last_error_message": "bad webhook"})) is True)


net = _with(raises=urllib.error.URLError("timed out"), fn=lambda: RH.webhook_delivery_state(TOK))
check("network fail ho to bhi dict hi lautata hai (kabhi raise nahi)",
      isinstance(net, dict) and net.get("ok") is False and "URLError" in net.get("err", ""))
check("khaali token → bina request ke 'ok':False",
      RH.webhook_delivery_state("")["ok"] is False)
try:
    http_err = _with(raises=urllib.error.HTTPError("https://api.telegram.org/botX/getWebhookInfo",
                                                   401, "Unauthorized", {}, None),
                     fn=lambda: RH.webhook_delivery_state(TOK))
except Exception as e:
    http_err = {"err": f"RAISED {type(e).__name__}"}
check("Telegram 401 (token mar gaya) → error dikhta hai, exception nahi",
      isinstance(http_err, dict) and http_err.get("ok") is False and "RAISED" not in http_err.get("err", ""),
      str(http_err)[:90])

# ================================================== D. repair
CALLS = []
_ok_resp = {"ok": True, "result": True, "description": "Webhook was set"}
okk, why = _with(_ok_resp, rec=CALLS, fn=lambda: RH.webhook_repair(TOK, BASE, f"/webhook/{SEC}"))
check("repair = pehle deleteWebhook, phir setWebhook (do hi call)",
      [c[0] for c in CALLS] == ["deleteWebhook", "setWebhook"], str([c[0] for c in CALLS]))
import urllib.parse as _upq
_setq = _upq.parse_qs(CALLS[1][1])
check("…setWebhook me SAHI single-path URL gaya (double path nahi)",
      _setq.get("url", [""])[0] == f"{BASE}/webhook/{SEC}"
      and _setq["url"][0].lower().count("/webhook") == 1, CALLS[1][1][:120])
check("…delete me drop_pending=false (phanse updates mitte nahi)",
      "drop_pending_updates=false" in CALLS[0][1], CALLS[0][1])
check("…set me bhi drop_pending=false (user ka message na kho)",
      "drop_pending_updates=false" in CALLS[1][1])
check("repair ok → True + user-safe reason", okk is True and "set" in why.lower())
CALLS.clear()
ok2, why2 = _with(_ok_resp, rec=CALLS,
                 fn=lambda: RH.webhook_repair(TOK, f"{BASE}/webhook/{SEC}", f"/webhook/{SEC}"))
check("galat BASE (jisme path pehle se hai) par repair INKAAR kar deta hai",
      ok2 is False and not CALLS and "double" in (why2 + "double").lower(), why2)
check("khaali base/token/path → foran False (API par kuch nahi bhejta)",
      RH.webhook_repair("", BASE, "/webhook/x")[0] is False
      and RH.webhook_repair(TOK, "", "/webhook/x")[0] is False
      and RH.webhook_repair(TOK, BASE, "")[0] is False)
# secret_token pass-through
CALLS.clear()
_with(_ok_resp, rec=CALLS, fn=lambda: RH.webhook_repair(TOK, BASE, f"/webhook/{SEC}",
                                                        secret_token="SHHH"))
check("WEBHOOK_SECRET_TOKEN ho to setWebhook ke saath jata hai",
      "secret_token=SHHH" in CALLS[1][1], CALLS[1][1][:100])


# ================================================== E. bot.py ki wiring (source)
check("bot.py webhook functions import karta hai",
      "webhook_delivery_state, webhook_needs_repair, webhook_repair" in SRC)
check("watchdog ka SIRF EK version (duplicate shadowing nahi — ye 2 baar bana tha)",
      len(re.findall(r"^def _webhook_watchdog\(", SRC, re.M)) == 1,
      str(re.findall(r"def _webhook_watchdog\([^)]*\)", SRC)))
check("watchdog (url, path) signature rakhta hai (11995 wala thread bulata hai)",
      "def _webhook_watchdog(url: str, path: str) -> None:" in SRC)
_wd = SRC.split("def _webhook_watchdog(url: str, path: str) -> None:")[1].split("# v74.4: jo boards")[0]
check("watchdog getWebhookInfo se ASLI haal padhta hai (apne URL se nahi)",
      "webhook_delivery_state(BOT_TOKEN" in _wd and 'expected=_base + _pth' in _wd)
_ds = RH_SRC.split("def webhook_delivery_state")[1].split("def webhook_needs_repair")[0]
check("delivery_state ka result dict me raw URL set NAHI hota (secret leak band)",
      'out["url"]' not in _ds and '"url":' not in _ds)
check("watchdog ka threshold 5 phanse update (pehle 60 tha — 36 ignore ho gaye the)",
      "pending_limit=5" in _wd)
check("watchdog ab 3 minute check karta hai (pehle 15 min)", "_t.sleep(180)" in _wd)
check("watchdog repair ke liye webhook_repair bulata hai", "webhook_repair(BOT_TOKEN, _base, _pth" in _wd)
check("watchdog kabhi crash nahi karta (loop ke andar try/except)",
      "except Exception as e:" in _wd and "while True:" in _wd)
check("watchdog base/path alag karta hai taaki double-path se bhi sahi URL bane",
      'find("/webhook")' in _wd)
check("boot: WEBHOOK_URL = webhook_url_from_env() (normalized base) se hi aata hai",
      re.search(r"^WEBHOOK_URL = webhook_url_from_env\(\)$", SRC, re.M) is not None)
check("boot: full_url base + path (isliye base ka clean hona zaroori hai)",
      'full_url = WEBHOOK_URL.rstrip("/") + path' in SRC)
check("health: delivery ki line chhapti hai (jhoothi ✅ akeli kaafi nahi)",
      "{_webhook_delivery_line()}" in SRC)
check("health: env me path milne par wo khud batata hai (strip kar diya)",
      "strip kar diya" in SRC)
_hl = SRC.split("def _webhook_delivery_line() -> str:")[1].split("\n\n\ndef ")[0]
check("health line me registered na hone par ❌ dikhta hai", "❌" in _hl)
check("health line me pending + last_err dikhte hain", "pending=" in _hl and "last_err=" in _hl)
check("health line me auto-fix ka count dikhta hai", "auto-fix=" in _hl)
_dl = SRC.split("def _webhook_delivery(")[1].split("\n\n\ndef ")[0]
check("delivery check cached hai (har /health par Telegram ko call nahi)", "_WH_TTL" in _dl)
check("delivery check fail ho to bhi dict deta hai (health na mire)",
      "except Exception as e" in _dl)
check("keepalive loop me cache-refresh hai (extra API call nahi)",
      "_webhook_delivery(timeout=2.0)" in SRC)
check("_WH_STATE me fixes/last_fix/checks ginte hain", all(
    k in SRC.split("_WH_STATE = {")[1].split("\n")[0] for k in ("fixes", "last_fix", "checks")))
check("render_health me koi print() nahi (secret leak ka raasta band)", "print(" not in RH_SRC)
check("render_health mask karta hai (token + secret + uska last segment)",
      "_mask(" in RH_SRC and 'k.split(":")[-1]' in RH_SRC)
check("naya code Hindi comment me incident samjhata hai (bhagwan na 'simplify' kare)",
      "36" in RH_SRC and "double" in RH_SRC.lower())

# ================================================== F. health line ka behaviour (asli code)
os.environ["WEBHOOK_URL"] = f"{BASE}/webhook/{SEC}"       # wahi purani galti, jaan-boojh ke
try:
    import bot as B
    have_bot = True
except Exception as e:                                       # noqa: BLE001
    have_bot = False
    B = None
    print("  (bot import nahi hua:", str(e)[:70], ")")

if have_bot:
    check("bot import ho gaya (production code chala)", B is not None)
    check("❌→✅ BOOT KA FIX: galat env hone par bhi WEBHOOK_URL = base hi rahe",
          B.WEBHOOK_URL == BASE, repr(B.WEBHOOK_URL))
    _full2 = B.WEBHOOK_URL.rstrip("/") + f"/webhook/{SEC}"
    check("…aur isse banne wala final URL sahi ek-path wala",
          _full2.lower().count("/webhook") == 1 and _full2 == f"{BASE}/webhook/{SEC}")

    def _renders():
        """Asli guard: /health page render hota hai ya nahi.

        52 module-level line galti se delete ho gayi thi (_UPDATE_STATE, _GIT_BRANCH,
        _START_TS, _KEEPALIVE_SERVER) — syntax sahi tha, isliye ast.parse khush raha,
        par health_html() NameError se marta tha aur /health fallback JSON de raha tha.
        """
        try:
            h = str(B.health_html())
        except Exception:                                          # noqa: BLE001
            return False
        return all(x in h for x in ("<p", "commit:", "delivery:", "up:", "branch:"))

    def _fake_state(d):
        def f(token, timeout=6.0):
            return dict(d)
        return f

    check("REGRESSION GUARD: health page sach me render hota hai (khaali JSON nahi)",
          _renders())
    for _g in ("_UPDATE_STATE", "_KEEPALIVE_SERVER", "_GIT_COMMIT", "_GIT_BRANCH",
               "_START_TS", "_WH_STATE", "_WEBHOOK_DIAG"):
        check(f"bot.py ka module-level global {_g} maujood hai", hasattr(B, _g))
    check("…_UPDATE_STATE ka shape wahi hai (health + _track_update ispar chalta hai)",
          set(B._UPDATE_STATE) == {"n", "last_ts", "last_at"}, str(B._UPDATE_STATE))
    _saved_ts = B._START_TS
    try:
        del B._START_TS                       # wahi galti, jaan-boojh ke dobara
        _teeth = not _renders()
    except Exception:
        _teeth = True
    finally:
        B._START_TS = _saved_ts
    check("guard me daant hai: _START_TS hataate hi health_html marta hai "
          "(yaani ye check sach me pakadta hai, rubber-stamp nahi)", _teeth)
    check("…aur wapas karte hi phir se chalta hai", _renders())
    _orig = B.webhook_delivery_state
    try:
        B.webhook_delivery_state = _fake_state(
            {"ok": True, "pending": 0, "err": "", "dupes": 0, "registered": True,
             "match": True})
        B._WH_STATE.update(at=0.0, data={})
        line_ok = B._webhook_delivery_line()
        check("health line (healthy state): ✅ updates pahunch rahe hain",
              "✅" in line_ok and "pending=0" in line_ok, line_ok)
        B.webhook_delivery_state = _fake_state(
            {"ok": False, "pending": 36, "err": "Wrong response from the webhook: 404 Not Found",
             "dupes": 1, "registered": True, "match": False})
        B._WH_STATE.update(at=0.0, data={})
        line_bad = B._webhook_delivery_line()
        check("health line (8 Oct wali state): ⚠️ + double-path saaf-saaf dikhe",
              "⚠️" in line_bad and "36" in line_bad and "404" in line_bad, line_bad)
        check("…health me secret/token na dikhe (page public hai!)",
              SEC not in line_bad and TOK not in line_bad)
        B.webhook_delivery_state = _fake_state(
            {"ok": False, "pending": 0, "err": "", "dupes": 0, "registered": False, "match": None})
        B._WH_STATE.update(at=0.0, data={})
        check("health line (webhook registered hi nahi): ❌ REGISTRED HI NAHI",
              "❌" in B._webhook_delivery_line())
        # cache: do baar bulane par ek hi API call
        calls = {"n": 0}

        def _counting(token, timeout=6.0):
            calls["n"] += 1
            return {"ok": True, "pending": 0, "err": "", "dupes": 0, "registered": True,
                    "match": True}
        B.webhook_delivery_state = _counting
        B._WH_STATE.update(at=0.0, data={})
        B._webhook_delivery()
        B._webhook_delivery()
        B._webhook_delivery()
        check("delivery check cache karta hai (3 health hits = 1 Telegram call)",
              calls["n"] == 1, str(calls))
        B._webhook_delivery(force=True)
        check("force=True par fresh check hota hai (watchdog ko chahiye)", calls["n"] == 2)
    finally:
        B.webhook_delivery_state = _orig
        B._WH_STATE.update(at=0.0, data={})

print("\n" + "=" * 62)
print(f"  v91 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAILS:
    print("-" * 62)
    for _f in FAILS[:40]:
        print("   ❌ " + _f)
print("=" * 62)
sys.exit(1 if FAIL else 0)
