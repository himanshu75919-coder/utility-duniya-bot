# -*- coding: utf-8 -*-
"""
📱 NUMBER INFO — NUMBER API (v99)
=================================
User ka apna number-lookup API (bot me built-in):

    GET {MYNUM_API_URL}?key={MYNUM_API_KEY}&tool=num&term={10-digit}

Response shape (live-verified):
    HIT : {"success": true, "data": {"owner_name": ..., "father_name": ...,
            "mobile_no": ..., "alt_mobile": ..., "aadhar_card_no": ...,
            "circle": "VI DELHI", "address": ...,
            "owner_name_": ..., "circle_": ... (extra records `_` suffix me)}}
    MISS: {"success": true, "data": {}, "raw": "✖️ No result found"}

Rules:
  • Sirf 10-digit Indian mobile bhejta hai (91/0 prefix auto-strip — API
    91 ke saath "No result" deti hai, live-verified).
  • Aadhaar number HAMESHA mask hota hai (XXXX-XXXX-1234) — poora Aadhaar
    dikhana kanoon ke khilaaf hai (Aadhaar Act).
  • Key ki VALUE kabhi kahin print nahi hoti (status me sirf set/not-set).
  • Ye module kabhi raise nahi karta — hamesha dict deta hai.

Render → Environment (zaroorat ho tabhi — default built-in hai):
    MYNUM_API_URL      (default: neeche _BUILTIN_URL)
    MYNUM_API_KEY      (default: Demo)
    MYNUM_API_TIMEOUT  (default: 40 — API slow hai, 10-60 second)
"""
from __future__ import annotations

import os
import re
import time

try:
    from modules.core import net as _netmod
    _NET = True
except Exception:                                            # pragma: no cover
    _netmod = None
    _NET = False

try:
    from modules.core.cache import TTLCache as _TTLCache
    _CACHE = _TTLCache(maxsize=1024, default_ttl=21600)      # 6 ghante
except Exception:                                            # pragma: no cover
    _CACHE = None

UA = {
    "User-Agent": "UtilityDuniyaBot/1.0 (+mynum)",
    "Accept": "application/json, */*",
}

_BUILTIN_URL = "https://jgvicvhgfwcfndgookul.supabase.co/functions/v1/bot-api"
_BUILTIN_KEY = "Demo"

_NUM_RE = re.compile(r"\D")
_JUNK = {"", "na", "n/a", "none", "null", "-", "undefined", "0"}
_OPS = {"AIRTEL", "JIO", "VI", "VODAFONE", "VODA", "IDEA", "BSNL", "MTNL",
        "AIRCEL", "RELIANCE", "TATA", "DOCOMO", "UNINOR", "MTS"}


# --------------------------------------------------------------------------- config
def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or "").strip() or default


def api_url() -> str:
    """Number API endpoint (default built-in). Tests fake server bhi de sakte hain."""
    return _env("MYNUM_API_URL", _BUILTIN_URL)


def api_key() -> str:
    return _env("MYNUM_API_KEY", _BUILTIN_KEY)


def api_timeout() -> int:
    try:
        return max(10, min(60, int(_env("MYNUM_API_TIMEOUT", "40"))))
    except ValueError:
        return 40


def is_configured() -> bool:
    """Built-in API — hamesha ready (net available ho to)."""
    return bool(api_url().startswith("http") and _NET)


# --------------------------------------------------------------------------- helpers
def _digits10(number) -> str:
    """91/0 prefix hatao → 10 digit, warna "" (API ko 10-digit hi chahiye)."""
    d = _NUM_RE.sub("", str(number or ""))
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 else ""


def _clean(v) -> str:
    s = re.sub(r"\s+", " ", str(v or "").strip())
    return "" if s.lower() in _JUNK else s


def mask_aadhar(v) -> str:
    """Aadhaar HAMESHA mask — sirf aakhri 4 digit (kanoon ki maang)."""
    if str(v or "").strip().lower() in _JUNK:
        return ""
    d = _NUM_RE.sub("", str(v or ""))
    if len(d) < 4:
        return ""
    if len(d) == 12:
        return "XXXX-XXXX-" + d[-4:]
    return "X" * (len(d) - 4) + d[-4:]


def _split_circle(circle):
    """'AIRTEL DELHI' → (AIRTEL, DELHI) · 'DELHI VODA' → (VODA, DELHI)."""
    toks = _clean(circle).upper().split()
    op = next((t for t in toks if t in _OPS), "")
    if not op:
        return "", _clean(circle)
    rest = " ".join(t for t in toks if t != op)
    return op, rest


# --------------------------------------------------------------------------- parse + lookup
def parse_payload(data: dict, ms: int = 0) -> dict:
    """API ke JSON ko bot ke card-shape me badlo. Kabhi raise nahi karta."""
    try:
        d = (data or {}).get("data") if isinstance(data, dict) else None
        if not isinstance(d, dict) or not d:
            return {"ok": False, "not_found": True,
                    "error": "❌ Is number ka record number API me nahi mila."}
        recs = [k for k in d if re.fullmatch(r"owner_name_*", k)]
        if not recs:
            return {"ok": False, "not_found": True,
                    "error": "❌ Is number ka record number API me nahi mila."}
        op, circ = _split_circle(d.get("circle"))
        owner = {k: v for k, v in {
            "name": _clean(d.get("owner_name")),
            "father": _clean(d.get("father_name")),
            "alt": _clean(d.get("alt_mobile")),
            "phone": _clean(d.get("mobile_no")),
            "region": circ,
            "govt_id": mask_aadhar(d.get("aadhar_card_no")),
            "address": _clean(d.get("address")),
        }.items() if v}
        return {"ok": True, "source": "myapi", "operator": op, "circle": circ,
                "type": "", "ported": "", "country": "India",
                "country_code": "+91", "owner": owner,
                "extra": {"records": len(recs)}, "latency_ms": int(ms or 0)}
    except Exception:                                            # noqa: BLE001
        return {"ok": False, "error": "API ka jawab samajh nahi aaya."}


def lookup(number) -> dict:
    """Number API se record laao (cache 6 ghante). Kabhi raise nahi karta."""
    try:
        digits = _digits10(number)
        if not digits:
            return {"ok": False, "error": "Sahi 10-digit mobile number bhejo."}
        ck = f"mynum:{digits}"
        if _CACHE is not None:
            hit = _CACHE.get(ck)
            if hit is not None:
                return {**hit, "cached": True}
        if _netmod is None:
            return {"ok": False, "error": "Network lib ready nahi."}
        t0 = time.time()
        try:
            r = _netmod.http_get(
                api_url(),
                params={"key": api_key(), "tool": "num", "term": digits},
                headers=dict(UA), timeout=api_timeout(), retries=1)
        except Exception as e:                                   # noqa: BLE001
            return {"ok": False,
                    "error": f"Number API se connect nahi hua: {str(e)[:90]}"}
        ms = int((time.time() - t0) * 1000)
        if r.status_code in (401, 403):
            return {"ok": False, "auth": True, "status": r.status_code,
                    "error": (f"API ne key reject ki (HTTP {r.status_code}). "
                              "Render me MYNUM_API_KEY check karo.")}
        if r.status_code == 429:
            return {"ok": False, "rate_limited": True,
                    "error": "API ki limit khatam (429). Thodi der baad try karo."}
        if r.status_code >= 400:
            return {"ok": False, "status": r.status_code,
                    "error": f"Number API HTTP {r.status_code}."}
        try:
            data = r.json()
        except Exception:                                        # noqa: BLE001
            return {"ok": False, "error": "API ne JSON nahi bheja."}
        out = parse_payload(data, ms)
        if out.get("ok") and _CACHE is not None:
            _CACHE.put(ck, out, 21600)                            # 6 ghante
        return out
    except Exception:                                            # noqa: BLE001
        return {"ok": False, "error": "Number lookup me dikkat aayi."}


# --------------------------------------------------------------------------- status
def status() -> dict:
    """/numapi ke liye — key ki VALUE kabhi print nahi hoti (sirf set/not-set)."""
    return {"configured": is_configured(), "url": api_url(),
            "key_set": bool(api_key()), "timeout_s": api_timeout(),
            "cache_hours": 6, "net_ok": _NET}


def status_card() -> str:
    """Telegram-ready card (HTML). Key kabhi nahi dikhti."""
    s = status()
    key_line = "✅ set (chhupi hui)" if s["key_set"] else "— (khali)"
    host = re.sub(r"^https?://", "", s["url"]).split("/")[0][:40]
    return ("📱 <b>NUMBER INFO — NUMBER API</b>\n"
            "──────────────────────\n"
            "🔌 <b>Status:</b> ✅ SET HAI (built-in)\n"
            f"• <b>API:</b> <code>{_esc(host)}</code> <i>(tool=num)</i>\n"
            f"• <b>Key:</b> {key_line} — <code>MYNUM_API_KEY</code> se badlo\n"
            f"• <b>Timeout:</b> {s['timeout_s']}s   • <b>Cache:</b> {s['cache_hours']} ghante\n"
            "──────────────────────\n"
            "🧪 <b>Live test:</b> <code>/numapi 9876543210</code>\n"
            "📖 Guide: <code>NUMBER-INFO-API-SETUP.md</code>\n"
            "<i>Key Render me hi rehti hai — bot kabhi dikhata nahi.</i>")


def _esc(t: str) -> str:
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


__all__ = [
    "is_configured", "lookup", "parse_payload", "status", "status_card",
    "api_url", "api_key", "mask_aadhar",
]
