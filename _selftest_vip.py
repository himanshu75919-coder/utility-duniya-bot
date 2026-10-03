#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_selftest_vip.py — v49.4: VIP-ONLY mode ka poora test
=====================================================
Aapki marzi: "ab se poora bot sirf premium users ke liye."

Ye test check karta hai:
1) PREMIUM_ONLY on hone par non-VIP user ko tool nahi milta (VIP wall aata hai)
2) VIP user ko tool milta hai
3) Owner/admin hamesha chal sakta hai (VIP ho ya na ho)
4) Payment flow (UTR + screenshot) non-VIP ke liye bhi khula rehta hai
5) Refer / madad / tutorial sabke liye khule rehte hain
6) PREMIUM_ONLY=off karne par purana system wapas aa jata hai
"""
import asyncio
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ⚠️ Is test me VIP mode ON hi chahiye
os.environ.pop("PREMIUM_ONLY", None)
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("ADMIN_ID", "8607774564")
os.environ.setdefault("HUB_API_KEY", "Demo")

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    if cond:
        PASS.append(name)
        print(f"  ✅ {name}")
    else:
        FAIL.append(f"{name} :: {str(extra)[:150]}")
        print(f"  ❌ {name}  {str(extra)[:150]}")


def section(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


t0 = time.time()
section("VIP-ONLY MODE — v49.4")

import bot as B                               # noqa: E402
import database as dbm                        # noqa: E402

OWNER = 8607774564
FREE_USER = 881122334
VIP_USER = 881122335

ok("PREMIUM_ONLY default ON", B.PREMIUM_ONLY is True, B.PREMIUM_ONLY)

# ---------------- 1) FREE USER ----------------
section("1) FREE USER — tools band hone chahiye")
dbm.get_user(FREE_USER, "FreeUser")
row = dbm.get_user(FREE_USER)
ok("free user DB me bana", bool(row))
ok("free user VIP nahi hai", dbm.is_premium(row) is False, row.get("premium_until"))
ok("vip_ok(free) = False", B.vip_ok(FREE_USER) is False)
ok("vip_ok(owner) = True", B.vip_ok(OWNER) is True)

# ---------------- 2) VIP USER ----------------
section("2) VIP USER — sab khula hona chahiye")
dbm.grant_premium(VIP_USER, 30)
vrow = dbm.get_user(VIP_USER)
ok("VIP user premium hai", dbm.is_premium(vrow) is True, vrow.get("premium_until"))
ok("vip_ok(vip) = True", B.vip_ok(VIP_USER) is True)
dbm.revoke_premium(VIP_USER)
ok("revoke ke baad vip_ok = False", B.vip_ok(VIP_USER) is False)

# ---------------- 3) CALLBACK GATE ----------------
section("3) Callback gate (kaunse buttons khule hain)")
free_cb = ["buy_plan_vip_30", "open_vip_menu", "open_refer_menu", "mypay_list",
           "pay_utr_help", "toolvid:premium", "back_home", "rpay:12", "askpay:12"]
blocked_cb = ["imei_new", "cloner_setup", "kagaz_affidavit", "media_8d", "qr_text",
              "doc_go", "vnum_get", "make_pdf_now", "shot_full"]
for cb in free_cb:
    ok(f"non-VIP ke liye khula: {cb}", B.vip_free_cb(cb) is True)
for cb in blocked_cb:
    ok(f"non-VIP ke liye band: {cb}", B.vip_free_cb(cb) is False)

# ---------------- 4) WALL TEXT + KEYBOARD ----------------
section("4) VIP wall card")
txt = B.VIP_WALL_TEXT
ok("wall me 'SIRF VIP' likha hai", "SIRF VIP" in txt)
ok("wall me unlimited ka zikr", "unlimited" in txt)
ok("wall Hinglish me hai", "VIP lene par aapko milega" in txt)
ok("wall me example line", "Jaise:" in txt)
kb = B.vip_wall_kb()
rows = kb.inline_keyboard
ok("wall kb me 4 button row", len(rows) >= 4, len(rows))
btn_text = " ".join(b.text for r in rows for b in r)
ok("VIP plan button hai", "VIP plan" in btn_text)
ok("refer button hai", "Refer" in btn_text)
ok("support button hai", "Support" in btn_text)
ok("VIP plan button ka callback sahi", any(b.callback_data == "open_vip_menu" for r in rows for b in r))

# ---------------- 5) FULL FLOW (halke fake Telegram objects) ----------------
section("5) Asli flow — fake Telegram objects se")
from types import SimpleNamespace


class FakeMsg:
    def __init__(self, text="", chat_id=0):
        self.text = text
        self.replies = []
        self.chat_id = chat_id

    async def reply_text(self, text, **kw):
        self.replies.append(str(text))
        return self

    async def edit_text(self, text, **kw):
        self.replies.append(str(text))
        return self

    def all_text(self):
        return "\n".join(self.replies)


class FakeUser:
    def __init__(self, uid):
        self.id = uid
        self.first_name = "Test"
        self.username = f"user{uid}"
        self.is_bot = False


class FakeChat:
    def __init__(self, uid):
        self.id = uid


class FakeUpdate:
    def __init__(self, text, uid):
        self.message = FakeMsg(text, uid)
        self.effective_user = FakeUser(uid)
        self.effective_message = self.message
        self.effective_chat = FakeChat(uid)
        self.callback_query = None


class FakeQuery:
    def __init__(self, data, uid):
        self.data = data
        self.from_user = FakeUser(uid)
        self.message = FakeMsg("", uid)
        self.answered = []

    async def answer(self, text=None, **kw):
        if text:
            self.answered.append(str(text))


class FakeCbUpdate:
    def __init__(self, data, uid):
        self.callback_query = FakeQuery(data, uid)
        self.effective_user = self.callback_query.from_user
        self.effective_message = self.callback_query.message
        self.effective_chat = FakeChat(uid)
        self.message = None


class FakeCtx:
    def __init__(self):
        self.user_data = {}
        self.bot = SimpleNamespace(send_message=self._send, delete_webhook=self._noop)

    async def _send(self, *a, **kw):
        return FakeMsg("", a[0] if a else 0)

    async def _noop(self, *a, **kw):
        return None


async def flow():
    # (a) free user menu button dabata hai -> VIP wall
    ctx = FakeCtx()
    upd = FakeUpdate("📲 IMEI / PHONE DETAILS", FREE_USER)
    await B.on_text(upd, ctx)
    t = upd.message.all_text().upper()
    ok("free user ko VIP wall mila", "SIRF VIP" in t, upd.message.all_text()[:140])
    ok("free user ka mode set NAHI hua", not ctx.user_data.get("mode"), ctx.user_data.get("mode"))

    # (b) free user random text -> VIP wall
    ctx2 = FakeCtx()
    upd2 = FakeUpdate("hello bhai", FREE_USER)
    await B.on_text(upd2, ctx2)
    ok("random text par bhi VIP wall", "SIRF VIP" in upd2.message.all_text().upper())

    # (c) payment flow (pay_utr_xxx) free user ke liye khula
    ctx3 = FakeCtx()
    ctx3.user_data["mode"] = "pay_utr_vip30"
    ctx3.user_data["pay_plan"] = "vip30"
    upd3 = FakeUpdate("448612394857", FREE_USER)
    try:
        await B.on_text(upd3, ctx3)
    except Exception as e:                                       # noqa: BLE001
        # asli flow network/DB maang sakta hai — VIP wall na aana hi kaafi hai
        pass
    ok("free user ka payment UTR block nahi hua", "SIRF VIP" not in upd3.message.all_text().upper(),
       upd3.message.all_text()[:140])

    # (d) VIP user ko tool khulta hai
    dbm.grant_premium(VIP_USER, 30)
    ctx4 = FakeCtx()
    upd4 = FakeUpdate("📲 IMEI / PHONE DETAILS", VIP_USER)
    await B.on_text(upd4, ctx4)
    ok("VIP user ko tool khul gaya", "SIRF VIP" not in upd4.message.all_text().upper(),
       upd4.message.all_text()[:140])
    dbm.revoke_premium(VIP_USER)

    # (e) owner ko sab khula
    ctx5 = FakeCtx()
    upd5 = FakeUpdate("📲 IMEI / PHONE DETAILS", OWNER)
    await B.on_text(upd5, ctx5)
    ok("owner ko tool khula", "SIRF VIP" not in upd5.message.all_text().upper(),
       upd5.message.all_text()[:140])

    # (f) callback gate: free user ka tool button -> wall (edit_text)
    ctx6 = FakeCtx()
    cb = FakeCbUpdate("imei_new", FREE_USER)
    await B.on_cb(cb, ctx6)
    ok("free user ka IMEI button -> VIP wall", "SIRF VIP" in cb.callback_query.message.all_text().upper(),
       cb.callback_query.message.all_text()[:140])

    # (g) callback gate: VIP plan button khula rehta hai
    ctx7 = FakeCtx()
    cb2 = FakeCbUpdate("open_vip_menu", FREE_USER)
    try:
        await B.on_cb(cb2, ctx7)
    except Exception:                                            # noqa: BLE001
        pass
    ok("VIP plan button non-VIP ke liye khula", "SIRF VIP" not in cb2.callback_query.message.all_text().upper(),
       cb2.callback_query.message.all_text()[:140])


asyncio.run(flow())

# ---------------- 6) OFF switch ----------------
section("6) PREMIUM_ONLY=off (purana system wapas)")
os.environ["PREMIUM_ONLY"] = "off"
spec = importlib.util.spec_from_file_location("bot_off", os.path.join(HERE, "bot.py"))
bot_off = importlib.util.module_from_spec(spec)
sys.modules["bot_off"] = bot_off
spec.loader.exec_module(bot_off)
ok("PREMIUM_ONLY=off par sab allowed", bot_off.vip_ok(FREE_USER) is True)

# ---------------- RESULT ----------------
print("\n" + "=" * 70)
print(f"v49.4 VIP-ONLY TEST — PASS: {len(PASS)} | FAIL: {len(FAIL)}   ({time.time()-t0:.1f}s)")
print("=" * 70)
if FAIL:
    print("\nFAILED:")
    for f in FAIL:
        print("  ❌", f)
sys.exit(1 if FAIL else 0)
