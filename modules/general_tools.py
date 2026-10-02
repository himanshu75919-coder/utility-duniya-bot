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
