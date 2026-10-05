# -*- coding: utf-8 -*-
"""
📱 NUMBER INFO — DIRECT PROVIDER (v57)
======================================
Aap apni carrier / phone-validation API **Render ke Environment tab** me lagao,
bot usse seedha live data lega. Key bot me kabhi log nahi hoti, kisi message me
nahi dikhti, aur GitHub par nahi jaati.

Render → utility-duniya-bot → Environment me ye daalo:
------------------------------------------------------------------
NUMINFO_PROVIDER_URL   = aapki API ka endpoint     (zaroori)
NUMINFO_PROVIDER_KEY   = us API ki key             (optional, provider ke hisaab se)
NUMINFO_PROVIDER_PARAM = number wale param ka naam (default: number)
NUMINFO_PROVIDER_AUTH  = query | header | bearer | none   (default: query)
NUMINFO_PROVIDER_KEY_PARAM = key wale param ka naam (default: key)
NUMINFO_PROVIDER_HEADER    = header ka naam (auth=header par, default: X-Api-Key)
NUMINFO_PROVIDER_METHOD    = GET (default) | POST
NUMINFO_DEMO               = on karne par SAMPLE (dummy) card dikhta hai —
                             bina API bhi dekh sakte ho ki kaisa aayega
------------------------------------------------------------------

URL me `{number}` placeholder bhi chalta hai — jaise:
    https://api.example.com/lookup/{number}?full=1

Ye module **kabhi raise nahi karta** — hamesha dict deta hai:
    {"ok": True, "operator": ..., "circle": ..., "type": ..., "source": "provider"}
    {"ok": False, "error": "...", "soft": True}

Agar provider set nahi hai ya fail hua, bot purane apne sources (hub → offline
phonenumbers) par chala jaata hai — Number Info tool kabhi band nahi hota.
"""
from __future__ import annotations

import os
import re
import time

try:
    from modules.core.net import NetError, http_get, http_post
    _NET = True
except Exception:                                            # pragma: no cover
    NetError = Exception                                     # type: ignore
    http_get = None                                          # type: ignore
    http_post = None                                         # type: ignore
    _NET = False

try:
    from modules.core.cache import TTLCache as _TTLCache
    _CACHE = _TTLCache(maxsize=1024, default_ttl=21600)      # 6 ghante
except Exception:                                            # pragma: no cover
    _CACHE = None

UA = {
    "User-Agent": "UtilityDuniyaBot/1.0 (+numinfo)",
    "Accept": "application/json, text/plain, */*",
}

# jaan-boojh kar provider ki key kabhi kahin print nahi hoti
_NUM_RE = re.compile(r"\D")

# --------------------------------------------------------------------------- config
_PLACEHOLDER = {"", "demo", "yourkey", "your_key", "xxx", "none", "changeme", "null"}


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or "").strip() or default


def provider_url() -> str:
    """Aapki API ka endpoint (khaali = provider set nahi hai)."""
    return _env("NUMINFO_PROVIDER_URL")


def provider_key() -> str:
    return _env("NUMINFO_PROVIDER_KEY")


def provider_param() -> str:
    """Number kis param me jaata hai (numverify: 'number', abstractapi: 'phone')."""
    return _env("NUMINFO_PROVIDER_PARAM", "number")


def provider_auth() -> str:
    """query | header | bearer | none."""
    a = _env("NUMINFO_PROVIDER_AUTH", "query").lower()
    return a if a in ("query", "header", "bearer", "none") else "query"


def provider_method() -> str:
    """GET (default) ya POST — kuch APIs POST maangti hain (v59.3)."""
    return "post" if _env("NUMINFO_PROVIDER_METHOD", "GET").strip().lower().startswith("p") else "get"


def provider_key_param() -> str:
    """query auth me key kis naam se jaati hai (numverify: 'access_key')."""
    return _env("NUMINFO_PROVIDER_KEY_PARAM", "key")


def provider_header_name() -> str:
    return _env("NUMINFO_PROVIDER_HEADER", "X-Api-Key")


def provider_timeout() -> int:
    try:
        return max(4, min(30, int(_env("NUMINFO_PROVIDER_TIMEOUT", "12"))))
    except ValueError:
        return 12


def is_configured() -> bool:
    """Provider ready hai? (URL set ho + net available ho.)"""
    u = provider_url()
    return bool(u and u.startswith("http") and _NET)


# --------------------------------------------------------------------------- helpers
def _digits(number: str) -> str:
    """Sirf digits — 10-digit Indian number ko 91XXXXXXXXXX bana deta hai."""
    d = _NUM_RE.sub("", number or "")
    if len(d) == 10:
        d = "91" + d
    return d


def _flatten(d, depth: int = 0, prefix: str = ""):
    """Nested JSON ko ek flat dict me laao (provider ke shape kuch bhi ho).

    Do tarah ki keys banti hain:
      • flat key       — {"carrier": {"name": "Airtel"}} → "name"
      • prefixed key   — wahi → "carriername" (Twilio-style responses ke liye)
    """
    out = {}
    if depth > 3 or not isinstance(d, dict):
        return out
    for k, v in d.items():
        key = str(k).lower().replace("_", "").replace("-", "").replace(" ", "")
        if key and prefix and ("name" in key or "type" in key or "code" in key
                               or "region" in key or "location" in key):
            # prefixed version pehle rakho (zyada specific)
            out.setdefault(prefix + key, v if not isinstance(v, (dict, list)) else None)
        if isinstance(v, dict):
            out.update(_flatten(v, depth + 1, prefix=key))
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            out.update(_flatten(v[0], depth + 1, prefix=key))
        elif v not in (None, "", [], {}):
            out.setdefault(key, v)
    return out



def _pick(flat: dict, *names):
    for n in names:
        k = n.lower().replace("_", "").replace("-", "")
        if k in flat and flat[k] not in (None, "", [], {}):
            return flat[k]
    return None


# provider ke response me line-type ke alag-alag naam aate hain
_LINE_MAP = {
    "mobile": "📱 Mobile",
    "wireless": "📱 Mobile",
    "cell": "📱 Mobile",
    "landline": "☎️ Landline",
    "fixedline": "☎️ Landline",
    "fixed": "☎️ Landline",
    "fixed_line": "☎️ Landline",
    "voip": "💻 VoIP / Internet",
    "tollfree": "🆓 Toll Free",
    "toll_free": "🆓 Toll Free",
    "premium": "💎 Premium Rate",
    "satellite": "🛰️ Satellite",
    "unknown": "❔ Unknown",
}


def _nice_line_type(raw) -> str:
    s = str(raw or "").strip().lower().replace(" ", "").replace("_", "")
    if not s or s in ("na", "n/a", "null", "none", "-", "unknown", "undefined", "0"):
        return ""
    for k, v in _LINE_MAP.items():
        if k in s:
            return v
    return f"❔ {raw}"


def _clean_name(v) -> str:
    """Provider ke 'NA' / 'null' / '-' jaise junk ko khaali banao."""
    s = str(v or "").strip()
    return "" if s.lower() in ("", "na", "n/a", "null", "none", "-", "unknown", "undefined") else s


# --------------------------------------------------------------------------- lookup
DEMO_NOTE = ("Ye DEMO/sample data hai — kisi asli vyakti ka nahi. "
             "Asli data ke liye apni API lagao.")


def parse_payload(data: dict, ms: int = 0) -> dict:
    """Provider ke JSON response ko bot ke samajh wale shape me badlo.

    v59.6: yehi hissa lookup() bhi use karta hai — aur `/numtest` (mapping
    preview) bhi, taaki jo bot dikhata hai wahi user ko dikhe.
    """
    flat = _flatten(data)

    # provider kabhi kabhi galat number par valid:false deta hai
    valid = _pick(flat, "valid", "isvalid", "validnumber", "status")
    if isinstance(valid, bool) and valid is False and _pick(flat, "valid") is False:
        _msg = _clean_name(_pick(flat, "message", "error", "reason")) or \
            "Provider ke hisaab se ye number valid nahi hai."
        return {"ok": False, "invalid_number": True, "error": _msg, "latency_ms": ms}

    # kabhi response error-only hota hai
    if not valid and _pick(flat, "error", "errormessage") and not _pick(
            flat, "carrier", "operator", "network", "networkname"):
        return {"ok": False,
                "error": _clean_name(_pick(flat, "error", "errormessage"))[:120]}

    operator = _clean_name(_pick(flat, "carrier", "carrier_name", "carriername",
                                 "operator", "operatorname", "network",
                                 "network_name", "networkname", "provider",
                                 "providername"))
    circle = _clean_name(_pick(flat, "location", "circle", "region", "state",
                               "zone", "geolocation", "area",
                               "carrier_region", "carrierregion"))
    line_type = _nice_line_type(_pick(flat, "linetype", "line_type", "type",
                                      "numbertype", "phonetype", "carrier_type",
                                      "carrier_type_raw", "carriertype"))
    ported = _clean_name(_pick(flat, "ported", "mnp", "isported", "portability"))
    country = _clean_name(_pick(flat, "countryname", "country", "countryname_en"))
    country_code = _clean_name(_pick(flat, "countrycode", "countryprefix", "dialcode"))

    # ---------- v58: OWNER / EXTRA fields (agar AAPKI API bheje) ----------
    # Ye sirf tab bharte hain jab aapki API response me ye fields hon.
    # Hum khud kahin se ye data NAHI laate — jo API deti hai wahi dikhate hain.
    _owner = {
        "name": _clean_name(_pick(flat, "name", "ownername", "ownername",
                                  "subscribername", "customername", "fullname",
                                  "holdername", "username")),
        "father": _clean_name(_pick(flat, "father", "fathername", "fathersname",
                                    "guardian", "guardianname", "sonof", "so")),
        "alt": _clean_name(_pick(flat, "alt", "altmobile", "alternate",
                                 "altnumber", "phones", "altphones",
                                 "othernumbers", "linkednumbers")),
        "region": _clean_name(_pick(flat, "region", "state", "circle",
                                    "telecomcircle", "location", "area")),
        "govt_id": _clean_name(_pick(flat, "govtid", "idnumber", "aadhaar",
                                     "uid", "documentid", "idproof")),
        "address": _clean_name(_pick(flat, "address", "addresses", "fulladdress",
                                     "permanentaddress", "addr")),
    }
    # v59.3: agar aapki API sirf owner data (naam/pita/pata) bhejti hai aur
    # operator/circle nahi — to bhi kaam kare (pehle "format match nahi hua"
    # bolta tha, jabki naam aa gaya tha). Ab dono me se kuch bhi ho to OK.
    if not any((operator, circle, line_type)) and not any(_owner.values()):
        return {"ok": False, "error": ("Provider ne carrier/owner data nahi diya — response "
                                       "ka format match nahi hua. URL/params check karo.")}

    _extra = {}
    if isinstance(data, dict):
        for _k in ("addresses", "address_list", "alt_numbers", "numbers",
                   "phones_list", "other_numbers"):
            if isinstance(data.get(_k), list):
                _extra[_k] = [str(x) for x in data[_k][:6] if x]
            _flatk = _k.replace("_", "").lower()
            if _flatk in flat and isinstance(flat.get(_flatk), list):
                _extra[_k] = [str(x) for x in flat[_flatk][:6] if x]

    out = {
        "ok": True,
        "source": "provider",
        "operator": operator,
        "circle": circle,
        "type": line_type,
        "ported": ported,
        "country": country,
        "country_code": country_code,
        "owner": {k: v for k, v in _owner.items() if v},
        "extra": _extra,
        "latency_ms": ms,
        "provider_live": True,
        "provider_host": re.sub(r"^https?://", "", provider_url()).split("/")[0][:40],
    }
    return out


def demo_mode() -> bool:
    """NUMINFO_DEMO=on → Number Info card SAMPLE (dummy) data ke saath dikhta hai.

    Isse aap bina API dekh sakte ho ki card kaisa aayega. Koi asli vyakti ka
    data nahi hota — sab clearly nakli values hain.
    """
    return _env("NUMINFO_DEMO", "").strip().lower() in ("1", "on", "true", "yes", "haan", "y")


def demo_result(number: str = "") -> dict:
    """Sample (dummy) result — bilkul wahi shape jo asli API deti hai."""
    digits = _digits(number) or "9000000001"
    _intl = "+91 " + (digits[-10:] if len(digits) >= 10 else digits)
    return {
        "ok": True,
        "source": "demo",
        "demo": True,
        "operator": "Jio",
        "circle": "Bihar",
        "type": "📱 Mobile",
        "ported": None,
        "country": "India",
        "country_code": "+91",
        "owner": {
            "name": "RAHUL KUMAR (SAMPLE)",
            "father": "MOHAN LAL KUMAR (SAMPLE)",
            "alt": "9000000001",
            "region": "BIHAR JIO",
            "govt_id": "000000000000 (SAMPLE)",
            "address": ("S/O MOHAN LAL KUMAR, Ward 02, SAMPLE NAGAR, Post SAMPLE, "
                        "Dist. SAMPLE, Bihar, 000000 (SAMPLE)"),
        },
        "extra": {},
        "latency_ms": 0,
        "provider_live": False,
        "note": DEMO_NOTE,
    }


def lookup(number: str) -> dict:
    """Provider se carrier data laao. Kabhi raise nahi karta."""
    if not is_configured():
        # v59.5: URL set nahi, par DEMO mode ON → sample card dikhao (dummy data)
        if demo_mode():
            return demo_result(number)
        return {"ok": False, "not_configured": True,
                "error": "NUMINFO_PROVIDER_URL set nahi hai (Number Info apne sources se chalega)."}

    digits = _digits(number)
    if not digits:
        return {"ok": False, "error": "Number khaali hai."}

    ck = f"np:{hash(digits)}"
    if _CACHE is not None:
        hit = _CACHE.get(ck)
        if hit is not None:
            return {**hit, "cached": True, "provider_live": True}

    url = provider_url().replace("{number}", digits)
    params: dict = {}
    headers = dict(UA)
    key = provider_key()
    auth = provider_auth()

    if "{number}" not in provider_url():
        params[provider_param()] = digits
    if key:
        if auth == "query":
            params[provider_key_param()] = key
        elif auth == "header":
            headers[provider_header_name()] = key
        elif auth == "bearer":
            headers["Authorization"] = f"Bearer {key}"
    # provider_url ke apne query params preserve karo (jaise ?full=1)
    if "?" in url:
        from urllib.parse import parse_qsl, urlsplit
        _sp = urlsplit(url)
        for _k, _v in parse_qsl(_sp.query, keep_blank_values=True):
            params.setdefault(_k, _v)
        url = f"{_sp.scheme}://{_sp.netloc}{_sp.path}"

    t0 = time.time()
    try:
        if provider_method() == "post" and http_post is not None:
            # POST API: number/key body me jaate hain (JSON)
            _body = dict(params)
            r = http_post(url, json=_body or None, params=None, headers=headers,
                          timeout=provider_timeout(), retries=1)
        else:
            r = http_get(url, params=params or None, headers=headers,
                         timeout=provider_timeout(), retries=1)
        ms = int((time.time() - t0) * 1000)
        if r.status_code == 401 or r.status_code == 403:
            return {"ok": False, "auth": True, "status": r.status_code,
                    "error": ("Provider ne key reject ki (HTTP %d). Render me "
                              "NUMINFO_PROVIDER_KEY check karo." % r.status_code)}
        if r.status_code == 429:
            return {"ok": False, "rate_limited": True, "status": 429,
                    "error": "Provider ki limit khatam (HTTP 429). Thodi der baad try karo."}
        if r.status_code >= 400:
            return {"ok": False, "status": r.status_code,
                    "error": f"Provider HTTP {r.status_code}. URL/params check karo."}
        try:
            data = r.json()
        except Exception:                                    # noqa: BLE001
            return {"ok": False, "error": "Provider ne JSON nahi bheja (URL galat ho sakta hai)."}
    except Exception as e:                                   # noqa: BLE001
        return {"ok": False, "error": f"Provider se connect nahi hua: {str(e)[:90]}",
                "soft": True}

    out = parse_payload(data)
    if _CACHE is not None:
        _CACHE.put(ck, out, 21600)                            # 6 ghante
    return out


# --------------------------------------------------------------------------- status
def status() -> dict:
    """`/numapi` command ke liye — key kabhi print nahi hoti (sirf set/unset)."""
    u = provider_url()
    k = provider_key()
    return {
        "configured": is_configured(),
        "url": u or "(set nahi hai)",
        "url_has_number_placeholder": "{number}" in u,
        "key_set": bool(k and k.lower() not in _PLACEHOLDER),
        "auth": provider_auth(),
        "param": provider_param(),
        "key_param": provider_key_param(),
        "header": provider_header_name(),
        "timeout_s": provider_timeout(),
        "cache_hours": 6,
        "net_ok": _NET,
    }


def status_card() -> str:
    """Telegram-ready card (HTML). Key kabhi nahi dikhti."""
    s = status()
    ok = "✅ SET HAI" if s["configured"] else "⚠️ SET NAHI HAI"
    key_line = "✅ set (chhupi hui)" if s["key_set"] else "— (khali)"

    if s["configured"]:
        how = (f"• <b>URL:</b> <code>{_esc(s['url'][:70])}</code>\n"
               f"• <b>Number param:</b> <code>{_esc(s['param'])}</code>"
               + ("  <i>(URL me {'{number}'} placeholder hai)</i>"
                  if s["url_has_number_placeholder"] else "") + "\n"
               f"• <b>Key:</b> {key_line}   • <b>Auth:</b> {s['auth']}\n"
               f"• <b>Timeout:</b> {s['timeout_s']}s   • <b>Cache:</b> {s['cache_hours']} ghante")
        return (f"📱 <b>NUMBER INFO — PROVIDER</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔌 <b>Status:</b> {ok}\n{how}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "<i>Number Info ab aapki API se live data lega. Key Render me hi "
                "rehti hai — bot kabhi dikhata nahi.</i>")
    return ("📱 <b>NUMBER INFO — PROVIDER</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔌 <b>Status:</b> {ok}\n"
            "• URL: <i>(khali)</i>   • Key: <i>(khali)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Aapki API lagane ke liye</b> — Render → <b>utility-duniya-bot</b> → "
            "<b>Environment</b> me ye 2 lines add karo:\n"
            "<code>NUMINFO_PROVIDER_URL</code> = aapki API ka endpoint\n"
            "<code>NUMINFO_PROVIDER_KEY</code> = us API ki key\n\n"
            "👉 Poori guide: <code>NUMBER-INFO-API-SETUP.md</code> (GitHub par)\n"
            "<i>Abhi Number Info purane apne sources se chal raha hai — kaam band nahi hai.</i>")


def _esc(t: str) -> str:
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


__all__ = [
    "is_configured", "lookup", "status", "status_card",
    "provider_url", "provider_key", "provider_auth", "provider_param",
]
