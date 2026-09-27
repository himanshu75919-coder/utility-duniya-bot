#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility Duniya Bot v2
- 12 tools (koi paid API nahi) + Telegram native bottom keyboard
- UPI Payment QR (sahi wala, GPay/PhonePe me chalega) + WhatsApp Link Generator
- Referral + UPI premium (screenshot direct ADMIN ko) + force-join + admin panel
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
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv()

import qrcode
import requests
from PIL import Image
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
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
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "").strip()
FORCE_CHANNEL_LINK = os.getenv("FORCE_CHANNEL_LINK", "").strip()
UPI_ID = os.getenv("UPI_ID", "").strip()
UPI_NAME = os.getenv("UPI_NAME", "UtilityBot").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
FREE_LIMIT = int(os.getenv("FREE_LIMIT", "15") or 15)
REFER_NEED = int(os.getenv("REFER_NEED", "5") or 5)
TRIAL_LIMIT = 2  # premium tools ke roz free trials
DB_PATH = os.getenv("DB_PATH", "botdata.db")

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)   # token logs me na dikhe
logging.getLogger("httpcore").setLevel(logging.WARNING)
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
    # v2 columns (purane users ka data safe rahega)
    for stmt in ("ALTER TABLE users ADD COLUMN trial_date TEXT DEFAULT ''",
                 "ALTER TABLE users ADD COLUMN trial_count INTEGER DEFAULT 0"):
        try:
            con.execute(stmt)
        except Exception:
            pass
    try:
        con.commit()
    except Exception:
        pass
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
                "premium_until": "", "referred_by": 0, "referrals": 0,
                "trial_date": today, "trial_count": 0}
    cols = [d[0] for d in cur.description]
    u = dict(zip(cols, row))
    if u.get("last_date") != today:
        cur.execute("UPDATE users SET uses_today=0,last_date=? WHERE user_id=?", (today, uid))
        con.commit()
        u["uses_today"] = 0
        u["last_date"] = today
    if u.get("trial_date") != today:
        try:
            cur.execute("UPDATE users SET trial_count=0,trial_date=? WHERE user_id=?", (today, uid))
            con.commit()
        except Exception:
            pass
        u["trial_count"] = 0
        u["trial_date"] = today
    con.close()
    return u


def add_use(uid: int):
    con = db()
    con.execute("UPDATE users SET uses_today=uses_today+1 WHERE user_id=?", (uid,))
    con.commit()
    con.close()


def add_trial(uid: int):
    con = db()
    con.execute("UPDATE users SET trial_count=trial_count+1 WHERE user_id=?", (uid,))
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

# ---------------- PURE HELPERS ----------------
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


def fetch_yt_thumb(vid: str):
    """Best quality thumbnail lao (khokhli/placeholder image ko reject karo)."""
    for q in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            r = requests.get(f"https://img.youtube.com/vi/{vid}/{q}.jpg", timeout=12)
            if r.status_code == 200 and len(r.content) > 5000:
                img = Image.open(io.BytesIO(r.content))
                if img.width > 150:  # 120px wala nakli placeholder reject
                    bio = io.BytesIO(r.content)
                    bio.seek(0)
                    return bio
        except Exception:
            continue
    return None


# ---- UPI payment QR (sahi format: upi://pay?pa=..&pn=..&cu=INR) ----
UPI_RE = re.compile(r"^[\w.\-]{2,256}@[a-zA-Z]{2,64}$")


def build_upi_link(pa: str, pn: str, amt=None) -> str:
    link = f"upi://pay?pa={pa}&pn={quote(pn or 'User')}&cu=INR"
    if amt:
        link += f"&am={amt:.2f}"
    return link


# ---- WhatsApp link ----
def normalize_phone(text: str):
    d = re.sub(r"\D", "", text or "")
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    if re.match(r"^[6-9]\d{9}$", d):
        return d
    return None


def build_wa_link(num: str, msg: str) -> str:
    base = f"https://wa.me/91{num}"
    return base + (f"?text={quote(msg)}" if msg else "")

# ---------------- UI ----------------
# (inline tools grid hata diya - saare tools ab Telegram ke Menu button me)


BACK = InlineKeyboardMarkup([[InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")]])

# Purana fixed keyboard hata diya - ab Telegram ka asli Menu button (grid) use hoga
# BTN_MODE sirf un users ke liye rakha hai jinke paas purana keyboard bacha ho


# Batch Hub style collapsible grid keyboard (grid icon se khulta/band hota hai)
KB_BTNS = [
    ["📷 QR Code", "✍️ Stylish Fonts"],
    ["🔐 Password", "🖼️ Image→PDF"],
    ["🗜️ Compress Photo", "🔗 URL Short"],
    ["🎬 YT Thumbnail", "📝 Text Tools"],
    ["🧮 EMI Calc", "🎂 Age Calc"],
    ["💰 UPI QR 💎", "📱 WA Link 💎"],
    ["💎 Premium", "🎁 Refer & Earn"],
    ["👤 My Account"],
]


def main_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t) for t in row] for row in KB_BTNS],
        resize_keyboard=True,
        input_field_placeholder="Grid dabao, tool chuno 👇",
    )


BTN_MODE = {
    "📷 QR Code": "qr", "✍️ Stylish Fonts": "font",
    "🖼️ Image→PDF": "pdf", "🗜️ Compress Photo": "comp",
    "🔗 URL Short": "short", "🎬 YT Thumbnail": "yt",
    "📝 Text Tools": "text", "🧮 EMI Calc": "emi",
    "🎂 Age Calc": "age", "💰 UPI QR 💎": "upi", "📱 WA Link 💎": "wa",
}

PROMPTS = {
    "qr": "📷 QR Code banane ke liye koi bhi TEXT ya LINK bhejo:",
    "font": "✍️ Stylish banane ke liye apna naam/text bhejo:",
    "pdf": "🖼️ Jiss PHOTO ka PDF banana hai, wo bhejo:",
    "comp": "🗜️ Compress karne ke liye PHOTO bhejo:",
    "short": "🔗 Chhota karne ke liye LAMBA LINK bhejo:",
    "yt": "🎬 YouTube video ka LINK bhejo (HD thumbnail milega):",
    "text": "📝 Apna TEXT bhejo (words count + UPPER/lower sab milega):",
    "emi": "🧮 EMI Calculator\n\nLoan amount (₹) bhejo:\n(jaise: 100000)",
    "age": "🎂 Age Calculator\n\nApni birth date bhejo (DD-MM-YYYY):\n(jaise: 15-08-2005)",
    "upi": "💰 UPI Payment QR (💎 Premium tool — roz 2 FREE trial)\n\nApni UPI ID bhejo:\n(jaise: name@okhdfc)",
    "wa": "📱 WhatsApp Link Generator (💎 Premium tool — roz 2 FREE trial)\n\nMobile number bhejo (10 digit):\n(jaise: 9876543210)",
}

WELCOME = (
    "👋 Namaste! Main hoon Utility Duniya Bot 🌟\n\n"
    "12 kaam ke tools, bilkul FREE:\n"
    "📷 QR • ✍️ Fonts • 🔐 Password • 🖼️ PDF\n"
    "🗜️ Compress • 🔗 Short • 🎬 YT • 📝 Text\n"
    "🧮 EMI • 🎂 Age • 💰 UPI QR 💎 • 📱 WA Link 💎\n\n"
    f"🆓 Roz {FREE_LIMIT} FREE uses + Premium tools ke {TRIAL_LIMIT} trials.\n"
    f"🎁 {REFER_NEED} doston ko refer karo = 30 din Premium FREE\n"
    "💎 ya sirf ₹49 me Premium lo\n\n"
    "📲 Neeche grid icon (▦) dabao — saare tools khulenge!\nDubara dabao to band ho jayega. 👇"
)

LIMIT_MSG = (
    "⏳ Aaj ka FREE limit khatam! (roz {lim} uses)\n\n"
    "Unlimited paane ke 2 tareeke:\n"
    "🎁 {need} doston ko refer karo = 30 din FREE Premium\n"
    "💎 ya ₹49 me Premium lo\n\n"
    "Kal limit apne aap reset ho jayegi. 👍"
)

TRIAL_MSG = (
    "🔒 {tool} Premium tool hai!\n\n"
    f"Roz ke {TRIAL_LIMIT} FREE trials khatam. Unlimited pao:\n"
    "💎 ₹49 me Premium lo\n"
    "🎁 ya {need} refer = 30 din FREE"
)

# ---------------- GUARDS ----------------
async def ensure_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
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


async def _send_limit_msg(update: Update, text: str):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Refer & Earn", callback_data="ref")],
        [InlineKeyboardButton("💎 Premium (₹49)", callback_data="prem")],
    ])
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)


async def use_or_block(uid: int, update: Update) -> bool:
    u = get_user(uid)
    if is_premium(u):
        return True
    if u["uses_today"] < FREE_LIMIT:
        add_use(uid)
        return True
    await _send_limit_msg(update, LIMIT_MSG.format(lim=FREE_LIMIT, need=REFER_NEED))
    return False


async def trial_or_block(uid: int, update: Update, tool: str) -> bool:
    """Premium tools: premium = unlimited, free = roz TRIAL_LIMIT trials."""
    u = get_user(uid)
    if is_premium(u):
        return True
    left = TRIAL_LIMIT - (u.get("trial_count") or 0)
    if left > 0:
        add_trial(uid)
        note = f"🎁 FREE Trial use ho gaya ({left - 1} bache aaj). Unlimited ke liye Premium lo! 💎"
        if update.callback_query:
            await update.callback_query.message.reply_text(note)
        else:
            await update.message.reply_text(note)
        return True
    await _send_limit_msg(update, TRIAL_MSG.format(tool=tool, need=REFER_NEED))
    return False

# ---------------- COMMANDS ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, user.first_name or "")
    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_id = int(context.args[0].split("_")[1])
            count = add_referral(user.id, ref_id)
            if count:
                await update.message.reply_text(
                    f"🎉 Welcome! Tum refer hokar aaye ho. Roz {FREE_LIMIT} FREE uses milenge!",
                    reply_markup=main_keyboard())
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
    await update.message.reply_text(WELCOME, reply_markup=main_keyboard())


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_joined(update, context):
        return
    await update.message.reply_text("⌨️ Neeche grid me saare tools hain — koi dabao 👇", reply_markup=main_keyboard())


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("mode", None)
    await update.message.reply_text("❌ Cancel ho gaya. /menu se dobara chuno.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ HELP\n\n📲 Neeche grid icon (▦) dabao = saare tools khulenge!\nKoi tool dabao, kaam shuru. ✅\n\n"
        "/menu - saare tools\n/premium - premium plans\n/refer - refer & earn\n/account - mera account\n/cancel - cancel\n\n"
        f"Roz {FREE_LIMIT} FREE uses + {TRIAL_LIMIT} premium trials. /refer se unlimited FREE pao! 🎁")


async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    prem = "💎 ACTIVE" if is_premium(u) else "Free"
    left = "Unlimited ♾️" if is_premium(u) else f"{max(0, FREE_LIMIT - u['uses_today'])}/{FREE_LIMIT} bache"
    trials = "Unlimited ♾️" if is_premium(u) else f"{max(0, TRIAL_LIMIT - (u.get('trial_count') or 0))}/{TRIAL_LIMIT} bache"
    await update.message.reply_text(
        f"👤 MY ACCOUNT\n\n⭐ Plan: {prem}\n📊 Aaj ke uses: {left}\n💎 Premium trials: {trials}\n🎁 Referrals: {u['referrals']}\n\n"
        f"{REFER_NEED} referrals = 30 din Premium FREE! /refer", reply_markup=BACK)


async def cmd_refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    me = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{u['user_id']}"
    need = REFER_NEED - (u["referrals"] % REFER_NEED)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Doston ko Share Karo", url=f"https://t.me/share/url?url={link}&text=FREE Utility Bot - QR, UPI QR, Fonts, PDF sab kuch!")],
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
        "Premium me:\n♾️ Unlimited saare uses\n💰 UPI QR + 📱 WA Link unlimited\n⚡ jaldi naye tools\n\n"
        "Plan chuno, UPI se pay karo, screenshot bhejo — kuch min me active! ⚡",
        reply_markup=kb)

# ---- Har tool ka apna /command (Telegram ke Menu/grid button me dikhega) ----
async def cmd_tool(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    if not await ensure_joined(update, context):
        return
    context.user_data["mode"] = mode
    await update.message.reply_text(PROMPTS[mode] + "\n\n/cancel kabhi bhi dabao.", reply_markup=BACK)


async def cmd_qr(update, context): await cmd_tool(update, context, "qr")
async def cmd_font(update, context): await cmd_tool(update, context, "font")
async def cmd_pdf(update, context): await cmd_tool(update, context, "pdf")
async def cmd_comp(update, context): await cmd_tool(update, context, "comp")
async def cmd_short(update, context): await cmd_tool(update, context, "short")
async def cmd_yt(update, context): await cmd_tool(update, context, "yt")
async def cmd_text(update, context): await cmd_tool(update, context, "text")
async def cmd_emi(update, context): await cmd_tool(update, context, "emi")
async def cmd_age(update, context): await cmd_tool(update, context, "age")
async def cmd_upi(update, context): await cmd_tool(update, context, "upi")
async def cmd_wa(update, context): await cmd_tool(update, context, "wa")


async def cmd_password(update, context):
    if not await ensure_joined(update, context):
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("8", callback_data="p8"), InlineKeyboardButton("12", callback_data="p12"),
         InlineKeyboardButton("16", callback_data="p16"), InlineKeyboardButton("20", callback_data="p20")],
        [InlineKeyboardButton("⬅️ Menu", callback_data="menu")],
    ])
    await update.message.reply_text("🔐 Kitne character ka password chahiye?", reply_markup=kb)


async def _post_init(app: Application):
    try:
        await app.bot.set_my_commands([])  # hamburger menu hatao - sirf grid keyboard
        log.info("Commands cleared - sirf grid keyboard rahega")
    except Exception as e:
        log.warning("clear commands fail: %s", e)

# ---------------- ADMIN ----------------
def is_admin(uid: int) -> bool:
    return bool(ADMIN_ID) and uid == ADMIN_ID


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
            await q.message.reply_text(WELCOME, reply_markup=main_keyboard())
        return

    if data == "menu":
        context.user_data.pop("mode", None)
        await q.message.reply_text("⌨️ Neeche grid me saare tools hain — koi dabao 👇", reply_markup=main_keyboard())
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
        upi_link = f"upi://pay?pa={UPI_ID}&pn={quote(UPI_NAME)}&am={amt}&cu=INR&tn=UtilityDuniyaPremium"
        context.user_data["mode"] = "pay"
        context.user_data["plan_days"] = int(days)
        await q.message.reply_photo(
            photo=make_qr_bytes(upi_link),
            caption=(f"💎 {days} din Premium = ₹{amt}\n\n1️⃣ UPI app se is QR par ₹{amt} pay karo\n"
                     f"2️⃣ Payment ka SCREENSHOT yahin bhejo (photo)\n3️⃣ Admin verify karke kuch min me active karega! ⚡\n\nUPI ID: {UPI_ID}"),
            reply_markup=BACK)
        return

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
        await q.message.reply_text(f"🔐 Tumhara {n}-digit password:\n\n{rech(pw)}\n\n(Dabakar copy karo. Kisi se share mat karo!)",
                                   reply_markup=BACK)
        return

    # QR smart choice: payment QR ya normal
    if data == "upi_yes":
        pending = context.user_data.get("qr_pending")
        if not pending:
            return
        context.user_data["upi_id"] = pending
        context.user_data["mode"] = "upi_name"
        context.user_data.pop("qr_pending", None)
        await q.message.reply_text(f"💰 Payment QR banate hain!\n✅ UPI ID: {pending}\n\nAb apna NAAM bhejo (QR par dikhega):\n(jaise: Ramesh Kumar)", reply_markup=BACK)
        return
    if data == "upi_no":
        pending = context.user_data.get("qr_pending")
        if not pending:
            return
        if not await use_or_block(uid, update):
            return
        context.user_data.pop("qr_pending", None)
        context.user_data.pop("mode", None)
        await q.message.reply_text("📝 Normal text QR bana diya (isme payment NAHI hoga):")
        await q.message.reply_photo(photo=make_qr_bytes(pending), caption="📷 Tumhara QR ready! ✅", reply_markup=BACK)
        return

    if data == "acc":
        await cmd_account(update, context)
        return
    if data in PROMPTS:
        context.user_data["mode"] = data
        await q.message.reply_text(PROMPTS[data] + "\n\n/cancel kabhi bhi dabao.", reply_markup=BACK)
        return


def rech(s: str) -> str:
    return f"`{s}`"

# ---------------- MESSAGE ROUTERS ----------------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = (update.message.text or "").strip()

    # --- bottom keyboard buttons ---
    if text in BTN_MODE:
        if not await ensure_joined(update, context):
            return
        mode = BTN_MODE[text]
        context.user_data["mode"] = mode
        await update.message.reply_text(PROMPTS[mode] + "\n\n/cancel kabhi bhi dabao.", reply_markup=BACK)
        return
    if text == "🔐 Password":
        if not await ensure_joined(update, context):
            return
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("8", callback_data="p8"), InlineKeyboardButton("12", callback_data="p12"),
             InlineKeyboardButton("16", callback_data="p16"), InlineKeyboardButton("20", callback_data="p20")],
            [InlineKeyboardButton("⬅️ Menu", callback_data="menu")],
        ])
        await update.message.reply_text("🔐 Kitne character ka password chahiye?", reply_markup=kb)
        return
    if text == "💎 Premium":
        await cmd_premium(update, context)
        return
    if text == "🎁 Refer & Earn":
        await cmd_refer(update, context)
        return
    if text == "👤 My Account":
        await cmd_account(update, context)
        return

    mode = context.user_data.get("mode")
    if not mode:
        await update.message.reply_text("👇 Neeche grid icon (▦) dabao — saare tools khulenge!", reply_markup=main_keyboard())
        return
    if not await ensure_joined(update, context):
        return

    if mode == "pay":
        await update.message.reply_text("📸 Payment ka SCREENSHOT photo ke roop me bhejo (text nahi).")
        return

    if mode == "qr":
        nospace = text.replace(" ", "")
        # UPI ID detect hui? to sahi payment QR ka option do
        if UPI_RE.match(nospace):
            context.user_data["qr_pending"] = nospace
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Payment QR (sahi wala ✅)", callback_data="upi_yes")],
                [InlineKeyboardButton("📝 Normal text QR", callback_data="upi_no")],
            ])
            await update.message.reply_text(
                "Ye to UPI ID lag rahi hai! 👇\n\n"
                "💰 Payment QR = GPay/PhonePe se scan karke PAISA aayega ✅\n"
                "📝 Normal QR = sirf text dikhega (payment NAHI hoga)\n\nKya banana hai?", reply_markup=kb)
            return
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
        bio = fetch_yt_thumb(vid)
        if not bio:
            await update.message.reply_text("⚠️ Is video ka thumbnail nahi mila. Dusra link try karo:")
            return
        await update.message.reply_photo(
            photo=bio, caption=f"🎬 HD Thumbnail mil gaya!\n🔗 https://youtu.be/{vid}", reply_markup=BACK)
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

    # ---- UPI payment QR flow ----
    if mode == "upi":
        upi = text.replace(" ", "")
        if not UPI_RE.match(upi):
            await update.message.reply_text("⚠️ Sahi UPI ID bhejo (jaise name@okhdfc ya number@ybl):")
            return
        context.user_data["upi_id"] = upi
        context.user_data["mode"] = "upi_name"
        await update.message.reply_text(f"✅ UPI ID: {upi}\n\nAb apna NAAM bhejo (payment par dikhega):\n(jaise: Ramesh Kumar)")
        return

    if mode == "upi_name":
        context.user_data["upi_name"] = text[:40]
        context.user_data["mode"] = "upi_amt"
        await update.message.reply_text("💰 Fixed AMOUNT lagana hai? (dukandaaron ke liye best)\n\nAmount bhejo (jaise 100) ya skip likho:")
        return

    if mode == "upi_amt":
        amt = None
        if text.lower() not in ("skip", "0", "no", "n"):
            try:
                amt = round(float(text.replace("₹", "").replace(",", "").strip()), 2)
            except Exception:
                await update.message.reply_text("⚠️ Sahi amount bhejo (jaise 100) ya skip likho:")
                return
            if amt < 1 or amt > 1000000:
                await update.message.reply_text("⚠️ Amount 1 se 1000000 tak rakho, ya skip likho:")
                return
        if not await trial_or_block(uid, update, "UPI QR"):
            context.user_data.pop("mode", None)
            return
        link = build_upi_link(context.user_data.get("upi_id", ""), context.user_data.get("upi_name", "User"), amt)
        cap = (f"💰 UPI Payment QR ready!\n\n🆔 {context.user_data.get('upi_id')}\n👤 {context.user_data.get('upi_name')}\n"
               + (f"💵 Fixed amount: ₹{amt:,.0f}\n" if amt else "💵 Amount: customer khud bharega\n")
               + "\n📲 GPay / PhonePe / Paytm se scan karo — payment seedha tumhe aayega! ✅")
        await update.message.reply_photo(photo=make_qr_bytes(link), caption=cap, reply_markup=BACK)
        for k in ("mode", "upi_id", "upi_name"):
            context.user_data.pop(k, None)
        return

    # ---- WhatsApp link flow ----
    if mode == "wa":
        num = normalize_phone(text)
        if not num:
            await update.message.reply_text("⚠️ Sahi 10-digit mobile number bhejo (jaise 9876543210):")
            return
        context.user_data["wa_num"] = num
        context.user_data["mode"] = "wa_msg"
        await update.message.reply_text(f"✅ Number: +91 {num}\n\nAb default MESSAGE bhejo (jo chat khulne par likha aayega) ya skip likho:")
        return

    if mode == "wa_msg":
        msg = "" if text.lower() == "skip" else text[:500]
        if not await trial_or_block(uid, update, "WA Link"):
            context.user_data.pop("mode", None)
            return
        link = build_wa_link(context.user_data.get("wa_num", ""), msg)
        cap = (f"📱 WhatsApp Link ready!\n\n🔗 {link}\n\nIs link par click karte hi WhatsApp chat khulegi ✅\n"
               "Bio / status / dukaan ke board par lagao! 🚀")
        await update.message.reply_photo(photo=make_qr_bytes(link), caption=cap, reply_markup=BACK)
        for k in ("mode", "wa_num"):
            context.user_data.pop(k, None)
        return

    if mode in ("pdf", "comp"):
        await update.message.reply_text("📸 Photo bhejo (text nahi). /cancel se wapas jao.")
        return


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = context.user_data.get("mode")
    if not mode:
        await update.message.reply_text("👇 Neeche keyboard se tool dabao ⌨️", reply_markup=main_keyboard())
        return
    if not await ensure_joined(update, context):
        return

    # payment screenshot -> DIRECT admin ko (tumhari personal ID par)
    if mode == "pay":
        if not ADMIN_ID:
            await update.message.reply_text("⚠️ Admin set nahi hai. /cancel dabao.")
            return
        days = context.user_data.get("plan_days", 30)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"✅ Approve {days}din", callback_data=f"ap:{uid}:{days}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"dc:{uid}"),
        ]])
        uname = f"@{update.effective_user.username}" if update.effective_user.username else "(username nahi hai)"
        try:
            await update.message.forward(ADMIN_ID)
            await context.bot.send_message(
                ADMIN_ID,
                f"💰 Naya Premium Payment!\n\n👤 Naam: {update.effective_user.first_name}\n🔗 {uname}\n🆔 ID: {uid}\n📦 Plan: {days} din\n\nUpar screenshot dekho, verify karke Approve/Reject dabao 👇",
                reply_markup=kb)
            await update.message.reply_text("✅ Screenshot admin ko bhej diya! Verify hote hi Premium active ho jayega (kuch min). 🙏", reply_markup=BACK)
        except Exception as e:
            log.warning("admin forward fail: %s", e)
            await update.message.reply_text("⚠️ Kuch gadbad hui, screenshot dobara bhejo.")
        context.user_data.pop("mode", None)
        return

    if mode not in ("pdf", "comp"):
        await update.message.reply_text("👇 Neeche keyboard se tool dabao ⌨️", reply_markup=main_keyboard())
        return
    if not await use_or_block(uid, update):
        return

    try:
        f = None
        if update.message.photo:
            f = await context.bot.get_file(update.message.photo[-1].file_id)
        elif update.message.document and (update.message.document.mime_type or "").startswith("image/"):
            f = await context.bot.get_file(update.message.document.file_id)
        if not f:
            await update.message.reply_text("⚠️ Photo bhejo (PDF/file nahi).")
            return
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
        raise SystemExit("❌ BOT_TOKEN nahi mila! Render Environment me BOT_TOKEN=... dalo.")
    db().close()
    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("qr", cmd_qr))
    app.add_handler(CommandHandler("font", cmd_font))
    app.add_handler(CommandHandler("password", cmd_password))
    app.add_handler(CommandHandler("pdf", cmd_pdf))
    app.add_handler(CommandHandler("compress", cmd_comp))
    app.add_handler(CommandHandler("short", cmd_short))
    app.add_handler(CommandHandler("yt", cmd_yt))
    app.add_handler(CommandHandler("text", cmd_text))
    app.add_handler(CommandHandler("emi", cmd_emi))
    app.add_handler(CommandHandler("age", cmd_age))
    app.add_handler(CommandHandler("upi", cmd_upi))
    app.add_handler(CommandHandler("wa", cmd_wa))
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
    app.add_handler(MessageHandler(filters.ATTACHMENT, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)

    if WEBHOOK_URL:
        port = int(os.getenv("PORT", "10000"))
        log.info("Webhook mode on port %s", port)
        app.run_webhook(listen="0.0.0.0", port=port, url_path=BOT_TOKEN,
                        webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}")
    else:
        log.info("Polling mode (WEBHOOK_URL khali hai - Render par WEBHOOK_URL dalo!)")
        app.run_polling()


if __name__ == "__main__":
    main()
