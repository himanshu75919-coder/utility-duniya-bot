# -*- coding: utf-8 -*-
"""
Smart OSINT & Digital Investigation Hub — v32 PRO
=================================================
Vehicle RTO, Phone Carrier/Circle, IFSC Bank Branch, Pincode (+ area-name search), Domain/IP Lookup,
and REAL Username Existence Checker (GitHub / YouTube / TikTok / Steam / Telegram verified).

NOTE: Default me sirf PUBLIC / lawful sources use hote hain (telecom carrier+circle, bank branch,
pin code, IP geo).
"""

import os
import re
import requests

try:
    from modules import api_hub as hub
except Exception:            # pragma: no cover
    hub = None

# v50: shared cache — IFSC/pincode/IP/area ka data din bhar same rehta hai,
# baar-baar API call karne se API quota + time dono bachte hain.
try:
    from modules.core.cache import TTLCache as _TTLCache
    _INFO = _TTLCache(maxsize=4096, default_ttl=1800)
    _CACHED = True
except Exception:            # pragma: no cover - core na ho to bina cache chalega
    _INFO = None
    _CACHED = False

import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType


def _cget(key):
    """Cache se lao; cache na ho ya miss ho to None."""
    if not _CACHED:
        return None
    return _INFO.get(key)


def _cput(key, val, ttl=None):
    """Cache me daalo (sirf successful results lambe TTL ke saath)."""
    if not _CACHED:
        return
    _INFO.put(key, val, ttl)


def _ok(res):
    return isinstance(res, dict) and res.get("ok")

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
        # v49.12: SAARE website links hata diye (user ka order) — sirf SMS tarika
        "links": [],
        "sms": {"rc": f"VAHAN {clean}", "challan": f"CHALLAN {clean}", "number": "7738299899"},
        "note": "RC + challan ka poora record SMS se: 'VAHAN <number>' aur 'CHALLAN <number>' likh kar 7738299899 par bhejo (official MoRTH/NIC gateway, free).",
    }


# =====================================================================================
# PHONE NUMBER
# =====================================================================================
def lookup_phone_info(number_str: str) -> dict:
    """Carrier, circle/region, timezone, number type (100% public data)."""
    clean = re.sub(r"[^\d+]", "", number_str or "")
    if not clean:
        return {"ok": False, "error": "Number bhejo (jaise <code>9876543210</code> ya <code>+919876543210</code>)"}

    if not clean.startswith("+"):
        if len(clean) == 10:
            clean = "+91" + clean
        elif len(clean) == 11 and clean.startswith("1"):
            # v50 fix: Indian toll-free 1800-xxxxxxx (11 digit, '1' se shuru)
            # pehle ye "+1800..." ban jata tha = US country code, number galat parse hota tha
            clean = "+91" + clean
        elif len(clean) == 12 and clean.startswith("91"):
            clean = "+" + clean
        else:
            clean = "+" + clean

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
        # v49.13: bahar wale links hata diye (user ka order) — koi link nahi.
        "links": [],
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
    if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", clean):
        return {"ok": False,
                "error": ("IFSC format galat hai. Sahi format: <b>4 letter + 0 + 6 digit/letter</b>\n"
                          f"📌 Jaise: <code>SBIN0000001</code> · <code>HDFC0001234</code>\n"
                          f"Aapne bheja: <code>{clean}</code>")}
    hit = _cget("ifsc:" + clean)
    if hit is not None:
        return {**hit, "cached": True}
    if hub is not None and hub.hub_ready():
        res = hub.hub_ifsc(clean)
        if res.get("ok"):
            _cput("ifsc:" + clean, res, 86400)
            return res
    try:
        r = requests.get(f"https://ifsc.razorpay.com/{clean}", headers=UA_HEADERS, timeout=8)
        if r.status_code == 200:
            d = r.json()
            maps_q = requests.utils.quote(f"{d.get('BANK')} {d.get('BRANCH')} {d.get('ADDRESS')}")
            out = {
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
            _cput("ifsc:" + clean, out, 86400)   # IFSC data bahut stable — 24 ghante
            return out
        if r.status_code == 404:
            return {"ok": False, "error": f"'{clean}' RBI database me nahi mila. Spelling check karo."}
        return {"ok": False, "error": f"IFSC server busy hai (HTTP {r.status_code}). Thodi der baad try karo."}
    except requests.Timeout:
        return {"ok": False, "error": "IFSC server ne jawab dene me time laga diya. Thodi der baad try karo."}
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
    # India ke real pincode 1-9 se start hote hain (0 se koi pincode nahi)
    if clean[0] == "0":
        return {"ok": False,
                "error": ("Ye pincode valid nahi lagta — India ka pincode <b>0 se start nahi hota</b>.\n"
                          f"📌 Jaise: <code>800001</code> (Patna) · <code>110001</code> (Delhi)\n"
                          f"Aapne bheja: <code>{clean}</code>")}
    hit = _cget("pin:" + clean)
    if hit is not None:
        return {**hit, "cached": True}
    if hub is not None and hub.hub_ready():
        res = hub.hub_pincode(clean)
        if res.get("ok"):
            _cput("pin:" + clean, res, 604800)
            return res
    try:
        r = requests.get(f"https://api.postalpincode.in/pincode/{clean}", headers=UA_HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data and data[0].get("Status") == "Success":
                po_list = data[0].get("PostOffice", [])
                primary = po_list[0] if po_list else {}
                names = [p.get("Name") for p in po_list[:10]]
                out = {
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
                _cput("pin:" + clean, out, 604800)   # pincode data saal bhar same — 7 din
                return out
        return {"ok": False,
                "error": (f"Pincode <code>{clean}</code> India Post database me nahi mila.\n"
                          "📌 Sahi 6-digit pincode bhejo, jaise <code>800001</code> (Patna GPO)")}
    except requests.Timeout:
        return {"ok": False, "error": "India Post server slow hai. Thodi der baad try karo."}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


# v50: India Post ka /postoffice endpoint sirf lagbhag-exact naam par chalta hai aur
# fuzzy match par poore India ke results deta hai (pehle Patna ke liye Telangana ke
# post office aate the). Isliye: (a) suffix strip karke dobara try karte hain,
# (b) results ko score karke sort karte hain taaki sahi district upar aaye.
_PO_SUFFIXES = ("GPO", "H.O.", "HO", "S.O.", "SO", "B.O.", "BO",
                "POST OFFICE", "POSTOFFICE", "SUB OFFICE", "BRANCH OFFICE",
                "HEAD OFFICE", "CANTT")


def _area_variants(name: str):
    """Search karne layak naam ke variants — (variant, kitna-andaza) ke saath."""
    n = re.sub(r"\s+", " ", name.strip())
    up = n.upper()
    out = [(n, False)]
    for s in sorted(_PO_SUFFIXES, key=len, reverse=True):
        if up.endswith(" " + s):
            stripped = n[: -(len(s) + 1)].strip()
            if stripped:
                out.append((stripped, True))
    if " " in n:
        first = n.split()[0]
        if len(first) >= 3:
            out.append((first, True))
    seen, res = set(), []
    for v, approx in out:
        k = v.lower()
        if k not in seen:
            seen.add(k)
            res.append((v, approx))
    return res[:4]


def _po_score(p: dict, core: str) -> int:
    """Kitna close hai ye post office user ke sawaal ke — zyada = upar."""
    nm = (p.get("Name") or "").strip().lower()
    di = (p.get("District") or "").lower()
    st = (p.get("State") or "").lower()
    ql = core.lower()
    s = 0
    if nm == ql:
        s += 100
    elif nm.startswith(ql):
        s += 60
    elif ql in nm:
        s += 40
    if di == ql:
        s += 50
    elif di.startswith(ql):
        s += 30
    if ql in st:
        s += 10
    if f"({ql})" in nm:
        s += 25
    return s


def search_by_area_name(area: str) -> dict:
    """Area/post-office ke naam se pincode dhoondhta hai (India Post API).

    v50: suffix-stripping + score-based ranking + honest "approximate" flag.
    """
    q = re.sub(r"[^A-Za-z\s.]", "", area or "").strip()
    if len(q) < 3:
        return {"ok": False, "error": "Kam se kam 3 letter ka area name bhejo (jaise: <code>Patna GPO</code>, <code>Gaya</code>)"}
    if len(q) > 60:
        return {"ok": False, "error": "Area ka naam bahut lamba hai — sirf area/post-office ka naam bhejo."}
    _k = "area:" + q.lower()
    hit = _cget(_k)
    if hit is not None:
        return {**hit, "cached": True}

    # query ka "core" — district match karne ke liye (GPO/SO jaise suffix hata kar)
    core = re.sub(r"\s+(GPO|SO|HO|BO|CANTT|POST OFFICE)$", "", q, flags=re.I).strip() or q

    last_err = ""
    for variant, approx in _area_variants(q):
        try:
            r = requests.get(
                f"https://api.postalpincode.in/postoffice/{requests.utils.quote(variant)}",
                headers=UA_HEADERS, timeout=8)
        except requests.Timeout:
            last_err = "India Post server slow hai. Thodi der baad try karo."
            continue
        except Exception as e:                     # noqa: BLE001
            last_err = str(e)[:100]
            continue
        if r.status_code != 200:
            last_err = f"India Post server busy hai (HTTP {r.status_code})."
            continue
        try:
            data = r.json()
        except ValueError:
            last_err = "India Post ne sahi jawab nahi bheja."
            continue
        if not (data and data[0].get("Status") == "Success"):
            continue
        pos = data[0].get("PostOffice") or []
        if not pos:
            continue
        ranked = sorted(pos, key=lambda p: -_po_score(p, core))
        out = {
            "ok": True,
            "query": q,
            "matched_via": variant,
            "approximate": approx or (variant.lower() != q.lower()),
            "results": [
                {
                    "name": p.get("Name", ""),
                    "pincode": p.get("Pincode", ""),
                    "district": p.get("District", ""),
                    "state": p.get("State", ""),
                    "taluk": p.get("Taluk", ""),
                }
                for p in ranked[:10]
            ],
            "total": len(pos),
        }
        _cput(_k, out, 604800)
        return out

    return {"ok": False, "error": last_err or (
        f"'{q}' naam ka koi post office India Post database me nahi mila.\n\n"
        "💡 <b>Ye try karo:</b>\n"
        "• Poora naam bhejo — jaise <code>Danapur Cantt</code>, <code>Civil Lines</code>\n"
        "• Ya seedha <b>6-digit pincode</b> bhejo (jaise <code>800001</code>) — wo 100% chalta hai"
    )}


# =====================================================================================
# IP / DOMAIN
# =====================================================================================
def lookup_ip_domain(target: str) -> dict:
    """IP & Domain geolocation + ISP (ip-api.com)."""
    clean = re.sub(r"^https?://", "", (target or "").strip()).split("/")[0].strip()
    if not clean:
        return {"ok": False, "error": "Domain ya IP bhejo (jaise google.com ya 8.8.8.8)"}
    # v50: protocol/path/userinfo hata do — "https://user:pass@site.com/x" jaisa input safe nahi
    clean = clean.split("@")[-1].strip().lower()
    if not re.match(r"^[a-z0-9.\-:]{3,253}$", clean):
        return {"ok": False,
                "error": ("Ye valid website ya IP nahi lagta.\n"
                          "📌 Jaise: <code>google.com</code> ya <code>8.8.8.8</code>\n"
                          f"Aapne bheja: <code>{clean[:40]}</code>")}
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
    _ik = "ip:" + clean
    hit = _cget(_ik)
    if hit is not None:
        return {**hit, "cached": True}
    if hub is not None and hub.hub_ready():
        res = hub.hub_ip(clean)
        if res.get("ok"):
            _cput(_ik, res, 3600)
            return res
    try:
        r = requests.get(f"http://ip-api.com/json/{clean}", params={"fields": "status,message,query,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting"},
                         headers=UA_HEADERS, timeout=8)
        if r.status_code == 200:
            d = r.json()
            if d.get("status") == "success":
                out = {
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
                _cput(_ik, out, 3600)   # IP geo badal sakta hai — 1 ghanta
                return out
            msg = d.get("message") or ""
            if "private" in msg.lower() or "reserved" in msg.lower():
                return {"ok": False, "private_ip": True,
                        "error": "Ye private / reserved IP hai — iski public info nahi hoti."}
            return {"ok": False,
                    "error": f"'{clean}' ka koi public record nahi mila. Domain ki spelling check karo."}
        if r.status_code == 429:
            return {"ok": False,
                    "error": "IP lookup server ki limit poori ho gayi. 1 minute baad try karo."}
        return {"ok": False, "error": f"API status {r.status_code}"}
    except requests.Timeout:
        return {"ok": False, "error": "IP server ne jawab dene me time laga diya. Thodi der baad try karo."}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


# =====================================================================================
# v52.2: 🌍 DOMAIN OSINT — whois(RDAP) + DNS(DoH) + subdomains(crt.sh) + IP geo
# =====================================================================================
_DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}$")


def _doh_query(name: str, qtype: str) -> list:
    """DNS records Google DNS-over-HTTPS (public JSON API) se — koi extra dependency nahi.
    Sirf public DNS data wapas deta hai (A/AAAA/MX/NS/TXT/SOA/CNAME)."""
    try:
        r = requests.get("https://dns.google/resolve",
                         params={"name": name, "type": qtype},
                         headers=UA_HEADERS, timeout=8)
        if r.status_code != 200:
            return []
        out = []
        for ans in r.json().get("Answer", []) or []:
            data = ans.get("data")
            if data:
                out.append(data)
        return out
    except Exception:
        return []


def domain_osint(target: str) -> dict:
    """Domain ka full public OSINT: RDAP whois + DNS records + certificate-transparency
    subdomains + primary A-record ki IP info. Sab sources public/official hain."""
    clean = (target or "").strip().lower().rstrip(".")
    clean = re.sub(r"^https?://", "", clean).split("/")[0]
    clean = clean.split("@")[-1].strip()
    if not _DOMAIN_RE.match(clean):
        return {"ok": False,
                "error": (f"'{clean[:40]}' valid domain nahi lagta.\n"
                          "📌 Jaise: <code>google.com</code>, <code>onrender.com</code>, "
                          "<code>bihar.gov.in</code>\n"
                          "<b>IP bhi ho sakta hai</b> (jaise <code>8.8.8.8</code>) — "
                          "wo IP info card milega.")}
    ck = "dom:" + clean
    hit = _cget(ck)
    if hit is not None:
        return {**hit, "cached": True}

    # 1) DNS: A record pehle (IP info ke liye)
    a_recs = _doh_query(clean, "A")
    result = {
        "ok": True, "domain": clean,
        "a": a_recs[:4], "aaaa": _doh_query(clean, "AAAA")[:2],
        "mx": _doh_query(clean, "MX")[:5], "ns": _doh_query(clean, "NS")[:6],
        "txt": _doh_query(clean, "TXT")[:3],
        "whois": None, "whois_error": "",
        "subdomains": [], "subdomains_error": "",
        "ip_info": None,
    }

    # 2) RDAP whois (rdap.org redirect karta hai sahi registry pe — free, no key)
    try:
        r = requests.get(f"https://rdap.org/domain/{clean}",
                         headers=UA_HEADERS, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            d = r.json()
            ev = {e.get("eventAction"): (e.get("eventDate") or "")[:10]
                  for e in d.get("events", []) or []}
            registrar = ""
            for ent in d.get("entities", []) or []:
                if "registrar" in (ent.get("roles") or []):
                    voc = ent.get("vcardArray")
                    if isinstance(voc, list) and len(voc) > 1:
                        for field in voc[1]:
                            if field and field[0] == "fn":
                                registrar = str(field[3])
                    break
            ns_from_rdap = [n.get("ldhName", "").rstrip(".").lower()
                            for n in d.get("nameservers", []) or [] if n.get("ldhName")]
            if ns_from_rdap and not result["ns"]:
                result["ns"] = ns_from_rdap[:6]
            result["whois"] = {
                "registrar": registrar or "N/A",
                "created": ev.get("registration", "N/A"),
                "expires": ev.get("expiration", "N/A"),
                "updated": ev.get("last changed", "N/A"),
                "status": ", ".join((d.get("status") or [])[:4]) or "N/A",
            }
        else:
            result["whois_error"] = (f"whois data nahi mila (RDAP {r.status_code}) — "
                                     "kuch domains ki registry RDAP support nahi karti")
    except Exception:
        result["whois_error"] = "whois server abhi jawab nahi diya (timeout)"

    # 3) Subdomains — Certificate Transparency (crt.sh public feed, free)
    try:
        r = requests.get("https://crt.sh/?q=%25." + clean + "&output=json",
                         headers=UA_HEADERS, timeout=25)
        if r.status_code == 200:
            names = []
            for row in r.json() or []:
                nm = (row.get("name_value") or "").strip().lstrip("*.")
                if nm and nm != clean and nm.endswith("." + clean) and nm not in names:
                    names.append(nm)
            result["subdomains"] = sorted(set(names))[:12]
            result["subdomains_total"] = len(set(names))
        else:
            result["subdomains_error"] = "certificate feed abhi jawab nahi di"
    except Exception:
        result["subdomains_error"] = "certificate feed timeout — baaki data theek hai"

    # 4) Primary A-record ki IP info (existing engine reuse)
    if a_recs:
        geo = lookup_ip_domain(a_recs[0])
        if geo.get("ok"):
            result["ip_info"] = geo

    if not result["a"] and not result["whois"] and not result["subdomains"]:
        return {"ok": False,
                "error": (f"'{clean}' ka koi public DNS/whois record nahi mila.\n"
                          "Domain ka spelling check karo, ya ye abhi register nahi hua.")}
    _cput(ck, result, 21600)   # whois/subdomains 6 ghante tak valid
    return result


# =====================================================================================
# v52.2: 🏦 UPI VERIFY — VPA format + bank handle (NPCI public bank codes)
# =====================================================================================
UPI_BANK_HANDLES = {
    "sbi": "State Bank of India (SBI)",
    "esic": "State Bank of India (SBI)",
    "okaxis": "Axis Bank",
    "utib": "Axis Bank (pehle UTI Bank)",
    "yes": "Axis Bank (pehle YES Bank)",
    "ybl": "Axis Bank (pehle YES Bank)",
    "okicici": "ICICI Bank",
    "icici": "ICICI Bank",
    "hdfcbank": "HDFC Bank",
    "kotak": "Kotak Mahindra Bank",
    "pnb": "Punjab National Bank",
    "bara": "Bank of Baroda",
    "bof": "Bank of India",
    "canara": "Canara Bank",
    "indusind": "IndusInd Bank",
    "iob": "Oriental Bank of Commerce (ab Bank of Baroda)",
    "central": "The Central Bank of India",
    "kfk": "The Central Bank of India",
    "union": "Union Bank of India",
    "nabi": "Bank of India (pehle NAB)",
    "corporate": "Corporation Bank (ab Bank of Baroda)",
    "andhra": "Bank of Baroda (pehle Andhra Bank)",
    "andhrabank": "Bank of Baroda (pehle Andhra Bank)",
    "vijaya": "Bank of Baroda (pehle Vijaya Bank)",
    "vib": "Bank of Baroda (pehle Vijaya Bank)",
    "dcb": "DCB Bank",
    "fcb": "Federal Bank",
    "idfk": "IDFC First Bank",
    "rbl": "RBL Bank",
    "idib": "IDBI Bank",
    "esfbank": "SBI (State Bank of India)",
    "esicbank": "SBI (State Bank of India)",
    "paytm": "Paytm Payments Bank",
    "amazpay": "Amazon Payments Bank",
    "esicupi": "SBI (State Bank of India)",
    "esfb": "SBI (State Bank of India)",
    "esic2": "SBI (State Bank of India)",
    "esicupay": "SBI (State Bank of India)",
}

_VPA_RE = re.compile(r"^([a-zA-Z0-9][a-zA-Z0-9._\-]{1,24})@([a-zA-Z][a-zA-Z0-9]{1,24})$")


def upi_verify(target: str) -> dict:
    """VPA (UPI ID) ka format check + bank handle ka bank naam.
    NOTE: sirf PUBLIC info hai — linked mobile, account number, kaun hai wo kisi bhi
    VPA se publicly nahi milta (aur isliye is tool me bhi nahi dikhega)."""
    clean = (target or "").strip().lower()
    clean = clean.replace(" ", "").lstrip("@")
    if not clean or "@" not in clean:
        return {"ok": False,
                "error": ("Ye VPA nahi lagta. VPA me <code>@</code> hota hai.\n"
                          "📌 Jaise: <code>rahul@sbi</code>, <code>9876543210@hdfcbank</code>\n"
                          "Aapka VPA app me Settings → UPI ID se milta hai.")}
    m = _VPA_RE.match(clean)
    if not m:
        return {"ok": False,
                "error": (f"'{clean[:40]}' valid VPA format nahi hai.\n"
                          "Format: <code>localpart@bankhandle</code> — jaise "
                          "<code>rahul@sbi</code> (localpart me letters/numbers/. _ - chalte hain).")}
    local, handle = m.group(1), m.group(2)
    bank = UPI_BANK_HANDLES.get(handle)
    out = {
        "ok": True,
        "vpa": clean,
        "local": local,
        "handle": handle,
        "bank": bank,
        "handle_known": bank is not None,
        "notes": [],
    }
    if not bank:
        out["notes"].append(f"Handle <code>@{handle}</code> meri known-bank list me nahi hai — "
                            "ye chhoti bank ya naya PSP handle ho sakta hai.")
    if re.match(r"^\d{10}$", local):
        out["notes"].append("Local part ek 10-digit number hai (mobile-style VPA) — "
                            "ye valid hai, par isse linked mobile number public nahi hota.")
    if len(local) > 25:
        out["notes"].append("Localpart 25 chars se lamba hai — bahut kam banks accept karte hain.")
    return out


# =====================================================================================
# v52.2: 📡 TG PUBLIC INFO — t.me public page (sirf public info)
# =====================================================================================
def tg_user_public(username: str) -> dict:
    """t.me/{username} ki PUBLIC page se name + about nikaalta hai (sirf wahi jo
    koi bhi public page par dekh sakta hai). Private channels/members nahi."""
    uname = (username or "").strip().lower()
    uname = re.sub(r"^https?://(?:t\.me|telegram\.(?:me|dog))/?", "", uname).split("/")[0].lstrip("@")
    if not re.match(r"^[a-z][a-z0-9_]{3,31}$", uname):
        return {"ok": False,
                "error": ("Valid @username bhejo — jaise <code>@telegram</code> ya "
                          "<code>somechannel</code>.\n"
                          "📌 Jo public channel hai, uska @username profile me dikhta hai.")}
    try:
        r = requests.get(f"https://t.me/{uname}", headers=UA_HEADERS, timeout=10)
        if r.status_code == 404:
            return {"ok": False, "exists": False,
                    "error": (f"<code>@{uname}</code> ka koi public Telegram page nahi mila — "
                              "username galat hai ya page private/removed hai.")}
        page = r.text
        title = re.search(r'property="og:title"\s+content="([^"]+)"', page)
        desc = re.search(r'class="tgme_page_description[^"]*"[^>]*>(.*?)</div>', page, re.S)
        name = (title.group(1) if title else "").strip()
        # t.me: user milne par actual naam aata hai; na milne par generic "Telegram: Contact @x"
        if name.startswith("Telegram: Contact"):
            return {"ok": False, "exists": False,
                    "error": (f"<code>@{uname}</code> ka koi public profile nahi mila — "
                              "username galat hai, ya profile private hai, ya user remove ho gaya.")}
        bio = ""
        if desc:
            bio = re.sub(r"<[^>]+>", "", desc.group(1)).strip()
        return {"ok": True, "exists": True, "type": "public_page",
                "username": uname, "name": name or f"@{uname}", "bio": bio}
    except Exception:
        return {"ok": False, "error": "Telegram public page abhi jawab nahi diya — 1 minute baad try karo."}
