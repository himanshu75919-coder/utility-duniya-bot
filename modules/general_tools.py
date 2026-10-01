# -*- coding: utf-8 -*-
"""
General Utility Tools
QR code, Image-to-PDF, URL Shortener, EMI & Interest, Age, Password, Multi-Source Web Search Engine, and 6-Store App Finder.
"""

import io
import math
from concurrent.futures import ThreadPoolExecutor
import random
import re
import string
from datetime import date, datetime
from html import escape as hesc
from urllib.parse import quote, unquote
import qrcode
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance
import img2pdf

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def make_qr_bytes(text: str, box_size: int = 18, fill: str = "black", back: str = "white") -> io.BytesIO:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill, back_color=back).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def wifi_qr_data(ssid: str, password: str = "", security: str = "WPA") -> str:
    """WiFi par scan karte hi connect ho jaye — aisa QR banane ka data."""
    sec = security if password else "nopass"
    return f"WIFI:T:{sec};S:{ssid};P:{password};;"


def vcard_data(name: str, phone: str, org: str = "", email: str = "") -> str:
    """Contact card (scan karne par phone me contact save ho jata hai)."""
    parts = ["BEGIN:VCARD", "VERSION:3.0", f"N:{name};;;;", f"FN:{name}"]
    if org:
        parts.append(f"ORG:{org}")
    if phone:
        parts.append(f"TEL;TYPE=CELL:{phone}")
    if email:
        parts.append(f"EMAIL:{email}")
    parts.append("END:VCARD")
    return "\n".join(parts)


def gen_password(n: int = 16) -> str:
    n = max(8, min(64, n))
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        pwd = "".join(random.choices(chars, k=n))
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in "!@#$%^&*" for c in pwd)
        ):
            return pwd


PASSPHRASE_WORDS = [
    "tiger", "ganga", "monsoon", "tandoor", "cricket", "himalaya", "chai", "diwali", "auto", "bazaar",
    "kite", "mango", "peacock", "railway", "samosa", "thunder", "village", "yatra", "zenith", "bullet",
]


def gen_passphrase(words: int = 4, sep: str = "-") -> str:
    """Yaad rakhne layak strong passphrase (jaise: Mango-Thunder-87-Chai)."""
    picked = random.sample(PASSPHRASE_WORDS, k=max(3, min(words, 6)))
    picked = [w.capitalize() if i % 2 == 0 else w for i, w in enumerate(picked)]
    picked.insert(random.randint(1, len(picked)), str(random.randint(10, 99)))
    return sep.join(picked)


def gen_pin(length: int = 6) -> str:
    """Random numeric PIN (UPI/ATM style) — pehla digit 0 nahi hota."""
    return str(random.randint(1, 9)) + "".join(random.choice("0123456789") for _ in range(max(3, length) - 1))


def password_strength(pwd: str) -> tuple:
    """(score 0-5, label, suggestions) — password kitna strong hai."""
    score = 0
    if len(pwd) >= 10:
        score += 1
    if len(pwd) >= 14:
        score += 1
    if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd):
        score += 1
    if any(c.isdigit() for c in pwd):
        score += 1
    if any(not c.isalnum() for c in pwd):
        score += 1
    labels = {0: "Bahut Kamzor 🔴", 1: "Kamzor 🔴", 2: "Thoda Kamzor 🟠", 3: "Theek ✅", 4: "Strong 💪", 5: "Bahut Strong 🔥"}
    return score, labels.get(min(score, 5), "Theek"), []


def name_passwords(name: str):
    clean = re.sub(r"[^a-zA-Z]", "", name.title()) or "User"
    year = date.today().year
    syms = ["@", "#", "$", "!", "&"]
    out = []
    for s in syms:
        out.append(f"{clean}{s}{random.randint(100, 999)}")
        out.append(f"{clean}{s}{year}")
    out.append(f"{clean[::-1].title()}@{random.randint(1000, 9999)}")
    return list(dict.fromkeys(out))[:6]


def calc_emi(p: float, annual: float, months: int) -> float:
    if months <= 0:
        return 0.0
    r = annual / (12.0 * 100.0)
    if r == 0:
        return p / months
    emi = p * r * ((1 + r) ** months) / (((1 + r) ** months) - 1)
    return emi


def emi_schedule(p: float, annual: float, n: int):
    emi = calc_emi(p, annual, n)
    r = annual / (12.0 * 100.0)
    bal = p
    rows = []
    for m in range(1, min(n + 1, 13)):
        interest = bal * r
        principal = emi - interest
        bal = max(0.0, bal - principal)
        rows.append((m, emi, principal, interest, bal))
    return emi, rows


def calc_age(dob: date):
    today = date.today()
    if dob > today:
        return None
    years = today.year - dob.year
    months = today.month - dob.month
    days = today.day - dob.day
    if days < 0:
        months -= 1
        prev_month = (today.month - 1) or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days_in_prev = (date(prev_year, prev_month + 1, 1) - date(prev_year, prev_month, 1)).days if prev_month < 12 else 31
        days += days_in_prev
    if months < 0:
        years -= 1
        months += 12
    total_days = (today - dob).days
    next_bday = date(today.year, dob.month, dob.day) if (dob.month, dob.day) >= (today.month, today.day) else date(today.year + 1, dob.month, dob.day)
    days_to_bday = (next_bday - today).days
    return years, months, days, total_days, days_to_bday, next_bday.strftime("%A")


def zodiac(d: int, m: int) -> str:
    cuts = [
        (1, 20, "♑ Makar (Capricorn)"),
        (2, 19, "♒ Kumbh (Aquarius)"),
        (3, 20, "♓ Meen (Pisces)"),
        (4, 20, "♈ Mesh (Aries)"),
        (5, 21, "♉ Vrishabh (Taurus)"),
        (6, 21, "♊ Mithun (Gemini)"),
        (7, 23, "♋ Kark (Cancer)"),
        (8, 23, "♌ Singh (Leo)"),
        (9, 23, "♍ Kanya (Virgo)"),
        (10, 23, "♎ Tula (Libra)"),
        (11, 22, "♏ Vrishchik (Scorpio)"),
        (12, 22, "♐ Dhanu (Sagittarius)"),
        (12, 32, "♑ Makar (Capricorn)"),
    ]
    for mon, day, name in cuts:
        if m == mon and d <= day:
            return name
        if m == mon - 1 and d > cuts[mon - 2][1]:
            return name
    return "✨ Rashi"


def shorten_isgd(url: str):
    try:
        r = requests.get(f"https://is.gd/create.php?format=simple&url={url}", headers=UA, timeout=4)
        if r.status_code == 200 and r.text.startswith("https://is.gd/"):
            return r.text.strip()
    except Exception:
        pass
    return None


def shorten_tiny(url: str):
    try:
        r = requests.get(f"https://tinyurl.com/api-create.php?url={url}", headers=UA, timeout=4)
        if r.status_code == 200 and "tinyurl.com" in r.text:
            return r.text.strip()
    except Exception:
        pass
    return None


def build_upi_link(pa: str, pn: str, amt=None, note: str = "") -> str:
    base = f"upi://pay?pa={pa}&pn={quote(pn)}"
    if amt:
        base += f"&am={amt:.2f}&cu=INR"
    if note:
        base += f"&tn={quote(note)}"
    return base


def pages_to_pdf(pages: list, a4: bool = False, quality: int = 90) -> bytes:
    """Images ko PDF banata hai. a4=True → sab pages A4 size me fit ho jaate hain (print friendly)."""
    processed = []
    for b in pages:
        im = Image.open(io.BytesIO(b)).convert("RGB")
        if a4:
            # A4 ratio par fit karo (white padding ke saath) — print par edges nahi katte
            target_w, target_h = 1654, 2339  # A4 @ 200 DPI
            im.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
            canvas.paste(im, ((target_w - im.width) // 2, (target_h - im.height) // 2))
            im = canvas
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality, optimize=True)
        processed.append(buf.getvalue())
    if a4:
        layout = img2pdf.get_layout_fun((img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297)))
        return img2pdf.convert(processed, layout_fun=layout)
    return img2pdf.convert(processed)


def site_screenshot(url: str, fullpage: bool = False, width: int = 1280, height: int = 800):
    """
    Website ka screenshot — 3-engine fallback chain:
      1) thum.io (fast, HD)   2) thum.io fullpage   3) microlink.io (backup)
    """
    u = url if url.startswith(("http://", "https://")) else "https://" + url
    candidates = []
    if fullpage:
        candidates.append(f"https://image.thum.io/get/width/{width}/crop/3000/noanimate/{u}")
        candidates.append(f"https://image.thum.io/get/width/{width}/noanimate/{u}")
    else:
        candidates.append(f"https://image.thum.io/get/width/{width}/crop/{height}/noanimate/{u}")
        candidates.append(f"https://image.thum.io/get/width/{width}/noanimate/{u}")

    for api in candidates:
        try:
            r = requests.get(api, headers=UA, timeout=15)
            if r.status_code == 200 and len(r.content) > 3000:
                return io.BytesIO(r.content)
        except Exception:
            continue

    # Backup engine: microlink
    try:
        r = requests.get("https://api.microlink.io/", params={"url": u, "screenshot": "true", "meta": "false",
                                                             "waitUntil": "networkidle0"},
                         headers=UA, timeout=30)
        if r.status_code == 200:
            j = r.json()
            shot = ((j.get("data") or {}).get("screenshot") or {}).get("url")
            if shot:
                r2 = requests.get(shot, headers=UA, timeout=25)
                if r2.status_code == 200 and len(r2.content) > 3000:
                    return io.BytesIO(r2.content)
    except Exception:
        pass
    return None


def _ddg_lite(query, headers, max_results):
    out = []
    try:
        r = requests.post("https://lite.duckduckgo.com/lite/", data={"q": query}, headers=headers, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            links = soup.find_all("a", class_="result-link")
            snippets = soup.find_all("td", class_="result-snippet")
            for i, a in enumerate(links[:max_results]):
                href = a.get("href", "")
                if "uddg=" in href:
                    href = unquote(href.split("uddg=")[1].split("&")[0])
                if href.startswith("http"):
                    out.append({"title": a.get_text(strip=True), "url": href,
                                "snippet": (snippets[i].get_text(strip=True)[:130] if i < len(snippets) else ""),
                                "src": "DuckDuckGo"})
    except Exception:
        pass
    return out


def _ddg_html(query, headers, max_results):
    out = []
    try:
        r = requests.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=headers, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for res in soup.find_all("div", class_="result")[:max_results]:
                a = res.find("a", class_="result__a")
                sn = res.find("a", class_="result__snippet")
                if a and a.get("href"):
                    href = a["href"]
                    if "uddg=" in href:
                        href = unquote(href.split("uddg=")[1].split("&")[0])
                    if href.startswith("http"):
                        out.append({"title": a.get_text(strip=True), "url": href,
                                    "snippet": (sn.get_text(strip=True)[:130] if sn else ""),
                                    "src": "DuckDuckGo"})
    except Exception:
        pass
    return out


def _bing_search(query, headers, max_results):
    out = []
    try:
        r = requests.get(f"https://www.bing.com/search?q={quote(query)}", headers=headers, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for li in soup.find_all("li", class_="b_algo")[:max_results]:
                h2 = li.find("h2")
                if h2 and h2.find("a"):
                    a = h2.find("a")
                    p = li.find("p")
                    out.append({"title": a.get_text(strip=True), "url": a.get("href", ""),
                                "snippet": (p.get_text(strip=True)[:130] if p else ""), "src": "Bing"})
    except Exception:
        pass
    return out


def search_web_rich(query: str, max_results: int = 6) -> list[dict]:
    """3-engine parallel search (DuckDuckGo Lite + DDG HTML + Bing) — merge, dedupe, verified links."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [
            ex.submit(_ddg_lite, query, headers, max_results),
            ex.submit(_ddg_html, query, headers, max_results),
            ex.submit(_bing_search, query, headers, max_results),
        ]
        for f in futs:
            try:
                results.extend(f.result(timeout=12) or [])
            except Exception:
                pass

    # Dedupe (domain+path) aur junk hatao
    seen, clean = set(), []
    for r in results:
        u = (r.get("url") or "").strip()
        t = (r.get("title") or "").strip()
        if not u.startswith("http") or not t:
            continue
        key = u.split("?")[0].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        clean.append(r)
        if len(clean) >= max_results:
            break
    return clean


def get_app_store_links(app_name: str) -> dict:
    """Returns 6 trusted Official & MOD APK download stores including GetModPC"""
    q = quote(app_name.strip())
    stores = [
        {"name": "📱 Google Play Store (Official)", "url": f"https://play.google.com/store/search?q={q}&c=apps", "badge": "🏆 Official"},
        {"name": "⚡ GetModPC (Premium Mod/PC)", "url": f"https://getmodpc.com/?s={q}", "badge": "🔥 Verified Mod"},
        {"name": "📦 APKPure (Direct APK & OBB)", "url": f"https://apkpure.com/search?q={q}", "badge": "⚡ Fast Mirror"},
        {"name": "🛡️ APKMirror (Clean & Safe)", "url": f"https://www.apkmirror.com/?post_type=app_release&searchtype=apk&s={q}", "badge": "🛡️ 100% Safe"},
        {"name": "💎 HappyMod (Unlocked VIP Mods)", "url": f"https://happymod.com/search.html?q={q}", "badge": "💎 Free Unlocked"},
        {"name": "🚀 Uptodown (Official Store)", "url": f"https://en.uptodown.com/android/search/{q}", "badge": "🚀 Global Mirror"},
        {"name": "🧩 APKCombo (APK + OBB + Mod)", "url": f"https://apkcombo.com/search/{q}", "badge": "🧩 All Versions"},
        {"name": "🟢 F-Droid (Open Source, 100% Safe)", "url": f"https://search.f-droid.org/?q={q}", "badge": "🟢 Open Source"},
    ]
    return {"app_name": app_name.title(), "stores": stores}
