# -*- coding: utf-8 -*-
"""v93 SELFTEST — 🧯 HTML SAFETY NET.

Owner ki shikayat: "mera code crash ho jaata hai baar baar."

Jaanch me mili sabse badi wajah: bot.py me ~500 jagah parse_mode=HTML ke saath
direct reply_text/edit_text/send_message hota hai. Text me zara si HTML gadbad
(engine ke title me `<`, adhoora tag, user ke naam me `&`) → Telegram poora
message reject:

    telegram.error.BadRequest: Can't parse entities: can't find end tag 'b'

Kaam ho chuka hota hai, jawab taiyaar hota hai — par user tak jaata nahi, aur
user ko "⚠️ Chhota sa ghatna ho gaya!" dikhta hai. Wahi "crash" hai.

Ye test ek FAKE Bot class par asli wrapper chalata hai (network zero) aur
confirm karta hai ki message kabhi gayab nahi hota.
"""
import asyncio
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v93_html_tmp.db"))

PASS = 0
FAIL = 0
FAILS = []


def check(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILS.append(label)
        print(f"   ❌ FAIL: {label} {extra}")


def read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


print("v93 SELFTEST — 🧯 HTML Safety Net")

from telegram.error import BadRequest                            # noqa: E402
from modules.core import htmlnet as HN                           # noqa: E402

# ============================================================================
print("\n[A] Pure helpers")
# ============================================================================
check("A1 strip_tags tags hata deta hai",
      HN.strip_tags("<b>Hi</b> <i>dost</i>") == "Hi dost", HN.strip_tags("<b>Hi</b> <i>dost</i>"))
check("A2 strip_tags entities padhne-layak karta hai",
      HN.strip_tags("A &amp; B &lt;x&gt;") == "A & B <x>", HN.strip_tags("A &amp; B &lt;x&gt;"))
check("A3 double-decode nahi hota (&amp;lt; -> '<lt;' nahi)",
      HN.strip_tags("&amp;lt;b&amp;gt;") == "&lt;b&gt;", HN.strip_tags("&amp;lt;b&amp;gt;"))
check("A4 khaali/None par crash nahi",
      HN.strip_tags(None) == "(empty)" and HN.strip_tags("") == "(empty)")
check("A5 parse-error detection: asli Telegram messages pakadta hai",
      HN._is_parse_error(BadRequest("Can't parse entities: can't find end tag 'b'"))
      and HN._is_parse_error(BadRequest("Can't parse entities: unsupported start tag"))
      and HN._is_parse_error(BadRequest("message is too long: can't parse entities")))
check("A6 baaki errors ko parse-error nahi maanta",
      not HN._is_parse_error(BadRequest("chat not found"))
      and not HN._is_parse_error(ValueError("x"))
      and not HN._is_parse_error("message text is empty"))


# ============================================================================
print("\n[B] Wrapper — asli tarah ka Bot")
# ============================================================================
class _FakeBot:
    """Bot jaisa dikhne wala fake: kwargs record karta hai, script ke hisaab se fail."""

    def __init__(self, fail_times=1, err="Can't parse entities: can't find end tag 'b'",
                 always=False):
        self.calls = []
        self.fail_times = fail_times
        self.err = err
        self.always = always

    async def send_message(self, chat_id, text=None, parse_mode=None, **kw):
        self.calls.append({"text": text, "parse_mode": parse_mode, **kw})
        # Asli Telegram sirf tab "parse entities" deta hai jab parse_mode set ho.
        # Plain (parse_mode=None) text par ye error kabhi nahi aata.
        if parse_mode and (self.always or len(self.calls) <= self.fail_times):
            raise BadRequest(self.err)
        return {"ok": True, "n": len(self.calls)}

    async def send_photo(self, chat_id, photo=None, caption=None, parse_mode=None, **kw):
        self.calls.append({"caption": caption, "parse_mode": parse_mode, **kw})
        if parse_mode and (self.always or len(self.calls) <= self.fail_times):
            raise BadRequest(self.err)
        return {"ok": True, "n": len(self.calls)}


HN.patch_bot_html_safety(_FakeBot)

# B1 — pehli koshish fail, repair karke dobara: message MILTA hai
b = _FakeBot(fail_times=1)
r = asyncio.run(b.send_message(1, "<b>Adhoora</b> text <i>khula", parse_mode="HTML"))
check("B1 parse-error par message dobara chala gaya (gayab nahi hua)",
      isinstance(r, dict) and r.get("ok"), str(r))
check("B2 doosri koshish me text repair hua (khaali nahi)",
      len(b.calls) >= 2 and bool(b.calls[-1]["text"]), str(b.calls))

# B3 — hamesha fail kare to plain-text fallback par jaata hai
b2 = _FakeBot(always=True)
r2 = asyncio.run(b2.send_message(1, "<b>x</b> & y", parse_mode="HTML"))
check("B3 hamesha fail ho to bhi message gaya (plain fallback)",
      isinstance(r2, dict) and r2.get("ok"), str(r2))
_last = b2.calls[-1]
check("B4 fallback me parse_mode hata diya gaya", _last["parse_mode"] is None, str(_last))
check("B5 fallback text me koi HTML tag nahi bacha",
      "<b>" not in str(_last["text"]) and "x" in str(_last["text"]), str(_last["text"]))

# B6 — parse_mode na ho to wrapper BILKUL chhedta nahi (behaviour pehle jaisa)
class _NoParseBot(_FakeBot):
    """parse_mode na hone par bhi galti se error de de — wrapper ko retry NAHI karna."""

    async def send_message(self, chat_id, text=None, parse_mode=None, **kw):
        self.calls.append({"text": text, "parse_mode": parse_mode, **kw})
        raise BadRequest("Can't parse entities: can't find end tag 'b'")


b3 = _NoParseBot()
try:
    asyncio.run(b3.send_message(1, "plain text"))
    _raised = False
except BadRequest:
    _raised = True
check("B6 bina parse_mode wrapper retry NAHI karta (error jaisa tha waisa aage)",
      _raised and len(b3.calls) == 1, f"calls={len(b3.calls)}")

# B7 — doosra error (chat not found) aage badhta hai — net sirf HTML par hai
b4 = _FakeBot(always=True, err="chat not found")
try:
    asyncio.run(b4.send_message(1, "<b>x</b>", parse_mode="HTML"))
    _raised2 = False
except BadRequest:
    _raised2 = True
check("B7 non-HTML error re-raise hota hai (RetryAfter/Forbidden ka apna handling hai)",
      _raised2)
check("B8 non-HTML error par dobara koshish nahi hoti", len(b4.calls) == 1, str(len(b4.calls)))

# B9 — photo caption par bhi net chalta hai
b5 = _FakeBot(always=True)
r5 = asyncio.run(b5.send_photo(1, photo=b"x", caption="<b>Bad</b> caption", parse_mode="HTML"))
check("B9 photo caption par bhi net chalta hai", isinstance(r5, dict) and r5.get("ok"), str(r5))
check("B10 caption plain ho gaya (tag nahi bacha)",
      "<b>" not in str(b5.calls[-1].get("caption")), str(b5.calls[-1]))

# B11 — idempotent: dobara patch karne par double-wrap nahi
_before = _FakeBot.send_message
HN.patch_bot_html_safety(_FakeBot)
HN.patch_bot_html_safety(_FakeBot)
check("B11 patch idempotent hai (double-wrap nahi)", _FakeBot.send_message is _before)

# B12 — POSITIONAL text par bhi net chalta hai.
# PTB ke reply_text/edit_text bot ko text positional bhejte hain — isliye
# signature se sahi index nikalna zaroori tha (pehle yahi off-by-one bug tha).
b6 = _FakeBot(fail_times=1)
r6 = asyncio.run(b6.send_message(1, "<b>pos</b> <i>khula", parse_mode="HTML"))
check("B12 positional text par bhi message bach gaya",
      isinstance(r6, dict) and r6.get("ok"), str(r6))
# repair ne adhoora <i> band kar diya — ab har tag ka joda hai (Telegram accept karega)
_t13 = str(b6.calls[-1]["text"])
check("B13 positional text repair hua — har tag ab balanced hai",
      _t13.count("<i>") == _t13.count("</i>") and _t13.count("<b>") == _t13.count("</b>"),
      _t13)

# B14 — edit_message_text (55 jagah use hota hai) bhi guard me hai
class _EditBot:
    def __init__(self):
        self.calls = []

    async def edit_message_text(self, text=None, chat_id=None, message_id=None,
                                parse_mode=None, **kw):
        self.calls.append({"text": text, "parse_mode": parse_mode})
        if parse_mode:
            raise BadRequest("Can't parse entities: can't find end tag 'i'")
        return {"ok": True}


HN.patch_bot_html_safety(_EditBot)
b7 = _EditBot()
r7 = asyncio.run(b7.edit_message_text("<i>adhoora", chat_id=1, message_id=2, parse_mode="HTML"))
check("B14 edit_message_text par bhi net chalta hai (55 call-sites safe)",
      isinstance(r7, dict) and r7.get("ok") and "<i>" not in str(b7.calls[-1]["text"]),
      str(b7.calls))

# ============================================================================
print("\n[C] bot.py me wiring")
# ============================================================================
BOT_SRC = read("bot.py")
check("C1 bot.py net ko import-time par lagata hai",
      "patch_bot_html_safety()" in BOT_SRC)
check("C2 net fail ho to bhi bot chalta rahega (try/except me hai)",
      "HTML safety net skip" in BOT_SRC)
check("C3 net Telegram Bot class par lagta hai (default)",
      "from telegram import Bot as cls" in read("modules/core/htmlnet.py"))
check("C4 send_message + edit_message_text dono guard hain",
      '"send_message"' in read("modules/core/htmlnet.py")
      and '"edit_message_text"' in read("modules/core/htmlnet.py"))

# ============================================================================
print("\n[D] Asli telegram.Bot par patch lagta hai (bot import karke)")
# ============================================================================
try:
    import bot as _B                                             # noqa: F401
    from telegram import Bot as _RealBot
    check("D1 bot import hua aur asli Bot class par net laga",
          getattr(_RealBot, HN._PATCHED_FLAG, False) is True)
    check("D2 send_message wrap hua hai",
          getattr(_RealBot.send_message, "__ud_wrapped__", False) is True)
except Exception as _e:                                          # noqa: BLE001
    FAIL += 1
    FAILS.append(f"D1/D2 bot import: {type(_e).__name__}: {str(_e)[:100]}")
    print(f"   ❌ FAIL: D bot import — {type(_e).__name__}: {str(_e)[:120]}")

print("\n" + "=" * 64)
for _l in FAILS:
    print("  ❌", _l)
print(f"RESULT: {PASS} PASS / {FAIL} FAIL")
print(f"  v93 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 64)
sys.exit(1 if FAIL else 0)
