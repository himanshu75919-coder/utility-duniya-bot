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
import sys
import json
import logging
import os
import re
import socket
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

# v60: SAFE CONFIG LAYER — peeche `int(os.getenv("ADMIN_ID", "0") or 0)` tha.
# Render ke Environment tab me galti se aisi value aa jaye:
#     ADMIN_ID = 12345   # mera id      <- int() CRASH -> bot start hi nahi hota
#     FREE_CREDITS = 25 credits          <- CRASH
# ...to "Application failed to start" aata tha aur samajh hi nahi aata ki kyun.
# Ab `env_int` kachra value ko ignore karke default le leta hai + warn karta hai.
from modules.core.safeconf import (
    env_bool as _env_bool,
    env_float as _env_float,
    env_int as _env_int,
    env_str as _env_str,
)
from modules.core.guard import (
    crash_state as guard_crash_state,
    guarded,
    install_global_guard,
    register_gc_trigger,
    start_hang_watchdog,
    start_memory_watchdog,
)
from modules.core.safesend import (
    safe_answer_cb,
    safe_delete,
    safe_edit,
    safe_reply,
    safe_send_document,
    safe_send_photo,
    safe_send_text,
    safe_send_video,
    trim_callback_data,
)
from modules.core.vault import db_path as vault_db_path, vault
# v60.4: 💼 BUSINESS STUDIO — 10 naye earning tools (invoice, resume, biodata,
# certificate, ID card, visiting card, letter, UPI poster, labels, EMI card)
from modules.business_tools import (
    BRAND as BIZ_BRAND,
    visiting_card_image as biz_vcard,
    upi_qr_image as biz_upi_qr,
    resume_image as biz_resume,
    set_brand as biz_set_brand,
    to_pdf as biz_to_pdf,
    emi_breakup as biz_emi_breakup,
    emi_card_image as biz_emi_card,
    has_devanagari as biz_has_hindi,
    certificate_image as biz_certificate,
    biodata_image as biz_biodata,
    idcard_image as biz_idcard,
    invoice_image as biz_invoice,
    label_sheet_image as biz_labels,
    salary_slip_image as biz_salary,       # v62
    menu_card_image as biz_menucard,       # v62
    letter_image as biz_letter,
)



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
from telegram.error import Conflict
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    filters,
)

# Internal modules
from database import (
    CREDITS_START,
    parse_dt,
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
    # v60: premium ledger — premium ka PERMANENT record (kabhi na khoye)
    ledger_for,
    ledger_all,
    premium_ledger_stats,
    restore_premium_from_ledger,
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
    YT_QUALITY_OPTIONS,
    yt_cached_qualities,
    yt_warm_qualities,
    _yt_quality_download,
    friendly_dl_error,
)
from modules.toolkit_extras import (
    analyze_link,
    expand_url,
    shorten_url,
)
from modules import api_hub as hubapi
from modules.render_health import (webhook_url_from_env, webhook_url_usable,
                                   webhook_preflight)
from modules.imei_lookup import (
    device_title as imei_title,
    fetch_imei_details,
    help_card as imei_help_card,
    is_configured as imei_api_ready,
    render_caption as render_imei_caption,
    render_text as render_imei_text,
    search_device as imei_search_device,
    specs_filename as imei_specs_filename,
    specs_json_bytes as imei_specs_json,
    validate_imei as imei_validate,
)
from modules import numinfo_provider as numprov
from modules.osint_tools import (
    search_by_area_name,
    lookup_ifsc,
    lookup_phone_info,
    lookup_pincode,
)
from modules.gaming_tools import (
    ff_player_info,
    bgmi_player_info,
)
from modules.temp_mail import (
    tm_create,
    tm_poll,
    tm_delete,
)
from modules.general_tools import (
    vcard_data,
    wifi_qr_data,
    app_lookup,
    make_branded_qr,
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
# v53.0: per-tool telemetry — kaunsa tool kitni baar fail hua, kaunsi upstream
# API DEAD hai. Admin `/sys` par dikhta hai (pehle 58 jagah `except: pass` tha
# aur kisi ko pata hi nahi chalta tha ki BGMI/FF jaisa tool kab se toota hua hai).
from modules.core.telemetry import (
    note as tel_note,
    snapshot as tel_snapshot,
    worst_tools as tel_worst_tools,
)
from modules.core.cache import TTLCache
from modules.core.html_safe import cut_html, strip_html

# Info-tools ka shared cache (IFSC / pincode / IP / area) — same sawaal par
# API call dobara nahi hoti. 30 min TTL: ye data din bhar change nahi hota.
INFO_CACHE = TTLCache(maxsize=_env_int("INFO_CACHE_SIZE", 4096, lo=64, hi=200000),
                      default_ttl=_env_int("INFO_CACHE_TTL", 1800, lo=30, hi=86400))
# v60: memory watchdog in caches ko safai ke waqt khali kar sakta hai (Render
# free plan par 512 MB se aage jaate hi "Killed" ho jata tha).
def _clear_caches_mem() -> None:
    try:
        INFO_CACHE.clear()
    except Exception:
        pass
    for _c in ("APP_CACHE", "GAME_CACHE", "IMEI_CACHE", "MEDIA_QCACHE", "_HUB_MEM"):
        _o = globals().get(_c)
        if _o is not None and hasattr(_o, "clear"):
            try:
                _o.clear()
            except Exception:
                pass
register_gc_trigger(_clear_caches_mem)

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
    "media_tts":   (8,  60,  "Text → Hindi Voice"),
    "yt_q":        (8,  120, "YouTube Quality"),
    # normal info tools
    "bgmi":        (8,  60,  "BGMI UID"),
    "ffuid":       (8,  60,  "FF UID"),
    "tempmail":    (10, 120, "Temp Mail"),
    "ifsc":        (15, 60,  "IFSC Info"),
    "pin":         (15, 60,  "Pincode Info"),
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
    # ---- v60.4: BUSINESS STUDIO (CPU-heavy file generation) ----
    "biz_invoice":     (12, 120, "Invoice / Bill"),
    "biz_resume":      (10, 120, "Resume / CV"),
    "biz_biodata":     (10, 120, "Marriage Bio-data"),
    "biz_certificate": (12, 120, "Certificate"),
    "biz_idcard":      (10, 120, "ID Card"),
    "biz_vcard":       (10, 120, "Visiting Card"),
    "biz_letter":      (12, 120, "Application / Letter"),
    "biz_upi":         (12, 120, "UPI Poster"),
    "biz_labels":      (10, 120, "Price Label Sheet"),
    "biz_emi":         (12, 120, "EMI / Loan Card"),
    "biz_salary":      (10, 120, "Salary Slip"),          # v62
    "biz_menucard":    (10, 120, "Menu / Rate Card"),     # v62
}

# ---------------- CONFIG ----------------
BOT_TOKEN = _env_str("BOT_TOKEN", "").strip()
ADMIN_ID = _env_int("ADMIN_ID", 0)

# v33: ek se zyada admin (ADMINS=123,456) — owner + helper admins kaam kar sakte hain
_ADMIN_EXTRA = [_env_int(x, 0) for x in re.split(r"[,\s]+", os.getenv("ADMINS", "") or "") if str(x).strip()]
_ADMIN_EXTRA = [x for x in _ADMIN_EXTRA if x > 0]
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
FREE_LIMIT = _env_int("FREE_LIMIT", 10, lo=1, hi=100000)
# v59.7: @username ko CLICKABLE banaya — koi bhi tap kare to seedha owner se
# chat khul jaati hai (uske baad "Start" dabate hi message bhej sakta hai).
# Username Render env se badla ja sakta hai (OWNER_USERNAME) — code chhune ki zaroorat nahi.
OWNER_USERNAME = (os.getenv("OWNER_USERNAME", "").strip().lstrip("@")
                  or "Supermannn_x")
SUPPORT_USERNAME = "@" + OWNER_USERNAME
SUPPORT_URL = f"https://t.me/{OWNER_USERNAME}"
SUPPORT_LINK = f'<a href="{SUPPORT_URL}">@{OWNER_USERNAME}</a>'
# v57: BRAND_TAG pehle bot.py me DEFINED hi nahi tha par numinfo card me use hota tha
# -> AttributeError/NameError crash (kabhi live hit nahi hua kyunki wo branch galat
# number par nahi chalti thi). Ab Render env se padha jaata hai (default wahi brand).
BRAND_TAG = (os.getenv("BRAND_TAG", "").strip() or SUPPORT_USERNAME)
# clickable version (HTML messages ke liye) — tap karo → owner se chat khul jaaye
BRAND_LINK = f'🔥 Powered by <a href="{SUPPORT_URL}">{BRAND_TAG}</a>'
REFER_NEED = _env_int("REFER_NEED", 5, lo=1, hi=10000)
HTML = "HTML"
BAN_MSG = f"🚫 Aapka account ban hai. Admin se baat karo: {SUPPORT_LINK}"
BOT_VERSION = "v62.0 FREE4ALL — Salary Slip + Menu Card (2 naye tools) · saare tools 100% FREE · v60.4 FORTRESS base"
START_TIME = datetime.now()

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("utility-super-bot")


# =====================================================================
#  v60 — 🛡️ EVERY PREMIUM GRANT = INSTANT BACKUP
# ---------------------------------------------------------------------
# Sabse bada darr ye tha ki "premium user delete na ho". Isko pakka karne ke
# liye hum `grant_premium` ko wrap kar dete hain: jaise hi kisi ko VIP milta
# hai (payment approve, admin grant, referral VIP — kuch bhi), uske 1-2 second
# ke andar encrypted backup uth jata hai.
#
# Matlab: agar aaj raat 11 baje kisi ne VIP liya aur 11:05 par Render ne
# service restart kar di — to bot dobara uthte hi us VIP ko WAPAS le aayega.
# Zero loss window.
# =====================================================================
_grant_premium_raw = grant_premium


def _grant_premium_autosave(uid: int, days: int):
    """grant_premium ka safe wrapper + turant vault backup."""
    out = _grant_premium_raw(uid, days)
    try:
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None and loop.is_running():
            loop.create_task(vault.backup_soon(reason=f"grant:{uid}"))
        else:
            # alag thread se (sync context me bhi kaam kare)
            threading.Thread(target=lambda: asyncio.run(
                vault.backup_soon(reason=f"grant:{uid}")), daemon=True).start()
    except Exception as _e:                                      # noqa: BLE001
        log.debug("grant autosave skip: %s", str(_e)[:90])
    return out


grant_premium = _grant_premium_autosave      # poore bot me yahi use hoga
log.info("🛡️ Premium auto-backup wrapper ON — har VIP grant par backup uthega")


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
    "bgmi",                # 🎮 BGMI UID
    "ffuid",               # 🔥 FF UID
    "tempmail",            # 📧 TEMP MAIL
    "qr",                  # 📷 QR CODE (text/wifi/vcard)
    "short",               # 🔗 URL SHORT
    "linkcheck",           # 🔍 LINK CHECK
    "appfind",             # 📦 APP FINDER
    # ---- v60.4: 💼 BUSINESS STUDIO (10 earning tools) ----
    "biz_invoice",         # 🧾 Invoice / GST Bill
    "biz_resume",          # 💼 Resume / CV
    "biz_biodata",         # 💍 Marriage Bio-data
    "biz_certificate",     # 🎓 Certificate
    "biz_idcard",          # 🪪 ID Card
    "biz_vcard",           # 📇 Visiting Card
    "biz_letter",          # 📄 Application / Letter
    "biz_upi",             # 💳 UPI Scan & Pay Poster
    "biz_labels",          # 🏷️ Price Label Sheet
    "biz_emi",             # 🧮 EMI / Loan Card
    # ---- v62: 2 naye earning tools ----
    "biz_salary",          # 💰 Salary Slip
    "biz_menucard",        # 🍽️ Menu / Rate Card
}

PREMIUM_TOOL_NAMES = {
    "insta_dl": "📥 Video Downloader",
    "numinfo": "📱 Number Info",
    "cloner": "🔄 Channel Cloner",
    "bankpdf": "🏦 Bank Statement → Excel",
    "kagaz": "📜 Sarkari Kagaz Suite",
    "mediastudio": "⚡ Media Studio (MP3/Status/Karaoke)",
    "imei": "📲 IMEI / Phone Details",
    "terabox": "⚡ Terabox / Cloud Downloader",
    "vnum": "🌐 Virtual Numbers (OTP)",
    "pp_stamp": "📸 Passport Photo (Name/DOP)",
    "print_sheet": "🖨️ 8-in-1 Print Sheet",
    "doc_compress": "📄 Document PDF Compress",
    "sarkari": "🏛️ Sarkari Seva Portals",
    "ifsc": "🏦 IFSC Info",
    "pin": "📮 Pincode Info",
    "bgmi": "🎮 BGMI UID",
    "ffuid": "🔥 FF UID",
    "tempmail": "📧 Temp Mail",
    "qr": "📷 QR Code",
    "short": "🔗 URL Short",
    "linkcheck": "🔍 Link Check",
    "appfind": "📦 App Finder",
    # ---- v60.4: 💼 BUSINESS STUDIO ----
    "biz_invoice": "🧾 Invoice / GST Bill",
    "biz_resume": "💼 Resume / CV Maker",
    "biz_biodata": "💍 Marriage Bio-data",
    "biz_certificate": "🎓 Certificate Maker",
    "biz_idcard": "🪪 ID Card Maker",
    "biz_vcard": "📇 Visiting Card Maker",
    "biz_letter": "📄 Application / Letter",
    "biz_upi": "💳 UPI Scan & Pay Poster",
    "biz_labels": "🏷️ Price Label Sheet",
    "biz_emi": "🧮 EMI / Loan Card",
    "biz_salary": "💰 Salary Slip",
    "biz_menucard": "🍽️ Menu / Rate Card",
}


def is_premium_tool(action: str) -> bool:
    return action in PREMIUM_TOOLS


def credits_left(u: dict, uid: int = 0) -> int:
    """Bache hue credits (VIP/admin/owner ke liye 999999 = unlimited).

    v61: ALL_FREE mode me SABKE liye unlimited (999999) — isse credits
    kabhi khatam nahi hote, "credits khatam, VIP lo" screen kabhi nahi
    aati, aur saare premium tools sabke liye khul jaate hain.
    """
    if ALL_FREE:
        return 999999
    if uid and is_admin(uid):
        return 999999
    if is_premium(u):
        return 999999
    try:
        return get_credits(uid or u.get("user_id", 0))
    except Exception:
        return 0


def credits_line(u: dict, uid: int = 0) -> str:
    """Chhoti line: credits kitne bache hain.

    v58: VIP/unlimited par ye line AB KHALI rehti hai — user ka order tha ki
    tool ke start me "⚡ Credits: ♾️ Unlimited (VIP)" kahi bhi na dikhe.
    """
    left = credits_left(u, uid)
    if left >= 999999:
        return ""
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
        "• 📲 IMEI • 📦 App Finder • 📌 Pinterest Download • aur saare tools\n"
        "• 💼 Business Studio — Invoice, Resume, Biodata, Certificate,\n"
        "   ID Card, Visiting Card, Letter, UPI QR, Price Tag, EMI Card\n"
        "• ♾️ 30/60/90/120 din ya LIFETIME — sab plans\n\n"
        f"💎 <b>VIP plans:</b> 30d ₹49 • 60d ₹89 • 90d ₹129 • 120d ₹169 • Lifetime ₹199\n"
        "👇 Neeche se VIP lo, unlimited use karo:"
    )


# ======================================================================
# v49.4: VIP-ONLY MODE — saare tools sirf VIP / premium users ke liye
# ======================================================================
# Aapki marzi: "ab se sirf premium users hi use kar sakte hain."
# PREMIUM_ONLY=off karte hi purana system wapas (free tools + credits).
# ======================================================================
#  v61: 🎉 ALL-FREE MODE  —  SAARE TOOLS SABKE LIYE FREE
# ======================================================================
#  Boss ka order: "premium features hata do, saare tools free hone chahiye."
#
#  Kaise kaam karta hai:
#    ALL_FREE = on  (DEFAULT)  ->  har user har tool chala sakta hai.
#                                  Koi credit nahi, koi VIP wall nahi,
#                                  koi "premium lo" wala message nahi.
#    ALL_FREE = off            ->  purana VIP/credits system wapas
#                                  (ya PREMIUM_ONLY=on likh do — wahi
#                                   kaam karega).
#
#  ⚠️ SABSE ZAROORI: is switch se KISI USER KA DATA DELETE NAHI HOTA.
#     DB me premium_until, credits, payments, referrals — sab jaisa hai
#     waisa hi rehta hai. Sirf darwaza khul jata hai. Kabhi bhi
#     ALL_FREE=off karoge to purane VIP waale wapas VIP honge.
# ======================================================================
ALL_FREE = _env_bool("ALL_FREE", True)
if _env_bool("PREMIUM_ONLY", False):
    ALL_FREE = False          # saaf-saaf PREMIUM_ONLY=on likha hai -> premium mode
PREMIUM_ONLY = not ALL_FREE

VIP_WALL_TEXT = (
    "👑 <b>YE TOOL SIRF VIP MEMBERS KE LIYE HAI</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Aapka account <b>free</b> hai — is liye premium tools band hain.\n\n"
    "💎 <b>VIP lene par aapko milega:</b>\n"
    "• 📥 Video Downloader (Instagram, YouTube, FB, X, TikTok… 20+ sites)\n"
    "• 📱 Number Info + 📲 IMEI full spec-sheet + 🏦 IFSC Info\n"
    "• 🔄 Channel Cloner (auto-forward) + 📡 TG Public Info + 🔥 FF/BGMI\n"
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
        [InlineKeyboardButton(f"💬 Support {SUPPORT_USERNAME}", url=SUPPORT_URL)],
    ])


# ---------- v61: FREE MODE ka apna card (VIP wall ki jagah) ----------
FREE_MODE_TEXT = (
    "🎉 <b>SAB TOOLS FREE HAIN!</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Koi VIP nahi, koi credits nahi, koi limit nahi.\n"
    "Aap seedha menu se <b>koi bhi tool</b> dabao — turant chalega. ✅\n\n"
    "📥 Video Downloader · 📱 Number Info · 📲 IMEI Details\n"
    "📸 Passport Photo · 🖨️ 8-in-1 Sheet · 📄 Doc PDF · 🔍 Link Check\n"
    "🏦 Bank PDF → Excel · 📜 Kagaz Suite · ⚡ Media Studio\n"
    "💼 Business Studio — Invoice, Resume, Biodata, Certificate,\n"
    "   ID Card, Visiting Card, Letter, UPI QR, Price Tag, EMI Card\n\n"
    "💡 <i>Naya tool chahiye? Batao — free me add kar dunga.</i>"
)


def free_mode_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Saare tools ki list", callback_data="alltools")],
        [InlineKeyboardButton("💬 Support / Madad", url=SUPPORT_URL)],
    ])


def all_tools_text() -> str:
    """v61: poore bot ke saare tools ki list — sab FREE."""
    _biz = "\n".join(
        f"   {k}. {v[0]} {hesc(v[1])} — {hesc(v[2])}"
        for k, v in enumerate(BIZ_MENU.values(), 1) if v and len(v) >= 3)
    _pv = "\n".join(
        f"   • {hesc(x)}" for x in sorted(set(PREMIUM_TOOL_NAMES.values())))
    return (
        "📋 <b>SAARE TOOLS — 100% FREE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>💼 Business Studio (photo + PDF, print-ready):</b>\n"
        f"{_biz}\n\n"
        "<b>⚡ Baaki saare tools:</b>\n"
        f"{_pv}\n\n"
        "✅ Kisi bhi tool ke liye <b>VIP / credits ki zaroorat NAHI</b>.\n"
        "👉 Neeche keyboard se seedha tool ka naam dabao."
    )


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
         InlineKeyboardButton("💬 Support", url=SUPPORT_URL)],
    ])


def check_limit_exceeded(u: dict, uid: int = 0) -> bool:
    """Purana naam — ab matlab: 'premium tool ke liye credits nahi bache'.
    Free tools par ab koi limit nahi hai."""
    return not can_use_premium_tool(u, uid)


def get_limit_exceeded_text(action: str = "") -> str:
    return get_credits_over_text(action)


def spend_credit_msg(uid: int, action: str = "") -> str:
    """1 credit kharch hone ke baad chhota note."""
    if ALL_FREE:
        return ""            # v61: free mode me credit kat hi nahi raha
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
        [InlineKeyboardButton(f"☎️ Contact {SUPPORT_USERNAME}", url=SUPPORT_URL)],
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
    [f"📮 {to_bold('PINCODE INFO')}", f"📧 {to_bold('TEMP MAIL')}"],
    [f"🎮 {to_bold('BGMI UID')}", f"🔥 {to_bold('FF UID')}"],
    [f"📷 {to_bold('QR CODE')}", f"📦 {to_bold('APP FINDER')}"],
    [f"🔗 {to_bold('URL SHORT')}", f"🔍 {to_bold('LINK CHECK')}"],
    [f"🏦 {to_bold('BANK STATEMENT → EXCEL')}", f"📜 {to_bold('SARKARI KAGAZ SUITE')}"],
    [f"💼 {to_bold('BUSINESS STUDIO')}", f"⚡ {to_bold('MEDIA STUDIO (MP3/STATUS)')}"],
    [f"📲 {to_bold('IMEI / PHONE DETAILS')}", f"💎 {to_bold('VIP PREMIUM')}"],
    [f"🎁 {to_bold('REFER & EARN')}", f"👤 {to_bold('MY ACCOUNT')}"],
    [f"❓ {to_bold('HELP / TUTORIAL')}", f"💬 {to_bold('SUPPORT / MADAD')}"],
]


# v61: FREE mode me "💎 VIP PREMIUM" button ki jagah kaam ki cheez
if ALL_FREE:
    for _row_v in KB_BTNS:
        for _i_v, _lab_v in enumerate(_row_v):
            if "VIP PREMIUM" in unbold(_lab_v).upper():
                _row_v[_i_v] = f"\U0001F4CB {to_bold('ALL TOOLS (FREE)')}"


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
    "BGMI UID": "bgmi",
    "BGMI": "bgmi",
    "FF UID": "ffuid",
    "FREE FIRE UID": "ffuid",
    "TEMP MAIL": "tempmail",
    "TEMPMAIL": "tempmail",
    "QR (LINK / TEXT)": "qr",
    "QR (WIFI SHARE)": "qr_wifi",
    "QR (CONTACT CARD)": "qr_vcard",
    "SARKARI SEVA PORTALS": "sarkari",
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
    # ---- v60.4: 💼 BUSINESS STUDIO (earning tools) ----
    "BUSINESS STUDIO": "bizstudio",
    "BUSINESS TOOLS": "bizstudio",
    "INVOICE": "biz_invoice", "INVOICE / BILL": "biz_invoice",
    "BILL BANAO": "biz_invoice", "GST BILL": "biz_invoice",
    "RESUME": "biz_resume", "RESUME / CV": "biz_resume", "CV MAKER": "biz_resume",
    "BIODATA": "biz_biodata", "MARRIAGE BIODATA": "biz_biodata",
    "SHAADI BIODATA": "biz_biodata", "VIVAH PARICHAY": "biz_biodata",
    "CERTIFICATE": "biz_certificate", "CERTIFICATE MAKER": "biz_certificate",
    "ID CARD": "biz_idcard", "ID CARD MAKER": "biz_idcard",
    "VISITING CARD": "biz_vcard", "VISITING CARD MAKER": "biz_vcard",
    "APPLICATION LETTER": "biz_letter", "LETTER MAKER": "biz_letter",
    "LEAVE APPLICATION": "biz_letter",
    "UPI QR": "biz_upi", "UPI PAYMENT QR": "biz_upi", "SCAN AND PAY": "biz_upi",
    "PRICE LABEL": "biz_labels", "RATE TAG": "biz_labels", "PRICE TAG": "biz_labels",
    "EMI / INTEREST CALC": "biz_emi", "EMI CALC": "biz_emi",
    "EMI CALCULATOR": "biz_emi", "EMI / VYAAJ CALC": "biz_emi",
    "INTEREST CALC": "biz_emi", "INTEREST CALCULATOR": "biz_emi",
    "EMI CARD": "biz_emi", "LOAN EMI": "biz_emi",
    "MEDIA STUDIO": "mediastudio",
    "MP3 STATUS STUDIO": "mediastudio",
    "VIP PREMIUM": "premium",
    "ALL TOOLS (FREE)": "alltools",      # v61
    "ALL TOOLS": "alltools",
    "SAARE TOOLS": "alltools",
    "REFER & EARN": "refer",
    "MY ACCOUNT": "account",
    "HELP / TUTORIAL": "tutorial",
    "SUPPORT / MADAD": "support",
    "MADAD / TUTORIAL": "tutorial",
    "MADAD": "tutorial",
    "ADMIN PANEL": "admin",
    "OWNER MODE": "owner",
}

# =====================================================================
#  v58 — NAYA TOOL PROMPT SYSTEM (aapka diya hua format)
# ---------------------------------------------------------------------
#  Har tool ka prompt ab teen hisson me:
#     1. Header  — 🔐 𝐈𝐌𝐄𝐈 𝐕𝟐 & 𝐆𝐒𝐌𝐀𝐑𝐄𝐍𝐀 𝐒𝐏𝐄𝐂𝐒 𝐄𝐍𝐆𝐈𝐍𝐄
#     2. Ask     — ✨ 15-digit IMEI Number ya Device Model Name / Code bhejein:
#     3. Examples— 📝 Examples: • 862407054987700 (IMEI Number) ...
#
#  ⚠️ v58 ki khaas baat: tool start par ab NA "⚡ Credits: ♾️ Unlimited (VIP)"
#     dikhta hai na "Tap /cancel any time to stop." — user ka order.
#
#  Ek jagah se poora bot badalta hai: neeche PROMPT_DATA me sirf
#  head/ask/examples badlo, saare 22 tools ka prompt apne aap badal jayega.
# =====================================================================
PROMPT_DATA = {
    # ---------------------------------------------------------- DOWNLOADERS
    "terabox": {
        "head": "⚡ TERABOX / CLOUD ENGINE",
        "ask": "Terabox / Drive / MediaFire ka link bhejein:",
        "ex": [("https://terabox.com/s/xxxxx", "Terabox"),
               ("https://drive.google.com/file/d/xxxxx", "Google Drive"),
               ("https://www.mediafire.com/file/xxxxx", "MediaFire")],
    },
    "insta_dl": {
        "head": "📥 VIDEO DOWNLOADER · 10+ APPS",
        "ask": "Kisi bhi app ka video link bhejein:",
        "ex": [("https://www.youtube.com/watch?v=xxxxx", "YouTube"),
               ("https://www.instagram.com/reel/xxxxx", "Instagram"),
               ("https://www.facebook.com/watch?v=xxxxx", "Facebook"),
               ("https://vt.tiktok.com/xxxxx", "TikTok"),
               ("https://x.com/i/status/xxxxx", "Twitter / X")],
    },
    # ---------------------------------------------------------- PHOTO TOOLS
    "pp_stamp": {
        "head": "📸 EXAM PASSPORT PHOTO STUDIO",
        "ask": "Apni front-facing photo bhejein (chehra saaf + roshni achi ho):",
        "ex": [("Studio photo", "white background best"),
               ("Mobile selfie", "simple background")],
    },
    "print_sheet": {
        "head": "🖨️ 8-IN-1 PRINT SHEET MAKER",
        "ask": "Ek photo bhejein — 8-in-1 print sheet ban jayegi:",
        "ex": [("Passport size photo", "print ke liye"),
               ("Selfie / family photo", "ek hi photo 8 baar")],
    },
    "doc_compress": {
        "head": "📄 DOCUMENT CAMERA → PDF",
        "ask": "Document ki photo bhejein (PDF ban jayegi):",
        "ex": [("10th / 12th marksheet", ""),
               ("Aadhaar / PAN / Voter ID", ""),
               ("Bank passbook page", "")],
    },
    # ------------------------------------------------------------- FINANCE
    "bankpdf": {
        "head": "🏦 BANK STATEMENT PDF → EXCEL",
        "ask": "Bank statement ka PDF bhejein (photo nahi, asli PDF):",
        "ex": [("SBI / HDFC / PNB / ICICI", "statement PDF"),
               ("Password wala PDF", "pehle password bhejein")],
    },
    "ifsc": {
        "head": "🏦 IFSC BANK BRANCH ENGINE",
        "ask": "IFSC code bhejein (11 characters):",
        "ex": [("SBIN0000001", "State Bank of India"),
               ("HDFC0001234", "HDFC Bank"),
               ("PUNB0123456", "Punjab National Bank")],
    },
    # ------------------------------------------------------------- GAMING
    "bgmi": {
        "head": "🎮 BGMI PLAYER CARD ENGINE",
        "ask": "BGMI UID bhejein (8-10 digit):",
        "ex": [("1067824210", "Player UID"),
               ("5123456789", "Player UID")],
    },
    "ffuid": {
        "head": "🔥 FREE FIRE UID ENGINE",
        "ask": "Free Fire UID bhejein (8-10 digit):",
        "ex": [("7860944073", "UID"),
               ("7860944073 BR", "UID + Region"),
               ("7860944073 IND", "UID + Region")],
    },
    # -------------------------------------------------------- PHONE / OSINT
    "imei": {
        "head": "🔐 IMEI V2 & GSMARENA SPECS ENGINE",
        "ask": "15-digit IMEI Number ya direct Device Model Name / Code bhejein:",
        "ex": [("862407054987700", "IMEI Number"),
               ("M2101K6P", "Model Code"),
               ("Redmi Note 10 Pro", "Device Name")],
    },
    "numinfo": {
        "head": "📱 NUMBER INFO V2 ENGINE",
        "ask": "10 Digit Number bhejein (API lagane par naam/pata/region bhi aata hai):",
        "ex": [("9876543210", "10 digit number"),
               ("7305190526", "koi bhi mobile number"),
               ("+91 98765 43210", "country code ke saath bhi chalta hai")],
    },
    "appfind": {
        "head": "📦 APP FINDER · PLAY · APPSTORE · F-DROID",
        "ask": "App ka naam ya package code bhejein:",
        "ex": [("whatsapp", "App ka naam"),
               ("com.whatsapp", "Package code"),
               ("free fire", "App ka naam")],
    },
    # ------------------------------------------------------------ LOCATION
    "pin": {
        "head": "📮 PINCODE / AREA INFO ENGINE",
        "ask": "Pincode ya area ka naam bhejein:",
        "ex": [("800001", "Patna ka pincode"),
               ("Rajendra Nagar", "Area ka naam"),
               ("Sitamarhi", "District ka naam")],
    },
    # ---------------------------------------------------------------- LINKS
    "qr": {
        "head": "📷 QR CODE MAKER",
        "ask": "Text ya link bhejein (HD QR ban jayega):",
        "ex": [(f"https://t.me/{OWNER_USERNAME}", "Telegram link"),
               ("My WiFi password is 12345", "Simple text")],
    },
    "short": {
        "head": "🔗 URL SHORTENER · 6 ENGINES",
        "ask": "Lamba link bhejein:",
        "ex": [("https://example.com/very/long/path?x=1", "Lamba link"),
               ("https://amazon.in/dp/xxxxx?ref=xyz", "Shopping link")],
    },
    "linkcheck": {
        "head": "🔍 LINK CHECK · 6-LAYER SCAN",
        "ask": "Link bhejein — safe hai ya fraud, poora check karunga:",
        "ex": [("http://sbi-kyc-verify.xyz", "Suspicious link"),
               ("https://google.com", "Normal link")],
    },
    "qr_wifi": {
        "head": "📶 WIFI SHARE QR",
        "ask": "WiFi ka naam (SSID) bhejein:",
        "ex": [("JioFiber_Home", "WiFi ka naam"),
               ("MyHome_5G", "WiFi ka naam")],
    },
    "qr_vcard": {
        "head": "👤 CONTACT CARD QR",
        "ask": "Apna naam bhejein (contact card bane ga):",
        "ex": [("Himanshu Kumar", "Naam"),
               ("Rahul Sah", "Naam")],
    },
    # ---------------------------------------------------------- MENU TOOLS
    "tempmail": {
        "head": "📧 TEMP MAIL ENGINE",
        "ask": "Naya email banane ke liye <code>NEW</code> bhejein:",
        "ex": [("NEW", "naya email ID + inbox")],
    },
    "kagaz": {
        "head": "📜 KAGAZ SUITE · GOVT PAPERS",
        "ask": "Neeche se apna document chunein:",
        "ex": [("Kirayanama", "rent agreement"),
               ("Affidavit / Notice 138", "legal papers"),
               ("GST / PAN check", "tax papers")],
    },
    # ------------------------------------------------- v60.4 BUSINESS STUDIO
    "biz_invoice": {
        "head": "🧾 INVOICE / GST BILL MAKER",
        "ask": "Ek line me likhein: <code>dukaan ka naam | grahak | items</code>",
        "ex": [("Sharma Electronics | Ramesh | LED 4x120, Wire 1x450",
                "2 item ka bill"),
               ("Kumar Store | Suresh | Sugar 2x48",
                "1 item, GST ke bina")],
    },
    "biz_resume": {
        "head": "💼 RESUME / CV MAKER",
        "ask": "Ek line me: <code>naam | pad/role | phone | education | skills</code>",
        "ex": [("Himanshu Kumar | Software Engineer | 9876543210 | B.Tech CSE | Python, SQL",
                "engineer ka CV"),
               ("Anjali Kumari | Accounts Assistant | 9812345678 | B.Com | Tally, Excel",
                "accounts ka CV")],
    },
    "biz_biodata": {
        "head": "💍 MARRIAGE BIO-DATA MAKER",
        "ask": "Ek line me: <code>naam | dob | education | job | father | phone</code>",
        "ex": [("Himanshu Kumar | 15-08-1998 | B.Tech | Engineer | Ram Kumar | 9876543210",
                "ladke ka biodata"),
               ("Anjali Kumari | 12-03-2000 | B.A | Teacher | Suresh Singh | 9812345678",
                "ladki ka biodata")],
    },
    "biz_certificate": {
        "head": "🎓 CERTIFICATE MAKER",
        "ask": "Ek line me: <code>sanstha | student ka naam | kaam/class | date</code>",
        "ex": [("Saraswati Coaching | Anjali Kumari | Class 10 Maths | 06-10-2026",
                "achievement certificate"),
               ("ABC Institute | Rahul Raj | Computer Course | 06-10-2026",
                "course certificate")],
    },
    "biz_idcard": {
        "head": "🪪 ID CARD MAKER (A4 par 10 card)",
        "ask": "Ek line me: <code>sanstha | naam | father | class | roll | phone</code>",
        "ex": [("Saraswati School | Anjali Kumari | Ramesh Kumar | X-A | 1042 | 9876543210",
                "student ID"),
               ("Patna Coaching | Rahul Raj | Suresh Raj | XI-B | 2051 | 9812345678",
                "coaching ID")],
    },
    "biz_vcard": {
        "head": "📇 VISITING CARD MAKER (A4 par 10 card)",
        "ask": "Ek line me: <code>naam | dukaan | phone | address</code>",
        "ex": [("Himanshu Kumar | Kumar Electronics | 9876543210 | Main Road Bihta",
                "dukaan ka card"),
               ("Dr. S. Sharma | Sharma Clinic | 9812345678 | Kankarbagh Patna",
                "clinic ka card")],
    },
    "biz_letter": {
        "head": "📄 APPLICATION / LETTER MAKER",
        "ask": "Ek line me: <code>kaam | naam | sanstha | karan</code>",
        "ex": [("leave | Himanshu Kumar | Saraswati School | sister wedding",
                "chhutti ka application"),
               ("character | Anjali Kumari | Patna College | passport ke liye",
                "character certificate")],
    },
    "biz_upi": {
        "head": "💳 UPI PAYMENT POSTER MAKER",
        "ask": "Ek line me: <code>UPI ID | dukaan ka naam | phone</code>",
        "ex": [("kumar@upi | Kumar Electronics | 9876543210", "dukaan ka QR board"),
               ("sharma@ybl | Sharma General Store | 9812345678", "kirana dukaan")],
    },
    "biz_labels": {
        "head": "🏷️ PRICE LABEL / RATE TAG SHEET",
        "ask": "Ek line me: <code>dukaan | item:rate:MRP, item2:rate</code>",
        "ex": [("Kumar Store | Sugar:48:55, Rice:95:110, Oil:165:180",
                "3 rate tag ek line me"),
               ("Sharma Kirana | Tea:130:150, Dal:140:155", "2 tag")],
    },
    "biz_salary": {
        "head": "💰 SALARY SLIP MAKER",
        "ask": "Ek line me: <code>company | naam | post | month | salary | advance</code>",
        "ex": [("Sharma Kirana | Ramesh Kumar | Salesman | September 2026 | 18000",
                "poora pay slip — PF, ESI, net pay ke saath"),
               ("Jai Maa Traders | Sunita Devi | Accountant | Oct 2026 | 25000 | 2000",
                "advance bhi kat jayega"),
               ("ABC Coaching | Rahul Sir | Teacher | " + "%B %Y" + " | 30000",
                "month khali chhodo to aaj ka mahina")],
    },
    "biz_menucard": {
        "head": "🍽️ MENU / RATE CARD",
        "ask": "Ek line me: <code>naam | tagline | item:rate, item:rate</code>",
        "ex": [("Hotel Shivam | Shudh Desi Khana | Chai:10, Samosa:15, Veg Thali:80",
                "dhaba ka menu card"),
               ("Sharma Kirana | Best Rate in Town | Sugar:48, Rice:95, Atta:32",
                "dukaan ka rate list"),
               ("Menu | | Idli:30, Dosa:50, Uttapam:60, Filter Coffee:20",
                "tagline khali chhodo to sirf list")],
    },
    "biz_emi": {
        "head": "🧮 EMI / LOAN CALCULATOR + CARD",
        "ask": "Ek line me: <code>loan amount | byaaj % | mahine</code>",
        "ex": [("250000 | 11.5 | 36", "2.5 lakh, 36 mahine"),
               ("500000 | 9.5 | 60", "5 lakh home loan"),
               ("50000 | 18 | 12", "50 hazaar personal loan")],
    },
    "mediastudio": {
        "head": "⚡ MEDIA STUDIO",
        "ask": "Neeche se option chunein:",
        "ex": [("YouTube → MP3", ""),
               ("Status video · Ringtone · Karaoke", ""),
               ("8D sound · Bass boost · Voice change", "")],
    },
}


def _render_tool_prompt(key: str) -> str:
    """PROMPT_DATA → ready-to-send HTML prompt (naya v58 format)."""
    d = PROMPT_DATA.get(key)
    if not d:
        return ""
    L = [f"{d['head'].split(' ')[0]} <b>{to_bold(d['head'].split(' ', 1)[1])}</b>"
         if " " in d["head"] else f"<b>{to_bold(d['head'])}</b>"]
    L.append("")
    L.append(f"✨ {d['ask']}")
    ex = d.get("ex") or []
    if ex:
        L.append("")
        L.append("📝 <b>Examples:</b>")
        for val, label in ex:
            L.append(f"• <code>{hesc(str(val))}</code>" + (f" ({label})" if label else ""))
    return "\n".join(L)


# backward-compat: purana naam `PROMPTS` wahi rehta hai (tests/tutorial isko use karte hain)
PROMPTS = {k: _render_tool_prompt(k) for k in PROMPT_DATA}

TUTORIAL_TEXT = (
    f"❓ <b>{to_bold('HELP — HAR TOOL EK LINE ME')}</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "📥 <b>Download:</b>\n"
    "• 📥 VIDEO DOWNLOADER → Insta/YT/FB/X ka link bhejo → video mil jayega\n"
    "   (YouTube par <b>quality chuno</b>: 1080p/720p/480p/360p — jo chaho wahi milegi)\n"
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
    "• 📱 NUMBER INFO → number bhejo → operator + circle\n"
    "• 🏦 IFSC → code bhejo → bank + branch + MICR\n"
    "• 📮 PINCODE → pincode ya area bhejo → district + post office\n"
    "• 🏦 IFSC INFO → IFSC code bhejo → bank + branch + MICR mil jaata hai\n"
    "• 🎮 BGMI UID / 🔥 FF UID → dost ka game UID bhejo → naam, level, rank, stats (public)\n"
    "• 📧 TEMP MAIL → NEW bhejo → ek-baar ka email + inbox (OTP/signup ke liye)\n"
    "\n"
    "⚡ <b>Media Studio:</b> YouTube→MP3, status video, ringtone, karaoke, 8D, bass, voice change, trim,\n"
    "   🗣️ text→Hindi voice (asli desi awaaz me MP3)\n"
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
    """Tool ke neeche 🎬 video tutorial + 📩 Support button (v59.7).

    v59.7: ab HAR tool me ye keyboard aata hai — user kabhi bhi ek tap me
    owner se baat kar sakta hai (tap → @Supermannn_x ki chat khulti hai).
    """
    rows = []
    if has_video(action):
        rows.append([InlineKeyboardButton("🎬 Tutorial Video (30 sec) — HIMANSHU",
                                          callback_data=f"toolvid:{action}")])
    rows.append([InlineKeyboardButton(f"📩 Support — seedha message karo {SUPPORT_USERNAME}",
                                      url=SUPPORT_URL)])
    return InlineKeyboardMarkup(rows)


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
    "trim/compress, 🗣️ text→Hindi voice. <b>No watermark.</b>\n"
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
    "sheohar": (26.5189, 85.2950), "madhubani": (26.3530, 86.0722),
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
        [InlineKeyboardButton("🗣️ Text → Hindi Voice (MP3)", callback_data="media_tts")],
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


# ============================================================
#  v58 — PERMANENT GUARD: ye do lines KABHI, KAHIN, KISI BHI
#  HAALAT ME tool start par nahi dikh sakti (user ka strict order).
#
#  Code me se lines hata di gayi hain, PAR ab ek aakhri suraksha bhi hai:
#  har prompt yahan se guzarta hai, aur agar kisi wajah se (purana cache,
#  future edit, kisi module se aaya text) ye lines aa jayein to yahin
#  delete ho jaati hain. Test bhi hai jo isko guard karta hai.
# ============================================================
_BANNED_PROMPT_PATTERNS = (
    re.compile(r"^.*Credits:\s*♾️\s*Unlimited.*$", re.M),
    re.compile(r"^.*Credits:\s*Unlimited.*$", re.M),
    re.compile(r"^.*Tap\s*/cancel any time.*$", re.M),
    re.compile(r"^.*/cancel any time to stop.*$", re.M),
)


def _sanitize_prompt(text: str) -> str:
    """Banned lines (credits-unlimited + /cancel hint) nikaal do + extra blank hatао."""
    if not text:
        return ""
    out = text
    for rx in _BANNED_PROMPT_PATTERNS:
        out = rx.sub("", out)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def tool_prompt(action: str) -> str:
    """Tool ka prompt — v58 format (header + ✨ ask + 📝 Examples).

    Har prompt `_sanitize_prompt()` se guzarta hai — isliye credits/cancel
    wali lines **permanently** gayab hain (structural guarantee).
    """
    body = PROMPTS.get(action)
    if not body:
        # purane ASK_LINES wale sub-modes (agar koi bacha ho) — safe fallback
        body = strip_tutorial_lines(ASK_LINES.get(action, "")).strip()
    return _sanitize_prompt(body)


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
    + ("\n\n🎉 <b>SAARE TOOLS 100% FREE HAIN</b> — na VIP, na credits, na limit ✅"
       if ALL_FREE else "\n\n👇 <b>Neeche menu se koi bhi tool dabao</b>")
)


# ---------------- COMMANDS ----------------
# v52 speed: welcome photo ka file_id cache — pehli baar upload hota hai, baad me
# Telegram CDN se turant serve hota hai (har /start par dobara upload NAHI = fast).
_WELCOME_FID = None


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

    global _WELCOME_FID
    # v52 speed: cache file_id use karo (CDN serve = instant, no re-upload)
    if _WELCOME_FID:
        try:
            await update.message.reply_photo(photo=_WELCOME_FID, caption=WELCOME_TEXT,
                                             reply_markup=kb_for(user.id), parse_mode=HTML)
            return
        except Exception:
            _WELCOME_FID = None
    banner_path = os.path.join(os.path.dirname(__file__), "welcome_banner.jpg")
    if os.path.exists(banner_path):
        try:
            with open(banner_path, "rb") as f:
                _m = await update.message.reply_photo(photo=f, caption=WELCOME_TEXT,
                                                      reply_markup=kb_for(user.id), parse_mode=HTML)
            try:
                _WELCOME_FID = _m.photo.file_id   # agli baar CDN se turant
            except Exception:
                pass
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
    if ALL_FREE:
        _st_f = "👑 OWNER/ADMIN" if is_admin(uid_) else "✅ ALL TOOLS FREE"
        await update.message.reply_text(
            f"👤 <b>{to_bold('MERI ACCOUNT')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Naam:</b> {hesc(u.get('name', 'User'))}\n"
            f"• <b>User ID:</b> <code>{u.get('user_id')}</code>\n"
            f"• <b>Status:</b> {_st_f}\n"
            f"• <b>Referrals:</b> {u.get('referrals', 0)}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎉 <b>Poore bot ke saare tools aapke liye khule hain.</b>\n"
            "❌ Na koi VIP, na credits, na limit.\n"
            "👉 Neeche menu se seedha tool dabao.",
            reply_markup=free_mode_kb(), parse_mode=HTML)
        return
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
            "• Premium: Video Downloader · Number Info · IMEI · Channel Cloner · "
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
            "📥 Video Downloader · 📱 Number Info · 📲 IMEI · 🔄 Cloner · 🏦 Bank PDF → Excel · "
            "📜 Document Suite · ⚡ Media Studio are now unlocked. 🚀",
            parse_mode=HTML)
    except Exception:
        pass


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
        await st.edit_text(f"❌ <b>IMEI API test failed:</b> {safe_html_err(str(res.get('error'))[:200])}\n\n"
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
        await st.edit_text(card + f"\n• Live test: ❌ {safe_html_err(str(res.get('error'))[:150])}", parse_mode=HTML)


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
    # v61: free mode me koi VIP bechna hi nahi hai — seedha free card
    if ALL_FREE and not is_admin(update.effective_user.id):
        await update.message.reply_text(FREE_MODE_TEXT, reply_markup=free_mode_kb(),
                                        parse_mode=HTML)
        return
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

# =====================================================================
# v59.3: 🛡️ HARDCORE CRASH-PROOF CORE
# ---------------------------------------------------------------
# 1) _startup_selfcheck()  — boot par saaf report: version, commit, modules,
#                            kaunsi API lagi hai (key KABHI print nahi hoti)
# 2) _supervise()          — process-level self-heal: main() crash ho to
#                            khud restart (Render ko 502 nahi milta)
# 3) loop exception guard  — background task crash bhi process ko nahi giraata
# =====================================================================
_GIT_COMMIT = (os.environ.get("RENDER_GIT_COMMIT") or "")[:7] or "local"
_CRASH_STATE = {"count": 0, "last": "", "why": ""}   # self-heal counter (health me dikhta hai)


def _startup_selfcheck() -> bool:
    """Boot par checks chalao aur saaf report print karo. Kabhi crash nahi karta."""
    ok = True
    print("=" * 64)
    print(f"🩺 SELF-CHECK | {BOT_VERSION}")
    print(f"   commit: {_GIT_COMMIT} | python: {sys.version.split()[0]}")
    # --- modules ---
    import importlib as _il
    _bad = []
    for _mn in ("api_hub", "channel_cloner", "desi_tools", "general_tools", "gaming_tools",
                "imei_lookup", "media_downloader", "numinfo_provider", "osint_hub",
                "osint_tools", "payguard", "render_health", "sarkari_hub", "temp_mail",
                "toolkit_extras", "tutorial_hub", "vip_payment"):
        try:
            _il.import_module(f"modules.{_mn}")
        except Exception as _e:                                  # noqa: BLE001
            _bad.append(f"{_mn}: {type(_e).__name__}")
    if _bad:
        ok = False
        print(f"   ❌ modules FAIL ({len(_bad)}): {', '.join(_bad[:4])}")
    else:
        print("   ✅ modules: sab OK")
    # --- optional deps (jo bina bhi bot chalta hai) ---
    _miss = []
    for _dep in ("telegram", "requests", "PIL", "qrcode", "phonenumbers",
                 "yt_dlp", "bs4", "pypdf", "img2pdf", "edge_tts"):
        try:
            _il.import_module(_dep)
        except Exception:                                        # noqa: BLE001
            _miss.append(_dep)
    print(f"   ✅ optional deps: {'sab OK' if not _miss else 'missing ' + ', '.join(_miss)}")
    # --- config (sirf set/not-set — key kabhi print nahi) ---
    print(f"   🔑 BOT_TOKEN: {'set' if BOT_TOKEN else 'MISSING'}"
          f" | 👑 ADMIN_ID: {'set' if os.environ.get('ADMIN_ID') else 'not set'}")
    try:
        print(f"   📱 Number Info API: {'🟢 set' if numprov.is_configured() else '⚪ not set'}"
              f" | 🏦 hub key: {'🟢 set' if os.environ.get('HUB_API_KEY') else '⚪ not set'}")
    except Exception:                                            # noqa: BLE001
        pass
    print(f"   🛡️  self-heal: crashes={_CRASH_STATE['count']}")
    _db = os.environ.get("DB_PATH") or os.environ.get("DATA_DIR") or "default (auto)"
    print(f"   🗄️  storage: {_db}"
          f" | 🌐 mode: {'WEBHOOK' if webhook_url_from_env() else 'POLLING'}"
          f" | 🔄 keepalive: {'ON' if os.environ.get('KEEPALIVE_ENABLED', '1') != '0' else 'OFF'}")
    print("=" * 64)
    return ok


def _supervise() -> None:
    """main() ko chalao; crash ho to KHUD restart karo (Render ko 502 na mile)."""
    _tries, _fast = 0, []
    while True:
        _tries += 1
        try:
            main()
            print("ℹ️ main() normal band hua (koi crash nahi) — process exit")
            return
        except KeyboardInterrupt:
            print("⛔ Manually band kiya gaya (KeyboardInterrupt) — exit")
            return
        except SystemExit:
            raise
        except BaseException as e:                               # noqa: BLE001
            _now = time.time()
            _fast = [t for t in _fast if _now - t < 600] + [_now]
            _CRASH_STATE["count"] += 1
            _CRASH_STATE["last"] = time.strftime("%d-%m-%Y %H:%M")
            _CRASH_STATE["why"] = f"{type(e).__name__}: {str(e)[:80]}"
            log.error("💥 CRASH #%s (%s: %s)", _tries, type(e).__name__, str(e)[:220])
            try:
                import traceback
                traceback.print_exc()
            except Exception:                                    # noqa: BLE001
                pass
            _wait = 60 if len(_fast) >= 8 else 5
            log.warning("🔁 SELF-HEAL: %ss baad khud restart kar raha hoon (try #%s)",
                        _wait, _tries + 1)
            time.sleep(_wait)




# ---------------- v59: /version — deploy hua hai ya nahi, turant pata karo ----------------
async def cmd_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/version — bot ka version + naye features ka status (sabke liye khula)."""
    _n_tools = len(PROMPT_DATA)
    _two_lines_gone = ("Credits: ♾️ Unlimited" not in PROMPTS.get("terabox", "")
                       and "cancel" not in PROMPTS.get("terabox", "").lower())
    _prompt_ok = "📝 <b>Examples:</b>" in PROMPTS.get("imei", "")
    _numpanel = bool(numprov.is_configured())
    _mode = "WEBHOOK (Conflict-free)" if webhook_url_from_env() else "POLLING"
    await update.message.reply_text(
        f"⚡ <b>{hesc(BOT_VERSION)}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔖 <b>Code commit:</b> <code>{hesc(_GIT_COMMIT or 'unknown')}</code>\n"
        f"🌐 <b>Mode:</b> {_mode} | ⏱️ <b>chal raha:</b> {_uptime_str()}\n"
        f"🩺 <b>Crashes:</b> {_CRASH_STATE['count']} (self-heal ON)\n"
        f"🌐 <b>Webhook check:</b> {hesc(_WEBHOOK_DIAG['decision'])}\n"
        f"🤖 <b>Live check:</b> {hesc(_last_update_line())}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎨 <b>Naya prompt system:</b> {'✅ CHALU' if _prompt_ok else '❌ purana'}\n"
        f"  • {_n_tools} tools me header + ✨ ask + 📝 Examples\n"
        f"🚫 <b>Credits/cancel line:</b> {'✅ poori tarah gayi' if _two_lines_gone else '❌ abhi hai'}\n"
        "📸 <b>IMEI photo:</b> ✅ chalu (device naam/code bhi chalta hai)\n"
        f"📱 <b>Number Info API:</b> {'🟢 lagi hui' if _numpanel else '⚪ set nahi (/numapi)'}\n"
        "🏦 <b>UPI tool:</b> 🗑️ hata diya gaya (poori code gayi)\n"
        "⚡ <b>YouTube quality buttons:</b> ✅ instant (cache + background warm)\n"
        "🧹 <b>Purane lecture/note lines:</b> ✅ saare tools se gayi\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Naya version live hai ya nahi — kaise pakdo:</b>\n"
        "1. Upar wala 🔖 commit Render ke latest commit jaisa hai = ✅ naya code LIVE\n"
        "2. Alag hai = deploy abhi chal raha hai, 2 minute baad /version dobara bhejo\n"
        "3. Browser me <b>/health</b> kholo: "
        "https://utility-duniya-bot.onrender.com/health\n"
        "<i>(v59.9: /version aur /health me ab commit + mode dono dikhte hain — "
        "pehle purana label chipka rehta tha, isliye confusion hoti thi.)</i>",
        parse_mode=HTML)


# ---------------- v59.5: /numdemo — Number Info ka SAMPLE card (kaisa dikhega) ----------------
async def cmd_numdemo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/numdemo — Number Info ka card SAMPLE (dummy) data ke saath dikhao.

    Isme koi asli vyakti ka data nahi hota — sirf dikhane ke liye hai ki
    aapki API lagne par card kaisa aayega. Koi credit nahi katta.
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Sirf admin ke liye.", parse_mode=HTML)
        return
    _res = {"international": "+91 90000 00001", "national": "9000000001",
            "type": "Mobile", "country": "India", "country_code": "+91",
            "timezones": "Asia/Kolkata"}
    try:
        _demo = numprov.demo_result("9000000001")
    except Exception:                                        # noqa: BLE001
        _demo = {}
    _owner = _demo.get("owner") or {
        "name": "RAHUL KUMAR (SAMPLE)", "father": "MOHAN LAL KUMAR (SAMPLE)",
        "alt": "9000000001", "region": "BIHAR JIO", "govt_id": "000000000000 (SAMPLE)",
        "address": "S/O MOHAN LAL KUMAR, Ward 02, SAMPLE NAGAR, Bihar, 000000 (SAMPLE)",
    }
    card = numinfo_card(_res, _owner, {}, "Jio", "Bihar", "📱 Mobile", "",
                        "🧪 <b>SAMPLE PREVIEW</b> — ye dummy data hai (asli data aapki API se aata hai)",
                        240)
    await update.message.reply_text(
        "🧪 <b>NUMBER INFO — SAMPLE PREVIEW</b>\n"
        "Ye bilkul wahi layout hai jo aapki API lagne par aayega.\n"
        "Isme koi asli vyakti ka data <b>nahi</b> hai — sab nakli values hain.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        + card
        + "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Asli data ke liye:</b> Render → Environment me\n"
        "<code>NUMINFO_PROVIDER_URL</code> + <code>NUMINFO_PROVIDER_KEY</code> "
        "daalo → <code>/numapi</code> se check karo.",
        parse_mode=HTML)


# ---------------- v59.7: /support — seedha owner se baat karo (clickable) ----------------
SUPPORT_TEXT = (
    "💬 <b>SUPPORT / MADAD</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Owner: {SUPPORT_LINK}\n\n"
        "Neeche wala button dabao → seedha owner ki chat khul jaayegi → "
        "<b>Start</b> dabao aur apni baat likho.\n\n"
        "<b>Kab message karo:</b>\n"
        "• Koi tool kaam na kare / error aaye\n"
        "• VIP payment ka sawaal\n"
        "• Koi naya tool chahiye\n"
        "• Kuch bhi samajh na aaye\n\n"
    "<i>Screenshot bhejo to sabse jaldi solve hota hai.</i>"
)


def support_card() -> tuple:
    """Support card ka (text, keyboard) — command aur menu button dono use karte hain."""
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📩 Message karo {SUPPORT_USERNAME}", url=SUPPORT_URL)],
        [InlineKeyboardButton("👑 VIP lo", callback_data="open_vip_menu"),
         InlineKeyboardButton("❓ Help", callback_data="back_home")],
    ])
    return (SUPPORT_TEXT, kb)


async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/support — owner se seedha baat karne ka card (ek tap me chat khul jaati hai)."""
    _txt, kb = support_card()
    await update.message.reply_text(_txt,
        parse_mode=HTML, reply_markup=kb)


# ---------------- v59.6: /numtest — kisi bhi API ka sample response → card preview ----------------
async def cmd_numtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/numtest <JSON> — apni API ke docs wala SAMPLE response paste karo → card dikhega.

    Isse aap bina API lagaye dekh sakte ho ki aapki API ka jawab bot ke card me
    kaise badlega. Koi API call nahi hoti, koi credit nahi katta, kuch save nahi hota.
    """
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Sirf admin ke liye.", parse_mode=HTML)
        return
    _raw = (update.message.text or "")
    for _pfx in ("/numtest", "/numcheck", "/numinfotest"):
        if _raw.lower().startswith(_pfx):
            _raw = _raw[len(_pfx):]
            break
    _raw = _raw.strip().strip("`")
    if not _raw:
        await update.message.reply_text(
            "🧪 <b>/numtest — MAPPING PREVIEW</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Apni API ke docs wala <b>sample JSON response</b> is command ke saath\n"
            "paste karo → main dikha dunga ki bot ka card <b>kaisa banega</b>.\n\n"
            "<b>Jaise:</b>\n"
            "<code>/numtest {\"carrier\": \"Jio\", \"location\": \"Bihar\", "
            "\"name\": \"Rahul Kumar\"}</code>\n\n"
            "ℹ️ Koi API call nahi hoti, koi credit nahi katta, kuch save nahi hota.",
            parse_mode=HTML)
        return
    try:
        _data = json.loads(_raw)
    except Exception:                                        # noqa: BLE001
        await update.message.reply_text(
            "❌ Ye valid JSON nahi hai. Docs se sample response <b>jaisa hai waisa</b> "
            "paste karo (curly brackets <code>{ }</code> ke saath).\n"
            "📌 Tip: JSON ek line me paste karna sabse aasan hai.", parse_mode=HTML)
        return
    if not isinstance(_data, dict):
        await update.message.reply_text("❌ JSON ka top part <code>{ }</code> hona chahiye.",
                                        parse_mode=HTML)
        return
    _parsed = await asyncio.to_thread(numprov.parse_payload, _data, 0)
    if not _parsed.get("ok"):
        await update.message.reply_text(
            "⚠️ <b>Is response se card nahi bana.</b>\n"
            f"📄 <b>Wajah:</b> {safe_html_err(str(_parsed.get('error') or 'unknown')[:200])}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot in naam se fields dhoondhta hai:\n"
            "• naam → <code>name</code> / <code>ownerName</code> / <code>subscriberName</code>\n"
            "• pita → <code>father</code> / <code>fatherName</code> / <code>guardian</code>\n"
            "• operator → <code>carrier</code> / <code>operator</code> / <code>network</code>\n"
            "• circle → <code>location</code> / <code>circle</code> / <code>region</code>\n\n"
            "Agar aapki API inme se alag naam bhejti hai — mujhe ye response bhejo, "
            "main 1 minute me map kar dunga.",
            parse_mode=HTML)
        return
    _owner = _parsed.get("owner") or {}
    _digits = re.sub(r"\D", "", str(_parsed.get("number") or "")) or "9000000001"
    _res = {"international": "+91 " + (_digits[-10:] if len(_digits) >= 10 else _digits),
            "national": _digits[-10:], "type": _parsed.get("type") or "Mobile",
            "country": _parsed.get("country") or "India", "country_code": "+91"}
    _card = numinfo_card(_res, _owner, _parsed.get("extra") or {},
                         str(_parsed.get("operator") or ""), str(_parsed.get("circle") or ""),
                         str(_parsed.get("type") or ""), "",
                         "🧪 <b>MAPPING PREVIEW</b> — aapke paste kiye response se "
                         "(koi API call nahi hui)", 0)
    await update.message.reply_text(
        "🧪 <b>MAPPING PREVIEW</b> — aapki API ka jawab aise card me badlega:\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        + _card
        + "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 Jo fields aapke JSON me nahi thi, unki line card me nahi aayi.\n"
        "💡 Asli API lagane ke liye: <code>/numapi</code> dekho.",
        parse_mode=HTML)


# ---------------- v57: /numapi — Number Info provider status (key kabhi nahi print hoti) ----------------
async def cmd_numapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/numapi — admin: Number Info ki apni API lagi hai ya nahi (live test bhi)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Sirf admin ke liye.", parse_mode=HTML)
        return
    card = numprov.status_card()
    args = [a.strip() for a in (context.args or []) if a.strip()]
    if not numprov.is_configured():
        await update.message.reply_text(card, parse_mode=HTML)
        return
    if not args:
        await update.message.reply_text(
            card + "\n\n🧪 <b>Live test chalao:</b> <code>/numapi 9876543210</code>",
            parse_mode=HTML)
        return
    test_no = args[0]
    st = await update.message.reply_text(
        f"🔎 Aapki API se <code>{hesc(test_no)}</code> test kar raha hoon…", parse_mode=HTML)
    t0 = time.perf_counter()
    res = await asyncio.to_thread(numprov.lookup, test_no)
    ms = int((time.perf_counter() - t0) * 1000)
    if res.get("ok"):
        await st.edit_text(
            "✅ <b>API CHAL RAHI HAI!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏢 <b>Operator:</b> {hesc(str(res.get('operator') or '—'))}\n"
            f"📍 <b>Circle:</b> {hesc(str(res.get('circle') or '—'))}\n"
            f"🔎 <b>Line Type:</b> {hesc(str(res.get('type') or '—'))}\n"
            f"🌍 <b>Country:</b> {hesc(str(res.get('country') or '—'))}\n"
            f"⚡ <b>Latency:</b> {ms}ms\n"
            f"🗄️ <b>Cache:</b> {'Haan (6 ghante)' if res.get('cached') else 'Nahi (fresh)'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📱 Ab Number Info tool aapki API se <b>live data</b> dega. 🔥",
            parse_mode=HTML)
        return
    await st.edit_text(
        "❌ <b>API test fail</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 <b>Wajah:</b> {safe_html_err(str(res.get('error') or 'unknown')[:220])}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Ye 4 cheezein check karo:</b>\n"
        "1️⃣ URL poori hai? (https:// se shuru + <code>/api</code> end)\n"
        "2️⃣ Key sahi hai? (copy-paste me space na ho)\n"
        "3️⃣ Auth type sahi? — numverify jaisa API: <code>NUMINFO_PROVIDER_AUTH=query</code>\n"
        "4️⃣ Param ka naam? — numverify: <code>NUMINFO_PROVIDER_PARAM=number</code>\n\n"
        "📖 Poori guide: <code>NUMBER-INFO-API-SETUP.md</code>\n"
        "ℹ️ <i>Tab tak Number Info purane sources se chal raha hai — band nahi hai.</i>",
        parse_mode=HTML)



# ======================================================================
#  v60 — 🛡️ PREMIUM VAULT COMMANDS (admin/owner)
#  Ye wahi 4 command hain jo aapko bharosa dilayenge ki premium safe hai.
# ======================================================================
async def cmd_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/vault — premium vault ki poori health report."""
    uid = update.effective_user.id
    if not is_admin(uid):
        # normal user ko bas itna — andar ki baat nahi
        await safe_reply(update.effective_message,
                         "🛡️ Aapka data 24x7 safe rakha jata hai.\n"
                         "Koi bhi cheez share karne ki zaroorat nahi hai.", parse_mode=HTML)
        return
    try:
        card = vault.status_card()
    except Exception as e:                                       # noqa: BLE001
        card = f"⚠️ Vault report banane me dikkat: {safe_html_err(str(e)[:120])}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Abhi backup banao", callback_data="vault_backup")],
        [InlineKeyboardButton("♻️ Backup se restore karo", callback_data="vault_restore")],
        [InlineKeyboardButton("👑 VIP users list (file)", callback_data="vault_vips")],
        [InlineKeyboardButton("🏠 Home", callback_data="back_home")],
    ])
    await safe_reply(update.effective_message, card, reply_markup=kb, parse_mode=HTML)


async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/backup — turant backup (admin)."""
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    msg = await safe_reply(update.effective_message,
                           "📦 <b>Backup ban raha hai…</b>\n<i>10-30 second lag sakte hain.</i>",
                           parse_mode=HTML)
    try:
        res = await vault.backup_now(reason=f"manual:{uid}", also_telegram=False)
    except Exception as e:                                       # noqa: BLE001
        res = {"ok": False, "why": f"{type(e).__name__}: {str(e)[:120]}"}
    ok = res.get("ok")
    txt = (f"{'✅' if ok else '⚠️'} <b>BACKUP {'OK' if ok else 'NAHI HUA'}</b>\n"
           "━━━━━━━━━━━━━━━━━━━━━━\n"
           f"📦 Size: {res.get('bytes', 0)/1024:.1f} KB\n"
           f"🐙 GitHub: <code>{hesc(str(res.get('github') or '-'))[:80]}</code>\n"
           f"👑 VIP count: {res.get('premium', {}).get('total_premium', '?')}\n")
    if not ok:
        txt += f"\n📄 <b>Wajah:</b> {safe_html_err(str(res.get('why') or 'unknown')[:200])}"
    if msg and getattr(msg, "msg", None):
        try:
            await safe_answer_cb(update.callback_query, "Backup ho gaya" if ok else "Backup fail")
            from modules.core.safesend import safe_edit
            await safe_edit(msg.msg, txt, parse_mode=HTML)
            return
        except Exception:                                        # noqa: BLE001
            pass
    await safe_reply(update.effective_message, txt, parse_mode=HTML)


async def cmd_restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/restore — sabse accha backup merge karo (premium-floor protected)."""
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    msg = await safe_reply(update.effective_message,
                           "♻️ <b>Backup check kar raha hoon…</b>\n"
                           "<i>VIP users ki ginti se pehle aur baad me milaan hoga.</i>",
                           parse_mode=HTML)
    try:
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, functools_partial(vault.restore_now, "manual"))
    except Exception as e:                                       # noqa: BLE001
        res = {"ok": False, "why": f"{type(e).__name__}: {str(e)[:120]}"}
    ok = res.get("ok")
    b = res.get("premium_before", {})
    a = res.get("premium_after", {})
    txt = [f"{'✅' if ok else '⚠️'} <b>RESTORE {'OK' if ok else 'NAHI HUA'}</b>",
           "━━━━━━━━━━━━━━━━━━━━━━",
           f"👑 <b>VIP pehle:</b> {b.get('total_premium', '?')}",
           f"👑 <b>VIP ab:</b> {a.get('total_premium', '?')}"]
    if res.get("source"):
        txt.append(f"📥 <b>Source:</b> <code>{hesc(str(res['source'])[:70])}</code>")
    if res.get("safety_copy"):
        txt.append(f"🛟 <b>Safety copy:</b> <code>{hesc(str(res['safety_copy'])[:60])}</code>")
    if res.get("blocked"):
        txt.append(f"\n🛑 <b>{len(res['blocked'])} backup BLOCK kiya gaya</b> "
                   "(VIP ghatt raha tha — aapka data bacha liya)")
    if not ok and res.get("why"):
        txt.append(f"\n📄 <b>Wajah:</b> {safe_html_err(str(res['why'])[:200])}")
    rep = res.get("report", {}).get("users", {})
    if rep:
        txt.append(f"\n📊 Users: {rep.get('total', '?')} (naye {rep.get('only_remote', 0)}, "
                   f"premium upgraded {rep.get('premium_upgraded', 0)})")
    await safe_reply(update.effective_message, "\n".join(txt), parse_mode=HTML)


def functools_partial(fn, *a, **kw):
    """functools.partial ka chhota wrapper (executor me chalane ke liye)."""
    import functools as _f
    return _f.partial(fn, *a, **kw)


async def cmd_vips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/vips — saare premium users ki CSV report (file)."""
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    try:
        rows = vault.premium_list_rows()
    except Exception as e:                                       # noqa: BLE001
        await safe_reply(update.effective_message,
                         f"⚠️ List nahi bani: {safe_html_err(str(e)[:120])}", parse_mode=HTML)
        return
    if not rows:
        await safe_reply(update.effective_message,
                         "👑 Abhi koi VIP user nahi hai.", parse_mode=HTML)
        return
    active = sum(1 for r in rows if not r["expired"])
    lines = ["user_id,name,username,premium_until,status,credits,referrals,joined"]
    for r in rows:
        nm = str(r["name"]).replace(",", " ").replace("\n", " ")[:40]
        un = str(r["username"]).replace(",", " ")[:30]
        lines.append(f"{r['user_id']},{nm},{un},{r['premium_until']},"
                     f"{'EXPIRED' if r['expired'] else 'ACTIVE'},{r['credits']},"
                     f"{r['referrals']},{r['joined']}")
    data = ("\ufeff" + "\n".join(lines)).encode("utf-8")
    bio = io.BytesIO(data)
    bio.name = f"vip_users_{datetime.now().strftime('%d%m%Y_%H%M')}.csv"
    await safe_send_document(
        update.effective_message.get_bot(), update.effective_chat.id, bio,
        filename=bio.name,
        caption=(f"👑 <b>PREMIUM USERS REPORT</b>\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━\n"
                 f"✅ Active: <b>{active}</b>\n"
                 f"🕓 Expired (record): {len(rows) - active}\n"
                 f"📊 Total: <b>{len(rows)}</b>\n\n"
                 f"💡 <i>Ye file kisi bhi backup se restore karne layak hai. "
                 f"Ise sambhal kar rakhein.</i>"),
        parse_mode="HTML",
        fallback_text=(f"👑 PREMIUM USERS — {active} active VIP"
                       f" + {len(rows) - active} expired (record)\n\n"
                       + "\n".join(f"• {r['user_id']} — {r['premium_until']}"
                                   + (" (expired)" if r["expired"] else "")
                                   for r in rows[:40])))


async def cmd_fixvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/fixvip <user_id> — ledger se kisi ka premium WAPAS lagao.

    Naam se hi pata chal jata hai: agar kabhi kisi ka VIP ghumm gaya ho, to
    ye command uska poora itihaas dekhegi aur sabse zyada wala premium wapas
    laga degi. Ye bot ki "kabhi premium na kho" wali guarantee ka manual
    control hai.
    """
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    args = context.args or []
    if not args or not str(args[0]).strip().lstrip("-").isdigit():
        await safe_reply(update.effective_message,
                         "📘 <b>Use:</b> <code>/fixvip 123456789</code>\n"
                         "Ledger ke record se us user ka premium wapas lag jayega.",
                         parse_mode="HTML")
        return
    target = int(str(args[0]).strip())
    try:
        before = ""
        row = get_user_row(target) or {}
        before = str(row.get("premium_until") or "")
        after = restore_premium_from_ledger(target)
    except Exception as e:                                       # noqa: BLE001
        await safe_reply(update.effective_message,
                         f"⚠️ Dikkat: {safe_html_err(str(e)[:120])}", parse_mode="HTML")
        return
    hist = ledger_for(target, 5)
    lines = [f"👑 <b>PREMIUM LEDGER REPAIR</b>",
             "━━━━━━━━━━━━━━━━━━━━━━",
             f"👤 <b>User:</b> <code>{target}</code>",
             f"📥 <b>Pehle:</b> {hesc(premium_rank_txt(before))}",
             f"📤 <b>Ab:</b> {hesc(premium_rank_txt(after))}"]
    if hist:
        lines.append("\n🧾 <b>Itihaas (aakhri 5):</b>")
        for h in hist:
            lines.append(f"• {hesc(str(h.get('created_at', ''))[:16])} — {hesc(str(h.get('action')))}"
                         f" ({h.get('days')} din) → {hesc(str(h.get('new_until') or '-'))}")
    if not after and not before:
        lines.append("\n⚪ Is user ka koi premium record nahi mila.")
    await safe_reply(update.effective_message, "\n".join(lines), parse_mode="HTML")


def premium_rank_txt(v: str) -> str:
    if not v:
        return "Free (koi VIP nahi)"
    try:
        if str(v).lower() == "lifetime":
            return "👑 LIFETIME VIP"
        d = parse_dt(v)
        return d.strftime("%d-%m-%Y") if d else str(v)
    except Exception:
        return str(v)


async def cmd_ledger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ledger — premium ka poora itihaas (kaun, kab, kitne din)."""
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    rows = ledger_all(30)
    st = premium_ledger_stats()
    lines = ["📒 <b>PREMIUM LEDGER (permanent record)</b>",
             "━━━━━━━━━━━━━━━━━━━━━━",
             f"✅ Grants: {st['grant']}  |  🚫 Revokes: {st['revoke']}  |  "
             f"👥 Users: {st['unique_users']}", ""]
    if not rows:
        lines.append("Abhi koi entry nahi hai.")
    for r in rows:
        lines.append(f"• <code>{r['user_id']}</code> {hesc(str(r['action']))} "
                     f"{r['days']}d → {hesc(str(r['new_until'] or '-')[:19])} "
                     f"<i>{hesc(str(r['created_at'])[:16])}</i>")
    lines += ["", "💡 <i>Ye record users table se alag hai — isliye premium ka "
              "saboot kabhi nahi khota. Kisi ka VIP ghumm jaye to: "
              "<code>/fixvip &lt;user_id&gt;</code></i>"]
    await safe_reply(update.effective_message, "\n".join(lines), parse_mode="HTML")



# ======================================================================
#  v60.4 — 💼 BUSINESS STUDIO (10 earning tools)
# ----------------------------------------------------------------------
# Ye block menu, submenu, aur text-parser sab handle karta hai. Har tool ek
# line ka input leta hai ("|" se alag) aur A4 print-ready file banata hai.
# Har function KABHI crash nahi karta — error ho to saaf Hinglish message.
# ======================================================================
BIZ_MENU = {
    "biz_invoice":     ("🧾", "Invoice / GST Bill",      "dukaan ka bill · estimate · quotation"),
    "biz_resume":      ("💼", "Resume / CV",             "job ke liye professional CV"),
    "biz_biodata":     ("💍", "Marriage Bio-data",       "shaadi ka biodata · Hindi me bhi"),
    "biz_certificate": ("🎓", "Certificate",             "achievement · course · bonafide"),
    "biz_idcard":      ("🪪", "ID Card (10 per page)",   "school / coaching / office"),
    "biz_vcard":       ("📇", "Visiting Card (10)",      "dukaan / clinic ka card"),
    "biz_letter":      ("📄", "Application / Letter",    "leave · NOC · character"),
    "biz_upi":         ("💳", "UPI Scan & Pay Poster",   "dukaan ka payment board"),
    "biz_labels":      ("🏷️", "Price Label Sheet",      "dukaan ke rate tag"),
    "biz_salary":      ("💰", "Salary Slip",            "staff ka monthly pay slip"),
    "biz_menucard":    ("🍽️", "Menu / Rate Card",       "dhaba · hotel · dukaan ka rate list"),
    "biz_emi":         ("🧮", "EMI / Loan Card",         "poora hisaab + schedule"),
}

BIZ_MENU_TEXT = (
    "💼 <b>𝐁𝐔𝐒𝐈𝐍𝐄𝐒𝐒 𝐒𝐓𝐔𝐃𝐈𝐎</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Dukaan, school, coaching, job aur loan — <b>12 kaam ki cheezein</b>\n"
    "sirf ek line likh kar banao. Sab <b>print-ready A4 PDF</b> me.\n\n"
    "👇 Neeche se tool chuno:"
)


def biz_menu_kb():
    rows, pair = [], []
    for key, (icon, name, _sub) in BIZ_MENU.items():
        pair.append(InlineKeyboardButton(f"{icon} {name}", callback_data=f"biz:{key}"))
        if len(pair) == 2:
            rows.append(pair); pair = []
    if pair:
        rows.append(pair)
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)


def _biz_split(line: str) -> list:
    """Ek line ko '|' ya ',' par todta hai (smart)."""
    t = str(line or "").strip()
    if "|" in t:
        return [x.strip() for x in t.split("|")]
    return [t]


def _biz_num(v, default=0.0):
    try:
        return float(str(v).replace(",", "").replace("₹", "").replace("Rs", "").strip() or default)
    except Exception:                                            # noqa: BLE001
        return float(default)


def _biz_items(txt: str) -> list:
    """'LED 4x120, Wire 1x450' -> [{name,qty,rate}]"""
    out = []
    for chunk in re.split(r"[,\n;]+", str(txt or "")):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.search(r"(\d+(?:\.\d+)?)\s*[xX*×]\s*(\d+(?:\.\d+)?)", chunk)
        if m:
            name = chunk[:m.start()].strip(" -:") or "Item"
            out.append({"name": name, "qty": _biz_num(m.group(1), 1),
                        "rate": _biz_num(m.group(2))})
        else:
            m2 = re.search(r"(\d+(?:\.\d+)?)\s*(?:rs|₹)?\s*$", chunk, re.I)
            if m2:
                out.append({"name": chunk[:m2.start()].strip(" -:") or "Item",
                            "qty": 1, "rate": _biz_num(m2.group(1))})
            else:
                out.append({"name": chunk, "qty": 1, "rate": 0})
    return out


def _biz_kind(kind: str) -> str:
    return {"invoice": "biz_invoice", "bill": "biz_invoice",
            "resume": "biz_resume", "cv": "biz_resume",
            "biodata": "biz_biodata", "bio": "biz_biodata",
            "certificate": "biz_certificate", "cert": "biz_certificate",
            "idcard": "biz_idcard", "id": "biz_idcard",
            "vcard": "biz_vcard", "visiting": "biz_vcard",
            "letter": "biz_letter", "application": "biz_letter",
            "upi": "biz_upi", "qr": "biz_upi",
            "labels": "biz_labels", "label": "biz_labels", "price": "biz_labels",
            "salary": "biz_salary", "payslip": "biz_salary", "slip": "biz_salary",
            "menucard": "biz_menucard", "menu": "biz_menucard",
            "ratecard": "biz_menucard", "ratelist": "biz_menucard",
            "emi": "biz_emi", "loan": "biz_emi"}.get(str(kind or "").lower().strip(), "")


def biz_parse(key: str, line: str, owner_name: str = "") -> dict:
    """Ek line ke input ko us tool ke dict me badlo. Kabhi crash nahi."""
    p = _biz_split(line)
    d: dict = {}
    try:
        if key == "biz_invoice":
            items = _biz_items(p[2]) if len(p) > 2 else _biz_items(p[-1])
            d = {"shop": p[0] if p else "", "buyer": p[1] if len(p) > 1 else "",
                 "items": items or [{"name": "Item", "qty": 1, "rate": 0}],
                 "doc_type": "TAX INVOICE", "number": f"INV-{datetime.now().strftime('%d%m%H%M')}",
                 "date": datetime.now().strftime("%d-%m-%Y"), "gstin": "",
                 "upi": "", "discount": 0, "advance": 0}
        elif key == "biz_resume":
            d = {"name": p[0] if p else owner_name,
                 "role": p[1] if len(p) > 1 else "", "phone": p[2] if len(p) > 2 else "",
                 "education": [{"course": p[3], "institute": "", "year": "", "percent": ""}]
                 if len(p) > 3 and p[3] else [],
                 "skills": p[4] if len(p) > 4 else "",
                 "email": p[5] if len(p) > 5 else "",
                 "objective": f"To work in a growth oriented organisation where I can "
                              f"use my skills as {p[1] if len(p) > 1 else 'a professional'}."}
        elif key == "biz_biodata":
            d = {"name": p[0] if p else owner_name, "dob": p[1] if len(p) > 1 else "",
                 "education": p[2] if len(p) > 2 else "", "job": p[3] if len(p) > 3 else "",
                 "father": p[4] if len(p) > 4 else "", "phone": p[5] if len(p) > 5 else ""}
        elif key == "biz_certificate":
            d = {"org": p[0] if p else "", "name": p[1] if len(p) > 1 else owner_name,
                 "course": p[2] if len(p) > 2 else "",
                 "date": p[3] if len(p) > 3 else datetime.now().strftime("%d-%m-%Y"),
                 "title": "CERTIFICATE OF EXCELLENCE"}
        elif key == "biz_idcard":
            d = {"org": p[0] if p else "",
                 "tagline": "STUDENT IDENTITY CARD", "session": datetime.now().strftime("%Y-%y"),
                 "students": [{"name": p[1] if len(p) > 1 else owner_name,
                               "father": p[2] if len(p) > 2 else "",
                               "class": p[3] if len(p) > 3 else "",
                               "roll": p[4] if len(p) > 4 else "",
                               "phone": p[5] if len(p) > 5 else ""}],
                 "footer": (p[0] if p else "")}
        elif key == "biz_vcard":
            d = {"owner": p[0] if p else owner_name, "shop": p[1] if len(p) > 1 else "",
                 "phone": p[2] if len(p) > 2 else "", "address": p[3] if len(p) > 3 else "",
                 "style": "band"}
        elif key == "biz_letter":
            d = {"type": (p[0] if p else "leave").lower().strip(),
                 "name": p[1] if len(p) > 1 else owner_name,
                 "org": p[2] if len(p) > 2 else "", "reason": p[3] if len(p) > 3 else ""}
        elif key == "biz_upi":
            d = {"upi": p[0] if p else "", "shop": p[1] if len(p) > 1 else "",
                 "upi_name": p[1] if len(p) > 1 else "", "phone": p[2] if len(p) > 2 else "",
                 "note": p[3] if len(p) > 3 else "Payment ka screenshot bhej dein"}
        elif key == "biz_labels":
            labels = []
            for chunk in re.split(r"[,\n;]+", p[1] if len(p) > 1 else ""):
                bits = [x.strip() for x in chunk.split(":") if x.strip()]
                if len(bits) >= 2:
                    labels.append({"name": bits[0], "price": _biz_num(bits[1]),
                                   "mrp": _biz_num(bits[2]) if len(bits) > 2 else 0})
            d = {"shop": p[0] if p else "", "labels": labels,
                 "footer": "Rate " + datetime.now().strftime("%d-%m-%Y") + " se laagu"}
        elif key == "biz_salary":
            # COMPANY | NAAM | POST | MONTH | SALARY | ADVANCE
            parts = [x.strip() for x in p if x.strip()]
            nums = [x for x in parts if _biz_num(x) > 0]
            texts = [x for x in parts if _biz_num(x) <= 0]
            d = {"company": texts[0] if texts else (owner_name or "COMPANY"),
                 "name": texts[1] if len(texts) > 1 else (owner_name or "Employee"),
                 "post": texts[2] if len(texts) > 2 else "Staff",
                 "month": texts[3] if len(texts) > 3 else datetime.now().strftime("%B %Y"),
                 "gross": _biz_num(nums[0]) if nums else 0,
                 "advance": _biz_num(nums[1]) if len(nums) > 1 else 0}
        elif key == "biz_menucard":
            # DHABA NAAM | TAGLINE | Chai:10, Samosa:15 | CONTACT
            parts = [x.strip() for x in p if x.strip()]
            items_src, rest = "", []
            for x in parts:
                if ":" in x and re.search(r":\s*\d", x) and not items_src:
                    items_src = x
                else:
                    rest.append(x)
            items = []
            for chunk in re.split(r"[,\n;]+", items_src):
                bits = [b.strip() for b in chunk.split(":") if b.strip()]
                if len(bits) >= 2:
                    items.append({"name": bits[0], "price": _biz_num(bits[1]),
                                  "tag": bits[2] if len(bits) > 2 else ""})
            _contact = ""
            for x in rest[2:]:
                if re.search(r"\d{6,}", x):
                    _contact = x
            d = {"name": rest[0] if rest else (owner_name or "MENU"),
                 "tagline": rest[1] if len(rest) > 1 else "",
                 "items": items, "contact": _contact,
                 "footer": "Rates " + datetime.now().strftime("%d-%m-%Y") + " se laagu"}
        elif key == "biz_emi":
            d = {"bank": "EMI / LOAN SUMMARY", "borrower": owner_name,
                 "loan_amount": _biz_num(p[0]) if p else 0,
                 "rate": _biz_num(p[1]) if len(p) > 1 else 10,
                 "months": int(_biz_num(p[2], 12)) if len(p) > 2 else 12}
    except Exception:                                            # noqa: BLE001
        pass
    return d


def biz_build(key: str, d: dict) -> dict:
    """Sahi function chalao — safe."""
    fn = {"biz_invoice": biz_invoice, "biz_resume": biz_resume,
          "biz_biodata": biz_biodata, "biz_certificate": biz_certificate,
          "biz_idcard": biz_idcard, "biz_vcard": biz_vcard,
          "biz_letter": biz_letter, "biz_upi": biz_upi_qr,
          "biz_labels": biz_labels, "biz_emi": biz_emi_card,
          "biz_salary": biz_salary, "biz_menucard": biz_menucard}.get(key)
    if fn is None:
        return {"ok": False, "error": "tool nahi mila"}
    return fn(d)


async def biz_send_result(msg, key: str, res: dict, uid: int, used: bool = True) -> None:
    """Result bhejo — image + PDF dono, aur credit ka message."""
    if not res or not res.get("ok"):
        why = (res or {}).get("error") or "kuch gadbad ho gayi"
        await safe_reply(
            msg,
            f"⚠️ <b>File nahi ban payi</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 {safe_html_err(str(why)[:200])}\n\n"
            f"💡 <b>Format yaad rakhein:</b> ek line me <code>|</code> se alag likhein.\n"
            f"Example dekhne ke liye tool ka naam dobara dabayein.",
            parse_mode="HTML")
        return
    _icon, name, _sub = BIZ_MENU.get(key, ("📄", "File", ""))
    bio = io.BytesIO(res["png"])
    bio.name = f"{key.replace('biz_', '')}_{datetime.now().strftime('%d%m_%H%M')}.png"
    cap = (f"✅ <b>{hesc(name)}</b> ready hai!\n"
           f"━━━━━━━━━━━━━━━━━━━━━━\n"
           f"🖨️ <i>A4 @ 200 DPI — seedha print karein</i>\n")
    if res.get("count"):
        cap += f"📦 Total: <b>{res['count']}</b>\n"
    if res.get("emi"):
        cap += (f"💰 EMI: <b>Rs. {biz_money(res['emi'])}</b>/month\n"
                f"📊 Total: Rs. {biz_money(res['total'])} "
                f"(byaaj Rs. {biz_money(res['interest'])})\n")
    if res.get("amount"):
        cap += f"💰 Total: <b>Rs. {biz_money(res['amount'])}</b>\n"
    if res.get("notice"):
        cap += f"📌 {hesc(str(res['notice'])[:120])}\n"
    if used:
        cap += spend_credit_msg(uid, key)
    sent = await safe_send_photo(msg.get_bot(), msg.chat_id, bio, caption=cap,
                                parse_mode="HTML")
    # PDF bhi bhejo (print aur WhatsApp share ke liye)
    try:
        pages = res.get("pages") or [res.get("png")]
        pdf = biz_to_pdf(pages)
        if pdf:
            from io import BytesIO as _B
            pio = _B(pdf)
            pio.name = f"{key.replace('biz_', '')}_{datetime.now().strftime('%d%m_%H%M')}.pdf"
            await safe_send_document(msg.get_bot(), msg.chat_id, pio,
                                     caption="📄 <b>PDF</b> — print / WhatsApp ke liye",
                                     parse_mode="HTML", filename=pio.name)
    except Exception as _e:                                      # noqa: BLE001
        log.debug("biz pdf skip: %s", str(_e)[:90])


def biz_money(v):
    try:
        from modules.business_tools import money as _m
        return _m(v)
    except Exception:                                            # noqa: BLE001
        return str(v)


# --------- helpers block khatam ---------

def arm_all_handlers(app) -> int:
    """🛡️ v60: HAR handler ko crash-shield me lapet do (ek hi jagah se).

    Ye "code crash ho jaata hai" ka sabse bada ilaaj hai. Isse pehle har tool
    ka code apne aap ko bachata tha — lekin koi bhi chhoti bug (kisi field ka
    missing hona, kisi API ka ajeeb jawab, kisi photo ka kharab format) us
    tool ke handler ko maar deti thi aur user ko "Chhota sa ghatna ho gaya"
    dikhta tha (credit bhi kat chuka hota tha).

    Ab: PTB ke saare handlers ka `callback` guard me lapet diya jata hai.
    Iska matlab:
      • koi bhi tool bug -> sirf wo ek tool ke liye message fail hota hai
      • bot kabhi nahi girta
      • user ko saaf message milta hai ("dobara try karo")
      • admin ko /sys par "kitne sambhale gaye" dikhta hai

    Returns: kitne handlers lapete gaye.
    """
    n = 0
    try:
        for group, handlers in (app.handlers or {}).items():
            for h in handlers:
                cb = getattr(h, "callback", None)
                if cb is None or getattr(cb, "_ud_guarded", False):
                    continue
                try:
                    wrapped = guarded(f"handler:{type(h).__name__}")(cb)
                    wrapped._ud_guarded = True
                    h.callback = wrapped
                    n += 1
                except Exception:                                # noqa: BLE001
                    continue
    except Exception as e:                                       # noqa: BLE001
        log.warning("arm_all_handlers me dikkat (bot normal chalega): %s", str(e)[:130])
    return n


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
        # v53.0: per-tool telemetry — ab koi tool chup-chaap fail nahi ho sakta.
        # DEAD upstream (jaise BGMI ke stats servers) sabse upar flag hota hai,
        # aur saaf likha aata hai ki us tool par credit nahi katna chahiye.
        + _telemetry_block()
        + _vault_admin_block()
        + "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Ye stats live hain — /admin dobara dabao to refresh ho jayenge.</i>"
    )


def _vault_admin_block() -> str:
    """v60: /sys me data-safety + crash-shield + memory ka block.

    Kabhi crash nahi karta — kuch bhi fail ho to khaali string.
    """
    try:
        from modules.core.guard import guard_stats
        from modules.core.vault import premium_floor_report
        g = guard_stats()
        floor = premium_floor_report(vault_db_path())
        st = vault.stats
        lb = vault.last_backup or {}
        lr = vault.last_restore or {}
        lines = [
            "🛡️ <b>PREMIUM VAULT (v60):</b>",
            f"   👑 VIP users: <b>{floor['total_premium']}</b> "
            f"(lifetime {floor['lifetime']} · active {floor['active']})",
            f"   💾 DB: <code>{hesc(vault_db_path())[:60]}</code>",
            f"   🔐 Backup: GitHub {'🟢' if vault.gh_ready() else '⚪'} · "
            f"Telegram {'🟢' if vault.telegram_ready() else '⚪'} · "
            f"har {vault.interval_minutes()} min",
            f"   📦 {st.get('backups', 0)} ✅ backups · {st.get('restores', 0)} restore · "
            f"{st.get('failures', 0)} fail",
        ]
        if lb.get("at"):
            lines.append(f"   🕒 Aakhri backup: {hesc(str(lb.get('at'))[:19])}")
        if lr.get("at"):
            lines.append(f"   ♻️ Aakhri restore: {hesc(str(lr.get('at'))[:19])} "
                         f"({'OK' if lr.get('ok') else 'fail'})")
        lines += [
            "",
            "🛡️ <b>CRASH SHIELD (v60):</b>",
            f"   🪖 Sambhale gaye: <b>{g.get('handled', 0)}</b> "
            f"(handler {g.get('handler', 0)} · task {g.get('task', 0)} · "
            f"thread {g.get('thread', 0)})",
            f"   💥 Fatal crashes: {g.get('fatal', 0)}  |  "
            f"🧠 RAM: {g.get('mem_mb', 0):.0f} MB (peak {g.get('mem_peak_mb', 0):.0f} MB)",
            f"   🧹 GC runs: {g.get('gc_runs', 0)} · "
            f"⏱️ loop lag: {g.get('heart_lag', 0)}s · beats {g.get('beats', 0)}",
        ]
        if g.get("last_why"):
            lines.append(f"   🔎 Aakhri: {hesc(str(g['last_why'])[:110])}")
        lines.append("   💡 Commands: /vault · /backup · /restore · /vips · /ledger · /fixvip")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)
    except Exception:                                            # noqa: BLE001
        return ""


def _telemetry_block(max_rows: int = 8) -> str:
    """v53.0: per-tool health + upstream status (admin /sys card ke liye).

    Fail-safe: telemetry me kuch bhi gadbad ho to system card phir bhi banta hai.
    """
    try:
        snap = tel_snapshot()
    except Exception:  # noqa: BLE001
        return ""
    if not snap.get("calls") and not snap.get("upstreams"):
        return ("📡 <b>Tool telemetry:</b> abhi koi tool call record nahi hua\n"
                "   <i>(bot start ke baad se koi tool use nahi hua)</i>\n")
    L = []
    L.append(f"📡 <b>Tool telemetry (v53.0):</b>")
    L.append(f"   🔢 calls: <b>{snap['calls']:,}</b>   "
             f"✅ {snap['ok']:,}   ❌ {snap['hard_fail']:,}   "
             f"⚠️ service-side {snap['soft_fail']:,}")
    L.append(f"   📈 success rate: <b>{snap['success_rate']}%</b>   "
             f"💳 credits charged: <b>{snap['credits_charged']:,}</b>")
    ups = snap.get("upstreams") or {}
    if ups:
        dead = snap.get("dead_upstreams") or []
        L.append("   🔌 <b>Upstream APIs:</b>")
        for name, u in sorted(ups.items(), key=lambda kv: (kv[1]["alive"] is not False, kv[0])):
            mark = "🟢" if u["alive"] is True else ("🔴" if u["alive"] is False else "⚪")
            age = f" · {u['age_sec']}s pehle" if u.get("age_sec") is not None else ""
            L.append(f"      {mark} {name}: {u['ok']} ok / {u['fail']} fail{age}")
            if u["alive"] is False and u["last_error"]:
                L.append(f"         ↳ <code>{str(u['last_error'])[:64]}</code>")
        if dead:
            L.append(f"   ⚠️ <b>BAND services:</b> {', '.join(dead)}")
            L.append("      → inke tools par credit NAHI katna chahiye")
    try:
        worst = tel_worst_tools(max_rows)
    except Exception:  # noqa: BLE001
        worst = []
    worst = [w for w in worst if w.get("calls")]
    if worst:
        L.append("   🩺 <b>Sabse zyada fail:</b>")
        for r in worst:
            L.append(f"      • {r['name']}: {r['fail']}/{r['calls']} fail "
                     f"({r['success_rate']}% ok, avg {r['avg_ms']}ms, p95 {r['p95_ms']}ms)")
    return "\n".join(L) + "\n"


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
# Brand logo (center me lagta hai). Ek baar load, phir process-lifetime cache.
_QR_LOGO_BYTES = None       # bytes | None — bot.py typing import nahi karta
_QR_LOGO_TRIED = False
# QR ~7089 bytes max (version 40, numeric). Text limit se upar DataOverflowError.
QR_MAX_CHARS = 2000


def _qr_logo_bytes():
    """Bot ka profile pic center logo ke liye (na mile/corrupt ho to None)."""
    global _QR_LOGO_BYTES, _QR_LOGO_TRIED
    if _QR_LOGO_TRIED:
        return _QR_LOGO_BYTES
    _QR_LOGO_TRIED = True
    try:
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_profile_pic.jpg")
        if os.path.exists(fp) and os.path.getsize(fp) < 4 * 1024 * 1024:
            with open(fp, "rb") as f:
                _QR_LOGO_BYTES = f.read(400_000) or None
    except Exception as e:                                    # noqa: BLE001
        log.debug("qr logo load fail: %s", str(e)[:80])
        _QR_LOGO_BYTES = None
    return _QR_LOGO_BYTES


def _hex_ok(v: str) -> bool:
    """Sirf valid 6-digit hex color accept karo (injection/bad-pixel se bachao)."""
    return bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", str(v or "").strip()))


def _qr_luminance(hexcolor: str) -> float:
    """Relative luminance 0(black)..1(white) — contrast check ke liye."""
    try:
        r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    except Exception:                                         # noqa: BLE001
        return 0.0
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0



# ============================================================
#  v57: PREMIUM CARD HELPERS — saare report cards ka EK hi look
#  Pehle har tool apna alag style banata tha (koi boxed, koi plain).
#  Ab ek jagah se: boxed header + source/time footer + brand line.
# ============================================================
PCARD_TOP = "┌──────────────────────────────"
PCARD_MID = "──────────────────────────────"
PCARD_BOT = "└──────────────────────────────"




# ============================================================
#  v57: SAFE HTML ERROR (engine errors me formatting bachi rahe)
#  Hamare engines kuch errors me <b>/<code> bhejte hain (jaise BGMI/FF ka
#  "UID kahan milega" help). Pehle bot.py usko hesc() kar deta tha, isliye
#  user ko literally "&lt;b&gt;Profile&lt;/b&gt;" dikhta tha — bedhadak bug.
#
#  Ab: sirf ye tags pass hote hain, baaki SAB escape hota hai.
#  Isse engine ki formatting dikhti hai AUR user ke daale hue text se
#  HTML-injection / Telegram "can't parse entities" crash nahi hota.
# ============================================================
_SAFE_TAG_RE = re.compile(
    r"</?(?:b|strong|i|em|u|ins|s|strike|del|code|pre|tg-spoiler)>"
    # <a> sirf POORA pair pass hota hai (https link + saada text + </a>).
    # Akela </a> ya <a href="javascript:..."> escape ho jaata hai — warna
    # Telegram "can't parse entities" de kar poora message reject karta hai.
    r"|<a\s+href=\"https?://[^\"<>]{1,200}\">[^<>]{0,300}</a>",
    re.IGNORECASE)
# sirf ye tags Telegram HTML me allowed hain (whitelist)
_SAFE_TAGS = frozenset(
    {"b", "strong", "i", "em", "u", "ins", "s", "strike", "del", "code",
     "pre", "tg-spoiler", "a"})
_TAG_SCAN_RE = re.compile(r"</?([a-zA-Z-]+)[^>]*>")


def _tags_balanced(html: str) -> bool:
    """Har allowed tag ka opening/closing match hai? (Telegram strict hai.)"""
    stack: list = []
    for m in _TAG_SCAN_RE.finditer(html):
        raw, tag = m.group(0), m.group(1).lower()
        if tag not in _SAFE_TAGS:
            return False
        if raw.startswith("</"):
            if not stack or stack[-1] != tag:
                return False
            stack.pop()
        elif not raw.endswith("/>"):
            stack.append(tag)
    return not stack


def safe_html_err(text) -> str:
    """Engine ka error → user-safe HTML (whitelist tags, baaki escaped).

    Do suraksha:
      1. Sirf whitelist tags + poora <a href="https://...">...</a> pair pass.
      2. Aakhir me tag-balance check — agar kuch bhi gadbad hai to poora
         escape kar dete hain (Telegram message reject na kare).
    """
    t = str(text or "")
    if not t:
        return ""
    out = []
    pos = 0
    for m in _SAFE_TAG_RE.finditer(t):
        out.append(hesc(t[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(hesc(t[pos:]))
    res = "".join(out)
    return res if _tags_balanced(res) else hesc(t)


def pcard_title(icon: str, name: str) -> str:
    """Premium boxed header:  ┌─── | 🏦 ɪꜰꜱᴄ ʀᴇᴘᴏʀᴛ | └───"""
    return f"{PCARD_TOP}\n│ {icon} <b>{to_bold(name)}</b>\n{PCARD_BOT}"


def pcard_foot(*, ms: float = 0, source: str = "", note: str = "",
               brand: bool = True) -> str:
    """Premium footer — source + response time + brand (sab optional)."""
    L = [PCARD_MID]
    if source:
        L.append(f"📡 <b>Source:</b> {source}")
    if ms:
        _m = float(ms)
        L.append(f"⚡ <b>Response:</b> {int(_m)}ms" if _m < 1000 else
                 f"⚡ <b>Response:</b> {_m / 1000:.1f}s")
    if note:
        L.append(note)
    if brand:
        L.append(BRAND_LINK)   # v59.7: clickable — tap = owner se baat
    return "\n".join(L)


def pcard_sep() -> str:
    return PCARD_MID


def numinfo_card(res: dict, owner: dict | None = None, extra: dict | None = None,
                 operator: str = "", circle: str = "", ltype: str = "",
                 ported_line: str = "", src_line: str = "", ms: float = 0) -> str:
    """📱 NUMBER INFO ka **ek hi** card layout (v59.2).

    Yehi layout handler aur `/numdemo` (sample preview) dono use karte hain —
    isliye demo bilkul asli jaisa dikhta hai. Owner ki lines sirf tab aati hain
    jab `owner` dict me wo field ho (yani jab AAPKI API wo bheje).
    """
    res = res or {}
    owner = owner or {}
    extra = extra or {}
    _obits = []
    if owner.get("name"):
        _obits.append(f"👤 <b>Name:</b> {hesc(str(owner['name']))}")
    if owner.get("father"):
        _obits.append(f"👨 <b>Father:</b> {hesc(str(owner['father']))}")
    if owner.get("alt"):
        _obits.append(f"📱 <b>Phones/Alt:</b> {hesc(str(owner['alt']))}")
    if owner.get("region"):
        _obits.append(f"🌐 <b>Region:</b> {hesc(str(owner['region']))}")
    if owner.get("govt_id"):
        _obits.append(f"🆔 <b>Govt ID:</b> {hesc(str(owner['govt_id']))}")
    _addr = str(owner.get("address") or "").strip()
    if _addr:
        # aapka format: label ke baad ek khali line, phir "   └ <pata>"
        _obits.append("🏠 <b>Address(es):</b>\n")
        for _ap in [x.strip() for x in _addr.split("|") if x.strip()][:4]:
            _obits.append(f"   └ {hesc(_ap[:300])}")
    for _k in ("addresses", "address_list"):
        for _a2 in (extra.get(_k) or [])[:4]:
            if _a2 and hesc(str(_a2))[:300] not in _addr:
                _obits.append(f"   └ {hesc(str(_a2)[:300])}")

    _card = list(_obits)
    if _obits:
        _card.append(pcard_sep())
    _card.append(f"📞 <b>Number:</b> <code>{hesc(str(res.get('international') or res.get('number') or ''))}</code>")
    if operator or circle:
        _card.append(f"🏢 <b>Operator:</b> {hesc(operator)}"
                     + (f"  •  📍 {hesc(circle)}" if circle else ""))
    if res.get("country"):
        _card.append(f"🌍 <b>Country:</b> {hesc(str(res['country']))}")
    if ltype:
        _card.append(f"📱 <b>Line Type:</b> {hesc(ltype)}")
    if ported_line:
        _card.append(ported_line.rstrip("\n"))
    if src_line:
        _card.append(f"📡 <b>Source:</b> {src_line}")
    _card.append(f"⚡ <b>Response:</b> {int(ms)}ms")
    _card.append(pcard_sep())
    if not _obits:
        _card.append("👤 <b>Name / Father / Phones / Region / Govt ID / Address</b> — "
                     "ye data aapki API se aata hai.")
        _card.append("💡 Render → Environment me <code>NUMINFO_PROVIDER_URL</code> + "
                     "<code>NUMINFO_PROVIDER_KEY</code> daalo → <code>/numapi</code> se check karo.")
    _card.append(BRAND_LINK)   # v59.7: clickable
    return "\n".join([_l for _l in _card if _l])


def build_qr_image(text: str, *, fg: str = "#111111", bg: str = "#FFFFFF",
                   logo: bool = True, size: int = 620,
                   label: str = "", tool: str = "qr") -> dict:
    """Branded QR PNG banao. Kabhi raise nahi karta — hamesha dict deta hai.

    Returns: {"ok": True, "bytes": BytesIO, "logo": bool, "note": str}
             {"ok": False, "error": "<hinglish>", "soft": bool}
    `soft=True` matlab service/limit ki galti hai (credit charge mat karna);
    `soft=False` matlab user ka input galat hai (message dikhao, credit bhi nahi).
    """
    t0 = time.time()
    txt = str(text or "").strip()
    note = ""

    if not txt:
        tel_note(tool, False, (time.time() - t0) * 1000, error="empty input")
        return {"ok": False, "soft": False,
                "error": "QR me kya daalna hai wo bhi bhejo — khaali message se QR nahi banta."}
    if len(txt.encode("utf-8")) > 8000 or len(txt) > QR_MAX_CHARS:
        tel_note(tool, False, (time.time() - t0) * 1000, error="text too long")
        return {"ok": False, "soft": False,
                "error": (f"Text bahut lamba hai ({len(txt):,} chars) — QR code me "
                          f"{QR_MAX_CHARS:,} chars tak hi fit hota hai. Thoda chhota bhejo.")}

    # colors: user ke hex validate karo, contrast kam ho to force-correct (QR scan
    # na hone wala QR bhej dena "premium" nahi hota)
    f = fg if _hex_ok(fg) else "#111111"
    b = bg if _hex_ok(bg) else "#FFFFFF"
    if f != fg or b != bg:
        note += "• Color format galat tha, default black/white laga diya.\n"
    if abs(_qr_luminance(f) - _qr_luminance(b)) < 0.30:
        f, b = "#111111", "#FFFFFF"
        note += ("• Aapke colors ka contrast bahut kam tha — QR scan nahi hota. "
                 "Black/white laga diya.\n")

    lg = _qr_logo_bytes() if logo else None
    try:
        buf = make_branded_qr(txt, fg=f, bg=b, logo_bytes=lg, size=size, label=label)
    except Exception as e:                                    # noqa: BLE001
        tel_note(tool, False, (time.time() - t0) * 1000, error=f"qr_build:{str(e)[:60]}")
        return {"ok": False, "soft": False,
                "error": clean_err(f"QR nahi ban paya — {e}")}
    tel_note(tool, True, (time.time() - t0) * 1000, credit=True)
    return {"ok": True, "bytes": buf, "logo": bool(lg), "note": note}


async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id

    # ---------- v56: PURANI / INACCESSIBLE MESSAGE GUARD ----------
    # PTB v21+ me `q.message` do tarah ka ho sakta hai:
    #   Message            → normal (reply_text / edit_text chalta hai)
    #   InaccessibleMessage→ bahut purana message (sirf chat + id hota hai,
    #                        reply_text bilkul NAHI hota) → pehle crash hota tha.
    # Yahan hum ek `cbmsg()` helper de dete hain jo dono case me safe rehta hai:
    # purana message ho to usi chat me NAYA message bhej dete hain.
    async def cbmsg():
        """Callback wale chat me message bhejne ke liye safe jagah."""
        m = getattr(q, "message", None)
        chat = getattr(update, "effective_chat", None) or getattr(m, "chat", None)
        if m is not None and getattr(m, "is_accessible", True) is not False and hasattr(m, "reply_text"):
            return m
        return chat if chat is not None else m

    # ---------- v49.4: VIP-ONLY GATE ----------
    # VIP lene / refer / madad / payment verify wale buttons sabke liye khule hain.
    if PREMIUM_ONLY and not vip_ok(uid) and not vip_free_cb(data):
        try:
            await q.message.edit_text(VIP_WALL_TEXT, reply_markup=vip_wall_kb(), parse_mode=HTML)
        except Exception:
            await q.message.reply_text(VIP_WALL_TEXT, reply_markup=vip_wall_kb(), parse_mode=HTML)
        return

    if data == "back_home":
        await safe_edit(q.message, WELCOME_TEXT, reply_markup=None, parse_mode=HTML)
        return

    # ==================================================================
    #  v60 — 🛡️ PREMIUM VAULT ke buttons (admin only)
    # ==================================================================
    if data in ("vault_backup", "vault_restore", "vault_vips"):
        if not is_admin(uid):
            await safe_answer_cb(q, "Ye sirf admin ke liye hai", show_alert=True)
            return
        class _Wrap:                                  # command functions ko Update chahiye
            def __init__(self, q):
                self.callback_query = q
                self.effective_user = q.from_user
                self.effective_chat = q.message.chat if q.message else None
                self.effective_message = q.message
        if data == "vault_backup":
            await safe_answer_cb(q, "Backup shuru…")
            await cmd_backup(_Wrap(q), context)
        elif data == "vault_restore":
            await safe_answer_cb(q, "Restore shuru…")
            await cmd_restore(_Wrap(q), context)
        else:
            await safe_answer_cb(q, "Report bana raha hoon…")
            await cmd_vips(_Wrap(q), context)
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
        contact_url = f"{SUPPORT_URL}?text={quote(order_text)}"
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
            [InlineKeyboardButton(f"💬 Admin se baat karo {SUPPORT_USERNAME}", url=contact_url)],
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
            [InlineKeyboardButton("💬 Support", url=SUPPORT_URL)],
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
                f"💬 Or talk to Support: {SUPPORT_LINK}",
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
        # v58: tool start par credits line NAHI (user ka order)
        await q.message.reply_text(tool_prompt("imei"),
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
    # ---------- v60.4: 💼 BUSINESS STUDIO buttons ----------
    if data == "bizstudio":
        context.user_data["mode"] = "biz_menu"
        await safe_edit(q.message, BIZ_MENU_TEXT, reply_markup=biz_menu_kb(), parse_mode=HTML)
        return
    if data.startswith("biz:"):
        _key = data.split(":", 1)[1]
        if _key not in BIZ_MENU:
            await safe_answer_cb(q, "Ye tool nahi mila", show_alert=True)
            return
        _u_b = get_user(uid, "")
        if not can_use_premium_tool(_u_b, uid):
            await safe_answer_cb(q, "Credits khatam — VIP lene par unlimited", show_alert=True)
            await safe_reply(q.message, get_credits_over_text(_key),
                             reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        await safe_answer_cb(q, "Bhejein 👇")
        context.user_data["mode"] = _key
        context.user_data.pop("biz_wait", None)
        _bk = _biz_kind(_key.replace("biz_", ""))
        await safe_reply(q.message, tool_prompt(_bk or _key), parse_mode=HTML,
                         reply_markup=InlineKeyboardMarkup([[
                             InlineKeyboardButton("⬅️ Business Studio", callback_data="bizstudio"),
                             InlineKeyboardButton("🏠 Home", callback_data="back_home")]]))
        return

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
        # v58: tool start par credits line NAHI (user ka order)
        await q.message.reply_text(tool_prompt(data), reply_markup=tool_tutorial_kb(data), parse_mode=HTML)
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
            "tts": ("🗣️ <b>TEXT → HINDI VOICE</b>\n\n"
                    "Ab apna <b>text bhejo</b> (Hindi me likhna best hai, max 1500 letters) —\n"
                    "main usse <b>ekdum real desi Hindi awaaz</b> me MP3 bana dunga.\n"
                    "📌 Jaise: <code>Bhai kaise ho? Aaj ka din bahut accha hai, chalo chai pe chalte hain.</code>\n"
                    "🎙️ Phir awaaz chunni hai — mard ya aurat.", "media_tts"),
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

    # ---------- v52: 🎞️ YOUTUBE QUALITY PICKER ----------
    # ---------- v52.3: 📌 PINTEREST — image pick (search results me se tap) ----------
    # ---------- 📧 TEMP MAIL inline buttons (v53.0) ----------
    if data in ("tm_inbox", "tm_otp"):
        sess = context.user_data.get("tempmail") or {}
        if not sess.get("address") or not sess.get("token"):
            await q.answer("Pehle NEW bhejo — temp email banao.", show_alert=True)
            return
        await q.answer("📬 Inbox check kar raha hoon…")
        _t0 = time.perf_counter()
        seen = context.user_data.get("tm_seen") or []
        res = await asyncio.to_thread(tm_poll, sess["address"], sess["token"], seen)
        _ms = (time.perf_counter() - _t0) * 1000
        if res.get("expired"):
            context.user_data["tempmail"] = {}
            context.user_data["tm_seen"] = []
            await q.message.reply_text(
                "⌛ Session expire ho gaya. <b>NEW</b> bhejo — naya email ban jayega.",
                parse_mode=HTML)
            return
        if not res.get("ok"):
            tel_note("tempmail", False, _ms, error=str(res.get("error") or "")[:120])
            await q.message.reply_text(str(res.get("error") or "Inbox nahi khula."),
                                       parse_mode=HTML)
            return
        tel_note("tempmail", True, _ms)
        context.user_data["tm_seen"] = res.get("all_ids") or seen
        msgs = res.get("messages") or []
        codes = res.get("new_codes") or res.get("codes") or []
        if data == "tm_otp":
            if not codes:
                await q.message.reply_text(
                    "🔑 <b>Abhi koi OTP nahi mila.</b>\n"
                    f"📮 <code>{hesc(sess['address'])}</code>\n\n"
                    f"📊 Inbox me {len(msgs)} message hai.\n"
                    "👉 Signup karo, phir 30-60 second baad <b>🔄 Inbox refresh</b> dabao.",
                    parse_mode=HTML)
                return
            L = ["🔑 <b>AAPKE OTP / CODES</b>", "━━━━━━━━━━━━━━━━━━━━━━"]
            for c in codes[:5]:
                _src = f"\n   <i>se: {hesc(str(c.get('subject') or c.get('from') or '')[:44])}</i>"
                L.append(f"  👉 <code>{hesc(str(c['code']))}</code>"
                         f"  ({hesc(str(c.get('label') or ''))}){_src}")
            L.append("\n━━━━━━━━━━━━━━━━━━━━━━")
            L.append(f"🏆 <b>Sabse likely: <code>{hesc(str(codes[0]['code']))}</b></code>")
            L.append("\n<i>⚠️ Ye code kisi ko mat batao — jis site par signup kiya "
                     "hai sirf wahin daalo.</i>")
            await q.message.reply_text(cut_html("\n".join(L), 3900), parse_mode=HTML)
            return
        # tm_inbox → chhota refresh summary
        if not msgs:
            await q.message.reply_text(
                f"📭 Inbox abhi bhi khali hai.\n📮 <code>{hesc(sess['address'])}</code>\n\n"
                "👉 Ye address signup me daalo, phir refresh dabao.", parse_mode=HTML)
            return
        L = [f"📧 <b>INBOX</b> — {res.get('count', 0)} message"
             + (f" · <b>{res.get('new_count')} NAYA</b>" if res.get("new_count") else ""),
             "━━━━━━━━━━━━━━━━━━━━━━"]
        if codes:
            L.append("🔑 <b>CODES:</b> " + " · ".join(
                f"<code>{hesc(str(c['code']))}</code>" for c in codes[:4]))
            L.append("")
        for i, m in enumerate(msgs[:4], 1):
            L.append(f"<b>{i}. {hesc(str(m.get('subject') or '')[:60])}</b>\n"
                     f"   📨 <code>{hesc(str(m.get('from') or '')[:40])}</code>\n"
                     f"   {hesc(str(m.get('body') or '')[:260])}\n")
        L.append("<i>🔄 Baar-baar refresh dabao — OTP aate hi upar dikhega.</i>")
        await q.message.reply_text(cut_html("\n".join(L), 3900), parse_mode=HTML)
        return

    if data == "tm_del":
        sess = context.user_data.get("tempmail") or {}
        if sess.get("address"):
            await asyncio.to_thread(tm_delete, sess["address"], sess.get("token", ""))
        context.user_data["tempmail"] = {}
        context.user_data["tm_seen"] = []
        await q.answer("🗑️ Temp email band ho gaya", show_alert=False)
        await q.message.reply_text(
            "🗑️ <b>Temp email band kar diya gaya.</b>\n"
            "📧 Naya chahiye to <b>TEMP MAIL</b> → <b>NEW</b> bhejo.",
            parse_mode=HTML)
        return

    if data.startswith("ytq:"):
        hstr = data.split(":", 1)[1]
        try:
            h = int(hstr)
        except ValueError:
            h = 1080
        if h == 0:  # ❌ Cancel (free)
            context.user_data.pop("yt_url", None)
            context.user_data.pop("mode", None)
            await q.message.edit_text("❌ Cancel ho gaya. Jab zaroorat ho to naya YouTube link bhejo. 👇")
            return
        url = context.user_data.pop("yt_url", None)
        context.user_data.pop("mode", None)
        _u_y = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u_y, uid):
            await q.answer("Credits finished!", show_alert=True)
            await q.message.reply_text(get_credits_over_text("insta_dl"),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        if not url:
            await q.answer("Pehle YouTube link bhejo (📥 Video Downloader)", show_alert=True)
            return
        st = await q.message.reply_text(
            f"📥 <b>{h}p</b> video download ho rahi hai...\n"
            "<i>(30 second - 2 minute, video ki length par depend)</i>", parse_mode=HTML)
        res = await asyncio.to_thread(_yt_quality_download, url, h)
        if not res.get("ok"):
            # v56: technical yt-dlp error ki jagah friendly Hindi + solution.
            _ferr = str(res.get("error") or "") or friendly_dl_error(platform="YouTube")
            await st.edit_text(fail_msg("YOUTUBE DOWNLOAD FAILED", _ferr),
                               parse_mode=HTML)
            return
        if res.get("type") == "link" and res.get("direct_url"):
            mb = res.get("size_mb") or 0
            await st.edit_text(
                f" <b>VIDEO ({h}p)</b> — file badi hai ({mb} MB, Telegram limit 48MB).\n"
                "Neeche ke direct link se browser/IDM me poora video download ho jayega:\n"
                f"<code>{res['direct_url']}</code>\n\n"
                + (res.get("note") or ""),
                parse_mode=HTML)
            add_use(uid)
            await q.message.reply_text(spend_credit_msg(uid, "insta_dl"), parse_mode=HTML)
            return
        if res.get("type") != "video" or not res.get("bytes"):
            await st.edit_text(fail_msg("VIDEO READY NAHI HUI", "Dobara try karo (link public hai kya?)"),
                               parse_mode=HTML)
            return
        media_buf = io.BytesIO(res["bytes"])
        media_buf.name = "youtube_video.mp4"
        dur = res.get("duration") or 0
        dur_line = f"• ⏱️ Length: {int(dur) // 60}m {int(dur) % 60}s\n" if dur else ""
        qnote = res.get("note_quality") or ""
        await q.message.reply_video(
            video=media_buf,
            caption=(
                f"📥 <b>YOUTUBE VIDEO — {h}p</b>\n"
                f"• 📝 {hesc(str(res.get('title') or '')[:60])}\n"
                f"{dur_line}• 📊 <b>Size:</b> {res.get('size_mb')} MB\n"
                f"• 🎞️ <b>Quality:</b> {h}p\n"
                f"• ⚙️ Engine: {hesc(str(res.get('engine') or ''))}\n"
                + (f"⚠️ {qnote}\n" if qnote else "")
            ),
            parse_mode=HTML,
            supports_streaming=True,
        )
        await st.delete()
        add_use(uid)
        await q.message.reply_text(spend_credit_msg(uid, "insta_dl"), parse_mode=HTML)
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

    if data.startswith("ttsvoice:"):
        vkey = data.split(":", 1)[1]
        _u_t = get_user(uid, q.from_user.first_name)
        if not can_use_premium_tool(_u_t, uid):
            await q.answer("Credits khatam!", show_alert=True)
            await q.message.reply_text(get_credits_over_text("mediastudio"),
                                       reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        txt = context.user_data.pop("tts_text", "")
        context.user_data.pop("mode", None)
        if not txt:
            await q.answer("Pehle text bhejo — Media Studio → Text → Hindi Voice", show_alert=True)
            return
        st = await q.message.reply_text("🗣️ <b>Hindi awaaz bana raha hoon...</b>\n<i>(5-15 seconds)</i>", parse_mode=HTML)
        res = await desi.hindi_tts(txt, vkey)
        if not res.get("ok"):
            await st.edit_text(fail_msg("HINDI VOICE FAILED", res.get("error", "")), parse_mode=HTML)
            return
        await st.delete()
        await q.message.reply_audio(
            audio=io.BytesIO(res["bytes"]), filename="hindi-voice.mp3",
            title="Hindi Voice — Utility Duniya", performer="Utility Duniya",
            caption=("🗣️ <b>TEXT → HINDI VOICE READY</b>\n"
                     f"🎙️ Awaaz: {vkey.upper()} · 📦 {res['size_mb']} MB\n\n"
                     + spend_credit_msg(uid, "mediastudio")),
            parse_mode=HTML)
        add_use(uid)
        return

    if data.startswith("ffimg:"):
        # v54.0: FF character portrait / outfit breakdown on-demand
        kind = data.split(":", 1)[1]
        imgs = context.user_data.get("ff_img") or {}
        url = imgs.get("char") if kind == "char" else imgs.get("outfit")
        if not url:
            await q.message.reply_text(
                "❌ Pehle FF UID ka result aana chahiye — "
                "🔥 FF UID me UID bhejo (e.g. <code>7860944073</code>).",
                parse_mode=HTML)
            return
        st = await q.message.reply_text(
            "️ Image load ho rahi hai..." + (" (outfit badi hai, ~3MB)" if kind == "outfit" else ""))
        try:
            await q.message.reply_photo(
                photo=url,
                caption=("🧍 <b>Equipped character</b>" if kind == "char"
                         else "👕 <b>Outfit / loadout breakdown</b>") +
                        "\n<i>Free Fire public profile data.</i>",
                parse_mode=HTML)
            await st.delete()
        except Exception as e:                               # noqa: BLE001
            await st.edit_text(
                f"❌ Image load nahi hui — <code>{hesc(str(e)[:60])}</code>\n"
                f"🔗 Direct: <code>{hesc(url)}</code>", parse_mode=HTML)
        tel_note("ffuid", True, 0, credit=False, cache_hit=True)
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

    # v55: Remove Links toggle — cloned caption se URLs/@username hata deta hai
    if data == "cloner_toggle_links":
        cfg = get_cloner_config(uid)
        new_val = not bool(cfg.get("remove_links"))
        save_cloner_config(uid, remove_links=new_val)
        if new_val:
            txt = ("🔗 <b>LINKS HATAO: ON 🟢</b>\n\n"
                   "Ab har cloned post ke caption se URLs, t.me links aur "
                   "@username apne aap hat jaayenge.\n"
                   "<i>(Normal text aur numbers jaise the waise rahenge.)</i>")
        else:
            txt = "🔗 <b>LINKS HATAO: OFF 🔴</b>\n\nAb caption jaisa hai waisa hi copy hoga."
        await q.message.reply_text(txt, reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
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
        save_cloner_config(uid, target="", caption="", watermark="", rename_tag="", replace_words="", remove_words="", thumbnail_file_id="", source_chat_id="", auto_status="off", remove_links=False)
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
            f"💬 Problem hai? Support: {SUPPORT_LINK}",
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
        await st.edit_text(f"⚠️ Proof save ho gaya (ID #{pid}) par admin ko bhej nahi paya.\nSupport ko batao: {SUPPORT_LINK}", parse_mode=HTML)
        return

    context.user_data.pop("mode", None)
    context.user_data.pop("pay_utr", None)
    context.user_data.pop("pay_shot_tries", None)
    context.user_data.pop("pay_utr_tries", None)
    await st.edit_text(
        user_payment_reply(pid, plan["name"], plan["price"], analysis),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 My payments", callback_data="mypay_list")],
            [InlineKeyboardButton("💬 Support", url=SUPPORT_URL)],
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
    # v59.7: madad/support sabke liye khula (VIP ho ya na ho — help chahiye to mile)
    if norm_text in ("💬 SUPPORT / MADAD", "SUPPORT / MADAD", "❓ HELP / TUTORIAL",
                     "HELP / TUTORIAL", "MADAD"):
        _txt, _kb = support_card() if "SUPPORT" in norm_text else (TUTORIAL_NOTICE, tutorial_kb())
        await update.message.reply_text(_txt, reply_markup=_kb, parse_mode=HTML)
        return
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
        
         "INTEREST", "VYAAJ CALC",
        # v51.1: weather tool permanently removed
        "WEATHER", "MAUSAM", "WEATHER / MAUSAM", "WEATHER / MAUSAM ",
        # v52.1: GOVT SERVICES (v52.0) user order par hataya
        "GOVT SERVICES", "GOVT", "GOVERNMENT", "GOVT SERVICE",
        # v54.0: VEHICLE / RTO INFO + CHALLAN — live RC/challan ke liye licensed
        # provider key chahiye jo available nahi hai (hub 410 "disabled" deta hai,
        # govt portals timeout/CAPTCHA). User order par tool hamesha ke liye hataya.
        "RTO VEHICLE INFO", "VEHICLE INFO + CHALLAN", "VEHICLE INFO",
        "VEHICLE / RTO INFO", "VEHICLE", "RTO", "CHALLAN",
        # v56.0: user order par 5 tools PERMANENTLY delete —
        # (1) 🌐 DOMAIN OSINT / IP  (2) 📌 PINTEREST  (3) 📄 WEB SCRAPER
        # (4) 🪪 AADHAAR EID       (5) 📡 TG PUBLIC INFO
        "DOMAIN OSINT / IP", "DOMAIN OSINT", "OSINT", "DOMAIN INFO",
        "IP INFO", "IP / DOMAIN INFO", "IP", "DOMAIN",
        "PINTEREST", "PINTEREST DOWNLOADER", "PINTEREST SEARCH",
        "WEB SCRAPER", "WEBSCRAPER", "SCRAPER", "WEB SCRAPE",
        "AADHAAR EID", "AADHAAR STATUS", "AADHAAR", "AADHAR", "EID",
        "TG PUBLIC INFO", "TG INFO", "TELEGRAM INFO", "TG PUBLIC",
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
                "WEATHER": "🌦️ Weather / Mausam",
            "MAUSAM": "🌦️ Weather / Mausam",
            "WEATHER / MAUSAM": "🌦️ Weather / Mausam",
            "WEATHER / MAUSAM ": "🌦️ Weather / Mausam",
            "GOVT SERVICES": "🏛️ Govt Services",
            "GOVT": "🏛️ Govt Services",
            "GOVERNMENT": "🏛️ Govt Services",
            "GOVT SERVICE": "🏛️ Govt Services",
            "RTO VEHICLE INFO": "🚗 Vehicle / RTO Info",
            "VEHICLE INFO + CHALLAN": "🚗 Vehicle / RTO Info",
            "VEHICLE INFO": "🚗 Vehicle / RTO Info",
            "VEHICLE / RTO INFO": "🚗 Vehicle / RTO Info",
            "VEHICLE": "🚗 Vehicle / RTO Info",
            "RTO": "🚗 Vehicle / RTO Info",
            "CHALLAN": "🚗 Vehicle / RTO Info",
            # ---- v56.0: 5 tools permanently deleted (short label) ----
            "DOMAIN OSINT / IP": "🌐 Domain OSINT / IP", "DOMAIN OSINT": "🌐 Domain OSINT",
            "OSINT": "🌐 OSINT", "DOMAIN INFO": "🌐 Domain Info",
            "IP INFO": "🌐 IP Info", "IP / DOMAIN INFO": "🌐 IP / Domain Info",
            "IP": "🌐 IP Info", "DOMAIN": "🌐 Domain Info",
            "PINTEREST": "📌 Pinterest", "PINTEREST DOWNLOADER": "📌 Pinterest",
            "PINTEREST SEARCH": "📌 Pinterest",
            "WEB SCRAPER": "📄 Web Scraper", "WEBSCRAPER": "📄 Web Scraper",
            "SCRAPER": "📄 Web Scraper", "WEB SCRAPE": "📄 Web Scraper",
            "AADHAAR EID": "🪪 Aadhaar EID", "AADHAAR STATUS": "🪪 Aadhaar EID",
            "AADHAAR": "🪪 Aadhaar EID", "AADHAR": "🪪 Aadhaar EID",
            "EID": "🪪 Aadhaar EID",
            "TG PUBLIC INFO": "📡 TG Public Info", "TG INFO": "📡 TG Public Info",
            "TELEGRAM INFO": "📡 TG Public Info", "TG PUBLIC": "📡 TG Public Info",
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
                "WEATHER": "🌦️ Weather abhi bot me nahi hai — aap 🌐 <b>IP / Domain Info</b> ya 📱 <b>Number Info</b> use kar sakte ho",
            "MAUSAM": "🌦️ Weather abhi bot me nahi hai — aap 🌐 <b>IP / Domain Info</b> ya 📱 <b>Number Info</b> use kar sakte ho",
            "WEATHER / MAUSAM": "🌦️ Weather abhi bot me nahi hai — aap 🌐 <b>IP / Domain Info</b> ya 📱 <b>Number Info</b> use kar sakte ho",
            "WEATHER / MAUSAM ": "🌦️ Weather abhi bot me nahi hai — aap 🌐 <b>IP / Domain Info</b> ya 📱 <b>Number Info</b> use kar sakte ho",
            "GOVT SERVICES": "🏛️ Govt Services abhi bot se hataya gaya hai — aap 📜 <b>Sarkari Kagaz Suite</b> aur 🏦 <b>IFSC/Pin/IP</b> use kar sakte ho",
            "GOVT": "🏛️ Govt Services abhi bot se hataya gaya hai — aap 📜 <b>Sarkari Kagaz Suite</b> aur 🏦 <b>IFSC/Pin/IP</b> use kar sakte ho",
            "GOVERNMENT": "🏛️ Govt Services abhi bot se hataya gaya hai — aap 📜 <b>Sarkari Kagaz Suite</b> aur 🏦 <b>IFSC/Pin/IP</b> use kar sakte ho",
            "GOVT SERVICE": "🏛️ Govt Services abhi bot se hataya gaya hai — aap 📜 <b>Sarkari Kagaz Suite</b> aur 🏦 <b>IFSC/Pin/IP</b> use kar sakte ho",
            "RTO VEHICLE INFO": "🚗 Vehicle/Challan info ke liye <b>official</b> source use karo: <b>VAHAN</b> (RC) vahan.parivahan.gov.in aur <b>eChallan</b> echallan.parivahan.gov.in — bot me ye tool ab nahi hai",
            "VEHICLE INFO + CHALLAN": "🚗 Vehicle/Challan info ke liye <b>official</b> source use karo: <b>VAHAN</b> (RC) vahan.parivahan.gov.in aur <b>eChallan</b> echallan.parivahan.gov.in — bot me ye tool ab nahi hai",
            "VEHICLE INFO": "🚗 Vehicle/Challan info ke liye <b>official</b> source use karo: <b>VAHAN</b> (RC) vahan.parivahan.gov.in aur <b>eChallan</b> echallan.parivahan.gov.in — bot me ye tool ab nahi hai",
            "VEHICLE / RTO INFO": "🚗 Vehicle/Challan info ke liye <b>official</b> source use karo: <b>VAHAN</b> (RC) vahan.parivahan.gov.in aur <b>eChallan</b> echallan.parivahan.gov.in — bot me ye tool ab nahi hai",
            "VEHICLE": "🚗 Vehicle/Challan info ke liye <b>official</b> source use karo: <b>VAHAN</b> (RC) vahan.parivahan.gov.in aur <b>eChallan</b> echallan.parivahan.gov.in — bot me ye tool ab nahi hai",
            "RTO": "🚗 Vehicle/Challan info ke liye <b>official</b> source use karo: <b>VAHAN</b> (RC) vahan.parivahan.gov.in aur <b>eChallan</b> echallan.parivahan.gov.in — bot me ye tool ab nahi hai",
            "CHALLAN": "🚗 Vehicle/Challan info ke liye <b>official</b> source use karo: <b>VAHAN</b> (RC) vahan.parivahan.gov.in aur <b>eChallan</b> echallan.parivahan.gov.in — bot me ye tool ab nahi hai",
            # ---------------- v56.0: 5 tools permanently deleted ----------------
            # (ye "kya use karo" suggestion line hai — label _why me hai)
            "DOMAIN OSINT / IP": "🌐 Domain OSINT / IP ki jagah → 📮 <b>Pincode Info</b> / 🏦 <b>IFSC Info</b> use karo",
            "DOMAIN OSINT": "🌐 Domain OSINT ki jagah → 📮 <b>Pincode Info</b> / 🏦 <b>IFSC Info</b> use karo",
            "OSINT": "🌐 OSINT tools ki jagah → 📮 <b>Pincode Info</b> / 🏦 <b>IFSC Info</b> use karo",
            "DOMAIN INFO": "🌐 Domain info ki jagah → 📮 <b>Pincode Info</b> / 🏦 <b>IFSC Info</b> use karo",
            "IP INFO": "🌐 IP info ki jagah → 📮 <b>Pincode Info</b> / 🏦 <b>IFSC Info</b> use karo",
            "IP / DOMAIN INFO": "🌐 IP / Domain info ki jagah → 📮 <b>Pincode Info</b> / 🏦 <b>IFSC Info</b> use karo",
            "IP": "🌐 IP info ki jagah → 📮 <b>Pincode Info</b> / 🏦 <b>IFSC Info</b> use karo",
            "DOMAIN": "🌐 Domain OSINT ki jagah → 📮 <b>Pincode Info</b> / 🏦 <b>IFSC Info</b> use karo",
            "PINTEREST": "📌 Pinterest ki jagah → 📥 <b>Video Downloader</b> ya ⚡ <b>Media Studio</b> (status/ringtone/MP3) use karo",
            "PINTEREST DOWNLOADER": "📌 Pinterest ki jagah → 📥 <b>Video Downloader</b> ya ⚡ <b>Media Studio</b> use karo",
            "PINTEREST SEARCH": "📌 Pinterest ki jagah → 📥 <b>Video Downloader</b> ya ⚡ <b>Media Studio</b> use karo",
            "WEB SCRAPER": "📄 Web Scraper ki jagah → browser me <b>Ctrl+A → Copy</b> karke text le lo, ya ⚡ <b>Media Studio</b> use karo",
            "WEBSCRAPER": "📄 Web Scraper ki jagah → browser me <b>Ctrl+A → Copy</b> karke text le lo",
            "SCRAPER": "📄 Web Scraper ki jagah → browser me <b>Ctrl+A → Copy</b> karke text le lo",
            "WEB SCRAPE": "📄 Web Scraper ki jagah → browser me <b>Ctrl+A → Copy</b> karke text le lo",
            "AADHAAR EID": "🪪 Aadhaar status khud check karo (official) → <b>resident.uidai.gov.in</b> ya <b>51969</b> par SMS",
            "AADHAAR STATUS": "🪪 Aadhaar status khud check karo (official) → <b>resident.uidai.gov.in</b> ya <b>51969</b> par SMS",
            "AADHAAR": "🪪 Aadhaar status khud check karo (official) → <b>resident.uidai.gov.in</b> ya <b>51969</b> par SMS",
            "AADHAR": "🪪 Aadhaar status khud check karo (official) → <b>resident.uidai.gov.in</b> ya <b>51969</b> par SMS",
            "EID": "🪪 Aadhaar status khud check karo (official) → <b>resident.uidai.gov.in</b> ya <b>51969</b> par SMS",
            "TG PUBLIC INFO": "📡 Channel ki member count Telegram app me hi dikhti hai — channel kholo, naam ke neeche <b>subscribers</b> likha hota hai",
            "TG INFO": "📡 Channel ki member count Telegram app me hi dikhti hai — channel kholo, naam ke neeche <b>subscribers</b>",
            "TELEGRAM INFO": "📡 Channel ki member count Telegram app me hi dikhti hai — channel kholo",
            "TG PUBLIC": "📡 Channel ki member count Telegram app me hi dikhti hai — channel kholo",
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
            # v58: credits line hatayi (VIP par khaali aati thi)
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

        # 3d. v60.4: 💼 BUSINESS STUDIO (10 earning tools)
        if action == "bizstudio":
            context.user_data["mode"] = "biz_menu"
            await update.message.reply_text(BIZ_MENU_TEXT, reply_markup=biz_menu_kb(),
                                            parse_mode=HTML)
            return
        if action and action.startswith("biz_"):
            _u_b = get_user(uid, user.first_name)
            if not can_use_premium_tool(_u_b, uid):
                await update.message.reply_text(get_credits_over_text(action),
                                                reply_markup=get_limit_exceeded_kb(),
                                                parse_mode=HTML)
                return
            context.user_data["mode"] = action
            context.user_data.pop("biz_wait", None)
            _bk = _biz_kind(action.replace("biz_", ""))
            await update.message.reply_text(
                tool_prompt(_bk or action) or f"✍️ <b>{hesc(BIZ_MENU.get(action, ('', action, ''))[1])}</b>",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎬 Tutorial", callback_data=f"toolvid:{_bk or action}"),
                    InlineKeyboardButton("🏠 Home", callback_data="back_home")]]),
                parse_mode=HTML)
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

        if action == "alltools":          # v61: saare tools ki list (FREE)
            await update.message.reply_text(all_tools_text(),
                                            reply_markup=free_mode_kb() if ALL_FREE else None,
                                            parse_mode=HTML)
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
        if action == "support":
            # v59.7: menu ka "💬 SUPPORT / MADAD" button — ek tap me owner se baat
            _txt, _kb = support_card()
            await update.message.reply_text(_txt, reply_markup=_kb, parse_mode=HTML)
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
            # v58: NA credits line, NA "/cancel" wali line — seedha tool prompt
            await update.message.reply_text(tool_prompt(action),
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
        await update.message.reply_text(
            f"✅ Rename Tag set: <b>{hesc(raw_text)}</b>",
            reply_markup=get_cloner_settings_kb(uid), parse_mode=HTML)
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
                await update.message.reply_text(
                    f"😅 Looks like you cannot find the UTR. No problem — talk to Support, "
                    f"they will verify it manually: {SUPPORT_LINK}", parse_mode=HTML)
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
    # ---------- v60.4: 💼 BUSINESS STUDIO input ----------
    if mode and str(mode).startswith("biz_") and mode != "biz_menu":
        _u_b = get_user(uid, user.first_name)
        if not can_use_premium_tool(_u_b, uid):
            context.user_data.pop("mode", None)
            await safe_reply(update.message, get_credits_over_text(mode),
                             reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            return
        _owner = (user.first_name or "") + (f" {user.last_name}" if user.last_name else "")
        _d = biz_parse(mode, raw_text, _owner.strip())
        _res = await asyncio.get_running_loop().run_in_executor(
            None, functools_partial(biz_build, mode, _d))
        _used = bool(_res and _res.get("ok"))
        if _used and not ALL_FREE:      # v61: free mode me credit nahi katta
            spend_credits(uid, 1)
        await biz_send_result(update.message, mode, _res or {}, uid, used=_used)
        return

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
        # v52: YouTube link → user khud quality chunta hai (360/480/720/1080)
        if re.search(r"(youtube\.com|youtu\.be)/", raw_text):
            # v59: INSTANT quality buttons.
            # PEHLE: poora metadata fetch hota tha (5-20 second!) phir buttons
            #        dikhte the — user ko lagta tha bot so gaya.
            # AB: cache ho to usse, warna standard options TURANT dikhte hain
            #     (1080/720/480/360). Background me cache bhar jaata hai taaki
            #     agli baar asli available qualities instantly dikhein.
            heights = yt_cached_qualities(raw_text)
            opts = heights if heights else list(YT_QUALITY_OPTIONS)
            if not heights:
                yt_warm_qualities(raw_text)      # background — block nahi karta
            rows = []
            for i in range(0, len(opts), 2):
                rows.append([InlineKeyboardButton(f"🎞️ {h}p" + (" ⭐" if h == opts[0] else ""),
                                                  callback_data=f"ytq:{h}") for h in opts[i:i + 2]])
            rows.append([InlineKeyboardButton("❌ Cancel", callback_data="ytq:0")])
            context.user_data["yt_url"] = raw_text
            context.user_data["mode"] = "yt_q"
            await st.edit_text(
                f"🎞️ <b>{to_bold('YOUTUBE QUALITY CHUNO')}</b>\n"
                "Video kon si quality me chahiye? <b>Jo dabao, wahi milegi.</b>\n"
                "⭐ = is video ki available best quality\n"
                "💳 1 credit jayega (video ready hone par)",
                reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
            return
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
                # v57: hesc — YouTube/IG title me `<`/`>` ho sakta hai
                # ("Song <Official> Video"), warna Telegram pura message reject.
                title_line = f"• 📝 {hesc(str(title))}\n" if title else ""
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
                             + (f"• 📝 {hesc(str(title))}\n" if title else "")
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
                    + (f"📝 <b>Title:</b> {hesc(str(title))}\n" if title else "")
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

    if mode == "bgmi":
        _t0 = time.perf_counter()
        res = await asyncio.to_thread(bgmi_player_info, raw_text)
        _ms = (time.perf_counter() - _t0) * 1000
        if res.get("ok"):
            st = res.get("stats") or {}
            pr = res.get("profile") or {}
            tel_note("bgmi", True, _ms, credit=True)
            await update.message.reply_text(
                spend_credit_msg(uid, "bgmi") + "\n" +
                pcard_title("🎮", "BGMI PLAYER CARD") + "\n"
                f"🎯 <b>{hesc(str(pr.get('name') or '—'))}</b>\n"
                + pcard_sep() + "\n"
                f"• <b>UID:</b> <code>{hesc(str(res.get('uid') or ''))}</code>\n"
                f"• <b>Level:</b> {hesc(str(pr.get('level', '—')))}\n"
                f"• <b>Rank Points:</b> {hesc(str(pr.get('rankPoints', '—')))}\n"
                f"• <b>Games:</b> {hesc(str(st.get('matches', '—')))} | "
                f"<b>Wins:</b> {hesc(str(st.get('wins', '—')))}\n"
                f"• <b>Kills:</b> {hesc(str(st.get('totalKills', '—')))} | "
                f"<b>Deaths:</b> {hesc(str(st.get('totalDeaths', '—')))}\n"
                f"• <b>K/D:</b> {hesc(str(st.get('killsPerMatch', '—')))}\n"
                f"• <b>Top 10:</b> {hesc(str(st.get('top10Finishes', '—')))} | "
                f"<b>Longest Kill:</b> {hesc(str(st.get('longestKill', '—')))}m\n"
                + (f"• <b>Title:</b> {hesc(str(pr.get('title')))[:40]}\n" if pr.get("title") else "")
                + pcard_foot(ms=_ms,
                             source=f"<code>{hesc(str(res.get('source') or 'public'))}</code>",
                             ),
                parse_mode=HTML)
        else:
            # ⚠️ v53.0: `service_busy` = SERVICE ki galti (BGMI ke public stats
            # servers abhi band hain), user ki nahi. Is case me **credit NAHI
            # katta** — pehle kat jata tha aur user ko kuch milta hi nahi tha.
            _soft = bool(res.get("service_busy"))
            tel_note("bgmi", False, _ms, soft=_soft,
                     error=str(res.get("error") or "")[:120])
            if _soft:
                await update.message.reply_text(str(res.get("error") or ""), parse_mode=HTML)
            else:
                # v57: safe_html_err — pehle hesc() tha isliye engine ka <b> tag
                # literal "&lt;b&gt;" ban ke dikhta tha (asli bug).
                await update.message.reply_text(
                    f"❌ {safe_html_err(res.get('error'))}",
                                                parse_mode=HTML)
        add_use(uid)
        return

    if mode == "ffuid":
        _t0 = time.perf_counter()
        # v53.0: region parsing ab engine ke andar hoti hai (REGION_ALIASES me
        # "india"→IND, "RU"→CIS jaise aliases bhi). Purana regex sirf 2-4 letter
        # codes pakadta tha, isliye "1633864660 india" fail ho jata tha.
        res = await asyncio.to_thread(ff_player_info, raw_text, "")
        _ms = (time.perf_counter() - _t0) * 1000
        if res.get("ok"):
            tel_note("ffuid", True, _ms, credit=True)
            lines = [
                f"🔥 <b>{to_bold('FREE FIRE PLAYER CARD')}</b>\n"
                f"🎯 <b>{hesc(str(res.get('nickname') or '—'))}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>UID:</b> <code>{hesc(str(res.get('uid') or ''))}</code>",
                f"• <b>Level:</b> {hesc(str(res.get('level', '—')))}"
                + (f" | <b>EXP:</b> {hesc(str(res.get('exp')))}" if res.get("exp") else ""),
                f"• <b>Region:</b> {hesc(str(res.get('region', '—')))}"
                + (f" | <b>Prime:</b> L{hesc(str(res.get('prime')))}" if res.get("prime") else ""),
                f"• <b>BR Rank:</b> {hesc(str(res.get('rank_br')))} ({hesc(str(res.get('rp_br')))} RP)",
            ]
            if res.get("rp_cs") not in (None, "—", ""):
                lines.append(f"• <b>CS Rank:</b> {hesc(str(res.get('rank_cs')))} "
                             f"({hesc(str(res.get('rp_cs')))})")
            if res.get("max_rank") not in (None, "—", ""):
                lines.append(f"• <b>Max Rank:</b> {hesc(str(res.get('max_rank')))}")
            if res.get("clan"):
                lines.append(f"• <b>Clan/Guild:</b> {hesc(str(res['clan'])[:40])}")
            if res.get("liked") not in (None, "—", ""):
                lines.append(f"• <b>Likes:</b> {hesc(str(res.get('liked')))}")
            if res.get("last_login") not in (None, "—", ""):
                lines.append(f"• <b>Last Login:</b> {hesc(str(res.get('last_login')))}")
            if res.get("created") not in (None, "—", ""):
                lines.append(f"• <b>Account Created:</b> {hesc(str(res.get('created')))}")
            if res.get("bio"):
                lines.append(f"• <b>Bio:</b> {hesc(str(res['bio'])[:100])}")
            lines += [pcard_foot(ms=_ms,
                                 source="<code>Garena public profile</code>",
                                 )]
            # ── v54.0: IMAGES ─────────────────────────────────────
            # Official profile banner (avatar + naam + level) photo ke roop me
            # jata hai — pehle sirf text card milta tha. Character portrait aur
            # outfit breakdown on-demand buttons par (outfit ~2.7MB hai, har
            # query par download wasteful).
            _pc = res.get("profile_card") or ""
            _char = res.get("character_image") or ""
            _outf = res.get("outfit_image") or ""
            _cap = spend_credit_msg(uid, "ffuid") + "\n" + "\n".join(lines)
            if res.get("character_name"):
                _cap = _cap.replace("━━━━━━━━━━━━━━━━━━━━━━\n<i>Public in-game",
                                    f"• <b>Character:</b> {hesc(str(res['character_name']))}\n"
                                    "━━━━━━━━━━━━━━━━━━━━━━\n<i>Public in-game", 1)
            _btns = []
            if _char:
                _btns.append([InlineKeyboardButton(
                    "🧍 Character photo", callback_data="ffimg:char")])
            if _outf:
                _btns.append([InlineKeyboardButton(
                    "👕 Outfit / loadout dekhiye", callback_data="ffimg:outfit")])
            context.user_data["ff_img"] = {"char": _char, "outfit": _outf,
                                           "card": _pc}
            if _pc:
                # banner URL se photo bhejo; fail ho to gracefully text-only
                try:
                    await update.message.reply_photo(
                        photo=_pc, caption=_cap, parse_mode=HTML,
                        reply_markup=InlineKeyboardMarkup(_btns) if _btns else None)
                except Exception as e:                       # noqa: BLE001
                    log.debug("ff profile_card send fail: %s", str(e)[:80])
                    await update.message.reply_text(
                        _cap, parse_mode=HTML,
                        reply_markup=InlineKeyboardMarkup(_btns) if _btns else None)
            else:
                await update.message.reply_text(
                    _cap, parse_mode=HTML,
                    reply_markup=InlineKeyboardMarkup(_btns) if _btns else None)
        else:
            _soft = bool(res.get("service_busy"))
            tel_note("ffuid", False, _ms, soft=_soft,
                     error=str(res.get("error") or "")[:120])
            if _soft:
                await update.message.reply_text(str(res.get("error") or ""), parse_mode=HTML)
            else:
                await update.message.reply_text(f"{res.get('error')}", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "tempmail":
        # v53.0: ab **OTP auto-detect** hota hai (temp mail ka asli use-case),
        # inline buttons aate hain (Refresh / Copy / Delete), aur naye messages
        # highlight hote hain. Pehle user ko 1200-char body dump me se 6-digit
        # code khud dhoondhna padta tha.
        cmd = (raw_text or "").strip().lower()
        sess = context.user_data.get("tempmail") or {}
        _tm_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Inbox refresh", callback_data="tm_inbox"),
             InlineKeyboardButton("🔑 OTP dhoondho", callback_data="tm_otp")],
            [InlineKeyboardButton("🗑️ Ye email band karo", callback_data="tm_del"),
             InlineKeyboardButton("⌨️ Menu", callback_data="back_home")],
        ])

        if cmd in ("inbox", "check", "box", "otp", "code", "refresh") and sess.get("address"):
            _t0 = time.perf_counter()
            seen_ids = context.user_data.get("tm_seen") or []
            res = await asyncio.to_thread(tm_poll, sess["address"], sess["token"], seen_ids)
            _ms = (time.perf_counter() - _t0) * 1000
            if res.get("expired"):
                context.user_data["tempmail"] = {}
                context.user_data["tm_seen"] = []
                tel_note("tempmail", False, _ms, error="session expired")
                await update.message.reply_text(
                    "⌛ Ye temp email session expire ho gaya hai.\n"
                    "📧 <b>NEW</b> bhejo — naya address ban jayega.",
                    parse_mode=HTML, reply_markup=_tm_kb)
                add_use(uid)
                return
            if not res.get("ok"):
                tel_note("tempmail", False, _ms, error=str(res.get("error") or "")[:120])
                await update.message.reply_text(str(res.get("error") or "Inbox nahi khula."),
                                                parse_mode=HTML, reply_markup=_tm_kb)
                add_use(uid)
                return
            tel_note("tempmail", True, _ms)
            context.user_data["tm_seen"] = res.get("all_ids") or seen_ids

            msgs = res.get("messages") or []
            codes = res.get("codes") or []
            if not msgs:
                await update.message.reply_text(
                    f"📭 <b>Inbox abhi khali hai</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📮 Aapka email: <code>{hesc(sess['address'])}</code>\n\n"
                    "Abhi is address par koi message nahi aaya.\n"
                    "👉 Jahan signup kiya wahan ye address daalo, phir yahan "
                    "<b>🔄 Inbox refresh</b> dabao.",
                    parse_mode=HTML, reply_markup=_tm_kb)
                add_use(uid)
                return

            L = [f"📧 <b>{to_bold('TEMP MAIL INBOX')}</b>\n"
                 f"📮 <code>{hesc(sess['address'])}</code>\n"
                 f"📊 {res.get('count', 0)} message"
                 + (f" · <b>{res.get('new_count')} NAYA</b>" if res.get("new_count") else "")
                 + "\n━━━━━━━━━━━━━━━━━━━━━━"]

            # 🔑 OTP sabse upar — yahi cheez user dhoondh raha hota hai
            if codes:
                L.append("")
                L.append("🔑 <b>AAPKE CODE (auto-detect):</b>")
                for c in codes[:4]:
                    _src = f" <i>({hesc(str(c.get('subject') or '')[:28])})</i>" if c.get("subject") else ""
                    L.append(f"  • <code>{hesc(str(c['code']))}</code> — "
                             f"{hesc(str(c.get('label') or ''))}{_src}")
                L.append("")
                L.append(f"👆 Sabse likely code: <b><code>{hesc(str(codes[0]['code']))}</b></code>")
            else:
                L.append("")
                L.append("🔑 <i>Koi OTP/verification code nahi mila in messages me.</i>")

            for i, m in enumerate(msgs[:5], 1):
                _new = " 🆕" if m.get("id") in (res.get("new_messages") and
                                               [x.get("id") for x in res.get("new_messages") or []]
                                               or []) else ""
                L.append(f"\n<b>{i}. {hesc(str(m.get('subject') or ''))}</b>{_new}\n"
                         f"📨 Se: <code>{hesc(str(m.get('from_name') or m.get('from') or ''))}</code>"
                         + (f" · {hesc(str(m.get('at'))[:16])}" if m.get("at") else "")
                         + (f"\n📎 {len(m.get('attachments') or [])} attachment"
                            if m.get("has_attachments") else "")
                         + f"\n{hesc(str(m.get('body') or '')[:420])}")
            L.append("\n━━━━━━━━━━━━━━━━━━━━━━")
            L.append("<i>🔄 Refresh dabate raho — OTP aate hi upar highlight ho jayega.</i>")
            await update.message.reply_text(cut_html("\n".join(L), 4000), parse_mode=HTML,
                                            reply_markup=_tm_kb)
            add_use(uid)
            return

        if cmd in ("del", "delete", "band", "close") and sess.get("address"):
            _d = await asyncio.to_thread(tm_delete, sess["address"], sess.get("token", ""))
            context.user_data["tempmail"] = {}
            context.user_data["tm_seen"] = []
            await update.message.reply_text(
                "🗑️ Temp email band kar diya gaya.\n"
                "📧 Naya chahiye to <b>NEW</b> bhejo.",
                parse_mode=HTML, reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⌨️ Menu", callback_data="back_home")]]))
            add_use(uid)
            return

        # NEW (ya koi bhi input) → naya mailbox
        _t0 = time.perf_counter()
        res = await asyncio.to_thread(tm_create)
        _ms = (time.perf_counter() - _t0) * 1000
        if not res.get("ok"):
            tel_note("tempmail", False, _ms, error=str(res.get("error") or "")[:120])
            await update.message.reply_text(str(res.get("error") or "Email nahi bana."),
                                            parse_mode=HTML)
            add_use(uid)
            return
        tel_note("tempmail", True, _ms, credit=True)
        # password sirf server-side (user_data) — user ko kabhi nahi dikhta
        context.user_data["tempmail"] = {"address": res["address"],
                                         "token": res["token"],
                                         "password": res.get("password", ""),
                                         "created": time.time()}
        context.user_data["tm_seen"] = []
        await update.message.reply_text(
            spend_credit_msg(uid, "tempmail") + "\n" +
            f"📧 <b>{to_bold('TEMP MAIL TAYAR')}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📮 <b>Aapka ek-baar email:</b>\n"
            f"<code>{hesc(res['address'])}</code>\n"
            f"🌐 Domain: <code>{hesc(str(res.get('domain') or ''))}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Ise kisi bhi jagah daalo — signup, OTP, password reset.\n"
            "   <i>(Jahan real email zaroori ho — bank/office — wahan mat use karo.)</i>\n\n"
            "🔑 <b>OTP khud nikal jayega</b> — message aate hi "
            "<b>🔄 Inbox refresh</b> dabao, code sabse upar dikhega.\n"
            f"⏳ Valid: ~{int((res.get('expires_in') or 2592000) // 86400)} din",
            parse_mode=HTML, reply_markup=_tm_kb)
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
        # ---------- v58: DEVICE NAAM / MODEL CODE ka rasta ----------
        # Prompt me likha tha "ya direct Device Model Name / Code bhejein" par
        # code sirf 15-digit IMEI leta tha — M2101K6P bhejne par seedha error.
        # Ab: agar input me LETTER hain (device naam/code) to device search
        # chalta hai — wahi premium card + PHONE KA PHOTO milta hai.
        _dev_q = (raw_text or "").strip()
        _dev_query = (not ok15) and bool(re.search(r"[A-Za-z]", _dev_q)) \
            and 2 <= len(_dev_q) <= 60
        if not ok15 and not _dev_query:
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
            ("🔎 <b>Device dhoondh raha hoon…</b>\n<i>5-15 second lagenge.</i>"
             if _dev_query else
             "🔎 <b>Phone ki details nikal raha hoon…</b>\n<i>5-15 second lagenge.</i>"),
            parse_mode=HTML)
        if _dev_query:
            res_i = await asyncio.to_thread(imei_search_device, _dev_q)
        else:
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
                + (f"🔢 <b>Query:</b> <code>{hesc(_dev_q[:40])}</code>\n"
                   if _dev_query else
                   f"🔢 IMEI: <code>{hesc(imei_clean)}</code>\n")
                + f"⚠️ {hesc(str(res_i.get('error'))[:160])}\n"
                + ("✅ <b>Koi credit nahi kata</b> — poora device naam likho "
                   "(jaise Redmi Note 10 Pro) ya 15-digit IMEI bhejein."
                   if _dev_query else
                   "✅ <b>Koi credit nahi kata</b> — IMEI check karke dobara bhejo "
                   "(dial <code>*#06#</code>)."),
                parse_mode=HTML)
            add_use(uid)
            return
        # v54.3: CREDIT FAIRNESS — pehle credit message PEHLE bhej diya jaata
        # tha, phir card bhejte waqt Telegram HTML error se crash ho jaata tha
        # (live screenshot 2:03 PM: "1 credit used" ke baad "Chhota sa ghatna").
        # Ab pehle card deliver hota hai, phir credit katta hai.
        photo_sent = False
        if res_i.get("photo") and not str(res_i["photo"]).lower().endswith(".gif"):
            try:
                await update.message.reply_photo(photo=res_i["photo"],
                                                 caption=render_imei_caption(res_i), parse_mode=HTML)
                photo_sent = True
            except Exception as e:                                 # noqa: BLE001
                log.debug("imei photo send fail: %s", str(e)[:80])
                photo_sent = False
        body = render_imei_text(res_i)
        if not photo_sent and not body.startswith("📲"):
            body = ("📲 <b>" + hesc(imei_title(res_i)) + "</b>\n"
                    f"🔢 <b>IMEI:</b> <code>{hesc(str(res_i.get('imei') or ''))}</code>\n" + body)
        _imei_sent = False
        try:
            await update.message.reply_text(body, parse_mode=HTML,
                                            disable_web_page_preview=True)
            _imei_sent = True
        except Exception as e:                                     # noqa: BLE001
            # HTML me koi masla ho to plain text (tags hata kar) bhejo —
            # user ko result mile, crash nahi.
            log.warning("imei card HTML fail, plain fallback: %s", str(e)[:100])
            try:
                await update.message.reply_text(
                    strip_html(body)[:4000], disable_web_page_preview=True)
                _imei_sent = True
            except Exception:                                      # noqa: BLE001
                pass
        if not _imei_sent:
            await update.message.reply_text(
                "❌ Device card Telegram par bhej nahi paya.\n"
                "✅ <b>Koi credit nahi kata.</b> Dobara try karo.", parse_mode=HTML)
            add_use(uid)
            return
        await update.message.reply_text(spend_credit_msg(uid, "imei"), parse_mode=HTML)
        try:
            buf_spec = io.BytesIO(imei_specs_json(res_i))
            buf_spec.name = imei_specs_filename(res_i)  # device search me bhi kaam karta hai
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
        # v57: offline validation turant (network nahi), phir provider + hub PARALLEL.
        # Pehle ye dono serial chalte the — user ko dono ka time jod kar lagta tha.
        res = lookup_phone_info(raw_text)
        if not res.get("ok"):
            tel_note("numinfo", False, 0, error=str(res.get("error"))[:90])
            await update.message.reply_text(f"❌ {res.get('error')}", parse_mode=HTML)
            context.user_data.pop("mode", None)
            return

        _t0 = time.perf_counter()
        _prov, _car = {}, {}
        try:
            _prov, _car = await asyncio.gather(
                asyncio.to_thread(numprov.lookup, raw_text),
                asyncio.to_thread(hubapi.hub_carrier_info, raw_text),
            )
        except Exception:                                          # noqa: BLE001
            _prov, _car = {}, {}
        _ms = (time.perf_counter() - _t0) * 1000

        # live data ka best available source (provider > hub > offline)
        _live = {k: v for k, v in (_prov or {}).items() if v not in (None, "", False)}
        if not _live.get("operator") and not _live.get("circle"):
            _hub_op, _hub_cir = _car.get("operator"), _car.get("circle")
            if _hub_op or _hub_cir:
                _live = {"operator": _hub_op, "circle": _hub_cir,
                         "type": _car.get("type"), "ported": _car.get("ported"),
                         "source": "hub"}

        _operator = str(_live.get("operator") or res["operator"])
        _circle = str(_live.get("circle") or res["circle"])
        _ltype = str(_live.get("type") or "")
        _ported = _live.get("ported")
        _src = str(_live.get("source") or "offline")
        # v57: offline mode me phonenumbers sirf COUNTRY deta hai (circle nahi).
        # Pehle wahi country "Circle/Region" me dikh jaati thi — confusing tha.
        if _src == "offline" and _circle.strip().lower() in (
                str(res.get("country") or "").strip().lower(), "", "india"):
            _circle = "⚪ live API set nahi (sirf country pata hai)"

        if _src == "demo":
            _src_line = ("🧪 <b>DEMO SAMPLE</b> — ye dummy data hai "
                         "(asli data ke liye apni API lagao → /numapi)")
        elif _src == "provider":
            _src_line = ("🟢 <b>LIVE</b> — aapki API se"
                         + (f" ({int(_prov.get('latency_ms') or _ms)}ms)" if _prov.get("latency_ms") else "")
                         + (f" • cache" if _prov.get("cached") else ""))
        elif _src == "hub":
            _src_line = "🟢 <b>LIVE</b> — hub carrier lookup se"
        else:
            _src_line = "⚪ <b>OFFLINE</b> — phonenumbers public database se (live carrier API set nahi hai)"

        _ported_line = ""
        if _ported not in (None, "", False):
            _pv = str(_ported).strip().lower()
            _ported_line = ("• <b>MNP (ported):</b> ✅ Haan — number apna network badal chuka hai\n"
                            if _pv in ("true", "1", "yes", "haan", "y") else
                            f"• <b>MNP (ported):</b> {hesc(str(_ported))}\n")

        # ---------- v59: 👤 AAPKE DIYE FORMAT ME CARD ----------
        # Ye card aapki API (Render me NUMINFO_PROVIDER_URL/KEY) ke response se
        # banta hai. Aapke format me — bilkul waisa hi:
        #     👤 Name: Sanjay Sah
        #     👨 Father: Ram Akwal Sah
        #     📱 Phones/Alt: 7305190526
        #     🌐 Region: BIHAR JIO
        #     🆔 Govt ID: 401635555849
        #     🏠 Address(es):
        #        └ S/O  Ram Akwal Sah, ...
        #     ────────────────────────
        _ow = (_live.get("owner") or {}) if isinstance(_live, dict) else {}
        _obits = []
        if _ow.get("name"):
            _obits.append(f"👤 <b>Name:</b> {hesc(str(_ow['name']))}")
        if _ow.get("father"):
            _obits.append(f"👨 <b>Father:</b> {hesc(str(_ow['father']))}")
        if _ow.get("alt"):
            _obits.append(f"📱 <b>Phones/Alt:</b> {hesc(str(_ow['alt']))}")
        if _ow.get("region"):
            _obits.append(f"🌐 <b>Region:</b> {hesc(str(_ow['region']))}")
        if _ow.get("govt_id"):
            _obits.append(f"🆔 <b>Govt ID:</b> {hesc(str(_ow['govt_id']))}")
        _addr = str(_ow.get("address") or "").strip()
        if _addr:
            # user ka exact format: label ke baad ek khali line, phir "   └ ..."
            _obits.append("🏠 <b>Address(es):</b>\n")
            for _ap in [x.strip() for x in _addr.split("|") if x.strip()][:4]:
                _obits.append(f"   └ {hesc(_ap[:300])}")
        # extra address list (agar API array bheje)
        _extra = (_live.get("extra") or {}) if isinstance(_live, dict) else {}
        for _k in ("addresses", "address_list"):
            for _a2 in (_extra.get(_k) or [])[:4]:
                if _a2 and hesc(str(_a2))[:300] not in _addr:
                    _obits.append(f"   └ {hesc(str(_a2)[:300])}")

        # v59.2: EK HI layout — renderer `numinfo_card()` me hai (neeche bhi
        # dekho), taaki `/numdemo` (sample preview) bilkul same dikhe.
        _ow = (_live.get("owner") or {}) if isinstance(_live, dict) else {}
        _extra = (_live.get("extra") or {}) if isinstance(_live, dict) else {}
        card = numinfo_card(res, _ow, _extra, _operator, _circle, _ltype,
                            _ported_line, _src_line, _ms)

        tel_note("numinfo", True, _ms, credit=True)
        await update.message.reply_text(
            spend_credit_msg(uid, "numinfo") + "\n" + card, parse_mode=HTML)
        add_use(uid)
        return

    if mode == "ifsc":
        # v50: to_thread — event loop block nahi hoga (rate-limit central gate se lagta hai)
        _t0 = time.perf_counter()
        i_res = await asyncio.to_thread(lookup_ifsc, raw_text)
        _ms = (time.perf_counter() - _t0) * 1000
        if i_res.get("ok"):
            rows = []   # v49.13: Google Maps link nahi
            card = (
                pcard_title("🏦", "IFSC BANK BRANCH REPORT") + "\n"
                f"🏛️ <b>{hesc(str(i_res['bank']))}</b>\n"
                + pcard_sep() + "\n"
                f"🔑 <b>IFSC:</b> <code>{hesc(str(i_res['ifsc']))}</code>\n"
                f"🏢 <b>Branch:</b> {hesc(str(i_res['branch']))}\n"
                f"📍 <b>Address:</b> {hesc(str(i_res['address']))}\n"
                f"🏙️ <b>City/State:</b> {hesc(str(i_res['city']))}, {hesc(str(i_res['state']))}\n"
                + (f"📞 <b>Contact:</b> {hesc(str(i_res['contact']))}\n" if i_res.get('contact') else "")
                + f"🔢 <b>MICR:</b> <code>{hesc(str(i_res['micr']))}</code>\n"
                + pcard_sep() + "\n"
                "💳 <b>Services:</b> "
                + "  ".join([
                    f"UPI {'✅' if i_res['upi'] else '❌'}",
                    f"NEFT {'✅' if i_res['neft'] else '❌'}",
                    f"RTGS {'✅' if i_res['rtgs'] else '❌'}",
                    f"IMPS {'✅' if i_res['imps'] else '❌'}",
                ]) + "\n"
                + pcard_foot(ms=_ms, source="official bank registry (Razorpay IFSC)")
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
            _t0 = time.perf_counter()
            p_res = await asyncio.to_thread(lookup_pincode, cleaned)
            _ms = (time.perf_counter() - _t0) * 1000
            if p_res.get("ok"):
                rows = []   # v49.13: Map link nahi
                _pos = list(p_res.get("post_offices") or [])
                card = (
                    pcard_title("📮", "PINCODE DETAILS") + "\n"
                    f"🔢 <b>Pincode:</b> <code>{hesc(str(p_res['pincode']))}</code>\n"
                    + pcard_sep() + "\n"
                    f"🏙️ <b>District:</b> {hesc(str(p_res['district']))}\n"
                    f"🗺️ <b>State:</b> {hesc(str(p_res['state']))}\n"
                    + (f"🏘️ <b>Taluk:</b> {hesc(str(p_res['taluk']))}\n" if p_res.get('taluk') else "")
                    # v57: khali field par line SKIP karo — pehle "📂 :  / " jaisa
                    # adhoora text dikhta tha (India Post har pincode ka division/
                    # circle nahi deta). Ab sirf jo data hai wahi dikhta hai.
                    + (f"📂 <b>Division/Region:</b> {hesc(str(p_res['division']))}"
                       + (f" / {hesc(str(p_res['region']))}" if p_res.get('region') else "")
                       + "\n" if (p_res.get('division') or p_res.get('region')) else "")
                    + (f"🔵 <b>Circle:</b> {hesc(str(p_res['circle']))}\n" if p_res.get('circle') else "")
                    + (f"🚚 <b>Delivery:</b> {hesc(str(p_res['delivery']))}\n"
                       if p_res.get('delivery') and str(p_res['delivery']).upper() not in ("N/A", "NA") else "")
                    + (f"🏷️ <b>Type:</b> {hesc(str(p_res.get('branch_type')))}\n"
                       if p_res.get('branch_type') and str(p_res['branch_type']).upper() not in ("N/A", "NA") else "")
                    + f"🏤 <b>Total Post Offices:</b> {hesc(str(p_res['total_offices']))}\n"
                    + pcard_sep() + "\n"
                    + f"🏤 <b>Post Offices ({len(_pos)}):</b>\n"
                    + "\n".join(f"   • {hesc(str(n))}" for n in _pos[:14])
                    + (f"\n   <i>… aur {len(_pos) - 14} aur</i>" if len(_pos) > 14 else "")
                    + "\n" + pcard_foot(ms=_ms, source="India Post official data")
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
                    pcard_title("📮", "AREA SEARCH") + "\n"
                    f"🔍 <b>Query:</b> <code>{hesc(a_res['query'])}</code>\n"
                    f"🏤 <b>{a_res['total']} post offices</b> mili{note}\n"
                    + pcard_sep() + "\n"
                    + "\n".join(lines)
                    + "\n" + pcard_foot(source="India Post official data", brand=False)
                    + "\n\n💡 Pincode copy karne ke liye neeche button par tap karo:",
                    reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML,
                )
            else:
                await st.edit_text(f"❌ {a_res.get('error')}\n\n💡 Ya 6-digit pincode bhejo (jaise <code>800001</code>)", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "qr":
        # v53.0: branded QR (logo + colors + telemetry) aur credit SIRF success par.
        # Color syntax: `<text> | #RRGGBB | #RRGGBB`  (2nd=foreground, 3rd=background)
        parts = [x.strip() for x in raw_text.split("|")]
        payload = parts[0]
        fg = parts[1] if len(parts) > 1 else "#111111"
        bg = parts[2] if len(parts) > 2 else "#FFFFFF"
        want_color = len(parts) > 1
        # 🛡️ logo sirf tab jab text chhota ho — lamba text = dense QR, logo se
        #    kuch phone ke camera scan nahi kar paate.
        res = await asyncio.to_thread(
            build_qr_image, payload, fg=fg, bg=bg,
            logo=not want_color and len(payload) <= 300,
            size=680 if len(payload) <= 120 else 620,
            label="UTILITY DUNIYA", tool="qr")
        if not res.get("ok"):
            # credit NAHI kata — QR bana hi nahi
            await update.message.reply_text(
                f"❌ {hesc(res.get('error'))}\n\n"
                "💡 <i>Credit nahi kata. Plain QR ke liye sirf text bhejo.</i>",
                parse_mode=HTML)
            tel_note("qr", False, 0, error="user_input", credit=False)
            return
        note = res.get("note") or ""
        cap = (spend_credit_msg(uid, "qr") + "\n" +
               f"📷 <b>{to_bold('HD QR CODE TAYYAR')}</b>\n\n"
               f"🔗 <code>{hesc(payload[:120])}{'…' if len(payload) > 120 else ''}</code>\n"
               f"📏 <b>Size:</b> {res['bytes'].getbuffer().nbytes // 1024} KB · "
               f"<b>Text:</b> {len(payload):,} chars\n")
        if res.get("logo"):
            cap += "🏷️ <b>Branded:</b> center logo + HD (error-correction H)\n"
        if want_color:
            cap += f"🎨 <b>Colors:</b> <code>{hesc(fg)}</code> / <code>{hesc(bg)}</code>\n"
        cap += ("\n<i>Scan karte hi link khul jayega.</i>")
        if note:
            cap += "\n\n" + note.rstrip("\n")
        await update.message.reply_photo(photo=res["bytes"], caption=cap, parse_mode=HTML)
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
                f"⚠️ {safe_html_err(str(res.get('error'))[:200])}\n"
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
                f"⚠️ {safe_html_err(str(res.get('error'))[:200])}\n"
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

    if mode == "media_tts":
        txt = raw_text.strip()
        if len(txt) < 5:
            await update.message.reply_text("❌ Thoda lamba text bhejo (min 5 letters).", parse_mode=HTML)
            return
        if len(txt) > 1500:
            await update.message.reply_text(
                f"❌ Text bahut lamba hai ({len(txt)} letters) — max 1500. Thoda chhota karke dobara bhejo.",
                parse_mode=HTML)
            return
        context.user_data["tts_text"] = txt
        context.user_data["mode"] = "media_tts_voice"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 MARD awaaz (Madhur)", callback_data="ttsvoice:male"),
             InlineKeyboardButton("🔊 AURAT awaaz (Swara)", callback_data="ttsvoice:female")],
        ])
        await update.message.reply_text(
            "✅ Text mil gaya!\n\nAb <b>awaaz chuno</b> (1 credit jayega):\n"
            "🎙️ <i>Dono awaazein ekdum real desi Hindi me hain.</i>",
            reply_markup=kb, parse_mode=HTML)
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
        if not raw_text.strip():
            await update.message.reply_text(
                "❌ WiFi ka naam khaali nahi ho sakta.\n\n"
                "📌 Jaise: <code>JioFiber_Home</code>\n"
                "📶 <b>WiFi ka naam (SSID) bhejo:</b>", parse_mode=HTML)
            return
        context.user_data["qr_wifi_ssid"] = raw_text.strip()
        context.user_data["mode"] = "qr_wifi_pass"
        await update.message.reply_text(
            "📶 <b>WiFi QR — Step 2/2</b>\n\n"
            f"WiFi Name (SSID): <code>{hesc(raw_text)}</code>\n\n"
            "Ab <b>WiFi password</b> bhejo:\n"
            "(agar open WiFi hai to <code>none</code> bhejo)", parse_mode=HTML)
        return

    if mode == "qr_wifi_pass":
        ssid = str(context.user_data.get("qr_wifi_ssid", "")).strip()
        pwd = raw_text.strip()
        open_net = pwd.lower() in ("none", "no", "skip", "-", "open", "")
        context.user_data.pop("mode", None)
        context.user_data.pop("qr_wifi_ssid", None)
        if not ssid:
            await update.message.reply_text(
                "❌ WiFi ka naam (SSID) set nahi hua. /qr_wifi se dobara shuru karo.",
                parse_mode=HTML)
            return
        # v53.0: special chars (`; : , " \`) engine escape karta hai — pehle raw
        # jate the aur QR galat SSID/password le kar connect fail karta tha.
        data = wifi_qr_data(ssid, "" if open_net else pwd)
        # ⚠️ WiFi QR me logo NAHI lagate: ye dense hota hai aur wall par print
        #    hota hai — logo se purane phones scan nahi kar paate. High-contrast
        #    black/white hi sabse reliable hai.
        res = await asyncio.to_thread(build_qr_image, data, logo=False, size=620,
                                      tool="qr_wifi")
        if not res.get("ok"):
            await update.message.reply_text(
                f"❌ {hesc(res.get('error'))}\n\n💡 <i>Credit nahi kata.</i>",
                parse_mode=HTML)
            return
        cap = (spend_credit_msg(uid, "qr") + "\n" +
               f"📶 <b>{to_bold('WIFI QR TAYYAR')}</b>\n\n"
               f"• <b>WiFi (SSID):</b> <code>{hesc(ssid)}</code>\n"
               f"• <b>Security:</b> {'Open (koi password nahi)' if open_net else 'WPA/WPA2'}\n"
               f"• <b>Password:</b> {'— nahi hai —' if open_net else f'<code>{hesc(pwd)}</code>'}\n"
               f"• <b>Hidden network:</b> nahi\n\n"
               "📱 Guest ye QR scan karega → uska phone <b>khud WiFi se jud jayega</b> ✅\n"
               "🖨️ <i>Isko print karke deewar par laga do — password kisi ko batana nahi padega!</i>\n\n"
               "⚠️ <b>Ek baat:</b> password QR ke andar encode hota hai, isliye jo bhi "
               "scan karega usse WiFi mil jayega. Sirf trusted logon ko scan karne do.")
        await update.message.reply_photo(photo=res["bytes"], caption=cap, parse_mode=HTML)
        add_use(uid)
        return

    if mode == "qr_vcard":
        name = raw_text.strip()
        # v53.0: naam validate karo — pehle khaali naam bhi accept ho jata tha
        # aur vCard me `FN:` khaali chali jati thi (phone contact "Unknown" banata).
        if len(re.sub(r"\s", "", name)) < 2:
            await update.message.reply_text(
                "❌ Naam kam se kam 2 akshar ka hona chahiye.\n\n"
                "📌 Jaise: <code>Himanshu Kumar</code>\n"
                "👉 <b>Apna naam bhejo:</b>", parse_mode=HTML)
            return
        context.user_data["qr_vc_name"] = name[:40]
        context.user_data["mode"] = "qr_vcard_phone"
        await update.message.reply_text(
            "👤 <b>Contact Card — Step 2/4</b>\n\n"
            f"Naam: <b>{hesc(name)}</b>\n\n"
            "Ab <b>phone number</b> bhejo:\n"
            "📌 Jaise: <code>9876543210</code> ya <code>+91 98765 43210</code>",
            parse_mode=HTML)
        return

    if mode == "qr_vcard_phone":
        digits = re.sub(r"\D", "", raw_text)
        if not (7 <= len(digits) <= 15):
            await update.message.reply_text(
                "❌ Ye phone number sahi nahi lag raha.\n\n"
                "📌 Jaise: <code>9876543210</code> ya <code>+91 98765 43210</code>\n"
                "👉 <b>Phone number dobara bhejo</b> (ya <code>skip</code>):", parse_mode=HTML)
            return
        context.user_data["qr_vc_phone"] = raw_text.strip()
        context.user_data["mode"] = "qr_vcard_org"
        await update.message.reply_text(
            "👤 <b>Contact Card — Step 3/4</b>\n\n"
            "Ab <b>company / dukaan ka naam</b> bhejo:\n"
            "📌 Jaise: <code>Kumar Electronics</code>\n\n"
            "<i>Nahi bharna? Sirf <code>skip</code> bhej do.</i>", parse_mode=HTML)
        return

    if mode == "qr_vcard_org":
        v = raw_text.strip()
        context.user_data["qr_vc_org"] = "" if v.lower() in ("skip", "-", "no", "none", "") else v[:60]
        context.user_data["mode"] = "qr_vcard_email"
        await update.message.reply_text(
            "👤 <b>Contact Card — Step 4/4</b>\n\n"
            "Ab <b>email</b> bhejo (optional):\n"
            "📌 Jaise: <code>rahul@shop.com</code>\n\n"
            "<i>Nahi bharna? Sirf <code>skip</code> bhej do.</i>", parse_mode=HTML)
        return

    if mode == "qr_vcard_email":
        v = raw_text.strip()
        email = ""
        if v.lower() not in ("skip", "-", "no", "none", ""):
            # sirf basic sanity — galat email par vCard phone me open hi nahi hota
            if re.fullmatch(r"[^@\s,;]{1,64}@[^@\s,;]{2,255}", v):
                email = v[:255]
            else:
                email = ""
        name = str(context.user_data.get("qr_vc_name", "")).strip()
        phone = str(context.user_data.get("qr_vc_phone", "")).strip()
        org = str(context.user_data.get("qr_vc_org", "")).strip()
        for k in ("mode", "qr_vc_name", "qr_vc_phone", "qr_vc_org"):
            context.user_data.pop(k, None)
        if not name or not phone:
            await update.message.reply_text(
                "❌ Naam ya phone number adhoora reh gaya. /qr_vcard se dobara shuru karo.",
                parse_mode=HTML)
            return
        if email == "" and v.lower() not in ("skip", "-", "no", "none", ""):
            await update.message.reply_text(
                f"⚠️ <code>{hesc(v[:40])}</code> email sahi format me nahi laga, "
                "isliye card me email nahi daala. Baaki card ban raha hai…",
                parse_mode=HTML)
        # v53.0: ab card me ORG + EMAIL bhi jata hai (pehle sirf naam/phone,
        # aur org hardcoded "Utility Duniya Bot" tha — user ka business nahi).
        data = vcard_data(name, phone, org=org, email=email)
        # ⚠️ logo NAHI: vCard QR contact-save ke liye scan hota hai, reliability
        #    sabse zaroori hai.
        res = await asyncio.to_thread(build_qr_image, data, logo=False, size=620,
                                      tool="qr_vcard")
        if not res.get("ok"):
            await update.message.reply_text(
                f"❌ {hesc(res.get('error'))}\n\n💡 <i>Credit nahi kata.</i>",
                parse_mode=HTML)
            return
        rows = [f"• <b>Naam:</b> {hesc(name)}", f"• <b>Phone:</b> <code>{hesc(phone)}</code>"]
        if org:
            rows.append(f"• <b>Company:</b> {hesc(org)}")
        if email:
            rows.append(f"• <b>Email:</b> <code>{hesc(email)}</code>")
        cap = (spend_credit_msg(uid, "qr") + "\n" +
               f"👤 <b>{to_bold('DIGITAL VISITING CARD TAYYAR')}</b>\n\n" +
               "\n".join(rows) + "\n\n"
               "📱 Scan karte hi contact phone me <b>save ho jayega</b> "
               "(naam + number + company + email) ✅\n"
               "🖨️ <i>Isko print karke counter par rakho, ya WhatsApp DP bana lo.</i>")
        await update.message.reply_photo(photo=res["bytes"], caption=cap, parse_mode=HTML)
        add_use(uid)
        return

    if mode == "short":
        st = await update.message.reply_text("🔗 Making short links (6 providers)...")
        _t0 = time.perf_counter()
        # v50: dono HTTP-heavy hain — thread me chalao, ek saath (parallel = 2x fast)
        links, exp = await asyncio.gather(
            asyncio.to_thread(shorten_url, raw_text, 3),
            asyncio.to_thread(expand_url, raw_text),
        )
        _ms = (time.perf_counter() - _t0) * 1000
        clean = exp.get("cleaned", raw_text)
        if links:
            body = "\n\n".join(f"{i}️⃣ <b>{name}</b> → <code>{u}</code>" for i, (name, u) in enumerate(links, 1))
            extra = ""
            if clean and clean != raw_text:
                extra = f"\n\n🧹 <b>Tracking-free original:</b>\n<code>{hesc(str(clean))}</code>"
            rows = [[InlineKeyboardButton(f"🔗 {name}", url=u)] for name, u in links]
            await st.edit_text(
                spend_credit_msg(uid, "short") + "\n"
                + pcard_title("🔗", "SHORT LINKS READY") + "\n"
                + body + extra + "\n"
                + pcard_foot(ms=_ms, source=f"{len(links)} shortener provider"),
                reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
        else:
            await st.edit_text(
                pcard_title("⚠️", "SHORT LINK NAHI BANA") + "\n"
                "Sab providers busy hain (ye unki taraf se hota hai, aapki galti nahi).\n"
                "🧹 <b>Tracking-free original link:</b>\n"
                f"<code>{hesc(str(clean))}</code>\n"
                + pcard_foot(ms=_ms, source="6 shortener providers", brand=False)
                + "\n\n💡 1 minute baad dobara try karo.",
                parse_mode=HTML,
            )
        add_use(uid)
        return

    if mode == "linkcheck":
        st = await update.message.reply_text("🔍 Running a 6-layer scan on the link...")
        _t0 = time.perf_counter()
        chk = await asyncio.to_thread(analyze_link, raw_text)
        _ms = (time.perf_counter() - _t0) * 1000
        risk = chk.get("risk", 0)
        bar = "█" * max(1, risk // 10) + "░" * (10 - max(1, risk // 10))
        reasons_txt = "\n".join(f"• {r}" for r in chk.get("reasons", [])[:8])
        sig = chk.get("signals", {})
        cap = (
            pcard_title("🛡️", "LINK CHECK REPORT") + "\n"
            + pcard_sep() + "\n"
            f"🎯 <b>Verdict:</b> {chk.get('verdict')}\n"
            f"📊 <b>Risk Score:</b> <code>{bar}</code> {risk}/100\n"
            f"🌐 <b>Final URL:</b> <code>{hesc(str(chk.get('final_url'))[:90])}</code>\n"
            f"🔁 Redirects: {sig.get('redirect_hops', 0)} | 🔓 HTTPS: {'✅' if sig.get('https') else '❌'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            + pcard_sep() + "\n"
            f"🔍 <b>What was found:</b>\n{reasons_txt}\n\n"
            f"💡 <b>What to do:</b> {chk.get('advice')}\n"
            + pcard_foot(ms=_ms, source="OpenPhish · URLScan · RDAP · 6-layer scan")
        )
        # v56: dead link par button banana bekaar tha + raw error dikhta tha.
        _reach = sig.get("reachable", True)
        if not _reach:
            cap += ("\n\n🔌 <b>Note:</b> Ye link abhi <b>khul nahi raha</b> — "
                    "domain galat/spelling galat hai, ya server band hai. "
                    "Aise link par OTP / password / UPI PIN <b>kabhi na dalo</b>.")
        kb_rows = []
        if chk.get("final_url"):
            kb_rows.append([InlineKeyboardButton("🌐 Final link kholo", url=chk["final_url"])])
        await st.edit_text(spend_credit_msg(uid, "linkcheck") + "\n" + cap,
                           reply_markup=InlineKeyboardMarkup(kb_rows) if kb_rows else None,
                           parse_mode=HTML)
        add_use(uid)
        return

    if mode == "appfind":
        # v53.0: ab **asli verification** hoti hai — Google Play + App Store +
        # F-Droid teeno par check, aur real app card (developer/rating/reviews/
        # downloads/icon) aata hai. Pehle sirf 8 blind search URLs bante the —
        # "xyzabc123fakeapp" bhejo tab bhi wahi 8 links aate the.
        # ⚠️ MOD/piracy sites (GetModPC, HappyMod) hata di gayi — modified APK
        #    distribute karna copyright violation hai aur malware ka bada source.
        _t0 = time.perf_counter()
        app_data = await asyncio.to_thread(app_lookup, raw_text)
        _ms = (time.perf_counter() - _t0) * 1000
        if not app_data.get("ok"):
            tel_note("appfind", False, _ms, error=str(app_data.get("error") or "")[:120])
            await update.message.reply_text(str(app_data.get("error") or "App search fail."),
                                            parse_mode=HTML)
            add_use(uid)
            return
        if not app_data.get("found"):
            # app mili hi nahi → credit NAHI katta (user ko kuch mila hi nahi)
            tel_note("appfind", False, _ms, error="not found")
            kb_stores = [[InlineKeyboardButton(f"{s['name']}", url=s["url"])]
                         for s in (app_data.get("stores") or [])]
            kb_stores.append([InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")])
            await update.message.reply_text(
                str(app_data.get("error") or "App nahi mili.")
                + "\n\n🔎 <b>Fir bhi khud dhoondhna ho to:</b>",
                reply_markup=InlineKeyboardMarkup(kb_stores), parse_mode=HTML)
            add_use(uid)
            return
        tel_note("appfind", True, _ms, credit=True)

        apps = app_data.get("apps") or []
        L = [pcard_title("📦", "APP FINDER"), 
             f"🔍 <b>Search:</b> <code>{hesc(app_data.get('query', '')[:36])}</code>",
             pcard_sep(),
             f"✅ <b>{len(apps)}</b> verified app" + ("s" if len(apps) != 1 else "")
             + " mili (Play Store / App Store / F-Droid par check kiya)",
             pcard_sep()]
        for i, a in enumerate(apps[:5], 1):
            _st = "🍎 iOS" if a.get("store") == "appstore" else "🤖 Android"
            L.append(f"\n<b>{i}. {hesc(str(a.get('title') or a.get('package') or ''))}</b>")
            _meta = []
            if a.get("rating"):
                _meta.append(f"⭐ {hesc(str(a['rating']))}")
            if a.get("votes"):
                _meta.append(f"({hesc(str(a['votes']))})")
            if a.get("downloads"):
                _meta.append(f"📥 {hesc(str(a['downloads']))}")
            if a.get("price"):
                _meta.append(f"💰 {hesc(str(a['price']))}")
            if _meta:
                L.append("   " + " · ".join(_meta))
            if a.get("developer"):
                L.append(f"   👨‍💻 {hesc(str(a['developer'])[:40])}"
                         + ("  🟢 <i>F-Droid par bhi</i>" if a.get("also_on_fdroid") else ""))
            if a.get("package"):
                L.append(f"   🆔 <code>{hesc(str(a['package'])[:52])}</code>")
            if a.get("tagline"):
                L.append(f"   ℹ️ <i>{hesc(str(a['tagline'])[:90])}</i>")
            L.append(f"   {_st}")
        L.append("\n" + pcard_sep())
        L.append(pcard_foot(ms=_ms, source="Google Play · App Store · F-Droid (live check)",
                            brand=False))
        L.append("👇 <b>Store me kholo:</b>")

        # buttons: pehle top app ke direct links, phir search links
        kb_stores = []
        _top = apps[0] if apps else {}
        if _top.get("store") == "play" and _top.get("package"):
            kb_stores.append([InlineKeyboardButton(
                "📱 Play Store par kholo (direct)", url=_top.get("url") or
                f"https://play.google.com/store/apps/details?id={_top['package']}")])
        elif _top.get("store") == "appstore" and _top.get("url"):
            kb_stores.append([InlineKeyboardButton("🍎 App Store par kholo (direct)",
                                                   url=_top["url"])])
        if _top.get("fdroid_url"):
            kb_stores.append([InlineKeyboardButton("🟢 F-Droid par kholo (open source)",
                                                   url=_top["fdroid_url"])])
        for s in (app_data.get("stores") or [])[:6]:
            kb_stores.append([InlineKeyboardButton(f"🔎 {s['name']} — search", url=s["url"])])
        kb_stores.append([InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")])

        await update.message.reply_text(
            spend_credit_msg(uid, "appfind") + "\n" + "\n".join(L)[:3600],
            reply_markup=InlineKeyboardMarkup(kb_stores), parse_mode=HTML)
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
# v51.3: Conflict warning ko spam na hone de — 2 minute me max 1 baar log
_CONFLICT_NOTE = {"t": 0.0}


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    # ---------- v51.3: CONFLICT (deploy me purana + naya instance ek saath) ----------
    # Ye SERVER-SIDE transient cheez hai: Render deploy ke dauran ~30 second tak
    # purana instance bhi chalta hai, dono getUpdates karte hain. Ye KHUD theek
    # ho jata hai (purana instance band hote hi). User ne koi galti nahi ki —
    # isliye user ko "ghatna" message NAHI dikhate, sirf ek saaf NOTE log hota hai.
    if isinstance(err, Conflict):
        _now = time.time()
        if _now - _CONFLICT_NOTE["t"] > 120:
            _CONFLICT_NOTE["t"] = _now
            log.warning(
                "CONFLICT (auto-fix hoga): deploy ke dauran purana + naya instance "
                "ek saath chalu the — ye 1-2 minute me khud theek ho jata hai. "
                "Bot band NAHI hua. Agar deploy ke 10 minute baad bhi bar-bar aaye, "
                "to Render me check karo ki koi doosra purana service same token "
                "par nahi chal raha.")
        return
    log.error("Exception handling update: %s", err)
    # v50: user bhi jaane ki koi chhota ghatna hua — chup-chaap na mile
    try:
        msg = getattr(update, "effective_message", None)
        if msg is not None:
            await msg.reply_text(
                "⚠️ <b>Chhota sa ghatna ho gaya!</b> Ye kaam nahi ho paya.\n"
                f"10 second baad dobara try karo. Problem bar-bar ho to Support: {SUPPORT_LINK}",
                parse_mode=HTML)
    except Exception:
        pass


# ---------------- POST INIT ----------------
async def _post_init(app: Application):
    # v59.3: 🛡️ background task crash bhi process ko na giraaye — sirf log ho
    try:
        import asyncio as _aio
        _loop = _aio.get_running_loop()

        def _loop_err(_loop2, _ctx):
            _ex = _ctx.get("exception")
            log.error("🛡️ background task error (bot chalta rahega): %s: %s",
                      type(_ex).__name__ if _ex else "?", str(_ex)[:200] if _ex else "")
        _loop.set_exception_handler(_loop_err)
        # v60: heartbeat — hang watchdog ko pata chale ki loop zinda hai
        from modules.core.guard import start_heartbeat_task
        start_heartbeat_task(_loop)
    except Exception:                                            # noqa: BLE001
        pass

    # ==================================================================
    #  v60 — 🛡️ PREMIUM VAULT ko chalu karo
    #  1) Boot par: pichhla backup MERGE karo (premium-floor protected)
    #     -> Render ne filesystem wipe kiya ho to bhi premium users wapas
    #  2) Background auto-backup thread chalu
    #  Ye dono kabhi crash nahi karte.
    # ==================================================================
    try:
        vault.bot = app.bot
        vault.owner_id = OWNER_ID
        _bchat = _env_int("VAULT_BACKUP_CHAT_ID", 0)
        vault.backup_chat = _bchat or OWNER_ID or None
    except Exception as e:                                       # noqa: BLE001
        log.warning("vault init skip: %s", str(e)[:120])

    try:
        if vault.enabled() and (vault.gh_ready() or vault.telegram_ready()):
            import asyncio as _aio2
            _res = await _aio2.get_running_loop().run_in_executor(
                None, functools_partial(vault.restore_now, "boot"))
            if _res.get("ok"):
                log.info("🛡️ BOOT RESTORE OK (%s) — VIP %s -> %s",
                         _res.get("source"), _res.get("premium_before", {}).get("total_premium"),
                         _res.get("premium_after", {}).get("total_premium"))
                if _res.get("n_users_added") or _res.get("report", {}).get("users", {}).get("only_remote"):
                    try:
                        await app.bot.send_message(
                            chat_id=OWNER_ID,
                            text=(f"🛡️ <b>VAULT BOOT RESTORE</b>\n"
                                  f"━━━━━━━━━━━━━━━━━━━━━━\n"
                                  f"📥 Source: <code>{hesc(str(_res.get('source'))[:70])}</code>\n"
                                  f"👑 VIP: {_res.get('premium_before', {}).get('total_premium')} ➜ "
                                  f"{_res.get('premium_after', {}).get('total_premium')}\n"
                                  f"ℹ️ <i>Pichhle backup se data wapas mila gaya.</i>"),
                            parse_mode="HTML")
                    except Exception:                            # noqa: BLE001
                        pass
            else:
                log.info("vault boot-restore skip: %s",
                         str(_res.get("why") or "")[:150])
    except Exception as e:                                       # noqa: BLE001
        log.warning("boot restore me dikkat (bot normal chalega): %s", str(e)[:150])

    try:
        vault.start_background(app.bot, OWNER_ID, vault.backup_chat)
    except Exception as e:                                       # noqa: BLE001
        log.warning("vault background skip: %s", str(e)[:120])

    commands = [
        BotCommand("start", "Bot chalu karo / menu kholo"),
        BotCommand("menu", "Saare tools ka menu"),
        BotCommand("premium", "Saare tools FREE — list dekho" if ALL_FREE
                   else "VIP plan lo (unlimited)"),
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
# v52: SELF-PING — bot apna hi public /health URL ping karta hai (Render LB ke through
# ye INBOUND request banta hai) -> free instance ka 15-min sleep timer reset ho jata hai.
# Result: cold start sirf pehli baar / deploy par; baad me bot ~24/7 jaagta hai = FAST respond.
_self_url = (os.environ.get("BOT_SELF_URL") or os.environ.get("RENDER_EXTERNAL_URL")
             or os.environ.get("RENDER_SERVICE_DNS_NAME") or "").strip()
if _self_url:
    if not _self_url.startswith("http"):
        _self_url = "https://" + _self_url
    _self_health = _self_url.rstrip("/") + "/health"
    if _self_health not in _KEEPALIVE_PEERS:
        _KEEPALIVE_PEERS.append(_self_health)
try:
    # v54.3: 10 → 4 minute. Render free instance 15 min inactivity par soti
    # hai; 4-min ping se bot + hub dono jaagte rehte hain → pehla reply fast.
    _KEEPALIVE_MINUTES = float(os.environ.get("KEEPALIVE_MINUTES") or 4)
except Exception:
    _KEEPALIVE_MINUTES = 4.0
_KEEPALIVE_STATE = {"last_run": None, "last_ok": None, "runs": 0}
# v59.9.2: webhook kyun on/off hua — /health par saaf dikhe (secret kabhi nahi).
_WEBHOOK_DIAG = {"mode_env": "(not set)", "url_env": "not set", "ext_env": "not set",
                 "decision": "abhi decide nahi hua", "why": "-"}
# v59.10: "bot sach me jawab de raha hai?" — aakhri update kab aaya (user ki
# sabse badi confusion: purana screenshot dekh kar lagta hai bot band hai).
_UPDATE_STATE = {"n": 0, "last_ts": 0.0, "last_at": None}
# v59.11: polling -> webhook switch ke waqt keepalive server ka port khaali karna
# padta hai (warna PTB webhook usi port par bind nahi kar payega).
_KEEPALIVE_SERVER = {"srv": None}

# v54.1: /health par **git commit SHA** bhi dikhao.
# Kyun: user screenshots bhejta hai aur pata nahi chalta tha ki Render par kaunsa
# commit chal raha hai (version same rehne par bhi code alag ho sakta hai). Render
# khud RENDER_GIT_COMMIT / RENDER_GIT_BRANCH env inject karta hai.
_GIT_COMMIT = (os.environ.get("RENDER_GIT_COMMIT") or "").strip()[:7]
_GIT_BRANCH = (os.environ.get("RENDER_GIT_BRANCH") or "").strip()
if not _GIT_COMMIT:
    try:  # local dev fallback (Render par ye branch chalega hi nahi)
        import subprocess as _sp
        _GIT_COMMIT = _sp.run(["git", "rev-parse", "--short=7", "HEAD"],
                              capture_output=True, text=True, timeout=3,
                              cwd=os.path.dirname(os.path.abspath(__file__))
                              ).stdout.strip()[:7]
    except Exception:                                            # noqa: BLE001
        _GIT_COMMIT = ""
_START_TS = time.time()


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


async def _track_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Har update (message/callback) ka time note karo — /health par dikhta hai.

    Koi reply nahi karta, sirf ginti karta hai (group=-10 me sabse pehle chalta hai).
    """
    try:
        _UPDATE_STATE["n"] += 1
        _UPDATE_STATE["last_ts"] = time.time()
        _UPDATE_STATE["last_at"] = time.strftime("%d-%m-%Y %H:%M:%S")
    except Exception:                                            # noqa: BLE001
        pass


def _last_update_line() -> str:
    """"Aakhri message: 3 min pehle" — 0 ho to saaf saaf likho."""
    if not _UPDATE_STATE["n"] or not _UPDATE_STATE["last_ts"]:
        return "abhi tak koi message nahi aaya (bot naya start hua hai)"
    _ago = int(max(0, time.time() - _UPDATE_STATE["last_ts"]))
    _ago_s = f"{_ago}s" if _ago < 60 else (f"{_ago // 60}m {_ago % 60}s" if _ago < 3600 else f"{_ago // 3600}h")
    return (f"aakhri message {_ago_s} pehle ({_UPDATE_STATE['last_at']})"
            f" | total {_UPDATE_STATE['n']} updates")


def _vault_health_html() -> str:
    """v60: /health par data-safety ki live proof (admin ko bharosa dilaane ke liye).

    Ye kabhi crash nahi karta — kuch bhi na mile to khaali string.
    """
    try:
        from modules.core.guard import guard_stats, mem_mb
        g = guard_stats()
        try:
            floor = vault.premium_floor_report_public()
        except Exception:                                        # noqa: BLE001
            from modules.core.vault import premium_floor_report
            floor = premium_floor_report(vault_db_path())
        lb = vault.last_backup or {}
        out = ["<p style='font-family:monospace'>--- v60 FORTRESS ---</p>",
               f"<p style='font-family:monospace'>db: {vault_db_path()} "
               f"| VIP users: {floor.get('total_premium', 0)} "
               f"(lifetime {floor.get('lifetime', 0)} + active {floor.get('active', 0)})</p>",
               f"<p style='font-family:monospace'>vault: enc=ON "
               f"github={'on' if vault.gh_ready() else 'off'} "
               f"tg={'on' if vault.telegram_ready() else 'off'} "
               f"interval={vault.interval_minutes()}m "
               f"| last_backup={lb.get('at') or 'abhi nahi'} "
               f"| backups={vault.stats.get('backups', 0)} "
               f"failures={vault.stats.get('failures', 0)}</p>",
               f"<p style='font-family:monospace'>crash-shield: caught="
               f"{g.get('handled', 0)} (handler {g.get('handler', 0)} / task "
               f"{g.get('task', 0)} / thread {g.get('thread', 0)}) "
               f"| fatal={g.get('fatal', 0)}</p>",
               f"<p style='font-family:monospace'>memory: {mem_mb():.0f} MB "
               f"(peak {g.get('mem_peak_mb', 0):.0f} MB) | gc_runs={g.get('gc_runs', 0)} "
               f"| loop_lag={g.get('heart_lag', 0)}s | beats={g.get('beats', 0)}</p>"]
        if g.get("last_why"):
            out.append(f"<p style='font-family:monospace'>last caught: "
                       f"{hesc(str(g['last_why'])[:140])}</p>")
        return "".join(out)
    except Exception as e:                                       # noqa: BLE001
        return f"<p style='font-family:monospace'>vault status n/a ({type(e).__name__})</p>"


def health_html() -> str:
    """/health ka poora report — POLLING (keepalive server) aur WEBHOOK dono me same.

    v59.9: pehle webhook mode me /health sirf chhota JSON deta tha, isliye user
    ko version/commit dikh hi nahi raha tha.
    """
    _ka = (f"keepalive pinger: last {_KEEPALIVE_STATE.get('last_run')} | ok={_KEEPALIVE_STATE.get('last_ok')}"
           f" | runs={_KEEPALIVE_STATE.get('runs')}")
    return ("<h1>Utility Duniya Super Bot chal raha hai - 24/7 ON. Status: 200 OK</h1>"
            f"<p style='font-family:monospace'>version: {BOT_VERSION}</p>"
            f"<p style='font-family:monospace'>commit: {_GIT_COMMIT or 'unknown'}"
            f" | branch: {_GIT_BRANCH or 'unknown'}"
            f" | mode: {'WEBHOOK' if WEBHOOK_URL else 'POLLING'}"
            f" | up: {int(time.time() - _START_TS) // 60}m</p>"
            f"<p style='font-family:monospace'>{_ka}</p>"
            f"<p style='font-family:monospace'>self-heal: crashes={_CRASH_STATE['count']}"
            f"{' | last=' + _CRASH_STATE['last'] if _CRASH_STATE['last'] else ' (koi crash nahi)'}</p>"
            f"{_vault_health_html()}"
            f"<p style='font-family:monospace'>bot: {_last_update_line()}</p>"
            f"<p style='font-family:monospace'>webhook: mode_env={_WEBHOOK_DIAG['mode_env']}"
            f" | url_env={_WEBHOOK_DIAG['url_env']} | render_url={_WEBHOOK_DIAG['ext_env']}"
            f" | decision={_WEBHOOK_DIAG['decision']} | why: {_WEBHOOK_DIAG['why']}</p>"
            f"<p style='font-family:monospace'>peers: {', '.join(_KEEPALIVE_PEERS)}</p>")


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
            self.wfile.write(health_html().encode("utf-8"))

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    try:
        with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
            _KEEPALIVE_SERVER["srv"] = httpd
            log.info("Keepalive server listening on port %s for UptimeRobot / Render", port)
            httpd.serve_forever()
    except Exception as e:
        log.warning("Keepalive server warning: %s", e)
    finally:
        _KEEPALIVE_SERVER["srv"] = None


def _stop_keepalive_server() -> None:
    """Keepalive server band karo — port khaali ho jaye (webhook ke liye zaroori)."""
    _srv = _KEEPALIVE_SERVER.get("srv")
    if _srv is None:
        return
    try:
        _srv.shutdown()          # doosre thread se call — blocked loop khul jaata hai
        _srv.server_close()
        log.info("Keepalive server band kiya — port %s khaali (webhook ke liye)",
                 os.environ.get("PORT", "10000"))
    except Exception as e:                                        # noqa: BLE001
        log.warning("Keepalive server band karte waqt dikkat: %s", str(e)[:90])


def _force_webhook_after_conflict(app) -> bool:
    """Polling me Conflict aa gaya? Webhook par switch kar do (wahan Conflict nahi hota).

    v59.11: pehle yahan sirf "15s baad try karo" hota tha — user ko Render logs me
    baar-baar CONFLICT dikhta tha. Ab pehla Conflict aate hi bot khud webhook par
    chala jata hai (Render URL + Telegram preflight pass hone par). Wahan
    getUpdates hota hi nahi -> Conflict dobara aana namumkin.

    True = webhook par switch ho gaya (process yahin chal raha hai).
    """
    global WEBHOOK_URL
    url = webhook_url_from_env()
    if not url:
        return False
    ok, why = webhook_url_usable(url)
    if not ok:
        log.warning("Conflict ke baad webhook bhi nahi chal sakta (%s) — polling retry karega", why)
        return False
    secret = (os.environ.get("WEBHOOK_SECRET") or BOT_TOKEN.split(":")[-1]).strip("/")
    pf_ok, pf_why = webhook_preflight(url, f"/webhook/{secret}", BOT_TOKEN,
                                      os.environ.get("WEBHOOK_SECRET_TOKEN") or None)
    if not pf_ok:
        log.warning("Conflict ke baad webhook preflight fail (%s) — polling retry karega", pf_why)
        return False
    WEBHOOK_URL = url
    _WEBHOOK_DIAG.update({"decision": "WEBHOOK (Conflict ke baad auto-switch)",
                          "why": "polling me Conflict tha — webhook par switch"})
    _stop_keepalive_server()
    from modules.render_health import install_webhook_health_routes
    install_webhook_health_routes(health_html)
    port = int(os.environ.get("PORT", "10000"))
    log.warning("🔁 POLLING me Conflict tha → ab WEBHOOK par switch kar raha hoon "
                "(getUpdates band, Conflict ab nahi aayega) | pid=%s", os.getpid())
    try:
        app.run_webhook(
            listen="0.0.0.0", port=port, url_path=f"/webhook/{secret}",
            webhook_url=url.rstrip("/") + f"/webhook/{secret}",
            allowed_updates=Update.ALL_TYPES, drop_pending_updates=True,
            secret_token=(os.environ.get("WEBHOOK_SECRET_TOKEN") or None) or None,
        )
        return True
    except Exception as e:                                        # noqa: BLE001
        log.error("Webhook switch fail (%s: %s) — polling retry karega", type(e).__name__, str(e)[:150])
        WEBHOOK_URL = ""
        return False


def main():
    # =====================================================================
    #  v60 — 🛡️ CRASH SHIELD SABSE PEHLE ON KARO
    #  (guard sabse pehle install hota hai taaki boot ke waqt bhi kuch crash
    #   ho to log me dikhe aur bot chalta rahe)
    # =====================================================================
    try:
        install_global_guard()
    except Exception as _e:                                      # noqa: BLE001
        log.warning("guard install skip: %s", str(_e)[:100])
    try:
        start_memory_watchdog()      # 💀 Render free 512MB — OOM kill se bachao
    except Exception as _e:                                      # noqa: BLE001
        log.warning("memory watchdog skip: %s", str(_e)[:100])
    try:
        start_hang_watchdog()        # 🧟 chup-chaap maut (hung loop) se bachao
    except Exception as _e:                                      # noqa: BLE001
        log.warning("hang watchdog skip: %s", str(_e)[:100])

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
    _WEBHOOK_DIAG["mode_env"] = str(os.environ.get("WEBHOOK_MODE") or "(not set)")
    _WEBHOOK_DIAG["url_env"] = "set" if os.environ.get("WEBHOOK_URL") else "not set"
    _WEBHOOK_DIAG["ext_env"] = "set" if os.environ.get("RENDER_EXTERNAL_URL") else "not set"
    _wh_ok, _wh_why = (False, "polling mode (WEBHOOK_MODE=off ya koi URL nahi)")
    if WEBHOOK_URL:
        _wh_ok, _wh_why = webhook_url_usable(WEBHOOK_URL)
        if not _wh_ok:
            log.warning("WEBHOOK chalu nahi ho sakta (%s) — ab POLLING par chalega", _wh_why)
            WEBHOOK_URL = ""
        else:
            # v59.9: Telegram se ek baar pooch lo — setWebhook maan gaya tabhi webhook.
            # Fail hua to chup-chaap POLLING (bot kabhi nahi rukta, koi crash nahi).
            _secret = (os.environ.get("WEBHOOK_SECRET") or BOT_TOKEN.split(":")[-1]).strip("/")
            _pf_ok, _pf_why = webhook_preflight(WEBHOOK_URL, f"/webhook/{_secret}", BOT_TOKEN,
                                                os.environ.get("WEBHOOK_SECRET_TOKEN") or None)
            if _pf_ok:
                _WEBHOOK_DIAG.update({"decision": "WEBHOOK", "why": "Telegram ne URL maan liya ✅"})
                log.info("WEBHOOK MODE confirm (Telegram ne URL maan liya) — koi Conflict nahi hoga")
            else:
                _WEBHOOK_DIAG.update({"decision": "POLLING (preflight fail)", "why": _pf_why})
                log.warning("WEBHOOK preflight fail (%s) — POLLING par chalega", _pf_why)
                WEBHOOK_URL = ""
    if not WEBHOOK_URL:
        log.warning("MODE = POLLING (safe default) | %s", _wh_why)
        if _WEBHOOK_DIAG["decision"].startswith("abhi"):
            _WEBHOOK_DIAG.update({"decision": "POLLING (safe)", "why": _wh_why})

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
    app.add_handler(CommandHandler(["imeistatus", "imeiapi"], cmd_imeistatus))
    app.add_handler(CommandHandler(["hubstatus", "hubapi", "api"], cmd_hubstatus))
    app.add_handler(CommandHandler(["version", "ver", "v"], cmd_version))
    app.add_handler(CommandHandler(["numapi", "numinfoapi", "numberapi"], cmd_numapi))
    app.add_handler(CommandHandler(["numdemo", "numinfodemo", "numpreview"], cmd_numdemo))
    app.add_handler(CommandHandler(["numtest", "numcheck", "numinfotest"], cmd_numtest))
    app.add_handler(CommandHandler(["support", "helpme", "owner", "contact"], cmd_support))
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
    # v60: 🛡️ PREMIUM VAULT commands (aapka data kabhi na khoye)
    app.add_handler(CommandHandler(["vault", "premiumvault", "datavault"], cmd_vault))
    app.add_handler(CommandHandler(["backup", "save"], cmd_backup))
    app.add_handler(CommandHandler(["restore", "recover"], cmd_restore))
    app.add_handler(CommandHandler(["vips", "viplist", "premiums"], cmd_vips))
    app.add_handler(CommandHandler(["fixvip", "vipfix"], cmd_fixvip))
    app.add_handler(CommandHandler(["ledger", "viphistory"], cmd_ledger))

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
    # v59.10: har update ka hisaab (group=-10 = sabse pehle, koi reply nahi karta)
    app.add_handler(TypeHandler(Update, _track_update), group=-10)
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

    # 🛡️ v60: SAARE handlers ko crash-shield me lapeto (sabse zaroori line)
    _armed = arm_all_handlers(app)
    log.info("🛡️ CRASH SHIELD: %s handlers lapete gaye — koi bhi tool crash ho to "
             "bot zinda rahega", _armed)

    app.add_error_handler(on_error)

    # v51.3: purana "v30 Ultra" hardcode text the — ab asli version dikhta hai logs me
    # v59.3: version + commit + self-check — ek nazar me pata chal jaye ki KAUNSA
    #        code chal raha hai (v58/v59 ka confusion khatam).
    print(f"🚀 Starting ToolVault / Utility Duniya Super Bot ({BOT_VERSION})")
    print(f"   commit {_GIT_COMMIT} | pid {os.getpid()} | {socket.gethostname()}")
    try:
        _startup_selfcheck()
    except Exception as _e:                                      # noqa: BLE001
        log.warning("self-check skip (crash nahi): %s", str(_e)[:120])
    # ---------- v47+: WEBHOOK MODE (Render par sabse safe) ----------
    # Polling me har deploy par 10-20 second tak do instance ek saath getUpdates
    # karte hain -> Telegram "Conflict: terminated by other getUpdates request".
    # Webhook me Telegram khud update bhejta hai, getUpdates hota hi nahi -> Conflict kabhi nahi.
    if WEBHOOK_URL:
        from modules.render_health import install_webhook_health_routes
        install_webhook_health_routes(health_html)
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

    # v59.9: agar pehle webhook lagi thi to hata do — warna getUpdates
    # "Conflict: can't use getUpdates method while webhook is active" dega.
    try:
        from telegram import Bot as _Bot
        _Bot(BOT_TOKEN).delete_webhook(drop_pending_updates=True)
        log.info("Purani webhook (agar thi) hata di — safai OK")
    except Exception as _e:                                      # noqa: BLE001
        log.debug("webhook cleanup skip: %s", str(_e)[:80])

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
            if "conflict" in _msg:
                # v59.11: retry se pehle webhook try karo — Conflict ki jad yahin khatam
                if _force_webhook_after_conflict(app):
                    return
                if _try < 5:
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
    # --check = sirf self-check chalao (deploy verify ke liye), warna supervisor
    if "--check" in sys.argv:
        _startup_selfcheck()
        sys.exit(0)
    _supervise()
