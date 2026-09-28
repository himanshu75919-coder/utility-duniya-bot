#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility Duniya Bot v18
- 19 tools grid | 10 TTS voices | YT HD download | Link bypass | Admin panel
- Referral + UPI premium (screenshot direct ADMIN) + force-join + ban system
"""

import asyncio
import glob
import subprocess
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as cf
import io
import logging
import os
import random
import re
import sqlite3
import string
import tempfile
import time
import threading
from datetime import date, datetime, timedelta
from html import escape as hesc
from urllib.parse import quote, urlparse

from dotenv import load_dotenv

load_dotenv()

import qrcode
import requests
from PIL import Image, ImageEnhance
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "").strip()
FORCE_CHANNEL_LINK = os.getenv("FORCE_CHANNEL_LINK", "").strip()
UPI_ID = os.getenv("UPI_ID", "").strip()
UPI_NAME = os.getenv("UPI_NAME", "UtilityBot").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
FREE_LIMIT = int(os.getenv("FREE_LIMIT", "15") or 15)
REFER_NEED = int(os.getenv("REFER_NEED", "5") or 5)
TRIAL_LIMIT = 2
DB_PATH = os.getenv("DB_PATH", "botdata.db")
HTML = "HTML"
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 10) UtilityDuniyaBot/1.0"}
BAN_MSG = "🚫 Tum ban ho. Admin se contact karo."
BOT_VERSION = "v20"
START_TIME = datetime.now()

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("utility-bot")


def code(s) -> str:
    return f"<code>{hesc(str(s))}</code>"


def bar(frac: float, n: int = 8) -> str:
    frac = max(0.0, min(1.0, frac))
    f = int(round(frac * n))
    return "🟩" * f + "⬜" * (n - f)


def inr(n) -> str:
    s = str(int(round(float(n))))
    if len(s) <= 3:
        return s
    last3, rest = s[-3:], s[:-3]
    parts = []
    while len(rest) > 2:
        parts.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.append(rest)
    return ",".join(reversed(parts)) + "," + last3

# ---------------- SPEED CACHE (repeat sawal = instant jawab) ----------------
_CACHE = {}

def cache_get(key):
    try:
        exp, val = _CACHE.get(key, (0, None))
        if exp > time.time():
            return (True, val)
    except Exception:
        pass
    return (False, None)

def cache_put(key, val, ttl=21600):
    try:
        if len(_CACHE) > 500:
            _CACHE.clear()
        _CACHE[key] = (time.time() + ttl, val)
    except Exception:
        pass

# ---------------- DATABASE ----------------
def db():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            name TEXT DEFAULT '',
            uses_today INTEGER DEFAULT 0,
            last_date TEXT DEFAULT '',
            premium_until TEXT DEFAULT '',
            referred_by INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            joined_at TEXT DEFAULT ''
        )"""
    )
    for stmt in ("ALTER TABLE users ADD COLUMN trial_date TEXT DEFAULT ''",
                 "ALTER TABLE users ADD COLUMN trial_count INTEGER DEFAULT 0",
                 "ALTER TABLE users ADD COLUMN username TEXT DEFAULT ''",
                 "ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0"):
        try:
            con.execute(stmt)
        except Exception:
            pass
    try:
        con.commit()
    except Exception:
        pass
    return con


def get_user(uid: int, name: str = "") -> dict:
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    today = date.today().isoformat()
    if not row:
        cur.execute(
            "INSERT INTO users(user_id,name,uses_today,last_date,joined_at) VALUES(?,?,0,?,?)",
            (uid, (name or "")[:60], today, datetime.now().isoformat(timespec="seconds")),
        )
        con.commit()
        con.close()
        return {"user_id": uid, "name": name, "uses_today": 0, "last_date": today,
                "premium_until": "", "referred_by": 0, "referrals": 0,
                "trial_date": today, "trial_count": 0, "username": "", "banned": 0}
    cols = [d[0] for d in cur.description]
    u = dict(zip(cols, row))
    if u.get("last_date") != today:
        cur.execute("UPDATE users SET uses_today=0,last_date=? WHERE user_id=?", (today, uid))
        con.commit()
        u["uses_today"] = 0
        u["last_date"] = today
    if u.get("trial_date") != today:
        try:
            cur.execute("UPDATE users SET trial_count=0,trial_date=? WHERE user_id=?", (today, uid))
            con.commit()
        except Exception:
            pass
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
        cur.execute("SELECT user_id,name,username FROM users WHERE username=?", (username.lower(),))
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
        cur.execute("SELECT name,referrals FROM users WHERE referrals>0 ORDER BY referrals DESC LIMIT ?", (n,))
        rows = cur.fetchall()
        con.close()
        return rows
    except Exception:
        return []


def recent_users(n: int = 10):
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT user_id,name,username FROM users ORDER BY rowid DESC LIMIT ?", (n,))
        rows = cur.fetchall()
        con.close()
        return rows
    except Exception:
        return []


def premium_users():
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT user_id,name,premium_until FROM users WHERE premium_until > ? ORDER BY premium_until DESC",
                    (datetime.now().isoformat(timespec="seconds"),))
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
    con = db()
    con.execute("UPDATE users SET uses_today=uses_today+1 WHERE user_id=?", (uid,))
    con.commit()
    con.close()


def refund_use(uid: int):
    try:
        con = db()
        con.execute("UPDATE users SET uses_today=CASE WHEN uses_today>0 THEN uses_today-1 ELSE 0 END WHERE user_id=?", (uid,))
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


def add_trial(uid: int):
    con = db()
    con.execute("UPDATE users SET trial_count=trial_count+1 WHERE user_id=?", (uid,))
    con.commit()
    con.close()


def is_premium(u: dict) -> bool:
    try:
        return datetime.fromisoformat(u["premium_until"]) > datetime.now() if u["premium_until"] else False
    except Exception:
        return False


def premium_expiry(u: dict) -> str:
    try:
        return datetime.fromisoformat(u["premium_until"]).strftime("%d-%m-%Y") if u["premium_until"] else "-"
    except Exception:
        return "-"


def grant_premium(uid: int, days: int) -> str:
    con = db()
    cur = con.cursor()
    cur.execute("SELECT premium_until FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    base = datetime.now()
    if row and row[0]:
        try:
            d = datetime.fromisoformat(row[0])
            if d > base:
                base = d
        except Exception:
            pass
    new = (base + timedelta(days=days)).isoformat(timespec="seconds")
    cur.execute("UPDATE users SET premium_until=? WHERE user_id=?", (new, uid))
    con.commit()
    con.close()
    return new


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
    con = db()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users")
    ids = [r[0] for r in cur.fetchall()]
    con.close()
    return ids


def stats():
    con = db()
    cur = con.cursor()
    today = date.today().isoformat()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_date=?", (today,))
    active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE premium_until > ?", (datetime.now().isoformat(timespec="seconds"),))
    prem = cur.fetchone()[0]
    con.close()
    return total, active, prem

# ---------------- PURE HELPERS ----------------
def make_qr_bytes(text: str) -> io.BytesIO:
    qr = qrcode.QRCode(box_size=12, border=4, error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio


def gen_password(n: int) -> str:
    n = max(4, min(int(n), 64))
    alphabet = string.ascii_letters + string.digits + "@#$%&*"
    return "".join(random.choice(alphabet) for _ in range(n))


def name_passwords(name: str):
    name = re.sub(r"\s+", "", name.strip())[:20] or "User"
    leet = "".join({"a": "@", "A": "@", "e": "3", "E": "3", "i": "1", "I": "!",
                    "o": "0", "O": "0", "s": "5", "S": "$"}.get(c, c) for c in name)
    s1, s2, s3 = random.sample("@#$%&*", 3)
    d4 = "".join(random.choice(string.digits) for _ in range(4))
    d3 = "".join(random.choice(string.digits) for _ in range(3))
    d2 = "".join(random.choice(string.digits) for _ in range(2))
    p1 = f"{name}{s1}{d4}"
    p2 = f"{leet}{d2}{s2}"
    mid = (name[:3].upper() + d3 + name[-2:].lower() + s3) if len(name) >= 3 else f"{name}{s3}{d3}"
    return [p1, p2, mid]


def calc_emi(p: float, annual: float, months: int) -> float:
    r = annual / 12 / 100
    if r <= 0:
        return p / months
    f = (1 + r) ** months
    return p * r * f / (f - 1)


def emi_schedule(p: float, annual: float, n: int):
    r = annual / 12 / 100
    emi = calc_emi(p, annual, n)
    bal = p
    rows = []
    yP = yI = 0.0
    for m in range(1, n + 1):
        interest = bal * r if r > 0 else 0.0
        princ = emi - interest
        if princ > bal:
            princ, interest = bal, emi - bal
        bal -= princ
        yP += princ
        yI += interest
        if m % 12 == 0 or m == n:
            rows.append(((m + 11) // 12, yP, yI, max(bal, 0.0)))
            yP = yI = 0.0
    return emi, rows


def calc_age(dob: date):
    today = date.today()
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    try:
        bday = date(today.year, dob.month, dob.day)
    except ValueError:
        bday = date(today.year, 2, 28)
    if bday < today:
        try:
            bday = date(today.year + 1, dob.month, dob.day)
        except ValueError:
            bday = date(today.year + 1, 2, 28)
    return years, (bday - today).days, (today - dob).days


def zodiac(d: int, m: int) -> str:
    z = [((1, 20), (2, 18), "♒ Aquarius (Kumbh)"), ((2, 19), (3, 20), "♓ Pisces (Meen)"),
         ((3, 21), (4, 19), "♈ Aries (Mesh)"), ((4, 20), (5, 20), "♉ Taurus (Vrishabh)"),
         ((5, 21), (6, 20), "♊ Gemini (Mithun)"), ((6, 21), (7, 22), "♋ Cancer (Kark)"),
         ((7, 23), (8, 22), "♌ Leo (Simha)"), ((8, 23), (9, 22), "♍ Virgo (Kanya)"),
         ((9, 23), (10, 22), "♎ Libra (Tula)"), ((10, 23), (11, 21), "♏ Scorpio (Vrishchik)"),
         ((11, 22), (12, 21), "♐ Sagittarius (Dhanu)"), ((12, 22), (1, 19), "♑ Capricorn (Makar)")]
    for (sm, sd), (em, ed), name in z:
        if (m == sm and d >= sd) or (m == em and d <= ed):
            return name
    return "⭐"


def shorten_isgd(url: str):
    try:
        r = requests.get("https://is.gd/create.php", params={"format": "simple", "url": url},
                         timeout=10, headers=UA)
        s = r.text.strip()
        return s if s.startswith("http") else None
    except Exception:
        return None


def shorten_tiny(url: str):
    try:
        r = requests.get("https://tinyurl.com/api-create.php", params={"url": url},
                         timeout=10, headers=UA)
        s = r.text.strip()
        return s if s.startswith("http") else None
    except Exception:
        return None


YT_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})")


def yt_id(link: str):
    m = YT_RE.search(link or "")
    return m.group(1) if m else None


def yt_exists(vid: str) -> bool:
    try:
        r = requests.get("https://www.youtube.com/oembed",
                         params={"url": "https://www.youtube.com/watch?v=" + vid, "format": "json"},
                         timeout=8, headers=UA)
        return r.status_code != 404
    except Exception:
        return True


def fetch_yt_best(vid: str):
    def one(q):
        try:
            r = requests.get(f"https://img.youtube.com/vi/{vid}/{q}.jpg", timeout=10, headers=UA)
            if r.status_code != 200 or len(r.content) < 5000:
                return None
            img = Image.open(io.BytesIO(r.content))
            w, h = img.size
            if w <= 150:
                return None
            return (w * h, r.content, w, h, q)
        except Exception:
            return None
    with ThreadPoolExecutor(max_workers=5) as ex:
        res = [x for x in ex.map(one, ("maxresdefault", "sddefault", "hq720", "hqdefault", "mqdefault")) if x]
    return max(res)[1:] if res else None


def enhance_thumb(data: bytes):
    """720p se chhoti ho to HD enhance karo."""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    if w >= 1280:
        return data, w, h, False
    nh = int(h * 1280 / w)
    img = img.resize((1280, nh), Image.LANCZOS)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    bio = io.BytesIO()
    img.save(bio, format="JPEG", quality=92)
    return bio.getvalue(), 1280, nh, True


UPI_RE = re.compile(r"^[\w.\-]{2,256}@[a-zA-Z]{2,64}$")


def build_upi_link(pa: str, pn: str, amt=None, note: str = "") -> str:
    link = f"upi://pay?pa={pa}&pn={quote(pn or 'User')}&cu=INR"
    if amt:
        link += f"&am={amt:.2f}"
    if note:
        link += f"&tn={quote(note[:40])}"
    return link


def si_result(p: float, r: float, t: float):
    i = p * r * t / 100
    return i, p + i


def ci_result(p: float, r: float, t: float, f: int):
    a = p * (1 + r / (100 * f)) ** (f * t)
    return a - p, a

# ---------------- RTO DATA ----------------
RTO_STATE = {"AN": "Andaman & Nicobar", "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh",
    "AS": "Assam", "BR": "Bihar", "CG": "Chhattisgarh", "CH": "Chandigarh", "DD": "Daman & Diu",
    "DL": "Delhi", "DN": "Dadra & Nagar Haveli", "GA": "Goa", "GJ": "Gujarat", "HP": "Himachal Pradesh",
    "HR": "Haryana", "JH": "Jharkhand", "JK": "Jammu & Kashmir", "KA": "Karnataka", "KL": "Kerala",
    "LA": "Ladakh", "LD": "Lakshadweep", "MH": "Maharashtra", "ML": "Meghalaya", "MN": "Manipur",
    "MP": "Madhya Pradesh", "MZ": "Mizoram", "NL": "Nagaland", "OD": "Odisha", "PB": "Punjab",
    "PY": "Puducherry", "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TR": "Tripura",
    "TS": "Telangana", "UK": "Uttarakhand", "UP": "Uttar Pradesh", "WB": "West Bengal"}
RTO_OFFICE = {
    "JH01": "Ranchi", "JH02": "Dhanbad", "JH05": "Jamshedpur (E. Singhbhum)",
    "BR01": "Patna",
    "UP14": "Ghaziabad", "UP16": "Noida (G.B. Nagar)", "UP32": "Lucknow", "UP65": "Varanasi", "UP78": "Kanpur",
    "HR26": "Gurgaon", "HR51": "Faridabad",
    "PB10": "Ludhiana", "PB65": "Mohali (SAS Nagar)",
    "RJ14": "Jaipur", "RJ19": "Jodhpur",
    "GJ01": "Ahmedabad", "GJ05": "Surat", "GJ06": "Vadodara",
    "MH01": "Mumbai South", "MH02": "Mumbai West", "MH04": "Thane", "MH12": "Pune",
    "MH14": "Pimpri-Chinchwad", "MH15": "Nashik", "MH20": "Chh. Sambhajinagar", "MH31": "Nagpur",
    "MP04": "Bhopal", "MP09": "Indore", "MP13": "Ujjain", "MP20": "Jabalpur",
    "CG04": "Raipur", "CG10": "Bilaspur",
    "OD02": "Bhubaneswar",
    "WB02": "Kolkata (Alipore)",
    "AS01": "Guwahati (Kamrup)",
    "UK07": "Dehradun", "UK08": "Haridwar",
    "JK01": "Srinagar", "JK02": "Jammu",
    "KA01": "Bengaluru Central", "KA05": "Bengaluru South", "KA09": "Mysuru",
    "TN09": "Chennai West",
    "KL01": "Thiruvananthapuram", "KL07": "Kochi (Ernakulam)",
    "TS09": "Hyderabad Central",
    "AP31": "Visakhapatnam",
    "GA01": "Panaji (North Goa)",
    "PY01": "Puducherry", "CH01": "Chandigarh",
    "SK01": "Gangtok", "ML05": "Shillong", "MN01": "Imphal", "TR01": "Agartala",
    "MZ01": "Aizawl", "NL01": "Kohima", "AN01": "Port Blair", "LA01": "Leh", "LA02": "Kargil",
}
VEH_RE = re.compile(r"^([A-Z]{2})\s?\-?([0-9]{1,2})\s?\-?([A-Z]{1,3})\s?\-?([0-9]{4})$")


def parse_vehicle(text: str):
    t = (text or "").upper().replace(" ", "").replace("-", "")
    m = VEH_RE.match(t) or VEH_RE.match((text or "").upper().strip())
    if not m:
        return None
    st, rto, series, num = m.group(1), m.group(2).zfill(2), m.group(3), m.group(4)
    return {"number": f"{st}-{rto} {series} {num}", "state": RTO_STATE.get(st),
            "rto": RTO_OFFICE.get(f"{st}{rto}"), "code": f"{st}{rto}"}

# ---------------- LINK CHECK ----------------
SHORTENERS = {"bit.ly", "tinyurl.com", "is.gd", "t.co", "goo.gl", "cutt.ly", "shorturl.at",
              "rebrand.ly", "s.id", "shorte.st", "adf.ly", "bc.vc", "tiny.cc", "ow.ly"}
RISKY_TLDS = {"tk", "ml", "ga", "cf", "gq", "top", "xyz", "buzz", "click", "link", "loan", "win"}
SUS_WORDS = ("login", "verify", "verification", "secure", "account", "update", "kyc",
             "bank", "free", "bonus", "winner", "prize", "lottery", "crypto", "wallet")


def link_check(url: str):
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    _hit, _val = cache_get(("lc", url))
    if _hit:
        return _val
    findings = []
    bad = warn = 0
    chain = []
    final = url
    try:
        r = requests.get(url, allow_redirects=True, timeout=8, headers=UA)
        final = r.url
        chain = [(h.status_code, h.url) for h in r.history[:5]] + [(r.status_code, r.url)]
        if len(r.history) >= 3:
            findings.append(("warn", f"🔀 {len(r.history)} redirects — short link ke peeche kuch chhupa ho sakta hai"))
            warn += 1
    except Exception:
        findings.append(("warn", "⚠️ Link khul nahi raha / timeout — saavdhaan raho"))
        warn += 1
    try:
        p = urlparse(final)
        host = (p.hostname or "").lower()
        if p.scheme == "http":
            findings.append(("warn", "🔓 http (secure https nahi) — password mat dalo")); warn += 1
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
            findings.append(("bad", "🚨 IP address wala link — aksar phishing hota hai")); bad += 1
        if "xn--" in host:
            findings.append(("bad", "🚨 Nqli (look-alike) domain — phishing ho sakta hai")); bad += 1
        if "@" in final.split("://", 1)[-1].split("/")[0]:
            findings.append(("bad", "🚨 @ wala link — asli site chhupai gayi hai")); bad += 1
        if host in SHORTENERS:
            findings.append(("warn", "🔗 Short link hai — asli pata upar Final URL me dekho")); warn += 1
        if host.split(".")[-1] in RISKY_TLDS:
            findings.append(("warn", "⚠️ Muft/sasti wali domain — fraud me zyada use hoti hai")); warn += 1
        if len(final) > 150:
            findings.append(("warn", "📏 Bahut lamba link — dhyaan se dekho")); warn += 1
        if len(host.split(".")) > 4:
            findings.append(("warn", "🧅 Bahut saare sub-domains — nakli site ho sakti hai")); warn += 1
        low = final.lower()
        if any(w in low for w in SUS_WORDS):
            findings.append(("warn", "🎣 Login/bonus/free jaisa shabd — lalach wale fraud se bacho")); warn += 1
        if p.port and p.port not in (80, 443):
            findings.append(("warn", f"🔌 Ajeeb port (:{p.port})")); warn += 1
    except Exception:
        findings.append(("warn", "⚠️ Link samajh nahi aaya"))
        warn += 1
    if bad:
        verdict = "🔴 RISKY — mat kholo, paise/password bilkul mat do!"
    elif warn >= 2:
        verdict = "🟡 SUSPICIOUS — saavdhaan! bina verify click mat karo"
    elif warn == 1:
        verdict = "🟡 Thoda saavdhaan raho"
    else:
        verdict = "🟢 Looks SAFE (basic check me saaf)"
    _out = {"final": final, "chain": chain, "findings": findings, "verdict": verdict}
    cache_put(("lc", url), _out)
    return _out

# ---------------- LINK BYPASS (earn links -> original) ----------------
BYPASS_DOMAINS = {"arolinks.com", "arlinks.in", "vplinks.in", "vplinks.com", "gplinks.com",
    "gplinks.in", "earnlink.io", "earnlink.com", "droplink.co", "ouo.io", "ouo.press",
    "linkvertise.com", "exlink.io", "tnlink.in", "rocklinks.net", "dulink.in",
    "mdiskshortener.link", "mdiskshortener.com", "indianshortener.com", "blinks.in",
    "shrinkearn.com", "shrinkme.io", "clk.sh", "aylink.co", "payskip.org"}


def bypass_link(url: str):
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    _hit, _val = cache_get(("bp", url))
    if _hit:
        return _val
    chain = []
    try:
        r = requests.get(url, headers=UA, timeout=12, allow_redirects=True)
        chain = [h.url for h in r.history] + [r.url]
        final = r.url
    except Exception as e:
        return ("ERR", f"⛔ Link khul nahi raha.\n({str(e)[:100]})", [])
    host = (urlparse(final).hostname or "").lower().lstrip("www.")
    if host not in BYPASS_DOMAINS and final.rstrip("/") != url.rstrip("/"):
        _r = ("OK", final, chain)
        cache_put(("bp", url), _r)
        return _r
    # page ke andar asli link dhoondo (meta-refresh / JS / get-link button)
    try:
        html = r.text or ""
        cands = []
        m = re.search(r"<meta[^>]+http-equiv=[\"']?refresh[\"']?[^>]+url=([\"']?)([^\"'>\s]+)", html, re.I)
        if m:
            cands.append(m.group(2))
        for m2 in re.finditer(r"window\.location(?:\.href)?\s*=\s*[\"']([^\"']+)[\"']", html):
            cands.append(m2.group(1))
        for m3 in re.finditer(r"<a[^>]*(?:get-link|getlink|continue|proceed|download-link)[^>]*href=[\"']([^\"']+)[\"']", html, re.I):
            cands.append(m3.group(1))
        for c in cands:
            if c.startswith("http") and (urlparse(c).hostname or "").lower().lstrip("www.") not in BYPASS_DOMAINS:
                _r = ("OK", c, chain + [c])
                cache_put(("bp", url), _r)
                return _r
    except Exception:
        pass
    return ("WAIT", final, chain)

# ---------------- NETWORK APIS ----------------
def ifsc_lookup(code: str):
    _hit, _val = cache_get(("ifsc", code))
    if _hit:
        return _val
    r = requests.get(f"https://ifsc.razorpay.com/{code}", timeout=12, headers=UA)
    if r.status_code != 200:
        return None
    try:
        j = r.json()
    except Exception:
        return None
    cache_put(("ifsc", code), j)
    return j


def pin_lookup(pin: str):
    _hit, _val = cache_get(("pin", pin))
    if _hit:
        return _val
    for _ in range(3):
        try:
            r = requests.get(f"https://api.postalpincode.in/pincode/{pin}", timeout=15, headers=UA)
            j = r.json()
            if isinstance(j, list) and j and j[0].get("Status") == "Success":
                cache_put(("pin", pin), j[0])
                return j[0]
            return None
        except Exception:
            continue
    return None

_IG_LOCK = threading.Lock()
_IG_LAST = [0.0]


def _ig_fetch(u: str):
    with _IG_LOCK:
        wait = 8 - (time.time() - _IG_LAST[0])
        if wait > 0:
            time.sleep(wait)
        try:
            r = requests.get("https://i.instagram.com/api/v1/users/web_profile_info/",
                             params={"username": u},
                             headers={"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
                                      "x-ig-app-id": "936619743392459"},
                             timeout=12)
            return (r.status_code, r)
        finally:
            _IG_LAST[0] = time.time()


def restore_md_marks(msg) -> str:
    """Telegram '__x__' ko underline bana ke markers KHA jata hai.
    Single-token username me underline->'__' , italic->'_' wapas lagao."""
    try:
        t = msg.text or ""
        ents = getattr(msg, "entities", None) or []
        if not t or " " in t.strip() or "\n" in t:
            return t
        spans = []
        for e in ents:
            try:
                ty = getattr(e, "type", "")
                mk = "__" if ty == "underline" else ("_" if ty == "italic" else None)
                if not mk:
                    continue
                o, l = int(e.offset), int(e.length)
                if o < 0 or l <= 0 or o + l > len(t):
                    continue
                spans.append((o, o + l, mk))
            except Exception:
                continue
        for a, b, mk in sorted(spans, reverse=True):
            t = t[:a] + mk + t[a:b] + mk + t[b:]
        return t
    except Exception:
        try:
            return msg.text or ""
        except Exception:
            return ""


def insta_lookup(username: str):
    _parts = ((username or "").strip().lstrip("@").split() or [""])
    u = _parts[0][:30]
    if not u or not all(ch.isalnum() or ch in "._" for ch in u):
        return None
    _hit, _val = cache_get(("ig", u.lower()))
    if _hit:
        return _val
    for _att in (1, 2):
        try:
            _code, _r = _ig_fetch(u)
        except Exception:
            return None
        if _code == 429:
            if _att == 1:
                time.sleep(8)
                continue
            return "RATELIMIT"
        if _code != 200:
            return None
        try:
            usr = _r.json().get("data", {}).get("user") or {}
        except Exception:
            return None
        if not usr.get("username"):
            return None
        d = {"username": usr.get("username"), "name": usr.get("full_name") or "-",
             "uid": str(usr.get("id") or "-"), "private": bool(usr.get("is_private")),
             "verified": bool(usr.get("is_verified")),
             "followers": (usr.get("edge_followed_by") or {}).get("count", 0),
             "following": (usr.get("edge_follow") or {}).get("count", 0),
             "posts": (usr.get("edge_owner_to_timeline_media") or {}).get("count", 0),
             "bio": (usr.get("biography") or "").strip(),
             "pic": usr.get("profile_pic_url_hd") or usr.get("profile_pic_url") or ""}
        cache_put(("ig", u.lower()), d, ttl=3600)
        return d
    return "RATELIMIT"


# ---------------- IMAGE TOOLS ----------------
def normalize_page(img: Image.Image) -> bytes:
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bands = img.getbands()
        bg.paste(img.convert("RGB") if img.mode == "P" else img,
                 mask=img.split()[-1] if "A" in bands else None)
        img = bg
    else:
        img = img.convert("RGB")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def pages_to_pdf(pages: list) -> bytes:
    try:
        import img2pdf
        return img2pdf.convert(pages)
    except Exception as e:
        log.warning("img2pdf fail, PIL fallback: %s", e)
        imgs = [Image.open(io.BytesIO(p)).convert("RGB") for p in pages]
        bio = io.BytesIO()
        imgs[0].save(bio, format="PDF", save_all=True, append_images=imgs[1:], resolution=300.0)
        return bio.getvalue()


def passport_make(data: bytes):
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    target = 7 / 9
    if w / h > target:
        nw = int(h * target)
        x = (w - nw) // 2
        img = img.crop((x, 0, x + nw, h))
    else:
        nh = int(w / target)
        y = max(0, (h - nh) // 3)
        img = img.crop((0, y, w, min(h, y + nh)))
    single = img.resize((700, 900), Image.LANCZOS)
    single = ImageEnhance.Contrast(single).enhance(1.05)
    single = ImageEnhance.Sharpness(single).enhance(1.3)
    sheet = Image.new("RGB", (1200, 1800), "white")
    tw, th = 360, 463
    thumb = single.resize((tw, th), Image.LANCZOS)
    for r in range(3):
        for c in range(3):
            sheet.paste(thumb, (30 + c * (tw + 15), 60 + r * (th + 15)))
    b1, b2 = io.BytesIO(), io.BytesIO()
    single.save(b1, format="JPEG", quality=97, subsampling=0)
    sheet.save(b2, format="JPEG", quality=97, subsampling=0)
    return b1.getvalue(), b2.getvalue()

# ---------------- TTS (10 voices) ----------------
TTS_VOICES = [
    ("swara", "👩 Hindi Female", "hi-IN-SwaraNeural", "+0%", "+0Hz"),
    ("madhur", "👨 Hindi Male", "hi-IN-MadhurNeural", "+0%", "+0Hz"),
    ("softf", "🌸 Soft Female", "hi-IN-SwaraNeural", "-12%", "-8Hz"),
    ("deepm", "🎙️ Deep Male", "hi-IN-MadhurNeural", "-5%", "-25Hz"),
    ("oldf", "👵 Old Female", "hi-IN-SwaraNeural", "-25%", "-30Hz"),
    ("oldm", "👴 Old Male", "hi-IN-MadhurNeural", "-25%", "-35Hz"),
    ("babyg", "👧 Baby Girl", "hi-IN-SwaraNeural", "+10%", "+120Hz"),
    ("babyb", "👦 Baby Boy", "hi-IN-MadhurNeural", "+10%", "+100Hz"),
    ("neerja", "👩 English Female", "en-IN-NeerjaNeural", "+0%", "+0Hz"),
    ("prabhat", "👨 English Male", "en-IN-PrabhatNeural", "+0%", "+0Hz"),
]


async def tts_make(text: str, voice: str, rate: str, pitch: str, outpath: str) -> bool:
    try:
        import edge_tts
        await edge_tts.Communicate(text[:400], voice, rate=rate, pitch=pitch).save(outpath)
        return True
    except Exception as e:
        log.warning("edge tts fail: %s", e)
    try:
        from gtts import gTTS
        lang = "hi" if re.search(r"[\u0900-\u097F]", text) else "en"
        await asyncio.to_thread(gTTS(text[:400], lang=lang).save, outpath)
        return True
    except Exception as e:
        log.warning("gtts fail: %s", e)
        return False

# ---------------- YT DOWNLOAD ----------------
YT_CLIENTS = ["web", "web_embedded", "android", "ios", "mweb", "tv"]
YTDL_BASE = {"quiet": True, "noplaylist": True, "socket_timeout": 25,
             "retries": 3, "fragment_retries": 3,
             "extractor_args": {"youtube": {"player_client": YT_CLIENTS}}}
# NOTE: impersonate REMOVED (v9 test: curl_cffi breaks YT requests). Clients+cookies only.


COOKIE_FILE = "/tmp/yt_cookies.txt"


def normalize_cookies(raw: bytes) -> bytes:
    try:
        txt = (raw or b"").decode("utf-8", "ignore")
    except Exception:
        return raw
    if not txt.strip() or txt.lstrip()[:1] == "[":
        return raw
    out = []
    for ln in txt.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#") and "HttpOnly_" not in s:
            out.append(ln)
            continue
        if "\t" in ln:
            out.append(ln)
            continue
        parts = s.split()
        if len(parts) >= 7 and ("." in parts[0] or parts[0].startswith("#HttpOnly_")):
            out.append("\t".join(parts[:6] + [" ".join(parts[6:])]))
        else:
            out.append(ln)
    return ("\n".join(out) + "\n").encode("utf-8")


def cookies_jar_count(path: str) -> int:
    try:
        from http.cookiejar import MozillaCookieJar
        j = MozillaCookieJar(path)
        j.load(ignore_discard=True, ignore_expires=True)
        return len(list(j))
    except Exception:
        return -1


def cookies_json_to_netscape(raw: bytes):
    import json as _js
    try:
        arr = _js.loads((raw or b"").decode("utf-8", "ignore"))
    except Exception:
        return None
    if not isinstance(arr, list):
        return None
    out = ["# Netscape HTTP Cookie File"]
    for c in arr:
        try:
            if not isinstance(c, dict):
                continue
            dom = str(c.get("domain", "") or "")
            if not dom:
                continue
            fl = "TRUE" if dom.startswith(".") else "FALSE"
            ph = str(c.get("path", "/") or "/")
            sc = "TRUE" if c.get("secure") else "FALSE"
            try:
                ex = int(float(c.get("expirationDate") or 0))
            except Exception:
                ex = 0
            nm = str(c.get("name", "") or "")
            vl = str(c.get("value", "") or "")
            if c.get("httpOnly") and not nm.startswith("#HttpOnly_"):
                nm = "#HttpOnly_" + nm
            out.append("\t".join([dom, fl, ph, sc, str(ex), nm, vl]))
        except Exception:
            continue
    if len(out) < 2:
        return None
    return ("\n".join(out) + "\n").encode("utf-8")


def _yt_race_one(url: str, client: str):
    import yt_dlp
    try:
        o = {"quiet": True, "noplaylist": True, "socket_timeout": 15,
             "retries": 1, "fragment_retries": 1}
        if client:
            o["extractor_args"] = {"youtube": {"player_client": [client]}}
        if os.path.exists(COOKIE_FILE):
            o["cookiefile"] = COOKIE_FILE
        with yt_dlp.YoutubeDL(o) as y:
            info = y.extract_info(url, download=False)
        return (info, client, "") if info else (None, client, "noinfo")
    except Exception as e:
        return (None, client, str(e)[:200])


def yt_race_info(url: str):
    """7 clients ek saath race - jo pehle info laaye wahi winner."""
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(_yt_race_one, url, c) for c in YT_CLIENTS]
        futs.append(ex.submit(_yt_race_one, url, None))
        _first_err = ""
        try:
            for f in cf.as_completed(futs, timeout=75):
                try:
                    r = f.result()
                except Exception:
                    continue
                if r and r[0]:
                    for g in futs:
                        g.cancel()
                    return r
                if r and len(r) > 2 and r[2] and not _first_err:
                    _first_err = r[2]
        except Exception:
            pass
    return (None, None, _first_err)


def _ffmpeg_exe():
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        return p if p and os.path.exists(p) else None
    except Exception:
        return None


def ytdl_download(url: str):
    import yt_dlp
    tmpd = tempfile.mkdtemp(prefix="ytdl_")
    try:
        info0, _win, _err = yt_race_info(url)
        if not info0:
            _e = (_err or "").lower()
            _bw = ("bot" in _e or "sign in" in _e or "reload" in _e or "format is not available" in _e or "only images" in _e or "403" in _e or "429" in _e or "forbidden" in _e or "rate-limit" in _e or "login" in _e or "confirm" in _e)
            if _bw:
                if os.path.exists(COOKIE_FILE):
                    return ("ERR", "\U0001F36A Cookies LAGI hain, phir bhi YouTube ne server-IP ko ROKA hai (bot protection). 10-15 min baad ya dusri video try karo.", None)
                return ("ERR", "YouTube ne server ko bot samajh ke ROKA hai. FIX: Admin /setcookies likhke YouTube login cookies lagaye - phir turant chalega!", None)
            raise RuntimeError("ytinfo")
    except Exception:
        return ("ERR", "⛔ Video info nahi mili. Link private/delete/blocked ho sakta hai. 🙏\nThodi der baad phir try karo, ya dusri video bhejo.", None)
    dur = info0.get("duration") or 0
    if dur > 600:
        return ("ERR", f"⏳ Video {dur // 60} min ki hai. Max 10 min tak download hoga (Telegram limit). Chhoti video bhejo! 🙏", None)
    opts = dict(YTDL_BASE)
    opts.update({"format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best",
                 "merge_output_format": "mp4",
                 "outtmpl": os.path.join(tmpd, "%(id)s.%(ext)s")})
    _ff = _ffmpeg_exe()
    if _ff:
        opts["ffmpeg_location"] = _ff
    try:
        if _win:
            opts["extractor_args"] = {"youtube": {"player_client": [_win] + [c for c in YT_CLIENTS if c != _win]}}
    except Exception:
        pass
    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            info = y.extract_info(url, download=True)
    except Exception:
        return ("ERR", "⛔ Download fail — YouTube ne is waqt block kiya hai (bot protection). 🙏\n\n✅ 10-15 min baad try karo\n✅ Ya dusri video/Shorts link bhejo", None)
    files = [f for f in glob.glob(os.path.join(tmpd, "*")) if os.path.isfile(f) and not f.endswith(".part")]
    if not files:
        return ("ERR", "⛔ File nahi bani. Dusra link try karo. 🙏", None)
    path = max(files, key=os.path.getsize)
    if os.path.getsize(path) > 48 * 1024 * 1024:
        try:
            os.remove(path)
        except Exception:
            pass
        return ("ERR", "📦 File 48MB se badi hai (Telegram limit). Chhoti video try karo! 🙏", None)
    return ("OK", info, path)

# ---------------- UI ----------------
BACK = InlineKeyboardMarkup([[InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")]])

KB_BTNS = [
    ["📷 QR Code", "🔐 Password"],
    ["🖼️ Image→PDF", "🔗 URL Short"],
    ["🎬 YT Thumbnail", "⬇️ YT Download"],
    ["🧮 EMI Calc", "🎂 Age Calculator"],
    ["💰 UPI QR Generator", "🆔 ID Finder"],
    ["🔊 Text to Speech", "🏦 IFSC Info"],
    ["📮 Pincode Info", "🪪 Passport Photo"],
    ["🔍 Link Check", "🔓 Link Bypass"],
    ["📈 Interest Calc", "🚗 RTO Vehicle Info"],
    ["💎 Premium", "🎁 Refer & Earn"],
    ["📸 Insta Info", "👤 My Account"],
    ["📱 Number Info"],
]


def main_keyboard(admin: bool = False):
    rows = [row[:] for row in KB_BTNS]
    if admin:
        rows.append(["🛠️ Admin Panel"])
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t) for t in row] for row in rows],
        resize_keyboard=True,
        input_field_placeholder="Grid dabao, tool chuno 👇",
    )


def kb_for(uid: int):
    return main_keyboard(admin=is_admin(uid))


BTN_MODE = {
    "📷 QR Code": "qr", "🖼️ Image→PDF": "pdf",
    "🔗 URL Short": "short", "🎬 YT Thumbnail": "yt",
    "⬇️ YT Download": "ytdl", "🧮 EMI Calc": "emi",
    "🎂 Age Calculator": "age", "💰 UPI QR Generator": "upi",
    "🆔 ID Finder": "idfind", "🏦 IFSC Info": "ifsc",
    "📮 Pincode Info": "pin", "🪪 Passport Photo": "pp",
    "🔍 Link Check": "linkcheck", "🔓 Link Bypass": "linkbypass",
    "🚗 RTO Vehicle Info": "rto",
    "📸 Insta Info": "insta",
    "📱 Number Info": "numinfo",
}

PROMPTS = {
    "qr": "📷 <b>QR Code Generator</b>\n\nKoi bhi TEXT ya LINK bhejo (HD QR banega):",
    "pdf": "🖼️ <b>Image→PDF (Full Quality, Multi-page!)</b>\n\n📸 PHOTO bhejo — ek-ek karke <b>10 tak</b> bhej sakte ho, phir ✅ dabao.\n\n💎 <b>Best quality tip:</b> photo ko 📎 attachment se <b>FILE/DOCUMENT</b> bana ke bhejo (4K/8K safe!)",
    "short": "🔗 <b>URL Shortener (2 links!)</b>\n\nLamba LINK bhejo — 2 short links + QR milega:",
    "yt": "🎬 <b>YT Thumbnail (720p+ HD)</b>\n\nYouTube video ka LINK bhejo:",
    "ytdl": "⬇️ <b>YT Video/Shorts Download (HD)</b> 💎 <i>roz 2 FREE trial</i>\n\nYouTube/Shorts ka LINK bhejo (max 10 min, 48MB):",
    "emi": "🧮 <b>EMI Calculator (Advanced)</b>\n\nLoan amount (₹) bhejo:\n(jaise: 100000)",
    "age": "🎂 <b>Age Calculator</b>\n\nApni birth date bhejo (DD-MM-YYYY):\n(jaise: 15-08-2005)",
    "upi": "💰 <b>UPI QR Generator</b> 💎 <i>roz 2 FREE trial</i>\n\nApni UPI ID bhejo:\n(jaise: name@okhdfc)",
    "idfind": ("🆔 <b>ID Finder</b>\n\n3 tareeke:\n1️⃣ Kisi ka koi <b>message FORWARD</b> karo → uski ID (100% ✅)\n2️⃣ <b>@username</b> bhejo → agar wo bot user hai to ID\n3️⃣ <b>me</b> likho → tumhari apni ID"),
    "ifsc": "🏦 <b>IFSC Details</b>\n\nIFSC code bhejo:\n(jaise: HDFC0001234)",
    "pin": "📮 <b>Pincode Details</b>\n\n6-digit pincode bhejo:\n(jaise: 834001)",
    "pp": "🪪 <b>Passport Photo Maker (HD)</b>\n\n📸 Apni PHOTO bhejo (chehra beech me, seedhi photo).\nSingle HD photo + print sheet (9 copies) milegi! 🖨️",
    "linkcheck": "🔍 <b>Link Checker</b>\n\nKoi bhi LINK bhejo — safe hai ya fraud, check karunga:",
    "linkbypass": "🔓 <b>Link Bypass</b>\n\narolinks / vplinks / gplinks jaisa EARN LINK bhejo — asli original link nikalunga:\n\n<i>Note: timer/JS wale kuch links browser me kholne padenge.</i>",
    "insta": ("📸 <b>Insta Info</b>" + chr(10) + chr(10) + "Insta username bhejo (bina @):" + chr(10) + "(jaise: virat.kohli)"),
    "numinfo": "📱 <b>Number Info (Circle + Operator)</b>\n\n10-digit mobile number bhejo:\n(jaise: 9876543210)",
    "rto": "🚗 <b>RTO Vehicle Info</b>\n\nGaadi number bhejo:\n(jaise: JH01AB1234)",
}

WELCOME = (
    "👋 Namaste! Main hoon <b>Utility Duniya Bot</b> 🌟\n\n"
    "🧰 <b>19 powerful tools</b>, bilkul FREE:\n"
    "📷 QR • 🔐 Password • 🖼️ PDF • 🔗 Short\n"
    "🎬 YT • ⬇️ Download • 🧮 EMI • 🎂 Age\n"
    "💰 UPI QR • 🆔 ID Finder • 🔊 10 Voices • 🏦 IFSC\n"
    "📮 Pincode • 🪪 Passport • 🔍 Link Check\n"
    "🔓 Bypass • 📈 Interest • 🚗 RTO • 📱 Number\n\n"
    f"🆓 Roz {FREE_LIMIT} FREE uses + Premium tools ke {TRIAL_LIMIT} trials\n"
    f"🎁 {REFER_NEED} doston ko refer karo = 30 din Premium FREE\n"
    "💎 ya sirf ₹49 me Premium lo\n\n"
    "📲 Neeche grid icon (▦) dabao — saare tools khulenge!\n"
    "👆 Har result <b>tap karke copy</b> hota hai!"
)

LIMIT_MSG = (
    "⏳ Aaj ka FREE limit khatam! (roz {lim} uses)\n\n"
    "Unlimited paane ke 2 tareeke:\n"
    f"🎁 {REFER_NEED} doston ko refer karo = 30 din FREE Premium\n"
    "💎 ya ₹49 me Premium lo\n\n"
    "Kal limit apne aap reset ho jayegi. 👍"
)

TRIAL_MSG = (
    "🔒 {tool} Premium tool hai!\n\n"
    f"Roz ke {TRIAL_LIMIT} FREE trials khatam. Unlimited pao:\n"
    "💎 ₹49 me Premium lo\n"
    f"🎁 ya {REFER_NEED} refer = 30 din FREE"
)

# ---------------- GUARDS ----------------
async def ensure_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not FORCE_CHANNEL or not FORCE_CHANNEL_LINK:
        return True
    uid = update.effective_user.id
    try:
        m = await context.bot.get_chat_member(FORCE_CHANNEL, uid)
        if m.status in ("member", "administrator", "creator"):
            return True
    except Exception as e:
        log.warning("force-join check fail-open: %s", e)
        return True
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel Join Karo", url=FORCE_CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Join Kar Liya", callback_data="joincheck")],
    ])
    msg = ("🔒 Pehle hamara channel join karo, phir saare tools FREE use karo!\n\n"
           "Join karke neeche ✅ dabao 👇")
    if update.callback_query:
        try:
            await update.callback_query.answer("Pehle channel join karo! 🔒", show_alert=True)
        except Exception:
            pass
        await update.callback_query.message.reply_text(msg, reply_markup=kb)
    else:
        await update.message.reply_text(msg, reply_markup=kb)
    return False


async def act(context: ContextTypes.DEFAULT_TYPE, chat_id: int, action: str):
    try:
        await context.bot.send_chat_action(chat_id, action)
    except Exception:
        pass


async def _send_limit_msg(update: Update, text: str):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Refer & Earn", callback_data="ref")],
        [InlineKeyboardButton("💎 Premium (₹49)", callback_data="prem")],
    ])
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)


async def use_or_block(uid: int, update: Update) -> bool:
    if is_banned(uid):
        if update.callback_query:
            await update.callback_query.message.reply_text(BAN_MSG)
        else:
            await update.message.reply_text(BAN_MSG)
        return False
    u = get_user(uid)
    if is_premium(u):
        return True
    if is_admin(uid):
        return True
    if u["uses_today"] < FREE_LIMIT:
        add_use(uid)
        return True
    await _send_limit_msg(update, LIMIT_MSG.format(lim=FREE_LIMIT))
    return False


async def trial_or_block(uid: int, update: Update, tool: str) -> bool:
    if is_banned(uid):
        if update.callback_query:
            await update.callback_query.message.reply_text(BAN_MSG)
        else:
            await update.message.reply_text(BAN_MSG)
        return False
    u = get_user(uid)
    if is_premium(u):
        return True
    if is_admin(uid):
        return True
    left = TRIAL_LIMIT - (u.get("trial_count") or 0)
    if left > 0:
        add_trial(uid)
        note = f"🎁 FREE Trial use ho gaya ({left - 1} bache aaj). Unlimited ke liye Premium lo! 💎"
        if update.callback_query:
            await update.callback_query.message.reply_text(note)
        else:
            await update.message.reply_text(note)
        return True
    await _send_limit_msg(update, TRIAL_MSG.format(tool=tool))
    return False

# ---------------- COMMANDS ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, user.first_name or "")
    save_username(user.id, user.username or "")
    if is_banned(user.id):
        await update.message.reply_text(BAN_MSG)
        return
    if context.args and context.args[0].startswith("ref_"):
        try:
            ref_id = int(context.args[0].split("_")[1])
            count = add_referral(user.id, ref_id)
            if count:
                await update.message.reply_text(
                    f"🎉 Welcome! Tum refer hokar aaye ho. Roz {FREE_LIMIT} FREE uses milenge!",
                    reply_markup=kb_for(user.id))
                try:
                    if count % REFER_NEED == 0:
                        grant_premium(ref_id, 30)
                        await context.bot.send_message(
                            ref_id, f"🎉 Badhai! {count} referrals pure! Tumhe 30 din ka Premium FREE mil gaya 💎")
                    else:
                        await context.bot.send_message(
                            ref_id, f"🎁 1 naya referral! Total: {count}/{REFER_NEED}. {REFER_NEED - (count % REFER_NEED)} aur = 30 din Premium FREE!")
                except Exception:
                    pass
        except Exception:
            pass
    if not await ensure_joined(update, context):
        return
    await update.message.reply_text(WELCOME, reply_markup=kb_for(user.id), parse_mode=HTML)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_joined(update, context):
        return
    await update.message.reply_text("⌨️ Neeche grid me saare tools hain — koi dabao 👇",
                                    reply_markup=kb_for(update.effective_user.id))


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for k in ("mode", "pdf_pages", "upi_id", "upi_name", "upi_amt", "emi_p", "emi_r",
              "int_type", "int_p", "int_r", "int_t", "tts_voice", "tts_name", "tts_rate",
              "tts_pitch", "qr_pending", "setcookies"):
        context.user_data.pop(k, None)
    await update.message.reply_text("❌ Cancel ho gaya. Grid se dobara chuno.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ <b>HELP</b>\n\n📲 Neeche grid icon (▦) dabao = saare tools khulenge!\n"
        "Koi tool dabao, bot jo mange wo bhejo. ✅\n\n"
        "👆 <b>Har result tap karke copy hota hai!</b>\n\n"
        "/menu - tools grid\n/premium - premium plans\n/refer - refer & earn\n"
        "/account - mera account\n/cancel - cancel\n\n"
        f"Roz {FREE_LIMIT} FREE uses + {TRIAL_LIMIT} premium trials. /refer se unlimited FREE pao! 🎁",
        parse_mode=HTML)


async def cmd_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    prem = is_premium(u)
    badge = "💎 <b>PREMIUM</b> ✨" if prem else "🆓 <b>FREE</b>"
    uses_left = FREE_LIMIT - u["uses_today"]
    tr_left = TRIAL_LIMIT - (u.get("trial_count") or 0)
    if prem:
        uses_line = "♾️ Unlimited"
        tr_line = "♾️ Unlimited"
    else:
        uses_line = f"{bar(uses_left / FREE_LIMIT)} {max(0, uses_left)}/{FREE_LIMIT}"
        tr_line = f"{bar(tr_left / TRIAL_LIMIT)} {max(0, tr_left)}/{TRIAL_LIMIT}"
    uname = f"@{update.effective_user.username}" if update.effective_user.username else "—"
    await update.effective_message.reply_text(
        f"👤 <b>MY ACCOUNT</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⭐ Plan: {badge}\n"
        + (f"📅 Premium tak: <b>{premium_expiry(u)}</b>\n" if prem else "") +
        f"📊 Aaj ke uses:\n{uses_line}\n"
        f"💎 Premium trials:\n{tr_line}\n"
        f"🎁 Referrals: <b>{u['referrals']}</b>\n"
        f"🆔 ID: {code(u['user_id'])}\n"
        f"🔗 {hesc(uname)}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎯 {REFER_NEED} referrals = 30 din Premium FREE!\n/refer",
        reply_markup=BACK, parse_mode=HTML)


async def cmd_refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    me = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{u['user_id']}"
    done = u["referrals"] % REFER_NEED
    need = REFER_NEED - done
    prog = bar(done / REFER_NEED)
    top = top_referrers()
    board = "".join(f"\n{i + 1}. {hesc((n or 'User')[:15])} — {c} 🎁" for i, (n, c) in enumerate(top)) or "\n—"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Doston ko Share Karo",
                              url=f"https://t.me/share/url?url={link}&text=FREE Utility Bot - 19 tools! QR, UPI QR, YT Download, Voice sab!")],
        [InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")],
    ])
    await update.effective_message.reply_text(
        f"🎁 <b>REFER &amp; EARN</b> 💰\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Dost jodo → <b>30 din Premium FREE!</b>\n\n"
        f"🔗 Tumhara link:\n{code(link)}\n\n"
        f"📊 Progress: {prog}\n"
        f"✅ {u['referrals']} referrals • 🎯 {need} aur = FREE Premium!\n\n"
        f"🏆 <b>Top Referrers:</b>{board}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📌 <b>Rules:</b> Dost link se /start kare = +1 referral. "
        f"Fake/double account = ban. Har {REFER_NEED} referrals par 30 din Premium auto! ⚡",
        reply_markup=kb, parse_mode=HTML)


async def cmd_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not UPI_ID:
        await update.effective_message.reply_text("💎 Premium jald aa raha hai! Tab tak /refer se FREE premium pao 🎁", reply_markup=BACK)
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ SILVER 30 din - ₹49", callback_data="plan49")],
        [InlineKeyboardButton("🔥 GOLD 90 din - ₹99", callback_data="plan99")],
        [InlineKeyboardButton("🎁 FREE me pao (Refer)", callback_data="ref")],
        [InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")],
    ])
    await update.effective_message.reply_text(
        "💎✨ <b>PREMIUM</b> ✨💎\n"
        "━━━━━━━━━━━━━━━\n"
        "✅ <b>Unlimited</b> saare 19 tools\n"
        "💰 UPI QR + ⬇️ YT Download + 🔊 10 Voices — bina limit!\n"
        "⚡ Sabse pehle naye tools\n"
        "🚫 Roz ka limit khatam = tension khatam\n"
        "━━━━━━━━━━━━━━━\n"
        "⭐ <b>SILVER</b> — 30 din — <b>₹49</b>\n"
        "🔥 <b>GOLD</b> — 90 din — <b>₹99</b> <i>(₹33/mahina!)</i>\n"
        "━━━━━━━━━━━━━━━\n"
        "1️⃣ Plan dabao → QR milega\n"
        "2️⃣ UPI se pay karo\n"
        "3️⃣ Screenshot bhejo → kuch min me active! ⚡\n\n"
        "🎁 <i>Paisa nahi? /refer se 5 dost = 30 din FREE!</i>",
        reply_markup=kb, parse_mode=HTML)

# ---- tool entries ----
async def cmd_tool(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    if not await ensure_joined(update, context):
        return
    context.user_data["mode"] = mode
    if mode == "pdf":
        context.user_data["pdf_pages"] = []
    await update.message.reply_text(PROMPTS[mode] + "\n\n/cancel kabhi bhi dabao.",
                                    reply_markup=BACK, parse_mode=HTML)


async def cmd_qr(u, c): await cmd_tool(u, c, "qr")
async def cmd_pdf(u, c): await cmd_tool(u, c, "pdf")
async def cmd_short(u, c): await cmd_tool(u, c, "short")
async def cmd_yt(u, c): await cmd_tool(u, c, "yt")
async def cmd_ytdl(u, c): await cmd_tool(u, c, "ytdl")
async def cmd_emi(u, c): await cmd_tool(u, c, "emi")
async def cmd_age(u, c): await cmd_tool(u, c, "age")
async def cmd_upi(u, c): await cmd_tool(u, c, "upi")
async def cmd_idfind(u, c): await cmd_tool(u, c, "idfind")
async def cmd_ifsc(u, c): await cmd_tool(u, c, "ifsc")
async def cmd_pin(u, c): await cmd_tool(u, c, "pin")
async def cmd_pp(u, c): await cmd_tool(u, c, "pp")
async def cmd_link(u, c): await cmd_tool(u, c, "linkcheck")
async def cmd_bypass(u, c): await cmd_tool(u, c, "linkbypass")
async def cmd_rto(u, c): await cmd_tool(u, c, "rto")
async def cmd_insta(u, c): await cmd_tool(u, c, "insta")


async def pwd_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_joined(update, context):
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Naam wala Password", callback_data="pwd_name")],
        [InlineKeyboardButton("🎲 Random Strong", callback_data="pwd_rand")],
        [InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")],
    ])
    await update.message.reply_text(
        "🔐 <b>Advanced Password Generator</b>\n\nApne <b>naam ke saath</b> password chahiye ya <b>random strong</b>?",
        reply_markup=kb, parse_mode=HTML)


async def tts_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_joined(update, context):
        return
    rows = []
    for i in range(0, len(TTS_VOICES), 2):
        row = [InlineKeyboardButton(TTS_VOICES[j][1], callback_data=f"tts_v:{TTS_VOICES[j][0]}")
               for j in range(i, min(i + 2, len(TTS_VOICES)))]
        rows.append(row)
    rows.append([InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")])
    await update.message.reply_text(
        "🔊 <b>Text to Speech (10 Voices!)</b> 💎 <i>roz 2 FREE trial</i>\n\n"
        "Voice chuno 👇\n<i>Hindi text Hindi voice me, English text English voice me best lagegi! Bhojpuri/Hinglish bhi chalegi ✅</i>",
        reply_markup=InlineKeyboardMarkup(rows), parse_mode=HTML)


async def int_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_joined(update, context):
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Simple Interest", callback_data="int_si")],
        [InlineKeyboardButton("📈 Compound Interest", callback_data="int_ci")],
        [InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")],
    ])
    await update.message.reply_text("📈 <b>Interest Calculator</b>\n\nKaunsa interest nikalna hai?",
                                    reply_markup=kb, parse_mode=HTML)

# ---------------- ADMIN ----------------
def is_admin(uid: int) -> bool:
    return bool(ADMIN_ID) and uid == ADMIN_ID


def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Stats", callback_data="adm_stats"),
         InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc")],
        [InlineKeyboardButton("💎 Give Premium", callback_data="adm_prem"),
         InlineKeyboardButton("🔍 User Info", callback_data="adm_info")],
        [InlineKeyboardButton("👥 Recent Users", callback_data="adm_recent"),
         InlineKeyboardButton("💎 Premium List", callback_data="adm_plist")],
        [InlineKeyboardButton("🚫 Ban", callback_data="adm_ban"),
         InlineKeyboardButton("✅ Unban", callback_data="adm_unban")],
        [InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")],
    ])


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        secs = int((datetime.now() - START_TIME).total_seconds())
        h = secs // 3600
        m = (secs % 3600) // 60
        msg = "Pong! Bot LIVE hai ⚡\n📌 Version: <b>" + BOT_VERSION + "</b>\n⏱️ Uptime: " + str(h) + "h " + str(m) + "m"
        await update.message.reply_text(msg, parse_mode=HTML)
    except Exception:
        pass


async def cmd_cktest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    lines = []
    try:
        ex = os.path.exists(COOKIE_FILE)
        lines.append("EXISTS: " + str(ex))
        if ex:
            raw = open(COOKIE_FILE, "rb").read()
            lines.append("SIZE: " + str(len(raw)))
            lines.append("TABS: " + str(raw.count(b"\t")))
            lines.append("JAR: " + str(cookies_jar_count(COOKIE_FILE)))
    except Exception as e:
        lines.append("ERR: " + str(e)[:100])
    await update.message.reply_text("CKT" + chr(10) + chr(10).join(lines))
    st = await update.message.reply_text("Probe chal raha (15-30s)...")
    try:
        r = await asyncio.to_thread(_yt_race_one, "https://www.youtube.com/watch?v=dQw4w9WgXcQ", None)
        if r and r[0]:
            await st.edit_text("PROBE: OK - " + str(r[0].get("title", "?"))[:60])
        else:
            _e = str(r[2] if r and len(r) > 2 else "?")
            await st.edit_text("PROBE-FAIL: " + _e[:200])
    except Exception as e:
        await st.edit_text("PROBE-ERR: " + str(e)[:150])


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    t, a, p = stats()
    await update.effective_message.reply_text(
        f"🛠️ <b>ADMIN PANEL</b> — full control!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Total: <b>{t}</b> • 🟢 Aaj: <b>{a}</b> • 💎 Premium: <b>{p}</b>\n"
        f"━━━━━━━━━━━━━━━\nNeeche se action chuno 👇",
        reply_markup=admin_kb(), parse_mode=HTML)


async def do_broadcast(bot, text: str):
    ids = all_user_ids()
    ok = fail = 0
    for uid in ids:
        try:
            await bot.send_message(uid, text)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    return len(ids), ok, fail


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    t, a, p = stats()
    await update.message.reply_text(f"📊 STATS\n\n👥 Total users: {t}\n🟢 Aaj active: {a}\n💎 Premium: {p}")


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Use: /broadcast tumhara message\nYa /admin → Broadcast dabao, phir message bhejo.")
        return
    await update.message.reply_text("📢 Bhej raha hoon...")
    n, ok, fail = await do_broadcast(context.bot, text)
    await update.message.reply_text(f"✅ Broadcast done! Total: {n}, Success: {ok}, Fail: {fail}")


async def cmd_setcookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    context.user_data["mode"] = "setcookies"
    await update.message.reply_text(
        "🍪 <b>YT Cookies Setup</b> (permanent download fix!) "
        "PHONE: Firefox app + 'Cookie-Editor' addon se youtube cookies JSON me Export karo. PC: Chrome me <b>'Get cookies.txt LOCALLY'</b> lagao → youtube.com kholo → Export → jo file mile (.txt ya .json) wo yahan 2-3 message me TEXT bhejo, phir DONE likho (ya FILE bhej do). "
        "⚠️ Note: deploy ke baad dobara bhejna padega (free server memory reset). Permanent ke liye Render me YT_COOKIES env me file ka text dalo.",
        parse_mode=HTML)


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        uid = int(context.args[0]); days = int(context.args[1]) if len(context.args) > 1 else 30
    except Exception:
        await update.message.reply_text("Use: /approve <user_id> <din>")
        return
    grant_premium(uid, days)
    await update.message.reply_text(f"✅ {uid} ko {days} din premium de diya!")
    try:
        await context.bot.send_message(uid, f"💎 Badhai! Tumhara {days} din ka Premium ACTIVE ho gaya! 🎉")
    except Exception:
        pass

# ---------------- CALLBACKS ----------------
async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data or ""
    uid = update.effective_user.id
    try:
        await q.answer()
    except Exception:
        pass

    if data == "joincheck":
        if await ensure_joined(update, context):
            await q.message.reply_text(WELCOME, reply_markup=kb_for(uid), parse_mode=HTML)
        return

    if data == "menu":
        context.user_data.pop("mode", None)
        await q.message.reply_text("⌨️ Neeche grid me saare tools hain — koi dabao 👇",
                                   reply_markup=kb_for(uid))
        return

    if data == "ref":
        await cmd_refer(update, context)
        return
    if data == "prem":
        await cmd_premium(update, context)
        return
    if data == "adm":
        await cmd_admin(update, context)
        return

    # ---- admin callbacks ----
    if data.startswith("adm_"):
        if not is_admin(uid):
            await q.message.reply_text("⛔ Sirf admin!")
            return
        if data == "adm_stats":
            t, a, p = stats()
            await q.message.reply_text(f"📊 <b>STATS</b>\n\n👥 Total: <b>{t}</b>\n🟢 Aaj active: <b>{a}</b>\n💎 Premium: <b>{p}</b>",
                                       reply_markup=admin_kb(), parse_mode=HTML)
        elif data == "adm_bc":
            context.user_data["mode"] = "admin_bc"
            await q.message.reply_text("📢 Jo message <b>sabko</b> bhejna hai, wo bhejo:\n(/cancel se wapas)", parse_mode=HTML)
        elif data == "adm_prem":
            context.user_data["mode"] = "admin_prem"
            await q.message.reply_text("💎 Format me bhejo:\n<code>user_id din</code>\n(jaise: <code>123456 30</code>)\n\n/cancel se wapas", parse_mode=HTML)
        elif data == "adm_info":
            context.user_data["mode"] = "admin_info"
            await q.message.reply_text("🔍 User ID bhejo (jaise: <code>123456</code>):", parse_mode=HTML)
        elif data == "adm_recent":
            rows = recent_users()
            txt = "👥 <b>Recent 10 Users:</b>\n" + ("".join(
                f"\n{i + 1}. {hesc(n or 'User')[:18]} — {code(i2)}" + (f" @{hesc(un)}" if un else "")
                for i, (i2, n, un) in enumerate(rows)) or "\n—")
            await q.message.reply_text(txt, reply_markup=admin_kb(), parse_mode=HTML)
        elif data == "adm_plist":
            rows = premium_users()
            txt = f"💎 <b>Premium Users ({len(rows)}):</b>\n" + ("".join(
                f"\n{i + 1}. {hesc(n or 'User')[:15]} — {code(i2)} (tak: {pu[:10]})"
                for i, (i2, n, pu) in enumerate(rows[:20])) or "\n—")
            await q.message.reply_text(txt, reply_markup=admin_kb(), parse_mode=HTML)
        elif data == "adm_ban":
            context.user_data["mode"] = "admin_ban"
            await q.message.reply_text("🚫 Ban karne ke liye User ID bhejo:", parse_mode=HTML)
        elif data == "adm_unban":
            context.user_data["mode"] = "admin_unban"
            await q.message.reply_text("✅ Unban ke liye User ID bhejo:", parse_mode=HTML)
        return

    if data in ("plan49", "plan99"):
        if not UPI_ID:
            await q.message.reply_text("💎 Premium jald aa raha hai! /refer se FREE pao 🎁", reply_markup=BACK)
            return
        amt = "49" if data == "plan49" else "99"
        days = "30" if data == "plan49" else "90"
        plan = "⭐ SILVER" if data == "plan49" else "🔥 GOLD"
        upi_link = f"upi://pay?pa={UPI_ID}&pn={quote(UPI_NAME)}&am={amt}&cu=INR&tn=UtilityDuniyaPremium"
        context.user_data["mode"] = "pay"
        context.user_data["plan_days"] = int(days)
        await q.message.reply_photo(
            photo=make_qr_bytes(upi_link),
            caption=(f"💎 <b>{plan}</b> — {days} din = <b>₹{amt}</b>\n\n"
                     f"1️⃣ UPI app se is QR par ₹{amt} pay karo\n"
                     f"2️⃣ Payment ka <b>SCREENSHOT</b> yahin bhejo\n"
                     f"3️⃣ Admin verify karke kuch min me active karega! ⚡\n\nUPI ID: {code(UPI_ID)}"),
            reply_markup=BACK, parse_mode=HTML)
        return

    if data.startswith("ap:") or data.startswith("dc:"):
        if not is_admin(uid):
            await q.message.reply_text("⛔ Sirf admin!")
            return
        parts = data.split(":")
        try:
            target = int(parts[1])
        except Exception:
            return
        if data.startswith("ap:"):
            days = int(parts[2]) if len(parts) > 2 else 30
            grant_premium(target, days)
            await q.message.reply_text(f"✅ {target} ko {days} din premium de diya!")
            try:
                await context.bot.send_message(target, f"💎 Badhai! Tumhara {days} din ka Premium ACTIVE ho gaya! 🎉")
            except Exception:
                pass
        else:
            await q.message.reply_text(f"❌ {target} ka payment reject kiya.")
            try:
                await context.bot.send_message(target, "❌ Tumhara payment verify nahi ho paya. Sahi screenshot dobara bhejo ya /premium me plan chuno.")
            except Exception:
                pass
        return

    if not await ensure_joined(update, context):
        return

    if data == "pwd_rand":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("8", callback_data="p8"), InlineKeyboardButton("12", callback_data="p12"),
             InlineKeyboardButton("16", callback_data="p16"), InlineKeyboardButton("32", callback_data="p32")],
            [InlineKeyboardButton("⌨️ Tools Grid", callback_data="menu")],
        ])
        await q.message.reply_text("🎲 Kitne character ka password? (3 options dunga, jo pasand wo copy karo 👆)",
                                   reply_markup=kb)
        return
    if data == "pwd_name":
        context.user_data["mode"] = "pwd_name"
        await q.message.reply_text("👤 Apna <b>naam</b> bhejo (password me use hoga):\n(jaise: Himanshu)",
                                   reply_markup=BACK, parse_mode=HTML)
        return
    if data in ("p8", "p12", "p16", "p32"):
        if not await use_or_block(uid, update):
            return
        n = int(data[1:])
        pws = [gen_password(n) for _ in range(3)]
        await q.message.reply_text(
            f"🔐 <b>{n}-digit passwords</b> (tap = copy 👆):\n\n1️⃣ {code(pws[0])}\n\n2️⃣ {code(pws[1])}\n\n3️⃣ {code(pws[2])}\n\n<i>Kisi se share mat karo!</i>",
            reply_markup=BACK, parse_mode=HTML)
        return

    if data == "upi_yes":
        pending = context.user_data.get("qr_pending")
        if not pending:
            return
        context.user_data["upi_id"] = pending
        context.user_data["mode"] = "upi_name"
        context.user_data.pop("qr_pending", None)
        await q.message.reply_text(f"💰 Payment QR banate hain!\n✅ UPI ID: {code(pending)}\n\nAb apna NAAM bhejo:",
                                   reply_markup=BACK, parse_mode=HTML)
        return
    if data == "upi_no":
        pending = context.user_data.get("qr_pending")
        if not pending:
            return
        if not await use_or_block(uid, update):
            return
        context.user_data.pop("qr_pending", None)
        context.user_data.pop("mode", None)
        await q.message.reply_photo(photo=make_qr_bytes(pending),
                                    caption="📝 Normal text QR (isme payment NAHI hoga)",
                                    reply_markup=BACK)
        return

    if data == "pdf_done":
        pages = context.user_data.get("pdf_pages") or []
        if not pages:
            await q.message.reply_text("⚠️ Pehle photo bhejo:")
            return
        if not await use_or_block(uid, update):
            return
        await act(context, update.effective_chat.id, "upload_document")
        try:
            pdf = await asyncio.to_thread(pages_to_pdf, pages)
        except Exception:
            refund_use(uid)
            await q.message.reply_text("⚠️ PDF banane me dikkat. Dusri photo try karo:")
            return
        bio = io.BytesIO(pdf)
        bio.name = "utility_duniya.pdf"
        bio.seek(0)
        await q.message.reply_document(document=bio,
                                       caption=f"🖼️ <b>{len(pages)}-page PDF</b> ready — full quality! ✅",
                                       reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("pdf_pages", None)
        context.user_data.pop("mode", None)
        return

    if data in ("int_si", "int_ci"):
        context.user_data["int_type"] = "SI" if data == "int_si" else "CI"
        context.user_data["mode"] = "int_p"
        await q.message.reply_text(f"{'📊 Simple' if data == 'int_si' else '📈 Compound'} Interest chuna ✅\n\nPaisa (Principal ₹) bhejo:\n(jaise: 50000)", reply_markup=BACK)
        return
    if data.startswith("int_f:"):
        try:
            f = int(data.split(":")[1])
        except Exception:
            return
        p = context.user_data.get("int_p", 0)
        r = context.user_data.get("int_r", 0)
        t = context.user_data.get("int_t", 0)
        if not p:
            await q.message.reply_text("⚠️ Server restart ho gaya tha. Interest grid se dobara shuru karo (limit nahi kata).")
            for k in ("mode", "int_type", "int_p", "int_r", "int_t"):
                context.user_data.pop(k, None)
            return
        if not await use_or_block(uid, update):
            return
        await send_interest_result(update, p, r, t, f)
        for k in ("mode", "int_type", "int_p", "int_r", "int_t"):
            context.user_data.pop(k, None)
        return

    if data.startswith("tts_v:"):
        v = data.split(":")[1]
        voices = {x[0]: x for x in TTS_VOICES}
        if v not in voices:
            return
        _, label, voice, rate, pitch = voices[v]
        context.user_data["tts_voice"] = voice
        context.user_data["tts_name"] = label
        context.user_data["tts_rate"] = rate
        context.user_data["tts_pitch"] = pitch
        context.user_data["mode"] = "tts_text"
        await q.message.reply_text(f"🔊 Voice: <b>{label}</b> ✅\n\nAb TEXT bhejo (400 letters tak):",
                                   reply_markup=BACK, parse_mode=HTML)
        return

    if data == "acc":
        await cmd_account(update, context)
        return


async def send_interest_result(update, p, r, t, f):
    si_i, si_t = si_result(p, r, t)
    ci_i, ci_t = ci_result(p, r, t, f)
    fn = {1: "Yearly", 2: "Half-yearly", 4: "Quarterly", 12: "Monthly"}.get(f, f"{f}x")
    extra = "💡 <b>Samjho:</b> SI me har saal same interest milta hai. CI me <b>interest par bhi interest</b> — lamba time = CI king! 👑\n"
    extra += "📌 Invest → CI zyada dega ✅ | Loan → SI wala sasta ✅"
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        f"📈 <b>INTEREST RESULT</b>\n━━━━━━━━━━━━━━━\n"
        f"💰 Paisa: ₹{inr(p)} | 📊 Rate: {r}% | ⏳ {t} saal\n\n"
        f"📊 <b>Simple Interest:</b>\n   Interest: ₹{inr(si_i)}\n   Total: ₹{inr(si_t)}\n\n"
        f"📈 <b>Compound Interest ({fn}):</b>\n   Interest: ₹{inr(ci_i)}\n   Total: ₹{inr(ci_t)}\n\n"
        f"🏆 CI se extra fayda: <b>₹{inr(ci_t - si_t)}</b>\n━━━━━━━━━━━━━━━\n{extra}",
        reply_markup=BACK, parse_mode=HTML)

# ---------------- MESSAGE ROUTERS ----------------
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_username(uid, update.effective_user.username or "")
    if is_banned(uid):
        await update.message.reply_text(BAN_MSG)
        return
    text = (update.message.text or "").strip()

    if text in BTN_MODE:
        if not await ensure_joined(update, context):
            return
        mode = BTN_MODE[text]
        context.user_data["mode"] = mode
        if mode == "pdf":
            context.user_data["pdf_pages"] = []
        await update.message.reply_text(PROMPTS[mode] + "\n\n/cancel kabhi bhi dabao.",
                                        reply_markup=BACK, parse_mode=HTML)
        return
    if text == "🔐 Password":
        await pwd_entry(update, context)
        return
    if text == "🔊 Text to Speech":
        await tts_entry(update, context)
        return
    if text == "📈 Interest Calc":
        await int_entry(update, context)
        return
    if text == "💎 Premium":
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

    mode = context.user_data.get("mode")
    if not mode:
        await update.message.reply_text("👇 Neeche grid icon (▦) dabao — saare tools khulenge!",
                                        reply_markup=kb_for(uid))
        return
    if not await ensure_joined(update, context):
        return

    # ---- ADMIN modes ----
    if mode == "admin_bc":
        if not is_admin(uid):
            return
        st = await update.message.reply_text("📢 Broadcasting...")
        n, ok, fail = await do_broadcast(context.bot, text)
        await st.edit_text(f"✅ Done! Total: {n}, Success: {ok}, Fail: {fail}")
        context.user_data.pop("mode", None)
        return
    if mode == "admin_prem":
        if not is_admin(uid):
            return
        try:
            parts = text.split()
            tuid, days = int(parts[0]), int(parts[1]) if len(parts) > 1 else 30
        except Exception:
            await update.message.reply_text("⚠️ Format: <code>user_id din</code> (jaise: <code>123456 30</code>)", parse_mode=HTML)
            return
        grant_premium(tuid, days)
        await update.message.reply_text(f"✅ {tuid} ko {days} din premium de diya!", reply_markup=admin_kb())
        try:
            await context.bot.send_message(tuid, f"💎 Badhai! Tumhara {days} din ka Premium ACTIVE ho gaya! 🎉")
        except Exception:
            pass
        context.user_data.pop("mode", None)
        return
    if mode == "admin_info":
        if not is_admin(uid):
            return
        try:
            tuid = int(text.strip().split()[0])
        except Exception:
            await update.message.reply_text("⚠️ Sahi user ID bhejo:")
            return
        r = get_user_row(tuid)
        if not r:
            await update.message.reply_text("😔 Ye user nahi mila.")
            context.user_data.pop("mode", None)
            return
        prem = "💎 YES" if is_premium(r) else "Free"
        await update.message.reply_text(
            f"🔍 <b>USER INFO</b>\n\n👤 {hesc(r.get('name') or '-')}\n"
            f"🔗 @{hesc(r.get('username') or '-')} • 🆔 {code(tuid)}\n"
            f"⭐ {prem} (tak: {premium_expiry(r)})\n🎁 Referrals: {r.get('referrals', 0)} | "
            f"📊 Uses: {r.get('uses_today', 0)} | 🚫 Ban: {r.get('banned', 0)}",
            reply_markup=admin_kb(), parse_mode=HTML)
        context.user_data.pop("mode", None)
        return
    if mode == "admin_ban":
        if not is_admin(uid):
            return
        try:
            tuid = int(text.strip().split()[0])
        except Exception:
            await update.message.reply_text("⚠️ Sahi user ID bhejo:")
            return
        if tuid == ADMIN_ID:
            await update.message.reply_text("😅 Khud ko ban nahi kar sakte!")
            return
        set_ban(tuid, 1)
        await update.message.reply_text(f"🚫 {tuid} banned!", reply_markup=admin_kb())
        context.user_data.pop("mode", None)
        return
    if mode == "admin_unban":
        if not is_admin(uid):
            return
        try:
            tuid = int(text.strip().split()[0])
        except Exception:
            await update.message.reply_text("⚠️ Sahi user ID bhejo:")
            return
        set_ban(tuid, 0)
        await update.message.reply_text(f"✅ {tuid} unbanned!", reply_markup=admin_kb())
        context.user_data.pop("mode", None)
        return

    if mode == "pay":
        await update.message.reply_text("📸 Payment ka SCREENSHOT photo ke roop me bhejo (text nahi).")
        return

    if mode == "qr":
        nospace = text.replace(" ", "")
        if UPI_RE.match(nospace):
            context.user_data["qr_pending"] = nospace
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Payment QR (sahi wala ✅)", callback_data="upi_yes")],
                [InlineKeyboardButton("📝 Normal text QR", callback_data="upi_no")],
            ])
            await update.message.reply_text(
                "Ye to UPI ID lag rahi hai! 👇\n\n"
                "💰 Payment QR = GPay/PhonePe se scan karke PAISA aayega ✅\n"
                "📝 Normal QR = sirf text dikhega (payment NAHI hoga)\n\nKya banana hai?", reply_markup=kb)
            return
        if not await use_or_block(uid, update):
            return
        if len(text) > 2000:
            refund_use(uid)
            await update.message.reply_text("⚠️ Text thoda chhota bhejo (2000 letters tak).")
            return
        await act(context, update.effective_chat.id, "upload_photo")
        await update.message.reply_photo(photo=make_qr_bytes(text),
                                         caption=f"📷 HD QR ready! ✅\n\n📝 Data: {code(text[:200])}",
                                         reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "pwd_name":
        name = re.sub(r"\s+", "", text)[:20]
        if not re.match(r"^[A-Za-z]{3,20}$", name):
            await update.message.reply_text("⚠️ Sirf naam bhejo (3-20 English letters, bina space):")
            return
        if not await use_or_block(uid, update):
            return
        pws = name_passwords(name)
        await update.message.reply_text(
            f"👤 <b>{hesc(name)} ke passwords</b> (tap = copy 👆):\n\n1️⃣ {code(pws[0])}\n\n2️⃣ {code(pws[1])}\n\n3️⃣ {code(pws[2])}\n\n💪 <i>Strong + yaad me aasaan!</i>",
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "short":
        if not await use_or_block(uid, update):
            return
        await act(context, update.effective_chat.id, "typing")
        url = text if text.startswith(("http://", "https://")) else "https://" + text
        if "." not in urlparse(url).netloc:
            refund_use(uid)
            await update.message.reply_text("⚠️ Sahi link bhejo (jaise google.com). Dobara try karo:")
            return
        s1, s2 = await asyncio.gather(asyncio.to_thread(shorten_isgd, url),
                                            asyncio.to_thread(shorten_tiny, url))
        if not s1 and not s2:
            refund_use(uid)
            await update.message.reply_text("⚠️ Short nahi ho paya (net slow?). Dobara try karo — limit wapas kar di! ✅")
            return
        msg = "🔗 <b>Short links ready!</b> (tap = copy 👆)\n"
        if s1:
            msg += f"\n1️⃣ {code(s1)}"
        if s2:
            msg += f"\n\n2️⃣ {code(s2)}"
        await update.message.reply_photo(photo=make_qr_bytes(s1 or s2), caption=msg,
                                         reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "yt":
        if not await use_or_block(uid, update):
            return
        await act(context, update.effective_chat.id, "upload_photo")
        vid = yt_id(text)
        if not vid:
            refund_use(uid)
            await update.message.reply_text("⚠️ Sahi YouTube link bhejo. Dobara try karo:")
            return
        res = await asyncio.to_thread(fetch_yt_best, vid)
        if not res:
            refund_use(uid)
            await update.message.reply_text("⚠️ Is video ka thumbnail nahi mila. Dusra link try karo (limit wapas ✅):")
            return
        data, w, h, q = res
        try:
            data, w, h, enh = await asyncio.to_thread(enhance_thumb, data)
        except Exception:
            enh = False
        bio = io.BytesIO(data)
        bio.name = f"thumbnail_{w}x{h}.jpg"
        bio.seek(0)
        tag = "⬆️ <b>HD Enhanced 720p+</b> ✨" if enh else "🏆 <b>Original Highest Quality</b>"
        await update.message.reply_document(
            document=bio,
            caption=f"🎬 {tag}!\n📐 Size: <b>{w}×{h}</b>\n🔗 https://youtu.be/{vid}",
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "ytdl":
        vid = yt_id(text)
        if not vid:
            await update.message.reply_text("⚠️ Sahi YouTube/Shorts link bhejo:")
            return
        if not await asyncio.to_thread(yt_exists, vid):
            await update.message.reply_text("⛔ Ye video YouTube par NAHI mili (delete/private). Dusra link bhejo! Trial kata hi nahi.")
            context.user_data.pop("mode", None)
            return
        if not await trial_or_block(uid, update, "YT Download"):
            context.user_data.pop("mode", None)
            return
        await act(context, update.effective_chat.id, "upload_video")
        status = await update.message.reply_text("⏳ <b>Downloading HD...</b> (thoda time lagega, ruko! ⏰)",
                                                 parse_mode=HTML)
        st, info, path = await asyncio.to_thread(ytdl_download, text)
        if st != "OK":
            refund_trial(uid)
            info = str(info) + " Trial wapas kar diya."
            try:
                thumb = await asyncio.to_thread(fetch_yt_best, vid)
            except Exception:
                thumb = None
            if thumb:
                data, w, h, _q = thumb
                bio = io.BytesIO(data)
                bio.name = "thumbnail.jpg"
                bio.seek(0)
                await update.message.reply_photo(
                    photo=bio,
                    caption=f"{info} 🎬 Video nahi aayi to thumbnail le lo! ({w}x{h})",
                    reply_markup=BACK, parse_mode=HTML)
                try:
                    await status.delete()
                except Exception:
                    pass
            else:
                await status.edit_text(info)
            context.user_data.pop("mode", None)
            return
        try:
            title = (info.get("title") or "video")[:80]
            dur = info.get("duration") or 0
            res = info.get("height") or "?"
            vf = open(path, "rb")
            try:
                await update.message.reply_video(
                    video=vf,
                caption=f"⬇️ <b>{hesc(title)}</b>\n⏱️ {dur // 60}:{dur % 60:02d} min • 📐 {res}p • 💾 {os.path.getsize(path) / 1048576:.1f} MB\n\n✅ Download karke chill karo! 🎬",
                    reply_markup=BACK, parse_mode=HTML)
            finally:
                try:
                    vf.close()
                except Exception:
                    pass
            try:
                await status.delete()
            except Exception:
                pass
        except Exception as e:
            await status.edit_text(f"⛔ Bhejne me dikkat: {str(e)[:150]}")
        finally:
            try:
                os.remove(path)
                os.rmdir(os.path.dirname(path))
            except Exception:
                pass
        context.user_data.pop("mode", None)
        return

    if mode == "emi":
        try:
            p = float(text.replace(",", "").replace("₹", "").strip())
            if p <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi amount bhejo (jaise 100000):")
            return
        context.user_data["emi_p"] = p
        context.user_data["mode"] = "emi_r"
        await update.message.reply_text(f"💰 Loan: ₹{inr(p)}\n\nAb saal ka Interest Rate % bhejo:\n(jaise: 10)")
        return
    if mode == "emi_r":
        try:
            r = float(text.replace("%", "").strip())
            if r < 0 or r > 60:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi rate bhejo (jaise 10):")
            return
        context.user_data["emi_r"] = r
        context.user_data["mode"] = "emi_n"
        await update.message.reply_text("📅 Ab kitne MAHINE ka loan hai? (jaise: 12)")
        return
    if mode == "emi_n":
        try:
            n = int(float(text.strip()))
            if n <= 0 or n > 360:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi mahine bhejo (jaise 12):")
            return
        p = context.user_data.get("emi_p", 0)
        r = context.user_data.get("emi_r", 0)
        if not p:
            await update.message.reply_text("⚠️ Server restart ho gaya tha. EMI grid se dobara shuru karo (limit nahi kata).")
            context.user_data.pop("mode", None)
            return
        if not await use_or_block(uid, update):
            return
        emi, rows = emi_schedule(p, r, n)
        total = emi * n
        tbl = "<pre>Saal | Asal   | Vyaaj  | Baki\n"
        for y, yp, yi, bal in rows[:30]:
            tbl += f"{y:>4} | {yp:>6.0f} | {yi:>6.0f} | {bal:>7.0f}\n"
        tbl += "</pre>"
        await update.message.reply_text(
            f"🧮 <b>EMI RESULT (Advanced)</b>\n━━━━━━━━━━━━━━━\n"
            f"💰 Loan: ₹{inr(p)} | 📊 {r}% | 📅 {n} mahine\n\n"
            f"💳 <b>Monthly EMI: ₹{inr(emi)}</b>\n"
            f"💵 Total payment: ₹{inr(total)}\n"
            f"📈 Total interest: ₹{inr(total - p)}\n\n"
            f"📋 <b>Saal-wise hisaab:</b>\n{tbl}\n"
            f"💡 <i>Tip: chhota time = kam interest! Prepayment se hazaaron bachao.</i>",
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "age":
        m = re.match(r"^\s*(\d{1,2})[-/](\d{1,2})[-/](\d{4})\s*$", text)
        if not m:
            await update.message.reply_text("⚠️ Format: DD-MM-YYYY (jaise 15-08-2005):")
            return
        try:
            dob = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if dob > date.today():
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi date bhejo (jaise 15-08-2005):")
            return
        if not await use_or_block(uid, update):
            return
        years, to_bday, total_days = calc_age(dob)
        wd = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dob.weekday()]
        await update.message.reply_text(
            f"🎂 <b>AGE CALCULATOR</b>\n━━━━━━━━━━━━━━━\n"
            f"🎉 Umar: <b>{years} saal</b>\n"
            f"📅 Din: {total_days:,} • 📆 Mahine: {total_days // 30:,} • ⏳ Hafte: {total_days // 7:,}\n"
            f"🌟 Janam din: <b>{wd}</b>\n"
            f"🔯 Rashi: <b>{zodiac(dob.day, dob.month)}</b>\n"
            f"🎈 Birthday me: <b>{to_bday} din</b> bache!",
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "upi":
        upi = text.replace(" ", "")
        if not UPI_RE.match(upi):
            await update.message.reply_text("⚠️ Sahi UPI ID bhejo (jaise name@okhdfc):")
            return
        context.user_data["upi_id"] = upi
        context.user_data["mode"] = "upi_name"
        await update.message.reply_text(f"✅ UPI ID: {code(upi)}\n\nAb apna NAAM bhejo (payment par dikhega):",
                                        reply_markup=BACK, parse_mode=HTML)
        return
    if mode == "upi_name":
        context.user_data["upi_name"] = text[:40]
        context.user_data["mode"] = "upi_amt"
        await update.message.reply_text("💰 Fixed AMOUNT lagana hai? (dukandaaron ke liye best)\n\nAmount bhejo (jaise 100) ya skip likho:")
        return
    if mode == "upi_amt":
        amt = None
        if text.lower() not in ("skip", "0", "no", "n"):
            try:
                amt = round(float(text.replace("₹", "").replace(",", "").strip()), 2)
            except Exception:
                await update.message.reply_text("⚠️ Sahi amount bhejo (jaise 100) ya skip likho:")
                return
            if amt < 1 or amt > 1000000:
                await update.message.reply_text("⚠️ Amount 1 se 1000000 tak rakho, ya skip likho:")
                return
        context.user_data["upi_amt"] = amt
        context.user_data["mode"] = "upi_note"
        await update.message.reply_text("📝 Payment NOTE lagana hai? (jaise: Dukaan payment)\n\nNote bhejo ya skip likho:")
        return
    if mode == "upi_note":
        note = "" if text.lower() == "skip" else text[:40]
        if not context.user_data.get("upi_id"):
            await update.message.reply_text("⚠️ Server restart ho gaya tha. UPI QR grid se dobara banao (trial nahi kata).")
            for k in ("mode", "upi_id", "upi_name", "upi_amt"):
                context.user_data.pop(k, None)
            return
        if not await trial_or_block(uid, update, "UPI QR"):
            context.user_data.pop("mode", None)
            return
        link = build_upi_link(context.user_data.get("upi_id", ""), context.user_data.get("upi_name", "User"),
                              context.user_data.get("upi_amt"), note)
        cap = (f"💰 <b>UPI Payment QR ready!</b>\n\n🆔 {code(context.user_data.get('upi_id'))}\n"
               f"👤 {hesc(context.user_data.get('upi_name', ''))}\n"
               + (f"💵 Fixed: ₹{inr(context.user_data.get('upi_amt') or 0)}\n" if context.user_data.get("upi_amt") else "💵 Amount: customer khud bharega\n")
               + (f"📝 Note: {hesc(note)}\n" if note else "")
               + f"\n🔗 Link: {code(link)}\n\n📲 GPay / PhonePe / Paytm se scan karo! ✅")
        await act(context, update.effective_chat.id, "upload_photo")
        await update.message.reply_photo(photo=make_qr_bytes(link), caption=cap,
                                         reply_markup=BACK, parse_mode=HTML)
        for k in ("mode", "upi_id", "upi_name", "upi_amt"):
            context.user_data.pop(k, None)
        return

    if mode == "setcookies":
        if not is_admin(uid):
            context.user_data.pop("mode", None)
            context.user_data.pop("ck_parts", None)
            return
        t = (text or "")
        if t.strip().lower() in ("done", "bas", "hogaya", "ho gaya", "complete", "khatam"):
            t = "".join(context.user_data.get("ck_parts", []))
            context.user_data.pop("ck_parts", None)
            if not t.strip():
                await update.message.reply_text("Pehle cookies ka text bhejo (2-3 message me), phir DONE likho.")
                return
        else:
            if len(t) < 50:
                await update.message.reply_text("Cookies ka text bhejo (clipboard wala poora), phir DONE likho.")
                return
            _parts = context.user_data.setdefault("ck_parts", [])
            _total = sum(len(x) for x in _parts) + len(t)
            if _total > 120000:
                context.user_data.pop("ck_parts", None)
                await update.message.reply_text("Bahut lamba ho gaya. /cancel karke dobara chhote parts me bhejo.")
                return
            _parts.append(t)
            await update.message.reply_text("Part " + str(len(_parts)) + " mil gaya (" + str(_total) + " chars). Aur ho to bhejo, warna DONE likho.")
            return
        low = t.lower()
        if not (("youtube" in low or "netscape" in low) and (t.count("\t") >= 10 or "#HttpOnly" in t or t.lstrip().startswith("["))):
            await update.message.reply_text("Ye cookies nahi lag rahi. Poora text bhejo (2-3 message me), phir DONE likho.")
            return
        raw = normalize_cookies(t.encode("utf-8", "ignore"))
        if raw.lstrip()[:1] == b"[":
            raw = cookies_json_to_netscape(raw)
            if not raw:
                await update.message.reply_text("JSON adhura lag raha hai. Poora bhejo phir DONE likho.")
                return
        try:
            with open(COOKIE_FILE, "wb") as fh:
                fh.write(raw)
        except Exception as e:
            await update.message.reply_text("Save fail: " + str(e)[:120])
            context.user_data.pop("mode", None)
            context.user_data.pop("ck_parts", None)
            return
        _n = cookies_jar_count(COOKIE_FILE)
        if _n <= 0:
            try:
                os.remove(COOKIE_FILE)
            except Exception:
                pass
            await update.message.reply_text("Cookies TOOTI lag rahi (0 login mile). Cookie-Editor se dobara Export karke bhejo.")
            context.user_data.pop("mode", None)
            context.user_data.pop("ck_parts", None)
            return
        await update.message.reply_text("Cookies save ho gayi ✅ (" + str(_n) + " login) Ab YT Download try karo!")
        context.user_data.pop("mode", None)
        context.user_data.pop("ck_parts", None)
        return

    if mode == "idfind":
        fo = getattr(update.message, "forward_origin", None)
        su = getattr(fo, "sender_user", None) if fo else None
        if su is not None:
            if not await use_or_block(uid, update):
                return
            nm = f"{su.first_name or ''} {su.last_name or ''}".strip() or "User"
            un = f"@{su.username}" if su.username else "— (username nahi hai)"
            await update.message.reply_text(
                f"🆔 <b>ID Mil Gayi!</b> ✅\n\n👤 Naam: {hesc(nm)}\n🔗 {hesc(un)}\n🆔 User ID: {code(su.id)}\n\n👆 <i>ID tap karke copy karo!</i>",
                reply_markup=BACK, parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        if fo is not None:
            await update.message.reply_text("🔒 Usne privacy on ki hai (forward hidden) — ID nahi mil sakti.\nKoi aur message forward karo ya @username bhejo:")
            return
        t = text.strip()
        if t.lower() in ("me", "mera", "self", "khud", "my"):
            if not await use_or_block(uid, update):
                return
            un = f"@{update.effective_user.username}" if update.effective_user.username else "—"
            await update.message.reply_text(f"👤 <b>Tumhari ID:</b>\n\n🆔 {code(uid)}\n🔗 {hesc(un)}",
                                            reply_markup=BACK, parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        un = t[1:] if t.startswith("@") else t
        if re.match(r"^[A-Za-z0-9_]{5,32}$", un):
            if not await use_or_block(uid, update):
                return
            r = await asyncio.to_thread(find_by_username, un)
            if r:
                await update.message.reply_text(
                    f"🆔 <b>ID Mil Gayi!</b> ✅\n\n👤 {hesc(r[1] or 'User')}\n🔗 @{hesc(r[2])}\n🆔 User ID: {code(r[0])}",
                    reply_markup=BACK, parse_mode=HTML)
            else:
                await update.message.reply_text(
                    f"😔 @{hesc(un)} hamare bot ka user nahi hai, isliye ID nahi mili.\n\n"
                    f"📌 <b>Telegram ka rule:</b> username se ID sirf bot users ki milti hai.\n"
                    f"✅ <b>100% tareeka:</b> uska koi message <b>FORWARD</b> karo!",
                    reply_markup=BACK, parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        await update.message.reply_text("⚠️ Koi message FORWARD karo, @username bhejo, ya 'me' likho:")
        return

    if mode == "numinfo":
        _dg = re.sub(r"\D", "", text or "")
        if len(_dg) == 12 and _dg.startswith("91"):
            _dg = _dg[2:]
        elif len(_dg) == 11 and _dg.startswith("0"):
            _dg = _dg[1:]
        if not re.match(r"^[6-9]\d{9}$", _dg):
            await update.message.reply_text("Sahi 10-digit mobile number bhejo (6-9 se shuru). Dobara try karo:")
            return
        if not await trial_or_block(uid, update, "Number Info"):
            context.user_data.pop("mode", None)
            return
        try:
            import phonenumbers as _pn
            from phonenumbers import geocoder as _pg, carrier as _pc
            _x = _pn.parse(_dg, "IN")
            _ok = _pn.is_valid_number(_x)
            _op = _pc.name_for_number(_x, "en") or "pata nahi (nayi series)"
            _rg = _pg.description_for_number(_x, "en") or "-"
        except Exception:
            refund_trial(uid)
            await update.message.reply_text("Number check nahi ho paya. Dobara try karo (trial wapas).")
            context.user_data.pop("mode", None)
            return
        _st = "Valid number" if _ok else "Invalid number"
        await update.message.reply_text(
            "\U0001F4F1 <b>NUMBER INFO</b>\nNumber: " + code("+91 " + _dg) + "\nStatus: " + _st +
            "\nOperator: " + hesc(_op) + "\nCircle/Region: " + hesc(_rg) +
            "\n\n<i>Note: number port (MNP) hua ho to operator purana dikh sakta hai.</i>",
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "insta":
        _rt = restore_md_marks(update.message)
        _u = ((_rt or "").strip().lstrip("@").split() or [""])
        u = _u[0][:30]
        if not u or not all(ch.isalnum() or ch in "._" for ch in u):
            await update.message.reply_text("Sahi Insta username bhejo (bina @). Dobara try karo:")
            return
        if not await trial_or_block(uid, update, "Insta Info"):
            context.user_data.pop("mode", None)
            return
        await act(context, update.effective_chat.id, "typing")
        st = await update.message.reply_text("\U0001F50E @" + code(u) + " ki report nikal raha hoon...", parse_mode=HTML)
        d = await asyncio.to_thread(insta_lookup, u)
        if d == "RATELIMIT":
            refund_trial(uid)
            await st.edit_text("Instagram busy hai (server-limit lag gayi). Trial WAPAS kar diya. 2-3 ghante baad dobara bhejo - limit khulne par report aa jayegi!")
            context.user_data.pop("mode", None)
            return
        if not d:
            refund_trial(uid)
            await st.edit_text("@" + code(u) + " nahi mila. Sahi username bhejo (trial wapas).", parse_mode=HTML)
            context.user_data.pop("mode", None)
            return
        NL = chr(10)
        pv = "PRIVATE" if d["private"] else "PUBLIC"
        vf = "VERIFIED ✅" if d["verified"] else "NOT VERIFIED ❌"
        cap = NL.join(["📸 <b>INSTAGRAM REPORT</b>",
            "Username: @" + hesc(d["username"]),
            "Name: " + hesc(d["name"]),
            "ID: " + code(d["uid"]),
            pv + " | " + vf,
            "Followers: " + str(d["followers"]) + " | Following: " + str(d["following"]) + " | Posts: " + str(d["posts"]),
            "Bio: " + (hesc(d["bio"][:300]) if d["bio"] else "-")])
        pic = None
        if d["pic"]:
            try:
                _r = await asyncio.to_thread(lambda: requests.get(d["pic"], timeout=15))
                if _r.status_code == 200 and len(_r.content) > 5000:
                    pic = _r.content
            except Exception:
                pic = None
        if pic:
            bio = io.BytesIO(pic)
            bio.name = "insta_dp.jpg"
            bio.seek(0)
            await update.message.reply_photo(photo=bio, caption=cap, reply_markup=BACK, parse_mode=HTML)
            try:
                await st.delete()
            except Exception:
                pass
        else:
            await st.edit_text(cap, reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "ifsc":
        c = text.replace(" ", "").upper()
        if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", c):
            await update.message.reply_text("⚠️ Sahi IFSC bhejo (jaise HDFC0001234):\nFormat: 4 letters + 0 + 6 characters")
            return
        if not await use_or_block(uid, update):
            return
        await act(context, update.effective_chat.id, "typing")
        try:
            d = await asyncio.to_thread(ifsc_lookup, c)
        except Exception:
            d = None
        if not d:
            refund_use(uid)
            await update.message.reply_text("⚠️ Ye IFSC galat lag raha hai. Sahi code bhejo (limit wapas ✅):")
            return
        await update.message.reply_text(
            f"🏦 <b>IFSC DETAILS</b> ✅\n━━━━━━━━━━━━━━━\n"
            f"🏛️ Bank: <b>{hesc(d.get('BANK', '-'))}</b>\n"
            f"🏢 Branch: <b>{hesc(d.get('BRANCH', '-'))}</b>\n"
            f"🔖 IFSC: {code(c)}\n"
            f"🏙️ City: {hesc(d.get('CITY', '-'))} • {hesc(d.get('STATE', '-'))}\n"
            f"📍 {hesc(str(d.get('ADDRESS', '-'))[:300])}\n"
            f"📞 {hesc(str(d.get('CONTACT', '-') or '-'))}",
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "pin":
        p = text.replace(" ", "")
        if not re.match(r"^[1-9][0-9]{5}$", p):
            await update.message.reply_text("⚠️ Sahi 6-digit pincode bhejo (jaise 834001):")
            return
        if not await use_or_block(uid, update):
            return
        await act(context, update.effective_chat.id, "typing")
        try:
            d = await asyncio.to_thread(pin_lookup, p)
        except Exception:
            d = None
        if not d:
            refund_use(uid)
            await update.message.reply_text("⚠️ Pincode nahi mila. Sahi pincode bhejo (limit wapas ✅):")
            return
        offices = d.get("PostOffice", []) or []
        o0 = offices[0] if offices else {}
        olist = "".join(f"\n{i + 1}. {hesc(o.get('Name', '-')[:30])} ({hesc(o.get('BranchType', '')[:12])})"
                        for i, o in enumerate(offices[:6]))
        await update.message.reply_text(
            f"📮 <b>PINCODE {code(p)}</b>\n━━━━━━━━━━━━━━━\n"
            f"🏛️ District: <b>{hesc(o0.get('District', '-'))}</b>\n"
            f"🗺️ State: <b>{hesc(o0.get('State', '-'))}</b>\n"
            f"📬 Post offices ({len(offices)}):{olist}\n"
            + (f"\n<i>+{len(offices) - 6} aur...</i>" if len(offices) > 6 else ""),
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "linkcheck":
        if not await use_or_block(uid, update):
            return
        await act(context, update.effective_chat.id, "typing")
        if " " in text or "." not in text:
            refund_use(uid)
            await update.message.reply_text("⚠️ Sahi link bhejo:")
            return
        st = await update.message.reply_text("🔍 <i>Link check ho raha hai...</i>", parse_mode=HTML)
        res = await asyncio.to_thread(link_check, text)
        fl = "".join(f"\n• {f}" for _, f in res["findings"]) or "\n• Koi dikkat nahi mili ✅"
        ch = ""
        if len(res["chain"]) > 1:
            ch = "\n\n🔀 <b>Redirect chain:</b>" + "".join(
                f"\n{i + 1}. {hesc(u[:70])}" for i, (_, u) in enumerate(res["chain"][:5])
            )
        await st.edit_text(
            f"🔍 <b>LINK REPORT</b>\n━━━━━━━━━━━━━━━\n🎯 Final: {code(res['final'][:200])}\n{fl}\n\n<b>{res['verdict']}</b>{ch}\n\n<i>Ye basic check hai — anjaan links par paise/password kabhi mat do! 🙏</i>",
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "linkbypass":
        if not await use_or_block(uid, update):
            return
        await act(context, update.effective_chat.id, "typing")
        if " " in text or "." not in text:
            refund_use(uid)
            await update.message.reply_text("⚠️ Sahi link bhejo:")
            return
        st = await update.message.reply_text("🔓 <i>Original link nikal raha hoon...</i>", parse_mode=HTML)
        status, final, chain = await asyncio.to_thread(bypass_link, text)
        if status == "OK":
            await st.edit_text(
                f"🔓 <b>ORIGINAL LINK MIL GAYA!</b> ✅\n\n🎯 {code(final[:300])}\n\n"
                f"🔀 {len(chain)} hops me khula\n👆 <i>Tap karke copy karo!</i>",
                reply_markup=BACK, parse_mode=HTML)
        elif status == "ERR":
            refund_use(uid)
            await st.edit_text(final)
        else:
            await st.edit_text(
                "⏳ <b>Ye link timer/JS protected hai</b> (arolinks/vplinks style) — bot se bypass nahi hua.\n\n"
                "✅ <b>Tareeka:</b>\n1️⃣ Link ko Chrome me kholo\n2️⃣ 5-10 sec wait → Continue dabao\n"
                "3️⃣ Jo final link mile, wo yahan bhejo — main check/download kar dunga! 🙏",
                reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "rto":
        v = parse_vehicle(text)
        if not v:
            await update.message.reply_text("⚠️ Sahi gaadi number bhejo (jaise JH01AB1234):")
            return
        if not await use_or_block(uid, update):
            return
        if not v["state"]:
            await update.message.reply_text("⚠️ State code galat hai. Sahi number bhejo:")
            return
        off = v["rto"] or f"RTO {v['code']} (code valid ✅)"
        await update.message.reply_text(
            f"🚗 <b>VEHICLE RTO INFO</b>\n━━━━━━━━━━━━━━━\n"
            f"🔢 Number: {code(v['number'])}\n"
            f"🗺️ State: <b>{hesc(v['state'])}</b>\n"
            f"🏢 RTO Office: <b>{hesc(off)}</b>\n━━━━━━━━━━━━━━━\n"
            f"📌 <b>Maalik/gaadi details ke liye</b> (free sarkari apps):\n"
            f"1️⃣ <b>mParivahan</b> app → RC Details\n"
            f"2️⃣ <b>Digilocker</b> → apni gaadi ka RC\n"
            f"<i>Privacy rule se owner data sirf sarkari app me milta hai. 🙏</i>",
            reply_markup=BACK, parse_mode=HTML)
        context.user_data.pop("mode", None)
        return

    if mode == "int_p":
        try:
            p = float(text.replace(",", "").replace("₹", "").strip())
            if p <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi paisa bhejo (jaise 50000):")
            return
        context.user_data["int_p"] = p
        context.user_data["mode"] = "int_r"
        await update.message.reply_text(f"💰 Paisa: ₹{inr(p)}\n\nAb saal ka Rate % bhejo:\n(jaise: 8)")
        return
    if mode == "int_r":
        try:
            r = float(text.replace("%", "").strip())
            if r < 0 or r > 100:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi rate bhejo (jaise 8):")
            return
        context.user_data["int_r"] = r
        context.user_data["mode"] = "int_t"
        await update.message.reply_text("⏳ Ab kitne SAAL ke liye? (jaise: 5)")
        return
    if mode == "int_t":
        try:
            t = float(text.strip())
            if t <= 0 or t > 50:
                raise ValueError
        except Exception:
            await update.message.reply_text("⚠️ Sahi saal bhejo (jaise 5):")
            return
        p = context.user_data.get("int_p", 0)
        r = context.user_data.get("int_r", 0)
        if not p:
            await update.message.reply_text("⚠️ Server restart ho gaya tha. Interest grid se dobara shuru karo (limit nahi kata).")
            for k in ("mode", "int_type", "int_p", "int_r", "int_t"):
                context.user_data.pop(k, None)
            return
        if context.user_data.get("int_type") == "CI":
            context.user_data["int_t"] = t
            context.user_data["mode"] = "int_f"
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Yearly", callback_data="int_f:1"),
                 InlineKeyboardButton("Half-yearly", callback_data="int_f:2")],
                [InlineKeyboardButton("Quarterly", callback_data="int_f:4"),
                 InlineKeyboardButton("Monthly", callback_data="int_f:12")],
            ])
            await update.message.reply_text("🔁 Interest kitni baar judta hai? (Compounding):", reply_markup=kb)
            return
        if not await use_or_block(uid, update):
            return
        await send_interest_result(update, p, r, t, 1)
        for k in ("mode", "int_type", "int_p", "int_r", "int_t"):
            context.user_data.pop(k, None)
        return

    if mode == "tts_text":
        if len(text) < 2:
            await update.message.reply_text("⚠️ Thoda lamba text bhejo:")
            return
        if not await trial_or_block(uid, update, "Text to Speech"):
            context.user_data.pop("mode", None)
            return
        voice = context.user_data.get("tts_voice", "hi-IN-SwaraNeural")
        vname = context.user_data.get("tts_name", "Voice")
        rate = context.user_data.get("tts_rate", "+0%")
        pitch = context.user_data.get("tts_pitch", "+0Hz")
        await act(context, update.effective_chat.id, "upload_voice")
        st = await update.message.reply_text(f"🔊 <i>{hesc(vname)} bol rahi hai... thoda ruko! 🎙️</i>", parse_mode=HTML)
        path = os.path.join(tempfile.gettempdir(), f"tts_{uid}_{random.randint(1, 99999)}.mp3")
        ok = await tts_make(text, voice, rate, pitch, path)
        if not ok or not os.path.exists(path):
            refund_trial(uid)
            await st.edit_text("⛔ Voice nahi ban payi. Thodi der baad try karo (trial wapas ✅).")
            context.user_data.pop("mode", None)
            return
        has_dev = bool(re.search(r"[\u0900-\u097F]", text))
        is_hv = voice.startswith("hi-")
        hint = ""
        if has_dev and not is_hv:
            hint = "\n💡 <i>Hindi text Hindi voice me best lagegi!</i>"
        elif not has_dev and is_hv and re.search(r"[A-Za-z]", text):
            hint = "\n💡 <i>English text English voice me best lagega!</i>"
        try:
            af = open(path, "rb")
            try:
                await update.message.reply_audio(
                    audio=af, title=f"{vname} - Utility Duniya",
                caption=f"🔊 <b>Voice ready!</b> ({hesc(vname)})\n📝 {hesc(text[:150])}{hint}",
                    reply_markup=BACK, parse_mode=HTML)
            finally:
                try:
                    af.close()
                except Exception:
                    pass
            try:
                await st.delete()
            except Exception:
                pass
        except Exception as e:
            await st.edit_text(f"⛔ Bhejne me dikkat: {str(e)[:120]}")
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
        context.user_data.pop("mode", None)
        return

    if mode == "int_f":
        await update.message.reply_text("🔁 Upar buttons se compounding chuno (Yearly/Monthly...).")
        return
    if mode in ("pdf", "pp"):
        await update.message.reply_text("📸 Photo bhejo (text nahi). /cancel se wapas jao.")
        return


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_username(uid, update.effective_user.username or "")
    if is_banned(uid):
        await update.message.reply_text(BAN_MSG)
        return
    mode = context.user_data.get("mode")
    if not mode:
        await update.message.reply_text("👇 Neeche grid icon (▦) dabao — saare tools khulenge!",
                                        reply_markup=kb_for(uid))
        return
    if not await ensure_joined(update, context):
        return

    if mode == "pay":
        if not ADMIN_ID:
            await update.message.reply_text("⚠️ Admin set nahi hai. /cancel dabao.")
            return
        days = context.user_data.get("plan_days", 30)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"✅ Approve {days}din", callback_data=f"ap:{uid}:{days}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"dc:{uid}"),
        ]])
        uname = f"@{update.effective_user.username}" if update.effective_user.username else "(username nahi hai)"
        try:
            await update.message.forward(ADMIN_ID)
            await context.bot.send_message(
                ADMIN_ID,
                f"💰 Naya Premium Payment!\n\n👤 Naam: {update.effective_user.first_name}\n🔗 {uname}\n🆔 ID: {uid}\n📦 Plan: {days} din\n\nUpar screenshot dekho, verify karke Approve/Reject dabao 👇",
                reply_markup=kb)
            await update.message.reply_text("✅ Screenshot admin ko bhej diya! Verify hote hi Premium active ho jayega (kuch min). 🙏", reply_markup=BACK)
        except Exception as e:
            log.warning("admin forward fail: %s", e)
            await update.message.reply_text("⚠️ Kuch gadbad hui, screenshot dobara bhejo.")
        context.user_data.pop("mode", None)
        return

    if mode == "idfind":
        fo = getattr(update.message, "forward_origin", None)
        su = getattr(fo, "sender_user", None) if fo else None
        if su is not None:
            if not await use_or_block(uid, update):
                return
            nm = f"{su.first_name or ''} {su.last_name or ''}".strip() or "User"
            un = f"@{su.username}" if su.username else "—"
            await update.message.reply_text(
                f"🆔 <b>ID Mil Gayi!</b> ✅\n\n👤 Naam: {hesc(nm)}\n🔗 {hesc(un)}\n🆔 User ID: {code(su.id)}",
                reply_markup=BACK, parse_mode=HTML)
            context.user_data.pop("mode", None)
        else:
            await update.message.reply_text("📩 Kisi ka message FORWARD karo (photo wala bhi chalega), ya @username bhejo:")
        return

    if mode == "setcookies":
        if not is_admin(uid):
            context.user_data.pop("mode", None)
            return
        doc = update.message.document
        if not doc or not (doc.file_name or "").lower().endswith((".txt", ".json")):
            await update.message.reply_text("cookies FILE bhejo (.txt ya .json document).")
            return
        try:
            tf = await context.bot.get_file(doc.file_id)
            cdata = bytes(await tf.download_as_bytearray())
        except Exception:
            await update.message.reply_text("Download fail, file dobara bhejo.")
            return
        _fn = (doc.file_name or "").lower()
        if _fn.endswith(".json") or cdata.lstrip()[:1] == b"[":
            _conv = cookies_json_to_netscape(cdata)
            if not _conv:
                await update.message.reply_text("JSON samajh nahi aaya. Cookie-Editor se dobara Export karke bhejo.")
                return
            cdata = _conv
        if b"youtube" not in cdata.lower() and b"#HttpOnly" not in cdata:
            await update.message.reply_text("Ye YouTube cookies file nahi lag rahi. Sahi file bhejo.")
            return
        try:
            with open(COOKIE_FILE, "wb") as fh:
                fh.write(normalize_cookies(cdata))
        except Exception as e:
            await update.message.reply_text("Save fail: " + str(e)[:120])
            return
        _n = cookies_jar_count(COOKIE_FILE)
        if _n <= 0:
            try:
                os.remove(COOKIE_FILE)
            except Exception:
                pass
            await update.message.reply_text("Cookies TOOTI lag rahi (0 login mile). Dobara Export karke bhejo.")
            context.user_data.pop("mode", None)
            return
        await update.message.reply_text("Cookies save ho gayi ✅ (" + str(_n) + " login)! Ab YT download try karo.")
        context.user_data.pop("mode", None)
        return

    if mode not in ("pdf", "pp"):
        await update.message.reply_text("👇 Neeche grid icon (▦) dabao — saare tools khulenge!",
                                        reply_markup=kb_for(uid))
        return

    try:
        f = None
        if update.message.photo:
            f = await context.bot.get_file(update.message.photo[-1].file_id)
        elif update.message.document and (update.message.document.mime_type or "").startswith("image/"):
            if (update.message.document.file_size or 0) > 12 * 1024 * 1024:
                await update.message.reply_text("⚠️ Photo 12MB se chhoti bhejo.")
                return
            f = await context.bot.get_file(update.message.document.file_id)
        if not f:
            await update.message.reply_text("⚠️ Photo bhejo (PDF/file nahi).")
            return
        data = bytes(await f.download_as_bytearray())
        Image.open(io.BytesIO(data)).verify()
    except Exception:
        await update.message.reply_text("⚠️ Photo kholne me dikkat. Dusri photo bhejo:")
        return

    if mode == "pdf":
        pages = context.user_data.setdefault("pdf_pages", [])
        if len(pages) >= 10:
            await update.message.reply_text("⚠️ Max 10 pages! Neeche ✅ dabao:")
            return
        try:
            img = Image.open(io.BytesIO(data))
            pages.append(await asyncio.to_thread(normalize_page, img))
        except Exception:
            await update.message.reply_text("⚠️ Photo kholne me dikkat. Dusri bhejo:")
            return
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Bas! PDF Banao ({len(pages)} pages)", callback_data="pdf_done")]])
        await update.message.reply_text(f"📄 Page {len(pages)} add ho gaya! ✅\n\nAur photo bhejo ya neeche ✅ dabao 👇", reply_markup=kb)
        return

    if mode == "pp":
        if not await use_or_block(uid, update):
            return
        await act(context, update.effective_chat.id, "upload_photo")
        st = await update.message.reply_text("🪪 <i>Passport photo ban rahi hai...</i>", parse_mode=HTML)
        try:
            single, sheet = await asyncio.to_thread(passport_make, data)
        except Exception:
            refund_use(uid)
            await st.edit_text("⚠️ Photo samajh nahi aayi. Seedhi, saaf photo bhejo:")
            return
        b1 = io.BytesIO(single)
        b1.name = "passport_hd.jpg"
        b1.seek(0)
        b2 = io.BytesIO(sheet)
        b2.name = "passport_print_4x6.jpg"
        b2.seek(0)
        await update.message.reply_document(document=b1, caption="🪪 <b>Passport Photo HD</b> (3.5×4.5cm) ✅",
                                            parse_mode=HTML)
        await update.message.reply_document(
            document=b2,
            caption="🖨️ <b>Print Sheet (4×6 inch, 9 copies)</b> ✅\n\n📌 Kisi bhi studio me 4×6 photo paper par print karwa lo — 9 photos ek saath!",
            reply_markup=BACK, parse_mode=HTML)
        try:
            await st.delete()
        except Exception:
            pass
        context.user_data.pop("mode", None)
        return


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Error: %s", context.error)

# ---------------- MAIN ----------------
async def _post_init(app: Application):
    try:
        await app.bot.set_my_commands([])
        log.info("Commands cleared - sirf grid keyboard rahega")
    except Exception as e:
        log.warning("clear commands fail: %s", e)


def _keepalive():
    # Self-ping: free server ko sleep hone se rokta hai (UptimeRobot jaisa, bot ke andar hi)
    import threading
    def _loop():
        while True:
            try:
                time.sleep(600)
                if WEBHOOK_URL:
                    requests.get(WEBHOOK_URL.rstrip("/"), timeout=10)
            except Exception:
                pass
    try:
        threading.Thread(target=_loop, daemon=True).start()
        log.info("keepalive on (10 min self-ping)")
    except Exception:
        pass


def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN nahi mila! Render Environment me BOT_TOKEN=... dalo.")
    _ck = os.getenv("YT_COOKIES", "")
    if _ck.strip():
        try:
            with open(COOKIE_FILE, "w", encoding="utf-8") as fh:
                fh.write(_ck.replace("\\n", "\n"))
            try:
                _raw = open(COOKIE_FILE, "rb").read()
                if _raw.lstrip()[:1] == b"[":
                    _conv = cookies_json_to_netscape(_raw)
                    if _conv:
                        open(COOKIE_FILE, "wb").write(_conv)
            except Exception:
                pass
            _raw0 = open(COOKIE_FILE, "rb").read()
            _raw0 = normalize_cookies(_raw0)
            open(COOKIE_FILE, "wb").write(_raw0)
            log.info("YT cookies env jar=%s", cookies_jar_count(COOKIE_FILE))
        except Exception as e:
            log.warning("cookies env fail: %s", e)
    db().close()
    app = (Application.builder().token(BOT_TOKEN).post_init(_post_init)
           .concurrent_updates(True)
           .connect_timeout(20).read_timeout(60).write_timeout(180).pool_timeout(60)
           .build())

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("account", cmd_account))
    app.add_handler(CommandHandler("refer", cmd_refer))
    app.add_handler(CommandHandler("premium", cmd_premium))
    app.add_handler(CommandHandler("qr", cmd_qr))
    app.add_handler(CommandHandler("password", pwd_entry))
    app.add_handler(CommandHandler("pdf", cmd_pdf))
    app.add_handler(CommandHandler("short", cmd_short))
    app.add_handler(CommandHandler("yt", cmd_yt))
    app.add_handler(CommandHandler("ytdl", cmd_ytdl))
    app.add_handler(CommandHandler("emi", cmd_emi))
    app.add_handler(CommandHandler("age", cmd_age))
    app.add_handler(CommandHandler("upi", cmd_upi))
    app.add_handler(CommandHandler("id", cmd_idfind))
    app.add_handler(CommandHandler("tts", tts_entry))
    app.add_handler(CommandHandler("ifsc", cmd_ifsc))
    app.add_handler(CommandHandler("pin", cmd_pin))
    app.add_handler(CommandHandler("pp", cmd_pp))
    app.add_handler(CommandHandler("link", cmd_link))
    app.add_handler(CommandHandler("bypass", cmd_bypass))
    app.add_handler(CommandHandler("interest", int_entry))
    app.add_handler(CommandHandler("rto", cmd_rto))
    app.add_handler(CommandHandler("insta", cmd_insta))
    app.add_handler(CommandHandler("cktest", cmd_cktest))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("setcookies", cmd_setcookies))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.ATTACHMENT, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)

    _keepalive()
    if WEBHOOK_URL:
        port = int(os.getenv("PORT", "10000"))
        log.info("Webhook mode on port %s", port)
        app.run_webhook(listen="0.0.0.0", port=port, url_path=BOT_TOKEN,
                        webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}")
    else:
        log.info("Polling mode (WEBHOOK_URL khali hai)")
        app.run_polling()


if __name__ == "__main__":
    main()
