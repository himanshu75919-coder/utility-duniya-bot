# -*- coding: utf-8 -*-
"""
joinwall.py — 🔐 FORCE-JOIN WALL (pehle channel join, phir bot)

User ki hiring (8 Oct 2026): "Force join gate banao". v105.1 (11 Oct):
channel REPLACE hua — ab DEFAULT = @osint_xpert / -1004393596502,
link = https://t.me/osint_xpert (purana @CypherGrid gaya). Env se kisi bhi
waqt badla ja sakta hai: FORCE_CHANNEL / FORCE_CHANNEL_LINK.

Design rules (ye jaan-boojh ke aise banaya hai):
  1) **Fail-open**: channel id galat ho, bot admin na ho, Telegram timeout ho jaye —
     user KABHI block nahi hoga. Bot pehle bhi "crashes" se ubhra hai; wall ki wajah
     se 100% users lock hona sabse bura bug hota.
  2) **Cache**: "join ho gaya" ka jawab 12 ghante tikta hai (har message par Telegram
     API call = slow). "nahi join kiya" sirf 45 second — join karne ke baad ka "check"
     foran kaam kare.
  3) **Owner exempt**: `ADMIN_ID` + `ADMINS` + `FORCE_JOIN_EXEMPT` wall nahi dekhte.
  4) **Groups chhod do**: gate sirf DM me lagta hai (group me "join karo" bhechna
     embarrassing + spam; wahan log already channel ke members hote hain).
  5) **Menu nahi kharab hota**: callback par wall ek NAYA message bane bhejta hai
     (purana menu waise hi rehta hai — join karke wahi button dobara dabao).

Env knobs:
  FORCE_CHANNEL          = @osint_xpert | -1004393596502  (khali = wall off;
                          key hi set na ho to code-default osint_xpert chalta)
  FORCE_CHANNEL_LINK     = https://t.me/osint_xpert                    (khali = khud banata hai)
  FORCE_JOIN             = auto | on | off      (default auto = channel ho to ON)
  FORCE_JOIN_GROUPS      = off                  (on karo to group chats me bhi gate)
  FORCE_JOIN_EXEMPT      = 12345,67890          (extra ids, comma se)
  FORCE_JOIN_OK_HOURS    = 12                   (kitni der me dobara verify)
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Tuple

from .safesend import safe_answer_cb, safe_edit, safe_send_text

__all__ = ["enabled", "channel", "link", "exempt", "allowed", "gate", "handle_check",
           "wall_text", "wall_kb", "reset", "stats", "health_line", "normalize_channel"]

# ------------------------------------------------------------------ config
_OK_TTL: float = max(60.0, float(os.environ.get("FORCE_JOIN_OK_HOURS") or 12) * 3600.0)
_NO_TTL: float = 45.0
_CACHE_MAX: int = 5000          # bounded — Render ke 512 MB par leak nahi karega
_cache: Dict[int, Tuple[bool, float]] = {}
_stats: Dict[str, int] = {"allowed": 0, "blocked": 0, "errors": 0, "exempt": 0, "joins": 0}


def _env(name: str, default: str = "") -> str:
    return str(os.environ.get(name) or default).strip()


def _flag(name: str, default: bool) -> bool:
    v = _env(name).lower()
    if not v:
        return default
    return v not in ("off", "0", "false", "no", "band", "nahi")


def normalize_channel(raw: str) -> Any:
    """'@CypherGrid' | 'CypherGrid' | 't.me/CypherGrid' | '-1004331054356' →
    Telegram ko jo chahiye: int (id) ya '@username'."""
    c = (raw or "").strip()
    if not c:
        return ""
    if c.startswith("@"):
        return c
    low = c.lower()
    for pre in ("https://", "http://"):
        if low.startswith(pre):
            c = c[len(pre):]
            low = c.lower()
    if low.startswith("t.me/"):
        c = c[5:]
    c = c.strip("/").strip()
    if not c:
        return ""
    body = c[1:] if c.startswith("-") else c
    if body.isdigit():
        return int(c)                      # numeric channel id (bot ko usme admin chahiye)
    return "@" + c                         # username


# v105.1 (user order 11 Oct): purana @CypherGrid HATAA — naya channel.
# Key HI na set ho to ye default chalta hai; explicit khali value ("" set
# karna) ab bhi wall OFF rakhti hai (backward compatible + test-locked).
DEFAULT_CHANNEL = "-1004393596502"
DEFAULT_LINK = "https://t.me/osint_xpert"


def channel() -> Any:
    """Channel jisme join karana hai ("" = koi nahi). Key missing → default."""
    if "FORCE_CHANNEL" not in os.environ:
        return normalize_channel(DEFAULT_CHANNEL)
    return normalize_channel(_env("FORCE_CHANNEL"))


def link() -> str:
    """Join ka button URL."""
    l = _env("FORCE_CHANNEL_LINK")
    if l:
        return l if l.startswith("http") else "https://" + l.lstrip("/")
    ch = channel()
    if isinstance(ch, str) and ch.startswith("@"):
        return "https://t.me/" + ch[1:]
    if "FORCE_CHANNEL" not in os.environ:
        return DEFAULT_LINK     # v105.1: default channel ka link
    return ""


def enabled() -> bool:
    """Wall chalu hai? (channel set + FORCE_JOIN off na ho)."""
    if not _flag("FORCE_JOIN", True):
        return False
    return bool(channel())


def exempt(uid: int) -> bool:
    """Ye user wall se maaf hai? (owner/admin + FORCE_JOIN_EXEMPT)."""
    try:
        u = int(uid)
    except Exception:
        return True
    if u <= 0:
        return True
    if u in _exempt_ids():
        _stats["exempt"] += 1
        return True
    return False


def _exempt_ids() -> set:
    ids = set()
    for n in ("ADMIN_ID", "OWNER_ID"):
        try:
            v = int(_env(n) or 0)
            if v > 0:
                ids.add(v)
        except Exception:
            pass
    for chunk in _env("ADMINS").replace(";", ",").split(","):
        try:
            v = int(chunk.strip())
            if v > 0:
                ids.add(v)
        except Exception:
            pass
    for chunk in _env("FORCE_JOIN_EXEMPT").replace(";", ",").split(","):
        try:
            v = int(chunk.strip())
            if v > 0:
                ids.add(v)
        except Exception:
            pass
    return ids


# ------------------------------------------------------------------ cache
def _cached(uid: int) -> Optional[bool]:
    hit = _cache.get(uid)
    if not hit:
        return None
    ok, ts = hit
    ttl = _OK_TTL if ok else _NO_TTL
    if time.time() - ts > ttl:
        _cache.pop(uid, None)
        return None
    return ok


def _put(uid: int, ok: bool) -> None:
    if len(_cache) >= _CACHE_MAX:
        # sabse purana aadha phenk do (bounded — memory kabhi na badhe)
        for k in sorted(_cache, key=lambda k: _cache[k][1])[: _CACHE_MAX // 2]:
            _cache.pop(k, None)
    _cache[uid] = (ok, time.time())


def reset(uid: Optional[int] = None) -> None:
    """User ka jawab bhool jao (join ke baad ka 'check' dobara poochhe)."""
    if uid is None:
        _cache.clear()
    else:
        _cache.pop(int(uid), None)


# ------------------------------------------------------------------ check
_OK_STATES = ("creator", "administrator", "member")


async def allowed(bot, uid: int) -> bool:
    """User channel ka member hai? Cache + fail-open."""
    if not enabled():
        return True
    try:
        uid = int(uid)
    except Exception:
        return True
    if uid in _exempt_ids():
        return True
    hit = _cached(uid)
    if hit is not None:
        return hit
    ch = channel()
    ok = True                      # ← default SAFE: query fail ho to user block NAHo
    try:
        m = await bot.get_chat_member(chat_id=ch, user_id=uid)
        status = str(getattr(m, "status", "") or "").lower()
        ok = status in _OK_STATES
    except Exception:
        _stats["errors"] += 1
        ok = True
    _put(uid, ok)
    return ok


# ------------------------------------------------------------------ UI
def wall_text() -> str:
    ch = channel()
    name = ch if isinstance(ch, str) else "channel"
    url = link()
    # link ho to clickable (copy bhi ho sakta hai); numeric-id mode me <code> me dikhao
    ch_line = (f'👉 Channel: <a href="{url}">{name}</a>' if url
               else f"👉 Channel: <code>{name}</code>")
    return ("<b>🔐 Pehle ek chhota sa kaam</b>\n"
            "──────────────────────\n"
            f"Neeche wala channel <b>join</b> karo — roz yahan <b>naye tools, "
            f"free updates aur offers</b> aate hain.\n"
            "📌 Ek baar join = uske baad bot hamesha khula (dubara kuch nahi).\n"
            + ch_line)


def wall_kb():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup   # noqa: PLC0415
    rows = []
    if link():
        rows.append([InlineKeyboardButton("🔗 Channel join karo", url=link())])
    rows.append([InlineKeyboardButton("✅ Join ho gaya — check karo", callback_data="fj:check")])
    return InlineKeyboardMarkup(rows)


DONE_TEXT = ("<b>🎉 Ho gaya! Welcome ✅</b>\n"
             "Ab bot khula hai — <b>/menu</b> se koi bhi tool kholo "
             "(video download, IFSC, pincode, number info, IMEI… sab free).")


# ------------------------------------------------------------------ gates
def _is_private(update) -> bool:
    try:
        ctype = str(getattr(update.effective_chat, "type", "") or "").lower()
    except Exception:
        return False
    return ctype in ("private", "")


async def gate(update, context) -> bool:
    """True = aage badho. False = wall bhej di (kuch aur mat karo)."""
    if not enabled():
        return True
    if not _is_private(update) and not _flag("FORCE_JOIN_GROUPS", False):
        return True
    try:
        uid = int(update.effective_user.id)
    except Exception:
        return True
    if uid in _exempt_ids():
        _stats["exempt"] += 1
        return True
    bot = getattr(context, "bot", None)          # context na mile bhi gate na tute
    if await allowed(bot, uid):
        _stats["allowed"] += 1
        return True
    _stats["blocked"] += 1
    q = getattr(update, "callback_query", None)
    chat_id = 0
    try:
        chat_id = int(update.effective_chat.id)
    except Exception:
        try:
            chat_id = int((q.message if q is not None else update.message).chat_id)
        except Exception:
            chat_id = uid
    if q is not None:
        await safe_answer_cb(q, "🙏 Pehle channel join karke aao", show_alert=True)
    # safesend layer: HTML toote, flood aaye, message lamba ho — crash nahi hoga
    await safe_send_text(bot, chat_id, wall_text(), reply_markup=wall_kb(),
                         disable_web_page_preview=True)
    return False


async def handle_check(update, context) -> bool:
    """'✅ Join ho gaya — check karo' button. Cache hata ke dobara poochhta hai.

    True = member mil gaya (caller ab user ka asli menu bhej sakta hai).
    """
    q = getattr(update, "callback_query", None)
    if q is None:
        return False
    try:
        uid = int(update.effective_user.id)
    except Exception:
        return False
    reset(uid)                                     # purana 'nahi' jawab bhool jao
    ok = await allowed(getattr(context, "bot", None), uid)
    if ok:
        _stats["joins"] += 1
        _put(uid, True)
    await safe_answer_cb(q, "🎉 Join ho gaya — welcome!" if ok else
                            "Ab bhi channel me nahi dikhe 🙏", show_alert=not ok)
    if ok:
        # wall wale message ko hi 'welcome' card me badal do (naya message flood nahi).
        # Asli menu bot.py bhejta hai (kb_for) — yahan koi dead button nahi chhodte.
        await safe_edit(getattr(q, "message", None), DONE_TEXT)
    return ok


# ------------------------------------------------------------------ health
def stats() -> dict:
    return dict(_stats)


def health_line() -> str:
    """/health ke liye ek line — taaki wall ka asli halat aap khud dekh sako."""
    if not enabled():
        why = "FORCE_JOIN=off" if _env("FORCE_JOIN") else "FORCE_CHANNEL khaali"
        return f"join-wall: OFF ({why})"
    ch = channel()
    return (f"join-wall: ON | ch={ch if not isinstance(ch, int) else 'id:' + str(ch)}"
            f" | ok-cache={len(_cache)} | allowed={_stats['allowed']}"
            f" blocked={_stats['blocked']} joins={_stats['joins']}"
            f" errors={_stats['errors']} (fail-open)")
