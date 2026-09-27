#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
All-in-One Utility Telegram Bot
- 10 free tools (koi paid API nahi)
- Referral system + UPI premium + force-join channel + admin panel
- Deploy: Render.com free plan (webhook) ya apne PC/phone par (polling)
"""

import asyncio
import io
import logging
import os
import random
import re
import sqlite3
import string
from datetime import date, datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

import qrcode
import requests
from PIL import Image
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "").strip()          # jaise @MyChannel (khali = band)
FORCE_CHANNEL_LINK = os.getenv("FORCE_CHANNEL_LINK", "").strip()  # jaise https://t.me/MyChannel
UPI_ID = os.getenv("UPI_ID", "").strip()                        # jaise name@upi
UPI_NAME = os.getenv("UPI_NAME", "UtilityBot").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()              # Render URL, jaise https://xxx.onrender.com
FREE_LIMIT = int(os.getenv("FREE_LIMIT", "15") or 15)           # free user: roz ke uses
REFER_NEED = int(os.getenv("REFER_NEED", "5") or 5)             # itne refer = 30 din premium
DB_PATH = os.getenv("DB_PATH", "botdata.db")

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger("utility-bot")

# ---------------- DATABASE ----------------
def db():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            name TEXT DEFAULT '',
            uses_today INTEGER DEFAULT 0,
            last_date TEXT DEFAULT '',
            premium_until TEXT DEFAULT '',
            referred_by INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            joined_at TEXT DEFAULT ''
        )"""
    )
    return con


def get_user(uid: int, name: str = "") -> dict:
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    today = date.today().isoformat()
    if not row:
        cur.execute(
            "INSERT INTO users(user_id,name,uses_today,last_date,joined_at) VALUES(?,?,0,?,?)",
            (uid, (name or "")[:60], today, datetime.now().isoformat(timespec="seconds")),
        )
        con.commit()
        con.close()
        return {"user_id": uid, "name": name, "uses_today": 0, "last_date": today,
                "premium_until": "", "referred_by": 0, "referrals": 0}
    cols = [d[0] for d in cur.description]
    u = dict(zip(cols, row))
    if u["last_date"] != today:
        cur.execute("UPDATE users SET uses_today=0,last_date=? WHERE user_id=?", (today, uid))
        con.commit()
        u["uses_today"] = 0
        u["last_date"] = today
    con.close()
    return u


def add_use(uid: int):
    con = db()
    con.execute("UPDATE users SET uses_today=uses_today+1 WHERE user_id=?", (uid,))
    con.commit()
    con.close()


def is_premium(u: dict) -> bool:
    try:
        return datetime.fromisoformat(u["premium_until"]) > datetime.now() if u["premium_until"] else False
    except Exception:
        return False


def grant_premium(uid: int, days: int) -> str:
    con = db()
    cur = con.cursor()
    cur.execute("SELECT premium_until FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    base = datetime.now()
    if row and row[0]:
        try:
            d = datetime.fromisoformat(row[0])
            if d > base:
                base = d
        except Exception:
            pass
    new = (base + timedelta(days=days)).isoformat(timespec="seconds")
    cur.execute("UPDATE users SET premium_until=? WHERE user_id=?", (new, uid))
    con.commit()
    con.close()
    return new


def add_referral(new_uid: int, ref_uid: int) -> int:
    """Naye user ko referrer se jodo. Referrer ka naya count lautao (0 = invalid)."""
    if new_uid == ref_uid or ref_uid <= 0:
        return 0
    con = db()
    cur = con.cursor()
    cur.execute("SELECT referred_by FROM users WHERE user_id=?", (new_uid,))
    r = cur.fetchone()
    if r and r[0]:
        con.close()
        return 0
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (ref_uid,))
    if not cur.fetchone():
        con.close()
        return 0
    cur.execute("UPDATE users SET referred_by=? WHERE user_id=?", (ref_uid, new_uid))
    cur.execute("UPDATE users SET referrals=referrals+1 WHERE user_id=?", (ref_uid,))
    cur.execute("SELECT referrals FROM users WHERE user_id=?", (ref_uid,))
    row = cur.fetchone()
    con.commit()
    con.close()
    return row[0] if row else 0


def all_user_ids():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users")
    ids = [r[0] for r in cur.fetchall()]
    con.close()
    return ids


def stats():
    con = db()
    cur = con.cursor()
    today = date.today().isoformat()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_date=?", (today,))
    active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE premium_until > ?", (datetime.now().isoformat(timespec="seconds"),))
    prem = cur.fetchone()[0]
    con.close()
    return total, active, prem

# ---------------- PURE HELPERS (testable) ----------------
BOLD = {**{chr(97 + i): chr(0x1D41A + i) for i in range(26)},
        **{chr(65 + i): chr(0x1D400 + i) for i in range(26)},
        **{chr(48 + i): chr(0x1D7CE + i) for i in range(10)}}
ITALIC = {**{chr(97 + i): chr(0x1D44E + i) for i in range(26)},
          **{chr(65 + i): chr(0x1D434 + i) for i in range(26)}}
MONO = {**{chr(97 + i): chr(0x1D68A + i) for i in range(26)},
        **{chr(65 + i): chr(0x1D670 + i) for i in range(26)},
        **{chr(48 + i): chr(0x1D7F6 + i) for i in range(10)}}
BUBBLE = {**{chr(97 + i): chr(0x24D0 + i) for i in range(26)},
          **{chr(65 + i): chr(0x24B6 + i) for i in range(26)},
          "0": "⓪", **{chr(49 + i): chr(0x2460 + i) for i in range(9)}}
SMALL = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ",
         "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
         "o": "ᴏ", "p": "ᴘ", "q": "Q", "r": "ʀ", "s": "ꜱ", "t": "ᴛ", "u": "ᴜ",
         "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}

FONTS = [("Bold", BOLD, False), ("Italic", ITALIC, False), ("Mono", MONO, False),
         ("Bubble", BUBBLE, False), ("Small Caps", SMALL, True)]


def style_text(t: str, table: dict, fold: bool = False) -> str:
    if fold:
        return "".join(table.get(c.lower(), c) for c in t)
    return "".join(table.get(c, c) for c in t)


def make_qr_bytes(text: str) -> io.BytesIO:
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio


def gen_password(n: int) -> str:
    n = max(4, min(int(n), 64))
    alphabet = string.ascii_letters + string.digits + "@#$%&*"
    return "".join(random.choice(alphabet) for _ in range(n))


def calc_emi(p: float, annual: float, months: int) -> float:
    r = annual / 12 / 100
    if r <= 0:
        return p / months
    f = (1 + r) ** months
    return p * r * f / (f - 1)


def calc_age(dob: date):
    today = date.today()
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    try:
        bday = date(today.year, dob.month, dob.day)
    except ValueError:
        bday = date(today.year, 2, 28)
    if bday < today:
        try:
            bday = date(today.year + 1, dob.month, dob.day)
        except ValueError:
            bday = date(today.year + 1, 2, 28)
    return years, (bday - today).days, (today - dob).days


def shorten(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    r = requests.get("https://is.gd/create.php", params={"format": "simple", "url": url}, timeout=12)
    return r.text.strip()


YT_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})")


def yt_id(link: str):
    m = YT_RE.search(link or "")
    return m.group(1) if m else None

# ---------------- UI TEXT ----------------
MENU_BTNS = [
    [("📷 QR Code", "qr"), ("✍️ Stylish Fonts", "font")],
    [("🔐 Password", "pwd"), ("🖼️ Image→PDF", "pdf")],
    [("🗜️ Compress Photo", "comp"), ("🔗 URL Short", "short")],
    [("🎬 YT Thumbnail", "yt"), ("📝 Text Tools", "text")],
    [("🧮 EMI Calc", "emi"), ("🎂 Age Calc", "age")],
    [("💎 Premium", "prem"), ("🎁 Refer & Earn", "ref")],
    [("👤 My Account", "acc")],
]


def menu_markup():
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d) for t, d in row] for row in MENU_BTNS])


BACK = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menu", callback_data="menu")]])

WELCOME = (
    "👋 Namaste! Main hoon Utility Bot\n\n"
    "10 kaam ke tools, bilkul FREE:\n"
    "📷 QR Code • ✍️ Stylish Fonts • 🔐 Password\n"
    "🖼️ Image→PDF • 🗜️ Photo Compress • 🔗 URL Short\n"
    "🎬 YT Thumbnail • 📝 Text Tools • 🧮 EMI • 🎂 Age\n\n"
    f"🆓 Roz {FREE_LIMIT} FREE uses. Unlimited chahiye?\n"
    f"🎁 {REFER_NEED} doston ko refer karo = 30 din Premium FREE\n"
    "💎 ya sirf ₹49 me Premium lo\n\n"
    "👇 Neeche se koi tool chuno:"
)

LIMIT_MSG = (
    "⏳ Aaj ka FREE limit khatam! (roz {lim} uses)\n\n"
    "Unlimited paane ke 2 tareeke:\n"
    "🎁 {need} doston ko refer karo = 30 din FREE Premium\n"
    "💎 ya ₹49 me Premium lo\n\n"
    "Kal limit apne aap reset ho jayegi. 👍"
)

# ---------------- GUARDS ----------------
async def ensure_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Force-join channel check. Fail-open: kuch gadbad ho to block mat karo."""
    if not FORCE_CHANNEL or not FORCE_CHANNEL_LINK:
        return True
    uid = update.effective_user.id
    try:
        m = await context.bot.get_chat_member(FORCE_CHANNEL, uid)
        if m.status in ("member", "administrator", "creator"):
            return True
    except Exception as e:
        log.warning("force-join check fail-open: %s", e)
        return True
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel Join Karo", url=FORCE_CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Join Kar Liya", callback_data="joincheck")],
    ])
    msg = ("🔒 Pehle hamara channel join karo, phir saare tools FREE use karo!\n\n"
           "Join karke neeche ✅ dabao 👇")
    if update.callback_query:
        try:
            await update.callback_query.answer("Pehle channel join karo! 🔒", show_alert=True)
        except Exception:
            pass
        await update.callback_query.message.reply_text(msg, reply_markup=kb)
    else:
        await update.message.reply_text(msg, reply_markup=kb)
    return False


async def use_or_block(uid: int, update: Update) -> bool:
    u = get_user(uid)
    if is_premium(u):
        return True
    if u["uses_today"] < FREE_LIMIT:
        add_use(uid)
        return True
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Refer & Earn", callback_data="ref")],
        [InlineKeyboardButton("💎 Premium (₹49)", callback_data="prem")],
    ])
    txt = LIMIT_MSG.format(lim=FREE_LIMIT, need=REFER_NEED)
    if update.callback_query:
        await update.callback_query.message.reply_text(txt, reply_markup=kb)
    else:
        await update.message.reply_text(txt, reply_markup=kb)
    return False

# ---------------- COMMANDS ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, user.first_name or "")
    # referral
    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_id = int(context.args[0].split("_")[1])
            count = add_referral(user.id, ref_id)
            if count:
                await update.message.reply_text(f"🎉 Welcome! Tum refer hokar aaye ho. Roz {FREE_LIMIT} FREE uses milenge!")
                try:
                    if count % REFER_NEED == 0:
                        grant_premium(ref_id, 30)
                        await context.bot.send_message(
                            ref_id, f"🎉 Badhai! {count} referrals pure! Tumhe 30 din ka Premium FREE mil gaya 💎")
                    else:
                        await context.bot.send_message(
                            ref_id, f"🎁 1 naya referral! Total: {count}/{REFER_NEED}. {REFER_NEED - (count % REFER_NEED)} aur = 30 din Premium FREE!")
                except Exception:
                    pass
        except Exception:
            pass
    if not await ensure_joined(update, context):
        return
    await update.message.reply_text(WELCOME, reply_markup=menu_markup())


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_joined(update, context):
        return
    await update.message.reply_text("👇 Koi tool chuno:", reply_markup=menu_markup())


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("mode", None)
    await update.message.reply_text("❌ Cancel ho gaya.", reply_markup=menu_markup())


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ HELP\n\n/menu - saare tools\n/premium - premium plans\n/refer - refer & earn\n/account - mera account\n/cancel - chal raha kaam cancel\n\n"
        f"Roz {FREE_LIMIT} FREE uses. /refer se unlimited FREE pao! 🎁")


async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    prem = "💎 ACTIVE" if is_premium(u) else "Free"
    left = "Unlimited ♾️" if is_premium(u) else f"{max(0, FREE_LIMIT - u['uses_today'])}/{FREE_LIMIT} bache"
    await update.message.reply_text(
        f"👤 MY ACCOUNT\n\n⭐ Plan: {prem}\n📊 Aaj ke uses: {left}\n🎁 Referrals: {u['referrals']}\n\n"
        f"{REFER_NEED} referrals = 30 din Premium FREE! /refer", reply_markup=BACK)


async def cmd_refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    me = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{u['user_id']}"
    need = REFER_NEED - (u["referrals"] % REFER_NEED)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Doston ko Share Karo", url=f"https://t.me/share/url?url={link}&text=FREE Utility Bot - QR, Fonts, PDF sab kuch!")],
        [InlineKeyboardButton("⬅️ Menu", callback_data="menu")],
    ])
    await update.message.reply_text(
        f"🎁 REFER & EARN (FREE Premium!)\n\nTumhara link:\n{link}\n\n"
        f"📊 Tumhare referrals: {u['referrals']}\n🎯 {need} aur referrals = 30 din Premium FREE!\n\n"
        "Dost link se /start karega = tumhe +1 referral. ✅", reply_markup=kb)


async def cmd_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not UPI_ID:
        await update.message.reply_text("💎 Premium jald aa raha hai! Tab tak /refer se FREE premium pao 🎁", reply_markup=BACK)
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 30 din - ₹49", callback_data="plan49")],
        [InlineKeyboardButton("🔥 90 din - ₹99", callback_data="plan99")],
        [InlineKeyboardButton("🎁 FREE me pao (Refer)", callback_data="ref")],
        [InlineKeyboardButton("⬅️ Menu", callback_data="menu")],
    ])
    await update.message.reply_text(
        "💎 PREMIUM PLANS\n\n⭐ 30 din = ₹49\n🔥 90 din = ₹99 (best value!)\n\n"
        "Premium me: ♾️ Unlimited uses + jaldi naye tools\n\n"
        "Plan chuno, UPI se pay karo, screenshot bhejo — 5 min me active! ⚡",
        reply_markup=kb)

# ---------------- ADMIN ----------------
def is_admin(uid: int) -> bool:
    return ADMIN_ID and uid == ADMIN_ID


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    t, a, p = stats()
    await update.message.reply_text(f"📊 STATS\n\n👥 Total users: {t}\n🟢 Aaj active: {a}\n💎 Premium: {p}")


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Use: /broadcast tumhara message")
        return
    ids = all_user_ids()
    ok = fail = 0
    await update.message.reply_text(f"📢 {len(ids)} users ko bhej raha hoon...")
    for uid in ids:
        try:
            await context.bot.send_message(uid, text)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await update.message.reply_text(f"✅ Broadcast done! Success: {ok}, Fail: {fail}")


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        uid = int(context.args[0]); days = int(context.args[1]) if len(context.args) > 1 else 30
    except Exception:
        await update.message.reply_text("Use: /approve <user_id> <din>")
        return
    grant_premium(uid, days)
    await update.message.reply_text(f"✅ {uid} ko {days} din premium de diya!")
    try:
        await context.bot.send_message(uid, f"💎 Badhai! Tumhara {days} din ka Premium ACTIVE ho gaya! 🎉")
    except Exception:
        pass

# ---------------- CALLBACKS ----------------
async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data or ""
    uid = update.effective_user.id
    try:
        await q.answer()
    except Exception:
        pass

    if data == "joincheck":
        if await ensure_joined(update, context):
            await q.message.reply_text(WELCOME, reply_markup=menu_markup())
        return

    if data == "menu":
        context.user_data.pop("mode", None)
        await q.message.reply_text("👇 Koi tool chuno:", reply_markup=menu_markup())
        return

    if data == "ref":
        await cmd_refer(update, context)
        return
    if data == "prem":
        await cmd_premium(update, context)
        return
    if data in ("plan49", "plan99"):
        if not UPI_ID:
            await q.message.reply_text("💎 Premium jald aa raha hai! /refer se FREE pao 🎁", reply_markup=BACK)
            return
        amt = "49" if data == "plan49" else "99"
        days = "30" if data == "plan49" else "90"
        upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={amt}&cu=INR&tn=UtilityBot{days}day"
        context.user_data["mode"] = "pay"
        context.user_data["plan_days"] = int(days)
        await q.message.reply_photo(
            photo=make_qr_bytes(upi_link),
            caption=(f"💎 {days} din Premium = ₹{amt}\n\n1️⃣ UPI app se is QR par ₹{amt} pay karo\n"
                     f"2️⃣ Payment ka SCREENSHOT yahin bhejo\n3️⃣ 5-10 min me Premium active! ⚡\n\nUPI ID: {UPI_ID}"),
            reply_markup=BACK)
        return

    # admin approve buttons: ap:<uid>:<days> / dc:<uid>
    if data.startswith("ap:") or data.startswith("dc:"):
        if not is_admin(uid):
            await q.message.reply_text("⛔ Sirf admin!")
            return
        parts = data.split(":")
        target = int(parts[1])
        if data.startswith("ap:"):
            days = int(parts[2]) if len(parts) > 2 else 30
            grant_premium(target, days)
            await q.message.reply_text(f"✅ {target} ko {days} din premium de diya!")
            try:
                await context.bot.send_message(target, f"💎 Badhai! Tumhara {days} din ka Premium ACTIVE ho gaya! 🎉")
            except Exception:
                pass
        else:
            await q.message.reply_text(f"❌ {target} ka payment reject kiya.")
            try:
                await context.bot.send_message(target, "❌ Tumhara payment verify nahi ho paya. Sahi screenshot dobara bhejo ya /premium me plan chuno.")
            except Exception:
                pass
        return

    # tool buttons need join check
    if not await ensure_joined(update, context):
        return

    if data == "pwd":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("8", callback_data="p8"), InlineKeyboardButton("12", callback_data="p12"),
             InlineKeyboardButton("16", callback_data="p16"), InlineKeyboardButton("20", callback_data="p20")],
            [InlineKeyboardButton("⬅️ Menu", callback_data="menu")],
        ])
        await q.message.reply_text("🔐 Kitne character ka password chahiye?", reply_markup=kb)
        return
    if data in ("p8", "p12", "p16", "p20"):
        if not await use_or_block(uid, update):
            return
        n = int(data[1:])
        pw = gen_password(n)
        await q.message.reply_text(f"🔐 Tumhara {n}-digit password:\n\n`{pw}`\n\n(Password ko dabakar copy karo. Kisi se share mat karo!)",
                                   reply_markup=BACK)
        return

    prompts = {
        "qr": "📷 QR Code banane ke liye koi bhi TEXT ya LINK bhejo:",
        "font": "✍️ Stylish banane ke liye apna naam/text bhejo:",
        "pdf": "🖼️ Jiss PHOTO ka PDF banana hai, wo bhejo:",
        "comp": "🗜️ Compress karne ke liye PHOTO bhejo:",
        "short": "🔗 Chhota karne ke liye LAMBA LINK bhejo:",
        "yt": "🎬 YouTube video ka LINK bhejo (thumbnail milega):",
        "text": "📝 Apna TEXT bhejo (words count + UPPER/lower sab milega):",
        "emi": "🧮 EMI Calculator\n\nLoan amount (₹) bhejo:\n(jaise: 100000)",
        "age": "🎂 Age Calculator\n\nApni birth date bhejo (DD-MM-YYYY):\n(jaise: 15-08-2005)",
        "acc": None,
    }
    if data == "acc":
        await cmd_account(update, context)
        return
    if data in prompts:
        context.user_data["mode"] = data
        await q.message.reply_text(prompts[data] + "\n\n/cancel kabhi bhi dabao.", reply_markup=BACK)
        return

# ---------------- MESSAGE ROUTERS ----------------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = context.user_data.get("mode")
    if not mode:
        await update.message.reply_text("👇 Pehle Menu se koi tool chuno:", reply_markup=menu_markup())
        return
    if not await ensure_joined(update, context):
        return
    text = (update.message.text or "").strip()

    # modes jo limit ke bahar (payment screenshot to photo me hai)
    if mode == "pay":
        await update.message.reply_text("📸 Payment ka SCREENSHOT photo ke roop me bhejo (text nahi).")
        return

    if mode == "qr":
        if not await use_or_block(uid, update):
            return
        if len(text) > 1000:
            await update.message.reply_text("⚠️ Text thoda chhota bhejo (1000 letters tak).")
            return
        await update.message.reply_photo(photo=make_qr_bytes(text), caption="📷 Tumhara QR Code ready! ✅", reply_markup=BACK)
        context.user_data.pop("mode", None)
        return

    if mode == "font":
        if not await use_or_block(uid, update):
            return
        if len(text) > 200:
            await update.message.reply_text("⚠️ 200 letters tak bhejo.")
            return
        out = "✍️ Stylish Fonts (dabakar copy karo):\n"
        for name, table, fold in FONTS:
            out += f"\n{name}:\n{style_text(text, table, fold)}\n"
        await update.message.reply_text(out, reply_markup=BACK)
        context.user_data.pop("mode", None)
        return

    if mode == "short":
        if not await use_or_block(uid, update):
            return
        try:
            s = shorten(text)
            if not s.startswith("http"):
                raise ValueError(s)
            await update.message.reply_text(f"🔗 Short link ready:\n\n{s}", reply_markup=BACK)
        except Exception:
            await update.message.reply_text("⚠️ Sahi link bhejo (jaise https://google.com). Dobara try karo:")
            return
        context.user_data.pop("mode", None)
        return

    if mode == "yt":
        if not await use_or_block(uid, update):
            return
        vid = yt_id(text)
        if not vid:
            await update.message.reply_text("⚠️ Sahi YouTube link bhejo. Dobara try karo:")
            return
        await update.message.reply_photo(
            photo=f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg",
            caption=f"🎬 Thumbnail mil gaya!\n🔗 https://youtu.be/{vid}", reply_markup=BACK)
        context.user_data.pop("mode", None)
        return

    if mode == "text":
        if not await use_or_block(uid, update):
            return
        words = len(text.split())
        chars = len(text)
        lines = text.count("\n") + 1
        await update.message.reply_text(
            f"📝 TEXT ANALYSIS\n\nWords: {words}\nCharacters: {chars}\nLines: {lines}\n\n"
            f"⬆️ UPPER:\n{text.upper()[:1000]}\n\n⬇️ lower:\n{text.lower()[:1000]}", reply_markup=BACK)
        context.user_data.pop("mode", None)
        return

    if mode == "emi":
        try:
            p = float(text.replace(",", "").replace("₹", "").strip())
            if p <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi amount bhejo (jaise 100000):")
            return
        context.user_data["emi_p"] = p
        context.user_data["mode"] = "emi_r"
        await update.message.reply_text(f"💰 Loan: ₹{p:,.0f}\n\nAb saal ka Interest Rate % bhejo:\n(jaise: 10)")
        return

    if mode == "emi_r":
        try:
            r = float(text.replace("%", "").strip())
            if r < 0 or r > 60:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi rate bhejo (jaise 10):")
            return
        context.user_data["emi_r"] = r
        context.user_data["mode"] = "emi_n"
        await update.message.reply_text("📅 Ab kitne MAHINE ka loan hai? (jaise: 12)")
        return

    if mode == "emi_n":
        try:
            n = int(float(text.strip()))
            if n <= 0 or n > 360:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi mahine bhejo (jaise 12):")
            return
        if not await use_or_block(uid, update):
            return
        p = context.user_data.get("emi_p", 0)
        r = context.user_data.get("emi_r", 0)
        emi = calc_emi(p, r, n)
        total = emi * n
        await update.message.reply_text(
            f"🧮 EMI RESULT\n\nLoan: ₹{p:,.0f}\nRate: {r}% saal\nTime: {n} mahine\n\n"
            f"💳 Monthly EMI: ₹{emi:,.0f}\n💰 Total payment: ₹{total:,.0f}\n📈 Total interest: ₹{total - p:,.0f}",
            reply_markup=BACK)
        context.user_data.pop("mode", None)
        return

    if mode == "age":
        m = re.match(r"^\s*(\d{1,2})[-/](\d{1,2})[-/](\d{4})\s*$", text)
        if not m:
            await update.message.reply_text("⚠️ Format: DD-MM-YYYY (jaise 15-08-2005):")
            return
        try:
            dob = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if dob > date.today():
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi date bhejo (jaise 15-08-2005):")
            return
        if not await use_or_block(uid, update):
            return
        years, to_bday, total_days = calc_age(dob)
        await update.message.reply_text(
            f"🎂 AGE RESULT\n\n🎉 Umar: {years} saal\n📅 Total din: {total_days:,}\n🎈 Birthday me: {to_bday} din bache",
            reply_markup=BACK)
        context.user_data.pop("mode", None)
        return

    if mode in ("pdf", "comp"):
        await update.message.reply_text("📸 Photo bhejo (text nahi). /cancel se wapas jao.")
        return


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = context.user_data.get("mode")
    if not mode:
        await update.message.reply_text("👇 Pehle Menu se tool chuno (Image→PDF / Compress):", reply_markup=menu_markup())
        return
    if not await ensure_joined(update, context):
        return

    # payment screenshot
    if mode == "pay":
        if not ADMIN_ID:
            await update.message.reply_text("⚠️ Admin set nahi hai. /cancel dabao.")
            return
        days = context.user_data.get("plan_days", 30)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"✅ Approve {days}din", callback_data=f"ap:{uid}:{days}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"dc:{uid}"),
        ]])
        try:
            await update.message.forward(ADMIN_ID)
            await context.bot.send_message(
                ADMIN_ID, f"💰 Naya payment!\nUser: {uid}\nNaam: {update.effective_user.first_name}\nPlan: {days} din",
                reply_markup=kb)
            await update.message.reply_text("✅ Screenshot mil gaya! 5-10 min me Premium active ho jayega. 🙏", reply_markup=BACK)
        except Exception:
            await update.message.reply_text("⚠️ Kuch gadbad hui, dobara bhejo.")
        context.user_data.pop("mode", None)
        return

    if mode not in ("pdf", "comp"):
        await update.message.reply_text("👇 Pehle Menu se tool chuno:", reply_markup=menu_markup())
        return
    if not await use_or_block(uid, update):
        return

    try:
        photo = update.message.photo[-1]
        f = await context.bot.get_file(photo.file_id)
        data = await f.download_as_bytearray()
        img = Image.open(io.BytesIO(bytes(data)))
    except Exception:
        await update.message.reply_text("⚠️ Photo kholne me dikkat. Dusri photo bhejo:")
        return

    if mode == "pdf":
        try:
            bio = io.BytesIO()
            img.convert("RGB").save(bio, format="PDF")
            bio.seek(0)
            bio.name = "photo.pdf"
            await update.message.reply_document(document=bio, caption="🖼️ Tumhara PDF ready! ✅", reply_markup=BACK)
        except Exception:
            await update.message.reply_text("⚠️ PDF banane me dikkat. Dusri photo try karo:")
            return
        context.user_data.pop("mode", None)
        return

    if mode == "comp":
        try:
            img2 = img.copy()
            img2.thumbnail((1280, 1280))
            bio = io.BytesIO()
            img2.convert("RGB").save(bio, format="JPEG", quality=55, optimize=True)
            before = len(data) / 1024
            after = bio.tell() / 1024
            bio.seek(0)
            bio.name = "compressed.jpg"
            await update.message.reply_document(
                document=bio,
                caption=f"🗜️ Compress ho gaya!\n📦 Pehle: {before:.0f} KB → Ab: {after:.0f} KB ✅",
                reply_markup=BACK)
        except Exception:
            await update.message.reply_text("⚠️ Compress me dikkat. Dusri photo try karo:")
            return
        context.user_data.pop("mode", None)
        return


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Error: %s", context.error)

# ---------------- MAIN ----------------
def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN nahi mila! .env file me BOT_TOKEN=... likho (README dekho).")
    db().close()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("account", cmd_account))
    app.add_handler(CommandHandler("refer", cmd_refer))
    app.add_handler(CommandHandler("premium", cmd_premium))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)

    if WEBHOOK_URL:
        port = int(os.getenv("PORT", "10000"))
        log.info("Webhook mode on port %s", port)
        app.run_webhook(listen="0.0.0.0", port=port, url_path=BOT_TOKEN,
                        webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}")
    else:
        log.info("Polling mode (apne PC/phone par chal raha hai)")
        app.run_polling()


if __name__ == "__main__":
    main()
