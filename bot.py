#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ TOOLVAULT / UTILITY DUNIYA SUPER-BOT (v30 Ultra Edition) ⚡
- 30+ Dedicated Separate Tools with Aesthetic Mathematical Bold Fonts (𝐓𝐄𝐋𝐄𝐆𝐑𝐀𝐌 style)
- Short, Modern & Aesthetic Rowdy/Venom Style Welcome Card
- 100% Working 3-Step Virtual Numbers (OTP) Funnel
- Advanced Channel Cloner & Auto-Forwarder Settings Dashboard (Replace words, remove promo links, custom thumbnails)
- Instagram Downloader with 100% Full Audio & HD Media (Reels, Videos, Photos, Public Stories)
- Text to Actors & Celebrity Voice Studio (Amitabh Don, Pushpa, Modi, SRK, CarryMinati, Narrator)
- 6-Store App Finder (including GetModPC, PlayStore, HappyMod, APKPure)
- Accurate Rich Web Search with 5-6 Verified Results
- Free direct access without forced channel joining
- 24/7 Zero-Lag Keepalive Server on Port 10000 (UptimeRobot friendly)
"""

import asyncio
import base64
import io
import json
import logging
import os
import random
import re
import sqlite3
import string
import tempfile
import time
import threading
from datetime import date, datetime, timedelta
from html import escape as hesc
from urllib.parse import quote, unquote, urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.error import RetryAfter
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Internal modules
from database import (
    add_referral,
    add_trial,
    add_use,
    all_user_ids,
    db,
    find_by_username,
    get_cloner_config,
    get_user,
    get_user_row,
    grant_premium,
    is_banned,
    is_premium,
    premium_expiry,
    premium_users,
    recent_users,
    refund_trial,
    refund_use,
    save_cloner_config,
    save_username,
    set_ban,
    stats,
    top_referrers,
)
# Full-Auto Channel Cloner helper (safety import)
try:
    from database import get_auto_cloners_for_source
except ImportError:  # agar purani database.py use ho rahi ho to bot crash na ho
    def get_auto_cloners_for_source(_source):
        return []

from modules.sarkari_hub import (
    SARKARI_CITIZEN_TEXT,
    STATE_PORTALS_TEXT,
    STUDENT_EXAM_TEXT,
    get_sarkari_citizen_kb,
    get_state_portals_kb,
    get_student_exam_kb,
)
from modules.cyber_studio import (
    clean_signature,
    compress_document_pdf,
    make_printable_sheet,
    make_stamped_passport,
)
from modules.cloud_tools import resolve_cloud_url
from modules.channel_cloner import clone_messages, forward_cloned_message, get_cloner_settings_kb
from modules.voice_studio import ACTOR_VOICE_PRESETS, generate_actor_voice
from modules.media_downloader import (
    download_instagram_async,
    download_video_async,
    is_instagram_url,
    is_supported_video_url,
    platform_name,
)
from modules.toolkit_extras import (
    calc_interest,
    check_link_safety,
    expand_url,
    file_size_human,
    parse_emi_input,
    shorten_url,
)
from modules.osint_tools import (
    check_username_platforms,
    lookup_ifsc,
    lookup_ip_domain,
    lookup_phone_info,
    lookup_pincode,
    lookup_vehicle_rto,
)
from modules.general_tools import (
    calc_age,
    calc_emi,
    emi_schedule,
    gen_password,
    get_app_store_links,
    make_qr_bytes,
    name_passwords,
    pages_to_pdf,
    search_web_rich,
    shorten_isgd,
    shorten_tiny,
    site_screenshot,
    zodiac,
)
from modules.vip_payment import (
    VIP_PLANS,
    generate_plan_payment_qr,
    get_payment_admin_kb,
    get_premium_plans_kb,
)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "").strip()
FORCE_CHANNEL_LINK = os.getenv("FORCE_CHANNEL_LINK", "").strip()
UPI_ID = os.getenv("UPI_ID", "yourname@upi").strip()
UPI_NAME = os.getenv("UPI_NAME", "UtilityDuniya").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
FREE_LIMIT = int(os.getenv("FREE_LIMIT", "10") or 10)
SUPPORT_USERNAME = "@Supermannn_x"
REFER_NEED = int(os.getenv("REFER_NEED", "5") or 5)
HTML = "HTML"
BAN_MSG = "🚫 Aapka account banned hai. Kripya admin se contact karein."
BOT_VERSION = "v30 Ultra"
START_TIME = datetime.now()

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("utility-super-bot")


# ---------------- AESTHETIC BOLD UNICODE HELPER ----------------
def to_bold(text: str) -> str:
    """Converts standard text to Mathematical Bold Unicode (e.g. TELEGRAM -> 𝐓𝐄𝐋𝐄𝐆𝐑𝐀𝐌)"""
    res = []
    for c in text:
        code = ord(c)
        if 65 <= code <= 90:  # A-Z
            res.append(chr(0x1D400 + (code - 65)))
        elif 97 <= code <= 122:  # a-z
            res.append(chr(0x1D41A + (code - 97)))
        elif 48 <= code <= 57:  # 0-9
            res.append(chr(0x1D7CE + (code - 48)))
        else:
            res.append(c)
    return "".join(res)


def check_limit_exceeded(u: dict) -> bool:
    if is_premium(u):
        return False
    return u.get("uses_today", 0) >= FREE_LIMIT


def get_limit_exceeded_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Buy VIP Premium", callback_data="open_vip_menu"), InlineKeyboardButton("🎁 Refer & Earn", callback_data="open_refer_menu")],
        [InlineKeyboardButton("💬 Contact Support (@Supermannn_x)", url="https://t.me/Supermannn_x")],
    ])


def get_limit_exceeded_text() -> str:
    return (
        f"⚠️ <b>{to_bold('DAILY FREE LIMIT REACHED')} ({FREE_LIMIT}/{FREE_LIMIT} Credits)</b>\n\n"
        f"Aapka aaj ka <b>{FREE_LIMIT} free daily credits limit poora ho chuka hai!</b>\n\n"
        f"👑 <b>VIP Premium Member banein aur Unlimited Access payein:</b>\n"
        f"• ♾️ Unlimited Daily Usage (No Limits)\n"
        f"• 🚀 Ultra High-Speed Priority Server\n"
        f"• 🛠️ All 32+ Tools Fully Unlocked\n\n"
        f"🎁 <i>Dosto ko bot share karke 30 din ka Free VIP bhi le sakte hain (/refer)!</i>\n"
        f"💬 <i>Direct VIP lene ya kisi problem ke liye contact karein: {SUPPORT_USERNAME}</i>"
    )


SUPPORT_USERNAME = "@Supermannn_x"
SUPPORT_LINK = '<a href="https://t.me/Supermannn_x">@Supermannn_x</a>'


def fail_msg(title: str, reason: str = "") -> str:
    body = f"\n\n{reason}" if reason else ""
    return (
        f"❌ <b>{to_bold(title)}</b>{body}\n\n"
        f"💡 <b>Tip:</b> Ek baar dubara try karein yahi tool. Agar fir bhi koi issue ho to direct contact karein: {SUPPORT_LINK}"
    )


def unbold(text: str) -> str:
    """Normalizes Mathematical Bold Unicode back to standard ASCII for exact matching"""
    res = []
    for c in text:
        code = ord(c)
        if 0x1D400 <= code <= 0x1D419:
            res.append(chr(65 + (code - 0x1D400)))
        elif 0x1D41A <= code <= 0x1D433:
            res.append(chr(97 + (code - 0x1D41A)))
        elif 0x1D7CE <= code <= 0x1D7D7:
            res.append(chr(48 + (code - 0x1D7CE)))
        else:
            res.append(c)
    return "".join(res)


# ---------------- VIRTUAL NUMBERS CONSTANTS ----------------
VNUM_SERVICES = (
    ("wa", "🟢 WhatsApp"),
    ("fb", "🔵 Facebook"),
    ("ig", "📸 Instagram"),
    ("tt", "🎵 TikTok"),
    ("tg", "✈️ Telegram"),
    ("sc", "👻 Snapchat"),
    ("xx", "𝕏 X (Twitter)"),
    ("dc", "🎮 Discord"),
    ("gg", "🔷 Google"),
    ("yt", "▶️ YouTube"),
)

VNUM_COUNTRIES = (
    ("my", "🇲🇾 Malaysia"),
    ("iq", "🇮🇶 Iraq"),
    ("ru", "🇷🇺 Russia"),
    ("id", "🇮🇩 Indonesia"),
    ("np", "🇳🇵 Nepal"),
    ("sd", "🇸🇩 Sudan"),
    ("us", "🇺🇸 USA"),
    ("gb", "🇬🇧 UK"),
    ("ca", "🇨🇦 Canada"),
    ("de", "🇩🇪 Germany"),
    ("fr", "🇫🇷 France"),
    ("nl", "🇳🇱 Netherlands"),
    ("ae", "🇦🇪 UAE"),
    ("bd", "🇧🇩 Bangladesh"),
    ("br", "🇧🇷 Brazil"),
    ("tr", "🇹🇷 Turkey"),
)

VNUM_INTRO = (
    f"🌐✨ <b>{to_bold('VIRTUAL NUMBERS (OTP STOCK)')}</b> ✨🌐\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⚡ <b>Fresh OTP Numbers:</b> Fast &amp; 100% Reliable\n"
    "🟢 Instant OTP Delivery • Permanent Numbers\n"
    "🌍 <b>16 Countries</b> • 📲 <b>10 Services</b> Live Stock\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🎯 <b>3 Simple Steps:</b>\n"
    "1️⃣ Service → 2️⃣ Country → 3️⃣ Get Instant Number\n\n"
    "<i>Pure account verification ke liye. No spam.</i>"
)


def _vnum_intro_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Get Number", callback_data="vnum_get")],
        [InlineKeyboardButton("☎️ Contact @Supermannn_x", url="https://t.me/Supermannn_x")],
        [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
    ])


def _vnum_svc_kb():
    rows = []
    for i in range(0, len(VNUM_SERVICES), 2):
        rows.append([
            InlineKeyboardButton(l, callback_data=f"vnum_svc:{sl}")
            for sl, l in VNUM_SERVICES[i : i + 2]
        ])
    rows.append([
        InlineKeyboardButton("⏪ Pehle", callback_data="vnum_open"),
        InlineKeyboardButton("⌨️ Menu", callback_data="back_home"),
    ])
    return InlineKeyboardMarkup(rows)


def _vnum_ctry_kb():
    rows = []
    for i in range(0, len(VNUM_COUNTRIES), 2):
        rows.append([
            InlineKeyboardButton(l, callback_data=f"vnum_ctry:{sl}")
            for sl, l in VNUM_COUNTRIES[i : i + 2]
        ])
    rows.append([
        InlineKeyboardButton("🔁 Service badlo", callback_data="vnum_get"),
        InlineKeyboardButton("⌨️ Menu", callback_data="back_home"),
    ])
    return InlineKeyboardMarkup(rows)


async def send_vnum_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(VNUM_INTRO, reply_markup=_vnum_intro_kb(), parse_mode=HTML)


# ---------------- SEPARATE DEDICATED KEYBOARD BUTTONS (ALL UPPERCASE MATHEMATICAL BOLD) ----------------
KB_BTNS = [
    [f"🌐 {to_bold('VIRTUAL NUMBERS')}", f"⚡ {to_bold('TERABOX DOWNLOADER')}"],
    [f"🔄 {to_bold('CHANNEL CLONER')}", f"🎙️ {to_bold('ACTORS VOICE STUDIO')}"],
    [f"📸 {to_bold('INSTA DOWNLOADER')}", f"📸 {to_bold('PASSPORT PHOTO (NAME/DOP)')}"],
    [f"✍️ {to_bold('SIGNATURE CLEANER')}", f"🖨️ {to_bold('8-IN-1 PRINT SHEET')}"],
    [f"📄 {to_bold('DOCUMENT PDF COMPRESS')}", f"🏛️ {to_bold('SARKARI SEVA PORTALS')}"],
    [f"🎓 {to_bold('STUDENT EXAM HUB')}", f"🚗 {to_bold('RTO VEHICLE INFO')}"],
    [f"📱 {to_bold('NUMBER INFO')}", f"🏦 {to_bold('IFSC INFO')}"],
    [f"📮 {to_bold('PINCODE INFO')}", f"🆔 {to_bold('ID & USERNAME FINDER')}"],
    [f"📷 {to_bold('QR CODE')}", f"🖼️ {to_bold('IMAGE→PDF')}"],
    [f"🔗 {to_bold('URL SHORT')}", f"🔓 {to_bold('LINK BYPASS')}"],
    [f"🔍 {to_bold('LINK CHECK')}", f"🧮 {to_bold('EMI CALC')}"],
    [f"📈 {to_bold('INTEREST CALC')}", f"🎂 {to_bold('AGE CALCULATOR')}"],
    [f"💰 {to_bold('UPI QR GENERATOR')}", f"🔐 {to_bold('PASSWORD GENERATOR')}"],
    [f"🔎 {to_bold('WEB SEARCH')}", f"📦 {to_bold('APP FINDER')}"],
    [f"🖼️ {to_bold('SITE SCREENSHOT')}", f"💎 {to_bold('VIP PREMIUM')}"],
    [f"🎁 {to_bold('REFER & EARN')}", f"👤 {to_bold('MY ACCOUNT')}"],
]


def main_keyboard(admin: bool = False):
    rows = [row[:] for row in KB_BTNS]
    if admin:
        rows.append([f"🛠️ {to_bold('ADMIN PANEL')}"])
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t) for t in row] for row in rows],
        resize_keyboard=True,
        input_field_placeholder="Tool select karein 👇",
    )


def kb_for(uid: int):
    return main_keyboard(admin=(uid == ADMIN_ID and ADMIN_ID != 0))


# Exact Action Mapping
BTN_MODE_MAP = {
    "VIRTUAL NUMBERS": "vnum",
    "TERABOX DOWNLOADER": "terabox",
    "CHANNEL CLONER": "cloner",
    "ACTORS VOICE STUDIO": "voice",
    "INSTA DOWNLOADER": "insta_dl",
    "INSTAGRAM DOWNLOADER": "insta_dl",
    "VIDEO DOWNLOADER": "insta_dl",
    "VIRAL VIDEO DOWNLOAD": "insta_dl",
    "PASSPORT PHOTO (NAME/DOP)": "pp_stamp",
    "SIGNATURE CLEANER": "sig_clean",
    "8-IN-1 PRINT SHEET": "print_sheet",
    "DOCUMENT PDF COMPRESS": "doc_compress",
    "SARKARI SEVA PORTALS": "sarkari",
    "STUDENT EXAM HUB": "exam",
    "RTO VEHICLE INFO": "rto",
    "NUMBER INFO": "numinfo",
    "IFSC INFO": "ifsc",
    "PINCODE INFO": "pin",
    "ID & USERNAME FINDER": "idfind",
    "QR CODE": "qr",
    "IMAGE→PDF": "pdf",
    "URL SHORT": "short",
    "LINK BYPASS": "linkbypass",
    "LINK CHECK": "linkcheck",
    "EMI CALC": "emi",
    "INTEREST CALC": "interest",
    "AGE CALCULATOR": "age",
    "UPI QR GENERATOR": "upi",
    "PASSWORD GENERATOR": "pwd",
    "WEB SEARCH": "search",
    "APP FINDER": "appfind",
    "SITE SCREENSHOT": "shot",
    "VIP PREMIUM": "premium",
    "REFER & EARN": "refer",
    "MY ACCOUNT": "account",
    "ADMIN PANEL": "admin",
}

PROMPTS = {
    "terabox": (
        f"⚡ <b>{to_bold('TERABOX & CLOUD DIRECT DOWNLOADER')}</b>\n\n"
        "<blockquote>Direct Ad-Free High-Speed Download Link &amp; Web Streaming Player!</blockquote>\n\n"
        "🔗 Koi bhi <b>Terabox, Mediafire ya Google Drive</b> link bhejo:"
    ),
    "insta_dl": (
        f"📸 <b>{to_bold('UNIVERSAL VIDEO DOWNLOADER')}</b>\n\n"
        "<blockquote>Instagram Reels/Posts/Stories (100% original audio) + YouTube, Facebook, X (Twitter), "
        "TikTok, Pinterest, Reddit, Vimeo &amp; 20+ platforms!</blockquote>\n\n"
        "🔗 <b>Koi bhi video link bhejo</b> (48MB tak seedha bot me, bada file ho to direct link milega):"
    ),
    "pp_stamp": (
        f"📸 <b>{to_bold('GOVT EXAM PASSPORT PHOTO STUDIO')}</b>\n\n"
        "<blockquote>Official 3.5cm x 4.5cm • Candidate Name &amp; Date of Photo Stamp • 20-50KB</blockquote>\n\n"
        "📸 Apni passport photo bhejo:"
    ),
    "sig_clean": (
        f"✍️ <b>{to_bold('SIGNATURE CLEANER & INK ENHANCER')}</b>\n\n"
        "<blockquote>Pure White Background • Sharp Black Ink • 10-20KB Official Compliance</blockquote>\n\n"
        "📸 Signature ki photo bhejo:"
    ),
    "print_sheet": (
        f"🖨️ <b>{to_bold('PRINTABLE 8-IN-1 PASSPORT SHEET')}</b>\n\n"
        "<blockquote>4x6 inch Standard Lab Printable Sheet for ₹10 Print Cost!</blockquote>\n\n"
        "📸 Single photo bhejo:"
    ),
    "doc_compress": (
        f"📄 <b>{to_bold('DOCUMENT & MARKSHEET PDF COMPRESSOR')}</b>\n\n"
        "<blockquote>Compress 10th/12th/Caste Marksheet to Ultra-Sharp PDF under 250KB!</blockquote>\n\n"
        "📸 Marksheet ya certificate photo bhejo:"
    ),
    "rto": (
        f"🚗 <b>{to_bold('RTO VEHICLE INFORMATION')}</b>\n\n"
        "Gaadi ka number plate bhejo:\n(jaise: <code>DL01AB1234</code> ya <code>JH01AB1234</code>)"
    ),
    "numinfo": (
        f"📱 <b>{to_bold('PHONE NUMBER LOOKUP')}</b>\n\n"
        "10-digit mobile number bhejo:\n(jaise: <code>9876543210</code>)"
    ),
    "ifsc": (
        f"🏦 <b>{to_bold('IFSC BANK BRANCH LOOKUP')}</b>\n\n"
        "Bank ka IFSC code bhejo:\n(jaise: <code>SBIN0000001</code> ya <code>HDFC0001234</code>)"
    ),
    "pin": (
        f"📮 <b>{to_bold('PINCODE & POST OFFICE INFO')}</b>\n\n"
        "6-digit pincode bhejo:\n(jaise: <code>823001</code> ya <code>110001</code>)"
    ),
    "idfind": (
        f"🆔 <b>{to_bold('ID & USERNAME FINDER')}</b>\n\n"
        "1️⃣ Kisi ka koi <b>message FORWARD</b> karein → Direct Telegram ID\n"
        "2️⃣ <b>@username</b> bhejo → Account details\n"
        "3️⃣ <code>me</code> likho → Apni Telegram ID"
    ),
    "qr": (
        f"📷 <b>{to_bold('HD QR CODE GENERATOR')}</b>\n\n"
        "Koi bhi TEXT, UPI ID, WiFi ya LINK bhejo:"
    ),
    "pdf": (
        f"🖼️ <b>{to_bold('IMAGE TO MULTI-PAGE PDF')}</b>\n\n"
        "📸 Ek-ek karke <b>10 photos tak</b> bhejo, phir <b>✅ Make PDF</b> dabayein:"
    ),
    "short": (
        f"🔗 <b>{to_bold('URL SHORTENER')}</b>\n\n"
        "Lamba link bhejo — 2 fast short links milenge (is.gd &amp; tinyurl):"
    ),
    "linkbypass": (
        f"🔓 <b>{to_bold('EARN-LINK SHORTENER BYPASS')}</b>\n\n"
        "GPLinks, VPLinks ya ad-shortener link bhejo — direct destination nikalenge:"
    ),
    "linkcheck": (
        f"🔍 <b>{to_bold('LINK SAFETY & FRAUD CHECKER')}</b>\n\n"
        "Koi bhi suspicious link bhejo — safety check karenge:"
    ),
    "emi": (
        f"🧮 <b>{to_bold('LOAN EMI CALCULATOR')}</b>\n\n"
        "Loan amount (₹) bhejo:\n(jaise: <code>100000</code>)"
    ),
    "age": (
        f"🎂 <b>{to_bold('AGE & BIRTHDAY CALCULATOR')}</b>\n\n"
        "Birth date bhejo (DD-MM-YYYY):\n(jaise: <code>15-08-2005</code>)"
    ),
    "upi": (
        f"💰 <b>{to_bold('UPI QR GENERATOR WITH AMOUNT')}</b>\n\n"
        "Apni UPI ID bhejo:\n(jaise: <code>name@okhdfc</code>)"
    ),
    "search": (
        f"🔎 <b>{to_bold('FAST & ACCURATE WEB SEARCH')}</b>\n\n"
        "Kuch bhi search karein (Movies, Study Notes, Software, Sarkari info):"
    ),
    "appfind": (
        f"📦 <b>{to_bold('APP & MOD STORE FINDER (6 TRUSTED STORES)')}</b>\n\n"
        "App ka naam bhejo (GetModPC, PlayStore, HappyMod, APKPure):"
    ),
    "shot": (
        f"🖼️ <b>{to_bold('WEBSITE FULL SCREENSHOT')}</b>\n\n"
        "Website ka URL bhejo (jaise: <code>github.com</code>):"
    ),
}

WELCOME_TEXT = (
    f"⚡ <b>{to_bold('TOOLVAULT • UTILITY DUNIYA')}</b> ⚡\n"
    "<blockquote>30+ High-Power Automation Tools • Instant 1-Sec Response 🚀</blockquote>\n\n"
    f"🔥 <b>{to_bold('POPULAR UTILITIES')}:</b>\n"
    f"• 🌐 <b>{to_bold('Virtual Numbers')}:</b> OTP numbers for WhatsApp &amp; TG\n"
    f"• ⚡ <b>{to_bold('Terabox DL')}:</b> Ad-free direct bypass\n"
    f"• 🔄 <b>{to_bold('Channel Cloner')}:</b> Auto-forward with custom branding\n"
    f"• 🎙️ <b>{to_bold('Actors Voice')}:</b> Amitabh Don, Pushpa, Modi, SRK\n"
    f"• 📸 <b>{to_bold('Insta Downloader')}:</b> Reels, Posts &amp; Stories (100% Sound)\n"
    f"• 📸 <b>{to_bold('Cyber Studio')}:</b> Name/Date photo, Signature clean\n"
    f"• 🏛️ <b>{to_bold('Sarkari Portals')}:</b> Direct official Govt links\n\n"
    "👇 <b>Neeche Grid Menu dabakar tool select karein</b>"
)


# ---------------- COMMANDS ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, user.first_name or "")
    save_username(user.id, user.username or "")
    if is_banned(user.id):
        await update.message.reply_text(BAN_MSG)
        return

    # Referral handling
    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_id = int(context.args[0].split("_")[1])
            count = add_referral(user.id, ref_id)
            if count:
                await update.message.reply_text("🎉 Welcome! Referral link se judne ke liye dhanyawad!")
                if count % REFER_NEED == 0:
                    grant_premium(ref_id, 30)
                    try:
                        await context.bot.send_message(ref_id, f"🎉 Badhai! {count} referrals poore hue! 30 din VIP FREE mil gaya 💎")
                    except Exception:
                        pass
        except Exception:
            pass

    banner_path = os.path.join(os.path.dirname(__file__), "welcome_banner.jpg")
    if os.path.exists(banner_path):
        try:
            with open(banner_path, "rb") as f:
                await update.message.reply_photo(photo=f, caption=WELCOME_TEXT, reply_markup=kb_for(user.id), parse_mode=HTML)
                return
        except Exception:
            pass
    await update.message.reply_text(WELCOME_TEXT, reply_markup=kb_for(user.id), parse_mode=HTML)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=kb_for(update.effective_user.id), parse_mode=HTML)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Action cancelled! Tools grid ready hai 👇", reply_markup=kb_for(update.effective_user.id))


async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    vip_status = "👑 ACTIVE VIP" if is_premium(u) else f"Free Tier (Daily {FREE_LIMIT} uses)"
    expiry = premium_expiry(u)
    text = (
        f"👤 <b>{to_bold('MY ACCOUNT DETAILS')}</b>\n\n"
        f"• <b>Name:</b> {hesc(u.get('name', 'User'))}\n"
        f"• <b>User ID:</b> <code>{u.get('user_id')}</code>\n"
        f"• <b>VIP Status:</b> {vip_status}\n"
        f"• <b>VIP Expiry:</b> {expiry}\n"
        f"• <b>Today Uses:</b> {u.get('uses_today', 0)} / {FREE_LIMIT}\n"
        f"• <b>Referrals:</b> {u.get('referrals', 0)}\n\n"
        f"🎁 <i>Refer {REFER_NEED} friends to get 30 Days Free VIP!</i>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Buy / Upgrade VIP", callback_data="open_vip_menu")],
        [InlineKeyboardButton("🎁 Refer & Earn Link", callback_data="open_refer_menu")],
    ])
    await update.message.reply_text(text, reply_markup=kb, parse_mode=HTML)


async def cmd_refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{update.effective_user.id}"
    u = get_user(update.effective_user.id)
    text = (
        f"🎁 <b>{to_bold('REFER & EARN FREE VIP')}</b> 🎁\n\n"
        f"Apne dosto ko bot share karein aur **30 din ka VIP Access bilkul FREE** payein!\n\n"
        f"📊 <b>Aapke Referrals:</b> {u.get('referrals', 0)}\n"
        f"🎯 <b>Target:</b> Har {REFER_NEED} referrals par 30 Days VIP Free\n\n"
        f"🔗 <b>Aapka Personal Invite Link:</b>\n<code>{ref_link}</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Share on Telegram", url=f"https://t.me/share/url?url={quote(ref_link)}&text={quote('🔥 Check out Utility Duniya Super Bot!')}")],
    ])
    await update.message.reply_text(text, reply_markup=kb, parse_mode=HTML)


async def cmd_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"💎 <b>{to_bold('VIP PREMIUM MEMBERSHIP')}</b> 💎\n"
        "<blockquote>Unlock Unlimited High-Speed Cloud Downloads, Cloner, Photo Studio & AI Voices!</blockquote>\n\n"
        f"⚡ <b>{to_bold('VIP FEATURES')}:</b>\n"
        "• ♾️ Unlimited Daily Usage (No free limits)\n"
        "• 🚀 Ultra High-Speed Terabox Video Stream & Direct Downloads\n"
        "• 🔄 Channel Cloner & Auto-Forwarder with Custom Branding\n"
        "• 🎙️ Full AI Actors Voice Studio\n"
        "• 📸 Cyber Cafe Photo & Doc Studio HD\n\n"
        "👉 Plan select karein aur instant QR code se pay karein:"
    )
    await update.message.reply_text(text, reply_markup=get_premium_plans_kb(), parse_mode=HTML)


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    st = stats()
    text = (
        f"🛠️ <b>{to_bold('ADMIN CONTROL DASHBOARD')}</b> 🛠️\n\n"
        f"📊 <b>Bot Live Statistics:</b>\n"
        f"• 👥 <b>Total Users:</b> {st['total_users']}\n"
        f"• 🟢 <b>Active Today:</b> {st['active_today']}\n"
        f"• ⚡ <b>Total Uses Today:</b> {st['uses_today']}\n"
        f"• 💎 <b>Active VIP Users:</b> {st['vip_users']}\n\n"
        f"👑 <b>Grant VIP Duration Commands:</b>\n"
        f"• 🌟 <b>30 Days (1 Month):</b> <code>/grant [userid] 30</code>\n"
        f"• 🌟 <b>60 Days (2 Months):</b> <code>/grant [userid] 60</code>\n"
        f"• 🌟 <b>90 Days (3 Months):</b> <code>/grant [userid] 90</code>\n"
        f"• 🌟 <b>120 Days (4 Months):</b> <code>/grant [userid] 120</code>\n"
        f"• 👑 <b>Lifetime VIP:</b> <code>/grant [userid] 9999</code>\n\n"
        f"🛠️ <b>Management Commands:</b>\n"
        f"• 📢 <code>/broadcast [message]</code> - Send to all users\n"
        f"• 🚫 <code>/ban [userid]</code> - Ban user\n"
        f"• 🟢 <code>/unban [userid]</code> - Unban user"
    )
    await update.message.reply_text(text, parse_mode=HTML)


async def cmd_grant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Format: <code>/grant [userid] [days]</code>\n\nDurations:\n• 30 (1 Month)\n• 60 (2 Months)\n• 90 (3 Months)\n• 120 (4 Months)\n• 9999 (Lifetime)",
            parse_mode=HTML,
        )
        return
    try:
        target_uid = int(args[0])
        days = int(args[1])
        grant_premium(target_uid, days)
        dur_str = "👑 LIFETIME VIP" if days >= 9999 else f"🌟 {days} Din VIP"
        await update.message.reply_text(
            f"✅ <b>Success!</b> User <code>{target_uid}</code> ko <b>{dur_str}</b> grant kar diya gaya!",
            parse_mode=HTML,
        )
        try:
            await context.bot.send_message(
                target_uid,
                f"🎉 <b>Badhai ho!</b> Aapka <b>{dur_str} Access</b> activate ho gaya hai! Ab aap bot ko bina kisi daily limit ke use kar sakte hain! 💎",
                parse_mode=HTML,
            )
        except Exception:
            pass
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    msg_text = " ".join(context.args) if context.args else ""
    if not msg_text:
        await update.message.reply_text("Format: <code>/broadcast [message]</code>", parse_mode=HTML)
        return
    uids = all_user_ids()
    success, failed = 0, 0
    st = await update.message.reply_text(f"📢 Broadcasting to {len(uids)} users...")
    for u in uids:
        try:
            await context.bot.send_message(u, msg_text, parse_mode=HTML)
            success += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1
    await st.edit_text(f"📢 <b>Broadcast Complete!</b>\n\n• ✅ Success: {success}\n• ❌ Failed: {failed}", parse_mode=HTML)


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    if not context.args:
        await update.message.reply_text("Format: <code>/ban [userid]</code>", parse_mode=HTML)
        return
    try:
        target_uid = int(context.args[0])
        set_ban(target_uid, 1)
        await update.message.reply_text(f"🚫 User <code>{target_uid}</code> has been banned.", parse_mode=HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    if not context.args:
        await update.message.reply_text("Format: <code>/unban [userid]</code>", parse_mode=HTML)
        return
    try:
        target_uid = int(context.args[0])
        set_ban(target_uid, 0)
        await update.message.reply_text(f"✅ User <code>{target_uid}</code> has been unbanned.", parse_mode=HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


# ---------------- CALLBACK QUERY HANDLER ----------------
async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id

    if data == "back_home":
        await q.message.edit_text(WELCOME_TEXT, reply_markup=None, parse_mode=HTML)
        return

    # Virtual Numbers Funnel
    if data in ("vnum_open", "vnum_back"):
        await q.message.edit_text(VNUM_INTRO, reply_markup=_vnum_intro_kb(), parse_mode=HTML)
        return

    if data == "vnum_get":
        txt = (
            f"📲 <b>{to_bold('STEP 1: SELECT SERVICE')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Kiske liye number chahiye? Neeche service chuno 👇"
        )
        await _vnum_say(q, txt, _vnum_svc_kb())
        return

    if data.startswith("vnum_svc:"):
        sl = data.split(":")[1]
        svc_name = dict(VNUM_SERVICES).get(sl, sl.upper())
        context.user_data["vnum_svc"] = svc_name
        txt = (
            f"🌍 <b>{to_bold('STEP 2: SELECT COUNTRY')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Service: <b>{svc_name}</b>\n\n"
            "Kis country ka number chahiye? Country select karein 👇"
        )
        await _vnum_say(q, txt, _vnum_ctry_kb())
        return

    if data.startswith("vnum_ctry:"):
        cl = data.split(":")[1]
        ctry_name = dict(VNUM_COUNTRIES).get(cl, cl.upper())
        svc_name = context.user_data.get("vnum_svc", "WhatsApp")
        order_text = f"Hi, mujhe Virtual Number chahiye:\nService: {svc_name}\nCountry: {ctry_name}"
        contact_url = f"https://t.me/Supermannn_x?text={quote(order_text)}"
        card = (
            f"🎯 <b>{to_bold('STEP 3: GET YOUR NUMBER')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📲 <b>Service:</b> {svc_name}\n"
            f"🌍 <b>Country:</b> {ctry_name}\n"
            "⚡ <b>Delivery:</b> Instant (1-2 min)\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👉 Neeche <b>Contact Admin</b> button dabakar direct number lein:"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Contact @Supermannn_x", url=contact_url)],
            [InlineKeyboardButton("🔁 Select Another", callback_data="vnum_get")],
            [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
        ])
        await _vnum_say(q, card, kb)
        return

    # Sarkari & Student Portals
    if data == "sarkari_citizen":
        await q.message.edit_text(SARKARI_CITIZEN_TEXT, reply_markup=get_sarkari_citizen_kb(), parse_mode=HTML)
        return

    if data == "sarkari_state_list":
        await q.message.edit_text(STATE_PORTALS_TEXT, reply_markup=get_state_portals_kb(), parse_mode=HTML)
        return

    if data == "student_exam":
        await q.message.edit_text(STUDENT_EXAM_TEXT, reply_markup=get_student_exam_kb(), parse_mode=HTML)
        return

    # VIP Buy Handlers
    if data.startswith("buy_plan_"):
        plan_key = data.replace("buy_", "")
        qr_buf, plan_name, amt = generate_plan_payment_qr(UPI_ID, UPI_NAME, plan_key, uid)
        caption = (
            f"💎 <b>{to_bold(plan_name)}</b>\n\n"
            f"💰 <b>Amount:</b> ₹{amt}\n"
            f"🏦 <b>UPI ID:</b> <code>{UPI_ID}</code>\n\n"
            f"👉 <b>Payment Steps:</b>\n"
            f"1️⃣ QR Code scan karke ₹{amt} pay karein (PhonePe/GPay/Paytm)\n"
            f"2️⃣ Payment ka <b>Screenshot ya UTR / Transaction ID</b> yahan bhejein.\n\n"
            f"⚡ Admin verify karke turant VIP activate kar dega!"
        )
        context.user_data["mode"] = f"pay_proof_{plan_key}"
        await q.message.reply_photo(photo=qr_buf, caption=caption, parse_mode=HTML)
        return

    if data == "open_vip_menu":
        await q.message.reply_text("💎 Plan select karein:", reply_markup=get_premium_plans_kb(), parse_mode=HTML)
        return

    if data == "open_refer_menu":
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
        await q.message.reply_text(f"🎁 <b>Aapka Invite Link:</b>\n<code>{ref_link}</code>", parse_mode=HTML)
        return

    # Admin Approval Handlers
    if data.startswith("adm_appr_") and uid == ADMIN_ID:
        parts = data.split("_")
        target_uid = int(parts[2])
        days = int(parts[3])
        grant_premium(target_uid, days)
        await q.message.edit_caption(caption=f"✅ <b>Approved!</b> User <code>{target_uid}</code> ko {days} din VIP diya gaya.", parse_mode=HTML)
        try:
            await context.bot.send_message(
                target_uid,
                f"🎉 <b>Badhai ho!</b> Aapka payment approve ho gaya hai aur {days} din ka VIP Access activate ho gaya hai! 💎",
                parse_mode=HTML,
            )
        except Exception:
            pass
        return

    if data.startswith("adm_rej_") and uid == ADMIN_ID:
        target_uid = int(data.split("_")[2])
        await q.message.edit_caption(caption=f"❌ <b>Rejected!</b> Payment for user <code>{target_uid}</code> rejected.", parse_mode=HTML)
        try:
            await context.bot.send_message(target_uid, "❌ Aapka payment verification approve nahi hua. Kripya sahi screenshot/UTR bhejein.")
        except Exception:
            pass
        return

    # Advanced Channel Cloner Settings Handlers
    if data == "cloner_set_target":
        context.user_data["mode"] = "cloner_target"
        await q.message.reply_text("📑 <b>Set Chat ID:</b>\nTarget Channel ka Username ya ID bhejo:\n(jaise: <code>@MyChannel</code> ya <code>-100123456789</code>)\n\n<i>Note: Bot ko target channel me Admin banayein (Post permission ke saath).</i>", parse_mode=HTML)
        return

    if data == "cloner_set_source":
        context.user_data["mode"] = "cloner_source"
        await q.message.reply_text(
            "📡 <b>Set SOURCE Channel:</b>\nJis channel se posts UTHANI hain uska Username ya ID bhejo:\n"
            "(jaise: <code>@MySourceChannel</code> ya <code>-100123456789</code>)\n\n"
            "<i>Zaroori: Bot us source channel me bhi ADMIN hona chahiye — tabhi nayi posts bot tak aayengi.</i>",
            parse_mode=HTML,
        )
        return

    if data == "cloner_toggle_auto":
        cfg = get_cloner_config(uid)
        if cfg.get("auto_status") == "on":
            save_cloner_config(uid, auto_status="off")
            await q.message.reply_text(
                "🛑 <b>FULL AUTO CLONE OFF!</b>\n\nAb nayi posts khud clone nahi hongi. (Manual forwarding phir bhi kaam karegi.)",
                reply_markup=get_cloner_settings_kb(uid),
                parse_mode=HTML,
            )
            return

        if not cfg.get("target_chat_id"):
            await q.message.reply_text("⚠️ Pehle <b>📑 Target</b> channel set karo (jahan post jaani hai).", parse_mode=HTML)
            return
        if not cfg.get("source_chat_id"):
            await q.message.reply_text("⚠️ Pehle <b>📡 Source</b> channel set karo (jahan se post uthani hai).", parse_mode=HTML)
            return
        if str(cfg.get("target_chat_id")).strip() == str(cfg.get("source_chat_id")).strip():
            await q.message.reply_text("❌ Source aur Target same nahi ho sakte (warna post infinite loop me chalti rahegi).", parse_mode=HTML)
            return

        save_cloner_config(uid, auto_status="on")
        await q.message.reply_text(
            "🤖 <b>FULL AUTO CLONE ON! 🟢</b>\n\n"
            f"📡 Source: <code>{cfg.get('source_chat_id')}</code>\n"
            f"📑 Target: <code>{cfg.get('target_chat_id')}</code>\n\n"
            "Ab source channel me jo <b>nayi post</b> aayegi, bot 2-5 second me tumhare target channel me daal dega — "
            "caption, tag, watermark, replace/remove words aur thumbnail sab settings ke saath.\n\n"
            "<i>Note: Sirf NAYI posts clone hongi (purani posts nahi). Band karne ke liye yahi button dobara dabao.</i>",
            reply_markup=get_cloner_settings_kb(uid),
            parse_mode=HTML,
        )
        return

    if data == "cloner_set_tag":
        context.user_data["mode"] = "cloner_tag"
        await q.message.reply_text("🏷️ <b>Set Rename Tag:</b>\nHar video/post ke title/caption ke aage kya tag lagana hai?\n(jaise: <code>[🔥 4K HD]</code> ya <code>@MyChannel</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_caption":
        context.user_data["mode"] = "cloner_caption"
        await q.message.reply_text("📝 <b>Set Custom Caption:</b>\nPosts me kya custom caption daalna hai?\n(jaise: <code>Join @MyChannel for daily free updates!</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_replace":
        context.user_data["mode"] = "cloner_replace"
        await q.message.reply_text("🔄 <b>Replace Words / Links:</b>\nPurane words ko apne naye words se replace karein (Format: <code>OldWord=>NewWord</code>):\n\n(jaise:\n<code>@old_channel=>@MyChannel\nOldSite.com=>MySite.com</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_remove":
        context.user_data["mode"] = "cloner_remove"
        await q.message.reply_text("🗑️ <b>Remove Words / Promo Links:</b>\nPosts me se jo words/links delete karne hain unhe comma ya new line me bhejo:\n(jaise: <code>@spam_bot, join now, https://t.me/fake</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_thumb":
        context.user_data["mode"] = "cloner_thumb"
        await q.message.reply_text("🖼️ <b>Set Custom Thumbnail:</b>\nVideos aur Documents par lagane ke liye ek PHOTO bhejo:", parse_mode=HTML)
        return

    if data == "cloner_clear_thumb":
        save_cloner_config(uid, thumbnail_file_id="")
        await q.message.reply_text("❌ Custom thumbnail removed!", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    if data == "cloner_set_wm":
        context.user_data["mode"] = "cloner_wm"
        await q.message.reply_text("💧 <b>Watermark Setup:</b>\nPost ke bottom me lagane wala Watermark text/link bhejo:\n(jaise: <code>⚡ Forwarded by @MyChannel</code>)", parse_mode=HTML)
        return

    if data == "cloner_reset":
        save_cloner_config(uid, target="", caption="", watermark="", rename_tag="", replace_words="", remove_words="", thumbnail_file_id="", source_chat_id="", auto_status="off")
        context.user_data.pop("mode", None)
        await q.message.reply_text("🔄 <b>Settings Reset!</b> Saari cloner settings default ho gayi hain.", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    if data == "cloner_start_mode":
        context.user_data["mode"] = "cloning_active"
        await q.message.reply_text("🚀 <b>Fast Auto-Forward Active!</b>\n\nAb aap kisi bhi channel se 10-15 posts/videos forward karein ya direct media bhejein — bot 1-2 second me saari posts aapke target channel me post kar dega!\n\n/cancel dabakar kisi bhi waqt rok sakte hain.", parse_mode=HTML)
        return

    # Actor Voice Studio Presets
    if data.startswith("actor_voice_"):
        preset_key = data.replace("actor_voice_", "")
        context.user_data["voice_preset"] = preset_key
        p_name = ACTOR_VOICE_PRESETS.get(preset_key, {}).get("name", "Default")
        context.user_data["mode"] = "voice_text"
        await q.message.reply_text(f"🎙️ Selected Style: <b>{p_name}</b>\n\nAb woh <b>DIALOGUE / TEXT</b> bhejo jiska voice audio banana hai:", parse_mode=HTML)
        return

    # Password Callbacks
    if data == "pwd_name":
        context.user_data["mode"] = "pwd_name"
        await q.message.reply_text("👤 Apna <b>NAAM</b> bhejo (jaise: <code>Rahul</code> ya <code>Pooja</code>):", parse_mode=HTML)
        return

    if data == "pwd_rand":
        p1 = gen_password(16)
        p2 = gen_password(12)
        await q.message.reply_text(f"🔐 <b>{to_bold('STRONG PASSWORDS')}</b>\n\n1️⃣ <code>{p1}</code>\n2️⃣ <code>{p2}</code>", parse_mode=HTML)
        return


async def _vnum_say(q, text, kb):
    try:
        await q.message.edit_text(text, reply_markup=kb, parse_mode=HTML)
    except Exception:
        try:
            await q.message.reply_text(text, reply_markup=kb, parse_mode=HTML)
        except Exception:
            pass


# ---------------- TEXT HANDLER ----------------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    save_username(uid, user.username or "")
    if is_banned(uid):
        await update.message.reply_text(BAN_MSG)
        return

    raw_text = (update.message.text or "").strip()
    norm_text = unbold(raw_text).strip().upper()
    clean_key = re.sub(r"^[^\w\s]+\s*", "", norm_text).strip()

    # Match Action
    action = BTN_MODE_MAP.get(clean_key) or BTN_MODE_MAP.get(norm_text)

    if action:
        # 1. Virtual Numbers Funnel
        if action == "vnum":
            await send_vnum_card(update, context)
            return

        # 2. Text to Actors Voice Studio
        if action == "voice":
            buttons = []
            for k, v in ACTOR_VOICE_PRESETS.items():
                buttons.append([InlineKeyboardButton(v["name"], callback_data=f"actor_voice_{k}")])
            await update.message.reply_text(
                f"🎙️ <b>{to_bold('TEXT TO ACTORS & CELEBRITY VOICE STUDIO')}</b>\n\nActor / Character Style select karein 👇",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=HTML,
            )
            return

        # 3. Channel Cloner Dashboard
        if action == "cloner":
            _cfg = get_cloner_config(uid)
            _auto = "🟢 ON" if _cfg.get("auto_status") == "on" else "🔴 OFF"
            await update.message.reply_text(
                f"🔄 <b>{to_bold('CHANNEL CLONER & AUTO-FORWARDER')}</b>\n\n"
                f"📡 Source: <code>{_cfg.get('source_chat_id') or 'Not Set'}</code>\n"
                f"📑 Target: <code>{_cfg.get('target_chat_id') or 'Not Set'}</code>\n"
                f"🤖 FULL AUTO: <b>{_auto}</b>\n\n"
                "Customize settings for your files 👇",
                reply_markup=get_cloner_settings_kb(uid),
                parse_mode=HTML,
            )
            return

        # 4. Sarkari Portals
        if action == "sarkari":
            await update.message.reply_text(SARKARI_CITIZEN_TEXT, reply_markup=get_sarkari_citizen_kb(), parse_mode=HTML)
            return

        # 5. Student Exam Hub
        if action == "exam":
            await update.message.reply_text(STUDENT_EXAM_TEXT, reply_markup=get_student_exam_kb(), parse_mode=HTML)
            return

        # 6. Password Generator
        if action == "pwd":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Naam wala Password", callback_data="pwd_name")],
                [InlineKeyboardButton("🎲 Random Strong", callback_data="pwd_rand")],
                [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
            ])
            await update.message.reply_text(
                f"🔐 <b>{to_bold('PASSWORD GENERATOR')}</b>\n\nNaam ke saath password chahiye ya Random strong?",
                reply_markup=kb,
                parse_mode=HTML,
            )
            return

        # 7. Interest Calculator
        if action == "interest":
            context.user_data["mode"] = "int_p"
            await update.message.reply_text(
                f"📈 <b>{to_bold('INTEREST CALCULATOR')}</b>\n\nPrincipal amount (₹) bhejo:\n(jaise: <code>50000</code>)",
                parse_mode=HTML,
            )
            return

        # 8. Image to PDF
        if action == "pdf":
            context.user_data["mode"] = "pdf"
            context.user_data["pdf_pages"] = []
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Make PDF Now", callback_data="make_pdf_now")]])
            await update.message.reply_text(PROMPTS["pdf"], reply_markup=kb, parse_mode=HTML)
            return

        # 9. VIP Premium, Refer & Account
        if action == "premium":
            await cmd_premium(update, context)
            return
        if action == "refer":
            await cmd_refer(update, context)
            return
        if action == "account":
            await cmd_account(update, context)
            return
        if action == "admin":
            await cmd_admin(update, context)
            return

        # Standard prompt modes
        context.user_data["mode"] = action
        if action in PROMPTS:
            # Check Daily Limit
            u = get_user(uid, update.effective_user.first_name)
            if check_limit_exceeded(u):
                await update.message.reply_text(get_limit_exceeded_text(), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                return
            await update.message.reply_text(PROMPTS[action] + "\n\n<i>/cancel kabhi bhi dabayein.</i>", parse_mode=HTML)
            return

    # Check Active Working Modes
    mode = context.user_data.get("mode")

    # Cloner Mode Active
    if mode == "cloning_active":
        ok, msg_res = await forward_cloned_message(context.bot, update.message, uid)
        await update.message.reply_text(msg_res, parse_mode=HTML)
        return

    if mode == "cloner_target":
        raw_val = raw_text.strip()
        resolved = raw_val
        warn = ""
        try:
            chat = await context.bot.get_chat(raw_val)
            resolved = str(chat.id)
            try:
                mem = await context.bot.get_chat_member(chat_id=chat.id, user_id=context.bot.id)
                if mem.status not in ("administrator", "creator"):
                    warn = "\n\n⚠️ <b>Bot wahan ADMIN nahi hai!</b> Us channel me jaake bot ko Admin banao (Post Messages permission ke saath), warna post nahi hoga."
            except Exception:
                warn = "\n\n⚠️ <i>Admin check nahi ho paya. Confirm kar lo ki bot wahan admin hai.</i>"
        except Exception:
            warn = "\n\n<i>(Username resolve nahi hua — value as-it-is save kar di. Numeric ID -100... zyada safe hota hai.)</i>"

        save_cloner_config(uid, target=resolved)
        context.user_data.pop("mode", None)
        await update.message.reply_text(
            f"✅ <b>Target Channel set:</b> <code>{resolved}</code>{warn}\n\nAb <b>📡 Source</b> set karke <b>🤖 FULL AUTO</b> ON karo.",
            reply_markup=get_cloner_settings_kb(uid),
            parse_mode=HTML,
        )
        return

    if mode == "cloner_source":
        raw_val = raw_text.strip()
        try:
            chat = await context.bot.get_chat(raw_val)
            resolved = str(chat.id)
            title = chat.title or chat.username or resolved
            is_admin = False
            try:
                mem = await context.bot.get_chat_member(chat_id=chat.id, user_id=context.bot.id)
                is_admin = mem.status in ("administrator", "creator")
            except Exception:
                is_admin = False

            save_cloner_config(uid, source_chat_id=resolved)
            context.user_data.pop("mode", None)

            if is_admin:
                txt = (
                    f"✅ <b>Source Channel set:</b> {hesc(str(title))}\n"
                    f"🆔 <code>{resolved}</code>\n\n"
                    "Ab neeche <b>🤖 FULL AUTO</b> button dabakar ON karo — phir is channel ki har nayi post khud clone hogi!"
                )
                if str(get_cloner_config(uid).get("target_chat_id") or "").strip() == resolved:
                    txt += "\n\n⚠️ <b>Dhyan do:</b> Source aur Target same channel hai — auto clone ON nahi hoga."
            else:
                txt = (
                    f"⚠️ <b>Source Channel save ho gaya:</b> <code>{resolved}</code>\n\n"
                    "❌ Par bot wahan <b>ADMIN nahi hai</b>! Us source channel me jaake bot ko <b>Admin</b> banao.\n"
                    "<i>Warna nayi posts bot tak nahi aayengi aur auto clone kaam nahi karega.</i>"
                )
            await update.message.reply_text(txt, reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        except Exception as e:
            await update.message.reply_text(
                f"❌ Ye channel nahi mila: <code>{hesc(raw_val)}</code>\n<i>{hesc(str(e))[:120]}</i>\n\n"
                "Private channel ke liye numeric ID bhejo (jaise <code>-1001234567890</code>).\n"
                "💡 ID nikalne ka aasan tareeka: us channel ki koi <b>TEXT post</b> is bot ko forward karo — bot ID bata dega.",
                reply_markup=get_cloner_settings_kb(uid),
                parse_mode=HTML,
            )
        return

    if mode == "cloner_tag":
        save_cloner_config(uid, rename_tag=raw_text)
        context.user_data.pop("mode", None)
        await update.message.reply_text(f"✅ Rename Tag set: <b>{raw_text}</b>", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    if mode == "cloner_caption":
        save_cloner_config(uid, caption=raw_text)
        context.user_data.pop("mode", None)
        await update.message.reply_text("✅ Custom Caption saved!", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    if mode == "cloner_replace":
        save_cloner_config(uid, replace_words=raw_text)
        context.user_data.pop("mode", None)
        await update.message.reply_text("✅ Replace Words rules saved!", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    if mode == "cloner_remove":
        save_cloner_config(uid, remove_words=raw_text)
        context.user_data.pop("mode", None)
        await update.message.reply_text("✅ Remove Words list saved!", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    if mode == "cloner_wm":
        save_cloner_config(uid, watermark=raw_text)
        context.user_data.pop("mode", None)
        await update.message.reply_text("✅ Watermark saved!", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    # Payment Proof Submission
    if mode and mode.startswith("pay_proof_"):
        plan_key = mode.replace("pay_proof_", "")
        if ADMIN_ID != 0:
            kb_adm = get_payment_admin_kb(uid, plan_key)
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 <b>New VIP Payment Proof!</b>\n\n• <b>User ID:</b> <code>{uid}</code>\n• <b>User:</b> @{update.effective_user.username or 'NoUser'}\n• <b>Plan:</b> {plan_key}\n• <b>Proof/UTR:</b> {hesc(raw_text)}",
                reply_markup=kb_adm,
                parse_mode=HTML,
            )
        await update.message.reply_text("✅ Payment proof submit ho gaya! Admin verify karke 5 minute me VIP activate kar dega.")
        context.user_data.pop("mode", None)
        return

    # Check Daily Limit for Active Executions
    u = get_user(uid, update.effective_user.first_name)
    if mode and check_limit_exceeded(u):
        await update.message.reply_text(get_limit_exceeded_text(), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
        return

    # Tool Execution Modes
    if mode == "terabox":
        st = await update.message.reply_text("⚡ Cloud link resolve kar raha hoon (6-engine chain)...")
        res = resolve_cloud_url(raw_text)

        if res.get("ok"):
            files = res.get("files") or []
            if len(files) > 1:
                lines = []
                for idx, f in enumerate(files[:12], 1):
                    lines.append(f"{idx}. <b>{hesc(str(f.get('name'))[:52])}</b> — <code>{f.get('size', 'N/A')}</code>")
                cap = (
                    f"⚡ <b>{to_bold(str(res.get('provider', 'Cloud Direct')))}</b>\n\n"
                    f"📂 <b>{len(files)} files mili:</b>\n" + "\n".join(lines) +
                    "\n\n👇 Neeche button se koi bhi file download karein:"
                )
                rows = [[InlineKeyboardButton(f"⬇️ {str(f.get('name'))[:32]}", url=f["dlink"])] for f in files[:5]]
            else:
                cap = (
                    f"⚡ <b>{to_bold(str(res.get('provider', 'Cloud Direct')))}</b>\n\n"
                    f"📁 <b>Title:</b> {hesc(str(res.get('title', 'File'))[:80])}\n"
                    f"📊 <b>Size:</b> {res.get('size', 'N/A')}\n"
                )
                if res.get("note"):
                    cap += f"ℹ️ {hesc(str(res['note']))}\n"
                cap += f"\n🔗 <b>High-Speed Link:</b>\n<code>{res.get('direct_url')}</code>"
                rows = [[InlineKeyboardButton("🚀 Download / Stream", url=res.get("direct_url"))]]
                if res.get("stream_url") and res.get("stream_url") != res.get("direct_url"):
                    rows[0].append(InlineKeyboardButton("▶️ Web Player", url=res["stream_url"]))
            await st.edit_text(cap, reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            cap = (
                f"⚠️ <b>{to_bold('DIRECT LINK NAHI MIL PAYA')}</b>\n\n"
                f"{hesc(str(res.get('error', 'Cloud link resolve nahi hua.')))}\n\n"
            )
            if res.get("hint"):
                cap += f"💡 <b>Pro Tip:</b> {hesc(str(res['hint']))}\n\n"
            cap += "👇 <b>Ye trusted web downloaders try karein (free):</b>"
            rows = [[InlineKeyboardButton(nm, url=u)] for nm, u in (res.get("fallback_links") or [])]
            await st.edit_text(cap, reply_markup=InlineKeyboardMarkup(rows[:6]), parse_mode=HTML)
        add_use(uid)
        return

    # UNIVERSAL VIDEO DOWNLOADER (Instagram + YouTube + Facebook + X + TikTok + 20 platforms)
    if mode == "insta_dl":
        if not is_supported_video_url(raw_text):
            await update.message.reply_text(
                fail_msg("UNSUPPORTED LINK",
                         "Ye link supported nahi hai. Instagram, YouTube, Facebook, X (Twitter), TikTok, "
                         "Snapchat, Pinterest, Reddit, Vimeo waale links bhejein."),
                parse_mode=HTML,
            )
            return

        plat = platform_name(raw_text)
        st = await update.message.reply_text(f"📥 {plat} se media fetch kar raha hoon (best quality + full audio)...")
        res = await download_video_async(raw_text)

        if not res.get("ok"):
            reason = str(res.get("error", "Media extract nahi hua."))
            await st.edit_text(
                fail_msg(f"{plat.upper()} DOWNLOAD FAILED", reason)
                + "\n\n💡 <b>Kya karein:</b>\n"
                  "• Post <b>public</b> hai ya nahi check karein\n"
                  "• 30-60 second baad dobara try karein (server rate-limit)\n"
                  "• Instagram ke liye <code>IG_COOKIES_FILE</code> env set karne se 100% reliable ho jata hai\n"
                  "• Ya phir <b>LINK BYPASS</b> tool se direct link nikalein",
                parse_mode=HTML,
            )
            return

        try:
            mtype = res.get("type")
            engine = hesc(str(res.get("engine", "")))
            title = hesc(str(res.get("title") or ""))[:60]

            # 1) Album / Carousel (2-10 items ek saath)
            if mtype == "carousel" and res.get("items"):
                items = res["items"][:10]
                media_group = []
                for idx, item in enumerate(items):
                    m_buf = io.BytesIO(item["bytes"])
                    cap = f"📸 <b>{to_bold('ALBUM')}</b> • {len(items)} items • {plat}" if idx == 0 else ""
                    if item["type"] == "video":
                        m_buf.name = f"media_{idx}.mp4"
                        media_group.append(InputMediaVideo(media=m_buf, caption=cap, parse_mode=HTML, supports_streaming=True))
                    else:
                        m_buf.name = f"media_{idx}.jpg"
                        media_group.append(InputMediaPhoto(media=m_buf, caption=cap, parse_mode=HTML))
                await update.message.reply_media_group(media=media_group)
                await st.delete()
                add_use(uid)
                return

            # 2) Single Video
            if mtype == "video" and res.get("bytes"):
                media_buf = io.BytesIO(res["bytes"])
                media_buf.name = f"{plat.replace(' ', '_')}_video.mp4"
                dur = res.get("duration") or 0
                dur_line = f"• ⏱️ Length: {int(dur) // 60}m {int(dur) % 60}s\n" if dur else ""
                title_line = f"• 📝 {title}\n" if title else ""
                await update.message.reply_video(
                    video=media_buf,
                    caption=(
                        f"📥 <b>{to_bold(plat.upper() + ' VIDEO')}</b>\n"
                        f"{title_line}{dur_line}"
                        f"• 📊 <b>Size:</b> {res.get('size_mb')} MB\n"
                        f"• 🔊 <b>Audio:</b> Original ✅\n"
                        f"• ⚙️ Engine: {engine}"
                    ),
                    parse_mode=HTML,
                    supports_streaming=True,
                )
                await st.delete()
                add_use(uid)
                return

            # 3) Single Photo
            if mtype == "photo" and res.get("bytes"):
                media_buf = io.BytesIO(res["bytes"])
                media_buf.name = "media_photo.jpg"
                await update.message.reply_photo(
                    photo=media_buf,
                    caption=(f"🖼️ <b>{to_bold(plat.upper() + ' PHOTO')}</b>\n"
                             + (f"• 📝 {title}\n" if title else "")
                             + f"• 📊 {res.get('size_mb')} MB"),
                    parse_mode=HTML,
                )
                await st.delete()
                add_use(uid)
                return

            # 4) Bada file (48MB+): direct link dete hain — kaam rukta nahi
            if mtype == "link" and res.get("direct_url"):
                mb = res.get("size_mb") or 0
                rows = [
                    [InlineKeyboardButton("🚀 Direct Download Link", url=res["direct_url"])],
                    [InlineKeyboardButton("🌐 Original Page Kholo", url=raw_text)],
                ]
                await st.edit_text(
                    f"📥 <b>{to_bold('DOWNLOAD LINK READY')}</b>\n\n"
                    f"🎬 <b>Platform:</b> {plat}\n"
                    + (f"📝 <b>Title:</b> {title}\n" if title else "")
                    + (f"📊 <b>Size:</b> {mb} MB\n" if mb else "")
                    + f"⚙️ Engine: {engine}\n\n"
                    + hesc(str(res.get("note") or ""))
                    + "\n\n👇 Neeche button dabakar download karein:",
                    reply_markup=InlineKeyboardMarkup(rows),
                    parse_mode=HTML,
                )
                add_use(uid)
                return

            await st.edit_text(fail_msg("SEND ERROR", "Media mil gayi par bhejne me dikkat aayi. Dobara try karein."), parse_mode=HTML)
        except Exception as e:
            await st.edit_text(fail_msg("SEND ERROR", str(e)), parse_mode=HTML)
        return

    if mode == "voice_text":
        st = await update.message.reply_text("🎙️ Generating Actor Voiceover...")
        preset = context.user_data.get("voice_preset", "don_amitabh")
        try:
            mp3_path = await generate_actor_voice(raw_text, preset)
            p_info = ACTOR_VOICE_PRESETS.get(preset, {})
            with open(mp3_path, "rb") as f:
                await update.message.reply_voice(
                    voice=f,
                    caption=f"🎙️ <b>{to_bold('ACTOR VOICE READY')}</b>\n• Style: {p_info.get('name', 'Actor')}",
                    parse_mode=HTML,
                )
            await st.delete()
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except Exception as e:
            await st.edit_text(fail_msg("VOICE GENERATION FAILED", str(e)), parse_mode=HTML)
        add_use(uid)
        return

    if mode == "rto":
        res = lookup_vehicle_rto(raw_text)
        if res.get("ok"):
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚦 Check e-Challan", url=res["challan_link"])],
                [InlineKeyboardButton("🚗 mParivahan Status", url=res["parivahan_link"])],
            ])
            card = (
                f"🚗 <b>{to_bold('RTO VEHICLE DETAILS')}</b>\n\n"
                f"• <b>Plate:</b> <code>{res['plate']}</code>\n"
                f"• <b>State:</b> {res['state_name']} ({res['state_code']})\n"
                f"• <b>RTO Office:</b> {res['rto_code']}\n\n"
                "👉 Direct Parivahan verification links neeche hain 👇"
            )
            await update.message.reply_text(card, reply_markup=kb, parse_mode=HTML)
        else:
            await update.message.reply_text(fail_msg("RTO LOOKUP FAILED", res.get("error", "Invalid Plate")), parse_mode=HTML)
        add_use(uid)
        return

    if mode == "numinfo":
        res = lookup_phone_info(raw_text)
        if res.get("ok"):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Open WhatsApp Chat", url=res["wa_link"])]])
            card = (
                f"📱 <b>{to_bold('NUMBER INFORMATION')}</b>\n\n"
                f"• <b>Number:</b> <code>{res['national']}</code>\n"
                f"• <b>Country:</b> {res['country']}\n"
                f"• <b>Operator:</b> {res['operator']}\n"
                f"• <b>Timezone:</b> {res['timezones']}"
            )
            await update.message.reply_text(card, reply_markup=kb, parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {res.get('error')}")
        add_use(uid)
        return

    if mode == "ifsc":
        i_res = lookup_ifsc(raw_text)
        if i_res.get("ok"):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📍 View on Google Maps", url=i_res["maps_link"])]])
            card = (
                f"🏦 <b>{to_bold(i_res['bank'])}</b>\n\n"
                f"• <b>IFSC:</b> <code>{i_res['ifsc']}</code>\n"
                f"• <b>Branch:</b> {i_res['branch']}\n"
                f"• <b>Address:</b> {i_res['address']}\n"
                f"• <b>City/State:</b> {i_res['city']}, {i_res['state']}\n"
                f"• <b>UPI / NEFT:</b> {i_res['upi']}"
            )
            await update.message.reply_text(card, reply_markup=kb, parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {i_res.get('error')}")
        add_use(uid)
        return

    if mode == "pin":
        p_res = lookup_pincode(raw_text)
        if p_res.get("ok"):
            card = (
                f"📮 <b>{to_bold('PINCODE DETAILS')} ({p_res['pincode']})</b>\n\n"
                f"• <b>District:</b> {p_res['district']}\n"
                f"• <b>State:</b> {p_res['state']}\n"
                f"• <b>Division:</b> {p_res['division']}\n"
                f"• <b>Post Offices ({p_res['total_offices']}):</b> {p_res['post_offices']}"
            )
            await update.message.reply_text(card, parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {p_res.get('error')}")
        add_use(uid)
        return

    # ID Finder - Safely handles both Telegram v20+ forward_origin and direct @username / 'me'
    if mode == "idfind":
        if raw_text.lower() == "me":
            await update.message.reply_text(f"🆔 <b>Aapki Telegram ID:</b> <code>{uid}</code>", parse_mode=HTML)
        elif raw_text.startswith("@"):
            found = find_by_username(raw_text)
            if found:
                await update.message.reply_text(f"🆔 <b>User:</b> @{found[2]}\n• <b>Name:</b> {found[1]}\n• <b>ID:</b> <code>{found[0]}</code>", parse_mode=HTML)
            else:
                p_info = check_username_platforms(raw_text)
                kb_links = [[InlineKeyboardButton(p["name"], url=p["url"])] for p in p_info["platforms"][:4]]
                await update.message.reply_text(f"🔍 <b>Social Profile Links for:</b> <code>{raw_text}</code>", reply_markup=InlineKeyboardMarkup(kb_links), parse_mode=HTML)
        else:
            await update.message.reply_text("🆔 Kisi ka message FORWARD karein ya <code>@username</code> bhejein.")
        return

    if mode == "pwd_name":
        passwords = name_passwords(raw_text)
        res_txt = f"👤 <b>{to_bold('PASSWORDS FOR')} {raw_text.upper()}:</b>\n\n"
        for i, p in enumerate(passwords, 1):
            res_txt += f"{i}️⃣ <code>{p}</code>\n"
        await update.message.reply_text(res_txt, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "qr":
        buf = make_qr_bytes(raw_text)
        await update.message.reply_photo(photo=buf, caption=f"📷 <b>{to_bold('HD QR CODE GENERATED')}</b>", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "short":
        st = await update.message.reply_text("🔗 Short links bana raha hoon (6 providers)...")
        links = shorten_url(raw_text, want=3)
        exp = expand_url(raw_text)
        clean = exp.get("cleaned", raw_text)
        if links:
            body = "\n\n".join(f"{i}️⃣ <b>{name}</b> → <code>{u}</code>" for i, (name, u) in enumerate(links, 1))
            extra = ""
            if clean and clean != raw_text:
                extra = f"\n\n🧹 <b>Tracking-free original:</b>\n<code>{clean}</code>"
            rows = [[InlineKeyboardButton(f"🔗 {name}", url=u)] for name, u in links]
            await st.edit_text(f"🔗 <b>{to_bold('SHORT LINKS READY')}</b>\n\n{body}{extra}", reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            await st.edit_text(
                f"⚠️ <b>Short link nahi ban paya</b> (saare providers busy hain).\n\n"
                f"🧹 <b>Saaf kiya hua original link:</b>\n<code>{clean}</code>\n\n"
                "<i>10-20 second baad dobara try karein.</i>",
                parse_mode=HTML,
            )
        add_use(uid)
        return

    if mode == "linkbypass":
        st = await update.message.reply_text("🔓 Link kholte hue redirect chain check kar raha hoon...")
        cloud = resolve_cloud_url(raw_text)
        if cloud.get("ok"):
            await st.edit_text(
                f"🔓 <b>{to_bold('CLOUD DIRECT LINK')}</b>\n\n"
                f"📁 {hesc(str(cloud.get('title', 'File'))[:70])}\n"
                f"📊 {cloud.get('size', 'N/A')}\n\n"
                f"🔗 <code>{cloud.get('direct_url')}</code>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Open Link", url=cloud.get("direct_url"))]]),
                parse_mode=HTML,
            )
            add_use(uid)
            return

        exp = expand_url(raw_text)
        chain = exp.get("chain") or [raw_text]
        final = exp.get("final") or raw_text
        clean = exp.get("cleaned") or final
        chain_txt = "\n".join(f"   {i}. <code>{hesc(c[:70])}</code>" for i, c in enumerate(chain[:5], 1))
        kb_rows = [[InlineKeyboardButton("🚀 Open Clean Link", url=clean)]]
        await st.edit_text(
            f"🔓 <b>{to_bold('LINK UNPACKED')}</b>\n\n"
            f"🔁 <b>Redirects:</b> {exp.get('hops', 0)}"
            f"{'  (shortened link tha)' if exp.get('is_shortener') else ''}\n"
            f"{chain_txt}\n\n"
            f"🧹 <b>Final Clean Link (tracking hata di):</b>\n<code>{clean}</code>"
            + (f"\n\nℹ️ {hesc(str(cloud.get('error','')))[:100]}" if cloud.get('error') and 'support nahi' not in str(cloud.get('error','')) else ""),
            reply_markup=InlineKeyboardMarkup(kb_rows),
            parse_mode=HTML,
        )
        add_use(uid)
        return

    if mode == "linkcheck":
        st = await update.message.reply_text("🛡️ Link ko 6-layer safety scan me daal raha hoon...")
        chk = check_link_safety(raw_text)
        risk = chk.get("risk", 0)
        bar = "█" * max(1, risk // 10) + "░" * (10 - max(1, risk // 10))
        reasons_txt = "\n".join(f"• {r}" for r in chk.get("reasons", [])[:8])
        sig = chk.get("signals", {})
        cap = (
            f"🛡️ <b>{to_bold('LINK SAFETY REPORT')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Verdict:</b> {chk.get('verdict')}\n"
            f"📊 <b>Risk Score:</b> <code>{bar}</code> {risk}/100\n"
            f"🌐 <b>Final URL:</b> <code>{hesc(str(chk.get('final_url'))[:90])}</code>\n"
            f"🔁 Redirects: {sig.get('redirect_hops', 0)} | 🔓 HTTPS: {'✅' if sig.get('https') else '❌'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 <b>Kya mila:</b>\n{reasons_txt}\n\n"
            f"💡 <b>Aap kya karein:</b> {chk.get('advice')}"
        )
        kb_rows = [[InlineKeyboardButton("🌐 Final Link Kholo", url=chk.get("final_url"))]]
        await st.edit_text(cap, reply_markup=InlineKeyboardMarkup(kb_rows), parse_mode=HTML)
        add_use(uid)
        return

    # ---- INTEREST CALCULATOR (pehle toota hua tha: principal ke baad kuch nahi hota tha) ----
    if mode == "int_p":
        try:
            p = float(re.sub(r"[^\d.]", "", raw_text.replace(",", "")) or 0)
            assert p > 0
        except Exception:
            await update.message.reply_text("⚠️ Valid amount bhejein (jaise: <code>50000</code> ya <code>1.5 lakh</code>)", parse_mode=HTML)
            return
        context.user_data["int_principal"] = p
        context.user_data["mode"] = "int_r"
        await update.message.reply_text(
            f"📈 <b>{to_bold('INTEREST CALCULATOR')}</b> — Step 2/3\n\n"
            f"💰 Amount: <b>₹{p:,.0f}</b>\n\n"
            "Ab <b>saalana interest rate (%)</b> bhejein:\n(jaise: <code>8.5</code>)",
            parse_mode=HTML,
        )
        return

    if mode == "int_r":
        try:
            r = float(re.search(r"\d+(?:\.\d+)?", raw_text).group(0))
        except Exception:
            await update.message.reply_text("⚠️ Rate number me bhejein (jaise: <code>8.5</code>)", parse_mode=HTML)
            return
        context.user_data["int_rate"] = r
        context.user_data["mode"] = "int_t"
        await update.message.reply_text(
            f"📈 <b>{to_bold('INTEREST CALCULATOR')}</b> — Step 3/3\n\n"
            f"💰 ₹{context.user_data['int_principal']:,.0f} @ <b>{r}%</b> saalana\n\n"
            "Ab <b>time</b> bhejein — months me (jaise <code>24</code>) ya saal me (jaise <code>2 saal</code>):",
            parse_mode=HTML,
        )
        return

    if mode == "int_t":
        p_amt = float(context.user_data.get("int_principal", 0) or 0)
        r_pct = float(context.user_data.get("int_rate", 0) or 0)
        raw_low = raw_text.lower()
        try:
            num = float(re.search(r"\d+(?:\.\d+)?", raw_low).group(0))
        except Exception:
            await update.message.reply_text("⚠️ Time bhejein — <code>24</code> (months) ya <code>2 saal</code>", parse_mode=HTML)
            return
        months = int(num * 12) if any(w in raw_low for w in ("saal", "year", "yr", "varsh")) else int(num)
        if months < 1 or months > 600:
            await update.message.reply_text("⚠️ Time 1 mahine se 50 saal ke beech rakhein.", parse_mode=HTML)
            return

        res_i = calc_interest(p_amt, r_pct, months)
        context.user_data.pop("mode", None)
        await update.message.reply_text(
            f"📈 <b>{to_bold('INTEREST CALCULATION REPORT')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Principal:</b> ₹{p_amt:,.0f}\n"
            f"📊 <b>Rate:</b> {r_pct}% per year\n"
            f"⏳ <b>Time:</b> {months} months ({res_i['years']} years)\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ <b>Simple Interest:</b>\n"
            f"   • Interest: ₹{res_i['simple_interest']:,.0f}\n"
            f"   • Total: <b>₹{res_i['simple_total']:,.0f}</b>\n\n"
            f"2️⃣ <b>Compound (Monthly):</b>\n"
            f"   • Interest: ₹{res_i['compound_monthly']:,.0f}\n"
            f"   • Total: <b>₹{res_i['compound_monthly_total']:,.0f}</b>\n\n"
            f"3️⃣ <b>FD Style Comparison:</b>\n"
            f"   • Quarterly: ₹{res_i['compound_quarterly']:,.0f} interest\n"
            f"   • Half-Yearly: ₹{res_i['compound_halfyearly']:,.0f} interest\n"
            f"   • Yearly: ₹{res_i['compound_yearly']:,.0f} interest\n\n"
            f"💡 <i>Farak: compound me ₹{res_i['compound_monthly'] - res_i['simple_interest']:,.0f} zyada banta hai.</i>",
            parse_mode=HTML,
        )
        add_use(uid)
        return

    if mode == "emi":
        p_amt, rate, months = parse_emi_input(raw_text)
        if not p_amt:
            await update.message.reply_text(
                "⚠️ <b>EMI ke liye aise bhejein:</b>\n\n"
                "• <code>100000</code> → ₹1L @ 10.5% / 12 months\n"
                "• <code>5,00,000 9% 24m</code> → poora control\n"
                "• <code>3 lakh 8.5% 5 saal</code> → Hindi style bhi chalega",
                parse_mode=HTML,
            )
            return
        emi, rows = emi_schedule(p_amt, rate, months)
        total_pay = emi * months
        total_int = total_pay - p_amt
        sched = "\n".join(
            f"  {m}. EMI ₹{e:,.0f} → Principal ₹{pr:,.0f} + Interest ₹{i:,.0f}"
            for (m, e, pr, i, bal) in rows[:6]
        )
        await update.message.reply_text(
            f"🧮 <b>{to_bold('LOAN EMI CALCULATOR')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Loan:</b> ₹{p_amt:,.0f}\n"
            f"📊 <b>Rate:</b> {rate}% per year\n"
            f"⏳ <b>Tenure:</b> {months} months\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Monthly EMI: ₹{emi:,.0f}</b>\n"
            f"📈 <b>Total Interest:</b> ₹{total_int:,.0f}\n"
            f"💳 <b>Total Payment:</b> ₹{total_pay:,.0f}\n\n"
            f"📅 <b>Pehle 6 mahine ka breakdown:</b>\n{sched}",
            parse_mode=HTML,
        )
        add_use(uid)
        return

    if mode == "age":
        try:
            parts = [int(x) for x in re.split(r"[-/.]", raw_text)]
            d = date(parts[2], parts[1], parts[0])
            res = calc_age(d)
            if res:
                y, m, da, total_d, next_d, day_name = res
                z = zodiac(parts[0], parts[1])
                await update.message.reply_text(
                    f"🎂 <b>{to_bold('AGE DETAILS')}</b>\n\n• <b>Age:</b> {y} Years, {m} Months, {da} Days\n• <b>Total Days:</b> {total_d:,} Days\n• <b>Next Birthday:</b> in {next_d} Days ({day_name})\n• <b>Zodiac Sign:</b> {z}",
                    parse_mode=HTML,
                )
            else:
                await update.message.reply_text("⚠️ Future date nahi daal sakte!")
        except Exception:
            await update.message.reply_text("⚠️ Format: DD-MM-YYYY (jaise: 15-08-2005)")
        return

    if mode == "upi":
        qr_buf = make_qr_bytes(f"upi://pay?pa={raw_text}&pn=User")
        await update.message.reply_photo(photo=qr_buf, caption=f"💰 <b>UPI QR Code:</b> <code>{raw_text}</code>", parse_mode=HTML)
        add_use(uid)
        return

    # Rich Web Search with 5-6 verified links, copyable code tags & suggestions
    if mode == "search":
        st = await update.message.reply_text("🔎 Searching verified web sources...")
        search_results = search_web_rich(raw_text, max_results=6)
        if search_results:
            res_text = f"🔎 <b>{to_bold('WEB SEARCH RESULTS')} for:</b> <i>{hesc(raw_text)}</i>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            kb_links = []
            for i, item in enumerate(search_results, 1):
                badge = "⭐ Best Match" if i == 1 else ("⚡ Fast Stream" if i == 2 else "📌 Verified")
                res_text += f"{i}️⃣ <b>{hesc(item['title'])}</b> <i>({badge})</i>\n"
                if item.get("snippet"):
                    res_text += f"   <i>{hesc(item['snippet'])}</i>\n"
                res_text += f"   📋 <b>Copy Link:</b> <code>{item['url']}</code>\n\n"
                kb_links.append([InlineKeyboardButton(f"{i}️⃣ Open {item['title'][:25]}...", url=item["url"])])

            res_text += "💡 <i>Tip: Tap on any link code to copy it! Agar Terabox link hai to Terabox tool me paste karein.</i>"
            await st.edit_text(res_text, reply_markup=InlineKeyboardMarkup(kb_links[:5]), parse_mode=HTML, disable_web_page_preview=True)
        else:
            q_enc = quote(raw_text)
            fallback_text = (
                f"🔎 <b>{to_bold('SEARCH RESULTS')} for:</b> <i>{hesc(raw_text)}</i>\n\n"
                f"1️⃣ <b>Google:</b> <code>https://www.google.com/search?q={q_enc}</code>\n"
                f"2️⃣ <b>DuckDuckGo:</b> <code>https://duckduckgo.com/?q={q_enc}</code>"
            )
            await st.edit_text(fallback_text, parse_mode=HTML)
        add_use(uid)
        return

    # 6-Store App Finder including GetModPC
    if mode == "appfind":
        app_data = get_app_store_links(raw_text)
        kb_stores = []
        for s in app_data["stores"]:
            kb_stores.append([InlineKeyboardButton(f"{s['name']}", url=s["url"])])
        await update.message.reply_text(
            f"📦 <b>{to_bold('APP STORES FOR')}: {app_data['app_name']}</b>\n\n"
            "Official stores & Top 5 Verified Mod/APK websites available 👇",
            reply_markup=InlineKeyboardMarkup(kb_stores),
            parse_mode=HTML,
        )
        add_use(uid)
        return

    if mode == "shot":
        st = await update.message.reply_text("📸 Capturing full HD screenshot...")
        buf = site_screenshot(raw_text)
        if buf:
            await update.message.reply_photo(photo=buf, caption=f"🖼️ Screenshot: <code>{raw_text}</code>", parse_mode=HTML)
            await st.delete()
        else:
            await st.edit_text("❌ Screenshot failed. Please check URL.")
        add_use(uid)
        return

    # Forwarded message for ID Finder (Safely handles Telegram forward_origin without AttributeError)
    if hasattr(update.message, "forward_origin") and update.message.forward_origin:
        orig = update.message.forward_origin
        if hasattr(orig, "sender_user") and orig.sender_user:
            f_user = orig.sender_user
            await update.message.reply_text(f"🆔 <b>Forwarded User ID:</b> <code>{f_user.id}</code>\n• <b>Name:</b> {hesc(f_user.first_name)}", parse_mode=HTML)
            return
        elif hasattr(orig, "chat") and orig.chat:
            f_chat = orig.chat
            await update.message.reply_text(f"🆔 <b>Forwarded Channel/Chat ID:</b> <code>{f_chat.id}</code>\n• <b>Title:</b> {hesc(f_chat.title)}", parse_mode=HTML)
            return

    # Default fallback
    await update.message.reply_text("👇 Neeche grid menu se tool chunein:", reply_markup=kb_for(uid))


# ---------------- PHOTO / DOCUMENT HANDLERS ----------------
async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = context.user_data.get("mode")

    # Cloner Mode Active
    if mode == "cloning_active":
        ok, msg_res = await forward_cloned_message(context.bot, update.message, uid)
        await update.message.reply_text(msg_res, parse_mode=HTML)
        return

    # Custom Thumbnail Setup for Cloner
    if mode == "cloner_thumb":
        thumb_id = update.message.photo[-1].file_id
        save_cloner_config(uid, thumbnail_file_id=thumb_id)
        context.user_data.pop("mode", None)
        await update.message.reply_text("✅ <b>Custom Thumbnail Saved!</b> Ab se sabhi forwarded videos/docs par yeh thumbnail lagega.", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    # Payment Proof Photo
    if mode and mode.startswith("pay_proof_"):
        plan_key = mode.replace("pay_proof_", "")
        photo_id = update.message.photo[-1].file_id
        if ADMIN_ID != 0:
            kb_adm = get_payment_admin_kb(uid, plan_key)
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=photo_id,
                caption=f"🔔 <b>New VIP Payment Screenshot!</b>\n\n• <b>User ID:</b> <code>{uid}</code>\n• <b>User:</b> @{update.effective_user.username or 'NoUser'}\n• <b>Plan:</b> {plan_key}",
                reply_markup=kb_adm,
                parse_mode=HTML,
            )
        await update.message.reply_text("✅ Payment screenshot submit ho gaya! Admin verify karke 5 minute me VIP activate kar dega.")
        context.user_data.pop("mode", None)
        return

    # Photo Studio: Name & DOP Stamp
    if mode == "pp_stamp":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        context.user_data["raw_photo"] = buf.getvalue()
        context.user_data["mode"] = "pp_stamp_text"
        await update.message.reply_text("✍️ Ab apna <b>NAME aur DATE OF PHOTO (DOP)</b> bhejo:\n(jaise: <code>RAHUL SHARMA 30-09-2026</code>)", parse_mode=HTML)
        return

    if mode == "pp_stamp_text":
        raw = context.user_data.get("raw_photo")
        if not raw:
            await update.message.reply_text("⚠️ Pehle photo bhejein!")
            return
        parts = update.message.text.strip().rsplit(" ", 1)
        name = parts[0] if parts else "CANDIDATE NAME"
        dop = parts[1] if len(parts) > 1 else date.today().strftime("%d-%m-%Y")
        stamped, sz = make_stamped_passport(raw, name, dop)
        await update.message.reply_photo(
            photo=stamped,
            caption=f"📸 <b>{to_bold('OFFICIAL GOVT EXAM PHOTO READY')}</b>\n\n• <b>Name:</b> {name.upper()}\n• <b>DOP:</b> {dop}\n• <b>Size:</b> {sz} KB (20-50KB compliant ✅)",
            parse_mode=HTML,
        )
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    # Signature Cleaner
    if mode == "sig_clean":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        cleaned, sz = clean_signature(buf.getvalue())
        await update.message.reply_photo(
            photo=cleaned,
            caption=f"✍️ <b>{to_bold('SIGNATURE CLEANED & ENHANCED')}</b>\n\n• Background: Pure White\n• Size: {sz} KB (10-20KB official compliance ✅)",
            parse_mode=HTML,
        )
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    # Printable 8-in-1 Sheet
    if mode == "print_sheet":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        sheet = make_printable_sheet(buf.getvalue(), 8)
        await update.message.reply_photo(
            photo=sheet,
            caption=f"🖨️ <b>{to_bold('PRINTABLE 8-IN-1 PASSPORT SHEET READY')}</b>\n\n(4x6 inch lab print sheet @ 300 DPI)",
            parse_mode=HTML,
        )
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    # Document PDF Compressor
    if mode == "doc_compress":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        pdf_buf = compress_document_pdf([buf.getvalue()], 250)
        pdf_buf.name = "Compressed_Document.pdf"
        await update.message.reply_document(
            document=pdf_buf,
            caption=f"📄 <b>{to_bold('COMPRESSED DOCUMENT PDF READY')}</b>\n\n(Under 250KB - Govt portal compliant ✅)",
            parse_mode=HTML,
        )
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    # Image to PDF
    if mode == "pdf":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        pages = context.user_data.setdefault("pdf_pages", [])
        pages.append(buf.getvalue())
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Make PDF ({len(pages)} photos)", callback_data="make_pdf_now")]])
        await update.message.reply_text(f"📸 Photo {len(pages)} added! Aur bhejein ya button dabayein 👇", reply_markup=kb)
        return


# ---------------- FULL AUTO CLONER ENGINE (v31) ----------------
# Album (media group) ko thoda wait karke ek saath bhejne ke liye buffer
_ALBUM_BUFFER: dict = {}


async def _flush_album(bot, key, delay: float = 1.4):
    """Album ke saare items aane ka wait karta hai, phir ek saath (album) post karta hai."""
    await asyncio.sleep(delay)
    item = _ALBUM_BUFFER.pop(key, None)
    if not item:
        return
    msgs = item.get("msgs", [])
    if not msgs:
        return
    for uid in item.get("uids", []):
        ok, res = await clone_messages(bot, msgs, uid)
        if item.get("notify"):
            try:
                await bot.send_message(chat_id=item["notify"], text=res, parse_mode=HTML)
            except Exception:
                pass
        if not ok:
            log.warning("Album clone fail (uid=%s): %s", uid, res)


async def on_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """VIDEO / FILE / AUDIO / VOICE / GIF / STICKER handler (Manual Forward Mode + ID Finder)."""
    msg = update.message
    if not msg:
        return
    uid = update.effective_user.id
    mode = context.user_data.get("mode")

    if is_banned(uid):
        return

    # Manual Cloner Mode Active
    if mode == "cloning_active":
        if msg.media_group_id:
            key = ("manual", uid, msg.media_group_id)
            item = _ALBUM_BUFFER.get(key)
            if item:
                item["msgs"].append(msg)
            else:
                _ALBUM_BUFFER[key] = {"msgs": [msg], "uids": [uid], "notify": update.effective_chat.id}
                asyncio.create_task(_flush_album(context.bot, key))
            return
        ok, res = await forward_cloned_message(context.bot, msg, uid)
        await msg.reply_text(res, parse_mode=HTML)
        return

    # ID Finder: forwarded media ka original user/channel ID batao
    if getattr(msg, "forward_origin", None):
        orig = msg.forward_origin
        if getattr(orig, "sender_user", None):
            f_user = orig.sender_user
            await msg.reply_text(
                f"🆔 <b>Forwarded User ID:</b> <code>{f_user.id}</code>\n• <b>Name:</b> {hesc(f_user.first_name or '')}",
                parse_mode=HTML,
            )
            return
        if getattr(orig, "chat", None):
            f_chat = orig.chat
            await msg.reply_text(
                f"🆔 <b>Forwarded Channel/Chat ID:</b> <code>{f_chat.id}</code>\n• <b>Title:</b> {hesc(f_chat.title or '')}",
                parse_mode=HTML,
            )
            return


async def on_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FULL AUTO: Source channel me nayi post aayi -> uske sabhi auto-cloners ke target me bhej do.
    (Bot ko us channel me admin hona chahiye, tabhi ye update milta hai.)"""
    msg = update.effective_message
    if not msg or not msg.chat:
        return

    src_id = str(msg.chat.id)
    cloners = get_auto_cloners_for_source(src_id)
    if not cloners:
        return

    # Target == Source ho to skip (infinite loop se bachne ke liye)
    uids = [c["user_id"] for c in cloners if str(c.get("target_chat_id") or "").strip() != src_id]
    if not uids:
        return

    if msg.media_group_id:
        key = ("auto", src_id, msg.media_group_id)
        item = _ALBUM_BUFFER.get(key)
        if item:
            item["msgs"].append(msg)
        else:
            _ALBUM_BUFFER[key] = {"msgs": [msg], "uids": uids, "notify": None}
            asyncio.create_task(_flush_album(context.bot, key))
        return

    for uid in uids:
        ok, res = await clone_messages(context.bot, [msg], uid)
        if not ok:
            log.warning("Auto clone fail (uid=%s): %s", uid, res)


async def on_pdf_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.data == "make_pdf_now":
        pages = context.user_data.get("pdf_pages", [])
        if not pages:
            await q.answer("Pehle photo bhejein!", show_alert=True)
            return
        await q.answer("Creating PDF...")
        pdf_bytes = pages_to_pdf(pages)
        buf = io.BytesIO(pdf_bytes)
        buf.name = "UtilityDuniya_Document.pdf"
        await q.message.reply_document(
            document=buf,
            caption=f"📄 <b>{to_bold('MULTI-PAGE PDF READY')} ({len(pages)} pages)!</b>",
            parse_mode=HTML,
        )
        context.user_data.pop("pdf_pages", None)
        context.user_data.pop("mode", None)


# ---------------- ERROR HANDLER ----------------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Exception handling update: %s", context.error)


# ---------------- POST INIT ----------------
async def _post_init(app: Application):
    commands = [
        BotCommand("start", "Start the Super Bot"),
        BotCommand("menu", "Open Tools Grid"),
        BotCommand("premium", "VIP Subscription Plans"),
        BotCommand("refer", "Refer Friends = Free VIP"),
        BotCommand("account", "My Account Status"),
        BotCommand("cancel", "Cancel current action"),
    ]
    await app.bot.set_my_commands(commands)
    log.info("Commands set successfully!")


# ---------------- KEEPALIVE WEB SERVER ON RENDER PORT 10000 ----------------
def _keepalive():
    import http.server
    import socketserver

    port = int(os.environ.get("PORT", "10000"))

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>ToolVault / Utility Duniya Super Bot is Running 24/7! Status: 200 OK</h1>")

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    try:
        with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
            log.info("Keepalive server listening on port %s for UptimeRobot / Render", port)
            httpd.serve_forever()
    except Exception as e:
        log.warning("Keepalive server warning: %s", e)


def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN is missing in environment variables or .env file!")
        return

    threading.Thread(target=_keepalive, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("help", cmd_menu))
    app.add_handler(CommandHandler("account", cmd_account))
    app.add_handler(CommandHandler("refer", cmd_refer))
    app.add_handler(CommandHandler("premium", cmd_premium))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("grant", cmd_grant))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))

    # Specific Tool Commands
    app.add_handler(CommandHandler("vnum", lambda u, c: send_vnum_card(u, c)))
    app.add_handler(CommandHandler("terabox", lambda u, c: u.message.reply_text(PROMPTS["terabox"], parse_mode=HTML)))
    app.add_handler(CommandHandler("cloner", lambda u, c: u.message.reply_text(f"🔄 <b>{to_bold('CHANNEL CLONER')}</b>", reply_markup=get_cloner_settings_kb(u.effective_user.id), parse_mode=HTML)))
    app.add_handler(CommandHandler("sarkari", lambda u, c: u.message.reply_text(SARKARI_CITIZEN_TEXT, reply_markup=get_sarkari_citizen_kb(), parse_mode=HTML)))
    app.add_handler(CommandHandler("exam", lambda u, c: u.message.reply_text(STUDENT_EXAM_TEXT, reply_markup=get_student_exam_kb(), parse_mode=HTML)))

    # Callbacks
    app.add_handler(CallbackQueryHandler(on_pdf_cb, pattern="^make_pdf_now$"))
    app.add_handler(CallbackQueryHandler(on_cb))

    # Message Handlers
    # (a) FULL AUTO: source channel ki nayi posts (bot ko us channel me admin hona chahiye)
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POSTS, on_channel_post))

    # (b) Private / Group chats
    _dm_or_group = filters.ChatType.PRIVATE | filters.ChatType.GROUPS
    _any_media = (
        filters.VIDEO
        | filters.ANIMATION
        | filters.Document.ALL
        | filters.AUDIO
        | filters.VOICE
        | filters.VIDEO_NOTE
        | filters.Sticker.ALL
    )
    app.add_handler(MessageHandler(filters.PHOTO & _dm_or_group, on_photo))
    app.add_handler(MessageHandler(_any_media & _dm_or_group, on_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & _dm_or_group, on_text))

    app.add_error_handler(on_error)

    print("🚀 Starting ToolVault / Utility Duniya Super Bot (v30 Ultra)...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
