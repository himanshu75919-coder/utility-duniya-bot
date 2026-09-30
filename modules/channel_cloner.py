# -*- coding: utf-8 -*-
"""
Channel Cloner & Auto-Forwarder with Custom Branding
Allows users to clone/forward posts, replace captions, add watermarks, and auto-post to target channels.
"""

from telegram import Bot, Message, InlineKeyboardButton, InlineKeyboardMarkup
from database import get_cloner_config, save_cloner_config


def get_cloner_menu_kb(uid: int):
    cfg = get_cloner_config(uid)
    target = cfg["target_chat_id"] or "Not Set ❌"
    caption = cfg["custom_caption"] or "Original (No change)"
    watermark = cfg["watermark"] or "None"
    
    buttons = [
        [
            InlineKeyboardButton(f"🎯 Target Channel: {target[:15]}", callback_data="cloner_set_target"),
        ],
        [
            InlineKeyboardButton("✍️ Set Custom Caption / Watermark", callback_data="cloner_set_caption"),
            InlineKeyboardButton("🗑️ Clear Caption", callback_data="cloner_clear_caption"),
        ],
        [
            InlineKeyboardButton("🚀 Start Forwarding / Cloning", callback_data="cloner_start_mode"),
            InlineKeyboardButton("⏹️ Stop / Reset", callback_data="cloner_reset"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_home"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


async def forward_cloned_message(bot: Bot, msg: Message, uid: int) -> tuple[bool, str]:
    """
    Takes any forwarded message or direct media from user and reposts to target channel
    with the user's custom caption and branding.
    """
    cfg = get_cloner_config(uid)
    target = cfg.get("target_chat_id")
    if not target:
        return False, "⚠️ Target channel set nahi hai! Pehle <b>Target Channel</b> set karein."
        
    custom_cap = cfg.get("custom_caption", "").strip()
    watermark = cfg.get("watermark", "").strip()
    
    # Build final caption
    orig_cap = msg.caption or msg.text or ""
    if custom_cap:
        final_caption = custom_cap
    else:
        final_caption = orig_cap
        
    if watermark:
        final_caption = f"{final_caption}\n\n{watermark}".strip()
        
    try:
        if msg.photo:
            photo_file_id = msg.photo[-1].file_id
            await bot.send_photo(chat_id=target, photo=photo_file_id, caption=final_caption, parse_mode="HTML")
        elif msg.video:
            await bot.send_video(chat_id=target, video=msg.video.file_id, caption=final_caption, parse_mode="HTML")
        elif msg.document:
            await bot.send_document(chat_id=target, document=msg.document.file_id, caption=final_caption, parse_mode="HTML")
        elif msg.audio:
            await bot.send_audio(chat_id=target, audio=msg.audio.file_id, caption=final_caption, parse_mode="HTML")
        elif msg.voice:
            await bot.send_voice(chat_id=target, voice=msg.voice.file_id, caption=final_caption, parse_mode="HTML")
        elif msg.text:
            await bot.send_message(chat_id=target, text=final_caption, parse_mode="HTML")
        else:
            await bot.copy_message(chat_id=target, from_chat_id=msg.chat_id, message_id=msg.message_id)
            
        return True, "✅ Post successfully cloned and forwarded to your channel!"
    except Exception as e:
        return False, f"❌ Error sending to channel: {str(e)}\n\n<i>Make sure the bot is added as ADMIN in target channel with Post Messages permission!</i>"
