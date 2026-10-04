# -*- coding: utf-8 -*-
"""
Web Scraper — v52.3
===================
📄 Kisi bhi PUBLIC page ka clean text extract (title + description + main text).
SSRF-protected (core.net se) — private/internal IPs kabhi nahi khole jayenge.
"""

import re
import requests
from bs4 import BeautifulSoup

from modules.core.net import is_safe_url, NetError

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
MAX_BYTES = 2_500_000   # 2.5 MB page cap


def _clean_ws(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def scrape_public_text(target: str) -> dict:
    """Public URL ka readable text nikalo (SSRF-guarded)."""
    url = (target or "").strip()
    if not re.match(r"^https?://", url):
        url = "https://" + url
    ok, why = is_safe_url(url)
    if not ok:
        return {"ok": False, "error": f"Ye URL safe nahi hai — {why or 'block ho gaya'}"}
    try:
        r = requests.get(url, headers=UA, timeout=15, stream=True,
                         allow_redirects=True)
        if r.status_code != 200:
            return {"ok": False, "error": f"Page ne {r.status_code} diya (nahi mila / access nahi hai)."}
        ctype = r.headers.get("content-type", "")
        if "html" not in ctype and "text" not in ctype:
            return {"ok": False,
                    "error": "Ye HTML text page nahi hai (image/PDF/file ho sakta hai). Koi article/blog page ka link bhejo."}
        chunks, total = [], 0
        for ch in r.iter_content(65536):
            total += len(ch)
            if total > MAX_BYTES:
                break
            chunks.append(ch)
        html = b"".join(chunks).decode("utf-8", errors="ignore")
    except requests.Timeout:
        return {"ok": False, "error": "Page slow hai — time limit ke andar nahi khula. 1 minute baad try karo."}
    except NetError as e:
        return {"ok": False, "error": str(e)[:120]}
    except Exception:
        return {"ok": False, "error": "Page open nahi ho paya. URL check karke dobara bhejo."}

    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside", "form", "iframe"]):
        t.decompose()
    title = (soup.title.get_text(strip=True) if soup.title else "") or "—"
    desc = ""
    md = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if md and md.get("content"):
        desc = md["content"].strip()[:200]
    main = soup.find("article") or soup.find("main") or soup.find("body") or soup
    text = _clean_ws(main.get_text("\n"))
    if len(text) < 80:
        return {"ok": False,
                "error": ("Page mila par readable text nahi nikla (ya to JS-based page hai "
                          "ya content bahut kam hai). Doosra page try karo.")}
    return {"ok": True, "url": url, "title": title[:150], "desc": desc,
            "text": text, "words": len(text.split())}
