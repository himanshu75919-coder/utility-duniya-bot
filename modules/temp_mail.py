# -*- coding: utf-8 -*-
"""
Temp Mail — v53.0 (PRO UPGRADE)
===============================
📧 Disposable email + inbox + **OTP auto-extraction** (mail.tm free public API).

v52.3 me kya kamzor tha:
  • `tm_create()` / `tm_messages()` kaam karte the ✅ (live test pass),
    par **OTP nikalne ka koi tarika nahi tha** — aur temp mail log **OTP ke liye hi**
    lete hain. User ko 1200-char ka poora email body dump milta tha (branding,
    footer, unsubscribe links ke beech), aur 6-digit code khud dhoondhna padta tha.
  • Koi auto-refresh nahi — user ko baar-baar `INBOX` type karna padta tha.
  • Naye/purane messages ka pata nahi chalta tha.
  • Attachments dikhti hi nahi thin.
  • Delete ka option nahi tha (mailbox hamesha bana rehta tha).
  • Raw `requests` — core.net ke pool/retry se bahar.

v53.0:
  • **`tm_otp_codes()`** — smart OTP/verification-code extractor:
      - context-aware (OTP / verification code / PIN / one-time / confirm)
      - false-positive filters (saal, phone number, pincode, amount, order id,
        "valid for 5 minutes" wala 5, dates)
      - ranked output with label + source (subject ya body)
  • **`tm_poll()`** — auto-refresh: kitne NAYE messages aaye, aur OTP mile to wo.
  • **Attachments** list (filename + size + download link).
  • **`tm_delete()`** — mailbox band karo.
  • **Body cleanup** — signature/unsubscribe/legal footer strip + plain-text fallback.
  • Saare calls `core.net` se (pooled + timeout + retry).

Privacy: password bot khud generate karta hai aur sirf `context.user_data` me rakhta
hai — user ko kabhi dikhta nahi. Address sirf isi chat me valid.
"""
from __future__ import annotations

import logging
import os
import re
import secrets
import string
import time
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from modules.core.net import NetError, http_get_json, http_post_json, http_post, http_get
from modules.core.telemetry import tracked as _tracked

log = logging.getLogger("ud.tempmail")

__all__ = [
    "tm_create", "tm_messages", "tm_delete", "tm_otp_codes", "tm_poll",
    "tm_domains", "extract_codes", "clean_body", "is_expired",
]

API = os.environ.get("MAILTM_API", "https://api.mail.tm").rstrip("/")
_TIMEOUT = float(os.environ.get("MAILTM_TIMEOUT", "18"))
_UA = os.environ.get("MAILTM_UA", "UtilityDuniyaBot/5.3 (temp mail helper)")
_H = {"User-Agent": _UA, "Accept": "application/json"}
_MAX_BODY = int(os.environ.get("MAILTM_BODY_CHARS", "1600"))
_TTL = 30 * 24 * 3600


def _auth(token: str) -> Dict[str, str]:
    return {**_H, "Authorization": f"Bearer {token}"}


# ============================================================ domains / create
def _hydra_items(payload: Any) -> List[dict]:
    """mail.tm ka jawab nikaalo — teeno shapes handle karta hai.

    ⚠️ Live audit (2026-10-05): `/domains` ab seedha **list** return karta hai,
    par `/messages` abhi bhi hydra-wrapped dict (`hydra:member`) deta hai.
    v52.3 ka code sirf hydra shape jaanta tha → `/domains` par AttributeError
    se crash hota tha. Ye helper teeno shapes sambhalta hai:
      1. `{"hydra:member": [...]}`   (API Platform / hydra)
      2. `[...]`                      (plain list)
      3. `{"data": [...]}` / `{"results": [...]}` / `{"domains": [...]}`
    """
    if payload is None:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("hydra:member", "member", "data", "results", "domains", "items"):
            v = payload.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
            if isinstance(v, dict):
                # nested hydra
                inner = v.get("hydra:member") or v.get("items")
                if isinstance(inner, list):
                    return [x for x in inner if isinstance(x, dict)]
        # single object
        return [payload]
    return []


def _hydra_total(payload: Any, fallback: int) -> int:
    if isinstance(payload, dict):
        for key in ("hydra:totalItems", "totalItems", "total", "count"):
            v = payload.get(key)
            if isinstance(v, int):
                return v
            try:
                if v is not None:
                    return int(v)
            except (TypeError, ValueError):
                continue
    return fallback


def tm_domains() -> List[str]:
    """Available email domains (mail.tm kabhi-kabhi domain badalta hai)."""
    try:
        d = http_get_json(f"{API}/domains", headers=_H, timeout=_TIMEOUT, retries=1)
    except Exception as e:                                          # noqa: BLE001
        log.debug("tm_domains fail: %s", str(e)[:80])
        return []
    out: List[str] = []
    for m in _hydra_items(d):
        dom = m.get("domain") or m.get("name")
        if not dom:
            continue
        # isActive explicitly False ho to skip (warna maan lo active hai)
        if m.get("isActive") is False:
            continue
        if m.get("isPrivate") is True:
            continue
        out.append(str(dom))
    # dedupe, order preserve
    seen, uniq = set(), []
    for d_ in out:
        if d_ not in seen:
            seen.add(d_)
            uniq.append(d_)
    return uniq


def _rand_local() -> str:
    """Readable par unique local-part. Ambiguous chars (0/O, 1/l) avoid."""
    abc = "abcdefghijkmnpqrstuvwxyz23456789"
    return "ud" + "".join(secrets.choice(abc) for _ in range(11))


@_tracked("tempmail.create")
def tm_create(preferred_domain: str = "") -> Dict[str, Any]:
    """Naya disposable email banao.

    Returns {"ok":True,"address","password","token","domain","expires_in"}
    Password **jaan-boojh kar** result me hai — bot ise `user_data` me rakhta hai
    taaki session expire hone par dobara login kar sake (user ko kabhi nahi dikhata).
    """
    domains = tm_domains()
    if not domains:
        return {"ok": False,
                "error": ("⏳ Mail service abhi koi domain nahi de payi.\n"
                          "Ye free service hai — 2-3 minute baad dobara <code>NEW</code> bhejo.")}
    domain = preferred_domain if preferred_domain in domains else domains[0]

    # 3 addresses try karo — kabhi-kabhi ek already taken hota hai (422)
    last_err = ""
    for attempt in range(3):
        address = f"{_rand_local()}@{domain}"
        password = "ud" + secrets.token_hex(10)
        try:
            acc = http_post_json(f"{API}/accounts",
                                 json={"address": address, "password": password},
                                 headers=_H, timeout=_TIMEOUT, retries=1)
        except NetError as e:
            last_err = e.message
            if e.status in (422, 429):
                continue
            return {"ok": False,
                    "error": f"Email banane me problem ({str(e.message)[:70]}). Dobara try karo."}
        except Exception as e:                                      # noqa: BLE001
            last_err = str(e)[:70]
            continue

        try:
            tok = http_post_json(f"{API}/token",
                                 json={"address": address, "password": password},
                                 headers=_H, timeout=_TIMEOUT, retries=1)
        except Exception as e:                                      # noqa: BLE001
            last_err = f"token: {str(e)[:50]}"
            continue
        token = (tok or {}).get("token")
        if not token:
            last_err = "token nahi mila"
            continue
        return {"ok": True, "address": address, "password": password, "token": token,
                "domain": domain, "account_id": (acc or {}).get("id", ""),
                "expires_in": (tok or {}).get("expires_in", _TTL),
                "created_at": time.time()}
    return {"ok": False, "error": f"Email banane me problem ({last_err[:70]}). Dobara try karo."}


def tm_delete(address: str, token: str) -> Dict[str, Any]:
    """Mailbox band karo (account delete). Best-effort."""
    if not token:
        return {"ok": False, "error": "Session nahi hai."}
    try:
        # delete ke liye account id chahiye — /me se le lo
        me = http_get_json(f"{API}/me", headers=_auth(token), timeout=_TIMEOUT, retries=0)
        aid = (me or {}).get("id")
        if not aid:
            return {"ok": False, "error": "Account ID nahi mili."}
        r = http_post(f"{API}/accounts/{aid}", headers=_auth(token), timeout=_TIMEOUT, retries=0)
        return {"ok": True}
    except Exception:                                               # noqa: BLE001
        return {"ok": False, "error": "Delete nahi ho paya (session khud expire ho jayega)."}


def is_expired(error_text: str = "") -> bool:
    """401 = session gaya."""
    t = str(error_text or "").lower()
    return "401" in t or "expire" in t or "unauthorized" in t or "jwt" in t


# ============================================================ OTP extraction
# Context words jo bataate hain ki ye number ek code hai
_CODE_CTX = re.compile(
    r"(?i)(otp|one[\s\-]?time|verification|verify|confirm(?:ation)?|security|"
    r"auth(?:entication)?|activation|sign[\s\-]?in|log[\s\-]?in|pin|passcode|"
    r"code|token|credential|2fa|mfa|magic[\s\-]?link|reset)")

# Number jo code NAHI hote (false positives)
_BAD_NUM = re.compile(
    r"(?i)(\b(?:19|20)\d{2}\b"                      # saal
    r"|\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"         # date
    r"|\b\d{5,6}\s*(?:rs|₹|inr|usd|\$|€)\b"          # amount
    r"|\b(?:rs|₹|inr|usd|\$|€)\s*\d{3,}\b"
    r"|\b\d{10,13}\b"                                # phone / order id
    r"|\b\d{1,2}:\d{2}\b"                            # time
    r"|\b\d+\s*(?:minute|minutes|min|hour|hours|hr|day|days|second|seconds|"
    r"month|months|year|years|times?|attempts?|tries|users?|%\s)\b)")

# Explicit "OTP: 123456" / "code is 123456" / "123456 is your code"
_EXPLICIT = re.compile(
    r"(?i)(?:(?:your|the|is|:)?\s*)"
    r"(?:otp|one[\s\-]?time\s*(?:password|passcode|code)?|verification\s*code|"
    r"confirm(?:ation)?\s*code|security\s*code|auth(?:entication)?\s*code|"
    r"activation\s*code|access\s*code|login\s*code|sign[\s\-]?in\s*code|"
    r"passcode|pin(?:\s*code)?|code)"
    r"(?:\s*(?:is|:|=|of|-|–|\|))?\s*"
    r"\**\s*(\d{4,10})\s*\**")

_EXPLICIT_REV = re.compile(
    r"(?i)(\d{4,10})\s*(?:is\s+)?(?:your|the)\s+"
    r"(?:otp|one[\s\-]?time\s*(?:password|passcode|code)?|verification\s*code|"
    r"confirm(?:ation)?\s*code|security\s*code|auth(?:entication)?\s*code|"
    r"activation\s*code|access\s*code|login\s*code|passcode|pin(?:\s*code)?|code)")

# HTML me code aksar ek alag <td>/<span>/<strong>/<b> me hota hai, bade font ke saath
_HTML_CODE_BLOCK = re.compile(
    r"(?i)<(?:td|span|div|strong|b|p|h\d)[^>]*"
    r"(?:font-size\s*:\s*(?:2\d|3\d|4\d)px|letter-spacing|text-align\s*:\s*center)[^>]*>\s*"
    r"(?:<[^>]+>\s*)*(\d{4,10})(?:\s*<[^>]+>)*\s*</(?:td|span|div|strong|b|p|h\d)>")

_BARE_CODE_LINE = re.compile(r"^\s*\**\s*(\d{4,10})\s*\**\s*$")


def extract_codes(subject: str = "", body_html: str = "", body_text: str = "") -> List[Dict[str, Any]]:
    """Email se OTP / verification codes nikalo (ranked).

    Returns [{"code","label","confidence","source"}] — sabse likely pehle.
    """
    subj = str(subject or "")
    html = str(body_html or "")
    text = str(body_text or "")
    found: List[Dict[str, Any]] = []
    seen = set()

    def _add(code: str, label: str, conf: float, source: str):
        c = re.sub(r"\D", "", code)
        if not (4 <= len(c) <= 10) or c in seen:
            return
        # obvious junk filter
        if len(set(c)) == 1 and len(c) > 6:      # 0000000
            return
        if re.fullmatch(r"(?:123|234|345|456|567|678|789|890|012)+", c) and len(c) > 6:
            return
        if _BAD_NUM.search(c):
            return
        seen.add(c)
        found.append({"code": c, "label": label, "confidence": round(conf, 2),
                      "source": source})

    # 1) HTML styled code block — sabse reliable (designers code ko alag dikhate hain)
    if html:
        for m in _HTML_CODE_BLOCK.findall(html):
            _add(m, "HTML code block", 0.97, "html")

    # 2) Explicit patterns in subject (highest — subject me code matlab wahi chahiye)
    for rx, src in ((_EXPLICIT, "subject"), (_EXPLICIT_REV, "subject")):
        for m in rx.findall(subj):
            _add(m, "Subject me explicit", 0.95, "subject")

    # 3) Explicit patterns in text body
    for rx in (_EXPLICIT, _EXPLICIT_REV):
        for m in rx.findall(text):
            _add(m, "Body me explicit", 0.93, "body")

    # 4) Explicit patterns in raw HTML (text extract miss kar deta hai)
    if html:
        plain = re.sub(r"<[^>]+>", " ", html)
        plain = re.sub(r"\s+", " ", plain)
        for rx in (_EXPLICIT, _EXPLICIT_REV):
            for m in rx.findall(plain):
                _add(m, "HTML me explicit", 0.90, "html")

    # 5) Standalone code line (poora paragraph sirf number)
    for line in text.split("\n"):
        m = _BARE_CODE_LINE.match(line)
        if m:
            _add(m.group(1), "Alag line par code", 0.88, "body")

    # 6) Context-based fallback: koi bhi 4-8 digit number jiske aas-paas
    #    "otp/code/verify" jaisa word ho (±40 chars window)
    if not found:
        for m in re.finditer(r"\b(\d{4,8})\b", text):
            s, e = m.span()
            window = text[max(0, s - 45):min(len(text), e + 45)]
            if _CODE_CTX.search(window) and not _BAD_NUM.search(window):
                _add(m.group(1), "Context se (aas-paas 'code/OTP')", 0.72, "body")

    found.sort(key=lambda x: (-x["confidence"], len(x["code"]) != 6, -len(x["code"])))
    return found[:6]


# ============================================================ body cleanup
_FOOTER_PAT = re.compile(
    r"(?i)(unsubscribe|manage (?:your )?(?:preferences|subscription)|"
    r"privacy policy|terms of (?:service|use)|all rights reserved|"
    r"copyright\s*©?\s*(?:19|20)\d{2}|this (?:is an|e-??mail was) "
    r"automatically generated|please do not reply|"
    r"you are receiving this|if you (?:did not|didn'?t) (?:request|sign)|"
    r"ignore this (?:e-?mail|message)|follow us on|"
    r"©\s*(?:19|20)\d{2}|view (?:this|in) (?:e-?mail|browser)|"
    r"add .* to your (?:contacts|address book)|"
    r"sent by|powered by|get the app|download the app)", re.I)


def clean_body(html: str = "", text: str = "", limit: int = _MAX_BODY) -> str:
    """Email body ko padhne-laayak banao: HTML strip + footer hatao.

    OTP ke liye zaroori hissa upar hota hai; footer/legal text hata dete hain
    taaki user ko code dhoondhne me dikkat na ho.
    """
    raw = str(text or "").strip()
    if not raw and html:
        try:
            soup = BeautifulSoup(html, "html.parser")
            for t in soup(["script", "style"]):
                t.decompose()
            raw = soup.get_text("\n")
        except Exception:                                           # noqa: BLE001
            raw = re.sub(r"<[^>]+>", " ", html)
    if not raw:
        return ""
    # entities + whitespace normalise
    raw = (raw.replace("&nbsp;", " ").replace("&amp;", "&")
              .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'")
              .replace("&quot;", '"'))
    lines: List[str] = []
    for ln in raw.split("\n"):
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if not ln:
            continue
        # footer/legal line → yahan se aage usually sab boilerplate
        if _FOOTER_PAT.search(ln) and len(ln.split()) <= 30:
            continue
        lines.append(ln)
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    if len(out) > limit:
        out = out[:limit].rsplit(" ", 1)[0] + " […]"
    return out


# ============================================================ messages
def _norm_msg(it: dict, token: str, fetch_body: bool = True) -> Dict[str, Any]:
    """mail.tm message object → saaf dict (+ full body fetch)."""
    mid = it.get("id") or ""
    frm = it.get("from") or {}
    subject = str(it.get("subject") or "(no subject)")
    intro = str(it.get("intro") or "")
    atts = []
    for a in (it.get("attachments") or []):
        if isinstance(a, dict):
            atts.append({"name": str(a.get("filename") or "file"),
                         "size": int(a.get("size") or 0),
                         "type": str(a.get("contentType") or "")})

    msg = {
        "id": mid,
        "subject": subject[:150],
        "from": str(frm.get("address") or "?") if isinstance(frm, dict) else str(frm),
        "from_name": (str(frm.get("name") or "").strip()
                      if isinstance(frm, dict) else "")[:60],
        "to": [str(t.get("address")) for t in (it.get("to") or []) if isinstance(t, dict)],
        "at": str(it.get("createdAt") or ""),
        "seen": bool(it.get("seen")),
        "intro": intro[:300],
        "attachments": atts,
        "has_attachments": bool(atts),
        "body": "",
        "codes": [],
    }
    if not fetch_body:
        # list view: intro se hi codes try karo (sasta)
        msg["codes"] = extract_codes(subject, "", intro)
        msg["body"] = clean_body("", intro, limit=400)
        return msg

    if mid:
        try:
            d = http_get_json(f"{API}/messages/{mid}", headers=_auth(token),
                              timeout=_TIMEOUT, retries=1)
            html = str(d.get("html") or "")
            if isinstance(html, list):                              # kabhi list of parts aata hai
                html = "\n".join(str(x) for x in html)
            txt = "\n".join(str(x) for x in (d.get("text") or [])) if isinstance(d.get("text"), list) \
                else str(d.get("text") or "")
            msg["body"] = clean_body(html, txt) or clean_body("", intro)
            msg["codes"] = extract_codes(subject, html, msg["body"] or txt or intro)
            msg["body_html_len"] = len(html)
        except NetError as e:
            if not is_expired(e.message):
                msg["body"] = clean_body("", intro)
                msg["codes"] = extract_codes(subject, "", intro)
                msg["error"] = str(e.message)[:80]
            else:
                raise
        except Exception as e:                                      # noqa: BLE001
            msg["body"] = clean_body("", intro)
            msg["codes"] = extract_codes(subject, "", intro)
            msg["error"] = str(e)[:80]
    return msg


@_tracked("tempmail.inbox")
def tm_messages(address: str, token: str, limit: int = 10,
                fetch_bodies: bool = True) -> Dict[str, Any]:
    """Inbox ke messages (+ har message ke OTP codes).

    Returns {"ok":True,"count","messages":[...],"codes":[...],"expired":bool}
    """
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(address or "")):
        return {"ok": False, "error": "Email address galat format me hai."}
    if not token:
        return {"ok": False, "expired": True,
                "error": "Session nahi hai — <b>NEW</b> bhejo, naya email ban jayega."}
    try:
        d = http_get_json(f"{API}/messages", headers=_auth(token),
                          timeout=_TIMEOUT, retries=1)
    except NetError as e:
        if e.status == 401 or is_expired(e.message):
            return {"ok": False, "expired": True,
                    "error": ("Ye temp email session expire ho gaya hai.\n"
                              "📧 <b>NEW</b> bhejo — naya address ban jayega.")}
        return {"ok": False, "error": f"Inbox open nahi hua ({str(e.message)[:70]})."}
    except Exception as e:                                          # noqa: BLE001
        return {"ok": False, "error": f"Inbox se connect nahi ho paya ({str(e)[:60]})."}

    items = _hydra_items(d)
    total = _hydra_total(d, len(items))
    out: List[Dict[str, Any]] = []
    all_codes: List[Dict[str, Any]] = []

    # Naye (unseen) messages pehle — OTP wahi hote hain
    try:
        items = sorted(items, key=lambda x: (bool(x.get("seen")),
                                             str(x.get("createdAt") or "")),
                       reverse=False)
        items = sorted(items, key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    except Exception:                                               # noqa: BLE001
        pass

    for i, it in enumerate(items[:limit]):
        if not isinstance(it, dict):
            continue
        try:
            m = _norm_msg(it, token, fetch_body=(fetch_bodies and i < 5))
        except NetError as e:
            if e.status == 401:
                return {"ok": False, "expired": True,
                        "error": "Session expire ho gaya — <b>NEW</b> bhejo."}
            m = _norm_msg(it, token, fetch_body=False)
        except Exception:                                           # noqa: BLE001
            m = _norm_msg(it, token, fetch_body=False)
        out.append(m)
        for c in m.get("codes") or []:
            all_codes.append({**c, "subject": m["subject"], "from": m["from"]})

    return {"ok": True, "address": address, "count": int(total),
            "fetched": len(out), "messages": out,
            "codes": all_codes[:8], "top_code": (all_codes[0]["code"] if all_codes else ""),
            "checked_at": time.time()}


@_tracked("tempmail.poll")
def tm_poll(address: str, token: str, seen_ids: Optional[List[str]] = None,
            limit: int = 5) -> Dict[str, Any]:
    """Auto-refresh: inbox check karo aur NAYE messages + OTP highlight karo.

    Args:
      seen_ids: pehle dekh chuke message IDs (bot user_data se bhejta hai)

    Returns tm_messages() ka result + {"new_count","new_messages","new_codes"}
    """
    res = tm_messages(address, token, limit=limit)
    if not res.get("ok"):
        return res
    seen = set(seen_ids or [])
    new_msgs = [m for m in res["messages"] if m["id"] and m["id"] not in seen]
    new_codes: List[Dict[str, Any]] = []
    for m in new_msgs:
        for c in (m.get("codes") or []):
            new_codes.append({**c, "subject": m["subject"], "from": m["from"]})
    if not new_codes and new_msgs:
        # naya message aaya par code nahi mila — intro se ek baar aur try
        for m in new_msgs:
            new_codes.extend(extract_codes(m["subject"], "", m.get("intro") or m.get("body") or ""))
    res["new_count"] = len(new_msgs)
    res["new_messages"] = new_msgs
    res["new_codes"] = new_codes[:5]
    res["top_code"] = (new_codes[0]["code"] if new_codes else res.get("top_code", ""))
    res["all_ids"] = [m["id"] for m in res["messages"] if m["id"]]
    return res
