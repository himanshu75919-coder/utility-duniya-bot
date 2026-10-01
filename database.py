# -*- coding: utf-8 -*-
"""
Database Manager for Utility Duniya Super Bot
Handles Users, Referrals, VIP Subscriptions, Payments, Channel Cloner Settings, and Stats.
"""

import os
import sqlite3
from datetime import date, datetime, timedelta

DB_PATH = os.getenv("DB_PATH", "botdata.db")


def db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Users table
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            name TEXT DEFAULT '',
            username TEXT DEFAULT '',
            uses_today INTEGER DEFAULT 0,
            last_date TEXT DEFAULT '',
            premium_until TEXT DEFAULT '',
            referred_by INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            joined_at TEXT DEFAULT '',
            trial_date TEXT DEFAULT '',
            trial_count INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0
        )"""
    )
    # Payment / VIP verification requests table
    cur.execute(
        """CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_name TEXT,
            amount INTEGER,
            utr_ref TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )"""
    )
    # Advanced Channel Cloner configs table
    cur.execute(
        """CREATE TABLE IF NOT EXISTS cloner_configs(
            user_id INTEGER PRIMARY KEY,
            target_chat_id TEXT DEFAULT '',
            custom_caption TEXT DEFAULT '',
            watermark TEXT DEFAULT '',
            rename_tag TEXT DEFAULT '',
            replace_words TEXT DEFAULT '',
            remove_words TEXT DEFAULT '',
            thumbnail_file_id TEXT DEFAULT '',
            filter_type TEXT DEFAULT 'all',
            status TEXT DEFAULT 'idle',
            source_chat_id TEXT DEFAULT '',
            auto_status TEXT DEFAULT 'off'
        )"""
    )
    # Migration checks
    for col, typ in [
        ("rename_tag", "TEXT DEFAULT ''"),
        ("replace_words", "TEXT DEFAULT ''"),
        ("remove_words", "TEXT DEFAULT ''"),
        ("thumbnail_file_id", "TEXT DEFAULT ''"),
        ("source_chat_id", "TEXT DEFAULT ''"),
        ("auto_status", "TEXT DEFAULT 'off'"),
    ]:
        try:
            cur.execute(f"ALTER TABLE cloner_configs ADD COLUMN {col} {typ}")
        except Exception:
            pass

    con.commit()
    return con


def get_user(uid: int, name: str = "") -> dict:
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    today = date.today().isoformat()
    if not row:
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            "INSERT INTO users(user_id, name, uses_today, last_date, joined_at, trial_date, trial_count, banned) VALUES(?,?,0,?,?,?,0,0)",
            (uid, (name or "")[:60], today, now_str, today),
        )
        con.commit()
        con.close()
        return {
            "user_id": uid,
            "name": name,
            "username": "",
            "uses_today": 0,
            "last_date": today,
            "premium_until": "",
            "referred_by": 0,
            "referrals": 0,
            "joined_at": now_str,
            "trial_date": today,
            "trial_count": 0,
            "banned": 0,
        }

    cols = [d[0] for d in cur.description]
    u = dict(zip(cols, row))

    if u.get("last_date") != today:
        cur.execute("UPDATE users SET uses_today=0, last_date=? WHERE user_id=?", (today, uid))
        con.commit()
        u["uses_today"] = 0
        u["last_date"] = today

    if u.get("trial_date") != today:
        cur.execute("UPDATE users SET trial_count=0, trial_date=? WHERE user_id=?", (today, uid))
        con.commit()
        u["trial_count"] = 0
        u["trial_date"] = today

    con.close()
    return u


def save_username(uid: int, username: str):
    if not username:
        return
    try:
        con = db()
        con.execute("UPDATE users SET username=? WHERE user_id=?", (username.lower(), uid))
        con.commit()
        con.close()
    except Exception:
        pass


def find_by_username(username: str):
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT user_id, name, username FROM users WHERE username=?", (username.lower().lstrip("@"),))
        r = cur.fetchone()
        con.close()
        return r
    except Exception:
        return None


def get_user_row(uid: int):
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        r = cur.fetchone()
        cols = [d[0] for d in cur.description] if cur.description else []
        con.close()
        return dict(zip(cols, r)) if r else None
    except Exception:
        return None


def top_referrers(n: int = 5):
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT name, referrals FROM users WHERE referrals>0 ORDER BY referrals DESC LIMIT ?", (n,))
        rows = cur.fetchall()
        con.close()
        return rows
    except Exception:
        return []


def recent_users(n: int = 10):
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT user_id, name, username FROM users ORDER BY rowid DESC LIMIT ?", (n,))
        rows = cur.fetchall()
        con.close()
        return rows
    except Exception:
        return []


def premium_users():
    try:
        con = db()
        cur = con.cursor()
        cur.execute(
            "SELECT user_id, name, premium_until FROM users WHERE premium_until > ? ORDER BY premium_until DESC",
            (datetime.now().isoformat(timespec="seconds"),),
        )
        rows = cur.fetchall()
        con.close()
        return rows
    except Exception:
        return []


def set_ban(uid: int, val: int):
    try:
        con = db()
        con.execute("UPDATE users SET banned=? WHERE user_id=?", (val, uid))
        con.commit()
        con.close()
    except Exception:
        pass


def is_banned(uid: int) -> bool:
    try:
        u = get_user(uid)
        return bool(u.get("banned"))
    except Exception:
        return False


def add_use(uid: int):
    try:
        con = db()
        con.execute("UPDATE users SET uses_today=uses_today+1 WHERE user_id=?", (uid,))
        con.commit()
        con.close()
    except Exception:
        pass


def refund_use(uid: int):
    try:
        con = db()
        con.execute("UPDATE users SET uses_today=CASE WHEN uses_today>0 THEN uses_today-1 ELSE 0 END WHERE user_id=?", (uid,))
        con.commit()
        con.close()
    except Exception:
        pass


def add_trial(uid: int):
    try:
        con = db()
        con.execute("UPDATE users SET trial_count=trial_count+1 WHERE user_id=?", (uid,))
        con.commit()
        con.close()
    except Exception:
        pass


def refund_trial(uid: int):
    try:
        con = db()
        con.execute("UPDATE users SET trial_count=CASE WHEN trial_count>0 THEN trial_count-1 ELSE 0 END WHERE user_id=?", (uid,))
        con.commit()
        con.close()
    except Exception:
        pass


def is_premium(u: dict) -> bool:
    if not u:
        return False
    prem = u.get("premium_until", "")
    if not prem:
        return False
    if prem == "lifetime":
        return True
    try:
        exp = datetime.fromisoformat(prem)
        return exp > datetime.now()
    except Exception:
        return False


def premium_expiry(u: dict) -> str:
    try:
        val = u.get("premium_until", "")
        if val == "lifetime":
            return "👑 LIFETIME VIP"
        return datetime.fromisoformat(val).strftime("%d-%m-%Y") if val else "Inactive (Free)"
    except Exception:
        return "-"


def grant_premium(uid: int, days: int) -> str:
    con = db()
    cur = con.cursor()
    cur.execute("SELECT premium_until FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    base = datetime.now()
    if row and row[0] and row[0] != "lifetime":
        try:
            d = datetime.fromisoformat(row[0])
            if d > base:
                base = d
        except Exception:
            pass
    if days >= 9999:
        new_val = "lifetime"
    else:
        new_val = (base + timedelta(days=days)).isoformat(timespec="seconds")
    cur.execute("UPDATE users SET premium_until=? WHERE user_id=?", (new_val, uid))
    con.commit()
    con.close()
    return new_val


def add_referral(new_uid: int, ref_uid: int) -> int:
    if new_uid == ref_uid or ref_uid <= 0:
        return 0
    con = db()
    cur = con.cursor()
    cur.execute("SELECT referred_by FROM users WHERE user_id=?", (new_uid,))
    r = cur.fetchone()
    if r and r[0]:
        con.close()
        return 0
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (ref_uid,))
    if not cur.fetchone():
        con.close()
        return 0
    cur.execute("UPDATE users SET referred_by=? WHERE user_id=?", (ref_uid, new_uid))
    cur.execute("UPDATE users SET referrals=referrals+1 WHERE user_id=?", (ref_uid,))
    cur.execute("SELECT referrals FROM users WHERE user_id=?", (ref_uid,))
    row = cur.fetchone()
    con.commit()
    con.close()
    return row[0] if row else 0


def all_user_ids():
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT user_id FROM users")
        ids = [r[0] for r in cur.fetchall()]
        con.close()
        return ids
    except Exception:
        return []


def stats():
    try:
        con = db()
        cur = con.cursor()
        today = date.today().isoformat()
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE last_date=?", (today,))
        active_today = cur.fetchone()[0]
        cur.execute("SELECT SUM(uses_today) FROM users WHERE last_date=?", (today,))
        uses_sum = cur.fetchone()[0] or 0
        cur.execute(
            "SELECT COUNT(*) FROM users WHERE premium_until='lifetime' OR premium_until > ?",
            (datetime.now().isoformat(timespec="seconds"),),
        )
        vip_cnt = cur.fetchone()[0]
        con.close()
        return {
            "total_users": total,
            "active_today": active_today,
            "uses_today": uses_sum,
            "vip_users": vip_cnt,
        }
    except Exception:
        return {"total_users": 0, "active_today": 0, "uses_today": 0, "vip_users": 0}


# Advanced Cloner helpers
def get_cloner_config(uid: int) -> dict:
    try:
        con = db()
        cur = con.cursor()
        cur.execute(
            """SELECT target_chat_id, custom_caption, watermark, rename_tag,
                      replace_words, remove_words, thumbnail_file_id, filter_type, status,
                      source_chat_id, auto_status
               FROM cloner_configs WHERE user_id=?""",
            (uid,),
        )
        r = cur.fetchone()
        con.close()
        if r:
            return {
                "target_chat_id": r[0] or "",
                "custom_caption": r[1] or "",
                "watermark": r[2] or "",
                "rename_tag": r[3] or "",
                "replace_words": r[4] or "",
                "remove_words": r[5] or "",
                "thumbnail_file_id": r[6] or "",
                "filter_type": r[7] or "all",
                "status": r[8] or "idle",
                "source_chat_id": r[9] or "",
                "auto_status": r[10] or "off",
            }
    except Exception:
        pass
    return {
        "target_chat_id": "",
        "custom_caption": "",
        "watermark": "",
        "rename_tag": "",
        "replace_words": "",
        "remove_words": "",
        "thumbnail_file_id": "",
        "filter_type": "all",
        "status": "idle",
        "source_chat_id": "",
        "auto_status": "off",
    }


def save_cloner_config(
    uid: int,
    target: str = None,
    caption: str = None,
    watermark: str = None,
    rename_tag: str = None,
    replace_words: str = None,
    remove_words: str = None,
    thumbnail_file_id: str = None,
    filter_type: str = None,
    status: str = None,
    source_chat_id: str = None,
    auto_status: str = None,
):
    try:
        cfg = get_cloner_config(uid)
        target = target if target is not None else cfg["target_chat_id"]
        caption = caption if caption is not None else cfg["custom_caption"]
        watermark = watermark if watermark is not None else cfg["watermark"]
        rename_tag = rename_tag if rename_tag is not None else cfg["rename_tag"]
        replace_words = replace_words if replace_words is not None else cfg["replace_words"]
        remove_words = remove_words if remove_words is not None else cfg["remove_words"]
        thumbnail_file_id = thumbnail_file_id if thumbnail_file_id is not None else cfg["thumbnail_file_id"]
        filter_type = filter_type if filter_type is not None else cfg["filter_type"]
        status = status if status is not None else cfg["status"]
        source_chat_id = source_chat_id if source_chat_id is not None else cfg.get("source_chat_id", "")
        auto_status = auto_status if auto_status is not None else cfg.get("auto_status", "off")

        con = db()
        con.execute(
            """INSERT OR REPLACE INTO cloner_configs(
                user_id, target_chat_id, custom_caption, watermark, rename_tag,
                replace_words, remove_words, thumbnail_file_id, filter_type, status,
                source_chat_id, auto_status
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                uid, target, caption, watermark, rename_tag, replace_words, remove_words,
                thumbnail_file_id, filter_type, status, source_chat_id, auto_status,
            ),
        )
        con.commit()
        con.close()
    except Exception:
        pass


def get_auto_cloners_for_source(source_chat_id) -> list:
    """Jis source channel me nayi post aayi, uske liye jitne users ka FULL AUTO ON hai
    unki poori cloner config list return karta hai."""
    out = []
    try:
        src = str(source_chat_id).strip()
        if src.startswith("@"):
            src = src.lower()
        con = db()
        cur = con.cursor()
        cur.execute(
            """SELECT user_id, target_chat_id, custom_caption, watermark, rename_tag,
                      replace_words, remove_words, thumbnail_file_id, auto_status, source_chat_id
               FROM cloner_configs WHERE auto_status='on'"""
        )
        rows = cur.fetchall()
        con.close()
        for r in rows:
            saved_src = (r[9] or "").strip()
            if saved_src.startswith("@"):
                saved_src = saved_src.lower()
            if saved_src and saved_src == src:
                out.append(
                    {
                        "user_id": r[0],
                        "target_chat_id": r[1] or "",
                        "custom_caption": r[2] or "",
                        "watermark": r[3] or "",
                        "rename_tag": r[4] or "",
                        "replace_words": r[5] or "",
                        "remove_words": r[6] or "",
                        "thumbnail_file_id": r[7] or "",
                        "auto_status": r[8] or "off",
                        "source_chat_id": r[9] or "",
                    }
                )
    except Exception:
        return []
    return out
