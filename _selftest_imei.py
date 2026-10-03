"""v41 TEST — IMEI / PHONE DETAILS (mock hub par end-to-end, net ki zarurat nahi).

Mock = asli hub ka /api/imei jawab (Apple iPhone 12 mini sample, jaisa user ne bheja tha).
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DB_PATH", "/tmp/_imei41_test.db")

# ---------------------------------------------------------------- mock data (asli hub jaisa)
APPLE = {
    "imei": "353010111111110", "imei2": None, "is_custom_result": False, "phone_number": None,
    "processing_countdown": 20, "requested_at": "2026-10-02T12:00:00+02:00",
    "result": {
        "header": {"brand": "APPLE", "imei": "353010111111110", "model": "iPhone 12 mini",
                   "photo": "https://www.imei.info/media/t/i/4/4vvvj3-5VFz.jpg"},
        "items": [
            {"role": "header", "title": "Basic Info"},
            {"role": "item", "title": "Code Name", "content": "A2398"},
            {"role": "item", "title": "Relase Year", "content": "2020"},
            {"role": "item", "title": "Operating systems", "content": "iOS 17"},
            {"role": "item", "title": "Chipset", "content": "Apple A14 Bionic"},
            {"role": "item", "title": "GPU type", "content": "Apple GPU"},
            {"role": "header", "title": "Dimensions"},
            {"role": "item", "title": "Height", "content": "131.5"},
            {"role": "item", "title": "Width", "content": "64.2 [mm]"},
            {"role": "item", "title": "Thickness", "content": "7.4 [mm]"},
            {"role": "header", "title": "Display"},
            {"role": "item", "title": "Display type", "content": "OLED"},
            {"role": "item", "title": "Display ", "content": "1080x2340 [px]"},
            {"role": "item", "title": "Diagonal ", "content": "5.4 [in]"},
            {"role": "header", "title": "Network"},
            {"role": "item", "title": "5G", "content": "True"},
            {"role": "item", "title": "4G", "content": "True"},
            {"role": "item", "title": "3G", "content": "True"},
            {"role": "item", "title": "2G", "content": "True"},
            {"role": "header", "title": "Battery"},
            {"role": "item", "title": "Type", "content": "Li-Ion"},
            {"role": "item", "title": "Capacity", "content": "2227.0 [mAh]"},
            {"role": "header", "title": "Camera"},
            {"role": "item", "title": "Main", "content": "12.0 [MPx]"},
            {"role": "item", "title": "Selfie", "content": "12.0 [MPx]"},
            {"role": "button", "title": "Full device specification",
             "content": "https://www.imei.info/phonedatabase/apple-iphone-12-mini/"},
            {"role": "header", "title": "Found an error? Help us and let us know:"},
            {"role": "button", "title": "Support Team Contact", "content": "mailto:info@imei.info"},
            {"role": "header", "title": "Check iPhone 12 mini specific : "},
            {"role": "group", "items": [
                {"content": "https://www.imei.info/imei-checker/", "role": "button", "title": "Services"},
                {"content": "https://www.hardreset.info/devices/APPLE/apple-iphone-12-mini/tutorials/",
                 "role": "button", "title": "Tutorials"}]},
        ],
    },
}

INVALID = {"imei": "353010111111110", "imei2": None, "is_custom_result": False, "phone_number": None,
           "processing_countdown": 20, "requested_at": "2026-10-02T12:00:00+02:00", "result": "Invalid IMEI"}
BADAUTH = {"error": "Invalid API key"}


class Handler(BaseHTTPRequestHandler):
    mode = "apple"

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if Handler.mode == "invalid":
            self._send(INVALID)
        elif Handler.mode == "badauth":
            self._send(BADAUTH)
        else:
            self._send(APPLE)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 8792), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["IMEI_API_BASE"] = "http://127.0.0.1:8792/api"
os.environ["IMEI_API_KEY"] = "testkey"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"

import bot  # noqa: E402
import database as dbm  # noqa: E402
from modules import imei_lookup as il  # noqa: E402

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("✅ " if cond else "❌ ") + name + ("" if cond else f"  — {str(extra)[:240]}"))


# --------------------------------------------------------- 1) IMEI CHECK (validate)
print("\n--- 1) IMEI VALIDATION (15 digit + Luhn) ---")
ok("sahi IMEI pass", il.validate_imei("353010111111110")[0] is True)
ok("Luhn galat → reject", il.validate_imei("123456789012345")[0] is False
   and "check digit" in il.validate_imei("123456789012345")[2], il.validate_imei("123456789012345"))
ok("12 digit → reject", il.validate_imei("353010111111")[0] is False
   and ("15 digits" in il.validate_imei("353010111111")[2] or "15 digit" in il.validate_imei("353010111111")[2]), il.validate_imei("353010111111"))
ok("spaces/dashes saaf hote hain", il.clean_imei("IMEI: 35-301011-1111110") == "353010111111110",
   il.clean_imei("IMEI: 35-301011-1111110"))
ok("16 digit (IMEISV) → pehle 15", il.clean_imei("3530101111111101") == "353010111111110")
ok("garbage → khaali", il.clean_imei("hello bhai") == "")

# --------------------------------------------------------- 2) ENGINE (mock hub)
print("\n--- 2) ENGINE (mock /api/imei) ---")
il.clear_cache()
r = il.fetch_imei_details("353010111111110")
ok("device mila (ok=True)", r.get("ok") is True, r)
ok("brand APPLE, model iPhone 12 mini", r.get("brand") == "APPLE" and r.get("model") == "iPhone 12 mini", r)
ok("title 'Apple iPhone 12 mini'", il.device_title(r) == "Apple iPhone 12 mini", il.device_title(r))
ok("photo URL aaya", str(r.get("photo", "")).endswith(".jpg"), r.get("photo"))
secs = {s["title"]: dict(s["rows"]) for s in (r.get("sections") or [])}
ok("6 spec section bane", len(r.get("sections") or []) == 6, list(secs))
for want in ("Basic Info", "Dimensions", "Display", "Network", "Battery", "Camera"):
    ok(f"section '{want}'", want in secs, list(secs))
ok("chipset ki value sahi", secs.get("Basic Info", {}).get("Chipset") == "Apple A14 Bionic", secs.get("Basic Info"))
ok("display 1080x2340", secs.get("Display", {}).get("Display") == "1080x2340 [px]", secs.get("Display"))
ok("True → ✅ (network)", secs.get("Network", {}).get("5G") == "✅", secs.get("Network"))
ok("API ka typo waise hi rehta (Relase Year)", "Relase Year" in secs.get("Basic Info", {}), secs.get("Basic Info"))
ok("'Found an error' header skip", not any("error" in t.lower() for t in secs), list(secs))
ok("mailto link skip, baaki links mile", len(r.get("links") or []) == 3
   and not any("mailto" in u for _t, u in r["links"]), r.get("links"))

cap = il.render_caption(r)
ok("caption ≤ 1024 (Telegram limit)", 0 < len(cap) <= 1024, len(cap))
ok("caption me device + IMEI", "Apple iPhone 12 mini" in cap and "353010111111110" in cap, cap[:200])
ok("caption me spec jhalak", "OLED" in cap and "Basic Info" in cap, cap[:300])
txt = il.render_text(r)
ok("text card me sab section", all(x in txt for x in ("Basic Info", "Display", "Network", "Battery", "Camera")), txt[:200])
ok("text card 4000 se chhota", len(txt) <= 4000, len(txt))
js = il.specs_json_bytes(r)
ok("JSON file banti hai", len(js) > 400, len(js))
jobj = json.loads(js.decode("utf-8"))
ok("JSON me specifications + Display.OLED", jobj["specifications"]["Display"]["Display type"] == "OLED", list(jobj))
ok("file ka naam Apple_iPhone_12_mini_specs.json", il.specs_filename(r) == "Apple_iPhone_12_mini_specs.json",
   il.specs_filename(r))
links = il.fallback_links("353010111111110")
ok("fallback links imei.info ke", len(links) == 2 and "imei.info" in links[0][1], links)

r2 = il.fetch_imei_details("353010111111110")
ok("dobara = cache se (API call bachi)", r2.get("cached") is True and r2.get("ok") is True, r2.get("cached"))

Handler.mode = "invalid"
il.clear_cache()
bad = il.fetch_imei_details("353010111111110")
ok("API 'Invalid IMEI' → saaf not-found", bad.get("ok") is False and bad.get("not_found") is True
   and ("not in the database" in str(bad.get("error")) or "database me nahi" in str(bad.get("error"))), bad)

Handler.mode = "badauth"
il.clear_cache()
ba = il.fetch_imei_details("353010111111110")
ok("galat key → 'Invalid API key' error", ba.get("ok") is False and "Invalid API key" in str(ba.get("error")), ba)
Handler.mode = "apple"
il.clear_cache()

# --------------------------------------------------------- 3) BOT FLOW
print("\n--- 3) BOT FLOW (Telegram) ---")
_PRE_PASS, _PRE_FAIL = list(PASS), list(FAIL)   # exec naye lists banata hai — purane bacha lo
PASS, FAIL = [], []
sys.argv = ["x"]
if os.path.exists("_selftest_v38_desi.py"):
    exec(open("_selftest_v38_desi.py", encoding="utf-8").read().split(
        "# ======================================================================\nasync def t1_menu()")[0])
else:
    import asyncio
    import re
    import unicodedata
    from telegram import Chat, Update, User
    from telegram.constants import ChatType

    OWNER = int(os.environ.get("ADMIN_ID", "8607774564"))

    def kb_label(action):
        for row in bot.KB_BTNS:
            for b in row:
                k = re.sub(r"^[^\w\s]+\s*", "", bot.unbold(b).strip().upper()).strip()
                if bot.BTN_MODE_MAP.get(k) == action:
                    return b
        return ""

    def fresh(uid, credits=5, vip=False):
        dbm.get_user(uid, "Tester")
        if vip:
            dbm.grant_premium(uid, 30)
        else:
            dbm.revoke_premium(uid)
        dbm.set_credits(uid, credits)

    class FakeSent:
        def __init__(self, owner):
            self.owner = owner

        async def edit_text(self, text, **kw):
            self.owner.replies.append(("edit", text, kw, None))
            return self

        async def delete(self):
            return True

    class FakeMsg:
        def __init__(self, text="", uid=8607774565):
            self.text = text
            self.caption = None
            self.photo = self.video = self.document = self.audio = self.voice = self.animation = None
            self.replies = []
            self.chat = Chat(id=uid, type=ChatType.PRIVATE)
            self.from_user = User(id=uid, first_name="Test", is_bot=False)
            self.message_id = 1

        async def reply_text(self, text, **kw):
            self.replies.append(("text", text, kw, None))
            return FakeSent(self)

        async def reply_photo(self, photo=None, caption="", **kw):
            self.replies.append(("photo", caption, kw, photo))
            return FakeSent(self)

        async def reply_document(self, document=None, **kw):
            self.replies.append(("document", kw.get("caption", ""), kw, document))
            return FakeSent(self)

        def kinds(self):
            return [k for k, *_ in self.replies]

        def all_text(self):
            parts = []
            for _k, t, kw, _ in self.replies:
                parts.append(t if isinstance(t, str) else "")
                kb = (kw or {}).get("reply_markup")
                if kb is not None and getattr(kb, "inline_keyboard", None):
                    for row in kb.inline_keyboard:
                        parts.append(" | ".join(b.text for b in row))
            return unicodedata.normalize("NFKC", "\n".join(parts))

        def cb_data(self):
            out = []
            for _k, _t, kw, _ in self.replies:
                kb = (kw or {}).get("reply_markup")
                if kb is not None and getattr(kb, "inline_keyboard", None):
                    out += [b.callback_data for row in kb.inline_keyboard for b in row if getattr(b, "callback_data", None)]
            return out

    class FakeQuery:
        def __init__(self, data, uid=8607774565):
            self.data = data
            self.from_user = User(id=uid, first_name="Test", is_bot=False)
            self.message = FakeMsg("", uid=uid)
            self.answers = []

        async def answer(self, text=None, show_alert=False):
            self.answers.append(text)

    class Ctx:
        def __init__(self):
            self.user_data = {}
            self.args = []
            self.bot = type("B", (), {"id": 999})()

    async def send_text(text, ctx, uid=8607774565):
        m = FakeMsg(text, uid=uid)
        upd = Update(update_id=1, message=m)
        upd.message.from_user = User(id=uid, first_name="Test", is_bot=False)
        await bot.on_text(upd, ctx)
        return m

    async def click(data, ctx, uid=8607774565):
        q = FakeQuery(data, uid=uid)
        upd = Update(update_id=2, callback_query=q)
        await bot.on_cb(upd, ctx)
        return q

USER = 8607774565


async def run_cmd(coro, ctx, uid=OWNER, args=None):
    ctx.args = list(args or [])
    m = FakeMsg("", uid=uid)
    upd = Update(update_id=5, message=m)
    upd.message.from_user = User(id=uid, first_name="Test", is_bot=False)
    await coro(upd, ctx)
    return m


def _urls(m):
    out = []
    for _k, _t, kw, _ in m.replies:
        kb = (kw or {}).get("reply_markup")
        if kb is not None and getattr(kb, "inline_keyboard", None):
            out += [b.url for row in kb.inline_keyboard for b in row]
    return [u for u in out if u]


# FakeMsg document object ko record nahi karta — chhota wrapper laga dete hain
_orig_reply_doc = FakeMsg.reply_document


async def _rec_doc(self, document=None, **kw):
    self.sent_docs = getattr(self, "sent_docs", [])
    self.sent_docs.append((kw.get("caption", ""), document))
    return await _orig_reply_doc(self, document=document, **kw)


FakeMsg.reply_document = _rec_doc


def _docs(m):
    return getattr(m, "sent_docs", [])


async def flows():
    # menu + prompt
    ok("menu me IMEI button hai", bool(kb_label("imei")), kb_label("imei"))
    fresh(USER, 5)
    ctx = Ctx()
    m = await send_text(kb_label("imei"), ctx, uid=USER)
    t = m.all_text()
    ok("prompt khulta hai", ("Now send the 15 digit IMEI" in t or "Ab 15 digit IMEI bhejo" in t), t[:220])
    ok("prompt me *#06# ka tarika", "*#06#" in t, t[:220])
    ok("prompt me credits line", "Credits" in t, t[:250])

    # sahi IMEI → photo + text + json + 1 credit
    before = dbm.get_credits(USER)
    m2 = await send_text("353010111111110", ctx, uid=USER)
    kinds = m2.kinds()
    ok("photo bheji gayi", "photo" in kinds, kinds)
    photo_cap = [t for k, t, _kw, _ in m2.replies if k == "photo"][0]
    ok("photo caption me device naam", "Apple iPhone 12 mini" in photo_cap, photo_cap[:200])
    ok("photo caption ≤ 1024", len(photo_cap) <= 1024, len(photo_cap))
    txt_all = m2.all_text()
    ok("poora spec card aaya (Display/Network)", "OLED" in txt_all and "1080x2340" in txt_all, txt_all[:250])
    docs = _docs(m2)
    ok("JSON spec file attach hui", len(docs) == 1, docs)
    if docs:
        fname = getattr(docs[0][1], "name", "")
        data = docs[0][1].getvalue() if hasattr(docs[0][1], "getvalue") else b""
        ok("file ka naam ..._specs.json", fname.endswith("_specs.json"), fname)
        ok("file ka andar specifications JSON", b'"specifications"' in data and b"OLED" in data, data[:120])
        ok("file caption me device naam", "Apple iPhone 12 mini" in docs[0][0], docs[0][0][:120])
    ok("1 credit kata", dbm.get_credits(USER) == before - 1, (before, dbm.get_credits(USER)))
    ok("'credit used' line aayi", ("credit used" in txt_all.lower() or "credit laga" in txt_all.lower()), txt_all[-200:])
    ok("mode clear ho gaya", "mode" not in ctx.user_data, ctx.user_data)
    ok("'Check another IMEI' button", any("imei_new" == c for c in m2.cb_data()), m2.cb_data())
    ok("imei.info ka link button", any("imei.info" in str(u or "") for u in _urls(m2)), _urls(m2))

    # galat IMEI (Luhn) → saaf error, credit nahi kata
    ctx2 = Ctx(); fresh(USER, 5)
    await send_text(kb_label("imei"), ctx2, uid=USER)
    m3 = await send_text("123456789012345", ctx2, uid=USER)
    ok("galat IMEI par saaf error", ("not valid" in m3.all_text().lower() or "sahi nahi" in m3.all_text().lower()), m3.all_text()[:200])
    ok("galat IMEI par credit nahi kata", dbm.get_credits(USER) == 5, dbm.get_credits(USER))
    ok("galat IMEI par mode chalu (retry ho sake)", ctx2.user_data.get("mode") == "imei", ctx2.user_data)

    # API me nahi mila → NOT FOUND + fallback + credit nahi kata
    Handler.mode = "invalid"
    il.clear_cache()
    ctx3 = Ctx(); fresh(USER, 5)
    await send_text(kb_label("imei"), ctx3, uid=USER)
    m4 = await send_text("353010111111110", ctx3, uid=USER)
    t4 = m4.all_text()
    ok("device na milne par NOT FOUND card", ("NOT FOUND" in t4.upper() or "NAHI MILE" in t4.upper()), t4[:220])
    ok("'credit nahi kata' likha hai", ("No credit was cut" in t4 or "credit nahi kata" in t4 or "Koi credit nahi kata" in t4), t4[:250])
    ok("fallback (imei.info) button mila", any("imei.info" in str(u or "") for u in _urls(m4)), _urls(m4))
    ok("not-found par credit nahi kata", dbm.get_credits(USER) == 5, dbm.get_credits(USER))
    Handler.mode = "apple"
    il.clear_cache()

    # 0 credits → block
    fresh(USER, 0)
    ctx4 = Ctx()
    m5 = await send_text(kb_label("imei"), ctx4, uid=USER)
    ok("0 credits par premium block", ("ALL CREDITS USED" in m5.all_text().upper() or "CREDITS KHATAM" in m5.all_text().upper()), m5.all_text()[:200])
    ok("block me VIP button", "open_vip_menu" in (m5.cb_data() or []), m5.cb_data())

    # VIP → unlimited
    fresh(USER, 0, vip=True)
    ctx5 = Ctx()
    await send_text(kb_label("imei"), ctx5, uid=USER)
    m6 = await send_text("353010111111110", ctx5, uid=USER)
    ok("VIP ko details mili (0 credits par bhi)", "Apple iPhone 12 mini" in m6.all_text(), m6.all_text()[:220])
    ok("VIP ke credits nahi kate", dbm.get_credits(USER) == 0, dbm.get_credits(USER))

    # API down → help card, credit safe
    os.environ["IMEI_API_BASE"] = "http://127.0.0.1:8799/api"     # kuch sun nahi raha
    il.clear_cache()
    fresh(USER, 5)
    ctx6 = Ctx()
    await send_text(kb_label("imei"), ctx6, uid=USER)
    m7 = await send_text("490154203237518", ctx6, uid=USER)
    ok("API down par saaf message", "not available" in m7.all_text().lower() or "*#06#" in m7.all_text(),
       m7.all_text()[:220])
    ok("API down par credit nahi kata", dbm.get_credits(USER) == 5, dbm.get_credits(USER))
    os.environ["IMEI_API_BASE"] = "http://127.0.0.1:8792/api"
    il.clear_cache()

    # callback: imei_new
    ctx7 = Ctx()
    q = await click("imei_new", ctx7, uid=USER)
    ok("'Check another IMEI' callback prompt laata hai", ("Now send the 15 digit IMEI" in q.message.all_text() or "Ab 15 digit IMEI bhejo" in q.message.all_text()),
       q.message.all_text()[:200])
    ok("callback mode set karta hai", ctx7.user_data.get("mode") == "imei", ctx7.user_data)

    # imeiagain callback
    fresh(USER, 5)
    ctx8 = Ctx()
    q2 = await click("imeiagain:353010111111110", ctx8, uid=USER)
    ok("'Check again' callback report deta hai", "Apple iPhone 12 mini" in q2.message.all_text(),
       q2.message.all_text()[:200])

    # admin status
    ctxa = Ctx()
    ma = await run_cmd(bot.cmd_imeistatus, ctxa, uid=OWNER, args=["353010111111110"])
    ok("/imeistatus admin ko test dikhata hai", "IMEI API is working" in ma.all_text(), ma.all_text()[:220])
    ctxb = Ctx()
    mb = await run_cmd(bot.cmd_imeistatus, ctxb, uid=123456789, args=["353010111111110"])
    ok("/imeistatus non-admin ko kuch nahi", not mb.all_text().strip(), mb.all_text()[:120])


asyncio.run(flows())

ALL_PASS, ALL_FAIL = _PRE_PASS + PASS, _PRE_FAIL + FAIL
print("\n" + "=" * 70)
print(f"V41 IMEI / PHONE DETAILS — PASS: {len(ALL_PASS)} | FAIL: {len(ALL_FAIL)}")
for f in ALL_FAIL:
    print("  ❌", f)
print("=" * 70)
sys.exit(1 if ALL_FAIL else 0)
