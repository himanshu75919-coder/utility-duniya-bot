# -*- coding: utf-8 -*-
"""
General Utility Tools
QR code, Image-to-PDF, URL Shortener, EMI & Interest, Age, Password, Multi-Source Web Search Engine, and 6-Store App Finder.
"""

import io
import re
from datetime import datetime, timezone
from urllib.parse import quote
import qrcode
import requests
from PIL import Image
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


def domain_age_days(domain: str):
    """FREE RDAP se domain kitne din purana hai. None = nahi mila (check skip)."""
    try:
        d = (domain or "").lower().strip().rstrip(".")
        if not d or re.match(r"^\d{1,3}(\.\d{1,3}){3}$", d) or not re.search(r"\.", d):
            return None
        r = requests.get(f"https://rdap.org/domain/{d}", headers=UA, timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return None
        j = r.json()
        for ev in (j.get("events") or []):
            if ev.get("eventAction") == "registration" and ev.get("eventDate"):
                dte = datetime.fromisoformat(str(ev["eventDate"]).replace("Z", "+00:00"))
                return max(0, (datetime.now(timezone.utc) - dte).days)
    except Exception:
        return None
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
