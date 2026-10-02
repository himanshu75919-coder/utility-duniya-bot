# -*- coding: utf-8 -*-
"""
Database Manager for Utility Duniya Super Bot
Handles Users, Referrals, VIP Subscriptions, Payments, Channel Cloner Settings, and Stats.
"""

import os
import sqlite3
from datetime import date, datetime, timedelta

DB_PATH = os.getenv("DB_PATH", "botdata.db")
# Naye user ko ye credits milte hain (ek baar ke — daily reset NAHI hota).
# Ye sirf premium tools (Video Downloader, Number Info, Channel Cloner, Private Channel Setup) me lagte hain.
CREDITS_START = int(os.getenv("FREE_CREDITS", "25") or 25)


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
    # --- payments table ka v33 upgrade (strict verification ke liye naye columns) ---
    try:
        cur.execute("PRAGMA table_info(payments)")
        have = {r[1] for r in cur.fetchall()}
        for col, typ in [
            ("plan_key", "TEXT DEFAULT ''"),
            ("plan_days", "INTEGER DEFAULT 0"),
            ("shot_file_id", "TEXT DEFAULT ''"),
            ("shot_unique_id", "TEXT DEFAULT ''"),
            ("flags", "TEXT DEFAULT '{}'"),
            ("reviewer", "INTEGER DEFAULT 0"),
            ("reviewed_at", "TEXT DEFAULT ''"),
            ("admin_msg_id", "INTEGER DEFAULT 0"),
            ("admin_chat_id", "INTEGER DEFAULT 0"),
            ("note", "TEXT DEFAULT ''"),
        ]:
            if col not in have:
                cur.execute(f"ALTER TABLE payments ADD COLUMN {col} {typ}")
    except Exception:
        pass
    con.commit()

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

    # CREDITS: 25 free credits (ek baar ke, daily nahi) — sirf premium tools ke liye
    try:
        have = [c[1] for c in cur.execute("PRAGMA table_info(users)").fetchall()]
        if "credits" not in have:
            cur.execute(f"ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT {CREDITS_START}")
    except Exception:
        pass

    # Chhote settings (tutorial link, telegra.ph token, admin ka chuna plan...)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS bot_meta(
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )"""
    )
    # Admin ne seedha (bina payment) kisko VIP di — uska record
    cur.execute(
        """CREATE TABLE IF NOT EXISTS vip_grants(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            days INTEGER,
            by_admin INTEGER,
            plan_key TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT ''
        )"""
    )
    con.commit()
    return con


def meta_get(key: str, default: str = "") -> str:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT value FROM bot_meta WHERE key=?", (key,))
        row = cur.fetchone()
        con.close()
        return (row[0] if row and row[0] else default)
    except Exception:
        return default


def meta_set(key: str, value: str) -> bool:
    try:
        con = db()
        con.execute("INSERT INTO bot_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, str(value)))
        con.commit()
        con.close()
        return True
    except Exception:
        return False


def add_vip_grant(uid: int, days: int, by_admin: int, plan_key: str = "", note: str = "") -> int:
    try:
        con = db()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO vip_grants(user_id,days,by_admin,plan_key,note,created_at) VALUES(?,?,?,?,?,?)",
            (uid, int(days), int(by_admin), plan_key, note, datetime.now().isoformat(timespec="seconds")))
        pid = cur.lastrowid
        con.commit()
        con.close()
        return int(pid or 0)
    except Exception:
        return 0


def list_vip_grants(limit: int = 10) -> list:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM vip_grants ORDER BY id DESC LIMIT ?", (int(limit),))
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        con.close()
        return rows
    except Exception:
        return []


def vip_grants_today() -> int:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM vip_grants WHERE created_at LIKE ?", (date.today().isoformat() + "%",))
        n = cur.fetchone()[0]
        con.close()
        return int(n or 0)
    except Exception:
        return 0


def get_user(uid: int, name: str = "") -> dict:
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    today = date.today().isoformat()
    if not row:
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute(
            "INSERT INTO users(user_id, name, uses_today, last_date, joined_at, trial_date, trial_count, banned, credits) VALUES(?,?,0,?,?,?,0,0,?)",
            (uid, (name or "")[:60], today, now_str, today, CREDITS_START),
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
            "credits": CREDITS_START,
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
    if cur.rowcount == 0:
        # User pehle bot start nahi kiya (row nahi hai) — bana do, warna VIP lagta hai par lagta nahi 😅
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute(
            "INSERT INTO users (user_id, name, premium_until, joined_at, trial_date) VALUES (?,?,?,?,?)",
            (uid, "", new_val, datetime.now().isoformat(timespec="seconds"), today),
        )
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


# ==========================================================================
# v33 — VIP PAYMENT VERIFICATION (strict) ke liye database functions
# ==========================================================================
import json as _json


def create_payment(uid: int, plan_key: str, plan_name: str, amount: int, plan_days: int,
                   utr: str, shot_file_id: str = "", shot_unique_id: str = "",
                   flags: dict | None = None) -> int:
    """Naya payment record banata hai (status=pending). Return: payment id"""
    try:
        con = db()
        cur = con.cursor()
        cur.execute(
            """INSERT INTO payments (user_id, plan_name, amount, utr_ref, status, created_at,
                                     plan_key, plan_days, shot_file_id, shot_unique_id, flags)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (uid, plan_name, int(amount), utr, "pending", datetime.now().isoformat(timespec="seconds"),
             plan_key, int(plan_days), shot_file_id, shot_unique_id, _json.dumps(flags or {})),
        )
        pid = cur.lastrowid
        con.commit()
        con.close()
        return pid
    except Exception:
        return 0


def get_payment(pid: int) -> dict:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM payments WHERE id=?", (pid,))
        row = cur.fetchone()
        cols = [d[0] for d in cur.description]
        con.close()
        return dict(zip(cols, row)) if row else {}
    except Exception:
        return {}


def set_payment_status(pid: int, status: str, reviewer: int = 0, note: str = "") -> bool:
    try:
        con = db()
        con.execute("UPDATE payments SET status=?, reviewer=?, reviewed_at=?, note=? WHERE id=?",
                    (status, reviewer, datetime.now().isoformat(timespec="seconds"), note, pid))
        con.commit()
        con.close()
        return True
    except Exception:
        return False


def set_payment_admin_msg(pid: int, chat_id: int, msg_id: int):
    try:
        con = db()
        con.execute("UPDATE payments SET admin_chat_id=?, admin_msg_id=? WHERE id=?", (chat_id, msg_id, pid))
        con.commit()
        con.close()
    except Exception:
        pass


def utr_exists(utr: str, exclude_pid: int = 0) -> bool:
    """Same UTR kisi aur payment me use ho chuka hai? (duplicate check)"""
    if not utr:
        return False
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT id FROM payments WHERE utr_ref=? AND id!=? AND status!='rejected' LIMIT 1",
                    (utr, exclude_pid))
        row = cur.fetchone()
        con.close()
        return bool(row)
    except Exception:
        return False


def shot_exists(unique_id: str, exclude_pid: int = 0) -> bool:
    """Same screenshot dobara use hua? (replay check)"""
    if not unique_id:
        return False
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT id FROM payments WHERE shot_unique_id=? AND id!=? AND status!='rejected' LIMIT 1",
                    (unique_id, exclude_pid))
        row = cur.fetchone()
        con.close()
        return bool(row)
    except Exception:
        return False


def pending_payments_count() -> int:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM payments WHERE status='pending'")
        n = cur.fetchone()[0]
        con.close()
        return int(n or 0)
    except Exception:
        return 0


def pending_payments(limit: int = 10) -> list:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM payments WHERE status='pending' ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        con.close()
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


def recent_payments(limit: int = 10, status: str = "") -> list:
    try:
        con = db()
        cur = con.cursor()
        if status:
            cur.execute("SELECT * FROM payments WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit))
        else:
            cur.execute("SELECT * FROM payments ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        con.close()
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


def user_payments(uid: int, limit: int = 5) -> list:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM payments WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        con.close()
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


def user_payment_history(uid: int) -> dict:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT status, COUNT(*) FROM payments WHERE user_id=? GROUP BY status", (uid,))
        rows = cur.fetchall()
        con.close()
        d = {k: int(v) for k, v in rows}
        return {"approved": d.get("approved", 0), "rejected": d.get("rejected", 0), "pending": d.get("pending", 0)}
    except Exception:
        return {"approved": 0, "rejected": 0, "pending": 0}


def payment_stats() -> dict:
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT status, COUNT(*), COALESCE(SUM(amount),0) FROM payments GROUP BY status")
        rows = cur.fetchall()
        con.close()
        st = {k: {"count": int(c), "amount": int(a or 0)} for k, c, a in rows}
        return {
            "pending": st.get("pending", {}).get("count", 0),
            "approved": st.get("approved", {}).get("count", 0),
            "rejected": st.get("rejected", {}).get("count", 0),
            "revenue": st.get("approved", {}).get("amount", 0),
        }
    except Exception:
        return {"pending": 0, "approved": 0, "rejected": 0, "revenue": 0}


# ======================================================================
#  CREDITS (25 free — ek baar ke). Sirf premium tools me lagte hain.
# ======================================================================
def get_credits(uid: int) -> int:
    """User ke bache hue credits. Row na ho to CREDITS_START."""
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
        row = cur.fetchone()
        con.close()
        if row is None or row[0] is None:
            return CREDITS_START
        return int(row[0])
    except Exception:
        return CREDITS_START


def set_credits(uid: int, n: int) -> int:
    try:
        con = db()
        con.execute("UPDATE users SET credits=? WHERE user_id=?", (max(0, int(n)), uid))
        con.commit()
        con.close()
    except Exception:
        pass
    return get_credits(uid)


def spend_credits(uid: int, n: int = 1) -> int:
    """Credits kam karta hai (0 se neeche nahi). Bacha hua returns."""
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
        row = cur.fetchone()
        cur_val = CREDITS_START if (row is None or row[0] is None) else int(row[0])
        new_val = max(0, cur_val - max(0, int(n)))
        if row is None:
            today = date.today().isoformat()
            now_str = datetime.now().isoformat(timespec="seconds")
            cur.execute(
                "INSERT INTO users(user_id, name, uses_today, last_date, joined_at, trial_date, trial_count, banned, credits) VALUES(?,?,0,?,?,?,0,0,?)",
                (uid, "", today, now_str, today, new_val))
        else:
            cur.execute("UPDATE users SET credits=? WHERE user_id=?", (new_val, uid))
        con.commit()
        con.close()
        return new_val
    except Exception:
        return get_credits(uid)


def add_credits(uid: int, n: int = 25) -> int:
    """Admin gift: credits badhao."""
    return set_credits(uid, get_credits(uid) + max(0, int(n)))


def credits_stats() -> dict:
    """Kitne users ke paas kitne credits bache — admin panel ke liye."""
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE COALESCE(credits, ?) > 0", (CREDITS_START,))
        with_credits = int(cur.fetchone()[0] or 0)
        cur.execute("SELECT COUNT(*) FROM users WHERE COALESCE(credits, ?) <= 0", (CREDITS_START,))
        out_of = int(cur.fetchone()[0] or 0)
        con.close()
        return {"with_credits": with_credits, "out_of_credits": out_of}
    except Exception:
        return {"with_credits": 0, "out_of_credits": 0}


def revoke_premium(uid: int) -> bool:
    try:
        con = db()
        con.execute("UPDATE users SET premium_until='' WHERE user_id=?", (uid,))
        con.commit()
        con.close()
        return True
    except Exception:
        return False
