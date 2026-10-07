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

import hashlib
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

# ============================================================ SERVICE (v74.3: sirf WhatsApp)
# User order: "temp number me sirf ek hi service ho — WhatsApp ke."
# (Purani 16 services ki list ek-ek karke badhayi jayegi jab wo test ho jaayen.)
SERVICES = (
    ("whatsapp", "WhatsApp", "💬", ("fi", "nl", "us")),
)

SVC_BY_KEY = {k: (lbl, em, rec) for k, lbl, em, rec in SERVICES}

# ============================================================ COUNTRIES (v74.3: 3 desh)
# User order: "country sirf 2-3 rakho jinke number par OTP easily aata hai."
# Teeno par WhatsApp OTP test: numbers milte hain + OTP aata hai. ✅
COUNTRIES = (
    {"cc": "fi", "name": "Finland",     "flag": "🇫🇮", "rc": "",          "rsf": "Finland",     "ts": ""},
    {"cc": "nl", "name": "Netherlands", "flag": "🇳🇱", "rc": "dutch",     "rsf": "Netherlands", "ts": ""},
    {"cc": "us", "name": "United States", "flag": "🇺🇸", "rc": "us",      "rsf": "USA",         "ts": "1"},
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


_MSG_START_RE = re.compile(
    r"(?:(?<=\s)|^)(G-[A-Za-z0-9]{4,10}\b|\d{3,4}[-\s]\d{3,4}\b|\d{4,8}\b|"
    r"Your\b|You\b|Yr\b|Dear\b|Code\b|OTP\b|code\b|OTP\b|Verification\b|"
    r"verification\b|\[|Enter\b|is your\b)", re.I)


def _dedupe_watermark(text: str) -> str:
    """temp-sms.org apna watermark (homoglyph me) aage lagata hai — hata do.

    v71.10 upgrade: pehle sirf pehla vaakya dekhta tha, watermark kabhi-kabhi
    bach jata tha (user ne screenshot me dekha: "1 Ṫℏΐš ... Temp-SMS.ðŗĝ ...").
    Ab: (1) non-ascii junk hatao, (2) 'SMS' wale token tak sab kaato,
    (3) warna message-jaisi shuruaat (G-xxxxxx / digits / Your / Code...) se pakdo.
    """
    try:
        t = str(text or "").replace("\u200b", "").strip()
        if not t:
            return t
        head = t[:70]
        _na = [ch for ch in head if ord(ch) > 127]
        if t and len(_na) / max(len(head), 1) < 0.12:
            return t                                    # saaf text — chhedo mat
        # asli bhasha (Hindi/Arabic/Chinese) ho to hilao bhi nahi — ye jail
        # sirf homoglyph junk ke liye hai (Latin/Math weird blocks)
        _lang = sum(1 for ch in _na if 0x0900 <= ord(ch) <= 0x097F
                    or 0x0600 <= ord(ch) <= 0x06FF
                    or 0x4E00 <= ord(ch) <= 0x9FFF)
        if _na and _lang / len(_na) >= 0.40:
            return t
        # (1) sirf ASCII bachao (homoglyph jail)
        a = "".join(ch if (32 <= ord(ch) < 127) else " " for ch in t)
        a = re.sub(r"\s+", " ", a).strip()
        # (2) 'SMS' wale token tak sab kaato (asli watermark: "Temp-SMS.org")
        m = re.search(r"\S*SMS\S*", a, re.I)
        if m and m.start() < 90:
            a = a[m.end():]
        # (3) message-jaisi shuruaat dhoondo
        m2 = _MSG_START_RE.search(a)
        if m2 and m2.start() > 0:
            a = a[m2.start():]
        a = re.sub(r"^\s*\d{1,2}\s+(?=\D)", "", a).strip()   # "1 " counter hatao
        a = re.sub(r"^[\s.\-•*]+", "", a).strip()
        return a if len(a) >= 6 else t
    except Exception:                                       # noqa: BLE001
        return str(text or "")


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

# ============================================================ v71.10: SERVICE-AWARE OTP
#  User ka order: "service select karne par usi service ka sahi (6 digit) OTP
#  aaye, n ki 4 digit ya kisi aur website ka."  Isliye har app ke apne rules:
#    kw   = SMS me ye shabd ho to wo IS app ka SMS hai
#    lens = is app ke OTP ki lambai (pehla = sabse common)
SVC_RULES = {
    "whatsapp":  {"kw": ("whatsapp",),                                    "lens": (6,),    "hint": "6 digit"},
    "telegram":  {"kw": ("telegram",),                                    "lens": (5, 6),  "hint": "5 ya 6 digit"},
    "instagram": {"kw": ("instagram",),                                   "lens": (6,),    "hint": "6 digit"},
    "facebook":  {"kw": ("facebook",),                                    "lens": (6,),    "hint": "6 digit"},
    "google":    {"kw": ("google",),                                      "lens": (6,),    "hint": "6 digit (G-xxxxxx)",
                  "re": r"\bG-([A-Za-z0-9]{4,10})\b"},
    "discord":   {"kw": ("discord",),                                     "lens": (6,),    "hint": "6 digit"},
    "tiktok":    {"kw": ("tiktok",),                                      "lens": (6,),    "hint": "6 digit"},
    "twitter":   {"kw": ("twitter", "x confirmation", "your x code"),     "lens": (6,),    "hint": "6 digit"},
    "snapchat":  {"kw": ("snapchat",),                                    "lens": (6,),    "hint": "6 digit"},
    "wechat":    {"kw": ("wechat",),                                      "lens": (6,),    "hint": "6 digit"},
    "signal":    {"kw": ("signal",),                                      "lens": (6,),    "hint": "6 digit"},
    "uber":      {"kw": ("uber", "ola "),                                 "lens": (6,),    "hint": "6 digit"},
    "amazon":    {"kw": ("amazon",),                                      "lens": (6,),    "hint": "6 digit"},
    "netflix":   {"kw": ("netflix",),                                     "lens": (4, 6),  "hint": "4 ya 6 digit"},
    "linkedin":  {"kw": ("linkedin",),                                    "lens": (6,),    "hint": "6 digit"},
    "tinder":    {"kw": ("tinder",),                                      "lens": (6,),    "hint": "6 digit"},
}

_PHONE_MASK = re.compile(r"\+?\d[\d\s().\-]{7,}\d")
_URL_MASK = re.compile(r"(?:https?://|www\.)\S+|[\w.-]+\.(?:com|org|net|in|app|io|co)\S*", re.I)


def svc_hint(svc_key: str) -> str:
    """Us app ke OTP ki lambai ka hint (card me dikhta hai)."""
    return (SVC_RULES.get(str(svc_key or "")) or {}).get("hint") or "4-6 digit"


def svc_lens(svc_key: str):
    return tuple((SVC_RULES.get(str(svc_key or "")) or {}).get("lens") or ())


def service_match(msg, svc_key: str) -> bool:
    """Ye SMS us app ka hai? (sender ya text me app ka naam)"""
    try:
        rule = SVC_RULES.get(str(svc_key or ""))
        if not rule:
            return True                     # service pata nahi → sab dikhao
        hay = (str((msg or {}).get("from") or "") + " "
               + str((msg or {}).get("text") or "")).lower()
        return any(str(k) in hay for k in rule.get("kw") or ())
    except Exception:                       # noqa: BLE001
        return False


def _digits_candidates(text: str):
    """SMS me se saare code-jaisa number candidates (phone/URL mask kar ke)."""
    out = []
    try:
        t = _PHONE_MASK.sub(" ", str(text or ""))
        t = _URL_MASK.sub(" ", t)
        for m in re.finditer(r"(?<![\w/])(\d{3,4})[-\s](\d{3,4})(?![\w/])", t):
            out.append(m.group(1) + m.group(2))          # 123-456 → 123456
        for m in re.finditer(r"(?<![\w/])(\d{4,8})(?![\w/])", t):
            out.append(m.group(1))
    except Exception:                       # noqa: BLE001
        pass
    return out


def extract_code_svc(text: str, svc_key: str) -> str:
    """Us app ke hisaab se sahi lambai ka OTP nikaalo (6 digit wala 6 hi)."""
    try:
        rule = SVC_RULES.get(str(svc_key or ""))
        if not rule:
            return extract_code(text)
        lens = tuple(rule.get("lens") or ())
        for c in _digits_candidates(text):
            if len(c) in lens:
                return c
        # kuch apps (Google) alnum code bhejte hain — "G-F9u0R6"
        pat = rule.get("re")
        if pat:
            m = re.search(pat, str(text or ""))
            if m and any(ch.isdigit() for ch in m.group(1)):
                return m.group(1)
        return ""
    except Exception:                       # noqa: BLE001
        return ""


def code_len_note(text: str, svc_key: str) -> str:
    """SMS me code hai PAR lambai galat — user ko saaf batao."""
    try:
        if not text:
            return ""
        if extract_code_svc(text, svc_key):
            return ""
        g = extract_code(text)
        if g and len(g) not in svc_lens(svc_key):
            lbl = (SVC_BY_KEY.get(str(svc_key or "")) or ("Ye app",))[0]
            return (f"is SMS ka code {len(g)} digit ka hai — {lbl} ka OTP "
                    f"{svc_hint(svc_key)} hota hai")
    except Exception:                       # noqa: BLE001
        pass
    return ""


def msg_fp(m) -> str:
    """Message ki chhoti fingerprint (purane vs naye pehchanne ke liye)."""
    base = "|".join((str((m or {}).get("from") or "")[:24],
                     str((m or {}).get("code") or ""),
                     str((m or {}).get("text") or "")[:80]))
    return hashlib.md5(base.encode("utf-8", "ignore")).hexdigest()[:12]


def snapshot(msgs, cap: int = 60):
    """Abhi ka inbox — 'baseline'. Sirf iske BAAD ke SMS 'naye' maane jayenge."""
    try:
        return [msg_fp(m) for m in (msgs or [])][:cap]
    except Exception:                       # noqa: BLE001
        return []


def fresh_and_matched(msgs, since, svc_key: str, limit: int = 8):
    """(dikhane wale naye matched messages, chhupe hue naye, total naye)."""
    try:
        since_set = set(since or ())
        fresh = [m for m in (msgs or []) if msg_fp(m) not in since_set]
        fresh = sorted(fresh, key=lambda m: str((m or {}).get("time") or ""))
        matched = [m for m in fresh if service_match(m, svc_key)]
        hidden = len(fresh) - len(matched)
        return matched[:limit], hidden, len(fresh)
    except Exception:                       # noqa: BLE001
        return [], 0, 0


def recency_min(txt) -> float:
    """'17 minutes ago' → 17.0 (chhota = naya). Pata na chale to bada number."""
    try:
        s = str(txt or "").lower()
        if not s:
            return 10 ** 6
        # bada unit pehle dekho — "2 minutes 5 seconds ago" = 2 min (5 sec nahi)
        if "hour" in s:
            m = re.search(r"(\d+)", s)
            return float(m.group(1)) * 60 if m else 60.0
        if "minute" in s:
            m = re.search(r"(\d+)", s)
            return float(m.group(1)) if m else 2.0
        if "day" in s:
            m = re.search(r"(\d+)", s)
            return float(m.group(1)) * 1440 if m else 1440.0
        if "week" in s:
            return 7 * 1440.0
        if "just now" in s:
            return 0.5
        if "second" in s:
            m = re.search(r"(\d+)", s)
            return (int(m.group(1)) / 60.0) if m else 0.5
    except Exception:                       # noqa: BLE001
        pass
    return 10 ** 6


def inbox_score(ib, svc_key: str = "") -> float:
    """Number kitna 'active + isi service ka' hai (assignment ke waqt scoring)."""
    try:
        msgs = (ib or {}).get("messages") or []
        sc = 0.0
        for m in msgs:
            rec = recency_min((m or {}).get("time"))
            if service_match(m, svc_key):
                sc += 3.0 if rec <= 180 else 1.0
            if rec <= 10:
                sc += 0.5
        la = recency_min((ib or {}).get("last_activity"))
        if la <= 15:
            sc += 1.0
        return sc
    except Exception:                       # noqa: BLE001
        return 0.0


SRC_PRIO = ("rc", "rsf", "ts")      # v71.10: sabse saaf source pehle (rc > rsf > ts)


def _rotate(lst, uid: int):
    """uid ke hisaab se list ghumao (sab users ek hi number par na tike)."""
    if not lst:
        return []
    i = int(uid or 0) % len(lst)
    return list(lst[i:]) + list(lst[:i])


def pick(numbers, taken=None, uid: int = 0, avoid=None, order=None):
    """Alag-alag users ko alag number — deterministic + 'taken' set respect.

    v71.10: pehle SAAF source (receivesms.co → receive-sms-free.cc → temp-sms)
    se chuno — temp-sms wale numbers me watermark/spam zyada aata tha.
    """
    try:
        cand = list(numbers or [])
        if not cand:
            return None
        taken = set(taken or ())
        avoid = set(avoid or ())
        order = tuple(order or SRC_PRIO)
        groups = {}
        for n in cand:
            groups.setdefault(str(n.get("src") or "rc"), []).append(n)
        chosen = None
        for src in order:                                   # 1) saaf source band
            g = [n for n in groups.get(src, [])
                 if n.get("nid") not in taken and n.get("nid") not in avoid]
            if g:
                chosen = g
                break
        if chosen is None:                                  # 2) sab taken — avoid chhod do
            for src in order:
                g = [n for n in groups.get(src, []) if n.get("nid") not in avoid]
                if g:
                    chosen = g
                    break
        if chosen is None:                                  # 3) aakhri sahara
            chosen = [n for n in cand if n.get("nid") not in avoid] or cand
        chosen = sorted(chosen, key=lambda n: str(n.get("nid")))
        idx = (int(uid or 0) * 2654435761) % len(chosen)
        return chosen[idx]
    except Exception:                                       # noqa: BLE001
        return None


def pick_best(cc: str, taken=None, uid: int = 0, svc_key: str = "",
              avoid=None, tries: int = 3):
    """v71.10: sabse ACCHA number chuno — jo abhi active ho aur usi app ke
    SMS aa rahe hon. Top 3 candidates ka inbox dekh kar score karte hain.

    Return: (number_dict | None, inbox_dict | {}, error-str)
    """
    try:
        p = pool(cc)
        if not p.get("ok"):
            return None, {}, (p.get("error") or "Is desh me number nahi mila.")
        nums = p.get("numbers") or []
        taken = set(taken or ())
        avoid = set(avoid or ())
        ordered = []
        for src in SRC_PRIO:
            g = [n for n in nums if str(n.get("src") or "rc") == src
                 and n.get("nid") not in taken and n.get("nid") not in avoid]
            ordered += _rotate(sorted(g, key=lambda n: str(n.get("nid"))), uid)
        if not ordered:
            ordered = _rotate(sorted([n for n in nums if n.get("nid") not in avoid],
                                     key=lambda n: str(n.get("nid"))), uid) or nums
        best, best_sc, first = None, -1.0, None
        for n in ordered[:max(1, int(tries))]:
            ib = inbox(n.get("nid"), force=True)
            if not ib.get("ok"):
                continue
            if first is None:
                first = (n, ib)
            sc = inbox_score(ib, svc_key)
            if sc > best_sc:
                best, best_sc = (n, ib), sc
            if sc >= 4.0:                                   # kaafi accha — aur fetch mat karo
                break
        if best is None:
            if first is None:
                return None, {}, "Number mila par inbox nahi khula — dobara try karo."
            best = first
        return best[0], best[1], ""
    except Exception as e:                                  # noqa: BLE001
        return None, {}, f"Technical dikkat ({type(e).__name__})."


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
