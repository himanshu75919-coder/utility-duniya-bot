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
import tempfile
from datetime import date, datetime, timezone   # v75: timezone (smart-detect message)
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
# v76 FORTRESS — 🧹 JANITOR: khud-safai (temp files + atke hue ffmpeg process +
# bounded cache prune + disk watchdog). Render free plan par "bot baar-baar
# crash" ke 3 chhupe kaaran isi se khatam hote hain.
from modules.core.janitor import (
    janitor_block as _janitor_block,
    janitor_stats as _janitor_stats,
    start_janitor,
)
# v76 — 🪣 saare module-cache ek registry me (memory pressure me ek saath saaf)
from modules.core.bounded import (
    cache_report as _bounded_report,
    clear_all_caches as _clear_module_caches,
    prune_all_caches as _prune_module_caches,
)
# v75 — 🧠 PRO ENGINE: saare tools ka universal advanced layer
#       (smart detect + provider race + result history + tool analytics)
from modules.core import proengine as pro
# v75.1 — 📤 BULK MODE (EXCEL): earning tool (list -> poora Excel report)
from modules import bulk_mode as BM
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
from modules.core.vault import (db_path as vault_db_path, vault,
                                set_main_loop as vault_set_main_loop)
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
# v76: 💰 EARN STUDIO — 5 NAYE premium kamai wale tools
#      (rent receipt · udhaar khata · offer poster · quotation · profit card)
#      Ye sab 100% OFFLINE hain — koi API kharidni nahi padti.
from modules.earn_studio import (
    EARN_MENU as EARN_STUDIO_MENU,
    EARN_ORDER as EARN_STUDIO_ORDER,
    earn_build as earn_studio_build,
    khata_image as biz_khata,
    poster_image as biz_poster,
    profit_card_image as biz_profit,
    quotation_image as biz_quote,
    rent_receipt_image as biz_rent,
)



from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    KeyboardButton,
    Message,          # v75: smart-detect ka 1-tap button (synthetic input message)
    ReplyKeyboardMarkup,
    Update,
)
from telegram.error import Conflict
from telegram.ext import (
    Application,
    ApplicationHandlerStop,     # v75.2: bulk file handler ke baad aage na jaaye
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
from modules import media_downloader as MD      # v66: cookies + client ladder
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
from modules.vehicle_tool import (
    vehicle_lookup as vahan_lookup,
    offline_parse as vahan_offline,
    provider_ready as vahan_provider_ready,
)
from modules.osint_tools import (
    search_by_area_name,
    lookup_ifsc,
    lookup_phone_info,
    lookup_pincode,
    lookup_whois,        # v70: 🌐 WEBSITE OWNER X-RAY (RDAP public record)
)
from modules.username_hunter import hunt_username     # v71.8: 🕵️ USERNAME HUNTER (public only)
from modules import temp_number as TN                 # v71.9: 📞 TEMP MAIL (NUMBER) — 100% FREE temp number + OTP
from modules import chat_xray as CXR                   # v73.0: 💬 WHATSAPP CHAT X-RAY (offline, free)
from modules import bseb_result as BSEBR               # v73.1: 📋 BOARD RESULT (BSEB official API)
from modules import boards as BRD                      # v74.5: BSEB + CBSE
from modules import captcha_bridge as CB              # v74.6: 🔐 captcha bridge (user solve karta hai)
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
from modules.core import httpio as http_engine   # v72.0: shared HTTP engine (speed + auto-retry)
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
    # v76: sabse pehle saare MODULE cache (osint / username / vehicle / imei ...)
    # — pehle inhe koi saaf hi nahi karta tha, isliye RAM dheere-dheere bharti thi.
    try:
        _clear_module_caches()
    except Exception:
        pass
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
    # v64: prefix key — "dl_instagram", "dl_youtube" … sab isi limit me aate hain
    "dl":          (15, 120, "Video Downloader"),
    "terabox":     (6,  120, "Terabox Downloader"),
    "bankpdf":     (5,  180, "Bank Statement → Excel"),
    "cxray":       (5,  300, "Chat X-Ray"),            # v73.0: apni chat ki report (FREE)
    "bsebr":       (10, 300, "Result Check (BSEB)"),   # v74.0: wizard (FREE)
    "rc":          (12, 300, "Result Check (BSEB)"),   # v74.0: rc_code/rc_roll (wizard steps)
    "media_ytmp3": (5,  120, "YouTube → MP3"),
    "media_tts":   (8,  60,  "Text → Hindi Voice"),
    "yt_q":        (8,  120, "YouTube Quality"),
    # normal info tools
    "bgmi":        (8,  60,  "BGMI UID"),
    "ffuid":       (8,  60,  "FF UID"),
    "tempmail":    (10, 120, "Temp Mail"),
    "tnum":        (25, 300, "Temp Mail (Number)"),    # v71.9: free temp number + OTP
    "ifsc":        (15, 60,  "IFSC Info"),
    "osint_whois": (12, 60,  "Website Owner (WHOIS)"),
    "uhunt":       (10, 60,  "Username Hunter (Public)"),
    "vahan":       (10, 120, "RC + Challan (Gaadi X-Ray)"),
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
    # ---- v76: 💰 EARN STUDIO (5 naye kamai wale tools) ----
    "biz_rent":        (10, 120, "Rent Receipt"),         # v76
    "biz_khata":       (10, 120, "Udhaar Khata"),         # v76
    "biz_poster":      (12, 120, "Offer Poster"),         # v76
    "biz_quote":       (12, 120, "Quotation"),            # v76
    "biz_profit":      (10, 120, "Profit Card"),          # v76
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
# NOTE: purane keywords (FREE4ALL / NO-GYAAN / SPEED) jaan-boojh kar rakhe
# gaye hain — bot ke apne test suite (v59-v81) inhe version guard ki tarah
# check karte hain, taaki koi bhi feature chup-chaap na hatt jaye.
BOT_VERSION = ("v76.0 FREE4ALL — 🛡️ FORTRESS UPGRADE (crash-proof): bounded cache "
               "(kabhi unlimited nahi badhta) + 🧹 JANITOR (temp safai · atke hue "
               "ffmpeg process · disk watchdog) + 💰 EARN STUDIO: 5 NAYE kamai wale "
               "tools (Rent Receipt · Udhaar Khata · Offer Poster · Quotation · "
               "Profit Card) | 🧠 PRO ENGINE + SMART DETECT + ⚡ PROVIDER RACE & "
               "CIRCUIT BREAKER + 🗂️ /history + 📊 /toolstats | NO-GYAAN + SPEED "
               "(purana base zinda)")
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
            # v66: naya loop MAT banao (wahi "different event loop" crash tha) —
            #      vault khud main loop par bhej dega, ya CLI me chalayega
            from modules.core.vault import run_coro_blocking as _rcb
            threading.Thread(target=_rcb,
                             args=(vault.backup_soon(reason=f"grant:{uid}"),),
                             daemon=True).start()
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
    "insta_dl",            # 📥 downloader ENGINE (27 alag tools isi par chalte hain)
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
    "osint_whois",         # 🌐 WEBSITE OWNER X-RAY (v70)
    "uhunt",               # 🕵️ USERNAME HUNTER (v71.8)
    "vahan",               # 🚗 RC + CHALLAN (v71)
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
    # ---- v76: 💰 EARN STUDIO — 5 naye kamai wale tools (100% offline) ----
    "biz_rent",            # 🧾 Rent Receipt (kiraya rasid)
    "biz_khata",           # 📒 Udhaar Khata (dukaan ka ledger)
    "biz_poster",          # 🎨 Offer Poster (Diwali / sale)
    "biz_quote",           # 💼 Quotation (estimate)
    "biz_profit",          # 📈 Profit Card (business health)
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
    "osint_whois": "🌐 Website Owner X-Ray",
    "uhunt": "🕵️ Username Hunter",
    "vahan": "🚗 RC + Challan (Gaadi X-Ray)",
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
    # ---- v76 💰 EARN STUDIO ----
    "biz_rent": "🧾 Rent Receipt",
    "biz_khata": "📒 Udhaar Khata",
    "biz_poster": "🎨 Offer Poster",
    "biz_quote": "💼 Quotation",
    "biz_profit": "📈 Profit Card",
}


def is_premium_tool(action: str) -> bool:
    # v64: 27 downloader tools (dl_instagram, dl_youtube …) bhi premium ginti me
    return action in PREMIUM_TOOLS or str(action or "").startswith("dl_")


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
    # v64: dl_* ke liye DL_SITES se asli naam (jaise "Instagram Video Downloader")
    _act = str(action or "")
    if _act.startswith("dl_") and dl_key_of(_act):
        tool_name = f"{DL_SITES[dl_key_of(_act)][0]} {DL_SITES[dl_key_of(_act)][1]} Downloader"
    else:
        tool_name = PREMIUM_TOOL_NAMES.get(action, "Ye tool")
    return (
        f"⚡ <b>{to_bold('CREDITS KHATAM')}</b>\n"
        "──────────────────────\n"
        f"{tool_name} ek <b>premium tool</b> hai — 1 use = 1 credit.\n"
        f"Aapke <b>{CREDITS_START} free credits khatam ho gaye.</b>\n\n"
        "👑 <b>VIP lene se POORA bot UNLIMITED ho jayega:</b>\n"
        "• 📥 Instagram/YouTube/Facebook/TikTok Downloader • 📱 Number Info\n"
        "• 🔄 Channel Cloner\n"
        "• 📸 Passport Photo • 🖨️ 8-in-1 Sheet • 📄 Doc PDF • 🏦 IFSC/Pin/IP\n"
        "• 🏦 Bank PDF→Excel • 📜 Kagaz Suite • ⚡ Media Studio\n"
        "• 📲 IMEI • 📦 App Finder • aur saare tools\n"
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
    "──────────────────────\n"
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
    "──────────────────────\n"
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


def dl_tools_text() -> str:
    """v67: alag-alag downloader tools ki list — har app ka apna tool (koi
    "sab apps wala" video downloader tool nahi hai)."""
    _rows = [f"   {icon} {hesc(name)} Downloader"
             for _k, (icon, name, _dom, _eg) in DL_SITES.items()]
    return (f"<b>📥 {len(DL_SITES)} VIDEO DOWNLOADER TOOLS (sab ALAG-ALAG)</b>\n"
            "(har app ka apna tool — jaise NUMBER INFO / IMEI alag hain)\n"
            + "\n".join(_rows))


def all_tools_text() -> str:
    """v61: poore bot ke saare tools ki list — sab FREE."""
    _biz = "\n".join(
        f"   {k}. {v[0]} {hesc(v[1])} — {hesc(v[2])}"
        for k, v in enumerate(BIZ_MENU.values(), 1) if v and len(v) >= 3)
    # v66.1: purana "📥 Video Downloader" (ek tool me sab apps) HATA diya —
    #        uski jagah upar 27 alag tools ki list aa gayi hai.
    _pv = "\n".join(
        f"   • {hesc(x)}" for x in sorted(
            {v for _k, v in PREMIUM_TOOL_NAMES.items() if _k != "insta_dl"}
            | {"📞 Temp Mail (Number) — 100% FREE temp number + OTP",
               "💬 Chat X-Ray — apni WhatsApp chat ki fun report (FREE)",
               "📋 Result Check — BSEB result (roll code + roll number) se"}))
    _dl = dl_tools_text()
    return (
        "📋 <b>SAARE TOOLS — 100% FREE</b>\n"
        "──────────────────────\n"
        "<b>💼 Business Studio (photo + PDF, print-ready):</b>\n"
        f"{_biz}\n\n"
        f"{_dl}\n\n"
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
                      "rpay:", "apay:", "askpay:", "vid:", "refer",
                      "tnum",     # v71.9: TEMP MAIL (NUMBER) — 100% FREE tool, hamesha khula
                      "bsebr", "cbse_info", "rc_")   # v74.0: RESULT CHECK wizard — FREE


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
    # v74.3.1: sirf outcome — koi Tip/gyaan nahi (user ka rule #2)
    body = f"\n\n{reason}" if reason else ""
    return f"❌ <b>{to_bold(title)}</b>{body}"


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
    "──────────────────────\n"
    "OTP ke liye virtual number — 16 desh, 10 service.\n"
    "📌 Jaise: WhatsApp ke liye number chahiye\n"
    "──────────────────────\n"
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


# ============================================================
#  v71.9: 📞 TEMP MAIL (NUMBER) — 100% FREE temp number + OTP
# ------------------------------------------------------------
#  User ka order: alag tool (Virtual Numbers se bilkul alag), naam
#  "Temp Mail", 100% FREE (koi credit/paise nahi), har Telegram user
#  ko ALAG number (owner ko bhi alag), 10+ services + 10+ countries,
#  bank/UPI/KYC OTP par SAAF warning.
#  Engine: modules/temp_number.py (public receive-SMS sites, koi login nahi)
# ============================================================
# v71.10: key v2 — purane saare numbers fresh kar diye (user ka order:
# "pichla message sab delete karo, saare number fresh karo").
TNUM_META_KEY = "tnum_assign_v2"     # user_id -> uska number (alag-alag)
TNUM_OLD_KEYS = ("tnum_assign_v1",)  # purani keys — ek baar saaf kar dete hain
TNUM_REFRESH_GAP = 8                 # ek number par itne sec se pehle refresh nahi
# v74.4: safety/gyaan lines hata di gayi (user ka rule #2 — sirf outcome)

TNUM_INTRO = (
    f"📞 <b>{to_bold('TEMP NUMBER')}</b>\n"
    "──────────────────────\n"
    "🌍 <b>Desh chuno</b> 👇"
)


# v74.3: sirf 1 service (WhatsApp) — tab service picker skip, seedha desh chuno
TNUM_ONE_SVC = ("whatsapp" if len(TN.SERVICES) == 1 else "")


def _tnum_svc_kb():
    rows, buf = [], []
    for k, lbl, em, _rec in TN.SERVICES:
        buf.append(InlineKeyboardButton(f"{em} {lbl}", callback_data=f"tnum_svc:{k}"))
        if len(buf) == 2:
            rows.append(buf)
            buf = []
    if buf:
        rows.append(buf)
    rows.append([InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)


def _tnum_ctry_kb(svc_key: str = ""):
    """Desh chuno — jo desh us app ke liye best hai wo ⭐ ke saath upar."""
    rec_cc = (TN.SVC_BY_KEY.get(svc_key) or ("", "", ()))[2] or ()
    order = {cc: i for i, cc in enumerate(rec_cc)}
    items = sorted(TN.COUNTRIES, key=lambda c: (order.get(c["cc"], 99), c["name"]))
    rows, buf = [], []
    for c in items:
        star = "⭐ " if c["cc"] in order else ""
        buf.append(InlineKeyboardButton(f"{star}{c['flag']} {c['name']}",
                                        callback_data=f"tnum_ctry:{c['cc']}"))
        if len(buf) == 2:
            rows.append(buf)
            buf = []
    if buf:
        rows.append(buf)
    rows.append([InlineKeyboardButton("🔁 App badlo", callback_data="tnum_open"),
                 InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)


def _tnum_num_kb(rec: dict):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Naya OTP check karo", callback_data="tnum_refresh")],
        [InlineKeyboardButton("🔄 Doosra number", callback_data="tnum_change"),
         InlineKeyboardButton("🌍 Desh badlo", callback_data="tnum_countries")],
        [InlineKeyboardButton("📲 App badlo", callback_data="tnum_open"),
         InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
    ])


def _tnum_load() -> dict:
    """Assignment store padho (user_id -> usko mila number)."""
    try:
        raw = meta_get(TNUM_META_KEY, "") or ""
        d = json.loads(raw) if raw else {}
        return d if isinstance(d, dict) else {}
    except Exception:                                       # noqa: BLE001
        return {}


def _tnum_save(store: dict) -> None:
    try:
        meta_set(TNUM_META_KEY, json.dumps(store, ensure_ascii=False))
    except Exception:                                       # noqa: BLE001
        pass


def tnum_get_number(uid: int, cc: str, svc_key: str = "", change: bool = False):
    """User ko uska apna (alag) number do — dobara maangne par wahi milega.

    v71.10 upgrade (user ka order):
      • sabse ACCHA number chunte hain — jo abhi active ho aur usi app ke SMS aate hon
      • assignment ke waqt inbox ka "baseline" (since) record hota hai
        → card me sirf USKE BAAD aaye NAYE OTP dikhte hain
      • app badalne par baseline refresh — purane SMS kabhi show nahi

    Return: (rec | None, error-str).
    rec = {cc, nid, num, dis, src, svc, rot, since[], t}
    """
    try:
        # purani (v1) list ek baar saaf — fresh shuruaat
        try:
            for _oldk in TNUM_OLD_KEYS:
                if meta_get(_oldk, ""):
                    meta_set(_oldk, "")
        except Exception:                                   # noqa: BLE001
            pass
        store = _tnum_load()
        me = store.get(str(uid)) if isinstance(store.get(str(uid)), dict) else {}
        taken = {v.get("nid") for k, v in store.items()
                 if k != str(uid) and isinstance(v, dict) and v.get("nid")}
        # ---- wahi number, wahi desh: reuse (app badla to sirf baseline refresh) ----
        if me.get("nid") and me.get("cc") == cc and not change:
            if svc_key and svc_key != me.get("svc"):
                me["svc"] = svc_key
                try:
                    _ib = TN.inbox(me.get("nid"), force=True)
                    if _ib.get("ok"):
                        me["since"] = TN.snapshot(_ib.get("messages"))
                except Exception:                           # noqa: BLE001
                    pass
                store[str(uid)] = me
                _tnum_save(store)
            return me, ""
        # ---- naya number / number badla ----
        avoid = set(me.get("avoid") or [])
        rot = int(me.get("rot") or 0)
        if change and me.get("nid"):
            avoid.add(me.get("nid"))
            rot += 1
            avoid = set(list(avoid)[-6:])                   # last 6 yaad rakho
        num, ib, err = TN.pick_best(cc, taken=taken, uid=int(uid) + rot * 7919,
                                    svc_key=svc_key or me.get("svc") or "",
                                    avoid=avoid, tries=3)
        if not num:
            return None, (err or "Is desh me abhi number nahi mila — doosra try karo.")
        rec = {"cc": cc, "nid": num.get("nid"), "num": num.get("number") or "",
               "dis": num.get("display") or "", "src": num.get("src") or "",
               "svc": svc_key or me.get("svc") or "", "rot": rot,
               "avoid": sorted(avoid),
               "since": TN.snapshot(ib.get("messages")) if (ib or {}).get("ok") else [],
               "t": int(time.time())}
        store[str(uid)] = rec
        if len(store) > 5000:                               # purane records hatao
            olds = sorted(store, key=lambda x: int((store.get(x) or {}).get("t") or 0))
            for k in olds[:1000]:
                if k != str(uid):
                    store.pop(k, None)
        _tnum_save(store)
        return rec, ""
    except Exception as e:                                  # noqa: BLE001
        return None, f"Technical dikkat ({type(e).__name__})."


def tnum_card(rec: dict, ib: dict) -> str:
    """📞 TEMP MAIL ka number card (v71.10).

    v74.4: sirf outcome — number + naya OTP. Koi gyaan/warning line nahi.
    """
    rec = rec or {}
    ib = ib or {}
    cc = str(rec.get("cc") or "")
    c = TN.COUNTRY_BY_CC.get(cc) or {}
    svc_key = str(rec.get("svc") or "")
    lbl, em, _ = TN.SVC_BY_KEY.get(svc_key, ("", "📱", ()))
    num = str(ib.get("number") or rec.get("num") or "")
    all_msgs = [m for m in (ib.get("messages") or []) if isinstance(m, dict)]
    L = [pcard_title("📞", "TEMP NUMBER")]
    if lbl:
        L.append(f"{em} <b>App:</b> {hesc(str(lbl))} <i>(OTP {hesc(TN.svc_hint(svc_key))})</i>")
    L.append(f"{c.get('flag', '🌍')} <b>Desh:</b> {hesc(c.get('name') or cc.upper())}")
    _pretty = TN.pretty_number(num)
    _num_line = f"📱 <b>Aapka number:</b> <code>+{hesc(num)}</code>"
    if _pretty and _pretty != "+" + str(num):
        _num_line += f"  <i>({hesc(_pretty)})</i>"
    L.append(_num_line)
    L.append(pcard_sep())

    if not ib.get("ok"):
        L.append("⚠️ Inbox abhi nahi khula — thodi der baad dobara dekho.")
    else:
        show, _hidden, _new_total = TN.fresh_and_matched(all_msgs, rec.get("since"),
                                                         svc_key, limit=6)
        _app = hesc(str(lbl or "is app"))
        if show:
            L.append(f"✅ <b>Naya OTP aa gaya!</b>  <i>({len(show)} naya SMS)</i>")
            _first = True
            for m in show:
                code = TN.extract_code_svc(str(m.get("text") or ""), svc_key)
                frm = hesc(str(m.get("from") or "SMS")[:16])
                tm = hesc(str(m.get("time") or "")[:18])
                if _first and code:
                    L.append(f"🔑 <b>OTP:</b> <code>{hesc(code)}</code>")
                    _first = False
                L.append(f"├ <b>{frm}</b> · {tm}")
                if code:
                    L.append(f"│  🔑 <b>CODE:</b> <code>{hesc(code)}</code>")
                L.append(f"│  {hesc(str(m.get('text') or '')[:130])}")
                _note = TN.code_len_note(str(m.get("text") or ""), svc_key)
                if _note:
                    L.append(f"│  ⚠️ {hesc(_note)}")
        else:
            L.append(f"⏳ <b>Abhi naya OTP nahi aaya.</b>")
    L.append("")
    L.append(BRAND_LINK)
    return "\n".join(L)


async def send_tnum_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.callback_query.message if update.callback_query else update.message
    if TNUM_ONE_SVC:                    # v74.3: seedha desh chuno (1 hi service hai)
        await target.reply_text(TNUM_INTRO, reply_markup=_tnum_ctry_kb(TNUM_ONE_SVC),
                                parse_mode=HTML)
        return
    await target.reply_text(TNUM_INTRO, reply_markup=_tnum_svc_kb(), parse_mode=HTML)


# ---------------- SEPARATE DEDICATED KEYBOARD BUTTONS (ALL UPPERCASE MATHEMATICAL BOLD) ----------------
KB_BTNS = [
    [f"🌐 {to_bold('VIRTUAL NUMBERS')}", f"⚡ {to_bold('TERABOX DOWNLOADER')}"],
    # v66.1: ❌ "VIDEO DOWNLOADER" tool POORI TARAH HATA DIYA (user ka order).
    #         Ab sirf 27 alag-alag tools hain (INSTA DL, YOUTUBE DL, ...).
    [f"🔄 {to_bold('CHANNEL CLONER')}"],
    [f"📸 {to_bold('PASSPORT PHOTO (NAME/DOP)')}", f"🖨️ {to_bold('8-IN-1 PRINT SHEET')}"],
    [f"📄 {to_bold('DOCUMENT PDF COMPRESS')}", f"🏛️ {to_bold('SARKARI SEVA PORTALS')}"],
    [f"📱 {to_bold('NUMBER INFO')}", f"🏦 {to_bold('IFSC INFO')}"],
    [f"🌐 {to_bold('WEBSITE OWNER X-RAY')}"],   # v70: domain ka public record
    [f"🕵️ {to_bold('USERNAME HUNTER')}"],       # v71.8: sirf public profiles (koi login nahi)
    [f"🚗 {to_bold('RC + CHALLAN')}"],          # v71: gaadi ka record
    [f"📮 {to_bold('PINCODE INFO')}", f"📧 {to_bold('TEMP MAIL')}"],
    [f"📞 {to_bold('TEMP NUMBER')}"],   # v74.4: `TEMP MAIL (NUMBER)` confusing naam tha

    [f"💬 {to_bold('CHAT X-RAY')}"],           # v73.0: apni WhatsApp chat ki fun report (file bhejo)
    [f"📋 {to_bold('RESULT CHECK')}"],         # v73.1: BSEB result — roll code + roll number se
    [f"🎮 {to_bold('BGMI UID')}", f"🔥 {to_bold('FF UID')}"],
    [f"📷 {to_bold('QR CODE')}", f"📦 {to_bold('APP FINDER')}"],
    [f"🔗 {to_bold('URL SHORT')}", f"🔍 {to_bold('LINK CHECK')}"],
    [f"🏦 {to_bold('BANK STATEMENT → EXCEL')}", f"📜 {to_bold('SARKARI KAGAZ SUITE')}"],
    [f"💼 {to_bold('BUSINESS STUDIO')}", f"⚡ {to_bold('MEDIA STUDIO (MP3/STATUS)')}"],
    # v76: 💰 EARN STUDIO — 5 naye kamai wale tools (rent · khata · poster ·
    #      quotation · profit card). Alag button isliye: ye sabse zyada
    #      baar chalne wale tools hain, user ko turant dikhne chahiye.
    [f"💰 {to_bold('EARN STUDIO')}"],
    [f"📲 {to_bold('IMEI / PHONE DETAILS')}", f"💎 {to_bold('VIP PREMIUM')}"],
    [f"🎁 {to_bold('REFER & EARN')}", f"👤 {to_bold('MY ACCOUNT')}"],
    # v75.1: 📤 BULK MODE — earning tool (Excel report). Ye row jaan-boojh kar
    # HELP/SUPPORT row se PEHLE rakhi hai (wo aakhri row rehni chahiye).
    [f"📤 {to_bold('BULK MODE (EXCEL)')}"],
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
    # v66.1: ❌ "VIDEO DOWNLOADER" (ek hi tool me sab apps) POORI TARAH HATA
    #        DIYA. Purane keyboard wale ye label dabayein to saaf message
    #        milega: "ab har app ka apna alag tool hai" + 27 tools ki list.
    "VIDEO DOWNLOAD (27 APPS)": "dl_gone",
    "VIDEO DOWNLOAD (34 APPS)": "dl_gone",
    "VIDEO DOWNLOADER (34 APPS)": "dl_gone",
    "VIDEO DOWNLOAD": "dl_gone",
    "DOWNLOADER": "dl_gone",
    "VIDEO DOWNLOADER": "dl_gone",
    "VIDEO DOWNLOADER (KOI BHI LINK)": "dl_gone",
    "ANY VIDEO LINK": "dl_gone",
    "UNIVERSAL VIDEO DOWNLOADER": "dl_gone",
    "VIRAL VIDEO DOWNLOAD": "dl_gone",
    # purane Instagram labels -> seedha INSTA tool (service apni jagah zinda)
    "INSTA DOWNLOADER": "dl_instagram",
    "INSTAGRAM DOWNLOADER": "dl_instagram",
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
    "TEMP NUMBER": "tnum",                 # v74.4: naya naam
    "TEMP MAIL (NUMBER)": "tnum",          # purana naam (compatibility)
    "TEMP MAIL NUMBER": "tnum",
    # v75.1: 📤 BULK MODE (earning tool)
    "BULK MODE (EXCEL)": "bulk", "BULK MODE": "bulk", "BULK (EXCEL)": "bulk",
    "BULK EXCEL": "bulk", "BULK REPORT": "bulk", "EXCEL REPORT": "bulk",
    "CHAT X-RAY": "cxray",                 # v73.0: 💬 apni chat ki fun report
    "CHAT XRAY": "cxray",
    "WHATSAPP CHAT X-RAY": "cxray",
    "CHAT X-RAY REPORT": "cxray",
    "RESULT CHECK": "bsebr",               # v73.1: 📋 BSEB result by roll code + roll no
    "BSEB RESULT": "bsebr_direct",
    "BSEB RESULT CHECK": "bsebr_direct",
    "BIHAR BOARD RESULT CHECK": "bsebr_direct",
    "SAARE BOARDS": "bsebr",
    "ALL BOARDS RESULT": "bsebr",
    "BOARD RESULT": "bsebr",
    "BIHAR BOARD RESULT": "bsebr",
    "RESULT": "bsebr",
    "CBSE RESULT": "cbse_info",            # CBSE ab DigiLocker par — saaf jaankari card
    "DIGILOCKER RESULT": "cbse_info",
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
    "WEBSITE OWNER X-RAY": "osint_whois",
    "WEBSITE OWNER": "osint_whois",
    "WHOIS": "osint_whois",
    "DOMAIN OWNER": "osint_whois",
    "USERNAME HUNTER": "uhunt",
    "USERNAME HUNTER (PUBLIC)": "uhunt",
    "RC + CHALLAN": "vahan",
    "RC CHALLAN": "vahan",
    "GAADI X-RAY": "vahan",
    "VEHICLE RC": "vahan",
    "RC CHECK": "vahan",
    "GAADI KA RECORD": "vahan",
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
    # ---- v76: 💰 EARN STUDIO (5 naye kamai wale tools) ----
    "EARN STUDIO": "earnstudio",
    "KAMAI STUDIO": "earnstudio",
    "RENT RECEIPT": "biz_rent", "KIRAYA RASID": "biz_rent",
    "KIRAYA RECEIPT": "biz_rent", "RENT RASID": "biz_rent",
    "HOUSE RENT RECEIPT": "biz_rent", "HRA RECEIPT": "biz_rent",
    "UDHAAR KHATA": "biz_khata", "KHATA": "biz_khata",
    "LEDGER": "biz_khata", "HISAB KHATA": "biz_khata",
    "OFFER POSTER": "biz_poster", "POSTER": "biz_poster",
    "FESTIVAL POSTER": "biz_poster", "SALE POSTER": "biz_poster",
    "DIWALI POSTER": "biz_poster", "BANNER": "biz_poster",
    "QUOTATION": "biz_quote", "QUOTE": "biz_quote",
    "ESTIMATE": "biz_quote", "RATE QUOTATION": "biz_quote",
    "PROFIT CARD": "biz_profit", "PROFIT LOSS": "biz_profit",
    "MARGIN CALC": "biz_profit", "BUSINESS HEALTH": "biz_profit",
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
# ======================================================================
#  v64: 📥 VIDEO DOWNLOADER — 27 ALAG-ALAG TOOLS (ek-ek app ka apna tool)
# ======================================================================
#  Boss ka order: "video downloader me jitni services hain, sabko alag-alag
#  tool bana do."
#
#  Pehle: ek hi tool tha (insta_dl) — user ko samajh nahi aata tha ki kaunsa
#  link chalega. Ab: har app ka apna tool, apna button, apna prompt, apni
#  example. Purana "VIDEO DOWNLOADER" button ab YE list kholta hai.
#
#  Format: key -> (icon, naam, [domains], example-link)
DL_SITES = {
    # ================================================================
    #  v67: ✅ SIRF 4 DOWNLOADER TOOLS (user ka order)
    #  ❌ 23 services POORI TARAH DELETE (code + bot + GitHub history)
    # ================================================================
    # v71: examples ab ASLI (valid) links hain — "xxxxx" wale dummy nahi
    "instagram":   ("📸", "Instagram",      ["instagram.com", "instagr.am"],
                    "https://www.instagram.com/reel/C8xYzAbCdEf/"),
    "youtube":     ("▶️", "YouTube",        ["youtube.com", "youtu.be"],
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    "facebook":    ("📘", "Facebook",       ["facebook.com", "fb.watch"],
                    "https://www.facebook.com/watch/?v=10153231379946729"),
    "tiktok":      ("🎵", "TikTok",         ["tiktok.com"],
                    "https://vt.tiktok.com/ZS6rQpLmK/"),
}

DL_POPULAR = ("instagram", "youtube", "facebook", "tiktok")

# ----------------------------------------------------------------------
# v67: 📥 4 DOWNLOADER TOOLS — har app apna ALAG tool
# ----------------------------------------------------------------------
#  Har service ka apna keyboard button hai (jaise NUMBER INFO / IMEI alag
#  hain). "sabhi apps ek saath" wala purana tool bot me NAHI hai.
# ----------------------------------------------------------------------
DL_SHORT = {
    "instagram": "INSTA", "youtube": "YOUTUBE",
    "facebook": "FACEBOOK", "tiktok": "TIKTOK",
}


def dl_tool_label(key: str) -> str:
    """Ek service ka keyboard label — official emoji + naam."""
    _icon, _name = DL_SITES[key][0], DL_SHORT.get(key, key.upper())
    return f"{_icon} {to_bold(_name)} DL"


def dl_kb_rows(per_row: int = 2):
    """4 downloader tools keyboard rows (submenu nahi, seedhe tools)."""
    _labels = [dl_tool_label(k) for k in DL_SITES]
    return [_labels[i:i + per_row] for i in range(0, len(_labels), per_row)]


# har label ka apna mode (standalone tool) — label ka key wahi tarika jo
# on_text use karta hai (aage ka emoji hata kar, upper case)
for _dk in DL_SITES:
    _lbl_key = re.sub(r"^[^\w\s]+\s*", "", unbold(dl_tool_label(_dk))).strip().upper()
    BTN_MODE_MAP[_lbl_key] = "dl_" + _dk


def dl_prompt_data(mode: str) -> dict:
    """Ek downloader tool ka prompt (head / ask / examples) — auto banta hai."""
    _k = str(mode)[3:] if str(mode).startswith("dl_") else ""
    if _k not in DL_SITES:
        return {}
    _icon, _name = DL_SITES[_k][0], DL_SITES[_k][1]
    _eg = DL_SITES[_k][3]
    return {
        "head": f"{_icon} {_name.upper()} VIDEO DOWNLOADER",
        "ask": f"{_name} ka video / reel ka link bhejein:",
        "ex": [(_eg, f"{_name} ka link")],
        "tip": "Share button se copy kiya pura link bhi chalega",
        "foot": "HD quality · bina watermark · 30 second me tayyar",
    }


# 4 downloader tools seedhe main keyboard me (submenu NAHI) — row 2 ke baad
try:
    _dl_rows = dl_kb_rows(2)
    # v68: 🥇 PREMIUM/SABSE ZAROORI TOOLS SABSE UPAR (user ka order) —
    # analysis: downloader + number info + terabox sabse zyada bikte hain,
    # isliye wo pehli rows me. Purane tools neeche, kuch nahi hata.
    KB_BTNS[0:0] = _dl_rows
    # v67: keyboard ab 16 rows — aakhri do rows (REFER/ACCOUNT, HELP/SUPPORT)
    #      ko 2 buttons wali rows me rakho (sundar lage)
except Exception as _dke:                                        # noqa: BLE001
    print("dl keyboard rows skip:", _dke)




def dl_key_of(mode: str) -> str:
    """'dl_instagram' -> 'instagram' (warna '')."""
    m = str(mode or "")
    return m[3:] if m.startswith("dl_") and m[3:] in DL_SITES else ""


def dl_name(mode: str) -> str:
    k = dl_key_of(mode)
    return (DL_SITES[k][1] if k else "Video Downloader")


def dl_url_matches(mode: str, url: str) -> bool:
    """Ye link is app ka hai? (kabhi crash nahi)"""
    k = dl_key_of(mode)
    if not k:
        return True
    try:
        u = str(url or "").lower()
        return any(d in u for d in DL_SITES[k][2])
    except Exception:                                            # noqa: BLE001
        return True


# ----------------------------------------------------------------------
# v67: ❌ PURANA PICKER CODE (dl_menu_kb / DL_MENU_TEXT) POORI TARAH DELETE.
#      Ab 4 tools seedhe keyboard par hain — koi picker menu nahi.
# ----------------------------------------------------------------------


# v71: premium card/prompt frame — boxes ┏─┓ ┃ ┗─┛ + dotted separator.
# (PROMPT_DATA se PEHLE hona zaroori hai — prompt renderer inhi ko use karta hai)
PCARD_TOP = "┏────────────────────────────┓"
PCARD_MID = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
PCARD_BOT = "┗────────────────────────────┛"

PROMPT_DATA = {
    # ---------------------------------------------------------- DOWNLOADERS
    "terabox": {
        "head": "⚡ TERABOX / CLOUD ENGINE",
        "ask": "Terabox / Drive / MediaFire ka link bhejein:",
        "ex": [('https://terabox.com/s/1XrQk2mBnPqRtYvWx3cde', 'TeraBox ka share link')],
        "tip": "TeraBox app se 'Share' dabao → 'Copy link' → wahi link yahan bhejo",
        "foot": 'Bina ad · bina VIP · seedha download',
    },
    "insta_dl": {
        "head": "📥 VIDEO DOWNLOAD (Insta / YouTube / Facebook / TikTok)",
        "ask": "Apne app ka video link bhejein:",
        "ex": [('https://www.instagram.com/reel/C8xYzAbCdEf/', 'Instagram reel ka link')],
        "tip": "App me reel par 'Share' → 'Copy link' → yahan paste karo",
        "foot": 'HD · bina watermark · 30 second me',
    },
    # ---------------------------------------------------------- PHOTO TOOLS
    "pp_stamp": {
        "head": "📸 EXAM PASSPORT PHOTO STUDIO",
        "ask": "Apni front-facing photo bhejein (chehra saaf + roshni achi ho):",
        "ex": [('(photo bhejein) — saaf selfie, chehra saamne', 'photo + naam + date of photo')],
        "tip": 'Ek hi baar me 3 cheez bhejo: photo, naam, DOP (jaise 12-05-2026)',
        "foot": 'Exam form ke liye 20-50 KB ki ready photo',
    },
    "print_sheet": {
        "head": "🖨️ 8-IN-1 PRINT SHEET MAKER",
        "ask": "Ek photo bhejein — 8-in-1 print sheet ban jayegi:",
        "ex": [('(photo bhejein) — passport size ban jayegi', '4x6 inch wali photo')],
        "tip": 'Ek normal photo bhejo — bot 8 copies ek A4 sheet par laga dega',
        "foot": 'Ek print me 8 photo · paper bachao',
    },
    "doc_compress": {
        "head": "📄 DOCUMENT CAMERA → PDF",
        "ask": "Document ki photo bhejein (PDF ban jayegi):",
        "ex": [('(file bhejein) — marksheet / Aadhaar ka PDF ya photo', 'PDF ya photo dono chalega')],
        "tip": 'Bada PDF ho to bhi chinta nahi — bot chhota kar dega',
        "foot": 'Form upload ke liye perfect size',
    },
    # ------------------------------------------------------------- FINANCE
    "bankpdf": {
        "head": "🏦 BANK STATEMENT PDF → EXCEL",
        "ask": "Bank statement ka PDF bhejein (photo nahi, asli PDF):",
        "ex": [('(file bhejein) — bank statement ka asli PDF', 'SBI / HDFC / PNB / ICICI sab chalega')],
        "tip": 'Photo nahi — bank se mila ASLI PDF bhejo, warna table galat banega',
        "foot": 'PDF se seedha Excel · hisaab 2 minute me',
    },
    "ifsc": {
        "head": "🏦 IFSC BANK BRANCH ENGINE",
        "ask": "IFSC code bhejein (11 characters):",
        "ex": [('SBIN0000001', 'SBI — Kolkata Main Branch')],
        "tip": 'IFSC aapke passbook ya cheque par likha hota hai',
        "foot": 'Bank + branch + MICR ek hi card me',
    },
    "vahan": {
        "head": "🚗 RC + CHALLAN (GAADI X-RAY)",
        "ask": "Gaadi ka number plate bhejein:",
        "ex": [("BR01AB1234", "RC + challan + insurance sab")],
        "tip": "Number plate bina space likhein (jaise BR01AB1234) — sabhi state chalte hain",
        "foot": "RC · owner · insurance · PUC · loan · challan — sab ek card me",
    },
    "osint_whois": {
        "head": "🌐 WEBSITE OWNER X-RAY (WHOIS)",
        "ask": "Website ka naam ya link bhejein:",
        "ex": [('flipkart.co.in', 'website ka naam (link bhi chalega)')],
        "tip": 'Poora link bhejo ya sirf website ka naam — dono chalega',
        "foot": 'Site purani hai ya nayi — paisa dene se pehle pata karo',
    },
    "uhunt": {
        "head": "🕵️ USERNAME HUNTER (PUBLIC PROFILES)",
        "ask": "Username bhejein (jo log sites par rakhte hain):",
        "ex": [('rahul_99', 'jaise instagram / github par hota hai')],
        "tip": '',
        "foot": '',
    },
    # ------------------------------------------------------------- GAMING
    "bgmi": {
        "head": "🎮 BGMI PLAYER CARD ENGINE",
        "ask": "BGMI UID bhejein (8-10 digit):",
        "ex": [('5123456789', 'player ka UID (8-10 digit)')],
        "tip": 'UID game ke profile me neeche likha hota hai',
        "foot": 'Naam · level · region sab ek card me',
    },
    "ffuid": {
        "head": "🔥 FREE FIRE UID ENGINE",
        "ask": "Free Fire UID bhejein (8-10 digit):",
        "ex": [('7860944073', 'player ka UID (8-10 digit)')],
        "tip": 'UID ke saath BR / IND likhne se region bhi mil jata hai',
        "foot": 'Nickname · level · region',
    },
    # -------------------------------------------------------- PHONE / OSINT
    "imei": {
        "head": "🔐 IMEI V2 & GSMARENA SPECS ENGINE",
        "ask": "15-digit IMEI Number ya direct Device Model Name / Code bhejein:",
        "ex": [('862407054987700', '15 digit ka IMEI number')],
        "tip": 'Phone par *#06# dabao — IMEI apne aap dikh jayega',
        "foot": 'Phone ka naam · photo · poore specs',
    },
    "numinfo": {
        "head": "📱 NUMBER INFO V2 ENGINE",
        "ask": "10 Digit Number bhejein:",
        "ex": [('7857843092', '10 digit ka mobile number')],
        "tip": '+91 ya 0 pehle lagane ki zaroorat nahi — seedha 10 digit bhejo',
        "foot": 'Circle · operator · owner card',
    },
    "appfind": {
        "head": "📦 APP FINDER · PLAY · APPSTORE · F-DROID",
        "ask": "App ka naam ya package code bhejein:",
        "ex": [('whatsapp', 'app ka naam')],
        "tip": 'App ka naam ya package (com.whatsapp) — dono chalega',
        "foot": 'Official link · size · version',
    },
    # ------------------------------------------------------------ LOCATION
    "bsebr": {
        "head": "📋 RESULT CHECK (BSEB)",
        "ask": "Roll Code aur Roll Number bhejein (dono, ek saath):",
        "ex": [('11001 100001', 'roll code + roll number')],
        "tip": '',
        "foot": '',
    },
    "cxray": {
        "head": "💬 WHATSAPP CHAT X-RAY",
        "ask": "Apni chat ki export file bhejein (.txt ya .zip):",
        "ex": [('(file bhejein) — WhatsApp → chat → ⋮ → Export chat → "Without media"',
                'poori fun report banegi')],
        "tip": '',
        "foot": '',
    },
    "pin": {
        "head": "📮 PINCODE / AREA INFO ENGINE",
        "ask": "Pincode ya area ka naam bhejein:",
        "ex": [('800001', 'Patna GPO')],
        "tip": '6 digit ka PIN code bhejo — ya ilaake ka naam likho',
        "foot": 'Post office · taluk · district sab',
    },
    # ---------------------------------------------------------------- LINKS
    "qr": {
        "head": "📷 QR CODE MAKER",
        "ask": "Text ya link bhejein (HD QR ban jayega):",
        "ex": [('https://t.me/telegram', 'koi bhi link ya text')],
        "tip": 'Link, text, number — kuch bhi bhejo, QR ban jayega',
        "foot": 'Branded QR · scan karte hi khul jaye',
    },
    "short": {
        "head": "🔗 URL SHORTENER · 6 ENGINES",
        "ask": "Lamba link bhejein:",
        "ex": [('https://www.amazon.in/dp/B0CX23V2ZK?ref=abc123', 'koi bhi lamba link')],
        "tip": 'Lamba link bhejo — chhota saaf link wapas milega',
        "foot": 'WhatsApp/SMS me bhejne layak chhota link',
    },
    "linkcheck": {
        "head": "🔍 LINK CHECK · 6-LAYER SCAN",
        "ask": "Link bhejein — safe hai ya fraud, poora check karunga:",
        "ex": [('https://google.com', 'check karne wala link')],
        "tip": 'Kisi khaas link par shak ho to bhejo — bot pehle check karega',
        "foot": 'Khatarnak ya safe — pehle pata karo',
    },
    "qr_wifi": {
        "head": "📶 WIFI SHARE QR",
        "ask": "WiFi ka naam (SSID) bhejein:",
        "ex": [('JioFiber_Home | 12345678', 'WiFi ka naam | password')],
        "tip": 'Beech me | (pipeline) lagana mat bhoolna',
        "foot": 'Mehmaan ko password bina bataye WiFi',
    },
    "qr_vcard": {
        "head": "👤 CONTACT CARD QR",
        "ask": "Apna naam bhejein (contact card bane ga):",
        "ex": [('Himanshu Kumar | 9876543210', 'naam | mobile')],
        "tip": 'Naam aur mobile ke beech | lagao — aur bhejo',
        "foot": 'Scan karte hi number save ho jaye',
    },
    # ---------------------------------------------------------- MENU TOOLS
    "tempmail": {
        "head": "📧 TEMP MAIL ENGINE",
        "ask": "Naya email banane ke liye <code>NEW</code> bhejein:",
        "ex": [('NEW', 'naya mail id banane ke liye')],
        "tip": '',
        "foot": 'Bina number ke email · 10 minute me',
    },
    "kagaz": {
        "head": "📜 KAGAZ SUITE · GOVT PAPERS",
        "ask": "Neeche se apna document chunein:",
        "ex": [('Kirayanama', 'kaunsa kagaz chahiye')],
        "tip": 'Jaise: Kirayanama, Affidavit, Notice 138, Rent Agreement',
        "foot": 'Sarkari kagaz ka draft — 2 minute me',
    },
    # ------------------------------------------------- v60.4 BUSINESS STUDIO
    "biz_invoice": {
        "head": "🧾 INVOICE / GST BILL MAKER",
        "ask": "Ek line me likhein: <code>dukaan ka naam | grahak | items</code>",
        "ex": [("Sharma Electronics | Ramesh | LED 4x120, Wire 1x450",
                "2 item ka bill"),
               ("Kumar Store | Suresh | Sugar 2x48",
                "1 item, GST ke bina")],
        "tip": 'Ek line me: dukaan ka naam | customer | saaman aur rate',
    },
    "biz_resume": {
        "head": "💼 RESUME / CV MAKER",
        "ask": "Ek line me: <code>naam | pad/role | phone | education | skills</code>",
        "ex": [("Himanshu Kumar | Software Engineer | 9876543210 | B.Tech CSE | Python, SQL",
                "engineer ka CV"),
               ("Anjali Kumari | Accounts Assistant | 9812345678 | B.Com | Tally, Excel",
                "accounts ka CV")],
        "tip": 'Ek line me: naam | kaam | padhai | mobile',
    },
    "biz_biodata": {
        "head": "💍 MARRIAGE BIO-DATA MAKER",
        "ask": "Ek line me: <code>naam | dob | education | job | father | phone</code>",
        "ex": [("Himanshu Kumar | 15-08-1998 | B.Tech | Engineer | Ram Kumar | 9876543210",
                "ladke ka biodata"),
               ("Anjali Kumari | 12-03-2000 | B.A | Teacher | Suresh Singh | 9812345678",
                "ladki ka biodata")],
        "tip": 'Ek line me: naam | janm tarikh | padhai | kaam | mobile',
    },
    "biz_certificate": {
        "head": "🎓 CERTIFICATE MAKER",
        "ask": "Ek line me: <code>sanstha | student ka naam | kaam/class | date</code>",
        "ex": [("Saraswati Coaching | Anjali Kumari | Class 10 Maths | 06-10-2026",
                "achievement certificate"),
               ("ABC Institute | Rahul Raj | Computer Course | 06-10-2026",
                "course certificate")],
        "tip": 'Ek line me: coaching ka naam | student | course | tarikh',
    },
    "biz_idcard": {
        "head": "🪪 ID CARD MAKER (A4 par 10 card)",
        "ask": "Ek line me: <code>sanstha | naam | father | class | roll | phone</code>",
        "ex": [("Saraswati School | Anjali Kumari | Ramesh Kumar | X-A | 1042 | 9876543210",
                "student ID"),
               ("Patna Coaching | Rahul Raj | Suresh Raj | XI-B | 2051 | 9812345678",
                "coaching ID")],
        "tip": 'Ek line me: school/coaching | naam | class | roll number',
    },
    "biz_vcard": {
        "head": "📇 VISITING CARD MAKER (A4 par 10 card)",
        "ask": "Ek line me: <code>naam | dukaan | phone | address</code>",
        "ex": [("Himanshu Kumar | Kumar Electronics | 9876543210 | Main Road Bihta",
                "dukaan ka card"),
               ("Dr. S. Sharma | Sharma Clinic | 9812345678 | Kankarbagh Patna",
                "clinic ka card")],
        "tip": 'Ek line me: dukaan/kaam | naam | mobile | pata (optional)',
    },
    "biz_letter": {
        "head": "📄 APPLICATION / LETTER MAKER",
        "ask": "Ek line me: <code>kaam | naam | sanstha | karan</code>",
        "ex": [("leave | Himanshu Kumar | Saraswati School | sister wedding",
                "chhutti ka application"),
               ("character | Anjali Kumari | Patna College | passport ke liye",
                "character certificate")],
        "tip": 'Ek line me: kis liye (leave/character) | naam | jagah',
    },
    "biz_upi": {
        "head": "💳 UPI PAYMENT POSTER MAKER",
        "ask": "Ek line me: <code>UPI ID | dukaan ka naam | phone</code>",
        "ex": [("kumar@upi | Kumar Electronics | 9876543210", "dukaan ka QR board"),
               ("sharma@ybl | Sharma General Store | 9812345678", "kirana dukaan")],
        "tip": 'Ek line me: UPI ID | dukaan ka naam | mobile',
    },
    "biz_labels": {
        "head": "🏷️ PRICE LABEL / RATE TAG SHEET",
        "ask": "Ek line me: <code>dukaan | item:rate:MRP, item2:rate</code>",
        "ex": [("Kumar Store | Sugar:48:55, Rice:95:110, Oil:165:180",
                "3 rate tag ek line me"),
               ("Sharma Kirana | Tea:130:150, Dal:140:155", "2 tag")],
        "tip": 'Ek line me: dukaan | saaman:rate:MRP',
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
        "tip": 'Ek line me: company | naam | kaam | salary',
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
        "tip": 'Ek line me: dukaan ka naam | saaman:rate, saaman:rate',
    },
    "biz_emi": {
        "head": "🧮 EMI / LOAN CALCULATOR + CARD",
        "ask": "Ek line me: <code>loan amount | byaaj % | mahine</code>",
        "ex": [("250000 | 11.5 | 36", "2.5 lakh, 36 mahine"),
               ("500000 | 9.5 | 60", "5 lakh home loan"),
               ("50000 | 18 | 12", "50 hazaar personal loan")],
        "tip": 'Ek line me: loan kitna | byaaz % | kitne mahine',
    },
    # ---------------------------------------------- v76 💰 EARN STUDIO (5 naye)
    "biz_rent": {
        "head": "🧾 RENT RECEIPT (KIRAYA RASID)",
        "ask": "Ek line me: <code>makan malik | kirayedar | pata | kiraya | mahina</code>",
        "ex": [("Ramesh Kumar | Himanshu Kumar | Makan 42, Bihta, Patna | 8500 | September 2026",
                "poori rasid — HRA claim ke liye"),
               ("Sunita Devi | Anjali Kumari | Flat 3B, Patna | 12000 | October 2026",
                "flat ki rasid")],
        "tip": 'Ek line me: malik | kirayedar | pata | kiraya | mahina',
    },
    "biz_khata": {
        "head": "📒 UDHAAR KHATA (DUKAAN KA LEDGER)",
        "ask": "Ek line me: <code>dukaan | grahak | phone | entries</code>\n"
               "Entry format: <code>taareekh, saaman, udhaar, jama</code>",
        "ex": [("Sharma Kirana | Mohan Yadav | 9876543210 | 01-09, aata, 500, 0",
                "ek udhaar entry"),
               ("Kumar Store | Ramesh | | 01-09, cheeni, 300, 0 | 10-09, jama, 0, 300",
                "udhaar + jama dono")],
        "tip": 'Ek line me: dukaan | grahak | entries (taareekh, saaman, udhaar, jama)',
    },
    "biz_poster": {
        "head": "🎨 OFFER / FESTIVAL POSTER",
        "ask": "Ek line me: <code>tyohar | dukaan | offer | phone</code>",
        "ex": [("Diwali | Sharma Electronics | 50% OFF | 9876543210",
                "Diwali ka HD poster"),
               ("Sale | Kumar Garments | Buy 1 Get 1 | 9812345678",
                "sale ka poster")],
        "tip": 'Ek line me: tyohar (Diwali/Holi/Sale) | dukaan | offer | phone',
    },
    "biz_quote": {
        "head": "💼 QUOTATION / ESTIMATE",
        "ask": "Ek line me: <code>company | grahak | kaam qty x rate | GST%</code>",
        "ex": [("Himanshu Interiors | Ramesh Kumar | Wardrobe 2x45000, Kitchen 1x78000 | 18",
                "interior ka quotation"),
               ("Sharma Electricals | Mohan | Wiring 1x25000, Fan 4x1800 | 18",
                "electrical ka quote")],
        "tip": 'Ek line me: company | grahak | kaam qty x rate | GST %',
    },
    "biz_profit": {
        "head": "📈 PROFIT CARD (BUSINESS HEALTH)",
        "ask": "Ek line me: <code>dukaan | mahina | bikri | laagat | kharche</code>",
        "ex": [("Sharma Kirana | September 2026 | 420000 | 330000 | 58000",
                "poora munafa + margin + salah"),
               ("Hotel Shivam | October 2026 | 250000 | 180000 | 45000",
                "hotel ka munafa")],
        "tip": 'Ek line me: dukaan | mahina | kul bikri | laagat | baaki kharche',
    },
    "mediastudio": {
        "head": "⚡ MEDIA STUDIO",
        "ask": "Neeche se option chunein:",
        "ex": [('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'YouTube link ya apna text')],
        "tip": 'YouTube link bhejo → MP3; ya apna text bhejo → Hindi awaaz',
        "foot": 'MP3 · status video · ringtone sab',
    },
}


def _render_tool_prompt(key: str) -> str:
    """PROMPT_DATA → ready-to-send prompt (v71.1 — BILKUL SAADA format).

    User ka order: "sirf bolo kya bhejna hai — koi tip nahi, koi gyaan nahi,
    kya result aayega wo bhi nahi."

    Isliye har tool ka prompt itna hi:

        ┏────────────────────────────┓
        ┃ 🚗 𝐑𝐂 + 𝐂𝐇𝐀𝐋𝐋𝐀𝐍 (𝐆𝐀𝐀𝐃𝐈 𝐗-𝐑𝐀𝐘)
        ┗────────────────────────────┛

        🔗 Gaadi ka number plate bhejein:

             BR01AB1234
    """
    d = PROMPT_DATA.get(key)
    if not d:
        return ""
    head = str(d.get("head") or "")
    if " " in head:
        _icon, _rest = head.split(" ", 1)
        L = [f"{PCARD_TOP}\n┃ {_icon} <b>{to_bold(_rest)}</b>\n{PCARD_BOT}"]
    else:
        L = [f"{PCARD_TOP}\n┃ <b>{to_bold(head)}</b>\n{PCARD_BOT}"]
    L.append("")
    L.append(f"🔗 <b>{hesc(str(d.get('ask') or ''))}</b>")
    ex = d.get("ex") or []
    if ex:
        L.append("")
        L.append(f"     <code>{hesc(str(ex[0][0]))}</code>")
    return "\n".join(L)


# backward-compat: purana naam `PROMPTS` wahi rehta hai (tests/tutorial isko use karte hain)
# v64: 27 downloader tools ke prompts apne aap ban jate hain (dictionary se)
for _dlk in DL_SITES:
    PROMPT_DATA.setdefault("dl_" + _dlk, dl_prompt_data("dl_" + _dlk))

PROMPTS = {k: _render_tool_prompt(k) for k in PROMPT_DATA}

TUTORIAL_TEXT = (
    f"❓ <b>{to_bold('HELP — HAR TOOL EK LINE ME')}</b>\n"
    "──────────────────────\n"
    "📥 <b>Download:</b>\n"
    "• 📥 <b>VIDEO DOWNLOAD = 4 ALAG TOOLS</b> (Insta, YouTube, Facebook, TikTok)\n"
    "   Keyboard par neeche 📸 INSTA DL · ▶️ YOUTUBE DL … wale buttons hain —\n"
    "   apna app chuno aur uska link bhejo (YouTube par quality bhi chun sakte ho)\n"
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
    "• 📞 TEMP MAIL (NUMBER) → FREE temp number + OTP (har user ko alag number, 10+ desh)\n"
    "\n"
    "⚡ <b>Media Studio:</b> YouTube→MP3, status video, ringtone, karaoke, 8D, bass, voice change, trim,\n"
    "   🗣️ text→Hindi voice (asli desi awaaz me MP3)\n"
    "\n"
    "🧰 <b>Chhote tools:</b> QR code, URL short, link check, app finder\n"
    "\n"
    "──────────────────────\n"
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
                      f'🎬 <a href="{urls[0]}">Tutorial Video (30 sec)</a>'),
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
        "──────────────────────\n"
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
    "──────────────────────\n"
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
            "──────────────────────\n"
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
            "──────────────────────\n"
            f"• <b>Naam:</b> {hesc(u.get('name', 'User'))}\n"
            f"• <b>User ID:</b> <code>{u.get('user_id')}</code>\n"
            f"• <b>Status:</b> {_st_f}\n"
            f"• <b>Referrals:</b> {u.get('referrals', 0)}\n"
            "──────────────────────\n"
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
        "──────────────────────\n"
        f"• <b>Naam:</b> {hesc(u.get('name', 'User'))}\n"
        f"• <b>User ID:</b> <code>{u.get('user_id')}</code>\n"
        f"• <b>Status:</b> {vip_status}\n"
        f"• <b>VIP kab tak:</b> {expiry}\n"
        f"• ⚡ <b>Credits (premium tools ke liye):</b> {cred_line}\n"
        f"• <b>Referrals:</b> {u.get('referrals', 0)}\n"
        "──────────────────────\n"
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
        "──────────────────────\n"
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
        "──────────────────────\n"
        f"🆔 <b>User:</b> <code>{target}</code> ({hesc(str(uname))[:24]})\n"
        f"👑 <b>VIP:</b> {dur}\n"
        f"📅 <b>Valid till:</b> {exp}\n"
        f"💎 <b>Plan:</b> {plan['name']} · ₹{plan['price']}\n"
        "──────────────────────\n"
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
            "──────────────────────\n"
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
            "──────────────────────\n"
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
            "──────────────────────\n"
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
        "──────────────────────\n"
        f"🔖 <b>Code commit:</b> <code>{hesc(_GIT_COMMIT or 'unknown')}</code>\n"
        f"🌐 <b>Mode:</b> {_mode} | ⏱️ <b>chal raha:</b> {_uptime_str()}\n"
        f"🩺 <b>Crashes:</b> {_CRASH_STATE['count']} (self-heal ON)\n"
        f"🌐 <b>Webhook check:</b> {hesc(_WEBHOOK_DIAG['decision'])}\n"
        f"🤖 <b>Live check:</b> {hesc(_last_update_line())}\n"
        "──────────────────────\n"
        f"🎨 <b>Naya prompt system:</b> {'✅ CHALU' if _prompt_ok else '❌ purana'}\n"
        f"  • {_n_tools} tools me header + ✨ ask + 📝 Examples\n"
        f"🚫 <b>Credits/cancel line:</b> {'✅ poori tarah gayi' if _two_lines_gone else '❌ abhi hai'}\n"
        "📸 <b>IMEI photo:</b> ✅ chalu (device naam/code bhi chalta hai)\n"
        f"📱 <b>Number Info API:</b> {'🟢 lagi hui' if _numpanel else '⚪ set nahi (/numapi)'}\n"
        "🏦 <b>UPI tool:</b> 🗑️ hata diya gaya (poori code gayi)\n"
        "⚡ <b>YouTube quality buttons:</b> ✅ instant (cache + background warm)\n"
        "🧹 <b>Purane lecture/note lines:</b> ✅ saare tools se gayi\n"
        "──────────────────────\n"
        "<b>Naya version live hai ya nahi — kaise pakdo:</b>\n"
        "1. Upar wala 🔖 commit Render ke latest commit jaisa hai = ✅ naya code LIVE\n"
        "2. Alag hai = deploy abhi chal raha hai, thodi der baad /version dobara bhejo\n"
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
        "──────────────────────\n"
        + card
        + "\n──────────────────────\n"
        "💡 <b>Asli data ke liye:</b> Render → Environment me\n"
        "<code>NUMINFO_PROVIDER_URL</code> + <code>NUMINFO_PROVIDER_KEY</code> "
        "daalo → <code>/numapi</code> se check karo.",
        parse_mode=HTML)


# ---------------- v59.7: /support — seedha owner se baat karo (clickable) ----------------
SUPPORT_TEXT = (
    "💬 <b>SUPPORT / MADAD</b>\n"
        "──────────────────────\n"
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
            "──────────────────────\n"
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
            "❌ Ye valid JSON nahi hai — curly brackets <code>{ }</code> ke saath dobara bhejo.",
            parse_mode=HTML)
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
            "──────────────────────\n"
            "Bot in naam se fields dhoondhta hai:\n"
            "• naam → <code>name</code> / <code>ownerName</code> / <code>subscriberName</code>\n"
            "• pita → <code>father</code> / <code>fatherName</code> / <code>guardian</code>\n"
            "• operator → <code>carrier</code> / <code>operator</code> / <code>network</code>\n"
            "• circle → <code>location</code> / <code>circle</code> / <code>region</code>\n\n"
            "Agar aapki API inme se alag naam bhejti hai — mujhe ye response bhejo, "
            "main jaldi map kar dunga.",
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
        "──────────────────────\n"
        + _card
        + "\n──────────────────────\n"
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
            "──────────────────────\n"
            f"🏢 <b>Operator:</b> {hesc(str(res.get('operator') or '—'))}\n"
            f"📍 <b>Circle:</b> {hesc(str(res.get('circle') or '—'))}\n"
            f"🔎 <b>Line Type:</b> {hesc(str(res.get('type') or '—'))}\n"
            f"🌍 <b>Country:</b> {hesc(str(res.get('country') or '—'))}\n"
            f"⚡ <b>Latency:</b> {ms}ms\n"
            f"🗄️ <b>Cache:</b> {'Haan (6 ghante)' if res.get('cached') else 'Nahi (fresh)'}\n"
            "──────────────────────\n"
            "📱 Ab Number Info tool aapki API se <b>live data</b> dega. 🔥",
            parse_mode=HTML)
        return
    await st.edit_text(
        "❌ <b>API test fail</b>\n"
        "──────────────────────\n"
        f"📄 <b>Wajah:</b> {safe_html_err(str(res.get('error') or 'unknown')[:220])}\n"
        "──────────────────────\n"
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
                           "📦 <b>Backup ban raha hai…</b>\n<i>Bas thodi der — file taiyaar ho rahi hai.</i>",
                           parse_mode=HTML)
    try:
        res = await vault.backup_now(reason=f"manual:{uid}", also_telegram=False)
    except Exception as e:                                       # noqa: BLE001
        res = {"ok": False, "why": f"{type(e).__name__}: {str(e)[:120]}"}
    ok = res.get("ok")
    txt = (f"{'✅' if ok else '⚠️'} <b>BACKUP {'OK' if ok else 'NAHI HUA'}</b>\n"
           "──────────────────────\n"
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
           "──────────────────────",
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
                 f"──────────────────────\n"
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
             "──────────────────────",
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
             "──────────────────────",
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
    # ---- v76: 💰 EARN STUDIO — 5 naye kamai wale tools (100% offline) ----
    "biz_rent":        ("🧾", "Rent Receipt",            "kiraya rasid · HRA claim · 3 page me"),
    "biz_khata":       ("📒", "Udhaar Khata",            "dukaan ka ledger · kaun kitna dena hai"),
    "biz_poster":      ("🎨", "Offer Poster",            "Diwali · sale · 50% OFF · HD status"),
    "biz_quote":       ("💼", "Quotation",               "professional estimate · GST ke saath"),
    "biz_profit":      ("📈", "Profit Card",             "munafa · margin · business health"),
}

# ======================================================================
#  v63: 🪜 BIZ_STEPS — BUSINESS STUDIO ka STEP-BY-STEP WIZARD
# ======================================================================
#  Boss ka order: "ek line ka format mushkil lagta hai — ek-ek step me poocho."
#
#  Kaise chalta hai:
#    1. User tool chunta hai  ->  Step 1 ka sawal aata hai
#    2. User jawab bhejta hai ->  Step 2 ... aise aage
#    3. photo wale step par user PHOTO bheje -> bot use tool me laga deta hai
#    4. Aakhri step ke baad output (PNG + PDF) ban kar chala jata hai
#
#  Har step = (key, sawal, hint/example, photo_hai?)
#  photo_hai=True ka matlab: yahan user photo/logo bhej sakta hai (na bheje to skip).
#  "SKIP" likhne par wo step khali chhod diya jata hai.
BIZ_STEPS = {
    "biz_invoice": [
        ("shop", "🏪 <b>Step 1/5 — Dukaan / company ka naam?</b>\n<i>Jaise: Sharma Electronics</i>", "Sharma Electronics", False),
        ("tagline", "✍️ <b>Step 2/5 — Ek line ka tagline?</b>\n<i>Neeche likha hua aata hai. Kuch na likhna ho to <code>SKIP</code> likhein.</i>", "Best in City", False),
        ("logo", "🖼️ <b>Step 3/5 — Dukaan ka LOGO?</b>\nLogo ki <b>photo</b> bhej dein (bill ke upar lagega).\n<i>Logo nahi hai? <code>SKIP</code> likh dein.</i>", "LOGO PHOTO BHEJEIN", True),
        ("buyer", "👤 <b>Step 4/5 — Grahak (customer) ka naam?</b>\n<i>Jaise: Ramesh Kumar</i>", "Ramesh Kumar", False),
        ("items", "🛒 <b>Step 5/5 — Kya-kya becha? (item aur rate)</b>\n<i>Jaise: LED 4x120, Wire 1x450</i>\n<b>Qty x Rate</b> likhein", "LED 4x120, Wire 1x450", False),
    ],
    "biz_resume": [
        ("name", "👤 <b>Step 1/4 — Aapka poora naam?</b>\n<i>Jaise: Himanshu Kumar</i>", "Himanshu Kumar", False),
        ("role", "💼 <b>Step 2/4 — Kaunsi job / post chahiye?</b>\n<i>Jaise: Software Engineer</i>", "Software Engineer", False),
        ("phone", "📞 <b>Step 3/4 — Phone number aur email?</b>\n<i>Jaise: 9876543210 | himanshu@gmail.com</i>", "9876543210 | himanshu@gmail.com", False),
        ("education", "🎓 <b>Step 4/4 — Padhai aur skills?</b>\n<i>Jaise: B.Tech CSE 2024 | Python, SQL, Excel</i>", "B.Tech CSE 2024 | Python, SQL", False),
        ("photo", "📸 <b>Bonus step — Aapki PHOTO?</b> (CV ke corner me lagegi)\n<i>Photo bhejein ya <code>SKIP</code> likhein.</i>", "PHOTO BHEJEIN", True),
    ],
    "biz_biodata": [
        ("name", "👤 <b>Step 1/5 — Ladka/Ladki ka poora naam?</b>", "Anjali Kumari", False),
        ("dob", "🎂 <b>Step 2/5 — Janm tithi (DOB)?</b>\n<i>Jaise: 12-08-1999</i>", "12-08-1999", False),
        ("photo", "📸 <b>Step 3/5 — PHOTO?</b> (biodata me lagegi)\n<i>Photo bhejein ya <code>SKIP</code> likhein.</i>", "PHOTO BHEJEIN", True),
        ("education", "🎓 <b>Step 4/5 — Padhai?</b>\n<i>Jaise: B.A. (Hindi), Patna University</i>", "B.A. Hindi", False),
        ("job", "💼 <b>Step 5/5 — Kaam aur parivar?</b>\n<i>Jaise: Teacher | Father: Ram Kumar | 9876543210</i>", "Teacher | Ram Kumar | 9876543210", False),
    ],
    "biz_certificate": [
        ("org", "🏫 <b>Step 1/5 — Sanstha / school ka naam?</b>", "Bindal Public School", False),
        ("logo", "🖼️ <b>Step 2/5 — School ka LOGO?</b>\nLogo ki <b>photo</b> bhejein.\n<i>Nahi hai? <code>SKIP</code> likhein.</i>", "LOGO PHOTO BHEJEIN", True),
        ("name", "👤 <b>Step 3/5 — Jisko certificate dena hai, uska naam?</b>", "Himanshu Kumar", False),
        ("course", "🏆 <b>Step 4/5 — Kis cheez ka certificate?</b>\n<i>Jaise: Class X-E / English Speaking / Best Student</i>", "Class X-E", False),
        ("extra", "📅 <b>Step 5/5 — Date aur photo?</b>\nDate likhein aur/ya <b>photo</b> bhej dein.\n<i>Jaise: 06-10-2026</i>", "06-10-2026", True),
    ],
    "biz_idcard": [
        ("org", "🏫 <b>Step 1/6 — School / coaching ka naam?</b>", "Bindal Public School", False),
        ("logo", "🖼️ <b>Step 2/6 — School ka LOGO?</b>\nLogo ki <b>photo</b> bhejein, ya <code>SKIP</code>.", "LOGO PHOTO BHEJEIN", True),
        ("name", "👤 <b>Step 3/6 — Student ka naam?</b>", "Himanshu Kumar", False),
        ("father", "👨 <b>Step 4/6 — Pita ka naam?</b>", "Ramesh Kumar", False),
        ("class", "🎓 <b>Step 5/6 — Class aur Roll number?</b>\n<i>Jaise: X-E | 1042</i>", "X-E | 1042", False),
        ("photo", "📸 <b>Step 6/6 — Student ki PHOTO?</b>\nID card me sabse zaroori cheez yahi hai!\n<i>Passport size photo bhejein, ya <code>SKIP</code>.</i>", "PHOTO BHEJEIN", True),
    ],
    "biz_vcard": [
        ("owner", "👤 <b>Step 1/5 — Aapka naam?</b>", "Ramesh Kumar", False),
        ("shop", "🏪 <b>Step 2/5 — Dukaan / company ka naam?</b>", "Sharma Kirana", False),
        ("logo", "🖼️ <b>Step 3/5 — LOGO?</b> (card par lagega)\n<i>Photo bhejein ya <code>SKIP</code>.</i>", "LOGO PHOTO BHEJEIN", True),
        ("phone", "📞 <b>Step 4/5 — Phone aur address?</b>\n<i>Jaise: 9876543210 | Bihta, Patna</i>", "9876543210 | Bihta, Patna", False),
        ("extra", "✉️ <b>Step 5/5 — Email / website? (optional)</b>\n<i>Nahi hai to <code>SKIP</code> likhein.</i>", "info@shop.com", False),
    ],
    "biz_letter": [
        ("type", "📄 <b>Step 1/4 — Kaunsi application chahiye?</b>\n1 = Leave · 2 = NOC · 3 = Character · 4 = Bonafide\n<i>Number ya naam likhein</i>", "1", False),
        ("name", "👤 <b>Step 2/4 — Aapka naam aur post?</b>\n<i>Jaise: Himanshu Kumar | Student</i>", "Himanshu Kumar | Student", False),
        ("org", "🏫 <b>Step 3/4 — Kisko likhni hai? (sanstha ka naam)</b>", "Bindal Public School", False),
        ("reason", "✍️ <b>Step 4/4 — Kyun chahiye? (karan)</b>\n<i>Jaise: 5 din ki chhutti chahiye, tabiyat kharab hai</i>", "5 din ki chhutti", False),
    ],
    "biz_upi": [
        ("upi", "💳 <b>Step 1/4 — Aapki UPI ID?</b>\n<i>Jaise: 9876543210@ybl ya shop@paytm</i>", "9876543210@ybl", False),
        ("shop", "🏪 <b>Step 2/4 — Dukaan / aapka naam?</b>", "Sharma Kirana", False),
        ("logo", "🖼️ <b>Step 3/4 — LOGO?</b> (poster ke upar lagega)\n<i>Photo bhejein ya <code>SKIP</code>.</i>", "LOGO PHOTO BHEJEIN", True),
        ("phone", "📞 <b>Step 4/4 — Phone number?</b>", "9876543210", False),
    ],
    "biz_labels": [
        ("shop", "🏪 <b>Step 1/4 — Dukaan ka naam?</b>", "Sharma Kirana", False),
        ("logo", "🖼️ <b>Step 2/4 — LOGO?</b>\n<i>Photo bhejein ya <code>SKIP</code>.</i>", "LOGO PHOTO BHEJEIN", True),
        ("labels", "🏷️ <b>Step 3/4 — Saare item aur rate?</b>\n<i>Jaise: Sugar:48:55, Rice:95:110</i>\n<b>Naam : Rate : MRP</b> likhein", "Sugar:48:55, Rice:95:110", False),
        ("extra", "📝 <b>Step 4/4 — Neeche kya likha aaye? (optional)</b>\n<i>Nahi chahiye to <code>SKIP</code></i>", "Rate 06-10-2026 se laagu", False),
    ],
    "biz_salary": [
        ("company", "🏢 <b>Step 1/6 — Company / dukaan ka naam?</b>", "Sharma Kirana", False),
        ("name", "👤 <b>Step 2/6 — Staff ka naam?</b>", "Ramesh Kumar", False),
        ("post", "💼 <b>Step 3/6 — Post / kaam kya hai?</b>\n<i>Jaise: Salesman, Accountant, Driver</i>", "Salesman", False),
        ("month", "📅 <b>Step 4/6 — Kis mahine ki salary?</b>\n<i>Jaise: September 2026</i>", "September 2026", False),
        ("gross", "💰 <b>Step 5/6 — Poori salary (gross) kitni hai?</b>\n<i>Sirf number likhein, jaise: 18000</i>", "18000", False),
        ("advance", "➖ <b>Step 6/6 — Advance / loan katta hai? (optional)</b>\n<i>Nahi to <code>0</code> ya <code>SKIP</code> likhein</i>", "500", False),
    ],
    "biz_menucard": [
        ("name", "🍽️ <b>Step 1/4 — Hotel / dukaan ka naam?</b>", "Hotel Shivam", False),
        ("tagline", "✍️ <b>Step 2/4 — Ek line ka tagline?</b>\n<i>Jaise: Shudh Desi Khana. Nahi chahiye to <code>SKIP</code></i>", "Shudh Desi Khana", False),
        ("logo", "🖼️ <b>Step 3/4 — LOGO?</b> (menu ke upar lagega)\n<i>Photo bhejein ya <code>SKIP</code>.</i>", "LOGO PHOTO BHEJEIN", True),
        ("items", "📋 <b>Step 4/4 — Saare item aur rate?</b>\n<i>Jaise: Chai:10, Samosa:15, Thali:80</i>\n<b>Naam : Rate</b> likhein", "Chai:10, Samosa:15", False),
    ],
    "biz_emi": [
        ("loan_amount", "💰 <b>Step 1/3 — Loan kitne ka hai?</b>\n<i>Sirf number, jaise: 250000</i>", "250000", False),
        ("rate", "📈 <b>Step 2/3 — Byaaj (interest) % saalana?</b>\n<i>Jaise: 11.5</i>", "11.5", False),
        ("months", "🗓️ <b>Step 3/3 — Kitne mahine me chukana hai?</b>\n<i>Jaise: 36</i>", "36", False),
    ],
    # ------------------------------------------------ v76 💰 EARN STUDIO (5 naye)
    "biz_rent": [
        ("owner", "🏠 <b>Step 1/6 — Makan malik ka naam?</b>\n<i>Jaise: Ramesh Kumar</i>", "Ramesh Kumar", False),
        ("tenant", "🙋 <b>Step 2/6 — Kirayedar ka naam?</b>\n<i>Jaise: Himanshu Kumar</i>", "Himanshu Kumar", False),
        ("address", "📍 <b>Step 3/6 — Makan / flat ka poora pata?</b>\n<i>Jaise: Makan No. 42, Bihta, Patna</i>", "Makan No. 42, Bihta, Patna", False),
        ("amount", "💰 <b>Step 4/6 — Mahine ka kiraya kitna hai?</b>\n<i>Sirf number, jaise: 8500</i>", "8500", False),
        ("month", "📅 <b>Step 5/6 — Kaunsa mahina?</b>\n<i>Jaise: September 2026</i>", "September 2026", False),
        ("mode", "💳 <b>Step 6/6 — Payment kaise mila? (aur PAN — optional)</b>\n<i>Jaise: PhonePe | ABCPK1234K</i>\n<i>PAN nahi to <code>SKIP</code></i>", "PhonePe", False),
    ],
    "biz_khata": [
        ("shop", "🏪 <b>Step 1/4 — Dukaan ka naam?</b>", "Sharma Kirana Store", False),
        ("customer", "🙋 <b>Step 2/4 — Grahak ka naam?</b>", "Mohan Yadav", False),
        ("phone", "📞 <b>Step 3/4 — Phone number? (optional)</b>\n<i>Nahi to <code>SKIP</code></i>", "9876543210", False),
        ("entries", "📒 <b>Step 4/4 — Hisaab likhein (har entry alag line)</b>\n<b>Format:</b> <code>taareekh, saaman, udhaar, jama</code>\n<i>Jaise: 01-09, aata, 500, 0</i>\n<i>Jaise: 10-09, jama diya, 0, 400</i>",
         "01-09, aata, 500, 0", False),
    ],
    "biz_poster": [
        ("theme", "🎊 <b>Step 1/6 — Kaunsa tyohar / offer?</b>\n1 = Diwali · 2 = Holi · 3 = Sale\n4 = New Year · 5 = Eid · 6 = Republic Day\n7 = Independence Day · 8 = Grand Opening\n<i>Number ya naam likhein</i>", "Diwali", False),
        ("shop", "🏪 <b>Step 2/6 — Dukaan ka naam?</b>", "Sharma Electronics", False),
        ("offer", "🔥 <b>Step 3/6 — Kya offer hai?</b>\n<i>Jaise: 50% OFF ya Buy 1 Get 1</i>", "50% OFF", False),
        ("phone", "📞 <b>Step 4/6 — Phone number?</b>", "9876543210", False),
        ("address", "📍 <b>Step 5/6 — Dukaan ka pata? (optional)</b>\n<i>Nahi to <code>SKIP</code></i>", "Main Road, Bihta, Patna", False),
        ("items", "📋 <b>Step 6/6 — Kya-kya mil raha hai? (optional)</b>\n<i>Jaise: LED TV, Mixer, Cooler</i>\n<i>Nahi to <code>SKIP</code></i>", "LED TV, Mixer, Cooler", False),
    ],
    "biz_quote": [
        ("shop", "🏢 <b>Step 1/6 — Aapki company / dukaan ka naam?</b>", "Himanshu Interiors", False),
        ("to", "🙋 <b>Step 2/6 — Grahak (client) ka naam?</b>", "Ramesh Kumar", False),
        ("items", "🛒 <b>Step 3/6 — Kaam / saaman ki list (qty x rate)</b>\n<i>Jaise: Wardrobe 2x45000, Kitchen 1x78000</i>", "Wardrobe 2x45000, Kitchen 1x78000", False),
        ("gst", "🧾 <b>Step 4/6 — GST kitna %?</b>\n<i>Jaise: 18 (nahi lagana to 0)</i>", "18", False),
        ("valid", "⏳ <b>Step 5/6 — Quotation kitne din tak maany rahe?</b>\n<i>Jaise: 30 din</i>", "30 din", False),
        ("phone", "📞 <b>Step 6/6 — Apna phone / payment ID? (optional)</b>\n<i>Jaise: 9876543210@ybl</i>\n<i>Nahi to <code>SKIP</code></i>", "9876543210@ybl", False),
    ],
    "biz_profit": [
        ("shop", "🏪 <b>Step 1/6 — Business ka naam?</b>", "Sharma Kirana Store", False),
        ("month", "📅 <b>Step 2/6 — Kaunsa mahina?</b>\n<i>Jaise: September 2026</i>", "September 2026", False),
        ("sale", "💰 <b>Step 3/6 — Is mahine kul kitni BIKRI hui?</b>\n<i>Sirf number, jaise: 420000</i>", "420000", False),
        ("cost", "📦 <b>Step 4/6 — Saaman kharidne me kitna kharcha? (laagat)</b>\n<i>Sirf number, jaise: 330000</i>", "330000", False),
        ("expense", "🧾 <b>Step 5/6 — Baaki kharche? (kiraya, bijli, staff)</b>\n<i>Sirf number, jaise: 58000</i>", "58000", False),
        ("expense_items", "📋 <b>Step 6/6 — Kharchon ki list? (optional)</b>\n<i>Jaise: Kiraya 12000, Bijli 3500, Staff 30000</i>\n<i>Nahi to <code>SKIP</code></i>", "Kiraya 12000, Bijli 3500, Staff 30000", False),
    ],
}
# photo wale step ke field-naam — inme bytes jaate hain, text nahi
BIZ_PHOTO_FIELDS = ("photo", "logo")

# purane BIZ_STEPS ka dhaancha badla to bhi bot na gire — safe fallback
def biz_steps(key: str) -> list:
    try:
        return list(BIZ_STEPS.get(key) or [])
    except Exception:                                            # noqa: BLE001
        return []


def biz_total_steps(key: str) -> int:
    return len(biz_steps(key))


def biz_step_prompt(key: str, idx: int) -> str:
    """Us step ka sawal + progress (Step 3/6) + format yaad dilana."""
    steps = biz_steps(key)
    if not steps or idx < 0 or idx >= len(steps):
        return ""
    _f, q, hint, is_photo = steps[idx][:4]
    _icon, name, _sub = BIZ_MENU.get(key, ("📄", "Tool", ""))
    bar_total = len(steps)
    bar = "●" * (idx + 1) + "○" * max(0, bar_total - idx - 1)
    return (f"{_icon} <b>{hesc(name)}</b>\n"
            f"──────────────────────\n"
            f"<code>{bar}</code>  <b>{idx + 1}/{bar_total}</b>\n\n"
            f"{q}\n\n"
            f"💡 <b>Example:</b> <code>{hesc(str(hint))[:70]}</code>")


# ======================================================================
#  v65: 🛡️ HARD CRASH-PROOF + 🚀 SPEED
# ======================================================================
#  Boss: "mere tools sab crash ho jaata hai — hard crash proof rakho,
#         aur 2 minute kyun rukna — 15 second me jawab do."
#
#  3 layer ka ilaaj:
#    1. `safe_tool_call()` — koi bhi tool ka function jo bhi galti kare,
#       bot nahi girta: exception pakad kar saaf message + log.
#    2. `with_tool_timeout()` — koi tool zyada atka rahe to usko ek
#       TAY ki hui waqt ke baad chhod do (asyncio level par).
#    3. `_progress_pinger()` — lamba kaam chale to har 5 second user ko
#       "ho raha hai" batata rahe (user ko lagta nahi ki bot mar gaya).
# ======================================================================
TOOL_HARD_TIMEOUT = 120      # koi bhi tool isse zyada nahi chalega
PROGRESS_EVERY = 5           # har 5 second progress ping


async def safe_tool_call(fn, *args, **kwargs):
    """Kisi bhi tool ko chalao — crash ho to (None, error) milega, bot gir nahi."""
    try:
        if asyncio.iscoroutinefunction(fn):
            return (await fn(*args, **kwargs)), None
        return await asyncio.get_running_loop().run_in_executor(
            None, functools_partial(fn, *args, **kwargs)), None
    except Exception as e:                                       # noqa: BLE001
        log.error(f"🛡️ safe_tool_call: {type(e).__name__}: {e}")
        return None, e


async def with_tool_timeout(coro, seconds: int = TOOL_HARD_TIMEOUT, name: str = "tool"):
    """Tool ko waqt ki hadd me chalao. Atka to None (bot zinda rehta hai)."""
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        log.warning(f"⏱️ {name} ne {seconds}s me jawab nahi diya — chhod diya")
        return None
    except Exception as e:                                       # noqa: BLE001
        log.error(f"🛡️ {name} error: {type(e).__name__}: {e}")
        return None


async def _progress_pinger(msg, text_fn, every: int = PROGRESS_EVERY,
                           stop: "asyncio.Event" = None, max_pings: int = 6):
    """Lamba kaam ke dauran har `every` second progress bhejo (aur user ko
    dikhe ki bot zinda hai). stop.set() hone par ruk jata hai."""
    t0 = time.time()
    _sent = 0
    try:
        while (stop is not None and not stop.is_set()) and _sent < max_pings:
            try:
                await asyncio.wait_for(stop.wait(), timeout=every)
                break
            except asyncio.TimeoutError:
                pass
            except Exception:                                    # noqa: BLE001
                break
            try:
                el = int(time.time() - t0)
                await safe_reply(msg, text_fn(el), parse_mode="HTML")
                _sent += 1
            except Exception:                                    # noqa: BLE001
                break
    except Exception:                                            # noqa: BLE001
        pass


class _StatusMsg:
    """v65: status message ka wrapper — jaise hi final result edit/delete hota hai,
    progress pinger KHUD ruk jata hai (result ke upar purani line nahi likhti)."""

    __slots__ = ("_msg", "_stop")

    def __init__(self, msg, stop):
        self._msg = msg
        self._stop = stop

    def _fin(self):
        try:
            if self._stop is not None:
                self._stop.set()
        except Exception:                                        # noqa: BLE001
            pass

    async def edit_text(self, *a, **kw):
        self._fin()
        return await self._msg.edit_text(*a, **kw)

    async def delete(self, *a, **kw):
        self._fin()
        return await self._msg.delete(*a, **kw)

    def __getattr__(self, name):
        return getattr(self._msg, name)


def _stop_ping(context):
    """v65: purana progress pinger band karo (nayi request aane par)."""
    try:
        _ev = context.user_data.pop("_ping_stop", None)
        if _ev is not None:
            _ev.set()
    except Exception:                                            # noqa: BLE001
        pass


async def _progress_edit(msg, base: str, every: int = PROGRESS_EVERY,
                         stop: "asyncio.Event" = None, max_pings: int = 12):
    """v65: EK HI message ko har `every` second update karo (live timer).
    User ko lagta rahe ki bot zinda hai — spam ki tarah nayi message nahi."""
    t0 = time.time()
    _n = 0
    try:
        while (stop is not None and not stop.is_set()) and _n < max_pings:
            try:
                await asyncio.wait_for(stop.wait(), timeout=every)
                break
            except asyncio.TimeoutError:
                pass
            except Exception:                                    # noqa: BLE001
                break
            try:
                _el = int(time.time() - t0)
                await safe_edit(
                    msg,
                    f"{base}\n⏱️ <i>{_el} second ho gaye… bas thoda sa aur, file taiyaar ho rahi hai.</i>",
                    parse_mode="HTML")
                _n += 1
            except Exception:                                    # noqa: BLE001
                break
    except Exception:                                            # noqa: BLE001
        pass


# ======================================================================
#  v66: 🍪 /cookies — "Sign in to confirm you're not a bot" ka PAKKA ilaaj
# ======================================================================
#  YouTube cloud server (Render) ke IP par bot-check lagata hai. Jab admin
#  apni YouTube cookies de deta hai to download hamesha chalta hai.
#  Admin: /cookies -> bot kehta hai file bhejo -> admin cookies.txt bhejta hai
#         -> bot usse save kar leta hai (DB me bhi, isliye redeploy par bachi
#         rehti hai) -> wahi file bot kaam me leta hai.
# ----------------------------------------------------------------------

def cookies_boot_restore() -> bool:
    """Boot par DB se cookies wapas likho (redeploy ke baad bhi kaam kare)."""
    try:
        txt = meta_get("yt_cookies", "") or ""
        if txt and len(txt) > 40:
            return bool(MD.save_cookies_text(txt))
    except Exception as e:                                       # noqa: BLE001
        log.debug("cookies boot restore skip: %s", str(e)[:90])
    return False


async def cmd_rcsetup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/rcsetup — RC/Challan live karne ka sabse aasan tarika (free)."""
    _on = carry = ""
    try:
        _on = "✅ LAGI HUI HAI" if vahan_provider_ready() else "❌ abhi nahi lagi"
    except Exception:                                        # noqa: BLE001
        _on = "❌ abhi nahi lagi"
    await update.message.reply_text(
        "🚗 <b>RC + CHALLAN — SETUP (v71.7)</b>\n"
        "──────────────────────\n"
        f"📌 <b>Provider status:</b> {_on}\n\n"
        "⚠️ <b>SACH PEHLE:</b> is API ke free plan (BASIC) me <b>sirf 10 requests/"
        "mahina</b> milti hain. Ek lookup = 1 request. Isliye bot aapse 1 hi request "
        "leti hai, aur limit khatam hote hi SAFA message deti hai (429 ka matlab "
        "yahi hota hai).\n\n"
        "🔧 <b>Render → utility-duniya-bot → Environment me:</b>\n\n"
        "<code>VEHICLE_PROVIDER_URL = https://vehicle-rc-information.p.rapidapi.com</code>\n"
        "<code>VEHICLE_PROVIDER_KEY = &lt;aapki X-RapidAPI-Key&gt;</code>\n\n"
        "🎯 <b>2 ya 3 free API jodni ho?</b> (limit shared ho jaati hai):\n"
        "<code>VEHICLE_PROVIDER_URL = url1|url2</code>\n"
        "<code>VEHICLE_PROVIDER_KEY = key1|key2</code>\n"
        "Ek ki limit khatam → bot khud doosre par chala jaata hai.\n\n"
        "⭐ <b>Zyada data chahiye?</b> (chassis, engine, owner mobile, PUCC):\n"
        "Playground → <b>Vehicle Information v2 [Advance]</b> → <b>Request</b> tab se "
        "poora URL copy karo → URL wali line me paste karo, aur ek line aur daalo:\n"
        "<code>VEHICLE_PROVIDER_BODY = {\"vehicle_number\":\"{number}\"}</code>\n\n"
        "✅ Baaki sab bot khud karta hai: sahi URL, sahi body, provider badalna, "
        "quota bachana — aap sirf 2-3 line daalo aur plate bhejo.\n"
        "🏆 Best value: <b>PRO ₹~880/mahina = 1000 lookups</b> (jab users badh jayein).\n"
        "💡 Provider na ho to bhi bot state + RTO + challan ka <b>sarkari tarika</b> deta hai.",
        parse_mode=HTML)
    return


async def cmd_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/speed — bot kitna tez hai, cache kitna bhara, kaunsa client bad hai."""
    try:
        _st = MD.dl_cache_stats()
        _fid = 0
        try:
            _fid = len([1 for _k in ("dlfid:test",)])  # placeholder
        except Exception:                                        # noqa: BLE001
            pass
        _ladder = " → ".join(c[0] for c in MD.YT_CLIENT_SETS)
        await update.message.reply_text(
            "⚡ <b>SPEED REPORT</b>\n"
            "──────────────────────\n"
            f"⏱️ <b>Max time:</b> {MD.FAST_DEADLINE} second (hard limit)\n"
            f"🧠 <b>Video cache:</b> {_st['items']} video "
            f"({_st['mb']} MB) — ye sab INSTANT milte hain\n"
            f"♻️ <b>Instant repeat:</b> ON (file_id cache, restart-proof)\n"
            f"🤖 <b>Client ladder:</b> <code>{hesc(_ladder)}</code>\n"
            f"🚫 <b>Bad-marked clients:</b> {_st['bad_clients']} "
            "(bot-check wale, 15 min ke liye hata diye)\n"
            f"🔀 <b>Parallel info:</b> ON (jo engine pehle jeete)\n"
            f"💾 <b>Disk cache:</b> {MD.disk_cache_stats()['files']} file "
            f"({MD.disk_cache_stats()['mb']} MB) — restart-proof\n"
            "──────────────────────\n"
            f"⏱️ <b>Keepalive:</b> har {int(os.environ.get('KEEPALIVE_MINUTES') or 3)} min",
            parse_mode=HTML)
    except Exception as e:                                       # noqa: BLE001
        await update.message.reply_text(f"Speed report fail: {hesc(str(e))[:120]}",
                                        parse_mode=HTML)


async def cmd_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cookies — YouTube/Instagram cookies ka status + tarika (admin)."""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("🚫 Sirf admin ke liye.", parse_mode=HTML)
        return
    st = MD.cookies_status()
    _ladder = " → ".join(c[0] for c in MD.YT_CLIENT_SETS)
    txt = (
        "🍪 <b>COOKIES STATUS</b>\n"
        "──────────────────────\n"
        f"{'✅' if st['set'] else '⚠️'} <b>Cookies:</b> "
        f"{'LAGI HAIN — bot-check nahi aayega' if st['set'] else 'NAHI lagi hain'}\n"
        f"📄 <b>Lines:</b> {st['lines']} | 📁 <code>{hesc(str(st['path'])[-40:]) or '—'}</code>\n"
        f"🤖 <b>Client ladder:</b> <code>{hesc(_ladder)}</code>\n"
        "──────────────────────\n"
        "<b>🍪 Cookies kaise deni hai (2 minute):</b>\n"
        "1️⃣ Android/iOS ke LIYE: <b>Telegram par wahi cookies.txt file</b> seedha "
        "is bot ko bhej dein (neeche tarika).\n"
        "2️⃣ PC par: Chrome me <b>\"Get cookies.txt LOCALLY\"</b> extension daalein → "
        "<code>youtube.com</code> kholein → extension se <b>cookies.txt</b> download karein.\n"
        "3️⃣ Wahi <b>cookies.txt</b> yahan bot ko <b>file ke roop me bhej dein</b> "
        "(command likhne ki zaroorat nahi).\n"
        "──────────────────────\n"
        "<b>Maine badal diya kya:</b>\n"
        "• 🤖 4 client ladder (android_vr → tv_embedded → android → web_safari)\n"
        "• ⚡ progressive format + 16 parallel chunks = video 1-2 second me\n"
        "• ⛔ 45 second hard limit — lambi wait hamesha ke liye khatam\n"
        "• 🍪 Cookies = YouTube ka bot-check poora band\n\n"
        "👉 Ab <b>cookies.txt file</b> bhej dijiye — main turant laga dunga."
    )
    await update.message.reply_text(txt, parse_mode=HTML)


async def on_doc_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """v66: admin 'cookies.txt' bhejta hai to bot use laga leta hai (group=-5)."""
    try:
        msg = update.effective_message
        u = update.effective_user
        if not msg or not msg.document or u is None:
            return
        if not is_admin(u.id):
            return
        doc = msg.document
        _name = (doc.file_name or "").lower()
        if "cookie" not in _name and not context.user_data.get("await_cookies"):
            return
        if (doc.file_size or 0) > 3 * 1024 * 1024:
            await msg.reply_text("❌ File bahut badi hai (3 MB se kam bhejein).",
                                 parse_mode=HTML)
            return
        _f = await context.bot.get_file(doc.file_id)
        _raw = bytes(await _f.download_as_bytearray())
        _txt = _raw.decode("utf-8", "ignore")
        if "youtube.com" not in _txt and "instagram.com" not in _txt:
            await msg.reply_text(
                "⚠️ Ye cookies file nahi lagti.\n"
                "✅ <b>cookies.txt</b> (Netscape format) bhejein — "
                "jisme <code>youtube.com</code> ki lines hon.", parse_mode=HTML)
            return
        _path = MD.save_cookies_text(_txt)
        if not _path:
            await msg.reply_text("❌ Cookies save nahi ho payi — dobara bhejein.",
                                 parse_mode=HTML)
            return
        try:
            meta_set("yt_cookies", _txt)     # redeploy ke baad bhi bachi rahe
        except Exception:                                        # noqa: BLE001
            pass
        context.user_data.pop("await_cookies", None)
        _st = MD.cookies_status()
        await msg.reply_text(
            "✅ <b>COOKIES LAG GAYIN!</b>\n"
            "──────────────────────\n"
            f"📄 <b>Lines:</b> {_st['lines']} | 🍪 <b>Status:</b> ON\n"
            "🎉 Ab YouTube ka <i>\"Sign in to confirm you're not a bot\"</i> "
            "error <b>nahi aayega</b>.\n"
            "👉 Ab koi bhi video link bhej ke test karein — 1-2 second me video milegi.\n\n"
            "🔒 Ye file safe hai (sirf download ke liye use hoti hai).",
            parse_mode=HTML)
    except Exception as e:                                       # noqa: BLE001
        log.warning("cookies file handle fail: %s", str(e)[:140])


# ======================================================================
#  v68: ⚡ INSTANT REPEAT — ek hi video dobara = 0.1 second
# ======================================================================
#  Telegram har file ka "file_id" deta hai. Ek baar upload hone ke baad
#  wahi file_id se dobara bhejna = 0 upload, 0 download, TURANT.
#  (viral reel 10 log bhejte hain -> pehla 8s, baaki sab 0.1s)
# ----------------------------------------------------------------------

def dl_fid_key(url: str, tag: str = "") -> str:
    import hashlib as _h
    _raw = (str(tag) + "|" + (url or "").strip().lower())[:400]
    return "dlfid:" + _h.sha1(_raw.encode("utf-8", "ignore")).hexdigest()[:24]


def dl_fid_get(url: str, tag: str = "") -> str:
    try:
        return meta_get(dl_fid_key(url, tag), "") or ""
    except Exception:                                            # noqa: BLE001
        return ""


def dl_fid_set(url: str, file_id: str, tag: str = "") -> None:
    try:
        if file_id:
            meta_set(dl_fid_key(url, tag), str(file_id))
    except Exception:                                            # noqa: BLE001
        pass


def dl_fid_forget(url: str, tag: str = "") -> None:
    try:
        meta_set(dl_fid_key(url, tag), "")
    except Exception:                                            # noqa: BLE001
        pass


def _biz_today() -> str:
    return datetime.now().strftime("%d-%m-%Y")


def biz_steps_kb(key: str, idx: int):
    """Wizard ke buttons: ⬅️ Peeche · ❌ Cancel (+ agla step ka hint)."""
    rows = []
    if idx > 0:
        rows.append([
            InlineKeyboardButton("⬅️ Peeche", callback_data=f"bizstep:{key}:{idx - 1}"),
            InlineKeyboardButton("❌ Cancel", callback_data="bizstudio"),
        ])
    else:
        rows.append([InlineKeyboardButton("❌ Cancel", callback_data="bizstudio")])
    rows.append([InlineKeyboardButton("💼 Business Studio", callback_data="bizstudio"),
                 InlineKeyboardButton("🏠 Home", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)


def biz_answers_to_dict(key: str, ans: dict) -> dict:
    """Wizard ke jawabon ko us tool ke dict me badlo — bilkul biz_parse jaisa.

    Line-format wale parser se hi guzarta hai, is liye output BILKUL same aata hai
    (purana one-line tarika bhi waise hi chalta rahega).
    """
    try:
        a = dict(ans or {})
        if key == "biz_invoice":
            one = " | ".join([str(a.get("shop") or ""), str(a.get("buyer") or ""),
                              str(a.get("items") or "")])
            d = biz_parse(key, one)
            d["tagline"] = str(a.get("tagline") or "").strip()
            if a.get("logo"):
                d["logo"] = a["logo"]
            return d
        if key == "biz_resume":
            one = " | ".join([str(a.get("name") or ""), str(a.get("role") or ""),
                              str(a.get("phone") or ""), "", ""])
            d = biz_parse(key, one)
            return d
        if key == "biz_biodata":
            one = " | ".join([str(a.get("name") or ""), str(a.get("dob") or ""),
                              str(a.get("education") or ""), str(a.get("job") or ""),
                              "", ""])
            d = biz_parse(key, one)
            if a.get("photo"):
                d["photo"] = a["photo"]
            return d
        if key == "biz_certificate":
            extra = str(a.get("extra") or "").strip()
            _date, _photo = "", None
            bits = [x.strip() for x in re.split(r"[|,]+", extra) if x.strip()] if extra else []
            for b2 in bits:
                if re.search(r"\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}", b2) or re.search(r"\d{4}", b2):
                    _date = b2
                else:
                    _photo = None
            d = biz_parse("biz_certificate",
                          " | ".join([str(a.get("org") or ""), str(a.get("name") or ""),
                                      str(a.get("course") or ""), _date or _biz_today()]))
            if a.get("logo"):
                d["logo"] = a["logo"]
            if a.get("photo"):
                d["photo"] = a["photo"]
            return d
        if key == "biz_idcard":
            one = " | ".join([str(a.get("org") or ""), str(a.get("name") or ""),
                              str(a.get("father") or "")])
            d = biz_parse(key, one)
            _cr = " | ".join([str(a.get("class") or ""), ""])
            _cls, _roll = "", ""
            parts = [x.strip() for x in re.split(r"[|,]+", str(a.get("class") or "")) if x.strip()]
            if parts:
                _cls = parts[0]
            if len(parts) > 1:
                _roll = parts[1]
            _sc = (d.get("students") or [{}])
            if _sc:
                _sc[0]["class"] = _cls
                _sc[0]["roll"] = _roll
            d["students"] = _sc
            if a.get("logo"):
                d["logo"] = a["logo"]
            if a.get("photo"):
                try:
                    d["students"][0]["photo"] = a["photo"]
                except Exception:                                # noqa: BLE001
                    pass
            return d
        if key == "biz_vcard":
            phone, addr = str(a.get("phone") or ""), ""
            parts = [x.strip() for x in re.split(r"[|,]+", phone) if x.strip()]
            if parts:
                phone = parts[0]
            if len(parts) > 1:
                addr = " ".join(parts[1:])
            d = biz_parse(key, " | ".join([str(a.get("owner") or ""),
                                           str(a.get("shop") or ""), phone, addr]))
            if a.get("logo"):
                d["logo"] = a["logo"]
            _ex = str(a.get("extra") or "").strip()
            if _ex and _ex.upper() != "SKIP":
                d["email"] = _ex
            return d
        if key == "biz_letter":
            t = str(a.get("type") or "").strip().lower()
            t = {"1": "leave", "2": "noc", "3": "character", "4": "bonafide"}.get(t, t or "leave")
            nm, post = str(a.get("name") or ""), ""
            parts = [x.strip() for x in re.split(r"[|,]+", nm) if x.strip()]
            if parts:
                nm = parts[0]
            if len(parts) > 1:
                post = parts[1]
            d = biz_parse(key, " | ".join([t, nm, str(a.get("org") or ""),
                                           str(a.get("reason") or ""), post]))
            return d
        if key == "biz_upi":
            d = biz_parse(key, " | ".join([str(a.get("upi") or ""),
                                           str(a.get("shop") or ""),
                                           str(a.get("phone") or "")]))
            if a.get("logo"):
                d["logo"] = a["logo"]
            return d
        if key == "biz_labels":
            d = biz_parse(key, " | ".join([str(a.get("shop") or ""),
                                           str(a.get("labels") or "")]))
            if a.get("logo"):
                d["logo"] = a["logo"]
            _ex = str(a.get("extra") or "").strip()
            if _ex and _ex.upper() != "SKIP":
                d["footer"] = _ex
            return d
        if key == "biz_salary":
            d = biz_parse(key, " | ".join([str(a.get("company") or ""),
                                           str(a.get("name") or ""),
                                           str(a.get("post") or ""),
                                           str(a.get("month") or ""),
                                           str(a.get("gross") or "0"),
                                           str(a.get("advance") or "0")]))
            return d
        if key == "biz_menucard":
            d = biz_parse(key, " | ".join([str(a.get("name") or ""),
                                           str(a.get("tagline") or ""),
                                           str(a.get("items") or "")]))
            if a.get("logo"):
                d["logo"] = a["logo"]
            return d
        if key == "biz_emi":
            d = biz_parse(key, " | ".join([str(a.get("loan_amount") or "0"),
                                           str(a.get("rate") or "10"),
                                           str(a.get("months") or "12")]))
            return d
    except Exception:                                            # noqa: BLE001
        pass
    return {}


BIZ_MENU_TEXT = (
    "💼 <b>𝐁𝐔𝐒𝐈𝐍𝐄𝐒𝐒 𝐒𝐓𝐔𝐃𝐈𝐎</b>\n"
    "──────────────────────\n"
    "Dukaan, school, coaching, job aur loan — <b>17 kaam ki cheezein</b>\n"
    "sirf ek line likh kar banao. Sab <b>print-ready A4 PDF</b> me.\n\n"
    "🆕 <b>Naye (v76):</b> Rent Receipt · Udhaar Khata · Offer Poster ·\n"
    "Quotation · Profit Card\n\n"
    "👇 Neeche se tool chuno:"
)

# v76: 💰 EARN STUDIO — 5 naye kamai wale tools ka alag premium menu
EARN_MENU_TEXT = (
    "💰 <b>𝐄𝐀𝐑𝐍 𝐒𝐓𝐔𝐃𝐈𝐎</b> <i>(v76 · naya)</i>\n"
    "──────────────────────\n"
    "Ye 5 tools India me <b>sabse zyada maang</b> wale hain —\n"
    "rent har mahine, khata roz, poster har tyohar.\n\n"
    "✅ 100% offline (koi API nahi) · ✅ Hindi + English\n"
    "✅ PNG <b>+ PDF</b> — seedha print ya WhatsApp\n\n"
    "👇 Tool chuno:"
)


def biz_menu_kb():
    rows, pair = [], []
    # v76: EARN STUDIO ka shortcut sabse upar
    rows.append([InlineKeyboardButton("💰 EARN STUDIO — naye tools ➡️",
                                      callback_data="earnstudio")])
    for key, (icon, name, _sub) in BIZ_MENU.items():
        if key in EARN_STUDIO_MENU:
            continue          # ye EARN STUDIO menu me hain
        pair.append(InlineKeyboardButton(f"{icon} {name}", callback_data=f"biz:{key}"))
        if len(pair) == 2:
            rows.append(pair); pair = []
    if pair:
        rows.append(pair)
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)


def earn_menu_kb():
    """v76: 💰 EARN STUDIO ka keyboard (5 naye premium tools)."""
    rows = []
    for key in EARN_STUDIO_ORDER:
        icon, name, sub = EARN_STUDIO_MENU.get(key, ("📄", key, ""))
        rows.append([InlineKeyboardButton(f"{icon} {name}",
                                          callback_data=f"biz:{key}")])
    rows.append([InlineKeyboardButton("💼 Business Studio", callback_data="bizstudio"),
                 InlineKeyboardButton("🏠 Home", callback_data="back_home")])
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
            # v63: session sahi academic year (April se March) — pehle galat tha
            _yr = datetime.now().year if datetime.now().month >= 4 else datetime.now().year - 1
            d = {"org": p[0] if p else "",
                 "tagline": "STUDENT IDENTITY CARD",
                 "session": f"{_yr}-{str(_yr + 1)[-2:]}",
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

        # ------------------------------------------- v76 💰 EARN STUDIO (5 naye)
        elif key == "biz_rent":
            # ek line: makan-malik | kirayedar | pata | kiraya | mahina | mode|PAN
            d = {"owner": (p[0] if p else "") or owner_name,
                 "tenant": p[1] if len(p) > 1 else "",
                 "address": p[2] if len(p) > 2 else "",
                 "amount": _biz_num(p[3]) if len(p) > 3 else 0,
                 "month": (p[4] if len(p) > 4 else ""),
                 "mode": (p[5] if len(p) > 5 else "Cash")}
            if len(p) > 6:
                d["pan"] = p[6]
        elif key == "biz_khata":
            # ek line: dukaan | grahak | phone | entries
            d = {"shop": (p[0] if p else "") or owner_name,
                 "customer": p[1] if len(p) > 1 else "",
                 "phone": p[2] if len(p) > 2 else "",
                 "entries": p[3] if len(p) > 3 else ""}
        elif key == "biz_poster":
            d = {"theme": _poster_theme(p[0] if p else ""),
                 "shop": (p[1] if len(p) > 1 else "") or owner_name,
                 "offer": (p[2] if len(p) > 2 else "") or "SALE",
                 "phone": p[3] if len(p) > 3 else "",
                 "address": p[4] if len(p) > 4 else "",
                 "items": p[5] if len(p) > 5 else ""}
        elif key == "biz_quote":
            d = {"shop": (p[0] if p else "") or owner_name,
                 "to": p[1] if len(p) > 1 else "",
                 "items": _biz_items(p[2] if len(p) > 2 else ""),
                 "gst": _biz_num(p[3], 18) if len(p) > 3 else 18,
                 "valid": (p[4] if len(p) > 4 else "") or "15 din",
                 "upi": p[5] if len(p) > 5 else ""}
        elif key == "biz_profit":
            d = {"shop": (p[0] if p else "") or owner_name,
                 "month": p[1] if len(p) > 1 else "",
                 "sale": _biz_num(p[2]) if len(p) > 2 else 0,
                 "cost": _biz_num(p[3]) if len(p) > 3 else 0,
                 "expense": _biz_num(p[4]) if len(p) > 4 else 0,
                 "expense_items": p[5] if len(p) > 5 else ""}
    except Exception:                                            # noqa: BLE001
        pass
    return d


# v76: poster theme ka naam -> key (user "Diwali" likhe ya "1", dono chalenge)
_POSTER_THEME_MAP = {
    "1": "diwali", "diwali": "diwali", "deepawali": "diwali", "दिवाली": "diwali",
    "2": "holi", "holi": "holi", "होली": "holi",
    "3": "sale", "sale": "sale", "offer": "sale", "sail": "sale",
    "4": "newyear", "new year": "newyear", "naye saal": "newyear",
    "5": "eid", "eid": "eid", "ईद": "eid",
    "6": "republic", "republic day": "republic", "ganatantra": "republic",
    "7": "independence", "15 august": "independence", "swatantrata": "independence",
    "8": "opening", "grand opening": "opening", "nayi dukaan": "opening",
}


def _poster_theme(raw: str) -> str:
    """User ne jo bhi likha (naam ya number) -> sahi theme key."""
    try:
        t = str(raw or "").strip().lower()
        if t in _POSTER_THEME_MAP:
            return _POSTER_THEME_MAP[t]
        for k, v in _POSTER_THEME_MAP.items():
            if len(k) > 3 and k in t:
                return v
    except Exception:                                            # noqa: BLE001
        pass
    return "sale"


def biz_build(key: str, d: dict) -> dict:
    """Sahi function chalao — safe."""
    fn = {"biz_invoice": biz_invoice, "biz_resume": biz_resume,
          "biz_biodata": biz_biodata, "biz_certificate": biz_certificate,
          "biz_idcard": biz_idcard, "biz_vcard": biz_vcard,
          "biz_letter": biz_letter, "biz_upi": biz_upi_qr,
          "biz_labels": biz_labels, "biz_emi": biz_emi_card,
          "biz_salary": biz_salary, "biz_menucard": biz_menucard}.get(key)
    if fn is None:
        # v76: 💰 EARN STUDIO ke 5 naye tools (rent · khata · poster · quote · profit)
        try:
            if str(key) in EARN_STUDIO_MENU:
                return earn_studio_build(key, d)
        except Exception:                                        # noqa: BLE001
            pass
        return {"ok": False, "error": "tool nahi mila"}
    return fn(d)


async def biz_send_result(msg, key: str, res: dict, uid: int, used: bool = True) -> None:
    """Result bhejo — image + PDF dono, aur credit ka message."""
    if not res or not res.get("ok"):
        why = (res or {}).get("error") or "kuch gadbad ho gayi"
        await safe_reply(
            msg,
            f"⚠️ <b>File nahi ban payi</b>\n"
            f"──────────────────────\n"
            f"📄 {safe_html_err(str(why)[:200])}\n\n"
            f"💡 <b>Format yaad rakhein:</b> ek line me <code>|</code> se alag likhein.\n"
            f"Example dekhne ke liye tool ka naam dobara dabayein.",
            parse_mode="HTML")
        return
    _icon, name, _sub = BIZ_MENU.get(key, ("📄", "File", ""))
    bio = io.BytesIO(res["png"])
    bio.name = f"{key.replace('biz_', '')}_{datetime.now().strftime('%d%m_%H%M')}.png"
    cap = (f"✅ <b>{hesc(name)}</b> ready hai!\n"
           f"──────────────────────\n"
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
        "──────────────────────\n"
        f"⏱️ <b>Uptime:</b> {_uptime_str()}\n"
        f"🧵 <b>Threads:</b> {threads}   |   🧠 <b>RAM:</b> {mem}\n"
        f"📦 <b>Python objects:</b> {objs:,}\n"
        "──────────────────────\n"
        f"🗃️ <b>Cache entries:</b> {cs['entries']} / {cs['maxsize']}\n"
        f"   {hit_icon} <b>Hit rate:</b> {hit}%  "
        f"(hits {cs['hits']} · miss {cs['misses']})\n"
        f"   💡 jitna zyada hit, utni kam API call = fast + free\n"
        "──────────────────────\n"
        f"🚦 <b>Rate limiter:</b>\n"
        f"   ✅ allowed: {ls['allowed']:,}   "
        f"{blk_icon} blocked: {blk:,}\n"
        f"   🔑 active users tracked: {ls['active_buckets']}\n"
        f"   ⚙️ default: {ls['default_limit']} req / {ls['default_window']}s\n"
        "──────────────────────\n"
        f"🌐 <b>Mode:</b> {'WEBHOOK' if webhook_url_from_env() else 'POLLING'}\n"
        f"🔌 <b>Premium-only:</b> {'ON' if PREMIUM_ONLY else 'OFF'}\n"
        f"👑 <b>Admins:</b> {len(ADMIN_IDS)}\n"
        "──────────────────────\n"
        # v53.0: per-tool telemetry — ab koi tool chup-chaap fail nahi ho sakta.
        # DEAD upstream (jaise BGMI ke stats servers) sabse upar flag hota hai,
        # aur saaf likha aata hai ki us tool par credit nahi katna chahiye.
        + _telemetry_block()
        + _vault_admin_block()
        + "──────────────────────\n"
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
        # v76: bounded cache + janitor report
        try:
            _jb = _janitor_block()
            if _jb:
                lines.append("")
                lines.append(_jb)
            _br = _bounded_report() or {}
            if _br.get("caches"):
                _top = _br["caches"][:3]
                lines.append(
                    "   🪣 Cache: <b>%s</b>/%s entry · %s baar saaf"
                    % (_br.get("total_entries", 0), _br.get("total_limit", 0),
                       _br.get("clears", 0)))
                for _c in _top:
                    lines.append(
                        f"      • {hesc(str(_c.get('name')))}: "
                        f"{_c.get('size')}/{_c.get('maxsize')} "
                        f"(hit {_c.get('hit_rate')}%)")
        except Exception:                                        # noqa: BLE001
            pass
        lines.append("   💡 Commands: /vault · /backup · /restore · /vips · /ledger · /fixvip")
        lines.append("──────────────────────")
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
        "──────────────────────\n"
        f"👥 <b>Total Users:</b> {st['total_users']}   |   🟢 <b>Active today:</b> {st['active_today']}\n"
        f"⚡ <b>Uses today:</b> {st['uses_today']}   |   💎 <b>Active VIP:</b> {st['vip_users']}\n"
        "──────────────────────\n"
        f"💳 <b>Pending Payments:</b> {pend}  {'🔴 (to verify!)' if pend else '✅'}\n"
        f"✅ <b>Approved Total:</b> {ps['approved']}   |   ❌ <b>Rejected:</b> {ps['rejected']}\n"
        f"💰 <b>Total Revenue:</b> ₹{ps['revenue']:,}\n"
        f"🎁 <b>Manual VIP given today:</b> {vip_grants_today()}\n"
        f"🎟️ <b>Credits wale users:</b> {credits_stats()['with_credits']} · <b>khatam:</b> {credits_stats()['out_of_credits']}\n"
        "──────────────────────\n"
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
        "──────────────────────\n"
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
        "🧾 <b>My Payments</b>\n──────────────────────\n" + "\n".join(lines) +
        "\n──────────────────────\n⏳ admin is verifying · ✅ VIP active · ❌ rejected",
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
    """Premium boxed header (v71):  ┏─┓ | ┃ 🏦 𝐈𝐅𝐒𝐂 𝐑𝐄𝐏𝐎𝐑𝐓 | ┗─┛

    Aakhir me ek nayi line jaati hai — isse title ke baad hamesha khali
    line aati hai (aapki shikayat: "likhne ke beech space nahi hota").
    """
    return f"{PCARD_TOP}\n┃ {icon} <b>{to_bold(name)}</b>\n{PCARD_BOT}\n"


def pcard_foot(*, ms: float = 0, source: str = "", note: str = "",
               brand: bool = True, cached: bool = False) -> str:
    """Premium footer — source + response time + brand (sab optional).

    v75.2: `cached=True` par seedha "instant (pehle check kiya tha)" dikhta hai.
    Pehle cache-hit par bhi "Response: 1ms" aa jaata tha — user ko samajh hi
    nahi aata tha ki ye **taakat** hai ya kuch toota hua. Ab saaf dikhta hai:
    bot ko pehle se pata tha (0 API call) — premium feel + bharosa.
    """
    L = ["", PCARD_MID]
    if source:
        L.append(f"📡 <b>Source:</b> {source}")
    if cached:
        L.append("⚡ <b>Instant</b> — ye pehle check kiya ja chuka tha "
                 "(0 API call, turant jawab)")
    elif ms:
        _m = float(ms)
        L.append(f"⚡ <b>Response:</b> {int(_m)}ms" if _m < 1000 else
                 f"⚡ <b>Response:</b> {_m / 1000:.1f}s")
    if note:
        L.append(note)
    if brand:
        L.append(BRAND_LINK)   # v59.7: clickable — tap = owner se baat
    return "\n".join(L)


def pcard_sep() -> str:
    """Separator — pehle aur baad me khali line (card saaf-suthra dikhe)."""
    return "\n" + PCARD_MID + "\n"


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

    def _digits_only(x) -> str:
        return re.sub(r"\D", "", str(x or ""))

    # ---------- v69: user ka SAMPLE format — bilkul isi tarah ----------
    #     👤 Name: Sanjay Sah
    #     👨 Father: Ram Akwal Sah
    #     📱 Phone: 7857843092
    #     📱 Alt: 7305190526
    #     🌐 Circle: BIHAR JIO
    #     🆔 Govt ID: 401635555849
    #     🏠 Address:
    #     └ S/O Ram Akwal Sah, ward 02, ... Sitamari, Bihar, 843324
    _nat = (_digits_only(res.get("national")) or _digits_only(res.get("number"))
            or _digits_only(res.get("e164")) or _digits_only(res.get("international")))
    _phone = _nat[-10:] if len(_nat) >= 10 else _nat
    _ph = _digits_only(owner.get("phone") or owner.get("mobile") or owner.get("number")) or _phone
    if _ph:
        _phone = _ph[-10:] if len(_ph) >= 10 else _ph
    _alts = []
    for _a in re.split(r"[,;|/\s]+", str(owner.get("alt") or "")):
        _ad = _digits_only(_a)
        if _ad and _ad[-10:] != _phone and _ad not in _alts:
            _alts.append(_ad)
    for _k in ("alt_numbers", "numbers", "phones_list", "other_numbers"):
        for _a2 in (extra.get(_k) or []):
            _ad = _digits_only(_a2)
            if _ad and _ad[-10:] != _phone and _ad not in _alts:
                _alts.append(_ad)

    _obits = []
    if owner.get("name"):
        _obits.append(f"👤 <b>Name:</b> {hesc(str(owner['name']))}")
    if owner.get("father"):
        _obits.append(f"👨 <b>Father:</b> {hesc(str(owner['father']))}")
    if _phone:
        _obits.append(f"📱 <b>Phone:</b> <code>{hesc(_phone)}</code>")
    if _alts:
        _obits.append(f"📱 <b>Alt:</b> <code>{hesc(', '.join(_alts[:4]))}</code>")
    _circ = " ".join([str(circle or owner.get("region") or "").strip(),
                      str(operator or "").strip()]).strip()
    if _circ:
        _obits.append(f"🌐 <b>Circle:</b> {hesc(_circ)}")
    if owner.get("govt_id"):
        _obits.append(f"🆔 <b>Govt ID:</b> <code>{hesc(str(owner['govt_id']))}</code>")
    _addr = str(owner.get("address") or "").strip()
    _alines = [x.strip() for x in _addr.split("|") if x.strip()][:4]
    for _k in ("addresses", "address_list"):
        for _a2 in (extra.get(_k) or [])[:4]:
            if _a2 and hesc(str(_a2))[:300] not in _addr:
                _alines.append(str(_a2))
    if _alines:
        _obits.append("🏠 <b>Address:</b>")
        for _ap in _alines[:4]:
            _obits.append(f"└ {hesc(_ap[:300])}")

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
    _owner_any = bool(owner.get("name") or owner.get("father") or owner.get("govt_id")
                      or owner.get("address"))
    if not _obits or not _owner_any:
        _card.append("👤 <b>Name / Father / Phones / Region / Govt ID / Address</b> — "
                     "ye data aapki API se aata hai.")
        _card.append("💡 Render → Environment me <code>NUMINFO_PROVIDER_URL</code> + "
                     "<code>NUMINFO_PROVIDER_KEY</code> daalo → <code>/numapi</code> se check karo.")
    _card.append(BRAND_LINK)   # v59.7: clickable
    return "\n".join([_l for _l in _card if _l])


def vahan_card(res: dict, offline: dict | None = None, note: str = "") -> str:
    """🚘 VEHICLE INFO REPORT — bilkul user ke diye format me (v71.1).

    User ka order: "sirf ye format, SMS/lecture lines nahi". Isliye card me
    sirf wahi rows jo user ne dikhaye — jo data na ho wahan "-" / "N/A".
    """
    res = res or {}
    offline = offline or {}
    rc = res.get("rc") or {}
    ch = res.get("challans") or []

    def _v(*keys, dash="-"):
        for k in keys:
            v = str(rc.get(k) or "").strip()
            if v and v.lower() not in ("none", "null", "na", "n/a", "-"):
                return v
        return dash

    _plate = (str(rc.get("plate") or offline.get("plate") or "")).upper()
    _model = " ".join([x for x in (_v("maker", dash=""), _v("model", dash="")) if x]).strip() or "-"
    _cc = _v("cc")
    _engine = (f"{_cc} CC" if _cc != "-" else "N/A CC")
    _ins = " · ".join([x for x in (_v("ins_company", dash=""), _v("ins_upto", dash="")) if x]) or "N/A"
    _fin_raw = str(rc.get("financer") or "").strip()
    if not _fin_raw or _fin_raw.lower() in ("null", "na", "n/a", "nan"):
        _fin = "N/A"
    elif _fin_raw.lower() in ("no", "none", "no loan", "not financed", "0"):
        _fin = "✅ No Loan"
    else:
        _fin = _fin_raw
    _rto = _v("authority", "office_code") if _v("authority", dash="") else \
        (str(offline.get("district") or "N/A"))
    _city = _v("city")
    if _city == "-":
        # v71.5: "BR30 RTA, Sitamarhi" → Sitamarhi ; "SANGRUR RTA, Punjab" → SANGRUR
        _auth = str(rc.get("authority") or "").strip()
        _toks = [t for t in (x.strip(".,") for x in re.split(r"\s+", _auth)) if t]
        _toks = [t for t in _toks if not re.fullmatch(r"[A-Z]{2}\d{1,2}", t.upper())]
        _off = next((i for i, t in enumerate(_toks) if t.upper() in (
            "RTA", "RTO", "ARTO", "DTO", "SRTO", "ZRTO", "DTC", "STA")), None)
        if _off == 0 and len(_toks) > 1:
            _city = _toks[1]
        elif _toks and _off not in (0, None):
            _city = _toks[0]
        elif _toks:
            _city = _toks[-1] if len(_toks) > 1 and "," in _auth else _toks[0]
        else:
            _city = str(offline.get("district") or "-")
    _status = _v("status", "rc_status")
    _status = "⚠️ N/A" if _status == "-" else _status
    _puc = _v("puc_upto")
    _puc = "⚠️ N/A" if _puc == "-" else _puc

    VS = "────────────────────"
    L = ["┏────────────────────────────┓",
         f"🚘 <b>{to_bold('VEHICLE INFO REPORT')}</b>",
         "┗────────────────────────────┛",
         ""]
    if note:
        # v71.6: jab live data na aaye to SAAF wajah yahin dikhao
        L += [f"⚠️ <b>Note:</b> {note}", ""]
    L += [
         f"🚗 <b>{to_bold('VEHICLE INFORMATION')}</b>",
         f"🔢 <b>Number:</b> <code>{hesc(_plate)}</code>",
         VS,
         f"├ 👤 <b>Owner:</b> {hesc(_v('owner'))}",
         f"├ 🚘 <b>Model:</b> {hesc(_model)}",
         f"├ ⛽ <b>Fuel:</b> {hesc(_v('fuel'))}",
         f"├ 🏙️ <b>City:</b> {hesc(_city or '-')}",
         f"📞 <b>Phone:</b> {hesc(_v('mobile', dash='NA'))}",
         f"📍 <b>RTO:</b> {hesc(_rto or 'N/A')}",
         "🏠 <b>Address:</b>",
         hesc(_v("address", dash="-")),
         VS,
         f"🏍️ <b>{to_bold('Technical')} &amp; {to_bold('RC Specifications')}</b>",
         f"├ 🆔 <b>RC Status :</b> {hesc(_status)}",
         f"├ 🎨 <b>Color :</b> {hesc(_v('colour', 'color', dash='N/A'))}",
         f"├ ⚙️ <b>Engine :</b> {hesc(_engine)}",
         f"├ 📅 <b>Reg Date :</b> {hesc(_v('reg_date', 'mfg_year', dash='N/A'))}",
         f"├ 🛡️ <b>Insurance :</b> {hesc(_ins)}",
         f"├ 🌫️ <b>PUC :</b> {hesc(_puc)}",
         f"└ 🏦 <b>Finance :</b> {hesc(_fin)}",
         VS,
         ""]

    # ---------- CHALLAN ----------
    _cnt = int(res.get("count") or 0)
    _pend = int(res.get("pending") or 0)
    _amt = int(res.get("amount") or 0)
    L.append(f"🚨 <b>{to_bold('CHALLAN SUMMARY')}</b>")
    if ch:
        L.append(f"📋 <b>Total:</b> {_cnt or len(ch)}  •  ❌ <b>Pending:</b> {_pend or len(ch)}"
                 + (f"  •  💰 ₹{_amt:,}" if _amt else ""))
        L.append(VS)
        L.append(f"🚨 <b>{to_bold('CHALLAN INFO')}</b>")
        for _c in ch[:6]:
            L.append("")
            L.append(f"🔹 <b>Challan #:</b> <code>{hesc(str(_c.get('number') or '-'))}</code>")
            if _c.get("accused"):
                L.append(f"   👤 <b>Accused:</b> {hesc(str(_c['accused']))}")
            if _c.get("amount"):
                L.append(f"   💰 <b>Amount:</b> ₹{hesc(str(_c['amount']))}")
            if _c.get("date"):
                L.append(f"   📅 <b>Date:</b> {hesc(str(_c['date']))}")
            _st = str(_c.get("status") or "").upper()
            if _st:
                _st = ("❌ " + _st) if "PEND" in _st else ("✅ " + _st)
                L.append(f"   {_st}")
            if _c.get("offence"):
                L.append(f"   🛑 <b>Offence:</b> {hesc(str(_c['offence']))}")
    elif rc:
        L.append("✅ Koi challan nahi — saaf record")
    else:
        L.append("⚠️ Challan check nahi ho paya — wajah upar ⚠️ Note me likhi hai.")

    L.append("")
    # v75.2: cache-hit par saaf dikhta hai (premium feel + bharosa)
    if res.get("cached"):
        L.append("⚡ <b>Instant</b> — ye pehle check kiya ja chuka tha "
                 "(0 API call, turant jawab)")
    L.append(BRAND_LINK)
    return "\n".join([_l for _l in L if _l is not None])


def uhunt_card(res: dict) -> str:
    """🕵️ USERNAME HUNTER ka card (v71.8) — sirf PUBLIC profiles."""
    res = res or {}
    un = str(res.get("username") or "")
    found = list(res.get("found") or [])
    unknown = list(res.get("unknown") or [])
    nf = int(res.get("not_found") or 0)
    ms = float(res.get("ms") or 0)
    EM = {"dev": "💻", "social": "💬", "creative": "🎨", "music": "🎵",
          "video": "🎬", "gaming": "🎮", "other": "🔹"}
    L = [pcard_title("🕵️", "USERNAME HUNTER"),
         f"🔎 <b>Username:</b> <code>{hesc(un)}</code>",
         pcard_sep()]
    if found:
        L.append(f"✅ <b>Mila — {len(found)} jagah:</b>")
        for it in found[:24]:
            L.append(f"├ {EM.get(str(it.get('cat')), '🔹')} "
                     f"<b>{hesc(str(it.get('site')))}</b> — "
                     f"<code>{hesc(str(it.get('url')))}</code>")
        L.append(pcard_sep())
    else:
        L.append("😕 <b>Kisi bhi site par ye username nahi mila.</b>")
        L.append(pcard_sep())
    _tail = f"❌ Nahi mila: <b>{nf}</b>"
    if unknown:
        _tail += f"  •  ⚪ Check nahi ho paya: <b>{len(unknown)}</b>"
    L.append(_tail)
    L.append(f"🕒 {int(res.get('checked') or 0)} sites · {ms / 1000:.1f}s")
    L.append("")
    L.append(BRAND_LINK)
    return "\n".join(L)


def whois_card(res: dict) -> str:
    """🌐 WEBSITE OWNER X-RAY ka card (v70).

    Sab data public registry (RDAP) se — koi link nahi, sab bot ke andar.
    """
    res = res or {}
    L = [pcard_title("🌐", "WEBSITE OWNER X-RAY")]
    L.append(f"🔖 <b>Domain:</b> <code>{hesc(str(res.get('domain') or ''))}</code>")

    _created, _age = str(res.get("created_fmt") or ""), str(res.get("age") or "")
    if _created:
        L.append(f"📅 <b>Banaya:</b> {hesc(_created)}"
                 + (f"  •  ⏳ {hesc(_age)} purana" if _age else ""))
    _exp, _dl = str(res.get("expires_fmt") or ""), res.get("days_left")
    if _exp:
        _dl_txt = ""
        if isinstance(_dl, int):
            _dl_txt = (f"  •  ⚠️ sirf {_dl} din bache" if 0 <= _dl <= 30
                       else (f"  •  ✅ {_dl} din bache" if _dl > 30 else "  •  ⛔ khatam ho gaya"))
        L.append(f"⌛ <b>Khatam:</b> {hesc(_exp)}{_dl_txt}")
    if res.get("changed_fmt"):
        L.append(f"🔄 <b>Last update:</b> {hesc(str(res['changed_fmt']))}")
    if res.get("registrar"):
        L.append(f"🏢 <b>Registry Company:</b> {hesc(str(res['registrar']))}")
    _own = str(res.get("registrant") or "").strip()
    L.append("👤 <b>Owner:</b> "
             + (hesc(_own) if _own else "🔒 Registry me chhupa hua (khula naam nahi mila)"))
    if res.get("nameservers"):
        L.append("🛰️ <b>Servers:</b> " + hesc(", ".join(res["nameservers"][:4])))
    if res.get("status"):
        L.append("📋 <b>Status:</b> " + hesc(" · ".join(res["status"])))
    _dn = str(res.get("dnssec") or "").lower()
    if _dn:
        L.append("🔐 <b>Extra Security:</b> "
                 + ("✅ haan (extra safe)" if _dn == "true" else "❌ nahi (basic hai)"))

    # aam aadmi ke liye seedha matlab
    # v70: umar "7 mahine" bhi ho sakti hai — sirf saal ginte hain (month bug fix)
    _age_s = str(res.get("age") or "")
    _ym = re.search(r"(\d+)\s*saal", _age_s)
    _mm = re.search(r"(\d+)\s*mahine", _age_s)
    _yrs = (int(_ym.group(1)) if _ym else 0) + ((int(_mm.group(1)) / 12) if _mm else 0)
    if _yrs >= 5:
        _verdict = "✅ Ye website purani hai — bharosa karne layak lagti hai."
    elif _yrs >= 2:
        _verdict = "🟡 Ye website 2-5 saal purani hai — theek hai, par badi payment se pehle soch lo."
    elif _yrs:
        _verdict = "🔴 Ye website nayi hai (2 saal se kam) — online paisa dene se pehle 100 baar soch lo."
    else:
        _verdict = ""
    L.append(pcard_sep())
    if _verdict:
        L.append(f"💡 <b>Matlab:</b> {_verdict}")
    L.append("ℹ️ Owner ka naam tabhi dikhta hai jab registry me khula ho — "
             "warna registry khud chhupa deti hai.")
    L.append(pcard_foot(ms=float(res.get("latency_ms") or 0),
                        source="public registry record (RDAP)"
                               + (" · cache" if res.get("cached") else "")))
    return "\n".join([_l for _l in L if _l])


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

    # ==================================================================
    #  v75 — 🧠 SMART DETECT ka 1-tap button (PRO ENGINE)
    #  ------------------------------------------------------------------
    #  User ne input bheja -> bot ne pahchana -> "chalaun?" button dikhaya.
    #  Ab wahi button daba hai. Hum user ka value server-side se uthate hain
    #  aur on_text ko bilkul WAISA hi Update dete hain jaise user ne wo text
    #  khud type kiya ho. Isliye tool ka poora flow, credits, rate-limit,
    #  VIP gate — sab exactly same rehta hai (koi shortcut nahi).
    # ==================================================================
    if data.startswith("pro_go:"):
        _tok = data.split(":", 1)[1]
        _hit = pro.pending_get(_tok)
        if not _hit:
            await safe_answer_cb(q, "Ye button purana ho gaya — value dobara bhejo", show_alert=True)
            return
        # VIP wall wahi lagti hai jo normal input par lagti hai
        if PREMIUM_ONLY and not vip_ok(uid):
            await send_vip_wall(update, context)
            return
        # ---- v75: EARNING RULE — credits gate (button path ki tarah hi) ----
        if is_premium_tool(_hit.action):
            _u_pg = get_user(uid, q.from_user.first_name or "")
            if not can_use_premium_tool(_u_pg, uid):
                await safe_answer_cb(q, "Credits khatam", show_alert=False)
                try:
                    await q.message.reply_text(get_credits_over_text(_hit.action),
                                               reply_markup=get_limit_exceeded_kb(),
                                               parse_mode=HTML)
                except Exception:                                # noqa: BLE001
                    pass
                return
        try:
            context.user_data["mode"] = _hit.action
            context.user_data["_pro_tool"] = _hit.label
            context.user_data["_pro_mode"] = _hit.action
            _m = Message(
                message_id=getattr(q.message, "message_id", 0) or 0,
                date=datetime.now(timezone.utc),
                chat=update.effective_chat,
                from_user=q.from_user,
                text=_hit.value,
            )
            try:
                _m.set_bot(context.bot)
            except Exception:                                    # noqa: BLE001
                pass
            _synth = Update(update_id=update.update_id, message=_m)
            await safe_answer_cb(q, f"⚡ {_hit.label} chalu…")
            await on_text(_synth, context)
        except Exception as _pe:                                 # noqa: BLE001
            log.warning("pro_go fail: %s", str(_pe)[:160])
            context.user_data.pop("mode", None)
            try:
                await q.message.reply_text(
                    f"⚠️ <b>{_hit.label}</b> abhi nahi chala.\n"
                    f"Value dobara bhejo (tool khud pahchan lega):\n<code>{_hit.value}</code>",
                    parse_mode=HTML)
            except Exception:                                    # noqa: BLE001
                pass
        return

    # ---------- v75.1: 📤 BULK MODE ke buttons ----------
    if data == "bulk_cancel":
        context.user_data.pop("mode", None)
        context.user_data.pop("bulk_kind", None)
        context.user_data.pop("bulk_entries", None)
        await safe_answer_cb(q, "Cancel ho gaya")
        await q.message.reply_text("❌ <b>Bulk mode band.</b>", parse_mode=HTML)
        return

    if data == "bulk_go":
        _bk = str(context.user_data.get("bulk_kind") or "")
        _be = list(context.user_data.get("bulk_entries") or [])
        if not _bk or not _be:
            await safe_answer_cb(q, "List purani ho gayi — dobara bhejo", show_alert=True)
            return
        _lim, _vip = BM.limits_for(uid)
        _be = _be[:_lim]
        # typing indicator — bhaari kaam ki suchna
        await safe_answer_cb(q, f"⚡ {len(_be)} entries check ho rahi hain…")
        _prog = await cbmsg().reply_text(
            f"⚡ <b>Chalu…</b> 0/{len(_be)}", parse_mode=HTML)
        _last = {"t": 0.0, "n": 0}

        def _on_prog(i, total):
            """Har entry par — par edit sirf har ~8 entries ya 1.2s me (limit safe)."""
            now = time.time()
            if i < total and (i - _last["n"]) < 8 and (now - _last["t"]) < 1.2:
                return
            _last["n"], _last["t"] = i, now
            try:
                asyncio.create_task(safe_edit(
                    _prog, f"⚡ <b>Chalu…</b> {i}/{total}", parse_mode="HTML"))
            except Exception:                                    # noqa: BLE001
                pass

        try:
            _res = await asyncio.to_thread(BM.run_bulk, _bk, _be, _on_prog)
        except Exception as _bex:                                # noqa: BLE001
            log.warning("bulk run fail: %s", str(_bex)[:150])
            _res = {"ok": False, "total": len(_be), "passed": 0, "failed": len(_be),
                    "rows": [], "headers": [], "kind": _bk, "seconds": 0}
        # progress message saaf
        try:
            await safe_delete(_prog)
        except Exception:                                        # noqa: BLE001
            pass
        if not _res.get("rows"):
            await cbmsg().reply_text(
                "❌ <b>Report nahi ban payi.</b>\n"
                "Ek-ek karke try karo, ya thodi der baad dobara bhejo.", parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        # Excel file banao + bhejo
        _fname = BM.file_name(_bk, int(_res.get("total") or len(_be)))
        _blob = await asyncio.to_thread(BM.to_xlsx, _res)
        if not _blob:
            _blob = await asyncio.to_thread(BM.to_csv, _res)
            _fname = _fname.rsplit(".", 1)[0] + ".csv"
        _cap = BM.bulk_result_text(_res, _bk, _vip)
        try:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=io.BytesIO(_blob), filename=_fname,
                caption=_cap, parse_mode=HTML)
        except Exception as _sd:                                 # noqa: BLE001
            log.warning("bulk send fail: %s", str(_sd)[:140])
            await cbmsg().reply_text(_cap, parse_mode=HTML)
        # earning: credit/use count
        try:
            add_use(uid)
            pro.record_result(uid, "bulk", title=f"Bulk ({_bk})",
                              ok=True, ms=int(float(_res.get("seconds") or 0) * 1000))
        except Exception:                                        # noqa: BLE001
            pass
        context.user_data.pop("mode", None)
        context.user_data.pop("bulk_kind", None)
        context.user_data.pop("bulk_entries", None)
        return

    # ---------- v75: 🗂️ /history ke buttons ----------
    if data == "pro_histclear":
        pro.results.clear(uid)
        await safe_answer_cb(q, "🧹 History saaf ho gayi")
        await q.message.reply_text("🧹 <b>History saaf ho gayi.</b>", parse_mode=HTML)
        return

    if data.startswith("pro_re:"):
        _tool = data.split(":", 1)[1]
        await safe_answer_cb(q, "🔁 Ready")
        context.user_data["mode"] = _tool
        context.user_data["_pro_tool"] = _tool
        context.user_data["_pro_mode"] = _tool
        await q.message.reply_text(
            f"🔁 <b>{_tool}</b> ready — apna input bhejo.", parse_mode=HTML)
        return

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
            "──────────────────────\n"
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
            "──────────────────────\n"
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
            "──────────────────────\n"
            f"📲 <b>Service:</b> {svc_name}\n"
            f"🌍 <b>Desh:</b> {ctry_name}\n"
            "⚡ <b>Agla step:</b> turant — admin ko message bhejo\n"
            "──────────────────────\n\n"
            "👉 Number lene ke liye neeche <b>Contact Admin</b> dabao:"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"💬 Admin se baat karo {SUPPORT_USERNAME}", url=contact_url)],
            [InlineKeyboardButton("🔁 Doosra chuno", callback_data="vnum_get")],
            [InlineKeyboardButton("⌨️ Menu", callback_data="back_home")],
        ])
        await _vnum_say(q, card, kb)
        return

    # ---------- 📋 RESULT CHECK (BSEB) wizard (v74.0) ----------
    if data in ("rc_new", "bsebr_new"):
        context.user_data["mode"] = "rc_board"
        context.user_data.pop("rcdb", None)
        context.user_data.pop("rc_code_val", None)
        await _vnum_say(q, _rc_pick_card(0), _rc_pick_kb(0))
        return

    if data == "rc_noop":
        await q.answer("Yahi page hai 🙂")
        return

    if data.startswith("rc_page:"):
        try:
            pg = int(data.split(":", 1)[1])
        except Exception:                                        # noqa: BLE001
            pg = 0
        context.user_data["mode"] = "rc_board"
        await _vnum_say(q, _rc_pick_card(pg), _rc_pick_kb(pg))
        return

    if data.startswith("rcb:"):
        key = data.split(":", 1)[1]
        if key not in BRD.BOARDS:
            await _vnum_say(q, _rc_pick_card(0), _rc_pick_kb(0))
            return
        context.user_data.pop("mode", None)
        _cap, _kb = rc_board_card(key)
        await _rc_say_photo(q, key, _cap, _kb)
        return

    if data.startswith("rc_how:"):
        # v74.3: gyaan card hata diya — purane message ka button ab card kholta hai
        key = data.split(":", 1)[1]
        _cap, _kb = rc_board_card(key)
        await _rc_say_photo(q, key, _cap, _kb)
        return

    if data.startswith("rc_cap:"):                     # v74.6: captcha bridge start
        key = data.split(":", 1)[1]
        _urls = RC_CAP_ENDPOINTS.get(key) or []
        _form = None
        _last_why = "form_nahi"
        for _u in _urls:
            _f = await asyncio.to_thread(CB.fetch_form, _u)
            if _f.get("ok"):
                _form = _f
                break
            _last_why = _f.get("why") or "form_nahi"
        context.user_data.pop("mode", None)
        if not _form:
            _kb = InlineKeyboardMarkup([[InlineKeyboardButton(
                "◀️ Saare boards", callback_data="rc_new")]])
            await _vnum_say(q, rcap_fail_card(_last_why, key), _kb)
            return
        context.user_data["mode"] = "rc_cap_ans"
        context.user_data["rcap"] = {"key": key, "form": _form, "tries": 0}
        _ask = ("🔐 <b>Captcha likho + Roll Number</b>\n"
                + ("<i>jaise: AB12C 1234567 dob</i>" if _form.get("needs_dob")
                   else "<i>jaise: AB12C 1234567</i>"))
        try:
            await q.message.delete()
        except Exception:                                    # noqa: BLE001
            pass
        try:
            await q.message.reply_photo(io.BytesIO(_form["img"]), caption=_ask,
                                        parse_mode=HTML)
        except Exception:                                    # noqa: BLE001
            await _vnum_say(q, _ask, None)
        return

    if data.startswith("rc_live:"):
        key = data.split(":", 1)[1]
        if key == "bseb":
            context.user_data["mode"] = "rc_exam"
            context.user_data.pop("rcdb", None)
            await _vnum_say(q, rc_exam_card(), _rc_exam_kb())
            return
        _cap, _kb = rc_board_card(key)
        await _rc_say_photo(q, key, _cap, _kb)
        return

    if data == "rc_back_ex":
        context.user_data["mode"] = "rc_exam"
        await _vnum_say(q, rc_exam_card(), _rc_exam_kb())
        return

    if data == "rc_back_yr":
        db = context.user_data.get("rcdb") or {}
        _ek = str(db.get("exam") or "matric")
        context.user_data["mode"] = "rc_year"
        await _vnum_say(q, rc_year_card(_ek), _rc_year_kb())
        return

    if data.startswith("rc_ex:"):
        key = data.split(":", 1)[1]
        if key not in BSEBR.EXAMS:
            await _vnum_say(q, rc_exam_card(), _rc_exam_kb())
            return
        db = context.user_data.get("rcdb") or {}
        db["exam"] = key
        context.user_data["rcdb"] = db
        context.user_data["mode"] = "rc_year"
        await _vnum_say(q, rc_year_card(key), _rc_year_kb())
        return

    if data.startswith("rc_yr:"):
        try:
            year = int(data.split(":", 1)[1])
        except Exception:                                        # noqa: BLE001
            year = BSEBR.CURRENT_YEAR
        db = context.user_data.get("rcdb") or {}
        _ek = str(db.get("exam") or "matric")
        db["year"] = year
        context.user_data["rcdb"] = db
        if year != int(BSEBR.CURRENT_YEAR):
            context.user_data.pop("mode", None)
            await _vnum_say(q, rc_archive_card(_ek, year),
                            InlineKeyboardMarkup([
                                [InlineKeyboardButton(f"✅ {BSEBR.CURRENT_YEAR} ka result dekho",
                                                      callback_data="rc_new")],
                                [InlineKeyboardButton("ℹ️ CBSE result?", callback_data="cbse_info")],
                                [InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")]]))
            return
        context.user_data["mode"] = "rc_code"
        await _vnum_say(q, rc_ask_code_card(_ek, year), _rc_step_kb())
        return

    if data == "rc_retry":
        db = context.user_data.get("rcdb") or {}
        _rc = str(db.get("rc") or "")
        _rn = str(db.get("rn") or "")
        if _rc and _rn:
            await q.answer("Dobara try kar raha hoon…")
            await rc_deliver(q.message, context, uid, _rc, _rn)
        else:
            context.user_data["mode"] = "rc_exam"
            await _vnum_say(q, rc_exam_card(), _rc_exam_kb())
        return

    if data == "cbse_info":
        await _vnum_say(q, cbse_info_card(), _rc_result_kb())
        return

    # ---------- 📞 TEMP MAIL (NUMBER) inline buttons (v71.9) ----------
    #  100% FREE tool (koi credit nahi) — har user ko apna ALAG number.
    #  Virtual Numbers (vnum) se bilkul alag hai: uska kaam admin/manual hai.
    if data == "tnum_open":
        await _vnum_say(q, TNUM_INTRO,
                        _tnum_ctry_kb(TNUM_ONE_SVC) if TNUM_ONE_SVC else _tnum_svc_kb())
        return

    if data.startswith("tnum_svc:"):
        sk = data.split(":", 1)[1]
        if sk not in TN.SVC_BY_KEY:
            sk = "whatsapp"
        context.user_data["tnum_svc"] = sk
        lbl, em, _rc = TN.SVC_BY_KEY.get(sk, ("App", "📱", ()))
        await _vnum_say(
            q,
            f"{em} <b>{to_bold('STEP 2: DESH CHUNO')}</b>\n"
            "──────────────────────\n"
            f"App: <b>{hesc(str(lbl))}</b>\n\n"
            "⭐ wale desh is app ke liye sabse best chalte hain.\n"
            "Neeche se desh chuno 👇",
            _tnum_ctry_kb(sk))
        return

    if data == "tnum_countries":
        sk = str(context.user_data.get("tnum_svc") or "whatsapp")
        lbl, em, _rc = TN.SVC_BY_KEY.get(sk, ("App", "📱", ()))
        await _vnum_say(
            q,
            f"{em} <b>{to_bold('DESH CHUNO')}</b>\n"
            "──────────────────────\n"
            f"App: <b>{hesc(str(lbl))}</b>\n\nNeeche se desh chuno 👇",
            _tnum_ctry_kb(sk))
        return

    if data.startswith("tnum_ctry:") or data == "tnum_change":
        sk = str(context.user_data.get("tnum_svc") or "")
        _me = _tnum_load().get(str(uid)) or {}
        if data == "tnum_change":
            cc = str(_me.get("cc") or "")
            if not cc:
                await _vnum_say(q, TNUM_INTRO, _tnum_svc_kb())
                return
            change = True
        else:
            cc = data.split(":", 1)[1]
            change = False
        _rlm = check_limit(uid, "tnum", limit=25, window=300,
                           bypass=has_unlimited(uid), tool_name="Temp Mail (Number)")
        if _rlm:
            await q.answer("Thoda slow 🙂", show_alert=False)
            await _vnum_say(q, _rlm, _tnum_ctry_kb(sk))
            return
        await q.answer("Number nikaal raha hoon... ⌛")
        rec, err = await asyncio.to_thread(tnum_get_number, uid, cc,
                                           sk or str(_me.get("svc") or ""), change)
        if not rec:
            await _vnum_say(
                q,
                "⚠️ <b>Number nahi mila.</b>\n"
                "──────────────────────\n"
                f"{hesc(str(err or 'Site slow hai — dobara try karo.'))}\n\n"
                "👉 Doosra desh chuno 👇",
                _tnum_ctry_kb(sk))
            return
        ib = await asyncio.to_thread(TN.inbox, rec["nid"])
        context.user_data["tnum_last_ref"] = 0
        await _vnum_say(q, tnum_card(rec, ib), _tnum_num_kb(rec))
        return

    if data == "tnum_refresh":
        _me = _tnum_load().get(str(uid)) or {}
        if not _me.get("nid"):
            await _vnum_say(q, TNUM_INTRO, _tnum_svc_kb())
            return
        _now = time.time()
        _last = float(context.user_data.get("tnum_last_ref") or 0)
        if _now - _last < TNUM_REFRESH_GAP:
            await q.answer(f"⏳ {int(TNUM_REFRESH_GAP - (_now - _last))}s baad dobara dabao 🙂",
                           show_alert=False)
            return
        _rlm = check_limit(uid, "tnum", limit=25, window=300,
                           bypass=has_unlimited(uid), tool_name="Temp Mail (Number)")
        if _rlm:
            await q.answer("Thoda slow 🙂", show_alert=False)
            await _vnum_say(q, _rlm, _tnum_num_kb(_me))
            return
        context.user_data["tnum_last_ref"] = _now
        await q.answer("🔁 Naye SMS dekh raha hoon...")
        ib = await asyncio.to_thread(TN.inbox, _me.get("nid"), 1.0, True)
        await _vnum_say(q, tnum_card(_me, ib), _tnum_num_kb(_me))
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
            "──────────────────────\n"
            f"💰 <b>Paisa:</b> ₹{amt}\n"
            f"🏦 <b>UPI ID:</b> <code>{UPI_ID}</code>\n"
            "──────────────────────\n"
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
            "──────────────────────\n"
            f"👤 <b>User:</b> <code>{target_uid}</code>\n"
            f"💰 <b>Amount:</b> ₹{pay.get('amount')}\n"
            f"👑 <b>Given:</b> {dur}\n"
            f"🕒 <b>Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            "──────────────────────\n"
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
                "──────────────────────\n"
                f"🧾 <b>Payment ID:</b> #{pid}\n"
                f"💰 <b>Amount:</b> ₹{pay.get('amount')}\n"
                f"👑 <b>VIP:</b> {dur}\n"
                f"📅 <b>Valid till:</b> {exp}\n"
                "──────────────────────\n"
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
            f"📜 <b>Manual VIP Log (last {len(rows)})</b>\n──────────────────────\n" + "\n".join(lines) +
            "\n──────────────────────\n<i>These are the VIPs you gave with /activate (no payment).</i>",
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
            "🧾 <b>My Payments</b>\n──────────────────────\n" + "\n".join(lines) +
            "\n──────────────────────\n⏳ = admin is verifying · ✅ = VIP active · ❌ = rejected",
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
            "🧾 <b>Last 10 Payments</b>\n──────────────────────\n" + "\n".join(lines) +
            f"\n──────────────────────\n💰 Revenue: ₹{ps['revenue']:,} · ✅ {ps['approved']} · ❌ {ps['rejected']} · ⏳ {ps['pending']}",
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
            "──────────────────────\n"
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
    # ---------- v64: 📥 VIDEO DOWNLOADER ke 27 tools ----------
    # v66: 🎯 27-app ka PICKER HATA DIYA (user ka order).
    # Purane message par ye button dabaya jaye to naya tarika batao —
    # picker dobara na khule.
    if data == "dlmenu" or data.startswith("dlvpage:"):
        context.user_data.pop("mode", None)
        await safe_answer_cb(q, "Ab har app apna alag tool hai ⬇️")
        _hint = ("🎯 <b>BADLAV — ab har app APNA ALAG TOOL hai</b>\n"
                 "──────────────────────\n"
                 "Pehle sab apps ek hi menu me the. Ab keyboard par "
                 "<b>neeche wale</b> buttons dikhenge:\n"
                 "   📸 INSTA DL · ▶️ YOUTUBE DL · 📘 FACEBOOK DL · 🎵 TIKTOK DL\n\n"
                 "👉 Keyboard par <b>neeche</b> daba ke apna app chuno, "
                 "ya seedha <b>link bhej do</b> — main khud pehchan lunga.\n\n"
                 "📋 Poori list: <b>ALL TOOLS (FREE)</b> dabao.")
        await safe_reply(q.message, _hint, parse_mode=HTML)
        return
    if data.startswith("dlv:"):
        _dk = str(data).split(":", 1)[1]
        if _dk == "any":                 # v66.1: purana "sabhi apps" tool gaya
            context.user_data.pop("mode", None)
            await safe_answer_cb(q, "Ye purana tool hata diya gaya", show_alert=True)
            await safe_reply(q.message,
                             "❌ <b>\"VIDEO DOWNLOADER\" (sabhi apps wala) tool "
                             "hata diya gaya hai</b>\n\n"
                             "Ab <b>har app ka apna alag tool</b> hai 👇\n"
                             + dl_tools_text(),
                             parse_mode=HTML)
            return
        if _dk not in DL_SITES:
            await safe_answer_cb(q, "Ye app nahi mila", show_alert=True)
            return
        _dmode = "dl_" + _dk
        context.user_data["mode"] = _dmode
        context.user_data.pop("biz_step", None)
        context.user_data.pop("biz_ans", None)
        await safe_answer_cb(q, "Link bhejein 👇")
        _head = ("🌐 <b>SABHI APPS KA DOWNLOADER</b>" if _dk == "any"
                 else f"{DL_SITES[_dk][0]} <b>{hesc(DL_SITES[_dk][1])} DOWNLOADER</b>")
        _body = (f"{_head}\n"
                 f"──────────────────────\n"
                 f"✨ Is app ka video / reel / shorts ka <b>link bhejein</b>:\n\n"
                 f"💡 <b>Example:</b> <code>{(DL_SITES[_dk][3] if _dk != 'any' else 'https://www.instagram.com/reel/xxxxx')}</code>\n\n"
                 f"✅ HD · bina watermark · no ad")
        await safe_reply(q.message, _body, parse_mode=HTML,
                         reply_markup=InlineKeyboardMarkup([[
                             InlineKeyboardButton("🏠 Home", callback_data="back_home")]]))
        return

    # v76: 💰 EARN STUDIO — 5 naye kamai wale tools ka apna menu
    if data == "earnstudio":
        context.user_data["mode"] = "earn_menu"
        await safe_edit(q.message, EARN_MENU_TEXT, reply_markup=earn_menu_kb(),
                        parse_mode=HTML)
        return

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
        context.user_data["mode"] = _key
        context.user_data.pop("biz_wait", None)
        context.user_data.pop("biz_ans", None)
        _steps_v = biz_steps(_key)
        if _steps_v:
            # v63: EK-EK STEP me poocho — step 1 se shuru
            await safe_answer_cb(q, "Chaliye, step by step 👇")
            context.user_data["biz_step"] = 0
            await safe_reply(q.message, biz_step_prompt(_key, 0),
                             reply_markup=biz_steps_kb(_key, 0), parse_mode=HTML)
            return
        await safe_answer_cb(q, "Bhejein 👇")
        _bk = _biz_kind(_key.replace("biz_", ""))
        await safe_reply(q.message, tool_prompt(_bk or _key), parse_mode=HTML,
                         reply_markup=InlineKeyboardMarkup([[
                             InlineKeyboardButton("⬅️ Business Studio", callback_data="bizstudio"),
                             InlineKeyboardButton("🏠 Home", callback_data="back_home")]]))
        return

    # v63: wizard ka ⬅️ Peeche / step-jump button
    if data.startswith("bizstep:"):
        try:
            _sp = data.split(":", 2)
            _k2, _i2 = _sp[1], int(_sp[2])
        except Exception:                                        # noqa: BLE001
            await safe_answer_cb(q, "Kuch gadbad hai", show_alert=True)
            return
        if _k2 not in BIZ_MENU:
            await safe_answer_cb(q, "Tool nahi mila", show_alert=True)
            return
        _n2 = biz_total_steps(_k2)
        _i2 = max(0, min(_i2, max(0, _n2 - 1)))
        context.user_data["mode"] = _k2
        context.user_data["biz_step"] = _i2
        await safe_answer_cb(q, "Theek hai 👇")
        try:
            await safe_edit(q.message, biz_step_prompt(_k2, _i2),
                            reply_markup=biz_steps_kb(_k2, _i2), parse_mode=HTML)
        except Exception:                                        # noqa: BLE001
            await safe_reply(q.message, biz_step_prompt(_k2, _i2),
                             reply_markup=biz_steps_kb(_k2, _i2), parse_mode=HTML)
        return

    if data == "cloner_guide":
        await q.message.reply_text(

            "🔄 <b>AUTO FORWARD (CLONER) — 3 STEP</b>\n"
            "──────────────────────\n"
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
            "──────────────────────\n"
            "<b>Step 1:</b> SOURCE channel set karo (posts yahan se aayenge)\n"
            "<b>Step 2:</b> TARGET channel set karo (posts yahan jayenge)\n"
            "<b>Step 3:</b> FULL AUTO CHALU karo\n"
            "──────────────────────\n"
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
        await q.message.reply_text("🧪 <b>TEST RESULT</b>\n──────────────────────\n" + "\n".join(lines), parse_mode=HTML)
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
                "──────────────────────\n"
                "First tell the <b>state</b>: <code>Bihar</code> / <code>UP</code> / <code>Jharkhand</code>\n"
                "<i>(Bihar: stamp 6.5% + registration 3% · 1% less for women/joint)</i>", parse_mode=HTML)
            return
        if kind == "land":
            context.user_data["mode"] = "kagaz_land_value"
            await q.message.reply_text(
                f"📐 <b>{to_bold('BIGHA / KATTHA / DHUR CONVERTER')}</b>\n"
                "──────────────────────\n"
                "Type the area — example:\n"
                "• <code>2 bigha</code>\n• <code>5 katha</code>\n• <code>10 decimal</code>\n• <code>1200 sqft</code>\n"
                "• <code>3 dhur</code> / <code>1 acre</code> / <code>2.5 gaj</code>\n"
                "──────────────────────\n"
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
            L = ["🔑 <b>AAPKE OTP / CODES</b>", "──────────────────────"]
            for c in codes[:5]:
                _src = f"\n   <i>se: {hesc(str(c.get('subject') or c.get('from') or '')[:44])}</i>"
                L.append(f"  👉 <code>{hesc(str(c['code']))}</code>"
                         f"  ({hesc(str(c.get('label') or ''))}){_src}")
            L.append("\n──────────────────────")
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
             "──────────────────────"]
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
        # v65: "30 second - 2 minute" wala message HATA diya.
        #      Ab turant shuru + har 5 second live timer (15 second ka target).
        _stop_ping(context)
        _yt_stop = asyncio.Event()
        context.user_data["_ping_stop"] = _yt_stop
        _raw_st = await q.message.reply_text(
            f"⚡ <b>{h}p</b> — kaam shuru ho gaya!\n"
            "🔄 <i>Video download ho rahi hai… zyada se zyada 30 second.</i>",
            parse_mode=HTML)
        st = _StatusMsg(_raw_st, _yt_stop)
        asyncio.create_task(_progress_edit(
            _raw_st, f"⚡ <b>{h}p</b> — download chal raha hai…",
            every=PROGRESS_EVERY, stop=_yt_stop, max_pings=12))
        # v68: yahi video+quality pehle bheji thi? file_id se TURANT
        _fidq = dl_fid_get(url, f"q{h}")
        if _fidq:
            try:
                await q.message.reply_video(
                    video=_fidq, supports_streaming=True, parse_mode=HTML,
                    caption=(f"⚡ <b>INSTANT</b> — {h}p video pehle hi ready thi "
                             f"(0.1 second)"))
                await st.delete()
                add_use(uid)
                await q.message.reply_text(spend_credit_msg(uid, "insta_dl"),
                                           parse_mode=HTML)
                return
            except Exception:                                    # noqa: BLE001
                dl_fid_forget(url, f"q{h}")
        _qres = await with_tool_timeout(
            asyncio.to_thread(_yt_quality_download, url, h), 40, "yt-quality")
        res = _qres or {"ok": False,
                        "error": ("⏱️ 40 second me video taiyaar nahi hui — "
                                  "chhoti quality (360p) try karo. Credit nahi katta.")}
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
        _sentq = await q.message.reply_video(
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
        # v68: agli baar ke liye file_id yaad rakho (0.1 second delivery)
        try:
            dl_fid_set(url, _sentq.video.file_id, f"q{h}")
        except Exception:                                        # noqa: BLE001
            pass
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
            "──────────────────────\n"
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


# ======================================================================
#  v75.1/v75.2 — 📤 BULK MODE (EXCEL) — earning tool
#  ------------------------------------------------------------------
#  User apni list deta hai (paste ya .xlsx/.csv/.txt FILE) -> hum pahchante
#  hain, confirm button dete hain, phir parallel engine se saara check karke
#  Excel bhejte hain.
#  File support zaroori tha: CA / bank agent / insurance agent ke paas list
#  FILE me hoti hai — "paste karo" unke liye ajeeb lagta hai.
# ======================================================================
async def _bulk_offer(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      raw_text: str, source_name: str = "") -> None:
    """List (paste ya file se) pahchano -> confirm card dikhao."""
    uid = update.effective_user.id if update.effective_user else 0
    _b_lim, _b_vip = BM.limits_for(uid)
    _ents, _lines = BM.extract_entries(raw_text, limit=BM.VIP_LIMIT)
    if not _ents:
        await update.message.reply_text(
            "📤 <b>List khaali lagi.</b>\n"
            "Ek-ek entry nayi line me bhejo — ya <b>.xlsx / .csv / .txt</b> file "
            "bhej do (dono chalta hai).", parse_mode=HTML)
        return
    _b_kind, _b_match, _b_samp = BM.detect_kind(_ents)
    if not _b_kind:
        await update.message.reply_text(
            "❓ <b>List pahchan nahi paya.</b>\n"
            "Ye 5 cheezein chalti hain:\n"
            "• 🏦 IFSC code (SBIN0001234)\n"
            "• 📮 Pincode (800001)\n"
            "• 📱 Mobile number (9876543210)\n"
            "• 🚗 Gaadi number (BR01AB1234)\n"
            "• 🔍 Link (https://…)\n\n"
            "Sahi format me dobara bhejo.", parse_mode=HTML)
        return
    _b_good, _b_skip = BM.filter_valid(_b_kind, _ents)
    if not _b_good:
        await update.message.reply_text("❌ Koi sahi entry nahi mili — format check karo.",
                                        parse_mode=HTML)
        return
    context.user_data["bulk_kind"] = _b_kind
    context.user_data["bulk_entries"] = _b_good[:BM.VIP_LIMIT]
    _cnt = min(len(_b_good), _b_lim)
    _kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Chalu karo ({_cnt} entries)", callback_data="bulk_go")],
        [InlineKeyboardButton("❌ Cancel", callback_data="bulk_cancel")],
    ])
    _card = (BM.table_preview_text(_b_kind, len(_b_good), _b_match, _b_samp, _lines,
                                   _b_vip, _b_lim, source_name=source_name)
             if source_name else
             BM.preview_text(_b_kind, len(_b_good), _b_match, _b_samp, _lines,
                             _b_vip, _b_lim))
    if _b_skip:
        _card += f"\n⚠️ <i>{_b_skip} line skip hui (format match nahi)</i>"
    if len(_b_good) > _b_lim:
        _card += (f"\n⚠️ <i>{len(_b_good) - _b_lim} extra entries chhoot jayengi "
                  f"(free limit {_b_lim})</i>")
    await update.message.reply_text(_card, reply_markup=_kb, parse_mode=HTML)


async def on_bulk_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """v75.2: BULK MODE me user FILE bheje (.xlsx / .csv / .txt) -> wahi flow.

    Ye handler group=-4 me chalta hai (cookies handler ke baad, baaki sabse
    pehle). File handle ho gayi to `ApplicationHandlerStop` raise karte hain —
    isse baaki handlers (media/downloader) use dobara nahi chhoote.
    """
    try:
        msg = update.effective_message
        u = update.effective_user
        if not msg or not msg.document or u is None:
            return
        if str(context.user_data.get("mode") or "") != "bulk_wait":
            return                                  # bulk mode me nahi hai -> aage jao
        doc = msg.document
        _name = (doc.file_name or "").lower()
        if not _name.endswith((".xlsx", ".xlsm", ".csv", ".txt", ".tsv")):
            raise ApplicationHandlerStop            # koi aur file -> normal handler
        if (doc.file_size or 0) > 8 * 1024 * 1024:
            await msg.reply_text("❌ File bahut badi hai (8 MB se kam bhejo).",
                                 parse_mode=HTML)
            raise ApplicationHandlerStop
        _wait = await msg.reply_text("📥 <b>File padh raha hoon…</b>", parse_mode=HTML)
        try:
            _f = await context.bot.get_file(doc.file_id)
            _blob = bytes(await _f.download_as_bytearray())
            _txt = await asyncio.to_thread(BM.read_table_bytes, doc.file_name or "", _blob)
        except Exception as _fe:                                 # noqa: BLE001
            log.warning("bulk file read fail: %s", str(_fe)[:140])
            _txt = ""
        if not _txt.strip():
            await _wait.edit_text(
                "❌ <b>File padhi nahi gayi.</b>\n"
                "Excel (.xlsx) ya CSV (.csv) bhejo — ya list seedha chat me paste kar do.",
                parse_mode=HTML)
            raise ApplicationHandlerStop
        try:
            await safe_delete(_wait)
        except Exception:                                        # noqa: BLE001
            pass
        await _bulk_offer(update, context, _txt, source_name=doc.file_name or "file")
        # ⚠️ ZAROORI: yahin rok do. Warna wahi Excel file group-0 ke media
        # handler ko bhi mil jaati hai (downloader "unknown file" reply kar deta)
        # — user ko do jawab aate aur confusion hota.
        raise ApplicationHandlerStop
    except ApplicationHandlerStop:
        raise
    except Exception as _be:                                     # noqa: BLE001
        log.warning("on_bulk_file skip: %s", str(_be)[:140])
        raise ApplicationHandlerStop


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
        # v56.0: user order par 4 tools PERMANENTLY delete —
        # (1) 🌐 DOMAIN OSINT / IP  (2) 📄 WEB SCRAPER
        # (3) 🪪 AADHAAR EID       (4) 📡 TG PUBLIC INFO
        "DOMAIN OSINT / IP", "DOMAIN OSINT", "OSINT", "DOMAIN INFO",
        "IP INFO", "IP / DOMAIN INFO", "IP", "DOMAIN",
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
            "──────────────────────\n"
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

        # 1b. v71.9: 📞 TEMP MAIL (NUMBER) — 100% FREE, koi credit nahi.
        #     Ye alag tool hai (Virtual Numbers se bilkul alag).
        if action == "tnum":
            await send_tnum_card(update, context)
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
                "──────────────────────\n"
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

        # 3a-bulk. v75.1: 📤 BULK MODE (EXCEL) — earning tool
        if action == "bulk":
            context.user_data["mode"] = "bulk_wait"
            context.user_data["_pro_tool"] = "Bulk Mode"
            context.user_data["_pro_mode"] = "bulk"
            _bd, _ = BM.limits_for(uid)
            await update.message.reply_text(BM.bulk_intro_text(vip=_bd >= BM.VIP_LIMIT),
                                            parse_mode=HTML)
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
        # 3d-2. v76: 💰 EARN STUDIO (5 naye kamai wale tools)
        if action == "earnstudio":
            context.user_data["mode"] = "earn_menu"
            await update.message.reply_text(EARN_MENU_TEXT, reply_markup=earn_menu_kb(),
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
                "──────────────────────\n"
                "🔗 <b>Link/Text</b> — website, YouTube, any text\n"
                "📶 <b>WiFi</b> — guests scan and connect, no password to tell\n"
                "👤 <b>Contact Card</b> — scan and the contact saves",
                reply_markup=kb, parse_mode=HTML)
            return

        if action == "dl_gone":            # v66.1: purane "VIDEO DOWNLOADER" label
            context.user_data.pop("mode", None)
            await update.message.reply_text(
                "❌ <b>\"VIDEO DOWNLOADER\" tool HATA diya gaya hai</b>\n"
                "──────────────────────\n"
                "Ab <b>har app ka apna ALAG tool</b> hai — jaise NUMBER INFO, "
                "IMEI, CHANNEL CLONER alag-alag hain:\n\n"
                + dl_tools_text()
                + "\n\n👉 Keyboard par <b>neeche</b> wo 4 buttons dikhte hain — "
                "apna app dabao aur link bhejo.\n"
                "✅ HD video, bina watermark, 15 second ke andar.",
                reply_markup=main_keyboard(is_admin(update.effective_user.id)),
                parse_mode=HTML)
            return

        if action == "dlmenu":            # purane keyboard ka picker button
            context.user_data.pop("mode", None)
            await update.message.reply_text(
                "🎯 <b>Ab har app ka apna ALAG tool hai</b>\n"
                "──────────────────────\n"
                + dl_tools_text()
                + "\n\n👉 Keyboard par <b>neeche</b> wale buttons dabao — "
                "📸 INSTA DL, ▶️ YOUTUBE DL, 📘 FACEBOOK DL …",
                parse_mode=HTML)
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
                "──────────────────────\n"

                "You are the owner of this bot — everything is unlimited ✅\n"
                "• No daily limit\n"
                "• No VIP payment\n"
                "• All tools are open\n"
                "──────────────────────\n"
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

        # v73.1: 📋 RESULT CHECK (BSEB) + CBSE jaankari — apna card + inline buttons
        if action == "bsebr":
            context.user_data["mode"] = "rc_board"
            context.user_data.pop("rcdb", None)
            await update.message.reply_text(_rc_pick_card(0),
                                            reply_markup=_rc_pick_kb(0),
                                            parse_mode=HTML)
            return
        if action == "bsebr_direct":
            context.user_data["mode"] = "rc_exam"
            context.user_data.pop("rcdb", None)
            await update.message.reply_text(rc_exam_card(),
                                            reply_markup=_rc_exam_kb(),
                                            parse_mode=HTML)
            return
        if action == "cbse_info":
            await update.message.reply_text(cbse_info_card(),
                                            reply_markup=_rc_result_kb(), parse_mode=HTML)
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

    # ==================================================================
    #  v75 — 🧠 SMART DETECT (PRO ENGINE, ENGINE-1)
    #  ------------------------------------------------------------------
    #  NAYA BEHAVIOUR: user ko button dabane ki zaroorat hi nahi.
    #  Wo seedha "SBIN0001234" ya "9876543210" ya ek link bhej de — bot
    #  khud pahchan leta hai ki ye kya hai aur SAHI tool chala deta hai.
    #
    #  Kab chalta hai (teeno sach hone chahiye):
    #    1. Koi tool mode already active na ho (warna user ka input chori na ho)
    #    2. Text kisi button se match na hua ho
    #    3. User ne smart detect band na kiya ho (/smart se toggle)
    #
    #  High-confidence input (IFSC / IMEI / mobile / URL / gaadi / GST / PAN)
    #  = turant chalta hai. Medium (pincode / username / domain / email)
    #  = 1-tap confirm button, khud se nahi chalta (galat tool na khule).
    # ==================================================================
    if not action and not mode and raw_text and len(raw_text) <= 300 \
            and pro.AUTO_MODE != "off" and pro.detect_enabled(uid):
        try:
            _hit = pro.detect(raw_text)
            if _hit:
                _autoran = bool(_hit.high and _hit.action in pro._AUTORUN)
                # ---- v75: EARNING RULE — premium tool ka credit gate ----------
                #  Auto-run se credits bypass NAHI hone chahiye. Ye bilkul wahi
                #  check hai jo button dabane par lagta hai (isliye earning model
                #  auto-detect se bilkul nahi tootta).
                if _autoran and is_premium_tool(_hit.action):
                    _u_p = get_user(uid, user.first_name or "")
                    if not can_use_premium_tool(_u_p, uid):
                        await update.message.reply_text(
                            get_credits_over_text(_hit.action),
                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
                        return
                if _autoran and pro.AUTO_MODE == "auto":
                    context.user_data["mode"] = _hit.action
                    context.user_data["_pro_tool"] = _hit.label
                    context.user_data["_pro_mode"] = _hit.action
                    mode = _hit.action
                    try:
                        await update.message.reply_text(
                            f"{_hit.get('emoji') or '🧠'} <b>{_hit.label}</b> chala raha hoon…",
                            parse_mode=HTML)
                    except Exception:                            # noqa: BLE001
                        pass
                else:
                    _skb = pro.smart_kb(_hit)
                    if _skb is not None:
                        await update.message.reply_text(pro.smart_line(_hit),
                                                        reply_markup=_skb,
                                                        parse_mode=HTML)
                        return
        except Exception as _pe:                                 # noqa: BLE001
            log.debug("smart detect skip: %s", str(_pe)[:110])

    # ---------- v75: is run ka naam record karo (analytics ke liye) ----------
    #  Kaunsa tool chal raha hai — `_pro_tool` me daal do. Handler poora hone
    #  par `_on_text_pro` wrapper ise padh kar result history + tool stats me
    #  likh deta hai (koi tool ka code chhue bina).
    if mode and not context.user_data.get("_pro_tool"):
        _mkey = str(mode)
        _ptn = None
        if _mkey in TOOL_RATE_LIMITS:
            _ptn = TOOL_RATE_LIMITS[_mkey][2]
        else:
            for _k in TOOL_RATE_LIMITS:
                if _mkey.startswith(_k + "_"):
                    _ptn = TOOL_RATE_LIMITS[_k][2]
                    break
        context.user_data["_pro_tool"] = _ptn or _mkey.replace("_", " ").title()
        context.user_data["_pro_mode"] = _mkey

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
            f"👤 <b>USER DETAIL</b>\n──────────────────────\n"
            f"🆔 <b>ID:</b> <code>{target}</code>\n"
            f"👋 <b>Name:</b> {hesc(str(row.get('name') or u.get('name') or '-'))}\n"
            f"👑 <b>VIP:</b> {'👑 LIFETIME' if prem == 'lifetime' else (premium_expiry(u) if prem else '❌ No')}\n"
            f"⚡ <b>Uses today:</b> {u.get('uses_today', 0)}\n"
            f"🎟️ <b>Credits left:</b> {get_credits(target)} / {CREDITS_START}\n"
            f"🚫 <b>Banned:</b> {'Yes' if u.get('banned') else 'No'}\n"
            f"📜 <b>Payments:</b> ✅ {hist['approved']} · ❌ {hist['rejected']} · ⏳ {hist['pending']}\n"
            "──────────────────────",
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
                "──────────────────────\n"
                f"📝 <b>You sent:</b> <code>{hesc(raw_text[:40])}</code>\n"
                f"⚠️ <b>Reason:</b> {res.get('reason')}\n"
                "──────────────────────\n"
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
            "──────────────────────\n"
            f"🧾 <b>UTR:</b> <code>{hesc(utr)}</code>\n"
            f"📋 <b>Type:</b> {res.get('kind')}\n"
            f"💎 <b>Plan:</b> {plan['name']} (₹{plan['price']})\n"
            "──────────────────────\n"

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
        _key_b = str(mode)
        _steps_b = biz_steps(_key_b)

        # ---------- v63: STEP-BY-STEP WIZARD ----------
        if _steps_b:
            _idx_b = int(context.user_data.get("biz_step") or 0)
            _ans_b = dict(context.user_data.get("biz_ans") or {})
            _txt_b = str(raw_text or "").strip()

            # SMART: step 1 me hi poori line (jaise "A | B | C") aa gayi?
            # to poora jawab maan lo aur seedha file bana do (purana tarika chalta rahe).
            if _idx_b == 0 and _txt_b.count("|") >= 1 and len(_txt_b) > 12:
                _d0 = biz_parse(_key_b, _txt_b, _owner.strip())
                _r0 = await asyncio.get_running_loop().run_in_executor(
                    None, functools_partial(biz_build, _key_b, _d0))
                context.user_data.pop("biz_step", None)
                context.user_data.pop("biz_ans", None)
                _ok0 = bool(_r0 and _r0.get("ok"))
                if _ok0 and not ALL_FREE:
                    spend_credits(uid, 1)
                await biz_send_result(update.message, _key_b, _r0 or {}, uid, used=_ok0)
                return

            # SKIP / nahi / -  -> step khali
            if _txt_b.upper() in ("SKIP", "-", "NAHI", "NO", "NONE", "❌"):
                _txt_b = ""
            _fld_b, _q_b, _hint_b, _isphoto_b = _steps_b[min(_idx_b, len(_steps_b) - 1)][:4]
            if not _isphoto_b:
                _ans_b[_fld_b] = _txt_b
            context.user_data["biz_ans"] = _ans_b
            _idx_b += 1

            if _idx_b < len(_steps_b):
                context.user_data["biz_step"] = _idx_b
                await safe_reply(update.message, biz_step_prompt(_key_b, _idx_b),
                                 reply_markup=biz_steps_kb(_key_b, _idx_b), parse_mode=HTML)
                return

            # saare step ho gaye -> file banao
            context.user_data.pop("biz_step", None)
            context.user_data.pop("biz_ans", None)
            _d = biz_answers_to_dict(_key_b, _ans_b)
            _res = await asyncio.get_running_loop().run_in_executor(
                None, functools_partial(biz_build, _key_b, _d))
            _used = bool(_res and _res.get("ok"))
            if _used and not ALL_FREE:      # v61: free mode me credit nahi katta
                spend_credits(uid, 1)
            await biz_send_result(update.message, _key_b, _res or {}, uid, used=_used)
            return

        # ---------- purana ONE-LINE tarika (agar upar wale steps na hon) ----------
        _d = biz_parse(_key_b, raw_text, _owner.strip())
        _res = await asyncio.get_running_loop().run_in_executor(
            None, functools_partial(biz_build, _key_b, _d))
        _used = bool(_res and _res.get("ok"))
        if _used and not ALL_FREE:      # v61: free mode me credit nahi katta
            spend_credits(uid, 1)
        await biz_send_result(update.message, _key_b, _res or {}, uid, used=_used)
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
            await st.edit_text(cap.strip(), parse_mode=HTML)
        add_use(uid)
        return

    # UNIVERSAL VIDEO DOWNLOADER (Instagram + YouTube + Facebook + X + TikTok + 20 platforms)
    # v64: 27 alag downloader tools — sab isi engine par chalte hain,
    # bas platform ka naam/check alag. Purana "insta_dl" bhi waise hi chalta hai.
    _dl_mode_orig = str(mode or "")
    _dl_here = dl_key_of(_dl_mode_orig)
    if _dl_here:
        mode = "insta_dl"
    if mode == "insta_dl":
        if not is_supported_video_url(raw_text):
            await update.message.reply_text(
                fail_msg("UNSUPPORTED LINK",
                         "This link is not supported. Send links from Instagram, YouTube, Facebook or TikTok."),
                parse_mode=HTML,
            )
            return

        plat = platform_name(raw_text)
        # v64: agar user sahi tool me nahi hai to use batao (par kaam ho jaye)
        if _dl_here and not dl_url_matches(_dl_mode_orig, raw_text):
            try:
                await update.message.reply_text(
                    f"ℹ️ Ye link <b>{hesc(plat)}</b> ka hai — aap "
                    f"<b>{hesc(DL_SITES[_dl_here][1])}</b> ke tool me hain.\n"
                    f"Koi baat nahi, main phir bhi download kar deta hoon 👇\n"
                    f"<i>(Agli baar sahi app ka tool chuno — keyboard par "
                    f"neeche 📸 INSTA DL · ▶️ YOUTUBE DL · 📘 FACEBOOK DL · 🎵 TIKTOK DL.)</i>",
                    parse_mode=HTML)
            except Exception:                                    # noqa: BLE001
                pass
        _u = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u, uid):
            await update.message.reply_text(get_credits_over_text("insta_dl"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        # v65: TURANT jawab (1 second me) — user ko pata chale bot kaam kar raha hai
        _stop_ping(context)
        st = await update.message.reply_text(
            f"⚡ <b>{hesc(plat)}</b> — link mil gaya!\n"
            f"🔄 Download shuru kar diya… <i>(HD, bina watermark)</i>\n"
            f"⏱️ <i>Zyada se zyada <b>30 second</b> — warna main direct link de dunga.</i>",
            parse_mode=HTML)
        # v65: progress pinger — har 5 second "ho raha hai" (user ko lage na ki bot mar gaya)
        _ping_stop = asyncio.Event()
        _ping_task = asyncio.create_task(_progress_pinger(
            update.message,
            lambda el: (f"⏳ <b>{hesc(plat)}</b> — kaam chal raha hai… ({el}s)\n"
                        "🔄 <i>Bas thoda sa aur — file taiyaar ho rahi hai.</i>"),
            every=5, stop=_ping_stop))
        context.user_data["_ping_stop"] = _ping_stop
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
        # v68: ⚡ INSTANT REPEAT — yahi video pehle bheji thi? file_id se TURANT bhejo
        _fid = dl_fid_get(raw_text)
        if _fid:
            try:
                await update.message.reply_video(
                    video=_fid, supports_streaming=True, parse_mode=HTML,
                    caption=(f"⚡ <b>{to_bold('INSTANT')}</b> — ye video pehle hi "
                             f"download ho chuki thi (0.1 second)\n"
                             f"📥 {hesc(plat)} • HD • bina watermark"))
                _ev = context.user_data.get("_ping_stop")
                if _ev is not None:
                    _ev.set()
                add_use(uid)
                await st.delete()
                await update.message.reply_text(spend_credit_msg(uid, "insta_dl"),
                                                parse_mode=HTML)
                return
            except Exception:                                    # noqa: BLE001
                dl_fid_forget(raw_text)      # purana file_id kharab — dobara download

        # v68: hard timeout — koi bhi tool bot ko 40 second se zyada nahi rok sakta
        res = await with_tool_timeout(download_video_async(raw_text), 40, "video-dl")
        if res is None:
            res = {"ok": False,
                   "error": ("⏱️ Server ne 40 second me jawab nahi diya (link bhaari "
                             "ya platform slow hai).\n✅ <b>Dobara try karo</b> — doosri "
                             "baar cache se TURANT milega.\n💳 Credit nahi katta.")}

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
                _sent = await update.message.reply_video(
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
                # v68: agli baar ke liye file_id yaad rakho (0.1 second delivery)
                try:
                    dl_fid_set(raw_text, _sent.video.file_id)
                except Exception:                                # noqa: BLE001
                    pass
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
                fail_msg("SEND FAILED", "Got the media but Telegram did not accept it."),
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
                "──────────────────────\n"
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
                _cap = _cap.replace("──────────────────────\n<i>Public in-game",
                                    f"• <b>Character:</b> {hesc(str(res['character_name']))}\n"
                                    "──────────────────────\n<i>Public in-game", 1)
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
                    "──────────────────────\n"
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
                 + "\n──────────────────────"]

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
            L.append("\n──────────────────────")
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
            "──────────────────────\n"
            f"📮 <b>Aapka ek-baar email:</b>\n"
            f"<code>{hesc(res['address'])}</code>\n"
            f"🌐 Domain: <code>{hesc(str(res.get('domain') or ''))}</code>\n"
            "──────────────────────\n"
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
                "──────────────────────\n"
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

        # v75 — ⚡ SPEED FIX (PRO ENGINE): pehle yahan `asyncio.gather` tha.
        #  gather SLOWEST source ka wait karta hai. Agar ek source dead/slow ho
        #  (provider API 9 second leta hai, hub 200ms me jawab de chuka hai) to
        #  bhi user 9 second wait karta tha — "bot atka hua" lagta tha.
        #  Ab `gather_soon`: jo jawab time ke andar aa gaya, wahi use hota hai.
        #  Slow source ko chhod diya jaata hai (fallback pehle se neeche hai).
        _pair, _ms = await pro.gather_soon(
            [asyncio.to_thread(numprov.lookup, raw_text),
             asyncio.to_thread(hubapi.hub_carrier_info, raw_text)],
            timeout=float(os.environ.get("NUMINFO_WAIT_S", "8")),
        )
        _prov = _pair[0] if (_pair and isinstance(_pair[0], dict)) else {}
        _car = _pair[1] if (len(_pair) > 1 and isinstance(_pair[1], dict)) else {}

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

        # v69: card sirf EK jagah banta hai — renderer `numinfo_card()` (neeche).
        # (yahan pehle ek purana duplicate block pada tha jo kuch nahi karta tha —
        #  hata diya, taaki format hamesha ek hi jagah se aaye.)
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

    if mode == "vahan":
        # v71: 🚗 GAADI X-RAY — provider laga ho to poora record BOT KE ANDAR,
        # warna plate ka sarkari matlab + official SMS tarika (jhooth nahi).
        _u_v = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u_v, uid):
            await update.message.reply_text(get_credits_over_text("vahan"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        _t0v = time.perf_counter()
        _off = await asyncio.to_thread(vahan_offline, raw_text)
        _vres = {}
        if _off.get("ok"):
            try:
                _vres = await asyncio.wait_for(asyncio.to_thread(vahan_lookup, raw_text), timeout=35)
            except Exception:                                      # noqa: BLE001
                _vres = {}
        _msv = (time.perf_counter() - _t0v) * 1000
        if not _off.get("ok") and not _vres.get("ok"):
            tel_note("vahan", False, _msv, error="bad plate")
            await update.message.reply_text(
                "❌ " + str(_off.get("error") or _vres.get("error") or "Record nahi mila."),
                parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        _vnote = ""
        if not _vres.get("ok"):
            _vnote = str(_vres.get("error") or _vres.get("hub_error") or "").strip()
            if not _vnote and not vahan_provider_ready():
                _vnote = ("Live record ke liye provider set nahi hai — <code>/rcsetup</code> "
                          "bhejo (2 line, free). Neeche plate ka sarkari matlab dikh raha hai.")
        _card_v = vahan_card(_vres if _vres.get("ok") else {}, _off, note=_vnote)
        tel_note("vahan", True, _msv, credit=True)
        await update.message.reply_text(
            spend_credit_msg(uid, "vahan") + "\n" + _card_v, parse_mode=HTML)
        add_use(uid)
        return

    if mode == "osint_whois":
        # v70: 🌐 WEBSITE OWNER X-RAY — sab result BOT KE ANDAR (koi link nahi)
        _u_w = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u_w, uid):
            await update.message.reply_text(get_credits_over_text("osint_whois"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        _t0w = time.perf_counter()
        w_res = await asyncio.to_thread(lookup_whois, raw_text)
        _msw = (time.perf_counter() - _t0w) * 1000
        if w_res.get("ok"):
            w_res["latency_ms"] = w_res.get("latency_ms") or _msw
            tel_note("osint_whois", True, _msw, credit=True)
            await update.message.reply_text(
                spend_credit_msg(uid, "osint_whois") + "\n" + whois_card(w_res),
                parse_mode=HTML)
        else:
            tel_note("osint_whois", False, _msw, error=str(w_res.get("error"))[:90])
            await update.message.reply_text(
                "❌ " + str(w_res.get("error") or "Record nahi mila.") + "\n\n"
                "💡 <b>Example:</b> <code>xyzshop.in</code> ya <code>flipkart.co.in</code>",
                parse_mode=HTML)
        add_use(uid)
        return

    if mode == "uhunt":
        # v71.8: 🕵️ USERNAME HUNTER — sirf PUBLIC profiles (koi login/OTP/session nahi)
        _u_h = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u_h, uid):
            await update.message.reply_text(get_credits_over_text("uhunt"),
                                            reply_markup=get_limit_exceeded_kb(),
                                            parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        _t0h = time.perf_counter()
        _h_res = {}
        try:
            _h_res = await asyncio.wait_for(asyncio.to_thread(hunt_username, raw_text),
                                            timeout=45)
        except Exception:                                      # noqa: BLE001
            _h_res = {}
        _msh = (time.perf_counter() - _t0h) * 1000
        if not _h_res.get("ok"):
            tel_note("uhunt", False, _msh, error="bad username")
            await update.message.reply_text(
                "❌ " + str(_h_res.get("error") or "Kuch nahi mila.") + "\n\n"
                "💡 <b>Example:</b> <code>rahul_99</code>",
                parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        _h_res["ms"] = _h_res.get("ms") or _msh
        tel_note("uhunt", True, _msh, credit=True)
        await update.message.reply_text(
            spend_credit_msg(uid, "uhunt") + "\n" + uhunt_card(_h_res), parse_mode=HTML)
        add_use(uid)
        return

    # v75.2: list mili (paste ya file) -> poora flow ek hi jagah
    if mode == "bulk_wait":
        await _bulk_offer(update, context, raw_text)
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
                + pcard_foot(ms=_ms, source="official bank registry (Razorpay IFSC)",
                             cached=bool(i_res.get("cached")))
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
                    + "\n" + pcard_foot(ms=_ms, source="India Post official data",
                                         cached=bool(p_res.get("cached")))
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
                f"❌ <b>GST CHECK NAHI HO PAYA</b>\n──────────────────────\n"
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
                "──────────────────────\n"
                f"• <b>GSTIN:</b> <code>{hesc(res.get('gstin'))}</code>\n"
                + kv_row("State", _st)
                + kv_row("PAN", res.get("pan"))
                + kv_row("PAN Holder Type", res.get("pan_holder_type"))
                + kv_row("Registration Type", res.get("registration_type"))
                + _chk_line
                + _extra
                + "──────────────────────\n"
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
                f"❌ <b>PAN CHECK NAHI HO PAYA</b>\n──────────────────────\n"
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
                "──────────────────────\n"
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
                + f"\n──────────────────────\n"
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

    # ---------------- v74.0: RESULT CHECK (BSEB) wizard ----------------
    if mode == "rc_code":
        rc = BSEBR.clean_digits(raw_text)
        if not re.match(r"^\d{3,6}$", rc):
            await update.message.reply_text(
                "❌ Roll Code 5 digit ka hota hai.\n\n"
                "💡 <b>Example:</b> <code>11001</code>\n"
                "<i>Admit card par 'Roll Code' likha hota hai.</i>", parse_mode=HTML)
            return
        db = context.user_data.get("rcdb") or {}
        context.user_data["rc_code_val"] = rc
        context.user_data["mode"] = "rc_roll"
        await update.message.reply_text(
            rc_ask_roll_card(str(db.get("exam") or "matric"),
                             db.get("year") or BSEBR.CURRENT_YEAR, rc),
            reply_markup=_rc_step_kb(), parse_mode=HTML)
        return

    if mode == "rc_roll":
        nums = re.findall(r"\d{4,9}", re.sub(r"(?<=\d),(?=\d)", "", raw_text))
        if not nums:
            await update.message.reply_text(
                "❌ Roll Number nahi mila.\n\n"
                "💡 <b>Example:</b> <code>2600046</code>", parse_mode=HTML)
            return
        db = context.user_data.get("rcdb") or {}
        await rc_deliver(update.message, context, uid,
                         context.user_data.get("rc_code_val") or "", nums[0])
        return

    if mode == "rc_cap_ans":                           # v74.6: captcha jawab
        st = context.user_data.get("rcap") or {}
        form = st.get("form") or {}
        key = str(st.get("key") or "")
        bits = (raw_text or "").split()
        cap_in = bits[0] if bits else ""
        roll_in = bits[1] if len(bits) > 1 else ""
        dob_in = bits[2] if len(bits) > 2 else ""
        if not cap_in or not roll_in:
            await update.message.reply_text(
                "✍️ Aise likho: <code>AB12C 1234567</code>", parse_mode=HTML)
            return
        st["tries"] = int(st.get("tries") or 0) + 1
        context.user_data["rcap"] = st
        _res = await asyncio.to_thread(CB.submit, form, cap_in, roll_in, dob_in)
        _kb_bs = InlineKeyboardMarkup([[InlineKeyboardButton(
            "◀️ Saare boards", callback_data="rc_new")]])
        if _res.get("ok"):
            stu = _res.get("student") or {}
            context.user_data.pop("mode", None)
            context.user_data.pop("rcap", None)
            _lbl = "Class 10 / Class 12"
            await update.message.reply_text(rcap_result_card(stu, _lbl, 2026, key),
                                            reply_markup=_kb_bs, parse_mode=HTML)
            try:
                _pdf = await asyncio.to_thread(BSEBR.build_pdf, stu, _lbl, 2026,
                                               "board record", key)
                if _pdf:
                    await update.message.reply_document(
                        io.BytesIO(_pdf),
                        filename=f"{(key or 'board').upper()}_{roll_in}_2026.pdf",
                        caption="📄 <b>Marksheet (WEB COPY)</b> — poora data isme hai ✅",
                        parse_mode=HTML)
            except Exception:                                # noqa: BLE001
                pass
            add_use(update.effective_user.id)
            return
        why = str(_res.get("why") or "")
        if why == "captcha_galat" and st["tries"] < 4:
            _f2 = await asyncio.to_thread(CB.fetch_form, (form.get("url") or ""))
            if _f2.get("ok"):
                st["form"] = _f2
                context.user_data["rcap"] = st
                try:
                    await update.message.reply_photo(
                        io.BytesIO(_f2["img"]),
                        caption="❌ Captcha galat tha — <b>naya captcha likho</b>",
                        parse_mode=HTML)
                    return
                except Exception:                            # noqa: BLE001
                    pass
        context.user_data.pop("mode", None)
        context.user_data.pop("rcap", None)
        await update.message.reply_text(rcap_fail_card(why, key),
                                        reply_markup=_kb_bs, parse_mode=HTML)
        return

    if mode == "rc_board":
        # user ne board ka naam likha — khojo
        hits = BRD.find(raw_text)
        if hits:
            if len(hits) == 1:
                key = hits[0][0]
                context.user_data.pop("mode", None)
                _cap, _kb = rc_board_card(key)
                img = None
                try:
                    img = await asyncio.to_thread(BRD.photo_bytes, key)
                except Exception:                                # noqa: BLE001
                    img = None
                try:
                    if img:
                        await update.message.reply_photo(io.BytesIO(img), caption=_cap,
                                                         reply_markup=_kb, parse_mode=HTML)
                    else:
                        await update.message.reply_text(_cap, reply_markup=_kb, parse_mode=HTML)
                except Exception:                                # noqa: BLE001
                    await update.message.reply_text(_cap, reply_markup=_kb, parse_mode=HTML)
                return
            rows = [[InlineKeyboardButton(str(b.get("short"))[:24], callback_data=f"rcb:{k}")]
                    for k, b in hits]
            rows.append([InlineKeyboardButton("🇮🇳 Saare boards", callback_data="rc_new")])
            await update.message.reply_text(
                f"🔍 <b>{len(hits)} board mile</b> — jo chahiye wo dabayein:",
                reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)
            return
        await update.message.reply_text(
            "❌ Is naam ka board nahi mila.\n\n"
            "💡 Poora naam likhein (jaise <code>UP Board</code>, <code>Maharashtra</code>, "
            "<code>Telangana</code>) — ya neeche se chuno:",
            reply_markup=_rc_pick_kb(0), parse_mode=HTML)
        return

    if mode in RC_STEPS:
        # user ne bina button dabe number type kar diya — sahi step dikha do
        db = context.user_data.get("rcdb") or {}
        _ek = str(db.get("exam") or "")
        if mode == "rc_exam" or not _ek:
            await update.message.reply_text(rc_exam_card(),
                                            reply_markup=_rc_exam_kb(), parse_mode=HTML)
        else:
            await update.message.reply_text(rc_year_card(_ek),
                                            reply_markup=_rc_year_kb(), parse_mode=HTML)
        return

    # ---------------- v73.0: CHAT X-RAY ----------------
    if mode == "cxray":
        await update.message.reply_text(
            "💬 <b>Chat ki file bhejein</b> (.txt ya .zip)\n"
            "<i>WhatsApp → chat kholo → ⋮ menu → Export chat → </i><b>Without media</b>",
            parse_mode=HTML)
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
        # v75.1 — ⚡ SPEED FIX: pehle `asyncio.gather` tha (SLOWEST ka wait).
        #  `shorten_url` 6 provider try karta hai aur `expand_url` redirect chain
        #  follow karta hai — dono me se koi ek slow ho to user dono ka time
        #  jod kar wait karta tha. Ab `gather_soon`: jo time me aa gaya wahi.
        _pair, _ms = await pro.gather_soon(
            [asyncio.to_thread(shorten_url, raw_text, 3),
             asyncio.to_thread(expand_url, raw_text)],
            timeout=float(os.environ.get("SHORT_WAIT_S", "9")),
        )
        links = _pair[0] if _pair and _pair[0] else []
        exp = _pair[1] if (len(_pair) > 1 and isinstance(_pair[1], dict)) else {}
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
            "──────────────────────\n"
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


# ============================================================
#  v74.0: 📋 RESULT CHECK PRO (sirf BSEB — Bihar Board)
# ------------------------------------------------------------
#  Portal jaisa poora flow: EXAM chuno → YEAR chuno → Roll Code →
#  Roll Number → Result card + PDF (web copy jaisi marksheet).
#  Matric = official open API · Inter = official portal form.
# ============================================================
RC_STEPS = ("rc_exam", "rc_year", "rc_board")

# v74.6: captcha bridge ke official endpoints (form khule to yahin se chalega)
RC_CAP_ENDPOINTS = {
    "cbse": ["https://cbseresults.nic.in/",
             "https://results.cbse.nic.in/",
             "https://cbseresults.nic.in/class10/",
             "https://cbseresults.nic.in/class12/"],
}


def rcap_result_card(stu: dict, label: str, year, key: str) -> str:
    """Bridge ka result card — sirf outcome."""
    b = BRD.BOARDS.get(key) or {}
    L = [pcard_title("📋", f"RESULT — {str(b.get('short') or key).upper()}"),
         f"🎓 {hesc(str(label))} · <b>{year}</b>", pcard_sep()]
    if stu.get("name"):
        L.append(f"👤 <b>{hesc(str(stu['name']))}</b>")
    for k2, lb in (("roll_no", "🔢 Roll"), ("school_name", "🏫 School"),
                   ("father_name", "👨 Father"), ("mother_name", "👩 Mother")):
        if stu.get(k2):
            L.append(f"{lb}: {hesc(str(stu[k2]))}")
    subs = stu.get("subjects") or []
    if subs:
        L.append("")
        L.append("📚 <b>Marks:</b>")
        for sub in subs[:15]:
            L.append("├ " + BSEBR._sub_line(sub))
    L.append(pcard_sep())
    if stu.get("total"):
        L.append(f"🎯 <b>Total:</b> {BSEBR._nice(stu.get('total'))}")
    if stu.get("result"):
        L.append(f"🏅 <b>Result:</b> {hesc(str(stu['result']))}")
    L.append("📄 <b>PDF marksheet</b> neeche hai ✅")
    L.append("")
    L.append(BRAND_LINK)
    return "\n".join(L)


def rcap_fail_card(why: str, key: str = "") -> str:
    b = BRD.BOARDS.get(key) or {}
    line = {"login": "❌ Result abhi nahi mila (portal band/login maangta hai)",
            "form_nahi": "❌ Result abhi nahi mila",
            "captcha_img_fail": "❌ Captcha image nahi khuli — dobara try karo",
            "roll_nahi": "❌ Ye roll number nahi mila",
            "captcha_galat": "❌ Captcha galat tha",
            "parse": "❌ Result aa gaya par padha nahi ja saka — dobara try karo",
            }.get(why, "❌ Result nahi mila — dobara try karo")
    return "\n".join([pcard_title("📋", f"RESULT — {str(b.get('short') or 'BOARD').upper()}"),
                       pcard_sep(), line, "", BRAND_LINK])


def _rc_pick_card(page: int = 0) -> str:
    """Board chuno (v74.5: sirf BSEB + CBSE)."""
    rows, pg, tot = BRD.page_boards(page)
    L = [pcard_title("📋", "RESULT CHECK"),
         f"🇮🇳 <b>Apna BOARD chuno</b>" + (f"  (page {pg + 1}/{tot})" if tot > 1 else ""),
         ""]
    for key, b in rows:
        live = " ✅ <b>LIVE</b>" if b.get("status") == "live" else ""
        L.append(f"{b.get('flag', '🔹')} <b>{hesc(str(b.get('short')))}</b>"
                 f" — {hesc(str(b.get('state')))}{live}")
    return "\n".join(L)


def _rc_pick_kb(page: int = 0):
    rows_b, pg, tot = BRD.page_boards(page)
    rows, buf = [], []
    for key, b in rows_b:
        live = "✅" if b.get("status") == "live" else ""
        buf.append(InlineKeyboardButton(f"{str(b.get('short'))[:22]}{live}",
                                        callback_data=f"rcb:{key}"))
        if len(buf) == 2:
            rows.append(buf)
            buf = []
    if buf:
        rows.append(buf)
    if tot > 1:                                    # v74.5: 1 page ho to nav row nahi
        nav = []
        if pg > 0:
            nav.append(InlineKeyboardButton("◀️ Peeche", callback_data=f"rc_page:{pg - 1}"))
        nav.append(InlineKeyboardButton(f"{pg + 1}/{tot}", callback_data="rc_noop"))
        if pg < tot - 1:
            nav.append(InlineKeyboardButton("Aage ▶️", callback_data=f"rc_page:{pg + 1}"))
        rows.append(nav)
    rows.append([InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)


def rc_board_card(key: str) -> tuple:
    """(caption, keyboard) — board ka apna card (official logo ke saath)."""
    b = BRD.BOARDS.get(str(key)) or {}
    if not b:
        return "", _rc_pick_kb(0)
    st = b.get("status")
    L = [f"🏛️ <b>{hesc(str(b.get('name', '')))}</b>",
         f"<b>{hesc(str(b.get('short', '')))}</b>"]
    if b.get("hi"):
        L.append(f"<i>{hesc(str(b['hi']))}</i>")
    L.append(f"📍 <b>State:</b> {hesc(str(b.get('state', '')))}")
    L.append(f"📚 <b>Exam:</b> {hesc(', '.join(b.get('exams') or []))}")
    L.append(f"🔢 <b>Chahiye:</b> {hesc(', '.join(b.get('need') or []))}")
    L.append(pcard_sep())
    L.append("✅ <b>LIVE</b> — result yahin se nikalta hai"
             if st == "live" else "⏳ <b>Jald live hoga</b>")
    L.append("")
    L.append(BRAND_LINK)
    rows = []
    if st == "live":
        rows.append([InlineKeyboardButton("🔎 Result check karo (LIVE ✅)",
                                          callback_data=f"rc_live:{key}")])
    elif key in RC_CAP_ENDPOINTS:
        rows.append([InlineKeyboardButton("🔎 Result check karo (🔐 captcha)",
                                          callback_data=f"rc_cap:{key}")])
    rows.append([InlineKeyboardButton("◀️ Saare boards", callback_data="rc_new")])
    return "\n".join(L), InlineKeyboardMarkup(rows)


async def _rc_say_photo(q, key, caption, kb):
    """Board ka card PHOTO ke saath bhejo (official logo / color badge)."""
    if q is None:
        return
    img = None
    try:
        img = await asyncio.to_thread(BRD.photo_bytes, key)
    except Exception:                                            # noqa: BLE001
        img = None
    try:
        if q is not None and getattr(q, "message", None) is not None:
            try:
                await q.message.delete()
            except Exception:                                    # noqa: BLE001
                pass
            if img:
                await q.message.reply_photo(io.BytesIO(img), caption=caption,
                                            reply_markup=kb, parse_mode=HTML)
                return
            await q.message.reply_text(caption, reply_markup=kb, parse_mode=HTML)
            return
    except Exception:                                            # noqa: BLE001
        pass
    await _vnum_say(q, caption, kb)


RC_STEPS_BOARD = True


def _rc_exam_kb():
    rows = [[InlineKeyboardButton(ex["btn"], callback_data=f"rc_ex:{k}")]
            for k, ex in BSEBR.EXAMS.items()]
    rows.append([InlineKeyboardButton("ℹ️ CBSE result?", callback_data="cbse_info")])
    rows.append([InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)


def _rc_year_kb():
    rows, buf = [], []
    for y in BSEBR.YEARS:
        lab = f"{y} ✅" if int(y) == int(BSEBR.CURRENT_YEAR) else str(y)
        buf.append(InlineKeyboardButton(lab, callback_data=f"rc_yr:{y}"))
        if len(buf) == 2:
            rows.append(buf)
            buf = []
    if buf:
        rows.append(buf)
    rows.append([InlineKeyboardButton("⏪ Exam badlo", callback_data="rc_back_ex")])
    return InlineKeyboardMarkup(rows)


def _rc_step_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏪ Year badlo", callback_data="rc_back_yr"),
         InlineKeyboardButton("⏪ Exam badlo", callback_data="rc_back_ex")],
        [InlineKeyboardButton("❌ Cancel", callback_data="back_home")],
    ])


def _rc_result_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Naya check", callback_data="rc_new"),
         InlineKeyboardButton("🔁 Dobara try", callback_data="rc_retry")],
        [InlineKeyboardButton("ℹ️ CBSE result?", callback_data="cbse_info"),
         InlineKeyboardButton("⌨️ Tools Grid", callback_data="back_home")],
    ])


def _rc_head(exam_key: str, year) -> str:
    ex = BSEBR.EXAMS.get(str(exam_key)) or {}
    return f"📋 <b>RESULT CHECK (BSEB)</b>\n🎓 {ex.get('short', 'BSEB')} · <b>{year}</b>"


def rc_exam_card() -> str:
    return "\n".join([
        pcard_title("📋", "RESULT CHECK (BSEB ✅ LIVE)"),
        "🔗 <b>Pehle EXAM chuno</b> (neeche buttons se):",
        "",
        "     🎓 Matric (10th) Annual",
        "     🎓 Inter (12th) Annual",
        "     🔁 Inter Special / Compartmental",
        "",
        "<i>Bihar Board (BSEB) ka result.</i>",
    ])


def rc_year_card(exam_key: str) -> str:
    return "\n".join([
        _rc_head(exam_key, BSEBR.CURRENT_YEAR),
        pcard_sep(),
        "🔗 <b>Ab YEAR chuno</b> (neeche buttons se):",
        "",
        f"     {BSEBR.CURRENT_YEAR} ✅  ← is saal ka result",
        "     2025 · 2024 · 2023 · 2022  (purane saal)",
        "",
        "<i>Purane saal ka result board ke live portal par nahi hota — "
        "us par poori jaankari milegi.</i>",
    ])


def rc_ask_code_card(exam_key: str, year) -> str:
    return "\n".join([
        _rc_head(exam_key, year),
        pcard_sep(),
        "🔗 <b>Ab Roll Code bhejein</b>:",
        "",
        "     <code>11001</code>",
        "",
        "<i>Admit card par 'Roll Code' likha hota hai (5 digit).</i>",
    ])


def rc_ask_roll_card(exam_key: str, year, roll_code: str) -> str:
    return "\n".join([
        _rc_head(exam_key, year),
        f"✅ Roll Code: <b>{hesc(str(roll_code))}</b>",
        pcard_sep(),
        "🔗 <b>Ab Roll Number bhejein</b>:",
        "",
        "     <code>2600046</code>",
        "",
        "<i>Admit card par 'Roll Number' likha hota hai (6-7 digit).</i>",
    ])


def rc_result_card(st: dict, exam_key: str, year) -> str:
    ex = BSEBR.EXAMS.get(str(exam_key)) or {}
    L = [pcard_title("📋", "BSEB RESULT"),
         f"🎓 <b>{hesc(str(ex.get('short', 'BSEB')))}</b> · {year}"]
    L.append(f"👤 <b>{hesc(str(st.get('name') or '-'))}</b>")
    if st.get("father"):
        L.append(f"👨 {hesc(str(st['father']))}")
    if st.get("school"):
        L.append(f"🏫 {hesc(str(st['school']))}")
    L.append(f"🔢 <b>Roll:</b> <code>{hesc(str(st.get('roll_code') or '-'))}"
             f" / {hesc(str(st.get('roll_no') or '-'))}</code>")
    if st.get("reg_no"):
        L.append(f"🆔 <b>Reg No:</b> {hesc(str(st['reg_no']))}")
    if st.get("bseb_id"):
        L.append(f"🎫 <b>BSEB ID:</b> {hesc(str(st['bseb_id']))}")
    if st.get("exam_type"):
        L.append(f"🧾 <b>Exam Type:</b> {hesc(str(st['exam_type']))}")
    subs = st.get("subjects") or []
    if subs:
        L.append(pcard_sep())
        L.append("📚 <b>Marks (subject-wise):</b>")
        for sub in subs[:15]:
            L.append("├ " + BSEBR._sub_line(sub))
    L.append(pcard_sep())
    tot = st.get("total")
    L.append(f"🎯 <b>Total:</b> {BSEBR._nice(tot)}")
    L.append(f"🏅 <b>Result:</b> {BSEBR.result_text(st)}"
             + (f" · {hesc(str(st.get('division')))}" if st.get("division") else ""))
    if st.get("is_topper"):
        L.append("🏆 <b>TOPPER!</b> — board ki topper list me naam 🎉")
    L.append("")
    L.append("📄 <b>PDF marksheet</b> neeche hai ✅")
    L.append("")
    L.append(BRAND_LINK)
    return "\n".join(L)


def rc_archive_card(exam_key: str, year) -> str:
    ex = BSEBR.EXAMS.get(str(exam_key)) or {}
    return "\n".join([
        _rc_head(exam_key, year),
        pcard_sep(),
        f"⚠️ <b>{year} ka result nahi mila</b> — sirf <b>{BSEBR.CURRENT_YEAR}</b> ka chalta hai.",
        "",
        BRAND_LINK,
    ])


def rc_notlive_card(exam_key: str, year, rc: str, rn: str) -> str:
    ex = BSEBR.EXAMS.get(str(exam_key)) or {}
    L = [_rc_head(exam_key, year),
         f"👤 <b>{hesc(str(ex.get('short', 'BSEB')))}</b>",
         f"🔎 <b>Check kiya:</b> <code>{hesc(rc)} / {hesc(rn)}</code>",
         "",
         "⏳ <b>Is roll ka result abhi live nahi hai</b>",
         "<i>Board ne is roll ka result declare nahi kiya, ya number galat hai.</i>",
         pcard_sep(),
         "📅 <b>Result kab aata hai:</b>",
         "• Matric (10th) — <b>March-April</b>",
         "• Inter (12th) — <b>March-April</b>",
         "• Compartment — <b>May-August</b>",
         "",
         "🔤 Roll Code aur Roll Number ulta ho gaya ho to dobara bhej dein.",
         "✅ Result declare hote hi yahi se turant mil jayega.",
         "",
         BRAND_LINK]
    return "\n".join(L)


def rc_server_card(exam_key: str, year) -> str:
    return "\n".join([
        _rc_head(exam_key, year),
        pcard_sep(),
        "❌ <b>Bihar Board ka server abhi jawab nahi de raha</b>",
        "<i>(result season me server par bahut load hota hai)</i>",
        "",
        "👉 1-2 minute baad <b>🔁 Dobara try</b> dabayein — aapke number yaad hain.",
        "",
        BRAND_LINK,
    ])


def rc_parse_card(exam_key: str, year) -> str:
    return "\n".join([
        _rc_head(exam_key, year),
        pcard_sep(),
        "⚠️ <b>Result nahi padha ja saka</b> — dobara try karein.",
        "",
        BRAND_LINK,
    ])


def cbse_info_card() -> str:
    return "\n".join([
        pcard_title("🏛️", "CBSE — CENTRAL BOARD OF SECONDARY EDUCATION"),
        "🇮🇳 <b>All India</b>",
        pcard_sep(),
        "⏳ <b>Jald live hoga</b>",
        "",
        BRAND_LINK,
    ])


async def rc_deliver(target, context, uid: int, rc: str, rn: str):
    """Result lao → card + PDF bhejo (kabhi khaali nahi)."""
    db = context.user_data.get("rcdb") or {}
    exam_key = str(db.get("exam") or "matric")
    try:
        year = int(db.get("year") or BSEBR.CURRENT_YEAR)
    except Exception:                                            # noqa: BLE001
        year = BSEBR.CURRENT_YEAR
    db["rc"], db["rn"] = str(rc), str(rn)
    context.user_data["rcdb"] = db
    st = await target.reply_text("🔎 Bihar Board se result nikal raha hoon…")
    res = await asyncio.to_thread(BSEBR.check, exam_key, year, rc, rn)
    try:
        await st.delete()
    except Exception:                                            # noqa: BLE001
        pass
    if res.get("ok"):
        stu = res.get("student") or {}
        await target.reply_text(rc_result_card(stu, exam_key, year),
                                reply_markup=_rc_result_kb(), parse_mode=HTML)
        try:
            _label = (BSEBR.EXAMS.get(exam_key) or {}).get("label") or "BSEB"
            pdf = await asyncio.to_thread(BSEBR.build_pdf, stu, _label, year,
                                          "board record")
            if pdf:
                await target.reply_document(
                    io.BytesIO(pdf),
                    filename=BSEBR.pdf_filename(exam_key, rc, rn, year),
                    caption="📄 <b>Marksheet (WEB COPY)</b> — poora data isme hai "
                            "(sirf jaankari ke liye) ✅",
                    parse_mode=HTML)
        except Exception as e:                                   # noqa: BLE001
            log.warning("result pdf fail: %s", str(e)[:120])
        context.user_data.pop("mode", None)
        context.user_data.pop("rc_code_val", None)
        add_use(uid)
        return
    _stt = str(res.get("status") or "")
    if _stt == "server":
        await target.reply_text(rc_server_card(exam_key, year),
                                reply_markup=_rc_result_kb(), parse_mode=HTML)
    elif _stt == "parse":
        await target.reply_text(rc_parse_card(exam_key, year),
                                reply_markup=_rc_result_kb(), parse_mode=HTML)
    else:
        await target.reply_text(rc_notlive_card(exam_key, year, rc, rn),
                                reply_markup=_rc_result_kb(), parse_mode=HTML)
    context.user_data.pop("mode", None)
    context.user_data.pop("rc_code_val", None)


def cxray_caption(st: dict) -> str:
    """Image ke saath chhoti summary (HTML)."""
    users = st.get("users") or []
    top = users[0] if users else {"name": "-", "n": 0, "share": 0}
    ek = st.get("emoji_king") or ("", 0)
    ha = st.get("haha_king") or ("", 0)
    nt = st.get("night") or {}
    ntop = (nt.get("top") or ("", 0)) if isinstance(nt, dict) else ("", 0)
    bh, bhn = (st.get("busy_hour") or (None, 0))
    L = [
        f"💬 <b>{to_bold('WHATSAPP CHAT X-RAY')}</b>",
        f"📊 <b>Total:</b> {st.get('total', 0):,} messages · {st.get('days', 0):,} din "
        f"· {st.get('per_day', 0):g}/din",
        f"👑 <b>Top chatter:</b> {hesc(str(top.get('name', '-')))} ({top.get('n', 0)} msg, "
        f"{top.get('share', 0)}%)",
    ]
    if ek[1]:
        L.append(f"😄 <b>Emoji King:</b> {hesc(str(ek[0]))} ({ek[1]} emoji)")
    if ha[1]:
        L.append(f"🤣 <b>Hasi King:</b> {hesc(str(ha[0]))} ({ha[1]}x)")
    if ntop[1]:
        L.append(f"🦉 <b>Raat ka jagaadu (12-5 baje):</b> {hesc(str(ntop[0]))} ({nt.get('n', 0)} msg)")
    if bhn:
        L.append(f"⏰ <b>Sabse busy waqt:</b> {int(bh):02d}:00 ({bhn} msg)")
    if st.get("media"):
        L.append(f"🖼️ <b>Media files:</b> {st['media']}")
    L.append("")
    L.append("🔒 <i>File sirf padhi gayi — kahin save ya upload nahi hui.</i>")
    L.append(BRAND_LINK)
    return "\n".join(L)


async def handle_new_tool_file(update, context, uid, msg, mode, kind, data, mime=""):
    """v38: aayi hui file ko mode ke hisaab se process karo. True = handle ho gaya."""
    say = msg.reply_text

    # ---------- 💬 CHAT X-RAY (v73.0) ----------
    if mode == "cxray":
        if kind != "chat":
            await say("❌ Ye chat ki export file nahi lagti.\n"
                      "📄 WhatsApp chat ki <b>.txt</b> (ya .zip) file bhejein —\n"
                      "<i>WhatsApp → chat kholo → ⋮ (menu) → Export chat → </i>"
                      "<b>Without media</b>", parse_mode=HTML)
            return True
        fname = (getattr(getattr(msg, "document", None), "file_name", "") or "")
        st = await say("🔎 Chat padh raha hoon… (5-20 second)")
        res = await asyncio.to_thread(CXR.analyze_file, data, fname)
        if not res.get("ok"):
            try:
                await st.edit_text("❌ " + str(res.get("error") or "File samajh nahi aayi."),
                                   parse_mode=HTML)
            except Exception:                                    # noqa: BLE001
                await say("❌ " + str(res.get("error") or "File samajh nahi aayi."),
                          parse_mode=HTML)
            return True
        s2 = res["stats"]
        cap = cxray_caption(s2)
        img = await asyncio.to_thread(CXR.report_image, s2)
        try:
            await st.delete()
        except Exception:                                        # noqa: BLE001
            pass
        if img:
            try:
                await msg.reply_photo(io.BytesIO(img), caption=cap, parse_mode=HTML)
            except Exception:                                    # noqa: BLE001
                await msg.reply_text(cap, parse_mode=HTML)
        else:
            await msg.reply_text(cap, parse_mode=HTML)
        context.user_data.pop("mode", None)
        add_use(uid)
        return True

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

    # ==================================================================
    #  v63: 💼 BUSINESS STUDIO WIZARD — photo/logo wala step
    # ==================================================================
    #  User jab tool ke step par ho aur us step me photo maangi gayi ho,
    #  to yahan photo download kar ke usi tool ke dict me daal dete hain.
    # v65: agar pichhla progress-pinger chal raha tha to use band karo
    try:
        _old_stop = context.user_data.get("_ping_stop")
        if _old_stop is not None:
            _old_stop.set()
            context.user_data.pop("_ping_stop", None)
    except Exception:                                            # noqa: BLE001
        pass

    if mode and str(mode).startswith("biz_") and mode != "biz_menu":
        _steps_p = biz_steps(str(mode))
        _idx_p = context.user_data.get("biz_step")
        if _steps_p and _idx_p is not None:
            _idx_p = int(_idx_p)
            _fld_p, _q_p, _hint_p, _isphoto_p = _steps_p[min(_idx_p, len(_steps_p) - 1)][:4]
            if _isphoto_p:
                try:
                    _tf = await update.message.photo[-1].get_file()
                    _buf = io.BytesIO()
                    await _tf.download_to_memory(_buf)
                    _pbytes = _buf.getvalue()
                except Exception:                                # noqa: BLE001
                    _pbytes = b""
                if _pbytes:
                    _ans_p = dict(context.user_data.get("biz_ans") or {})
                    _ans_p[_fld_p] = _pbytes
                    context.user_data["biz_ans"] = _ans_p
                    _idx_p += 1
                    if _idx_p < len(_steps_p):
                        context.user_data["biz_step"] = _idx_p
                        await safe_reply(update.message,
                                         "✅ <b>Photo lag gayi!</b> 👌\n\n"
                                         + biz_step_prompt(str(mode), _idx_p),
                                         reply_markup=biz_steps_kb(str(mode), _idx_p),
                                         parse_mode=HTML)
                        return
                    # aakhri step tha -> file banao
                    context.user_data.pop("biz_step", None)
                    context.user_data.pop("biz_ans", None)
                    _d_p = biz_answers_to_dict(str(mode), _ans_p)
                    _r_p = await asyncio.get_running_loop().run_in_executor(
                        None, functools_partial(biz_build, str(mode), _d_p))
                    _ok_p = bool(_r_p and _r_p.get("ok"))
                    if _ok_p and not ALL_FREE:
                        spend_credits(uid, 1)
                    await biz_send_result(update.message, str(mode), _r_p or {}, uid,
                                          used=_ok_p)
                    return
                await safe_reply(update.message,
                                 "⚠️ Photo padhi nahi ja saki. Dobara bhejein, "
                                 "ya <code>SKIP</code> likh dein.", parse_mode=HTML)
                return
        else:
            # photo-step nahi chal raha — to ye photo kisi aur kaam ka hai
            pass

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
                  "media_trim_wait", "media_compress_wait", "media_status_audio",
                  "cxray")                     # v73.0: 💬 chat export file (.txt/.zip)
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
            if kind is None and mode == "cxray" and (fname.endswith(".txt") or fname.endswith(".zip")):
                kind = "chat"          # v73.0: WhatsApp export file
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
        # v66: vault ko batao ki MAIN loop kaun hai — thread se backup ab
        #      isi loop par chalta hai (pehle "different event loop" crash tha)
        try:
            vault_set_main_loop(_loop)
            log.info("🛡️ Vault: main event loop register ho gaya (backup crash fix)")
        except Exception as _ve:                                 # noqa: BLE001
            log.debug("vault loop register skip: %s", str(_ve)[:80])
        # v66: cookies wapas laga do (admin ne pehle bheji thi to)
        try:
            if cookies_boot_restore():
                log.info("🍪 YouTube cookies restore ho gayin (bot-check fix ON)")
        except Exception as _ce:                                 # noqa: BLE001
            log.debug("cookies restore skip: %s", str(_ce)[:80])

        def _loop_err(_loop2, _ctx):
            _ex = _ctx.get("exception")
            if _ex is None:
                return          # v68: khaali context = asli error nahi (log na bharo)
            log.warning("🛡️ background task error (bot chalta rahega): %s: %s",
                        type(_ex).__name__, str(_ex)[:200])
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
                                  f"──────────────────────\n"
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
    _KEEPALIVE_MINUTES = float(os.environ.get("KEEPALIVE_MINUTES") or 3)  # v74.3: 4→3 min
except Exception:
    _KEEPALIVE_MINUTES = 3.0
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


def _webhook_watchdog(url: str, path: str) -> None:
    """v74.4: webhook ka PERMANENT ilaaj — har 15 min khud check,

    error/URL-mismatch mile to khud dobara set kar deta hai (3 retry).
    Kuch bhi galat ho, bot chup-chaap theek ho jata hai — user ko pata bhi nahi.
    """
    import time as _t
    import urllib.request
    import json as _json
    _full = (url or "").rstrip("/") + (path or "")
    if not _full:
        return
    _api = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    _secret = (os.environ.get("WEBHOOK_SECRET_TOKEN") or "").strip()
    while True:
        _t.sleep(900)                                  # 15 min
        try:
            with urllib.request.urlopen(_api + "getWebhookInfo", timeout=25) as r:
                info = (_json.loads(r.read().decode("utf-8", "ignore")) or {}).get("result") or {}
            need = (str(info.get("url") or "") != _full) or bool(info.get("last_error_message")) \
                or int(info.get("pending_update_count") or 0) > 60
            if not need:
                continue
            for _try in range(3):
                try:
                    body = {"url": _full, "drop_pending_updates": False}
                    if _secret:
                        body["secret_token"] = _secret
                    req = urllib.request.Request(
                        _api + "setWebhook", data=_json.dumps(body).encode(),
                        headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=25) as r2:
                        if (_json.loads(r2.read().decode("utf-8", "ignore")) or {}).get("ok"):
                            log.info("WEBHOOK self-heal OK — dobara set ho gaya (try %s)", _try + 1)
                            break
                except Exception:                      # noqa: BLE001
                    _t.sleep(5)
        except Exception:                              # noqa: BLE001
            pass


# v74.4: jo boards abhi `portal` hain — inka result page har 6 ghante check hota
# hai (Render se). Jis din page khulega (roll form + captcha nahi), admin ko
# message jayega — usi din us board ko LIVE banayenge.
_BOARD_WATCH = (
    # v74.5: sirf CBSE (baaki boards hata diye). Jis din CBSE ka roll-number
    # page bina login/captcha khulega, usi din LIVE add hoga.
    ("cbse", "https://cbseresults.nic.in/"),
    ("cbse2", "https://results.cbse.nic.in/"),
)
_BW_STATE = os.path.join(tempfile.gettempdir(), "ud_bw_seen.txt")


def _board_watch_loop(app) -> None:
    """Har 6 ghante boards ka result page check — khula mile to admin ko batao."""
    import time as _t
    import urllib.request
    _aid = 0
    try:
        _aid = int(os.environ.get("ADMIN_ID") or 0)
    except Exception:                                  # noqa: BLE001
        _aid = 0
    if not _aid:
        return
    while True:
        _t.sleep(6 * 3600)
        try:
            seen = set()
            try:
                with open(_BW_STATE, "r", encoding="utf-8") as fh:
                    seen = {x.strip() for x in fh if x.strip()}
            except Exception:                          # noqa: BLE001
                pass
            found = []
            for key, url in _BOARD_WATCH:
                if key in seen:
                    continue
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=15) as r:
                        html = r.read(400000).decode("utf-8", "ignore")
                    low = html.lower()
                    if ("captcha" in low) or ("turnstile" in low):
                        continue
                    if "roll" not in low:
                        continue
                    found.append((key, url))
                except Exception:                      # noqa: BLE001
                    continue
            if found:
                for k, _u in found:
                    seen.add(k)
                try:
                    with open(_BW_STATE, "w", encoding="utf-8") as fh:
                        fh.write("\n".join(sorted(seen)))
                except Exception:                      # noqa: BLE001
                    pass
                try:
                    app.bot.send_message(
                        chat_id=_aid,
                        text=("📡 <b>BOARD WATCH</b> — in boards ka result page khula mila "
                              "(roll + captcha nahi):\n"
                              + "\n".join(f"• <code>{k}</code>" for k, _u in found)
                              + "\nBolo to LIVE add kar dun."),
                        parse_mode="HTML")
                except Exception:                      # noqa: BLE001
                    pass
        except Exception:                              # noqa: BLE001
            pass


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
        # v76: janitor (khud-safai) ki health — Render par crash ke chhupe kaaran
        try:
            js = _janitor_stats() or {}
            br = _bounded_report() or {}
            out.append(
                f"<p style='font-family:monospace'>janitor: "
                f"on={js.get('on')} runs={js.get('runs', 0)} "
                f"tmp_cleaned={js.get('tmp_dirs', 0)}d/{js.get('tmp_files', 0)}f "
                f"freed={js.get('mb_freed', 0)}MB "
                f"procs_killed={js.get('procs_killed', 0)} "
                f"disk={js.get('disk_pct', 0)}%</p>")
            out.append(
                f"<p style='font-family:monospace'>caches: "
                f"{br.get('total_entries', 0)}/{br.get('total_limit', 0)} entries "
                f"| clears={br.get('clears', 0)} "
                f"evictions={br.get('evictions', 0)}</p>")
        except Exception:                                        # noqa: BLE001
            pass
        return "".join(out)
    except Exception as e:                                       # noqa: BLE001
        return f"<p style='font-family:monospace'>vault status n/a ({type(e).__name__})</p>"


def _http_engine_line() -> str:
    """v72.0: shared HTTP engine ki live stats (speed + auto-retry upgrade)."""
    try:
        st = http_engine.stats()
        return (f"session=shared+auto-retry calls={st.get('calls', 0)} "
                f"retries={st.get('retries', 0)} fails={st.get('fails', 0)} "
                f"avg={st.get('avg_ms', 0)}ms")
    except Exception as e:                                       # noqa: BLE001
        return f"n/a ({type(e).__name__})"


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
            f"<p style='font-family:monospace'>http engine: {_http_engine_line()}</p>"
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
    """v74.1: Render ka "No open ports detected" warning fix.

    Pehle default 10000 tha — agar Render koi aur PORT deta (ya env miss ho)
    to scan warning aata tha. Ab: PORT env → RENDER_PORT → 10000, aur bind
    fail hone par 3 retry (port release hone ka waqt milta hai).
    """
    import http.server
    import socketserver

    try:
        port = int(os.environ.get("PORT") or os.environ.get("RENDER_PORT") or "10000")
    except Exception:                                            # noqa: BLE001
        port = 10000

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

    class _Srv(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    for _try in range(3):
        try:
            with _Srv(("0.0.0.0", port), Handler) as httpd:
                _KEEPALIVE_SERVER["srv"] = httpd
                log.info("Keepalive server listening on port %s (bind try %s) — Render scan OK",
                         port, _try + 1)
                httpd.serve_forever()
            break
        except Exception as e:                                   # noqa: BLE001
            log.warning("Keepalive bind try %s fail (port %s): %s", _try + 1, port, e)
            import time as _t2
            _t2.sleep(3.0)
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


# =====================================================================
#  v75 — 🧠 PRO ENGINE WRAPPERS + COMMANDS
# =====================================================================
#  Ye wrappers on_text / on_cb ko lapette hain — bas itna kaam:
#    (1) tool ka time naapo,
#    (2) result history + tool analytics me likho,
#    (3) crash ho to bhi FAIL likho (chup-chaap gayab na ho).
#  Isse KUCH BHI tool ka andar ka code nahi badla (aapke prompts bhi safe).
# =====================================================================

async def _on_text_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """on_text ka wrapper — har tool run ka hisaab rakhta hai."""
    t0 = time.perf_counter()
    ok_done = True
    try:
        context.user_data.pop("_pro_tool", None)
        context.user_data.pop("_pro_mode", None)
        await on_text(update, context)
    except Exception:
        ok_done = False
        raise
    finally:
        try:
            tool = context.user_data.pop("_pro_tool", None)
            _mkey = context.user_data.pop("_pro_mode", None) or tool
            if tool:
                _uid = update.effective_user.id if update.effective_user else 0
                _ms = int((time.perf_counter() - t0) * 1000)
                pro.record_result(_uid, str(_mkey), title=str(tool),
                                  ok=ok_done, ms=_ms)
        except Exception:                                        # noqa: BLE001
            pass


async def _on_cb_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """on_cb ka wrapper — callback wale tools ka bhi hisaab."""
    t0 = time.perf_counter()
    ok_done = True
    try:
        context.user_data.pop("_pro_tool", None)
        context.user_data.pop("_pro_mode", None)
        await on_cb(update, context)
    except Exception:
        ok_done = False
        raise
    finally:
        try:
            tool = context.user_data.pop("_pro_tool", None)
            _mkey = context.user_data.pop("_pro_mode", None) or tool
            if tool:
                _uid = update.effective_user.id if update.effective_user else 0
                _ms = int((time.perf_counter() - t0) * 1000)
                pro.record_result(_uid, str(_mkey), title=str(tool),
                                  ok=ok_done, ms=_ms)
        except Exception:                                        # noqa: BLE001
            pass


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🗂️ /history — user ke aakhri results (1-tap dobara chalane ke saath)."""
    uid = update.effective_user.id
    get_user(uid, update.effective_user.first_name or "")
    txt = pro.history_text(uid, 8)
    kb = pro.history_kb(uid, 5)
    await update.message.reply_text(txt, reply_markup=kb or None, parse_mode=HTML)


async def cmd_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📤 /bulk — ek saath poora Excel report (IFSC/pincode/mobile/gaadi/link)."""
    uid = update.effective_user.id
    get_user(uid, update.effective_user.first_name or "")
    context.user_data["mode"] = "bulk_wait"
    context.user_data["_pro_tool"] = "Bulk Mode"
    context.user_data["_pro_mode"] = "bulk"
    _lim, _vip = BM.limits_for(uid)
    await update.message.reply_text(BM.bulk_intro_text(vip=_vip), parse_mode=HTML)


async def cmd_smart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🧠 /smart — smart auto-detect ON/OFF + kya-kya pahchanta hai."""
    uid = update.effective_user.id
    on = pro.detect_enabled(uid)
    new = pro.set_detect_enabled(uid, not on)
    icon = "🟢 ON" if new else "🔴 OFF"
    lines = [
        "🧠 <b>SMART DETECT</b>",
        "──────────────────────",
        f"Status: <b>{icon}</b>",
    ]
    if new:
        lines += [
            "──────────────────────",
            "Ab aap seedha input bhej sakte ho — bot khud tool chala lega:",
            "• <code>SBIN0001234</code> → 🏦 IFSC",
            "• <code>9876543210</code> → 📱 Number Info",
            "• <code>800001</code> → 📮 Pincode",
            "• <code>BR01AB1234</code> → 🚗 RC + Challan",
            "• koi bhi link → 🔍 Link Check",
            "• <code>@username</code> → 🕵️ Username Hunter",
            "• 15-digit number → 🔐 IMEI",
        ]
    else:
        lines += ["", "Ab tools sirf button se chalenge."]
    await update.message.reply_text("\n".join(lines), parse_mode=HTML)


async def cmd_toolstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 /toolstats — admin: kaunsa tool kitna chala, kitna pass (earning analytics)."""
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(pro.toolstats_text(15), parse_mode=HTML)
    try:
        brk = pro.breaker_stats()
        if brk:
            _open = [b for b in brk if b["state"] != "closed"]
            if _open:
                await update.message.reply_text(
                    "🔌 <b>PROVIDER HEALTH</b>\n──────────────────────\n"
                    + "\n".join(f"• <b>{b['name']}</b> — {b['state']} "
                                f"(fail {b['fails']}, heal {b['heals']})"
                                for b in _open[:12]),
                    parse_mode=HTML)
    except Exception:                                            # noqa: BLE001
        pass


def main():
    # =====================================================================
    #  v60 — 🛡️ CRASH SHIELD SABSE PEHLE ON KARO
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
    # v76: 🧹 JANITOR — temp safai + atke hue ffmpeg process + cache prune +
    #       disk watchdog. (Crash ke 3 chhupe kaaran isi se band hote hain.)
    try:
        start_janitor()
    except Exception as _e:                                      # noqa: BLE001
        log.warning("janitor skip: %s", str(_e)[:100])

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

    # v65: NetworkError ("Unknown error in HTTP implementation") ka pakka ilaaj —
    #      bada connection pool + HTTP/1.1. Pehle pool chhota hone se
    #      ek saath kai file/photo bhejne par connection toot jaata tha.
    app = (Application.builder().token(BOT_TOKEN).post_init(_post_init)
           .connect_timeout(30.0).read_timeout(60.0).write_timeout(240.0)
           .media_write_timeout(300.0).pool_timeout(60.0)
           .connection_pool_size(64).http_version("1.1")
           .get_updates_connection_pool_size(16)
           .build())

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
    app.add_handler(CommandHandler(["speed", "tez", "fast"], cmd_speed))
    app.add_handler(CommandHandler(["rcsetup", "rcsetup_"], cmd_rcsetup))
    app.add_handler(CommandHandler(["cookies", "cookie", "biscuit"], cmd_cookies))
    app.add_handler(CommandHandler(["vault", "premiumvault", "datavault"], cmd_vault))
    app.add_handler(CommandHandler(["backup", "save"], cmd_backup))
    app.add_handler(CommandHandler(["restore", "recover"], cmd_restore))
    app.add_handler(CommandHandler(["vips", "viplist", "premiums"], cmd_vips))
    app.add_handler(CommandHandler(["fixvip", "vipfix"], cmd_fixvip))
    app.add_handler(CommandHandler(["ledger", "viphistory"], cmd_ledger))
    # v75 — 🧠 PRO ENGINE commands
    app.add_handler(CommandHandler(["history", "recent", "myrecent"], cmd_history))
    app.add_handler(CommandHandler(["smart", "autodetect", "auto"], cmd_smart))
    app.add_handler(CommandHandler(["bulk", "bulkexcel", "report"], cmd_bulk))
    app.add_handler(CommandHandler(["toolstats", "analytics", "toolreport"], cmd_toolstats))

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
    # v75: on_cb ko PRO wrapper se jodo (tool analytics + history)
    app.add_handler(CallbackQueryHandler(_on_cb_pro))

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
    app.add_handler(MessageHandler(filters.Document.ALL & _dm_or_group, on_doc_cookies),
                    group=-5)          # v66: admin ki cookies.txt file
    app.add_handler(MessageHandler(_any_media & _dm_or_group, on_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & _dm_or_group, _on_text_pro))
    # v75.2: 📤 BULK MODE ke liye FILE input (.xlsx/.csv/.txt) — group=-4
    # (cookies handler -5 ke baad, baaki sabse pehle). File handle ho gayi to
    # ApplicationHandlerStop se aage koi handler use nahi chhoota.
    app.add_handler(MessageHandler(filters.Document.ALL & _dm_or_group, on_bulk_file),
                    group=-4)

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
    try:                                           # v74.4: board live-watch (har 6h)
        threading.Thread(target=_board_watch_loop, args=(app,), daemon=True).start()
    except Exception:                              # noqa: BLE001
        pass
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
        log.info("WEBHOOK MODE ON — polling OFF (Conflict ka koi chance nahi) | "
                 "instance=%s pid=%s", socket.gethostname(), os.getpid())
        try:                                           # v74.4: webhook self-heal
            threading.Thread(target=_webhook_watchdog,
                             args=(WEBHOOK_URL, path), daemon=True).start()
            log.info("WEBHOOK watchdog ON — har 15 min self-check (permanent ilaaj)")
        except Exception:                              # noqa: BLE001
            pass
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
    # v66: 🛡️ POLLING ab KABHI "give up" nahi karti.
    #  Pehle: 5 try ke baad `raise` -> supervisor -> main() dobara -> phir fail
    #         -> Render restart -> user ko lagta tha "bot crash ho gaya".
    #  Ab   : Conflict aaye to bas intezaar (backoff), chalta rahega.
    _try = 0
    while True:
        _try += 1
        try:
            app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES,
                            close_loop=False)
            log.warning("Polling ruk gayi (normal return) — dobara shuru kar raha hoon")
            time.sleep(3)
            continue
        except Exception as e:                                  # noqa: BLE001
            _msg = str(e).lower()
            log.error("Polling band hui (%s: %s)", type(e).__name__, str(e)[:200])
            if "conflict" in _msg:
                # purana instance band hone ka intezaar — webhook try bhi karo
                if _force_webhook_after_conflict(app):
                    return
                wait = min(300, 15 * _try)
                log.warning("Do instance ek saath chal rahe hain — %ss baad dobara "
                            "koshish (try #%s). Bot chalta rahega, koi crash nahi.", wait, _try)
                time.sleep(wait)
                continue
            wait = min(60, 5 * _try)
            log.warning("%ss baad dobara koshish (try #%s) — bot crash NAHI hoga",
                        wait, _try)
            time.sleep(wait)
            continue


if __name__ == "__main__":
    # --check = sirf self-check chalao (deploy verify ke liye), warna supervisor
    if "--check" in sys.argv:
        _startup_selfcheck()
        sys.exit(0)
    _supervise()
