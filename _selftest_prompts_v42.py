"""v42 TEST — CHHOTE PROMPTS (jaise user ne video me dikhaya).

Rule (user ka): koi bhi tool khole → TITLE + 1 line kaam ki baat + 📌 Example + "Now send ..."
Koi lambi instruction list nahi (tutorial video har tool ke neeche hai, wahi samjhata hai).
"""
import asyncio
import os
import re
import sys

os.environ.setdefault("PREMIUM_ONLY", "off")   # tools ka behaviour test karne ke liye
import unicodedata

os.environ["DB_PATH"] = "/tmp/_prompts42.db"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Chat, Update, User  # noqa: E402
from telegram.constants import ChatType  # noqa: E402

import bot  # noqa: E402
import database as dbm  # noqa: E402

PASS, FAIL = [], []
OWNER = 8607774564
USER = 777000222
MENU_TOOLS = ("kagaz", "mediastudio", "clips")   # menu/video-tool: Example ki jagah Limit line


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {str(detail)[:200]}" if detail and not cond else ""))


def norm(t):
    return unicodedata.normalize("NFKC", t or "")


def clean_key(text):
    n = bot.unbold(text).strip().upper()
    return re.sub(r"^[^\w\s]+\s*", "", n).strip()


# ======================================================================
# 1) HAR PROMPT KA STYLE
# ======================================================================
def test_prompt_style():
    print("\n--- 1) HAR TOOL KA PROMPT: CHHOTA + EXAMPLE + ASK ---")
    too_long, no_example, no_ask, has_bullet, has_sep = [], [], [], [], []
    for k in sorted(bot.PROMPTS):
        p = bot.tool_prompt(k)
        lines = [l for l in p.split("\n") if l.strip()]
        if len(lines) > 5 or len(p) > 320:
            too_long.append((k, len(lines), len(p)))
        if k not in MENU_TOOLS and "Example" not in p:
            no_example.append(k)
        last = lines[-1].lower()
        if not any(w in last for w in ("send", "type", "select", "pick", "tap", "open", "forward",
                                       "choose", "example", "now")):
            no_ask.append((k, lines[-1][:60]))
        if any(l.strip().startswith(("•", "-")) for l in lines):
            has_bullet.append(k)
        if "━━━" in p:
            has_sep.append(k)
    ok(f"saare {len(bot.PROMPTS)} prompts 5 line + 320 char ke andar", not too_long, too_long)
    ok("har input-tool me 📌 Example hai", not no_example, no_example)
    ok("har prompt aakhir me mangta hai (Now send...)", not no_ask, no_ask)
    ok("prompt me koi lambi bullet list nahi", not has_bullet, has_bullet)
    ok("prompt me koi separator line nahi (clean look)", not has_sep, has_sep)


# ======================================================================
# 2) KHAS TOOLS (user ne video me ye maange)
# ======================================================================
def test_special_prompts():
    print("\n--- 2) JO USER NE VIDEO ME BOLAA ---")
    tb = bot.tool_prompt("terabox")
    ok("terabox: ad-free likha hai", "ad-free" in tb.lower(), tb)
    ok("terabox: 'dobara link bhejo' wali line", "again" in tb.lower(), tb)
    ok("terabox: example link", "terabox.com" in tb, tb)

    ni = bot.tool_prompt("numinfo")
    ok("numinfo: 10 digit number maangta hai", "10 digit" in ni.lower(), ni)
    ok("numinfo: example number set hai (9876543210)", "9876543210" in ni, ni)
    ok("numinfo: chhota (4 line)", len([l for l in ni.split("\n") if l.strip()]) <= 5, ni)

    veh = bot.tool_prompt("rto")
    ok("vehicle: example plate hai", "BR30AR0802" in veh, veh)
    ok("vehicle: lambi bullet list nahi", "•" not in veh, veh)

    im = bot.tool_prompt("imei")
    ok("imei: *#06# ka tarika", "*#06#" in im, im)
    ok("imei: example IMEI hai", "353010111111110" in im, im)
    ok("imei: chhota (5 line)", len([l for l in im.split("\n") if l.strip()]) <= 5, im)

    for k, want in (("ifsc", "SBIN0000001"), ("pin", "800001"), ("pin", "Rajendra Nagar"),
                    ("short", "example.com"), ("appfind", "instagram"), ("ip", "8.8.8.8"),
                    ("qr", "t.me/"), ("linkcheck", "sbi-kyc-verify"), ("shot", "github.com")):
        p = bot.tool_prompt(k)
        ok(f"{k}: example '{want}'", want in p, p)

    kg = bot.KAGAZ_MENU_TEXT
    ok("kagaz menu chhota (4 line)", len([l for l in kg.split("\n") if l.strip()]) <= 5, kg)
    ok("kagaz menu me 'Select from the menu' line", "Select from the menu" in kg, kg)
    md = bot.MEDIA_MENU_TEXT
    ok("media studio menu chhota (4 line)", len([l for l in md.split("\n") if l.strip()]) <= 5, md)


# ======================================================================
# 3) ASLI FLOW (Telegram) — prompt chhota dikhe
# ======================================================================
class FakeSent:
    message_id = 1

    def __init__(self, owner=None):
        self.owner = owner
        self.chat = Chat(id=1, type=ChatType.PRIVATE)

    async def delete(self):
        return True


class FakeMsg:
    def __init__(self, text="", uid=USER):
        self.text = text
        self.replies = []
        self.chat = Chat(id=uid, type=ChatType.PRIVATE)
        self.from_user = User(id=uid, first_name="Tester", is_bot=False)
        self.message_id = 7

    async def reply_text(self, text, **kw):
        self.replies.append((text, kw))
        return FakeSent(self)

    def all_text(self):
        parts = []
        for t, kw in self.replies:
            parts.append(t if isinstance(t, str) else "")
            kb = (kw or {}).get("reply_markup")
            if kb is not None and getattr(kb, "inline_keyboard", None):
                for row in kb.inline_keyboard:
                    parts.append(" | ".join(b.text for b in row))
        return norm("\n".join(parts))

    def first(self):
        return self.replies[0][0] if self.replies else ""


class Ctx:
    def __init__(self):
        self.user_data = {}
        self.args = []
        self.bot = type("B", (), {"id": 999})()


def kb_label(action):
    for row in bot.KB_BTNS:
        for b in row:
            if bot.BTN_MODE_MAP.get(clean_key(b)) == action:
                return b
    return ""


async def flows():
    print("\n--- 3) ASLI FLOW: TOOL KHOLNE PAR KYA DIKHTA HAI ---")
    for action, label in (("numinfo", "NUMBER INFO"), ("ifsc", "IFSC"), ("rto", "VEHICLE"),
                          ("imei", "IMEI"), ("terabox", "TERABOX")):
        dbm.set_credits(USER, 25)
        dbm.get_user(USER, "Tester")
        ctx = Ctx()
        m = FakeMsg(kb_label(action), uid=USER)
        upd = Update(update_id=1, message=m)
        upd.message.from_user = User(id=USER, first_name="Tester", is_bot=False)
        await bot.on_text(upd, ctx)
        shown = m.first()
        lines = [l for l in shown.split("\n") if l.strip()]
        # 4-5 line ka prompt + credits line + /cancel line = max 7
        ok(f"{action}: card chhota (max 7 line)", len(lines) <= 7, shown)
        ok(f"{action}: card me example/ask line", ("Example" in shown or "Now send" in shown or "Jaise:" in shown or "bhejo" in shown
                                                   or "Select" in shown), shown[:150])

    # premium tool par sirf 1 credits line (lambi explanation nahi)
    dbm.set_credits(USER, 25)
    ctx = Ctx()
    m = FakeMsg(kb_label("numinfo"), uid=USER)
    upd = Update(update_id=2, message=m)
    upd.message.from_user = User(id=USER, first_name="Tester", is_bot=False)
    await bot.on_text(upd, ctx)
    full = m.all_text()
    ok("premium card me credits line hai", "Credits" in full, full[:200])
    ok("premium card me '(1 use of this tool = 1 credit)' line GAYAB", "1 use of this tool" not in full, full)


asyncio.run(flows())

print("\n" + "=" * 70)
print(f"V42 CHHOTE PROMPTS — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
for f in FAIL:
    print("  ❌", f)
print("=" * 70)
sys.exit(1 if FAIL else 0)
