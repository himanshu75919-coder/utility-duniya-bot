# -*- coding: utf-8 -*-
"""
UPI (VPA) VERIFY — APNI API (optional, opt-in)
==============================================
Ye module UPI ID ka **account holder name / status** laata hai — PAR sirf
tab jab aap khud koi legal UPI/penny-drop verification API lagao (apni key
Render me daal ke).

Kyun opt-in:
  • NPCI ka "Validate Address API" sirf payment companies (PSP/merchant) ko
    milta hai — kisi bhi public bot ko nahi.
  • Jo bot bina API ke number/VPA se naam "nikaal" dete hain, wo leaked ya
    unauthorized data use karte hain. DPDP Act (2023) me uski sazaa
    ₹250 crore tak hai + bot ban ho jaata hai.
  • Legal B2B APIs (Eko, InstantPay, Surepay, PayU) me **consent** param
    hota hai — matlab ye payee-verification ke liye hai, aur uske liye
    business KYC + paid wallet chahiye (~₹1-2 per lookup).

Agar aap aisi API lagate ho to bas env vars daal do — card me naam aa jayega.
Na lagao to tool purane tarike se chalta rahega (format + bank handle +
honest note). **Kuch bhi crash nahi hota, tool kabhi band nahi hota.**

ENV VARS (Render → Environment):
    UPI_VERIFY_URL        = API ka endpoint (jaise https://api.example.com/vpa/verify)
    UPI_VERIFY_KEY        = aapki API key
    UPI_VERIFY_AUTH       = query | header | bearer | none        (default: query)
    UPI_VERIFY_KEY_PARAM  = key kis naam se jaati hai             (default: key)
    UPI_VERIFY_HEADER     = auth=header par header ka naam        (default: X-Api-Key)
    UPI_VERIFY_PARAM      = VPA kis param me jaata hai            (default: vpa)
    UPI_VERIFY_METHOD     = GET | POST                            (default: GET)
    UPI_VERIFY_CONSENT    = Y | N    (B2B KYC APIs me "consent: Y" chahiye; default Y)
    UPI_VERIFY_TIMEOUT    = 4-30 seconds                          (default: 12)
"""
from __future__ import annotations

import os
import time
from typing import Optional

try:
    from modules.core.net import http_get, http_post
except Exception:                                              # noqa: BLE001
    http_get = None
    http_post = None

# numinfo_provider ke parsing helpers reuse karo (ek hi jagah logic rahe)
try:
    from modules.numinfo_provider import (
        _flatten as _flat, _pick as _pickval, _clean_name as _clean, _digits,
    )
except Exception:                                              # noqa: BLE001
    def _flat(d, prefix=""):                                   # type: ignore
        return d if isinstance(d, dict) else {}

    def _pickval(d, *keys):                                    # type: ignore
        return ""

    def _clean(v):                                             # type: ignore
        return ""

    def _digits(v):                                            # type: ignore
        return ""

__all__ = ["is_configured", "verify", "status", "status_card",
           "provider_url", "provider_key"]

_CACHE: dict = {}
_CACHE_TTL = 6 * 3600


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or "").strip() or default


def provider_url() -> str:
    return _env("UPI_VERIFY_URL")


def provider_key() -> str:
    return _env("UPI_VERIFY_KEY")


def _auth() -> str:
    return _env("UPI_VERIFY_AUTH", "query").lower()


def _timeout() -> int:
    try:
        return max(4, min(30, int(_env("UPI_VERIFY_TIMEOUT", "12"))))
    except Exception:                                          # noqa: BLE001
        return 12


def is_configured() -> bool:
    return bool(provider_url() and provider_key())


def status() -> dict:
    return {
        "configured": is_configured(),
        "url": provider_url(),
        "auth": _auth(),
        "param": _env("UPI_VERIFY_PARAM", "vpa"),
        "method": _env("UPI_VERIFY_METHOD", "GET").upper(),
        "key_set": bool(provider_key()),
    }


def status_card() -> str:
    st = status()
    if not st["configured"]:
        return (
            "🏦 <b>UPI VERIFY — NAAM API</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔌 <b>Status:</b> ⚪ SET NAHI HAI\n\n"
            "Iske bina tool <b>format + bank handle</b> check karta hai aur\n"
            "saaf-saaf batata hai ki holder ka naam public nahi hota.\n\n"
            "<b>Agar aapke paas legal UPI/KYC API hai</b> (Eko · InstantPay ·\n"
            "Surepay · PayU — paid, business KYC chahiye), to Render →\n"
            "Environment me ye daalo:\n"
            "<code>UPI_VERIFY_URL</code>  = API endpoint\n"
            "<code>UPI_VERIFY_KEY</code>  = API key\n"
            "<code>UPI_VERIFY_PARAM</code> = vpa  <i>(VPA jis param me jaata hai)</i>\n"
            "<code>UPI_VERIFY_AUTH</code> = query | header | bearer\n\n"
            "📖 Poori jankari: <code>UPI-NAAM-API-SETUP.md</code>"
        )
    return (
        "🏦 <b>UPI VERIFY — NAAM API</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔌 <b>Status:</b> ✅ SET HAI\n"
        f"• <b>URL:</b> <code>{_clean(st['url'])[:80]}</code>\n"
        f"• <b>Method:</b> {st['method']}   • <b>Auth:</b> {st['auth']}\n"
        f"• <b>VPA param:</b> <code>{_clean(st['param'])}</code>\n"
        "• <b>Key:</b> ✅ set (chhupi hui)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>UPI ID bhejne par holder ka naam API se aayega.</i>"
    )


def verify(vpa: str) -> dict:
    """VPA → {ok, name, status, bank, ...}. Kabhi raise nahi karta."""
    v = (vpa or "").strip().lower()
    if not v or "@" not in v:
        return {"ok": False, "error": "Valid UPI ID bhejein (jaise rahul@sbi)."}
    if not is_configured():
        return {"ok": False, "not_configured": True,
                "error": "UPI name API set nahi hai."}
    ck = f"up:{v}"
    now = time.time()
    hit = _CACHE.get(ck)
    if hit and (now - hit[0]) < _CACHE_TTL:
        return {**hit[1], "cached": True}

    url = provider_url()
    params = {}
    if "{vpa}" in url:
        url = url.replace("{vpa}", v)
    else:
        params[_env("UPI_VERIFY_PARAM", "vpa")] = v
    headers = {}
    if _env("UPI_VERIFY_CONSENT", "Y").upper() in ("Y", "YES", "1", "TRUE"):
        params.setdefault("consent", "Y")
    key = provider_key()
    a = _auth()
    if a == "header":
        headers[_env("UPI_VERIFY_HEADER", "X-Api-Key")] = key
    elif a == "bearer":
        headers["Authorization"] = f"Bearer {key}"
    elif a != "none":
        params[_env("UPI_VERIFY_KEY_PARAM", "key")] = key

    t0 = time.time()
    data: Optional[dict] = None
    err = ""
    try:
        if _env("UPI_VERIFY_METHOD", "GET").upper() == "POST":
            if http_post is None:
                raise RuntimeError("http_post available nahi hai")
            r = http_post(url, json_body=params, headers=headers, timeout=_timeout())
        else:
            if http_get is None:
                raise RuntimeError("http_get available nahi hai")
            r = http_get(url, params=params or None, headers=headers,
                         timeout=_timeout(), retries=1)
        ms = int((time.time() - t0) * 1000)
        code = getattr(r, "status_code", 200)
        if code in (401, 403):
            return {"ok": False, "auth": True,
                    "error": f"API ne key reject ki (HTTP {code}). UPI_VERIFY_KEY check karo."}
        if code == 429:
            return {"ok": False, "rate_limited": True,
                    "error": "API ki limit khatam (HTTP 429). Thodi der baad try karo."}
        if code >= 400:
            return {"ok": False, "error": f"API HTTP {code}. URL/params check karo."}
        data = r.json() if hasattr(r, "json") else None
    except Exception as e:                                     # noqa: BLE001
        err = f"{type(e).__name__}: {str(e)[:90]}"
        ms = int((time.time() - t0) * 1000)

    if not isinstance(data, dict):
        return {"ok": False, "soft": True,
                "error": f"API se sahi jawab nahi aaya. {err}".strip()}

    flat = _flat(data)
    name = _clean(_pickval(flat, "name", "accountname", "account_holder_name",
                           "holdername", "beneficiaryname", "payeename",
                           "registeredname", "customer_name", "recipientname"))
    bank = _clean(_pickval(flat, "bank", "bankname", "bank_name", "ifsc",
                           "payeeifsc", "issuer"))
    stat = _clean(_pickval(flat, "status", "vpa_status", "result", "message",
                           "actcode", "statuscode"))
    valid_raw = _pickval(flat, "valid", "isvalid", "vpa_valid", "accountexists",
                         "success", "exists")
    valid = str(valid_raw).strip().lower() in ("true", "1", "yes", "y", "valid")
    if not valid and stat:
        valid = any(w in stat.lower() for w in ("success", "valid", "active", "ok"))
    mobile = _clean(_pickval(flat, "mobile", "mobilenumber", "phonenumber",
                             "registeredmobile", "altmobile"))
    if not name and not bank and not stat:
        return {"ok": False, "soft": True,
                "error": "API ne naam/bank nahi diya — response ka format match nahi hua."}
    out = {
        "ok": True,
        "vpa": v,
        "name": name,
        "bank": bank,
        "status": stat,
        "valid": valid,
        "mobile": _digits(mobile)[-10:] if mobile else "",
        "latency_ms": ms,
        "source": "provider",
    }
    _CACHE[ck] = (now, out)
    if len(_CACHE) > 500:
        for k in sorted(_CACHE, key=lambda x: _CACHE[x][0])[:120]:
            _CACHE.pop(k, None)
    return dict(out)
