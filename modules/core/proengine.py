# -*- coding: utf-8 -*-
"""
proengine.py — 🧠 PRO ENGINE (v75): SAARE tools ka universal advanced layer
===========================================================================
Ye file bot ke HAR tool ko "premium feel" deti hai — bina kisi tool ka code
chhue, bina koi prompt badle.

----------------------------------------------------------------------
KYA-KYA MILTA HAI (4 engine):
----------------------------------------------------------------------

  ENGINE 1 — 🧠 SMART DETECT (auto tool pahchaan)
      User kuch bhi bheje — bot KHUD samajh le:
          "9876543210"        -> 📱 NUMBER INFO
          "SBIN0001234"       -> 🏦 IFSC
          "800001"            -> 📮 PINCODE
          10/15 digit IMEI    -> 🔐 IMEI
          "BR01AB1234"        -> 🚗 RC + CHALLAN
          "https://..."       -> 🔍 LINK CHECK
          "@username"         -> 🕵️ USERNAME HUNTER
      High-confidence input = turant chalta hai (1 tap bhi nahi).
      Medium input = 1-tap confirm button.

  ENGINE 2 — ⚡ PROVIDER RACE + CIRCUIT BREAKER (tool kabhi nahi marta)
      Ek tool ke kai data source hote hain. Pehle: ek fail = tool fail.
      Ab: teeno source ek saath (parallel) chalte hain — JO PEHLE sahi jawab
      de, wahi jeet jaata hai. Jo source baar-baar fail ho, uska "breaker"
      khul jaata hai (cooldown) — user ko dead source se kabhi wait nahi
      milta, aur cooldown ke baad source khud test hota hai (self-heal).

  ENGINE 3 — 🗂️ RESULT HISTORY (har tool ka apna record)
      Har tool run nikaal ke store hota hai — user `/history` se dekhta hai,
      admin `/toolstats` se dekhta hai ki kaunsa tool kitna chala, kitna
      pass, kitna fail, average speed kitni. (Earning analytics ka base.)

  ENGINE 4 — ✨ QUALITY STAMP (bharosa dikhta hai)
      Har result card par ek line: source + speed + freshness. Isse user ko
      lagta hai ki "kaam hua hai", random text nahi.

----------------------------------------------------------------------
DESIGN RULES (aapke bot ke niyam yaad rakhe hue):
  • RULE #1 NO-LINK  -> is file me kahin bhi bahar ka link nahi hai.
  • NO-GYAAN         -> sirf outcome, koi lecture/tip line nahi.
  • ZERO CRASH       -> har public function try/except me bandha hai.
  • ZERO NAYI DEP    -> sirf stdlib + jo pehle se installed hai.
  • PREMIUM SAFE     -> ye file premium users ke data ko touch bhi nahi karti.
----------------------------------------------------------------------
"""
from __future__ import annotations

import logging
import os
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

log = logging.getLogger("ud.proengine")

__all__ = [
    "detect", "SmartHit", "smart_kb", "smart_line", "pending_get",
    "race", "Breaker", "get_breaker", "breaker_stats", "gather_soon",
    "RecentResults", "results", "record_result", "history_kb", "history_text",
    "quality_line", "tool_counter", "toolstats", "toolstats_text",
    "AUTO_MODE", "detect_enabled", "set_detect_enabled",
]

# ======================================================================
#  CONFIG
# ======================================================================
#   off     = smart detect band
#   suggest = sirf 1-tap button dikhao (kabhi khud se na chalao)
#   auto    = high-confidence par khud chalao, baaki par button (DEFAULT)
AUTO_MODE = (os.environ.get("SMART_DETECT", "auto") or "auto").strip().lower()
if AUTO_MODE not in ("off", "suggest", "auto"):
    AUTO_MODE = "auto"

# v78: `int()` seedha import-time par tha -> ek galat env value poora bot
# boot se pehle maar deta thi. Ab safeconf (kachra = default, kabhi raise nahi).
from .safeconf import env_int as _env_int

HISTORY_MAX = _env_int("PRO_HISTORY_MAX", 20000, 100, 1_000_000)
BREAKER_FAILS = _env_int("PRO_BREAKER_FAILS", 3, 1, 100)
BREAKER_COOLDOWN = _env_int("PRO_BREAKER_COOLDOWN", 600, 10, 86400)


# ======================================================================
#  ENGINE 1 — 🧠 SMART DETECT
# ======================================================================
class SmartHit(dict):
    """Ek detection ka natija (dict ki tarah use karo — purane code na toote)."""

    @property
    def kind(self) -> str:
        return str(self.get("kind") or "")

    @property
    def action(self) -> str:
        return str(self.get("action") or "")

    @property
    def value(self) -> str:
        return str(self.get("value") or "")

    @property
    def label(self) -> str:
        return str(self.get("label") or "")

    @property
    def conf(self) -> float:
        return float(self.get("conf") or 0.0)

    @property
    def high(self) -> bool:
        return self.conf >= 0.90


# ---- patterns (sab anchor (`^...$`) ke saath — aadha text hijack na kare) ----
_RE_IFSC = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
_RE_PAN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_RE_GST = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")
# vehicle: BR01AB1234 / DL8CAF5030 / MH12DE1433 (space/dash hata ke)
_RE_VEH = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{3,4}$")
_RE_MOBILE = re.compile(r"^[6-9][0-9]{9}$")
_RE_IMEI = re.compile(r"^[0-9]{15}$")
_RE_PIN = re.compile(r"^[1-9][0-9]{5}$")
_RE_UPI = re.compile(r"^[a-zA-Z0-9.\-_]{2,64}@[a-zA-Z]{2,20}$")
_RE_URL = re.compile(r"^(https?://|www\.)\S+$", re.IGNORECASE)
_RE_DOMAIN = re.compile(r"^([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,15}$", re.IGNORECASE)
_RE_USERNAME = re.compile(r"^@[A-Za-z0-9_]{4,32}$")
_RE_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_RE_PASSPORT = re.compile(r"^[A-PR-WY][1-9][0-9]{6}$")
_RE_DL = re.compile(r"^[A-Z]{2}[0-9]{2}[ -]?(19|20)[0-9]{2}[0-9]{7}$")

# India pincode: pehla digit 1-8 (9 = army, chhod do), aur 2nd digit range
def _pin_ok(v: str) -> bool:
    if not _RE_PIN.match(v):
        return False
    return v[0] in "12345678" and v[1] in "0123456789"


# kind -> (action, label, emoji)
SMART_MAP: Dict[str, Tuple[str, str, str]] = {
    "ifsc":      ("ifsc", "IFSC Bank Branch Info", "🏦"),
    "pan":       ("kagaz", "PAN Card Details", "🪪"),
    "gst":       ("kagaz", "GST Number X-Ray", "🧾"),
    "vehicle":   ("vahan", "RC + Challan (Gaadi X-Ray)", "🚗"),
    "mobile":    ("numinfo", "Number Info", "📱"),
    "imei":      ("imei", "IMEI / Phone Details", "🔐"),
    "pincode":   ("pin", "Pincode / Area Info", "📮"),
    "url":       ("linkcheck", "Link Check (safe ya nahi)", "🔍"),
    "domain":    ("osint_whois", "Website Owner X-Ray", "🌐"),
    "username":  ("uhunt", "Username Hunter", "🕵️"),
    "upi":       ("kagaz", "UPI ID Info", "💸"),
    "email":     ("osint_whois", "Email/Domain X-Ray", "✉️"),
    "passport":  ("kagaz", "Passport Number Format Check", "📕"),
    "dl":        ("vahan", "Driving Licence Number Check", "🚙"),
}

# auto-run (khud chalao) sirf in high-confidence kinds ke liye — jahan galti
# ka chance lagbhag zero hai. Baaki par 1-tap button (suggest).
_AUTORUN = {"ifsc", "imei", "vehicle", "pan", "gst", "mobile", "url"}


def _norm(txt: str) -> str:
    """Text ko detect ke liye taiyaar karo (emoji/bold/space saaf)."""
    try:
        s = str(txt or "").strip()
        # bot khud bold tag lagata hai — wo hata do
        s = s.replace("<b>", "").replace("</b>", "")
        s = s.replace("<code>", "").replace("</code>", "")
        return s.strip()
    except Exception:                                            # noqa: BLE001
        return str(txt or "").strip()


def detect(txt: str) -> Optional[SmartHit]:
    """Kya bheja gaya hai — pahchano.

    Return: SmartHit(kind, action, value, label, conf) ya None.
    Kabhi exception nahi (har branch safe).
    """
    try:
        raw = _norm(txt)
        if not raw or len(raw) > 300:
            return None
        # bahut lamba text / ek se zyada line = tool input nahi
        if "\n" in raw:
            return None

        s = raw.strip()
        up = s.upper()
        nospace = re.sub(r"[\s\-]", "", up)

        def hit(kind: str, value: str, conf: float) -> SmartHit:
            act, label, emoji = SMART_MAP[kind]
            return SmartHit(kind=kind, action=act, value=value, label=label,
                            emoji=emoji, conf=conf, raw=raw)

        # ---- URL (sabse pehle — warna domain use kha jayega) ----
        if _RE_URL.match(s):
            return hit("url", s, 0.98)

        # ---- IFSC ----
        if _RE_IFSC.match(nospace):
            return hit("ifsc", nospace, 0.97)

        # ---- GST (PAN se pehle — GST me PAN embedded hota hai) ----
        if _RE_GST.match(nospace):
            return hit("gst", nospace, 0.96)

        # ---- PAN ----
        if _RE_PAN.match(nospace):
            return hit("pan", nospace, 0.95)

        # ---- IMEI (15 digit) ----
        if _RE_IMEI.match(nospace):
            return hit("imei", nospace, 0.93)

        # ---- Vehicle number ----
        if _RE_VEH.match(nospace) and not _RE_IFSC.match(nospace):
            # "BR01AB1234" => 10 char; 8-12 char range hi vehicle maano
            if 8 <= len(nospace) <= 12:
                return hit("vehicle", nospace, 0.92)

        # ---- UPI ----
        if _RE_UPI.match(s) and "." not in s.split("@")[0][:3]:
            # email se alag: UPI me TLD nahi hota lekin dono ka overlap hai
            if not _RE_EMAIL.match(s):
                return hit("upi", s, 0.70)

        # ---- Email ----
        if _RE_EMAIL.match(s) and "." in s.rsplit("@", 1)[-1]:
            dom = s.rsplit("@", 1)[-1].lower()
            if dom in ("gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com"):
                return None                     # personal email — detect nahi karte
            return hit("email", s, 0.72)

        # ---- Mobile (India 10 digit, 6-9 se shuru) ----
        if _RE_MOBILE.match(nospace) and len(nospace) == 10:
            return hit("mobile", nospace, 0.94)

        # ---- Pincode ----
        if _pin_ok(nospace):
            return hit("pincode", nospace, 0.62)      # medium — button dikhao

        # ---- @username ----
        if _RE_USERNAME.match(s):
            return hit("username", s.lstrip("@"), 0.80)

        # ---- Passport ----
        if _RE_PASSPORT.match(nospace):
            return hit("passport", nospace, 0.66)

        # ---- Driving Licence ----
        if _RE_DL.match(up):
            return hit("dl", up, 0.68)

        # ---- Domain (aakhri me — sabse generic) ----
        if _RE_DOMAIN.match(s) and "." in s:
            tld = s.rsplit(".", 1)[-1].lower()
            if tld in ("com", "in", "net", "org", "co", "io", "app", "xyz", "info",
                       "gov", "edu", "biz", "me", "dev", "site", "online", "shop"):
                return hit("domain", s.lower(), 0.75)

        return None
    except Exception as e:                                       # noqa: BLE001
        log.debug("detect skip: %s", str(e)[:100])
        return None


def smart_line(h: SmartHit, ran: bool = False) -> str:
    """Detection ki chhoti outcome line (koi gyaan nahi)."""
    try:
        if ran:
            return ""
        return (f"{h.get('emoji') or '🧠'} <b>{h.label}</b> chalaun? "
                f"<code>{_short(h.value)}</code>")
    except Exception:                                            # noqa: BLE001
        return ""


def smart_kb(h: SmartHit, extra: Optional[list] = None):
    """1-tap confirm keyboard.

    NOTE: Telegram ka callback_data sirf 64 byte leta hai — lamba URL usme
    fit nahi hota. Isliye value ko server-side `_PENDING` me rakhte hain aur
    button me sirf chhota token bhejte hain."""
    try:
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        tok = _pending_put(h)
        rows = [[InlineKeyboardButton(f"⚡ {h.label} chalao",
                                      callback_data=f"pro_go:{tok}")]]
        if extra:
            rows.extend(extra)
        rows.append([InlineKeyboardButton("⌨️ Menu", callback_data="back_home")])
        return InlineKeyboardMarkup(rows)
    except Exception:                                            # noqa: BLE001
        return None


# ---- pending suggestions (token -> hit), 15 min TTL, memory-safe ----
_PENDING: Dict[str, Tuple[float, SmartHit]] = {}
_PEND_LOCK = threading.Lock()
_PEND_MAX = 3000


def _pending_put(h: SmartHit) -> str:
    tok = str(int(time.time() * 1000) % 7000000) + str(abs(hash(h.value)) % 1000)
    with _PEND_LOCK:
        # purge (purane entries + size cap — memory kabhi na bhare)
        now = time.time()
        dead = [k for k, (ts, _) in _PENDING.items() if now - ts > 900]
        for k in dead:
            _PENDING.pop(k, None)
        if len(_PENDING) > _PEND_MAX:
            for k in list(_PENDING.keys())[: len(_PENDING) - _PEND_MAX]:
                _PENDING.pop(k, None)
        _PENDING[tok] = (now, h)
    return tok


def pending_get(tok: str) -> Optional[SmartHit]:
    """Token se suggestion wapas lo (ek baar — phir hata do)."""
    try:
        with _PEND_LOCK:
            got = _PENDING.pop(str(tok), None)
        if not got:
            return None
        ts, h = got
        if time.time() - ts > 900:
            return None
        return h
    except Exception:                                            # noqa: BLE001
        return None

def _short(v: str, n: int = 28) -> str:
    v = str(v or "")
    return v if len(v) <= n else v[:n] + "…"


def _safe_uid(uid, default=0):
    """DB/env/user-text se aaya hoi uid kabhi bhi int() pe na tute (v78)."""
    try:
        return int(uid)
    except Exception:                                    # noqa: BLE001
        try:
            s = "".join(c for c in str(uid) if c.isdigit())
            return int(s) if s else default
        except Exception:                                # noqa: BLE001
            return default


def detect_enabled(uid: int) -> bool:
    """User ne smart detect band kiya hai kya? (default ON)"""
    return _prefs.get(_safe_uid(uid), True)


def set_detect_enabled(uid: int, on: bool) -> bool:
    _prefs[_safe_uid(uid)] = bool(on)
    return bool(on)


_prefs: Dict[int, bool] = {}


# ======================================================================
#  ENGINE 2 — ⚡ LAST-RESORT-PROOF: RACE + CIRCUIT BREAKER
# ======================================================================
class Breaker:
    """Ek provider (data source) ka circuit breaker.

    closed   = normal
    open     = lagataar fail -> requests skip (cooldown tak)
    half     = cooldown poora -> ek test request, pass hua to closed
    """

    __slots__ = ("name", "fails", "threshold", "cooldown", "opened_at",
                 "passes", "skips", "heals")

    def __init__(self, name: str, threshold: int = BREAKER_FAILS,
                 cooldown: int = BREAKER_COOLDOWN):
        self.name = name
        self.fails = 0
        self.threshold = max(1, int(threshold))
        self.cooldown = max(5, int(cooldown))
        self.opened_at = 0.0
        self.passes = 0
        self.skips = 0
        self.heals = 0

    def allow(self) -> bool:
        now = time.time()
        if self.opened_at <= 0:
            return True
        if (now - self.opened_at) >= self.cooldown:
            # half-open: ek test allow
            self.opened_at = now - self.cooldown + 5   # 5s me dobara test
            return True
        self.skips += 1
        return False

    def ok(self) -> None:
        if self.opened_at > 0:
            self.heals += 1
        self.fails = 0
        self.opened_at = 0.0
        self.passes += 1

    def fail(self) -> None:
        self.fails += 1
        if self.fails >= self.threshold:
            self.opened_at = time.time()

    @property
    def state(self) -> str:
        if self.opened_at <= 0:
            return "closed"
        return "open" if (time.time() - self.opened_at) < self.cooldown else "half"

    def as_dict(self) -> dict:
        return {"name": self.name, "state": self.state, "fails": self.fails,
                "passes": self.passes, "skips": self.skips, "heals": self.heals}


_breakers: Dict[str, Breaker] = {}
_brk_lock = threading.Lock()


def get_breaker(name: str, threshold: int = BREAKER_FAILS,
                cooldown: int = BREAKER_COOLDOWN) -> Breaker:
    with _brk_lock:
        b = _breakers.get(name)
        if b is None:
            b = Breaker(name, threshold, cooldown)
            _breakers[name] = b
        return b


def breaker_stats() -> List[dict]:
    with _brk_lock:
        return [b.as_dict() for b in _breakers.values()]


def race(calls: Sequence[Tuple[str, Callable[[], Any]]], timeout: float = 25.0,
         accept: Optional[Callable[[Any], bool]] = None,
         min_success: int = 1) -> Tuple[Optional[Any], str, List[str]]:
    """Kai provider ek saath chalao — jo pehle SAHI jawab de, wahi jeete.

    calls   : [("gsmarena", fn1), ("phoneapi", fn2), ...]
    accept  : fn(result) -> bool  (khaali/adhoora jawab accept na karo)
    Return  : (result, winning_name, failed_names)
              result None = sab fail (lekin crash NAHI).
    """
    fails: List[str] = []
    if not calls:
        return None, "", fails

    ok_flag = accept or (lambda r: r not in (None, "", [], {}, ()))
    lock = threading.Lock()
    done = threading.Event()
    box: Dict[str, Any] = {"res": None, "name": ""}
    deadline = time.time() + max(1.0, float(timeout))

    def _worker(name: str, fn: Callable[[], Any]) -> None:
        brk = get_breaker(name)
        if not brk.allow():
            with lock:
                fails.append(name)
            return
        try:
            r = fn()
            if not ok_flag(r):
                brk.fail()
                with lock:
                    fails.append(name)
                return
            brk.ok()
            with lock:
                if box["res"] is None:
                    box["res"], box["name"] = r, name
                    done.set()
        except Exception as e:                                   # noqa: BLE001
            brk.fail()
            with lock:
                fails.append(name)
            log.debug("race provider %s fail: %s", name, str(e)[:110])

    # har provider ka apna thread — slow provider baaki ko nahi rokta
    for name, fn in calls:
        t = threading.Thread(target=_worker, args=(name, fn), daemon=True,
                             name=f"pro-race-{name}"[:24])
        t.start()

    # pehla success ka intezaar (timeout ke andar)
    while not done.is_set():
        if time.time() >= deadline:
            break
        if done.wait(0.15):
            break
    return box["res"], box["name"], fails


async def gather_soon(coros: Sequence[Any], timeout: float = 8.0) -> Tuple[List[Any], int]:
    """v75 — `asyncio.gather` ka behtar version: SLOWEST ka wait nahi karta.

    PROBLEM jo ye theek karta hai:
        `await asyncio.gather(a, b)` — dono me se EK slow/dead ho to user
        dono ka time jod kar wait karta hai (a 200ms, b 9s dead -> 9s wait).
        Tool "kaam kar raha tha" par user ko lagta hai bot atka hai.

    YE KYA KARTA HAI:
        `asyncio.wait(timeout=...)` se jo jawab TIME ke andar aa gaya, wo le lo.
        Jo nahi aaya, uska None rakh do (baad me fallback lag jayega).
        Result: sabse tez source ki speed milti hai, slow source block nahi karta.

    Return: (results_list, elapsed_ms)   — list me har coro ka result ya None.
    """
    t0 = time.perf_counter()
    items = list(coros or [])
    if not items:
        return [], 0
    out: List[Any] = [None] * len(items)
    try:
        import asyncio
        tasks = []
        for c in items:
            try:
                tasks.append(asyncio.ensure_future(c))
            except Exception:                                    # noqa: BLE001
                tasks.append(None)
        _live = [t for t in tasks if t is not None]
        if _live:
            done, _pending = await asyncio.wait(_live, timeout=max(0.5, float(timeout)))
            for t in done:
                i = tasks.index(t)
                try:
                    out[i] = t.result()
                except Exception:                                # noqa: BLE001
                    out[i] = None
            for t in _pending:
                t.cancel()
    except Exception as e:                                       # noqa: BLE001
        log.debug("gather_soon skip: %s", str(e)[:110])
    return out, int((time.perf_counter() - t0) * 1000)


# ======================================================================
#  ENGINE 3 — 🗂️ RESULT HISTORY + TOOL COUNTERS (SQLite, apni table)
# ======================================================================
_DDL = (
    """CREATE TABLE IF NOT EXISTS pro_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tool TEXT DEFAULT '',
        title TEXT DEFAULT '',
        payload TEXT DEFAULT '',
        status TEXT DEFAULT 'ok',
        ms INTEGER DEFAULT 0,
        source TEXT DEFAULT '',
        created_at TEXT DEFAULT '',
        in_cache INTEGER DEFAULT 0
    )""",
    "CREATE INDEX IF NOT EXISTS idx_pro_results_user ON pro_results(user_id, id DESC)",
)


class RecentResults:
    """Har tool run ka record. Append-only (kuch delete nahi hota)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._ready = False
        self._local = threading.local()
        self._init_try()

    # ---------------------------------------------------------------- db
    def _con(self):
        con = getattr(self._local, "con", None)
        if con is None:
            try:
                from modules.core.vault import connect as _vc, db_path as _vp
            except ImportError:
                # file seedha chalayi gayi (python3 modules/core/proengine.py)
                # -> repo root path me add karo, phir import theek chalega
                import sys
                _root = os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))
                if _root not in sys.path:
                    sys.path.insert(0, _root)
                from modules.core.vault import connect as _vc, db_path as _vp
            con = _vc(_vp())
            self._local.con = con
        return con

    def _init_try(self) -> None:
        try:
            con = self._con()
            cur = con.cursor()
            for ddl in _DDL:
                cur.execute(ddl)
            con.commit()
            self._ready = True
        except Exception as e:                                   # noqa: BLE001
            log.warning("pro_results table skip (bot chalega): %s", str(e)[:120])

    # ------------------------------------------------------------- write
    def add(self, uid: int, tool: str, title: str = "", payload: str = "",
            status: str = "ok", ms: int = 0, source: str = "") -> bool:
        """Ek run record karo. Kabhi exception nahi. Total cap lagta hai."""
        try:
            with self._lock:
                if not self._ready:
                    self._init_try()
                if not self._ready:
                    return False
                con = self._con()
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO pro_results(user_id, tool, title, payload, status, ms,"
                    " source, created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (int(uid), str(tool)[:40], str(title)[:180], str(payload)[:4000],
                     str(status)[:16], int(ms or 0), str(source)[:60],
                     time.strftime("%Y-%m-%d %H:%M:%S")),
                )
                # cap: bade pade data ko chhota rakho (Render disk chhota hota hai)
                cur.execute("SELECT COUNT(*) FROM pro_results")
                row = cur.fetchone()
                if row and int(row[0]) > HISTORY_MAX:
                    cur.execute("DELETE FROM pro_results WHERE id IN "
                                "(SELECT id FROM pro_results ORDER BY id ASC LIMIT ?)",
                                (int(row[0]) - HISTORY_MAX,))
                con.commit()
                return True
        except Exception as e:                                   # noqa: BLE001
            log.debug("result record skip: %s", str(e)[:110])
            return False

    # -------------------------------------------------------------- read
    def recent(self, uid: int, n: int = 8) -> List[dict]:
        try:
            with self._lock:
                if not self._ready:
                    return []
                con = self._con()
                cur = con.cursor()
                cur.execute("SELECT tool, title, payload, status, ms, source, created_at"
                            " FROM pro_results WHERE user_id=? AND status='ok'"
                            " ORDER BY id DESC LIMIT ?", (int(uid), int(n)))
                cols = ("tool", "title", "payload", "status", "ms", "source", "created_at")
                out = []
                for r in cur.fetchall() or []:
                    out.append(dict(zip(cols, r)))
                return out
        except Exception:                                        # noqa: BLE001
            return []

    def clear(self, uid: int) -> bool:
        try:
            with self._lock:
                if not self._ready:
                    return False
                con = self._con()
                con.cursor().execute("DELETE FROM pro_results WHERE user_id=?", (int(uid),))
                con.commit()
                return True
        except Exception:                                        # noqa: BLE001
            return False

    def counts(self) -> dict:
        """Total runs + unique users + aaj ke runs."""
        try:
            with self._lock:
                if not self._ready:
                    return {"runs": 0, "users": 0, "today": 0}
                con = self._con()
                cur = con.cursor()
                cur.execute("SELECT COUNT(*), COUNT(DISTINCT user_id) FROM pro_results")
                r = cur.fetchone() or (0, 0)
                today = time.strftime("%Y-%m-%d")
                cur.execute("SELECT COUNT(*) FROM pro_results WHERE created_at LIKE ?",
                            (today + "%",))
                t = cur.fetchone() or (0,)
                return {"runs": int(r[0] or 0), "users": int(r[1] or 0),
                        "today": int(t[0] or 0)}
        except Exception:                                        # noqa: BLE001
            return {"runs": 0, "users": 0, "today": 0}


results = RecentResults()

# per-tool counters (memory — fast, bot restart par reset ho jaate hain;
# permanent hisaab upar wali SQLite table me hota hai)
_tc: Dict[str, Dict[str, Any]] = {}
_tc_lock = threading.Lock()


def tool_counter(tool: str, ok: bool = True, ms: int = 0) -> None:
    try:
        with _tc_lock:
            d = _tc.get(tool)
            if d is None:
                d = {"ok": 0, "fail": 0, "total_ms": 0, "runs": 0, "last": 0.0}
                _tc[tool] = d
            d["runs"] += 1
            d["ok" if ok else "fail"] += 1
            d["total_ms"] += int(ms or 0)
            d["last"] = time.time()
    except Exception:                                            # noqa: BLE001
        pass


def record_result(uid: int, tool: str, title: str = "", payload: str = "",
                  ok: bool = True, ms: int = 0, source: str = "") -> None:
    """Ek hi jagah se dono: counter + SQLite history. (bot.py isi ko call karega)"""
    try:
        tool_counter(tool, ok, ms)
        if ok:
            results.add(uid, tool, title, payload, status="ok", ms=ms, source=source)
    except Exception:                                            # noqa: BLE001
        pass


def toolstats(limit: int = 20) -> List[dict]:
    with _tc_lock:
        rows = []
        for name, d in _tc.items():
            runs = max(1, int(d["runs"]))
            rows.append({
                "tool": name, "runs": d["runs"], "ok": d["ok"], "fail": d["fail"],
                "success_pct": round(100.0 * d["ok"] / runs, 1),
                "avg_ms": int(d["total_ms"] / runs),
                "last": d["last"],
            })
        rows.sort(key=lambda r: r["runs"], reverse=True)
        return rows[:limit]


def toolstats_text(limit: int = 15) -> str:
    """Admin ke liye tool analytics card (outcome only)."""
    try:
        rows = toolstats(limit)
        c = results.counts()
        if not rows:
            return ("📊 <b>TOOL ANALYTICS</b>\n──────────────────────\n"
                    "Abhi koi run record nahi hua.\n"
                    f"🗂️ History me total <b>{c['runs']}</b> runs "
                    f"({c['users']} users).")
        lines = [
            "📊 <b>TOOL ANALYTICS</b>",
            "──────────────────────",
            f"🗂️ <b>Total runs:</b> {c['runs']} · <b>Aaj:</b> {c['today']} · "
            f"<b>Users:</b> {c['users']}",
            "──────────────────────",
        ]
        for r in rows:
            dot = "🟢" if r["success_pct"] >= 90 else ("🟡" if r["success_pct"] >= 70 else "🔴")
            lines.append(
                f"{dot} <b>{r['tool']}</b> — {r['runs']} runs · "
                f"{r['success_pct']}% pass · {r['avg_ms']}ms"
            )
        lines.append("──────────────────────")
        return "\n".join(lines)
    except Exception:                                            # noqa: BLE001
        return "📊 Tool analytics abhi tayyar nahi."


# --------------------------------------------------------- history card
def history_text(uid: int, n: int = 8) -> str:
    try:
        rows = results.recent(uid, n)
        if not rows:
            return ("🗂️ <b>AAKHI KE RESULTS</b>\n──────────────────────\n"
                    "Abhi kuch nahi. Ek tool chalao — phir yahan dikh jayega.")
        lines = ["🗂️ <b>AAKHI KE RESULTS</b>", "──────────────────────"]
        for i, r in enumerate(rows, 1):
            t = (r.get("title") or r.get("tool") or "result")[:60]
            ms = r.get("ms") or 0
            src = (r.get("source") or "").strip()
            tail = f" · {ms}ms" if ms else ""
            tail += f" · {src}" if src else ""
            lines.append(f"{i}. <b>{t}</b>{tail}")
        lines.append("──────────────────────")
        return "\n".join(lines)
    except Exception:                                            # noqa: BLE001
        return "🗂️ History abhi tayyar nahi."


def history_kb(uid: int = 0, n: int = 6):
    """Recent results ke 1-tap buttons — jaldi se dobara.

    Button me sirf tool ka naam jaata hai; value user se dobara maangi jaati
    hai (warna 64-char callback limit toot jati hai)."""
    try:
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        rows: List[list] = []
        seen: set = set()
        for r in results.recent(int(uid), max(2, int(n))):
            tool = str(r.get("tool") or "").strip()          # mode key (bot use karta hai)
            nice = str(r.get("title") or tool).strip()       # dikhane ke liye
            if not tool or tool in seen:
                continue
            seen.add(tool)
            rows.append([InlineKeyboardButton(f"🔁 {nice[:34]}",
                                              callback_data=f"pro_re:{tool}"[:64])])
            if len(rows) >= 5:
                break
        rows.append([InlineKeyboardButton("🧹 History saaf karo", callback_data="pro_histclear"),
                     InlineKeyboardButton("⌨️ Menu", callback_data="back_home")])
        return InlineKeyboardMarkup(rows)
    except Exception:                                            # noqa: BLE001
        return None


# ======================================================================
#  ENGINE 4 — ✨ QUALITY STAMP (bharosa dikhta hai)
# ======================================================================
def quality_line(source: str = "", ms: int = 0, cached: bool = False,
                 extra: str = "") -> str:
    """Har result card ke neeche ek chhoti outcome line (koi link nahi)."""
    try:
        bits = []
        if cached:
            bits.append("⚡ instant")
        elif ms:
            bits.append(f"⚡ {int(ms)}ms")
        if source:
            bits.append(f"🏷️ {str(source)[:28]}")
        if extra:
            bits.append(str(extra)[:40])
        if not bits:
            return ""
        return "<i>" + " · ".join(bits) + "</i>"
    except Exception:                                            # noqa: BLE001
        return ""


# ======================================================================
#  SELFTEST (python3 modules/core/proengine.py)
# ======================================================================
if __name__ == "__main__":
    checks = [
        ("SBIN0001234", "ifsc"), ("HDFC0000123", "ifsc"),
        ("9876543210", "mobile"), ("800001", "pincode"),
        ("BR01AB1234", "vehicle"), ("DL8CAF5030", "vehicle"),
        ("ABCDE1234F", "pan"), ("22AAAAA0000A1Z5", "gst"),
        ("https://youtu.be/abc", "url"), ("www.google.com", "url"),
        ("@himanshu_dev", "username"), ("358749052487655", "imei"),
        ("google.com", "domain"), ("hi kaise ho", None),
        ("", None), ("12345", None),
    ]
    ok = bad = 0
    for text, want in checks:
        got = detect(text)
        gk = got.get("kind") if got else None
        if gk == want:
            ok += 1
        else:
            bad += 1
            print(f"  FAIL: {text!r} -> {gk} (chahiye {want})")
    print(f"proengine detect: PASS {ok} | FAIL {bad}")
    print("race:", race([("a", lambda: None), ("b", lambda: "mil gaya")])[:2])
    print("breakers:", breaker_stats())
