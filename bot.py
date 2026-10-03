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
import socket
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
# Full-Auto Channel Cloner helper (safety import)
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

    check_link_safety,
    expand_url,

    rate_from_per_hundred,
    shorten_url,
    village_compound_interest,
)
from modules.vehicle_challan import (
    render_report as render_vehicle_report,
    valid_plate as vehicle_plate_ok,
)
# ---- OSINT hub: health-only status; private lookups retired ----
from modules import osint_hub as hub
from modules.osint_hub import (
    is_configured as vehicle_api_ready,
    vehicle_report_v2 as hub_vehicle,
)
from modules import clip_maker as clipm
from modules import ai_brain as aib
from modules.clip_maker import (
    CLIP_COUNT as CLIP_MAKER_COUNT,
    MAX_MINUTES as CLIP_MAKER_MAX_MIN,
    TARGET_LEN as CLIP_MAKER_LEN,
    best_of_best as clips_best_of_best,
    caption_for as clips_caption,
    cleanup as clips_cleanup,
    download_direct as clips_download_direct,
    fmt_t as clips_fmt_t,
    help_card as clips_help_card,
    is_direct_video_url as clips_is_direct_url,
    is_youtube_url as clips_is_yt_url,
    probe_info as clips_probe,
    ytdlp_available as clips_ytdlp_available,
    youtube_download as clips_youtube_download,
)
from modules.render_health import webhook_url_from_env
from modules.imei_lookup import (
    device_title as imei_title,
    fallback_links as imei_fallback_links,
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
    check_username_platforms,
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

    pages_to_pdf,

    site_screenshot,

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
# Render ka webhook default overlapping polling instances se Telegram Conflict rokta hai.
WEBHOOK_URL = webhook_url_from_env()
# purana daily-limit constant (v36 tak) — ab credits system hai; sirf backward-compat ke liye rakha hai
FREE_LIMIT = int(os.getenv("FREE_LIMIT", "10") or 10)
async def hub_with_progress(wait_msg, hub_fn, arg, what="", timeout=24):
    """Hub API ko background me chalao aur user ko LIVE progress dikhao.

    Pehle bot 60 second tak chup rehta tha - user ko lagta tha bot mar gaya.
    Ab har 6 sec me "data aa raha hai... Xs" dikhta hai, aur 24 sec ke baad
    bhi result na aaye to call background me chalti rehti hai aur result
    baad me bhej diya jata hai (deliver_hub_later).

    Returns: (result_dict | None, task)
             None  ->  abhi tak nahi aaya, task abhi bhi chal raha hai
    """
    loop = asyncio.get_running_loop()
    task = loop.create_task(asyncio.to_thread(hub_fn, arg))
    waited = 0
    while waited < timeout:
        try:
            res = await asyncio.wait_for(asyncio.shield(task), timeout=6)
            return (res if isinstance(res, dict) else {}), task
        except asyncio.TimeoutError:
            waited += 6
            try:
                await wait_msg.edit_text(
                    f"\U0001f50e <b>{hesc(what or 'Searching...')}</b>\n"
                    f"<i>Source se data aa raha hai... <b>{waited}s</b> ho gaye.</i>\n"
                    "Bas thoda aur wait karein \u23f3", parse_mode=HTML)
            except Exception:                                    # noqa: BLE001
                pass
        except Exception as e:                                   # noqa: BLE001
            return {"ok": False, "has_data": False,
                    "error": clean_err(str(e), 120)}, task
    return None, task


async def deliver_hub_later(task, context, chat_id, build_fn):
    """Hub call der se poora ho to result baad me yahin bhej do (60s tak bhi)."""
    try:
        res = await task
    except Exception as e:                                       # noqa: BLE001
        res = {"ok": False, "has_data": False, "error": clean_err(str(e), 120)}
    if not isinstance(res, dict):
        res = {}
    try:
        text = build_fn(res)
    except Exception:                                            # noqa: BLE001
        text = "\u274c <b>Result taiyar karte waqt error aa gaya.</b> Dobara try karein."
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=HTML)
    except Exception:                                            # noqa: BLE001
        pass


SUPPORT_USERNAME = "@Supermannn_x"
REFER_NEED = int(os.getenv("REFER_NEED", "5") or 5)
HTML = "HTML"
BAN_MSG = "🚫 Your account is banned. Please contact the admin."
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


# ============================================================
#  CREDITS SYSTEM (v37)
#  • Naye user ko 25 credits — EK BAAR KE (daily reset NAHI)
#  • Premium tools (sirf 4): VIDEO DOWNLOADER, NUMBER INFO,
#    CHANNEL CLONER, PRIVATE CHANNEL SETUP — 1 use = 1 credit
#  • Baaki SAARE tools bilkul FREE (koi credit nahi, koi limit nahi)
#  • VIP / Owner / Admin = unlimited (credits nahi lagte)
# ============================================================
PREMIUM_TOOLS = {
    "insta_dl",            # 📥 VIDEO DOWNLOADER
    "numinfo",             # 📱 NUMBER INFO
    "cloner",              # 🔄 CHANNEL CLONER (auto-forward setup)
    "cloner_private_help",  # 🔒 PRIVATE CHANNEL SETUP
    # ---- v38 MARU-TOAD PACK (chhupe tools) ----
    "bankpdf",             # 🏦 BANK STATEMENT PDF → EXCEL
    "kagaz",               # 📜 SARKARI KAGAZ SUITE
    "mediastudio",         # ⚡ MEDIA STUDIO (MP3/STATUS/KARAOKE)
    # ---- VEHICLE RTO + OFFICIAL LINKS; live provider requires explicit authorization ----
    "vehicle",             # 🚗 RTO INFO + OFFICIAL LINKS
    # ---- IMEI / DEVICE MODEL (TAC-only lookup) ----
    "imei",                # 📲 IMEI & PHONE SPEC CARD
    # ---- v43 CLIP MAKER (video → 4-7 clips) ----
    "clips",               # 🎬 CLIP MAKER
    # ---- Aadhaar access: official UIDAI/NFSA portal guidance only ----
    "aadhaar",             # 🆔 OFFICIAL PORTAL GUIDANCE
}

PREMIUM_TOOL_NAMES = {
    "insta_dl": "📥 Video Downloader",
    "numinfo": "📱 Number Info (safe metadata)",
    "cloner": "🔄 Channel Cloner",
    "cloner_private_help": "🔒 Private Channel Setup",
    "bankpdf": "🏦 Bank Statement → Excel",
    "kagaz": "📜 Sarkari Kagaz Suite",
    "mediastudio": "⚡ Media Studio (MP3/Status/Karaoke)",
    "vehicle": "🚗 RTO Info + Official Links",
    "imei": "📲 IMEI / Device Model (TAC)",
    "clips": "🎬 Clip Maker (video → 4-7 clips)",
    "aadhaar": "🆔 Aadhaar (official portal only)",
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
        return "⚡ <b>Credits:</b> 0 / %d — <b>all used!</b> Get VIP for premium tools: /premium" % CREDITS_START
    return f"⚡ <b>Credits:</b> {left} / {CREDITS_START} (for premium tools)"


def can_use_premium_tool(u: dict, uid: int = 0) -> bool:
    """Premium tool chalane layak hai? (VIP/admin hamesha, baaki credits hone par)"""
    return credits_left(u, uid) > 0


def get_credits_over_text(action: str = "") -> str:
    tool_name = PREMIUM_TOOL_NAMES.get(action, "Ye tool")
    return (
        f"⚡ <b>{to_bold('ALL CREDITS USED')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{tool_name} is a <b>premium tool</b>. It uses 1 credit per use.\n"
        f"Your <b>{CREDITS_START} free credits are finished.</b>\n\n"
        "✅ <b>All other tools are still FREE</b> — no credits, no limit:\n"
        "   📸 Passport Photo • 🖨️ 8-in-1 Sheet • 📄 Doc PDF • 🖼️ Image→PDF • 📄 Document Suite\n"
        "   🏦 IFSC • 📮 Pincode • 🆔 ID Finder • 🌐 IP Info • 📷 QR • 📈 Interest Calc • 🧮 Registry Cost...\n\n"
        "👑 <b>Get VIP for the premium tools:</b>\n"
        "• 📥 Video Downloader — <b>unlimited</b>\n"
        "• 📱 Number Info (safe metadata + official safety links) — <b>unlimited</b>\n"
        "• 🆔 Aadhaar — <b>official UIDAI/NFSA portal guide only</b>\n"
        "• 🚗 Vehicle — <b>RTO/state info + official links</b>; live data needs an authorized provider\n"
        "• 🔄 Channel Cloner + Auto-Forward — <b>unlimited</b>\n"
        "• 🔒 Private Channel Setup — <b>unlimited</b>\n"
        "• 🏦 Bank PDF → Excel • 📜 Document Suite • ⚡ Media Studio — <b>unlimited</b>\n"
        "• 📲 IMEI / Device Model (TAC only) — <b>unlimited</b>\n"
        "• 🎬 Clip Maker (video → 4-7 clips) — <b>unlimited</b>\n"
        "• ♾️ Whole bot unlimited (no limits at all)\n\n"
        "🎁 <i>Want VIP free? Share with {n} friends (/refer).</i>"
    ).replace("{n}", str(REFER_NEED))


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
        [InlineKeyboardButton("💎 Get VIP (Unlimited)", callback_data="open_vip_menu")],
        [InlineKeyboardButton("🎬 How to get VIP? (30 sec video)", callback_data="toolvid:premium")],
        [InlineKeyboardButton(f"🎁 Refer & Earn (Free VIP)", callback_data="open_refer_menu"),
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
            f"⚡ <b>1 credit used</b> — <b>0 credits left!</b>\n\n"
            f"That was your last free use of {name}.\n"
            "From now on this premium tool is locked. VIP opens it unlimited. "
            "All free tools keep working without credits. → /premium"
        )
    if left <= 5:
        return (f"⚡ <b>1 credit used</b> — left: <b>{left}/{CREDITS_START}</b>\n"
                f"<i>Only {left} premium uses left, after that VIP is needed (/premium)</i>")
    return f"⚡ <b>1 credit used</b> — left: <b>{left}/{CREDITS_START}</b>"


SUPPORT_USERNAME = "@Supermannn_x"
SUPPORT_LINK = '<a href="https://t.me/Supermannn_x">@Supermannn_x</a>'

# ---- v45 branding: har nayi card par "Powered by @Supermannn_x" ----
BRAND_TAG = os.environ.get("BRAND_TAG", SUPPORT_USERNAME)
BRAND_LINE = f"⚡ Powered by {BRAND_TAG}  |  API Developer / Telegram: {BRAND_TAG}"


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


def _mask_govt_id(val: str) -> str:
    """Aadhaar/Document number partially mask (DPDP-safe). Full chahiye to NUM_SHOW_FULL_IDS=1."""
    if os.environ.get("NUM_SHOW_FULL_IDS") == "1":
        return str(val)
    s = re.sub(r"\D", "", str(val or ""))
    if len(s) <= 8:
        return str(val)
    return f"{s[:4]}{'*' * (len(s) - 8)}{s[-4:]}"


def fail_msg(title: str, reason: str = "") -> str:
    body = f"\n\n{reason}" if reason else ""
    return (
        f"❌ <b>{to_bold(title)}</b>{body}\n\n"
        f"💡 <b>Tip:</b> Try the same tool once more. If the problem stays, contact support: {SUPPORT_LINK}"
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
    "<i>Only for account verification. No spam.</i>"
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
    [f"📮 {to_bold('PINCODE INFO')}", f"🆔 {to_bold('ID & USERNAME FINDER')}"],
    [f"🌐 {to_bold('IP / DOMAIN INFO')}", f"🔒 {to_bold('PRIVATE CHANNEL SETUP')}"],
    [f"📷 {to_bold('QR CODE')}", f"🖼️ {to_bold('IMAGE→PDF')}"],
    [f"🔗 {to_bold('URL SHORT')}", f"🔓 {to_bold('LINK BYPASS')}"],
    [f"🔍 {to_bold('LINK CHECK')}", f"📈 {to_bold('INTEREST CALC')}"],
    [f"📦 {to_bold('APP FINDER')}", f"🖼️ {to_bold('SITE SCREENSHOT')}"],
    [f"🏦 {to_bold('BANK STATEMENT → EXCEL')}", f"📜 {to_bold('SARKARI KAGAZ SUITE')}"],
    [f"⚡ {to_bold('MEDIA STUDIO (MP3/STATUS)')}", f"🚗 {to_bold('RTO + OFFICIAL LINKS')}"],
    [f"📲 {to_bold('IMEI / PHONE DETAILS')}", f"🎬 {to_bold('CLIP MAKER')}"],
    [f"🆔 {to_bold('AADHAAR OFFICIAL PORTALS')}"],
    [f"💎 {to_bold('VIP PREMIUM')}", f"🎁 {to_bold('REFER & EARN')}"],
    [f"👤 {to_bold('MY ACCOUNT')}", f"❓ {to_bold('HELP / TUTORIAL')}"],
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
    "PRIVATE CHANNEL SETUP": "cloner_private_help",
    "IP INFO": "ip",
    "QR (LINK / TEXT)": "qr",
    "QR (WIFI SHARE)": "qr_wifi",
    "QR (CONTACT CARD)": "qr_vcard",
    "SITE SCREENSHOT (HD)": "shot",
    "SITE SCREENSHOT (FULL PAGE)": "shot_full",
    "SARKARI SEVA PORTALS": "sarkari",
    "RTO VEHICLE INFO": "rto",
    "RTO + OFFICIAL LINKS": "rto",
    "VEHICLE INFO + CHALLAN": "rto",
    "VEHICLE INFO": "rto",
    "IMEI / PHONE DETAILS": "imei",
    "IMEI INFO": "imei",
    "IMEI LOOKUP": "imei",
    "PHONE INFO (IMEI)": "imei",
    "CLIP MAKER": "clips",
    "CLIPS MAKER": "clips",
    "VIDEO CLIP MAKER": "clips",
    "NUMBER INFO": "numinfo",
    "AADHAAR OFFICIAL PORTALS": "aadhaar",
    "AADHAAR FAMILY": "aadhaar",
    "AADHAR FAMILY": "aadhaar",
    "AADHAAR": "aadhaar",
    "AADHAAR FAMILY INFO": "aadhaar",
    "IFSC INFO": "ifsc",
    "PINCODE INFO": "pin",
    "ID & USERNAME FINDER": "idfind",
    "QR CODE": "qr",
    "IMAGE→PDF": "pdf",
    "URL SHORT": "short",
    "LINK BYPASS": "linkbypass",
    "LINK CHECK": "linkcheck",
    "INTEREST CALC": "interest",
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
    "SITE SCREENSHOT": "shot",
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
        f"⚡ <b>{to_bold('TERABOX & CLOUD')}</b>\n"
        "✅ <b>Ad-free</b> download + stream (Terabox, Mediafire, Drive, Mega)\n"
        "⚠️ Server rejects sometimes — just send the link again.\n"
        "📌 Example: <code>https://terabox.com/s/xxxxx</code>\n"
        "🔗 <b>Now send your link:</b>"
    ),
    "insta_dl": (
        f"📥 <b>{to_bold('VIDEO DOWNLOADER')}</b>\n"
        "Instagram, YouTube, Facebook, X, TikTok, Pinterest, Reddit (20+ sites)\n"
        "📌 Example: <code>https://www.instagram.com/reel/xxxxx</code>\n"
        "🔗 <b>Now send the video link:</b>"
    ),
    "pp_stamp": (
        f"📸 <b>{to_bold('GOVT EXAM PASSPORT PHOTO')}</b>\n"
        "Send photo → then name → then date. Output: 3.5 × 4.5 cm with name/date stamp.\n"
        "📌 Example: photo, <code>Rahul Kumar</code>, <code>02-10-2026</code>\n"
        "📸 <b>Now send your passport photo:</b>"
    ),
    "print_sheet": (
        f"🖨️ <b>{to_bold('8-IN-1 PRINT SHEET')}</b>\n"
        "One photo → 4×6 inch sheet with 8 copies (print at any shop, ₹10-20).\n"
        "📌 Example: any passport size photo\n"
        "📸 <b>Now send one photo:</b>"
    ),
    "doc_compress": (
        f"📄 <b>{to_bold('DOCUMENT / MARKSHEET PDF')}</b>\n"
        "Marksheet or certificate photo → sharp PDF (100KB-500KB, size buttons come after).\n"
        "📌 Example: 10th marksheet photo\n"
        "📸 <b>Now send the marksheet or certificate photo:</b>"
    ),
    "ip": (
        f"🌐 <b>{to_bold('IP / DOMAIN INFO')}</b>\n"
        "📌 Example: <code>8.8.8.8</code> or <code>google.com</code>\n"
        "👉 <b>Now send the IP or website name:</b>"
    ),
    "bankpdf": (
        f"🏦 <b>{to_bold('BANK STATEMENT PDF TO EXCEL')}</b>\n"
        "Send the <b>PDF file</b> (not a photo). Password PDF? The bot will ask for it.\n"
        "📌 Example: SBI / HDFC / PNB statement PDF\n"
        "📄 <b>Now send your bank statement PDF:</b>"
    ),
    "kagaz": (
        f"📜 <b>{to_bold('DOCUMENT SUITE (BIHAR/UP)')}</b>\n"
        "Rent agreement, affidavit, notice 138, bayana, loan paper, registry cost, bigha→kattha.\n"
        "⚡ 1 credit per document · ⚠️ Get the draft checked by a notary\n"
        "👇 <b>Select your document from the menu below:</b>"
    ),
    "mediastudio": (
        f"⚡ <b>{to_bold('MEDIA STUDIO')}</b>\n"
        "YouTube→MP3, status video, ringtone, karaoke, 8D, voice change, trim, compress. No watermark.\n"
        "👇 <b>Select an option below:</b>"
    ),
    "rto": (
        f"🚗 <b>{to_bold('RTO + OFFICIAL VEHICLE LINKS')}</b>\n"
        "Free me RTO/state format info aur official VAHAN/e-Challan links milenge.\n"
        "Live RC/challan details ke liye authorized provider ya official OTP/CAPTCHA portal zaroori hai; owner ka private data yahan nahi dikhaya jata.\n"
        "📌 Dummy format example: <code>XX00XX0000</code>\n"
        "🔢 <b>Number plate bhejein:</b>"
    ),
    "imei": (
        f"📲 <b>{to_bold('IMEI / DEVICE MODEL')}</b>\n"
        "Apne/authorized device ka 15 digit IMEI bhejein. Sirf pehle 8 digit TAC API ko jayega.\n"
        "Catalog me available brand/model aur specs + <code>.json</code> copy file mil sakti hai; full specs har model ke liye guaranteed nahi.\n"
        "📍 IMEI: phone par <code>*#06#</code> dial karein.\n"
        "🔢 <b>Ab 15 digit IMEI bhejein:</b>"
    ),
    "clips": (
        f"🎬 <b>{to_bold('CLIP MAKER')}</b>\n"
        "Video → 4-7 short clips (25-60 sec). Best moments = loud + action parts.\n"
        "📌 Limit: 15 min · 20MB file · ya direct <code>.mp4</code> link\n"
        "⚠️ Use your own video or one you are allowed to reuse.\n"
        "📸 <b>Now send the video file (or link):</b>"
    ),
    "numinfo": (
        f"📱 <b>{to_bold('NUMBER INFO')}</b>\n"
        "Operator/carrier, circle (region), number type, validity aur spam-safety links.\n"
        "🔒 Naam, family/linked numbers, ghar ka pata ya government-ID leaked databases se fetch nahi hote.\n"
        "📌 Format: <code>XXXXXXXXXX</code> (10 digits)\n"
        "🔢 <b>Apna ya authorized number bhejein:</b>"
    ),
    "aadhaar": (
        f"🆔 <b>{to_bold('AADHAAR / FAMILY')}</b>\n"
        "Is bot me Aadhaar ya family-member lookup nahi hota.\n"
        "Apne record ke liye UIDAI/NFSA ka official portal use karein; OTP/consent wahan required ho sakta hai.\n"
        "🔒 Aadhaar number is chat me mat bhejein."
    ),
    "ifsc": (
        f"🏦 <b>{to_bold('IFSC BANK BRANCH')}</b>\n"
        "Bank, branch, address, MICR (printed on passbook / cheque).\n"
        "📌 Example: <code>SBIN0000001</code>\n"
        "🔤 <b>Now send the IFSC code:</b>"
    ),
    "pin": (
        f"📮 <b>{to_bold('PINCODE & POST OFFICE')}</b>\n"
        "6 digit pincode → district, state + all post offices.\n"
        "📌 Example: <code>800001</code> or <code>Rajendra Nagar</code>\n"
        "📮 <b>Now send the pincode or area name:</b>"
    ),
    "idfind": (
        f"🆔 <b>{to_bold('ID & USERNAME FINDER')}</b>\n"
        "Your ID, someone's ID (forward a message) or @username check on 5 platforms.\n"
        "📌 Example: <code>me</code> / <code>@username</code> / forward any message\n"
        "🆔 <b>Now send me / @username / or forward a message:</b>"
    ),
    "qr": (
        f"📷 <b>{to_bold('HD QR CODE GENERATOR')}</b>\n"
        "📌 Example: <code>https://t.me/utility_duniya_bot</code>\n"
        "🔗 <b>Now send the text or link:</b>"
    ),
    "pdf": (
        f"🖼️ <b>{to_bold('IMAGE TO PDF')}</b> — up to 10 photos\n"
        "Send photos one by one, then tap the button (A4 = best for printing).\n"
        "📌 Example: 3 marksheet photos, then tap <b>A4 PDF</b>\n"
        "📸 <b>Now send your photos:</b>"
    ),
    "short": (
        f"🔗 <b>{to_bold('URL SHORTENER')}</b>\n"
        "📌 Example: <code>https://example.com/very/long/path?x=1</code>\n"
        "🔗 <b>Now send the long link:</b>"
    ),
    "linkbypass": (
        f"🔓 <b>{to_bold('LINK BYPASS')}</b>\n"
        "Real link behind ad links — no ads, no waiting.\n"
        "📌 Example: <code>https://gplinks.co/xxxxx</code>\n"
        "🔗 <b>Now send that link:</b>"
    ),
    "linkcheck": (
        f"🔍 <b>{to_bold('LINK SAFETY CHECK')}</b>\n"
        "Check before opening — fake or safe.\n"
        "📌 Example: <code>http://sbi-kyc-verify.xyz</code>\n"
        "🔍 <b>Now send the link:</b>"
    ),
    "appfind": (
        f"📦 <b>{to_bold('APP FINDER')}</b>\n"
        "Direct links from 8 trusted stores (Play Store, APKPure, UptoDown...).\n"
        "📌 Example: <code>instagram</code>\n"
        "📦 <b>Now send the app name:</b>"
    ),
    "shot": (
        f"🖼️ <b>{to_bold('WEBSITE SCREENSHOT (HD)')}</b>\n"
        "📌 Example: <code>github.com</code>\n"
        "🌐 <b>Now send the website URL:</b>"
    ),
    "shot_full": (
        f"📜 <b>{to_bold('FULL PAGE SCREENSHOT')}</b>\n"
        "Takes 10-20 seconds (full long page).\n"
        "📌 Example: <code>flipkart.com</code>\n"
        "📜 <b>Now send the website URL:</b>"
    ),
    "qr_wifi": (
        f"📶 <b>{to_bold('WIFI SHARE QR')}</b>\n"
        "Guest scans it → phone connects to WiFi automatically.\n"
        "📌 Example: <code>JioFiber_Home</code>\n"
        "📶 <b>Now send the WiFi name (SSID):</b>"
    ),
    "qr_vcard": (
        f"👤 <b>{to_bold('CONTACT CARD QR')}</b>\n"
        "Scan it → contact saves automatically.\n"
        "📌 Example: <code>Himanshu Kumar</code>\n"
        "👤 <b>Now send your name:</b>"
    ),
}
TUTORIAL_TEXT = (
    f"❓ <b>{to_bold('HELP / TUTORIAL — EVERY TOOL IN 1 LINE')}</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"

    "📥 <b>Download & sharing:</b>\n"
    "• VIDEO DOWNLOADER → send an Instagram/YouTube/FB/X link, get the video\n"
    "• TERABOX / CLOUD → TeraBox, Drive, MediaFire or Mega link → direct download link\n"
    "• CHANNEL CLONER → set Source + Target, turn FULL AUTO ON, posts copy by themselves\n"
    "\n"
    "📄 <b>Documents:</b>\n"
    "• DOC PDF COMPRESS → marksheet photo → 100-500KB PDF\n"
    "• IMAGE→PDF → up to 10 photos in one PDF (A4 print ready)\n"
    "• PASSPORT PHOTO → photo + name/date → print-ready photo with stamp\n"
    "• 8-IN-1 SHEET → one photo → 8 copies on a 4x6 sheet\n"
    "• BANK PDF → EXCEL → statement PDF → Excel/CSV table\n"
    "• DOCUMENT SUITE → rent agreement, affidavit, notice, registry cost, bigha/kattha\n"
    "\n"
    "🔍 <b>Information:</b>\n"
    "• RTO → number plate → state + RTO office + official links\n"
    "• NUMBER INFO → 10 digit number → operator, circle, useful links\n"
    "• IFSC → code → bank, branch, MICR\n"
    "• PINCODE → pincode or area name → post offices\n"
    "• IP INFO → IP or website → location, ISP\n"
    "• ID FINDER → <code>me</code> or <code>@username</code> → real check\n"
    "\n"
    "⚡ <b>Media Studio:</b> YouTube→MP3, status video, ringtone, karaoke, 8D, bass boost, voice change, trim, compress\n"
    "\n"
    "🧰 <b>Small tools:</b> QR code, site screenshot, URL short, link bypass, link check, app finder, interest calculator\n"
    "\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⌨️ <b>Commands:</b> /start /menu /help /tutorial /cancel\n"
    "\n"
    "💬 <b>Stuck?</b> Every tool has a 🎬 Tutorial Video button under it. Close any tool with <b>/cancel</b>."
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
            await answer_cb("The video for this tool is coming soon!", True)
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
                text=("⚠️ Could not send the video. You can watch it here:\n"
                      f'🎬 <a href="{urls[0]}">Tutorial Video (30 sec)</a>\n\n'
                      "<i>Tip: the video may take 2-3 seconds to start.</i>"),
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
        "❓ <b>HELP / TUTORIAL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎬 <b>Every tool has its own 30 second video tutorial</b> (with HIMANSHU)!\n\n"
        "<b>How to watch:</b>\n"
        "1️⃣ Open any tool (for example 📥 VIDEO DOWNLOADER)\n"
        "2️⃣ Tap the <b>🎬 Tutorial Video</b> button under it\n"
        "3️⃣ Watch the video — full steps in 30 seconds\n\n"
        "👇 Or open a tool video directly from here:"
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
    "pin": "📮 <b>Now send the pincode or area name</b>:",
    "idfind": "🆔 <b>Now send</b> <code>me</code> / <code>@username</code> / or forward any message:",
    "shot_full": "📜 <b>Now send the website URL:</b>",
    "qr_wifi": "📶 <b>Now send the WiFi name (SSID):</b>",
    "qr_vcard": "👤 <b>Now send your name:</b>",
}


KAGAZ_MENU_TEXT = (
    f"📜 <b>{to_bold('DOCUMENT SUITE (BIHAR/UP)')}</b>\n"
    "Ready drafts: rent agreement, affidavit, notice 138, bayana, loan paper, "
    "registry total cost, bigha/kattha converter.\n"
    "⚡ Every document = <b>1 credit</b> · ⚠️ Get the draft checked by a notary\n"
    "👇 <b>Select from the menu below:</b>"
)

MEDIA_MENU_TEXT = (
    f"⚡ <b>{to_bold('MEDIA STUDIO')}</b>\n"
    "YouTube→MP3, status video, ringtone, karaoke, 8D, bass boost, voice change, "
    "video trim/compress, video→MP3. <b>No watermark.</b>\n"
    "⚡ Every option = <b>1 credit</b>\n"
    "👇 <b>Select from the menu below:</b>"
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
        [InlineKeyboardButton("🧮 Registry Total Cost", callback_data="kagaz_registry"),
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
    return (f"📜 <b>{to_bold('DOCUMENT SUITE')}</b> — {key}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✍️ Type the <b>{label}</b>\n"
            f"<i>(example: {hint})</i>\n"
            f"🚫 To leave it empty, type <code>skip</code> · ❌ To stop, send /start\n"
            f"📊 Step {step + 1} of {len(fields)}")


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
    f"⚡ <b>{to_bold('TOOLVAULT • UTILITY DUNIYA')}</b> ⚡\n"
    "<blockquote>30+ High-Power Automation Tools • Instant 1-Sec Response 🚀</blockquote>\n\n"
    f"🔥 <b>{to_bold('POPULAR UTILITIES')}:</b>\n"
    f"• 🌐 <b>{to_bold('Virtual Numbers')}:</b> OTP numbers for WhatsApp &amp; TG\n"
    f"• ⚡ <b>{to_bold('Terabox DL')}:</b> Ad-free direct bypass\n"
    f"• 🔄 <b>{to_bold('Channel Cloner')}:</b> Auto-forward with custom branding\n"
    f"• 📸 <b>{to_bold('Insta Downloader')}:</b> Reels, Posts &amp; Stories (100% Sound)\n"
    f"• 📸 <b>{to_bold('Cyber Studio')}:</b> Name/Date photo, Signature clean\n"
    f"• 🏛️ <b>{to_bold('Sarkari Portals')}:</b> Direct official Govt links\n\n"
    "👇 <b>Tap any tool in the menu below</b>"
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
                await update.message.reply_text("🎉 Welcome! Thanks for joining with a referral link!")
                if count % REFER_NEED == 0:
                    grant_premium(ref_id, 30)
                    try:
                        await context.bot.send_message(ref_id, f"🎉 Congrats! {count} referrals done! You got 30 days VIP free 💎")
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
    await update.message.reply_text("✅ Cancelled! Your tools menu is ready 👇", reply_markup=kb_for(update.effective_user.id))


async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_ = update.effective_user.id
    u = get_user(uid_, update.effective_user.first_name)
    vip_status = "👑 ACTIVE VIP" if is_premium(u) else ("👑 OWNER/ADMIN" if is_admin(uid_) else "🆓 Free User")
    expiry = premium_expiry(u)
    left = credits_left(u, uid_)
    cred_line = "♾️ Unlimited (VIP)" if left >= 999999 else f"{left} / {CREDITS_START}"
    if left < 999999 and left <= 0:
        cred_line += " — <b>finished!</b> (get VIP for premium tools)"
    text = (
        f"👤 <b>{to_bold('MY ACCOUNT DETAILS')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Name:</b> {hesc(u.get('name', 'User'))}\n"
        f"• <b>User ID:</b> <code>{u.get('user_id')}</code>\n"
        f"• <b>Status:</b> {vip_status}\n"
        f"• <b>VIP Expiry:</b> {expiry}\n"
        f"• ⚡ <b>Credits (for premium tools):</b> {cred_line}\n"
        f"• <b>Referrals:</b> {u.get('referrals', 0)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🆓 <b>FREE tools</b> — always free, no credits (passport photo, PDF, IFSC, QR, link tools... all)\n"
        "💎 <b>PREMIUM tools</b> — 1 credit per use: 📥 Video Downloader · 📱 Number Info · "
        "🆔 Aadhaar Official Portals · 🚗 RTO + Official Links · 📲 IMEI · 🔄 Channel Cloner · "
        "🔒 Private Channel Setup · 🏦 Bank PDF → Excel · 📜 Document Suite · ⚡ Media Studio · "
        "🎬 Clip Maker\n\n"
        f"🎁 <i>Free VIP: share with {REFER_NEED} friends (/refer) — or get it from /premium.</i>"
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
        f"Share this bot with your friends and get **30 days VIP Access FREE**!\n\n"
        f"📊 <b>Your referrals:</b> {u.get('referrals', 0)}\n"
        f"🎯 <b>Target:</b> every {REFER_NEED} referrals = 30 Days VIP Free\n\n"
        f"🔗 <b>Your Personal Invite Link:</b>\n<code>{ref_link}</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Share on Telegram", url=f"https://t.me/share/url?url={quote(ref_link)}&text={quote('🔥 Check out Utility Duniya Super Bot!')}")],
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
    rows.append([InlineKeyboardButton("📜 Manual VIP Log", callback_data="admgiftlist"),
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
            f"❌ <b>User not found:</b> <code>{hesc(raw_key)}</code>\n\n"
            "• <b>User ID</b> (example <code>8607774564</code>) — the person must have started the bot once\n"
            "• Or the same <b>@username</b> the person set in the bot\n\n"
            "➡️ Type it like this: <code>/activate 123456789</code>",
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
            [InlineKeyboardButton("📜 Manual VIP Log", callback_data="admgiftlist"),
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
            "All tools are now <b>unlimited</b> 🚀\n"
            "(The admin gave you this VIP — no payment needed.)",
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
            "📥 Video Downloader · 📱 Number Info · 🆔 Aadhaar Official Portals · 🚗 RTO + Official Links · 📲 IMEI · "
            "🔄 Cloner · 🔒 Private Setup · 🏦 Bank PDF → Excel · "
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


# ---------------- v43: CLIP MAKER ----------------
def clip_choice_kb(mode=None, vertical=None, use_ai=None):
    def _tick(txt, on):
        return txt + ("  ✅" if on else "")
    if use_ai is None:
        use_ai = aib.ai_available()
    rows = [
        [InlineKeyboardButton(_tick("🎯 Best Moments", mode == "smart"), callback_data="clmode:smart"),
         InlineKeyboardButton(_tick("⏱️ Equal Parts", mode == "equal"), callback_data="clmode:equal")],
        [InlineKeyboardButton(_tick("🖥️ Normal 16:9", vertical is False), callback_data="clorient:169"),
         InlineKeyboardButton(_tick("📱 9:16 (Shorts)", vertical is True), callback_data="clorient:916")],
        [InlineKeyboardButton(_tick("🧠 Smart AI", use_ai), callback_data="clai:toggle")],
        [InlineKeyboardButton("🚀 Make clips", callback_data="clipgo")],
    ]
    return InlineKeyboardMarkup(rows)


def clip_choice_text(mode=None, vertical=None, use_ai=None) -> str:
    m = "🎯 Best Moments" if mode != "equal" else "⏱️ Equal Parts"
    o = "📱 9:16 (Shorts)" if vertical else "🖥️ 16:9 (normal)"
    if use_ai is None:
        use_ai = aib.ai_available()
    ai_line = (f"🧠 Smart AI: <b>ON</b> · {hesc(aib.ai_label())}\n"
               "<i>AI video dekhta hai — funny/loud/action wale asli best moments.</i>\n"
               if use_ai else
               "🧠 Smart AI: <b>OFF</b> · classic loud+scene analysis\n")
    return (
        "🎬 <b>CLIP MAKER</b>\n"
        f"Mode: <b>{m}</b> · Format: <b>{o}</b> · Clips: <b>{CLIP_MAKER_COUNT}</b>\n"
        f"{ai_line}"
        "👇 Setting badlo ya seedha <b>🚀 Make clips</b> dabao:"
    )


async def send_clips_now(context, chat_id: int, uid: int, status, src_path: str,
                         mode: str, vertical: bool, use_ai: bool = False) -> bool:
    """Clips banao + bhejo. Success par True. Credit sirf success par katta hai."""
    t0 = time.time()
    ai_moments, ai_engine, ai_note = None, "", ""
    # 🧠 AI step (v44): AI ke paas kaam do — fail ho to classic engine chalta rahega
    if use_ai and aib.ai_available() and mode == "smart":
        try:
            await status.edit_text(
                "🧠 <b>AI video dekh raha hai…</b>\n"
                "<i>Funny / loud / action wale asli best moments dhoond raha hoon. "
                "1-3 min lag sakte hain.</i>", parse_mode=HTML)
        except Exception:
            pass
        try:
            info_ai = await asyncio.to_thread(clipm.probe_info, src_path)
            dur_ai = float(info_ai.get("duration") or 0)

            ai_res = await asyncio.to_thread(aib.plan_moments, src_path, dur_ai,
                                             CLIP_MAKER_COUNT, 15.0, float(CLIP_MAKER_LEN), None, None)
            if ai_res.get("ok") and ai_res.get("moments"):
                ai_moments = ai_res["moments"]
                ai_engine = str(ai_res.get("engine") or "AI")
                tr = int(ai_res.get("transcript") or 0)
                ai_note = f"🧠 AI: {hesc(ai_engine)}" + (f" · transcript {tr} lines" if tr else "")
            else:
                ai_note = f"⚠️ AI skip: {hesc(str(ai_res.get('error'))[:90])}"
        except Exception as e:
            ai_note = f"⚠️ AI skip: {hesc(str(e)[:80])}"
    try:
        res = await asyncio.to_thread(clipm.analyze, src_path, mode, vertical, CLIP_MAKER_COUNT,
                                      ai_moments, ai_engine)
    except Exception as e:
        res = {"ok": False, "error": f"Clip engine error: {str(e)[:120]}"}
    if not res.get("ok"):
        err = hesc(str(res.get("error") or "Clips could not be made.")[:220])
        try:
            await status.edit_text(
                "❌ <b>CLIPS NOT MADE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ {err}\n"
                "✅ <b>No credit was cut</b> — you can try again.", parse_mode=HTML)
        except Exception:
            pass
        clips_cleanup(res.get("outdir") or "")
        add_use(uid)
        return False

    clips = res.get("clips") or []
    best_idx = {c.get("idx") for c in clips_best_of_best(clips)}
    try:
        await status.edit_text(
            f"✂️ <b>{len(clips)} clips ready</b> — sending now…\n"
            + (f"<i>{ai_note}</i>\n" if ai_note else "")
            + f"<i>{res.get('scenes', 0)} scene cuts · {res.get('loud_peaks', 0)} loud moments mile</i>",
            parse_mode=HTML)
    except Exception:
        pass

    sent = 0
    for c in clips:
        cap = clips_caption(c, len(clips), vertical)
        if c.get("idx") in best_idx:
            cap += "\n🔥 <b>Best of best</b>"
        try:
            with open(c["path"], "rb") as fh:
                await context.bot.send_video(
                    chat_id=chat_id, video=fh, caption=cap, parse_mode="HTML",
                    width=int(c.get("width") or 0) or None, height=int(c.get("height") or 0) or None,
                    duration=int(c.get("dur") or 0) or None, supports_streaming=True)
            sent += 1
        except RetryAfter as e:
            await asyncio.sleep(float(getattr(e, "retry_after", 3)) + 1)
            try:
                with open(c["path"], "rb") as fh:
                    await context.bot.send_video(chat_id=chat_id, video=fh, caption=cap,
                                                 parse_mode="HTML", supports_streaming=True)
                sent += 1
            except Exception:
                pass
        except Exception as e:
            log.warning("clip send fail: %s", e)
        await asyncio.sleep(0.7)

    clips_cleanup(res.get("outdir") or "")
    clips_cleanup(os.path.dirname(src_path) if src_path else "")

    if not sent:
        try:
            await status.edit_text("❌ The clips were made but could not be sent — please try again. "
                                   "No credit was cut.", parse_mode=HTML)
        except Exception:
            pass
        add_use(uid)
        return False

    try:
        await status.edit_text(
            f"✅ <b>{sent} clips sent</b> ({'9:16' if vertical else '16:9'}) — "
            f"took {int(time.time() - t0)} sec.\n"
            "🔥 = best of best (score-wise top). Baaki clips upar hain.", parse_mode=HTML)
    except Exception:
        pass
    await context.bot.send_message(chat_id=chat_id, text=spend_credit_msg(uid, "clips"), parse_mode=HTML)
    add_use(uid)
    return True


async def start_clip_job(context, chat_id: int, uid: int, src_path: str, mode: str, vertical: bool,
                         use_ai: bool = False):
    status = await context.bot.send_message(
        chat_id=chat_id,
        text=("🔍 <b>Analysing the video…</b>\n<i>Loud moments + scene cuts dekh raha hoon. "
              "10-15 min video par 1-3 minute lag sakte hain.</i>"),
        parse_mode=HTML)
    await send_clips_now(context, chat_id, uid, status, src_path, mode, vertical, use_ai)


async def cmd_vehstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/vehstatus — safe config check only; never queries a sample plate."""
    if not is_admin(update.effective_user.id):
        return
    if not vehicle_api_ready():
        await update.message.reply_text(
            "🚗 <b>Live vehicle/challan provider configured nahi hai.</b>\n\n"
            "Abhi bot sirf RTO/state info aur official VAHAN/e-Challan links dikhata hai.\n"
            "Live lookup tabhi enable karein jab provider ki written authorization ho; "
            "/vehstatus kisi real number plate ko test nahi karta.",
            parse_mode=HTML)
        return
    await update.message.reply_text(
        "✅ <b>Authorized provider config detected.</b>\n"
        "🔒 Privacy ke liye /vehstatus koi sample plate ya owner record query nahi karta.\n"
        "Provider ka health/status check uske documented health endpoint se alag se karein.",
        parse_mode=HTML)


async def cmd_hubstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/hubstatus — admin health check only; no personal identifiers are queried."""
    if not is_admin(update.effective_user.id):
        return
    st = await update.message.reply_text("🔌 <b>Hub health check…</b>\n<i>Koi phone/plate/Aadhaar query nahi hoga.</i>",
                                         parse_mode=HTML)
    try:
        txt = await asyncio.to_thread(hub.hub_status)
    except Exception as e:                                       # noqa: BLE001
        txt = f"❌ <b>Hub test failed:</b> {clean_err(str(e), 200)}"
    try:
        await st.edit_text(txt, parse_mode=HTML)
    except Exception:                                            # noqa: BLE001
        await update.message.reply_text(txt, parse_mode=HTML)


async def cmd_imeistatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/imeistatus — admin: check the IMEI API is working (live test)."""
    if not is_admin(update.effective_user.id):
        return
    if not imei_api_ready():
        await update.message.reply_text(
            "⚠️ <b>IMEI device catalog configured nahi hai.</b>\n\nRender → Environment me ye values rakhein:\n"
            "<code>IMEI_API_BASE=https://osint-api-hub.onrender.com/api</code>\n"
            "<code>IMEI_API_KEY=Demo</code>\n"
            "<i>Bot network par sirf 8-digit TAC bhejta hai; full IMEI nahi.</i>",
            parse_mode=HTML)
        return
    args = [a.strip() for a in (context.args or []) if a.strip()]
    ok15, imei_in, imei_e = imei_validate(args[0] if args else "353010111111110")
    if not ok15:
        await update.message.reply_text(f"❌ {imei_e}", parse_mode=HTML)
        return
    st = await update.message.reply_text(
        f"🔎 Testing the device catalog with TAC <code>{hesc(imei_in[:8])}</code> only…",
        parse_mode=HTML)
    res = fetch_imei_details(imei_in, use_cache=False)
    if res.get("ok"):
        await st.edit_text(
            "✅ <b>TAC/device-model lookup working hai</b>\n"
            f"📲 <b>{hesc(imei_title(res))}</b>\n"
            f"• Brand: {hesc(str(res.get('brand') or '-'))}\n"
            f"• Catalog sections: {len(res.get('sections') or [])} (full specs har model ke liye available nahi)\n"
            f"• JSON file: {len(imei_specs_json(res))} bytes · {hesc(imei_specs_filename(res))}\n"
            f"• Photo: {'✅' if res.get('photo') else '❌'}\n\n" +
            hesc(render_imei_text(res))[:900], parse_mode=HTML)
    else:
        await st.edit_text(f"❌ <b>IMEI API test failed:</b> {hesc(str(res.get('error'))[:200])}\n\n"
                           "Check IMEI_API_BASE / IMEI_API_KEY.", parse_mode=HTML)


async def cmd_aistatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/aistatus — admin: AI Brain ka status + live test."""
    if not is_admin(update.effective_user.id):
        return
    st = await update.message.reply_text("🧠 <b>AI Brain check kar raha hoon…</b>", parse_mode=HTML)
    card = aib.status_card()
    if not aib.ai_available():
        await st.edit_text(card, parse_mode=HTML)
        return
    res = await asyncio.to_thread(aib.live_test)
    if res.get("ok"):
        await st.edit_text(card + f"\n• Live test: ✅ <b>working</b> ({hesc(str(res.get('say')))} · "
                                  f"{hesc(str(res.get('engine')))})", parse_mode=HTML)
    else:
        await st.edit_text(card + f"\n• Live test: ❌ {hesc(str(res.get('error'))[:150])}", parse_mode=HTML)


async def cmd_clipstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/clipstatus — admin: clip engine ready hai ya nahi (ffmpeg + limits)."""
    if not is_admin(update.effective_user.id):
        return
    ff = clipm.ffmpeg_path()
    ok_ff = bool(ff and (os.path.exists(ff) or __import__("shutil").which(ff)))
    await update.message.reply_text(
        "🎬 <b>CLIP MAKER — status</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• ffmpeg: {'✅ ' + hesc(ff[:60]) if ok_ff else '❌ not found (Render build me ffmpeg install karo)'}\n"
        f"• Limit: <b>{int(CLIP_MAKER_MAX_MIN)} min</b> video · <b>{CLIP_MAKER_COUNT}</b> clips · "
        "clip 25-60 sec\n"
        f"• YouTube (yt-dlp): {'✅ available' if clips_ytdlp_available() else '❌ not installed (file ya direct .mp4 link chalega)'}\n"
        f"• Direct .mp4 link download: ✅\n"
        f"• 🧠 AI Brain: {'✅ ' + hesc(aib.ai_label()) if aib.ai_available() else '❌ off (GEMINI_API_KEY / GROQ_API_KEY set karo)'}\n"
        f"• Output: 16:9 (480p) ya 9:16 (540x960)\n"
        "• 🧠 AI: sirf <b>🎯 Best Moments</b> mode me lagta hai (Equal Parts me nahi)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Test: menu se 🎬 CLIP MAKER kholo aur ek chhota video bhejo.</i>",
        parse_mode=HTML)


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

            f"👑 <b>You are the OWNER / ADMIN of this bot</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Everything is <b>unlimited</b> for you — no daily limit, no VIP payment.\n"
            "You never need to buy premium 😄\n"
            "💳 <b>Pending payments (to verify):</b> \n"
            "👉 To verify payments open <b>/payments</b> or <b>/admin</b>.",
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
        f"\n🎟️ <i>Note: every new user gets {CREDITS_START} free credits for the premium tools "
        "(Video Downloader, Number Info, Cloner, Bank PDF, Document Suite, Media Studio). "
        "All other tools are always free.</i>\n\n"
        "👉 Select a plan and pay with the instant QR code:"
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
        f"🎟️ <b>Users with credits:</b> {credits_stats()['with_credits']} · <b>finished:</b> {credits_stats()['out_of_credits']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 Pick anything from the menu below:"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💳 Pending Payments ({pend})", callback_data="admpay_list"),
         InlineKeyboardButton("🧾 Payment History", callback_data="admhist")],
        [InlineKeyboardButton("🎁 VIP Activate (friend / direct payment)", callback_data="admact_home")],
        [InlineKeyboardButton("👥 Recent Users", callback_data="admusers"),
         InlineKeyboardButton("🔍 User Search / Give VIP", callback_data="admsearch")],
        [InlineKeyboardButton("🚫 Ban / Unban", callback_data="admbanmenu"),
         InlineKeyboardButton("📢 Broadcast", callback_data="admbcmenu")],
        [InlineKeyboardButton("📜 Manual VIP Log", callback_data="admgiftlist"),
         InlineKeyboardButton("📖 Text Tutorial Page (admin)", callback_data="admtut")],
        [InlineKeyboardButton("📊 Command List", callback_data="admcmds")],
    ])
    await message.reply_text(text, reply_markup=kb, parse_mode=HTML)


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
        [InlineKeyboardButton("📩 Ask the user again", callback_data=f"askpay:{pid}")],
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

    # ---------- 🎬 TOOL KA TUTORIAL VIDEO (har tool ka apna video) ----------
    if data.startswith("toolvid:"):
        key = data.split(":", 1)[1]
        if has_video(key):
            await q.answer("🎬 Sending the tutorial video (30 sec)...")
        await send_tool_video(context.bot, q.message.chat.id, key, answer_cb=q.answer)
        return

    # Virtual Numbers Funnel
    if data in ("vnum_open", "vnum_back"):
        await q.message.edit_text(VNUM_INTRO, reply_markup=_vnum_intro_kb(), parse_mode=HTML)
        return

    if data == "vnum_get":
        txt = (
            f"📲 <b>{to_bold('STEP 1: SELECT SERVICE')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "What do you need the number for? Pick a service below 👇"
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
            "Which country number do you need? Select a country 👇"
        )
        await _vnum_say(q, txt, _vnum_ctry_kb())
        return

    if data.startswith("vnum_ctry:"):
        cl = data.split(":")[1]
        ctry_name = dict(VNUM_COUNTRIES).get(cl, cl.upper())
        svc_name = context.user_data.get("vnum_svc", "WhatsApp")
        order_text = f"Hi, I need a Virtual Number:\nService: {svc_name}\nCountry: {ctry_name}"
        contact_url = f"https://t.me/Supermannn_x?text={quote(order_text)}"
        card = (
            f"🎯 <b>{to_bold('STEP 3: GET YOUR NUMBER')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📲 <b>Service:</b> {svc_name}\n"
            f"🌍 <b>Country:</b> {ctry_name}\n"
            "⚡ <b>Delivery:</b> Instant (1-2 min)\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👉 Tap the <b>Contact Admin</b> button below to get the number:"
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

    # VIP Buy Handlers
    if data.startswith("buy_plan_"):
        plan_key = data.replace("buy_", "")
        qr_buf, plan_name, amt = generate_plan_payment_qr(UPI_ID, UPI_NAME, plan_key, uid)
        pending_n = len(pending_payments(20))
        if pending_n >= 3:
            mine = [p for p in pending_payments(20) if p.get("user_id") == uid]
            if len(mine) >= 3:
                await q.answer("You already have 3 payments pending — the admin will verify them.", show_alert=True)
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
            "📲 <b>Step 1:</b> Scan this QR and pay ₹" f"{amt} \n"
            "   (PhonePe / GPay / Paytm / BHIM)\n\n"
            "📝 <b>Step 2:</b> After paying, send the <b>UTR / Transaction ID</b> here\n"
            "📸 <b>Step 3:</b> Send the payment <b>screenshot</b>\n\n"
            "⚠️ <b>Strict check:</b> the UTR must be correct and the screenshot must be of a real payment "
            "(not a photo or meme). Wrong proof = no VIP."
        )
        kb_pay = InlineKeyboardMarkup([
            [InlineKeyboardButton("❓ Where do I find the UTR?", callback_data="pay_utr_help")],
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
            await q.answer("Payment record not found.", show_alert=True)
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
            exp = ("👑 LIFETIME" if days >= 9999
                   else (premium_expiry(user_obj) or "—"))
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
            await q.answer("Record not found.", show_alert=True)
            return
        if pay.get("status") == "approved":
            await q.answer("This payment is approved — it cannot be rejected.", show_alert=True)
            return
        set_payment_status(pid, "rejected", reviewer=uid, note="admin reject")
        await _edit_admin_msg(
            f"❌ <b>REJECTED — Payment #{pid}</b>\n\n"
            f"👤 User: <code>{pay.get('user_id')}</code>\n💰 ₹{pay.get('amount')}\n🧾 UTR: <code>{pay.get('utr_ref')}</code>\n\n"
            "<i>The user got a message with the reason.</i>",
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
            await q.answer("Record not found.", show_alert=True)
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
            f"💳 <b>Pending Payments ({len(pend)})</b>\nTap to see the full proof + approve/reject 👇",
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
            "Current link:</i>",
            parse_mode=HTML, disable_web_page_preview=True)
        return

    if data.startswith("vehagain:"):
        plate = data.split(":", 1)[1]
        _u = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u, uid):
            await q.answer("No credits left — get VIP for unlimited checks.", show_alert=True)
            return
        def _veh_again_text(lv):
            if not lv.get("ok"):
                return ("\u26a0\ufe0f <b>Live RC / challan report nahi mil paaya.</b>\n"
                        + hesc(str(lv.get("error") or "source slow")[:120])
                        + "\n\n\U0001f49a <b>Koi credit nahi kata.</b>")
            if not (lv.get("has_data") or _veh_has_rc_data(lv)):
                return ("\U0001f50e <b>Is number ka koi RC / challan record nahi mila.</b>\n"
                        "\U0001f49a <b>Koi credit nahi kata.</b>")
            note = ("\u267b\ufe0f <b>Cached result</b> \u2014 koi credit nahi kata."
                    if lv.get("cached") else spend_credit_msg(uid, "vehicle"))
            return note + "\n\n" + render_vehicle_report(lv)

        wait_v = await q.message.reply_text(
            "\U0001f50e <b>Checking live RC + challan record again\u2026</b>", parse_mode=HTML)
        live, _task = await hub_with_progress(wait_v, hub_vehicle, plate,
                                              "Live RC + challan check chal raha hai\u2026",
                                              timeout=18)
        if live is None:
            asyncio.create_task(deliver_hub_later(_task, context, wait_v.chat_id, _veh_again_text))
            try:
                await wait_v.edit_text(
                    "\u23f3 <b>Source slow hai…</b>\n"
                    "<i>Result taiyar hote hi yahin bhej denge (30-60 sec).</i>", parse_mode=HTML)
            except Exception:                                    # noqa: BLE001
                pass
            add_use(uid)
            return
        if live.get("ok") and not (live.get("has_data") or _veh_has_rc_data(live)):
            await q.answer("No RC / challan record found for this number — no credit was cut.", show_alert=True)
            add_use(uid)
            return
        if live.get("ok"):
            # cache se aaya → dobara credit NAHI katte (v45 fairness fix)
            if live.get("cached"):
                await q.message.reply_text(
                    "♻️ <b>Ye abhi ka hi result hai</b> (5 minute cache) — "
                    "<b>koi credit nahi kata.</b>", parse_mode=HTML)
            else:
                await q.message.reply_text(spend_credit_msg(uid, "vehicle"), parse_mode=HTML)
            rows_live = [
                [InlineKeyboardButton("🚨 Check / pay on e-Challan (official)",
                                      url="https://echallan.parivahan.gov.in/"),
                 InlineKeyboardButton("📄 VAHAN RC status",
                                      url="https://vahan.parivahan.gov.in/nrservices/faces/user/searchstatus.xhtml")],
                [InlineKeyboardButton("🔄 Check again", callback_data=f"vehagain:{live['plate']}")],
            ]
            await q.message.reply_text(render_vehicle_report(live), reply_markup=InlineKeyboardMarkup(rows_live),
                                       parse_mode=HTML)
        else:
            await q.answer(str(live.get("error"))[:180], show_alert=True)
        add_use(uid)
        return

    if data.startswith("clai:"):
        _cur = context.user_data.get("clip_ai")
        if _cur is None:
            _cur = aib.ai_available()
        context.user_data["clip_ai"] = not bool(_cur)
        if context.user_data["clip_ai"] and not aib.ai_available():
            context.user_data["clip_ai"] = False
            await q.answer("AI key server par set nahi hai — classic mode hi chalega.", show_alert=True)
        try:
            await q.message.edit_text(
                clip_choice_text(context.user_data.get("clip_mode"), context.user_data.get("clip_vert"),
                                 context.user_data.get("clip_ai")),
                reply_markup=clip_choice_kb(context.user_data.get("clip_mode"), context.user_data.get("clip_vert"),
                                            context.user_data.get("clip_ai")), parse_mode=HTML)
        except Exception:
            await q.answer("Setting badal gayi ✅")
        return

    if data.startswith("clmode:") or data.startswith("clorient:") or data == "clipgo":
        _src = context.user_data.get("clip_src") or ""
        if not _src or not os.path.exists(_src):
            await q.answer("Send the video first.", show_alert=True)
            await q.message.reply_text(tool_prompt("clips"), parse_mode=HTML)
            return
        if data.startswith("clmode:"):
            context.user_data["clip_mode"] = "equal" if data.endswith("equal") else "smart"
            await q.answer("Mode set ✅")
            await q.message.edit_text(clip_choice_text(context.user_data.get("clip_mode"),
                                                       context.user_data.get("clip_vert")),
                                      reply_markup=clip_choice_kb(context.user_data.get("clip_mode"),
                                                                  context.user_data.get("clip_vert")),
                                      parse_mode=HTML)
            return
        if data.startswith("clorient:"):
            context.user_data["clip_vert"] = data.endswith("916")
            await q.answer("Format set ✅")
            await q.message.edit_text(clip_choice_text(context.user_data.get("clip_mode"),
                                                       context.user_data.get("clip_vert")),
                                      reply_markup=clip_choice_kb(context.user_data.get("clip_mode"),
                                                                  context.user_data.get("clip_vert")),
                                      parse_mode=HTML)
            return
        # 🚀 clipgo
        _u_cg = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u_cg, uid):
            await q.answer("No credits left — get VIP for unlimited clips.", show_alert=True)
            await q.message.reply_text(get_credits_over_text("clips"),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        mode_c = context.user_data.get("clip_mode") or "smart"
        vert_c = bool(context.user_data.get("clip_vert"))
        ai_c = context.user_data.get("clip_ai")
        if ai_c is None:
            ai_c = aib.ai_available()
        ai_c = bool(ai_c) and aib.ai_available()
        context.user_data["mode"] = None
        context.user_data["clip_src"] = None
        await q.answer("Making clips… 🎬")
        await q.message.edit_text(
            "🎬 <b>Clips ban rahe hain…</b>\n"
            f"Mode: <b>{'🎯 Best Moments' if mode_c == 'smart' else '⏱️ Equal Parts'}</b> · "
            f"<b>{'9:16' if vert_c else '16:9'}</b> · "
            f"AI <b>{'ON 🧠' if ai_c else 'OFF'}</b>\n"
            "<i>Analysing phir cutting. Please wait.</i>", parse_mode=HTML)
        asyncio.create_task(start_clip_job(context, q.message.chat.id, uid, _src, mode_c, vert_c, ai_c))
        return

    if data.startswith("imeiagain:"):
        imei = re.sub(r"\D", "", data.split(":", 1)[1])[:15]
        _u_ii = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u_ii, uid):
            await q.answer("No credits left — get VIP for unlimited checks.", show_alert=True)
            return
        await q.message.reply_text("🔎 <b>Checking this IMEI again…</b>", parse_mode=HTML)
        res_ii = fetch_imei_details(imei, use_cache=False)
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
            await q.answer("Record not found.", show_alert=True)
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

            "🔄 <b>AUTO FORWARD (CLONER) — 3 STEPS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ Set <b>SOURCE</b> (channel to copy posts from)\n"
            "2️⃣ Set <b>TARGET</b> (channel to send posts to — bot must be admin there)\n"
            "3️⃣ Turn <b>FULL AUTO ON</b> — done, posts copy by themselves\n"
            "\n"
            "🎬 Watch the video below — full steps in 30 seconds:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Tutorial Video (30 sec) — HIMANSHU", callback_data="toolvid:cloner")],
                [InlineKeyboardButton("🚀 Start Setup (3 Steps)", callback_data="cloner_setup")],
                [InlineKeyboardButton("📊 My Settings", callback_data="cloner_status")],
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
            "<b>Step 1:</b> Set SOURCE channel (posts come from here)\n"
            "<b>Step 2:</b> Set TARGET channel (posts go here)\n"
            "<b>Step 3:</b> Turn FULL AUTO ON\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 Source: <code>{cfg.get('source_chat_id') or '— not set'}</code>\n"
            f"📑 Target: <code>{cfg.get('target_chat_id') or '— not set'}</code>\n\n"
            "⚠️ <b>Remember:</b> Make the bot <b>Admin</b> in both channels.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{src_ok} Set Source", callback_data="cloner_set_source")],
                [InlineKeyboardButton(f"{tgt_ok} Set Target", callback_data="cloner_set_target")],
                [InlineKeyboardButton("🤖 FULL AUTO ON/OFF", callback_data="cloner_toggle_auto")],
                [InlineKeyboardButton("🧪 Send Test Post", callback_data="cloner_test")],
                [InlineKeyboardButton("📘 Read Guide", callback_data="cloner_guide")],
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
            await q.answer("Set the Target channel first!", show_alert=True)
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
                test_msg = await context.bot.send_message(tgt, "🧪 <b>TEST POST</b>\n\nThis message was sent by the ToolVault bot.\nIf you can see it → your <b>target channel works fine ✅</b>\n\n<i>This test message is deleted in 5 seconds.</i>", parse_mode=HTML)
                lines.append("\n✅ <b>Test post sent to target</b> — check your channel!")
                import asyncio as _aio
                async def _del_later():
                    await _aio.sleep(5)
                    try:
                        await context.bot.delete_message(tgt, test_msg.message_id)
                    except Exception:
                        pass
                _aio.create_task(_del_later())
            else:
                lines.append("\n⚠️ Make the bot <b>Admin</b> in the target channel (Post Messages permission) — then test again.")
        except Exception as e:
            lines.append(f"\n❌ Problem: <code>{hesc(str(e))}</code>\n💡 Check: are the source/target usernames correct? Is the bot admin in both?")
        await q.message.reply_text("🧪 <b>TEST RESULT</b>\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines), parse_mode=HTML)
        return

    # ============ PRIVATE CHANNEL SETUP (aasan tareeka) ============
    if data == "cloner_private":
        await q.message.reply_text(

            "🔒 <b>COPY POSTS FROM A PRIVATE CHANNEL?</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Very easy — <b>no login, no password</b>. Just 3 things:\n"
            "1️⃣ In your <b>private channel</b> go to <b>Administrators</b> → <b>Add Admin</b> → add this bot (<code>@utility_duniya_bot</code>) ✅\n"
            "   <i>(This is the only 'login' — bot only needs to be inside. Do it once.)</i>\n"
            "2️⃣ <b>FORWARD any one post</b> (video/PDF/photo) from that channel to this bot\n"
            "   → the bot picks up the channel ID by itself\n"
            "3️⃣ The bot gives you a button: <b>📡 Make this SOURCE</b> — tap it, source is set\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "After that set <b>Target</b> and turn <b>FULL AUTO</b> ON. Done! 🎉\n"
            "⚠️ Telegram does not allow forwarding from channels with copy protection — in that case the bot grabs the post directly (auto mode) because it is <b>admin</b> there."
            "",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to setup", callback_data="cloner_setup")],
            ]),
            parse_mode=HTML,
        )
        return

    if data.startswith("fc_src:"):
        cid = data.split(":", 1)[1]
        try:
            chat = await context.bot.get_chat(int(cid))
            title = chat.title or str(cid)
        except Exception:
            await q.answer("Add the bot to that channel as admin, then try again", show_alert=True)
            return
        save_cloner_config(uid, source_chat_id=cid)
        context.user_data["mode"] = "cloner_target"
        await q.message.reply_text(
            f"✅ <b>Source set:</b> {hesc(str(title))}\n🆔 <code>{cid}</code>\n\n"
            "👉 Now send the <b>TARGET channel</b> (where posts go):\n"
            "(example <code>@MyChannel</code> or <code>-1001234567890</code>)",
            parse_mode=HTML)
        return

    if data.startswith("fc_tgt:"):
        cid = data.split(":", 1)[1]
        save_cloner_config(uid, target=cid)
        cfg_now = get_cloner_config(uid)
        ready = bool(cfg_now.get("source_chat_id"))
        await q.message.reply_text(
            f"✅ <b>Target set:</b> <code>{cid}</code>\n\n"
            + ("🎉 Both are set — now tap <b>FULL AUTO ON</b>!" if ready else "👉 Now set the <b>SOURCE</b> channel.")
            ,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🤖 Turn FULL AUTO ON", callback_data="cloner_toggle_auto")],
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
        if kind not in KAGAZ_FIELDS:
            await q.message.reply_text("❌ This document was not found.", parse_mode=HTML)
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
            "ytmp3": ("🎵 <b>YOUTUBE → MP3</b>\n\nNow send the <b>YouTube link of the song</b>:\n<i>(example https://youtu.be/xxxx)</i>", "media_ytmp3"),
            "status": ("🎬 <b>STATUS VIDEO MAKER</b>\n\n1️⃣ First <b>send a photo</b> (the status is made on it)", "media_status_photo"),
            "ringtone": ("🎧 <b>RINGTONE CUTTER</b>\n\nSend a song (MP3) or video — I make a 30 second ringtone from it.", "media_ringtone"),
            "karaoke": ("🎤 <b>KARAOKE MAKER</b>\n\nSend a song (MP3) or video — I remove the vocals and keep the music.", "media_karaoke"),
            "8d": ("🔊 <b>8D SOUND</b>\n\nSend a song — I add the 8D effect.", "media_8d"),
            "bass": ("💥 <b>BASS BOOST</b>\n\nSend a song — full bass, loud sound.", "media_bass"),
            "voice": ("🗣️ <b>VOICE CHANGE</b>\n\nSend a voice note / audio / video — then pick a voice.", "media_voice_wait"),
            "v2mp3": ("🎼 <b>VIDEO → MP3</b>\n\nSend a video — I make its MP3.", "media_v2mp3"),
            "trim": ("✂️ <b>VIDEO TRIM</b>\n\nSend a video (max 2 minutes) — then give the time (example <code>0:10 to 0:45</code>).", "media_trim_wait"),
            "compress": ("🗜️ <b>VIDEO COMPRESS</b>\n\nSend a video (max 2 minutes) — I make the size small (easy to send on WhatsApp).", "media_compress_wait"),
        }.get(kind)
        if not ask:
            await q.message.reply_text("❌ Option not found.", parse_mode=HTML)
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
    if data == "shot_hd":
        context.user_data["mode"] = "shot"
        await q.message.reply_text(tool_prompt("shot"), reply_markup=tool_tutorial_kb("shot"), parse_mode=HTML)
        return
    if data == "shot_full":
        context.user_data["mode"] = "shot_full"
        await q.message.reply_text(tool_prompt("shot_full"), reply_markup=tool_tutorial_kb("shot_full"), parse_mode=HTML)
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
            await q.answer("Send the photo first!", show_alert=True)
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
                caption=(f"📄 <b>{to_bold('COMPRESSED PDF READY')}</b>\n"
                         f"• {len(pages)} page • {size_kb:.0f} KB • {kb_target} KB limit me ✅\n"
                         f"• Mode: {'⚫ Black & White' if gray else '🌈 Colour'}\n\n"
                         "You can upload it on the government portal."),
                parse_mode=HTML)
        except Exception as e:
            await q.message.reply_text(f"❌ Could not make the PDF: <code>{hesc(str(e))}</code>", parse_mode=HTML)
        context.user_data.pop("doc_pages", None)
        context.user_data.pop("doc_kb", None)
        context.user_data.pop("doc_gray", None)
        context.user_data.pop("mode", None)
        add_use(uid)
        return

    # ============ PERSONAL RECORDS (retired for privacy) ============
    if data.startswith("numrec:"):
        await q.answer("Leaked personal-record search privacy ke liye available nahi hai.", show_alert=True)
        return

    # Copy buttons (pincode / area results)
    if data.startswith("copy_"):
        await q.answer(f"📋 {data[5:]} — tap to copy", show_alert=True)
        return

    # Advanced Channel Cloner Settings Handlers
    if data == "cloner_set_target":
        context.user_data["mode"] = "cloner_target"
        await q.message.reply_text("📑 <b>Set Channel ID:</b>\nSend the TARGET channel username or ID:\n(example: <code>@MyChannel</code> ya <code>-100123456789</code>)\n\n<i>Note: Make the bot Admin in the target channel (with Post permission).</i>", parse_mode=HTML)
        return

    if data == "cloner_set_source":
        context.user_data["mode"] = "cloner_source"
        await q.message.reply_text(
            "📡 <b>Set SOURCE Channel:</b>\nSend the username or ID of the channel to copy posts FROM:\n"
            "(example <code>@MySourceChannel</code> or <code>-1001234567890</code>)\n\n"
            "<i>Important: the bot must be ADMIN in that source channel too — only then new posts reach the bot.</i>",
            parse_mode=HTML,
        )
        return

    if data == "cloner_toggle_auto":
        cfg = get_cloner_config(uid)
        if cfg.get("auto_status") == "on":
            save_cloner_config(uid, auto_status="off")
            await q.message.reply_text(
                "🛑 <b>FULL AUTO CLONE OFF!</b>\n\nNew posts will not be copied automatically now. (Manual forwarding still works.)",
                reply_markup=get_cloner_settings_kb(uid),
                parse_mode=HTML,
            )
            return

        if not cfg.get("target_chat_id"):
            await q.message.reply_text("⚠️ First set the <b>📑 Target</b> channel (where the post should go).", parse_mode=HTML)
            return
        if not cfg.get("source_chat_id"):
            await q.message.reply_text("⚠️ First set the <b>📡 Source</b> channel (where the post comes from).", parse_mode=HTML)
            return
        if str(cfg.get("target_chat_id")).strip() == str(cfg.get("source_chat_id")).strip():
            await q.message.reply_text("❌ Source and Target cannot be the same (the post would loop forever).", parse_mode=HTML)
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

            "Now every <b>new post</b> in the source channel is copied to your target channel in 2-5 seconds — with caption, tag, watermark, replace/remove words and thumbnail settings.\n"
            "<i>Note: only NEW posts are copied (not old ones). Tap the same button again to stop.</i>",
            reply_markup=get_cloner_settings_kb(uid),
            parse_mode=HTML,
        )
        return

    if data == "cloner_set_tag":
        context.user_data["mode"] = "cloner_tag"
        await q.message.reply_text("🏷️ <b>Set Rename Tag:</b>\nWhich tag should be added in front of every video/post title?\n(example <code>[🔥 4K HD]</code> or <code>@MyChannel</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_caption":
        context.user_data["mode"] = "cloner_caption"
        await q.message.reply_text("📝 <b>Set Custom Caption:</b>\nWhich custom caption should be added to posts?\n(example <code>Join @MyChannel for daily free updates!</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_replace":
        context.user_data["mode"] = "cloner_replace"
        await q.message.reply_text("🔄 <b>Replace Words / Links:</b>\nReplace old words with your words (format: <code>OldWord=>NewWord</code>):\n\n(example:\n<code>@old_channel=>@MyChannel\nOldSite.com=>MySite.com</code>)", parse_mode=HTML)
        return

    if data == "cloner_set_remove":
        context.user_data["mode"] = "cloner_remove"
        await q.message.reply_text("🗑️ <b>Remove Words / Promo Links:</b>\nSend the words/links to delete from posts (comma or new line):\n(example: <code>@spam_bot, join now, https://t.me/fake</code>)", parse_mode=HTML)
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
        await q.message.reply_text("💧 <b>Watermark Setup:</b>\nSend the watermark text/link to show at the bottom of posts:\n(example: <code>⚡ Forwarded by @MyChannel</code>)", parse_mode=HTML)
        return

    if data == "cloner_reset":
        save_cloner_config(uid, target="", caption="", watermark="", rename_tag="", replace_words="", remove_words="", thumbnail_file_id="", source_chat_id="", auto_status="off")
        context.user_data.pop("mode", None)
        await q.message.reply_text("🔄 <b>Settings Reset!</b> All cloner settings are back to default.", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
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
        await q.message.reply_text("🚀 <b>Fast Auto-Forward Active!</b>\n\nNow forward 10-15 posts/videos from any channel, or send media directly — the bot posts everything to your target channel in 1-2 seconds!\n\nStop it any time with /cancel.", parse_mode=HTML)
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

            "❌ <b>This does not look like a payment screenshot!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📸 <b>Send the screenshot like this:</b>\n"
            "1️⃣ Open PhonePe / GPay / Paytm on your phone\n"
            "2️⃣ Go to <b>History / Passbook</b>\n"
            "3️⃣ Tap that payment\n"
            "4️⃣ Take a <b>screenshot</b> → send it here (amount, success and UTR must be clear)\n"
            "⚠️ Selfies, photos or memes are rejected as proof.\n"
            "<i>Your UTR is saved — just send the correct screenshot.</i>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❓ Where do I find the UTR?", callback_data="pay_utr_help")]]),
            parse_mode=HTML,
        )
        return

    # --- duplicate checks (ek UTR / ek image sirf ek baar) ---
    utr_dup = utr_exists(utr)
    shot_dup = shot_exists(photo_obj.file_unique_id)
    if shot_dup:
        await st.edit_text(

            "🚫 <b>This screenshot was already used!</b>\n"
            "One screenshot can get VIP only once.\n"
            "📸 Make a new payment and send the <b>screenshot</b> of that new payment.\n"
            "💬 Any problem? Support: @Supermannn_x",
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
        await st.edit_text("❌ Could not save the record. Try again in a bit or contact Support.")
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
        await st.edit_text(f"⚠️ Proof saved (ID #{pid}) but could not send it to the admin. Tell Support: @Supermannn_x")
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

        # 3. Channel Cloner Dashboard (premium — 1 credit per FULL AUTO / Fast-Forward)
        if action == "cloner":
            _cfg = get_cloner_config(uid)
            _u_cl = get_user(uid, user.first_name)
            _auto = "🟢 ON" if _cfg.get("auto_status") == "on" else "🔴 OFF"
            _cl_note = ""
            if not can_use_premium_tool(_u_cl, uid):
                _cl_note = ("\n⚠️ <b>All credits used</b> — FULL AUTO ON and Fast-Forward are locked.\n"
                            "👑 With VIP both work unlimited (/premium).\n")
            await update.message.reply_text(
                f"🔄 <b>{to_bold('CHANNEL CLONER & AUTO-FORWARDER')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📡 Source: <code>{_cfg.get('source_chat_id') or 'Not Set'}</code>\n"
                f"📑 Target: <code>{_cfg.get('target_chat_id') or 'Not Set'}</code>\n"
                f"🤖 FULL AUTO: <b>{_auto}</b>\n"
                f"{credits_line(_u_cl, uid)}\n"
                "<i>(FULL AUTO ON and Fast-Forward ON use 1 credit each)</i>\n"
                f"{_cl_note}\n"
                "Customize settings for your files 👇",
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

        # 4. Sarkari Portals
        if action == "sarkari":
            await update.message.reply_text(SARKARI_CITIZEN_TEXT, reply_markup=get_sarkari_citizen_kb(), parse_mode=HTML)
            return

        # 6b. QR Code (4 types)
        if action == "qr":
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

        # 6c. Site Screenshot (2 types)
        if action == "shot":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🖼️ HD Screenshot (top part)", callback_data="shot_hd")],
                [InlineKeyboardButton("📜 Full Page Screenshot (whole page)", callback_data="shot_full")],
                [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
            ])
            await update.message.reply_text(
                f"🖼️ <b>{to_bold('SITE SCREENSHOT')}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
                "🖼️ <b>HD</b> — top part of the website, fast\n"
                "📜 <b>Full Page</b> — the whole long page, a bit slow\n\n"
                "Send the URL first, the screenshot is made for you.",
                reply_markup=kb, parse_mode=HTML)
            return

        # 7. Interest Calculator — sirf CHAKRAVRIDDHI (compound), gaon/kasbe wala byaaj system
        if action == "interest":
            context.user_data["mode"] = "int_p"
            await update.message.reply_text(
                f"📈 <b>{to_bold('VYAAJ (CHAKRAVRIDDHI) CALCULATOR')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"

                "This is the <b>compound interest</b> calculation — the same way village interest works at ₹x per ₹100 per month.\n"
                "<i>(The simple interest option has been removed — compound is the real calculation.)</i>\n"
                "Just 3 steps:\n"
                "1️⃣ How much money you took (principal)\n"
                "2️⃣ Interest per ₹100 per month\n"
                "3️⃣ How many months\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Step 1/3 — how much money did you take?</b>\n"
                "Send: <code>50000</code> or <code>1.5 lakh</code> or <code>50k</code>",
                parse_mode=HTML,
            )
            return

        # 8. Image to PDF
        if action == "pdf":
            context.user_data["mode"] = "pdf"
            context.user_data["pdf_pages"] = []
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Make Normal PDF", callback_data="make_pdf_now"),
                 InlineKeyboardButton("📄 A4 Print PDF", callback_data="make_pdf_a4")],
            ])
            await update.message.reply_text(tool_prompt("pdf"), reply_markup=kb, parse_mode=HTML)
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
        if action == "cloner_private_help":
            _u = get_user(uid, update.effective_user.first_name)
            if not can_use_premium_tool(_u, uid):
                await update.message.reply_text(get_credits_over_text("cloner_private_help"),
                                                reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                return
            await update.message.reply_text(

                "🔒 <b>COPY POSTS FROM A PRIVATE CHANNEL?</b>\n"
                "No login, no password — just 3 things:\n"
                "1️⃣ Make this bot <b>@utility_duniya_bot</b> an <b>Admin</b> in your private channel\n"
                "2️⃣ <b>Forward any one post</b> (video/PDF) from that channel here\n"
                "3️⃣ The bot gives a button — tap <b>📡 Make this SOURCE</b> ✅\n"
                "Then set the Target and turn FULL AUTO ON. Done!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📘 Full Guide", callback_data="cloner_private")],
                    [InlineKeyboardButton("🚀 Open Setup", callback_data="cloner_setup")],
                ]),
                parse_mode=HTML)
            return
        if action in ("tutorial", "help"):
            await update.message.reply_text(TUTORIAL_NOTICE, reply_markup=tutorial_kb(), parse_mode=HTML)
            return
        if action == "aadhaar":
            await q.message.reply_text(
                "🔒 <b>Aadhaar/family lookup yahan supported nahi hai.</b>\n"
                "Aadhaar number bot ko mat bhejein. Apne record ke liye UIDAI MyAadhaar ya NFSA ke official portal ka use karein; OTP/consent wahan required ho sakta hai.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("UIDAI MyAadhaar", url="https://myaadhaar.uidai.gov.in/")],
                    [InlineKeyboardButton("NFSA official portal", url="https://nfsa.gov.in/")],
                ]), parse_mode=HTML)
            context.user_data.pop("mode", None)
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
                    warn = "\n\n⚠️ <b>The bot is not ADMIN there!</b> Open that channel and make the bot Admin (with Post Messages permission), otherwise posting will fail."
            except Exception:
                warn = "\n\n⚠️ <i>Admin check failed. Please confirm the bot is admin there.</i>"
        except Exception:
            warn = "\n\n<i>(Username could not be resolved — the value is saved as it is. A numeric ID (-100...) is safer.)</i>"

        save_cloner_config(uid, target=resolved)
        context.user_data.pop("mode", None)
        cfg_now = get_cloner_config(uid)
        ready = bool(cfg_now.get("source_chat_id")) and bool(cfg_now.get("target_chat_id"))
        kb_done = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 Turn FULL AUTO ON (Step 3)", callback_data="cloner_toggle_auto")],
            [InlineKeyboardButton("🧪 Send Test Post", callback_data="cloner_test")],
            [InlineKeyboardButton("📘 Read Guide", callback_data="cloner_guide")],
            [InlineKeyboardButton("⚙️ Saari Settings", callback_data="cloner_status")],
        ])
        await update.message.reply_text(
            f"✅ <b>Step 2 done! Target set:</b> <code>{resolved}</code>{warn}\n\n"
            + ("🎉 <b>Both channels are set!</b>\n\n"
               "👉 <b>Step 3:</b> tap <b>FULL AUTO ON</b> below — after that every new post (video, PDF, photo, album) goes to the target automatically."
               if ready else
               "👉 Also do <b>Step 1</b>: send the <b>📡 SOURCE</b> channel (posts come from there).")
            + "\n\n<i>The bot must be Admin in both channels.</i>",
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
                f"❌ Channel not found: <code>{hesc(raw_val)}</code>\n<i>{hesc(str(e))[:120]}</i>\n\n"
                "For a private channel send the numeric ID (example <code>-1001234567890</code>).\n"
                "💡 Easy way to get the ID: forward any <b>TEXT post</b> from that channel to this bot — the bot will tell you the ID.",
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
                "❌ User not found. Send the numeric ID (example <code>8607774564</code>) "
                "or the same @username the user set in the bot.", parse_mode=HTML)
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
                "❌ User not found. Send the numeric ID (example <code>8607774564</code>) "
                "or the same @username the user set in the bot.", parse_mode=HTML)
            return
        u = get_user(target)
        row = get_user_row(target)
        prem = u.get("premium_until") or ""
        hist = user_payment_history(target)
        await update.message.reply_text(
            f"👤 <b>USER DETAIL</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>ID:</b> <code>{target}</code>\n"
            f"👋 <b>Name:</b> {hesc(str((row[1] if row else '') or u.get('name') or '-'))}\n"
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
                failed += 1
            if (sent + failed) % 25 == 0:
                await asyncio.sleep(1)
        await st.edit_text(f"✅ <b>Broadcast done!</b>\n• Sent: {sent}\n• Failed (may have blocked the bot): {failed}", parse_mode=HTML)
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
            await update.message.reply_text(f"🟢 Ban removed: <code>{target}</code>.", parse_mode=HTML)
        else:
            set_ban(target, 1)
            await update.message.reply_text(f"🚫 User banned: <code>{target}</code>.", parse_mode=HTML)
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
                f"❌ <b>This UTR is not valid!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 <b>You sent:</b> <code>{hesc(raw_text[:40])}</code>\n"
                f"⚠️ <b>Reason:</b> {res.get('reason')}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                + utr_help_text() +
                f"\n\n🔁 <b>Now send the correct UTR</b> ({tries}/5 try)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Open the plan again", callback_data=f"buy_plan_{plan_key}")]]),
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
            "✅ <b>UTR is correct!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧾 <b>UTR:</b> <code>{hesc(utr)}</code>\n"
            f"📋 <b>Type:</b> {res.get('kind')}\n"
            f"💎 <b>Plan:</b> {plan['name']} (₹{plan['price']})\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"

            "📸 <b>Step 3:</b> Now send the payment <b>screenshot</b>\n"
            "⚠️ <b>Please note:</b>\n"
            "• The screenshot must show payment <b>success</b> (amount + UTR)\n"
            "• Selfies, photos or random images are <b>rejected</b>\n"
            "• Send the screenshot <b>soon</b>, otherwise the flow resets",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Plan badlo", callback_data="open_vip_menu")]]),
            parse_mode=HTML,
        )
        return

    # ---------- PAYMENT STEP 3: text bhej diya screenshot ki jagah ----------
    if mode and mode.startswith("pay_shot_"):
        plan_key = mode.replace("pay_shot_", "")
        await update.message.reply_text(

            "📸 <b>Now I need a screenshot (not text)!</b>\n"
            "Open the payment app on your phone → take a <b>screenshot</b> of that payment → send it here.\n"
            "⚠️ The screenshot must show: <b>amount, success/paid, and UTR</b>.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎫 Open the plan again", callback_data=f"buy_plan_{plan_key}")]]),
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
                    "\n\n👇 Download any file with the buttons below:"
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
                        f"• 🔊 <b>Audio:</b> Original ✅\n"
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
                    [InlineKeyboardButton("🌐 Open Original Page", url=raw_text)],
                ]
                await st.edit_text(
                    f"📥 <b>{to_bold('DOWNLOAD LINK READY')}</b>\n\n"
                    f"🎬 <b>Platform:</b> {plat}\n"
                    + (f"📝 <b>Title:</b> {title}\n" if title else "")
                    + (f"📊 <b>Size:</b> {mb} MB\n" if mb else "")
                    + f"⚙️ Engine: {engine}\n\n"
                    + hesc(str(res.get("note") or ""))
                    + "\n\n👇 Tap the button below to download:",
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
        res = lookup_ip_domain(raw_text)
        if res.get("ok"):
            flags = []
            flags.append("🛡️ Proxy/VPN: " + ("⚠️ Yes (hidden connection)" if res.get("is_proxy") else "✅ No"))
            flags.append("🏢 Datacenter/Hosting: " + ("✅ Yes (server/VPN line)" if res.get("is_hosting") else "❌ No (normal internet line)"))
            flags.append("📱 Mobile network: " + ("✅ Yes" if res.get("is_mobile") else "❌ No"))
            rows = [[InlineKeyboardButton("🗺️ See on Map", url=res["maps_link"])]]
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
                "\n\n<i>This is public IP information (for websites/servers). It does not show anyone's home address.</i>",
                reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
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
            rows_ = [[InlineKeyboardButton(txt, url=url)] for txt, url in base["links"]]
            return (
                f"🚗 <b>{to_bold('VEHICLE / RTO INFO')}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔖 <b>Number Plate:</b> <code>{base['pretty']}</code>\n"
                f"🗺️ <b>State:</b> {base['state_name']} ({base['state_code']})\n"
                f"🏢 <b>RTO Office:</b> {base['rto_code']} — {base['district']}\n"
                + (f"🚙 <b>Vehicle Class (from series):</b> {base['vehicle_class']}\n" if base.get("vehicle_class") else "")
                + "━━━━━━━━━━━━━━━━━━━━━━\n"
                + (extra + "\n" if extra else "")
                + f"ℹ️ <i>{base['note']}</i>\n\n"
                "👇 Check officially here:"
            ), InlineKeyboardMarkup(rows_)

        # ---- live RC + challan report (agar API set hai) ----
        if vehicle_api_ready() and vehicle_plate_ok(raw_text):
            # v45: seedha aapka naya /api/vehicle-report (RC + challan ek hi call me)
            _u = get_user(uid, update.effective_user.first_name)
            if not can_use_premium_tool(_u, uid):
                await update.message.reply_text(get_credits_over_text("vehicle"),
                                                reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                card_txt, kb_free = _free_card("✅ <b>Free part:</b> RTO office + official check links are open below.")
                await update.message.reply_text(card_txt, reply_markup=kb_free, parse_mode=HTML)
                context.user_data.pop("mode", None)
                add_use(uid)
                return
            wait = await update.message.reply_text("🔎 <b>Checking live RC + challan record…</b>\n<i>Please wait 5-20 seconds.</i>",
                                                   parse_mode=HTML)
            def _veh_late_text(lv):
                """Live report der se aaye to ye text bhejenge."""
                if not lv.get("ok"):
                    return ("\u26a0\ufe0f <b>Live RC / challan report nahi mil paaya.</b>\n"
                            + hesc(str(lv.get("error") or "source slow")[:120])
                            + "\n\n\U0001f49a <b>Koi credit nahi kata.</b>")
                if not (lv.get("has_data") or _veh_has_rc_data(lv)):
                    return ("\U0001f50e <b>Is number ka koi RC / challan record nahi mila.</b>\n"
                            "\U0001f49a <b>Koi credit nahi kata.</b>")
                note = ("\u267b\ufe0f <b>Cached result</b> \u2014 koi credit nahi kata."
                        if lv.get("cached") else spend_credit_msg(uid, "vehicle"))
                return note + "\n\n" + render_vehicle_report(lv)

            live, _task = await hub_with_progress(wait, hub_vehicle, raw_text,
                                                  "Live RC + challan check chal raha hai\u2026",
                                                  timeout=18)
            if live is None:
                # free card TURANT, live report baad me
                card_txt, kb_free = _free_card(
                    "\u23f3 <b>Live RC + challan report aa raha hai\u2026</b>\n"
                    "<i>Milte hi yahin bhej denge (30-60 sec). Abhi tak koi credit nahi kata.</i>")
                await update.message.reply_text(card_txt, reply_markup=kb_free, parse_mode=HTML)
                asyncio.create_task(deliver_hub_later(_task, context, chat_id, _veh_late_text))
                try:
                    await wait.delete()
                except Exception:                                # noqa: BLE001
                    pass
                add_use(uid)
                return
            try:
                await wait.delete()
            except Exception:                                    # noqa: BLE001
                pass
            if live.get("ok") and not (live.get("has_data") or _veh_has_rc_data(live)):
                card_txt, kb_free = _free_card(
                    "🔎 <b>No RC / challan record found for this number.</b>\n"
                    "✅ <b>No credit was cut</b> — check the number plate once and send again.")
                await update.message.reply_text(card_txt, reply_markup=kb_free, parse_mode=HTML)
                add_use(uid)
                return
            if live.get("ok"):
                if live.get("cached"):
                    await update.message.reply_text(
                        "♻️ <b>Ye abhi ka hi result hai</b> (5 minute cache) — "
                        "<b>koi credit nahi kata.</b>", parse_mode=HTML)
                else:
                    await update.message.reply_text(spend_credit_msg(uid, "vehicle"), parse_mode=HTML)
                rows_live = [
                    [InlineKeyboardButton("🚨 Check / pay on e-Challan (official)",
                                          url="https://echallan.parivahan.gov.in/"),
                     InlineKeyboardButton("📄 VAHAN RC status",
                                          url="https://vahan.parivahan.gov.in/nrservices/faces/user/searchstatus.xhtml")],
                    [InlineKeyboardButton("🔄 Check this number again", callback_data=f"vehagain:{live['plate']}")],
                ]
                await update.message.reply_text(render_vehicle_report(live),
                                                reply_markup=InlineKeyboardMarkup(rows_live), parse_mode=HTML)
                add_use(uid)
                return
            # API fail → free card + reason
            card_txt, kb_free = _free_card(f"⚠️ <b>Live report not available:</b> {hesc(str(live.get('error'))[:120])}")
            await update.message.reply_text(card_txt, reply_markup=kb_free, parse_mode=HTML)
            add_use(uid)
            return

        card_txt, kb_free = _free_card(
            "🔒 <b>Live RC/challan data abhi available nahi hai.</b>\n"
            "Authorized provider configure hone tak sirf RTO/state parsing aur official VAHAN/e-Challan links dikhte hain.\n"
            "Apni RC/challan status official portal par check karein.")
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
                imei_help_card("Live IMEI details are not available right now. Please try later."),
                parse_mode=HTML)
            add_use(uid)
            return
        wait = await update.message.reply_text(
            "🔎 <b>Fetching the device details…</b>\n<i>Please wait 5-15 seconds.</i>", parse_mode=HTML)
        res_i = fetch_imei_details(imei_clean)
        try:
            await wait.delete()
        except Exception:
            pass
        if not res_i.get("ok"):
            rows_fb = [[InlineKeyboardButton(t, url=u)] for t, u in imei_fallback_links(imei_clean)]
            await update.message.reply_text(
                "❌ <b>DEVICE DETAILS NOT FOUND</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔎 TAC (first 8 digits): <code>{hesc(imei_clean[:8])}</code>\n"
                f"⚠️ {hesc(str(res_i.get('error'))[:160])}\n"
                "✅ <b>No credit was cut</b> — check the number and send again.\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👇 You can also check on the official site:",
                reply_markup=InlineKeyboardMarkup(rows_fb), parse_mode=HTML)
            add_use(uid)
            return
        await update.message.reply_text(spend_credit_msg(uid, "imei"), parse_mode=HTML)
        if res_i.get("photo") and not str(res_i["photo"]).lower().endswith(".gif"):
            try:
                await update.message.reply_photo(photo=res_i["photo"],
                                                 caption=render_imei_caption(res_i), parse_mode=HTML)
            except Exception:
                pass
        body = render_imei_text(res_i)
        await update.message.reply_text(body, parse_mode=HTML, disable_web_page_preview=True)
        try:
            buf_spec = io.BytesIO(imei_specs_json(res_i))
            buf_spec.name = imei_specs_filename(res_i)
            await update.message.reply_document(
                document=buf_spec,
                caption=("📄 <b>" + hesc(imei_title(res_i)) + "</b> — catalog me available device details\n"
                         "<i>JSON copy file; har model ke liye full specifications guaranteed nahi.</i>"),
                parse_mode=HTML)
        except Exception as e:
            log.warning("imei json file send fail: %s", e)
        rows_i = [[InlineKeyboardButton(t, url=u)] for t, u in (res_i.get("links") or [])[:3]]
        rows_i.append([InlineKeyboardButton("🔄 Check another IMEI", callback_data="imei_new")])
        await update.message.reply_text("👇 More:", reply_markup=InlineKeyboardMarkup(rows_i), parse_mode=HTML)
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
            caption=(f"📸 <b>{to_bold('OFFICIAL GOVT EXAM PHOTO READY')}</b>\n"
                     f"• <b>Name:</b> {hesc(name.upper())}\n• <b>DOP:</b> {hesc(dop)}\n"
                     f"• <b>Size:</b> {sz} KB (20-50KB ✅)"),
            parse_mode=HTML)
        context.user_data.pop("mode", None)
        context.user_data.pop("raw_photo", None)
        add_use(uid)
        return

    if mode in ("clips", "clips_wait", "clips_mode"):
        url = (raw_text or "").strip()
        _u_cl = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u_cl, uid):
            await update.message.reply_text(get_credits_over_text("clips"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            add_use(uid)
            return
        if url.lower().startswith("http") and (clips_is_direct_url(url) or clips_is_yt_url(url)):
            st = await update.message.reply_text("⬇️ <b>Downloading the video…</b>\n<i>Please wait.</i>",
                                                 parse_mode=HTML)
            d = tempfile.mkdtemp(prefix="clipin_")
            if clips_is_yt_url(url):
                if not clips_ytdlp_available():
                    clips_cleanup(d)
                    await st.edit_text(
                        "⚠️ <b>YouTube download is not available right now.</b>\n\n"
                        "👉 Send the <b>video file</b> itself, or a <b>direct .mp4 link</b>.",
                        parse_mode=HTML)
                    add_use(uid)
                    return
                r = await asyncio.to_thread(clips_youtube_download, url, d,
                                            CLIP_MAKER_MAX_MIN, 400.0)
            else:
                r = await asyncio.to_thread(clips_download_direct, url, os.path.join(d, "src.mp4"))
            if not r.get("ok"):
                clips_cleanup(d)
                await st.edit_text(
                    "❌ <b>DOWNLOAD FAILED</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ {hesc(str(r.get('error'))[:200])}\n"
                    "✅ No credit was cut. 👉 Send the video <b>file</b> instead — that always works.",
                    parse_mode=HTML)
                add_use(uid)
                return
            info = await asyncio.to_thread(clips_probe, r["path"])
            dur = float(info.get("duration") or 0)
            if dur and dur > CLIP_MAKER_MAX_MIN * 60:
                clips_cleanup(d)
                await st.edit_text("⚠️ Video is <b>%d min</b> long — limit is <b>%d min</b>."
                                   % (int(dur // 60), int(CLIP_MAKER_MAX_MIN)), parse_mode=HTML)
                add_use(uid)
                return
            context.user_data["clip_src"] = r["path"]
            context.user_data["clip_mode"] = None
            context.user_data["clip_vert"] = None
            context.user_data["mode"] = "clips_mode"
            await st.edit_text(
                "✅ <b>Video downloaded</b> — %s · %sMB\n\n" % (
                    clips_fmt_t(dur) if dur else "?", r.get("size_mb"))
                + clip_choice_text(None, None, context.user_data.get("clip_ai")),
                reply_markup=clip_choice_kb(None, None, context.user_data.get("clip_ai")), parse_mode=HTML)
            add_use(uid)
            return
        await update.message.reply_text(
            clips_help_card() + "\n\n📸 <b>Now send the video file (or a direct .mp4 link):</b>",
            parse_mode=HTML)
        add_use(uid)
        return

    if mode == "numinfo":
        # ---------- Safe local phone metadata only; personal-record lookup stays disabled ----------
        _u = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u, uid):
            await update.message.reply_text(get_credits_over_text("numinfo"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            add_use(uid)
            return

        res = lookup_phone_info(raw_text)          # local (free): operator, circle, validity
        if not res.get("ok"):
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
            add_use(uid)
            return

        # 1) basic card — turant (koi wait nahi)
        rows = []
        pair = []
        for label, url in res["links"]:
            pair.append(InlineKeyboardButton(label, url=url))
            if len(pair) == 2:
                rows.append(pair); pair = []
        if pair:
            rows.append(pair)

        card = [
            f"📱 <b>{to_bold('NUMBER INFORMATION')}</b>",
            "━━━━━━━━━━━━━━━━━━━━━━",
            f"• <b>Number:</b> <code>{res['international']}</code>",
            f"• <b>National:</b> {res['national']}",
            f"• <b>Type:</b> {res['type']} {res['series_note']}",
            f"• <b>Operator:</b> {res['operator']}",
            f"• <b>Circle/Region:</b> {res['circle']}",
            f"• <b>Country:</b> {res['country']} ({res.get('country_code') or '—'})",
            f"• <b>Timezone:</b> {res['timezones']}",
            f"• <b>Valid:</b> {'✅ Haan' if res['valid'] else '⚠️ Suspicious'}",
            "━━━━━━━━━━━━━━━━━━━━━━",
        ]

        card.extend([
            "🔒 <b>Personal-record lookup disabled</b>",
            "Leaked data se naam, family/linked numbers, address ya government-ID fetch nahi hote.",
            "Sirf upar diya gaya non-sensitive phone metadata dikhaya gaya hai.",
            "━━━━━━━━━━━━━━━━━━━━━━",
        ])

        await update.message.reply_text("\n".join(card),
                                        reply_markup=InlineKeyboardMarkup(rows) if rows else None,
                                        parse_mode=HTML)
        add_use(uid)
        return

    if mode == "aadhaar":
        context.user_data.pop("mode", None)
        await update.message.reply_text(
            "🔒 <b>Aadhaar/family lookup yahan supported nahi hai.</b>\n"
            "Aadhaar number is chat me mat bhejein. Apne records ke liye UIDAI MyAadhaar ya NFSA official portal use karein.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("UIDAI MyAadhaar", url="https://myaadhaar.uidai.gov.in/")],
                [InlineKeyboardButton("NFSA official portal", url="https://nfsa.gov.in/")],
            ]), parse_mode=HTML)
        return

    if mode == "ifsc":
        i_res = lookup_ifsc(raw_text)
        if i_res.get("ok"):
            rows = [[InlineKeyboardButton("📍 Branch on Google Maps", url=i_res["maps_link"])]]
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
                rows = [[InlineKeyboardButton("📍 See on Map", url=p_res["maps_link"])]] if p_res.get("maps_link") else []
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
            st = await update.message.reply_text("🔍 Finding the pincode from the area name...")
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
                    "\n\n💡 Tap the button below to copy the pincode:",
                    reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML,
                )
            else:
                await st.edit_text(f"❌ {a_res.get('error')}\n\n💡 Or send a 6-digit pincode (example <code>800001</code>)", parse_mode=HTML)
        add_use(uid)
        return

    # ID & USERNAME FINDER — REAL existence check (GitHub/Telegram/YouTube/TikTok/Steam)
    if mode == "idfind":
        if raw_text.lower() == "me":
            await update.message.reply_text(
                f"🆔 <b>Your Telegram ID:</b> <code>{uid}</code>\n"
                f"👤 <b>Name:</b> {hesc(update.effective_user.first_name or '')}\n"
                f"🔗 <b>Username:</b> @{update.effective_user.username or 'not set'}",
                parse_mode=HTML,
            )
            return

        if raw_text.startswith("@") or re.fullmatch(r"[A-Za-z0-9._\-]{2,}", raw_text.strip()):
            st = await update.message.reply_text("🔍 Checking 5 platforms for the real account...")
            p_info = check_username_platforms(raw_text)
            if not p_info.get("ok"):
                await st.edit_text(f"❌ {p_info.get('error')}", parse_mode=HTML)
                return

            lines = []
            for r in p_info["results"]:
                if r["exists"] is True:
                    extra = f" — <i>{hesc(str(r['extra'])[:45])}</i>" if r.get("extra") else ""
                    lines.append(f"✅ <b>{r['label']}</b> — account FOUND{extra}")
                elif r["exists"] is False:
                    lines.append(f"❌ <b>{r['label']}</b> — no account found")
                else:
                    lines.append(f"❔ <b>{r['label']}</b> — could not check")

            # Lazy search (bot DB) se Telegram ID bhi mil jaye to
            found = find_by_username("@" + p_info["username"])
            id_line = f"\n🆔 <b>ID saved with the bot:</b> <code>{found[0]}</code> ({hesc(found[1])})" if found else ""

            rows = [[InlineKeyboardButton(f"🔗 {l['label']}", url=l["url"])] for l in p_info["links"][:8]]
            await st.edit_text(
                f"🔍 <b>{to_bold('USERNAME CHECK')}:</b> <code>@{p_info['username']}</code>\n"
                f"(found on {p_info['found']}/5 platforms)\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                + "\n".join(lines) + id_line +
                "\n━━━━━━━━━━━━━━━━━━━━━━\n"
                "👇 Direct links to open the other platforms:",
                reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML,
            )
            add_use(uid)
            return

        await update.message.reply_text(

            "🆔 <b>ID & USERNAME FINDER</b>\n"
            "\n"
            "Three ways:\n"
            "1️⃣ Send <code>me</code> → your own Telegram ID\n"
            "2️⃣ <b>Forward a message</b> from any user/channel → their ID\n"
            "3️⃣ Send <code>@username</code> → real check on 5 platforms ✅/❌\n"
            "\n"
            "<i>Note: a private user's ID is shown only if the message is forwardable.</i>",
            parse_mode=HTML,
        )
        return




    if mode == "qr":
        buf = make_qr_bytes(raw_text)
        await update.message.reply_photo(
            photo=buf,
            caption=f"📷 <b>{to_bold('HD QR CODE READY')}</b>\n\n🔗 <code>{hesc(raw_text[:80])}</code>\n\n<i>The link opens as soon as you scan it.</i>",
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
            "📐 Now type the <b>land area</b> — simple format:\n"
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
            await update.message.reply_text("❌ Could not read the rate. Type only the number (example <code>3000</code>).", parse_mode=HTML)
            return
        context.user_data["mode"] = "kagaz_registry_buyer"
        context.user_data["kagaz_reg_rate"] = rate
        await update.message.reply_text(
            "👤 Who is the buyer? Type <code>male</code> / <code>female</code> / <code>joint</code>\n"
            "<i>(Bihar: 1% less stamp duty for women or joint with a woman)</i>", parse_mode=HTML)
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
            "📄 <b>Send the bank statement PDF</b> (as a document/file).\n"
            "<i>Send the PDF only — not a screenshot or photo (they have no table).</i>", parse_mode=HTML)
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
        await update.message.reply_text("👆 Pick an option from the buttons above.", parse_mode=HTML)
        return

    if mode == "media_ytmp3":
        await do_ytmp3(update, context, uid, raw_text.strip())
        return

    if mode in ("media_ringtone", "media_karaoke", "media_8d", "media_bass", "media_voice_wait",
                "media_v2mp3", "media_trim_wait", "media_compress_wait", "media_status_audio"):
        await update.message.reply_text("🎵 First <b>send an audio/video file</b> (as per the instructions above).", parse_mode=HTML)
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
            await update.message.reply_text("⚠️ Send both the photo and the song first.", parse_mode=HTML)
            context.user_data["mode"] = "media_status_photo"
            return
        await update.message.reply_text("🎬 Making the status video... (20-90 seconds)")
        res = desi.make_status_video(img, aud, txt, seconds=30)
        if not res.get("ok"):
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
            return
        await update.message.reply_video(video=res["bytes"], filename="status.mp4", supports_streaming=True,
                                         caption=("🎬 <b>STATUS VIDEO READY ✅</b> (9:16 — WhatsApp/Instagram status)\n"
                                                  "📥 Download it and put it straight on your status.\n\n"
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
            "Now send the <b>WiFi password</b>:\n"
            "(if it is open WiFi, send <code>none</code>)", parse_mode=HTML)
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
            "Now send the <b>phone number</b> (example <code>9876543210</code>):", parse_mode=HTML)
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
                     f"• <b>Name:</b> {hesc(name)}\n"
                     f"• <b>Phone:</b> <code>{hesc(phone)}</code>\n\n"
                     "📱 The contact saves on the phone as soon as it is scanned (name + number) ✅"),
            parse_mode=HTML)
        add_use(uid)
        return

    if mode == "short":
        st = await update.message.reply_text("🔗 Making short links (6 providers)...")
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

                f"⚠️ <b>Could not make a short link</b> (all providers are busy).\n"
                "🧹 <b>Cleaned original link:</b>",
                parse_mode=HTML,
            )
        add_use(uid)
        return

    if mode == "linkbypass":
        st = await update.message.reply_text("🔓 Opening the link and checking the redirect chain...")
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
            f"🧹 <b>Final Clean Link (tracking removed):</b>\n<code>{clean}</code>"
            + (f"\n\nℹ️ {hesc(str(cloud.get('error','')))[:100]}" if cloud.get('error') and 'not supported' not in str(cloud.get('error','')) else ""),
            reply_markup=InlineKeyboardMarkup(kb_rows),
            parse_mode=HTML,
        )
        add_use(uid)
        return

    if mode == "linkcheck":
        st = await update.message.reply_text("🛡️ Running a 6-layer safety scan on the link...")
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
            f"🔍 <b>What was found:</b>\n{reasons_txt}\n\n"
            f"💡 <b>What to do:</b> {chk.get('advice')}"
        )
        kb_rows = [[InlineKeyboardButton("🌐 Open Final Link", url=chk.get("final_url"))]]
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
                "⚠️ <b>How much money did you take (principal)?</b> Send it like:\n"
                "<code>50000</code> ya <code>1.5 lakh</code> ya <code>50k</code>", parse_mode=HTML)
            return
        context.user_data["int_principal"] = p_amt
        context.user_data["mode"] = "int_rate"
        await update.message.reply_text(
            f"📈 <b>{to_bold('VYAAJ (CHAKRAVRIDDHI) CALCULATOR')}</b> — Step 1/3 ✅\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Amount:</b> {inr(p_amt)} ({words_amount(p_amt)})\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Step 2/3 — <b>What is the monthly interest?</b>\n\n"
            "👉 <b>How many rupees per ₹100 per month?</b>\n"
            "   (example: ₹5 per ₹100 per month → send only <code>5</code>)\n\n"
            "Or if you know the percentage: <code>3% month</code>\n"
            "<i>(monthly, not yearly)</i>",
            parse_mode=HTML,
        )
        return

    if mode == "int_rate":
        t = raw_text.lower().replace("%", " ").strip()
        m = re.search(r"\d+(?:\.\d+)?", t)
        if not m:
            await update.message.reply_text("⚠️ Send the interest number (example <code>5</code> = ₹5 per ₹100 per month)", parse_mode=HTML)
            return
        per_ht = float(m.group(0))
        if per_ht > 100:
            await update.message.reply_text("⚠️ That is too high. How many rupees per ₹100 per month (example 2, 3, 5)?", parse_mode=HTML)
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
            f"📊 Interest: <b>₹{per_ht:g} per ₹100 per month</b> ({monthly_rate:g}% per month)\n"
            f"🧮 First month interest: <b>{inr(first_int)}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Step 3/3 — <b>How many months should I calculate?</b>\n"
            "(example <code>12</code> months, or <code>2 years</code>)",
            parse_mode=HTML,
        )
        return

    if mode == "int_time":
        t = raw_text.lower()
        years = re.search(r"(\d+(?:\.\d+)?)\s*(saal|sal|year|yr)", t)
        months_only = re.search(r"(\d+(?:\.\d+)?)\s*(months?|mahine|mahina|m\b)", t)
        bare = re.search(r"^(\d+)\s*$", t.strip())
        months = 0
        if years:
            months += int(float(years.group(1)) * 12)
        if months_only:
            months += int(float(months_only.group(1)))
        if not years and not months_only and bare:
            months = int(bare.group(1))
        if months < 1 or months > 600:
            await update.message.reply_text("⚠️ Send the time: <code>12</code> (months) or <code>2 years</code>", parse_mode=HTML)
            return

        principal = float(context.user_data.get("int_principal", 0))
        rate_m = float(context.user_data.get("int_monthly_rate", 0))
        per_ht = context.user_data.get("int_per_hundred", rate_m)
        v = village_compound_interest(principal, rate_m, months)
        context.user_data.pop("mode", None)

        # Mahine ka table (pehle 6) + milestones
        rows_txt = []
        for r in v["rows"][:6]:
            rows_txt.append(f"   {r['month']}. Interest {inr(r['interest'])} → Total {inr(r['closing'])}")
        if months > 6:
            rows_txt.append(f"   ... ({months - 6} months and keeps growing like this)")
        mile_txt = "".join(f"\n   • after {k}: <b>{inr(amt)}</b>" for k, amt in v["milestones"].items())

        from datetime import timedelta as _td
        _msg_date = getattr(update.message, "date", None)
        end_date = (_msg_date + _td(days=30 * months)) if _msg_date else None
        end_line = f"\n📅 <b>{months} months later (approx):</b> {end_date.strftime('%d %b %Y')}" if end_date else ""

        await update.message.reply_text(
            f"📈 <b>{to_bold('COMPOUND INTEREST REPORT')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Money taken:</b> {inr(v['principal'])} ({words_amount(v['principal'])})\n"
            f"📊 <b>Interest:</b> ₹{per_ht:g} per ₹100 per month ({rate_m:g}% monthly)\n"
            f"⏳ <b>Time:</b> {months} months\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ First month interest: <b>{inr(v['first_month_interest'])}</b>\n"
            f"2️⃣ {months} months <b>total interest:</b> <b>{inr(v['total_interest'])}</b>\n"
            f"3️⃣ <b>You have to pay back: {inr(v['total_payable'])}</b> ({words_amount(v['total_payable'])})\n"
            f"{end_line}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Month by month (compound):</b>\n" + "\n".join(rows_txt) +
            (f"\n\n🎯 <b>What you will owe when:</b>{mile_txt}" if mile_txt else "") +
            "\n━━━━━━━━━━━━━━━━━━━━━━\n"

            "💡 <b>Understand:</b> this is <b>compound</b> interest — interest that is not paid every month is added to the principal and then earns interest too. That is why it grows very fast.\n"
            "👉 If you paid <b>only interest every month</b>, the principal would stay the same and interest would stay ₹{first:,.0f}/month (the village way).\n"
            "<i>This information is not financial advice.</i>".format(first=v["first_month_interest"]),
            parse_mode=HTML,
        )
        add_use(uid)
        return

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
        st = await update.message.reply_text("📸 " + ("Taking the full page screenshot (this takes time)..." if fullpage else "Taking the HD screenshot..."))
        buf = site_screenshot(raw_text, fullpage=fullpage)
        if buf:
            await update.message.reply_photo(
                photo=buf,
                caption=(f"📜 <b>{to_bold('FULL PAGE SCREENSHOT')}</b>\n🌐 <code>{hesc(raw_text[:80])}</code>" if fullpage
                         else f"🖼️ <b>{to_bold('HD SCREENSHOT')}</b>\n🌐 <code>{hesc(raw_text[:80])}</code>\n\n📜 Need the full page? Menu → 'SITE SCREENSHOT' → 📜 Full Page."),
                parse_mode=HTML)
            await st.delete()
        else:
            await st.edit_text(

                "❌ Could not take the screenshot.\n"
                "💡 <b>What to do:</b>\n"
                "• Send the URL with <code>https://</code> in front\n"
                "• The site may have blocked the bot — try another site\n"
                "• Try again after 10-20 seconds")
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
                "👇 What should this channel become?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📡 Make this SOURCE (posts come from here)", callback_data=f"fc_src:{f_chat.id}")],
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
                 "bankpdf_pass": "🏦 BANK PDF", "clips_mode": "🎬 CLIP MAKER"}.get(_mode_now)
        if _name:
            await update.message.reply_text(
                f"🤔 <b>Samajh nahi aaya.</b> {_name} tool chalu hai — "
                "upar likhe steps ke hisaab se dobara bhejo, ya /cancel karke naya tool kholo.",
                parse_mode=HTML)
            return
    await update.message.reply_text("👇 Pick a tool from the grid menu below:", reply_markup=kb_for(uid))


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
        await update.message.reply_text("❌ This does not look like a YouTube link. Send a link like <code>https://youtu.be/xxxx</code>",
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
        if res.get("locked"):
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

    # ---------- 🎬 CLIP MAKER ----------
    if mode in ("clips", "clips_wait", "clips_mode") and kind in ("video", "video_note", "animation"):
        _u_c = get_user(uid)
        if not can_use_premium_tool(_u_c, uid):
            await say(get_credits_over_text("clips"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return True
        d = tempfile.mkdtemp(prefix="clipin_")
        p = os.path.join(d, "src.mp4")
        try:
            with open(p, "wb") as fh:
                fh.write(data)
        except Exception as e:
            await say(fail_msg("FILE SAVE FAILED", str(e)[:120]), parse_mode=HTML)
            return True
        info = await asyncio.to_thread(clips_probe, p)
        dur = float(info.get("duration") or 0)
        if dur and dur > CLIP_MAKER_MAX_MIN * 60:
            clips_cleanup(d)
            await say(
                "⚠️ <b>Video is too long</b> — this one is <b>%d min</b>. Limit is <b>%d min</b> "
                "(server limit).\n👉 Send a shorter part of the video."
                % (int(dur // 60) or 1, int(CLIP_MAKER_MAX_MIN)), parse_mode=HTML)
            return True
        if dur and dur < 20:
            clips_cleanup(d)
            await say("⚠️ <b>Video is too short</b> — need at least 20 seconds of video.", parse_mode=HTML)
            return True
        context.user_data["clip_src"] = p
        context.user_data["clip_mode"] = None
        context.user_data["clip_vert"] = None
        context.user_data["mode"] = "clips_mode"
        await say(
            "✅ <b>Video received</b> — %s · %sMB%s\n\n" % (
                clips_fmt_t(dur) if dur else "?", round(len(data) / 1048576, 1),
                "" if info.get("has_audio") else " · ⚠️ no sound (scene-wise clips)") +
            clip_choice_text(None, None, context.user_data.get("clip_ai")),
            reply_markup=clip_choice_kb(None, None, context.user_data.get("clip_ai")), parse_mode=HTML)
        return True

    # ---------- ⚡ MEDIA STUDIO ----------
    if mode == "media_menu":
        await say("👆 Pick an option from the buttons above (MP3 / Status / Karaoke...).")
        return True

    if mode == "media_ytmp3" and kind == "text":
        return False

    if mode in ("media_ringtone",) and kind in ("audio", "video", "voice", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        context.user_data["media_audio"] = data
        context.user_data["mode"] = "media_ringtone_start"
        await say("⏱️ From which second should the ringtone start? (example <code>45</code> or <code>1:20</code>)\n"
                  "<i>The ringtone will be 30 seconds long.</i>", parse_mode=HTML)
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
        await say("🗣️ Now <b>pick a voice</b> (kid / heavy / robot / ghost / gadget / echo):",
                  reply_markup=voice_preset_kb(), parse_mode=HTML)
        return True

    if mode == "media_trim_wait" and kind in ("video", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        context.user_data["media_video"] = data
        context.user_data["mode"] = "media_trim_time"
        await say("✂️ From where to where should I cut? Type it like: <code>0:10 0:45</code>\n"
                  "<i>(start time and end time)</i>", parse_mode=HTML)
        return True

    if mode == "media_compress_wait" and kind in ("video", "video_note"):
        if not can_use_premium_tool(get_user(uid), uid):
            await say(get_credits_over_text("mediastudio"), reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return True
        st = await say("🗜️ Compressing the video... (30 seconds - 3 minutes)\n<i>Big videos take more time.</i>")
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
        await say("✍️ Now what <b>text should be on the status</b>? (1-3 lines)\n<i>example: Happy Birthday Rahul 🎂</i>", parse_mode=HTML)
        return True

    return False


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
        await update.message.reply_text("✅ <b>Custom Thumbnail Saved!</b> From now this thumbnail is used on all forwarded videos/documents.", reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
        return

    # ---------- v38: STATUS VIDEO (photo) ----------
    if mode == "media_status_photo":
        photo_file = await update.message.photo[-1].get_file()
        buf = io.BytesIO()
        await photo_file.download_to_memory(buf)
        context.user_data["media_status_photo"] = buf.getvalue()
        context.user_data["mode"] = "media_status_audio"
        await update.message.reply_text(
            "🎵 Now <b>send the song</b> (MP3/audio file for the status).\n"
            "<i>If you want a song from YouTube, first make it with 🎵 YouTube → MP3, then send it here.</i>", parse_mode=HTML)
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

            "📝 <b>First send the UTR</b> (as text), then the screenshot.\n"
            "Open the payment app → transaction details → copy the <b>UTR / Ref No</b> (12 digit) and send it here.\n"
            "❓ Not sure where to find it? Tap the button below.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❓ Where do I find the UTR?", callback_data="pay_utr_help")]]),
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
        await update.message.reply_text(f"📸 {len(pages)} photo(s) added! Send more or tap the button 👇", reply_markup=kb)
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

    # ---------- v38: naye tools ke files (PDF / audio / video / image) ----------
    _our_modes = ("bankpdf", "bankpdf_pass", "media_ringtone", "media_ringtone_start",
                  "media_karaoke", "media_8d", "media_bass", "media_voice_wait", "media_v2mp3",
                  "media_trim_wait", "media_compress_wait", "media_status_audio",
                  "clips", "clips_wait", "clips_mode")
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


async def on_pdf_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.data in ("make_pdf_now", "make_pdf_a4"):
        pages = context.user_data.get("pdf_pages", [])
        if not pages:
            await q.answer("Send the photo first!", show_alert=True)
            return
        a4 = (q.data == "make_pdf_a4")
        await q.answer("Making the A4 PDF..." if a4 else "Making the PDF...")
        pdf_bytes = pages_to_pdf(pages, a4=a4)
        buf = io.BytesIO(pdf_bytes)
        buf.name = "UtilityDuniya_A4_Document.pdf" if a4 else "UtilityDuniya_Document.pdf"
        await q.message.reply_document(
            document=buf,
            caption=(f"📄 <b>{to_bold('A4 PRINT-READY PDF')}</b>\n"
                     f"• {len(pages)} pages • A4 size (nothing gets cut when printed) ✅\n"
                     f"• You can print it directly" if a4 else
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

    # Tutorial page (telegra.ph) — background me banta/update hota hai, bot rukta nahi
    threading.Thread(target=publish_tutorial_now, daemon=True).start()
    # Keepalive server SIRF polling mode me — webhook mode me yehi port PTB use karega
    if not WEBHOOK_URL:
        threading.Thread(target=_keepalive, daemon=True).start()

    app = (Application.builder().token(BOT_TOKEN).post_init(_post_init)
           .connect_timeout(30.0).read_timeout(60.0).write_timeout(240.0)
           .media_write_timeout(300.0).pool_timeout(60.0).build())

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("help", cmd_tutorial))
    app.add_handler(CommandHandler(["tutorial", "madad", "guide"], cmd_tutorial))
    app.add_handler(CommandHandler(["activate", "grantvip"], cmd_activate))
    app.add_handler(CommandHandler("tutrefresh", cmd_tutrefresh))
    app.add_handler(CommandHandler(["vehstatus", "vehicleapi"], cmd_vehstatus))
    app.add_handler(CommandHandler(["hubstatus", "hubapi", "osintstatus"], cmd_hubstatus))
    app.add_handler(CommandHandler(["imeistatus", "imeiapi"], cmd_imeistatus))
    app.add_handler(CommandHandler(["clipstatus", "clipapi"], cmd_clipstatus))
    app.add_handler(CommandHandler(["aistatus", "aiapi"], cmd_aistatus))
    app.add_handler(CommandHandler(["credits", "addcredits"], cmd_credits))
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
    app.add_handler(CommandHandler("terabox", lambda u, c: u.message.reply_text(tool_prompt("terabox"), reply_markup=tool_tutorial_kb("terabox"), parse_mode=HTML)))
    app.add_handler(CommandHandler("cloner", lambda u, c: u.message.reply_text(f"🔄 <b>{to_bold('CHANNEL CLONER')}</b>", reply_markup=get_cloner_settings_kb(u.effective_user.id), parse_mode=HTML)))
    app.add_handler(CommandHandler("sarkari", lambda u, c: u.message.reply_text(SARKARI_CITIZEN_TEXT, reply_markup=get_sarkari_citizen_kb(), parse_mode=HTML)))

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
    # ---------- v47: WEBHOOK MODE (Render par sabse safe) ----------
    # Polling me har deploy par 10-20 second tak do instance ek saath getUpdates
    # karte hain -> Telegram "Conflict: terminated by other getUpdates request".
    # Webhook me Telegram khud update bhejta hai, getUpdates hota hi nahi -> Conflict kabhi nahi.
    if WEBHOOK_URL:
        # PTB ka default webhook server sirf Telegram POST route banata hai; Render/UptimeRobot
        # ke GET / aur GET /health ko 404 se bachane ke liye same port par health routes jodein.
        from modules.render_health import install_webhook_health_routes
        install_webhook_health_routes()
        port = int(os.environ.get("PORT", "10000"))
        secret = (os.environ.get("WEBHOOK_SECRET") or BOT_TOKEN.split(":")[-1]).strip("/")
        path = f"/webhook/{secret}"
        full_url = WEBHOOK_URL.rstrip("/") + path
        # Secret webhook path ko logs me kabhi print na karein.
        log.warning("WEBHOOK MODE | instance=%s pid=%s | polling OFF (koi Conflict nahi)",
                    socket.gethostname(), os.getpid())
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

    # NOTE: polling me ek hi bot instance chalna chahiye. Agar do instance (do Render
    # service / do deploy ek saath) getUpdates karenge to Telegram "Conflict:
    # terminated by other getUpdates request" dega aur bot chup ho jayega.
    # Permanent chhutkara chahiye to Environment me WEBHOOK_URL daal do.
    log.warning("STARTING POLLING | instance=%s pid=%s | only ONE instance must run",
                socket.gethostname(), os.getpid())
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
