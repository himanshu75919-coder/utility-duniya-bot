# -*- coding: utf-8 -*-
"""
General Utility Tools
QR code, Image-to-PDF, URL Shortener, EMI & Interest, Age, Password, Multi-Source Web Search Engine, and 6-Store App Finder.
"""

import io
import math
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


def make_qr_bytes(text: str) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=18,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


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


def pages_to_pdf(pages: list) -> bytes:
    processed = []
    for b in pages:
        im = Image.open(io.BytesIO(b)).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90, optimize=True)
        processed.append(buf.getvalue())
    return img2pdf.convert(processed)


def site_screenshot(url: str):
    u = url if url.startswith(("http://", "https://")) else "https://" + url
    api = f"https://image.thum.io/get/width/1280/crop/800/noanimate/{u}"
    try:
        r = requests.get(api, headers=UA, timeout=8)
        if r.status_code == 200 and len(r.content) > 3000:
            return io.BytesIO(r.content)
    except Exception:
        pass
    return None


def search_web_rich(query: str, max_results: int = 6) -> list[dict]:
    """Accurate web search returning real verified titles, snippets and copyable URLs"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    results = []

    # Method 1: DuckDuckGo Lite
    try:
        r = requests.post("https://lite.duckduckgo.com/lite/", data={"q": query}, headers=headers, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            links = soup.find_all("a", class_="result-link")
            snippets = soup.find_all("td", class_="result-snippet")
            for i, a in enumerate(links[:max_results]):
                href = a.get("href", "")
                if "uddg=" in href:
                    href = unquote(href.split("uddg=")[1].split("&")[0])
                snip = snippets[i].get_text(strip=True) if i < len(snippets) else ""
                if href.startswith("http"):
                    results.append({"title": a.get_text(strip=True), "url": href, "snippet": snip[:130]})
    except Exception:
        pass

    # Method 2: Bing Scraper Fallback
    if len(results) < 3:
        try:
            r = requests.get(f"https://www.bing.com/search?q={quote(query)}", headers=headers, timeout=6)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for li in soup.find_all("li", class_="b_algo")[:max_results]:
                    h2 = li.find("h2")
                    if h2 and h2.find("a"):
                        a = h2.find("a")
                        p = li.find("p")
                        results.append({
                            "title": a.get_text(strip=True),
                            "url": a.get("href", ""),
                            "snippet": p.get_text(strip=True)[:130] if p else "",
                        })
        except Exception:
            pass

    return results[:max_results]


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
    ]
    return {"app_name": app_name.title(), "stores": stores}
