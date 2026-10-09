# -*- coding: utf-8 -*-
"""
👪 FAMILY INFO — FAMILYINFO API (v100)
=====================================
User ka apna family-lookup API (bot me built-in):

    GET {FAMINFO_API_URL}?key={FAMINFO_API_KEY}&tool=familyinfo&term={12-digit Aadhaar}

Response shape (live-verified, 9 Oct 2026):
    HIT : {"success": true, "data": {"card_number": ..., "card_type": "PHH",
            "aadhaar_mask": "401****849", "statedist": "BIHAR / SITAMARHI",
            "fps_id": ..., "fps_name": ..., "family_count": "5",
            "full_address": ..., "name": ..., "member_id": ...,
            "ekyc_status": "VERIFIED ✅", ("name_"/"name__"... extra members),
            "generated": ...}}
    MISS: {"success": true, "data": {"family_info_not_found_for": term},
            "raw": "✖️ Family Info Not Found for: ..."}

SAKHT NIYAM (Aadhaar leak-proof):
  • Sirf 12-digit Verhoeff-valid Aadhaar API tak jaata hai (typo turant pakda).
  • Poora Aadhaar KAHIN nahi — na card me, na error me, na log me.
    Sirf mask: XXXX-XXXX-1234 (aakhri 4 digit).
  • API ka apna `aadhaar_mask` (401****849 — 6 digit khule!) bhi NAHI dikhate —
    hamaara mask usse sakht hai.
  • Key ki VALUE kabhi kahin print nahi hoti.
  • Ye module kabhi raise nahi karta — hamesha dict deta hai.

Render → Environment (zaroorat ho tabhi — default built-in hai):
    FAMINFO_API_URL      (default: neeche _BUILTIN_URL)
    FAMINFO_API_KEY      (default: Demo)
    FAMINFO_API_TIMEOUT  (default: 40 — API slow hai, 10-60 second)
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
    "User-Agent": "UtilityDuniyaBot/1.0 (+faminfo)",
    "Accept": "application/json, */*",
}

_BUILTIN_URL = "https://jgvicvhgfwcfndgookul.supabase.co/functions/v1/bot-api"
_BUILTIN_KEY = "Demo"

_NUM_RE = re.compile(r"\D")
_JUNK = {"", "na", "n/a", "none", "null", "-", "undefined", "0"}


# --------------------------------------------------------------------------- config
def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or "").strip() or default


def api_url() -> str:
    return _env("FAMINFO_API_URL", _BUILTIN_URL)


def api_key() -> str:
    return _env("FAMINFO_API_KEY", _BUILTIN_KEY)


def api_timeout() -> int:
    try:
        return max(10, min(60, int(_env("FAMINFO_API_TIMEOUT", "40"))))
    except ValueError:
        return 40


def is_configured() -> bool:
    """Built-in API — hamesha ready (net available ho to)."""
    return bool(api_url().startswith("http") and _NET)


# --------------------------------------------------------------------------- helpers
def _digits12(number) -> str:
    """Sirf digits → 12 hon to wahi, warna "" (space wale Aadhaar bhi chalte hain)."""
    d = _NUM_RE.sub("", str(number or ""))
    return d if len(d) == 12 else ""


def verhoeff_ok(num: str) -> bool:
    """Aadhaar ka asli checksum (Verhoeff) — typo pakadne ke liye."""
    try:
        d = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
             [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
             [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
             [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
             [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
             [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
             [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
             [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
             [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
             [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
        p = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
             [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
             [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
             [8, 9, 1, 6, 0, 4, 3, 7, 2, 5],
             [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
             [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
             [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
             [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]]
        s = str(num or "")
        if len(s) != 12 or not s.isdigit():
            return False
        c = 0
        for i, ch in enumerate(reversed(s)):
            c = d[c][p[i % 8][int(ch)]]
        return c == 0
    except Exception:                                            # noqa: BLE001
        return False


def _clean(v) -> str:
    s = re.sub(r"\s+", " ", str(v or "").strip())
    return "" if s.lower() in _JUNK else s


def mask_aadhar12(v) -> str:
    """Aadhaar HAMESHA mask — sirf aakhri 4 digit (XXXX-XXXX-1234)."""
    d = _NUM_RE.sub("", str(v or ""))
    if len(d) != 12:
        return ""
    return "XXXX-XXXX-" + d[-4:]


def _ekyc(v) -> str:
    s = _clean(v)
    if not s:
        return ""
    if "VERIFIED" in s.upper() or "✅" in s:
        return "✅ Verified"
    if "PENDING" in s.upper():
        return "⏳ Pending"
    return s[:24]


# --------------------------------------------------------------------------- parse + lookup
def parse_payload(data: dict, ms: int = 0, query: str = "") -> dict:
    """API ke JSON ko card-shape me badlo. Kabhi raise nahi karta.

    `query` = user ka Aadhaar (mask karke dikhane ke liye — poora KABHI nahi).
    """
    try:
        d = (data or {}).get("data") if isinstance(data, dict) else None
        if not isinstance(d, dict) or not d or "family_info_not_found_for" in d:
            return {"ok": False, "not_found": True,
                    "error": "❌ Is Aadhaar par family record nahi mila."}
        if not d.get("name") and not d.get("card_number"):
            return {"ok": False, "not_found": True,
                    "error": "❌ Is Aadhaar par family record nahi mila."}
        members = []
        for i in range(20):   # "", "_", "__", ... (cap 20, safety)
            suf = "_" * i
            nm = _clean(d.get("name" + suf))
            if not nm and i > 0 and not _clean(d.get("member_id" + suf)):
                continue      # gap ho sakta hai — aage dekho
            if nm:
                members.append({
                    "name": nm,
                    "member_id": _clean(d.get("member_id" + suf)),
                    "ekyc": _ekyc(d.get("ekyc_status" + suf)),
                })
            if len(members) >= 15:
                break
        # NOTE: API ka `aadhaar_mask` (6 digit khule) JAAN-BOOJH kar ignore —
        # sirf hamaara sakht mask (aakhri 4) dikhta hai.
        return {"ok": True, "source": "famapi",
                "aadhaar_mask": mask_aadhar12(query),
                "card_number": _clean(d.get("card_number")),
                "card_type": _clean(d.get("card_type")),
                "state_dist": _clean(d.get("statedist")),
                "fps": _clean(d.get("fps_name") or d.get("fps_id")),
                "family_count": _clean(d.get("family_count")) or str(len(members) or ""),
                "address": _clean(d.get("full_address")),
                "members": members, "generated": _clean(d.get("generated")),
                "latency_ms": int(ms or 0)}
    except Exception:                                            # noqa: BLE001
        return {"ok": False, "error": "API ka jawab samajh nahi aaya."}


def lookup(aadhar) -> dict:
    """Family API se record laao (cache 6 ghante). Kabhi raise nahi karta."""
    try:
        digits = _digits12(aadhar)
        if not digits:
            return {"ok": False, "error": "Sahi 12-digit Aadhaar number bhejo."}
        if not verhoeff_ok(digits):
            return {"ok": False,
                    "error": "❌ Aadhaar number galat lag raha hai — 12-digit sahi likho."}
        ck = f"fam:{digits}"
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
                params={"key": api_key(), "tool": "familyinfo", "term": digits},
                headers=dict(UA), timeout=api_timeout(), retries=1)
        except Exception as e:                                   # noqa: BLE001
            return {"ok": False,
                    "error": f"Family API se connect nahi hua: {str(e)[:90]}"}
        ms = int((time.time() - t0) * 1000)
        if r.status_code in (401, 403):
            return {"ok": False, "auth": True, "status": r.status_code,
                    "error": (f"API ne key reject ki (HTTP {r.status_code}). "
                              "Render me FAMINFO_API_KEY check karo.")}
        if r.status_code == 429:
            return {"ok": False, "rate_limited": True,
                    "error": "API ki limit khatam (429). Thodi der baad try karo."}
        if r.status_code >= 400:
            return {"ok": False, "status": r.status_code,
                    "error": f"Family API HTTP {r.status_code}."}
        try:
            data = r.json()
        except Exception:                                        # noqa: BLE001
            return {"ok": False, "error": "API ne JSON nahi bheja."}
        out = parse_payload(data, ms, digits)
        if out.get("ok") and _CACHE is not None:
            _CACHE.put(ck, out, 21600)                            # 6 ghante
        return out
    except Exception:                                            # noqa: BLE001
        return {"ok": False, "error": "Family lookup me dikkat aayi."}


__all__ = [
    "is_configured", "lookup", "parse_payload", "api_url", "api_key",
    "mask_aadhar12", "verhoeff_ok",
]
