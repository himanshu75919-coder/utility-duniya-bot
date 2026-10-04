# -*- coding: utf-8 -*-
"""
Smart OSINT & Digital Investigation Hub — v32 PRO
=================================================
Vehicle RTO, Phone Carrier/Circle, IFSC Bank Branch, Pincode (+ area-name search), Domain/IP Lookup,
and REAL Username Existence Checker (GitHub / YouTube / TikTok / Steam / Telegram verified).

NOTE (safety): Default me sirf PUBLIC / lawful sources use hote hain (telecom carrier+circle, bank branch,
pin code, IP geo). "Public records" lookup (naam/address wala) ek OPTIONAL feature hai jo bot owner ne
v49.9 se HAMESHA BAND hai (leaked personal data — DPDP Act/Aadhaar Act ke khilaf).
Iska misuse (kisi ko pareshan karna / blackmail / fraud) India me CRIME hai (IT Act + DPDP Act).
"""

import os
import re
import requests

try:
    from modules import api_hub as hub
except Exception:            # pragma: no cover
    hub = None
import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType

UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# =====================================================================================
# RTO / VEHICLE
# =====================================================================================
RTO_STATES = {
    "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh", "AS": "Assam", "BR": "Bihar",
    "CG": "Chhattisgarh", "CH": "Chandigarh", "DD": "Daman & Diu", "DL": "Delhi",
    "DN": "Dadra & Nagar Haveli", "GA": "Goa", "GJ": "Gujarat", "HP": "Himachal Pradesh",
    "HR": "Haryana", "JH": "Jharkhand", "JK": "Jammu & Kashmir", "KA": "Karnataka",
    "KL": "Kerala", "LA": "Ladakh", "LD": "Lakshadweep", "MH": "Maharashtra",
    "ML": "Meghalaya", "MN": "Manipur", "MP": "Madhya Pradesh", "MZ": "Mizoram",
    "NL": "Nagaland", "OD": "Odisha", "OR": "Odisha", "PB": "Punjab", "PY": "Puducherry",
    "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TR": "Tripura",
    "TS": "Telangana", "UA": "Uttarakhand", "UK": "Uttarakhand", "UP": "Uttar Pradesh",
    "WB": "West Bengal",
}

# Popular RTO office codes (district level) — bade shehar
RTO_DISTRICTS = {
    "BR01": "Patna", "BR02": "Gaya", "BR06": "Muzaffarpur", "BR07": "Darbhanga", "BR10": "Bhagalpur",
    "UP32": "Lucknow", "UP65": "Varanasi", "UP70": "Prayagraj", "UP78": "Kanpur", "UP16": "Noida (Gautam Buddha Nagar)",
    "DL01": "Delhi (Mall Road)", "DL02": "Delhi (IP Depot)", "DL08": "Delhi (Wazirpur)", "DL09": "Delhi (Dwarka)",
    "MH01": "Mumbai (Tardeo)", "MH02": "Mumbai (Andheri)", "MH12": "Pune", "MH43": "Navi Mumbai",
    "KA01": "Bengaluru (Koramangala)", "KA03": "Bengaluru (Indiranagar)", "KA05": "Bengaluru (Jayanagar)",
    "TN01": "Chennai (Ayanavaram)", "TN22": "Chennai (Meenambakkam)", "TN38": "Coimbatore",
    "GJ01": "Ahmedabad", "GJ05": "Surat", "GJ18": "Vadodara",
    "RJ14": "Jaipur", "RJ19": "Jodhpur", "RJ27": "Udaipur",
    "MP09": "Bhopal", "MP13": "Indore", "MP20": "Jabalpur",
    "HR26": "Gurugram", "HR51": "Faridabad", "PB10": "Ludhiana", "PB65": "Mohali",
    "JH01": "Ranchi", "JH05": "Jamshedpur", "WB02": "Kolkata (Beltala)", "WB06": "Kolkata (Kasba)",
    "OD02": "Bhubaneswar", "OD05": "Cuttack", "TS09": "Hyderabad (Khairatabad)", "TS07": "Hyderabad (Ranga Reddy)",
    "KL01": "Thiruvananthapuram", "KL07": "Ernakulam (Kochi)", "AP39": "Visakhapatnam",
}

VEHICLE_CLASS = {
    "1": "Car / Jeep / Taxi (Non-commercial)", "2": "Car / Jeep (Commercial)", "3": "Auto Rickshaw (Non-Comm)",
    "4": "Auto Rickshaw (Commercial)", "5": "Motorcycle / Scooter (Non-Comm)", "6": "Motorcycle (Commercial)",
    "7": "Truck / Lorry (Non-Comm)", "8": "Truck / Lorry (Commercial)", "9": "Bus (Non-Comm)",
    "0": "Bus (Commercial / School)", "11": "Tractor", "12": "E-Rickshaw / E-Cart", "13": "Trailer",
}


def lookup_vehicle_rto(plate: str) -> dict:
    """Parses Indian number plate: state, RTO office, vehicle class + official check links."""
    clean = re.sub(r"[^A-Za-z0-9]", "", plate or "").upper()
    if len(clean) < 6:
        return {"ok": False, "error": "Wrong format. Type it like: <code>BR01AB1234</code> or <code>DL8CAF5030</code>"}

    m = re.match(r"^([A-Z]{2})(\d{1,2})([A-Z]{0,3})(\d{1,4})$", clean)
    if not m:
        return {"ok": False, "error": "Number plate format not understood. Example: <code>BR01AB1234</code>"}

    state_code, rto_no, series, number = m.groups()
    state_name = RTO_STATES.get(state_code)
    if not state_name:
        return {"ok": False, "error": f"'{state_code}' state code is not valid (example: BR, UP, DL, MH...)"}

    rto_code = f"{state_code}{int(rto_no):02d}"
    district = RTO_DISTRICTS.get(rto_code, "RTO office (district code " + str(int(rto_no)) + ")")
    class_code = series[:1] if series else ""
    v_class = VEHICLE_CLASS.get(class_code, "") if class_code.isdigit() else ""

    return {
        "ok": True,
        "plate": clean,
        "pretty": f"{state_code} {int(rto_no):02d} {series} {number}".strip(),
        "state_code": state_code,
        "state_name": state_name,
        "rto_code": rto_code,
        "district": district,
        "vehicle_class": v_class,
        "links": [
            ("🔎 RC Details (VAHAN)", "https://vahan.parivahan.gov.in/nrservices/faces/user/searchstatus.xhtml"),
            ("🎫 e-Challan Check", "https://echallan.parivahan.gov.in/index/accused-challan"),
            ("🛡️ Insurance (IIB)", "https://iib.gov.in/IIB/InsuPolicySearch.aspx"),
            ("📄 DL Status (Sarathi)", "https://sarathi.parivahan.gov.in/sarathiservice/stateSelection.do"),
            ("📲 mParivahan App", "https://play.google.com/store/apps/details?id=com.nic.mparivahan"),
        ],
        "note": "VAHAN/Parivahan par OTP aur captcha lagta hai, isliye asli RC details wahi milti hain — ye tool aapko official page par le jata hai.",
    }


# =====================================================================================
# PHONE NUMBER
# =====================================================================================
def lookup_phone_info(number_str: str) -> dict:
    """Carrier, circle/region, timezone, number type + safety links (100% public data)."""
    clean = re.sub(r"[^\d+]", "", number_str or "")
    if not clean:
        return {"ok": False, "error": "Number bhejo (jaise <code>9876543210</code> ya <code>+919876543210</code>)"}

    if not clean.startswith("+"):
        clean = ("+91" + clean) if len(clean) == 10 else ("+" + clean)

    try:
        parsed = phonenumbers.parse(clean, None)
    except Exception as e:
        return {"ok": False, "error": f"Could not read the number: {str(e)[:80]}"}

    region_code = phonenumbers.region_code_for_number(parsed)
    valid = phonenumbers.is_valid_number(parsed)
    possible = phonenumbers.is_possible_number(parsed)

    if not possible:
        return {"ok": False, "error": "This number does not look possible (wrong digits)."}

    ntype_map = {
        PhoneNumberType.MOBILE: "📱 Mobile", PhoneNumberType.FIXED_LINE: "☎️ Landline",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "📱 Mobile / Landline",
        PhoneNumberType.TOLL_FREE: "🆓 Toll Free", PhoneNumberType.VOIP: "💻 VoIP / Internet Number",
        PhoneNumberType.PREMIUM_RATE: "💎 Premium Rate", PhoneNumberType.SHARED_COST: "💠 Shared Cost",
        PhoneNumberType.PERSONAL_NUMBER: "👤 Personal Number", PhoneNumberType.PAGER: "📟 Pager",
        PhoneNumberType.UAN: "🏢 UAN (Corporate)", PhoneNumberType.VOICEMAIL: "📨 Voicemail",
        PhoneNumberType.UNKNOWN: "❔ Type unknown",
    }
    ntype = ntype_map.get(number_type(parsed), "❔ Unknown")

    country = geocoder.description_for_number(parsed, "en") or "India"
    operator = carrier.name_for_number(parsed, "en") or ""
    zones = ", ".join(timezone.time_zones_for_number(parsed)) or "Asia/Kolkata"
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    digits = e164.lstrip("+")

    # Indian mobile series hint (6/7/8/9 se shuru hone wale mobile)
    series_note = ""
    if region_code == "IN" and len(digits) == 12 and digits[2] in "6789":
        series_note = "Indian mobile series ✅"

    return {
        "ok": True,
        "valid": bool(valid),
        "number": digits,
        "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
        "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "e164": e164,
        "country": country,
        "country_code": region_code or "-",
        "operator": operator or "Could not detect (may be a new or ported number)",
        "circle": country or "India",
        "timezones": zones,
        "type": ntype,
        "series_note": series_note,
        "links": [
            ("💬 WhatsApp Check", f"https://wa.me/{digits}"),
            ("✈️ Telegram Check", f"https://t.me/+{digits}"),
            ("🔍 Truecaller Search", f"https://www.truecaller.com/search/in/{digits}"),
            ("🌐 Google Search", f"https://www.google.com/search?q=%22{digits}%22"),
            ("🚨 Chakshu (Spam Report - TRAI)", "https://sancharsaathi.gov.in/sfc/"),
            ("🚔 Cyber Crime Helpline 1930", "https://cybercrime.gov.in/"),
        ],
        "note": "Number port (MNP) hua ho to carrier/circle badal sakta hai.",
    }


# =====================================================================================
# IFSC
# =====================================================================================
def lookup_ifsc(code: str) -> dict:
    """Razorpay public IFSC API — bank branch, MICR, UPI/NEFT/IMPS, map link."""
    clean = re.sub(r"[^A-Za-z0-9]", "", code or "").upper()
    if len(clean) != 11:
        return {"ok": False, "error": "IFSC is 11 characters (example SBIN0000001, HDFC0001234)"}
    if hub is not None and hub.hub_ready():
        res = hub.hub_ifsc(clean)
        if res.get("ok"):
            return res
    try:
        r = requests.get(f"https://ifsc.razorpay.com/{clean}", headers=UA_HEADERS, timeout=8)
        if r.status_code == 200:
            d = r.json()
            maps_q = requests.utils.quote(f"{d.get('BANK')} {d.get('BRANCH')} {d.get('ADDRESS')}")
            return {
                "ok": True,
                "ifsc": clean,
                "bank": d.get("BANK", "Bank"),
                "branch": d.get("BRANCH", "Branch"),
                "address": d.get("ADDRESS", "Address"),
                "city": d.get("CITY", ""),
                "district": d.get("DISTRICT", ""),
                "state": d.get("STATE", ""),
                "contact": d.get("CONTACT", ""),
                "micr": d.get("MICR", "N/A"),
                "neft": bool(d.get("NEFT")),
                "rtgs": bool(d.get("RTGS")),
                "imps": bool(d.get("IMPS")),
                "upi": bool(d.get("UPI")),
                "maps_link": f"https://maps.google.com/?q={maps_q}",
            }
        return {"ok": False, "error": f"'{clean}' RBI database me nahi mila. Spelling check karo."}
    except Exception as e:
        return {"ok": False, "error": f"API busy hai: {str(e)[:80]}"}


# =====================================================================================
# PINCODE (+ area-name search)
# =====================================================================================
def lookup_pincode(pincode: str) -> dict:
    """India Post API — district, state, taluk, division + map link."""
    clean = re.sub(r"[^\d]", "", pincode or "")
    if len(clean) != 6:
        return {"ok": False, "error": "Pincode is 6 digits (example 800001)"}
    if hub is not None and hub.hub_ready():
        res = hub.hub_pincode(clean)
        if res.get("ok"):
            return res
    try:
        r = requests.get(f"https://api.postalpincode.in/pincode/{clean}", headers=UA_HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data and data[0].get("Status") == "Success":
                po_list = data[0].get("PostOffice", [])
                primary = po_list[0] if po_list else {}
                names = [p.get("Name") for p in po_list[:10]]
                return {
                    "ok": True,
                    "pincode": clean,
                    "district": primary.get("District", ""),
                    "state": primary.get("State", ""),
                    "taluk": primary.get("Taluk", ""),
                    "division": primary.get("Division", ""),
                    "region": primary.get("Region", ""),
                    "circle": primary.get("Circle", ""),
                    "branch_type": primary.get("BranchType", ""),
                    "delivery": primary.get("DeliveryStatus", ""),
                    "post_offices": names,
                    "total_offices": len(po_list),
                    "maps_link": f"https://maps.google.com/?q={requests.utils.quote(primary.get('District', '') + ' ' + primary.get('State', ''))}",
                }
        return {"ok": False, "error": "Pincode not found. Send a correct 6-digit pincode."}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def search_by_area_name(area: str) -> dict:
    """Area/post-office ke naam se pincode dhoondhta hai (India Post API)."""
    q = re.sub(r"[^A-Za-z\s.]", "", area or "").strip()
    if len(q) < 3:
        return {"ok": False, "error": "Kam se kam 3 letter ka area name bhejo (jaise: Patna GPO, Kankarbagh)"}
    try:
        r = requests.get(f"https://api.postalpincode.in/postoffice/{requests.utils.quote(q)}", headers=UA_HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data and data[0].get("Status") == "Success":
                pos = data[0].get("PostOffice", [])[:10]
                return {
                    "ok": True,
                    "query": q,
                    "results": [
                        {
                            "name": p.get("Name", ""),
                            "pincode": p.get("Pincode", ""),
                            "district": p.get("District", ""),
                            "state": p.get("State", ""),
                            "taluk": p.get("Taluk", ""),
                        }
                        for p in pos
                    ],
                    "total": len(data[0].get("PostOffice", [])),
                }
        return {"ok": False, "error": ("No post office found with this name. Send the <b>real name</b> "
                                       "(example <code>Rajendra Nagar</code>, <code>Patna GPO</code>, <code>Boring Road SO</code>).")}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


# =====================================================================================
# IP / DOMAIN
# =====================================================================================
def lookup_ip_domain(target: str) -> dict:
    """IP & Domain geolocation + ISP (ip-api.com)."""
    clean = re.sub(r"^https?://", "", (target or "").strip()).split("/")[0].strip()
    if not clean:
        return {"ok": False, "error": "Domain ya IP bhejo (jaise google.com ya 8.8.8.8)"}
    # 🏠 v46: private / LAN IP ka koi public record nahi hota (hub se pehle block)
    _m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", clean)
    if _m:
        _o = [int(x) for x in _m.groups()]
        if not all(0 <= x <= 255 for x in _o):
            return {"ok": False, "error": "This is not a valid IP address (each part must be 0-255)."}
        if (_o[0] in (0, 10, 127) or (_o[0] == 192 and _o[1] == 168)
                or (_o[0] == 172 and 16 <= _o[1] <= 31) or (_o[0] == 169 and _o[1] == 254)):
            return {"ok": False, "private_ip": True,
                    "error": "Ye private / LAN IP hai (ghar ka router ya local network). Iski public info nahi hoti. Public IP ya website ka naam bhejo."
                             "No public info exists for it. Send a public IP or a domain instead."}
    # 🌐 v45: pehle user ka API hub, phir purana ip-api
    if hub is not None and hub.hub_ready():
        res = hub.hub_ip(clean)
        if res.get("ok"):
            return res
    try:
        r = requests.get(f"http://ip-api.com/json/{clean}", params={"fields": "status,message,query,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting"},
                         headers=UA_HEADERS, timeout=8)
        if r.status_code == 200:
            d = r.json()
            if d.get("status") == "success":
                return {
                    "ok": True,
                    "query": clean,
                    "ip": d.get("query", clean),
                    "isp": d.get("isp", "N/A"),
                    "org": d.get("org", "N/A"),
                    "country": d.get("country", "N/A"),
                    "country_code": d.get("countryCode", ""),
                    "region": d.get("regionName", "N/A"),
                    "city": d.get("city", "N/A"),
                    "zip": d.get("zip", ""),
                    "timezone": d.get("timezone", "N/A"),
                    "as": d.get("as", "N/A"),
                    "lat": d.get("lat"), "lon": d.get("lon"),
                    "is_proxy": bool(d.get("proxy")),
                    "is_mobile": bool(d.get("mobile")),
                    "is_hosting": bool(d.get("hosting")),
                    "maps_link": f"https://maps.google.com/?q={d.get('lat')},{d.get('lon')}" if d.get("lat") else "",
                }
            return {"ok": False, "error": d.get("message", "No info found")}
        return {"ok": False, "error": f"API status {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


# =====================================================================================
# PUBLIC-RECORDS LOOKUP (OPTIONAL — bot owner ne enable kiya; env se off ho sakta hai)
# =====================================================================================
NUM_INFO_API_BASE = lambda: os.environ.get("NUM_INFO_API_BASE", "https://osint-api-hub.onrender.com").rstrip("/")
NUM_INFO_API_KEY = lambda: os.environ.get("NUM_INFO_API_KEY", "Demo")
# v49.9: leaked personal-record lookup HAMESHA off (kabhi on nahi hoga)
NUM_LEAK_ENABLED = lambda: False

PUBLIC_RECORD_WARNING = (
    "⚠️ <b>IMPORTANT:</b>\n"
    "This is <b>public/leaked record</b> information (it may contain someone's personal details).\n"
    "• Using it to <b>harass, blackmail or defraud</b> anyone is a <b>CRIME</b> in India "
    "(IT Act + DPDP Act — jail/fine possible)\n"
    "• Look up only <b>your own</b> information, or for <b>legal</b> work (example: complaint about a fraud number)\n"
    "• The bot owner can switch this feature off any time (NUM_LEAK_ENABLED=off)"
)


def lookup_public_records(number: str) -> dict:
    """
    v49.9 (IMPORTANT): Ye feature JAAN-BOOJH KAR band hai — HAMESHA.

    Number se naam / pita ka naam / pata / Aadhaar dikhana **leaked (chori ke) database**
    se aata hai. India me ye:
      • DPDP Act 2023 ke khilaf hai (personal data ka galat istemal)
      • Aadhaar Act sec. 38 — Aadhaar number dikhana/batna = jail ho sakti hai
      • Telegram bhi aise bots ko PERMANENT BAN kar deta hai
    Isliye ye function ab kabhi personal record return nahi karega — chahe koi env set ho.
    (Kanooni tarika: sirf carrier/operator/HLR data + official complaint links.)
    """
    return {
        "ok": False,
        "blocked": True,
        "legal_block": True,
        "error": ("Naam/pata/Aadhaar jaise personal records leaked databases se aate hain — "
                  "inhe dikhana/becna kayde se MANA hai (DPDP Act 2023 + Aadhaar Act). "
                  "Bot ban ho jata aur FIR ka khatra hota hai. Isliye ye band hai."),
        "safe_alternatives": {
            "carrier": "📱 Operator/Circle data (legal) — NUMBER INFO tool me",
            "complaint": "🚨 Spam/fraud: Sanchar Saathi ya 1930",
        },
    }


def number_safety_info(number: str) -> dict:
    """LEGAL help card: carrier data (agar provider ho) + official complaint/report links."""
    digits = re.sub(r"\D", "", number or "")
    info = {"ok": True, "number": digits}
    try:
        if hub is not None and hub.hub_ready():
            car = hub.hub_carrier_info(digits)
            if car.get("ok"):
                info.update({"operator": car.get("operator"), "circle": car.get("circle"),
                             "type": car.get("type"), "ported": car.get("ported")})
    except Exception:
        pass
    info["links"] = [
        ("🚫 Spam/Fraud report (Chakshu)", "https://sancharsaathi.gov.in/sfc/"),
        ("🚨 Cyber Crime — 1930", "https://cybercrime.gov.in/"),
        ("🔎 MNP / Ported check", "https://tafcop.dgtelecom.gov.in/"),
    ]
    return info


# =====================================================================================
# USERNAME — REAL EXISTENCE CHECKER (verified working sources)
# =====================================================================================
def _gh_exists(u):
    try:
        r = requests.get(f"https://api.github.com/users/{u}", headers=UA_HEADERS, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return True, f"{d.get('name') or u} • {d.get('public_repos', 0)} repos • {d.get('followers', 0)} followers"
        return False, ""
    except Exception:
        return None, ""


def _tg_exists(u):
    """Telegram: real name/photo hote hain to exist karta hai; warna page 'Telegram: Contact @user' dikhata hai."""
    try:
        r = requests.get(f"https://t.me/{u}", headers=UA_HEADERS, timeout=10)
        t = r.text
        m = re.search(r'<meta property="og:title" content="([^"]*)"', t)
        title = (m.group(1) if m else "").strip()
        desc = re.search(r'<meta property="og:description" content="([^"]*)"', t)
        has_photo = "tgme_page_photo" in t
        dtext = (desc.group(1) if desc else "").strip()
        low_all = (title + " " + dtext).lower()
        generic_page = (("new era of messaging" in low_all) or ("fast. secure. powerful" in low_all)
                        or title in ("Telegram", "Telegram Messenger"))
        is_real = (bool(title) and not title.startswith("Telegram: Contact @")
                   and not generic_page and (has_photo or dtext))
        if is_real:
            extra = title
            if desc and desc.group(1) and len(desc.group(1)) < 60:
                extra = f"{title} — {desc.group(1)}"
            return True, extra[:90]
        return False, ""
    except Exception:
        return None, ""


def _yt_exists(u):
    try:
        r = requests.get(f"https://www.youtube.com/@{u}", headers=UA_HEADERS, timeout=12)
        t = r.text
        if r.status_code == 200 and ("channelId" in t or "externalId" in t):
            m = re.search(r'"title":"([^"]{1,60})"', t) or re.search(r"<title>([^<]{1,60})</title>", t)
            return True, (m.group(1) if m else "")
        return False, ""
    except Exception:
        return None, ""


def _tt_exists(u):
    try:
        r = requests.get(f"https://www.tiktok.com/@{u}", headers=UA_HEADERS, timeout=12)
        return ('"uniqueId"' in r.text), ""
    except Exception:
        return None, ""


def _steam_exists(u):
    try:
        r = requests.get(f"https://steamcommunity.com/id/{u}", headers=UA_HEADERS, timeout=12)
        if "could not be found" in r.text.lower():
            return False, ""
        m = re.search(r'<span class="actual_persona_name">([^<]+)</span>', r.text)
        return True, (m.group(1) if m else "")
    except Exception:
        return None, ""


CHECKERS = {
    "github": ("🐙 GitHub", _gh_exists, "https://github.com/{}"),
    "telegram": ("✈️ Telegram", _tg_exists, "https://t.me/{}"),
    "youtube": ("▶️ YouTube", _yt_exists, "https://www.youtube.com/@{}"),
    "tiktok": ("🎵 TikTok", _tt_exists, "https://www.tiktok.com/@{}"),
    "steam": ("🎮 Steam", _steam_exists, "https://steamcommunity.com/id/{}"),
}

# Ye sirf direct link dete hain (in par reliable "exists" check possible nahi — login wall)
LINK_ONLY = [
    ("📸 Instagram", "https://instagram.com/{}"),
    ("🐦 X (Twitter)", "https://x.com/{}"),
    ("👽 Reddit", "https:/user/{}"),
    ("📌 Pinterest", "https:/{}"),
    ("👻 Snapchat", "https://www.snapchat.com/add/{}"),
    ("📘 Facebook", "https://facebook.com/{}"),
    ("🎧 Spotify", "https://open.spotify.com/user/{}"),
    ("🟣 Twitch", "https://www.twitch.tv/{}"),
    ("🧵 Threads", "https://www.threads.net/@{}"),
]


def check_username_platforms(username: str) -> dict:
    """Real check (GitHub/Telegram/YouTube/TikTok/Steam) + baaki ke direct links."""
    u = (username or "").lstrip("@").strip()
    u = re.sub(r"[^A-Za-z0-9._\-]", "", u)
    if len(u) < 2:
        return {"ok": False, "error": "Username must be at least 2 letters (example <code>@himanshu</code>)"}

    results = []
    for key, (label, fn, url_tpl) in CHECKERS.items():
        exists, extra = fn(u)
        results.append({
            "key": key, "label": label, "exists": exists, "extra": extra, "url": url_tpl.format(u),
        })

    links = [{"label": lab, "url": tpl.format(u)} for lab, tpl in LINK_ONLY]

    # 🆔 v45: hub se asli profile data (Instagram / Snapchat / X)
    profiles = {}
    if hub is not None and hub.hub_ready():
        try:
            ig = hub.hub_insta_profile(u)
            if ig.get("ok"):
                profiles["instagram"] = ig
        except Exception:
            pass
        try:
            sp = hub.hub_snap_stories(u)
            if sp.get("ok"):
                profiles[] = sp
        except Exception:
            pass
        try:
            tw = hub._profile(u)
            if tw.get("ok"):
                profiles[] = tw
        except Exception:
            pass
    return {"ok": True, "username": u, "results": results, "links": links,
            "profiles": profiles,
            "found": sum(1 for r in results if r["exists"] is True)}
