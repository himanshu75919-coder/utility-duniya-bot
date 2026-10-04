# -*- coding: utf-8 -*-
"""
Pinterest Downloader — v52.3
============================
📌 Pinterest image HD download:
  • Direct PIN link bhejo → original quality image download
  • Keyword bhejo → public image search (Pinterest images priority) → 6 options → tap karke download

Sirf PUBLIC Pinterest images. i.pinimg.com (Pinterest ka official CDN) se
direct download — koi API key nahi chahiye.
"""

import re
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
PINIMG_RE = re.compile(
    r"https://i\.pinimg\.com/(?:originals|[0-9]+x)/([a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{32}\.[a-z]+)")
_SIZE_RANK = {"originals": 5, "736": 4, "564x": 3, "474x": 2, "236x": 1}


def _original_url(path: str) -> str:
    return f"https://i.pinimg.com/originals/{path}"


def _pick_best(urls: list) -> str:
    """Sabse badi size wali URL chuno."""
    def rank(u):
        m = re.search(r"i\.pinimg\.com/([^/]+)/", u)
        size = m.group(1) if m else ""
        return _SIZE_RANK.get(size, 0)
    return sorted(urls, key=rank, reverse=True)[0]


def pinterest_from_pin_link(target: str) -> dict:
    """Pinterest PIN link se original image nikalo."""
    t = (target or "").strip()
    m = re.search(r"pinterest\.[a-z.]+/pin/(\d+)", t)
    if m:
        pin_id = m.group(1)
    elif re.fullmatch(r"\d{9,}", t):
        pin_id = t
    else:
        m2 = re.search(r"/(\d{9,})", t)
        pin_id = m2.group(1) if m2 else None
    if not pin_id:
        return {"ok": False,
                "error": ("Ye Pinterest PIN link nahi lagta.\n"
                          "📌 Pinterest app me pin par ⋯ → <b>Copy link</b> → yahan paste karo.\n"
                          "Jaise: <code>https://pin.it/xxxxx</code> ya "
                          "<code>pinterest.com/pin/1234567890/</code>")}
    try:
        r = requests.get(f"https://www.pinterest.com/pin/{pin_id}/",
                         headers=UA, timeout=20,
                         cookies={"pinOverlayDismissed": "true"})
        if r.status_code == 404:
            return {"ok": False,
                    "error": ("Ye pin nahi mila — ho sakta hai deleted ho ya "
                              "private ho. Doosra pin link bhejo.")}
        paths = set(PINIMG_RE.findall(r.text))
        # og:image fallback
        og = re.findall(r'og:image"\s+content="([^"]+)"', r.text)
        urls = [_original_url(p) for p in paths] + og
        if not urls:
            return {"ok": False,
                    "error": ("Pin mila par image data nahi nikal paaya (kabhi-kabhi "
                              "Pinterest datacenter IP par kam deta hai). Dobara try karo.")}
        best = _pick_best(urls)
        d = requests.get(best, headers=UA, timeout=30)
        if d.status_code != 200 or len(d.content) < 2000:
            # ek aur try karo
            for u in urls[:4]:
                if u == best:
                    continue
                d2 = requests.get(u, headers=UA, timeout=30)
                if d2.status_code == 200 and len(d2.content) > 2000:
                    d = d2
                    break
        if d.status_code != 200 or len(d.content) < 2000:
            return {"ok": False,
                    "error": "Image download fail ho gayi. Link ka sahi hona check karo / dobara try karo."}
        ct = d.headers.get("content-type", "")
        ext = ".jpg" if "jpeg" in ct or "jpg" in ct else (".png" if "png" in ct else ".webp")
        return {"ok": True, "bytes": d.content, "ext": ext,
                "note": "Pinterest se public image (original quality)"}
    except requests.Timeout:
        return {"ok": False, "error": "Pinterest server slow hai abhi. 1 minute baad try karo."}
    except Exception:
        return {"ok": False, "error": "Pinterest se connect nahi ho paya. Thodi der baad try karo."}


def pinterest_search(keyword: str) -> dict:
    """Keyword se public image search (Pinterest images priority).
    6 best options wapas deta hai — user tap karega to wo download hoga."""
    kw = (keyword or "").strip()
    if not kw or len(kw) < 2:
        return {"ok": False, "error": "Koi keyword bhejo — jaise <code>cat wallpaper</code>, <code>logo design</code>"}
    results, seen = [], set()
    for q in [f"{kw} pinterest", f"{kw} site:pinterest.com", kw]:
        try:
            r = requests.get("https://www.bing.com/images/search",
                             params={"q": q, "form": "HDRSC2"}, headers=UA, timeout=20)
            murls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?)&quot;', r.text)
            for u in murls:
                u = u.strip()
                # pinimg URLs ko original size pe upgrade karo
                m = PINIMG_RE.search(u)
                if m:
                    u = _original_url(m.group(1))
                if u not in seen:
                    seen.add(u)
                    results.append(u)
            if len(results) >= 6:
                break
        except Exception:
            continue
    if not results:
        return {"ok": False,
                "error": (f"'{kw}' ke liye koi public image nahi mili. Doosra keyword try karo, "
                          "ya seedha kisi pin ka link bhejo.")}
    # Pinterest (pinimg) wale results upar lao
    results.sort(key=lambda u: 0 if "pinimg.com" in u else 1)
    top = results[:6]
    return {"ok": True, "results": top, "is_pinterest": ["pinimg.com" in u for u in top]}
