# -*- coding: utf-8 -*-
"""
Channel Cloner & Auto-Forwarder ENGINE (v31 Ultra)
==================================================
2 tarah se kaam karta hai:

1) MANUAL MODE  : User posts bot ko forward karta hai -> bot branding ke saath target channel me daalta hai.
2) FULL AUTO    : Bot khud SOURCE channel ki har nayi post uthata hai -> target channel me apne caption,
                  watermark, rename tag, replace/remove words aur thumbnail ke saath post kar deta hai.
                  (Bot ko source + target dono channel me ADMIN hona chahiye.)

Extra features:
- Album / Media group (2-10 photos+videos) ek saath album banakar bhejta hai (fallback: ek-ek karke).
- FloodWait (RetryAfter) par khud wait karke dobara try karta hai.
- Caption me galat HTML ho to bina parse_mode dobara bhej deta hai (error nahi aata).
- Thumbnail fail ho jaye to bina thumbnail bhej deta hai.
"""

import asyncio
import logging
import re

from telegram import (
    Bot,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAudio,
)
from telegram.error import RetryAfter, BadRequest

from database import get_cloner_config, save_cloner_config

log = logging.getLogger(__name__)

HTML = "HTML"


# --------------------------------------------------------------------------------
# USER GUIDE (simple Hinglish — pehli baar use karne wale ke liye)
# --------------------------------------------------------------------------------
CLONER_GUIDE_TEXT = (
    "📘 <b>AUTO FORWARD KAISE KAAM KARTA HAI?</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "Dekho, samajh lo aise 👇\n\n"
    "1️⃣ <b>SOURCE</b> = jis channel se posts aayengi\n"
    "   (jaise: tumhara lecture wala channel, PDF/notes wala channel)\n\n"
    "2️⃣ <b>TARGET</b> = jis channel me posts bhejni hain\n"
    "   (jaise: apna new channel, apni website/group, apna paid channel)\n\n"
    "3️⃣ Bot <b>khud</b> source ki nayi post uthata hai → 2-5 second me target me daal deta hai\n"
    "   (Caption, tag, watermark, thumbnail — sab tumhari settings ke saath) 🎉\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "⚠️ <b>2 ZAROORI BAATEIN:</b>\n"
    "• Bot ko <b>Source</b> aur <b>Target</b> dono channel me <b>Admin</b> banana padega\n"
    "• Private channel ho? Koi dikkat nahi — us private channel me bot ko admin add karo,\n"
    "   phir us channel ki koi bhi post bot ko <b>forward</b> kar do — bot khud ID pakad lega ✅\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "📦 <b>Kya-kya bhej sakte ho:</b>\n"
    "• 🎥 Video lectures • 📄 PDF / notes • 🖼️ Photos • 🎵 Audio • 📁 Files\n"
    "• 🖼️ Album (2-10 photos/videos ek saath) bhi album hi ban kar jayenge\n\n"
    "⚡ <b>Sirf NAYI posts</b> clone hoti hain (jo post already source me hai wo nahi).\n"
    "Purani posts chahiye to <b>🚀 Manual Forward Mode</b> use karo — jitni chaaho forward kar do, bot ek-ek ko target me daal dega."
)


def cloner_summary_text(cfg: dict) -> str:
    src = cfg.get("source_chat_id") or "❌ Set nahi"
    tgt = cfg.get("target_chat_id") or "❌ Set nahi"
    auto = "🟢 ON (chal raha hai)" if cfg.get("auto_status") == "on" else "🔴 OFF"
    tag = cfg.get("rename_tag") or "—"
    wm = cfg.get("watermark") or "—"
    return (
        "📋 <b>TUMHARI AUTO FORWARD SETTING</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 📡 <b>Source:</b> <code>{src}</code>\n"
        f"2️⃣ 📑 <b>Target:</b> <code>{tgt}</code>\n"
        f"3️⃣ 🤖 <b>Full Auto:</b> {auto}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Tag: {tag}\n💧 Watermark: {wm}\n"
        f"🖼️ Thumbnail: {'✅ set hai' if cfg.get('thumbnail_file_id') else '❌ nahi'}"
    )


# --------------------------------------------------------------------------------
# KEYBOARD / DASHBOARD
# --------------------------------------------------------------------------------
def get_cloner_settings_kb(uid: int):
    cfg = get_cloner_config(uid)

    target = cfg.get("target_chat_id") or ""
    target_txt = f"{target[:16]}" if target else "Set nahi ❌"
    source = cfg.get("source_chat_id") or ""
    source_txt = f"{source[:16]}" if source else "Set nahi ❌"
    auto_on = cfg.get("auto_status") == "on"
    auto_txt = "ON 🟢" if auto_on else "OFF 🔴"

    buttons = [
        [InlineKeyboardButton("🚀 AUTO FORWARD SETUP (3 Steps)", callback_data="cloner_setup")],
        [InlineKeyboardButton("📘 Kaise Use Karein? (Guide)", callback_data="cloner_guide")],
        [
            InlineKeyboardButton("🤖 FULL AUTO: " + auto_txt, callback_data="cloner_toggle_auto"),
            InlineKeyboardButton("🧪 Test Forward", callback_data="cloner_test"),
        ],
        [
            InlineKeyboardButton(f"📡 Source: {source_txt}", callback_data="cloner_set_source"),
            InlineKeyboardButton(f"📑 Target: {target_txt}", callback_data="cloner_set_target"),
        ],
        [InlineKeyboardButton("🔒 Private Channel? Aise karo", callback_data="cloner_private")],
        [InlineKeyboardButton("🚀 Manual Forward Mode (ek-ek post)", callback_data="cloner_start_mode")],
        [
            InlineKeyboardButton("🏷️ Rename Tag", callback_data="cloner_set_tag"),
            InlineKeyboardButton("📝 Custom Caption", callback_data="cloner_set_caption"),
        ],
        [
            InlineKeyboardButton("🔄 Replace Words", callback_data="cloner_set_replace"),
            InlineKeyboardButton("🗑️ Remove Words", callback_data="cloner_set_remove"),
        ],
        [
            InlineKeyboardButton("🖼️ Thumbnail", callback_data="cloner_set_thumb"),
            InlineKeyboardButton("💧 Watermark", callback_data="cloner_set_wm"),
        ],
        [
            InlineKeyboardButton("❌ Thumbnail Hatao", callback_data="cloner_clear_thumb"),
            InlineKeyboardButton("🔄 Reset Settings", callback_data="cloner_reset"),
        ],
        [InlineKeyboardButton("📊 Meri Setting Dekho", callback_data="cloner_status")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(buttons)


# --------------------------------------------------------------------------------
# CAPTION PROCESSING
# --------------------------------------------------------------------------------
def process_cloned_caption(text: str, cfg: dict) -> str:
    """Applies word replacement, word removal, custom caption, rename tag and watermark rules"""
    custom_cap = (cfg.get("custom_caption") or "").strip()
    replace_rules = (cfg.get("replace_words") or "").strip()
    remove_rules = (cfg.get("remove_words") or "").strip()
    watermark = (cfg.get("watermark") or "").strip()
    rename_tag = (cfg.get("rename_tag") or "").strip()

    if custom_cap:
        result = custom_cap
    else:
        result = text or ""

    # 1. Apply Remove Words
    if remove_rules:
        words_to_remove = [w.strip() for w in re.split(r"[,|\n]", remove_rules) if w.strip()]
        for w in words_to_remove:
            result = re.sub(re.escape(w), "", result, flags=re.IGNORECASE)

    # 2. Apply Replace Words (Format: old=>new or old:new)
    if replace_rules:
        for line in replace_rules.split("\n"):
            if "=>" in line:
                old_w, new_w = line.split("=>", 1)
                result = re.sub(re.escape(old_w.strip()), new_w.strip(), result, flags=re.IGNORECASE)
            elif ":" in line:
                old_w, new_w = line.split(":", 1)
                result = re.sub(re.escape(old_w.strip()), new_w.strip(), result, flags=re.IGNORECASE)

    # Clean double spaces
    result = re.sub(r"[ \t]+", " ", result).strip()

    # 3. Add Rename Tag / Prefix
    if rename_tag:
        result = f"{rename_tag} {result}".strip()

    # 4. Add Watermark
    if watermark:
        result = f"{result}\n\n{watermark}".strip()

    return result


# --------------------------------------------------------------------------------
# LOW-LEVEL SEND HELPERS (error proof)
# --------------------------------------------------------------------------------
async def _safe_call(func, **kwargs):
    """Bhejne ki koshish karta hai. FloodWait par wait karta hai, thumbnail/caption
    ki wajah se error aaye to bina uske dobara bhejta hai."""
    try:
        return await func(**kwargs)
    except RetryAfter as e:
        wait = int(getattr(e, "retry_after", 5) or 5) + 1
        log.warning("FloodWait: %ss wait kar rahe hain...", wait)
        await asyncio.sleep(wait)
        return await func(**kwargs)
    except BadRequest as e:
        err = str(e).lower()
        # Thumbnail ki wajah se fail hua -> bina thumbnail bhejo
        if "thumbnail" in err and "thumbnail" in kwargs:
            kwargs.pop("thumbnail", None)
            return await func(**kwargs)
        # Caption me galat HTML -> bina formatting bhejo
        if ("parse" in err or "entit" in err) and kwargs.get("parse_mode"):
            kwargs.pop("parse_mode", None)
            return await func(**kwargs)
        raise


def message_kind(msg: Message) -> str:
    """Kis type ka message hai - sirf jaankari ke liye."""
    if msg is None:
        return "empty"
    if msg.photo:
        return "photo"
    if msg.video:
        return "video"
    if msg.animation:
        return "animation"
    if msg.document:
        return "document"
    if msg.audio:
        return "audio"
    if msg.voice:
        return "voice"
    if msg.video_note:
        return "video_note"
    if msg.sticker:
        return "sticker"
    if msg.text:
        return "text"
    return "other"


async def send_single(bot: Bot, msg: Message, target: str, cfg: dict):
    """Ek message ko branding ke saath target channel me bhejta hai."""
    caption = process_cloned_caption(msg.caption or msg.text or "", cfg)
    thumb = (cfg.get("thumbnail_file_id") or "").strip() or None
    cap = caption or None

    if msg.photo:
        await _safe_call(bot.send_photo, chat_id=target, photo=msg.photo[-1].file_id, caption=cap, parse_mode=HTML)
    elif msg.video:
        await _safe_call(
            bot.send_video,
            chat_id=target,
            video=msg.video.file_id,
            caption=cap,
            thumbnail=thumb,
            supports_streaming=True,
            parse_mode=HTML,
        )
    elif msg.animation:
        await _safe_call(
            bot.send_animation,
            chat_id=target,
            animation=msg.animation.file_id,
            caption=cap,
            thumbnail=thumb,
            parse_mode=HTML,
        )
    elif msg.document:
        await _safe_call(
            bot.send_document,
            chat_id=target,
            document=msg.document.file_id,
            caption=cap,
            thumbnail=thumb,
            parse_mode=HTML,
        )
    elif msg.audio:
        await _safe_call(
            bot.send_audio,
            chat_id=target,
            audio=msg.audio.file_id,
            caption=cap,
            thumbnail=thumb,
            parse_mode=HTML,
        )
    elif msg.voice:
        await _safe_call(bot.send_voice, chat_id=target, voice=msg.voice.file_id, caption=cap, parse_mode=HTML)
    elif msg.video_note:
        await _safe_call(bot.send_video_note, chat_id=target, video_note=msg.video_note.file_id)
    elif msg.sticker:
        await _safe_call(bot.send_sticker, chat_id=target, sticker=msg.sticker.file_id)
    elif msg.text:
        if not caption:
            return
        await _safe_call(bot.send_message, chat_id=target, text=caption, parse_mode=HTML, disable_web_page_preview=True)
    else:
        # Poll, location, contact, dice... in sab ko copy kar dete hain
        await _safe_call(bot.copy_message, chat_id=target, from_chat_id=msg.chat_id, message_id=msg.message_id)


def _album_item(msg: Message, caption: str, parse_mode: str):
    """Album (media group) ke liye InputMedia banata hai. Support na ho to None."""
    if msg.photo:
        return InputMediaPhoto(media=msg.photo[-1].file_id, caption=caption or None, parse_mode=parse_mode if caption else None)
    if msg.video:
        return InputMediaVideo(
            media=msg.video.file_id,
            caption=caption or None,
            parse_mode=parse_mode if caption else None,
            supports_streaming=True,
        )
    if msg.document:
        return InputMediaDocument(media=msg.document.file_id, caption=caption or None, parse_mode=parse_mode if caption else None)
    if msg.audio:
        return InputMediaAudio(media=msg.audio.file_id, caption=caption or None, parse_mode=parse_mode if caption else None)
    return None


async def send_album(bot: Bot, msgs: list, target: str, cfg: dict):
    """2-10 messages ka album ek saath bhejta hai. Fail ho to ek-ek karke bhejta hai."""
    media = []
    caption_used = False
    for m in msgs:
        cap = ""
        if not caption_used:
            cap = process_cloned_caption(m.caption or m.text or "", cfg)
            if cap:
                caption_used = True
        item = _album_item(m, cap, HTML)
        if item is None:
            break
        media.append(item)

    if len(media) != len(msgs):
        # Album me mix types nahi jaate -> ek-ek karke bhej do
        for m in msgs:
            await send_single(bot, m, target, cfg)
        return

    try:
        await bot.send_media_group(chat_id=target, media=media)
    except Exception as e:
        log.warning("Album send fail (%s) -> ek-ek karke bhej rahe hain", e)
        for m in msgs:
            await send_single(bot, m, target, cfg)


# --------------------------------------------------------------------------------
# MAIN CLONE FUNCTIONS
# --------------------------------------------------------------------------------
async def clone_messages(bot: Bot, msgs: list, uid: int) -> tuple:
    """Ek ya ek se zyada (album) messages ko user ki settings ke hisaab se clone karta hai."""
    msgs = [m for m in msgs if m is not None]
    if not msgs:
        return False, "❌ Koi message nahi mila."

    cfg = get_cloner_config(uid)
    target = (cfg.get("target_chat_id") or "").strip()
    if not target:
        return False, "⚠️ <b>Target Chat ID set nahi hai!</b> Pehle <b>📑 Target</b> button se channel set karein."

    try:
        if len(msgs) == 1:
            await send_single(bot, msgs[0], target, cfg)
        else:
            await send_album(bot, msgs, target, cfg)
        count = len(msgs)
        extra = f" ({count} items album)" if count > 1 else ""
        return True, f"⚡ <b>Success!</b> Post{extra} target channel me chala gaya with your branding ✅"
    except Exception as e:
        log.error("Clone failed: %s", e)
        return False, (
            f"❌ <b>Error:</b> <code>{str(e)[:200]}</code>\n\n"
            "<i>Check karo: bot target channel me ADMIN hai? (Post Messages permission ke saath)</i>"
        )


async def forward_cloned_message(bot: Bot, msg: Message, uid: int) -> tuple:
    """Manual mode: user ka forward kiya hua single message clone karta hai."""
    return await clone_messages(bot, [msg], uid)
