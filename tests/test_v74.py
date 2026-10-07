# -*- coding: utf-8 -*-
"""
v74 SELFTEST — 📞 TEMP MAIL (NUMBER) v2 — "sirf mera naya OTP" upgrade
=======================================================================
User ka order (7 Oct, screenshot ke saath):
  • "pichla message sab delete karo, fresh number laao"
  • "sirf mera OTP rahe — dusra kisi ka nahi"
  • "jab koi OTP giraaye tabhi dikhe — purane OTP nahi"
  • "WhatsApp chuna hai to 6 digit OTP aaye, 4 digit nahi"
  • "otp system upgrade karo — best service ke accordingly"
  • "sirf mere bot/service ke OTP aaye, other websites ka nahi"

Sab kuch 100% OFFLINE test hota hai (koi network call nahi).
"""
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv74_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V74"
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
print("  v74 SELFTEST — TEMP MAIL (NUMBER) v2 — sirf NAYA + sahi-service OTP")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import temp_number as TN                             # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

# =====================================================================
section("1) Service rules — har app ka apna OTP rule (16/16)")
check("SVC_RULES me har service ka rule hai",
      all(s[0] in TN.SVC_RULES for s in TN.SERVICES),
      [s[0] for s in TN.SERVICES if s[0] not in TN.SVC_RULES])
check("har rule me kw + lens + hint hai",
      all(r.get("kw") and r.get("lens") and r.get("hint") for r in TN.SVC_RULES.values()))
check("WhatsApp = 6 digit (user ka example)", TN.SVC_RULES["whatsapp"]["lens"] == (6,))
check("Telegram = 5/6 digit (Telegram ka OTP 5 hota hai)",
      5 in TN.SVC_RULES["telegram"]["lens"])
check("Netflix = 4/6 (Netflix 4-digit bhejta hai)", TN.SVC_RULES["netflix"]["lens"] == (4, 6))
check("svc_hint kaam karta hai", "6 digit" in TN.svc_hint("whatsapp"))
check("unknown service pe hint fallback", TN.svc_hint("nope") == "4-6 digit")

# =====================================================================
section("2) Smart OTP extraction — sahi lambai, phone/URL ignore")
check("WhatsApp 6-digit (hyphen): '123-456' → 123456",
      TN.extract_code_svc("Your WhatsApp code is 123-456. Don't share this code.",
                          "whatsapp") == "123456")
check("WhatsApp 6-digit plain", TN.extract_code_svc("Your WhatsApp code is 445566.", "whatsapp") == "445566")
check("WhatsApp par 4-digit REJECT (user ka order: 4 digit nahi chahiye)",
      TN.extract_code_svc("Your WhatsApp code is 8424", "whatsapp") == "")
check("Google 'G-875371' → 875371",
      TN.extract_code_svc("G-875371 is your Google verification code.", "google") == "875371")
check("Telegram 5-digit → 12345",
      TN.extract_code_svc("Telegram code: 12345", "telegram") == "12345")
check("Instagram 6-digit", TN.extract_code_svc("123456 is your Instagram code", "instagram") == "123456")
check("phone number code nahi samjha jata (828-276-8125 ignore)",
      TN.extract_code_svc("Your WhatsApp code is 445566. Call +1 828-276-8125", "whatsapp") == "445566")
check("URL ke andar ka number ignore (kinobu link case)",
      TN.extract_code_svc("reply at https://staging.kinobu.app/n/b7d568705d9342", "whatsapp") == "")
check("Google alnum code 'G-F9u0R6' → F9u0R6 (yehi asli code hota hai)",
      TN.extract_code_svc("G-F9u0R6 is your Google verification code.", "google") == "F9u0R6")
check("Google par galti se G- prefix code nahi banta",
      "G-" not in TN.extract_code_svc("G-F9u0R6 is your Google verification code.", "google"))
check("unknown service par generic extractor chalta hai (backward-compat)",
      TN.extract_code_svc("Your verification code is 278080", "") == "278080")
check("purana extract_code() waise hi hai (kuch nahi toota)",
      TN.extract_code("Your Yotta verification code is: 278080") == "278080")

check("code_len_note: 4-digit par saaf batata hai",
      "4 digit" in TN.code_len_note("Your WhatsApp code is 8424", "whatsapp"))
check("code_len_note: sahi 6-digit par kuch nahi bolta",
      TN.code_len_note("Your WhatsApp code is 445566", "whatsapp") == "")

# =====================================================================
section("3) Service filter — sirf chuni app ka SMS dikhega")
check("WhatsApp SMS match", TN.service_match({"from": "WhatsApp", "text": "code 123-456"}, "whatsapp"))
check("WhatsApp SMS text me bhi match",
      TN.service_match({"from": "5551212", "text": "Your WhatsApp code is 445566"}, "whatsapp"))
check("dusri site ka SMS WhatsApp par match NAHI",
      not TN.service_match({"from": "SoulChill", "text": "Verification code: 875371"}, "whatsapp"))
check("Google SMS google par match",
      TN.service_match({"from": "Google", "text": "G-123456 is your Google verification code"}, "google"))
check("X/Twitter SMS", TN.service_match({"from": "X", "text": "Your X confirmation code is 123456"}, "twitter"))
check("service pata na ho to sab pass (fallback)",
      TN.service_match({"from": "X", "text": "hello"}, ""))

# =====================================================================
section("4) Watermark cleaner — screenshot wala junk hatata hai")
_shot = ("1 \u1e6a\u210f\u0390\u0161 \u1e82\u1e43\u1e43\u0253\u1e15\u1e91 "
         "\u1e89\u1ead\u015b \u1e65\u0165\u1ed1\u013e\u1ebd\u044a \u1e9b\u0433\u1e93\u20b5 "
         "\u1e7b\u1eb5\u1e41\u0441-\u1e60M\u015e.\u1ec0\u1ec1\u0491 "
         "G-DtQ5 h is your Google verification code.")
_c1 = TN._dedupe_watermark(_shot)
check("watermark wale SMS se asli text bacha", "Google verification code" in _c1, _c1[:70])
check("watermark ka nishaan gaya (non-ascii junk nahi)", "\u1e60" not in _c1 and "\u1e6a" not in _c1)
check("cleaner saaf text ko chedta nahi",
      TN._dedupe_watermark("Your WhatsApp code is 445566.") == "Your WhatsApp code is 445566.")
check("Hindi text ko jail me nahi daalta",
      "\u0906\u092a\u0915\u093e" in TN._dedupe_watermark("\u0906\u092a\u0915\u093e OTP 123456 \u0939\u0948"))
check("khaali text par crash nahi", TN._dedupe_watermark("") == "")

# =====================================================================
section("5) 'Naya vs purana' engine — sirf naya OTP (user ka order)")
_m_old = {"from": "22395", "time": "3 hour ago", "text": "Your Google code is 111111", "code": "111111"}
_m_new = {"from": "WhatsApp", "time": "1 min ago", "text": "Your WhatsApp code is 445566", "code": "445566"}
_m_junk = {"from": "SoulChill", "time": "2 min ago", "text": "Verification code: 875371", "code": "875371"}
_since = TN.snapshot([_m_old])
check("msg_fp deterministic", TN.msg_fp(_m_old) == TN.msg_fp(dict(_m_old)))
check("alag messages ki alag fingerprint", TN.msg_fp(_m_old) != TN.msg_fp(_m_new))
show, hidden, total = TN.fresh_and_matched([_m_old, _m_new, _m_junk], _since, "whatsapp")
check("purana SMS nahi dikhta (baseline me tha)", _m_old not in show)
check("naya WhatsApp OTP dikhta hai", _m_new in show and len(show) == 1)
check("dusri site wala naya SMS chhupa (hidden=1)", hidden == 1, str(hidden))
check("total naye = 2", total == 2, str(total))
show2, _, _ = TN.fresh_and_matched([_m_old, _m_new], [], "whatsapp")
check("baseline khaali ho to sab naye maane jate hain (service match ke saath)",
      _m_new in show2 and len(show2) == 1)
check("recency: '17 minutes ago' → 17", TN.recency_min("17 minutes ago") == 17.0)
check("recency: '1 hour ago' → 60", TN.recency_min("1 hour ago") == 60.0)
check("recency: '2 minutes 5 seconds ago' → 2", TN.recency_min("2 minutes 5 seconds ago") == 2.0)

# =====================================================================
section("6) Source priority — saaf source pehle (watermark wala aakhir me)")
_pool_mix = ([{"nid": f"rc:us:{i}", "src": "rc", "number": f"1555000{i}", "cc": "us"} for i in range(4)]
             + [{"nid": f"ts:us:{i}", "src": "ts", "number": f"1444000{i}", "cc": "us"} for i in range(4)])
_picked = [TN.pick(_pool_mix, taken=set(), uid=u)["src"] for u in (1, 2, 3, 4, 5)]
check("mix pool me sabko rc (saaf source) mila", set(_picked) == {"rc"}, str(_picked))
_picked_ts = [TN.pick([n for n in _pool_mix if n["src"] == "ts"], taken=set(), uid=u)["src"]
              for u in (1, 2, 3)]
check("rc na ho to ts chalta hai (achha fallback)", set(_picked_ts) == {"ts"})
_uids = [11, 22, 33, 44, 55, 66]
_nids = {TN.pick(_pool_mix, taken=set(), uid=u)["nid"] for u in _uids}
check("6 alag users → alag-alag numbers (alag rahenge hi)", len(_nids) >= 4, str(len(_nids)))

# =====================================================================
section("7) pick_best — sabse active + sahi-service number chunta hai")
_orig_pool, _orig_inbox = TN.pool, TN.inbox
_MOCK_POOL = {"ok": True, "numbers": [
    {"nid": "rc:us:1", "src": "rc", "number": "15551111", "cc": "us"},
    {"nid": "rc:us:2", "src": "rc", "number": "15552222", "cc": "us"},
    {"nid": "rc:us:3", "src": "rc", "number": "15553333", "cc": "us"}], "notes": []}
_INBOXES = {
    "rc:us:1": {"ok": True, "number": "15551111", "last_activity": "2 days ago",
                "messages": [{"from": "Shop", "time": "2 days ago", "text": "Sale!", "code": ""}]},
    "rc:us:2": {"ok": True, "number": "15552222", "last_activity": "30 seconds ago",
                "messages": [{"from": "WhatsApp", "time": "1 minutes ago",
                              "text": "Your WhatsApp code is 445566", "code": "445566"}]},
    "rc:us:3": {"ok": True, "number": "15553333", "last_activity": "1 hour ago",
                "messages": [{"from": "WhatsApp", "time": "2 hours ago",
                              "text": "Your WhatsApp code is 111111", "code": "111111"}]},
}
_CALLS = []
TN.pool = lambda cc, refresh=False: _MOCK_POOL
TN.inbox = lambda nid, ttl=12.0, force=False: (_CALLS.append(nid) or _INBOXES[nid])
try:
    num, ib, err = TN.pick_best("us", svc_key="whatsapp", uid=7, tries=3)
    check("pick_best ne sabse active WhatsApp number chuna (+15552222)",
          num and num["number"] == "15552222", str(num and num["number"]))
    check("pick_best ne inbox bhi saath diya", bool(ib.get("ok")))
    check("pick_best ne max 3 hi numbers dekhe (spam nahi)", len(_CALLS) <= 3, str(len(_CALLS)))
    _CALLS.clear()
    num2, ib2, _ = TN.pick_best("us", svc_key="whatsapp", uid=7, avoid={"rc:us:2", "rc:us:3"}, tries=3)
    check("avoid set respect hota hai (pehle jaisa number dobara nahi)",
          num2 and num2["nid"] == "rc:us:1", str(num2 and num2["nid"]))
    sc_good = TN.inbox_score(_INBOXES["rc:us:2"], "whatsapp")
    sc_bad = TN.inbox_score(_INBOXES["rc:us:1"], "whatsapp")
    check("scoring: active + matched number ka score zyada", sc_good > sc_bad, f"{sc_good} vs {sc_bad}")
finally:
    TN.pool, TN.inbox = _orig_pool, _orig_inbox

# =====================================================================
section("8) Card v2 — waiting / naya OTP / hidden count / bank warning")
_rec = {"cc": "us", "num": "15552222", "svc": "whatsapp", "since": TN.snapshot([_m_old])}
_card_new = bot.tnum_card(_rec, {"ok": True, "number": "15552222",
                                 "messages": [_m_old, _m_new, _m_junk], "last_activity": "1 min ago"})
check("card: naya OTP sabse upar highlight", "🔑 <b>OTP:</b> <code>445566</code>" in _card_new)
check("card: purana SMS (3 hour ago) card me NAHI", "111111" not in _card_new)
check("card: dusri site ka naya SMS bhi NAHI (SoulChill/875371)", "875371" not in _card_new)
# v74.4: hidden-count jaisi internal baatein card me nahi (sirf outcome)
check("card: app + OTP hint dikhata hai", "WhatsApp" in _card_new and "6 digit" in _card_new)
check("card: koi safety/bank line nahi (sirf outcome)",
      "BANK" not in _card_new.upper() and "KYC" not in _card_new.upper())

_card_wait = bot.tnum_card(_rec, {"ok": True, "number": "15552222",
                                  "messages": [_m_old, _m_junk], "last_activity": "2 min ago"})
check("card waiting: 'abhi koi naya OTP nahi aaya'", "nahi aaya" in _card_wait)
check("card waiting: app ka naam wahi", "WhatsApp" in _card_wait)
check("card waiting: saaf 'naya OTP nahi aaya' line", "nahi aaya" in _card_wait)

_card_len = bot.tnum_card({"cc": "us", "num": "15552222", "svc": "whatsapp", "since": []},
                          {"ok": True, "number": "15552222", "last_activity": "1 min ago",
                           "messages": [{"from": "WhatsApp", "time": "1 min ago",
                                         "text": "Your WhatsApp code is 8424", "code": "8424"}]})
check("card: 4-digit wale par saaf note (WhatsApp ka nahi lagta)", "4 digit" in _card_len)

_card_bank = bot.tnum_card({"cc": "us", "num": "15552222", "svc": "whatsapp", "since": []},
                           {"ok": True, "number": "15552222", "last_activity": "1 min ago",
                            "messages": [{"from": "SBI", "time": "1 min ago",
                                          "text": "SBI bank OTP 998877 for UPI", "code": "998877"}]})
check("card: bank SMS chhupa + koi warning line nahi (v74.4)",
      "998877" not in _card_bank and "⛔" not in _card_bank)

_card_fail = bot.tnum_card(_rec, {"ok": False, "error": "site slow"})
check("card: inbox fail par saaf line (khaali card nahi)", "nahi khula" in _card_fail)
check("card: moti line (━) kahin nahi", "━" not in _card_new + _card_wait + _card_bank)

# =====================================================================
section("9) Bot wiring — fresh numbers (key v2) + naya flow")
check("store key v2 hai (purane saare numbers fresh)", 'TNUM_META_KEY = "tnum_assign_v2"' in BOT_SRC)
check("purani v1 key saaf karne ka code hai", 'TNUM_OLD_KEYS' in BOT_SRC
      and 'TNUM_OLD_KEYS = ("tnum_assign_v1",)' in BOT_SRC)
check("assignment ab pick_best se hota hai (best number)", "TN.pick_best(" in BOT_SRC)
check("baseline (since) save hota hai", '"since": TN.snapshot' in BOT_SRC)
check("card fresh+matched filter use karta hai",
      "TN.fresh_and_matched(" in BOT_SRC and "TN.extract_code_svc(" in BOT_SRC)
check("intro chhota hai — koi gyaan nahi (v74.4)", len(bot.TNUM_INTRO.splitlines()) <= 4)
check("refresh button label update (Naya OTP check karo)",
      "Naya OTP check karo" in BOT_SRC)
check("tool FREE hi hai (premium 42, tnum bahar)",
      "tnum" not in bot.PREMIUM_TOOLS and len(bot.PREMIUM_TOOLS) == 42)
check("temp number ab 1 app / 3 desh (v74.3 order — WhatsApp fi/nl/us)",
      len(TN.SERVICES) == 1 and [c["cc"] for c in TN.COUNTRIES] == ["fi", "nl", "us"])
# =====================================================================
section("10) E2E — nakli Telegram: fresh number → naya OTP → purana chhupa")
import asyncio                                                    # noqa: E402


class _QMsg:
    def __init__(self):
        self.chat = type("C", (), {"id": 99})()
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

    async def answer(self, text=None, show_alert=False):
        pass


class _Upd:
    def __init__(self, q):
        self.callback_query = q
        self.effective_user = q.from_user
        self.effective_chat = q.from_user


class _Ctx:
    def __init__(self):
        self.user_data = {}
        self.bot = object()


_old_pool, _old_inbox = TN.pool, TN.inbox
_MPOOL = {"ok": True, "numbers": [{"nid": f"rc:us:{i}", "src": "rc", "number": f"1555999{i}",
                                   "cc": "us"} for i in range(3)], "notes": []}
_OLDJUNK = [{"from": "22905", "time": "3 hour ago", "text": "[WeChat] WeChat code (021075)", "code": "021075"},
            {"from": "Google", "time": "1 hour ago", "text": "G-999999 is your Google verification code.", "code": "999999"}]
_STATE = {"otp": False}      # assignment ke BAAD True karenge (naya OTP gira)


def _ibox_e2e(nid, ttl=12.0, force=False):
    msgs = list(_OLDJUNK)
    if _STATE["otp"]:        # asli duniya me: OTP baad me aata hai
        msgs = [{"from": "WhatsApp", "time": "1 min ago",
                 "text": "Your WhatsApp code is 556677. Don't share this code.", "code": "556677"}] + msgs
    return {"ok": True, "number": "15559990", "messages": msgs,
            "last_activity": "1 min ago", "count24": 12, "cached": False}


TN.pool = lambda cc, refresh=False: _MPOOL if cc == "us" else {"ok": False, "error": "nahi"}
TN.inbox = _ibox_e2e


async def _flow():
    uid = 909090
    c = _Ctx()
    q1 = _Q("tnum_open", uid)
    await bot.on_cb(_Upd(q1), c)
    check("E2E: intro chhota (koi gyaan nahi)", len((q1.message.out[-1] or "").splitlines()) <= 5)
    q2 = _Q("tnum_svc:whatsapp", uid)
    await bot.on_cb(_Upd(q2), c)
    check("E2E: app chuna → desh list", "DESH CHUNO" in bot.unbold(q2.message.out[-1]))
    q3 = _Q("tnum_ctry:us", uid)
    await bot.on_cb(_Upd(q3), c)
    a3 = q3.message.out[-1]
    check("E2E: fresh number mila (baseline ke saath)", "Aapka number" in a3)
    _STATE["otp"] = True          # ab naya WhatsApp OTP girta hai
    _rec = bot._tnum_load().get(str(uid)) or {}
    check("E2E: baseline (since) save hua — purane WeChat/Google SMS record ho gaye",
          len(_rec.get("since") or []) >= 2, str(len(_rec.get("since") or [])))
    check("E2E: purana WeChat code card me nahi", "021075" not in a3)
    check("E2E: purana Google code card me nahi", "999999" not in a3)
    q4 = _Q("tnum_refresh", uid)
    c.user_data["tnum_last_ref"] = 0
    await bot.on_cb(_Upd(q4), c)
    a4 = q4.message.out[-1]
    check("E2E: naya WhatsApp OTP aa gaya (556677)", "<code>556677</code>" in a4)
    check("E2E: refresh ke baad bhi purane SMS chhupe", "021075" not in a4 and "999999" not in a4)
    check("E2E: card me koi bank/safety line nahi", "KYC" not in a4.upper())


try:
    asyncio.run(_flow())
finally:
    TN.pool, TN.inbox = _old_pool, _old_inbox

print(f"\n{'=' * 62}")
print(f"  v74 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
