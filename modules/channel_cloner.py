# -*- coding: utf-8 -*-
"""
Advanced Channel Cloner & Auto-Forwarder Settings Dashboard
Allows users to clone posts, replace words, remove promo links, add custom thumbnails, and fast-forward media.
"""

import re
import asyncio
from telegram import Bot, Message, InlineKeyboardButton, InlineKeyboardMarkup
from database import get_cloner_config, save_cloner_config


def get_cloner_settings_kb(uid: int):
    cfg = get_cloner_config(uid)
    target = cfg["target_chat_id"] or "Not Set ❌"
    has_thumb = "✅ Active" if cfg["thumbnail_file_id"] else "None ❌"

    buttons = [
        [
            InlineKeyboardButton(f"📑 Set Chat ID ({target[:10]})", callback_data="cloner_set_target"),
            InlineKeyboardButton("🏷️ Set Rename Tag", callback_data="cloner_set_tag"),
        ],
        [
            InlineKeyboardButton("📝 Set Caption", callback_data="cloner_set_caption"),
            InlineKeyboardButton("🔄 Replace Words", callback_data="cloner_set_replace"),
        ],
        [
            InlineKeyboardButton("🗑️ Remove Words", callback_data="cloner_set_remove"),
            InlineKeyboardButton("🔄 Reset Settings", callback_data="cloner_reset"),
        ],
        [
            InlineKeyboardButton(f"🖼️ Set Thumbnail ({has_thumb})", callback_data="cloner_set_thumb"),
            InlineKeyboardButton("❌ Remove Thumbnail", callback_data="cloner_clear_thumb"),
        ],
        [
            InlineKeyboardButton("💧 Watermark Setup", callback_data="cloner_set_wm"),
            InlineKeyboardButton("🚀 Start Fast Auto-Forward", callback_data="cloner_start_mode"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def process_cloned_caption(text: str, cfg: dict) -> str:
    """Applies word replacement, word removal, custom caption, and watermark rules"""
    custom_cap = cfg.get("custom_caption", "").strip()
    replace_rules = cfg.get("replace_words", "").strip()
    remove_rules = cfg.get("remove_words", "").strip()
    watermark = cfg.get("watermark", "").strip()
    rename_tag = cfg.get("rename_tag", "").strip()

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


async def forward_cloned_message(bot: Bot, msg: Message, uid: int) -> tuple[bool, str]:
    """
    Takes any forwarded message or direct media from user and reposts to target channel
    with all custom transformations in under 0.5s.
    """
    cfg = get_cloner_config(uid)
    target = cfg.get("target_chat_id")
    if not target:
        return False, "⚠️ <b>Target Chat ID set nahi hai!</b> Pehle <b>Set Chat ID</b> se channel add karein."

    orig_caption = msg.caption or msg.text or ""
    final_caption = process_cloned_caption(orig_caption, cfg)
    thumb_id = cfg.get("thumbnail_file_id")

    try:
        if msg.photo:
            photo_file_id = msg.photo[-1].file_id
            await bot.send_photo(chat_id=target, photo=photo_file_id, caption=final_caption, parse_mode="HTML")
        elif msg.video:
            await bot.send_video(
                chat_id=target,
                video=msg.video.file_id,
                caption=final_caption,
                thumbnail=thumb_id or None,
                parse_mode="HTML",
            )
        elif msg.document:
            await bot.send_document(
                chat_id=target,
                document=msg.document.file_id,
                caption=final_caption,
                thumbnail=thumb_id or None,
                parse_mode="HTML",
            )
        elif msg.audio:
            await bot.send_audio(chat_id=target, audio=msg.audio.file_id, caption=final_caption, parse_mode="HTML")
        elif msg.voice:
            await bot.send_voice(chat_id=target, voice=msg.voice.file_id, caption=final_caption, parse_mode="HTML")
        elif msg.text:
            await bot.send_message(chat_id=target, text=final_caption, parse_mode="HTML")
        else:
            await bot.copy_message(chat_id=target, from_chat_id=msg.chat_id, message_id=msg.message_id)

        return True, "⚡ <b>Success!</b> Post forwarded to target channel with your custom branding!"
    except Exception as e:
        return False, f"❌ Error sending to target: {str(e)}\n\n<i>Make sure bot is ADMIN in target channel with Post Messages permission!</i>"
