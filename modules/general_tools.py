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


def screenshot_url_error(url: str) -> str:
    """v50: screenshot se pehle URL validate karo.

    Returns "" agar URL theek hai, warna user ko dikhane layak reason.
    (site_screenshot ka return type BytesIO|None hi rakha hai — tuple nahi,
     warna callers ka `if buf:` check tut jaata kyunki tuple hamesha truthy hota hai.)
    """
    u = url if url.startswith(("http://", "https://")) else "https://" + url
    try:
        from modules.core.net import is_safe_url
    except Exception:            # noqa: BLE001
        return ""
    ok, why = is_safe_url(u)
    return "" if ok else why


def site_screenshot(url: str, fullpage: bool = False, width: int = 1280, height: int = 800):
    """
    Website ka screenshot — 3-engine fallback chain:
      1) thum.io (fast, HD)   2) thum.io fullpage   3) microlink.io (backup)

    Returns: io.BytesIO (image) ya None.
    """
    u = url if url.startswith(("http://", "https://")) else "https://" + url
    if screenshot_url_error(u):
        return None
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


# =====================================================================================
# 🌦️ WEATHER — Open-Meteo (100% FREE, koi API key nahi) — v50
# =====================================================================================
WMO_WEATHER = {
    0: ("☀️", "Bilkul saaf aasmaan"),
    1: ("🌤️", "Zyada tar dhoop, thode baadal"),
    2: ("⛅", "Aadhi dhoop, aadhi baadal"),
    3: ("☁️", "Poora baadal — dhundla"),
    45: ("🌫️", "Khuwaan (fog)"),
    48: ("🌫️", "Barf ka khuwaan (icing fog)"),
    51: ("🌦️", "Halki bheedi (drizzle)"),
    53: ("🌦️", "Bheedi"),
    55: ("🌧️", "Tez bheedi"),
    56: ("🌧️", "Halki barf-bheedi"),
    57: ("🌧️", "Tez barf-bheedi"),
    61: ("🌦️", "Halki baarish"),
    63: ("🌧️", "Baarish"),
    65: ("🌧️", "Tez baarish"),
    66: ("❄️", "Barf-baarish"),
    67: ("❄️", "Tez barf-baarish"),
    71: ("🌨️", "Halki barf"),
    73: ("❄️", "Baarish saath barf"),
    75: ("❄️", "Tez barf"),
    77: ("❄️", "Barf ke daane (snow grains)"),
    80: ("🌦️", "Halki baarish ke chhank"),
    81: ("🌧️", "Baarish ke chhank"),
    82: ("⛈️", "Tez baarish ke chhank"),
    85: ("🌨️", "Barf ke chhank"),
    86: ("❄️", "Tez barf ke chhank"),
    95: ("⛈️", "Baadline (thunderstorm)"),
    96: ("⛈️", "Baadline + barfdaane"),
    99: ("⛈️", "Tez baadline + barfdaane"),
}

WEATHER_CITY_ALIASES = {
    "gaya": "Gaya", "gaya bihar": "Gaya", "patna": "Patna",
    "muzaffarpur": "Muzaffarpur", "bhagalpur": "Bhagalpur",
    "munger": "Munger", "darbhanga": "Darbhanga",
    "sitamarhi": "Sitamarhi", "hajipur": "Hazipur",
}


def weather_report(query: str) -> dict:
    """City naam → abhi ka mausam + aage 3 din ka forecast (Open-Meteo, free, no key).

    Returns {ok, place, temp, feels, humidity, wind, rain_today, icon, desc,
             sunrise, sunset, forecast:[{date,icon,max,min,rain}]}
    """
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "Shehar ka naam bhejo (jaise <code>Gaya</code> ya <code>Pune</code>)."}
    alias = WEATHER_CITY_ALIASES.get(q.lower())

    # 1) geocoding (naam → lat/lon)
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": alias or q, "count": 6, "language": "en", "format": "json"},
            headers=UA, timeout=12,
        )
        hits = (r.json() or {}).get("results") or []
    except Exception as e:
        return {"ok": False, "error": f"City search fail ho gaya: {str(e)[:80]}"}
    if not hits:
        return {"ok": False,
                "error": ("Ye sheher nahi mila. Poora naam likho (jaise <code>Gaya</code>, "
                          "<code>Pune</code>, <code>Ranchi</code>, <code>Kolkata</code>).")}
    hits.sort(key=lambda h: 0 if str(h.get("country", "")).lower() == "india" else 1)
    hit = hits[0]
    lat, lon = hit["latitude"], hit["longitude"]
    place = ", ".join(x for x in [hit.get("name"), hit.get("admin1"), hit.get("country")] if x)

    # 2) current + daily forecast
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code,precipitation",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset",
            "timezone": "auto", "forecast_days": 4,
        }, headers=UA, timeout=15)
        j = r.json()
    except Exception as e:
        return {"ok": False, "error": f"Weather server se jawab nahi aaya: {str(e)[:80]}"}

    cur = j.get("current") or {}
    daily = j.get("daily") or {}
    codes = daily.get("weather_code") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    prob = daily.get("precipitation_probability_max") or []
    days = daily.get("time") or []
    sunr = (daily.get("sunrise") or [""])[0]
    suns = (daily.get("sunset") or [""])[0]
    try:
        code_now = int(cur.get("weather_code", 0) or 0)
    except Exception:
        code_now = 0
    icon, desc = WMO_WEATHER.get(code_now, ("🌡️", "Weather update"))

    forecast = []
    for i in range(1, min(4, len(days))):
        try:
            di_code = int(codes[i] or 0)
        except Exception:
            di_code = 0
        forecast.append({
            "date": days[i],
            "icon": WMO_WEATHER.get(di_code, ("🌡️", ""))[0],
            "max": tmax[i] if i < len(tmax) and tmax[i] is not None else None,
            "min": tmin[i] if i < len(tmin) and tmin[i] is not None else None,
            "rain": prob[i] if i < len(prob) and prob[i] is not None else None,
        })
    try:
        rain_today = int(prob[0]) if prob and prob[0] is not None else None
    except Exception:
        rain_today = None

    def _hhmm(s):
        return str(s).split("T")[-1][:5] if s else "—"

    return {
        "ok": True, "place": place, "city": hit.get("name", q),
        "temp": cur.get("temperature_2m"), "feels": cur.get("apparent_temperature"),
        "humidity": cur.get("relative_humidity_2m"), "wind": cur.get("wind_speed_10m"),
        "rain_today": rain_today, "icon": icon, "desc": desc,
        "sunrise": _hhmm(sunr), "sunset": _hhmm(suns),
        "forecast": forecast, "lat": lat, "lon": lon,
    }


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
