#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility Duniya Super Bot (v30 Ultra Edition)
- 25+ High-Power Utilities & Automation Tools
- Sarkari Seva & Student Exam Hub
- Cyber Cafe AI Document Studio (Name/DOP Photo, Signature Cleaner, Printable Sheet, PDF Compress)
- Terabox & Multi-Cloud Direct Stream/Downloader
- Channel Cloner & Auto-Forwarder with Custom Branding
- AI Voice Clone & Celebrity Voiceover Studio
- Universal Social Media & Viral Reels Downloader
- Smart OSINT & Vehicle/Phone/IFSC/Pincode Investigation Hub
- VIP Subscription & UPI Dynamic QR Payment System
"""

import asyncio
import io
import json
import logging
import os
import random
import re
import string
import tempfile
import time
import threading
from datetime import date, datetime, timedelta
from html import escape as hesc
from urllib.parse import quote, unquote, urlparse

from dotenv import load_dotenv

load_dotenv()

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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

# Import internal modules
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
from modules.channel_cloner import forward_cloned_message, get_cloner_menu_kb
from modules.voice_studio import VOICE_PRESETS, generate_voice
from modules.media_downloader import extract_media_info, is_supported_media_url
from modules.osint_tools import (
    check_username_platforms,
    lookup_ifsc,
    lookup_ip_domain,
    lookup_phone_info,
    lookup_pincode,
    lookup_vehicle_rto,
)
from modules.general_tools import (
    app_finder,
    calc_age,
    calc_emi,
    emi_schedule,
    gen_password,
    make_qr_bytes,
    name_passwords,
    pages_to_pdf,
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
FREE_LIMIT = int(os.getenv("FREE_LIMIT", "20") or 20)
REFER_NEED = int(os.getenv("REFER_NEED", "5") or 5)
HTML = "HTML"
BAN_MSG = "🚫 Aapka account banned hai. Kripya admin se contact karein."
BOT_VERSION = "v30 Ultra"
START_TIME = datetime.now()

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("utility-super-bot")

# Main Grid Buttons
KB_BTNS = [
    ["🌐 Virtual Numbers", "⚡ Terabox & Cloud Direct"],
    ["🔄 Channel Cloner / Forwarder", "🎙️ AI Voice Clone & TTS"],
    ["🎬 Viral Reels & Video Downloader", "🏛️ Sarkari Seva Portals"],
    ["🎓 Student Exam & Result Hub", "📸 Photo (Name/DOP Stamp)"],
    ["✍️ Signature Cleaner (10-20KB)", "🖨️ Printable 8-in-1 Sheet"],
    ["📄 Document PDF Compressor", "🕵️ OSINT & Vehicle/Phone Info"],
    ["📷 QR Code", "🖼️ Image→PDF"],
    ["🔗 URL Short & Bypass", "🔎 Web Search"],
    ["📦 App Finder", "🖼️ Site Screenshot"],
    ["🧮 EMI & Interest Calc", "🎂 Age Calculator"],
    ["💰 UPI QR Generator", "🆔 ID & Username Finder"],
    ["🔐 Password Generator", "🏦 IFSC & Pincode Info"],
    ["💎 VIP Premium", "🎁 Refer & Earn"],
    ["👤 My Account"],
]


def main_keyboard(admin: bool = False):
    rows = [row[:] for row in KB_BTNS]
    if admin:
        rows.append(["🛠️ Admin Panel"])
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t) for t in row] for row in rows],
        resize_keyboard=True,
        input_field_placeholder="Grid dabao ya tool select karein 👇",
    )


def kb_for(uid: int):
    return main_keyboard(admin=(uid == ADMIN_ID and ADMIN_ID != 0))


# Mode mapping
BTN_MODE = {
    "📷 QR Code": "qr",
    "🖼️ Image→PDF": "pdf",
    "🔗 URL Short & Bypass": "short",
    "🧮 EMI & Interest Calc": "emi",
    "🎂 Age Calculator": "age",
    "💰 UPI QR Generator": "upi",
    "🆔 ID & Username Finder": "idfind",
    "🏦 IFSC & Pincode Info": "ifsc_menu",
    "📸 Photo (Name/DOP Stamp)": "pp_stamp",
    "✍️ Signature Cleaner (10-20KB)": "sig_clean",
    "🖨️ Printable 8-in-1 Sheet": "print_sheet",
    "📄 Document PDF Compressor": "doc_compress",
    "⚡ Terabox & Cloud Direct": "cloud_dl",
    "🎬 Viral Reels & Video Downloader": "media_dl",
    "🎙️ AI Voice Clone & TTS": "voice_studio",
    "🔄 Channel Cloner / Forwarder": "channel_cloner",
    "🕵️ OSINT & Vehicle/Phone Info": "osint_menu",
    "🔎 Web Search": "search",
    "📦 App Finder": "appfind",
    "🖼️ Site Screenshot": "shot",
    "🔐 Password Generator": "pwd",
}

PROMPTS = {
    "qr": "📷 <b>QR Code Generator (HD)</b>\n\nKoi bhi TEXT, UPI ID ya LINK bhejo:",
    "pdf": "🖼️ <b>Image → PDF Multi-Page Converter</b>\n\n📸 Ek-ek karke <b>10 photos tak</b> bhejo, phir <b>✅ Make PDF</b> dabao:",
    "short": "🔗 <b>URL Shortener & Bypass</b>\n\nLamba URL link bhejo (is.gd & tinyurl short links turant milenge):",
    "emi": "🧮 <b>EMI Calculator</b>\n\nLoan amount (₹) bhejo:\n(jaise: <code>100000</code>)",
    "age": "🎂 <b>Age Calculator</b>\n\nApni birth date bhejo (DD-MM-YYYY):\n(jaise: <code>15-08-2005</code>)",
    "upi": "💰 <b>UPI QR Generator</b>\n\nApni UPI ID bhejo:\n(jaise: <code>name@okhdfc</code>)",
    "idfind": "🆔 <b>ID & Username Finder</b>\n\n1️⃣ Kisi ka koi <b>message FORWARD</b> karein\n2️⃣ <b>@username</b> bhejo\n3️⃣ <code>me</code> likho apni ID ke liye",
    "pp_stamp": "📸 <b>Govt Exam Photo Studio (Name + Date of Photo Stamp)</b>\n\nApni passport photo bhejo:",
    "sig_clean": "✍️ <b>Signature Cleaner & Ink Enhancer (10-20KB)</b>\n\nSignature ki photo bhejo (background white karke 10-20KB banayega):",
    "print_sheet": "🖨️ <b>Printable 8-in-1 Passport Sheet</b>\n\nSingle photo bhejo (4x6 inch printable sheet ready karega):",
    "doc_compress": "📄 <b>Document / Marksheet PDF Compressor</b>\n\nMarksheet ya certificate ki photo bhejo:",
    "cloud_dl": "⚡ <b>Terabox & Multi-Cloud Direct Downloader</b>\n\nTerabox, Mediafire ya Google Drive ka link bhejo (Ad-Free fast download link milega):",
    "media_dl": "🎬 <b>Viral Reels & Video Downloader</b>\n\nInstagram Reels, YouTube Shorts, X, ya Pinterest ka link bhejo:",
    "search": "🔎 <b>Web Search</b>\n\nKuch bhi search karein (Top 5 fast links milenge):",
    "appfind": "📦 <b>App Finder</b>\n\nApp ka naam bhejo (Official Play Store & APK download link):",
    "shot": "🖼️ <b>Website Screenshot (Full HD)</b>\n\nWebsite ka URL bhejo (e.g. <code>github.com</code>):",
}

WELCOME_TEXT = (
    "⚡ <b>UTILITY DUNIYA SUPER-BOT</b> ⚡\n"
    "<blockquote>25+ Ultra-Powerful Tools • Lightning Fast • All-in-One Engine 🚀</blockquote>\n\n"
    "🔥 <b>Trending Power Tools:</b>\n"
    "• ⚡ <b>Terabox Fast Downloader:</b> Ad-free direct bypass\n"
    "• 🔄 <b>Channel Cloner:</b> Auto-forward with custom branding\n"
    "• 🎙️ <b>AI Voice Clone:</b> Modi, Alpha, Anime text-to-speech\n"
    "• 📸 <b>Cyber Cafe Studio:</b> Name/Date stamp, Signature clean\n"
    "• 🏛️ <b>Sarkari Seva Portals:</b> Aadhaar, PAN, Ration, Ayushman, DL\n"
    "• 🎓 <b>Student Exam Hub:</b> SSC, Railway, Admit cards, Results\n"
    "• 🕵️ <b>Smart OSINT:</b> Vehicle RTO, Phone Operator, IFSC, Pin\n\n"
    "⌨️ <b>Neeche Grid Menu dabakar tool select karein 👇</b>"
)


# Force join check
async def ensure_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not FORCE_CHANNEL:
        return True
    uid = update.effective_user.id
    if uid == ADMIN_ID and ADMIN_ID != 0:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_CHANNEL, user_id=uid)
        if member.status in ("creator", "administrator", "member"):
            return True
    except Exception:
        return True

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=FORCE_CHANNEL_LINK or f"https://t.me/{FORCE_CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton("✅ I Have Joined", callback_data="check_joined")],
    ])
    msg_target = update.callback_query.message if update.callback_query else update.message
    if msg_target:
        await msg_target.reply_text(
            f"⚠️ <b>Bot use karne ke liye hamara channel join karein:</b>\n\nChannel: {FORCE_CHANNEL}",
            reply_markup=kb,
            parse_mode=HTML,
        )
    return False


# ---------------- COMMANDS ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id, user.first_name or "")
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

    if not await ensure_joined(update, context):
        return

    # Welcome banner or text
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
    if not await ensure_joined(update, context):
        return
    await update.message.reply_text(WELCOME_TEXT, reply_markup=kb_for(update.effective_user.id), parse_mode=HTML)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Action cancelled! Main menu ready hai 👇", reply_markup=kb_for(update.effective_user.id))


async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    vip_status = "👑 ACTIVE" if is_premium(u) else "Free Tier (Daily 20 uses)"
    expiry = premium_expiry(u)
    text = (
        f"👤 <b>MY ACCOUNT DETAILS</b>\n\n"
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
        f"🎁 <b>REFER & EARN FREE VIP</b> 🎁\n\n"
        f"Apne dosto ko bot share karein aur **30 din ka VIP Access bilkul FREE** payein!\n\n"
        f"📊 <b>Aapke Referrals:</b> {u.get('referrals', 0)}\n"
        f"🎯 <b>Target:</b> Har {REFER_NEED} referrals par 30 Days VIP Free\n\n"
        f"🔗 <b>Aapka Personal Invite Link:</b>\n<code>{ref_link}</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Share on Telegram", url=f"https://t.me/share/url?url={quote(ref_link)}&text={quote('🔥 Check out this Super Utility Bot!')}")],
    ])
    await update.message.reply_text(text, reply_markup=kb, parse_mode=HTML)


async def cmd_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 <b>VIP PREMIUM MEMBERSHIP</b> 💎\n"
        "<blockquote>Unlock Unlimited High-Speed Cloud Downloads, Cloner, Photo Studio & AI Voices!</blockquote>\n\n"
        "⚡ <b>VIP Features:</b>\n"
        "• ♾️ Unlimited Daily Usage (No 20-use limit)\n"
        "• 🚀 Ultra High-Speed Cloud Video Stream & Direct Downloads\n"
        "• 🔄 Channel Cloner & Auto-Forwarder\n"
        "• 🎙️ Full AI Voiceover & TTS Studio\n"
        "• 📸 Cyber Cafe Photo & Doc Studio HD\n\n"
        "👉 Plan select karein aur instant QR code se pay karein:"
    )
    await update.message.reply_text(text, reply_markup=get_premium_plans_kb(), parse_mode=HTML)


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    st = stats()
    text = (
        "🛠️ <b>ADMIN DASHBOARD</b> 🛠️\n\n"
        f"• 👥 <b>Total Users:</b> {st['total_users']}\n"
        f"• 🟢 <b>Active Today:</b> {st['active_today']}\n"
        f"• ⚡ <b>Uses Today:</b> {st['uses_today']}\n"
        f"• 💎 <b>VIP Subscribers:</b> {st['vip_users']}\n\n"
        "Commands:\n"
        "/broadcast [text] - Send message to all users\n"
        "/grant [userid] [days] - Give VIP access\n"
        "/ban [userid] - Ban user\n"
        "/unban [userid] - Unban user"
    )
    await update.message.reply_text(text, parse_mode=HTML)


# ---------------- CALLBACK QUERY HANDLER ----------------
async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id

    if data == "check_joined":
        if await ensure_joined(update, context):
            await q.message.reply_text("✅ Dhanyawad! Saare tools unlocked hain 👇", reply_markup=kb_for(uid))
        return

    if data == "back_home":
        await q.message.edit_text(WELCOME_TEXT, reply_markup=None, parse_mode=HTML)
        return

    # Sarkari & Student Handlers
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
            f"💎 <b>{plan_name}</b>\n\n"
            f"💰 <b>Amount:</b> ₹{amt}\n"
            f"🏦 <b>UPI ID:</b> <code>{UPI_ID}</code>\n\n"
            f"👉 <b>Payment Steps:</b>\n"
            f"1️⃣ Neeche QR Code scan karein (Google Pay / PhonePe / Paytm / CRED)\n"
            f"2️⃣ ₹{amt} pay karein\n"
            f"3️⃣ Payment ka <b>Screenshot ya UTR (Transaction ID)</b> yahan bot me bhejein.\n\n"
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
                f"🎉 <b>Badhai ho!</b> Aapka payment verify ho gaya hai aur {days} din ka VIP Access activate kar diya gaya hai! 💎\n\nAb aap unlimited high-speed tools enjoy kar sakte hain!",
                parse_mode=HTML,
            )
        except Exception:
            pass
        return

    if data.startswith("adm_rej_") and uid == ADMIN_ID:
        target_uid = int(data.split("_")[2])
        await q.message.edit_caption(caption=f"❌ <b>Rejected!</b> Payment for user <code>{target_uid}</code> was rejected.", parse_mode=HTML)
        try:
            await context.bot.send_message(target_uid, "❌ Aapka payment verification approve nahi hua. Kripya sahi screenshot/UTR bhejein ya admin se sampark karein.")
        except Exception:
            pass
        return

    # Cloner Callbacks
    if data == "cloner_set_target":
        context.user_data["mode"] = "cloner_target"
        await q.message.reply_text("🎯 <b>Target Channel ka Username ya ID bhejo:</b>\n(jaise: <code>@MyChannelName</code> ya <code>-100123456789</code>)\n\n<i>Note: Bot ko target channel me Admin banayein (Post Messages permission ke saath).</i>", parse_mode=HTML)
        return

    if data == "cloner_set_caption":
        context.user_data["mode"] = "cloner_caption"
        await q.message.reply_text("✍️ <b>Custom Caption / Watermark text bhejo:</b>\n(jaise: <code>Join @MyChannel for daily updates!</code>)", parse_mode=HTML)
        return

    if data == "cloner_clear_caption":
        save_cloner_config(uid, caption="")
        await q.message.reply_text("🗑️ Custom caption cleared! Ab original caption jayegi.", reply_markup=get_cloner_menu_kb(uid), parse_mode=HTML)
        return

    if data == "cloner_start_mode":
        context.user_data["mode"] = "cloning_active"
        await q.message.reply_text("🚀 <b>Cloner Mode Active!</b>\n\nAb aap kisi bhi channel se post forward karein ya videos/PDFs bhein — bot automatically custom caption ke saath target channel me post karega!\n\n/cancel dabakar kisi bhi waqt rok sakte hain.", parse_mode=HTML)
        return

    if data == "cloner_reset":
        save_cloner_config(uid, target="", caption="", watermark="")
        context.user_data.pop("mode", None)
        await q.message.reply_text("⏹️ Cloner settings reset ho gayi hain.", reply_markup=kb_for(uid), parse_mode=HTML)
        return

    # Voice Studio Presets
    if data.startswith("voice_set_"):
        preset_key = data.replace("voice_set_", "")
        context.user_data["voice_preset"] = preset_key
        p_name = VOICE_PRESETS.get(preset_key, {}).get("name", "Default")
        context.user_data["mode"] = "voice_text"
        await q.message.reply_text(f"🎙️ Selected Voice: <b>{p_name}</b>\n\nAb woh <b>TEXT</b> bhejo jiska voiceover banana hai (Hindi/English):", parse_mode=HTML)
        return


# ---------------- TEXT HANDLER ----------------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    save_username(uid, user.username or "")
    if is_banned(uid):
        await update.message.reply_text(BAN_MSG)
        return

    text = (update.message.text or "").strip()

    # Grid Button Clicks
    if text in BTN_MODE:
        if not await ensure_joined(update, context):
            return
        mode = BTN_MODE[text]
        context.user_data["mode"] = mode

        if mode == "pdf":
            context.user_data["pdf_pages"] = []
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Make PDF Now", callback_data="make_pdf_now")]])
            await update.message.reply_text(PROMPTS[mode], reply_markup=kb, parse_mode=HTML)
            return

        if mode == "voice_studio":
            buttons = []
            for k, v in VOICE_PRESETS.items():
                buttons.append([InlineKeyboardButton(v["name"], callback_data=f"voice_set_{k}")])
            await update.message.reply_text("🎙️ <b>AI VOICE CLONE & TTS STUDIO</b>\n\nVoice model select karein 👇", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=HTML)
            return

        if mode == "channel_cloner":
            await update.message.reply_text("🔄 <b>CHANNEL CLONER & AUTO-FORWARDER</b>\n\nSettings configure karein 👇", reply_markup=get_cloner_menu_kb(uid), parse_mode=HTML)
            return

        if mode == "osint_menu":
            text_osint = (
                "🕵️ <b>SMART OSINT & INVESTIGATION HUB</b>\n\n"
                "• 🚗 <b>RTO Vehicle:</b> <code>/rto DL01AB1234</code>\n"
                "• 📱 <b>Phone Info:</b> <code>/phone 9876543210</code>\n"
                "• 🏦 <b>IFSC Lookup:</b> <code>/ifsc SBIN0000001</code>\n"
                "• 📮 <b>Pincode:</b> <code>/pin 823001</code>\n"
                "• 🌐 <b>IP/Domain:</b> <code>/whois google.com</code>\n"
                "• 👤 <b>Username Check:</b> <code>/user rahul123</code>"
            )
            await update.message.reply_text(text_osint, parse_mode=HTML)
            return

        if mode == "ifsc_menu":
            await update.message.reply_text("🏦 <b>IFSC ya Pincode bhejo:</b>\n(jaise: <code>SBIN0000001</code> ya <code>823001</code>)", parse_mode=HTML)
            context.user_data["mode"] = "ifsc_pin"
            return

        if mode == "pwd":
            p1 = gen_password(16)
            p2 = gen_password(12)
            await update.message.reply_text(f"🔐 <b>Strong Passwords Generated:</b>\n\n1️⃣ <code>{p1}</code>\n2️⃣ <code>{p2}</code>", parse_mode=HTML)
            return

        if mode in PROMPTS:
            await update.message.reply_text(PROMPTS[mode] + "\n\n<i>/cancel kabhi bhi dabayein.</i>", parse_mode=HTML)
            return

    if text == "🏛️ Sarkari Seva Portals":
        await update.message.reply_text(SARKARI_CITIZEN_TEXT, reply_markup=get_sarkari_citizen_kb(), parse_mode=HTML)
        return

    if text == "🎓 Student Exam & Result Hub":
        await update.message.reply_text(STUDENT_EXAM_TEXT, reply_markup=get_student_exam_kb(), parse_mode=HTML)
        return

    if text == "💎 VIP Premium":
        await cmd_premium(update, context)
        return

    if text == "🎁 Refer & Earn":
        await cmd_refer(update, context)
        return

    if text == "👤 My Account":
        await cmd_account(update, context)
        return

    if text == "🛠️ Admin Panel":
        await cmd_admin(update, context)
        return

    # Check Active Mode
    mode = context.user_data.get("mode")

    # Cloner Forwarding Active
    if mode == "cloning_active":
        ok, msg_res = await forward_cloned_message(context.bot, update.message, uid)
        await update.message.reply_text(msg_res, parse_mode=HTML)
        return

    if mode == "cloner_target":
        save_cloner_config(uid, target=text)
        context.user_data.pop("mode", None)
        await update.message.reply_text(f"✅ Target channel set to: <b>{text}</b>", reply_markup=get_cloner_menu_kb(uid), parse_mode=HTML)
        return

    if mode == "cloner_caption":
        save_cloner_config(uid, caption=text)
        context.user_data.pop("mode", None)
        await update.message.reply_text("✅ Custom caption saved!", reply_markup=get_cloner_menu_kb(uid), parse_mode=HTML)
        return

    # Payment Proof Submission
    if mode and mode.startswith("pay_proof_"):
        plan_key = mode.replace("pay_proof_", "")
        if ADMIN_ID != 0:
            kb_adm = get_payment_admin_kb(uid, plan_key)
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 <b>New VIP Payment Proof!</b>\n\n• <b>User ID:</b> <code>{uid}</code>\n• <b>User:</b> @{update.effective_user.username or 'NoUser'}\n• <b>Plan:</b> {plan_key}\n• <b>Proof/UTR:</b> {hesc(text)}",
                reply_markup=kb_adm,
                parse_mode=HTML,
            )
        await update.message.reply_text("✅ Payment proof submit ho gaya! Admin verify karke 5 minute me VIP activate kar dega.")
        context.user_data.pop("mode", None)
        return

    # Tool Execution Modes
    if mode == "cloud_dl":
        st = await update.message.reply_text("⚡ Processing cloud download link...")
        res = resolve_cloud_url(text)
        if res.get("ok"):
            cap = (
                f"⚡ <b>{res.get('provider', 'Cloud Direct')}</b>\n\n"
                f"📁 <b>Title:</b> {hesc(res.get('title', 'File'))}\n"
                f"📊 <b>Size:</b> {res.get('size', 'HD')}\n\n"
                f"🔗 <b>High-Speed Link:</b>\n{res.get('direct_url')}"
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Download Fast / Stream", url=res.get("direct_url"))],
            ])
            await st.edit_text(cap, reply_markup=kb, parse_mode=HTML)
        else:
            await st.edit_text(f"❌ {res.get('error', 'Could not resolve link.')}")
        add_use(uid)
        return

    if mode == "media_dl":
        st = await update.message.reply_text("🎬 Extracting media...")
        res = extract_media_info(text)
        if res.get("ok"):
            cap = (
                f"🎬 <b>{hesc(res.get('title', 'Video'))}</b>\n\n"
                f"📱 <b>Source:</b> {res.get('source')}\n"
                f"🔗 <b>Direct Link:</b>\n{res.get('direct_url')}"
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Download Video HD", url=res.get("direct_url"))],
            ])
            await st.edit_text(cap, reply_markup=kb, parse_mode=HTML)
        else:
            await st.edit_text(f"❌ {res.get('error', 'Could not fetch video.')}")
        add_use(uid)
        return

    if mode == "voice_text":
        st = await update.message.reply_text("🎙️ Generating AI Voiceover...")
        preset = context.user_data.get("voice_preset", "modi")
        try:
            mp3_path = await generate_voice(text, preset)
            with open(mp3_path, "rb") as f:
                await update.message.reply_voice(voice=f, caption="🎙️ Generated by Utility Duniya AI Studio")
            await st.delete()
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except Exception as e:
            await st.edit_text(f"❌ Voice generation error: {str(e)}")
        add_use(uid)
        return

    if mode == "qr":
        buf = make_qr_bytes(text)
        await update.message.reply_photo(photo=buf, caption="📷 <b>HD QR Code Generated!</b>", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "short":
        s1 = shorten_isgd(text) or "Failed"
        s2 = shorten_tiny(text) or "Failed"
        await update.message.reply_text(f"🔗 <b>Shortened Links:</b>\n\n1️⃣ <code>{s1}</code>\n2️⃣ <code>{s2}</code>", parse_mode=HTML)
        add_use(uid)
        return

    if mode == "emi":
        try:
            p = float(text.replace(",", ""))
            emi, rows = emi_schedule(p, 10.5, 12)
            await update.message.reply_text(f"🧮 <b>Loan EMI (₹{int(p):,} @ 10.5% for 1 Year):</b>\n\nMonthly EMI: <b>₹{int(emi):,}</b>", parse_mode=HTML)
        except Exception:
            await update.message.reply_text("⚠️ Kripya valid number bhejein (jaise: 100000)")
        return

    if mode == "age":
        try:
            parts = [int(x) for x in re.split(r"[-/.]", text)]
            d = date(parts[2], parts[1], parts[0])
            res = calc_age(d)
            if res:
                y, m, da, total_d, next_d, day_name = res
                z = zodiac(parts[0], parts[1])
                await update.message.reply_text(
                    f"🎂 <b>Age Details:</b>\n\n• <b>Age:</b> {y} Years, {m} Months, {da} Days\n• <b>Total Days:</b> {total_d:,} Days\n• <b>Next Birthday in:</b> {next_d} Days ({day_name})\n• <b>Zodiac:</b> {z}",
                    parse_mode=HTML,
                )
            else:
                await update.message.reply_text("⚠️ Future date nahi daal sakte!")
        except Exception:
            await update.message.reply_text("⚠️ Format: DD-MM-YYYY (jaise: 15-08-2005)")
        return

    if mode == "shot":
        st = await update.message.reply_text("📸 Capturing full HD screenshot...")
        buf = site_screenshot(text)
        if buf:
            await update.message.reply_photo(photo=buf, caption=f"🖼️ Screenshot: <code>{text}</code>", parse_mode=HTML)
            await st.delete()
        else:
            await st.edit_text("❌ Screenshot failed. Please check URL.")
        add_use(uid)
        return

    if mode == "search":
        q = quote(text)
        res_text = (
            f"🔎 <b>Search Results for:</b> <i>{hesc(text)}</i>\n\n"
            f"1️⃣ <a href='https://www.google.com/search?q={q}'>Google Search</a>\n"
            f"2️⃣ <a href='https://duckduckgo.com/?q={q}'>DuckDuckGo Fast</a>\n"
            f"3️⃣ <a href='https://en.wikipedia.org/wiki/Special:Search?search={q}'>Wikipedia Encyclopedia</a>"
        )
        await update.message.reply_text(res_text, parse_mode=HTML, disable_web_page_preview=False)
        add_use(uid)
        return

    if mode == "appfind":
        res = app_finder(text)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Google Play Store", url=res["play_url"])],
            [InlineKeyboardButton("📥 APKPure Direct", url=res["apkpure_url"])],
        ])
        await update.message.reply_text(f"📦 <b>App: {res['title']}</b>", reply_markup=kb, parse_mode=HTML)
        add_use(uid)
        return

    if mode == "ifsc_pin":
        clean = text.strip()
        if len(clean) == 6 and clean.isdigit():
            p_res = lookup_pincode(clean)
            if p_res.get("ok"):
                await update.message.reply_text(
                    f"📮 <b>Pincode {clean}:</b>\n• District: {p_res['district']}\n• State: {p_res['state']}\n• Offices: {p_res['post_offices']}",
                    parse_mode=HTML,
                )
            else:
                await update.message.reply_text("❌ Pincode not found.")
        else:
            i_res = lookup_ifsc(clean)
            if i_res.get("ok"):
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("📍 View on Google Maps", url=i_res["maps_link"])]])
                await update.message.reply_text(
                    f"🏦 <b>{i_res['bank']} ({i_res['ifsc']})</b>\n• Branch: {i_res['branch']}\n• Address: {i_res['address']}\n• UPI/NEFT: {i_res['upi']}",
                    reply_markup=kb,
                    parse_mode=HTML,
                )
            else:
                await update.message.reply_text("❌ IFSC code not found.")
        add_use(uid)
        return

    # Fallback to main menu
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
            caption=f"📸 <b>Official Govt Exam Photo Ready!</b>\n\n• <b>Name:</b> {name.upper()}\n• <b>DOP:</b> {dop}\n• <b>Size:</b> {sz} KB (20-50KB compliant ✅)",
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
            caption=f"✍️ <b>Signature Cleaned & Contrast Enhanced!</b>\n\n• Background: Pure White\n• Size: {sz} KB (10-20KB official limit ✅)",
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
            caption="🖨️ <b>Printable 8-in-1 Passport Sheet (4x6 inch) Ready!</b>\n\nKisi bhi photo lab me sirf ₹5-₹10 me print karwayein!",
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
            caption="📄 <b>Compressed Document PDF Ready!</b>\n\n(Under 250KB - Govt portal compliant ✅)",
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
        await q.message.reply_document(document=buf, caption=f"📄 <b>Multi-Page PDF Ready ({len(pages)} pages)!</b>", parse_mode=HTML)
        context.user_data.pop("pdf_pages", None)
        context.user_data.pop("mode", None)


# ---------------- ERROR HANDLER ----------------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Exception handling update: %s", context.error)


# ---------------- POST INIT ----------------
async def _post_init(app: Application):
    commands = [
        BotCommand("start", "Start the Super Bot"),
        BotCommand("menu", "Open Main Menu"),
        BotCommand("premium", "VIP Subscription & Plans"),
        BotCommand("refer", "Refer Friends = Free VIP"),
        BotCommand("account", "My Account & Limits"),
        BotCommand("cancel", "Cancel current action"),
    ]
    await app.bot.set_my_commands(commands)
    log.info("Commands set successfully!")


# ---------------- KEEPALIVE WEB SERVER ----------------
def _keepalive():
    """Lightweight webserver to keep hosting active on Render / Koyeb"""
    import http.server
    import socketserver

    port = int(os.environ.get("PORT", "8080"))

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Utility Duniya Super Bot is Running 24/7!</h1>")

        def log_message(self, format, *args):
            pass

    try:
        with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
            log.info("Keepalive server listening on port %s", port)
            httpd.serve_forever()
    except Exception as e:
        log.warning("Keepalive server warning: %s", e)


def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN is missing in environment variables or .env file!")
        return

    # Start keepalive in background thread
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

    # Callbacks
    app.add_handler(CallbackQueryHandler(on_pdf_cb, pattern="^make_pdf_now$"))
    app.add_handler(CallbackQueryHandler(on_cb))

    # Messages
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    app.add_error_handler(on_error)

    print("🚀 Starting Utility Duniya Super Bot...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
