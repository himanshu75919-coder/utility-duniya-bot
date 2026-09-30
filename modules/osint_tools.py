# -*- coding: utf-8 -*-
"""
Smart OSINT & Digital Investigation Hub
Vehicle RTO, Phone Carrier/Circle, IFSC Bank Branch, Pincode, Domain/IP Lookup, and Username Checker.
"""

import re
import requests
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

RTO_STATES = {
    "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh", "AS": "Assam", "BR": "Bihar",
    "CG": "Chhattisgarh", "CH": "Chandigarh", "DD": "Daman & Diu", "DL": "Delhi",
    "DN": "Dadra & Nagar Haveli", "GA": "Goa", "GJ": "Gujarat", "HP": "Himachal Pradesh",
    "HR": "Haryana", "JH": "Jharkhand", "JK": "Jammu & Kashmir", "KA": "Karnataka",
    "KL": "Kerala", "LA": "Ladakh", "LD": "Lakshadweep", "MH": "Maharashtra",
    "ML": "Meghalaya", "MN": "Manipur", "MP": "Madhya Pradesh", "MZ": "Mizoram",
    "NL": "Nagaland", "OD": "Odisha", "PB": "Punjab", "PY": "Puducherry",
    "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TR": "Tripura",
    "TS": "Telangana", "UK": "Uttarakhand", "UP": "Uttar Pradesh", "WB": "West Bengal",
}


def lookup_vehicle_rto(plate: str) -> dict:
    """Parses Indian license plate and returns State, District RTO, and official verification links"""
    clean = re.sub(r"[^A-Za-z0-9]", "", plate).upper()
    if len(clean) < 4:
        return {"ok": False, "error": "Invalid registration number format (e.g. DL01AB1234)"}
    
    state_code = clean[:2]
    state_name = RTO_STATES.get(state_code, "India State RTO")
    rto_code = clean[:4]
    
    challan_link = f"https://echallan.parivahan.gov.in/index/accused-challan"
    mparivahan = "https://parivahan.gov.in/rcdlstatus/?pur_cd=102"
    
    return {
        "ok": True,
        "plate": clean,
        "state_code": state_code,
        "state_name": state_name,
        "rto_code": rto_code,
        "challan_link": challan_link,
        "parivahan_link": mparivahan,
    }


def lookup_phone_info(number_str: str) -> dict:
    """Extracts country, circle, carrier/operator, and WhatsApp link"""
    clean = re.sub(r"[^\d+]", "", number_str)
    if not clean.startswith("+"):
        if len(clean) == 10:
            clean = "+91" + clean
        else:
            clean = "+" + clean
            
    try:
        parsed = phonenumbers.parse(clean, None)
        if not phonenumbers.is_valid_number(parsed):
            return {"ok": False, "error": "Invalid international phone number"}
            
        country = geocoder.description_for_number(parsed, "en")
        operator = carrier.name_for_number(parsed, "en") or "Indian Cellular Telecom"
        tz_list = timezone.time_zones_for_number(parsed)
        wa_link = f"https://wa.me/{clean.lstrip('+')}"
        
        return {
            "ok": True,
            "number": clean,
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "country": country or "India",
            "operator": operator,
            "timezones": ", ".join(tz_list),
            "wa_link": wa_link,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def lookup_ifsc(code: str) -> dict:
    """Razorpay IFSC API lookup"""
    clean = re.sub(r"[^A-Za-z0-9]", "", code).upper()
    url = f"https://ifsc.razorpay.com/{clean}"
    try:
        r = requests.get(url, headers=UA_HEADERS, timeout=5)
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
                "state": d.get("STATE", ""),
                "micr": d.get("MICR", "N/A"),
                "upi": "✅ Supported" if d.get("UPI") else "❌ No",
                "neft": "✅ Supported" if d.get("NEFT") else "❌ No",
                "imps": "✅ Supported" if d.get("IMPS") else "❌ No",
                "maps_link": f"https://maps.google.com/?q={maps_q}",
            }
        return {"ok": False, "error": "IFSC code not found in RBI database"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def lookup_pincode(pincode: str) -> dict:
    """India Post Pincode API lookup"""
    clean = re.sub(r"[^\d]", "", pincode)
    if len(clean) != 6:
        return {"ok": False, "error": "Pincode must be 6 digits"}
    url = f"https://api.postalpincode.in/pincode/{clean}"
    try:
        r = requests.get(url, headers=UA_HEADERS, timeout=6)
        if r.status_code == 200:
            data = r.json()
            if data and data[0].get("Status") == "Success":
                po_list = data[0].get("PostOffice", [])
                primary = po_list[0] if po_list else {}
                names = [p.get("Name") for p in po_list[:8]]
                return {
                    "ok": True,
                    "pincode": clean,
                    "district": primary.get("District", ""),
                    "state": primary.get("State", ""),
                    "division": primary.get("Division", ""),
                    "circle": primary.get("Circle", ""),
                    "post_offices": ", ".join(names),
                    "total_offices": len(po_list),
                }
        return {"ok": False, "error": "Pincode not found"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def lookup_ip_domain(target: str) -> dict:
    """IP & Domain WHOIS / Geolocation lookup"""
    clean = re.sub(r"^https?://", "", target).split("/")[0].strip()
    url = f"http://ip-api.com/json/{clean}"
    try:
        r = requests.get(url, headers=UA_HEADERS, timeout=5)
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
                    "region": d.get("regionName", "N/A"),
                    "city": d.get("city", "N/A"),
                    "timezone": d.get("timezone", "N/A"),
                    "as": d.get("as", "N/A"),
                }
        return {"ok": False, "error": "Domain or IP info could not be retrieved"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_username_platforms(username: str) -> dict:
    """Checks social media presence across popular platforms"""
    u = username.lstrip("@").strip()
    platforms = [
        {"name": "GitHub", "url": f"https://github.com/{u}"},
        {"name": "Telegram", "url": f"https://t.me/{u}"},
        {"name": "Instagram", "url": f"https://instagram.com/{u}"},
        {"name": "Twitter / X", "url": f"https://x.com/{u}"},
        {"name": , "url": f"https:/user/{u}"},
        {"name": , "url": f"https:/{u}"},
    ]
    return {"ok": True, "username": u, "platforms": platforms}
