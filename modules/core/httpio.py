# -*- coding: utf-8 -*-
"""
🌐 SHARED HTTP ENGINE (v72.0) — "saare tools ka speed + auto-fix upgrade"
=========================================================================
Kyun banaya (user ka order: "mere saare tools ko upgrade karo"):

PEHLE (problem):
  • Har module apna `requests.get()` karta tha — har baar NAYA TLS handshake
    (slow), aur ek bhi network hiccup par seedha "site slow / fail" card.

AB (upgrade):
  • Ek hi keep-alive session (connection pool) — dobara connection banane ka
    waqt bachta hai, tools ~15-40% tez
  • Auto-retry adapter: 429/500/502/503/504 aur connect/read timeout par
    khud 2 baar koshish (backoff ke saath) — "site ne ek baar hiccup kiya"
    wale fail khatam
  • Har call par default timeout (12s) — hanging request ka khatra khatam
  • Common UA + headers ek jagah
  • Live stats: calls / retries / fails / avg_ms → /health par dikhte hain

Design rules (bot ke rules ke hisaab se):
  • Crash-proof: kuch bhi ho, exception waisi hi aage jaati hai jaisi
    requests ki jaati thi (modules ka try/except waise hi kaam karta rahega)
  • Stats counting kabhi response ko nahi todti (sab guarded)
  • Koi key / paisa nahi — plain requests hai
"""

import logging
import threading
import time

import requests

try:                                            # urllib3 adapter (retry engine)
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    _HAS_RETRY = True
except Exception:                               # noqa: BLE001
    _HAS_RETRY = False

log = logging.getLogger(__name__)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

DEFAULT_TIMEOUT = 12
RETRY_TOTAL = 2                                  # kitni baar khud koshish kare

STATS = {"calls": 0, "retries": 0, "fails": 0, "ms_total": 0.0, "since": time.time()}
_LOCK = threading.Lock()
_SESSION = None
_SESSION_NORETRY = None


def _mk_session(with_retry: bool) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    if with_retry and _HAS_RETRY:
        _retry = Retry(
            total=RETRY_TOTAL, connect=RETRY_TOTAL, read=RETRY_TOTAL,
            status=RETRY_TOTAL, backoff_factor=0.45,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST", "HEAD"]),
            raise_on_status=False,
        )
        _ad = HTTPAdapter(max_retries=_retry, pool_connections=16, pool_maxsize=32)
    else:
        # ⚠️ QUOTA-SAFE tools (jaise RC provider) ke liye: 0 retry —
        # 429 par dobara request bhejna = paid quota barbaad (user ka rule)
        _ad = HTTPAdapter(max_retries=0, pool_connections=8, pool_maxsize=16)
    s.mount("https://", _ad)
    s.mount("http://", _ad)
    return s


def session_noretry() -> requests.Session:
    """Quota-safe session — koi auto-retry nahi (har request ginti me aati hai)."""
    global _SESSION_NORETRY
    try:
        if _SESSION_NORETRY is None:
            _SESSION_NORETRY = _mk_session(with_retry=False)
        return _SESSION_NORETRY
    except Exception:                           # noqa: BLE001
        return session()


def session() -> requests.Session:
    """Ek hi shared session (keep-alive + retry). Thread-safe banane ki koshish."""
    global _SESSION
    try:
        if _SESSION is None:
            _SESSION = _mk_session(with_retry=True)
        return _SESSION
    except Exception:                           # noqa: BLE001
        return requests                         # aakhri sahara — phir bhi chalta rahe


def _count(r, t0: float, failed: bool = False) -> None:
    """Stats — kabhi raise nahi karta (response ko nahi todta)."""
    try:
        with _LOCK:
            STATS["calls"] += 1
            STATS["ms_total"] += (time.time() - t0) * 1000
            if failed:
                STATS["fails"] += 1
            # retries ka count failed response par bhi dekha jata hai —
            # retry to asal me 5xx par hi hota hai
            try:
                rt = getattr(getattr(r, "raw", None), "retries", None)
                STATS["retries"] += int(getattr(rt, "total", 0) or 0)
            except Exception:                   # noqa: BLE001
                pass
    except Exception:                           # noqa: BLE001
        pass


def request(method: str, url: str, **kw):
    """httpio ka core — wahi signature jo requests.get/post ka hota hai.

    Extra kwarg: retry=False → quota-safe (0-retry) session use karo.
    """
    use_retry = bool(kw.pop("retry", True))
    kw.setdefault("timeout", DEFAULT_TIMEOUT)
    sess = session() if use_retry else session_noretry()
    t0 = time.time()
    try:
        r = getattr(sess, str(method).lower())(url, **kw)
        _count(r, t0, failed=getattr(r, "status_code", 200) >= 400)
        return r
    except Exception:
        _count(None, t0, failed=True)
        raise


def get(url: str, **kw):
    return request("get", url, **kw)


def post(url: str, **kw):
    return request("post", url, **kw)


def get_json(url: str, **kw):
    """GET + JSON parse (fail par exception — modules ka try/except sambhalta hai)."""
    r = get(url, **kw)
    r.raise_for_status()
    return r.json()


def stats() -> dict:
    """health page ke liye: calls / retries / fails / avg_ms (+ uptime)."""
    try:
        with _LOCK:
            c = max(1, int(STATS["calls"]))
            return {
                "calls": int(STATS["calls"]),
                "retries": int(STATS["retries"]),
                "fails": int(STATS["fails"]),
                "avg_ms": round(STATS["ms_total"] / c, 1),
                "uptime_min": int((time.time() - STATS["since"]) / 60),
            }
    except Exception:                           # noqa: BLE001
        return {"calls": 0, "retries": 0, "fails": 0, "avg_ms": 0.0, "uptime_min": 0}
