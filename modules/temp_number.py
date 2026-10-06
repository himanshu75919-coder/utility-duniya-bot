# -*- coding: utf-8 -*-
"""
📞 TEMP MAIL (NUMBER + OTP) — v71.9
===================================
User ka order: "alag tool 'Temp Mail' — 100% FREE, har user ko ALAG number,
10+ services + 10+ countries, banking OTP par saaf warning."

Kaam kaise karta hai (100% free — koi key / paisa / login NAHI):
  • Ye tool public "receive SMS" sites se number + inbox padhta hai
    (jaise browser me wahi page kholna — bilkul wahi kaam, koi login nahi)
  • 3 sources: receivesms.co (primary) · receive-sms-free.cc · temp-sms.org
  • Har Telegram user ko uske uid se ek ALAG number milta hai —
    bot ke meta-store me "taken" list rehti hai, doosre user ka number repeat nahi
  • Bank / UPI / KYC / paise wale OTP ke liye HARD warning (user ka order)

Red lines (kabhi nahi):
  ✗ Bank / UPI / KYC / loan / wallet / paisa transfer — ye number mat do
  ✗ Kisi ka personal data, login chori, hacking — kuch nahi
  ✗ Paid API / key / paisa — sab kuch free

Crash-proof: har public function try/except me hai; fail hone par
    {"ok": False, "error": "saaf wajah"}
return karta hai — khaali/blank card kabhi nahi (user ka rule).
"""

import html as _html
import logging
import re
import threading
import time

import requests

log = logging.getLogger(__name__)

UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ============================================================ SERVICES (16)
# (key, label, emoji, recommended-country order)
SERVICES = (
    ("whatsapp",  "WhatsApp",       "💬", ("us", "ca", "fi", "uk", "nl")),
    ("telegram",  "Telegram",       "✈️", ("us", "ca", "uk")),
    ("instagram", "Instagram",      "📸", ("us", "ca", "uk", "fi")),
    ("facebook",  "Facebook",       "📘", ("us", "ca", "uk")),
    ("google",    "Google / Gmail", "🔎", ("us", "ca", "nz", "au")),
    ("discord",   "Discord",        "🎮", ("us", "ca")),
    ("tiktok",    "TikTok",         "🎵", ("us", "ca")),
    ("twitter",   "X (Twitter)",    "🐦", ("us", "ca")),
    ("snapchat",  "Snapchat",       "👻", ("us", "ca")),
    ("wechat",    "WeChat",         "🟩", ("us", "ca")),
    ("signal",    "Signal",         "🔒", ("us", "ca")),
    ("uber",      "Uber / Ola",     "🚕", ("us", "ca", "uk", "au")),
    ("amazon",    "Amazon",         "📦", ("us", "ca", "uk", "de")),
    ("netflix",   "Netflix",        "🎬", ("us", "ca", "uk")),
    ("linkedin",  "LinkedIn",       "💼", ("us", "ca", "uk")),
    ("tinder",    "Tinder",         "💘", ("us", "ca", "uk")),
)

SVC_BY_KEY = {k: (lbl, em, rec) for k, lbl, em, rec in SERVICES}

# ============================================================ COUNTRIES (26)
# rc  = receivesms.co slug  ("" = is source par nahi)
# rsf = receive-sms-free.cc URL naam
# ts  = temp-sms.org dial-code prefix
COUNTRIES = (
    {"cc": "us", "name": "United States", "flag": "🇺🇸", "rc": "us",         "rsf": "USA",         "ts": "1"},
    {"cc": "uk", "name": "United Kingdom", "flag": "🇬🇧", "rc": "",          "rsf": "",            "ts": "44"},
    {"cc": "ca", "name": "Canada",         "flag": "🇨🇦", "rc": "canadian",  "rsf": "Canada",      "ts": ""},
    {"cc": "au", "name": "Australia",      "flag": "🇦🇺", "rc": "australian", "rsf": "",           "ts": "61"},
    {"cc": "de", "name": "Germany",        "flag": "🇩🇪", "rc": "german",    "rsf": "",            "ts": ""},
    {"cc": "fr", "name": "France",         "flag": "🇫🇷", "rc": "french",    "rsf": "",            "ts": ""},
    {"cc": "nl", "name": "Netherlands",    "flag": "🇳🇱", "rc": "dutch",     "rsf": "Netherlands", "ts": ""},
    {"cc": "nz", "name": "New Zealand",    "flag": "🇳🇿", "rc": "new-zealand", "rsf": "",          "ts": "64"},
    {"cc": "fi", "name": "Finland",        "flag": "🇫🇮", "rc": "",          "rsf": "Finland",     "ts": ""},
    {"cc": "se", "name": "Sweden",         "flag": "🇸🇪", "rc": "swedish",   "rsf": "",            "ts": ""},
    {"cc": "ch", "name": "Switzerland",    "flag": "🇨🇭", "rc": "swiss",     "rsf": "",            "ts": ""},
    {"cc": "pl", "name": "Poland",         "flag": "🇵🇱", "rc": "",          "rsf": "Poland",      "ts": ""},
    {"cc": "be", "name": "Belgium",        "flag": "🇧🇪", "rc": "",          "rsf": "Belgium",     "ts": "32"},
    {"cc": "at", "name": "Austria",        "flag": "🇦🇹", "rc": "",          "rsf": "",            "ts": "43"},
    {"cc": "es", "name": "Spain",          "flag": "🇪🇸", "rc": "spanish",   "rsf": "",            "ts": ""},
    {"cc": "it", "name": "Italy",          "flag": "🇮🇹", "rc": "",          "rsf": "",            "ts": ""},
    {"cc": "no", "name": "Norway",         "flag": "🇳🇴", "rc": "norwegian", "rsf": "",            "ts": ""},
    {"cc": "pr", "name": "Puerto Rico",    "flag": "🇵🇷", "rc": "puerto-rico", "rsf": "",          "ts": ""},
    {"cc": "ar", "name": "Argentina",      "flag": "🇦🇷", "rc": "argentine", "rsf": "",            "ts": ""},
    {"cc": "co", "name": "Colombia",       "flag": "🇨🇴", "rc": "colombian", "rsf": "",            "ts": ""},
    {"cc": "hr", "name": "Croatia",        "flag": "🇭🇷", "rc": "croatian",  "rsf": "",            "ts": ""},
    {"cc": "cy", "name": "Cyprus",         "flag": "🇨🇾", "rc": "cyprus",    "rsf": "",            "ts": ""},
    {"cc": "hu", "name": "Hungary",        "flag": "🇭🇺", "rc": "hungarian", "rsf": "",            "ts": ""},
    {"cc": "mt", "name": "Malta",          "flag": "🇲🇹", "rc": "malta",     "rsf": "",            "ts": ""},
    {"cc": "sk", "name": "Slovakia",       "flag": "🇸🇰", "rc": "slovak",    "rsf": "",            "ts": ""},
    {"cc": "lk", "name": "Sri Lanka",      "flag": "🇱🇰", "rc": "sri-lanka", "rsf": "",            "ts": ""},
)

COUNTRY_BY_CC = {c["cc"]: c for c in COUNTRIES}

RC_BASE = "https://receivesms.co"
RSF_BASE = "https://receive-sms-free.cc"
TS_BASE = "https://temp-sms.org"

# ============================================================ HTTP + THROTTLE
_SESSION = requests.Session()
_SESSION.headers.update(UA)

_LOCK = threading.Lock()
_LAST_REQ = {}          # host -> ts (last request time)
_BLOCK_UNTIL = {}       # host -> ts (429/403 ke baad chhutti)
_MIN_GAP = {            # host -> min seconds between 2 requests
    "receivesms.co": 1.0,
    "receive-sms-free.cc": 3.5,
    "temp-sms.org": 2.0,
}
_CACHE = {}             # key -> (expire_ts, value)


def _cache_get(key):
    try:
        item = _CACHE.get(key)
        if item and item[0] > time.time():
            return item[1]
    except Exception:                                       # noqa: BLE001
        pass
    return None


def _cache_set(key, val, ttl):
    try:
        _CACHE[key] = (time.time() + float(ttl), val)
        if len(_CACHE) > 400:                               # chhota-sa safai
            now = time.time()
            for k in [k for k, v in _CACHE.items() if v[0] <= now][:100]:
                _CACHE.pop(k, None)
    except Exception:                                       # noqa: BLE001
        pass


def _host_of(url: str) -> str:
    try:
        return url.split("/")[2].lower()
    except Exception:                                       # noqa: BLE001
        return ""


def _get(url: str, timeout: int = 14):
    """Throttled GET. 429/403 par host ko thodi der 'chhutti' de deta hai.

    Return: (status_code, text) — kabhi raise nahi karta.
    """
    host = _host_of(url)
    try:
        with _LOCK:
            until = _BLOCK_UNTIL.get(host, 0)
            if until > time.time():
                return 0, f"blocked:{int(until - time.time())}s"
            gap = _MIN_GAP.get(host, 1.2)
            wait = _LAST_REQ.get(host, 0) + gap - time.time()
            if wait > 0:
                time.sleep(min(wait, gap))
            _LAST_REQ[host] = time.time()
        r = _SESSION.get(url, timeout=timeout, allow_redirects=True)
        code, text = r.status_code, r.text
        if code in (429, 403, 503):
            with _LOCK:
                _BLOCK_UNTIL[host] = time.time() + (180 if code == 429 else 120)
        return code, text
    except Exception as e:                                  # noqa: BLE001
        return 0, f"error:{type(e).__name__}"


# ============================================================ HELPERS
def _txt(raw: str) -> str:
    """HTML → saaf text (tags hatao + entities kholo + space theek)."""
    try:
        s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", str(raw or ""),
                   flags=re.S | re.I)
        s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
        s = re.sub(r"<[^>]+>", " ", s)
        s = _html.unescape(s)
        s = s.replace("\u200b", "").replace("\xa0", " ")
        return re.sub(r"\s+", " ", s).strip()
    except Exception:                                       # noqa: BLE001
        return ""


def pretty_number(digits: str) -> str:
    """+18282768125 → +1 828-276-8125 (sirf dikhane ke liye)."""
    d = re.sub(r"\D", "", digits or "")
    if not d:
        return ""
    if len(d) == 11 and d.startswith("1"):
        return f"+1 {d[1:4]}-{d[4:7]}-{d[7:]}"
    if len(d) == 12 and d.startswith("44"):
        return f"+44 {d[2:6]} {d[6:]}"
    return "+" + d


# ============================================================ PARSERS
_RC_CARD = re.compile(r'<a class="card card-link" href="/([a-z-]+)-phone-number/(\d+)/">(.*?)</a>',
                      re.S | re.I)


def _rc_pool(cc: str, slug: str):
    """receivesms.co country page → [{nid, number}]."""
    code, html = _get(f"{RC_BASE}/{slug}-phone-numbers/{cc}/")
    if code != 200:
        return [], f"receivesms.co:{code}"
    out, seen = [], set()
    for _slug, num_id, block in _RC_CARD.findall(html):
        if num_id in seen:
            continue
        seen.add(num_id)
        m = re.search(r"<strong>\s*\+?([\d\s\-()]{7,20})\s*</strong>", block)
        num = re.sub(r"\D", "", m.group(1)) if m else ""
        out.append({"nid": f"rc:{cc}:{num_id}", "cc": cc, "number": num,
                    "display": pretty_number(num) if num else "", "src": "rc"})
    return out, ("" if out else "khaali")


def _rsf_pool(cc: str, name: str):
    """receive-sms-free.cc country page → locked countries skip."""
    if not name:
        return [], "skip"
    code, html = _get(f"{RSF_BASE}/Free-{name}-Phone-Number/")
    if code != 200:
        return [], f"receive-sms-free.cc:{code}"
    ids = []
    for m in re.finditer(rf"Free-{re.escape(name)}-Phone-Number/(\d+)/", html):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    out = [{"nid": f"rsf:{cc}:{i}", "cc": cc, "number": i,
            "display": pretty_number(i), "src": "rsf"} for i in ids[:24]]
    return out, ("" if out else "khaali")


def _ts_pool(cc: str, dial: str, refresh=False):
    """temp-sms.org homepage → numbers (dial code se filter)."""
    if not dial:
        return [], "skip"
    home = _cache_get("ts:home")
    if home is None or refresh:
        code, html = _get(TS_BASE + "/")
        if code != 200:
            return [], f"temp-sms.org:{code}"
        nums = sorted({n for n in re.findall(r'href="/sms/(\d+)"', html)})
        home = nums
        _cache_set("ts:home", home, 600)
    # +1 wale US maane jaate hain (202/276 = USA), baaki dial-code match
    out = []
    for n in home:
        if cc == "us" and n.startswith("1") and not n.startswith(("11", "12", "13", "14", "15", "16", "17", "18", "19")):
            pass
        if not n.startswith(dial):
            continue
        if cc == "us" and len(n) < 11:
            continue
        out.append({"nid": f"ts:{cc}:{n}", "cc": cc, "number": n,
                    "display": pretty_number(n), "src": "ts"})
    return out, ("" if out else "khaali")


def pool(cc: str, refresh: bool = False) -> dict:
    """Ek desh ke saare numbers (3 sources mila kar). Cached 30 min.

    Return: {"ok": True, "numbers": [...], "notes": [...]}
            {"ok": False, "error": "saaf wajah"}
    """
    cc = (cc or "").lower()
    c = COUNTRY_BY_CC.get(cc)
    if not c:
        return {"ok": False, "error": "Ye desh support me nahi hai."}
    key = f"pool:{cc}"
    if not refresh:
        hit = _cache_get(key)
        if hit is not None:
            return hit
    nums, notes = [], []
    for fn, args in (
        (_rc_pool, (cc, c.get("rc") or "")),
        (_rsf_pool, (cc, c.get("rsf") or "")),
        (_ts_pool, (cc, c.get("ts") or "")),
    ):
        try:
            if fn is _rc_pool and not c.get("rc"):
                continue
            got, note = fn(*args) if fn is not _ts_pool else fn(*args)
            for n in got:
                if n["nid"] not in {x["nid"] for x in nums}:
                    nums.append(n)
            if got:
                notes.append(f"{got[0]['src']}:{len(got)}")
        except Exception as e:                              # noqa: BLE001
            notes.append(f"err:{type(e).__name__}")
    res = {"ok": bool(nums), "numbers": nums, "notes": notes,
           "error": "" if nums else "Is desh me abhi number khaali hai — thodi der baad ya doosra desh try karo."}
    _cache_set(key, res, 1800)
    return res


# ------------------------------------------------------------ INBOX
_RC_ART = re.compile(r'<article class="entry-card[^"]*">(.*?)</article>', re.S)
_RSF_ITEM = re.compile(r'<div class="sms-item[^"]*">(.*?)</div>\s*</div>\s*</div>', re.S)


def _rc_inbox(cc: str, num_id: str):
    code, html = _get(f"{RC_BASE}/{cc}-phone-number/{num_id}/")
    if code != 200:
        return None, f"receivesms.co:{code}"
    mnum = re.search(r"Phone Number\s*\+?([\d\s\-]{8,20})", html)
    num = re.sub(r"\D", "", mnum.group(1)) if mnum else ""
    last = re.search(r"Last activity:\s*([^<]{2,40})", html)
    c24 = re.search(r"Messages \(24h\):\s*(\d+)", html)
    msgs = []
    for block in _RC_ART.findall(html)[:14]:
        frm = re.search(r'class="from-link"[^>]*>([^<]+)<', block)
        code_m = re.search(r'data-code="(\d+)"', block)
        tim = re.search(r'class="muted"[^>]*>([^<]{2,40})<', block)
        txt = re.search(r'<div class="sms">(.*?)</div>', block, re.S)
        text = _txt(txt.group(1)) if txt else ""
        if not (text or code_m):
            continue
        msgs.append({"from": _txt(frm.group(1)) if frm else "",
                     "time": _txt(tim.group(1)) if tim else "",
                     "text": text,
                     "code": code_m.group(1) if code_m else ""})
    return {"number": num, "messages": msgs,
            "last_activity": _txt(last.group(1)) if last else "",
            "count24": int(c24.group(1)) if c24 else 0}, ""


def _rsf_inbox(cc: str, num: str):
    c = COUNTRY_BY_CC.get(cc) or {}
    name = c.get("rsf") or ""
    if not name:
        return None, "skip"
    code, html = _get(f"{RSF_BASE}/Free-{name}-Phone-Number/{num}/")
    if code != 200:
        return None, f"receive-sms-free.cc:{code}"
    mnum = re.search(r"Phone number\s*\+?([\d\s]{8,20})", html)
    num_full = re.sub(r"\D", "", mnum.group(1)) if mnum else num
    msgs = []
    # sms-item blocks — split se (aakhri block bhi pakda jaye)
    for block in re.split(r'<div class="sms-item', html)[1:][:14]:
        frm = re.search(r'class="sender-badge"[^>]*>([^<]+)<', block)
        tim = re.search(r'class="time-text[^"]*"[^>]*>(.*?)</span>', block, re.S)
        txt = re.search(r'<p class="sms-content[^"]*">(.*?)</p>', block, re.S)
        text = _txt(txt.group(1)) if txt else ""
        if not text:
            continue
        msgs.append({"from": _txt(frm.group(1)) if frm else "",
                     "time": _txt(tim.group(1)) if tim else "",
                     "text": text, "code": extract_code(text)})
    return {"number": num_full, "messages": msgs,
            "last_activity": "", "count24": 0}, ""


def _ts_inbox(cc: str, num: str):
    code, html = _get(f"{TS_BASE}/sms/{num}")
    if code != 200:
        return None, f"temp-sms.org:{code}"
    body = html.split('id="messages"', 1)[-1]
    chunks = body.split('<hr class="hr-bottom-line">')[1:]
    msgs = []
    for ch in chunks[:14]:
        frm = re.search(r"<b>\s*\+?([^<]{2,24})\s*</b>", ch)
        tim = re.search(r"date-padding[^>]*>\s*([^<]{2,40})", ch)
        txt = re.search(r'msg-padding[^>]*>(.*?)</div>', ch, re.S)
        text = _dedupe_watermark(_txt(txt.group(1)) if txt else "")
        if not text:
            continue
        msgs.append({"from": _txt(frm.group(1)) if frm else "",
                     "time": _txt(tim.group(1)) if tim else "",
                     "text": text, "code": extract_code(text)})
    return {"number": num, "messages": msgs,
            "last_activity": "", "count24": 0}, ""


def _dedupe_watermark(text: str) -> str:
    """temp-sms.org apna watermark homoglyph me ghusata hai — us pehle
    jhoothe vaakya ko hata do (asli SMS text bacha rahe)."""
    try:
        parts = re.split(r"(?<=\.)\s+", text, maxsplit=1)
        if len(parts) == 2:
            head = parts[0]
            non_ascii = sum(1 for ch in head if ord(ch) > 127)
            if head and non_ascii / max(len(head), 1) > 0.18:
                return parts[1].strip()
    except Exception:                                       # noqa: BLE001
        pass
    return text


def inbox(nid: str, ttl: float = 12.0, force: bool = False) -> dict:
    """Ek number ka inbox (latest messages). Cached — bar-bar site nahi chedte.

    Return: {"ok": True, "number", "display", "messages": [...],
             "last_activity", "count24", "cached": bool}
            {"ok": False, "error": "saaf wajah"}
    """
    if not force:
        hit = _cache_get(f"inbox:{nid}")
        if hit is not None:
            h = dict(hit)
            h["cached"] = True
            return h
    try:
        parts = str(nid or "").split(":")
        src = parts[0] if parts else ""
        cc = parts[1] if len(parts) > 2 else ""
        key = ":".join(parts[2:]) if len(parts) > 2 else ""
        if not src or not cc or not key:
            return {"ok": False, "error": "Number id galat hai."}
        if src == "rc":
            data, err = _rc_inbox(cc, key)
        elif src == "rsf":
            data, err = _rsf_inbox(cc, key)
        elif src == "ts":
            data, err = _ts_inbox(cc, key)
        else:
            data, err = None, "source pata nahi"
        if not data:
            return {"ok": False, "error": err or "Site ne jawab nahi diya.",
                    "src": src}
        num = data.get("number") or key
        res = {"ok": True, "nid": nid, "src": src, "cc": cc,
               "number": num, "display": pretty_number(num),
               "messages": data.get("messages") or [],
               "last_activity": data.get("last_activity") or "",
               "count24": int(data.get("count24") or 0),
               "cached": False, "ts": time.time()}
        if any(m.get("code") for m in res["messages"]) or res["messages"]:
            pass  # sirf dhyan se save karo
        _cache_set(f"inbox:{nid}", res, ttl)
        return res
    except Exception as e:                                  # noqa: BLE001
        log.warning("tnum inbox fail: %s", e)
        return {"ok": False, "error": f"Technical dikkat ({type(e).__name__})."}


# ============================================================ PICK / CODE / BANK
def pick(numbers, taken=None, uid: int = 0, avoid=None):
    """Alag-alag users ko alag number — deterministic + 'taken' set respect."""
    try:
        cand = list(numbers or [])
        if not cand:
            return None
        taken = set(taken or ())
        avoid = set(avoid or ())
        cand.sort(key=lambda n: str(n.get("nid")))
        free = [n for n in cand if n.get("nid") not in taken and n.get("nid") not in avoid]
        if not free:
            free = [n for n in cand if n.get("nid") not in avoid] or cand
        idx = (int(uid or 0) * 2654435761) % len(free)
        return free[idx]
    except Exception:                                       # noqa: BLE001
        return None


CODE_PATTERNS = (
    r"(?:code|otp|pin|password|verification)\D{0,26}(\d{4,8})",
    r"(\d{4,8})\D{0,26}(?:is your|verification code|otp)",
    r"\b(\d{6})\b",
)


def extract_code(text: str) -> str:
    """SMS text se OTP nikaalo (pehla sahi pattern)."""
    t = _txt(text)
    for pat in CODE_PATTERNS:
        m = re.search(pat, t, re.I)
        if m:
            return m.group(1)
    return ""


_BANK_RE = re.compile(
    r"\b(bank|upi|kyc|loan|wallet|aadhaar|aadhar|pan\s*card|paytm|phonepe|gpay|"
    r"google\s*pay|bhim|imps|neft|rtgs|credit\s*card|debit\s*card|transaction|"
    r"balance|refund|insurance|mutual\s*fund|demat|trading|broker|"
    r"sbi|hdfc|icici|axis|kotak|pnb|bob|idfc|yes\s*bank|federal\s*bank)\b",
    re.I,
)


def looks_banky(text: str) -> bool:
    """Bank/paise wala SMS lagta hai? (warna user ko 'safe' batana galat hoga)"""
    try:
        return bool(_BANK_RE.search(_txt(text)))
    except Exception:                                       # noqa: BLE001
        return False
