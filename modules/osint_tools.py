# -*- coding: utf-8 -*-
"""
Smart OSINT & Digital Investigation Hub — v32 PRO
=================================================
Vehicle RTO, Phone Carrier/Circle, IFSC Bank Branch, Pincode (+ area-name search).

NOTE: Default me sirf PUBLIC / lawful sources use hote hain (telecom carrier+circle, bank branch,
pin code, IP geo).
"""

import re
from urllib.parse import quote as _quote

from modules.core.net import NetError, http_get

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
    # v71.1: Bihar ke saare RTO (user ka BR30AR0802 -> BR30 = Sitamarhi)
    "BR03": "Ara (Bhojpur)", "BR04": "Chhapra (Saran)", "BR05": "Motihari (Champaran)",
    "BR08": "Munger", "BR09": "Begusarai", "BR11": "Purnia", "BR12": "Saharsa",
    "BR13": "Sasaram (Rohtas)", "BR14": "Hajipur (Vaishali)", "BR15": "Siwan",
    "BR16": "Khagaria", "BR17": "Samastipur", "BR18": "Bettiah", "BR19": "Chapra",
    "BR20": "Jamui", "BR21": "Araria", "BR22": "Madhubani", "BR23": "Sitamarhi",
    "BR24": "Buxar", "BR25": "Jehanabad", "BR26": "Nawada", "BR27": "Jamalpur",
    "BR28": "Gopalganj", "BR29": "Sheikhpura", "BR30": "Sitamarhi",
    "BR31": "Sheohar", "BR32": "Arwal", "BR33": "Kishanganj", "BR34": "Kaimur (Bhabua)",
    "BR35": "Katihar", "BR36": "Supaul", "BR37": "Madhepura", "BR38": "Saharsa",
    "BR39": "Bhagalpur", "BR43": "Nalanda (Biharsharif)", "BR44": "Lakhisarai",
    "BR45": "Aurangabad", "BR46": "Bankura", "BR50": "Muzaffarpur",
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
    plate = plate if isinstance(plate, str) else ("" if plate is None else str(plate))  # v78
    clean = re.sub(r"[^A-Za-z0-9]", "", plate).upper()
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
    number_str = number_str if isinstance(number_str, str) else ("" if number_str is None else str(number_str))  # v78
    clean = re.sub(r"[^\d+]", "", number_str)
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
    code = code if isinstance(code, str) else ("" if code is None else str(code))  # v78
    clean = re.sub(r"[^A-Za-z0-9]", "", code).upper()
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
        r = http_get(f"https://ifsc.razorpay.com/{clean}", headers=UA_HEADERS, timeout=8)
        if r.status_code == 200:
            d = r.json()
            maps_q = _quote(f"{d.get('BANK')} {d.get('BRANCH')} {d.get('ADDRESS')}")
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
    except NetError:
        return {"ok": False, "error": "IFSC server ne jawab dene me time laga diya. Thodi der baad try karo."}
    except Exception as e:
        return {"ok": False, "error": f"API busy hai: {str(e)[:80]}"}


# =====================================================================================
# PINCODE (+ area-name search)
# =====================================================================================
def lookup_pincode(pincode: str) -> dict:
    """India Post API — district, state, taluk, division + map link."""
    pincode = pincode if isinstance(pincode, str) else ("" if pincode is None else str(pincode))  # v78
    clean = re.sub(r"[^\d]", "", pincode)
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
        r = http_get(f"https://api.postalpincode.in/pincode/{clean}", headers=UA_HEADERS, timeout=8)
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
                    "maps_link": f"https://maps.google.com/?q={_quote(primary.get('District', '') + ' ' + primary.get('State', ''))}",
                }
                _cput("pin:" + clean, out, 604800)   # pincode data saal bhar same — 7 din
                return out
        return {"ok": False,
                "error": (f"Pincode <code>{clean}</code> India Post database me nahi mila.\n"
                          "📌 Sahi 6-digit pincode bhejo, jaise <code>800001</code> (Patna GPO)")}
    except NetError:
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
    area = area if isinstance(area, str) else ("" if area is None else str(area))  # v86: junk-proof
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
            r = http_get(
                f"https://api.postalpincode.in/postoffice/{_quote(variant)}",
                headers=UA_HEADERS, timeout=8)
        except NetError:
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
# 🌐 WEBSITE OWNER X-RAY  (v70)  — RDAP = sarkari/registry ka PUBLIC domain record
# =====================================================================================
# Ye "WHOIS" ka naya (RDAP) version hai — domain kiska naam par hai, kab bana,
# kab khatam, kaun registrar, kaunse nameserver. Sab public registry se aata hai
# (jaisa registry ke apne page par hota hai). Owner ka naam registry khud aksar
# chhupa deti hai — hum jhooth nahi bolte, jo milta hai wahi dikhate hain.
import re as _re70

_RDAP_URL = "https://rdap.org/domain/{d}"
_WHOIS_DOMAIN_RE = _re70.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$")


def _clean_domain(domain: str) -> str:
    """'https://www.XyzShop.in/page?x=1' → 'xyzshop.in'"""
    d = str(domain or "").strip().lower()
    d = _re70.sub(r"^[a-z]+://", "", d)          # https:// hatao
    d = d.split("/")[0].split("?")[0].split("#")[0]
    d = d.split("@")[-1]                          # user@domain
    d = _re70.sub(r"^www\.", "", d)
    d = d.rstrip(".").replace(" ", "")
    if ":" in d:
        d = d.split(":")[0]
    if any(ord(ch) > 127 for ch in d):            # Hindi/IDN → punycode
        try:
            d = d.encode("idna").decode("ascii")
        except Exception:                         # noqa: BLE001
            pass
    return d


def _fmt_date(iso: str) -> str:
    """'2026-07-29T04:00:00Z' → '29-07-2026' (bukha nahi to '')."""
    m = _re70.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def _age_of(iso: str) -> str:
    """'2019-03-12...' → '6 saal 6 mahine'"""
    from datetime import date
    m = _re70.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    if not m:
        return ""
    try:
        b = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return ""
    t = date.today()
    if b > t:
        return ""
    mo = (t.year - b.year) * 12 + (t.month - b.month) - (1 if t.day < b.day else 0)
    y, mo = divmod(mo, 12)
    parts = ([f"{y} saal"] if y else []) + ([f"{mo} mahine"] if mo else [])
    return " ".join(parts) or "1 mahine se kam"


def _days_left(iso: str) -> int | None:
    from datetime import date
    m = _re70.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    if not m:
        return None
    try:
        e = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None
    return (e - date.today()).days


_STATUS_HING = {
    "active": "✅ active",
    "client transfer prohibited": "🔒 transfer locked (safe)",
    "client delete prohibited": "🔒 delete locked (safe)",
    "client renew prohibited": "🔒 renew locked",
    "client update prohibited": "🔒 update locked",
    "client hold": "⚠️ hold (domain band ho sakta hai)",
    "pending delete": "⛔ delete hone wala hai",
    "pending transfer": "🔄 transfer chal raha hai",
    "pending renew": "🔄 renew chal raha hai",
    "server hold": "⚠️ server hold",
    "inactive": "⚠️ inactive",
    "redemption period": "⛔ redemption (chhoot gaya hai)",
}


def _vcard_name(ent: dict) -> str:
    """entity ke vcard se naam nikaalo (registrar/registrant)."""
    try:
        for it in (ent.get("vcardArray") or [None, []])[1]:
            if isinstance(it, list) and it and str(it[0]).lower() in ("fn", "org", "name"):
                if len(it) >= 4 and str(it[3]).strip():
                    return _clean_name_basic(str(it[3]))
    except Exception:                                     # noqa: BLE001
        pass
    return ""


def _clean_name_basic(t: str) -> str:
    t = _re70.sub(r"\s+", " ", str(t or "")).strip()
    return t[:80]


def parse_rdap(data: dict, domain: str = "", ms: int = 0) -> dict:
    """RDAP JSON → bot ka samajh wala shape (test ke liye alag rakha hai)."""
    data = data if isinstance(data, dict) else {}
    dom = str(data.get("ldhName") or domain or "").lower()

    registrar = ""
    registrant = ""
    for ent in (data.get("entities") or []):
        if not isinstance(ent, dict):
            continue
        roles = [str(r).lower() for r in (ent.get("roles") or [])]
        nm = _vcard_name(ent)
        if "registrar" in roles and not registrar:
            registrar = nm or registrar
        if ("registrant" in roles or "administrative" in roles or "technical" in roles) \
                and not registrant and nm:
            registrant = nm

    ev = {}
    for e in (data.get("events") or []):
        if isinstance(e, dict) and e.get("eventAction"):
            ev[str(e["eventAction"]).lower()] = str(e.get("eventDate") or "")

    created = ev.get("registration") or ev.get("registered") or ""
    expires = ev.get("expiration") or ""
    changed = ev.get("last changed") or ev.get("last update of rdap database") or ""

    nss = []
    for ns in (data.get("nameservers") or []):
        if isinstance(ns, dict):
            nm = str(ns.get("ldhName") or ns.get("unicodeName") or "").lower().rstrip(".")
            if nm:
                nss.append(nm)

    st_raw = [str(x) for x in (data.get("status") or [])]
    st_h = [_STATUS_HING.get(x.lower(), x) for x in st_raw]

    if not dom:
        return {"ok": False, "error": "Domain samajh nahi aaya — jaise <code>xyzshop.in</code> bhejo."}

    return {
        "ok": True,
        "domain": dom,
        "registrar": registrar,
        "registrant": registrant,
        "created": created, "created_fmt": _fmt_date(created), "age": _age_of(created),
        "expires": expires, "expires_fmt": _fmt_date(expires),
        "days_left": _days_left(expires),
        "changed": changed, "changed_fmt": _fmt_date(changed),
        "nameservers": nss[:4],
        "status": st_h, "status_raw": st_raw,
        "dnssec": str((data.get("secureDNS") or {}).get("delegationSigned", "")),
        "latency_ms": ms,
    }


def lookup_whois(domain: str) -> dict:
    """Domain ka public record (RDAP) — kabhi raise nahi karta, hamesha dict."""
    d = _clean_domain(domain)
    if not d or not _WHOIS_DOMAIN_RE.match(d) or "." not in d:
        return {"ok": False,
                "error": ("Ye domain sahi nahi lagta. Aise bhejo: <code>xyzshop.in</code> "
                          "ya <code>example.com</code> (poora link bhi chalega).")}

    _ck = "whois:" + d
    try:
        hit = _cget(_ck)
        if hit:
            hit = dict(hit)
            hit["cached"] = True
            return hit
    except Exception:                                     # noqa: BLE001
        pass

    import time as _t70
    import requests as _rq70
    t0 = _t70.time()
    try:
        r = _rq70.get(_RDAP_URL.format(d=d), timeout=20,
                         headers={"Accept": "application/rdap+json",
                                  "User-Agent": "UtilityDuniyaBot/1.0"})
    except Exception as e:                                # noqa: BLE001
        return {"ok": False, "error": f"Registry tak baat nahi pahunchi ({str(e)[:60]}). Dobara try karo."}

    ms = int((_t70.time() - t0) * 1000)
    if r.status_code == 404:
        return {"ok": False, "error": ("Is domain ka public record nahi mila — spelling check karo "
                                       "(ya ye TLD RDAP me nahi hai).")}
    if r.status_code != 200:
        return {"ok": False, "error": f"Registry ne jawab nahi diya (HTTP {r.status_code}). Thodi der baad try karo."}
    try:
        data = r.json()
    except Exception:                                     # noqa: BLE001
        return {"ok": False, "error": "Registry ka jawab samajh nahi aaya — dobara try karo."}

    out = parse_rdap(data, d, ms)
    if out.get("ok"):
        try:
            if _CACHED:
                _INFO.set(_ck, out, ttl=3600)             # 1 ghanta — record din bhar same
        except Exception:                                 # noqa: BLE001
            pass
    return out
