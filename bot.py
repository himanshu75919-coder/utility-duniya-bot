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
    create_payment,
    get_payment,
    payment_stats,
    pending_payments,
    pending_payments_count,
    recent_payments,
    revoke_premium,
    set_payment_admin_msg,
    set_payment_status,
    shot_exists,
    user_payment_history,
    user_payments,
    utr_exists,
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
    compress_document_pdf,
    make_printable_sheet,
    make_stamped_passport,
)
from modules.cloud_tools import resolve_cloud_url
from modules.channel_cloner import (
    CLONER_GUIDE_TEXT,
    clone_messages,
    cloner_summary_text,
    forward_cloned_message,
    get_cloner_settings_kb,
)
from modules.voice_studio import (
    ACTOR_VOICE_PRESETS,
    VOICE_LAB,
    VOICE_LAB_MAP,
    VOICE_SPEEDS,
    generate_actor_voice,
    generate_voice,
    voice_label,
)
from modules.media_downloader import (
    download_instagram_async,
    download_video_async,
    is_instagram_url,
    is_supported_video_url,
    platform_name,
)
from modules.toolkit_extras import (
    calc_interest,
    emi_full_report,
    check_link_safety,
    expand_url,
    file_size_human,
    parse_emi_input,
    rate_from_per_hundred,
    shorten_url,
    village_compound_interest,
)
from modules.osint_tools import (
    NUM_LEAK_ENABLED,
    PUBLIC_RECORD_WARNING,
    check_username_platforms,
    lookup_public_records,
    search_by_area_name,
    lookup_ifsc,
    lookup_ip_domain,
    lookup_phone_info,
    lookup_pincode,
    lookup_vehicle_rto,
)
from modules.general_tools import (
    gen_passphrase,
    gen_pin,
    password_strength,
    vcard_data,
    wifi_qr_data,
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
from modules.payguard import (
    MAX_BAD_TRIES,
    admin_payment_card,
    analyze_screenshot,
    shot_verdict_line,
    user_payment_reply,
    utr_help_text,
    validate_utr,
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

# v33: ek se zyada admin (ADMINS=123,456) — owner + helper admins kaam kar sakte hain
_ADMIN_EXTRA = [int(x) for x in re.split(r"[,\s]+", os.getenv("ADMINS", "")) if x.strip().isdigit()]
ADMIN_IDS = {x for x in {ADMIN_ID, *_ADMIN_EXTRA} if x}
OWNER_ID = ADMIN_ID


def is_admin(uid: int) -> bool:
    """Owner/admin hai? Uske liye koi premium limit nahi lagti."""
    return bool(ADMIN_IDS) and uid in ADMIN_IDS
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


def check_limit_exceeded(u: dict, uid: int = 0) -> bool:
    """Owner/admin ke liye koi limit nahi. VIP ke liye nahi. Free users ke liye FREE_LIMIT."""
    if uid and is_admin(uid):
        return False
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


def inr(amount, decimals: int = 0) -> str:
    """Indian style money format: 100000 -> ₹1,00,000 | 12500000 -> ₹1,25,00,000 (lakh/crore style)."""
    try:
        neg = amount < 0
        n = abs(float(amount))
        if decimals:
            whole = int(n)
            frac = round((n - whole) * (10 ** decimals))
        else:
            whole = int(round(n))      # rupee tak round (89,792.8 -> 89,793)
            frac = 0
        st = str(whole)
        if len(st) > 3:
            head, tail = st[:-3], st[-3:]
            parts = []
            while len(head) > 2:
                parts.insert(0, head[-2:]); head = head[:-2]
            if head:
                parts.insert(0, head)
            st = ",".join(parts) + "," + tail
        out = f"₹{st}"
        if decimals and frac:
            out += f".{frac:0{decimals}d}"
        return ("-₹" + out[1:]) if neg else out
    except Exception:
        return f"₹{amount}"


def words_amount(amount) -> str:
    """1,00,000 -> '1 lakh' | 1,25,00,000 -> '1.25 crore' (samajhne me aasan)."""
    try:
        n = float(amount)
    except Exception:
        return ""
    if n >= 10000000:
        return f"{n / 10000000:.2f} crore".replace(".00", "")
    if n >= 100000:
        return f"{n / 100000:.2f} lakh".replace(".00", "")
    if n >= 1000:
        return f"{n / 1000:.1f} hazaar".replace(".0", "")
    return ""


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
    [f"📥 {to_bold('VIDEO DOWNLOADER')}", f"📸 {to_bold('PASSPORT PHOTO (NAME/DOP)')}"],
    [f"🖨️ {to_bold('8-IN-1 PRINT SHEET')}", f"📄 {to_bold('DOCUMENT PDF COMPRESS')}"],
    [f"🏛️ {to_bold('SARKARI SEVA PORTALS')}", f"🎓 {to_bold('STUDENT EXAM HUB')}"],
    [f"📱 {to_bold('NUMBER INFO')}", f"🏦 {to_bold('IFSC INFO')}"],
    [f"📮 {to_bold('PINCODE INFO')}", f"🆔 {to_bold('ID & USERNAME FINDER')}"],
    [f"🌐 {to_bold('IP / DOMAIN INFO')}", f"🔒 {to_bold('PRIVATE CHANNEL SETUP')}"],
    [f"📷 {to_bold('QR CODE')}", f"🖼️ {to_bold('IMAGE→PDF')}"],
    [f"🔗 {to_bold('URL SHORT')}", f"🔓 {to_bold('LINK BYPASS')}"],
    [f"🔍 {to_bold('LINK CHECK')}", f"🧮 {to_bold('EMI CALC')}"],
    [f"📈 {to_bold('INTEREST CALC')}", f"🎂 {to_bold('AGE CALCULATOR')}"],
    [f"💰 {to_bold('UPI QR GENERATOR')}", f"🔐 {to_bold('PASSWORD GENERATOR')}"],
    [f"🔎 {to_bold('WEB SEARCH')}", f"📦 {to_bold('APP FINDER')}"],
    [f"🖼️ {to_bold('SITE SCREENSHOT')}", f"💎 {to_bold('VIP PREMIUM')}"],
    [f"🎁 {to_bold('REFER & EARN')}", f"👤 {to_bold('MY ACCOUNT')}"],
    [f"❓ {to_bold('MADAD / TUTORIAL')}"],
]


def main_keyboard(admin: bool = False):
    rows = [row[:] for row in KB_BTNS]
    if admin:
        rows.append([f"🛠️ {to_bold('ADMIN PANEL')}", f"👑 {to_bold('OWNER MODE')}"])
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t) for t in row] for row in rows],
        resize_keyboard=True,
        input_field_placeholder="Tool select karein 👇",
    )


def kb_for(uid: int):
    return main_keyboard(admin=is_admin(uid))


# Exact Action Mapping
BTN_MODE_MAP = {
    "VIRTUAL NUMBERS": "vnum",
    "TERABOX DOWNLOADER": "terabox",
    "CHANNEL CLONER": "cloner",
    "ACTORS VOICE STUDIO": "voice",
    "INSTA DOWNLOADER": "insta_dl",
    "INSTAGRAM DOWNLOADER": "insta_dl",
    "VIDEO DOWNLOADER": "insta_dl",
    "UNIVERSAL VIDEO DOWNLOADER": "insta_dl",
    "VIRAL VIDEO DOWNLOAD": "insta_dl",
    "PASSPORT PHOTO (NAME/DOP)": "pp_stamp",
    "8-IN-1 PRINT SHEET": "print_sheet",
    "DOCUMENT PDF COMPRESS": "doc_compress",
    "DOCUMENT PDF COMPRESSOR": "doc_compress",
    "IP / DOMAIN INFO": "ip",
    "PRIVATE CHANNEL SETUP": "cloner_private_help",
    "IP INFO": "ip",
    "QR (LINK / TEXT)": "qr",
    "QR (UPI PAYMENT)": "qr_upi",
    "QR (WIFI SHARE)": "qr_wifi",
    "QR (CONTACT CARD)": "qr_vcard",
    "PASSWORD (NAAM WALA)": "pwd_name",
    "PASSWORD (RANDOM)": "pwd_rand",
    "PASSWORD (RANDOM PIN)": "pwd_pin",
    "PASSWORD (EASY WORDS)": "pwd_phrase",
    "SITE SCREENSHOT (HD)": "shot",
    "SITE SCREENSHOT (FULL PAGE)": "shot_full",
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
    "MADAD / TUTORIAL": "tutorial",
    "MADAD": "tutorial",
    "HELP / TUTORIAL": "tutorial",
    "ADMIN PANEL": "admin",
    "OWNER MODE": "owner",
}

PROMPTS = {
    "terabox": (
        f"⚡ <b>{to_bold('TERABOX & CLOUD DIRECT DOWNLOADER')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein:</b> app me file ka <b>Share</b> → <b>Copy link</b> → wo link yahan paste karke bhejo.\n"
        "✅ Chalte hain: <b>Terabox, Mediafire, Google Drive, Mega</b>\n"
        "🎁 Milega: bina ad, bina speed-limit <b>direct download link</b> + browser player\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔗 <b>Ab apna link bhejo</b> (jaise <code>https://terabox.com/s/xxxxx</code>):"
    ),
    "insta_dl": (
        f"📥 <b>{to_bold('UNIVERSAL VIDEO DOWNLOADER')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein:</b> app me video ke <b>Share</b> → <b>Copy link</b> → yahan paste karke bhejo.\n"
        "✅ Chalte hain: <b>Instagram, YouTube, Facebook, X/Twitter, TikTok, Pinterest, Reddit, Vimeo</b> (20+ sites)\n"
        "📦 48MB tak video seedha bot me aayega; bada file ho to <b>direct download link</b> milega.\n"
        "🎵 Instagram Reel ka <b>original audio</b> bhi milta hai.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔗 <b>Ab video ka link bhejo:</b>"
    ),
    "pp_stamp": (
        f"📸 <b>{to_bold('GOVT EXAM PASSPORT PHOTO STUDIO')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein:</b> 1️⃣ photo bhejo → 2️⃣ <b>naam</b> likho → 3️⃣ <b>photo ki date</b> (DD-MM-YYYY) → ready ✅\n"
        "🎁 Milega: official <b>3.5 × 4.5 cm</b> photo (20-50KB) + neeche naam &amp; date ka stamp (SSC/Railway/BPSC form ke liye)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 <b>Ab apni passport photo bhejo:</b>"
    ),
    "print_sheet": (
        f"🖨️ <b>{to_bold('PRINTABLE 8-IN-1 PASSPORT SHEET')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein:</b> ek passport photo bhejo → bot usi ki <b>8 copies ek 4×6 inch sheet</b> par laga dega.\n"
        "🖨️ Ye sheet kisi bhi photo studio par ₹10-20 me print karwa lo — 8 photo mil jayengi!\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 <b>Ab apni ek photo bhejo:</b>"
    ),
    "doc_compress": (
        f"📄 <b>{to_bold('DOCUMENT & MARKSHEET PDF COMPRESSOR')}</b>\n\n"
        "<blockquote>10th/12th/Caste marksheet → sharp PDF, 100KB se 500KB tak size aap chuno</blockquote>\n\n"
        "📸 Marksheet ya certificate ki <b>photo bhejo</b> (2-3 photos bhi bhej sakte ho, sab ek PDF me aayengi):\n"
        "<i>Photo bhejte hi size ke buttons aa jayenge 👇</i>"
    ),
    "ip": (
        f"🌐 <b>{to_bold('IP / DOMAIN INFO')}</b>\n\n"
        "Kisi bhi <b>IP address</b> ya <b>website</b> ke baare me poori detail:\n"
        "• Kahan hai (desha/state/city) • Kaunsi company (ISP) • VPN/Proxy hai ya nahi\n\n"
        "👉 IP bhejo (jaise <code>8.8.8.8</code>) ya website ka naam (jaise <code>google.com</code>):"
    ),
    "rto": (
        f"🚗 <b>{to_bold('RTO VEHICLE INFORMATION')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein:</b> number plate bhejo → pata chalega ki <b>kaunse state + kaunse RTO (district)</b> ki gaadi hai.\n"
        "✅ Milega: state, RTO office, district + <b>5 official link</b> (VAHAN, e-Challan, insurance, DL, mParivahan) — "
        "wahan se asli RC/owner/challan status dekh sakte ho.\n"
        "<i>Asli RC details Parivahan par OTP daal kar hi milti hain — hum aapko seedha wahan pahuncha dete hain.</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔢 <b>Ab number plate bhejo</b> (jaise <code>BR01AB1234</code>):"
    ),
    "numinfo": (
        f"📱 <b>{to_bold('NUMBER INFORMATION')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein:</b> 10 digit number bhejo → <b>operator, circle (region), number type</b> + aage check karne ke 6 link "
        "(WhatsApp, Telegram, Truecaller, Google, Chakshu spam-report, 1930 cyber helpline).\n"
        "🧾 Result ke neeche <b>Public Records</b> ka button milega — chaho to wahan se naam/pata bhi dekh sakte ho "
        "(<i>uska misuse crime hai — sirf legal kaam ke liye</i>). MNP ke baad operator badal bhi sakta hai.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔢 <b>Ab 10 digit number bhejo</b> (jaise <code>9876543210</code>):"
    ),
    "ifsc": (
        f"🏦 <b>{to_bold('IFSC BANK BRANCH LOOKUP')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein:</b> passbook/cheque par IFSC code likha hota hai — wahi yahan bhejo.\n"
        "✅ Milega: <b>bank ka naam, branch, address, MICR code</b>, UPI/NEFT/RTGS/IMPS support + Maps link.\n"
        "💸 Paisa bhejne se pehle <b>branch check karna</b> zaroori hai — galat IFSC se paisa wapas aata hai.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔤 <b>Ab IFSC code bhejo</b> (jaise <code>SBIN0000001</code>):"
    ),
    "pin": (
        f"📮 <b>{to_bold('PINCODE & POST OFFICE INFO')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein — 2 tareeke:</b>\n"
        "1️⃣ <b>6-digit pincode</b> bhejo (jaise <code>800001</code>) → district, state, division + saare post offices\n"
        "2️⃣ <b>Area / post office ka naam</b> bhejo (jaise <code>Rajendra Nagar</code>) → pincode mil jayega\n"
        "📦 Online form, order ya courier me pincode galat ho to ye tool kaam aayega.\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    ),
    "idfind": (
        f"🆔 <b>{to_bold('ID & USERNAME FINDER')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein (3 tareeke):</b>\n"
        "1️⃣ <code>me</code> bhejo → apni Telegram ID + username\n"
        "2️⃣ Kisi ka <b>message forward</b> karo → uski Telegram ID (user ya channel ki)\n"
        "3️⃣ <code>@username</code> bhejo → <b>asli check</b>: GitHub, Telegram, YouTube, TikTok, Steam par account hai ya nahi (✅/❌) "
        "+ 9 aur platforms ke direct link\n\n"
        "<i>Ye ID kaam aati hai: channel ID nikalne, force-subscribe lagane, kisi ko report/block karne ke liye.</i>"
    ),
    "qr": (
        f"📷 <b>{to_bold('HD QR CODE GENERATOR')}</b>\n\n"
        "Koi bhi TEXT, UPI ID, WiFi ya LINK bhejo:"
    ),
    "pdf": (
        f"🖼️ <b>{to_bold('IMAGE TO MULTI-PAGE PDF')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaise use karein:</b> ek-ek karke <b>10 photos tak</b> bhejo → phir neeche wala button dabao.\n"
        "📄 <b>Normal PDF</b> = jaisa hai waisa | <b>A4 PDF</b> = printer par sahi size (kuch kat nahi aayega)\n"
        "📸 <b>Ab photos bhejo:</b>"
    ),
    "short": (
        f"🔗 <b>{to_bold('URL SHORTENER')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaam:</b> lamba link chhota kar dena, taaki WhatsApp/Telegram par share karna aasan ho.\n"
        "🔗 <b>Ab lamba link bhejo</b> (jaise <code>https://example.com/very/long/path?x=1</code>):"
    ),
    "linkbypass": (
        f"🔓 <b>{to_bold('LINK BYPASS / UNPACK')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaam:</b> ad-wale short link (GPLinks/VPLinks/redirect) ka <b>asli destination</b> nikalna — bina ad ke.\n"
        "🔗 <b>Ab woh link bhejo:</b>"
    ),
    "linkcheck": (
        f"🔍 <b>{to_bold('LINK SAFETY & FRAUD CHECKER')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaam:</b> link kholne se pehle check karo — <b>fake/scam hai ya asli</b> (bank wale fake link aksar aise pakde jaate hain).\n"
        "🔍 <b>Ab link bhejo</b> (jaise <code>http://sbi-kyc-verify.xyz</code>):"
    ),
    "emi": (
        f"🧮 <b>{to_bold('LOAN EMI CALCULATOR')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaam:</b> batata hai <b>har mahine kitni EMI</b> jayegi aur <b>loan kitne mahine/din me poora chuk jayega</b>.\n"
        "📝 Aise likh kar bhejo:\n"
        "• <code>100000</code> → ₹1 lakh, 10.5% saalana, 12 mahine\n"
        "• <code>5,00,000 9% 24m</code> → poora control\n"
        "• <code>3 lakh 8.5% 5 saal</code> → Hindi me bhi chalega\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    ),
    "age": (
        f"🎂 <b>{to_bold('AGE & BIRTHDAY CALCULATOR')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaam:</b> janm tithi se <b>exact umar</b> (saal-mahine-din) + agla birthday kitne din baad + rashi.\n"
        "🎂 <b>Birth date bhejo</b> (DD-MM-YYYY), jaise <code>15-08-2005</code>:"
    ),
    "upi": (
        f"💰 <b>{to_bold('UPI QR GENERATOR WITH AMOUNT')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaam:</b> apna payment QR banana (dukaan, auto, tuition fees) — customer scan karega, paisa seedha account me.\n"
        "💰 <b>Apni UPI ID bhejo</b> (jaise <code>9876543210@ybl</code>):"
    ),
    "search": (
        f"🔎 <b>{to_bold('FAST & ACCURATE WEB SEARCH')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaam:</b> Google jaisa search — <b>DuckDuckGo + Bing ke asli results</b> ek saath (title + link + description).\n"
        "🔎 <b>Kya dhoondhna hai? Likh kar bhejo</b> (jaise <code>Bihar board 12th result date</code>):"
    ),
    "appfind": (
        f"📦 <b>{to_bold('APP & MOD STORE FINDER (8 TRUSTED STORES)')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Kaam:</b> app ka naam bhejo → 8 trusted store ke <b>direct links</b> (Play Store, APKPure, APKCombo, HappyMod, Uptodown, F-Droid...) "
        "— kisi random site se APK download mat karo, virus ka khatra hota hai.\n"
        "📦 <b>App ka naam bhejo</b> (jaise <code>instagram</code>):"
    ),
    "shot": (
        f"🖼️ <b>{to_bold('WEBSITE SCREENSHOT (HD)')}</b>\n\n"
        "Website ka URL bhejo (jaise: <code>github.com</code>):\n"
        "<i>Poora lamba page chahiye? Menu se 'SITE SCREENSHOT' → 📜 Full Page chunein.</i>"
    ),
    "shot_full": (
        f"📜 <b>{to_bold('FULL PAGE SCREENSHOT')}</b>\n\n"
        "Website ka URL bhejo — poora upar se neeche tak page capture hoga (lambi site ke liye best):\n"
        "<i>Thoda time lagega (10-20 sec), wait karein.</i>"
    ),
    "qr_upi": (
        f"💰 <b>{to_bold('UPI PAYMENT QR')}</b>\n\n"
        "Apni <b>UPI ID</b> bhejo (jaise: <code>9876543210@ybl</code>)\n"
        "<i>Isse dukaan/gadi ke liye payment QR ban jayega.</i>"
    ),
    "qr_wifi": (
        f"📶 <b>{to_bold('WIFI SHARE QR')}</b>\n\n"
        "Apne <b>WiFi ka naam (SSID)</b> bhejo (jaise: <code>JioFiber_Home</code>):\n"
        "<i>Guest scan karega → WiFi automatic connect ho jayega.</i>"
    ),
    "qr_vcard": (
        f"👤 <b>{to_bold('CONTACT CARD QR')}</b>\n\n"
        "Apna <b>naam</b> bhejo (jaise: <code>Himanshu Kumar</code>):\n"
        "<i>Scan karne par contact save ho jayega.</i>"
    ),
    "pwd_pin": (
        f"🔢 <b>{to_bold('RANDOM PIN GENERATOR')}</b>\n\n"
        "<i>Ye mode khud 5 random 6-digit PIN bana dega.</i>"
    ),
    "pwd_phrase": (
        f"🧠 <b>{to_bold('EASY WORDS PASSWORD')}</b>\n\n"
        "<i>Ye mode 4 strong password dega jo yaad rakhna aasan hai.</i>"
    ),
}

TUTORIAL_TEXT = (
    f"❓ <b>{to_bold('MADAD / TUTORIAL — HAR TOOL 1 LINE ME')}</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "🎯 <b>Roz kaam ke tools:</b>\n"
    "• 🔄 <b>CHANNEL CLONER</b> → Source channel do, Target do, FULL AUTO ON — posts khud copy hongi. "
    "Bot ko dono channel me Admin banao. Private channel? Uski koi post bot ko forward karo, bot ID pakad lega.\n"
    "• 📥 <b>VIDEO DOWNLOADER</b> → Instagram/YouTube/Facebook ka link bhejo, video mil jayega\n"
    "• ⚡ <b>TERABOX</b> → TeraBox link bhejo, direct download link milega\n"
    "• 💎 <b>TERABOX/CLOUD</b> (GDrive, MediaFire, Mega) → link paste karo, direct link milega\n\n"
    "🎙️ <b>Voice:</b>\n"
    "• 🎙️ <b>VOICE STUDIO</b> → Koi bhi text likho, asli awaaz me audio ban jayega (24 actor + 30 lab voices)\n\n"
    "📄 <b>Document:</b>\n"
    "• 📄 <b>DOC PDF COMPRESS</b> → Marksheet ki photo bhejo, 100-500KB ka PDF banao\n"
    "• 🖼️ <b>IMAGE→PDF</b> → 10 photos tak → ek PDF (A4 print bhi)\n"
    "• 📸 <b>PASSPORT PHOTO</b> → Photo + naam/DOB do → print-ready sheet\n"
    "• 🖨️ <b>8-IN-1 SHEET</b> → Ek photo se 8 copies ek A4 par\n\n"
    "🔍 <b>Info:</b>\n"
    "• 🚗 <b>RTO</b> → Gaadi ka number bhejo → state/RTO/links\n"
    "• 📱 <b>NUMBER INFO</b> → 10 digit number → operator/circle (+ 🧾 chaho to public records button)\n"
    "• 🏦 <b>IFSC</b> → IFSC code → bank, branch, MICR\n"
    "• 📮 <b>PINCODE</b> → pincode ya area ka naam → post offices\n"
    "• 🌐 <b>IP INFO</b> → IP ya website → location, ISP\n"
    "• 🆔 <b>ID FINDER</b> → <code>me</code> ya <code>@username</code> → asli check\n\n"
    "🧰 <b>Roz ke chhote tools:</b>\n"
    "• 📷 <b>QR</b> → link, UPI, WiFi, contact card ka QR\n"
    "• 🔐 <b>PASSWORD</b> → naam wala / easy words / random / PIN\n"
    "• 🧮 <b>EMI</b> → <code>500000 9% 24m</code> → EMI + kitne din me poora\n"
    "• 📈 <b>VYAAJ</b> → <code>50000</code> → <code>5</code> (₹100 par ₹5) → <code>12</code> mahine → chakravriddhi hisaab\n"
    "• 📸 <b>SCREENSHOT</b> → website ka URL → HD ya full page photo\n"
    "• 🔎 <b>WEB SEARCH</b> → kuch bhi dhoondo\n"
    "• 📦 <b>APP FINDER</b> → app ka naam → safe download links\n"
    "• 🔗 <b>URL SHORT</b> / 🔓 <b>LINK BYPASS</b> / 🔍 <b>LINK CHECK</b>\n"
    "• 🎂 <b>AGE CALC</b> → DOB → kitne saal/mahine/din\n"
    "• 👨‍👩‍👦 <b>FAMILY TREE</b> → naam → relationship calculator\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⌨️ <b>Commands:</b> /start /menu /help /tutorial /cancel\n\n"
    "💬 <b>Stuck ho gaye?</b> Koi bhi tool kholo — uske andar bhi chhota guide milta hai. "
    "Aur har tool me <b>⚙️ /cancel</b> dabakar nikal sakte ho."
)


VOICE_HOME_TEXT = (
    f"🎙️ <b>{to_bold('ACTORS VOICE STUDIO')}</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Yahan aap <b>text likh kar asli awaaz</b> bana sakte ho (jaise video ke liye voiceover):\n\n"
    "🎭 <b>Actor / Character Voices</b> — 24 alag-alag awaazein\n"
    "   (Don, South mass hero, Shayar, Robot, Anime girl, News anchor... sab alag 🔥)\n\n"
    "🧪 <b>Voice Lab</b> — 30 awaazein + speed control\n"
    "   (Hindi, English, Tamil, Telugu, Bengali, Marathi, Urdu, Arabic, French... )\n\n"
    "💡 <i>Hindi me likhoge to Hindi awaaz, English me likhoge to English awaaz — hum khud set kar lenge.</i>"
)

VOICE_GUIDE_TEXT = (
    "📘 <b>VOICE STUDIO — KAISE USE KAREIN?</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "1️⃣ Upar <b>Actor Voices</b> ya <b>Voice Lab</b> me se koi chuno\n"
    "2️⃣ Jo <b>text/dialogue</b> bolwana hai, wo chat me bhejo\n"
    "   (jaise: <i>Beta, mehnat karo, safalta zaroor milegi</i>)\n"
    "3️⃣ Bot 2-5 second me <b>voice note</b> bana dega — download karke video me lagao ✅\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⚡ <b>Speed badalni ho?</b> Voice Lab ke upar 🐢 Normal ⚡ Tez 🚀 Bahut Tez buttons hain\n"
    "🌍 <b>Dusri language?</b> Jo voice chuno, usi bhasha me text likho\n\n"
    "⚠️ <b>Note:</b> Ye asli neural voices hain, par kisi celebrity ki official recording nahi — "
    "style/mood wali awaazein hain."
)


def voice_home_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎭 Actor / Character Voices (24)", callback_data="voice_actors")],
        [InlineKeyboardButton("🧪 Voice Lab (30 voices + speed)", callback_data="vlab_list")],
        [InlineKeyboardButton("📘 Kaise Use Karein?", callback_data="voice_guide")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home")],
    ])


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
    if is_admin(update.effective_user.id):
        st = payment_stats()
        await update.message.reply_text(
            f"👑 <b>Aap is bot ke OWNER/ADMIN ho</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Aapke liye <b>sab kuch unlimited</b> hai — na daily limit, na VIP paisa.\n"
            "Aapko premium lene ki koi zaroorat nahi 😄\n\n"
            f"💳 <b>Pending payments (verify karne hain):</b> {st['pending']}\n"
            f"💰 <b>Total revenue:</b> ₹{st['revenue']}\n\n"
            "👉 Payment verify karne ke liye <b>/payments</b> bhejo ya <b>/admin</b> kholein.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💳 Pending Payments ({st['pending']})", callback_data="admpay_list")],
                [InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_home")],
            ]),
            parse_mode=HTML,
        )
        return

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
    if not is_admin(update.effective_user.id):
        return
    await admin_panel_send(update.message, context, update.effective_user.id)


async def admin_panel_send(message, context, uid: int):
    """Naya advanced admin panel (buttons ke saath)."""
    st = stats()
    ps = payment_stats()
    pend = pending_payments_count()
    text = (
        f"🛠️ <b>{to_bold('ADMIN CONTROL DASHBOARD')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Total Users:</b> {st['total_users']}   |   🟢 <b>Aaj Active:</b> {st['active_today']}\n"
        f"⚡ <b>Aaj ke Uses:</b> {st['uses_today']}   |   💎 <b>Active VIP:</b> {st['vip_users']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>Pending Payments:</b> {pend}  {'🔴 (verify karo!)' if pend else '✅'}\n"
        f"✅ <b>Approved Total:</b> {ps['approved']}   |   ❌ <b>Rejected:</b> {ps['rejected']}\n"
        f"💰 <b>Total Revenue:</b> ₹{ps['revenue']:,}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 Neeche se kuch bhi karo:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 Pending Payments ({pend})", callback_data="admpay_list"),
         InlineKeyboardButton("🧾 Payment History", callback_data="admhist")],
        [InlineKeyboardButton("👥 Recent Users", callback_data="admusers"),
         InlineKeyboardButton("🔍 User Search / VIP Dena", callback_data="admsearch")],
        [InlineKeyboardButton("🚫 Ban / Unban", callback_data="admbanmenu"),
         InlineKeyboardButton("📢 Broadcast", callback_data="admbcmenu")],
        [InlineKeyboardButton("📊 Command List", callback_data="admcmds")],
    ])
    await message.reply_text(text, reply_markup=kb, parse_mode=HTML)


async def cmd_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/payments — sirf admin ke liye: pending payments ki list."""
    if not is_admin(update.effective_user.id):
        return
    pend = pending_payments(10)
    if not pend:
        await update.message.reply_text("✅ <b>Koi pending payment nahi hai!</b> Sab verify ho chuke hain.", parse_mode=HTML)
        return
    await update.message.reply_text(
        f"💳 <b>{to_bold('PENDING PAYMENTS')}</b> ({len(pend)})\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Neeche kisi bhi payment par tap karke <b>poora proof + approve/reject</b> buttons dekho 👇",
        reply_markup=admin_pending_kb(pend), parse_mode=HTML)


def admin_pending_kb(pend: list):
    rows = []
    for p in pend:
        amt = p.get("amount", 0)
        rows.append([InlineKeyboardButton(
            f"#{p['id']} · ₹{amt} · {str(p.get('plan_key') or p.get('plan_name'))[:14]} · user {p['user_id']}",
            callback_data=f"admpay_view:{p['id']}")])
    rows.append([InlineKeyboardButton("🔄 Refresh", callback_data="admpay_list")])
    rows.append([InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def admin_payment_kb(pid: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve 30 din", callback_data=f"apay:{pid}:30"),
         InlineKeyboardButton("✅ Approve 60 din", callback_data=f"apay:{pid}:60")],
        [InlineKeyboardButton("✅ Approve 90 din", callback_data=f"apay:{pid}:90"),
         InlineKeyboardButton("✅ Approve 120 din", callback_data=f"apay:{pid}:120")],
        [InlineKeyboardButton("👑 Approve LIFETIME", callback_data=f"apay:{pid}:9999"),
         InlineKeyboardButton("❌ Reject", callback_data=f"rpay:{pid}")],
        [InlineKeyboardButton("📩 User se dobara maango", callback_data=f"askpay:{pid}")],
    ])


async def cmd_mypay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User apni payments ka status dekh sakta hai."""
    uid = update.effective_user.id
    rows = user_payments(uid, 5)
    if not rows:
        await update.message.reply_text("📭 Abhi tak koi payment nahi bheji. VIP lene ke liye <b>/premium</b> dabao.", parse_mode=HTML)
        return
    icons = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    lines = []
    for r in rows:
        lines.append(f"{icons.get(r.get('status'), '❔')} <b>#{r['id']}</b> · {r.get('plan_name')} · ₹{r.get('amount')} · "
                     f"UTR <code>{r.get('utr_ref')}</code> · <b>{str(r.get('status')).upper()}</b>")
    await update.message.reply_text(
        "🧾 <b>Meri Payments</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines) +
        "\n━━━━━━━━━━━━━━━━━━━━━━\n⏳ admin verify kar raha hai · ✅ VIP mil gaya · ❌ reject",
        parse_mode=HTML)


async def cmd_revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /revoke [user_id] — VIP hata do."""
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: <code>/revoke [user_id]</code>", parse_mode=HTML)
        return
    target = int(context.args[0])
    revoke_premium(target)
    await update.message.reply_text(f"🚫 User <code>{target}</code> ki VIP hata di gayi.", parse_mode=HTML)


async def cmd_grant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
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
    if not is_admin(update.effective_user.id):
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
    if not is_admin(update.effective_user.id):
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
    if not is_admin(update.effective_user.id):
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
        pending_n = len(pending_payments(20))
        if pending_n >= 3:
            mine = [p for p in pending_payments(20) if p.get("user_id") == uid]
            if len(mine) >= 3:
                await q.answer("Aapke 3 payment already pending hain — admin verify karega.", show_alert=True)
                return
        context.user_data["mode"] = f"pay_utr_{plan_key}"
        context.user_data["pay_utr_tries"] = 0
        context.user_data["pay_shot_tries"] = 0
        caption = (
            f"💎 <b>{to_bold(plan_name)}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Amount:</b> ₹{amt}\n"
            f"🏦 <b>UPI ID:</b> <code>{UPI_ID}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📲 <b>Step 1:</b> Is QR ko scan karke ₹" f"{amt} pay karein\n"
            "   (PhonePe / GPay / Paytm / BHIM)\n\n"
            "📝 <b>Step 2:</b> Payment hone ke baad <b>UTR / Transaction ID</b> yahan bhejein\n"
            "📸 <b>Step 3:</b> Payment ka <b>screenshot</b> bhejein\n\n"
            "⚠️ <b>Strict check:</b> UTR sahi hona chahiye aur screenshot asli payment ka hona chahiye "
            "(photo/hasne wali image nahi). Galat proof par VIP nahi milega."
        )
        kb_pay = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ UTR kahan milega?", callback_data="pay_utr_help")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/Supermannn_x")],
        ])
        await q.message.reply_photo(photo=qr_buf, caption=caption, reply_markup=kb_pay, parse_mode=HTML)
        return

    if data == "pay_utr_help":
        await q.message.reply_text(utr_help_text(), parse_mode=HTML)
        return

    if data == "open_vip_menu":
        await q.message.reply_text("💎 Plan select karein:", reply_markup=get_premium_plans_kb(), parse_mode=HTML)
        return

    if data == "open_refer_menu":
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
        await q.message.reply_text(f"🎁 <b>Aapka Invite Link:</b>\n<code>{ref_link}</code>", parse_mode=HTML)
        return

    # ================= ADMIN: PAYMENT APPROVE / REJECT (v33 — FIXED + STRICT) =================
    async def _edit_admin_msg(text, kb=None):
        """Admin message chahe photo-caption ho ya text — dono me kaam kare (purana bug yahi tha)."""
        for fn, kw in ((q.message.edit_caption, {"caption": text, "parse_mode": HTML, "reply_markup": kb}),
                       (q.message.edit_text, {"text": text, "parse_mode": HTML, "reply_markup": kb})):
            try:
                await fn(**kw)
                return True
            except Exception:
                continue
        try:
            await q.message.reply_text(text, reply_markup=kb, parse_mode=HTML)
            return True
        except Exception:
            return False

    if data.startswith("apay:"):
        if not is_admin(uid):
            await q.answer("Ye sirf admin ke liye hai.", show_alert=True)
            return
        _, pid_s, days_s = data.split(":")
        pid, days = int(pid_s), int(days_s)
        pay = get_payment(pid)
        if not pay:
            await q.answer("Payment record nahi mila.", show_alert=True)
            return
        if pay.get("status") == "approved":
            await q.answer("✅ Ye payment pehle hi approve ho chuka hai!", show_alert=True)
            return
        target_uid = int(pay["user_id"])
        grant_premium(target_uid, days)
        set_payment_status(pid, "approved", reviewer=uid, note=f"{days} din")
        dur = "👑 LIFETIME VIP" if days >= 9999 else f"{days} din VIP"
        ok_edit = await _edit_admin_msg(
            f"✅ <b>APPROVED — Payment #{pid}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> <code>{target_uid}</code>\n"
            f"💰 <b>Amount:</b> ₹{pay.get('amount')}\n"
            f"👑 <b>Diya:</b> {dur}\n"
            f"🕒 <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ User ko message chala gaya.",
            kb=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💳 Aur Pending ({pending_payments_count()})", callback_data="admpay_list"),
                 InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]))
        await q.answer("✅ VIP activate ho gaya!")
        try:
            user_obj = get_user(target_uid)
            new_until = "👑 LIFETIME" if days >= 9999 else premium_expiry(user_obj)
            await context.bot.send_message(
                target_uid,
                "🎉 <b>MUBARAK HO! VIP ACTIVATE HO GAYA</b> 💎\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧾 <b>Payment ID:</b> #{pid}\n"
                f"👑 <b>Plan:</b> {dur}\n"
                f"📅 <b>Valid till:</b> {new_until}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Ab aapko <b>koi daily limit nahi</b> — saare tools unlimited chalayein! 🚀\n"
                "<i>Bot enjoy karo aur dosto ko bhi batao 😄</i>",
                parse_mode=HTML)
        except Exception:
            pass
        if not ok_edit:
            await q.message.reply_text(f"✅ Payment #{pid} approve ho gaya ({dur}).")
        return

    if data.startswith("rpay:"):
        if not is_admin(uid):
            await q.answer("Sirf admin.", show_alert=True)
            return
        pid = int(data.split(":")[1])
        pay = get_payment(pid)
        if not pay:
            await q.answer("Record nahi mila.", show_alert=True)
            return
        if pay.get("status") == "approved":
            await q.answer("Ye payment approve ho chuka hai — reject nahi ho sakta.", show_alert=True)
            return
        set_payment_status(pid, "rejected", reviewer=uid, note="admin reject")
        await _edit_admin_msg(
            f"❌ <b>REJECTED — Payment #{pid}</b>\n\n"
            f"👤 User: <code>{pay.get('user_id')}</code>\n💰 ₹{pay.get('amount')}\n🧾 UTR: <code>{pay.get('utr_ref')}</code>\n\n"
            "<i>User ko wajah ke saath message bhej diya gaya.</i>",
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]))
        await q.answer("Rejected")
        try:
            await context.bot.send_message(
                int(pay["user_id"]),
                f"❌ <b>Payment #{pid} verify nahi ho paya</b>\n\n"
                "Wajah ho sakti hai:\n"
                "• UTR galat ya pehle use ho chuka\n"
                "• Screenshot saaf nahi tha / payment ka nahi tha\n"
                "• Amount match nahi kar raha\n\n"
                "🔁 Sahi proof ke saath dobara bhej sakte ho: <b>/premium</b>\n"
                "💬 Ya Support se baat karo: @Supermannn_x",
                parse_mode=HTML)
        except Exception:
            pass
        return

    if data.startswith("askpay:"):
        if not is_admin(uid):
            return
        pid = int(data.split(":")[1])
        pay = get_payment(pid)
        if not pay:
            await q.answer("Record nahi mila.", show_alert=True)
            return
        await q.answer("User ko message bhej diya")
        try:
            await context.bot.send_message(
                int(pay["user_id"]),
                f"📩 <b>Admin ko thodi aur jaankari chahiye — Payment #{pid}</b>\n\n"
                "Kripya ye bhejein:\n"
                "1️⃣ Payment ka <b>saaf screenshot</b> (jisme amount + UTR dikhe)\n"
                "2️⃣ UTR / Transaction ID <b>text me</b>\n"
                "3️⃣ Transaction ka <b>time aur amount</b>\n\n"
                "👉 Yahan seedha bhej do, admin dekh lega.",
                parse_mode=HTML)
        except Exception:
            await q.message.reply_text("⚠️ User ko message nahi bhej paye (shayad bot block kar diya).")
        return

    # ---------- Admin panel ke buttons ----------
    if data == "admin_home":
        if not is_admin(uid):
            await q.answer("Sirf admin.", show_alert=True)
            return
        await admin_panel_send(q.message, context, uid)
        return

    if data == "admpay_list":
        if not is_admin(uid):
            return
        pend = pending_payments(10)
        if not pend:
            await q.message.reply_text("✅ <b>Koi pending payment nahi hai!</b>", parse_mode=HTML)
            return
        await q.message.reply_text(
            f"💳 <b>Pending Payments ({len(pend)})</b>\nTap karke poora proof + approve/reject dekho 👇",
            reply_markup=admin_pending_kb(pend), parse_mode=HTML)
        return

    if data.startswith("admpay_view:"):
        if not is_admin(uid):
            return
        pid = int(data.split(":")[1])
        pay = get_payment(pid)
        if not pay:
            await q.answer("Record nahi mila.", show_alert=True)
            return
        card = admin_payment_card(pay, user_row=get_user_row(int(pay["user_id"])),
                                  history=user_payment_history(int(pay["user_id"])))
        await q.message.reply_text(card, reply_markup=admin_payment_kb(pid), parse_mode=HTML)
        await q.answer("Card bhej diya ✅")
        return

    if data == "mypay_list":
        rows = user_payments(uid, 5)
        if not rows:
            await q.message.reply_text("📭 Abhi tak koi payment nahi bheji. VIP lene ke liye <b>/premium</b> dabao.", parse_mode=HTML)
            return
        icons = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
        lines = [f"{icons.get(r.get('status'), '❔')} <b>#{r['id']}</b> · {r.get('plan_name')} · ₹{r.get('amount')} · "
                 f"UTR <code>{r.get('utr_ref')}</code> · {str(r.get('status')).upper()}" for r in rows]
        await q.message.reply_text(
            "🧾 <b>Meri Payments</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines) +
            "\n━━━━━━━━━━━━━━━━━━━━━━\n⏳ = admin verify kar raha hai · ✅ = VIP mil gaya · ❌ = reject",
            parse_mode=HTML)
        return

    if data == "admhist":
        if not is_admin(uid):
            return
        rows = recent_payments(10)
        if not rows:
            await q.message.reply_text("Koi payment record nahi hai.", parse_mode=HTML)
            return
        icons = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
        lines = [f"{icons.get(r.get('status'), '❔')} #{r['id']} · user <code>{r['user_id']}</code> · "
                 f"₹{r.get('amount')} · {str(r.get('plan_name'))[:18]} · {str(r.get('created_at'))[:16]}" for r in rows]
        ps = payment_stats()
        await q.message.reply_text(
            "🧾 <b>Last 10 Payments</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines) +
            f"\n━━━━━━━━━━━━━━━━━━━━━━\n💰 Revenue: ₹{ps['revenue']:,} · ✅ {ps['approved']} · ❌ {ps['rejected']} · ⏳ {ps['pending']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]),
            parse_mode=HTML)
        return

    if data == "admusers":
        if not is_admin(uid):
            return
        users = recent_users(10)
        lines = [f"• <code>{u[0]}</code> — {hesc(str(u[1] or '')[:20])}" for u in users]
        await q.message.reply_text("👥 <b>Recent Users</b>\n\n" + "\n".join(lines), parse_mode=HTML)
        return

    if data == "admcmds":
        if not is_admin(uid):
            return
        await q.message.reply_text(
            "📊 <b>Admin Commands</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
            "• <code>/payments</code> — pending payment verify\n"
            "• <code>/grant [user_id] [din]</code> — VIP do (9999 = lifetime)\n"
            "• <code>/revoke [user_id]</code> — VIP hatao\n"
            "• <code>/broadcast [message]</code> — sabko message\n"
            "• <code>/ban [user_id]</code> / <code>/unban [user_id]</code>\n"
            "• <code>/admin</code> — ye panel",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]),
            parse_mode=HTML)
        return

    if data == "admbcmenu":
        if not is_admin(uid):
            return
        context.user_data["mode"] = "adm_broadcast"
        await q.message.reply_text("📢 <b>Broadcast</b>\n\nJo message sab users ko bhejna hai, wo likh kar bhejo.\n<i>(/cancel se ruk sakte ho)</i>", parse_mode=HTML)
        return

    if data == "admbanmenu":
        if not is_admin(uid):
            return
        context.user_data["mode"] = "adm_ban"
        await q.message.reply_text(
            "🚫 <b>Ban / Unban</b>\n\nAise bhejo:\n"
            "<code>ban 123456789</code> → ban karo\n<code>unban 123456789</code> → unban karo",
            parse_mode=HTML)
        return

    if data == "admsearch":
        if not is_admin(uid):
            return
        context.user_data["mode"] = "adm_search"
        await q.message.reply_text(
            "🔍 <b>User Search</b>\n\nUser ki <b>ID</b> ya <b>@username</b> bhejo — poori detail + VIP dene/hataane ke buttons mil jayenge.",
            parse_mode=HTML)
        return

    if data.startswith("ugrant:"):
        if not is_admin(uid):
            return
        _, t_uid, days = data.split(":")
        t_uid, days = int(t_uid), int(days)
        grant_premium(t_uid, days)
        dur = "👑 LIFETIME VIP" if days >= 9999 else f"{days} din VIP"
        await q.answer(f"✅ {dur} diya gaya")
        await q.message.reply_text(f"✅ <b>Done!</b> User <code>{t_uid}</code> ko {dur} diya gaya.", parse_mode=HTML)
        try:
            await context.bot.send_message(t_uid, f"🎉 <b>Admin ne aapko {dur} de diya!</b> 💎\n\nAb saare tools unlimited chalayein 🚀", parse_mode=HTML)
        except Exception:
            pass
        return

    if data.startswith("urevoke:"):
        if not is_admin(uid):
            return
        t_uid = int(data.split(":")[1])
        revoke_premium(t_uid)
        await q.answer("VIP hata diya")
        await q.message.reply_text(f"🚫 User <code>{t_uid}</code> ki VIP hata di gayi.", parse_mode=HTML)
        return

    if data.startswith("uban:"):
        if not is_admin(uid):
            return
        _, t_uid, val = data.split(":")
        set_ban(int(t_uid), int(val))
        await q.answer("Ho gaya")
        await q.message.reply_text(("🚫 Ban kar diya" if val == "1" else "🟢 Unban kar diya") + f" — <code>{t_uid}</code>", parse_mode=HTML)
        return

    # ---- PURANE messages ke buttons (backward compatible — pehle jo bheje the wo bhi chalenge) ----
    if data.startswith("adm_appr_") and is_admin(uid):
        parts = data.split("_")
        target_uid = int(parts[2]); days = int(parts[3])
        grant_premium(target_uid, days)
        dur = "👑 LIFETIME VIP" if days >= 9999 else f"{days} din VIP"
        ok_edit = await _edit_admin_msg(f"✅ <b>Approved!</b> User <code>{target_uid}</code> ko {dur} diya gaya.")
        await q.answer("✅ Done")
        try:
            await context.bot.send_message(target_uid, f"🎉 <b>Badhai ho!</b> Aapka payment approve ho gaya — {dur} activate! 💎", parse_mode=HTML)
        except Exception:
            pass
        if not ok_edit:
            await q.message.reply_text(f"✅ User {target_uid} ko {dur} diya gaya.")
        return

    if data.startswith("adm_rej_") and is_admin(uid):
        target_uid = int(data.split("_")[2])
        ok_edit = await _edit_admin_msg(f"❌ <b>Rejected!</b> User <code>{target_uid}</code> ka payment reject kar diya.")
        await q.answer("Rejected")
        try:
            await context.bot.send_message(target_uid, "❌ Aapka payment verify nahi ho paya. Sahi screenshot/UTR ke saath dobara bhejein (/premium).")
        except Exception:
            pass
        if not ok_edit:
            await q.message.reply_text(f"❌ User {target_uid} ka payment reject kar diya.")
        return

    # ============ AUTO FORWARD — WIZARD / GUIDE / TEST / STATUS ============
    if data == "cloner_guide":
        await q.message.reply_text(
            CLONER_GUIDE_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Ab Setup Karein (3 Steps)", callback_data="cloner_setup")],
                [InlineKeyboardButton("📊 Meri Setting Dekho", callback_data="cloner_status")],
            ]),
            parse_mode=HTML,
        )
        return

    if data == "cloner_setup":
        cfg = get_cloner_config(uid)
        src_ok = "✅" if cfg.get("source_chat_id") else "1️⃣"
        tgt_ok = "✅" if cfg.get("target_chat_id") else "2️⃣"
        await q.message.reply_text(
            "🚀 <b>AUTO FORWARD SETUP — sirf 3 step</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{src_ok} <b>Step 1:</b> SOURCE channel set karo (jahan se posts aayengi)\n"
            f"{tgt_ok} <b>Step 2:</b> TARGET channel set karo (jahan posts jayengi)\n"
            "3️⃣ <b>Step 3:</b> FULL AUTO ko ON karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 Source abhi: <code>{cfg.get('source_chat_id') or '— set nahi'}</code>\n"
            f"📑 Target abhi: <code>{cfg.get('target_chat_id') or '— set nahi'}</code>\n\n"
            "⚠️ <b>Yaad rakho:</b> Bot ko dono channel me <b>Admin</b> banao.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{src_ok} Source Set Karein", callback_data="cloner_set_source")],
                [InlineKeyboardButton(f"{tgt_ok} Target Set Karein", callback_data="cloner_set_target")],
                [InlineKeyboardButton("🤖 FULL AUTO ON/OFF", callback_data="cloner_toggle_auto")],
                [InlineKeyboardButton("🧪 Test Post Bhejo", callback_data="cloner_test")],
                [InlineKeyboardButton("📘 Guide Padho", callback_data="cloner_guide")],
            ]),
            parse_mode=HTML,
        )
        return

    if data == "cloner_status":
        cfg = get_cloner_config(uid)
        await q.message.reply_text(
            cloner_summary_text(cfg),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Setup Theek Karo", callback_data="cloner_setup")],
                [InlineKeyboardButton("📘 Guide", callback_data="cloner_guide")],
            ]),
            parse_mode=HTML,
        )
        return

    if data == "cloner_test":
        cfg = get_cloner_config(uid)
        tgt = cfg.get("target_chat_id")
        if not tgt:
            await q.answer("Pehle Target set karein!", show_alert=True)
            return
        src = cfg.get("source_chat_id")
        lines = []
        try:
            if src:
                ch = await context.bot.get_chat(src)
                me = await context.bot.get_chat_member(src, context.bot.id)
                lines.append(f"📡 <b>Source:</b> {ch.title or src} — bot admin: {'✅' if me.status in ('administrator','creator') else '❌ ADMIN nahi hai'}")
            ch2 = await context.bot.get_chat(tgt)
            me2 = await context.bot.get_chat_member(tgt, context.bot.id)
            admin_ok = me2.status in ("administrator", "creator")
            lines.append(f"📑 <b>Target:</b> {ch2.title or tgt} — bot admin: {'✅' if admin_ok else '❌ ADMIN nahi hai'}")
            if admin_ok:
                test_msg = await context.bot.send_message(tgt, "🧪 <b>TEST POST</b>\n\nYe message ToolVault bot ne bheja hai.\nAgar ye aapko dikh raha hai → <b>target channel bilkul theek hai ✅</b>\n\n<i>Ye test message 5 second me delete ho jayega.</i>", parse_mode=HTML)
                lines.append("\n✅ <b>Target me test post bhej diya</b> — apne channel me check karo!")
                import asyncio as _aio
                async def _del_later():
                    await _aio.sleep(5)
                    try:
                        await context.bot.delete_message(tgt, test_msg.message_id)
                    except Exception:
                        pass
                _aio.create_task(_del_later())
            else:
                lines.append("\n⚠️ Target me bot ko <b>Admin</b> banao (Post Messages permission) — phir dobara test karo.")
        except Exception as e:
            lines.append(f"\n❌ Problem: <code>{hesc(str(e))}</code>\n💡 Check karo: source/target ka username sahi hai? bot dono me admin hai?")
        await q.message.reply_text("🧪 <b>TEST RESULT</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines), parse_mode=HTML)
        return

    # ============ PRIVATE CHANNEL SETUP (aasan tareeka) ============
    if data == "cloner_private":
        await q.message.reply_text(
            "🔒 <b>PRIVATE CHANNEL SE POST UTHANI HAI?</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Bilkul aasan hai — <b>na koi login, na password</b>. Sirf 3 kaam:\n\n"
            "1️⃣ Apne <b>private channel</b> me jaao → <b>Administrators</b> → <b>Add Admin</b> → is bot "
            "(<code>@utility_duniya_bot</code>) ko add karo ✅\n"
            "   <i>(Ye hi 'login' hai — bot ko andar aane dena. Bas ek baar karna hai.)</i>\n\n"
            "2️⃣ Us channel ki <b>koi bhi ek post</b> (video/PDF/photo) yahan is bot ko <b>FORWARD</b> kar do\n"
            "   → bot khud us channel ki ID pakad lega\n\n"
            "3️⃣ Bot aapko button dega: <b>📡 Ye channel Source banao</b> — dabao, source set ho gaya\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Iske baad <b>Target</b> set karke <b>FULL AUTO</b> ON kar do. Done! 🎉\n\n"
            "⚠️ Copy restriction wale channel ki posts Telegram forward nahi karne deta — "
            "us case me bot us channel me <b>admin</b> hone ke kaaran direct utha lega (auto mode me).",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Setup par wapas", callback_data="cloner_setup")],
            ]),
            parse_mode=HTML,
        )
        return

    if data.startswith("fc_src:"):
        cid = data.split(":", 1)[1]
        try:
            chat = await context.bot.get_chat(int(cid))
            title = chat.title or str(cid)
        except Exception as e:
            await q.answer("Bot ko us channel me add karo (admin), phir try karo", show_alert=True)
            return
        save_cloner_config(uid, source_chat_id=cid)
        context.user_data["mode"] = "cloner_target"
        await q.message.reply_text(
            f"✅ <b>Source set:</b> {hesc(str(title))}\n🆔 <code>{cid}</code>\n\n"
            "👉 Ab <b>TARGET channel</b> bhejo (jahan posts bhejni hain):\n"
            "(jaise <code>@MyChannel</code> ya <code>-1001234567890</code>)",
            parse_mode=HTML)
        return

    if data.startswith("fc_tgt:"):
        cid = data.split(":", 1)[1]
        save_cloner_config(uid, target=cid)
        cfg_now = get_cloner_config(uid)
        ready = bool(cfg_now.get("source_chat_id"))
        await q.message.reply_text(
            f"✅ <b>Target set:</b> <code>{cid}</code>\n\n"
            + ("🎉 Dono set ho gaye — ab <b>FULL AUTO ON</b> dabao!" if ready else "👉 Ab <b>SOURCE</b> channel set karo.")
            ,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 FULL AUTO ON karo", callback_data="cloner_toggle_auto")],
                [InlineKeyboardButton("⚙️ Saari Settings", callback_data="cloner_status")],
            ]),
            parse_mode=HTML)
        return

    # ============ NAYE TOOL CALLBACKS ============
    if data == "qr_upi":
        context.user_data["mode"] = "qr_upi"
        await q.message.reply_text(PROMPTS["qr_upi"], parse_mode=HTML)
        return
    if data == "qr_wifi":
        context.user_data["mode"] = "qr_wifi"
        await q.message.reply_text(PROMPTS["qr_wifi"], parse_mode=HTML)
        return
    if data == "qr_vcard":
        context.user_data["mode"] = "qr_vcard"
        await q.message.reply_text(PROMPTS["qr_vcard"], parse_mode=HTML)
        return
    if data == "pwd_pin":
        context.user_data["mode"] = "pwd_pin"
        await q.message.reply_text("🔢 PIN bana raha hoon...", parse_mode=HTML)
        # turant hi generate kar do
        context.user_data["mode"] = "pwd_pin"
        pins = [gen_pin(6) for _ in range(5)]
        await q.message.reply_text(
            f"🔢 <b>{to_bold('RANDOM PINS (6 digit)')}</b>\n\n" +
            "\n".join(f"{i}️⃣ <code>{p}</code>" for i, p in enumerate(pins, 1)) +
            "\n\n⚠️ <i>Ye UPI/ATM PIN jaisa kuch nahi hai — kisi ko share na karein.</i>",
            parse_mode=HTML)
        context.user_data.pop("mode", None)
        return
    if data == "pwd_phrase":
        phrases = [gen_passphrase(4) for _ in range(4)]
        await q.message.reply_text(
            f"🧠 <b>{to_bold('EASY WORDS STRONG PASSWORDS')}</b>\n"
            "<i>(yaad rakhna aasan, todna mushkil)</i>\n\n" +
            "\n".join(f"{i}️⃣ <code>{p}</code>  ({password_strength(p)[1]})" for i, p in enumerate(phrases, 1)) +
            "\n\n💡 <i>Tip: apna symbol/word mila do (jaise <code>@</code>) — aur strong ho jayega.</i>",
            parse_mode=HTML)
        return
    if data == "qr_text":
        context.user_data["mode"] = "qr"
        await q.message.reply_text(PROMPTS["qr"], parse_mode=HTML)
        return
    if data == "shot_hd":
        context.user_data["mode"] = "shot"
        await q.message.reply_text(PROMPTS["shot"], parse_mode=HTML)
        return
    if data == "shot_full":
        context.user_data["mode"] = "shot_full"
        await q.message.reply_text(PROMPTS["shot_full"], parse_mode=HTML)
        return

    # Document compress: size + grayscale + GO
    if data in ("doc_kb_100", "doc_kb_200", "doc_kb_300", "doc_kb_500"):
        context.user_data["doc_kb"] = int(data.split("_")[-1])
        await q.answer(f"Size set: {context.user_data['doc_kb']} KB ✅")
        return
    if data == "doc_gray":
        context.user_data["doc_gray"] = not context.user_data.get("doc_gray", False)
        state = "ON ✅" if context.user_data["doc_gray"] else "OFF"
        await q.answer(f"Black & White: {state}", show_alert=True)
        return
    if data == "doc_go":
        pages = context.user_data.get("doc_pages", [])
        if not pages:
            await q.answer("Pehle photo bhejein!", show_alert=True)
            return
        kb_target = context.user_data.get("doc_kb", 300)
        gray = context.user_data.get("doc_gray", False)
        await q.answer("PDF ban raha hai...")
        try:
            pdf_buf = compress_document_pdf(pages, kb_target, grayscale=gray)
            pdf_buf.name = f"Document_{kb_target}KB.pdf"
            size_kb = len(pdf_buf.getvalue()) / 1024
            await q.message.reply_document(
                document=pdf_buf,
                caption=(f"📄 <b>{to_bold('COMPRESSED PDF READY')}</b>\n"
                         f"• {len(pages)} page • {size_kb:.0f} KB • {kb_target} KB limit me ✅\n"
                         f"• Mode: {'⚫ Black & White' if gray else '🌈 Colour'}\n\n"
                         "Govt portal par upload kar sakte ho."),
                parse_mode=HTML)
        except Exception as e:
            await q.message.reply_text(f"❌ PDF nahi ban paya: <code>{hesc(str(e))}</code>", parse_mode=HTML)
        context.user_data.pop("doc_pages", None)
        context.user_data.pop("doc_kb", None)
        context.user_data.pop("doc_gray", None)
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    # ============ PUBLIC RECORDS (optional feature) ============
    if data.startswith("numrec:"):
        number = data.split(":", 1)[1]
        if not NUM_LEAK_ENABLED():
            await q.answer("Ye feature abhi band hai.", show_alert=True)
            return
        await q.answer("Dhoondh raha hoon... (5-15 second)")
        st = await q.message.reply_text("🧾 <b>Public records dhoondh raha hoon...</b>\n<i>Isme 5-20 second lag sakte hain, wait karein.</i>", parse_mode=HTML)
        try:
            res = await asyncio.to_thread(lookup_public_records, number)
        except Exception as e:
            res = {"ok": False, "error": str(e)[:120]}

        if not res.get("ok"):
            await st.edit_text(
                f"❌ <b>Public record nahi mila</b>\n\n{res.get('error')}\n\n"
                "💡 <i>Ho sakta hai is number ka record database me na ho. Koi dusra number try karo.</i>",
                parse_mode=HTML)
            add_use(uid)
            return

        lines = [f"🧾 <b>{to_bold('PUBLIC RECORDS')}</b> — <code>+{hesc(res['number'])}</code>",
                 f"<i>Mile: {res['count']} record (database me total {res.get('record_count', res['count'])} hain)</i>",
                 "━━━━━━━━━━━━━━━━━━━━━━"]
        for i, rec in enumerate(res["records"], 1):
            lines.append(f"<b>{i}. {hesc(rec['name'])}</b>")
            if rec.get("father"):
                lines.append(f"   👨 <b>Pita ka naam:</b> {hesc(rec['father'])}")
            if rec.get("address"):
                lines.append(f"   🏠 <b>Pata:</b> {hesc(rec['address'])}")
            if rec.get("phone"):
                lines.append(f"   📞 <b>Linked number:</b> <code>{hesc(rec['phone'])}</code>")
            if rec.get("doc"):
                lines.append(f"   🪪 <b>Doc/Aadhaar:</b> <code>{hesc(rec['doc'])}</code>")
            if rec.get("region"):
                lines.append(f"   🗺️ <b>Region/Operator:</b> {hesc(rec['region'])}")
            lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("ℹ️ <b>Kabhi-kabhi record dusre bande ka bhi ho sakta hai</b> — number recycle/port hone par aisa hota hai. "
                     "Naam ya pata match karke hi bharosa karo.")
        lines.append("")
        lines.append(PUBLIC_RECORD_WARNING)

        kb_rec = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚨 Fraud/Spam? 1930 par complaint", url="https://cybercrime.gov.in/")],
            [InlineKeyboardButton("🚫 Chakshu me report (TRAI)", url="https://sancharsaathi.gov.in/")],
        ])
        await st.edit_text("\n".join(lines), reply_markup=kb_rec, parse_mode=HTML)
        add_use(uid)
        return

    # Copy buttons (pincode / area results)
    if data.startswith("copy_"):
        await q.answer(f"📋 {data[5:]} — dabakar copy karo", show_alert=True)
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
        context.user_data["voice_kind"] = "actor"
        p_info = ACTOR_VOICE_PRESETS.get(preset_key, {})
        context.user_data["mode"] = "voice_text"
        await q.message.reply_text(
            f"🎙️ <b>Voice chuni:</b> {p_info.get('name', 'Default')}\n"
            f"🌍 Language: <b>{p_info.get('lang', 'Hindi')}</b>\n"
            f"🔊 Asli engine voice: <code>{p_info.get('voice', '')}</code>\n\n"
            "Ab woh <b>DIALOGUE / TEXT</b> bhejo jiska audio banana hai\n"
            "(Hindi me likho to Hindi voice, English me likho to English voice — hum khud adjust kar lenge 😊)",
            parse_mode=HTML)
        return

    # ---------- VOICE STUDIO HOME ----------
    if data == "voice_home":
        await q.message.reply_text(VOICE_HOME_TEXT, reply_markup=voice_home_kb(), parse_mode=HTML)
        return

    if data == "voice_guide":
        await q.message.reply_text(VOICE_GUIDE_TEXT, reply_markup=voice_home_kb(), parse_mode=HTML)
        return

    if data == "voice_actors":
        buttons = []
        items = list(ACTOR_VOICE_PRESETS.items())
        for i in range(0, len(items), 2):
            row = [InlineKeyboardButton(items[i][1]["name"], callback_data=f"actor_voice_{items[i][0]}")]
            if i + 1 < len(items):
                row.append(InlineKeyboardButton(items[i + 1][1]["name"], callback_data=f"actor_voice_{items[i + 1][0]}"))
            buttons.append(row)
        buttons.append([InlineKeyboardButton("🔙 Voice Studio", callback_data="voice_home")])
        await q.message.reply_text(
            f"🎭 <b>{to_bold('ACTOR / CHARACTER VOICES')}</b> — {len(items)} alag-aslag asli voices\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Har voice ek alag asli neural voice hai (koi copy nahi). Sunne ke liye chuno 👇</i>",
            reply_markup=InlineKeyboardMarkup(buttons), parse_mode=HTML)
        return

    if data == "vlab_list":
        speeds = context.user_data.get("vlab_speed", "normal")
        rows = [[InlineKeyboardButton(
            ("✅ " if k == speeds else "") + label, callback_data=f"vlab_spd_{k}") for k, (label, rate) in VOICE_SPEEDS.items()]]
        items = list(VOICE_LAB_MAP.items())
        for i in range(0, len(items), 2):
            row = [InlineKeyboardButton(items[i][1][0], callback_data=f"vlab_v_{items[i][0]}")]
            if i + 1 < len(items):
                row.append(InlineKeyboardButton(items[i + 1][1][0], callback_data=f"vlab_v_{items[i + 1][0]}"))
            rows.append(row)
        rows.append([InlineKeyboardButton("🔙 Voice Studio", callback_data="voice_home")])
        await q.message.reply_text(
            f"🧪 <b>{to_bold('VOICE LAB')}</b> — {len(items)} voices × {len(VOICE_SPEEDS)} speeds\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ Speed abhi: <b>{VOICE_SPEEDS[speeds][0]}</b> ({VOICE_SPEEDS[speeds][1]})\n\n"
            "Pehle <b>speed</b> chuno (upar), phir <b>voice</b> chuno — aur text bhejo.\n"
            "<i>Har voice alag language/personality ki hai.</i>",
            reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        return

    if data.startswith("vlab_spd_"):
        key = data.replace("vlab_spd_", "")
        context.user_data["vlab_speed"] = key
        await q.answer(f"Speed: {VOICE_SPEEDS.get(key, ('Normal', '+0%'))[0]} ✅", show_alert=True)
        return

    if data.startswith("vlab_v_"):
        vkey = data.replace("vlab_v_", "")
        label, short = VOICE_LAB_MAP.get(vkey, ("Hindi Male", "hi-IN-MadhurNeural"))
        context.user_data["vlab_voice"] = short
        context.user_data["vlab_voice_label"] = label
        context.user_data["mode"] = "voice_lab_text"
        spd = context.user_data.get("vlab_speed", "normal")
        await q.message.reply_text(
            f"🧪 <b>Voice Lab — voice chuni:</b> {label}\n"
            f"🔊 Engine: <code>{short}</code>\n"
            f"⚡ Speed: {VOICE_SPEEDS[spd][0]} ({VOICE_SPEEDS[spd][1]})\n\n"
            "Ab <b>text / dialogue</b> bhejo (us voice ki language me likho, jaise Tamil voice ke liye Tamil):",
            parse_mode=HTML)
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


async def submit_payment_proof(update, context, uid: int, plan_key: str, photo_obj):
    """
    Screenshot aane par: (1) strict image check, (2) DB me record, (3) admin ko full card + working buttons.
    """
    plan = VIP_PLANS.get(plan_key, VIP_PLANS["plan_30"])
    utr = context.user_data.get("pay_utr") or ""
    tries = context.user_data.get("pay_shot_tries", 0)
    user = update.effective_user

    st = await update.message.reply_text("🔍 Screenshot verify kar raha hoon...")
    try:
        tg_file = await photo_obj.get_file()
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        img_bytes = buf.getvalue()
    except Exception as e:
        await st.edit_text(f"❌ Screenshot download nahi ho paya. Dobara bhejo.\n<i>{hesc(str(e))[:90]}</i>", parse_mode=HTML)
        return

    analysis = await asyncio.to_thread(analyze_screenshot, img_bytes, plan["price"])

    # --- strict gate: photo/meme bhejne par reject (3 try tak) ---
    if not analysis["ok"] and analysis["verdict"] == "bad" and tries < MAX_BAD_TRIES:
        context.user_data["pay_shot_tries"] = tries + 1
        await st.edit_text(
            "❌ <b>Ye payment ka screenshot nahi lag raha!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{shot_verdict_line(analysis)}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📸 <b>Aise screenshot bhejo:</b>\n"
            "1️⃣ Phone me PhonePe / GPay / Paytm kholo\n"
            "2️⃣ <b>History / Passbook</b> me jao\n"
            "3️⃣ Us payment par tap karo (₹" + str(plan['price']) + " wala)\n"
            "4️⃣ <b>Screenshot</b> lo → yahan bhejo (jisme <b>amount, success aur UTR</b> saaf dikhe)\n\n"
            f"⚠️ Selfie / photo / meme bhejne par proof reject hota hai ({tries + 1}/{MAX_BAD_TRIES} try)\n"
            "<i>Aapka UTR save hai — bas sahi screenshot bhejo.</i>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❓ UTR kahan milega?", callback_data="pay_utr_help")]]),
            parse_mode=HTML,
        )
        return

    # --- duplicate checks (ek UTR / ek image sirf ek baar) ---
    utr_dup = utr_exists(utr)
    shot_dup = shot_exists(photo_obj.file_unique_id)
    if shot_dup:
        await st.edit_text(
            "🚫 <b>Ye screenshot pehle bhi use ho chuka hai!</b>\n\n"
            "Ek hi screenshot se dobara VIP nahi mil sakti.\n"
            "📸 Naya payment karke us naye payment ka <b>screenshot</b> bhejo.\n\n"
            "💬 Koi dikkat ho to Support: @Supermannn_x",
            parse_mode=HTML)
        return
    flags = {
        "username": user.username or "",
        "name": user.first_name or "",
        "shot": analysis,
        "utr_dup": utr_dup,
        "shot_dup": shot_dup,
        "forced": bool(not analysis["ok"] and tries >= MAX_BAD_TRIES),
    }

    pid = create_payment(uid, plan_key, plan["name"], plan["price"], plan["days"], utr,
                         photo_obj.file_id, photo_obj.file_unique_id, flags)
    if not pid:
        await st.edit_text("❌ Record save nahi ho paya. Thodi der baad dobara try karo ya Support se baat karo.")
        return

    card = admin_payment_card(
        {"id": pid, "user_id": uid, "plan_key": plan_key, "plan_name": plan["name"],
         "amount": plan["price"], "plan_days": plan["days"], "utr_ref": utr,
         "shot_file_id": photo_obj.file_id, "flags": json.dumps(flags),
         "created_at": datetime.now().strftime("%d-%m-%Y %H:%M")},
        user_row=get_user_row(uid), history=user_payment_history(uid))

    sent_any = False
    for admin_id in ADMIN_IDS:
        try:
            m = await context.bot.send_photo(chat_id=admin_id, photo=photo_obj.file_id, caption=card,
                                             reply_markup=admin_payment_kb(pid), parse_mode=HTML)
            set_payment_admin_msg(pid, admin_id, m.message_id)
            sent_any = True
        except Exception:
            try:
                m = await context.bot.send_message(chat_id=admin_id, text=card,
                                                  reply_markup=admin_payment_kb(pid), parse_mode=HTML)
                set_payment_admin_msg(pid, admin_id, m.message_id)
                sent_any = True
            except Exception:
                continue

    if not sent_any:
        await st.edit_text(f"⚠️ Proof save ho gaya (ID #{pid}) par admin ko bhej nahi paye. Support ko batayein: @Supermannn_x")
        return

    context.user_data.pop("mode", None)
    context.user_data.pop("pay_utr", None)
    context.user_data.pop("pay_shot_tries", None)
    context.user_data.pop("pay_utr_tries", None)
    await st.edit_text(
        user_payment_reply(pid, plan["name"], plan["price"], analysis),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Meri payments dekho", callback_data="mypay_list")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/Supermannn_x")],
        ]),
        parse_mode=HTML)


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
            await update.message.reply_text(VOICE_HOME_TEXT, reply_markup=voice_home_kb(), parse_mode=HTML)
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

        # 6. Password Generator (4 options)
        if action == "pwd":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Naam wala Password (yaad rahega)", callback_data="pwd_name")],
                [InlineKeyboardButton("🧠 Easy Words Password", callback_data="pwd_phrase")],
                [InlineKeyboardButton("🎲 Random Strong Password", callback_data="pwd_rand")],
                [InlineKeyboardButton("🔢 Random PIN (6 digit)", callback_data="pwd_pin")],
                [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
            ])
            await update.message.reply_text(
                f"🔐 <b>{to_bold('PASSWORD GENERATOR')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Kaisa password chahiye? 👇\n\n"
                "👤 <b>Naam wala</b> — apna naam daalo, usse strong passwords\n"
                "🧠 <b>Easy Words</b> — yaad rakhne me aasan, par strong\n"
                "🎲 <b>Random Strong</b> — sabse tough (heavy use ke liye)\n"
                "🔢 <b>PIN</b> — sirf numbers (UPI/ATM jaise)",
                reply_markup=kb,
                parse_mode=HTML,
            )
            return

        # 6b. QR Code (4 types)
        if action == "qr":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Link / Text ka QR", callback_data="qr_text")],
                [InlineKeyboardButton("💰 UPI Payment QR", callback_data="qr_upi")],
                [InlineKeyboardButton("📶 WiFi Share QR", callback_data="qr_wifi")],
                [InlineKeyboardButton("👤 Contact Card QR", callback_data="qr_vcard")],
                [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
            ])
            await update.message.reply_text(
                f"📷 <b>{to_bold('QR CODE GENERATOR')}</b> — 4 kaam ke QR\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔗 <b>Link/Text</b> — website, YouTube, koi bhi text\n"
                "💰 <b>UPI</b> — dukaan/gadi ke liye payment QR\n"
                "📶 <b>WiFi</b> — guest scan kare, password batane ki zaroorat nahi\n"
                "👤 <b>Contact Card</b> — scan par number save",
                reply_markup=kb, parse_mode=HTML)
            return

        # 6c. Site Screenshot (2 types)
        if action == "shot":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🖼️ HD Screenshot (upar ka hissa)", callback_data="shot_hd")],
                [InlineKeyboardButton("📜 Full Page Screenshot (poora page)", callback_data="shot_full")],
                [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
            ])
            await update.message.reply_text(
                f"🖼️ <b>{to_bold('SITE SCREENSHOT')}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
                "🖼️ <b>HD</b> — website ka top hissa, fast\n"
                "📜 <b>Full Page</b> — poori lambi page, thoda slow\n\n"
                "Pehle URL bhejo, screenshot ban jayega.",
                reply_markup=kb, parse_mode=HTML)
            return

        # 7. Interest Calculator — sirf CHAKRAVRIDDHI (compound), gaon/kasbe wala byaaj system
        if action == "interest":
            context.user_data["mode"] = "int_p"
            await update.message.reply_text(
                f"📈 <b>{to_bold('VYAAJ (CHAKRAVRIDDHI) CALCULATOR')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Ye <b>chakravriddhi (compound) byaaj</b> ka hisaab hai — jaisa gaon/kasbe me ₹100 par ₹x mahina wale byaaj me hota hai.\n"
                "<i>(Simple byaaj ka option humne hata diya hai — chakravriddhi hi asli hisaab hai.)</i>\n\n"
                "3 step ka kaam hai, bas:\n"
                "1️⃣ Kitna paisa liya (principal)\n"
                "2️⃣ ₹100 par kitne rupaye mahina byaaj\n"
                "3️⃣ Kitne mahine ka hisaab\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Step 1/3 — kitna paisa liya?</b>\n"
                "Bhejo: <code>50000</code> ya <code>1.5 lakh</code> ya <code>50k</code>",
                parse_mode=HTML,
            )
            return

        # 8. Image to PDF
        if action == "pdf":
            context.user_data["mode"] = "pdf"
            context.user_data["pdf_pages"] = []
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Normal PDF banao", callback_data="make_pdf_now"),
                 InlineKeyboardButton("📄 A4 Print PDF", callback_data="make_pdf_a4")],
            ])
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
            if not is_admin(uid):
                await update.message.reply_text("⛔ Ye sirf admin ke liye hai.", parse_mode=HTML)
                return
            await admin_panel_send(update.message, context, uid)
            return
        if action == "owner":
            if not is_admin(uid):
                await update.message.reply_text("⛔ Ye sirf owner ke liye hai.", parse_mode=HTML)
                return
            await update.message.reply_text(
                f"👑 <b>{to_bold('OWNER MODE')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Aap is bot ke malik ho — sab kuch unlimited ✅\n"
                "• Koi daily limit nahi\n"
                "• VIP paisa nahi lagta\n"
                "• Saare tools khule hue hain\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🛠️ <b>Owner ke kaam:</b>\n"
                "• Payment verify karna → <b>/payments</b>\n"
                "• VIP dena/lena → <b>/grant [user_id] [din]</b>\n"
                "• Sab users ko message → <b>/broadcast [message]</b>\n"
                "• Admin panel → <b>/admin</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Pending Payments", callback_data="admpay_list")],
                    [InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_home")],
                ]),
                parse_mode=HTML,
            )
            return
        if action == "cloner_private_help":
            await update.message.reply_text(
                "🔒 <b>PRIVATE CHANNEL SE POST UTHANI HAI?</b>\n\n"
                "Na koi login, na password — sirf 3 kaam:\n\n"
                "1️⃣ Apne private channel me bot <b>@utility_duniya_bot</b> ko <b>Admin</b> banao\n"
                "2️⃣ Us channel ki <b>koi ek post</b> (video/PDF) yahan <b>forward</b> karo\n"
                "3️⃣ Bot button dega — <b>📡 Ye SOURCE banao</b> dabao ✅\n\n"
                "Phir Target set karke FULL AUTO ON. Bas!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📘 Poora Guide", callback_data="cloner_private")],
                    [InlineKeyboardButton("🚀 Setup Kholein", callback_data="cloner_setup")],
                ]),
                parse_mode=HTML)
            return
        if action in ("tutorial", "help"):
            await update.message.reply_text(TUTORIAL_TEXT, parse_mode=HTML)
            return

        # Standard prompt modes
        context.user_data["mode"] = action
        if action in PROMPTS:
            # Check Daily Limit
            u = get_user(uid, update.effective_user.first_name)
            if check_limit_exceeded(u, uid):
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
        cfg_now = get_cloner_config(uid)
        ready = bool(cfg_now.get("source_chat_id")) and bool(cfg_now.get("target_chat_id"))
        kb_done = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 FULL AUTO ON karo (Step 3)", callback_data="cloner_toggle_auto")],
            [InlineKeyboardButton("🧪 Test Post Bhejo", callback_data="cloner_test")],
            [InlineKeyboardButton("📘 Guide Padho", callback_data="cloner_guide")],
            [InlineKeyboardButton("⚙️ Saari Settings", callback_data="cloner_status")],
        ])
        await update.message.reply_text(
            f"✅ <b>Step 2 poora! Target set:</b> <code>{resolved}</code>{warn}\n\n"
            + ("🎉 <b>Dono channel set ho gaye!</b>\n\n"
               "👉 <b>Step 3:</b> neeche <b>FULL AUTO ON</b> dabao — bas! Uske baad source ki har nayi post (video, PDF, photo, album) apne aap target me chali jayegi."
               if ready else
               "👉 Ab <b>Step 1</b> bhi kar lo: <b>📡 SOURCE</b> channel bhejo (jahan se posts aayengi).")
            + "\n\n<i>Bot ko dono channel me Admin banana zaroori hai.</i>",
            reply_markup=kb_done,
            parse_mode=HTML,
        )
        return

    if mode == "cloner_source":
        raw_val = raw_text.strip()
        try:
            chat = await context.bot.get_chat(raw_val)
            resolved = str(chat.id)
            title = chat.title or chat.username or resolved
            bot_is_admin = False
            try:
                mem = await context.bot.get_chat_member(chat_id=chat.id, user_id=context.bot.id)
                bot_is_admin = mem.status in ("administrator", "creator")
            except Exception:
                bot_is_admin = False

            save_cloner_config(uid, source_chat_id=resolved)
            context.user_data.pop("mode", None)

            if bot_is_admin:
                txt = (
                    f"✅ <b>Step 1 poora! Source set:</b> {hesc(str(title))}\n"
                    f"🆔 <code>{resolved}</code>\n\n"
                    "👉 Ab <b>Step 2</b>: mujhe <b>TARGET channel</b> bhejo (jahan posts bhejni hain)"
                )
                if str(get_cloner_config(uid).get("target_chat_id") or "").strip() == resolved:
                    txt += "\n\n⚠️ <b>Dhyan do:</b> Source aur Target same channel hai — auto clone ON nahi hoga."
            else:
                txt = (
                    f"⚠️ <b>Step 1: Source save ho gaya</b> <code>{resolved}</code>\n\n"
                    "❌ Par bot wahan <b>ADMIN nahi hai</b>! Us source channel me jaake bot ko <b>Admin</b> banao.\n"
                    "<i>Warna nayi posts bot tak nahi aayengi aur auto clone kaam nahi karega.</i>\n\n"
                    "👉 Ab bhi <b>Step 2</b> kar lo: TARGET channel bhejo (jahan posts bhejni hain)"
                )
            context.user_data["mode"] = "cloner_target"
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

    # ---------- ADMIN: user search / ban / broadcast (text modes) ----------
    if mode == "adm_search":
        context.user_data.pop("mode", None)
        target = None
        key = raw_text.strip().lstrip("@")
        if key.isdigit():
            target = int(key)
        else:
            found = find_by_username("@" + key)
            if found:
                target = found[0]
        if not target:
            await update.message.reply_text(
                "❌ User nahi mila. Numeric ID bhejo (jaise <code>8607774564</code>) "
                "ya wahi @username jo usne bot me set kiya ho.", parse_mode=HTML)
            return
        u = get_user(target)
        row = get_user_row(target) or {}
        prem = u.get("premium_until") or ""
        hist = user_payment_history(target)
        await update.message.reply_text(
            f"👤 <b>USER DETAIL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>ID:</b> <code>{target}</code>\n"
            f"👋 <b>Naam:</b> {hesc(str(row.get('name') or u.get('name') or '-'))}\n"
            f"👑 <b>VIP:</b> {'👑 LIFETIME' if prem == 'lifetime' else (premium_expiry(u) if prem else '❌ Nahi')}\n"
            f"⚡ <b>Aaj ke uses:</b> {u.get('uses_today', 0)}\n"
            f"🚫 <b>Banned:</b> {'Haan' if u.get('banned') else 'Nahi'}\n"
            f"📜 <b>Payments:</b> ✅ {hist['approved']} · ❌ {hist['rejected']} · ⏳ {hist['pending']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 30 din VIP do", callback_data=f"ugrant:{target}:30"),
                 InlineKeyboardButton("👑 90 din VIP do", callback_data=f"ugrant:{target}:90")],
                [InlineKeyboardButton("👑 LIFETIME do", callback_data=f"ugrant:{target}:9999"),
                 InlineKeyboardButton("🚫 VIP hatao", callback_data=f"urevoke:{target}")],
                [InlineKeyboardButton("🚫 Ban karo", callback_data=f"uban:{target}:1"),
                 InlineKeyboardButton("🟢 Unban", callback_data=f"uban:{target}:0")],
            ]),
            parse_mode=HTML)
        return

    if mode == "adm_broadcast":
        context.user_data.pop("mode", None)
        ids = all_user_ids()
        sent = failed = 0
        st = await update.message.reply_text(f"📢 {len(ids)} users ko bhej raha hoon...")
        for i in ids:
            try:
                await context.bot.send_message(i, raw_text, parse_mode=HTML)
                sent += 1
            except Exception:
                failed += 1
            if (sent + failed) % 25 == 0:
                await asyncio.sleep(1)
        await st.edit_text(f"✅ <b>Broadcast done!</b>\n• Bheja: {sent}\n• Fail (block kiye honge): {failed}", parse_mode=HTML)
        return

    if mode == "adm_ban":
        parts = raw_text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await update.message.reply_text("Format: <code>ban 123456789</code> ya <code>unban 123456789</code>", parse_mode=HTML)
            return
        act, target = parts[0].lower(), int(parts[1])
        if act.startswith("unban"):
            set_ban(target, 0)
            await update.message.reply_text(
                f"🟢 <b>Unban ho gaya</b> — <code>{target}</code>\n\n"
                "Aur kisi ko ban/unban karna ho to aise hi likho: <code>ban 123456</code>",
                parse_mode=HTML)
        else:
            set_ban(target, 1)
            await update.message.reply_text(
                f"🚫 <b>Ban ho gaya</b> — <code>{target}</code>\n\n"
                "Unban karna ho to: <code>unban 123456</code>",
                parse_mode=HTML)
        return

    # ---------- ADMIN: user search / ban / broadcast (text modes) ----------
    if mode == "adm_search":
        context.user_data.pop("mode", None)
        target = None
        key = raw_text.strip().lstrip("@")
        if key.isdigit():
            target = int(key)
        else:
            found = find_by_username("@" + key)
            if found:
                target = found[0]
        if not target:
            await update.message.reply_text(
                "❌ User nahi mila. Numeric ID bhejo (jaise <code>8607774564</code>) "
                "ya wahi @username jo usne bot me set kiya ho.", parse_mode=HTML)
            return
        u = get_user(target)
        row = get_user_row(target)
        prem = u.get("premium_until") or ""
        hist = user_payment_history(target)
        await update.message.reply_text(
            f"👤 <b>USER DETAIL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>ID:</b> <code>{target}</code>\n"
            f"👋 <b>Naam:</b> {hesc(str((row[1] if row else '') or u.get('name') or '-'))}\n"
            f"👑 <b>VIP:</b> {'👑 LIFETIME' if prem == 'lifetime' else (premium_expiry(u) if prem else '❌ Nahi')}\n"
            f"⚡ <b>Aaj ke uses:</b> {u.get('uses_today', 0)}\n"
            f"🚫 <b>Banned:</b> {'Haan' if u.get('banned') else 'Nahi'}\n"
            f"📜 <b>Payments:</b> ✅ {hist['approved']} · ❌ {hist['rejected']} · ⏳ {hist['pending']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 30 din VIP do", callback_data=f"ugrant:{target}:30"),
                 InlineKeyboardButton("👑 90 din VIP do", callback_data=f"ugrant:{target}:90")],
                [InlineKeyboardButton("👑 LIFETIME do", callback_data=f"ugrant:{target}:9999"),
                 InlineKeyboardButton("🚫 VIP hatao", callback_data=f"urevoke:{target}")],
                [InlineKeyboardButton("🚫 Ban karo", callback_data=f"uban:{target}:1"),
                 InlineKeyboardButton("🟢 Unban", callback_data=f"uban:{target}:0")],
            ]),
            parse_mode=HTML)
        return

    if mode == "adm_broadcast":
        context.user_data.pop("mode", None)
        ids = all_user_ids()
        sent = failed = 0
        st = await update.message.reply_text(f"📢 {len(ids)} users ko bhej raha hoon...")
        for i in ids:
            try:
                await context.bot.send_message(i, raw_text, parse_mode=HTML)
                sent += 1
            except Exception:
                failed += 1
            if (sent + failed) % 25 == 0:
                await asyncio.sleep(1)
        await st.edit_text(f"✅ <b>Broadcast done!</b>\n• Bheja: {sent}\n• Fail (block kiye honge): {failed}", parse_mode=HTML)
        return

    if mode == "adm_ban":
        context.user_data.pop("mode", None)
        parts = raw_text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await update.message.reply_text("Format: <code>ban 123456789</code> ya <code>unban 123456789</code>", parse_mode=HTML)
            return
        act, target = parts[0].lower(), int(parts[1])
        if act.startswith("unban"):
            set_ban(target, 0)
            await update.message.reply_text(f"🟢 User <code>{target}</code> ka ban hata diya.", parse_mode=HTML)
        else:
            set_ban(target, 1)
            await update.message.reply_text(f"🚫 User <code>{target}</code> ban kar diya.", parse_mode=HTML)
        return

    # ---------- PAYMENT STEP 1: UTR (strict format check) ----------
    if mode and mode.startswith("pay_utr_"):
        plan_key = mode.replace("pay_utr_", "")
        plan = VIP_PLANS.get(plan_key, VIP_PLANS["plan_30"])
        res = validate_utr(raw_text)

        if not res["ok"]:
            tries = context.user_data.get("pay_utr_tries", 0) + 1
            context.user_data["pay_utr_tries"] = tries
            await update.message.reply_text(
                f"❌ <b>Ye UTR valid nahi hai!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 <b>Aapne bheja:</b> <code>{hesc(raw_text[:40])}</code>\n"
                f"⚠️ <b>Wajah:</b> {res.get('reason')}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                + utr_help_text() +
                f"\n\n🔁 <b>Ab sahi UTR bhejo</b> ({tries}/5 try)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Plan dobara kholo", callback_data=f"buy_plan_{plan_key}")]]),
                parse_mode=HTML,
            )
            if tries >= 5:
                await update.message.reply_text("😅 Lagta hai UTR nahi mil raha. Koi baat nahi — Support se baat kar lo, wo haath se verify kar dega: @Supermannn_x")
                context.user_data.pop("mode", None)
            return

        utr = res["utr"]
        if utr_exists(utr):
            await update.message.reply_text(
                "🚫 <b>Ye UTR pehle bhi use ho chuka hai!</b>\n\n"
                f"🧾 <code>{hesc(utr)}</code>\n\n"
                "Ek UTR se sirf <b>ek hi baar</b> VIP milti hai. Naya payment kar do ya sahi UTR bhejo.",
                parse_mode=HTML)
            return

        context.user_data["pay_utr"] = utr
        context.user_data["pay_plan"] = plan_key
        context.user_data["pay_shot_tries"] = 0
        context.user_data["mode"] = f"pay_shot_{plan_key}"
        context.user_data["pay_utr_kind"] = res.get("kind", "")
        await update.message.reply_text(
            "✅ <b>UTR sahi hai!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧾 <b>UTR:</b> <code>{hesc(utr)}</code>\n"
            f"📋 <b>Type:</b> {res.get('kind')}\n"
            f"💎 <b>Plan:</b> {plan['name']} (₹{plan['price']})\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📸 <b>Step 3:</b> Ab payment ka <b>screenshot</b> bhejo\n\n"
            "⚠️ <b>Dhyan do:</b>\n"
            "• Screenshot me payment <b>success</b> dikhna chahiye (amount + UTR)\n"
            "• Selfie, photo ya koi random image bhejne par system <b>reject</b> kar dega\n"
            "• Screenshot <b>jaldi</b> bhejo, warna flow reset ho jayega",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Plan badlo", callback_data="open_vip_menu")]]),
            parse_mode=HTML,
        )
        return

    # ---------- PAYMENT STEP 3: text bhej diya screenshot ki jagah ----------
    if mode and mode.startswith("pay_shot_"):
        plan_key = mode.replace("pay_shot_", "")
        await update.message.reply_text(
            "📸 <b>Ab screenshot chahiye (text nahi)!</b>\n\n"
            "Phone me payment app kholo → us payment ka <b>screenshot</b> lo → yahan bhejo.\n"
            "⚠️ Screenshot me dikhna chahiye: <b>amount, success/paid, aur UTR</b>.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Plan dobara kholo", callback_data=f"buy_plan_{plan_key}")]]),
            parse_mode=HTML)
        return

    # Check Daily Limit for Active Executions
    u = get_user(uid, update.effective_user.first_name)
    if mode and check_limit_exceeded(u, uid):
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
        st = await update.message.reply_text("🎙️ Awaaz ban rahi hai... (2-5 second)")
        preset = context.user_data.get("voice_preset") or "don_deep"
        if preset not in ACTOR_VOICE_PRESETS:
            preset = "don_deep"
        try:
            mp3_path, info = await generate_actor_voice(raw_text, preset)
            p_info = ACTOR_VOICE_PRESETS.get(preset, {})
            note = info.get("note") or ""
            caption = (
                f"🎙️ <b>{to_bold('VOICE READY')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎭 Style: <b>{p_info.get('name', 'Actor')}</b>\n"
                f"🌍 Language: {info.get('lang', '—')}\n"
                f"🔊 Voice: <code>{info.get('voice_short') or info.get('voice', '')}</code>"
                + (f"\n\n{note}" if note else "")
                + "\n\n🔁 Dusri voice try karne ke liye menu se Voice Studio kholein."
            )
            with open(mp3_path, "rb") as f:
                await update.message.reply_voice(voice=f, caption=caption, parse_mode=HTML)
            await st.delete()
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except Exception as e:
            await st.edit_text(fail_msg("VOICE GENERATION FAILED", str(e)), parse_mode=HTML)
        add_use(uid)
        return

    if mode == "voice_lab_text":
        st = await update.message.reply_text("🧪 Voice Lab me awaaz ban rahi hai... (2-5 second)")
        short = context.user_data.get("vlab_voice", "hi-IN-MadhurNeural")
        label = context.user_data.get("vlab_voice_label", "Voice")
        spd_key = context.user_data.get("vlab_speed", "normal")
        spd_label, rate = VOICE_SPEEDS.get(spd_key, ("▶️ Normal", "+0%"))
        try:
            mp3_path, info = await generate_voice(raw_text, short, rate, "+0Hz", label=label)
            note = info.get("note") or ""
            caption = (
                f"🧪 <b>{to_bold('VOICE LAB AUDIO READY')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎤 Voice: <b>{label}</b>\n"
                f"🔊 Engine: <code>{info.get('voice', short)}</code>\n"
                f"⚡ Speed: {spd_label} ({rate})"
                + (f"\n\n{note}" if note else "")
            )
            with open(mp3_path, "rb") as f:
                await update.message.reply_voice(voice=f, caption=caption, parse_mode=HTML)
            await st.delete()
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except Exception as e:
            await st.edit_text(fail_msg("VOICE LAB FAILED", str(e)), parse_mode=HTML)
        add_use(uid)
        return

    if mode == "ip":
        res = lookup_ip_domain(raw_text)
        if res.get("ok"):
            flags = []
            flags.append("🛡️ Proxy/VPN: " + ("⚠️ Haan (chhupa hua connection)" if res.get("is_proxy") else "✅ Nahi"))
            flags.append("🏢 Datacenter/Hosting: " + ("✅ Haan (server/VPN line)" if res.get("is_hosting") else "❌ Nahi (normal internet line)"))
            flags.append("📱 Mobile network: " + ("✅ Haan" if res.get("is_mobile") else "❌ Nahi"))
            rows = [[InlineKeyboardButton("🗺️ Map par dekho", url=res["maps_link"])]]
            await update.message.reply_text(
                f"🌐 <b>{to_bold('IP / DOMAIN INFORMATION')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Query:</b> <code>{hesc(res['query'])}</code>\n"
                f"• <b>IP:</b> <code>{res['ip']}</code>\n"
                f"• <b>Country:</b> {res['country']} ({res.get('country_code') or '—'})\n"
                f"• <b>State:</b> {res['region']}\n"
                f"• <b>City:</b> {res['city']} — PIN {res['zip']}\n"
                f"• <b>Lat/Long:</b> {res['lat']}, {res['lon']}\n"
                f"• <b>ISP / Company:</b> {res['isp']}\n"
                f"• <b>Organization:</b> {res['org']}\n"
                f"• <b>Network:</b> {res.get('as', '—')}\n"
                f"• <b>Timezone:</b> {res['timezone']}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(flags) +
                "\n\n<i>Ye public IP ki jaankari hai (website/server dekhne ke liye). Kisi ka ghar ka pata nahi milta.</i>",
                reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "rto":
        res = lookup_vehicle_rto(raw_text)
        if res.get("ok"):
            rows = [[InlineKeyboardButton(txt, url=url)] for txt, url in res["links"]]
            card = (
                f"🚗 <b>{to_bold('RTO VEHICLE DETAILS')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔖 <b>Number Plate:</b> <code>{res['pretty']}</code>\n"
                f"🗺️ <b>State:</b> {res['state_name']} ({res['state_code']})\n"
                f"🏢 <b>RTO Code:</b> {res['rto_code']} — {res['district']}\n"
                + (f"🚙 <b>Vehicle Class (series se):</b> {res['vehicle_class']}\n" if res.get("vehicle_class") else "")
                + "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"ℹ️ <i>{res['note']}</i>\n\n"
                "👇 Neeche se official check karein:"
            )
            await update.message.reply_text(card, reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            await update.message.reply_text(fail_msg("RTO LOOKUP FAILED", res.get("error", "Invalid Plate")), parse_mode=HTML)
        add_use(uid)
        return

    if mode == "numinfo":
        res = lookup_phone_info(raw_text)
        if res.get("ok"):
            rows = []
            pair = []
            for label, url in res["links"]:
                pair.append(InlineKeyboardButton(label, url=url))
                if len(pair) == 2:
                    rows.append(pair); pair = []
            if pair:
                rows.append(pair)
            card = (
                f"📱 <b>{to_bold('NUMBER INFORMATION')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Number:</b> <code>{res['international']}</code>\n"
                f"• <b>National:</b> {res['national']}\n"
                f"• <b>Type:</b> {res['type']} {res['series_note']}\n"
                f"• <b>Operator:</b> {res['operator']}\n"
                f"• <b>Circle/Region:</b> {res['circle']}\n"
                f"• <b>Country:</b> {res['country']} ({res.get('country_code') or '—'})\n"
                f"• <b>Timezone:</b> {res['timezones']}\n"
                f"• <b>Valid:</b> {'✅ Haan' if res['valid'] else '⚠️ Shaq hai'}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"ℹ️ <i>{res['note']}</i>\n\n"
                "👇 Aage check karne ke links:"
            )
            if NUM_LEAK_ENABLED():
                rows.insert(0, [InlineKeyboardButton("🧾 Public Records bhi dekho (naam/pata)", callback_data=f"numrec:{res['e164']}")])
            await update.message.reply_text(card, reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "ifsc":
        i_res = lookup_ifsc(raw_text)
        if i_res.get("ok"):
            rows = [[InlineKeyboardButton("📍 Google Maps par Branch", url=i_res["maps_link"])]]
            card = (
                f"🏦 <b>{to_bold(i_res['bank'])}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔑 <b>IFSC:</b> <code>{i_res['ifsc']}</code>\n"
                f"🏢 <b>Branch:</b> {i_res['branch']}\n"
                f"📍 <b>Address:</b> {i_res['address']}\n"
                f"🏙️ <b>City/State:</b> {i_res['city']}, {i_res['state']}\n"
                + (f"📞 <b>Contact:</b> {i_res['contact']}\n" if i_res.get('contact') else "")
                + f"🔢 <b>MICR:</b> <code>{i_res['micr']}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💳 <b>Services:</b> "
                + " ".join([
                    f"UPI {'✅' if i_res['upi'] else '❌'}",
                    f"NEFT {'✅' if i_res['neft'] else '❌'}",
                    f"RTGS {'✅' if i_res['rtgs'] else '❌'}",
                    f"IMPS {'✅' if i_res['imps'] else '❌'}",
                ])
            )
            await update.message.reply_text(card, reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {i_res.get('error')}", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "pin":
        cleaned = re.sub(r"[^\d]", "", raw_text)
        if len(cleaned) == 6:
            p_res = lookup_pincode(cleaned)
            if p_res.get("ok"):
                rows = [[InlineKeyboardButton("📍 Map par dekho", url=p_res["maps_link"])]] if p_res.get("maps_link") else []
                card = (
                    f"📮 <b>{to_bold('PINCODE DETAILS')}</b> — <code>{p_res['pincode']}</code>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>District:</b> {p_res['district']}\n"
                    f"• <b>State:</b> {p_res['state']}\n"
                    + (f"• <b>Taluk:</b> {p_res['taluk']}\n" if p_res.get('taluk') else "")
                    + f"• <b>Division/Region:</b> {p_res['division']} / {p_res['region']}\n"
                    f"• <b>Circle:</b> {p_res['circle']}\n"
                    f"• <b>Delivery:</b> {p_res['delivery'] or 'N/A'}\n"
                    f"• <b>Type:</b> {p_res.get('branch_type') or 'N/A'}\n"
                    f"• <b>Total Post Offices:</b> {p_res['total_offices']}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏤 <b>Post Offices:</b>\n" + "\n".join(f"   • {n}" for n in p_res['post_offices'])
                )
                await update.message.reply_text(card, reply_markup=InlineKeyboardMarkup(rows) if rows else None, parse_mode=HTML)
            else:
                await update.message.reply_text(f"❌ {p_res.get('error')}", parse_mode=HTML)
        else:
            # Area / post-office ke naam se pincode dhoondo
            st = await update.message.reply_text("🔍 Area naam se pincode dhoondh raha hoon...")
            a_res = search_by_area_name(raw_text)
            if a_res.get("ok"):
                lines = []
                rows = []
                for r in a_res["results"][:8]:
                    lines.append(f"• <b>{hesc(r['name'])}</b> — <code>{r['pincode']}</code> ({hesc(r['district'])}, {hesc(r['state'])})")
                    rows.append([InlineKeyboardButton(f"📋 {r['pincode']} — {r['name'][:28]}", callback_data=f"copy_{r['pincode']}")])
                await st.edit_text(
                    f"📮 <b>{to_bold('AREA SEARCH')}: {hesc(a_res['query'])}</b>\n"
                    f"({a_res['total']} post offices mili)\n\n" + "\n".join(lines) +
                    "\n\n💡 Pincode copy karne ke liye neeche button dabayein:",
                    reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML,
                )
            else:
                await st.edit_text(f"❌ {a_res.get('error')}\n\n💡 Ya 6-digit pincode bhejein (jaise <code>800001</code>)", parse_mode=HTML)
        add_use(uid)
        return

    # ID & USERNAME FINDER — REAL existence check (GitHub/Telegram/YouTube/TikTok/Steam)
    if mode == "idfind":
        if raw_text.lower() == "me":
            await update.message.reply_text(
                f"🆔 <b>Aapki Telegram ID:</b> <code>{uid}</code>\n"
                f"👤 <b>Naam:</b> {hesc(update.effective_user.first_name or '')}\n"
                f"🔗 <b>Username:</b> @{update.effective_user.username or 'set nahi'}",
                parse_mode=HTML,
            )
            return

        if raw_text.startswith("@") or re.fullmatch(r"[A-Za-z0-9._\-]{2,}", raw_text.strip()):
            st = await update.message.reply_text("🔍 Asli check kar raha hoon (5 platforms)...")
            p_info = check_username_platforms(raw_text)
            if not p_info.get("ok"):
                await st.edit_text(f"❌ {p_info.get('error')}", parse_mode=HTML)
                return

            lines = []
            for r in p_info["results"]:
                if r["exists"] is True:
                    extra = f" — <i>{hesc(str(r['extra'])[:45])}</i>" if r.get("extra") else ""
                    lines.append(f"✅ <b>{r['label']}</b> — account MILA{extra}")
                elif r["exists"] is False:
                    lines.append(f"❌ <b>{r['label']}</b> — account nahi hai")
                else:
                    lines.append(f"❔ <b>{r['label']}</b> — check nahi ho paya")

            # Lazy search (bot DB) se Telegram ID bhi mil jaye to
            found = find_by_username("@" + p_info["username"])
            id_line = f"\n🆔 <b>Bot ke paas saved ID:</b> <code>{found[0]}</code> ({hesc(found[1])})" if found else ""

            rows = [[InlineKeyboardButton(f"🔗 {l['label']}", url=l["url"])] for l in p_info["links"][:8]]
            await st.edit_text(
                f"🔍 <b>{to_bold('USERNAME CHECK')}:</b> <code>@{p_info['username']}</code>\n"
                f"({p_info['found']}/5 platform par mila)\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                + "\n".join(lines) + id_line +
                "\n━━━━━━━━━━━━━━━━━━━━━━\n"
                "👇 Baaki platforms par directly kholne ke links:",
                reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML,
            )
            add_use(uid)
            return

        await update.message.reply_text(
            "🆔 <b>ID & USERNAME FINDER</b>\n\n"
            "Ye 3 tareeke se kaam karta hai:\n"
            "1️⃣ <code>me</code> bhejo → apni ID milegi\n"
            "2️⃣ Kisi user/channel ka <b>message forward</b> karo → uski ID milegi\n"
            "3️⃣ <code>@username</code> bhejo → 5 platforms par asli check hoga ✅/❌\n\n"
            "<i>Note: private user ki ID sirf tab milti hai jab wo message forwardable ho.</i>",
            parse_mode=HTML,
        )
        return

    if mode == "pwd_name":
        passwords = name_passwords(raw_text)
        res_txt = f"👤 <b>{to_bold('PASSWORDS FOR')} {hesc(raw_text.upper())}:</b>\n\n"
        for i, p in enumerate(passwords, 1):
            sc, lab, _ = password_strength(p)
            res_txt += f"{i}️⃣ <code>{p}</code>  ({lab})\n"
        res_txt += "\n💡 <i>Naam wale password yaad rakhne me aasan hote hain, par inme number/symbol zaroor rakhein.</i>"
        await update.message.reply_text(res_txt, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "pwd_pin":
        pins = [gen_pin(6) for _ in range(5)]
        await update.message.reply_text(
            f"🔢 <b>{to_bold('RANDOM PINS (6 digit)')}</b>\n\n" +
            "\n".join(f"{i}️⃣ <code>{p}</code>" for i, p in enumerate(pins, 1)) +
            "\n\n⚠️ <i>Umeed hai ye UPI/ATM PIN jaisa kuch nahi hai — kisi ko share na karein.</i>",
            parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "pwd_phrase":
        phrases = [gen_passphrase(4) for _ in range(4)]
        await update.message.reply_text(
            f"🧠 <b>{to_bold('MEMORABLE STRONG PASSWORDS')}</b>\n"
            "<i>(yaad rakhna aasan, todna mushkil)</i>\n\n" +
            "\n".join(f"{i}️⃣ <code>{p}</code>  ({password_strength(p)[1]})" for i, p in enumerate(phrases, 1)) +
            "\n\n💡 <i>Tip: inme thoda apna symbol/word mila do (jaise <code>@</code> laga kar) — aur bhi strong ho jayega.</i>",
            parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "qr":
        buf = make_qr_bytes(raw_text)
        await update.message.reply_photo(
            photo=buf,
            caption=f"📷 <b>{to_bold('HD QR CODE READY')}</b>\n\n🔗 <code>{hesc(raw_text[:80])}</code>\n\n<i>Scan karte hi ye link khul jayega.</i>",
            parse_mode=HTML)
        add_use(uid)
        return

    if mode == "qr_upi":
        context.user_data["qr_upi_id"] = raw_text.strip()
        context.user_data["mode"] = "qr_upi_amt"
        await update.message.reply_text(
            "💰 <b>UPI QR — Step 2/2</b>\n\n"
            f"UPI ID: <code>{hesc(raw_text)}</code>\n\n"
            "Ab <b>amount</b> bhejein (₹). Fixed amount nahi chahiye to <code>0</code> bhejo:\n"
            "(jaise: <code>500</code> ya <code>0</code>)", parse_mode=HTML)
        return

    if mode == "qr_upi_amt":
        upi_id = context.user_data.get("qr_upi_id", "")
        try:
            amt = float(re.sub(r"[^\d.]", "", raw_text) or 0)
        except Exception:
            amt = 0
        context.user_data.pop("mode", None)
        link = f"upi://pay?pa={upi_id}&pn=Payee"
        if amt > 0:
            link += f"&am={amt:.2f}&cu=INR&tn=Payment"
        buf = make_qr_bytes(link, box_size=14, fill="#0b3d91")
        await update.message.reply_photo(
            photo=buf,
            caption=(f"💰 <b>{to_bold('UPI PAYMENT QR')}</b>\n\n"
                     f"• <b>UPI ID:</b> <code>{hesc(upi_id)}</code>\n"
                     f"• <b>Amount:</b> {'₹' + format(amt, ',.0f') if amt > 0 else 'Koi bhi amount (open QR)'}\n\n"
                     "📲 PhonePe / GPay / Paytm / BHIM se scan karein — paisa seedha usi UPI par jayega.\n"
                     "<i>Tip: QR print karke dukaan par bhi laga sakte hain.</i>"),
            parse_mode=HTML)
        add_use(uid)
        return

    if mode == "qr_wifi":
        context.user_data["qr_wifi_ssid"] = raw_text.strip()
        context.user_data["mode"] = "qr_wifi_pass"
        await update.message.reply_text(
            "📶 <b>WiFi QR — Step 2/2</b>\n\n"
            f"WiFi Name (SSID): <code>{hesc(raw_text)}</code>\n\n"
            "Ab <b>WiFi password</b> bhejein:\n"
            "(open WiFi hai to <code>none</code> bhejo)", parse_mode=HTML)
        return

    if mode == "qr_wifi_pass":
        ssid = context.user_data.get("qr_wifi_ssid", "")
        pwd = raw_text.strip()
        context.user_data.pop("mode", None)
        data = wifi_qr_data(ssid, "" if pwd.lower() == "none" else pwd)
        buf = make_qr_bytes(data, box_size=14)
        await update.message.reply_photo(
            photo=buf,
            caption=(f"📶 <b>{to_bold('WIFI QR READY')}</b>\n\n"
                     f"• <b>WiFi:</b> <code>{hesc(ssid)}</code>\n"
                     f"• <b>Password:</b> <code>{hesc(pwd) if pwd.lower() != 'none' else 'Open (no password)'}</code>\n\n"
                     "📱 Guest aayein → phone se ye QR scan karein → WiFi automatically connect ho jayega ✅\n"
                     "<i>Print karke deewar par chipka do — password batane ki zaroorat nahi!</i>"),
            parse_mode=HTML)
        add_use(uid)
        return

    if mode == "qr_vcard":
        context.user_data["qr_vc_name"] = raw_text.strip()[:40]
        context.user_data["mode"] = "qr_vcard_phone"
        await update.message.reply_text(
            "👤 <b>Contact Card — Step 2/2</b>\n\n"
            f"Naam: <b>{hesc(raw_text)}</b>\n\n"
            "Ab <b>phone number</b> bhejein (jaise <code>9876543210</code>):", parse_mode=HTML)
        return

    if mode == "qr_vcard_phone":
        name = context.user_data.get("qr_vc_name", "")
        phone = raw_text.strip()
        context.user_data.pop("mode", None)
        data = vcard_data(name, phone, org="Utility Duniya Bot")
        buf = make_qr_bytes(data, box_size=14)
        await update.message.reply_photo(
            photo=buf,
            caption=(f"👤 <b>{to_bold('DIGITAL VISITING CARD READY')}</b>\n\n"
                     f"• <b>Naam:</b> {hesc(name)}\n"
                     f"• <b>Phone:</b> <code>{hesc(phone)}</code>\n\n"
                     "📱 Scan karte hi phone me contact save ho jayega (naam + number) ✅"),
            parse_mode=HTML)
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

    # ---- INTEREST / VYAAJ CALCULATOR (sirf CHAKRAVRIDDHI / compound — gaon-kasbe wala byaaj system) ----
    if mode == "int_p":
        try:
            val = raw_text.lower().replace(",", "").replace("₹", "").strip()
            if "lakh" in val or "lac" in val:
                p_amt = float(re.search(r"\d+(?:\.\d+)?", val).group(0)) * 100000
            elif "hazaar" in val or "hazar" in val or re.search(r"\d+\s*k\b", val):
                p_amt = float(re.search(r"\d+(?:\.\d+)?", val).group(0)) * 1000
            else:
                p_amt = float(re.search(r"\d+(?:\.\d+)?", val).group(0))
            assert p_amt > 0
        except Exception:
            await update.message.reply_text(
                "⚠️ <b>Kitna paisa liya (principal)?</b> Aise bhejein:\n"
                "<code>50000</code> ya <code>1.5 lakh</code> ya <code>50k</code>", parse_mode=HTML)
            return
        context.user_data["int_principal"] = p_amt
        context.user_data["mode"] = "int_rate"
        await update.message.reply_text(
            f"📈 <b>{to_bold('VYAAJ (CHAKRAVRIDDHI) CALCULATOR')}</b> — Step 1/3 ✅\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Amount:</b> {inr(p_amt)} ({words_amount(p_amt)})\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Step 2/3 — <b>Mahine ka byaaj kitna hai?</b>\n\n"
            "👉 <b>₹100 par kitne rupaye mahina?</b>\n"
            "   (jaise gaon me ₹100 par ₹5 mahina chalta hai → sirf <code>5</code> bhejo)\n\n"
            "Ya agar percentage pata hai to aise: <code>3% mahina</code>\n"
            "<i>(saalana nahi — mahine ka hisaab bhejein)</i>",
            parse_mode=HTML,
        )
        return

    if mode == "int_rate":
        t = raw_text.lower().replace("%", " ").strip()
        m = re.search(r"\d+(?:\.\d+)?", t)
        if not m:
            await update.message.reply_text("⚠️ Byaaj ka number bhejein (jaise <code>5</code> = ₹100 par ₹5 mahina)", parse_mode=HTML)
            return
        per_ht = float(m.group(0))
        if per_ht > 100:
            await update.message.reply_text("⚠️ Ye bahut zyada hai. ₹100 par kitne rupaye mahina (jaise 2, 3, 5)?", parse_mode=HTML)
            return
        monthly_rate = rate_from_per_hundred(per_ht)   # ₹x per ₹100 per month = x% monthly
        context.user_data["int_monthly_rate"] = monthly_rate
        context.user_data["int_per_hundred"] = per_ht
        context.user_data["mode"] = "int_time"
        principal = context.user_data.get("int_principal", 0)
        first_int = principal * monthly_rate / 100.0
        await update.message.reply_text(
            f"✅ <b>Step 2/3 purra!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Amount: <b>{inr(principal)}</b> ({words_amount(principal)})\n"
            f"📊 Byaaj: <b>₹100 par ₹{per_ht:g} mahina</b> ({monthly_rate:g}% per month)\n"
            f"🧮 Pehle mahine ka byaaj: <b>{inr(first_int)}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Step 3/3 — <b>Kitne mahine ka hisaab chahiye?</b>\n"
            "(jaise <code>12</code> mahine, ya <code>2 saal</code>, ya <code>1 saal 6 mahine</code>)",
            parse_mode=HTML,
        )
        return

    if mode == "int_time":
        t = raw_text.lower()
        years = re.search(r"(\d+(?:\.\d+)?)\s*(saal|sal|year|yr)", t)
        months_only = re.search(r"(\d+(?:\.\d+)?)\s*(mahine|mahina|month|m\b)", t)
        bare = re.search(r"^(\d+)\s*$", t.strip())
        months = 0
        if years:
            months += int(float(years.group(1)) * 12)
        if months_only:
            months += int(float(months_only.group(1)))
        if not years and not months_only and bare:
            months = int(bare.group(1))
        if months < 1 or months > 600:
            await update.message.reply_text("⚠️ Time bhejein: <code>12</code> (mahine) ya <code>2 saal</code> ya <code>1 saal 6 mahine</code>", parse_mode=HTML)
            return

        principal = float(context.user_data.get("int_principal", 0))
        rate_m = float(context.user_data.get("int_monthly_rate", 0))
        per_ht = context.user_data.get("int_per_hundred", rate_m)
        v = village_compound_interest(principal, rate_m, months)
        context.user_data.pop("mode", None)

        # Mahine ka table (pehle 6) + milestones
        rows_txt = []
        for r in v["rows"][:6]:
            rows_txt.append(f"   {r['month']}. Byaaj {inr(r['interest'])} → Total {inr(r['closing'])}")
        if months > 6:
            rows_txt.append(f"   ... ({months - 6} mahine aur aise hi badhta jayega)")
        mile_txt = "".join(f"\n   • {k} baad: <b>{inr(amt)}</b>" for k, amt in v["milestones"].items())

        from datetime import timedelta as _td
        _msg_date = getattr(update.message, "date", None)
        end_date = (_msg_date + _td(days=30 * months)) if _msg_date else None
        end_line = f"\n📅 <b>{months} mahine baad (approx):</b> {end_date.strftime('%d %b %Y')}" if end_date else ""

        await update.message.reply_text(
            f"📈 <b>{to_bold('CHAKRAVRIDDHI BYAAJ REPORT')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Paisa liya:</b> {inr(v['principal'])} ({words_amount(v['principal'])})\n"
            f"📊 <b>Byaaj:</b> ₹100 par ₹{per_ht:g} mahina ({rate_m:g}% monthly)\n"
            f"⏳ <b>Time:</b> {months} mahine\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ Pehle mahine ka byaaj: <b>{inr(v['first_month_interest'])}</b>\n"
            f"2️⃣ {months} mahine ka <b>kul byaaj:</b> <b>{inr(v['total_interest'])}</b>\n"
            f"3️⃣ <b>Aapko wapas dena hoga: {inr(v['total_payable'])}</b> ({words_amount(v['total_payable'])})\n"
            f"{end_line}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Mahine-dar-mahine (chakravriddhi):</b>\n" + "\n".join(rows_txt) +
            (f"\n\n🎯 <b>Kitna kab hoga:</b>{mile_txt}" if mile_txt else "") +
            "\n━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>Samjho:</b> ye <b>chakravriddhi (compound)</b> byaaj hai — jo byaaj har mahine nahi diya jata, "
            "wo principal me jud kar agle mahine byaaj bhi deta hai. Isliye bahut tezi se badhta hai.\n"
            "👉 Agar aap <b>har mahine sirf byaaj</b> dete rahe, to principal wahi rehta aur byaaj ₹{first:,.0f}/mahina hi lagta (jaise gaon me byaaj bharte hain).\n"
            "<i>Yeh jaankari financial advice nahi hai.</i>".format(first=v["first_month_interest"]),
            parse_mode=HTML,
        )
        add_use(uid)
        return

    if mode == "emi":
        p_amt, rate, months = parse_emi_input(raw_text)
        if not p_amt:
            await update.message.reply_text(
                "⚠️ <b>EMI ke liye aise bhejein:</b>\n\n"
                "• <code>100000</code> → ₹1L @ 10.5% / 12 mahine\n"
                "• <code>5,00,000 9% 24m</code> → poora control\n"
                "• <code>3 lakh 8.5% 5 saal</code> → Hindi style bhi chalega",
                parse_mode=HTML,
            )
            return
        rep_e = emi_full_report(p_amt, rate, months)
        emi, rows = emi_schedule(p_amt, rate, months)
        sched = "\n".join(
            f"   {m}. {d.strftime('%d %b %y')}: {inr(e)}  (byaaj {inr(i)})"
            for (m, e, pr, i, bal), d in zip(rows[:5], [r["date"] for r in rep_e["rows"][:5]])
        )
        await update.message.reply_text(
            f"🧮 <b>{to_bold('LOAN EMI FULL REPORT')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Loan:</b> {inr(p_amt)} ({words_amount(p_amt)})\n"
            f"📊 <b>Rate:</b> {rate}% per year\n"
            f"⏳ <b>Tenure:</b> {months} mahine ({rep_e['years_text']})\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Har mahine EMI: {inr(rep_e['emi'])}</b>\n"
            f"📈 <b>Kul byaaj:</b> {inr(rep_e['total_interest'])}\n"
            f"💳 <b>Kul dena hoga:</b> {inr(rep_e['total_payment'])} ({words_amount(rep_e['total_payment'])})\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Pehli EMI:</b> {rep_e['first_emi_date'].strftime('%d %b %Y')}\n"
            f"🏁 <b>Aakhri EMI:</b> {rep_e['last_emi_date'].strftime('%d %b %Y')}\n"
            f"⏱️ <b>Poora loan khatam:</b> {months} mahine = <b>{rep_e['total_days']:,} din me</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📆 <b>Pehli 5 EMI ki date:</b>\n{sched}\n"
            "💡 <i>Har mahine ki fix date par EMI dene se loan time se pehle khatam ho jayega.</i>",
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

    if mode in ("shot", "shot_full"):
        fullpage = (mode == "shot_full")
        st = await update.message.reply_text("📸 " + ("Full page screenshot le raha hoon (thoda time lagta hai)..." if fullpage else "HD screenshot le raha hoon..."))
        buf = site_screenshot(raw_text, fullpage=fullpage)
        if buf:
            await update.message.reply_photo(
                photo=buf,
                caption=(f"📜 <b>{to_bold('FULL PAGE SCREENSHOT')}</b>\n🌐 <code>{hesc(raw_text[:80])}</code>" if fullpage
                         else f"🖼️ <b>{to_bold('HD SCREENSHOT')}</b>\n🌐 <code>{hesc(raw_text[:80])}</code>\n\n📜 Poora page chahiye? Menu se 'SITE SCREENSHOT' → 📜 Full Page chunein."),
                parse_mode=HTML)
            await st.delete()
        else:
            await st.edit_text(
                "❌ Screenshot nahi ban paya.\n\n💡 <b>Kya karein:</b>\n"
                "• URL mein <code>https://</code> laga kar bhejein\n"
                "• Site ne bot block kiya ho sakta hai — koi dusri site try karein\n"
                "• 10-20 second baad dobara try karein")
        add_use(uid)
        return

    # Forwarded message for ID Finder + Auto-Forward channel pakadna
    if hasattr(update.message, "forward_origin") and update.message.forward_origin:
        orig = update.message.forward_origin
        if hasattr(orig, "sender_user") and orig.sender_user:
            f_user = orig.sender_user
            await update.message.reply_text(f"🆔 <b>Forwarded User ID:</b> <code>{f_user.id}</code>\n• <b>Name:</b> {hesc(f_user.first_name)}", parse_mode=HTML)
            return
        elif hasattr(orig, "chat") and orig.chat:
            f_chat = orig.chat
            await update.message.reply_text(
                f"🆔 <b>Channel mila:</b> {hesc(str(f_chat.title or ''))}\n"
                f"🆔 <b>ID:</b> <code>{f_chat.id}</code>\n\n"
                "👇 Is channel ko kya banayein?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📡 Ye SOURCE banao (isse posts aayengi)", callback_data=f"fc_src:{f_chat.id}")],
                    [InlineKeyboardButton("📑 Ye TARGET banao (yahan posts jayengi)", callback_data=f"fc_tgt:{f_chat.id}")],
                ]),
                parse_mode=HTML,
            )
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

    # ---------- PAYMENT: screenshot aane par strict verify ----------
    if mode and mode.startswith("pay_shot_"):
        plan_key = mode.replace("pay_shot_", "")
        await submit_payment_proof(update, context, uid, plan_key, update.message.photo[-1])
        return

    # UTR ke intezaar me photo aa gayi?
    if mode and mode.startswith("pay_utr_"):
        plan_key = mode.replace("pay_utr_", "")
        await update.message.reply_text(
            "📝 <b>Pehle UTR bhejo</b> (text me), screenshot uske baad.\n\n"
            "Payment app kholo → transaction details → <b>UTR / Ref No</b> (12 digit) copy karke yahan bhejo.\n"
            "❓ Pata nahi kahan milega? Neeche button dabao.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❓ UTR kahan milega?", callback_data="pay_utr_help")]]),
            parse_mode=HTML)
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

    # Document PDF Compressor (size option + grayscale)
    if mode == "doc_compress":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        pages = context.user_data.setdefault("doc_pages", [])
        pages.append(buf.getvalue())

        rows = [
            [InlineKeyboardButton("🟢 100 KB (sabse chhota)", callback_data="doc_kb_100"),
             InlineKeyboardButton("🔵 200 KB", callback_data="doc_kb_200")],
            [InlineKeyboardButton("🟣 300 KB (safe)", callback_data="doc_kb_300"),
             InlineKeyboardButton("🟠 500 KB (best quality)", callback_data="doc_kb_500")],
            [InlineKeyboardButton("⚫ Black & White (aur chhota)", callback_data="doc_gray")],
            [InlineKeyboardButton(f"✅ {len(pages)} photo se PDF banao", callback_data="doc_go")],
        ]
        await update.message.reply_text(
            f"📄 <b>{to_bold('DOCUMENT PDF COMPRESS')}</b>\n\n"
            f"📸 {len(pages)} photo mili (marksheet/certificate). Aur bhej sakte ho ya size choose karo 👇\n\n"
            "💡 <b>Size guide:</b> Govt portals usually 100-300 KB maangte hain.",
            reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        return

    # Image to PDF
    if mode == "pdf":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        pages = context.user_data.setdefault("pdf_pages", [])
        pages.append(buf.getvalue())
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Normal PDF ({len(pages)} photos)", callback_data="make_pdf_now"),
             InlineKeyboardButton("📄 A4 Print PDF", callback_data="make_pdf_a4")],
        ])
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
    if q.data in ("make_pdf_now", "make_pdf_a4"):
        pages = context.user_data.get("pdf_pages", [])
        if not pages:
            await q.answer("Pehle photo bhejein!", show_alert=True)
            return
        a4 = (q.data == "make_pdf_a4")
        await q.answer("A4 PDF ban raha hai..." if a4 else "PDF ban raha hai...")
        pdf_bytes = pages_to_pdf(pages, a4=a4)
        buf = io.BytesIO(pdf_bytes)
        buf.name = "UtilityDuniya_A4_Document.pdf" if a4 else "UtilityDuniya_Document.pdf"
        await q.message.reply_document(
            document=buf,
            caption=(f"📄 <b>{to_bold('A4 PRINT-READY PDF')}</b>\n"
                     f"• {len(pages)} pages • A4 size (print par kat nahi aayega) ✅\n"
                     f"• Printer me seedha print kar sakte hain" if a4 else
                     f"📄 <b>{to_bold('MULTI-PAGE PDF READY')} ({len(pages)} pages)!</b>"),
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
    app.add_handler(CommandHandler(["tutorial", "madad", "guide"], lambda u, c: u.message.reply_text(TUTORIAL_TEXT, parse_mode=HTML)))
    app.add_handler(CommandHandler("account", cmd_account))
    app.add_handler(CommandHandler("refer", cmd_refer))
    app.add_handler(CommandHandler("premium", cmd_premium))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler(["payments", "pending"], cmd_payments))
    app.add_handler(CommandHandler("mypay", cmd_mypay))
    app.add_handler(CommandHandler("revoke", cmd_revoke))
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
    app.add_handler(CallbackQueryHandler(on_pdf_cb, pattern="^(make_pdf_now|make_pdf_a4)$"))
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
