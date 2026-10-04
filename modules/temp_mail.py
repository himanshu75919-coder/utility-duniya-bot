# -*- coding: utf-8 -*-
"""
Temp Mail — v52.3
=================
📧 Disposable email + inbox (mail.tm ka free public API — koi API key nahi).
Password bot hi generate karta hai aur user_data me rakhta hai — user ko
sirf email address dikhta hai.
"""

import re
import secrets
import string
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "UtilityDuniyaBot/5.2 (temp mail helper)"}
API = "https://api.mail.tm"
TTL = 30 * 24 * 3600   # 30 din ke liye valid session


def _rand_local() -> str:
    abc = string.ascii_lowercase + string.digits
    return "ud" + "".join(secrets.choice(abc) for _ in range(12))


def tm_create() -> dict:
    """Naya disposable email banao. {address, token, domain} wapas."""
    try:
        d = requests.get(f"{API}/domains", headers=UA, timeout=15).json()
        members = d.get("hydra:member") or []
        if not members:
            return {"ok": False, "error": "Mail service abhi koi domain nahi de payi. Baad me try karo."}
        domain = members[0].get("domain")
        address = f"{_rand_local()}@{domain}"
        password = "ud" + secrets.token_hex(9)
        r = requests.post(f"{API}/accounts",
                          json={"address": address, "password": password},
                          headers=UA, timeout=15)
        if r.status_code not in (200, 201):
            return {"ok": False, "error": f"Email banane me problem (code {r.status_code}). Dobara try karo."}
        acc = r.json()
        r2 = requests.post(f"{API}/token",
                           json={"address": address, "password": password},
                           headers=UA, timeout=15)
        if r2.status_code != 200:
            return {"ok": False, "error": "Session token nahi mila. Dobara try karo."}
        token = r2.json().get("token")
        return {"ok": True, "address": address, "token": token, "domain": domain,
                "expires_in": r2.json().get("expires_in", TTL)}
    except requests.Timeout:
        return {"ok": False, "error": "Mail service slow hai abhi. 1 minute baad try karo."}
    except Exception:
        return {"ok": False, "error": "Mail service se connect nahi ho paya. Thodi der baad try karo."}


def tm_messages(address: str, token: str) -> dict:
    """Inbox ke messages lao (subject + body text)."""
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", address or ""):
        return {"ok": False, "error": "Email address galat format me hai."}
    try:
        r = requests.get(f"{API}/messages", headers={**UA, "Authorization": f"Bearer {token}"},
                         timeout=15)
        if r.status_code == 401:
            return {"ok": False, "expired": True,
                    "error": "Ye temp email session expire ho gaya hai — naya banana padega."}
        if r.status_code != 200:
            return {"ok": False, "error": f"Inbox open nahi hua (code {r.status_code})."}
        items = (r.json() or {}).get("hydra:member") or []
        out = []
        for it in items[:10]:
            mid = it.get("id")
            subj = it.get("subject") or "(no subject)"
            frm = (it.get("from") or {}).get("address", "?")
            body = ""
            try:
                rd = requests.get(f"{API}/messages/{mid}",
                                  headers={**UA, "Authorization": f"Bearer {token}"},
                                  timeout=15).json()
                html = rd.get("text", "") or ""
                soup = BeautifulSoup(html, "html.parser")
                body = re.sub(r"\n{3,}", "\n\n", soup.get_text(" ") or html)
            except Exception:
                body = "(message body nahi nikli)"
            out.append({"subject": subj[:120], "from": frm, "body": body[:1200]})
        return {"ok": True, "count": len(items), "messages": out}
    except requests.Timeout:
        return {"ok": False, "error": "Mail service slow hai. Dobara try karo."}
    except Exception:
        return {"ok": False, "error": "Inbox se connect nahi ho paya."}
