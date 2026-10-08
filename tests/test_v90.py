# -*- coding: utf-8 -*-
"""
v90 SELFTEST — 🔐 FORCE-JOIN WALL (modules/core/joinwall.py) — sab OFFLINE.

User ki hiring: "Force join gate banao". Ye file wall ke wo behaviours lock
kartī hai jo live par dikhte nahi, par galat ho to sabse bura lagta hai:
  A. channel normalize + link fallback (numeric id par galat URL na bane)
  B. kaun allowed: creator/administrator/member = haan; left/kicked/restricted
     = nahi; **har exception par fail-open** (user kabhi lock na ho — ye design
     hai, kyunki ek galat block = hamesha ka khoya user)
  C. cache: "haan" 12 ghante, "nahi" 45 second, aur bounded (Render 512 MB)
  D. gate/handle_check + bot.py ki wiring (fj:check gate SE PEHLE chale)
"""
import asyncio
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v90_tmp.db"))

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


from modules.core import joinwall as JW                                       # noqa: E402

_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
_jw = open(os.path.join(_ROOT, "modules", "core", "joinwall.py"), encoding="utf-8").read()


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ------------------------------------------------------------------ fakes
class _M:
    def __init__(self, status):
        self.status = status


class _Bot:
    """Fake PTB Bot: get_chat_member ka jawab control me, bheje message record."""

    def __init__(self, status="member", raises=None):
        self.status, self.raises, self.calls, self.sent = status, raises, 0, []

    async def get_chat_member(self, chat_id=None, user_id=None):
        self.calls += 1
        if self.raises:
            raise self.raises
        return _M(self.status)

    async def send_message(self, **kw):
        self.sent.append(kw)
        return object()


class _Ctx:
    def __init__(self, status="left", raises=None):
        self.bot = _Bot(status, raises)

    @property
    def msgs(self):
        return self.bot.sent


class _Msg:
    def __init__(self):
        self.edits = []
        self.chat_id = 4242

    async def edit_text(self, *a, **kw):
        # safesend kwargs bhejta hai (text=…, parse_mode=…) — dono case record
        shown = str(a) + str({k: v for k, v in kw.items() if k != "reply_markup"})
        self.edits.append((shown, kw))
        return object()


class _Q:
    def __init__(self, data="x"):
        self.data = data
        self.answers = []
        self.message = _Msg()

    async def answer(self, *a, **kw):
        self.answers.append((a, kw))
        return True


class _Upd:
    def __init__(self, uid=5001, pvt=True, data="menu", cb=True):
        self.callback_query = _Q(data) if cb else None
        self.effective_user = type("U", (), {"id": uid})()
        self.effective_chat = type("C", (), {"id": uid,
                                             "type": "private" if pvt else "group"})()
        self.message = None


def _env(**kw):
    for k, v in kw.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)


def _wall(**kw):
    """Wall ON, owner 8607774564, koi extra exempt nahi — standard setup."""
    _env(FORCE_CHANNEL="@CypherGrid", FORCE_CHANNEL_LINK="https://t.me/CypherGrid",
         FORCE_JOIN="on", ADMIN_ID="8607774564", ADMINS="", FORCE_JOIN_EXEMPT="",
         FORCE_JOIN_OK_HOURS=kw.get("ok_h", 12))
    JW.reset()


_wall()

# ================================================== A. config / normalize
check("normalize: '@CypherGrid' jaisa hai", JW.normalize_channel("@CypherGrid") == "@CypherGrid")
check("normalize: 'CypherGrid' → '@CypherGrid'", JW.normalize_channel("CypherGrid") == "@CypherGrid")
check("normalize: 'https://t.me/CypherGrid' → '@CypherGrid'",
      JW.normalize_channel("https://t.me/CypherGrid") == "@CypherGrid")
check("normalize: 't.me/CypherGrid/' trailing slash sab handle",
      JW.normalize_channel("t.me/CypherGrid/") == "@CypherGrid")
check("normalize: numeric id → int (Bot API ko -100… int chahiye)",
      JW.normalize_channel("-1004331054356") == -1004331054356)
check("numeric id ka type int hai (string bhejo to Telegram 400 deta hai)",
      isinstance(JW.normalize_channel("-1004331054356"), int))
check("normalize: khaali → khaali", JW.normalize_channel("   ") == "")
check("link khaali ho to @name se banata hai",
      (_env(FORCE_CHANNEL_LINK=""), JW.link() == "https://t.me/CypherGrid"))
_env(FORCE_CHANNEL_LINK="https://t.me/CypherGrid")
check("channel set + FORCE_JOIN=on → wall ON", JW.enabled() is True)
_env(FORCE_JOIN="off")
check("FORCE_JOIN=off = kill switch (wall foran band)", JW.enabled() is False)
_env(FORCE_JOIN="auto", FORCE_CHANNEL="")
check("channel khaali = wall band (aap galti se sabko lock na kar do)",
      JW.enabled() is False)
_env(FORCE_JOIN="auto", FORCE_CHANNEL="@CypherGrid")
check("mode 'auto' (default) bhi wall chalata hai jab channel set ho",
      JW.enabled() is True)
_env(FORCE_CHANNEL="-1004331054356", FORCE_CHANNEL_LINK="")
check("numeric-id mode: link khali rahe (galat channel par na le jaye)", JW.link() == "")
_kb = JW.wall_kb()
check("…par 'check karo' button phir bhi mile (wall bekaar na ho)",
      _kb.inline_keyboard[-1][0].callback_data == "fj:check")
_cb_data = [b.callback_data for r in _kb.inline_keyboard for b in r if b.callback_data]
check("wall ka sirf EK callback button (fj:check) — koi bypass ka hole nahi",
      _cb_data == ["fj:check"], str(_cb_data))
check("wall ke buttons me se koi bhi 'menu' callback nahi bhejta (dead button = 0)",
      all("menu" != (b.callback_data or "") for r in JW.wall_kb().inline_keyboard for b in r))
_env(FORCE_CHANNEL="@CypherGrid", FORCE_CHANNEL_LINK="https://t.me/CypherGrid")
_kb2 = JW.wall_kb()
check("username mode me '🔗 Channel join karo' URL button bhi hai",
      _kb2.inline_keyboard[0][0].url == "https://t.me/CypherGrid")
check("wall text me channel ka naam + link dikhē (user ko samajh aaye)",
      "@CypherGrid" in JW.wall_text() and "https://t.me/CypherGrid" in JW.wall_text())
check("wall text me 🎬 / .mp4 nahi (v80 ka 'tutorial hatao' rule)",
      "🎬" not in JW.wall_text() and ".mp4" not in JW.wall_text())
check("health line bina crash (aap /health se ON/OFF dekh sako)",
      "join-wall:" in JW.health_line())

# ================================================== B. kaun allowed hai
_env(FORCE_JOIN_OK_HOURS="12")
for st, want in (("creator", True), ("administrator", True), ("member", True),
                 ("restricted", False), ("left", False), ("kicked", False)):
    JW.reset()
    check(f"Telegram status '{st}' → allowed={want}",
          _run(JW.allowed(_Bot(st), 7001)) is want, st)
JW.reset()
check("Telegram error → FAIL-OPEN (wall kabhi user ko na baandhe)",
      _run(JW.allowed(_Bot(raises=Exception("chat not found")), 7002)) is True)
check("…aur wo error gina bhi (aap /health me dekh sako)", JW.stats()["errors"] >= 1)
JW.reset()
check("bot ko channel ka admin banana zaroori — health line ye warning deti hai",
      "⚠️" not in JW.health_line() or "getChatMember" in JW.health_line())
check("admin/creator bhi allowed (wo to channel ke maalik hi hain)",
      _run(JW.allowed(_Bot("administrator"), 7003)) is True)
JW.reset()
_env(FORCE_JOIN="off")
check("wall OFF → koi API punch nahi (bekaar ka round-trip = latency)",
      _run(JW.allowed(_Bot("left"), 7004)) is True and _Bot("left").calls == 0)
_env(FORCE_JOIN="on")

# ================================================== C. exempt list
_wall()
check("owner (ADMIN_ID) exempt — wall khud use kabhi na pakde",
      JW.exempt(8607774564) is True)
_env(ADMINS="111, 222")
check("ADMINS ke log exempt (array support)", JW.exempt(111) is True and JW.exempt(222) is True)
_env(FORCE_JOIN_EXEMPT="333,444")
check("FORCE_JOIN_EXEMPT se test-user exempt (aap bina join test kar sako)",
      JW.exempt(333) is True and JW.exempt(444) is True)
check("aam user exempt NAHI", JW.exempt(9999) is False)
_env(ADMIN_ID="", ADMINS="", FORCE_JOIN_EXEMPT="")
check("ADMIN_ID khaali/galat ho to bhi exempt kaam kare (ValueError na uthe)",
      JW.exempt(1234) is False)
_wall()

# ================================================== D. cache
b = _Bot("member")
_run(JW.allowed(b, 8001))
_run(JW.allowed(b, 8001))
_run(JW.allowed(b, 8001))
check("'haan' cache hota hai → baaki calls me Telegram ko dobara nahi poochta",
      b.calls == 1, f"calls={b.calls}")
b2 = _Bot("left")
_run(JW.allowed(b2, 8002))
_run(JW.allowed(b2, 8002))
check("'nahi' bhi chhota cache (45 s) — har message par 2 API calls na ho (phela)",
      b2.calls == 1, f"calls={b2.calls}")
JW._cache[8002] = (False, time.time() - 60)      # 45 s se zyada purana
_run(JW.allowed(b2, 8002))
check("45 s baad dobara poochta hai (varna join karne ke baad 'check karo' kaam na kare)",
      b2.calls == 2, f"calls={b2.calls}")
JW._cache[8003] = (True, time.time() + 999)
check("cache me 'haan' = allowed foran (API call 0) — hot path fast",
      _run(JW.allowed(_Bot("left"), 8003)) is True)
JW.reset()
for i in range(JW._CACHE_MAX + 200):
    JW._put(200000 + i, True)
check(f"cache bounded ({JW._CACHE_MAX} entries) — 512 MB par leak nahi",
      len(JW._cache) <= JW._CACHE_MAX, str(len(JW._cache)))
JW.reset()
check("reset() = wall ka memory saaf (aap FORCE_JOIN=off/on ke saath test kar sako)",
      len(JW._cache) == 0)

# ================================================== E. gate behaviour
ctx = _Ctx("left")
check("aam user, channel ka member NAHI → gate False (tool nahi chalega)",
      _run(JW.gate(_Upd(uid=9001), ctx)) is False)
check("…aur use wall dikhi (message bheja)", len(ctx.msgs) == 1)
check("wall me URL button + check button dono hain",
      "fj:check" in str(ctx.msgs[0]) and "https://t.me/CypherGrid" in str(ctx.msgs[0]))
_wall()
_cw = _Ctx("left")
_run(JW.gate(_Upd(uid=9031), _cw))
_wb = _cw.msgs[0].get("reply_markup") if _cw.msgs else None
check("bheji gayi wall ka markup me koi 'menu' callback nahi (wall tod ke andar na ghusé)",
      _wb is not None and "menu" not in str(_wb.inline_keyboard))
check("blocked ginता", JW.stats()["blocked"] >= 1)
ctx2 = _Ctx("member")
_run(JW.gate(_Upd(uid=9002), ctx2))
check("member → gate True aur koi wall nahi (10 lakh users ko spam na ho)",
      not ctx2.msgs)
check("allowed ginता", JW.stats()["allowed"] >= 1)
ctx3 = _Ctx("left")
check("GROUP chat me wall NAHI (private-only — beizzati + spam se bachna)",
      _run(JW.gate(_Upd(uid=9003, pvt=False), ctx3)) is True and not ctx3.msgs)
ctx4 = _Ctx("left")
check("owner exempt → gate True, wall nahi",
      _run(JW.gate(_Upd(uid=8607774564), ctx4)) is True and not ctx4.msgs)
check("exempt ginता", JW.stats()["exempt"] >= 1)
ctx5 = _Ctx("left")
ctx5.bot.raises = Exception("boom")
check("Telegram hi fail ho jaye to user KO allow (fail-open) — wall kabhi jail na bane",
      _run(JW.gate(_Upd(uid=9005), ctx5)) is True and not ctx5.msgs)
check("context/ bot na mile → allow (kabhi lock nahi)",
      _run(JW.gate(_Upd(uid=9006), None)) is True)
_env(FORCE_JOIN="off")
ctx7 = _Ctx("left")
check("kill switch se gate hamesha True (aap 1 env var se pura gate band)",
      _run(JW.gate(_Upd(uid=9007), ctx7)) is True and not ctx7.msgs)
_wall()

# ================================================== F. 'check karo' button
u = _Upd(uid=9011, data="fj:check")
c = _Ctx("member")
_ret = _run(JW.handle_check(u, c))
check("member mila → handle_check True batata hai (bot ab menu bhejta hai)", _ret is True)
check("join ke baad 'check karo' → wall wala message hi EDIT hua (naya message flood nahi)",
      bool(u.callback_query.message.edits), str(u.callback_query.message.edits)[:60])
_ed = u.callback_query.message.edits[0] if u.callback_query.message.edits else ("", {})
check("…text me 'Ho gaya' welcome hai", "Ho gaya" in _ed[0])
check("…aur koi DEAD button nahi lagaya (bot 'menu' callback handle nahi karta isliye)",
      _ed[1].get("reply_markup") is None)
check("spinner band hone ke liye answer() chala", bool(u.callback_query.answers))
check("edit HTML me hua (safe_edit ka parse_mode)", _ed[1].get("parse_mode") == "HTML")
check("joins ginता (aap dekh sako kitne log wall se channel me ghusé)",
      JW.stats()["joins"] >= 1)
u2 = _Upd(uid=9012, data="fj:check")
c2 = _Ctx("left")
_ret2 = _run(JW.handle_check(u2, c2))
check("abhi bhi member nahi → False + koi jhootha 'Ho gaya' edit nahi",
      _ret2 is False and not u2.callback_query.message.edits)
check("…user ko alert me saaf bola 'nahi dikhe'",
      any("nahi" in str(x) for x in u2.callback_query.answers),
      str(u2.callback_query.answers)[:80])
u3 = _Upd(uid=9013, data="fj:check")
c3 = _Ctx("left")
_run(JW.handle_check(u3, c3))
check("'check karo' ke baad cache 'nahi' se update (baar-baar tap = API spam nahi)",
      JW._cache.get(9013, (None,))[0] is False)
check("joinwall me koi dead 'menu' callback button nahi",
      'callback_data=\"menu\"' not in _jw and "done_kb" not in _jw)
check("DONE_TEXT me tool-list wala waada hai (user ko pata chale ki bot khul gaya)",
      "bot khula hai" in JW.DONE_TEXT)
check("handle_check bina callback_query ke chup-chaap False (crash nahi)",
      _run(JW.handle_check(_Upd(uid=9014, cb=False), _Ctx("member"))) is False)

# ================================================== G. bot.py wiring
_st = _SRC.split("async def cmd_start")[1].split("\nasync def ")[0]
check("/start par gate hai", "JW.gate(update, context)" in _st)
check("…ban check ke BAAD (ban = block, wall se pehle)",
      _st.index("is_banned") < _st.index("JW.gate"))
check("…referral credit wall se PEHLE capture hota hai (user wall par atke to ref na kho)",
      _st.index('startswith("ref_")') < _st.index("JW.gate"))
check("gate welcome banner bhejne se PEHLE hai (blocked user ko menu na mile)",
      _st.index("JW.gate") < _st.index("global _WELCOME_FID"))
_cbw = _SRC.split("async def _on_cb_pro")[1].split("\nasync def ")[0]
check("callback wrapper me 'fj:' gate SE PEHLE handle hota hai",
      "startswith(\"fj:\")" in _cbw and _cbw.index("fj:") < _cbw.index("JW.gate"))
check("…aur gate pass na ho to return (tool ke callback na chalein)",
      "if not await JW.gate(update, context):\n        return" in _cbw)
_txw = _SRC.split("async def _on_text_pro")[1].split("\nasync def ")[0]
check("text wrapper par bhi gate (bina menu ke text se tool kholne ka hole band)",
      "JW.gate(update, context)" in _txw)
_fjb = _cbw.split('startswith("fj:")')[1].split("return")[0]
check("join hone par bot APNA asli menu bhejta hai (WELCOME_TEXT + kb_for — nayi copy nahi)",
      "WELCOME_TEXT" in _fjb and "kb_for(" in _fjb)
check("…menu ek hi baar jaaye (dobara tap par flood nahi)", "_fj_menu" in _fjb)
check("…aur menu ka send fail ho to bhi callback crash na ho (try/except)",
      "except Exception" in _fjb)
check("joinwall import hai", "from modules.core import joinwall as JW" in _SRC)
check("/health me join-wall ki line (ON/OFF + kitne block hue)",
      "<p style='font-family:monospace'>{JW.health_line()}</p>" in _SRC)
check("gate ke 3i sites: /start + callback + text (ek bhi chhuta ho to hole)",
      _SRC.count("JW.gate(update, context)") == 3)
check("joinwall me koi 🎬/toolvid/open_refer nahi (purana kachra wapas na aaye)",
      "🎬" not in _jw and "toolvid" not in _jw and "open_refer" not in _jw)
check("joinwall safe_* layer use karta hai (send fail ho to crash na ho)",
      "safe_send_text" in _jw and "safe_answer_cb" in _jw and "safe_edit" in _jw)
check("cache bounded implementation me trim hai", "_cache.pop(" in _jw and "_CACHE_MAX" in _jw)
check("fail-open comment code me likha hai (bhagwan na koi ise 'fix' kar de)",
      "fail-open" in _jw)

print("\n" + "=" * 62)
print(f"  v90 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAILS:
    print("-" * 62)
    for _f in FAILS[:40]:
        print("   ❌ " + _f)
print("=" * 62)
sys.exit(1 if FAIL else 0)
