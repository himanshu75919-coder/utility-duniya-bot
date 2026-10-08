#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v83 SELFTEST — ULTRA-PRO ALL-TOOLS (v83.0)
==========================================
Ye test v83 ke fixes ko asli bot.py functions par check karta hai:
  1) YouTube quality picker: handler khatam hote hi progress ticker band (overwrite nahi karega)
  2) Galat/khaali callback ID (jaise "admpay_view:") → crash nahi, user ko saaf jawab
  3) Dead buttons "menu" aur "alltools" ab sach me jawab dete hain
  4) Benign Telegram errors (message not found / not modified) user ko error nahi dikhate
  5) Version v83 par bump hua

Chalane ka tarika:
    python3 tests/test_v83_pro_all.py
"""
import asyncio
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="ud_test_v83_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("PREMIUM_ONLY", "off")
os.environ.setdefault("ALL_FREE", "1")
for _k in ("FORCE_CHANNEL", "FORCE_CHANNEL_LINK", "WEBHOOK_URL"):
    os.environ.pop(_k, None)

from types import SimpleNamespace  # noqa: E402

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name}" + (f"  [{extra}]" if extra and not cond else ""))


SINK = []


class _User:
    def __init__(self, uid):
        self.id = uid
        self.first_name = "Tester"
        self.last_name = ""
        self.username = "tester"
        self.is_bot = False
        self.language_code = "en"


class _Msg:
    def __init__(self, text, uid):
        self.text = text
        self.caption = None
        self.message_id = 1
        self.chat_id = uid
        self.chat = SimpleNamespace(id=uid, type="private", title="", username=None)
        self.from_user = _User(uid)
        for a in ("photo", "document", "video", "audio", "voice", "sticker", "animation",
                  "entities", "caption_entities", "reply_to_message", "forward_origin"):
            setattr(self, a, None)

    async def reply_text(self, text="", **kw):
        SINK.append(("text", str(text)))
        return _Msg(text, self.chat_id)

    async def edit_text(self, text="", **kw):
        SINK.append(("edit", str(text)))
        return self

    async def edit_caption(self, *a, **kw):
        return self

    async def edit_reply_markup(self, *a, **kw):
        return self

    async def delete(self):
        return True

    async def reply_chat_action(self, *a, **kw):
        return True


class _CQ:
    def __init__(self, data, uid):
        self.id = "1"
        self.data = data
        self.from_user = _User(uid)
        self.message = _Msg("", uid)
        self.chat_instance = "1"
        self.inline_message_id = None

    async def answer(self, *a, **kw):
        return True

    async def edit_message_text(self, text="", **kw):
        SINK.append(("edit", str(text)))
        return self.message


class _Upd:
    def __init__(self, uid, text=None, cq=None):
        self.update_id = 1
        self.effective_user = _User(uid)
        self.effective_chat = SimpleNamespace(id=uid, type="private", title="", username=None)
        self.message = _Msg(text, uid) if text is not None else None
        self.callback_query = _CQ(cq, uid) if cq is not None else None
        self.effective_message = self.message or (self.callback_query.message if self.callback_query else None)
        for a in ("edited_message", "channel_post", "inline_query", "my_chat_member",
                  "chat_member", "chat_join_request", "poll", "pre_checkout_query"):
            setattr(self, a, None)


class _Bot:
    id = 0
    username = "testbot"
    first_name = "T"

    async def get_chat_member(self, *a, **kw):
        return SimpleNamespace(status="member", user=_User(0))

    async def send_message(self, chat_id, text="", **kw):
        SINK.append(("send", str(text)))
        return _Msg(text, chat_id)

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)

        async def _f(*a, **kw):
            return True
        return _f


class _Ctx:
    def __init__(self, uid=5001):
        self.user_data = {}
        self.chat_data = {}
        self.bot_data = {}
        self.bot = _Bot()
        self.args = []
        self.job_queue = None
        self.error = None


def run(coro):
    return asyncio.run(coro)


def main():
    import bot as B

    print("=" * 62)
    print("1) Progress ticker handler ke end par band hota hai (quality picker safe)")
    print("=" * 62)
    ctx = _Ctx()
    ev = asyncio.Event() if False else None  # placeholder (asyncio.Event loop ke andar banega)

    async def _ticker_case():
        import asyncio as _a
        _ev = _a.Event()
        _c = _Ctx()
        _c.user_data["_ping_stop"] = _ev
        await B._on_text_pro(_Upd(5001, text="hello bot"), _c)
        return _ev.is_set(), "_ping_stop" in _c.user_data

    set_after, still_there = run(_ticker_case())
    ok("ticker event handler return ke baad SET hai", set_after)
    ok("ticker key user_data se hata diya gaya", not still_there)

    print("=" * 62)
    print("2) Galat / khaali callback ID → crash nahi, saaf jawab")
    print("=" * 62)
    SINK.clear()
    crashed = None
    # admpay_view: sirf admin ko reach hota hai (non-admin pe handler pehle hi return karta hai),
    # isliye admin uid (ADMIN_ID=1) se test karte hain.
    _admin = int(os.environ.get("ADMIN_ID", "1"))
    try:
        run(B._on_cb_pro(_Upd(_admin, cq="admpay_view:"), _Ctx(_admin)))
    except Exception as e:  # noqa: BLE001
        crashed = e
    ok("admpay_view: (khaali ID) exception nahi phenkta", crashed is None, repr(crashed)[:120])
    ok("user ko 'purana ya adhoora' jawab mila",
       any("purana ya adhoora" in t for _k, t in SINK), str(SINK)[:160])

    print("=" * 62)
    print("3) Dead buttons: 'menu' aur 'alltools' ab jawab dete hain")
    print("=" * 62)
    SINK.clear()
    run(B._on_cb_pro(_Upd(5001, cq="alltools"), _Ctx()))
    ok("alltools: tools ki list bheji gayi",
       any("SAARE TOOLS" in t for _k, t in SINK), str(SINK)[:160])
    SINK.clear()
    run(B._on_cb_pro(_Upd(5001, cq="menu"), _Ctx()))
    ok("menu: welcome/menu wapas aaya (edit ya send)",
       any(_k in ("edit", "send", "text") for _k, _t in SINK), str(SINK)[:160])

    print("=" * 62)
    print("4) Benign Telegram errors user ko error nahi dikhate")
    print("=" * 62)
    for _msg in ("Message to edit not found", "Message is not modified: specified new message content",
                 "Query is too old and response timeout expired"):
        SINK.clear()
        _c = _Ctx()
        _c.error = Exception(_msg)
        _u = _Upd(5001, text="x")
        run(B.on_error(_u, _c))
        ok(f"benign skip: {_msg[:28]}", not SINK, str(SINK)[:120])
    SINK.clear()
    _c = _Ctx()
    _c.error = Exception("kuch aur galat hua")
    run(B.on_error(_Upd(5001, text="x"), _c))
    ok("non-benign error par user ko 'Chhota sa ghatna' message jaata hai",
       any("Chhota sa ghatna" in t for _k, t in SINK), str(SINK)[:120])

    print("=" * 62)
    print("5) Version v83 par hai")
    print("=" * 62)
    ok("BOT_VERSION v84 se shuru hota hai (v83 history bhi)",
       B.BOT_VERSION.startswith("v84") and "v83.0" in B.BOT_VERSION, B.BOT_VERSION[:20])
    ok("BOT_VERSION me guard words (v77/FREE4ALL/SPEED) abhi bhi hain",
       "v77" in B.BOT_VERSION and "FREE4ALL" in B.BOT_VERSION and "SPEED" in B.BOT_VERSION)

    print("\n" + "=" * 62)
    print(f"v83 SELFTEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
    if FAIL:
        print("FAILED:", FAIL)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
