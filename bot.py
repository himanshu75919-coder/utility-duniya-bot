#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility Duniya Bot — v108.0 SLIM
=====================================================================

  ✅ IS BOT ME SIRF 2 TOOLS HAIN:
        📱 NUMBER INFO    — 10 digit number  → operator / circle / record
        👪 FAMILY INFO    — 12 digit Aadhaar → ration card + family

  ❌ v108 me ye 15 tools PERMANENTLY DELETE kar diye gaye (user ka order):
        YouTube DL · TikTok DL · Insta DL · Channel Cloner ·
        Terabox Downloader · Website Owner X-Ray · Temp Mail ·
        Temp Number · QR Code · QR Scanner · Link Check · URL Short ·
        Business Studio · Bank Statement→Excel · Media Studio ·
        My Account · Support/Madad · Virtual Numbers · RC+Challan ·
        Pincode · IFSC · Result Check · IMEI · VIP Premium
     Inka code, buttons, handlers, modules aur libraries — sab hata diye.

  🧠 KYUN (Render free plan = 512 MB RAM):
     Purana bot yt-dlp + ffmpeg + Pillow + reportlab + telethon load karta
     tha — idle par hi ~450 MB. OOM killer bot ko maar deta tha ("Killed")
     aur beech kaam me bot ruk jaata tha. Ab sirf halki libraries bachi
     hain, isliye bot 512 MB ki limit ke aas-paas kabhi nahi jaata.

  🔒 NUMBER INFO / FAMILY INFO ka code JAISA KA TAISA hai — card layout,
     API call, timeout, error message sab bilkul pehle jaisa.
"""

import asyncio
import logging
import os
import re
import socket
import sys
import threading
import time
from html import escape as hesc

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:                                                # noqa: BLE001
    pass

# ---------------- CORE (crash shield / memory / safety) ----------------
from modules.core.safeconf import (env_bool as _env_bool, env_int as _env_int,
                                   env_str as _env_str)
from modules.core.guard import (crash_state as guard_crash_state,
                                guarded, install_global_guard,
                                start_hang_watchdog, start_memory_watchdog,
                                mem_mb as _mem_mb, free_memory as _free_mem)
from modules.core.janitor import (janitor_block as _janitor_block,
                                  janitor_stats as _janitor_stats,
                                  start_janitor)
from modules.core.bounded import (cache_report as _bounded_report,
                                  clear_all_caches as _bounded_clear)
from modules.core import updategate as _ug
from modules.core import joinwall as JW
from modules.core import memtrace as _mt
from modules.core.safesend import (safe_answer_cb, safe_delete, safe_edit,
                                   safe_reply, safe_send_text)
from modules.core.vault import (db_path as vault_db_path, vault,
                                set_main_loop as vault_set_main_loop)
from modules.core import check_limit, limiter_stats
from modules.core.telemetry import (note as tel_note, snapshot as tel_snapshot,
                                    worst_tools as tel_worst_tools)
from modules.core.cache import TTLCache

# ---------------- TELEGRAM ----------------
from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, TypeHandler, filters)

# ---------------- DATABASE (users / ban / vault backup) ----------------
from database import (add_referral, add_use, all_user_ids, find_by_username,
                      get_user, get_user_row, grant_premium, is_banned,
                      is_premium, meta_get, meta_set, recent_users,
                      save_username, set_ban, stats)

# ---------------- THE ONLY TWO TOOLS ----------------
from modules import mynum_api as mynum                 # 📱 NUMBER INFO ka API
from modules import familyinfo_api as faminfo          # 👪 FAMILY INFO ka API
from modules.osint_tools import lookup_phone_info      # offline number parse
from modules.render_health import (webhook_url_from_env, webhook_url_usable,
                                   webhook_preflight, webhook_delivery_state,
                                   webhook_needs_repair, webhook_repair)



# =====================================================================
#  CONFIG
# =====================================================================
BOT_TOKEN = _env_str("BOT_TOKEN", "")
ADMIN_ID = _env_int("ADMIN_ID", 0)

_ADMIN_EXTRA = [x.strip() for x in _env_str("ADMINS", "").split(",") if x.strip()]
_ADMIN_EXTRA = [int(x) for x in _ADMIN_EXTRA if x.lstrip("-").isdigit()]
ADMIN_IDS = {x for x in ([ADMIN_ID] + _ADMIN_EXTRA) if x}
OWNER_ID = ADMIN_ID


def is_admin(uid: int) -> bool:
    """Owner/admin hai? Uske liye koi premium limit nahi lagti."""
    return bool(ADMIN_IDS) and uid in ADMIN_IDS


OWNER_USERNAME = (_env_str("OWNER_USERNAME", "") or "Supermannn_x").lstrip("@")
SUPPORT_USERNAME = "@" + OWNER_USERNAME
SUPPORT_URL = f"https://t.me/{OWNER_USERNAME}"
SUPPORT_LINK = f'<a href="{SUPPORT_URL}">@{OWNER_USERNAME}</a>'
BRAND_TAG = (_env_str("BRAND_TAG", "") or SUPPORT_USERNAME)
BRAND_LINK = f'🔥 Powered by <a href="{SUPPORT_URL}">{BRAND_TAG}</a>'

HTML = "HTML"
BAN_MSG = f"🚫 Aapka account ban hai. Admin se baat karo: {SUPPORT_LINK}"
WEBHOOK_URL = (_env_str("WEBHOOK_URL", "") or webhook_url_from_env()).rstrip("/")

BOT_VERSION = (
    "v108.0 SLIM — ✂️ 15 tools PERMANENTLY DELETE (YouTube/TikTok/Insta DL, "
    "Cloner, Terabox, Whois X-Ray, Temp Mail, Temp Number, QR, Link Check, "
    "URL Short, Business Studio, Bank→Excel, Media Studio, My Account, "
    "Support) + 🪶 yt-dlp/ffmpeg/Pillow/reportlab/telethon dependencies gayi "
    "— Render free 512MB par idle RAM ~450MB se girkar ~110MB | "
    "✅ bache: 📱 NUMBER INFO + 👪 FAMILY INFO (code bilkul unchanged)"
)
START_TIME = time.time()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Application").setLevel(logging.WARNING)
log = logging.getLogger("utility-duniya")

# v93: Telegram HTML ko hamesha repair karke bhejo (parse-entity crash band)
try:
    from modules.core.htmlnet import patch_bot_html_safety
    patch_bot_html_safety()
except Exception as _he:                                         # noqa: BLE001
    log.debug("html net skip: %s", str(_he)[:80])

# ALL_FREE: dono tools sabke liye khule (koi VIP / credit nahi)
ALL_FREE = _env_bool("ALL_FREE", True)
PREMIUM_ONLY = False


# Info-tools ka shared cache (IFSC / pincode / IP / area) — same sawaal par
# API call dobara nahi hoti. 30 min TTL: ye data din bhar change nahi hota.
INFO_CACHE = TTLCache(maxsize=_env_int("INFO_CACHE_SIZE", 4096, lo=64, hi=200000),
                      default_ttl=_env_int("INFO_CACHE_TTL", 1800, lo=30, hi=86400))


# har tool ki rate limit: (kitni baar, kitne second me, naam)
TOOL_RATE_LIMITS = {
    "numinfo":    (10, 60, "Number Info"),
    "familyinfo": (10, 60, "Family Info"),
}

PREMIUM_TOOL_NAMES = {
    "numinfo": "📱 Number Info",
    "familyinfo": "👪 Family Info",
}


# ---------------- AESTHETIC BOLD UNICODE HELPER ----------------
def to_bold(text: str) -> str:
    """v102: FONT COPY (user order — OSINT Lookup style).

    Pehle ye Mathematical Bold Unicode banata tha (𝐅𝐀𝐌𝐈𝐋) — ab text
    SAADA rehta hai; asli bold Telegram ke HTML <b> se aata hai. Isi liye
    ab har button/prompt/card OSINT bot jaisa clean plain font dikhta hai.
    """
    return text


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


async def _reply_nonempty(msg, text, **kw):
    """v82: khaali text par Telegram 'Message text is empty' error deta tha — aur media bhej
    dene ke BAAD bhi user ko galat 'SEND FAILED' dikhta tha (free mode me credit note khaali
    hota hai). Ab khaali ho to chup-chaap skip; warna normal reply."""
    if text is None or not str(text).strip():
        return None
    return await msg.reply_text(text, **kw)


def credits_left(u: dict, uid: int = 0) -> int:
    """v108: dono tools 100% free hain — hamesha unlimited."""
    return 999999


def can_use_premium_tool(u: dict, uid: int = 0) -> bool:
    """Tool chalane layak hai? (v108: hamesha haan — sab free hai)"""
    return True


def get_credits_over_text(action: str = "") -> str:
    """v108: credits system hata diya — ye kabhi nahi dikhta, safe fallback."""
    return "⚠️ Thodi der baad try karo."


def get_limit_exceeded_kb():
    return None


def spend_credit_msg(uid: int, action: str = "") -> str:
    """v108: koi credit nahi katta — khaali string (card ke upar kuch nahi)."""
    return ""


# =====================================================================
#  ⌨️  MENU — sirf 2 buttons (v108)
# =====================================================================
KB_BTNS = [
    [f"📱 {to_bold('NUMBER INFO')}", f"👪 {to_bold('FAMILY INFO')}"],
]


def main_keyboard(admin: bool = False):
    rows = [row[:] for row in KB_BTNS]
    if admin:
        rows.append([f"🛠️ {to_bold('ADMIN PANEL')}"])
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t) for t in row] for row in rows],
        resize_keyboard=True,
        input_field_placeholder="Select a tool 👇",
    )


def kb_for(uid: int):
    return main_keyboard(admin=is_admin(uid))


# Button ka text → tool ka mode
BTN_MODE_MAP = {
    "NUMBER INFO": "numinfo",
    "NUMBER": "numinfo",
    "NUM INFO": "numinfo",
    "FAMILY INFO": "familyinfo",
    "FAMILY": "familyinfo",
    "ADMIN PANEL": "admin_panel",
}


# ---------------------------------------------------------------------
#  v108: DELETE ho chuke tools — purane keyboard wale users agar inme se
#  koi button daba dein to crash/silence nahi, saaf jawab milta hai.
# ---------------------------------------------------------------------
_REMOVED_TOOLS = {
    "YOUTUBE DL": "▶️ YouTube DL", "YOUTUBE": "▶️ YouTube DL",
    "TIKTOK DL": "🎵 TikTok DL", "TIKTOK": "🎵 TikTok DL",
    "INSTA DL": "📸 Insta DL", "INSTAGRAM DL": "📸 Insta DL",
    "INSTAGRAM": "📸 Insta DL", "INSTA": "📸 Insta DL",
    "FACEBOOK DL": "📘 Facebook DL",
    "CHANNEL CLONER": "🔄 Channel Cloner", "CLONER": "🔄 Channel Cloner",
    "TERABOX DOWNLOADER": "⚡ Terabox Downloader", "TERABOX": "⚡ Terabox Downloader",
    "WEBSITE OWNER X-RAY": "🌐 Website Owner X-Ray", "WHOIS": "🌐 Website Owner X-Ray",
    "TEMP MAIL": "📧 Temp Mail", "TEMPMAIL": "📧 Temp Mail",
    "TEMP NUMBER": "📞 Temp Number", "TEMP MAIL (NUMBER)": "📞 Temp Number",
    "VIRTUAL NUMBERS": "🌐 Virtual Numbers", "VNUM": "🌐 Virtual Numbers",
    "QR CODE": "📷 QR Code", "QR SCANNER": "📷 QR Scanner", "QR": "📷 QR Code",
    "LINK CHECK": "🔍 Link Check", "LINKCHECK": "🔍 Link Check",
    "URL SHORT": "🔗 URL Short", "SHORT": "🔗 URL Short",
    "BUSINESS STUDIO": "💼 Business Studio", "BIZ STUDIO": "💼 Business Studio",
    "BANK STATEMENT → EXCEL": "🏦 Bank Statement → Excel",
    "BANK STATEMENT TO EXCEL": "🏦 Bank Statement → Excel",
    "BANK STATEMENT - EXCEL": "🏦 Bank Statement → Excel",
    "BANKPDF": "🏦 Bank Statement → Excel",
    "MEDIA STUDIO (MP3/STATUS)": "⚡ Media Studio", "MEDIA STUDIO": "⚡ Media Studio",
    "MY ACCOUNT": "👤 My Account", "ACCOUNT": "👤 My Account",
    "SUPPORT / MADAD": "💬 Support / Madad", "SUPPORT": "💬 Support / Madad",
    "MADAD": "💬 Support / Madad",
    "RC + CHALLAN": "🚗 RC + Challan", "GAADI X-RAY": "🚗 RC + Challan",
    "PINCODE INFO": "📮 Pincode Info", "PINCODE": "📮 Pincode Info",
    "IFSC INFO": "🏦 IFSC Info", "IFSC": "🏦 IFSC Info",
    "RESULT CHECK": "📋 Result Check",
    "IMEI / PHONE DETAILS": "📲 IMEI / Phone Details", "IMEI": "📲 IMEI / Phone Details",
    "VIP PREMIUM": "💎 VIP Premium", "ALL TOOLS (FREE)": "📋 All Tools",
}


def removed_tool_text(name: str) -> str:
    return (
        f"🗑️ <b>{hesc(name)} ab is bot me nahi hai.</b>\n"
        f"{PCARD_MID}\n\n"
        "Ye tool permanently delete kar diya gaya hai taaki bot halka rahe "
        "aur kabhi beech me na ruke.\n\n"
        "✅ <b>Ab sirf 2 tools hain:</b>\n"
        "   📱 <b>NUMBER INFO</b>  — 10 digit number bhejo\n"
        "   👪 <b>FAMILY INFO</b>  — 12 digit Aadhaar bhejo\n\n"
        "👇 Neeche naya menu use karo (ya /refresh dabao)"
    )


# =====================================================================
#  CARD / PROMPT STYLE (v102 OSINT-plain — bilkul pehle jaisa)
# =====================================================================
PCARD_TOP = ""
PCARD_MID = "━━━━━━━━━━━━━━━━━━━━━━"
PCARD_BOT = ""

PROMPT_DATA = {
    "numinfo": {
        "head": "📱 NUMBER INFO V2 ENGINE",
        "ask": "10 Digit Number bhejein:",
        "ex": [('7857843092', '10 digit ka mobile number')],
        "tip": '+91 ya 0 pehle lagane ki zaroorat nahi — seedha 10 digit bhejo',
        "foot": 'Circle · operator · owner card',
    },
    "familyinfo": {
        "head": "👪 FAMILY INFO",
        "ask": "12-digit Aadhaar number bhejein:",
        "ex": [('401635555849', '12-digit Aadhaar number')],
        "tip": 'Aadhaar hamesha masked rehta hai (XXXX-XXXX-1234) — poora kabhi nahi dikhta',
        "foot": 'Ration card · family members · eKYC',
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
    # v102: OSINT-style — plain header line + heavy divider, no ┏ box,
    # no unicode-bold (to_bold ab identity hai; asli bold <b> se)
    if " " in head:
        _icon, _rest = head.split(" ", 1)
        L = [f"{_icon} <b>{_rest}</b>", PCARD_MID]
    else:
        L = [f"<b>{head}</b>", PCARD_MID]
    L.append("")
    L.append(f"🔗 <b>{hesc(str(d.get('ask') or ''))}</b>")
    ex = d.get("ex") or []
    if ex:
        L.append("")
        L.append(f"     <code>{hesc(str(ex[0][0]))}</code>")
    return "\n".join(L)


PROMPTS = {k: _render_tool_prompt(k) for k in PROMPT_DATA}


def tool_prompt(action: str) -> str:
    """Tool ka prompt (v102 plain format) — bilkul pehle jaisa."""
    return PROMPTS.get(action, "")


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
    return f"{icon} <b>{to_bold(name)}</b>\n{PCARD_MID}\n"


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

    Yehi layout number API ka record card banata hai. Owner ki lines sirf
    tab aati hain jab `owner` dict me wo field ho (yani jab API wo bheje).
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
                     "ye data number API se aata hai.")
        _card.append("💡 Record nahi mila? Number sahi likho → <code>/numapi</code> se API test karo.")
    _card.append(BRAND_LINK)   # v59.7: clickable
    return "\n".join([_l for _l in _card if _l])


def familyinfo_card(res: dict, src_line: str = "", ms: float = 0) -> str:
    """👪 FAMILY INFO card — v102 redesign (user order: OSINT-style saaf-suthra
    look — har block ke beech space, ━ dividers, faaltu IDs nahi).

    Aadhaar HAMESHA masked — poora number is card me kahin nahi aata.
    """
    res = res if isinstance(res, dict) else {}
    L = ["👪 <b>FAMILY INFO — RATION CARD</b>",
         PCARD_MID,
         ""]
    L.append(f"🔐 <b>Aadhaar:</b>       <code>{hesc(str(res.get('aadhaar_mask') or 'XXXX-XXXX-••••'))}</code>")
    if res.get("card_number"):
        _ct = f"   ·   {hesc(str(res['card_type']))}" if res.get("card_type") else ""
        L.append(f"🪪 <b>Ration Card:</b>  <code>{hesc(str(res['card_number']))}</code>{_ct}")
    if res.get("state_dist"):
        _sd = str(res["state_dist"])
        if "/" in _sd:
            _a, _b = [x.strip() for x in _sd.split("/", 1)]
            L.append(f"📍 <b>State:</b>        {hesc(_a)}")
            L.append(f"📍 <b>Dist:</b>         {hesc(_b)}")
        else:
            L.append(f"📍 <b>State/Dist:</b>   {hesc(_sd)}")
    if res.get("fps"):
        L.append(f"🏪 <b>FPS Shop:</b>     <code>{hesc(str(res['fps']))}</code>")
    if res.get("family_count"):
        L.append(f"👥 <b>Members:</b>      {hesc(str(res['family_count']))}")
    _addr = str(res.get("address") or "").strip()
    if _addr:
        L.append("")
        L.append("🏠 <b>Address:</b>")
        _toks = [x.strip() for x in _addr[:300].split(",") if x.strip()]
        _cur = ""
        for tk in _toks:
            if _cur and len(_cur) + len(tk) + 2 > 40:
                L.append(f"   {hesc(_cur)}")
                _cur = tk
            else:
                _cur = (f"{_cur}, {tk}" if _cur else tk)
        if _cur:
            L.append(f"   {hesc(_cur)}")
    _mem = res.get("members") or []
    if _mem:
        L += ["", PCARD_MID, "", "👨‍👩‍ <b>FAMILY MEMBERS</b>", ""]
        for _i, _m in enumerate(_mem[:12], 1):
            _mn = hesc(str(_m.get("name") or "—"))
            _me = str(_m.get("ekyc") or "").strip()
            # v102: member_id (21-digit) dikhana BAND — faaltu shor tha
            L.append(f"   {_i}.  <b>{_mn}</b>" + (f"   —   {hesc(_me)}" if _me else ""))
    L += ["", PCARD_MID, ""]
    _bits = []
    if src_line:
        _bits.append(f"📡 <b>Source:</b> {src_line}")
    if ms:
        _bits.append(f"⚡ <b>Speed:</b> {int(ms)}ms")
    if _bits:
        L.append("   |   ".join(_bits))
    L.append("✅ <b>Lookup Status: SUCCESS</b>")
    L += ["", BRAND_LINK]
    return "\n".join(L)


# ---------------- v101: ⏳ WAIT-FEW-SECONDS + TYPING PUMP ----------------
# User ka order: tool me input bhejte hi sirf "Wait few seconds" dikhao,
# phir result. Beech me bot "typing..." dikhata rahe (active lage) — jab tak
# result na bheja jaaye. Typing pump khud ruk jaata hai jab bot koi bhi
# message send/edit/delete karta hai (niche wala Bot-wrapper dekhता hai).
WAIT_NOTE = "⏳ <b>Wait few seconds...</b>"


_TYPING_STOP: dict = {}


def _arm_typing(bot, chat_id: int):
    """Chal raha typing pump 4.3s ke tick par 'typing...' bhejta rehta hai."""
    try:
        if chat_id in _TYPING_STOP:
            return  # already pumping
        _TYPING_STOP[chat_id] = False

        async def _pump():
            try:
                for _ in range(40):                      # ~3 min hard cap
                    if _TYPING_STOP.get(chat_id, True):
                        return
                    await bot.send_chat_action(chat_id=chat_id, action="typing")
                    await asyncio.sleep(4.3)
            except Exception:                            # noqa: BLE001
                pass
            finally:
                _TYPING_STOP.pop(chat_id, None)

        asyncio.get_running_loop().create_task(_pump())
    except Exception:                                    # noqa: BLE001
        pass


def _stop_typing(chat_id):
    if chat_id in _TYPING_STOP:
        _TYPING_STOP[chat_id] = True


async def _wait_st(target):
    """⏳ 'Wait few seconds' note bhejo + typing pump arm karo. st lauta do."""
    m = await target.reply_text(WAIT_NOTE, parse_mode=HTML)
    try:
        _stop_typing(target.chat_id)                     # purana pump (agar) reset
        _arm_typing(target.get_bot(), target.chat_id)
    except Exception:                                    # noqa: BLE001
        pass
    return m


def _wrap_bot_typing_stop():
    """Jab bhi bot user ko message bheje/edit kare → us chat ka typing pump band."""
    from telegram import Bot as _TGBot
    for _nm in ("send_message", "send_photo", "send_video", "send_audio", "send_document",
                "send_animation", "send_voice", "edit_message_text", "edit_message_caption",
                "edit_message_media", "delete_message"):
        if getattr(_TGBot, "_v101_wrapped", False):
            break
        def _mk(name):
            _orig = getattr(_TGBot, name)

            async def _w(self, *a, **k):
                r = await _orig(self, *a, **k)
                try:
                    cid = k.get("chat_id")
                    if cid is None and a:
                        cid = a[0]
                    if cid is not None:
                        _stop_typing(int(cid))
                except Exception:                        # noqa: BLE001
                    pass
                return r
            return _w
        _nf = _mk(_nm)
        try:  # v101: HTML-net (v93) ka marker zinda rakho — tests dhundhte hain
            if getattr(_TGBot, _nm, None) is not None and getattr(getattr(_TGBot, _nm), "__ud_wrapped__", False):
                _nf.__ud_wrapped__ = True
        except Exception:                        # noqa: BLE001
            pass
        setattr(_TGBot, _nm, _nf)
    try:
        _TGBot._v101_wrapped = True
    except Exception:                                    # noqa: BLE001
        pass


try:
    _wrap_bot_typing_stop()
except Exception as _we:                                         # noqa: BLE001
    log.debug("typing wrap skip: %s", str(_we)[:80])


# =====================================================================
#  WELCOME
# =====================================================================
WELCOME_TEXT = (
    f"⚡ <b>{to_bold('UTILITY DUNIYA BOT')}</b> ⚡\n"
    "<blockquote>2 kaam ke tools — tez, free aur bina rukawat 🚀</blockquote>\n\n"
    "📱 <b>NUMBER INFO</b>\n"
    "   10 digit mobile number bhejo → operator, circle aur record\n\n"
    "👪 <b>FAMILY INFO</b>\n"
    "   12 digit Aadhaar bhejo → ration card + family members\n\n"
    "🎉 <b>Dono 100% FREE hain</b> — na VIP, na credits, na limit ✅\n\n"
    "👇 Neeche menu se tool dabao"
)

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

    # v81.0: 🔐 FORCE-JOIN WALL — referral handle karne ke BAAD, welcome se PEHLE.
    # (Referral pehle isliye ki wall ke baad user wapas na aaye to referrer ka
    # credit na kho — ye behaviour v52 se aisa hi chal raha hai.)
    if not await JW.gate(update, context):
        return

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


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Band kar diya! Menu ready hai 👇", reply_markup=kb_for(update.effective_user.id))


async def cmd_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/refresh — keyboard/menu dobara set karo (purana menu hatane ke liye)."""
    context.user_data.pop("mode", None)
    await update.message.reply_text(
        "🔄 <b>Menu refresh ho gaya!</b>\n"
        "Purane buttons hata diye gaye hain — ab neeche wala naya menu use karo 👇",
        reply_markup=kb_for(update.effective_user.id), parse_mode=HTML)


def functools_partial(fn, *a, **kw):
    """functools.partial ka chhota wrapper (executor me chalane ke liye)."""
    import functools as _f
    return _f.partial(fn, *a, **kw)


# v60: memory watchdog in caches ko safai ke waqt khali kar sakta hai
# (Render free plan par 512 MB se aage jaate hi "Killed" ho jata tha).
def _clear_caches_mem() -> None:
    try:
        INFO_CACHE.clear()
    except Exception:                                            # noqa: BLE001
        pass
    for _m in ("mynum_api", "familyinfo_api", "osint_tools"):
        try:
            _mod = sys.modules.get("modules." + _m)
            for _at in ("_CACHE", "_INFO", "_MEM"):
                _o = getattr(_mod, _at, None)
                if _o is not None and hasattr(_o, "clear"):
                    _o.clear()
        except Exception:                                        # noqa: BLE001
            pass
    try:
        _bounded_clear()
    except Exception:                                            # noqa: BLE001
        pass


def _memtrace_boot() -> None:
    """MEM_TRACE=on ho to tracemalloc chalu (MEM_TRACE_SECONDS baad apne aap band)."""
    try:
        from modules.core import memtrace as _mt
        if _mt.maybe_start_from_env():
            log.info("🩸 leak-hunt ON (MEM_TRACE) — /health par 'leak-hunt:' line dikhegi")
    except Exception as e:                                         # noqa: BLE001
        log.debug("memtrace skip: %s", str(e)[:80])


def _mem_relief(tag: str = "") -> None:
    """Bhaari kaam ke baad RAM foran wapas lao (OS ko pages lautao).

    Kyun: guard ka watchdog ab har 15s chalta hai — RAM 389MB cross hote hi cache
    trim hota hai, aur 410MB par naye heavy jobs rok diye jaate hain. free_memory() ab malloc_trim
    bhi karta hai, isliye RSS sach me girta hai (pehle gc_runs=3 par bhi 0 MB gira
    tha — 8 Oct ko yahi napa tha).
    """
    try:
        from modules.core.guard import free_memory as _fm, mem_mb as _mm
        soft = float(os.environ.get("MEM_RELIEF_MB") or 340)
        m = _mm()
        if m >= soft:
            r = _fm(aggressive=m >= soft + 60)
            if r.get("freed_mb", 0) >= 1:
                log.info("🧹 mem-relief%s: %.0f → %.0f MB (trim=%s)", (" " + tag) if tag else "",
                         r["before_mb"], r["after_mb"], r.get("trim"))
    except Exception as e:                                          # noqa: BLE001
        log.debug("mem relief skip: %s", str(e)[:80])


def _leak_hunt_line() -> str:
    """/health par tracemalloc ki line (MEM_TRACE=on par). Off ho to khaali."""
    try:
        from modules.core import memtrace as _mt
        rep = _mt.report()
        return (f"<p style='font-family:monospace'>{hesc(rep)}</p>" if rep else "")
    except Exception:                                              # noqa: BLE001
        return ""


def _bot_idle() -> bool:
    """Memory-pressure restart ka green signal: abhi koi kaam chal hi nahi raha."""
    try:
        u = _ug.stats() or {}
        busy = int(u.get("parallel") or 0) + int(u.get("waiting_chat_lock") or 0)
        return busy == 0
    except Exception:                                            # noqa: BLE001
        return False


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


def _cb_data_short(update) -> str:
    """v83: log ke liye callback data ka chhota tukda (crash-free)."""
    try:
        return str(getattr(getattr(update, "callback_query", None), "data", "") or "")[:40]
    except Exception:                                            # noqa: BLE001
        return ""


async def _cb_stale_reply(update, context) -> None:
    """v83: callback me galti (purana/adhoora button) → user ko chhota saaf jawab, crash nahi."""
    try:
        _chat = getattr(update, "effective_chat", None)
        if _chat is not None:
            await context.bot.send_message(
                _chat.id,
                "❌ <b>Ye button purana ya adhoora ho gaya.</b>\n"
                "Menu se tool dobara kholo — phir kaam karega.",
                parse_mode=HTML)
    except Exception:                                            # noqa: BLE001
        pass


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


# v59.10: "bot sach me jawab de raha hai?" — aakhri update kab aaya (user ki
# sabse badi confusion: purana screenshot dekh kar lagta hai bot band hai).
_UPDATE_STATE = {"n": 0, "last_ts": 0.0, "last_at": None}


def _last_update_line() -> str:
    """"Aakhri message: 3 min pehle" — 0 ho to saaf saaf likho."""
    if not _UPDATE_STATE["n"] or not _UPDATE_STATE["last_ts"]:
        return "abhi tak koi message nahi aaya (bot naya start hua hai)"
    _ago = int(max(0, time.time() - _UPDATE_STATE["last_ts"]))
    _ago_s = f"{_ago}s" if _ago < 60 else (f"{_ago // 60}m {_ago % 60}s" if _ago < 3600 else f"{_ago // 3600}h")
    return (f"aakhri message {_ago_s} pehle ({_UPDATE_STATE['last_at']})"
            f" | total {_UPDATE_STATE['n']} updates")


# =====================================================================
#  BOOT SELF-CHECK + CRASH SUPERVISOR
# =====================================================================
_BOOT_TS = time.time()
_GIT_COMMIT = (os.environ.get("RENDER_GIT_COMMIT") or "")[:7]
_GIT_BRANCH = os.environ.get("RENDER_GIT_BRANCH") or ""
if not _GIT_COMMIT:
    try:
        import subprocess as _sp
        _GIT_COMMIT = _sp.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       stderr=_sp.DEVNULL, timeout=5
                                       ).decode().strip()
    except Exception:                                            # noqa: BLE001
        _GIT_COMMIT = ""
_START_TS = time.time()
# self-heal counter — `_supervise()` isme ginti badhata hai, /health par dikhta hai
_CRASH_STATE = {"count": 0, "last": "", "why": ""}


def _startup_selfcheck() -> None:
    """Boot par ek nazar ka check — v108 me sirf 2 tools, isliye chhota hai."""
    print("=" * 62)
    print(f"🔎 SELF-CHECK | {BOT_VERSION.split('—')[0].strip()}")
    print("=" * 62)
    ok = True
    for _mn in ("mynum_api", "familyinfo_api", "osint_tools", "render_health"):
        try:
            __import__("modules." + _mn)
            print(f"   ✅ modules/{_mn}.py")
        except Exception as _e:                                  # noqa: BLE001
            ok = False
            print(f"   ❌ modules/{_mn}.py — {type(_e).__name__}: {str(_e)[:70]}")
    print(f"   🧰 tools live: 📱 NUMBER INFO + 👪 FAMILY INFO (sirf 2)")
    print(f"   📱 Number Info API: {'🟢 set' if mynum.is_configured() else '⚪ default'}")
    try:
        print(f"   👪 Family Info API: {'🟢 set' if faminfo.is_configured() else '⚪ default'}")
    except Exception:                                            # noqa: BLE001
        pass
    print(f"   👑 ADMIN_ID: {'🟢 ' + str(ADMIN_ID) if ADMIN_ID else '🔴 set nahi'}")
    print(f"   🔑 BOT_TOKEN: {'🟢 mil gaya' if BOT_TOKEN else '🔴 missing'}")
    try:
        print(f"   🧠 boot RAM: {_mem_mb():.0f} MB (Render free limit 512 MB)")
    except Exception:                                            # noqa: BLE001
        pass
    try:
        print(f"   🛡️ vault: {'🟢 on' if vault.enabled() else '⚪ off'}"
              f" | github={'🟢' if vault.gh_ready() else '⚪'}")
    except Exception:                                            # noqa: BLE001
        pass
    print(f"   🛡️ self-heal: crashes={_CRASH_STATE['count']}")
    print("=" * 62)
    if not ok:
        print("⚠️ Upar ❌ wali line dekho — wahi module load nahi hua.")


def _hard_restart(reason: str, delay: float = 3.0, extra_env: dict = None) -> None:
    """v82: process ko SAAF restart karo — naya event loop, naya Application, koi leak nahi.
    os.execv se PID same rehta hai (Render ko crash/naya deploy jaisa nahi lagta).
    Fail ho to chup-chaap return — process isi state me chalta rahega."""
    try:
        _now = time.time()
        _last = float(os.environ.get("UDB_LAST_RESTART") or 0)
        _n = int(os.environ.get("UDB_RESTARTS") or 0) + 1
        if _now - _last < 120:                           # bahut jaldi-jaldi ho raha ho to thoda ruko
            delay = max(delay, 60.0)
        if os.path.basename(sys.argv[0] if sys.argv else "") != "bot.py":
            # v82: sirf `python bot.py` (Render) par process replace karo; tests/import me nahi
            log.warning("🔁 restart skip (bot.py se nahi chal raha): %s", reason)
            return
        log.warning("🔁 HARD RESTART #%s: %s (%.0fs baad)", _n, reason, delay)
        for _h in logging.getLogger().handlers:
            try:
                _h.flush()
            except Exception:                            # noqa: BLE001
                pass
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(delay)
        _env = dict(os.environ)
        _env.update({"UDB_RESTARTS": str(_n), "UDB_LAST_RESTART": str(time.time())})
        if extra_env:
            _env.update({k: str(v) for k, v in extra_env.items()})
        os.execve(sys.executable, [sys.executable, os.path.abspath(__file__)], _env)
    except Exception as _e:                              # noqa: BLE001
        log.error("hard restart fail (%s) — isi process me chalta rahega", str(_e)[:120])


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
            _hard_restart(f"crash {type(e).__name__}", delay=_wait)   # v82: saaf process restart
            time.sleep(_wait)


# =====================================================================
#  ADMIN / STATUS COMMANDS
# =====================================================================
async def cmd_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/version — kaunsa code chal raha hai."""
    _mem = ""
    try:
        _mem = f"\n🧠 <b>RAM:</b> {_mem_mb():.0f} MB / 512 MB"
    except Exception:                                            # noqa: BLE001
        pass
    await update.message.reply_text(
        f"🤖 <b>{to_bold('UTILITY DUNIYA BOT')}</b>\n"
        f"{PCARD_MID}\n"
        f"📦 <b>Version:</b> <code>{hesc(BOT_VERSION.split('|')[0].strip())}</code>\n"
        f"🔖 <b>Commit:</b> <code>{hesc(_GIT_COMMIT or 'unknown')}</code>\n"
        f"🌐 <b>Mode:</b> {'WEBHOOK' if WEBHOOK_URL else 'POLLING'}\n"
        f"⏱️ <b>Uptime:</b> {_uptime_str()}{_mem}\n"
        f"🧰 <b>Tools:</b> 📱 Number Info · 👪 Family Info\n"
        f"🛡️ <b>Self-heal:</b> crashes={_CRASH_STATE['count']}\n"
        f"{PCARD_MID}\n{BRAND_LINK}",
        parse_mode=HTML)


# ---------------- v99: /numapi — Number API status + live test (purana provider gaya) ----------------
async def cmd_numapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/numapi — admin: number API status + live test (`/numapi 9876543210`)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Sirf admin ke liye.", parse_mode=HTML)
        return
    card = mynum.status_card()
    args = [a.strip() for a in (context.args or []) if a.strip()]
    if not args:
        await update.message.reply_text(
            card + "\n\n🧪 <b>Live test chalao:</b> <code>/numapi 9876543210</code>",
            parse_mode=HTML)
        return
    test_no = args[0]
    st = await update.message.reply_text(
        f"🔎 Number API se <code>{hesc(test_no)}</code> test kar raha hoon… (30-40s lag sakta hai)",
        parse_mode=HTML)
    t0 = time.perf_counter()
    res = await asyncio.to_thread(mynum.lookup, test_no)
    ms = int((time.perf_counter() - t0) * 1000)
    if res.get("ok"):
        _ow = res.get("owner") or {}
        await st.edit_text(
            "✅ <b>API CHAL RAHI HAI!</b>\n"
            "──────────────────────\n"
            f"👤 <b>Name:</b> {hesc(str(_ow.get('name') or '—'))}\n"
            f"🏢 <b>Operator:</b> {hesc(str(res.get('operator') or '—'))}\n"
            f"📍 <b>Circle:</b> {hesc(str(res.get('circle') or '—'))}\n"
            f"🆔 <b>Govt ID:</b> {hesc(str(_ow.get('govt_id') or '—'))}\n"
            f"⚡ <b>Latency:</b> {ms}ms\n"
            f"🗄️ <b>Cache:</b> {'Haan (6 ghante)' if res.get('cached') else 'Nahi (fresh)'}\n"
            "──────────────────────\n"
            "📱 Ab Number Info tool number API se <b>live data</b> dega. 🔥",
            parse_mode=HTML)
        return
    await st.edit_text(
        "❌ <b>API test fail</b>\n"
        "──────────────────────\n"
        f"📄 <b>Wajah:</b> {safe_html_err(str(res.get('error') or 'unknown')[:220])}\n"
        "──────────────────────\n"
        "<b>Ye 4 cheezein check karo:</b>\n"
        "1️⃣ Number 10-digit sahi likha?\n"
        "2️⃣ API slow hai — 30-40 second wait karo\n"
        "3️⃣ Key dead? — Render me <code>MYNUM_API_KEY</code> check karo\n"
        "4️⃣ <code>/numapi</code> se dobara test karo\n\n"
        "📖 Poori guide: <code>NUMBER-INFO-API-SETUP.md</code>\n"
        "ℹ️ <i>Tab tak Number Info offline mode se chal raha hai — band nahi hai.</i>",
        parse_mode=HTML)


async def cmd_famapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/famapi — admin: Family Info API status + live test."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Sirf admin ke liye.", parse_mode=HTML)
        return
    try:
        card = faminfo.status_card()
    except Exception:                                            # noqa: BLE001
        card = "👪 <b>FAMILY INFO API</b>\n(status card uplabdh nahi)"
    args = [a.strip() for a in (context.args or []) if a.strip()]
    if not args:
        await update.message.reply_text(
            card + "\n\n🧪 <b>Live test:</b> <code>/famapi 401635555849</code>",
            parse_mode=HTML)
        return
    st = await update.message.reply_text("🔎 Family API test kar raha hoon…",
                                         parse_mode=HTML)
    t0 = time.perf_counter()
    res = await asyncio.to_thread(faminfo.lookup, args[0])
    ms = int((time.perf_counter() - t0) * 1000)
    if res.get("ok"):
        await st.edit_text(f"✅ <b>FAMILY API CHAL RAHI HAI</b> ({ms}ms)\n"
                           f"{PCARD_MID}\n"
                           f"🪪 Card: <code>{hesc(str(res.get('card_number') or '—'))}</code>\n"
                           f"👥 Members: {hesc(str(res.get('family_count') or '—'))}",
                           parse_mode=HTML)
        return
    await st.edit_text(f"❌ <b>Family API fail</b> ({ms}ms)\n{PCARD_MID}\n"
                       f"<code>{hesc(str(res.get('error') or 'unknown')[:200])}</code>",
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


def _vault_admin_block() -> str:
    """Admin /sys card me vault (data-safety) ki chhoti report."""
    try:
        lb = vault.last_backup or {}
        _st = vault.stats or {}
        L = ["🛡️ <b>Premium Vault:</b> " + ("🟢 ON" if vault.enabled() else "🔴 OFF")]
        L.append(f"   ☁️ GitHub: {'🟢 ready' if vault.gh_ready() else '⚪ off'}"
                 f"   ·   ✈️ Telegram: {'🟢 ready' if vault.telegram_ready() else '⚪ off'}")
        L.append(f"   🕒 last backup: {hesc(str(lb.get('at') or 'abhi nahi'))}"
                 f"   ·   📦 {_st.get('backups', 0)} ok / {_st.get('failures', 0)} fail")
        try:
            _vk = vault.key_source()
            if _vk != "env":
                L.append("   ⚠️ <b>VAULT_KEY set karo</b> — BotFather se token badla "
                         "to purane backup padhe nahi ja payenge")
        except Exception:                                        # noqa: BLE001
            pass
        return "\n".join(L) + "\n"
    except Exception as e:                                       # noqa: BLE001
        return f"🛡️ <b>Vault:</b> status nahi mila ({type(e).__name__})\n"


def system_stats_text() -> str:
    """Admin ka /sys card (v108 — chhota aur saaf)."""
    s = stats() or {}
    try:
        _m = f"{_mem_mb():.0f} MB / 512 MB"
    except Exception:                                            # noqa: BLE001
        _m = "n/a"
    L = [
        f"🛠️ <b>{to_bold('SYSTEM STATUS')}</b>",
        PCARD_MID,
        f"👥 <b>Users:</b> {s.get('users', 0):,}   ·   🚀 <b>Uses:</b> {s.get('uses', 0):,}",
        f"⏱️ <b>Uptime:</b> {_uptime_str()}",
        f"🧠 <b>RAM:</b> {_m}",
        f"🌐 <b>Mode:</b> {'WEBHOOK' if WEBHOOK_URL else 'POLLING'}"
        f"   ·   🔖 <code>{hesc(_GIT_COMMIT or '?')}</code>",
        f"🛡️ <b>Self-heal:</b> crashes={_CRASH_STATE['count']}",
        f"🧰 <b>Tools:</b> 📱 Number Info · 👪 Family Info",
        PCARD_MID,
    ]
    try:
        L.append(_vault_admin_block())
    except Exception:                                            # noqa: BLE001
        pass
    try:
        L.append(_telemetry_block())
    except Exception:                                            # noqa: BLE001
        pass
    try:
        L.append(_janitor_block())
    except Exception:                                            # noqa: BLE001
        pass
    L.append(BRAND_LINK)
    return "\n".join([x for x in L if x])


async def admin_panel_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="adm_sys")],
        [InlineKeyboardButton("🛡️ Backup abhi", callback_data="adm_backup")],
    ])
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(system_stats_text(), reply_markup=kb, parse_mode=HTML)


async def cmd_sys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Sirf admin ke liye.", parse_mode=HTML)
        return
    await admin_panel_send(update, context)


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_sys(update, context)


# =====================================================================
#  📥 TEXT HANDLER — yahi dono tools chalate hain
# =====================================================================
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

    action = BTN_MODE_MAP.get(clean_key) or BTN_MODE_MAP.get(norm_text)

    # ---------- v108: delete ho chuke tool ka purana button ----------
    if not action:
        _gone = _REMOVED_TOOLS.get(clean_key) or _REMOVED_TOOLS.get(norm_text)
        if _gone:
            context.user_data.pop("mode", None)
            await update.message.reply_text(removed_tool_text(_gone),
                                            reply_markup=kb_for(uid),
                                            parse_mode=HTML)
            return

    # ---------- admin panel ----------
    if action == "admin_panel":
        if not is_admin(uid):
            await update.message.reply_text("🚫 Sirf admin ke liye.", parse_mode=HTML)
            return
        context.user_data.pop("mode", None)
        await admin_panel_send(update, context)
        return

    # ---------- tool ka button daba → prompt dikhao ----------
    if action in PROMPTS:
        context.user_data["mode"] = action
        await update.message.reply_text(tool_prompt(action), parse_mode=HTML)
        return

    mode = str(context.user_data.get("mode") or "")

    # ---------- v108: bina button ke bhi seedha kaam kare ----------
    # 10 digit = number info, 12 digit = family info (user ka time bache)
    if not mode:
        _d = re.sub(r"\D", "", raw_text)
        if len(_d) == 10 and _d[0] in "6789":
            mode = "numinfo"
        elif len(_d) == 12:
            mode = "familyinfo"

    if not mode:
        await update.message.reply_text(
            "👇 <b>Pehle neeche se tool chuno:</b>\n\n"
            "   📱 <b>NUMBER INFO</b> — 10 digit mobile number\n"
            "   👪 <b>FAMILY INFO</b> — 12 digit Aadhaar number\n\n"
            "<i>Ya seedha number bhej do — bot khud pehchan lega.</i>",
            reply_markup=kb_for(uid), parse_mode=HTML)
        return

    # ---------- CENTRAL RATE-LIMIT GATE (pehle jaisa) ----------
    # Admin ko bypass. Limit lagti hai to user ko saaf message milta hai.
    if mode and not is_admin(uid):
        _rl = TOOL_RATE_LIMITS.get(mode)
        if _rl:
            _lim, _win, _tname = _rl
            _rlmsg = check_limit(uid, mode, limit=_lim, window=_win,
                                 bypass=is_admin(uid), tool_name=_tname)
            if _rlmsg:
                await update.message.reply_text(_rlmsg, parse_mode=HTML)
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
        _wn = await _wait_st(update.message)
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
        # v99: purane saare API gaye (provider slot + hub) — ab sirf AAPKA number API.
        _t0 = time.perf_counter()
        try:
            _mres = await asyncio.wait_for(
                asyncio.to_thread(mynum.lookup, raw_text), 55)
        except asyncio.TimeoutError:
            _mres = {"ok": False, "error": "API slow (55s)"}
        except Exception:                                        # noqa: BLE001
            _mres = {"ok": False}
        _ms = (time.perf_counter() - _t0) * 1000
        _prov = _mres if isinstance(_mres, dict) else {}

        # live data (number API) — na mile to offline card
        _live = {k: v for k, v in (_prov or {}).items() if v not in (None, "", False)}
        if not _prov.get("ok"):
            _live = {}

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

        if _src == "myapi":
            _recext = _prov.get("extra") if isinstance(_prov.get("extra"), dict) else {}
            _recn = int(_recext.get("records") or 0)
            _src_line = ("🟢 <b>LIVE</b> — number API se"
                         + (f" ({int(_prov.get('latency_ms') or _ms)}ms)" if (_prov.get("latency_ms") or _ms) else "")
                         + (" • cache" if _prov.get("cached") else "")
                         + (f" • 📑 {_recn} records" if _recn > 1 else ""))
        else:
            _src_line = "⚪ <b>OFFLINE</b> — API me record nahi mila (number sahi hai?)"

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
        await _reply_nonempty(update.message, spend_credit_msg(uid, "numinfo") + "\n" + card, parse_mode=HTML)
        add_use(uid)
        return

    if mode == "familyinfo":
        # v100: 👪 FAMILY INFO — Aadhaar → ration family record (poora Aadhaar kahin nahi).
        _u_fi = get_user(uid, update.effective_user.first_name)
        if not can_use_premium_tool(_u_fi, uid):
            await update.message.reply_text(get_credits_over_text("familyinfo"),
                                            reply_markup=get_limit_exceeded_kb(), parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        _wfi = await _wait_st(update.message)
        _t0fi = time.perf_counter()
        try:
            _fres = await asyncio.wait_for(
                asyncio.to_thread(faminfo.lookup, raw_text), 55)
        except asyncio.TimeoutError:
            _fres = {"ok": False, "error": "API slow (55s) — dobara try karo."}
        except Exception:                                        # noqa: BLE001
            _fres = {"ok": False, "error": "Family lookup me dikkat aayi."}
        _msfi = (time.perf_counter() - _t0fi) * 1000
        _fres = _fres if isinstance(_fres, dict) else {"ok": False}
        if not _fres.get("ok"):
            tel_note("familyinfo", False, 0, error=str(_fres.get("error"))[:90])
            await update.message.reply_text(f"❌ {_fres.get('error') or 'Record nahi mila.'}",
                                            parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        _fline = "🟢 <b>LIVE</b> — family API se" + (" (⚡ cache)" if _fres.get("cached") else "")
        _fcard = familyinfo_card(_fres, _fline, _msfi)
        tel_note("familyinfo", True, _msfi, credit=True)
        await _reply_nonempty(update.message, spend_credit_msg(uid, "familyinfo") + "\n" + _fcard, parse_mode=HTML)
        add_use(uid)
        return


    # yahan tak pahunche = mode set tha par handle nahi hua
    context.user_data.pop("mode", None)
    await update.message.reply_text(
        "🤔 <b>Samajh nahi aaya.</b>\n\nNeeche menu se tool chuno 👇",
        reply_markup=kb_for(uid), parse_mode=HTML)


async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """v108: ab sirf admin panel + join-wall ke buttons bache hain."""
    q = update.callback_query
    await safe_answer_cb(q)
    data = str(q.data or "")
    uid = q.from_user.id

    if data == "adm_sys" and is_admin(uid):
        await admin_panel_send(update, context)
        return
    if data == "adm_backup" and is_admin(uid):
        try:
            # NOTE: vault.backup_now ek async method hai — await hi karna hai
            res = await vault.backup_now(reason=f"admin-button:{uid}",
                                         also_telegram=False)
        except Exception as e:                                   # noqa: BLE001
            res = {"ok": False, "why": f"{type(e).__name__}: {str(e)[:120]}"}
        await q.message.reply_text(
            ("✅ <b>Backup ho gaya</b>" if res.get("ok") else
             "⚠️ <b>Backup fail:</b> "
             f"<code>{hesc(str(res.get('why'))[:150])}</code>"),
            parse_mode=HTML)
        return

    # purana / delete ho chuka button
    await _cb_stale_reply(update, context)


async def _on_text_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Join-wall gate ke baad asli text handler."""
    if not await JW.gate(update, context):
        return
    t0 = time.perf_counter()
    try:
        await on_text(update, context)
    finally:
        try:
            if (time.perf_counter() - t0) > 2.0:
                _mem_relief("text")
        except Exception:                                        # noqa: BLE001
            pass


async def _on_cb_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Join-wall ka apna button pehle, phir gate, phir on_cb."""
    _cb = getattr(update, "callback_query", None)
    if _cb is not None and str(getattr(_cb, "data", "") or "").startswith("fj:"):
        if await JW.handle_check(update, context):
            try:
                _uid = int(update.effective_user.id)
                if not context.user_data.get("_fj_menu"):
                    context.user_data["_fj_menu"] = True
                    await _cb.message.reply_text(WELCOME_TEXT, reply_markup=kb_for(_uid),
                                                 parse_mode=HTML)
            except Exception:                                    # noqa: BLE001
                pass
        return
    if not await JW.gate(update, context):
        return
    try:
        await on_cb(update, context)
    except (ValueError, IndexError) as _bad:
        log.warning("callback data galat/purana (%s): %s",
                    _cb_data_short(update), str(_bad)[:120])
        await _cb_stale_reply(update, context)


async def on_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Photo / video / file — v108 me inka koi tool nahi bacha."""
    try:
        if is_banned(update.effective_user.id):
            return
        await update.message.reply_text(
            "📵 <b>Is bot me file / photo / video ka koi tool nahi hai.</b>\n\n"
            "   📱 <b>NUMBER INFO</b> — 10 digit number bhejo\n"
            "   👪 <b>FAMILY INFO</b> — 12 digit Aadhaar bhejo",
            reply_markup=kb_for(update.effective_user.id), parse_mode=HTML)
    except Exception:                                            # noqa: BLE001
        pass


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
    # v82: khaali text wala error (free-mode credit note) — user ko koi galat error nahi dikhana
    if "message text is empty" in str(err).lower():
        log.info("v82: khaali message skip (user ko error nahi): %s", str(err)[:80])
        return
    # v83: benign Telegram errors — message pehle hi delete/purana ho gaya (bot ka bug nahi)
    _es = str(err).lower()
    if any(_s in _es for _s in ("message to edit not found", "message is not modified",
                                 "message to delete not found", "query is too old",
                                 "message can't be edited", "message can't be deleted")):
        log.info("v83: benign Telegram error skip: %s", str(err)[:80])
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
    try:
        _loop = asyncio.get_running_loop()
        try:
            vault_set_main_loop(_loop)
            log.info("🛡️ Vault: main event loop register ho gaya")
        except Exception as _ve:                                 # noqa: BLE001
            log.debug("vault loop register skip: %s", str(_ve)[:80])

        def _loop_err(_loop2, _ctx):
            _ex = _ctx.get("exception")
            if _ex is None:
                return
            log.warning("🛡️ background task error (bot chalta rahega): %s: %s",
                        type(_ex).__name__, str(_ex)[:200])
        _loop.set_exception_handler(_loop_err)
        from modules.core.guard import start_heartbeat_task
        start_heartbeat_task(_loop)
    except Exception:                                            # noqa: BLE001
        pass

    # ---- 🛡️ PREMIUM VAULT: boot par pichhla backup merge + auto-backup ----
    try:
        vault.bot = app.bot
        vault.owner_id = OWNER_ID
        _bchat = _env_int("VAULT_BACKUP_CHAT_ID", 0)
        vault.backup_chat = _bchat or OWNER_ID or None
    except Exception as e:                                       # noqa: BLE001
        log.warning("vault init skip: %s", str(e)[:120])

    try:
        if vault.enabled() and (vault.gh_ready() or vault.telegram_ready()):
            _res = await asyncio.get_running_loop().run_in_executor(
                None, functools_partial(vault.restore_now, "boot"))
            if _res.get("ok"):
                log.info("🛡️ BOOT RESTORE OK (%s)", _res.get("source"))
            else:
                log.info("vault boot-restore skip: %s", str(_res.get("why") or "")[:150])
    except Exception as e:                                       # noqa: BLE001
        log.warning("boot restore me dikkat (bot normal chalega): %s", str(e)[:150])

    try:
        vault.start_background(app.bot, OWNER_ID, vault.backup_chat)
    except Exception as e:                                       # noqa: BLE001
        log.warning("vault background skip: %s", str(e)[:120])

    commands = [
        BotCommand("start", "Bot chalu karo / menu kholo"),
        BotCommand("menu", "Dono tools ka menu"),
        BotCommand("cancel", "Chalu kaam band karo"),
        BotCommand("refresh", "Menu / keyboard naya karo"),
    ]
    try:
        await app.bot.set_my_commands(commands)
        log.info("Commands set ho gaye ✅")
    except Exception as e:                                       # noqa: BLE001
        log.warning("set_my_commands skip: %s", str(e)[:100])


_KEEPALIVE_PEERS = [p.strip().rstrip("/") for p in
                    _env_str("KEEPALIVE_PEERS", "").split(",") if p.strip()]
_self_url = _env_str("BOT_SELF_URL", "").strip().rstrip("/")
if _self_url and _self_url not in _KEEPALIVE_PEERS:
    _KEEPALIVE_PEERS.append(_self_url)
_KEEPALIVE_MINUTES = _env_int("KEEPALIVE_MINUTES", 10, lo=2, hi=60)
_KEEPALIVE_STATE = {"last_run": None, "last_ok": None, "runs": 0}
_WEBHOOK_DIAG = {"mode_env": "", "url_env": "", "ext_env": "",
                 "decision": "abhi decide nahi hua", "why": ""}
_KEEPALIVE_SERVER = {"srv": None}
_WH_STATE = {"at": 0.0, "data": {}, "fixes": 0, "last_fix": "", "checks": 0}
_WH_TTL = 60.0


def _webhook_delivery(force: bool = False, timeout: float = 2.0) -> dict:
    """getWebhookInfo ka cached haal (kabhi raise nahi karta, kabhi slow nahi)."""
    now = time.time()
    if not force and (now - _WH_STATE["at"]) < _WH_TTL and _WH_STATE["data"]:
        return _WH_STATE["data"]
    try:
        d = webhook_delivery_state(BOT_TOKEN, timeout=timeout)
    except Exception as e:                                        # noqa: BLE001
        d = {"ok": True, "pending": 0, "err": "", "dupes": 0, "registered": True,
             "note": f"check fail: {type(e).__name__}"}
    _WH_STATE["data"] = d
    _WH_STATE["at"] = now
    _WH_STATE["checks"] += 1
    return d


def _webhook_delivery_line() -> str:
    d = _webhook_delivery()
    if not d.get("registered"):
        return "delivery: ❌ Telegram par webhook REGISTRED HI NAHI (update kabhi nahi aayenge)"
    bits = [f"pending={int(d.get('pending') or 0)}"]
    if int(d.get("dupes") or 0) > 0:
        bits.append(f"⚠️ URL me /webhook {1 + int(d['dupes'])}x (double path = sab 404)")
    if d.get("err"):
        bits.append(f"last_err={str(d['err'])[:60]}")
    bits.append("✅ updates pahunch rahe hain" if d.get("ok") else "⚠️ delivery me dikkat")
    if _WH_STATE["fixes"]:
        bits.append(f"auto-fix={_WH_STATE['fixes']}"
                    + (f" ({_WH_STATE['last_fix'][:40]})" if _WH_STATE["last_fix"] else ""))
    return "delivery: " + " | ".join(bits)


def _webhook_watchdog(url: str, path: str) -> None:
    """v74.4 → v81.1: webhook ka PERMANENT ilaaj — har 3 min check, khud repair.

    v81.1 me iske DO asli kameel bug band kiye (8 Oct ko bot 20 minute se isiliye
    chup raha, ye watchdog chalta hua bhi kuch nahi bola):
      1) Ye apne *apne banaye* URL se tulna karta tha (`WEBHOOK_URL + path`). Env me
         URL hi double (`…/webhook/x/webhook/x`) tha to watchdog ko wo "sahi" lagta
         raha — kabhi repair nahi ki. Ab registered URL ka shape khud check hota hai
         ('/webhook' do baar = foran theek) aur Telegram ke getWebhookInfo se asli
         haal padha jaata hai.
      2) `pending > 60` ka threshold tha — us din 36 update phanse the, yaani neeche,
         to ye chup raha. Ab 5 se upar = turant repair.
      3) 15 minute ka gap tha → ab 3 minute (ek chhota getWebhookInfo call).
    Kuch bhi galat ho, bot chup-chaap theek ho jata hai — user ko pata bhi nahi.
    """
    import time as _t
    _full = (url or "").rstrip("/") + (path or "")
    if not _full:
        return
    _secret = (os.environ.get("WEBHOOK_SECRET_TOKEN") or "").strip()
    # base + path alag-alag nikaal lo (double-path wale env se bhi sahi URL banega)
    _low = _full.lower()
    if "/webhook" in _low:
        _base, _pth = _full[:_low.find("/webhook")], _full[_low.find("/webhook"):]
    else:
        _base, _pth = _full.rstrip("/"), (path or "")
    while True:
        _t.sleep(180)                                 # v81.1: 15 min → 3 min
        try:
            d = webhook_delivery_state(BOT_TOKEN, timeout=12.0, expected=_base + _pth)
            _WH_STATE["data"] = d
            _WH_STATE["at"] = time.time()
            _WH_STATE["checks"] += 1
            need = webhook_needs_repair(d, pending_limit=5)
            if not need and d.get("match") is not False:
                continue
            ok, why = webhook_repair(BOT_TOKEN, _base, _pth, _secret or None)
            _WH_STATE["fixes"] += 1
            _WH_STATE["last_fix"] = str(why)[:80]
            (log.info if ok else log.warning)(
                "🔌 webhook watchdog: %s | pending=%s | err=%s",
                why, d.get("pending"), str(d.get("err") or "-")[:60])
        except Exception as e:                        # noqa: BLE001
            log.debug("webhook watchdog loop: %s", e)


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
        # v81.1: 🔌 delivery ka state /health ke liye fresh rakho (repair ka kaam
        # watchdog thread karta hai; yahan sirf cache bharta hai — extra API call nahi)
        try:
            _webhook_delivery(timeout=2.0)
        except Exception as e:                                    # noqa: BLE001
            log.debug("webhook delivery cache skip: %s", e)


def _vault_health_html() -> str:
    """/health par data-safety + crash-shield ki live proof. Kabhi raise nahi karta."""
    out = []
    try:
        from modules.core.guard import guard_stats
        g = guard_stats()
        lb = vault.last_backup or {}
        try:
            _vk = vault.key_source()
        except Exception:                                        # noqa: BLE001
            _vk = "?"
        out.append(_hline(lambda: JW.health_line()))
        out.append("<p style='font-family:monospace'>--- FORTRESS ---</p>")
        out.append(_hline(lambda: f"db: {hesc(str(vault_db_path()))}"))
        out.append(_hline(lambda: (
            f"vault: enc=ON github={'on' if vault.gh_ready() else 'off'} "
            f"tg={'on' if vault.telegram_ready() else 'off'} "
            f"interval={vault.interval_minutes()}m "
            f"| last_backup={hesc(str(lb.get('at') or 'abhi nahi'))} "
            f"| backups={vault.stats.get('backups', 0)} "
            f"failures={vault.stats.get('failures', 0)} key={_vk}")))
        out.append(_hline(lambda: (
            f"crash-shield: caught={g.get('handled', 0)} "
            f"(handler {g.get('handler', 0)} / task {g.get('task', 0)} / "
            f"thread {g.get('thread', 0)}) | fatal={g.get('fatal', 0)}")))
        out.append(_hline(lambda: (
            f"memory: {_mem_mb():.0f} MB (peak {g.get('mem_peak_mb', 0):.0f} MB) "
            f"| gc_runs={g.get('gc_runs', 0)} | loop_lag={g.get('heart_lag', 0)}s "
            f"| trim={g.get('trim_runs', 0)} | restart_at="
            f"{g.get('restart_at_mb', 0):.0f}MB restarts={g.get('restarts', 0)}")))
        out.append(_hline(lambda: _ug.health_line()))
        out.append(_hline(lambda: (
            f"janitor: {hesc(str((_janitor_stats() or {}).get('runs', 0)))} runs "
            f"| caches: {(_bounded_report() or {}).get('total_entries', 0)} entries")))
        if g.get("last_why"):
            out.append(_hline(lambda: f"last caught: {hesc(str(g['last_why'])[:140])}"))
    except Exception as e:                                       # noqa: BLE001
        out.append("<p style='font-family:monospace'>"
                   f"vault status n/a ({type(e).__name__})</p>")
    return "".join(out)


def _hline(fn) -> str:
    """/health ki ek line — isme error aaye to sirf WAHI line 'n/a' hoti hai.

    ⚠️ v108 FIX (ye asli production bug tha): pehle health_html() ki koi ek
    line exception de deti thi to POORA page khaali chala jaata tha. Render
    ko 200 to milta tha par body khaali — isliye "zinda magar atka" app ko
    Render dobara nahi uthata tha (render.yaml me v77 ka ye note likha tha).
    Ab har line alag-alag guard me hai: page kabhi khaali nahi aayega.
    """
    try:
        return f"<p style='font-family:monospace'>{fn()}</p>"
    except Exception as e:                                       # noqa: BLE001
        return (f"<p style='font-family:monospace'>"
                f"(ye line nahi ban payi: {type(e).__name__})</p>")


def health_html() -> str:
    """/health ka report — POLLING aur WEBHOOK dono me same. Kabhi raise nahi karta."""
    parts = ["<h1>Utility Duniya Bot chal raha hai - 24/7 ON. Status: 200 OK</h1>"]
    parts.append(_hline(lambda: f"version: {hesc(BOT_VERSION)}"))
    parts.append(_hline(lambda: "tools: NUMBER INFO + FAMILY INFO"))
    parts.append(_hline(lambda: (
        f"commit: {_GIT_COMMIT or 'unknown'} | branch: {_GIT_BRANCH or 'unknown'}"
        f" | mode: {'WEBHOOK' if WEBHOOK_URL else 'POLLING'}"
        f" | up: {int(time.time() - _START_TS) // 60}m")))
    parts.append(_hline(lambda: f"ram: {_mem_mb():.0f} MB / 512 MB"))
    parts.append(_hline(lambda: (
        f"keepalive pinger: last {_KEEPALIVE_STATE.get('last_run')}"
        f" | ok={_KEEPALIVE_STATE.get('last_ok')}"
        f" | runs={_KEEPALIVE_STATE.get('runs')}")))
    parts.append(_hline(lambda: (
        f"self-heal: crashes={_CRASH_STATE['count']}"
        + (" | last=" + _CRASH_STATE["last"] if _CRASH_STATE["last"]
           else " (koi crash nahi)"))))
    try:
        parts.append(_vault_health_html())
    except Exception:                                            # noqa: BLE001
        pass
    parts.append(_hline(lambda: f"bot: {_last_update_line()}"))
    parts.append(_hline(lambda: (
        f"webhook: mode_env={_WEBHOOK_DIAG['mode_env']}"
        f" | url_env={_WEBHOOK_DIAG['url_env']}"
        f" | render_url={_WEBHOOK_DIAG['ext_env']}"
        f" | decision={_WEBHOOK_DIAG['decision']} | why: {_WEBHOOK_DIAG['why']}")))
    if WEBHOOK_URL:
        parts.append(_hline(_webhook_delivery_line))
    try:
        parts.append(_leak_hunt_line())
    except Exception:                                            # noqa: BLE001
        pass
    parts.append(_hline(lambda: f"peers: {', '.join(_KEEPALIVE_PEERS)}"))
    return "".join(p for p in parts if p)


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
#  MAIN
# =====================================================================
def main():
    # ---- 🛡️ CRASH SHIELD sabse pehle ----
    try:
        install_global_guard()
    except Exception as _e:                                      # noqa: BLE001
        log.warning("guard install skip: %s", str(_e)[:100])
    try:
        start_memory_watchdog()      # Render free 512MB — OOM kill se bachao
    except Exception as _e:                                      # noqa: BLE001
        log.warning("memory watchdog skip: %s", str(_e)[:100])
    try:
        from modules.core.guard import register_idle_check as _ric
        _ric(_bot_idle)
    except Exception:                                            # noqa: BLE001
        pass
    _memtrace_boot()
    try:
        start_hang_watchdog()
    except Exception as _e:                                      # noqa: BLE001
        log.warning("hang watchdog skip: %s", str(_e)[:100])
    try:
        start_janitor()
    except Exception as _e:                                      # noqa: BLE001
        log.warning("janitor skip: %s", str(_e)[:100])

    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN missing (Render → Environment me daalo)")
        return

    # ---------- MODE DECIDE (crash-proof) ----------
    global WEBHOOK_URL
    _WEBHOOK_DIAG["mode_env"] = str(os.environ.get("WEBHOOK_MODE") or "(not set)")
    _wu_raw = str(os.environ.get("WEBHOOK_URL") or "").strip()
    _WEBHOOK_DIAG["url_env"] = ("not set" if not _wu_raw else "set ✅")
    _WEBHOOK_DIAG["ext_env"] = "set" if os.environ.get("RENDER_EXTERNAL_URL") else "not set"
    if os.environ.get("UDB_FORCE_POLLING") == "1":
        WEBHOOK_URL = ""
    _wh_ok, _wh_why = (False, "polling mode (WEBHOOK_MODE=off ya koi URL nahi)")
    if WEBHOOK_URL:
        _wh_ok, _wh_why = webhook_url_usable(WEBHOOK_URL)
        if not _wh_ok:
            log.warning("WEBHOOK chalu nahi ho sakta (%s) — ab POLLING par chalega", _wh_why)
            WEBHOOK_URL = ""
        else:
            _secret = (os.environ.get("WEBHOOK_SECRET") or BOT_TOKEN.split(":")[-1]).strip("/")
            _pf_ok, _pf_why = webhook_preflight(WEBHOOK_URL, f"/webhook/{_secret}", BOT_TOKEN,
                                                os.environ.get("WEBHOOK_SECRET_TOKEN") or None)
            if _pf_ok:
                _WEBHOOK_DIAG.update({"decision": "WEBHOOK", "why": "Telegram ne URL maan liya ✅"})
                log.info("WEBHOOK MODE confirm — koi Conflict nahi hoga")
            else:
                _WEBHOOK_DIAG.update({"decision": "POLLING (preflight fail)", "why": _pf_why})
                log.warning("WEBHOOK preflight fail (%s) — POLLING par chalega", _pf_why)
                WEBHOOK_URL = ""
    if not WEBHOOK_URL:
        log.warning("MODE = POLLING (safe default) | %s", _wh_why)
        if _WEBHOOK_DIAG["decision"].startswith("abhi"):
            _WEBHOOK_DIAG.update({"decision": "POLLING (safe)", "why": _wh_why})

    # Keepalive server SIRF polling mode me (webhook mode me PTB wahi port lega)
    if not WEBHOOK_URL:
        threading.Thread(target=_keepalive, daemon=True).start()

    if os.environ.get("KEEPALIVE_ENABLED", "1") != "0" and _KEEPALIVE_PEERS:
        threading.Thread(target=_keepalive_pinger, daemon=True).start()
        log.info("Keepalive pinger ON → %s (har %s min)",
                 ", ".join(_KEEPALIVE_PEERS), _KEEPALIVE_MINUTES)

    _ug_proc = None
    try:
        _ug_proc = _ug.build_processor()
    except Exception as _uge:                                    # noqa: BLE001
        log.warning("update gate build skip: %s", str(_uge)[:120])
    _app_builder = (Application.builder().token(BOT_TOKEN).post_init(_post_init)
                    .connect_timeout(30.0).read_timeout(60.0).write_timeout(120.0)
                    .pool_timeout(60.0).connection_pool_size(32)
                    .http_version("1.1").get_updates_connection_pool_size(16))
    if _ug_proc is not None:
        _app_builder = _app_builder.concurrent_updates(_ug_proc)
    app = _app_builder.build()

    # ---------------- Commands ----------------
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler(["menu", "tools"], cmd_menu))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler(["refresh", "newmenu"], cmd_refresh))
    app.add_handler(CommandHandler(["version", "ver", "v"], cmd_version))
    app.add_handler(CommandHandler(["numapi", "numinfoapi", "numberapi"], cmd_numapi))
    app.add_handler(CommandHandler(["famapi", "familyapi"], cmd_famapi))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler(["sys", "system", "health"], cmd_sys))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler(["vault", "premiumvault", "datavault"], cmd_vault))
    app.add_handler(CommandHandler(["backup", "save"], cmd_backup))
    app.add_handler(CommandHandler(["restore", "recover"], cmd_restore))

    # ---------------- Updates ----------------
    app.add_handler(TypeHandler(Update, _track_update), group=-10)
    app.add_handler(CallbackQueryHandler(_on_cb_pro))

    _dm_or_group = filters.ChatType.PRIVATE | filters.ChatType.GROUPS
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & _dm_or_group,
                                   _on_text_pro))
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.AUDIO
         | filters.VOICE | filters.ANIMATION) & _dm_or_group, on_other))

    _armed = arm_all_handlers(app)
    log.info("🛡️ CRASH SHIELD: %s handlers lapete gaye", _armed)
    app.add_error_handler(on_error)

    print(f"🚀 Starting Utility Duniya Bot ({BOT_VERSION.split('|')[0].strip()})")
    print(f"   commit {_GIT_COMMIT} | pid {os.getpid()} | {socket.gethostname()}")
    try:
        _startup_selfcheck()
    except Exception as _e:                                      # noqa: BLE001
        log.warning("self-check skip (crash nahi): %s", str(_e)[:120])

    # ---------------- WEBHOOK ----------------
    if WEBHOOK_URL:
        from modules.render_health import install_webhook_health_routes
        install_webhook_health_routes(health_html)
        port = int(os.environ.get("PORT", "10000"))
        secret = (os.environ.get("WEBHOOK_SECRET") or BOT_TOKEN.split(":")[-1]).strip("/")
        path = f"/webhook/{secret}"
        full_url = WEBHOOK_URL.rstrip("/") + path
        log.info("WEBHOOK MODE ON — polling OFF | instance=%s pid=%s",
                 socket.gethostname(), os.getpid())
        try:
            threading.Thread(target=_webhook_watchdog,
                             args=(WEBHOOK_URL, path), daemon=True).start()
        except Exception:                                        # noqa: BLE001
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
        except Exception as e:                                   # noqa: BLE001
            log.error("Webhook fail (%s: %s) — POLLING par switch",
                      type(e).__name__, str(e)[:200])
            if os.environ.get("UDB_FORCE_POLLING") != "1":
                _hard_restart(f"webhook fail ({type(e).__name__}) → polling", delay=3.0,
                              extra_env={"UDB_FORCE_POLLING": "1"})
            try:
                app.bot.delete_webhook(drop_pending_updates=True)
            except Exception:                                    # noqa: BLE001
                pass

    # ---------------- POLLING ----------------
    # v108 FIX: pehle yahan `_Bot(...).delete_webhook(...)` BINA await ke tha —
    # PTB v21+ me ye ek coroutine hai, isliye wo kabhi CHALTA HI NAHI tha
    # (logs me sirf "coroutine was never awaited" warning aati thi). Matlab
    # purani webhook lagi reh jaati thi aur Telegram getUpdates par
    # "Conflict: can't use getUpdates while webhook is active" de deta tha.
    # Ab sach me delete hoti hai.
    try:
        from telegram import Bot as _Bot

        async def _drop_wh():
            _b = _Bot(BOT_TOKEN)
            async with _b:
                await _b.delete_webhook(drop_pending_updates=True)

        asyncio.run(_drop_wh())
        log.info("Purani webhook (agar thi) hata di — getUpdates ab saaf chalega")
    except Exception as _e:                                      # noqa: BLE001
        log.debug("webhook cleanup skip: %s", str(_e)[:80])

    log.warning("STARTING POLLING | instance=%s pid=%s | only ONE instance must run",
                socket.gethostname(), os.getpid())
    _try = 0
    _bad_streak = [0]
    while True:
        _try += 1
        try:
            app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES,
                            close_loop=False)
            log.warning("Polling ruk gayi (normal return) — dobara shuru kar raha hoon")
            time.sleep(3)
            continue
        except Exception as e:                                   # noqa: BLE001
            _msg = str(e).lower()
            log.error("Polling band hui (%s: %s)", type(e).__name__, str(e)[:200])
            if "conflict" not in _msg:
                _bad_streak[0] += 1
                if _bad_streak[0] >= 3:
                    _hard_restart(f"polling fail x3 ({type(e).__name__})", delay=5.0)
                    _bad_streak[0] = 0
            if "conflict" in _msg:
                if _force_webhook_after_conflict(app):
                    return
                wait = min(300, 15 * _try)
                log.warning("Do instance ek saath chal rahe hain — %ss baad dobara "
                            "koshish (try #%s). Bot chalta rahega.", wait, _try)
                time.sleep(wait)
                continue
            wait = min(60, 5 * _try)
            log.warning("%ss baad dobara koshish (try #%s) — bot crash NAHI hoga", wait, _try)
            time.sleep(wait)
            continue


if __name__ == "__main__":
    if "--check" in sys.argv:
        _startup_selfcheck()
        sys.exit(0)
    _supervise()
