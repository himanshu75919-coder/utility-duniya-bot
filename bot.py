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
import io
import json
import logging
import os
import re
import socket
import tempfile
import time
import threading
from datetime import date, datetime
from html import escape as hesc
from urllib.parse import quote

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
    CREDITS_START,
    add_credits,
    credits_stats,
    get_credits,

    spend_credits,
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

    add_use,
    all_user_ids,

    find_by_username,
    get_cloner_config,
    get_user,
    get_user_row,
    grant_premium,
    is_banned,
    is_premium,
    premium_expiry,

    recent_users,

    save_cloner_config,
    save_username,
    set_ban,
    stats,

    add_vip_grant,
    list_vip_grants,
    meta_get,
    meta_set,
    vip_grants_today,
)
# Full-Auto Channel Cloner helper (import guard)
try:
    from database import get_auto_cloners_for_source
except ImportError:  # agar purani database.py use ho rahi ho to bot crash na ho
    def get_auto_cloners_for_source(_source):
        return []

from modules.sarkari_hub import (
    SARKARI_CITIZEN_TEXT,
    STATE_PORTALS_TEXT,
    get_sarkari_citizen_kb,
    get_state_portals_kb,
)
from modules.cyber_studio import (
    compress_document_pdf,
    make_printable_sheet,
    make_stamped_passport,
)
from modules.cloud_tools import resolve_cloud_url
from modules import desi_tools as desi
from modules.desi_tools import (
    KAGAZ_FIELDS,
    KAGAZ_MAKERS,

    VOICE_PRESETS,
    convert_land,
    land_text,
    statement_summary_text,
    statement_passwords,
    parse_bank_statement,
    registry_cost,
    registry_text,
)
from modules.tutorial_hub import (

    has_video,
    publish_tutorial,
    strip_tutorial_lines,

    video_caption,
    video_urls,
)
from modules.channel_cloner import (

    clone_messages,
    cloner_summary_text,
    forward_cloned_message,
    get_cloner_settings_kb,
)
from modules.media_downloader import (

    download_video_async,

    is_supported_video_url,
    platform_name,
)
from modules.toolkit_extras import (
    analyze_link,
    expand_url,
    shorten_url,
)
from modules.vehicle_challan import (
    fetch_vehicle_report,
    is_configured as vehicle_api_ready,
    render_report as render_vehicle_report,
    valid_plate as vehicle_plate_ok,
)
from modules import api_hub as hubapi
from modules.render_health import webhook_url_from_env, webhook_url_usable
from modules.imei_lookup import (
    device_title as imei_title,
    fallback_links as imei_fallback_links,  # v49.13: UI se hata (module me info ke liye rakha)
    fetch_imei_details,
    help_card as imei_help_card,
    is_configured as imei_api_ready,
    render_caption as render_imei_caption,
    render_text as render_imei_text,
    specs_filename as imei_specs_filename,
    specs_json_bytes as imei_specs_json,
    validate_imei as imei_validate,
)
from modules.osint_tools import (
    search_by_area_name,
    lookup_ifsc,
    lookup_ip_domain,
    lookup_phone_info,
    lookup_pincode,
    lookup_vehicle_rto,
)
from modules.general_tools import (

    vcard_data,
    wifi_qr_data,

    get_app_store_links,
    make_qr_bytes,

)
from modules.payguard import (
    MAX_BAD_TRIES,
    admin_payment_card,
    analyze_screenshot,
    user_payment_reply,
    utr_help_text,
    validate_utr,
)
from modules.vip_payment import (
    VIP_PLANS,
    generate_plan_payment_qr,

    get_premium_plans_kb,
)

# ---------------- v50: CORE LAYER (cache + rate-limit + safe HTTP) ----------------
from modules.core import check_limit, limiter_stats
from modules.core.cache import TTLCache

# Info-tools ka shared cache (IFSC / pincode / IP / area) — same sawaal par
# API call dobara nahi hoti. 30 min TTL: ye data din bhar change nahi hota.
INFO_CACHE = TTLCache(maxsize=int(os.getenv("INFO_CACHE_SIZE", "4096")),
                      default_ttl=int(os.getenv("INFO_CACHE_TTL", "1800")))

# ---------------------------------------------------------------------------
# v50: PER-TOOL RATE LIMITS
# mode: (max uses, window seconds, tool ka naam jo message me dikhega)
#
# Kyun zaroori tha: pehle koi bhi user kisi bhi tool ko jitna chahe spam kar
# sakta tha. Isse (a) aapki API quota khatam hoti thi, (b) upstream providers
# (razorpay / postalpincode / ip-api / thum.io) aapka server IP block kar dete
# the, (c) Render free plan ka CPU limit hit hota tha → bot sab ke liye slow.
#
# Limits jaan-boojh kar generous hain — normal user kabhi nahi takrayega.
# Override: env me RATE_LIMIT_<MODE>="limit:window" daal do.
TOOL_RATE_LIMITS = {
    # heavy / mehnga (CPU ya bahut API kharcha)
    "insta_dl":    (6,  120, "Video Downloader"),
    "terabox":     (6,  120, "Terabox Downloader"),
    "bankpdf":     (5,  180, "Bank Statement → Excel"),
    "media_ytmp3": (5,  120, "YouTube → MP3"),
    # normal info tools
    "ip":          (15, 60,  "IP / Domain Info"),
    "ifsc":        (15, 60,  "IFSC Info"),
    "pin":         (15, 60,  "Pincode Info"),
    "rto":         (8,  60,  "Vehicle Info"),
    "imei":        (8,  60,  "IMEI Lookup"),
    "numinfo":     (10, 60,  "Number Info"),
    "linkcheck":   (10, 60,  "Link Check"),
    "short":       (10, 60,  "URL Shortener"),
    "appfind":     (15, 60,  "App Finder"),
    # document tools (local CPU)
    "pp_stamp":    (10, 120, "Passport Photo"),
    "print_sheet": (10, 120, "8-in-1 Print Sheet"),
    "doc_compress":(10, 120, "Document PDF"),
    "kagaz":       (15, 120, "Kagaz Suite"),
}

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
# Render ka webhook default overlapping polling instances se Telegram Conflict rokta hai.
WEBHOOK_URL = webhook_url_from_env()
# purana daily-limit constant (v36 tak) — ab credits system hai; sirf backward-compat ke liye rakha hai
FREE_LIMIT = int(os.getenv("FREE_LIMIT", "10") or 10)
SUPPORT_USERNAME = "@Supermannn_x"
REFER_NEED = int(os.getenv("REFER_NEED", "5") or 5)
HTML = "HTML"
BAN_MSG = "🚫 Aapka account ban hai. Admin se baat karo: @Supermannn_x"
BOT_VERSION = "v51.1 Premium Earning"  # v51.1: WEATHER tool bhi permanently delete (total 6) + per-tool removal messages
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


# ============================================================
#  CREDITS SYSTEM (v37 → v51 FULL PREMIUM)
#  • Naye user ko 25 credits — EK BAAR KE (daily reset NAHI)
#  • v51: AB SAARE tools premium hain (1 use = 1 credit)
#  • VIP / Owner / Admin = unlimited (credits nahi lagte)
# ============================================================
PREMIUM_TOOLS = {
    "insta_dl",            # 📥 VIDEO DOWNLOADER
    "numinfo",             # 📱 NUMBER INFO
    "cloner",              # 🔄 CHANNEL CLONER (auto-forward setup)
    # ---- v38 MARU-TOAD PACK (chhupe tools) ----
    "bankpdf",             # 🏦 BANK STATEMENT PDF → EXCEL
    "kagaz",               # 📜 SARKARI KAGAZ SUITE
    "mediastudio",         # ⚡ MEDIA STUDIO (MP3/STATUS/KARAOKE)
    # ---- v40 VEHICLE INFO + CHALLAN (live API) ----
    "rto",                 # 🚗 VEHICLE & CHALLAN REPORT (action key = "rto")
    # ---- v41 IMEI / PHONE DETAILS (live API) ----
    "imei",                # 📲 IMEI & PHONE SPEC CARD
    # ---- v51: baaki saare tools bhi premium (earning model) ----
    "terabox",             # ⚡ TERABOX / CLOUD DOWNLOADER
    "vnum",                # 🌐 VIRTUAL NUMBERS (OTP)
    "pp_stamp",            # 📸 PASSPORT PHOTO (NAME/DOP)
    "print_sheet",         # 🖨️ 8-IN-1 PRINT SHEET
    "doc_compress",        # 📄 DOCUMENT PDF COMPRESS
    "sarkari",             # 🏛️ SARKARI SEVA PORTALS
    "ifsc",                # 🏦 IFSC INFO
    "pin",                 # 📮 PINCODE INFO
    "ip",                  # 🌐 IP / DOMAIN INFO
    "qr",                  # 📷 QR CODE (text/wifi/vcard)
    "short",               # 🔗 URL SHORT
    "linkcheck",           # 🔍 LINK CHECK
    "appfind",             # 📦 APP FINDER
}

PREMIUM_TOOL_NAMES = {
    "insta_dl": "📥 Video Downloader",
    "numinfo": "📱 Number Info",
    "cloner": "🔄 Channel Cloner",
    "bankpdf": "🏦 Bank Statement → Excel",
    "kagaz": "📜 Sarkari Kagaz Suite",
    "mediastudio": "⚡ Media Studio (MP3/Status/Karaoke)",
    "rto": "🚗 Vehicle Info + Challan Report",
    "imei": "📲 IMEI / Phone Details",
    "terabox": "⚡ Terabox / Cloud Downloader",
    "vnum": "🌐 Virtual Numbers (OTP)",
    "pp_stamp": "📸 Passport Photo (Name/DOP)",
    "print_sheet": "🖨️ 8-in-1 Print Sheet",
    "doc_compress": "📄 Document PDF Compress",
    "sarkari": "🏛️ Sarkari Seva Portals",
    "ifsc": "🏦 IFSC Info",
    "pin": "📮 Pincode Info",
    "ip": "🌐 IP / Domain Info",
    "qr": "📷 QR Code",
    "short": "🔗 URL Short",
    "linkcheck": "🔍 Link Check",
    "appfind": "📦 App Finder",
}


def is_premium_tool(action: str) -> bool:
    return action in PREMIUM_TOOLS


def credits_left(u: dict, uid: int = 0) -> int:
    """Bache hue credits (VIP/admin/owner ke liye 999999 = unlimited)."""
    if uid and is_admin(uid):
        return 999999
    if is_premium(u):
        return 999999
    try:
        return get_credits(uid or u.get("user_id", 0))
    except Exception:
        return 0


def credits_line(u: dict, uid: int = 0) -> str:
    """Chhoti line: credits kitne bache hain."""
    left = credits_left(u, uid)
    if left >= 999999:
        return "⚡ <b>Credits:</b> ♾️ Unlimited (VIP)"
    if left <= 0:
        return "⚡ <b>Credits:</b> 0 / %d — <b>khatam!</b> Premium tools ke liye VIP lo: /premium" % CREDITS_START
    return f"⚡ <b>Credits:</b> {left} / {CREDITS_START} (premium tools ke liye)"


def can_use_premium_tool(u: dict, uid: int = 0) -> bool:
    """Premium tool chalane layak hai? (VIP/admin hamesha, baaki credits hone par)"""
    return credits_left(u, uid) > 0


def get_credits_over_text(action: str = "") -> str:
    tool_name = PREMIUM_TOOL_NAMES.get(action, "Ye tool")
    return (
        f"⚡ <b>{to_bold('CREDITS KHATAM')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{tool_name} ek <b>premium tool</b> hai — 1 use = 1 credit.\n"
        f"Aapke <b>{CREDITS_START} free credits khatam ho gaye.</b>\n\n"
        "👑 <b>VIP lene se POORA bot UNLIMITED ho jayega:</b>\n"
        "• 📥 Video Downloader • 📱 Number Info • 🔄 Channel Cloner\n"
        "• 📸 Passport Photo • 🖨️ 8-in-1 Sheet • 📄 Doc PDF • 🏦 IFSC/Pin/IP\n"
        "• 🏦 Bank PDF→Excel • 📜 Kagaz Suite • ⚡ Media Studio\n"
        "• 🚗 Vehicle • 📲 IMEI • 📦 App Finder • aur saare tools\n"
        "• ♾️ 30/60/90/120 din ya LIFETIME — sab plans\n\n"
        f"💎 <b>VIP plans:</b> 30d ₹49 • 60d ₹89 • 90d ₹129 • 120d ₹169 • Lifetime ₹199\n"
        "👇 Neeche se VIP lo, unlimited use karo:"
    )


# ======================================================================
# v49.4: VIP-ONLY MODE — saare tools sirf VIP / premium users ke liye
# ======================================================================
# Aapki marzi: "ab se sirf premium users hi use kar sakte hain."
# PREMIUM_ONLY=off karte hi purana system wapas (free tools + credits).
PREMIUM_ONLY = str(os.getenv("PREMIUM_ONLY", "on")).strip().lower() in ("on", "1", "yes", "true", "haan", "chalu")

VIP_WALL_TEXT = (
    "👑 <b>YE TOOL SIRF VIP MEMBERS KE LIYE HAI</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Aapka account <b>free</b> hai — is liye premium tools band hain.\n\n"
    "💎 <b>VIP lene par aapko milega:</b>\n"
    "• 📥 Video Downloader (Instagram, YouTube, FB, X, TikTok… 20+ sites)\n"
    "• 📱 Number Info + 🚗 Vehicle/Challan + 📲 IMEI full details\n"
    "• 🔄 Channel Cloner (auto-forward) + 🔒 Private Channel Setup\n"
    "• 🏦 Bank PDF → Excel · 📜 Kagaz Suite · ⚡ Media Studio\n"
    "• 📸 Passport Photo · 🖨️ 8-in-1 Sheet · 📄 Doc PDF · 🔍 Link Check\n"
    "• ♾️ <b>Sab kuch unlimited</b> — koi credit, koi limit nahi\n"
    "• ⚡ <b>Sabse fast</b> support + pehle naye tools\n\n"
    "📌 <b>Jaise:</b> ek baar VIP lo → poora bot khul jata hai, koi rok nahi.\n\n"
    "🎁 <i>Free VIP chahiye? %d dost ko bulao (/refer).</i>"
) % REFER_NEED


def vip_wall_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 VIP plan lo (💳 UPI / QR)", callback_data="open_vip_menu")],
        [InlineKeyboardButton("🎁 Refer & Earn — free VIP", callback_data="open_refer_menu")],
        [InlineKeyboardButton("📖 VIP me kya-kya milta hai?", callback_data="toolvid:premium")],
        [InlineKeyboardButton("💬 Support @Supermannn_x", url="https://t.me/Supermannn_x")],
    ])


def vip_ok(uid: int) -> bool:
    """VIP / owner / admin — tool chala sakte hain? (PREMIUM_ONLY=off par sab allowed)."""
    if not PREMIUM_ONLY:
        return True
    if uid and is_admin(uid):
        return True
    try:
        return bool(is_premium(get_user(uid, "")))
    except Exception:
        return False


def has_unlimited(uid: int) -> bool:
    """ASLI premium/owner check — rate-limit aur unlimited-use ke liye.

    ⚠️ `vip_ok()` iske liye use MAT karo: PREMIUM_ONLY=off (normal mode) me
    wo SABKE liye True deta hai, kyunki wo ek *mode gate* hai, premium check nahi.
    Ye function hamesha actual DB status dekhta hai.
    """
    if uid and is_admin(uid):
        return True
    try:
        return bool(is_premium(get_user(uid, "")))
    except Exception:
        return False


# Non-VIP users ke liye ye callbacks khule rehte hain (payment, refer, madad)
VIP_FREE_CB_EXACT = {
    "back_home", "cancel", "open_vip_menu", "mypay_list", "open_refer_menu",
    "pay_utr_help", "premium_plans", "menu_home", "home", "start",
}
VIP_FREE_CB_PREFIX = ("buy_plan_", "toolvid:", "adm", "admin", "ugrant:", "urevoke:", "uban:",
                      "rpay:", "apay:", "askpay:", "vid:", "refer")


def vip_free_cb(data: str) -> bool:
    if data in VIP_FREE_CB_EXACT:
        return True
    return any(str(data).startswith(p) for p in VIP_FREE_CB_PREFIX)


async def send_vip_wall(update: Update, context: ContextTypes.DEFAULT_TYPE = None):
    """VIP wall — jahan se bhi call karo, sahi jagah bhej dega."""
    kb = vip_wall_kb()
    try:
        msg = update.effective_message or (update.callback_query.message if update.callback_query else None)
    except Exception:
        msg = None
    if msg is not None:
        try:
            await msg.reply_text(VIP_WALL_TEXT, reply_markup=kb, parse_mode=HTML)
            return
        except Exception:
            pass
    try:
        tgt = update.effective_chat.id
    except Exception:
        return
    try:
        await context.bot.send_message(tgt, VIP_WALL_TEXT, reply_markup=kb, parse_mode=HTML)
    except Exception:
        pass


async def vip_gate(update: Update) -> bool:
    """True = allowed. False = wall bhej diya (aage kuch mat karo)."""
    try:
        uid = update.effective_user.id
    except Exception:
        return True
    if vip_ok(uid):
        return True
    await send_vip_wall(update, None)
    return False


def clean_err(text: str, limit: int = 200) -> str:
    """Error text ko user-friendly banao — URL/GitHub link/traceback/[youtube] kachra hata do."""
    t = str(text or "")
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"\[\w+\]\s*", "", t)                 # [youtube] [instagram] etc.
    t = re.sub(r"Traceback \(most recent call last\)[\s\S]*", "", t)
    t = re.sub(r"File \"[^\"]+\", line \d+[\s\S]*", "", t)
    t = re.sub(r"(ERROR:|warning:)\s*", "", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t).strip(" .;,-")
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0] + "…"
    return t or "Something went wrong on the server."


def get_limit_exceeded_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 VIP lo (Unlimited)", callback_data="open_vip_menu")],
        [InlineKeyboardButton("🎬 VIP kaise milega? (30 sec video)", callback_data="toolvid:premium")],
        [InlineKeyboardButton("🎁 Refer karo (Free VIP)", callback_data="open_refer_menu"),
         InlineKeyboardButton("💬 Support", url="https://t.me/Supermannn_x")],
    ])


def check_limit_exceeded(u: dict, uid: int = 0) -> bool:
    """Purana naam — ab matlab: 'premium tool ke liye credits nahi bache'.
    Free tools par ab koi limit nahi hai."""
    return not can_use_premium_tool(u, uid)


def get_limit_exceeded_text(action: str = "") -> str:
    return get_credits_over_text(action)


def spend_credit_msg(uid: int, action: str = "") -> str:
    """1 credit kharch hone ke baad chhota note."""
    left = spend_credits(uid, 1)
    name = PREMIUM_TOOL_NAMES.get(action, "Premium tool")
    if left <= 0:
        return (
            f"⚡ <b>1 credit laga</b> — <b>ab 0 credit bacha!</b>\n\n"
            f"{name} ka ye aakhri free use tha.\n"
            "Ab poora bot VIP ke saath unlimited chalega. → /premium"
        )
    if left <= 5:
        return (f"⚡ <b>1 credit laga</b> — bacha: <b>{left}/{CREDITS_START}</b>\n"
                f"<i>Sirf {left} premium use bache hain, uske baad VIP lena padega (/premium)</i>")
    return f"⚡ <b>1 credit laga</b> — bacha: <b>{left}/{CREDITS_START}</b>"


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
        f"💡 <b>Tip:</b> Ek baar dobara try karo. Problem rahe to support pe likho: {SUPPORT_LINK}"
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
    f"🌐 <b>{to_bold('VIRTUAL NUMBERS (OTP)')}</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "OTP ke liye virtual number — 16 desh, 10 service.\n"
    "📌 Jaise: WhatsApp ke liye number chahiye\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "1️⃣ Service chuno → 2️⃣ Country chuno → 3️⃣ Number lo\n"
    "<i>Sirf account verify karne ke liye. Spam nahi.</i>"
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
        InlineKeyboardButton("⏪ Back", callback_data="vnum_open"),
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
    [f"🔄 {to_bold('CHANNEL CLONER')}", f"📥 {to_bold('VIDEO DOWNLOADER')}"],
    [f"📸 {to_bold('PASSPORT PHOTO (NAME/DOP)')}", f"🖨️ {to_bold('8-IN-1 PRINT SHEET')}"],
    [f"📄 {to_bold('DOCUMENT PDF COMPRESS')}", f"🏛️ {to_bold('SARKARI SEVA PORTALS')}"],
    [f"📱 {to_bold('NUMBER INFO')}", f"🏦 {to_bold('IFSC INFO')}"],
    [f"📮 {to_bold('PINCODE INFO')}", f"🌐 {to_bold('IP / DOMAIN INFO')}"],
    [f"📷 {to_bold('QR CODE')}", f"📦 {to_bold('APP FINDER')}"],
    [f"🔗 {to_bold('URL SHORT')}", f"🔍 {to_bold('LINK CHECK')}"],
    [f"🏦 {to_bold('BANK STATEMENT → EXCEL')}", f"📜 {to_bold('SARKARI KAGAZ SUITE')}"],
    [f"⚡ {to_bold('MEDIA STUDIO (MP3/STATUS)')}", f"🚗 {to_bold('VEHICLE INFO + CHALLAN')}"],
    [f"📲 {to_bold('IMEI / PHONE DETAILS')}", f"💎 {to_bold('VIP PREMIUM')}"],
    [f"🎁 {to_bold('REFER & EARN')}", f"👤 {to_bold('MY ACCOUNT')}"],
    [f"❓ {to_bold('HELP / TUTORIAL')}"],
]


def main_keyboard(admin: bool = False):
    rows = [row[:] for row in KB_BTNS]
    if admin:
        rows.append([f"🛠️ {to_bold('ADMIN PANEL')}", f"👑 {to_bold('OWNER MODE')}"])
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t) for t in row] for row in rows],
        resize_keyboard=True,
        input_field_placeholder="Select a tool 👇",
    )


def kb_for(uid: int):
    return main_keyboard(admin=is_admin(uid))


# Exact Action Mapping
BTN_MODE_MAP = {
    "VIRTUAL NUMBERS": "vnum",
    "TERABOX DOWNLOADER": "terabox",
    "CHANNEL CLONER": "cloner",
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
    "IP INFO": "ip",
    "QR (LINK / TEXT)": "qr",
    "QR (WIFI SHARE)": "qr_wifi",
    "QR (CONTACT CARD)": "qr_vcard",
    "SARKARI SEVA PORTALS": "sarkari",
    "RTO VEHICLE INFO": "rto",
    "VEHICLE INFO + CHALLAN": "rto",
    "VEHICLE INFO": "rto",
    "IMEI / PHONE DETAILS": "imei",
    "IMEI INFO": "imei",
    "IMEI LOOKUP": "imei",
    "PHONE INFO (IMEI)": "imei",
    "NUMBER INFO": "numinfo",
    "IFSC INFO": "ifsc",
    "PINCODE INFO": "pin",
    "QR CODE": "qr",
    "URL SHORT": "short",
    "LINK CHECK": "linkcheck",
    "APP FINDER": "appfind",
    "BANK STATEMENT → EXCEL": "bankpdf",
    "BANK STATEMENT TO EXCEL": "bankpdf",
    "BANK STATEMENT - EXCEL": "bankpdf",
    "BANK PDF TO EXCEL": "bankpdf",
    "SARKARI KAGAZ SUITE": "kagaz",
    "KAGAZ SUITE": "kagaz",
    "MEDIA STUDIO (MP3/STATUS)": "mediastudio",
    "MEDIA STUDIO": "mediastudio",
    "MP3 STATUS STUDIO": "mediastudio",
    "VIP PREMIUM": "premium",
    "REFER & EARN": "refer",
    "MY ACCOUNT": "account",
    "HELP / TUTORIAL": "tutorial",
    "MADAD / TUTORIAL": "tutorial",
    "MADAD": "tutorial",
    "HELP / TUTORIAL": "tutorial",
    "ADMIN PANEL": "admin",
    "OWNER MODE": "owner",
}

PROMPTS = {
    "terabox": (
        f"⚡ <b>{to_bold('TERABOX / CLOUD')}</b>\n"
        "Terabox, Mediafire, Drive ya Mega ka link bhejo → seedha download link milega.\n"
        "📌 Jaise: <code>https://terabox.com/s/xxxxx</code>\n"
        "🔗 <b>Ab apna link bhejo:</b>"
    ),
    "insta_dl": (
        f"📥 <b>{to_bold('VIDEO DOWNLOADER')}</b>\n"
        "Instagram, YouTube, Facebook, X, TikTok, Pinterest, Reddit — 20+ sites.\n"
        "📌 Jaise: <code>https://www.instagram.com/reel/xxxxx</code>\n"
        "🔗 <b>Ab video ka link bhejo:</b>"
    ),
    "pp_stamp": (
        f"📸 <b>{to_bold('EXAM PASSPORT PHOTO')}</b>\n"
        "Photo + naam + date → 3.5 × 4.5 cm ready photo.\n"
        "📌 Jaise: photo bhejo, phir <code>Rahul Kumar</code>, phir <code>02-10-2026</code>\n"
        "📸 <b>Ab apni photo bhejo:</b>"
    ),
    "print_sheet": (
        f"🖨️ <b>{to_bold('8-IN-1 PRINT SHEET')}</b>\n"
        "Ek photo → 4×6 inch sheet me 8 copies. Dukaan pe ₹10-20 me print.\n"
        "📌 Jaise: koi bhi passport size photo\n"
        "📸 <b>Ab ek photo bhejo:</b>"
    ),
    "doc_compress": (
        f"📄 <b>{to_bold('DOCUMENT / MARKSHEET PDF')}</b>\n"
        "Marksheet ya certificate ki photo → saaf PDF (100KB-500KB).\n"
        "📌 Jaise: 10th marksheet ki photo\n"
        "📸 <b>Ab marksheet ya certificate ki photo bhejo:</b>"
    ),
    "ip": (
        f"🌐 <b>{to_bold('IP / DOMAIN INFO')}</b>\n"
        "IP ya website ka location, ISP, company sab milega.\n"
        "📌 Jaise: <code>8.8.8.8</code> ya <code>google.com</code>\n"
        "👉 <b>Ab IP ya website ka naam bhejo:</b>"
    ),
    "bankpdf": (
        f"🏦 <b>{to_bold('BANK STATEMENT PDF → EXCEL')}</b>\n"
        "Bank statement ka <b>PDF</b> bhejo (photo nahi) → Excel/CSV table ban jayegi.\n"
        "📌 Jaise: SBI / HDFC / PNB ka statement PDF\n"
        "📄 <b>Ab apna statement PDF bhejo:</b>"
    ),
    "kagaz": (
        f"📜 <b>{to_bold('KAGAZ SUITE (BIHAR/UP)')}</b>\n"
        "Kirayanama, affidavit, notice 138, bayana, loan paper, registry cost, bigha→kattha.\n"
        "⚡ Har document = 1 credit\n"
        "👇 <b>Neeche se apna document chuno:</b>"
    ),
    "mediastudio": (
        f"⚡ <b>{to_bold('MEDIA STUDIO')}</b>\n"
        "YouTube→MP3, status video, ringtone, karaoke, 8D, bass, voice change, trim, compress.\n"
        "👇 <b>Neeche se option chuno:</b>"
    ),
    "rto": (
        f"🚗 <b>{to_bold('VEHICLE / RTO INFO')}</b>\n"
        "Number plate bhejo → state, RTO office + official RC/challan links.\n"
        "📌 Jaise: <code>BR30AR0802</code>\n"
        "🔢 <b>Ab number plate bhejo:</b>"
    ),
    "imei": (
        f"📲 <b>{to_bold('IMEI / PHONE DETAILS')}</b>\n"
        "IMEI bhejo → phone ka naam, photo + poori spec sheet + JSON file.\n"
        "📌 Jaise: <code>353010111111110</code> · IMEI dekhne ke liye <code>*#06#</code> dial karo\n"
        "🔢 <b>Ab 15 digit IMEI bhejo:</b>"
    ),
    "numinfo": (
        f"📱 <b>{to_bold('NUMBER INFO')}</b>\n"
        "Mobile number bhejo → operator, circle aur number ka type.\n"
        "📌 Jaise: <code>9876543210</code>\n"
        "🔢 <b>Ab 10 digit mobile number bhejo:</b>"
    ),
    "ifsc": (
        f"🏦 <b>{to_bold('IFSC BANK BRANCH')}</b>\n"
        "IFSC code bhejo → bank, branch, address, MICR.\n"
        "📌 Jaise: <code>SBIN0000001</code>\n"
        "🔤 <b>Ab IFSC code bhejo:</b>"
    ),
    "pin": (
        f"📮 <b>{to_bold('PINCODE INFO')}</b>\n"
        "Pincode ya area ka naam bhejo → district, state + saare post office.\n"
        "📌 Jaise: <code>800001</code> ya <code>Rajendra Nagar</code>\n"
        "📮 <b>Ab pincode ya area ka naam bhejo:</b>"
    ),
    "qr": (
        f"📷 <b>{to_bold('QR CODE MAKER')}</b>\n"
        "Link ya text bhejo → HD QR code mil jayega.\n"
        "📌 Jaise: <code>https://t.me/utility_duniya_bot</code>\n"
        "🔗 <b>Ab text ya link bhejo:</b>"
    ),
    "short": (
        f"🔗 <b>{to_bold('URL SHORTENER')}</b>\n"
        "Lamba link chhota kar do.\n"
        "📌 Jaise: <code>https://example.com/very/long/path?x=1</code>\n"
        "🔗 <b>Ab lamba link bhejo:</b>"
    ),
    "linkcheck": (
        f"🔍 <b>{to_bold('LINK CHECK')}</b>\n"
        "Link kholne se pehle check karo — nakli hai ya safe.\n"
        "📌 Jaise: <code>http://sbi-kyc-verify.xyz</code>\n"
        "🔍 <b>Ab link bhejo:</b>"
    ),
    "appfind": (
        f"📦 <b>{to_bold('APP FINDER')}</b>\n"
        "App ka naam bhejo → 8 trusted store ke direct link.\n"
        "📌 Jaise: <code>instagram</code>\n"
        "📦 <b>Ab app ka naam bhejo:</b>"
    ),
    "qr_wifi": (
        f"📶 <b>{to_bold('WIFI SHARE QR')}</b>\n"
        "Guest QR scan karega → phone khud WiFi se jud jayega.\n"
        "📌 Jaise: <code>JioFiber_Home</code>\n"
        "📶 <b>Ab WiFi ka naam (SSID) bhejo:</b>"
    ),
    "qr_vcard": (
        f"👤 <b>{to_bold('CONTACT CARD QR')}</b>\n"
        "QR scan karte hi contact save ho jayega.\n"
        "📌 Jaise: <code>Himanshu Kumar</code>\n"
        "👤 <b>Ab apna naam bhejo:</b>"
    ),
}
TUTORIAL_TEXT = (
    f"❓ <b>{to_bold('HELP — HAR TOOL EK LINE ME')}</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "📥 <b>Download:</b>\n"
    "• 📥 VIDEO DOWNLOADER → Insta/YT/FB/X ka link bhejo → video mil jayega\n"
    "• ⚡ TERABOX / CLOUD → Terabox/Drive/MediaFire link bhejo → direct link mil jayega\n"
    "• 🔄 CHANNEL CLONER → Source + Target set karo, FULL AUTO ON karo, posts khud copy honge\n"
    "\n"
    "📄 <b>Document:</b>\n"
    "• 📸 PASSPORT PHOTO → photo + naam + date bhejo → print ready photo\n"
    "• 🖨️ 8-IN-1 SHEET → ek photo bhejo → 8 copies ki sheet\n"
    "• 📄 DOC PDF → marksheet ki photo bhejo → chhoti size ka PDF\n"
    "• 🏦 BANK PDF → EXCEL → statement PDF bhejo → Excel table\n"
    "• 📜 KAGAZ SUITE → kirayanama, affidavit, notice, registry cost\n"
    "\n"
    "🔍 <b>Information:</b>\n"
    "• 📲 IMEI → <code>*#06#</code> se IMEI lo, bhejo → full phone details\n"
    "• 🚗 VEHICLE → number plate bhejo → RTO office + official RC/challan link\n"
    "• 📱 NUMBER INFO → number bhejo → operator + circle\n"
    "• 🏦 IFSC → code bhejo → bank + branch + MICR\n"
    "• 📮 PINCODE → pincode ya area bhejo → district + post office\n"
    "• 🌐 IP / DOMAIN → IP ya website bhejo → location + ISP\n"
    "\n"
    "⚡ <b>Media Studio:</b> YouTube→MP3, status video, ringtone, karaoke, 8D, bass, voice change, trim\n"
    "\n"
    "🧰 <b>Chhote tools:</b> QR code, URL short, link check, app finder\n"
    "\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⌨️ <b>Commands:</b> /start /menu /help /cancel\n"
    "\n"
    "💬 <b>Atak gaye?</b> Har tool ke neeche 🎬 Tutorial Video button hai. Tool band karne ke liye <b>/cancel</b> dabao."
)

# ============================================================
# TUTORIAL SYSTEM (v34): tutorial text ab bot ke andar nahi,
# sirf ek PAGE par — bot me neeche link milta hai.
# ============================================================
TUTORIAL_FALLBACK_URL = (
    os.getenv("TUTORIAL_URL", "").strip()
    or "https://github.com/himanshu75919-coder/utility-duniya-bot/blob/main/TUTORIAL.md"
)


def tutorial_url() -> str:
    """Tutorial page ka link: env TUTORIAL_URL > auto page (telegra.ph) > fallback."""
    env = os.getenv("TUTORIAL_URL", "").strip()
    if env:
        return env
    try:
        saved = meta_get("tutorial_url", "")
        if saved:
            return saved
    except Exception:
        pass
    return TUTORIAL_FALLBACK_URL


async def send_tool_video(bot_obj, chat_id, key: str, answer_cb=None):
    """Tool ka tutorial video bhejta hai (CDN → raw → document → link fallback)."""
    if not has_video(key):
        if answer_cb:
            await answer_cb("Is tool ka video jald aa raha hai!", True)
        return False
    urls = video_urls(key)
    sent = False
    for u in urls:
        try:
            await bot_obj.send_video(
                chat_id=chat_id, video=u, caption=video_caption(key), parse_mode=HTML,
                supports_streaming=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 Watch Again", callback_data=f"toolvid:{key}")],
                ]),
            )
            sent = True
            break
        except Exception:
            continue
    if not sent:
        for u in urls:
            try:
                await bot_obj.send_document(chat_id=chat_id, document=u, caption=video_caption(key), parse_mode=HTML)
                sent = True
                break
            except Exception:
                continue
    if not sent:
        try:
            await bot_obj.send_message(
                chat_id=chat_id,
                text=("⚠️ Video send nahi ho paya. Aap yahan se dekh sakte ho:\n"
                      f'🎬 <a href="{urls[0]}">Tutorial Video (30 sec)</a>\n\n'
                      "<i>Tip: video start hone me 2-3 second lag sakte hain.</i>"),
                parse_mode=HTML)
        except Exception:
            pass
    return sent


def tutorial_kb():
    """MADAD / TUTORIAL ka keyboard — sirf 🎬 videos (koi text tutorial nahi)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Video Downloader", callback_data="toolvid:insta_dl"),
         InlineKeyboardButton("⚡ Terabox", callback_data="toolvid:terabox")],
        [InlineKeyboardButton("🔄 Cloner", callback_data="toolvid:cloner"),
         InlineKeyboardButton("🏦 Bank PDF → Excel", callback_data="toolvid:bankpdf")],
        [InlineKeyboardButton("📜 Kagaz Suite", callback_data="toolvid:kagaz"),
         InlineKeyboardButton("⚡ Media Studio", callback_data="toolvid:mediastudio")],
        [InlineKeyboardButton("💎 How to get VIP?", callback_data="toolvid:premium"),
         InlineKeyboardButton("❓ How to use bot?", callback_data="toolvid:tutorial")],
    ])


def tutorial_footer() -> str:
    """Bot me text tutorial nahi — isliye footer khaali."""
    return ""


def tutorial_link_line() -> str:
    return ""


# MADAD / TUTORIAL — sirf 🎬 video, koi text tutorial nahi
TUTORIAL_NOTICE = (
        "❓ <b>MADAD / TUTORIAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Har tool ke saath <b>🎬 30 second ka video</b> hai.\n"
        "📌 Jaise: 📥 Video Downloader kholo → neeche 🎬 button dabao → video dekh lo\n\n"
        "👇 Ya yahan se seedha tool ka video kholo:"
    )


def tool_tutorial_kb(action: str):
    """Tool ke neeche sirf 🎬 video tutorial (koi text tutorial nahi)."""
    if not has_video(action):
        return None
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Tutorial Video (30 sec) — HIMANSHU", callback_data=f"toolvid:{action}")],
    ])


# Jin tools me aakhir me "bhejo" wali line nahi thi — unke liye ask line
ASK_LINES = {
    "pin": "📮 <b>Ab pincode ya area ka naam bhejo:</b>",
    "qr_wifi": "📶 <b>Ab WiFi ka naam (SSID) bhejo:</b>",
    "qr_vcard": "👤 <b>Ab apna naam bhejo:</b>",
}


KAGAZ_MENU_TEXT = (
    f"📜 <b>{to_bold('DOCUMENT SUITE (BIHAR/UP)')}</b>\n"
    "Kirayanama, affidavit, notice 138, bayana, loan paper, "
    "registry cost, bigha/kattha, GST/PAN check.\n"
    "⚡ Har document = <b>1 credit</b> · ⚠️ Draft notary se check karwa lena\n"
    "👇 <b>Neeche se chuno:</b>"
)

HUB_KEY_MISSING_TEXT = (
    "🔌 <b>API HUB not available</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Ye check aapke API hub se chalta hai — abhi wo band hai.\n\n"
    "<i>Owner:</i> Render → Environment me <code>HUB_API_KEY</code> = <code>Demo</code> "
    "(ya apni key) daalo, aur <code>HUB_ENABLED=on</code> rakho."
)

MEDIA_MENU_TEXT = (
    f"⚡ <b>{to_bold('MEDIA STUDIO')}</b>\n"
    "YouTube→MP3, status video, ringtone, karaoke, 8D, bass, voice change, "
    "trim/compress. <b>No watermark.</b>\n"
    "⚡ Har option = <b>1 credit</b>\n"
    "👇 <b>Neeche se chuno:</b>"
)

CITY_COORDS = {
    "patna": (25.5941, 85.1376), "muzaffarpur": (26.1225, 85.3906), "gaya": (24.7955, 85.0002),
    "bhagalpur": (25.2425, 86.9842), "darbhanga": (26.1542, 85.8918), "purnia": (25.7771, 87.4753),
    "sitamarhi": (26.5921, 85.4835), "chapra": (25.7815, 84.7477), "chhapra": (25.7815, 84.7477),
    "hajipur": (25.6858, 85.2094), "ara": (25.5541, 84.6603), "bihar sharif": (25.1975, 85.5235),
    "motihari": (26.6472, 84.9149), "saharsa": (25.8798, 86.6015), "samastipur": (25.8629, 85.7811),
    "begusarai": (25.4182, 86.1272), "katihar": (25.5548, 87.5586), "munger": (25.3708, 86.4734),
    "nawada": (24.8876, 85.5432), "buxar": (25.5647, 83.9777), "siwan": (26.2196, 84.3561),
    "sasaram": (24.9538, 84.0128), "dehri": (24.9048, 84.1870), "gopalganj": (26.4674, 84.4410),
    "madhepura": (25.9219, 86.7921), "supaul": (26.1223, 86.6016), "araria": (26.1500, 87.5170),
    "kishanganj": (26.0890, 87.9477), "jamui": (24.9204, 86.2244), "lakhisarai": (25.1778, 86.0961),
    "sheikhpura": (25.1399, 85.8407), "arwal": (25.2450, 84.6660), "jehanabad": (25.2132, 84.9894),
    "bhabua": (25.0405, 83.6088), "kaimur": (25.0405, 83.6088), "rohtas": (24.9538, 84.0128),
    "sheohar": (26.5189, 85.2950), "sitamarhi": (26.5921, 85.4835), "madhubani": (26.3530, 86.0722),
    "bettiah": (26.8020, 84.5028), "forbesganj": (26.2900, 87.2600),
    "patna sahib": (25.5941, 85.1376),
    # UP ke aas-paas
    "varanasi": (25.3176, 82.9739), "lucknow": (26.8467, 80.9462), "gorakhpur": (26.7606, 83.3732),
    "kanpur": (26.4499, 80.3319), "allahabad": (25.4358, 81.8463), "prayagraj": (25.4358, 81.8463),
    "azamgarh": (26.0685, 83.1836), "ballia": (25.7585, 84.1488), "ghazipur": (25.5833, 83.5778),
    "deoria": (26.5024, 83.7791), "mirzapur": (25.1337, 82.5644), "jaunpur": (25.7464, 82.6837),
    # bade shehar
    "delhi": (28.6139, 77.2090), "kolkata": (22.5726, 88.3639), "mumbai": (19.0760, 72.8777),
    "ranchi": (23.3441, 85.3096), "jamshedpur": (22.8046, 86.2029), "dhanbad": (23.7957, 86.4304),
    "bengaluru": (12.9716, 77.5946), "hyderabad": (17.3850, 78.4867), "jaipur": (26.9124, 75.7873),
    "bhopal": (23.2599, 77.4126), "noida": (28.5355, 77.3910), "gurgaon": (28.4595, 77.0266),
}


def city_coords(text: str):
    """User ke likhe shehar se coordinates (default Patna)."""
    t = (text or "").lower().strip()
    for name, xy in CITY_COORDS.items():
        if name in t:
            return xy, name.title()
    return (25.5941, 85.1376), "Patna"


def kagaz_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Kirayanama (rent agreement)", callback_data="kagaz_kirayanama"),
         InlineKeyboardButton("⚖️ Affidavit", callback_data="kagaz_affidavit")],
        [InlineKeyboardButton("🚫 Legal Notice 138 (cheque bounce)", callback_data="kagaz_notice138")],
        [InlineKeyboardButton("🤝 Bayana / Pakki Rasid (zameen)", callback_data="kagaz_bayana"),
         InlineKeyboardButton("📝 Rin Shodh (loan paper)", callback_data="kagaz_loan")],
        [InlineKeyboardButton("🧾 Name/Address/Income Affidavit", callback_data="kagaz_nameaff")],
        [InlineKeyboardButton("🏢 GST Number Check karo", callback_data="kagaz_gst"),
         InlineKeyboardButton("🪪 PAN → GST Check", callback_data="kagaz_pan")],
        [InlineKeyboardButton("🧮 Registry ka total kharcha", callback_data="kagaz_registry"),
         InlineKeyboardButton("📐 Bigha/Kattha Converter", callback_data="kagaz_land")],
        [InlineKeyboardButton("🎬 Tutorial Video (30 sec) — HIMANSHU", callback_data="toolvid:kagaz")],
        [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
    ])


def media_menu_kb():
    rows = [
        [InlineKeyboardButton("🎵 YouTube → MP3", callback_data="media_ytmp3")],
        [InlineKeyboardButton("🎬 Status Video (photo+gaana+text)", callback_data="media_status")],
        [InlineKeyboardButton("🎧 Ringtone cutter", callback_data="media_ringtone"),
         InlineKeyboardButton("🎤 Karaoke (gaana hatao)", callback_data="media_karaoke")],
        [InlineKeyboardButton("🔊 8D sound", callback_data="media_8d"),
         InlineKeyboardButton("💥 Bass boost", callback_data="media_bass")],
        [InlineKeyboardButton("🗣️ Voice change", callback_data="media_voice"),
         InlineKeyboardButton("🎼 Video → MP3", callback_data="media_v2mp3")],
        [InlineKeyboardButton("✂️ Video trim", callback_data="media_trim"),
         InlineKeyboardButton("🗜️ Video compress", callback_data="media_compress")],
        [InlineKeyboardButton("🎬 Tutorial Video (30 sec) — HIMANSHU", callback_data="toolvid:mediastudio")],
        [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(rows)


def voice_preset_kb():
    rows = [[InlineKeyboardButton(lbl, callback_data=f"mvoicepk:{k}")] for k, (lbl, _f) in VOICE_PRESETS.items()]
    rows.append([InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)


def kagaz_ask_next(key: str, data: dict, step: int = 0) -> str:
    """Document ke fields ek-ek karke poocho — simple likho."""
    fields = KAGAZ_FIELDS[key]
    if step >= len(fields):
        return ""
    fname, label, hint = fields[step]
    return (f"📜 <b>{to_bold('KAGAZ SUITE')}</b> — {key}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✍️ <b>{label}</b> likho\n"
            f"<i>(jaise: {hint})</i>\n"
            f"🚫 Khaali chhodna hai to <code>skip</code> likho · ❌ Band karne ke liye /cancel\n"
            f"📊 Step {step + 1} / {len(fields)}")


def tool_prompt(action: str) -> str:
    """Tool ka prompt — sirf kaam ki baat + aakhir me ask (koi text tutorial nahi)."""
    body = strip_tutorial_lines(PROMPTS.get(action, "")).strip()
    lines = body.split("\n")
    while lines and (not lines[-1].strip() or set(lines[-1].strip()) <= set("━-— ")):
        lines.pop()
    if action in ASK_LINES and lines:
        tail = " ".join(lines[-2:]).lower()
        if not any(w in tail.lower() for w in ("send", "type", "select", "pick", "tap", "open", "forward", "choose")):
            lines.append("")
            lines.append(ASK_LINES[action])
    return "\n".join(lines)


def publish_tutorial_now(force: bool = False) -> str:
    """Tutorial page banao/update karo (telegra.ph) — link wapas deta hai."""
    try:
        return publish_tutorial(meta_get, meta_set, prompts_map=PROMPTS,
                                short_list=TUTORIAL_TEXT, force=force)
    except Exception as e:
        log.warning("Tutorial page did not publish: %s", e)
        return ""


WELCOME_TEXT = (
    f"⚡ <b>{to_bold('UTILITY DUNIYA SUPER BOT')}</b> ⚡\n"
    "<blockquote>Aapke saare daily kaam ke tools — ek hi jagah 🚀</blockquote>\n\n"
    f"🔥 <b>{to_bold('SABSE ZYADA USE HONE WALE')}:</b>\n"
    f"• 📲 <b>IMEI Details</b> — phone ka naam, photo + full specs\n"
    f"• 📥 <b>Video Downloader</b> — Insta / YouTube / FB / X\n"
    f"• ⚡ <b>Terabox</b> — bina ad ke seedha download\n"
    f"• 📸 <b>Photo &amp; PDF</b> — passport photo, marksheet PDF, 8-in-1 sheet\n"
    f"• 🏦 <b>Info Tools</b> — IFSC, Pincode, IP, Number info\n"
    f"• 📦 <b>App Finder</b> — app ka naam bhejo → official link + size\n\n"
    "👇 <b>Neeche menu se koi bhi tool dabao</b>"
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
                await update.message.reply_text("🎉 Swagat! Referral link se aaye ho — dhanyavaad!")
                if count % REFER_NEED == 0:
                    grant_premium(ref_id, 30)
                    try:
                        await context.bot.send_message(ref_id, f"🎉 Badhai ho! {count} referral poore! 30 din VIP free mil gaya 💎")
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


async def cmd_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/refresh — keyboard/menu dobara set karo (purana menu hatane ke liye)."""
    context.user_data.pop("mode", None)
    await update.message.reply_text(
        "🔄 <b>Menu refresh ho gaya!</b>\n"
        "Purane buttons hata diye gaye hain — ab neeche wala naya menu use karo 👇",
        reply_markup=kb_for(update.effective_user.id), parse_mode=HTML)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Band kar diya! Menu ready hai 👇", reply_markup=kb_for(update.effective_user.id))


async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_ = update.effective_user.id
    u = get_user(uid_, update.effective_user.first_name)
    vip_status = "👑 VIP ACTIVE" if is_premium(u) else ("👑 OWNER/ADMIN" if is_admin(uid_) else "🆓 Free User")
    expiry = premium_expiry(u)
    left = credits_left(u, uid_)
    cred_line = "♾️ Unlimited (VIP)" if left >= 999999 else f"{left} / {CREDITS_START}"
    if left < 999999 and left <= 0:
        cred_line += " — <b>khatam!</b> (premium tools ke liye VIP lo)"
    text = (
        f"👤 <b>{to_bold('MERI ACCOUNT')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Naam:</b> {hesc(u.get('name', 'User'))}\n"
        f"• <b>User ID:</b> <code>{u.get('user_id')}</code>\n"
        f"• <b>Status:</b> {vip_status}\n"
        f"• <b>VIP kab tak:</b> {expiry}\n"
        f"• ⚡ <b>Credits (premium tools ke liye):</b> {cred_line}\n"
        f"• <b>Referrals:</b> {u.get('referrals', 0)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>AB SAARE tools PREMIUM hain</b> — 1 use = 1 credit\n"
        "🎁 <b>Naye user ko 25 free credits</b> (ek baar ke) — unke baad VIP lo\n"
        "👑 <b>VIP = POORA bot UNLIMITED</b> (koi credit nahi, koi limit nahi)\n\n"
        f"🎁 <i>VIP free chahiye? {REFER_NEED} dost ko share karo (/refer) — ya /premium se lo.</i>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 VIP lo / upgrade karo", callback_data="open_vip_menu")],
        [InlineKeyboardButton("🎁 Refer link (free VIP)", callback_data="open_refer_menu")],
    ])
    await update.message.reply_text(text, reply_markup=kb, parse_mode=HTML)


async def cmd_refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{update.effective_user.id}"
    u = get_user(update.effective_user.id)
    text = (
        f"🎁 <b>{to_bold('REFER KARO — VIP FREE LO')}</b>\n\n"
        f"Doston ko bot share karo aur <b>30 din VIP FREE</b> pao!\n\n"
        f"📊 <b>Aapke referrals:</b> {u.get('referrals', 0)}\n"
        f"🎯 <b>Target:</b> har {REFER_NEED} referral = 30 din VIP Free\n\n"
        f"🔗 <b>Aapka invite link:</b>\n<code>{ref_link}</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Telegram pe share karo", url=f"https://t.me/share/url?url={quote(ref_link)}&text={quote('🔥 Utility Duniya Super Bot dekho!')}")],
    ])
    await update.message.reply_text(text, reply_markup=kb, parse_mode=HTML)


# ============================================================
# QUICK VIP ACTIVATE (v34) — dost / direct paisa wale ke liye
#   /admin → plan chuno → /activate <user_id>
# ============================================================
def active_plan_key(uid: int) -> str:
    key = ""
    try:
        key = meta_get(f"active_plan:{uid}", "")
    except Exception:
        pass
    return key if key in VIP_PLANS else "plan_30"


def activate_plan_kb(uid: int):
    cur = active_plan_key(uid)
    rows = []
    for key, pl in VIP_PLANS.items():
        mark = "✅" if key == cur else "🔸"
        rows.append([InlineKeyboardButton(f"{mark} {pl['name']} · ₹{pl['price']}",
                                          callback_data=f"admact_plan:{key}")])
    rows.append([InlineKeyboardButton("📜 Manual VIP diye gaye", callback_data="admgiftlist"),
                 InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def activate_home_text(uid: int) -> str:
    pl = VIP_PLANS[active_plan_key(uid)]
    return (

        "🎁 <b>VIP ACTIVATE (for friends / direct payment)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "If someone paid you <b>directly by cash or UPI</b>, or you want to give <b>free VIP</b> to someone — no proof needed, just activate it.\n"
        f"✅ <b>Selected plan:</b> {pl['name']}\n"
        f"     ₹{pl['price']} · {pl['days']} days\n"
        "<b>How to use:</b>\n"
        "1️⃣ Pick a plan below (30/60/90/120 days or Lifetime)\n"
        "2️⃣ Then type:\n"
        "     <code>/activate 123456789</code> → gives the selected plan\n"
        "     <code>/activate 123456789 90</code> → give a different number of days\n"
        "     <code>/activate @username</code> → @username also works\n\n"
        "ℹ️ The user instantly gets a 'VIP activated' message + the full record is saved."
    )


async def cmd_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/activate <user_id> [days] — give VIP directly without payment (admin only)."""
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    args = [a.strip() for a in (context.args or []) if a.strip()]
    plan_key = active_plan_key(uid)
    plan = VIP_PLANS[plan_key]

    if not args:
        # bina ID: plan chooser
        await update.message.reply_text(activate_home_text(uid), reply_markup=activate_plan_kb(uid), parse_mode=HTML)
        return

    raw_key = args[0]
    key = raw_key.lstrip("@")
    target = None
    if key.isdigit():
        target = int(key)
    else:
        found = find_by_username("@" + key)
        if found:
            try:
                target = int(found[0])
            except Exception:
                target = None
    if not target:
        await update.message.reply_text(
            f"❌ <b>User nahi mila:</b> <code>{hesc(raw_key)}</code>\n\n"
            "• <b>User ID</b> (jaise <code>8607774564</code>) — us bande ne bot kabhi start kiya ho\n"
            "• Ya wahi <b>@username</b> jo usne bot me set kiya hai\n\n"
            "➡️ Aise bhejo: <code>/activate 123456789</code>",
            parse_mode=HTML)
        return

    days = plan["days"]
    if len(args) > 1 and args[1].isdigit():
        days = int(args[1])
    days = max(1, min(days, 99999))
    dur = "👑 LIFETIME VIP" if days >= 9999 else f"{days} days VIP"

    try:
        grant_premium(target, days)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Problem while setting VIP: {hesc(str(e))}", parse_mode=HTML)
        return
    add_vip_grant(target, days, uid, plan_key=plan_key, note="activate (direct/admin)")

    u = get_user(target) or {}
    row = get_user_row(target) or {}
    uname = row.get("name") or u.get("name") or "-"
    exp = "👑 LIFETIME" if str(u.get("premium_until")) == "lifetime" else (premium_expiry(u) or "-")

    await update.message.reply_text(
        "✅ <b>VIP ACTIVATED!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>User:</b> <code>{target}</code> ({hesc(str(uname))[:24]})\n"
        f"👑 <b>VIP:</b> {dur}\n"
        f"📅 <b>Valid till:</b> {exp}\n"
        f"💎 <b>Plan:</b> {plan['name']} · ₹{plan['price']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✉️ User has been notified. Full record is saved in <b>Manual VIP Log</b>.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 VIP hatao", callback_data=f"urevoke:{target}"),
             InlineKeyboardButton("🎁 Plan Badlo", callback_data="admact_home")],
            [InlineKeyboardButton("📜 Manual VIP diye gaye", callback_data="admgiftlist"),
             InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_home")],
        ]),
        parse_mode=HTML)

    try:
        await context.bot.send_message(
            target,
            f"🎉 <b>Congratulations!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>{dur}</b> activated!\n"
            f"📅 Valid till: {exp}\n\n"
            "Ab saare tools <b>unlimited</b> hain 🚀\n"
            "(Ye VIP admin ne diya hai — koi payment nahi lagti.)",
            parse_mode=HTML)
    except Exception:
        pass


async def cmd_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/credits <user_id> [n] — admin: give credits to a user (default 25)."""
    if not is_admin(update.effective_user.id):
        return
    args = [a.strip() for a in (context.args or []) if a.strip()]
    if not args or not args[0].lstrip("-").isdigit():
        st_ = credits_stats()
        await update.message.reply_text(
            "🎟️ <b>CREDITS (for premium tools)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• New user gets: <b>{CREDITS_START}</b> credits (one time, not daily)\n"
            "• Premium: Video Downloader · Number Info · Channel Cloner · Private Setup · "
            "Bank PDF → Excel · Document Suite · Media Studio\n"
            "• All other tools are <b>free</b> (no credits)\n\n"
            "<b>How to use:</b>\n"
            "<code>/credits 123456789</code> → give that user 25 credits\n"
            "<code>/credits 123456789 50</code> → give 50 credits\n"
            "<code>/credits 123456789 0</code> → remove all credits\n\n"
            f"📊 Right now: <b>{st_['with_credits']}</b> users have credits · <b>{st_['out_of_credits']}</b> are finished.",
            parse_mode=HTML)
        return
    target = int(args[0])
    n = int(args[1]) if len(args) > 1 and args[1].lstrip("-").isdigit() else CREDITS_START
    new_val = add_credits(target, n)
    await update.message.reply_text(
        f"✅ <b>Credits added!</b>\n\n🆔 User: <code>{target}</code>\n🎟️ Added: <b>+{n}</b>\n"
        f"💰 Now left: <b>{new_val}</b>\n\n✉️ User has been notified.", parse_mode=HTML)
    try:
        await context.bot.send_message(
            target,
            f"🎁 <b>Great news!</b> You received <b>{n} credits</b> (total: {new_val}).\n"
            "📥 Video Downloader · 📱 Number Info · 🔄 Cloner · 🔒 Private Setup · 🏦 Bank PDF → Excel · "
            "📜 Document Suite · ⚡ Media Studio are now unlocked. 🚀",
            parse_mode=HTML)
    except Exception:
        pass


def _veh_has_rc_data(live: dict) -> bool:
    """Live jawab me asli RC/challan data hai?

    Hub khaali/unknown plate par sirf RTO office info deta hai (koi owner/maker/challan nahi).
    Aisi report par credit nahi katta — purana free RTO card dikha dete hain.
    """
    rc = live.get("rc") or {}
    if any(rc.get(k) for k in ("maker", "model", "owner", "reg_date", "chassis", "engine", "ins_company")):
        return True
    if live.get("challans"):
        return True
    return bool((live.get("summary") or {}).get("count"))


async def cmd_vehstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/vehstatus — admin: check the vehicle API is working (live test on a sample plate)."""
    if not is_admin(update.effective_user.id):
        return
    if not vehicle_api_ready():
        await update.message.reply_text(
            "⚠️ <b>Vehicle API key is not set.</b>\n\nAdd this on Render → Environment:\n"
            "<code>HUB_API_KEY</code> = your hub key  <i>(ek key = vehicle + imei + number + IP + IFSC + GST ...)</i>\n"
            "<code>VEHICLE_API_PARAM</code> = plate field name (default <code>vehicle_number</code>)\n\n"
            "Then redeploy. The 🚗 VEHICLE INFO + CHALLAN tool will show the live report.",
            parse_mode=HTML)
        return
    args = [a.strip() for a in (context.args or []) if a.strip()]
    plate = args[0] if args else "BR30AR0802"
    st = await update.message.reply_text(f"🔎 Testing the API with <code>{plate}</code>…", parse_mode=HTML)
    # v50: to_thread — vehicle API 5-70s leta hai; direct call poora bot freeze kar deta tha
    res = await asyncio.to_thread(fetch_vehicle_report, plate)
    if res.get("ok"):
        await st.edit_text(f"✅ <b>API is working</b> — RC fields: {len(res.get('rc') or {})}, "
                           f"challans: {len(res.get('challans') or [])}\n\n"
                           + render_vehicle_report(res)[:1500], parse_mode=HTML)
    else:
        await st.edit_text(f"❌ <b>API test failed:</b> {hesc(str(res.get('error'))[:200])}\n\n"
                           "Check VEHICLE_API_URL / KEY / PARAM.", parse_mode=HTML)


async def cmd_imeistatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/imeistatus — admin: check the IMEI API is working (live test)."""
    if not is_admin(update.effective_user.id):
        return
    if not imei_api_ready():
        await update.message.reply_text(
            "⚠️ <b>IMEI API is not set.</b>\n\nAdd this on Render → Environment:\n"
            "<code>HUB_API_KEY</code> = your hub key  <i>(ek hi key saare hub tools ke liye)</i>\n"
            "<i>(base set hai: osint-api-hub.onrender.com/api — Demo key chalti hai)</i>",
            parse_mode=HTML)
        return
    args = [a.strip() for a in (context.args or []) if a.strip()]
    ok15, imei_in, imei_e = imei_validate(args[0] if args else "353010111111110")
    if not ok15:
        await update.message.reply_text(f"❌ {imei_e}", parse_mode=HTML)
        return
    st = await update.message.reply_text(f"🔎 Testing the IMEI API with <code>{imei_in}</code>…",
                                         parse_mode=HTML)
    res = fetch_imei_details(imei_in, use_cache=False)
    if res.get("ok"):
        await st.edit_text(
            "✅ <b>IMEI API is working</b>\n"
            f"📲 <b>{hesc(imei_title(res))}</b>\n"
            f"• Brand: {hesc(str(res.get('brand') or '-'))}\n"
            f"• Spec sections: {len(res.get('sections') or [])}\n"
            f"• JSON file: {len(imei_specs_json(res))} bytes · {hesc(imei_specs_filename(res))}\n"
            f"• Photo: {'✅' if res.get('photo') else '❌'}\n\n" +
            hesc(render_imei_text(res))[:900], parse_mode=HTML)
    else:
        await st.edit_text(f"❌ <b>IMEI API test failed:</b> {hesc(str(res.get('error'))[:200])}\n\n"
                           "Check IMEI_API_BASE / IMEI_API_KEY.", parse_mode=HTML)


async def cmd_hubstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/hubstatus — admin: user ke API hub ka status + live test."""
    if not is_admin(update.effective_user.id):
        return
    st = await update.message.reply_text("🔌 <b>API Hub check kar raha hoon…</b>", parse_mode=HTML)
    card = hubapi.status_card()
    if not hubapi.hub_ready():
        await st.edit_text(card, parse_mode=HTML)
        return
    res = await asyncio.to_thread(hubapi.live_test)
    if res.get("ok"):
        await st.edit_text(card + f"\n• Live test: ✅ <b>working</b> ({hesc(str(res.get('say'))[:80])})\n"
                                  "• Ab ye tools hub par chal rahe hain: IP · IFSC · PINCODE · TERABOX · "
                                  "VIDEO DL (X) · KAGAZ (GST/PAN) · "
                                  "VEHICLE · IMEI · NUMBER INFO", parse_mode=HTML)
    else:
        await st.edit_text(card + f"\n• Live test: ❌ {hesc(str(res.get('error'))[:150])}", parse_mode=HTML)


async def cmd_tutrefresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/tutrefresh — rebuild the tutorial page (admin only)."""
    if not is_admin(update.effective_user.id):
        return
    st = await update.message.reply_text("⏳ <b>Building the tutorial page...</b>", parse_mode=HTML)
    try:
        loop = asyncio.get_running_loop()
        url = await loop.run_in_executor(None, publish_tutorial_now, True)
    except Exception:
        url = ""
    if url:
        await st.edit_text(
            "✅ <b>Tutorial page ready!</b>\n\n"
            f"📖 <a href=\"{url}\">{url}</a>\n\n"
            "This link works under every tool and inside the HELP / TUTORIAL button.",
            parse_mode=HTML, disable_web_page_preview=True)
    else:
        await st.edit_text(
            "⚠️ <b>Page could not be created</b> (internet / telegra.ph problem).\n"
            f"Fallback link is working for now:\n{TUTORIAL_FALLBACK_URL}\n\n"
            "You can set <code>TUTORIAL_URL</code> on Render to use your own link.",
            parse_mode=HTML, disable_web_page_preview=True)


async def cmd_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TUTORIAL_NOTICE, reply_markup=tutorial_kb(), parse_mode=HTML)


async def cmd_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        st = payment_stats()
        await update.message.reply_text(
            "👑 <b>Aap is bot ke OWNER / ADMIN ho</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Aapke liye sab kuch <b>unlimited</b> hai — na daily limit, na VIP payment.\n"
            "Aapko premium khareedne ki zaroorat kabhi nahi 😄\n"
            f"💳 <b>Pending payments (to verify):</b> {st['pending']}\n"
            "👉 Payments verify karne ke liye <b>/payments</b> ya <b>/admin</b> kholo.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💳 Pending Payments ({st['pending']})", callback_data="admpay_list")],
                [InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_home")],
            ]),
            parse_mode=HTML,
        )
        return

    text = (
        f"💎 <b>{to_bold('VIP PREMIUM')}</b>\n"
        "<blockquote>Sab kuch unlimited — bina kisi limit ke</blockquote>\n\n"
        f"⚡ <b>{to_bold('VIP ME KYA MILEGA')}:</b>\n"
        "• ♾️ Sab tools unlimited (koi credit nahi)\n"
        "• 📥 Video Downloader unlimited\n"
        "• ⚡ Terabox high-speed stream + direct download\n"
        "• 🔄 Channel Cloner + Auto-Forward\n"
        "• 📲 IMEI / Phone Details unlimited\n"
        "• 🏦 Bank PDF→Excel · 📜 Kagaz Suite · ⚡ Media Studio\n\n"
        f"🎟️ <i>Har naye user ko {CREDITS_START} free credits milte hain "
        "(Video Downloader, Number Info, Cloner, Bank PDF, Kagaz Suite, Media Studio, IMEI). "
        "Baaki saare tools hamesha free hain.</i>\n\n"
        "👉 Plan chuno aur QR code se pay karo:"
    )
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            list(get_premium_plans_kb().inline_keyboard) +
            [[InlineKeyboardButton("🎬 How to get VIP? (30 sec video)", callback_data="toolvid:premium")]]),
        parse_mode=HTML)


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await admin_panel_send(update.message, context, update.effective_user.id)


# ============================================================================
#  v50: SYSTEM HEALTH — admin ko live internal stats
# ============================================================================
_BOOT_TS = time.time()


def _uptime_str() -> str:
    s = int(time.time() - _BOOT_TS)
    d, r = divmod(s, 86400)
    h, r = divmod(r, 3600)
    m, sec = divmod(r, 60)
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m {sec}s"
    if m:
        return f"{m}m {sec}s"
    return f"{sec}s"


def system_stats_text() -> str:
    """Admin ke liye live system report — cache, rate-limit, memory, uptime."""
    import gc

    cs = INFO_CACHE.snapshot()
    ls = limiter_stats()

    # memory (best-effort — Render par /proc available hota hai)
    mem = ""
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    mem = f"{int(line.split()[1]) / 1024:.0f} MB"
                    break
    except Exception:  # noqa: BLE001
        mem = "n/a"

    threads = threading.active_count()
    objs = len(gc.get_objects())

    hit = cs["hit_rate"]
    hit_icon = "🟢" if hit >= 40 else ("🟡" if hit > 0 else "⚪")
    blk = ls["blocked"]
    blk_icon = "🔴" if blk > 50 else ("🟡" if blk > 0 else "🟢")

    return (
        f"📡 <b>{to_bold('SYSTEM HEALTH')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ <b>Uptime:</b> {_uptime_str()}\n"
        f"🧵 <b>Threads:</b> {threads}   |   🧠 <b>RAM:</b> {mem}\n"
        f"📦 <b>Python objects:</b> {objs:,}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗃️ <b>Cache entries:</b> {cs['entries']} / {cs['maxsize']}\n"
        f"   {hit_icon} <b>Hit rate:</b> {hit}%  "
        f"(hits {cs['hits']} · miss {cs['misses']})\n"
        f"   💡 jitna zyada hit, utni kam API call = fast + free\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚦 <b>Rate limiter:</b>\n"
        f"   ✅ allowed: {ls['allowed']:,}   "
        f"{blk_icon} blocked: {blk:,}\n"
        f"   🔑 active users tracked: {ls['active_buckets']}\n"
        f"   ⚙️ default: {ls['default_limit']} req / {ls['default_window']}s\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <b>Mode:</b> {'WEBHOOK' if webhook_url_from_env() else 'POLLING'}\n"
        f"🔌 <b>Premium-only:</b> {'ON' if PREMIUM_ONLY else 'OFF'}\n"
        f"👑 <b>Admins:</b> {len(ADMIN_IDS)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Ye stats live hain — /admin dobara dabao to refresh ho jayenge.</i>"
    )


async def admin_panel_send(message, context, uid: int):
    """Naya advanced admin panel (buttons ke saath)."""
    st = stats()
    ps = payment_stats()
    pend = pending_payments_count()
    text = (
        f"🛠️ <b>{to_bold('ADMIN CONTROL DASHBOARD')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Total Users:</b> {st['total_users']}   |   🟢 <b>Active today:</b> {st['active_today']}\n"
        f"⚡ <b>Uses today:</b> {st['uses_today']}   |   💎 <b>Active VIP:</b> {st['vip_users']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>Pending Payments:</b> {pend}  {'🔴 (to verify!)' if pend else '✅'}\n"
        f"✅ <b>Approved Total:</b> {ps['approved']}   |   ❌ <b>Rejected:</b> {ps['rejected']}\n"
        f"💰 <b>Total Revenue:</b> ₹{ps['revenue']:,}\n"
        f"🎁 <b>Manual VIP given today:</b> {vip_grants_today()}\n"
        f"🎟️ <b>Credits wale users:</b> {credits_stats()['with_credits']} · <b>khatam:</b> {credits_stats()['out_of_credits']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 Neeche menu se koi bhi option chuno:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 Pending Payments ({pend})", callback_data="admpay_list"),
         InlineKeyboardButton("🧾 Payment History", callback_data="admhist")],
        [InlineKeyboardButton("🎁 VIP Activate (friend / direct payment)", callback_data="admact_home")],
        [InlineKeyboardButton("👥 Recent Users", callback_data="admusers"),
         InlineKeyboardButton("🔍 User Search / Give VIP", callback_data="admsearch")],
        [InlineKeyboardButton("🚫 Ban / Unban", callback_data="admbanmenu"),
         InlineKeyboardButton("📢 Broadcast", callback_data="admbcmenu")],
        [InlineKeyboardButton("📜 Manual VIP diye gaye", callback_data="admgiftlist"),
         InlineKeyboardButton("📖 Text tutorial page (admin)", callback_data="admtut")],
        [InlineKeyboardButton("📡 System Health (live)", callback_data="admsys"),
         InlineKeyboardButton("📊 Command List", callback_data="admcmds")],
    ])
    await message.reply_text(text, reply_markup=kb, parse_mode=HTML)


async def cmd_sys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/sys — admin only: live system health (cache / rate-limit / uptime)."""
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(system_stats_text(), parse_mode=HTML)


async def cmd_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/payments — admin only: list of pending payments."""
    if not is_admin(update.effective_user.id):
        return
    pend = pending_payments(10)
    if not pend:
        await update.message.reply_text("✅ <b>No pending payments!</b> All are verified.", parse_mode=HTML)
        return
    await update.message.reply_text(
        f"💳 <b>{to_bold('PENDING PAYMENTS')}</b> ({len(pend)})\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Tap any payment to see the <b>full proof + approve/reject</b> buttons 👇",
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
        [InlineKeyboardButton("✅ Approve 30 days", callback_data=f"apay:{pid}:30"),
         InlineKeyboardButton("✅ Approve 60 days", callback_data=f"apay:{pid}:60")],
        [InlineKeyboardButton("✅ Approve 90 days", callback_data=f"apay:{pid}:90"),
         InlineKeyboardButton("✅ Approve 120 days", callback_data=f"apay:{pid}:120")],
        [InlineKeyboardButton("👑 Approve LIFETIME", callback_data=f"apay:{pid}:9999"),
         InlineKeyboardButton("❌ Reject", callback_data=f"rpay:{pid}")],
        [InlineKeyboardButton("📩 User se dobara poocho", callback_data=f"askpay:{pid}")],
    ])


async def cmd_mypay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User apni payments ka status dekh sakta hai."""
    uid = update.effective_user.id
    rows = user_payments(uid, 5)
    if not rows:
        await update.message.reply_text("📭 No payment sent yet. Tap <b>/premium</b> to get VIP.", parse_mode=HTML)
        return
    icons = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    lines = []
    for r in rows:
        lines.append(f"{icons.get(r.get('status'), '❔')} <b>#{r['id']}</b> · {r.get('plan_name')} · ₹{r.get('amount')} · "
                     f"UTR <code>{r.get('utr_ref')}</code> · <b>{str(r.get('status')).upper()}</b>")
    await update.message.reply_text(
        "🧾 <b>My Payments</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines) +
        "\n━━━━━━━━━━━━━━━━━━━━━━\n⏳ admin is verifying · ✅ VIP active · ❌ rejected",
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
    await update.message.reply_text(f"🚫 VIP removed from user <code>{target}</code>.", parse_mode=HTML)


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
        dur_str = "👑 LIFETIME VIP" if days >= 9999 else f"🌟 {days} Days VIP"
        await update.message.reply_text(
            f"✅ <b>Success!</b> <b>{dur_str}</b> granted to user <code>{target_uid}</code>.",
            parse_mode=HTML,
        )
        try:
            await context.bot.send_message(
                target_uid,
                f"🎉 <b>Congrats!</b> Your <b>{dur_str} Access</b> is active! Now you can use the bot with no daily limit! 💎",
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
        except Exception:
            # v50: message me `<` jaisa character ho to HTML parse fail hota tha —
            # ab plain text me dobara bhejo (user ko message zaroor mile)
            try:
                await context.bot.send_message(u, msg_text)
                success += 1
            except Exception:
                failed += 1
        await asyncio.sleep(0.04)
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

    # ---------- v49.4: VIP-ONLY GATE ----------
    # VIP lene / refer / madad / payment verify wale buttons sabke liye khule hain.
    if PREMIUM_ONLY and not vip_ok(uid) and not vip_free_cb(data):
        try:
            await q.message.edit_text(VIP_WALL_TEXT, reply_markup=vip_wall_kb(), parse_mode=HTML)
        except Exception:
            await q.message.reply_text(VIP_WALL_TEXT, reply_markup=vip_wall_kb(), parse_mode=HTML)
        return

    if data == "back_home":
        await q.message.edit_text(WELCOME_TEXT, reply_markup=None, parse_mode=HTML)
        return

    # ---------- 🎬 TOOL KA TUTORIAL VIDEO (har tool ka apna video) ----------
    if data.startswith("toolvid:"):
        key = data.split(":", 1)[1]
        if has_video(key):
            await q.answer("🎬 Tutorial video bhej raha hoon (30 sec)...")
        await send_tool_video(context.bot, q.message.chat.id, key, answer_cb=q.answer)
        return

    # Virtual Numbers Funnel
    if data in ("vnum_open", "vnum_back"):
        await q.message.edit_text(VNUM_INTRO, reply_markup=_vnum_intro_kb(), parse_mode=HTML)
        return

    if data == "vnum_get":
        txt = (
            f"📲 <b>{to_bold('STEP 1: SERVICE CHUNO')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Number kis kaam ke liye chahiye? Neeche se chuno 👇"
        )
        await _vnum_say(q, txt, _vnum_svc_kb())
        return

    if data.startswith("vnum_svc:"):
        sl = data.split(":")[1]
        svc_name = dict(VNUM_SERVICES).get(sl, sl.upper())
        context.user_data["vnum_svc"] = svc_name
        txt = (
            f"🌍 <b>{to_bold('STEP 2: DESH CHUNO')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Service: <b>{svc_name}</b>\n\n"
            "Kis desh ka number chahiye? Neeche se chuno 👇"
        )
        await _vnum_say(q, txt, _vnum_ctry_kb())
        return

    if data.startswith("vnum_ctry:"):
        cl = data.split(":")[1]
        ctry_name = dict(VNUM_COUNTRIES).get(cl, cl.upper())
        svc_name = context.user_data.get("vnum_svc", "WhatsApp")
        order_text = f"Hi, I need a Virtual Number:\nService: {svc_name}\nCountry: {ctry_name}"
        contact_url = f"https://t.me/Supermannn_x?text={quote(order_text)}"
        _vnum_note = "" if is_admin(uid) else spend_credit_msg(uid, "vnum")
        card = (
            (f"{_vnum_note}\n" if _vnum_note else "")
            + f"🎯 <b>{to_bold('STEP 3: NUMBER LO')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📲 <b>Service:</b> {svc_name}\n"
            f"🌍 <b>Desh:</b> {ctry_name}\n"
            "⚡ <b>Time:</b> 1-2 minute\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👉 Number lene ke liye neeche <b>Contact Admin</b> dabao:"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Admin se baat karo @Supermannn_x", url=contact_url)],
            [InlineKeyboardButton("🔁 Doosra chuno", callback_data="vnum_get")],
            [InlineKeyboardButton("⌨️ Menu", callback_data="back_home")],
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

    # VIP Buy Handlers
    if data.startswith("buy_plan_"):
        plan_key = data.replace("buy_", "")
        qr_buf, plan_name, amt = generate_plan_payment_qr(UPI_ID, UPI_NAME, plan_key, uid)
        pending_n = len(pending_payments(20))
        if pending_n >= 3:
            mine = [p for p in pending_payments(20) if p.get("user_id") == uid]
            if len(mine) >= 3:
                await q.answer("Aapke 3 payment already pending hain — admin check karega.", show_alert=True)
                return
        context.user_data["mode"] = f"pay_utr_{plan_key}"
        context.user_data["pay_utr_tries"] = 0
        context.user_data["pay_shot_tries"] = 0
        caption = (
            f"💎 <b>{to_bold(plan_name)}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Paisa:</b> ₹{amt}\n"
            f"🏦 <b>UPI ID:</b> <code>{UPI_ID}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📲 <b>Step 1:</b> Ye QR scan karke ₹" f"{amt} pay karo\n"
            "   (PhonePe / GPay / Paytm / BHIM)\n\n"
            "📝 <b>Step 2:</b> Pay karne ke baad <b>UTR / Transaction ID</b> yahan bhejo\n"
            "📸 <b>Step 3:</b> Payment ka <b>screenshot</b> bhejo\n\n"
            "⚠️ <b>Sakht check:</b> UTR sahi hona chahiye aur screenshot asli payment ka "
            "(photo ya meme nahi). Galat proof = VIP nahi."
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
        await q.message.reply_text(
            "💎 Select a plan:",
            reply_markup=InlineKeyboardMarkup(
                list(get_premium_plans_kb().inline_keyboard) +
                [[InlineKeyboardButton("🎬 How to get VIP? (30 sec video)", callback_data="toolvid:premium")]]),
            parse_mode=HTML)
        return

    if data == "open_refer_menu":
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
        await q.message.reply_text(f"🎁 <b>Your Invite Link:</b>\n<code>{ref_link}</code>", parse_mode=HTML)
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
            await q.answer("Admins only.", show_alert=True)
            return
        _, pid_s, days_s = data.split(":")
        pid, days = int(pid_s), int(days_s)
        pay = get_payment(pid)
        if not pay:
            await q.answer("❌ Ye payment record nahi mila.", show_alert=True)
            return
        if pay.get("status") == "approved":
            await q.answer("✅ This payment is already approved!", show_alert=True)
            return
        target_uid = int(pay["user_id"])
        grant_premium(target_uid, days)
        set_payment_status(pid, "approved", reviewer=uid, note=f"{days} days")
        dur = "👑 LIFETIME VIP" if days >= 9999 else f"{days} days VIP"
        ok_edit = await _edit_admin_msg(
            f"✅ <b>APPROVED — Payment #{pid}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> <code>{target_uid}</code>\n"
            f"💰 <b>Amount:</b> ₹{pay.get('amount')}\n"
            f"👑 <b>Given:</b> {dur}\n"
            f"🕒 <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ User has been notified.",
            kb=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💳 Aur Pending ({pending_payments_count()})", callback_data="admpay_list"),
                 InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]))
        await q.answer("✅ VIP activated!")
        try:
            user_obj = get_user(target_uid)
            exp = "👑 LIFETIME" if days >= 9999 else (premium_expiry(user_obj) or "—")
            await context.bot.send_message(
                target_uid,
                "🎉 <b>CONGRATS! VIP IS ACTIVE</b> 💎\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧾 <b>Payment ID:</b> #{pid}\n"
                f"💰 <b>Amount:</b> ₹{pay.get('amount')}\n"
                f"👑 <b>VIP:</b> {dur}\n"
                f"📅 <b>Valid till:</b> {exp}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ Ab saare premium tools <b>unlimited</b> hain — credits khatam "
                "hone ka koi tension nahi.\n\n"
                "🚀 <b>Start:</b> /menu\n"
                "📊 <b>My account:</b> /account\n\n"
                "🙏 Thanks for supporting us!",
                parse_mode=HTML)
        except Exception:
            pass
        if not ok_edit:
            await q.message.reply_text(f"✅ Payment #{pid} approved ({dur}).")
        return

    if data.startswith("rpay:"):
        if not is_admin(uid):
            await q.answer("Admins only.", show_alert=True)
            return
        pid = int(data.split(":")[1])
        pay = get_payment(pid)
        if not pay:
            await q.answer("❌ Record nahi mila.", show_alert=True)
            return
        if pay.get("status") == "approved":
            await q.answer("This payment is approved — it cannot be rejected.", show_alert=True)
            return
        set_payment_status(pid, "rejected", reviewer=uid, note="admin reject")
        await _edit_admin_msg(
            f"❌ <b>REJECTED — Payment #{pid}</b>\n\n"
            f"👤 User: <code>{pay.get('user_id')}</code>\n💰 ₹{pay.get('amount')}\n🧾 UTR: <code>{pay.get('utr_ref')}</code>\n\n"
            "<i>User ko reason ke saath message chala gaya.</i>",
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]))
        await q.answer("Rejected")
        try:
            await context.bot.send_message(
                int(pay["user_id"]),
                f"❌ <b>Payment #{pid} could not be verified</b>\n\n"
                "Possible reasons:\n"
                "• UTR is wrong or already used\n"
                "• Screenshot was unclear or not of a payment\n"
                "• Amount does not match\n\n"
                "🔁 You can send correct proof again: <b>/premium</b>\n"
                "💬 Or talk to Support: @Supermannn_x",
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
            await q.answer("❌ Record nahi mila.", show_alert=True)
            return
        await q.answer("User notified")
        try:
            await context.bot.send_message(
                int(pay["user_id"]),
                f"📩 <b>Admin needs some more details — Payment #{pid}</b>\n\n"
                "Please send these:\n"
                "1️⃣ A <b>clear screenshot</b> of the payment (amount + UTR visible)\n"
                "2️⃣ UTR / Transaction ID <b>as text</b>\n"
                "3️⃣ <b>Time and amount</b> of the transaction\n\n"
                "👉 Send it here directly, the admin will check it.",
                parse_mode=HTML)
        except Exception:
            await q.message.reply_text("⚠️ Could not message the user (maybe they blocked the bot).")
        return

    # ---------- Admin panel ke buttons ----------
    if data == "admin_home":
        if not is_admin(uid):
            await q.answer("Admins only.", show_alert=True)
            return
        await admin_panel_send(q.message, context, uid)
        return

    if data == "admpay_list":
        if not is_admin(uid):
            return
        pend = pending_payments(10)
        if not pend:
            await q.message.reply_text("✅ <b>No pending payments!</b>", parse_mode=HTML)
            return
        await q.message.reply_text(
            f"💳 <b>Pending Payments ({len(pend)})</b>\nPoora proof dekhne + approve/reject karne ke liye tap karo 👇",
            reply_markup=admin_pending_kb(pend), parse_mode=HTML)
        return

    if data == "admact_home":
        if not is_admin(uid):
            return
        await q.message.reply_text(activate_home_text(uid), reply_markup=activate_plan_kb(uid), parse_mode=HTML)
        return

    if data.startswith("admact_plan:"):
        if not is_admin(uid):
            return
        key = data.split(":", 1)[1]
        pl = VIP_PLANS.get(key) or VIP_PLANS["plan_30"]
        meta_set(f"active_plan:{uid}", key)
        await q.answer(f"✅ Plan set: {pl['days']} days")
        await q.message.reply_text(

            f"✅ <b>Plan selected:</b> {pl['name']} ({pl['days']} days)\n"
            f"<code>/activate 123456789</code> → gives that user <b>{pl['days']} days</b> VIP\n"
            "<code>/activate 123456789 90</code> → for a different number of days\n"
            "<code>/activate @username</code> → @username also works\n\n"
            "<i>The user is notified instantly.</i>",
            reply_markup=activate_plan_kb(uid), parse_mode=HTML)
        return

    if data == "admgiftlist":
        if not is_admin(uid):
            return
        rows = list_vip_grants(10)
        if not rows:
            await q.message.reply_text(

                "📜 <b>Manual VIP Log</b>\n"
                "\n"
                "No one has been given direct (no payment) VIP yet.\n"
                "Use <b>/activate</b> to give VIP.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]),
                parse_mode=HTML)
            return
        lines = []
        for r in rows:
            d = int(r.get("days") or 0)
            dur = "LIFETIME" if d >= 9999 else f"{d} days"
            lines.append(f"• <code>{r.get('user_id')}</code> — {dur} · by <code>{r.get('by_admin')}</code> · "
                         f"{str(r.get('created_at') or '')[:16]}")
        await q.message.reply_text(
            f"📜 <b>Manual VIP Log (last {len(rows)})</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines) +
            "\n━━━━━━━━━━━━━━━━━━━━━━\n<i>These are the VIPs you gave with /activate (no payment).</i>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Give VIP", callback_data="admact_home"),
                                                 InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]),
            parse_mode=HTML)
        return

    if data == "admtut":
        if not is_admin(uid):
            return
        await q.answer("Building page...")
        threading.Thread(target=publish_tutorial_now, kwargs={"force": True}, daemon=True).start()
        await q.message.reply_text(
            "📖 <b>Refreshing the tutorial page</b> (10-20 seconds).\n"
            f"🔗 Current link: {tutorial_url()}",
            parse_mode=HTML, disable_web_page_preview=True)
        return

    if data.startswith("vehagain:"):
        plate = data.split(":", 1)[1]
        _u = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u, uid):
            await q.answer("Credits khatam — VIP lo, unlimited checks milenge.", show_alert=True)
            return
        await q.message.reply_text("🔎 <b>Checking live RC + challan record again…</b>", parse_mode=HTML)
        # v50: to_thread — event loop block nahi hoga
        live = await asyncio.to_thread(fetch_vehicle_report, plate)
        if live.get("ok") and not _veh_has_rc_data(live):
            await q.answer("Is number ka RC / challan record nahi mila — koi credit nahi kata.", show_alert=True)
            add_use(uid)
            return
        if live.get("ok"):
            await q.message.reply_text(spend_credit_msg(uid, "vehicle"), parse_mode=HTML)
            rows_live = [
                [InlineKeyboardButton("🔄 Dobara check karo", callback_data=f"vehagain:{live['plate']}")],
            ]
            await q.message.reply_text(render_vehicle_report(live), reply_markup=InlineKeyboardMarkup(rows_live),
                                       parse_mode=HTML)
        else:
            await q.answer(str(live.get("error"))[:180], show_alert=True)
        add_use(uid)
        return

    if data.startswith("imeiagain:"):
        imei = re.sub(r"\D", "", data.split(":", 1)[1])[:15]
        _u_ii = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u_ii, uid):
            await q.answer("Credits khatam — VIP lo, unlimited checks milenge.", show_alert=True)
            return
        await q.message.reply_text("🔎 <b>Checking this IMEI again…</b>", parse_mode=HTML)
        res_ii = await asyncio.to_thread(fetch_imei_details, imei, False)
        if res_ii.get("ok"):
            await q.message.reply_text(spend_credit_msg(uid, "imei"), parse_mode=HTML)
            if res_ii.get("photo") and not str(res_ii["photo"]).lower().endswith(".gif"):
                try:
                    await q.message.reply_photo(photo=res_ii["photo"],
                                                caption=render_imei_caption(res_ii), parse_mode=HTML)
                except Exception:
                    pass
            await q.message.reply_text(render_imei_text(res_ii), parse_mode=HTML,
                                       disable_web_page_preview=True)
        else:
            await q.answer(str(res_ii.get("error"))[:180], show_alert=True)
        add_use(uid)
        return

    if data == "imei_new":
        context.user_data["mode"] = "imei"
        _u_in = get_user(uid, q.from_user.first_name)
        await q.message.reply_text(tool_prompt("imei") + "\n\n" + credits_line(_u_in, uid),
                                   reply_markup=tool_tutorial_kb("imei"), parse_mode=HTML)
        return

    if data.startswith("admpay_view:"):
        if not is_admin(uid):
            return
        pid = int(data.split(":")[1])
        pay = get_payment(pid)
        if not pay:
            await q.answer("❌ Record nahi mila.", show_alert=True)
            return
        card = admin_payment_card(pay, user_row=get_user_row(int(pay["user_id"])),
                                  history=user_payment_history(int(pay["user_id"])))
        await q.message.reply_text(card, reply_markup=admin_payment_kb(pid), parse_mode=HTML)
        await q.answer("Card sent ✅")
        return

    if data == "mypay_list":
        rows = user_payments(uid, 5)
        if not rows:
            await q.message.reply_text("📭 No payment sent yet. Tap <b>/premium</b> to get VIP.", parse_mode=HTML)
            return
        icons = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
        lines = [f"{icons.get(r.get('status'), '❔')} <b>#{r['id']}</b> · {r.get('plan_name')} · ₹{r.get('amount')} · "
                 f"UTR <code>{r.get('utr_ref')}</code> · {str(r.get('status')).upper()}" for r in rows]
        await q.message.reply_text(
            "🧾 <b>My Payments</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines) +
            "\n━━━━━━━━━━━━━━━━━━━━━━\n⏳ = admin is verifying · ✅ = VIP active · ❌ = rejected",
            parse_mode=HTML)
        return

    if data == "admhist":
        if not is_admin(uid):
            return
        rows = recent_payments(10)
        if not rows:
            await q.message.reply_text("No payment records.", parse_mode=HTML)
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

    if data == "admsys":
        if not is_admin(uid):
            return
        await q.message.reply_text(system_stats_text(), parse_mode=HTML)
        return

    if data == "admcmds":
        if not is_admin(uid):
            return
        await q.message.reply_text(

            "📊 <b>Admin Commands</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "• <code>/payments</code> — verify pending payments\n"
            "• <code>/activate [user_id] [days]</code> — give VIP directly (friend / direct payment, no proof)\n"
            "• <code>/credits [user_id] [n]</code> — give credits (default 25)\n"
            "• <code>/grant [user_id] [days]</code> — give VIP (9999 = lifetime)\n"
            "• <code>/revoke [user_id]</code> — remove VIP\n"
            "• <code>/broadcast [message]</code> — message all users\n"
            "• <code>/ban [user_id]</code> / <code>/unban [user_id]</code>\n"
            "• <code>/admin</code> — this panel",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛠️ Panel", callback_data="admin_home")]]),
            parse_mode=HTML)
        return

    if data == "admbcmenu":
        if not is_admin(uid):
            return
        context.user_data["mode"] = "adm_broadcast"
        await q.message.reply_text("📢 <b>Broadcast</b>\n\nType the message you want to send to all users.\n<i>(stop it any time with /cancel)</i>", parse_mode=HTML)
        return

    if data == "admbanmenu":
        if not is_admin(uid):
            return
        context.user_data["mode"] = "adm_ban"
        await q.message.reply_text(
            "🚫 <b>Ban / Unban</b>\n\nType it like this:\n"
            "<code>ban 123456789</code> → ban the user\n<code>unban 123456789</code> → unban the user",
            parse_mode=HTML)
        return

    if data == "admsearch":
        if not is_admin(uid):
            return
        context.user_data["mode"] = "adm_search"
        await q.message.reply_text(
            "🔍 <b>User Search</b>\n\nSend the user's <b>ID</b> or <b>@username</b> — you get full details + buttons to give or remove VIP.",
            parse_mode=HTML)
        return

    if data.startswith("ugrant:"):
        if not is_admin(uid):
            return
        _, t_uid, days = data.split(":")
        t_uid, days = int(t_uid), int(days)
        grant_premium(t_uid, days)
        dur = "👑 LIFETIME VIP" if days >= 9999 else f"{days} days VIP"
        await q.answer(f"✅ {dur} given")
        await q.message.reply_text(f"✅ <b>Done!</b> {dur} given to user <code>{t_uid}</code>.", parse_mode=HTML)
        try:
            await context.bot.send_message(t_uid, f"🎉 <b>The admin gave you {dur}!</b> 💎\n\nNow use all tools unlimited 🚀", parse_mode=HTML)
        except Exception:
            pass
        return

    if data.startswith("urevoke:"):
        if not is_admin(uid):
            return
        t_uid = int(data.split(":")[1])
        revoke_premium(t_uid)
        await q.answer("VIP removed")
        await q.message.reply_text(f"🚫 VIP removed from user <code>{t_uid}</code>.", parse_mode=HTML)
        return

    if data.startswith("uban:"):
        if not is_admin(uid):
            return
        _, t_uid, val = data.split(":")
        set_ban(int(t_uid), int(val))
        await q.answer("Done")
        await q.message.reply_text(("🚫 User banned" if val == "1" else "🟢 User unbanned") + f" — <code>{t_uid}</code>", parse_mode=HTML)
        return

    # ---- PURANE messages ke buttons (backward compatible — pehle jo bheje the wo bhi chalenge) ----
    if data.startswith("adm_appr_") and is_admin(uid):
        parts = data.split("_")
        target_uid = int(parts[2]); days = int(parts[3])
        grant_premium(target_uid, days)
        dur = "👑 LIFETIME VIP" if days >= 9999 else f"{days} days VIP"
        ok_edit = await _edit_admin_msg(f"✅ <b>Approved!</b> {dur} given to user <code>{target_uid}</code>.")
        await q.answer("✅ Done")
        try:
            await context.bot.send_message(target_uid, f"🎉 <b>Congrats!</b> Your payment is approved — {dur} activate! 💎", parse_mode=HTML)
        except Exception:
            pass
        if not ok_edit:
            await q.message.reply_text(f"✅ {dur} given to user {target_uid}.")
        return

    if data.startswith("adm_rej_") and is_admin(uid):
        target_uid = int(data.split("_")[2])
        ok_edit = await _edit_admin_msg(f"❌ <b>Rejected!</b> Payment of user <code>{target_uid}</code> was rejected.")
        await q.answer("Rejected")
        try:
            await context.bot.send_message(target_uid, "❌ Your payment could not be verified. Send it again with a clear screenshot and correct UTR (/premium).")
        except Exception:
            pass
        if not ok_edit:
            await q.message.reply_text(f"❌ Payment of user {target_uid} rejected.")
        return

    # ============ AUTO FORWARD — WIZARD / GUIDE / TEST / STATUS ============
    if data == "cloner_guide":
        await q.message.reply_text(

            "🔄 <b>AUTO FORWARD (CLONER) — 3 STEP</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ <b>SOURCE</b> set karo (jis channel se post copy hogi)\n"
            "2️⃣ <b>TARGET</b> set karo (jis channel me post jayegi — bot wahan admin ho)\n"
            "3️⃣ <b>FULL AUTO ON</b> karo — bas, posts khud copy hone lagengi\n"
            "\n"
            "🎬 Neeche video dekho — 30 second me poora tarika:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Tutorial Video (30 sec) — HIMANSHU", callback_data="toolvid:cloner")],
                [InlineKeyboardButton("🚀 Setup shuru karo", callback_data="cloner_setup")],
                [InlineKeyboardButton("📊 Meri settings", callback_data="cloner_status")],
            ]),
            parse_mode=HTML,
        )
        return

    if data in ("cloner_setup", "cloner_status"):
        _u = get_user(uid)
        if not can_use_premium_tool(_u, uid) and data == "cloner_setup":
            await q.answer("Credits finished — get VIP!", show_alert=True)
            await q.message.reply_text(get_credits_over_text("cloner"),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return

    if data == "cloner_setup":
        cfg = get_cloner_config(uid)
        src_ok = "✅" if cfg.get("source_chat_id") else "1️⃣"
        tgt_ok = "✅" if cfg.get("target_chat_id") else "2️⃣"
        await q.message.reply_text(

            "🚀 <b>AUTO FORWARD SETUP — only 3 steps</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Step 1:</b> SOURCE channel set karo (posts yahan se aayenge)\n"
            "<b>Step 2:</b> TARGET channel set karo (posts yahan jayenge)\n"
            "<b>Step 3:</b> FULL AUTO CHALU karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 Source: <code>{cfg.get('source_chat_id') or '— set nahi'}</code>\n"
            f"📑 Target: <code>{cfg.get('target_chat_id') or '— set nahi'}</code>\n\n"
            "⚠️ <b>Yaad rakho:</b> Bot ko dono channels me <b>Admin</b> banao.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{src_ok} Source set karo", callback_data="cloner_set_source")],
                [InlineKeyboardButton(f"{tgt_ok} Target set karo", callback_data="cloner_set_target")],
                [InlineKeyboardButton("🤖 FULL AUTO CHALU/BAND", callback_data="cloner_toggle_auto")],
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
                [InlineKeyboardButton("🚀 Fix Setup", callback_data="cloner_setup")],
                [InlineKeyboardButton("📘 Guide", callback_data="cloner_guide")],
            ]),
            parse_mode=HTML,
        )
        return

    if data == "cloner_test":
        cfg = get_cloner_config(uid)
        tgt = cfg.get("target_chat_id")
        if not tgt:
            await q.answer("Pehle Target channel set karo!", show_alert=True)
            return
        src = cfg.get("source_chat_id")
        lines = []
        try:
            if src:
                ch = await context.bot.get_chat(src)
                me = await context.bot.get_chat_member(src, context.bot.id)
                lines.append(f"📡 <b>Source:</b> {ch.title or src} — bot admin: {'✅' if me.status in ('administrator','creator') else '❌ Not an ADMIN there'}")
            ch2 = await context.bot.get_chat(tgt)
            me2 = await context.bot.get_chat_member(tgt, context.bot.id)
            admin_ok = me2.status in ("administrator", "creator")
            lines.append(f"📑 <b>Target:</b> {ch2.title or tgt} — bot admin: {'✅' if admin_ok else '❌ Not an ADMIN there'}")
            if admin_ok:
                test_msg = await context.bot.send_message(tgt, "🧪 <b>TEST POST</b>\n\nYe message ToolVault bot ne bheja hai.\nAgar aapko dikh raha hai → aapka <b>target channel sahi chal raha hai ✅</b>\n\n<i>Ye test message 5 second me delete ho jayega.</i>", parse_mode=HTML)
                lines.append("\n✅ <b>Test post target par chala gaya</b> — apna channel check karo!")
                import asyncio as _aio
                async def _del_later():
                    await _aio.sleep(5)
                    try:
                        await context.bot.delete_message(tgt, test_msg.message_id)
                    except Exception:
                        pass
                _aio.create_task(_del_later())
            else:
                lines.append("\n⚠️ Bot ko target channel me <b>Admin</b> banao (Post Messages permission ke saath) — phir dobara test karo.")
        except Exception as e:
            lines.append(f"\n❌ Dikkat: <code>{hesc(str(e))}</code>\n💡 Check karo: source/target username sahi hain? Bot dono me admin hai?")
        await q.message.reply_text("🧪 <b>TEST RESULT</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines), parse_mode=HTML)
        return

    if data.startswith("fc_src:"):
        cid = data.split(":", 1)[1]
        try:
            chat = await context.bot.get_chat(int(cid))
            title = chat.title or str(cid)
        except Exception:
            await q.answer("Bot ko us channel me admin banao, phir dobara try karo", show_alert=True)
            return
        save_cloner_config(uid, source_chat_id=cid)
        context.user_data["mode"] = "cloner_target"
        await q.message.reply_text(
            f"✅ <b>Source set:</b> {hesc(str(title))}\n🆔 <code>{cid}</code>\n\n"
            "👉 Ab <b>TARGET channel</b> bhejo (posts yahan jayenge):\n"
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
            + ("🎉 Dono set ho gaye — ab <b>FULL AUTO CHALU karo</b>!" if ready else "👉 Ab <b>SOURCE</b> channel set karo.")
            ,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 FULL AUTO CHALU karo", callback_data="cloner_toggle_auto")],
                [InlineKeyboardButton("⚙️ Saari Settings", callback_data="cloner_status")],
            ]),
            parse_mode=HTML)
        return

    # ============ NAYE TOOL CALLBACKS ============

    if data in ("bankpdf", "mediastudio"):
        context.user_data.pop("mode", None)
        if data == "mediastudio":
            context.user_data["mode"] = "media_menu"
            await q.message.reply_text(MEDIA_MENU_TEXT, reply_markup=media_menu_kb(), parse_mode=HTML)
            return
        context.user_data["mode"] = data
        _u0 = get_user(uid, q.from_user.first_name)
        if is_premium_tool(data) and not can_use_premium_tool(_u0, uid):
            await q.answer("Credits finished!", show_alert=True)
            await q.message.reply_text(get_credits_over_text(data),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        extra = ""
        if is_premium_tool(data):
            extra = "\n\n" + credits_line(_u0, uid)   # v42: lambi lines nahi — tutorial video samjhata hai
        await q.message.reply_text(tool_prompt(data) + extra, reply_markup=tool_tutorial_kb(data), parse_mode=HTML)
        return

    if data == "kagaz_menu":
        context.user_data["mode"] = "kagaz_menu"
        await q.message.reply_text(KAGAZ_MENU_TEXT, reply_markup=kagaz_menu_kb(), parse_mode=HTML)
        return

    if data.startswith("kagaz_") and data not in ("kagaz_menu",):
        kind = data.replace("kagaz_", "")
        _u_k = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u_k, uid):
            await q.answer("Credits finished!", show_alert=True)
            await q.message.reply_text(get_credits_over_text("kagaz"),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        context.user_data.pop("kagaz_data", None)
        if kind == "registry":
            context.user_data["mode"] = "kagaz_registry_state"
            await q.message.reply_text(
                f"🧮 <b>{to_bold('REGISTRY TOTAL COST')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "First tell the <b>state</b>: <code>Bihar</code> / <code>UP</code> / <code>Jharkhand</code>\n"
                "<i>(Bihar: stamp 6.5% + registration 3% · 1% less for women/joint)</i>", parse_mode=HTML)
            return
        if kind == "land":
            context.user_data["mode"] = "kagaz_land_value"
            await q.message.reply_text(
                f"📐 <b>{to_bold('BIGHA / KATTHA / DHUR CONVERTER')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Type the area — example:\n"
                "• <code>2 bigha</code>\n• <code>5 katha</code>\n• <code>10 decimal</code>\n• <code>1200 sqft</code>\n"
                "• <code>3 dhur</code> / <code>1 acre</code> / <code>2.5 gaj</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📐 <b>Now type your area:</b>", parse_mode=HTML)
            return
        if kind == "gst":
            if not hubapi.hub_ready():
                await q.message.reply_text(HUB_KEY_MISSING_TEXT, parse_mode=HTML)
                return
            context.user_data["mode"] = "kagaz_gst"
            await q.message.reply_text(
                "🏢 <b>GST NUMBER CHECK</b>\n"
                "GSTIN bhejo — legal name, trade name, status, type, state, address.\n"
                "📌 Example: <code>19BOKPS7056D1ZI</code>\n"
                "🔤 <b>Now send the 15 character GSTIN:</b>", parse_mode=HTML)
            return
        if kind == "pan":
            if not hubapi.hub_ready():
                await q.message.reply_text(HUB_KEY_MISSING_TEXT, parse_mode=HTML)
                return
            context.user_data["mode"] = "kagaz_pan"
            await q.message.reply_text(
                "🪪 <b>PAN → GST CHECK</b>\n"
                "PAN bhejo — us PAN par registered saare GST numbers.\n"
                "📌 Example: <code>AAYFK4129N</code>\n"
                "🔤 <b>Now send the 10 character PAN:</b>", parse_mode=HTML)
            return
        if kind not in KAGAZ_FIELDS:
            await q.message.reply_text("❌ Ye document nahi mila.", parse_mode=HTML)
            return
        context.user_data["mode"] = f"kagaz_fill_{kind}"
        context.user_data["kagaz_step"] = 0
        context.user_data["kagaz_data"] = {}
        await q.message.reply_text(kagaz_ask_next(kind, {}, 0), parse_mode=HTML)
        return

    if data.startswith("media_"):
        kind = data.replace("media_", "")
        _u_m = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u_m, uid):
            await q.answer("Credits finished!", show_alert=True)
            await q.message.reply_text(get_credits_over_text("mediastudio"),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        ask = {
            "ytmp3": ("🎵 <b>YOUTUBE → MP3</b>\n\nAb <b>gaane ka YouTube link</b> bhejo:\n<i>(jaise https://youtu.be/xxxx)</i>", "media_ytmp3"),
            "status": ("🎬 <b>STATUS VIDEO MAKER</b>\n\n1️⃣ First <b>send a photo</b> (the status is made on it)", "media_status_photo"),
            "ringtone": ("🎧 <b>RINGTONE CUTTER</b>\n\nSend a song (MP3) or video — I make a 30 second ringtone from it.", "media_ringtone"),
            "karaoke": ("🎤 <b>KARAOKE MAKER</b>\n\nGaana (MP3) ya video bhejo — awaaz hata kar sirf music rakh dunga.", "media_karaoke"),
            "8d": ("🔊 <b>8D SOUND</b>\n\nGaana bhejo — 8D effect laga dunga.", "media_8d"),
            "bass": ("💥 <b>BASS BOOST</b>\n\nGaana bhejo — poori bass, tez awaaz.", "media_bass"),
            "voice": ("🗣️ <b>VOICE CHANGE</b>\n\nVoice note / audio / video bhejo — phir voice chuno.", "media_voice_wait"),
            "v2mp3": ("🎼 <b>VIDEO → MP3</b>\n\nVideo bhejo — uska MP3 bana dunga.", "media_v2mp3"),
            "trim": ("✂️ <b>VIDEO TRIM</b>\n\nVideo bhejo (max 2 minute) — phir time batao (jaise <code>0:10 to 0:45</code>).", "media_trim_wait"),
            "compress": ("🗜️ <b>VIDEO COMPRESS</b>\n\nVideo bhejo (max 2 minute) — size chhota kar dunga (WhatsApp par bhejne layak).", "media_compress_wait"),
        }.get(kind)
        if not ask:
            await q.message.reply_text("❌ Ye option nahi mila.", parse_mode=HTML)
            return
        text, mode = ask
        context.user_data["mode"] = mode
        await q.message.reply_text(text, parse_mode=HTML)
        return

    if data.startswith("mvoicepk:"):
        preset = data.split(":", 1)[1]
        raw = context.user_data.pop("media_audio", None)
        if not raw:
            await q.message.reply_text("⚠️ Send the audio first.")
            return
        await q.message.reply_text("🗣️ Changing the voice... (10-30 seconds)")
        res = desi.voice_change(raw, preset)
        if not res.get("ok"):
            await q.answer("Failed", show_alert=True)
            await q.message.reply_text(f"❌ {res.get('error')}")
            return
        lbl = VOICE_PRESETS[preset][0]
        await q.message.reply_audio(audio=res["bytes"], filename="voice_changed.mp3",
                                    title=f"{lbl} — Utility Duniya", performer="HIMANSHU",
                                    caption=f"🗣️ <b>{lbl}</b> ready!\n{spend_credit_msg(uid, 'mediastudio')}",
                                    parse_mode=HTML)
        return

    if data == "qr_wifi":
        context.user_data["mode"] = "qr_wifi"
        await q.message.reply_text(tool_prompt("qr_wifi"), reply_markup=tool_tutorial_kb("qr_wifi"), parse_mode=HTML)
        return
    if data == "qr_vcard":
        context.user_data["mode"] = "qr_vcard"
        await q.message.reply_text(tool_prompt("qr_vcard"), reply_markup=tool_tutorial_kb("qr_vcard"), parse_mode=HTML)
        return

    if data == "qr_text":
        context.user_data["mode"] = "qr"
        await q.message.reply_text(tool_prompt("qr"), reply_markup=tool_tutorial_kb("qr"), parse_mode=HTML)
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
            await q.answer("Pehle photo bhejo!", show_alert=True)
            return
        kb_target = context.user_data.get("doc_kb", 300)
        gray = context.user_data.get("doc_gray", False)
        await q.answer("Making the PDF...")
        try:
            pdf_buf = compress_document_pdf(pages, kb_target, grayscale=gray)
            pdf_buf.name = f"Document_{kb_target}KB.pdf"
            size_kb = len(pdf_buf.getvalue()) / 1024
            await q.message.reply_document(
                document=pdf_buf,
                caption=(spend_credit_msg(uid, "doc_compress") + "\n" +
                         f"📄 <b>{to_bold('COMPRESSED PDF READY')}</b>\n"
                         f"• {len(pages)} page • {size_kb:.0f} KB • {kb_target} KB limit me ✅\n"
                         f"• Mode: {'⚫ Black & White' if gray else '🌈 Colour'}\n\n"
                         "Ye file government portal par upload kar sakte ho."),
                parse_mode=HTML)
        except Exception as e:
            await q.message.reply_text(f"❌ Could not make the PDF: <code>{hesc(str(e))}</code>", parse_mode=HTML)
        context.user_data.pop("doc_pages", None)
        context.user_data.pop("doc_kb", None)
        context.user_data.pop("doc_gray", None)
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    # v49.15: purane messages ke bache buttons (numrec/nsafe) - chup-chaap band, koi card nahi
    if data.startswith("numrec:") or data.startswith("nsafe:"):
        await q.answer()
        return

    # v51: deleted tools ke purane inline buttons — saaf message, koi crash nahi
    if data in ("shot_hd", "shot_full", "make_pdf_now", "make_pdf_a4", "pdf_clear",
                "cloner_private", "emi_calc", "emi_vyaaj"):
        context.user_data.pop("mode", None)
        context.user_data.pop("pdf_pages", None)
        await q.answer("Ye tool ab nahi hai (remove kar diya gaya).", show_alert=True)
        return

    # Copy buttons (pincode / area results)
    if data.startswith("copy_"):
        await q.answer(f"📋 {data[5:]} — tap to copy", show_alert=True)
        return

    # Advanced Channel Cloner Settings Handlers
    if data == "cloner_set_target":
        context.user_data["mode"] = "cloner_target"
        await q.message.reply_text("📑 <b>TARGET channel set karo:</b>\nUs channel ka username ya ID bhejo jahan post jayegi:\n(jaise: <code>@MyChannel</code> ya <code>-100123456789</code>)\n\n<i>Dhyan: target channel me bot ko Admin banao (Post permission ke saath).</i>", parse_mode=HTML)
        return

    if data == "cloner_set_source":
        context.user_data["mode"] = "cloner_source"
        await q.message.reply_text(
            "📡 <b>SOURCE channel set karo:</b>\nJis channel se post copy karni hai uska username ya ID bhejo:\n"
            "(jaise <code>@MySourceChannel</code> ya <code>-1001234567890</code>)\n\n"
            "<i>Zaroori: us source channel me bhi bot ko ADMIN banao — tabhi nayi posts bot tak pahunchti hain.</i>",
            parse_mode=HTML,
        )
        return

    if data == "cloner_toggle_auto":
        cfg = get_cloner_config(uid)
        if cfg.get("auto_status") == "on":
            save_cloner_config(uid, auto_status="off")
            await q.message.reply_text(
                "🛑 <b>FULL AUTO CLONE OFF!</b>\n\nAb nayi posts apne aap copy nahi hongi. (Manual forward phir bhi chalega.)",
                reply_markup=get_cloner_settings_kb(uid),
                parse_mode=HTML,
            )
            return

        if not cfg.get("target_chat_id"):
            await q.message.reply_text("⚠️ Pehle <b>📑 Target</b> channel set karo (jahan post jayegi).", parse_mode=HTML)
            return
        if not cfg.get("source_chat_id"):
            await q.message.reply_text("⚠️ Pehle <b>📡 Source</b> channel set karo (jahan se post aayegi).", parse_mode=HTML)
            return
        if str(cfg.get("target_chat_id")).strip() == str(cfg.get("source_chat_id")).strip():
            await q.message.reply_text("❌ Source aur Target ek hi nahi ho sakte (post ghoomti rehti rahegi).", parse_mode=HTML)
            return

        _u_c = get_user(uid)
        if not can_use_premium_tool(_u_c, uid):
            await q.answer("Credits finished!", show_alert=True)
            await q.message.reply_text(get_credits_over_text("cloner"),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        save_cloner_config(uid, auto_status="on")
        if credits_left(_u_c, uid) < 999999:
            await q.message.reply_text(spend_credit_msg(uid, "cloner").replace("1 credit used", "FULL AUTO ON — 1 credit used"),
                                       parse_mode=HTML)
        await q.message.reply_text(
            "🤖 <b>FULL AUTO CLONE ON! 🟢</b>\n\n"
            f"📡 Source: <code>{cfg.get('source_chat_id')}</code>\n"
            f"📑 Target: <code>{cfg.get('target_chat_id')}</code>\n\n"

            "Ab source channel ki har <b>nayi post</b> 2-5 second me aapke target channel me copy ho jayegi — caption, tag, watermark, replace/remove words aur thumbnail settings ke saath.\n"
            "<i>Dhyan: sirf NAYI posts copy hoti hain (purani nahi). Rokne ke liye wahi button dobara dabao.</i>",
            reply_markup=get_cloner_settings_kb(uid),
            parse_mode=HTML,
        )
        return

    if data == "cloner_set_tag":
        context.user_data["mode"] = "cloner_tag"
        await q.message.reply_text("🏷️ <b>Rename Tag set karo:</b>\nHar video/post ke title ke aage kaun sa tag lagega?\n(jaise <code>[🔥 4K HD]</code> ya <code>@MyChannel</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_caption":
        context.user_data["mode"] = "cloner_caption"
        await q.message.reply_text("📝 <b>Apna Caption set karo:</b>\nPost me kaun sa caption judega?\n(jaise <code>Roz free updates ke liye @MyChannel join karo!</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_replace":
        context.user_data["mode"] = "cloner_replace"
        await q.message.reply_text("🔄 <b>Replace Words / Links:</b>\nReplace old words with your words (format: <code>OldWord=>NewWord</code>):\n\n(example:\n<code>@old_channel=>@MyChannel\nOldSite.com=>MySite.com</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_remove":
        context.user_data["mode"] = "cloner_remove"
        await q.message.reply_text("🗑️ <b>Words / Promo Links Hatana:</b>\nWo words/links bhejo jo posts se delete karne hain (comma ya new line se):\n(jaise: <code>@spam_bot, join now, https://t.me/fake</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_thumb":
        context.user_data["mode"] = "cloner_thumb"
        await q.message.reply_text("🖼️ <b>Set Custom Thumbnail:</b>\nSend one PHOTO to use on videos and documents:", parse_mode=HTML)
        return

    if data == "cloner_clear_thumb":
        save_cloner_config(uid, thumbnail_file_id="")
        await q.message.reply_text("❌ Custom thumbnail removed!", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    if data == "cloner_set_wm":
        context.user_data["mode"] = "cloner_wm"
        await q.message.reply_text("💧 <b>Watermark set karo:</b>\nPost ke neeche kaun sa text/link dikhega?\n(jaise: <code>⚡ Forwarded by @MyChannel</code>)", parse_mode=HTML)
        return

    if data == "cloner_reset":
        save_cloner_config(uid, target="", caption="", watermark="", rename_tag="", replace_words="", remove_words="", thumbnail_file_id="", source_chat_id="", auto_status="off")
        context.user_data.pop("mode", None)
        await q.message.reply_text("🔄 <b>Settings reset ho gayi!</b> Cloner ki saari settings default par aa gayi.", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    if data == "cloner_start_mode":
        _u_m = get_user(uid)
        if not can_use_premium_tool(_u_m, uid):
            await q.answer("Credits finished!", show_alert=True)
            await q.message.reply_text(get_credits_over_text("cloner"),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        if credits_left(_u_m, uid) < 999999:
            await q.message.reply_text(spend_credit_msg(uid, "cloner").replace("1 credit used", "Fast Forward ON — 1 credit used"),
                                       parse_mode=HTML)
        context.user_data["mode"] = "cloning_active"
        await q.message.reply_text("🚀 <b>Fast Auto-Forward chalu!</b>\n\nAb kisi bhi channel se 10-15 post/video forward karo, ya media seedha bhejo — bot sab kuch 1-2 second me aapke target channel me daal dega!\n\nRokne ke liye /cancel dabao.", parse_mode=HTML)
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

    st = await update.message.reply_text("🔍 Checking the screenshot...")
    try:
        tg_file = await photo_obj.get_file()
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        img_bytes = buf.getvalue()
    except Exception as e:
        await st.edit_text(f"❌ Could not download the screenshot. Please send it again.\n<i>{hesc(str(e))[:90]}</i>", parse_mode=HTML)
        return

    analysis = await asyncio.to_thread(analyze_screenshot, img_bytes, plan["price"])

    # --- strict gate: photo/meme bhejne par reject (3 try tak) ---
    if not analysis["ok"] and analysis["verdict"] == "bad" and tries < MAX_BAD_TRIES:
        context.user_data["pay_shot_tries"] = tries + 1
        await st.edit_text(

            "❌ <b>Ye payment ka screenshot nahi lag raha!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📸 <b>Aise screenshot bhejo:</b>\n"
            "1️⃣ Phone me PhonePe / GPay / Paytm kholo\n"
            "2️⃣ <b>History / Passbook</b> me jao\n"
            "3️⃣ Us payment par tap karo\n"
            "4️⃣ <b>Screenshot</b> lo → yahan bhejo (amount, success aur UTR saaf dikhna chahiye)\n"
            "⚠️ Selfie, photo ya meme proof nahi mane jayenge.\n"
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

            "🚫 <b>Ye screenshot pehle use ho chuka hai!</b>\n"
            "Ek screenshot se sirf ek baar VIP milta hai.\n"
            "📸 Naya payment karo aur us naye payment ka <b>screenshot</b> bhejo.\n"
            "💬 Problem hai? Support: @Supermannn_x",
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
        await st.edit_text("❌ Record save nahi ho paya. Thodi der baad try karo ya Support se baat karo.")
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
        await st.edit_text(f"⚠️ Proof save ho gaya (ID #{pid}) par admin ko bhej nahi paya. Support ko batao: @Supermannn_x")
        return

    context.user_data.pop("mode", None)
    context.user_data.pop("pay_utr", None)
    context.user_data.pop("pay_shot_tries", None)
    context.user_data.pop("pay_utr_tries", None)
    await st.edit_text(
        user_payment_reply(pid, plan["name"], plan["price"], analysis),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 My payments", callback_data="mypay_list")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/Supermannn_x")],
        ]),
        parse_mode=HTML)


# ---------------- TEXT HANDLER ----------------
def kv_row(label, val):
    """Khaali value ho to line skip — GST/PAN card ke liye."""
    return f"• <b>{label}:</b> {hesc(str(val))}\n" if str(val or "").strip() else ""


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

    # ---------- v49.4: VIP-ONLY GATE ----------
    # Payment proof (pay_*) aur admin flows sabke liye khule rehte hain.
    _mode_now = str(context.user_data.get("mode") or "")
    if PREMIUM_ONLY and not vip_ok(uid) and not _mode_now.startswith(("pay_", "adm_")):
        context.user_data.pop("mode", None)
        await send_vip_wall(update, context)
        return

    # Match Action
    action = BTN_MODE_MAP.get(clean_key) or BTN_MODE_MAP.get(norm_text)

    # ---------- v49: purane keyboard ke hata diye gaye buttons ----------
    # Jo users purane menu par hata diye gaye hue tools daba rahe hain —
    # unko saaf message + naya keyboard mil jaye.
    _removed_keys = {
        "CLIP MAKER", "CLIPS MAKER", "VIDEO CLIP MAKER", "CLIPMAKER",
        "LINK BYPASS", "LINKBYPASS", "BYPASS",
        # v51: permanently delete hue tools
        "ID & USERNAME FINDER", "ID FINDER", "USERNAME FINDER",
        "PRIVATE CHANNEL SETUP",
        "IMAGE→PDF", "IMAGE TO PDF", "IMAGE - PDF", "IMAGE TO PDF ",
        "SITE SCREENSHOT", "SITE SCREENSHOT (HD)", "SITE SCREENSHOT (FULL PAGE)", "SCREENSHOT",
        "EMI / INTEREST CALC", "EMI CALC", "EMI CALCULATOR", "EMI / VYAAJ CALC",
        "INTEREST CALC", "INTEREST CALCULATOR", "INTEREST", "VYAAJ CALC",
        # v51.1: weather tool permanently removed
        "WEATHER", "MAUSAM", "WEATHER / MAUSAM", "WEATHER / MAUSAM ",
    }
    if not action and clean_key in _removed_keys:
        _why = {
            "CLIP MAKER": "🎬 Clip Maker",
            "CLIPS MAKER": "🎬 Clip Maker",
            "VIDEO CLIP MAKER": "🎬 Clip Maker",
            "CLIPMAKER": "🎬 Clip Maker",
            "LINK BYPASS": "🔓 Link Bypass",
            "LINKBYPASS": "🔓 Link Bypass",
            "BYPASS": "🔓 Link Bypass",
            "ID & USERNAME FINDER": "🆔 ID & Username Finder",
            "ID FINDER": "🆔 ID Finder",
            "USERNAME FINDER": "🆔 ID & Username Finder",
            "PRIVATE CHANNEL SETUP": "🔒 Private Channel Setup",
            "IMAGE→PDF": "🖼️ Image→PDF",
            "IMAGE TO PDF": "🖼️ Image→PDF",
            "IMAGE - PDF": "🖼️ Image→PDF",
            "SITE SCREENSHOT": "🖼️ Site Screenshot",
            "SITE SCREENSHOT (HD)": "🖼️ Site Screenshot",
            "SITE SCREENSHOT (FULL PAGE)": "🖼️ Site Screenshot",
            "SCREENSHOT": "🖼️ Site Screenshot",
            "EMI / INTEREST CALC": "🧮 EMI / Interest Calc",
            "EMI CALC": "🧮 EMI / Interest Calc",
            "EMI CALCULATOR": "🧮 EMI / Interest Calc",
            "EMI / VYAAJ CALC": "🧮 EMI / Interest Calc",
            "INTEREST CALC": "🧮 EMI / Interest Calc",
            "INTEREST CALCULATOR": "🧮 EMI / Interest Calc",
            "INTEREST": "🧮 EMI / Interest Calc",
            "VYAAJ CALC": "🧮 EMI / Interest Calc",
            "WEATHER": "🌦️ Weather / Mausam",
            "MAUSAM": "🌦️ Weather / Mausam",
            "WEATHER / MAUSAM": "🌦️ Weather / Mausam",
            "WEATHER / MAUSAM ": "🌦️ Weather / Mausam",
        }.get(clean_key, "Ye tool")
        _alt = {
            "CLIP MAKER": "🎬 Clip Maker ki jagah → 📥 <b>Video Downloader</b> / ⚡ <b>Terabox DL</b>",
            "CLIPS MAKER": "🎬 Clip Maker ki jagah → 📥 <b>Video Downloader</b> / ⚡ <b>Terabox DL</b>",
            "VIDEO CLIP MAKER": "🎬 Clip Maker ki jagah → 📥 <b>Video Downloader</b> / ⚡ <b>Terabox DL</b>",
            "CLIPMAKER": "🎬 Clip Maker ki jagah → 📥 <b>Video Downloader</b> / ⚡ <b>Terabox DL</b>",
            "LINK BYPASS": "🔓 Link Bypass ki jagah → 🔍 <b>Link Check</b> / 📥 <b>Video Downloader</b>",
            "LINKBYPASS": "🔓 Link Bypass ki jagah → 🔍 <b>Link Check</b> / 📥 <b>Video Downloader</b>",
            "BYPASS": "🔓 Link Bypass ki jagah → 🔍 <b>Link Check</b> / 📥 <b>Video Downloader</b>",
            "ID & USERNAME FINDER": "🆔 ID Finder ki jagah → 📱 <b>Number Info</b> (legal operator/circle info)",
            "ID FINDER": "🆔 ID Finder ki jagah → 📱 <b>Number Info</b> (legal operator/circle info)",
            "USERNAME FINDER": "🆔 ID Finder ki jagah → 📱 <b>Number Info</b> (legal operator/circle info)",
            "PRIVATE CHANNEL SETUP": "🔒 Private Channel Setup ki jagah → 🔄 <b>Channel Cloner</b>",
            "IMAGE→PDF": "🖼️ Image→PDF ki jagah → 📄 <b>Document PDF</b>",
            "IMAGE TO PDF": "🖼️ Image→PDF ki jagah → 📄 <b>Document PDF</b>",
            "IMAGE - PDF": "🖼️ Image→PDF ki jagah → 📄 <b>Document PDF</b>",
            "SITE SCREENSHOT": "🖼️ Site Screenshot ki jagah → 🔍 <b>Link Check</b> / 🌐 <b>IP / Domain Info</b>",
            "SITE SCREENSHOT (HD)": "🖼️ Site Screenshot ki jagah → 🔍 <b>Link Check</b> / 🌐 <b>IP / Domain Info</b>",
            "SITE SCREENSHOT (FULL PAGE)": "🖼️ Site Screenshot ki jagah → 🔍 <b>Link Check</b> / 🌐 <b>IP / Domain Info</b>",
            "SCREENSHOT": "🖼️ Site Screenshot ki jagah → 🔍 <b>Link Check</b> / 🌐 <b>IP / Domain Info</b>",
            "EMI / INTEREST CALC": "🧮 EMI Calc ki jagah → 📊 aap 🏦 <b>Bank PDF→Excel</b> se khud ka sheet bana sakte ho",
            "EMI CALC": "🧮 EMI Calc ki jagah → 📊 aap 🏦 <b>Bank PDF→Excel</b> se khud ka sheet bana sakte ho",
            "EMI CALCULATOR": "🧮 EMI Calc ki jagah → 📊 aap 🏦 <b>Bank PDF→Excel</b> se khud ka sheet bana sakte ho",
            "EMI / VYAAJ CALC": "🧮 EMI Calc ki jagah → 📊 aap 🏦 <b>Bank PDF→Excel</b> se khud ka sheet bana sakte ho",
            "INTEREST CALC": "🧮 EMI Calc ki jagah → 📊 aap 🏦 <b>Bank PDF→Excel</b> se khud ka sheet bana sakte ho",
            "INTEREST CALCULATOR": "🧮 EMI Calc ki jagah → 📊 aap 🏦 <b>Bank PDF→Excel</b> se khud ka sheet bana sakte ho",
            "INTEREST": "🧮 EMI Calc ki jagah → 📊 aap 🏦 <b>Bank PDF→Excel</b> se khud ka sheet bana sakte ho",
            "VYAAJ CALC": "🧮 EMI Calc ki jagah → 📊 aap 🏦 <b>Bank PDF→Excel</b> se khud ka sheet bana sakte ho",
            "WEATHER": "🌦️ Weather abhi bot me nahi hai — aap 🌐 <b>IP / Domain Info</b> ya 📱 <b>Number Info</b> use kar sakte ho",
            "MAUSAM": "🌦️ Weather abhi bot me nahi hai — aap 🌐 <b>IP / Domain Info</b> ya 📱 <b>Number Info</b> use kar sakte ho",
            "WEATHER / MAUSAM": "🌦️ Weather abhi bot me nahi hai — aap 🌐 <b>IP / Domain Info</b> ya 📱 <b>Number Info</b> use kar sakte ho",
            "WEATHER / MAUSAM ": "🌦️ Weather abhi bot me nahi hai — aap 🌐 <b>IP / Domain Info</b> ya 📱 <b>Number Info</b> use kar sakte ho",
        }.get(clean_key, "Neeche naya menu check karo")
        await update.message.reply_text(
            f"ℹ️ <b>{_why} hata diya gaya hai.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• {_alt}\n\n"
            "👇 Naya menu neeche hai:",
            reply_markup=kb_for(uid), parse_mode=HTML)
        return

    if action:
        # 1. Virtual Numbers Funnel (v51: premium — 1 credit per use)
        if action == "vnum":
            _u_v = get_user(uid, user.first_name)
            if not can_use_premium_tool(_u_v, uid):
                await update.message.reply_text(get_credits_over_text("vnum"),
                                                reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                return
            await update.message.reply_text(credits_line(_u_v, uid), parse_mode=HTML)
            await send_vnum_card(update, context)
            return

        # 3. Channel Cloner Dashboard (premium — 1 credit per FULL AUTO / Fast-Forward)
        if action == "cloner":
            _cfg = get_cloner_config(uid)
            _u_cl = get_user(uid, user.first_name)
            _auto = "🟢 CHALU" if _cfg.get("auto_status") == "on" else "🔴 BAND"
            _cl_note = ""
            if not can_use_premium_tool(_u_cl, uid):
                _cl_note = ("\n⚠️ <b>Credits khatam</b> — FULL AUTO CHALU aur Fast-Forward band hain.\n"
                            "👑 VIP me dono unlimited chalte hain (/premium).\n")
            await update.message.reply_text(
                f"🔄 <b>{to_bold('CHANNEL CLONER & AUTO-FORWARDER')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📡 Source: <code>{_cfg.get('source_chat_id') or 'Set nahi'}</code>\n"
                f"📑 Target: <code>{_cfg.get('target_chat_id') or 'Set nahi'}</code>\n"
                f"🤖 FULL AUTO: <b>{_auto}</b>\n"
                f"{credits_line(_u_cl, uid)}\n"
                "<i>(FULL AUTO CHALU aur Fast-Forward CHALU — dono 1-1 credit lete hain)</i>\n"
                f"{_cl_note}\n"
                "Apne posts ke liye settings badlo 👇",
                reply_markup=get_cloner_settings_kb(uid),
                parse_mode=HTML,
            )
            return

        # 3b. v38: SARKARI KAGAZ SUITE (menu)
        if action == "kagaz":
            context.user_data["mode"] = "kagaz_menu"
            await update.message.reply_text(KAGAZ_MENU_TEXT, reply_markup=kagaz_menu_kb(), parse_mode=HTML)
            return

        # 3c. v38: MEDIA STUDIO (menu)
        if action == "mediastudio":
            context.user_data["mode"] = "media_menu"
            await update.message.reply_text(MEDIA_MENU_TEXT, reply_markup=media_menu_kb(), parse_mode=HTML)
            return

        # 4. Sarkari Portals (v51: premium — 1 credit per use)
        if action == "sarkari":
            _u_s = get_user(uid, user.first_name)
            if not can_use_premium_tool(_u_s, uid):
                await update.message.reply_text(get_credits_over_text("sarkari"),
                                                reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                return
            note = spend_credit_msg(uid, "sarkari")
            await update.message.reply_text(note + "\n" + SARKARI_CITIZEN_TEXT, reply_markup=get_sarkari_citizen_kb(), parse_mode=HTML)
            return

        # 6b. QR Code (4 types) (v51: premium — 1 credit per QR)
        if action == "qr":
            _u_qr = get_user(uid, user.first_name)
            if not can_use_premium_tool(_u_qr, uid):
                await update.message.reply_text(get_credits_over_text("qr"),
                                                reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                return
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 QR of Link / Text", callback_data="qr_text")],
                [InlineKeyboardButton("📶 WiFi Share QR", callback_data="qr_wifi")],
                [InlineKeyboardButton("👤 Contact Card QR", callback_data="qr_vcard")],
                [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
            ])
            await update.message.reply_text(
                f"📷 <b>{to_bold('QR CODE GENERATOR')}</b> — 4 useful QR types\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔗 <b>Link/Text</b> — website, YouTube, any text\n"
                "📶 <b>WiFi</b> — guests scan and connect, no password to tell\n"
                "👤 <b>Contact Card</b> — scan and the contact saves",
                reply_markup=kb, parse_mode=HTML)
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
                await update.message.reply_text("⛔ Admins only.", parse_mode=HTML)
                return
            await admin_panel_send(update.message, context, uid)
            return
        if action == "owner":
            if not is_admin(uid):
                await update.message.reply_text("⛔ Owner only.", parse_mode=HTML)
                return
            await update.message.reply_text(
                f"👑 <b>{to_bold('OWNER MODE')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"

                "You are the owner of this bot — everything is unlimited ✅\n"
                "• No daily limit\n"
                "• No VIP payment\n"
                "• All tools are open\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🛠️ <b>Owner tasks:</b>\n"
                "• Verify payments → <b>/payments</b>\n"
                "• Give / remove VIP → <b>/grant [user_id] [days]</b>\n"
                "• Message all users → <b>/broadcast [message]</b>\n"
                "• Admin panel → <b>/admin</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Pending Payments", callback_data="admpay_list")],
                    [InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_home")],
                ]),
                parse_mode=HTML,
            )
            return
        if action in ("tutorial", "help"):
            await update.message.reply_text(TUTORIAL_NOTICE, reply_markup=tutorial_kb(), parse_mode=HTML)
            return

        # Standard prompt modes
        context.user_data["mode"] = action
        if action in PROMPTS:
            u = get_user(uid, update.effective_user.first_name)
            # SIRF premium tools par credits ka check (baaki saare tools FREE)
            if is_premium_tool(action) and not can_use_premium_tool(u, uid):
                await update.message.reply_text(get_credits_over_text(action),
                                                reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                return
            extra = ""
            if is_premium_tool(action):
                extra = "\n\n" + credits_line(u, uid)   # v42: lambi lines nahi
            await update.message.reply_text(tool_prompt(action) + extra + "\n\n<i>Tap /cancel any time to stop.</i>",
                                            reply_markup=tool_tutorial_kb(action), parse_mode=HTML)
            return

    # Check Active Working Modes
    mode = context.user_data.get("mode")

    # ---------- v50: CENTRAL RATE-LIMIT GATE ----------
    # Ek hi jagah se SAARE tools par limit lagti hai — har tool me alag code
    # likhne ki zaroorat nahi. Admin ko bypass; VIP ko bhi bypass.
    # Sub-steps (jaise "pp_stamp_text") apne parent tool ("pp_stamp") ki limit
    # share karte hain, taaki multi-step tool ek hi use me 5 baar na gina jaye.
    if mode and not is_admin(uid):
        _mstr = str(mode)
        _rl_key = _mstr if _mstr in TOOL_RATE_LIMITS else None
        if _rl_key is None:
            for _k in TOOL_RATE_LIMITS:
                if _mstr.startswith(_k + "_") and (_rl_key is None or len(_k) > len(_rl_key)):
                    _rl_key = _k
        if _rl_key:
            _lim, _win, _tname = TOOL_RATE_LIMITS[_rl_key]
            # NOTE: bypass ke liye has_unlimited() use hota hai, vip_ok() NAHI —
            # vip_ok() PREMIUM_ONLY=off me sabke liye True deta hai, jisse
            # rate-limit kabhi lagta hi nahi.
            _rlmsg = check_limit(uid, _rl_key, limit=_lim, window=_win,
                                 bypass=has_unlimited(uid), tool_name=_tname)
            if _rlmsg:
                await update.message.reply_text(_rlmsg, parse_mode=HTML)
                return

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
                    warn = "\n\n⚠️ <b>Bot wahan ADMIN nahi hai!</b> Us channel me jao aur bot ko Admin banao (Post Messages permission ke saath), warna posting fail hogi."
            except Exception:
                warn = "\n\n⚠️ <i>Admin check fail ho gaya. Ek baar confirm kar lo ki bot wahan admin hai.</i>"
        except Exception:
            warn = "\n\n<i>(Username resolve nahi ho paya — value jaisi hai waisi save kar di. Numeric ID (-100...) zyada safe hai.)</i>"

        save_cloner_config(uid, target=resolved)
        context.user_data.pop("mode", None)
        cfg_now = get_cloner_config(uid)
        ready = bool(cfg_now.get("source_chat_id")) and bool(cfg_now.get("target_chat_id"))
        kb_done = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 FULL AUTO CHALU karo (Step 3)", callback_data="cloner_toggle_auto")],
            [InlineKeyboardButton("🧪 Test Post Bhejo", callback_data="cloner_test")],
            [InlineKeyboardButton("📘 Guide Padho", callback_data="cloner_guide")],
            [InlineKeyboardButton("⚙️ Saari Settings", callback_data="cloner_status")],
        ])
        await update.message.reply_text(
            f"✅ <b>Step 2 done! Target set:</b> <code>{resolved}</code>{warn}\n\n"
            + ("🎉 <b>Both channels are set!</b>\n\n"
               "👉 <b>Step 3:</b> tap <b>FULL AUTO ON</b> below — after that every new post (video, PDF, photo, album) goes to the target automatically."
               if ready else
               "👉 <b>Step 1</b> bhi karo: <b>📡 SOURCE</b> channel bhejo (posts wahan se aayenge).")
            + "\n\n<i>Bot dono channels me Admin hona chahiye.</i>",
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
                    f"✅ <b>Step 1 done! Source set:</b> {hesc(str(title))}\n"
                    f"🆔 <code>{resolved}</code>\n\n"
                    "👉 Now <b>Step 2</b>: send me the <b>TARGET channel</b> (where posts go)"
                )
                if str(get_cloner_config(uid).get("target_chat_id") or "").strip() == resolved:
                    txt += "\n\n⚠️ <b>Note:</b> Source and Target are the same channel — auto clone will not turn on."
            else:
                txt = (
                    f"⚠️ <b>Step 1: Source saved</b> <code>{resolved}</code>\n\n"
                    "❌ But the bot is <b>not ADMIN</b> there! Open that source channel and make the bot <b>Admin</b>.\n"
                    "<i>Otherwise new posts will not reach the bot and auto clone will not work.</i>\n\n"
                    "👉 Also do <b>Step 2</b>: send the TARGET channel (where posts go)"
                )
            context.user_data["mode"] = "cloner_target"
            await update.message.reply_text(txt, reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        except Exception as e:
            await update.message.reply_text(
                f"❌ Channel nahi mila: <code>{hesc(raw_val)}</code>\n<i>{hesc(str(e))[:120]}</i>\n\n"
                "Private channel ke liye numeric ID bhejo (jaise <code>-1001234567890</code>).\n"
                "💡 ID nikalne ka aasan tarika: us channel ki koi ek <b>TEXT post</b> is bot ko forward karo — bot ID bata dega.",
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
                "ya wahi @username jo user ne bot me set kiya hai.", parse_mode=HTML)
            return
        u = get_user(target)
        row = get_user_row(target) or {}
        prem = u.get("premium_until") or ""
        hist = user_payment_history(target)
        await update.message.reply_text(
            f"👤 <b>USER DETAIL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>ID:</b> <code>{target}</code>\n"
            f"👋 <b>Name:</b> {hesc(str(row.get('name') or u.get('name') or '-'))}\n"
            f"👑 <b>VIP:</b> {'👑 LIFETIME' if prem == 'lifetime' else (premium_expiry(u) if prem else '❌ No')}\n"
            f"⚡ <b>Uses today:</b> {u.get('uses_today', 0)}\n"
            f"🎟️ <b>Credits left:</b> {get_credits(target)} / {CREDITS_START}\n"
            f"🚫 <b>Banned:</b> {'Yes' if u.get('banned') else 'No'}\n"
            f"📜 <b>Payments:</b> ✅ {hist['approved']} · ❌ {hist['rejected']} · ⏳ {hist['pending']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 Give 30 days VIP", callback_data=f"ugrant:{target}:30"),
                 InlineKeyboardButton("👑 Give 90 days VIP", callback_data=f"ugrant:{target}:90")],
                [InlineKeyboardButton("👑 Give LIFETIME", callback_data=f"ugrant:{target}:9999"),
                 InlineKeyboardButton("🚫 VIP hatao", callback_data=f"urevoke:{target}")],
                [InlineKeyboardButton("🚫 Ban", callback_data=f"uban:{target}:1"),
                 InlineKeyboardButton("🟢 Unban", callback_data=f"uban:{target}:0")],
            ]),
            parse_mode=HTML)
        return

    if mode == "adm_broadcast":
        context.user_data.pop("mode", None)
        ids = all_user_ids()
        sent = failed = 0
        st = await update.message.reply_text(f"📢 {len(ids)} users...")
        for i in ids:
            try:
                await context.bot.send_message(i, raw_text, parse_mode=HTML)
                sent += 1
            except Exception:
                # v50: HTML parse fail ho to plain text me bhejo
                try:
                    await context.bot.send_message(i, raw_text)
                    sent += 1
                except Exception:
                    failed += 1
            if (sent + failed) % 25 == 0:
                await asyncio.sleep(1)
        await st.edit_text(f"✅ <b>Broadcast done!</b>\n• Sent: {sent}\n• Failed (may have blocked the bot): {failed}", parse_mode=HTML)
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
                f"🟢 <b>Unbanned</b> — <code>{target}</code>\n\n"
                "To ban/unban anyone else, type it the same way: <code>ban 123456</code>",
                parse_mode=HTML)
        else:
            set_ban(target, 1)
            await update.message.reply_text(
                f"🚫 <b>Banned</b> — <code>{target}</code>\n\n"
                "To unban send: <code>unban 123456</code>",
                parse_mode=HTML)
        return

    # (v50: upar wala LIVE admin block ke baad ye poora DUPLICATE block delete kiya —
    #  ye kabhi run hi nahi hota tha, code 70 lines dead tha)

    # ---------- PAYMENT STEP 1: UTR (strict format check) ----------
    if mode and mode.startswith("pay_utr_"):
        plan_key = mode.replace("pay_utr_", "")
        plan = VIP_PLANS.get(plan_key, VIP_PLANS["plan_30"])
        res = validate_utr(raw_text)

        if not res["ok"]:
            tries = context.user_data.get("pay_utr_tries", 0) + 1
            context.user_data["pay_utr_tries"] = tries
            await update.message.reply_text(
                f"❌ <b>Ye UTR sahi nahi hai!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 <b>You sent:</b> <code>{hesc(raw_text[:40])}</code>\n"
                f"⚠️ <b>Reason:</b> {res.get('reason')}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                + utr_help_text() +
                f"\n\n🔁 <b>Ab sahi UTR bhejo</b> ({tries}/5 try)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Plan dobara kholo", callback_data=f"buy_plan_{plan_key}")]]),
                parse_mode=HTML,
            )
            if tries >= 5:
                await update.message.reply_text("😅 Looks like you cannot find the UTR. No problem — talk to Support, they will verify it manually: @Supermannn_x")
                context.user_data.pop("mode", None)
            return

        utr = res["utr"]
        if utr_exists(utr):
            await update.message.reply_text(
                "🚫 <b>This UTR was already used!</b>\n\n"
                f"🧾 <code>{hesc(utr)}</code>\n\n"
                "One UTR gives VIP only <b>once</b>. Make a new payment or send the correct UTR.",
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

            "📸 <b>Step 3:</b> Ab payment ka <b>screenshot</b> bhejo\n"
            "⚠️ <b>Dhyan rakho:</b>\n"
            "• Screenshot me payment <b>success</b> dikhna chahiye (amount + UTR)\n"
            "• Selfie, normal photo ya random image <b>reject</b> ho jayegi\n"
            "• Screenshot <b>jaldi</b> bhejo, warna flow reset ho jata hai",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Plan badlo", callback_data="open_vip_menu")]]),
            parse_mode=HTML,
        )
        return

    # ---------- PAYMENT STEP 3: text bhej diya screenshot ki jagah ----------
    if mode and mode.startswith("pay_shot_"):
        plan_key = mode.replace("pay_shot_", "")
        await update.message.reply_text(

            "📸 <b>Yahan screenshot chahiye (text nahi)!</b>\n"
            "Phone me payment app kholo → us payment ka <b>screenshot</b> lo → yahan bhejo.\n"
            "⚠️ Screenshot me dikhna chahiye: <b>amount, success/paid, aur UTR</b>.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Plan dobara kholo", callback_data=f"buy_plan_{plan_key}")]]),
            parse_mode=HTML)
        return

    # Premium tool ka mode active hai to credit check (free tools par koi rok nahi)
    u = get_user(uid, update.effective_user.first_name)
    if mode and is_premium_tool(mode) and not can_use_premium_tool(u, uid):
        context.user_data.pop("mode", None)
        await update.message.reply_text(get_credits_over_text(mode),
                                        reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
        return

    # Tool Execution Modes
    if mode == "terabox":
        st = await update.message.reply_text("⚡ Resolving the cloud link (6 engines)...")
        res = resolve_cloud_url(raw_text)

        if res.get("ok"):
            files = res.get("files") or []
            if len(files) > 1:
                lines = []
                for idx, f in enumerate(files[:12], 1):
                    lines.append(f"{idx}. <b>{hesc(str(f.get('name'))[:52])}</b> — <code>{f.get('size', 'N/A')}</code>")
                cap = (
                    f"⚡ <b>{to_bold(str(res.get('provider', 'Cloud Direct')))}</b>\n\n"
                    f"📂 <b>{len(files)} file(s) found:</b>\n" + "\n".join(lines) +
                    "\n\n👇 Neeche buttons se koi bhi file download karo:"
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
            await st.edit_text(spend_credit_msg(uid, "terabox") + "\n" + cap, reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            cap = (
                f"⚠️ <b>{to_bold('DIRECT LINK NOT FOUND')}</b>\n\n"
                f"{hesc(str(res.get('error', 'Could not resolve the cloud link.')))}\n\n"
            )
            if res.get("hint"):
                cap += f"💡 <b>Pro Tip:</b> {hesc(str(res['hint']))}\n\n"
            cap += "👇 <b>Try these trusted free downloaders:</b>"
            rows = [[InlineKeyboardButton(nm, url=u)] for nm, u in (res.get("fallback_links") or [])]
            await st.edit_text(cap, reply_markup=InlineKeyboardMarkup(rows[:6]), parse_mode=HTML)
        add_use(uid)
        return

    # UNIVERSAL VIDEO DOWNLOADER (Instagram + YouTube + Facebook + X + TikTok + 20 platforms)
    if mode == "insta_dl":
        if not is_supported_video_url(raw_text):
            await update.message.reply_text(
                fail_msg("UNSUPPORTED LINK",
                         "This link is not supported. Send links from Instagram, YouTube, Facebook, X (Twitter), TikTok, "
                         "Snapchat, Pinterest, Reddit or Vimeo."),
                parse_mode=HTML,
            )
            return

        plat = platform_name(raw_text)
        _u = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u, uid):
            await update.message.reply_text(get_credits_over_text("insta_dl"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        st = await update.message.reply_text(f"📥 {plat} — fetching the media (best quality + full audio)...")
        res = await download_video_async(raw_text)

        if not res.get("ok"):
            reason = str(res.get("error", "Could not extract the media."))
            await st.edit_text(
                fail_msg(f"{plat.upper()} DOWNLOAD FAILED", reason)
                + "\n\n💡 <b>What to do:</b>\n"
                  "• Check if the post is <b>public</b>\n"
                  "• Try again after 30-60 seconds (server rate-limit)\n"
                  "• For Instagram, setting the <code>IG_COOKIES_FILE</code> env makes it 100% reliable\n"
                  "• Or take the direct link with the <b>LINK BYPASS</b> tool",
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
                await update.message.reply_text(spend_credit_msg(uid, "insta_dl"), parse_mode=HTML)
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
                        + (f"• 🎞️ <b>Quality:</b> {hesc(str(res.get('quality')))} (FHD)\n"
                           if res.get("quality") else "")
                        + f"• 🔊 <b>Audio:</b> Original ✅\n"
                          f"• ⚙️ Engine: {engine}"
                    ),
                    parse_mode=HTML,
                    supports_streaming=True,
                )
                await st.delete()
                add_use(uid)
                await update.message.reply_text(spend_credit_msg(uid, "insta_dl"), parse_mode=HTML)
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
                await update.message.reply_text(spend_credit_msg(uid, "insta_dl"), parse_mode=HTML)
                return

            # 4) Bada file (48MB+): direct link dete hain — kaam rukta nahi
            if mtype == "link" and res.get("direct_url"):
                mb = res.get("size_mb") or 0
                rows = [
                    [InlineKeyboardButton("🚀 Direct Download Link", url=res["direct_url"])],
                    [InlineKeyboardButton("🌐 Original page kholo", url=raw_text)],
                ]
                await st.edit_text(
                    f"📥 <b>{to_bold('DOWNLOAD LINK READY')}</b>\n\n"
                    f"🎬 <b>Platform:</b> {plat}\n"
                    + (f"📝 <b>Title:</b> {title}\n" if title else "")
                    + (f"📊 <b>Size:</b> {mb} MB\n" if mb else "")
                    + f"⚙️ Engine: {engine}\n\n"
                    + hesc(str(res.get("note") or ""))
                    + "\n\n👇 Download karne ke liye neeche button par tap karo:",
                    reply_markup=InlineKeyboardMarkup(rows),
                    parse_mode=HTML,
                )
                add_use(uid)
                await update.message.reply_text(spend_credit_msg(uid, "insta_dl"), parse_mode=HTML)
                return

            await st.edit_text(
                fail_msg("SEND FAILED", "Got the media but Telegram did not accept it. Try once more.")
                + "\n\n💡 <b>Tip:</b> big videos par ye kuch baar hota hai. Dobara try karo ya "
                  "<b>✂️ MEDIA STUDIO → Video compress</b> se chhota karke bhejo.",
                parse_mode=HTML)
        except Exception as e:
            # v44: bade video par Telegram timeout → compressed version se dobara koshish
            _raw = res.get("bytes") or b""
            _fixed = False
            if _raw and len(_raw) > 6 * 1048576 and res.get("type") == "video":
                try:
                    await st.edit_text("📦 <b>Telegram took too long.</b> Size chhota karke dobara bhej raha hoon…",
                                       parse_mode=HTML)
                    _c = await asyncio.to_thread(desi.video_compress, _raw, 16.0, ".mp4")
                    if _c.get("ok"):
                        _buf = io.BytesIO(_c["bytes"])
                        _buf.name = f"{platform_name(raw_text).replace(' ', '_')}_compressed.mp4"
                        await update.message.reply_video(
                            video=_buf, parse_mode=HTML, supports_streaming=True,
                            caption=(f"📥 <b>{to_bold(platform_name(raw_text).upper() + ' VIDEO')}</b>\n"
                                     f"• 📊 <b>Size:</b> {_c.get('size_mb')} MB (compressed)\n"
                                     "• 🔊 <b>Audio:</b> Original ✅\n"
                                     "<i>Full-size file bhejne me network slow tha — ye compressed version hai.</i>"))
                        _fixed = True
                except Exception as _e2:
                    log.warning("insta compress retry fail: %s", _e2)
            if _fixed:
                await st.delete()
                add_use(uid)
                await update.message.reply_text(spend_credit_msg(uid, "insta_dl"), parse_mode=HTML)
                return
            await st.edit_text(
                fail_msg("SEND FAILED", clean_err(e))
                + "\n\n💡 <b>What to do:</b>\n"
                  "• Tap the tool again and send the same link (2nd try usually works)\n"
                  "• Big video? Use <b>✂️ MEDIA STUDIO → Video compress</b>\n"
                  "• Ya <b>📥 VIDEO DOWNLOADER</b> dobara kholo aur link bhejo",
                parse_mode=HTML)
        return

    if mode == "ip":
        # v50: to_thread — IP lookup HTTP karta hai, event loop free rahega
        res = await asyncio.to_thread(lookup_ip_domain, raw_text)
        if res.get("ok"):
            flags = []
            flags.append("🛡️ Proxy/VPN: " + ("⚠️ Yes (hidden connection)" if res.get("is_proxy") else "✅ No"))
            flags.append("🏢 Datacenter/Hosting: " + ("✅ Yes (server/VPN line)" if res.get("is_hosting") else "❌ No (normal internet line)"))
            flags.append("📱 Mobile network: " + ("✅ Yes" if res.get("is_mobile") else "❌ No"))
            rows = []   # v49.13: koi website/Map link nahi (user ka order)
            await update.message.reply_text(
                spend_credit_msg(uid, "ip") + "\n" +
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
                "\n\n<i>This is public IP information (for websites/servers). It does not show anyone's home address.</i>",
                reply_markup=InlineKeyboardMarkup(rows) if rows else None, parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "rto":
        base = lookup_vehicle_rto(raw_text)          # purana free lookup (district + links)
        if not base.get("ok"):
            await update.message.reply_text(fail_msg("VEHICLE LOOKUP FAILED", base.get("error", "Invalid plate")),
                                            parse_mode=HTML)
            add_use(uid)
            return

        def _free_card(extra: str = ""):
            # v49.12: koi website link/button NAHI — sirf SMS tarika (100% free, phone se)
            _pl = (base.get("plate") or str(raw_text or "").replace(" ", "").upper())
            sms = ("━━━━━━━━━━━━━━━━━━━━━━\n"
                   "📲 <b>RC + challan ka poora record — SMS se (30 sec, FREE)</b>\n"
                   f"1️⃣ SMS likho:  <code>VAHAN {_pl}</code>\n"
                   f"2️⃣ SMS likho:  <code>CHALLAN {_pl}</code>\n"
                   "3️⃣ Bhejo is number par:  <code>7738299899</code>\n"
                   "<i>(Official MoRTH / NIC gateway — reply me: owner naam, maker, model, "
                   "RC date, insurance, pending challan. Unlimited SMS pack me bilkul ₹0.)</i>\n"
                   "✅ <b>Koi website kholne ki zaroorat nahi — sab isi card me.</b>")
            return (
                f"🚗 <b>{to_bold('VEHICLE / RTO INFO')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔖 <b>Number Plate:</b> <code>{base['pretty']}</code>\n"
                f"🗺️ <b>State:</b> {base['state_name']} ({base['state_code']})\n"
                f"🏢 <b>RTO Office:</b> {base['rto_code']} — {base['district']}\n"
                + (f"🚙 <b>Vehicle Class (from series):</b> {base['vehicle_class']}\n" if base.get("vehicle_class") else "")
                + "━━━━━━━━━━━━━━━━━━━━━━\n"
                + (extra + "\n" if extra else "")
                + sms
            ), None

        # ---- live RC + challan report (agar API set hai) ----
        if vehicle_api_ready() and vehicle_plate_ok(raw_text):
            _u = get_user(uid, update.effective_user.first_name)
            if not can_use_premium_tool(_u, uid):
                await update.message.reply_text(get_credits_over_text("vehicle"),
                                                reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                card_txt, kb_free = _free_card("✅ <b>Free part:</b> RTO office + district yahan hai, aur neeche SMS se poora record.")
                await update.message.reply_text(card_txt, reply_markup=kb_free, parse_mode=HTML)
                context.user_data.pop("mode", None)
                add_use(uid)
                return
            wait = await update.message.reply_text("🔎 <b>Checking live RC + challan record…</b>\n<i>Please wait 5-20 seconds.</i>",
                                                   parse_mode=HTML)
            # v50: to_thread — 5-70s wala call, bot freeze nahi hoga
            live = await asyncio.to_thread(fetch_vehicle_report, raw_text)
            try:
                await wait.delete()
            except Exception:
                pass
            if live.get("ok") and not _veh_has_rc_data(live):
                card_txt, kb_free = _free_card(
                    "🔎 <b>No RC / challan record found for this number.</b>\n"
                    "✅ <b>No credit was cut</b> — check the number plate once and send again.")
                await update.message.reply_text(card_txt, reply_markup=kb_free, parse_mode=HTML)
                add_use(uid)
                return
            if live.get("ok"):
                await update.message.reply_text(spend_credit_msg(uid, "vehicle"), parse_mode=HTML)
                rows_live = [
                    [InlineKeyboardButton("🔄 Ye number dobara check karo", callback_data=f"vehagain:{live['plate']}")],
                ]
                await update.message.reply_text(render_vehicle_report(live),
                                                reply_markup=InlineKeyboardMarkup(rows_live), parse_mode=HTML)
                add_use(uid)
                return
            # API fail → free card + reason
            if live.get("hub_disabled"):
                _why = ("⚠️ <b>Live auto-check abhi band hai.</b>\n"
                        "<i>Neeche wala SMS tarika hamesha chalta hai (MoRTH ka official number).</i>")
            else:
                _why = f"⚠️ <b>Live report not available:</b> {hesc(str(live.get('error'))[:120])}"
            card_txt, kb_free = _free_card(_why)
            await update.message.reply_text(card_txt, reply_markup=kb_free, parse_mode=HTML)
            add_use(uid)
            return

        card_txt, kb_free = _free_card("🚨 <b>Challan + poori RC report ke liye:</b> neeche SMS karo — 30 second me aapke phone par aa jayega.")
        await update.message.reply_text(card_txt, reply_markup=kb_free, parse_mode=HTML)
        add_use(uid)
        return

    if mode == "imei":
        _u_i = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u_i, uid):
            await update.message.reply_text(get_credits_over_text("imei"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            add_use(uid)
            return
        ok15, imei_clean, imei_err = imei_validate(raw_text)
        if not ok15:
            await update.message.reply_text(
                "❌ <b>" + hesc(imei_err) + "</b>\n\n" + imei_help_card(),
                parse_mode=HTML)
            add_use(uid)
            return                       # mode chalu rehta hai — dobara bhej sakte ho
        if not imei_api_ready():
            await update.message.reply_text(
                imei_help_card("IMEI details abhi available nahi hain. Thodi der baad try karo."),
                parse_mode=HTML)
            add_use(uid)
            return
        wait = await update.message.reply_text(
            "🔎 <b>Phone ki details nikal raha hoon…</b>\n<i>5-15 second lagenge.</i>", parse_mode=HTML)
        res_i = await asyncio.to_thread(fetch_imei_details, imei_clean)
        try:
            await wait.delete()
        except Exception:
            pass
        if not res_i.get("ok"):
            # v49.13: imei.info wale link buttons hata diye (user ka order)
            await update.message.reply_text(
                "❌ <b>DEVICE DETAILS NAHI MILE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔢 IMEI: <code>{hesc(imei_clean)}</code>\n"
                f"⚠️ {hesc(str(res_i.get('error'))[:160])}\n"
                "✅ <b>Koi credit nahi kata</b> — IMEI check karke dobara bhejo (dial <code>*#06#</code>).",
                parse_mode=HTML)
            add_use(uid)
            return
        await update.message.reply_text(spend_credit_msg(uid, "imei"), parse_mode=HTML)
        photo_sent = False
        if res_i.get("photo") and not str(res_i["photo"]).lower().endswith(".gif"):
            try:
                await update.message.reply_photo(photo=res_i["photo"],
                                                 caption=render_imei_caption(res_i), parse_mode=HTML)
                photo_sent = True
            except Exception:
                photo_sent = False
        body = render_imei_text(res_i)
        if not photo_sent and not body.startswith("📲"):
            body = ("📲 <b>" + hesc(imei_title(res_i)) + "</b>\n"
                    f"🔢 <b>IMEI:</b> <code>{hesc(str(res_i.get('imei') or ''))}</code>\n" + body)
        await update.message.reply_text(body, parse_mode=HTML, disable_web_page_preview=True)
        try:
            buf_spec = io.BytesIO(imei_specs_json(res_i))
            buf_spec.name = imei_specs_filename(res_i)
            await update.message.reply_document(
                document=buf_spec,
                caption=("📄 <b>" + hesc(imei_title(res_i)) + "</b> — full specifications\n"
                         "<i>JSON copy file — open it or paste it anywhere (copy code style).</i>"),
                parse_mode=HTML)
        except Exception as e:
            log.warning("imei json file send fail: %s", e)
        # v49.13: device ke bahar wale links (imei.info/nanoreview) hata diye — sirf refresh
        rows_i = [[InlineKeyboardButton("🔄 Doosra IMEI check karo", callback_data="imei_new")]]
        await update.message.reply_text("👇 Next:", reply_markup=InlineKeyboardMarkup(rows_i), parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    if mode == "pp_stamp_text":
        raw = context.user_data.get("raw_photo")
        if not raw:
            context.user_data.pop("mode", None)
            await update.message.reply_text("⚠️ Please open 📸 PASSPORT PHOTO from the menu and send a photo first.",
                                            parse_mode=HTML)
            return
        txt = re.sub(r"\s+", " ", (raw_text or "")).strip()
        m_d = re.search(r"(\d{1,2})[\-/. ](\d{1,2})[\-/. ](\d{4})", txt)
        if m_d:
            name = txt[:m_d.start()].strip(" -.,")
            dop = f"{int(m_d.group(1)):02d}-{int(m_d.group(2)):02d}-{m_d.group(3)}"
        else:
            name, dop = txt, date.today().strftime("%d-%m-%Y")
        name = re.sub(r"[^A-Za-z .'\-]", "", name).strip()
        if len(name) < 2:
            await update.message.reply_text(
                "✍️ <b>Name samajh nahi aaya.</b>\nSend it like this: <code>RAHUL SHARMA 30-09-2026</code>",
                parse_mode=HTML)
            return
        if not m_d:
            await update.message.reply_text(
                f"⚠️ <b>Date nahi mili</b> — maine aaj ki date lagayi: <b>{dop}</b>\n"
                f"<i>Agar doosri date chahiye to dobara bhejo:</i> <code>{name.upper()} 01-01-2026</code>",
                parse_mode=HTML)
        wait = await update.message.reply_text("🎨 Making the photo… (5-10 seconds)")
        try:
            stamped, sz = await asyncio.to_thread(make_stamped_passport, raw, name.upper(), dop)
        except Exception as e:
            await wait.edit_text(fail_msg("PHOTO FAILED", clean_err(e)), parse_mode=HTML)
            return
        try:
            await wait.delete()
        except Exception:
            pass
        await update.message.reply_photo(
            photo=stamped,
            caption=(spend_credit_msg(uid, "pp_stamp") + "\n" +
                     f"📸 <b>{to_bold('OFFICIAL GOVT EXAM PHOTO READY')}</b>\n"
                     f"• <b>Name:</b> {hesc(name.upper())}\n• <b>DOP:</b> {hesc(dop)}\n"
                     f"• <b>Size:</b> {sz} KB (20-50KB ✅)"),
            parse_mode=HTML)
        context.user_data.pop("mode", None)
        context.user_data.pop("raw_photo", None)
        add_use(uid)
        return

    if mode == "numinfo":
        _u = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u, uid):
            await update.message.reply_text(get_credits_over_text("numinfo"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        res = lookup_phone_info(raw_text)
        # v49.6: aapke hub ka LEGAL carrier lookup (operator/circle live) — provider ho to
        _car = {}
        try:
            _car = await asyncio.to_thread(hubapi.hub_carrier_info, raw_text)
        except Exception:
            _car = {}
        if res.get("ok"):
            await update.message.reply_text(spend_credit_msg(uid, "numinfo"), parse_mode=HTML)
            card = (
                "╔═══════════════════════════╗\n"
                f"📱 <b>{to_bold('NUMBER INFO REPORT')}</b>\n"
                "╚═══════════════════════════╝\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Number:</b> <code>{res['international']}</code>\n"
                f"• <b>National:</b> {res['national']}\n"
                f"• <b>Type:</b> {res['type']} {res['series_note']}\n"
                f"• <b>Operator:</b> {(_car.get('operator') or res['operator'])}\n"
                f"• <b>Circle/Region:</b> {(_car.get('circle') or res['circle'])}\n"
                + (f"• <b>Number Type (live):</b> {hesc(str(_car.get('type')))}\n" if _car.get("type") else "")
                + (f"• <b>Ported (MNP):</b> {hesc(str(_car.get('ported')))}\n" if _car.get("ported") not in (None, "", False) else "")
                + f"• <b>Country:</b> {res['country']} ({res.get('country_code') or '—'})\n"
                + f"• <b>Timezone:</b> {res['timezones']}\n"
                f"• <b>Valid:</b> {'✅ Haan' if res['valid'] else '⚠️ Suspicious'}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"ℹ️ <i>{res['note']}</i>"
            )
            # v49.15: koi extra button nahi (purana card poora delete)
            await update.message.reply_text(card, parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "ifsc":
        # v50: to_thread — event loop block nahi hoga (rate-limit central gate se lagta hai)
        i_res = await asyncio.to_thread(lookup_ifsc, raw_text)
        if i_res.get("ok"):
            rows = []   # v49.13: Google Maps link nahi
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
            await update.message.reply_text(spend_credit_msg(uid, "ifsc") + "\n" + card,
                                            reply_markup=InlineKeyboardMarkup(rows) if rows else None, parse_mode=HTML)
        else:
            await update.message.reply_text(f"❌ {i_res.get('error')}", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "pin":
        cleaned = re.sub(r"[^\d]", "", raw_text)
        if len(cleaned) == 6:
            p_res = await asyncio.to_thread(lookup_pincode, cleaned)
            if p_res.get("ok"):
                rows = []   # v49.13: Map link nahi
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
                await update.message.reply_text(spend_credit_msg(uid, "pin") + "\n" + card,
                                                reply_markup=InlineKeyboardMarkup(rows) if rows else None, parse_mode=HTML)
            else:
                await update.message.reply_text(f"❌ {p_res.get('error')}", parse_mode=HTML)
        else:
            # Area / post-office ke naam se pincode dhoondo
            st = await update.message.reply_text("🔍 Area ke naam se pincode dhoondh raha hoon...")
            a_res = await asyncio.to_thread(search_by_area_name, raw_text)
            if a_res.get("ok"):
                lines = []
                rows = []
                for r in a_res["results"][:8]:
                    lines.append(f"• <b>{hesc(r['name'])}</b> — <code>{r['pincode']}</code> ({hesc(r['district'])}, {hesc(r['state'])})")
                    rows.append([InlineKeyboardButton(f"📋 {r['pincode']} — {r['name'][:28]}", callback_data=f"copy_{r['pincode']}")])
                # v50: honest header — agar naam strip karke match hua to batao
                note = ""
                if a_res.get("approximate"):
                    note = (f"\n⚠️ <i>'{hesc(a_res.get('matched_via') or a_res['query'])}' se match hua — "
                            "apna district/state confirm kar lena.</i>")
                elif a_res.get("total", 0) > 1:
                    note = "\n💡 <i>Ek hi naam kai jagah hota hai — apna district dekh kar chuno.</i>"
                if a_res.get("cached"):
                    note += "\n⚡ <i>cache se (instant)</i>"
                await st.edit_text(
                    spend_credit_msg(uid, "pin") + "\n" +
                    f"📮 <b>{to_bold('AREA SEARCH')}: {hesc(a_res['query'])}</b>\n"
                    f"({a_res['total']} post offices mili){note}\n\n" + "\n".join(lines) +
                    "\n\n💡 Pincode copy karne ke liye neeche button par tap karo:",
                    reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML,
                )
            else:
                await st.edit_text(f"❌ {a_res.get('error')}\n\n💡 Ya 6-digit pincode bhejo (jaise <code>800001</code>)", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "qr":
        buf = make_qr_bytes(raw_text)
        await update.message.reply_photo(
            photo=buf,
            caption=spend_credit_msg(uid, "qr") + "\n" + f"📷 <b>{to_bold('HD QR CODE TAYYAR')}</b>\n\n🔗 <code>{hesc(raw_text[:80])}</code>\n\n<i>Scan karte hi link khul jayega.</i>",
            parse_mode=HTML)
        add_use(uid)
        return



    # ---------------- v38: KAGAZ FILL (ek-ek field) ----------------
    if mode and mode.startswith("kagaz_fill_"):
        kind = mode.replace("kagaz_fill_", "")
        step = int(context.user_data.get("kagaz_step", 0))
        data = context.user_data.get("kagaz_data") or {}
        fields = KAGAZ_FIELDS.get(kind, [])
        if step < len(fields):
            fname = fields[step][0]
            data[fname] = "" if raw_text.strip().lower() in ("skip", "-", "no") else raw_text.strip()
        context.user_data["kagaz_data"] = data
        step += 1
        context.user_data["kagaz_step"] = step
        if step < len(fields):
            await update.message.reply_text(kagaz_ask_next(kind, data, step), parse_mode=HTML)
            return
        # sab fields mil gaye — PDF banao
        _u = get_user(uid, user.first_name)
        if not can_use_premium_tool(_u, uid):
            await update.message.reply_text(get_credits_over_text("kagaz"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        await update.message.reply_text("📄 Making the document PDF... (2-5 seconds)")
        try:
            pdf = KAGAZ_MAKERS[kind](data)
        except Exception as e:
            await update.message.reply_text(fail_msg("KAGAZ FAILED", str(e)[:150]), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        names = {"kirayanama": "Kirayanama", "affidavit": "Affidavit", "notice138": "Legal_Notice_138",
                 "bayana": "Bayana_Rasid", "loan": "Rin_Shodh", "nameaff": "Affidavit_Correction"}
        await update.message.reply_document(
            document=pdf, filename=f"{names.get(kind, 'Kagaz')}_{datetime.now().strftime('%d-%m-%Y')}.pdf",
            caption=("📜 <b>" + names.get(kind, "KAGAZ").upper() + " READY ✅</b>\n"
                     "🖨️ Print it, fill the needed places, get witness signatures.\n"
                     "⚠️ <i>Get it finalised by a notary / sub-registrar — this is a computer-made draft.</i>\n\n"
                     + spend_credit_msg(uid, "kagaz")),
            parse_mode=HTML)
        context.user_data.pop("mode", None)
        context.user_data.pop("kagaz_data", None)
        add_use(uid)
        return

    if mode == "kagaz_registry_state":
        st = raw_text.strip()
        context.user_data["kagaz_reg_state"] = st
        context.user_data["mode"] = "kagaz_registry_area"
        await update.message.reply_text(
            "📐 Ab <b>zameen ka area</b> likho — simple tarika:\n"
            "• <code>2 katha</code>  • <code>1500 sqft</code>  • <code>1 bigha</code>  • <code>5 decimal</code>",
            parse_mode=HTML)
        return

    if mode == "kagaz_registry_area":
        m = re.match(r"([\d.]+)\s*([a-zA-Zа-я\s]+)?", raw_text.strip())
        val = float(m.group(1)) if m and m.group(1) else 0.0
        unit = (m.group(2) or "sqft").strip() if m else "sqft"
        conv = convert_land(val, unit)
        if not conv.get("ok"):
            await update.message.reply_text(f"❌ {conv.get('error')}\nType it again (example <code>2 katha</code>)", parse_mode=HTML)
            return
        context.user_data["kagaz_reg_area"] = conv["sqft"]
        context.user_data["mode"] = "kagaz_registry_rate"
        await update.message.reply_text(
            f"✅ {conv['sqft']} Sq Ft is set.\n\n"
            "💰 Now tell the <b>MVR / circle rate</b> (₹ per Sq Ft):\n"
            "<i>In Bihar you can check the MVR (circle rate) on <code>bhumijankari.bihar.gov.in</code>. "
            "If you do not know it, type your deal rate.</i>\n"
            "example: <code>3000</code>", parse_mode=HTML)
        return

    if mode == "kagaz_registry_rate":
        try:
            rate = float(re.sub(r"[^\d.]", "", raw_text) or 0)
        except Exception:
            rate = 0
        if rate <= 0:
            await update.message.reply_text("❌ Rate padh nahi paya. Sirf number type karo (jaise <code>3000</code>).", parse_mode=HTML)
            return
        context.user_data["mode"] = "kagaz_registry_buyer"
        context.user_data["kagaz_reg_rate"] = rate
        await update.message.reply_text(
            "👤 Kharidar kaun hai? <code>male</code> / <code>female</code> / <code>joint</code> likho\n"
            "<i>(Bihar: aurat ya aurat ke saath joint par 1% kam stamp duty lagti hai)</i>", parse_mode=HTML)
        return

    if mode == "kagaz_registry_buyer":
        buyer = raw_text.strip().lower()
        st = context.user_data.get("kagaz_reg_state", "bihar")
        area = float(context.user_data.get("kagaz_reg_area") or 0)
        rate = float(context.user_data.get("kagaz_reg_rate") or 0)
        panch = 2.0 if str(st).lower().startswith("bih") else 0.0
        res = registry_cost(st, area, rate, buyer, panchayat_pct=panch)
        await update.message.reply_text(registry_text(res) + "\n\n" + spend_credit_msg(uid, "kagaz"), parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    if mode == "kagaz_gst":
        g = re.sub(r"\s+", "", raw_text or "").upper()
        st = await update.message.reply_text("🔎 <b>GSTIN check kar raha hoon…</b>", parse_mode=HTML)
        res = await asyncio.to_thread(hubapi.hub_gst, g)
        if not res.get("ok"):
            await st.edit_text(
                f"❌ <b>GST CHECK NAHI HO PAYA</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ {hesc(str(res.get('error'))[:200])}\n"
                "✅ Koi credit nahi kata. GSTIN 15 character ka hota hai (jaise <code>19BOKPS7056D1ZI</code>).",
                parse_mode=HTML)
            return
        _st = str(res.get("state") or "")
        if res.get("state_code"):
            _st = (_st + f" (code {res.get('state_code')})").strip()
        _chk = res.get("checksum_valid")
        _chk_line = ""
        if _chk is True:
            _chk_line = "• <b>Checksum:</b> ✅ sahi\n"
        elif _chk is False:
            _chk_line = ("• <b>Checksum:</b> ⚠️ match nahi hua "
                         f"(expected <code>{hesc(str(res.get('checksum_expected')))}</code>) — "
                         "GSTIN ka aakhri character galat lagta hai\n")
        _extra = kv_row("Legal Name", res.get("legal_name")) + kv_row("Trade Name", res.get("trade_name")) \
            + kv_row("Status", res.get("status")) + kv_row("Registered", res.get("reg_date")) \
            + kv_row("Address", res.get("address"))
        card = (f"🏢 <b>{to_bold('GST NUMBER DETAILS')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>GSTIN:</b> <code>{hesc(res.get('gstin'))}</code>\n"
                + kv_row("State", _st)
                + kv_row("PAN", res.get("pan"))
                + kv_row("PAN Holder Type", res.get("pan_holder_type"))
                + kv_row("Registration Type", res.get("registration_type"))
                + _chk_line
                + _extra
                + "━━━━━━━━━━━━━━━━━━━━━━\n"
                + ("" if _extra else
                   "ℹ️ Legal name / address / filing status hub ke records me nahi hain.\n"
                   "Upar ka data GSTIN ke format ka analysis hai (state, PAN, holder type, checksum).\n")
                + f"<i>Source: {hesc(str(res.get('source')))}</i>")
        await st.edit_text(card, parse_mode=HTML)
        await update.message.reply_text(spend_credit_msg(uid, "kagaz"), parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    if mode == "kagaz_pan":
        p10 = re.sub(r"[^A-Za-z0-9]", "", raw_text or "").upper()
        st = await update.message.reply_text("🔎 <b>PAN check kar raha hoon…</b>", parse_mode=HTML)
        res = await asyncio.to_thread(hubapi.hub_pan, p10)
        if not res.get("ok"):
            await st.edit_text(
                f"❌ <b>PAN CHECK NAHI HO PAYA</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ {hesc(str(res.get('error'))[:200])}\n"
                "✅ Koi credit nahi kata. PAN 10 character ka hota hai (jaise <code>AAYFK4129N</code>).",
                parse_mode=HTML)
            return
        rows = []
        for g in (res.get("gstins") or [])[:10]:
            rows.append(f"• <code>{hesc(g.get('gstin'))}</code>"
                        + (f" — {hesc(g.get('name'))}" if g.get("name") else "")
                        + (f" <i>({hesc(g.get('status'))})</i>" if g.get("status") else ""))
        card = (f"🪪 <b>{to_bold('PAN → GST DETAILS')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>PAN:</b> <code>{hesc(res.get('pan'))}</code>\n"
                + (kv_row("Format", "✅ sahi" if res.get("valid_format") else "")
                   if res.get("valid_format") is not None else "")
                + kv_row("Holder Type", res.get("holder_type"))
                + kv_row("Series", res.get("series"))
                + (f"• <b>Name:</b> {hesc(res.get('name'))}\n" if res.get("name") else "")
                + (f"• <b>PAN Status:</b> {hesc(res.get('status'))}\n" if res.get("status") else "")
                + f"• <b>GST numbers:</b> {len(res.get('gstins') or [])}\n\n"
                + ("\n".join(rows) if rows else
                   "<i>Is PAN par hub ke records me koi GST number nahi mila.</i>")
                + f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
                + ("ℹ️ Hub abhi PAN ka <b>offline analysis</b> deta hai (format + holder type + series).\n"
                   "GSTIN ki poori list ke liye upstream records chahiye.\n"
                   if not rows else "")
                + f"<i>Source: {hesc(str(res.get('source')))}</i>")
        await st.edit_text(card, parse_mode=HTML)
        await update.message.reply_text(spend_credit_msg(uid, "kagaz"), parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    if mode == "kagaz_land_value":
        m = re.match(r"([\d.]+)\s*([a-zA-Zа-я\s]+)?", raw_text.strip())
        val = float(m.group(1)) if m and m.group(1) else 0.0
        unit = (m.group(2) or "sqft").strip() if m else "sqft"
        res = convert_land(val, unit)
        if not res.get("ok"):
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
            return
        await update.message.reply_text(land_text(res) + "\n\n" + spend_credit_msg(uid, "kagaz"), parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    # ---------------- v38: BANK STATEMENT ----------------
    if mode == "bankpdf":
        await update.message.reply_text(
            "📄 <b>Bank statement ka PDF bhejo</b> (file/document ke roop me).\n"
            "<i>Sirf PDF bhejo — screenshot ya photo nahi (unme table nahi hoti).</i>", parse_mode=HTML)
        return

    if mode == "bankpdf_pass":
        pwd = raw_text.strip()
        raw = context.user_data.get("bankpdf_bytes")
        if not raw:
            await update.message.reply_text("⚠️ Send the PDF first.", parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        await update.message.reply_text("🔓 Opening the PDF...")
        res = parse_bank_statement(raw, password=pwd)
        if not res.get("ok"):
            await update.message.reply_text(
                f"❌ {res.get('error')}\n\n<i>Common passwords: last 4 digits of the account, or first 4 letters of the name + "
                "year (example <code>rame1990</code>), or the pattern the bank sent you.</i>", parse_mode=HTML)
            return
        await deliver_statement(update, context, uid, res)
        return

    if mode == "media_menu":
        await update.message.reply_text("👆 Upar wale buttons se option chuno.", parse_mode=HTML)
        return

    if mode == "media_ytmp3":
        await do_ytmp3(update, context, uid, raw_text.strip())
        return

    if mode in ("media_ringtone", "media_karaoke", "media_8d", "media_bass", "media_voice_wait",
                "media_v2mp3", "media_trim_wait", "media_compress_wait", "media_status_audio"):
        await update.message.reply_text("🎵 Pehle <b>audio/video file bhejo</b> (upar likhe tarike se).", parse_mode=HTML)
        return

    if mode == "media_ringtone_start":
        raw = context.user_data.get("media_audio")
        if not raw:
            context.user_data["mode"] = "media_ringtone"
            await update.message.reply_text("⚠️ Send the audio again.", parse_mode=HTML)
            return
        m = re.search(r"(\d{1,2}):(\d{2})", raw_text)
        if m:
            start = int(m.group(1)) * 60 + int(m.group(2))
        else:
            digits = re.sub(r"[^\d]", "", raw_text)
            start = int(digits) if digits else 0
        st = await update.message.reply_text("🎧 Making the ringtone...")
        res = await asyncio.to_thread(desi.audio_cut, raw, str(start), str(start + 30), "mp3")
        if not res.get("ok"):
            await st.edit_text(fail_msg("RINGTONE FAILED", res.get("error", "")), parse_mode=HTML)
            return
        await st.delete()
        await update.message.reply_audio(
            audio=res["bytes"], filename="ringtone.mp3", title="Ringtone", performer="Utility Duniya",
            duration=int(res.get("duration") or 30),
            caption=(f"🎧 <b>RINGTONE READY</b> — {res.get('duration')}s\n"
                     f"<i>starts at {start // 60}:{start % 60:02d}</i>\n\n" + spend_credit_msg(uid, "mediastudio")),
            parse_mode=HTML)
        context.user_data.pop("mode", None)
        context.user_data.pop("media_audio", None)
        add_use(uid)
        return

    if mode == "media_trim_time":
        m = re.findall(r"\d{1,2}:\d{2}|\d+", raw_text)
        if len(m) < 2:
            await update.message.reply_text("❌ Type it like: <code>0:10 0:45</code> (start to end)", parse_mode=HTML)
            return
        context.user_data["media_trim"] = (m[0], m[1])
        raw = context.user_data.get("media_video")
        if not raw:
            context.user_data["mode"] = "media_trim_wait"
            await update.message.reply_text("⚠️ Send the video again.")
            return
        await update.message.reply_text("✂️ Cutting the video... (10-60 seconds)")
        res = desi.video_trim(raw, m[0], m[1])
        if not res.get("ok"):
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
            return
        await update.message.reply_video(video=res["bytes"], filename="trimmed.mp4", supports_streaming=True,
                                         caption=f"✂️ <b>VIDEO READY</b> — {res.get('duration')}s · {res.get('size_mb')}MB\n\n"
                                                 + spend_credit_msg(uid, "mediastudio"), parse_mode=HTML)
        context.user_data.pop("mode", None)
        context.user_data.pop("media_video", None)
        add_use(uid)
        return

    if mode == "media_status_text":
        txt = raw_text.strip()
        img = context.user_data.get("media_status_photo")
        aud = context.user_data.get("media_status_audio")
        if not (img and aud):
            await update.message.reply_text("⚠️ Pehle photo aur gaana dono bhejo.", parse_mode=HTML)
            context.user_data["mode"] = "media_status_photo"
            return
        await update.message.reply_text("🎬 Making the status video... (20-90 seconds)")
        res = desi.make_status_video(img, aud, txt, seconds=30)
        if not res.get("ok"):
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
            return
        await update.message.reply_video(video=res["bytes"], filename="status.mp4", supports_streaming=True,
                                         caption=("🎬 <b>STATUS VIDEO TAIYAR ✅</b> (9:16 — WhatsApp/Instagram status)\n"
                                                  "📥 Download karke seedha apne status par lagao.\n\n"
                                                  + spend_credit_msg(uid, "mediastudio")), parse_mode=HTML)
        for k in ("media_status_photo", "media_status_audio", "mode"):
            context.user_data.pop(k, None)
        add_use(uid)
        return

    if mode == "qr_wifi":
        context.user_data["qr_wifi_ssid"] = raw_text.strip()
        context.user_data["mode"] = "qr_wifi_pass"
        await update.message.reply_text(
            "📶 <b>WiFi QR — Step 2/2</b>\n\n"
            f"WiFi Name (SSID): <code>{hesc(raw_text)}</code>\n\n"
            "Ab <b>WiFi password</b> bhejo:\n"
            "(agar open WiFi hai to <code>none</code> bhejo)", parse_mode=HTML)
        return

    if mode == "qr_wifi_pass":
        ssid = context.user_data.get("qr_wifi_ssid", "")
        pwd = raw_text.strip()
        context.user_data.pop("mode", None)
        data = wifi_qr_data(ssid, "" if pwd.lower() == "none" else pwd)
        buf = make_qr_bytes(data, box_size=14)
        await update.message.reply_photo(
            photo=buf,
            caption=(spend_credit_msg(uid, "qr") + "\n" +
                     f"📶 <b>{to_bold('WIFI QR READY')}</b>\n\n"
                     f"• <b>WiFi:</b> <code>{hesc(ssid)}</code>\n"
                     f"• <b>Password:</b> <code>{hesc(pwd) if pwd.lower() != 'none' else 'Open (no password)'}</code>\n\n"
                     "📱 Guests scan this QR → their phone connects to the WiFi automatically ✅\n"
                     "<i>Print it and stick it on the wall — no need to tell the password!</i>"),
            parse_mode=HTML)
        add_use(uid)
        return

    if mode == "qr_vcard":
        context.user_data["qr_vc_name"] = raw_text.strip()[:40]
        context.user_data["mode"] = "qr_vcard_phone"
        await update.message.reply_text(
            "👤 <b>Contact Card — Step 2/2</b>\n\n"
            f"Name: <b>{hesc(raw_text)}</b>\n\n"
            "Ab <b>phone number</b> bhejo (jaise <code>9876543210</code>):", parse_mode=HTML)
        return

    if mode == "qr_vcard_phone":
        name = context.user_data.get("qr_vc_name", "")
        phone = raw_text.strip()
        context.user_data.pop("mode", None)
        data = vcard_data(name, phone, org="Utility Duniya Bot")
        buf = make_qr_bytes(data, box_size=14)
        await update.message.reply_photo(
            photo=buf,
            caption=(spend_credit_msg(uid, "qr") + "\n" +
                     f"👤 <b>{to_bold('DIGITAL VISITING CARD READY')}</b>\n\n"
                     f"• <b>Name:</b> {hesc(name)}\n"
                     f"• <b>Phone:</b> <code>{hesc(phone)}</code>\n\n"
                     "📱 The contact saves on the phone as soon as it is scanned (name + number) ✅"),
            parse_mode=HTML)
        add_use(uid)
        return

    if mode == "short":
        st = await update.message.reply_text("🔗 Making short links (6 providers)...")
        # v50: dono HTTP-heavy hain — thread me chalao, ek saath (parallel = 2x fast)
        links, exp = await asyncio.gather(
            asyncio.to_thread(shorten_url, raw_text, 3),
            asyncio.to_thread(expand_url, raw_text),
        )
        clean = exp.get("cleaned", raw_text)
        if links:
            body = "\n\n".join(f"{i}️⃣ <b>{name}</b> → <code>{u}</code>" for i, (name, u) in enumerate(links, 1))
            extra = ""
            if clean and clean != raw_text:
                extra = f"\n\n🧹 <b>Tracking-free original:</b>\n<code>{clean}</code>"
            rows = [[InlineKeyboardButton(f"🔗 {name}", url=u)] for name, u in links]
            await st.edit_text(spend_credit_msg(uid, "short") + "\n" + f"🔗 <b>{to_bold('SHORT LINKS READY')}</b>\n\n{body}{extra}", reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            await st.edit_text(
                "⚠️ <b>Could not make a short link</b> (all providers are busy).\n"
                f"🧹 <b>Cleaned original link:</b>\n<code>{hesc(str(clean))}</code>",
                parse_mode=HTML,
            )
        add_use(uid)
        return

    if mode == "linkcheck":
        st = await update.message.reply_text("🔍 Running a 6-layer scan on the link...")
        chk = analyze_link(raw_text)
        risk = chk.get("risk", 0)
        bar = "█" * max(1, risk // 10) + "░" * (10 - max(1, risk // 10))
        reasons_txt = "\n".join(f"• {r}" for r in chk.get("reasons", [])[:8])
        sig = chk.get("signals", {})
        cap = (
            f"🛡️ <b>{to_bold('LINK CHECK REPORT')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Verdict:</b> {chk.get('verdict')}\n"
            f"📊 <b>Risk Score:</b> <code>{bar}</code> {risk}/100\n"
            f"🌐 <b>Final URL:</b> <code>{hesc(str(chk.get('final_url'))[:90])}</code>\n"
            f"🔁 Redirects: {sig.get('redirect_hops', 0)} | 🔓 HTTPS: {'✅' if sig.get('https') else '❌'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 <b>What was found:</b>\n{reasons_txt}\n\n"
            f"💡 <b>What to do:</b> {chk.get('advice')}"
        )
        kb_rows = [[InlineKeyboardButton("🌐 Final link kholo", url=chk.get("final_url"))]]
        await st.edit_text(spend_credit_msg(uid, "linkcheck") + "\n" + cap, reply_markup=InlineKeyboardMarkup(kb_rows), parse_mode=HTML)
        add_use(uid)
        return

    if mode == "appfind":
        app_data = get_app_store_links(raw_text)
        kb_stores = []
        for s in app_data["stores"]:
            kb_stores.append([InlineKeyboardButton(f"{s['name']}", url=s["url"])])
        await update.message.reply_text(
            spend_credit_msg(uid, "appfind") + "\n" +
            f"📦 <b>{to_bold('APP STORES FOR')}: {app_data['app_name']}</b>\n\n"
            "Official stores & Top 5 Verified Mod/APK websites available 👇",
            reply_markup=InlineKeyboardMarkup(kb_stores),
            parse_mode=HTML,
        )
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
                f"🆔 <b>Channel found:</b> {hesc(str(f_chat.title or ''))}\n"
                f"🆔 <b>ID:</b> <code>{f_chat.id}</code>\n\n"
                "👇 Ye channel kya banega?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📡 Ye SOURCE banao (posts yahan se aayenge)", callback_data=f"fc_src:{f_chat.id}")],
                    [InlineKeyboardButton("📑 Make this TARGET (posts go here)", callback_data=f"fc_tgt:{f_chat.id}")],
                ]),
                parse_mode=HTML,
            )
            return

    # Default fallback
    # v44: agar koi tool ka mode chalu hai to menu par na phenko — wahi tool dobara maango
    _mode_now = context.user_data.get("mode")
    if _mode_now and _mode_now in PROMPTS:
        await update.message.reply_text(
            "🤔 <b>Samajh nahi aaya</b> — lagta hai ye input is tool ke liye nahi tha.\n\n"
            + tool_prompt(_mode_now), reply_markup=tool_tutorial_kb(_mode_now), parse_mode=HTML)
        return
    if _mode_now:
        _name = {"pp_stamp_text": "📸 PASSPORT PHOTO", "pp_stamp": "📸 PASSPORT PHOTO",
                 "bankpdf_pass": "🏦 BANK PDF"}.get(_mode_now)
        if _name:
            await update.message.reply_text(
                f"🤔 <b>Samajh nahi aaya.</b> {_name} tool chalu hai — "
                "upar likhe steps ke hisaab se dobara bhejo, ya /cancel karke naya tool kholo.",
                parse_mode=HTML)
            return
    await update.message.reply_text("👇 Neeche grid menu se tool chuno:", reply_markup=kb_for(uid))


# ---------------- PHOTO / DOCUMENT HANDLERS ----------------
async def deliver_statement(update, context, uid, res):
    """Bank statement ka CSV + summary bhejo (1 credit)."""
    if not can_use_premium_tool(get_user(uid), uid):
        await update.message.reply_text(get_credits_over_text("bankpdf"),
                                        reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
        return
    await update.message.reply_document(
        document=res["csv"], filename=f"statement_{datetime.now().strftime('%d-%m-%Y')}.csv",
        caption=statement_summary_text(res), parse_mode=HTML)
    await update.message.reply_text(spend_credit_msg(uid, "bankpdf"), parse_mode=HTML)
    context.user_data.pop("mode", None)
    context.user_data.pop("bankpdf_bytes", None)
    add_use(uid)


async def do_ytmp3(update, context, uid, url):
    """YouTube link → MP3 (1 credit)."""
    if "youtu" not in url.lower() and "youtube" not in url.lower():
        await update.message.reply_text("❌ Ye YouTube link nahi lag raha. Aisa link bhejo: <code>https://youtu.be/xxxx</code>",
                                        parse_mode=HTML)
        return
    if not can_use_premium_tool(get_user(uid), uid):
        await update.message.reply_text(get_credits_over_text("mediastudio"),
                                        reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
        return
    st = await update.message.reply_text("🎵 Downloading the song... (15-60 seconds)")
    res = await asyncio.to_thread(desi.youtube_mp3, url, "192")
    if not res.get("ok"):
        await st.edit_text(fail_msg("MP3 FAILED", res.get("error", "")), parse_mode=HTML)
        return
    dur = int(res.get("duration") or 0)
    await st.delete()
    await update.message.reply_audio(
        audio=res["bytes"], filename="song.mp3",
        title=(res.get("title") or "Audio")[:60], performer=(res.get("uploader") or "Utility Duniya")[:40],
        duration=dur,
        caption=(f"🎵 <b>{hesc((res.get('title') or 'AUDIO')[:80])}</b>\n"
                 f"⏱️ {dur // 60}:{dur % 60:02d} · 📦 {res.get('size_mb')} MB\n\n"
                 + spend_credit_msg(uid, "mediastudio")),
        parse_mode=HTML)
    context.user_data.pop("mode", None)
    add_use(uid)


async def handle_new_tool_file(update, context, uid, msg, mode, kind, data, mime=""):
    """v38: aayi hui file ko mode ke hisaab se process karo. True = handle ho gaya."""
    say = msg.reply_text

    # ---------- 🏦 BANK PDF ----------
    if mode in ("bankpdf", "bankpdf_pass") and kind == "pdf":
        context.user_data["bankpdf_bytes"] = data
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("bankpdf"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return True
        st = await say("🔎 Reading the PDF table... (5-30 seconds)")
        res = await asyncio.to_thread(parse_bank_statement, data)
        if res.get("ok"):
            await st.delete()
            await deliver_statement(update, context, uid, res)
            return True
        if res.get("locked") and not res.get("wrong_password"):
            # v50 PRO: pehle KHUD common passwords try karo — user ko matlaagana nahi padega
            st.edit_text("🔒 PDF locked hai — main common passwords khud try kar raha hoon (2-5 sec)…",
                         parse_mode=HTML)
            cands = [c for c in statement_passwords() if len(c) >= 4][:8]
            for cand in cands:
                r2 = await asyncio.to_thread(parse_bank_statement, data, cand)
                if r2.get("ok"):
                    await st.delete()
                    await deliver_statement(update, context, uid, r2)
                    await say("🔓 <b>Auto-unlock ho gaya!</b> PDF ka password khud mil chuka tha ✅",
                              parse_mode=HTML)
                    return True
            context.user_data["mode"] = "bankpdf_pass"
            await st.edit_text(
                "🔒 <b>This PDF is locked with a password!</b>\n\nSend the password (as text).\n"
                "<i>Common patterns:</i>\n"
                "• last <b>4 digits</b> of the account (example <code>7561</code>)\n"
                "• <b>first 4 letters of name + birth year</b> (example <code>rame1990</code>)\n"
                "• or what the bank told you (example <code>ABCD1234</code>)\n\n"
                "🔑 <b>Now send the password:</b>", parse_mode=HTML)
            return True
        await st.edit_text(fail_msg("PDF READ FAILED", res.get("error", "")), parse_mode=HTML)
        context.user_data.pop("mode", None)
        return True

    # ---------- ⚡ MEDIA STUDIO ----------
    if mode == "media_menu":
        await say("👆 Upar wale buttons me se option chuno (MP3 / Status / Karaoke...).")
        return True

    if mode == "media_ytmp3" and kind == "text":
        return False

    if mode in ("media_ringtone",) and kind in ("audio", "video", "voice", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        context.user_data["media_audio"] = data
        context.user_data["mode"] = "media_ringtone_start"
        await say("⏱️ Ringtone kis second se shuru ho? (jaise <code>45</code> ya <code>1:20</code>)\n"
                  "<i>Ringtone 30 second ka banega.</i>", parse_mode=HTML)
        return True

    if mode in ("media_karaoke", "media_8d", "media_bass") and kind in ("audio", "video", "voice", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        names = {"media_karaoke": ("🎤 Karaoke", desi.make_karaoke),
                 "media_8d": ("🔊 8D sound", desi.eff_8d),
                 "media_bass": ("💥 Bass boost", desi.bass_boost)}
        label, fn = names[mode]
        st = await say(f"{label} in progress... (10-60 seconds)")
        res = await asyncio.to_thread(fn, data)
        if not res.get("ok"):
            await st.edit_text(fail_msg("FAILED", res.get("error", "")), parse_mode=HTML)
            return True
        await st.delete()
        extra = res.get("note") or ""
        await msg.reply_audio(audio=res["bytes"], filename="audio.mp3", title=label, performer="Utility Duniya",
                              caption=f"✅ <b>{label} ready!</b>\n{extra}\n\n" + spend_credit_msg(uid, "mediastudio"),
                              parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return True

    if mode == "media_v2mp3" and kind in ("video", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        st = await say("🎼 Extracting MP3 from the video...")
        res = await asyncio.to_thread(desi.video_to_mp3, data)
        if not res.get("ok"):
            await st.edit_text(fail_msg("FAILED", res.get("error", "")), parse_mode=HTML)
            return True
        await st.delete()
        await msg.reply_audio(audio=res["bytes"], filename="audio.mp3", title="Audio of the video",
                              performer="Utility Duniya",
                              caption="🎼 <b>MP3 ready!</b>\n\n" + spend_credit_msg(uid, "mediastudio"),
                              parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return True

    if mode == "media_voice_wait" and kind in ("audio", "video", "voice", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        context.user_data["media_audio"] = data
        await say("🗣️ Ab <b>voice chuno</b> (kid / heavy / robot / ghost / gadget / echo):",
                  reply_markup=voice_preset_kb(), parse_mode=HTML)
        return True

    if mode == "media_trim_wait" and kind in ("video", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        context.user_data["media_video"] = data
        context.user_data["mode"] = "media_trim_time"
        await say("✂️ Kahan se kahan tak kaatna hai? Aise likho: <code>0:10 0:45</code>\n"
                  "<i>(shuru ka time aur end ka time)</i>", parse_mode=HTML)
        return True

    if mode == "media_compress_wait" and kind in ("video", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        st = await say("🗜️ Video compress ho raha hai... (30 second - 3 minute)\n<i>Badi video me zyada time lagta hai.</i>")
        res = await asyncio.to_thread(desi.video_compress, data, 18.0)
        if not res.get("ok"):
            await st.edit_text(fail_msg("COMPRESS FAILED", res.get("error", "")) +
                               ("\n\n✂️ <b>TRIM</b> first to make it short, then compress." if res.get("too_long") else ""),
                               parse_mode=HTML)
            return True
        await st.delete()
        await msg.reply_video(video=res["bytes"], filename="compressed.mp4", supports_streaming=True,
                              caption=(f"🗜️ <b>VIDEO COMPRESSED</b> — {res.get('size_mb')} MB\n"
                                       f"{res.get('note') or ''}\n\n" + spend_credit_msg(uid, "mediastudio")),
                              parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return True

    if mode == "media_status_audio" and kind in ("audio", "voice"):
        context.user_data["media_status_audio"] = data
        context.user_data["mode"] = "media_status_text"
        await say("✍️ Ab <b>status par kya likhna hai</b>? (1-3 line)\n<i>jaise: Happy Birthday Rahul 🎂</i>", parse_mode=HTML)
        return True

    return False


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # v49.4: VIP-only (payment screenshot flow chhod kar)
    _m = str(context.user_data.get("mode") or "")
    if PREMIUM_ONLY and not vip_ok(update.effective_user.id) and not _m.startswith(("pay_", "adm_")):
        await send_vip_wall(update, context)
        return
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
        await update.message.reply_text("✅ <b>Thumbnail save ho gaya!</b> Ab se saare forwarded video/document par ye hi thumbnail lagega.", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    # ---------- v38: STATUS VIDEO (photo) ----------
    if mode == "media_status_photo":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        context.user_data["media_status_photo"] = buf.getvalue()
        context.user_data["mode"] = "media_status_audio"
        await update.message.reply_text(
            "🎵 Ab <b>gaana bhejo</b> (status ke liye MP3/audio file).\n"
            "<i>YouTube se gaana chahiye to pehle 🎵 YouTube → MP3 se banao, phir yahan bhejo.</i>", parse_mode=HTML)
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

            "📝 <b>Pehle UTR bhejo</b> (text me), phir screenshot.\n"
            "Payment app kholo → transaction details → <b>UTR / Ref No</b> (12 digit) copy karke yahan bhejo.\n"
            "❓ Samajh nahi aa raha kahan milega? Neeche button par tap karo.",
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
        await update.message.reply_text("✍️ Now send your <b>NAME and DATE OF PHOTO (DOP)</b>:\n(example: <code>RAHUL SHARMA 30-09-2026</code>)", parse_mode=HTML)
        return

    if mode == "pp_stamp_text":
        # v44: photo dobara bheji gayi → nayi photo lagao, naam-dop phir maango (crash nahi)
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        context.user_data["raw_photo"] = buf.getvalue()
        await update.message.reply_text(
            "🖼️ New photo set ✅\n✍️ Now send your <b>NAME and DATE OF PHOTO (DOP)</b>:\n"
            "(example: <code>RAHUL SHARMA 30-09-2026</code>)", parse_mode=HTML)
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
            caption=spend_credit_msg(uid, "print_sheet") + "\n" + f"🖨️ <b>{to_bold('PRINTABLE 8-IN-1 PASSPORT SHEET READY')}</b>\n\n(4x6 inch lab print sheet @ 300 DPI)",
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
            [InlineKeyboardButton("🟢 100 KB (smallest)", callback_data="doc_kb_100"),
             InlineKeyboardButton("🔵 200 KB", callback_data="doc_kb_200")],
            [InlineKeyboardButton("🟣 300 KB (safe)", callback_data="doc_kb_300"),
             InlineKeyboardButton("🟠 500 KB (best quality)", callback_data="doc_kb_500")],
            [InlineKeyboardButton("⚫ Black & White (smaller)", callback_data="doc_gray")],
            [InlineKeyboardButton(f"✅ {len(pages)} photos made into PDF", callback_data="doc_go")],
        ]
        await update.message.reply_text(
            f"📄 <b>{to_bold('DOCUMENT PDF COMPRESS')}</b>\n\n"
            f"📸 {len(pages)} photos received (marksheet/certificate). Send more or choose the size 👇\n\n"
            "💡 <b>Size guide:</b> government portals usually ask for 100-300 KB.",
            reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
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
    # v49.4: VIP-only
    if PREMIUM_ONLY and not vip_ok(update.effective_user.id):
        await send_vip_wall(update, context)
        return
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

    # ---------- v38: naye tools ke files (PDF / audio / video / image) ----------
    _our_modes = ("bankpdf", "bankpdf_pass", "media_ringtone", "media_ringtone_start",
                  "media_karaoke", "media_8d", "media_bass", "media_voice_wait", "media_v2mp3",
                  "media_trim_wait", "media_compress_wait", "media_status_audio")
    if mode in _our_modes:
        kind, att, fname, mime = None, None, "", ""
        if msg.document:
            fname = (msg.document.file_name or "").lower()
            mime = (msg.document.mime_type or "").lower()
            att = msg.document
            if "pdf" in mime or fname.endswith(".pdf"):
                kind = "pdf"
            elif mime.startswith("image/") or fname.endswith((".jpg", ".jpeg", ".png", ".webp")):
                kind = "image"
            elif mime.startswith("audio/") or fname.endswith((".mp3", ".m4a", ".wav", ".ogg", ".opus", ".aac")):
                kind = "audio"
            elif mime.startswith("video/") or fname.endswith((".mp4", ".mkv", ".mov", ".webm", ".3gp")):
                kind = "video"
        elif msg.video:
            kind, att = "video", msg.video
        elif msg.animation:
            kind, att = "video", msg.animation
        elif msg.video_note:
            kind, att = "video_note", msg.video_note
        elif msg.audio:
            kind, att = "audio", msg.audio
        elif msg.voice:
            kind, att = "voice", msg.voice
        if kind and att is not None:
            try:
                if getattr(att, "file_size", 0) and att.file_size > 20 * 1024 * 1024:
                    await msg.reply_text("⚠️ The file is bigger than 20MB — that is the Telegram bot limit. Send a smaller file "
                                         "(for videos, use ✂️ TRIM first).", parse_mode=HTML)
                    return
                tf = await att.get_file()
                buf = io.BytesIO()
                await tf.download_to_memory(buf)
                handled = await handle_new_tool_file(update, context, uid, msg, mode, kind, buf.getvalue(), mime)
                if handled:
                    return
            except Exception as e:
                await msg.reply_text(fail_msg("FILE ERROR", str(e)[:150]), parse_mode=HTML)
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


# ---------------- ERROR HANDLER ----------------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Exception handling update: %s", context.error)
    # v50: user bhi jaane ki koi chhota ghatna hua — chup-chaap na mile
    try:
        msg = getattr(update, "effective_message", None)
        if msg is not None:
            await msg.reply_text(
                "⚠️ <b>Chhota sa ghatna ho gaya!</b> Ye kaam nahi ho paya.\n"
                "10 second baad dobara try karo. Problem bar-bar ho to Support: @Supermannn_x",
                parse_mode=HTML)
    except Exception:
        pass


# ---------------- POST INIT ----------------
async def _post_init(app: Application):
    commands = [
        BotCommand("start", "Bot chalu karo / menu kholo"),
        BotCommand("menu", "Saare tools ka menu"),
        BotCommand("premium", "VIP plan lo (unlimited)"),
        BotCommand("refer", "Dost ko bulao = free VIP"),
        BotCommand("account", "Mera account aur credits"),
        BotCommand("cancel", "Chalu kaam band karo"),
        BotCommand("refresh", "Menu / keyboard naya karo"),
    ]
    await app.bot.set_my_commands(commands)
    log.info("Commands set ho gaye ✅")


# ---------------- v49.7 KEEPALIVE PINGER (hub ko ping -> dono 24/7 jaagte hain) ----------------
# Render free plan 15 min inactivity par service sula deta hai. Bot aur hub ab ek dusre ko
# ping karte hain, isliye dono hamesha jaagte rehte hain — koi bahar ki service nahi chahiye.
_KEEPALIVE_PEERS = [u.strip() for u in (
    os.environ.get("KEEPALIVE_PEERS") or "https://osint-api-hub.onrender.com/health"
).replace(";", ",").split(",") if u.strip()]
try:
    _KEEPALIVE_MINUTES = float(os.environ.get("KEEPALIVE_MINUTES") or 10)
except Exception:
    _KEEPALIVE_MINUTES = 10.0
_KEEPALIVE_STATE = {"last_run": None, "last_ok": None, "runs": 0}


def _keepalive_pinger():
    """Pehli ping 90 sec me, phir har ~10 min — Render free plan par bot+hub 24/7 ON."""
    import time as _t
    import urllib.request
    _first = True
    while True:
        _t.sleep(90.0 if _first else max(120.0, _KEEPALIVE_MINUTES * 60))
        _first = False
        for url in list(_KEEPALIVE_PEERS):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "utility-duniya-bot/keepalive"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    _KEEPALIVE_STATE.update({"last_run": time.strftime("%d-%m-%Y %H:%M"),
                                             "last_ok": r.status < 500,
                                             "runs": _KEEPALIVE_STATE["runs"] + 1})
            except Exception as e:
                _KEEPALIVE_STATE.update({"last_run": time.strftime("%d-%m-%Y %H:%M"),
                                         "last_ok": False, "last_error": str(e)[:80]})
                log.debug("keepalive ping fail: %s", e)


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
            _ka = (f"keepalive pinger: last {_KEEPALIVE_STATE.get('last_run')} | ok={_KEEPALIVE_STATE.get('last_ok')}"
                   f" | runs={_KEEPALIVE_STATE.get('runs')}")
            html = ("<h1>Utility Duniya Super Bot chal raha hai - 24/7 ON. Status: 200 OK</h1>"
                    f"<p style='font-family:monospace'>version: {BOT_VERSION}</p>"
                    f"<p style='font-family:monospace'>{_ka}</p>"
                    f"<p style='font-family:monospace'>peers: {', '.join(_KEEPALIVE_PEERS)}</p>")
            self.wfile.write(html.encode("utf-8"))

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

    # Tutorial page (telegra.ph) — background me banta/update hota hai, bot rukta nahi
    threading.Thread(target=publish_tutorial_now, daemon=True).start()

    # ---------- MODE DECIDE (crash-proof) ----------
    # v49.4: webhook tabhi jab WEBHOOK_MODE=on ho AUR URL sach me kaam kare.
    # Pehle yahi RENDER_EXTERNAL_URL se khud webhook on kar deta tha — Render ke
    # free plan par deploy ke waqt DNS ready nahi hota tha aur bot
    # "Bad webhook: failed to resolve host" par CRASH ho jata tha (aapka deploy fail).
    global WEBHOOK_URL
    _wh_ok, _wh_why = (False, "polling mode")
    if WEBHOOK_URL:
        _wh_ok, _wh_why = webhook_url_usable(WEBHOOK_URL)
        if not _wh_ok:
            log.warning("WEBHOOK chalu nahi ho sakta (%s) — ab POLLING par chalega", _wh_why)
            WEBHOOK_URL = ""
    if not WEBHOOK_URL:
        log.warning("MODE = POLLING (safe default) | %s", _wh_why)

    # Keepalive server SIRF polling mode me — webhook mode me yehi port PTB use karega
    if not WEBHOOK_URL:
        threading.Thread(target=_keepalive, daemon=True).start()

    # v49.7: bahar ki taraf ping (hub ko) -> Render free plan par bot+hub dono jaagte rehte hain
    if os.environ.get("KEEPALIVE_ENABLED", "1") != "0" and _KEEPALIVE_PEERS:
        threading.Thread(target=_keepalive_pinger, daemon=True).start()
        log.info("Keepalive pinger ON → %s (har %s min)", ", ".join(_KEEPALIVE_PEERS), _KEEPALIVE_MINUTES)

    app = (Application.builder().token(BOT_TOKEN).post_init(_post_init)
           .connect_timeout(30.0).read_timeout(60.0).write_timeout(240.0)
           .media_write_timeout(300.0).pool_timeout(60.0).build())

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler(["refresh", "newmenu"], cmd_refresh))
    app.add_handler(CommandHandler("help", cmd_tutorial))
    app.add_handler(CommandHandler(["tutorial", "madad", "guide"], cmd_tutorial))
    app.add_handler(CommandHandler(["activate", "grantvip"], cmd_activate))
    app.add_handler(CommandHandler("tutrefresh", cmd_tutrefresh))
    app.add_handler(CommandHandler(["vehstatus", "vehicleapi"], cmd_vehstatus))
    app.add_handler(CommandHandler(["imeistatus", "imeiapi"], cmd_imeistatus))
    app.add_handler(CommandHandler(["hubstatus", "hubapi", "api"], cmd_hubstatus))
    app.add_handler(CommandHandler(["credits", "addcredits"], cmd_credits))
    app.add_handler(CommandHandler("account", cmd_account))
    app.add_handler(CommandHandler("refer", cmd_refer))
    app.add_handler(CommandHandler("premium", cmd_premium))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler(["sys", "system", "health"], cmd_sys))
    app.add_handler(CommandHandler(["payments", "pending"], cmd_payments))
    app.add_handler(CommandHandler("mypay", cmd_mypay))
    app.add_handler(CommandHandler("revoke", cmd_revoke))
    app.add_handler(CommandHandler("grant", cmd_grant))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))

    # Specific Tool Commands
    # v49.4: tool commands bhi VIP-only (gate andar hai)
    async def _cmd_vnum(u, c):
        if await vip_gate(u):
            await send_vnum_card(u, c)

    async def _cmd_terabox(u, c):
        if await vip_gate(u):
            await u.message.reply_text(tool_prompt("terabox"), reply_markup=tool_tutorial_kb("terabox"), parse_mode=HTML)

    async def _cmd_cloner(u, c):
        if await vip_gate(u):
            await u.message.reply_text(f"🔄 <b>{to_bold('CHANNEL CLONER')}</b>", reply_markup=get_cloner_settings_kb(u.effective_user.id), parse_mode=HTML)

    async def _cmd_sarkari(u, c):
        if await vip_gate(u):
            await u.message.reply_text(SARKARI_CITIZEN_TEXT, reply_markup=get_sarkari_citizen_kb(), parse_mode=HTML)

    app.add_handler(CommandHandler("vnum", _cmd_vnum))
    app.add_handler(CommandHandler("terabox", _cmd_terabox))
    app.add_handler(CommandHandler("cloner", _cmd_cloner))
    app.add_handler(CommandHandler("sarkari", _cmd_sarkari))

    # Callbacks
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
    # ---------- v47+: WEBHOOK MODE (Render par sabse safe) ----------
    # Polling me har deploy par 10-20 second tak do instance ek saath getUpdates
    # karte hain -> Telegram "Conflict: terminated by other getUpdates request".
    # Webhook me Telegram khud update bhejta hai, getUpdates hota hi nahi -> Conflict kabhi nahi.
    if WEBHOOK_URL:
        from modules.render_health import install_webhook_health_routes
        install_webhook_health_routes()
        port = int(os.environ.get("PORT", "10000"))
        secret = (os.environ.get("WEBHOOK_SECRET") or BOT_TOKEN.split(":")[-1]).strip("/")
        path = f"/webhook/{secret}"
        full_url = WEBHOOK_URL.rstrip("/") + path
        # Secret webhook path ko logs me kabhi print na karein.
        log.warning("WEBHOOK MODE | instance=%s pid=%s | polling OFF (koi Conflict nahi)",
                    socket.gethostname(), os.getpid())
        try:
            app.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=path,
                webhook_url=full_url,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                secret_token=(os.environ.get("WEBHOOK_SECRET_TOKEN") or None) or None,
            )
            return
        except Exception as e:                                  # noqa: BLE001
            # v49.4: webhook fail (DNS/Telegram error) — bot band NAHI hoga, polling par switch
            log.error("Webhook fail ho gaya (%s: %s) — ab POLLING par switch kar raha hoon",
                      type(e).__name__, str(e)[:200])
            try:
                app.bot.delete_webhook(drop_pending_updates=True)
            except Exception:                                   # noqa: BLE001
                pass

    log.warning("STARTING POLLING | instance=%s pid=%s | only ONE instance must run",
                socket.gethostname(), os.getpid())
    # v49.4: Conflict (do instance ek saath) par crash na ho — thoda ruk kar retry
    for _try in range(1, 6):
        try:
            app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES,
                            close_loop=False)
            return
        except Exception as e:                                  # noqa: BLE001
            _msg = str(e).lower()
            log.error("Polling band hui (%s: %s)", type(e).__name__, str(e)[:200])
            if "conflict" in _msg and _try < 5:
                wait = 15 * _try
                log.warning("Do instance ek saath chal rahe hain — %ss baad dobara koshish (%s/5)", wait, _try)
                time.sleep(wait)
                continue
            if _try < 5:
                log.warning("5 second baad dobara koshish (%s/5)", _try)
                time.sleep(5)
                continue
            raise


if __name__ == "__main__":
    main()
