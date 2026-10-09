# -*- coding: utf-8 -*-
"""
v73 SELFTEST — 📞 TEMP MAIL (NUMBER) — 100% FREE temp number + OTP
==================================================================
Boss ka order (7 Oct 2026):
  • Alag tool (Virtual Numbers se bilkul alag), naam "Temp Mail"
  • 100% FREE — koi credit / paisa / key nahi
  • Har Telegram user ko ALAG number (owner ko bhi alag) — repeat nahi
  • 10+ services + 10+ countries
  • Bank / UPI / KYC OTP ke liye SAAF warning
  • "100% properly working" — crash-proof, khaali card kabhi nahi

Test 100% OFFLINE hai — koi network call nahi (sab fixtures + mocks).
"""
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv73_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V73"
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
print("  v73 SELFTEST — 📞 TEMP MAIL (NUMBER) — FREE temp number + OTP")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import temp_number as TN                             # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
TN_SRC = open(os.path.join(_ROOT, "modules", "temp_number.py"), encoding="utf-8").read()

# =====================================================================
section("1) Tool spec — 10+ services, 10+ countries (user ka order)")
check("services ab sirf 1 (WhatsApp) — v74.3 order", len(TN.SERVICES) == 1
      and TN.SERVICES[0][0] == "whatsapp", str(len(TN.SERVICES)))
check("countries ab 3 (fi/nl/us) — v74.3 order",
      [c["cc"] for c in TN.COUNTRIES] == ["fi", "nl", "us"], str(len(TN.COUNTRIES)))
check("service keys unique", len({s[0] for s in TN.SERVICES}) == len(TN.SERVICES))
check("country codes unique", len({c["cc"] for c in TN.COUNTRIES}) == len(TN.COUNTRIES))
check("har country me flag + naam hai",
      all(c.get("flag") and c.get("name") and c.get("cc") for c in TN.COUNTRIES))
check("WhatsApp list me hai (v74.3: sirf WhatsApp, baaki apps aage)",
      "whatsapp" in {s[0] for s in TN.SERVICES} and len(TN.SERVICES) == 1)
check("OTP-friendly desh list me hain (FI/NL/US)",
      [c["cc"] for c in TN.COUNTRIES] == ["fi", "nl", "us"])
check("100% free promise module doc me likha hai",
      "free" in TN.__doc__.lower() and "koi key" in TN.__doc__.lower())
check("bank red-line module doc me hai", "bank" in TN.__doc__.lower())
check("koi paid API / key nahi maangta (source doc me keya nahi)",
      "api_key" not in TN_SRC and "API_KEY" not in TN_SRC)

# =====================================================================
section("2) Parsers — 3 sources ke fixtures (offline)")

_RC_HTML = """
<title>US Phone Number +18282768125 - Receive SMS Online</title>
<span class="stat">Last activity: 17 minutes ago</span>
<span class="stat">Messages (24h): 49</span>
<article class="entry-card type--default">
  <div class="entry-head">
    <div class="entry-left"><strong class="from-label">From</strong>
      <a href="/who-called-me/18335532731/" class="from-link">18335532731</a></div>
    <div class="entry-right"><span class="chip" data-code="343846" title="Click to copy code">
      Code: <strong class="code" data-code="343846">343846</strong></span>
      <span class="muted">17 minutes ago</span></div>
  </div>
  <div class="entry-body"><div class="sms">Your verification code is 343846</div></div>
</article>
<article class="entry-card type--default">
  <div class="entry-head">
    <div class="entry-left"><strong class="from-label">From</strong>
      <a href="/who-called-me/22905/" class="from-link">22905</a></div>
    <div class="entry-right"><span class="chip" data-code="021075">
      Code: <strong class="code" data-code="021075">021075</strong></span>
      <span class="muted">34 minutes ago</span></div>
  </div>
  <div class="entry-body"><div class="sms">[WeChat] WeChat code (021075) may only be used once.</div></div>
</article>
"""

_RSF_HTML = """
<span class="nav">+12543207584</span>
<div class="sms-item p-3 border-bottom bg-white">
  <div class="d-flex justify-content-between align-items-center mb-2">
    <div class="d-inline-flex align-items-center gap-1">
      <span class="sender-badge">22395</span></div>
    <span class="time-text d-flex align-items-center gap-1">3 min ago</span>
  </div>
  <p class="sms-content m-0">Your Yotta verification code is: 278080. Don't share this code.</p>
</div>
<div class="sms-item p-3 border-bottom bg-white">
  <div class="d-flex justify-content-between align-items-center mb-2">
    <span class="sender-badge">Google</span>
    <span class="time-text">1 min ago</span>
  </div>
  <p class="sms-content m-0">G-556677 is your Google verification code.</p>
</div>
"""

_TS_HTML = """
<div id="messages" style="width:100%; display:none">
 <hr class="hr-bottom-line">
 <div class="row col-sm-10 col-md-10 col-lg-10"><b>+5689</b></div>
 <div class="row col-sm-2 col-md-2 col-lg-2 date-padding">2 minutes ago - <span class="ud">2026-10-06</span></div>
 <div class="row col-md-8 text-left msg-padding">1 \u0162\u0127\u00ed\u0161 \u1e82\u1e43\u1e43\u0253\u1e15\u1e91 \u1e89\u1ead\u015b \u1e65\u0165\u1ed1\u013e\u1ebd\u044a \u1e9b\u0433\u1e93\u20b5 \u1e7b\u1eb5\u1e41\u0441-\u1e60M\u015e.\u1ec0\u1ec1\u0491 G-F9u0R6 is your Google verification code.</div>
 <hr class="hr-bottom-line">
 <div class="row col-sm-10 col-md-10 col-lg-10"><b>+7107</b></div>
 <div class="row col-sm-2 col-md-2 col-lg-2 date-padding">5 minutes ago - <span class="ud">2026-10-06</span></div>
 <div class="row col-md-8 text-left msg-padding">Your OTP is 445566 for login.</div>
</div>
"""

_orig_get = TN._get
GETS = []


def _fake_get(url, timeout=14):
    GETS.append(url)
    if "receivesms.co" in url:
        return 200, _RC_HTML
    if "receive-sms-free.cc" in url:
        return 200, _RSF_HTML
    if "temp-sms.org" in url:
        return 200, _TS_HTML
    return 404, ""


TN._get = _fake_get
try:
    TN._CACHE.clear()
    rc = TN.inbox("rc:us:22071", force=True)
    check("receivesms fixture: ok", bool(rc.get("ok")))
    check("receivesms: number nikal aaya", rc.get("number") == "18282768125", str(rc.get("number")))
    check("receivesms: 2 message parse hue", len(rc.get("messages") or []) == 2,
          str(len(rc.get("messages") or [])))
    check("receivesms: OTP code mila (343846)",
          (rc.get("messages") or [{}])[0].get("code") == "343846")
    check("receivesms: sender + time bhi aaya",
          (rc.get("messages") or [{}])[0].get("from") == "18335532731"
          and "minutes ago" in (rc.get("messages") or [{}])[0].get("time", ""))

    TN._CACHE.clear()
    rsf = TN.inbox("rsf:us:12543207584", force=True)
    check("receive-sms-free fixture: ok", bool(rsf.get("ok")))
    check("receive-sms-free: 2 message parse hue", len(rsf.get("messages") or []) == 2,
          str(len(rsf.get("messages") or [])))
    check("receive-sms-free: Yotta code 278080",
          any(m.get("code") == "278080" for m in (rsf.get("messages") or [])))
    check("receive-sms-free: Google 'G-556677' bhi pakda",
          any("556677" in (m.get("text") or "") for m in (rsf.get("messages") or [])))

    TN._CACHE.clear()
    ts = TN.inbox("ts:uk:447405247565", force=True)
    check("temp-sms fixture: ok", bool(ts.get("ok")))
    check("temp-sms: 2 message parse hue", len(ts.get("messages") or []) == 2,
          str(len(ts.get("messages") or [])))
    _t0 = (ts.get("messages") or [{}])[0].get("text", "")
    check("temp-sms: watermark homoglyph hata (asli text bacha)",
          "Google verification code" in _t0 and "\u1e90" not in _t0, _t0[:60])
    check("temp-sms: dusra message bina watermark jaisa hai",
          "445566" in ((ts.get("messages") or [{}] * 2)[1].get("text", ""))
          or any("445566" in (m.get("text") or "") for m in (ts.get("messages") or [])))
finally:
    TN._get = _orig_get

# =====================================================================
section("3) OTP extractor + bank detector + number formatting")
check("code: 'Your X verification code is: 278080' → 278080",
      TN.extract_code("Your Yotta verification code is: 278080. Don't share") == "278080")
check("code: '983447 is your verification code' → 983447",
      TN.extract_code("983447 is your verification code") == "983447")
check("code: '[WeChat] WeChat code (564344) may only be used once' → 564344",
      TN.extract_code("[WeChat] WeChat code (564344) may only be used once") == "564344")
check("code: plain text me kuch nahi", TN.extract_code("Hello, how are you?") == "")
check("code: 4-digit bhi pakadta hai", TN.extract_code("Rogervoice code 8424") == "8424")

check("bank: 'SBI bank OTP' pakda", TN.looks_banky("Your SBI bank OTP is 1234"))
check("bank: UPI pakda", TN.looks_banky("UPI payment of Rs.500 debited"))
check("bank: paytm/wallet pakda", TN.looks_banky("Paytm wallet KYC update karo"))
check("bank: aadhaar bhi red-flag", TN.looks_banky("Aadhaar OTP request"))
check("normal OTP bank nahi hai", not TN.looks_banky("[TikTok] 053663 is your verification code"))

check("format: 11-digit US pretty", TN.pretty_number("18282768125") == "+1 828-276-8125",
      TN.pretty_number("18282768125"))
check("format: +44 UK pretty", TN.pretty_number("447405247565") == "+44 7405 247565")
check("format: baaki desh simple +", TN.pretty_number("64211057037") == "+64211057037")

# =====================================================================
section("4) Pick logic — har user ko ALAG number (100% offline)")
_pool = [{"nid": f"x:{i}", "number": f"10000000{i}"} for i in range(6)]
_taken = set()
pick1 = TN.pick(_pool, _taken, uid=111)
_taken.add(pick1["nid"])
pick2 = TN.pick(_pool, _taken, uid=222)
_taken.add(pick2["nid"])
pick3 = TN.pick(_pool, _taken, uid=333)
check("3 alag users → 3 ALAG numbers",
      len({pick1["nid"], pick2["nid"], pick3["nid"]}) == 3)
check("same user + same inputs → wahi number (deterministic)",
      TN.pick(_pool, set(), uid=111)["nid"] == pick1["nid"])
check("avoid set kaam karta hai",
      TN.pick(_pool, set(), uid=111, avoid={pick1["nid"]})["nid"] != pick1["nid"])
check("khaali pool par None (crash nahi)", TN.pick([], set(), uid=1) is None)
_all_taken = {n["nid"] for n in _pool}
check("sab taken ho jayein to bhi number milta hai (share-safe, crash nahi)",
      TN.pick(_pool, _all_taken, uid=999) is not None)

# =====================================================================
section("5) Bot wiring — keyboard, mode, callback, rate-limit (FREE)")
_kb_labels = [bot.unbold(b) for row in bot.KB_BTNS for b in row]
check("keyboard me 'TEMP NUMBER' button hai (v74.4 naya naam)",
      any("TEMP NUMBER" in _l.upper() for _l in _kb_labels))
check("purana 'TEMP MAIL' 📧 (email) button bhi zinda hai (kuch delete nahi hua)",
      any("\U0001F4E7" in b and "TEMP MAIL" in bot.unbold(b).upper()
          for row in bot.KB_BTNS for b in row))
check("BTN_MODE_MAP: TEMP NUMBER → tnum (+ purana naam bhi chalta hai)",
      bot.BTN_MODE_MAP.get("TEMP NUMBER") == "tnum"
      and bot.BTN_MODE_MAP.get("TEMP MAIL (NUMBER)") == "tnum")
check("BTN_MODE_MAP: TEMP MAIL (email) abhi bhi tempmail par", bot.BTN_MODE_MAP.get("TEMP MAIL") == "tempmail")
check("tnum FREE hai — PREMIUM_TOOLS me NAHI",
      "tnum" not in bot.PREMIUM_TOOLS)
check("premium count same (29) — free tool se nahi badla",
      len(bot.PREMIUM_TOOLS) == 29, str(len(bot.PREMIUM_TOOLS)))
check("rate-limit entry hai (25 / 300s)", bot.TOOL_RATE_LIMITS.get("tnum") == (25, 300, "Temp Mail (Number)"),
      str(bot.TOOL_RATE_LIMITS.get("tnum")))
check("VIP wall par bhi tool khula rehta hai (vip_free_cb)", bot.vip_free_cb("tnum_open"))
check("action dispatch me tnum hai", 'if action == "tnum":' in BOT_SRC)
check("callbacks: open/svc/ctry/refresh/change sab wired",
      all(x in BOT_SRC for x in ('"tnum_open"', 'startswith("tnum_svc:")',
                                 'startswith("tnum_ctry:")', '"tnum_refresh"', '"tnum_change"')))
check("credit / VIP wall wala line tnum ke liye NAHI hai (100% free)",
      'get_credits_over_text("tnum")' not in BOT_SRC)
check("assignment meta-store use hota hai (v2 — fresh numbers)",
      'TNUM_META_KEY = "tnum_assign_v2"' in BOT_SRC and "meta_get(TNUM_META_KEY" in BOT_SRC)

_p = bot.TNUM_INTRO
# v74.4: intro ab 3 line ka — koi gyaan/warning nahi (user ka rule #2)
check("intro card chhota hai (koi gyaan nahi)",
      len(_p.splitlines()) <= 4 and "BANK" not in _p.upper() and "100% FREE" not in _p)
check("intro me seedha desh chunne ki baat", "Desh chuno" in _p)
check("intro card me koi moti line (━) nahi — patli lines only",
      "━" not in _p and "─" in _p)
check("card title v102 header style (plain + ━)",
      "<b>TEMP NUMBER</b>" in bot.tnum_card({"cc": "us"}, {"ok": True, "number": "1", "messages": []})
      and "┏" not in bot.tnum_card({"cc": "us"}, {"ok": True, "number": "1", "messages": []}))

# =====================================================================
section("6) Assignment engine — 6 users, owner sab ALAG (mock pool, offline)")
_orig_pool, _orig_inbox = TN.pool, TN.inbox
_MOCK = {"ok": True, "numbers": [{"nid": f"rc:us:{i}", "cc": "us", "number": f"1555000{i:04d}",
                                  "display": f"+1 555-000-{i:04d}", "src": "rc"} for i in range(8)],
         "notes": ["mock"]}
TN.pool = lambda cc, refresh=False: (_MOCK if cc == "us"
                                    else {"ok": False, "error": "Ye desh support me nahi hai."})
TN.inbox = lambda nid, ttl=12.0, force=False: {"ok": True, "nid": nid, "number": nid.split(":")[-1],
                                               "display": "", "messages": [], "last_activity": "",
                                               "count24": 0, "cached": False}
try:
    bot._tnum_save({})                       # saaf slate
    users = [111111, 222222, 333333, 444444, 555555, 999999]   # 999999 = owner-style alag id
    nids = []
    for u in users:
        rec, err = bot.tnum_get_number(u, "us", "whatsapp")
        check(f"user {u}: number mila ({err or 'ok'})", bool(rec and rec.get("nid")))
        nids.append((rec or {}).get("nid"))
    check("6 users → 6 ALAG numbers (koi repeat nahi)", len(set(nids)) == 6, str(nids))
    r_again, _ = bot.tnum_get_number(111111, "us", "whatsapp")
    check("dobara maangne par WAHI number (stable)", r_again.get("nid") == nids[0])
    r_ch, _ = bot.tnum_get_number(111111, "us", "whatsapp", change=True)
    check("'Doosra number' naya deta hai", r_ch.get("nid") != nids[0], str(r_ch.get("nid")))
    r_bad, e_bad = bot.tnum_get_number(777777, "zz", "whatsapp")
    check("galat desh par crash nahi — saaf error", r_bad is None and bool(e_bad), str(e_bad))
    _store = bot._tnum_load()
    check("assignment store me sab record hai (6 users)", len(_store) >= 6, str(len(_store)))
finally:
    TN.pool, TN.inbox = _orig_pool, _orig_inbox

# =====================================================================
section("7) Card render — offline (code highlight + warnings + null-safety)")
_card = bot.tnum_card(
    {"cc": "de", "num": "4915510376239", "dis": "+49 15510 376239", "svc": "google",
     "since": []},
    {"ok": True, "number": "4915510376239",
     "messages": [{"from": "Google", "time": "19 minutes ago",
                   "text": "G-875371 is your Google verification code.", "code": "875371"},
                  {"from": "SBI", "time": "1 min ago",
                   "text": "SBI bank OTP 998877 for UPI", "code": "998877"}],
     "last_activity": "19 minutes ago", "count24": 510})
check("card me number dikhta hai", "+4915510376239" in _card)
check("card me OTP code dikhta hai", "<code>875371</code>" in _card)
# v74.4: safety/gyaan lines hata di gayi (user ka rule #2 — sirf outcome)
check("card me koi safety/warning line nahi (sirf outcome)",
      "⛔" not in _card and "PUBLIC" not in _card.upper()
      and not hasattr(bot, "TNUM_SAFE_LINE"))
check("card never empty (khaali inbox par bhi body hai)",
      len(bot.tnum_card({"cc": "us"}, {"ok": True, "number": "1", "messages": []})) > 120)
check("inbox fail par saaf line aati hai (khaali card nahi)",
      "nahi khula" in bot.tnum_card({"cc": "us"}, {"ok": False, "error": "site slow"}))
check("card me ━ divider (v102 style)", "━" in _card)


# =====================================================================
section("8) E2E — nakli Telegram par poora flow (offline, koi network nahi)")
import asyncio                                                     # noqa: E402


class _QMsg:
    def __init__(self):
        self.chat = type("C", (), {"id": 4242})()
        self.chat_id = 4242
        self.message_id = 1
        self.out = []

    async def edit_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return self


class _Q:
    def __init__(self, data, uid):
        self.data = data
        self.from_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.message = _QMsg()
        self.alerts = []

    async def answer(self, text=None, show_alert=False):
        self.alerts.append(text)


class _Upd:
    def __init__(self, q):
        self.callback_query = q
        self.effective_user = q.from_user
        self.effective_chat = q.from_user


class _Ctx:
    def __init__(self):
        self.user_data = {}
        self.bot = object()


_orig_pool2, _orig_inbox2 = TN.pool, TN.inbox
_MOCK2 = {"ok": True, "numbers": [{"nid": f"rc:us:{i}", "cc": "us", "number": f"1555123{i:04d}",
                                   "display": f"+1 555-123-{i:04d}", "src": "rc"} for i in range(5)],
          "notes": ["mock"]}
_CALLS = {"n": 0}


def _fake_inbox2(nid, ttl=12.0, force=False):
    """v71.10: pehla call = assignment baseline (khaali), phir naya SMS aata hai."""
    _CALLS["n"] += 1
    if _CALLS["n"] <= 1:
        msgs = []                          # assignment ke waqt inbox khaali tha
    else:
        msgs = [{"from": "WhatsApp", "time": "1 min ago",
                 "text": "Your WhatsApp code is 445566. Don't share this code.",
                 "code": "445566"}]
    return {"ok": True, "number": "15551230000", "display": "+1 555-123-0000",
            "messages": msgs, "last_activity": "1 min ago", "count24": 7,
            "cached": False}


TN.pool = lambda cc, refresh=False: _MOCK2 if cc == "us" else {"ok": False, "error": "support nahi"}
TN.inbox = _fake_inbox2


async def _run_flow():
    ctx = _Ctx()
    uid = 424242
    q1 = _Q("tnum_open", uid)
    await bot.on_cb(_Upd(q1), ctx)
    a = q1.message.out[-1] if q1.message.out else ""
    check("E2E open: intro chhota (koi gyaan nahi)",
          "Desh chuno" in a and "BANK" not in a.upper())
    check("E2E open: services keyboard me WhatsApp hai",
          any("whatsapp" in (b.callback_data or "") for r in bot._tnum_svc_kb().inline_keyboard for b in r))

    q2 = _Q("tnum_svc:whatsapp", uid)
    await bot.on_cb(_Upd(q2), ctx)
    a2 = q2.message.out[-1] if q2.message.out else ""
    check("E2E service chuna: desh list aayi (STEP 2)", "DESH CHUNO" in bot.unbold(a2))
    check("E2E service chuna: context me svc save hua", ctx.user_data.get("tnum_svc") == "whatsapp")

    q3 = _Q("tnum_ctry:us", uid)
    await bot.on_cb(_Upd(q3), ctx)
    a3 = q3.message.out[-1] if q3.message.out else ""
    check("E2E desh chuna: number card aaya", "Aapka number" in a3)
    check("E2E desh chuna: naya OTP card me hai (6-digit)", "<code>445566</code>" in a3)
    check("E2E desh chuna: card me koi safety line nahi", "KYC" not in a3.upper())
    _rec = bot._tnum_load().get(str(uid)) or {}
    check("E2E desh chuna: number store ho gaya", bool(_rec.get("nid")), str(_rec.get("nid")))

    q4 = _Q("tnum_refresh", uid)
    await bot.on_cb(_Upd(q4), ctx)
    a4 = q4.message.out[-1] if q4.message.out else ""
    check("E2E refresh: card dobara aaya (crash nahi)", "Aapka number" in a4)

    q5 = _Q("tnum_change", uid)
    ctx.user_data["tnum_last_ref"] = 0
    await bot.on_cb(_Upd(q5), ctx)
    a5 = q5.message.out[-1] if q5.message.out else ""
    _rec2 = bot._tnum_load().get(str(uid)) or {}
    check("E2E doosra number: naya number mila",
          "Aapka number" in a5 and _rec2.get("nid") != _rec.get("nid"),
          f"{_rec.get('nid')} -> {_rec2.get('nid')}")

    q6 = _Q("tnum_countries", uid)
    await bot.on_cb(_Upd(q6), ctx)
    a6 = q6.message.out[-1] if q6.message.out else ""
    check("E2E desh badlo: list wapas aayi", "DESH CHUNO" in bot.unbold(a6))

    q7 = _Q("tnum_ctry:zz", uid)
    await bot.on_cb(_Upd(q7), ctx)
    a7 = q7.message.out[-1] if q7.message.out else ""
    check("E2E galat desh: crash nahi, saaf message", "Number nahi mila" in a7, a7[:80])


try:
    asyncio.run(_run_flow())
finally:
    TN.pool, TN.inbox = _orig_pool2, _orig_inbox2

print(f"\n{'=' * 62}")
print(f"  v73 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
