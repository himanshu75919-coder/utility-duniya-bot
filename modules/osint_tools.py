# -*- coding: utf-8 -*-
"""
Phone number lookup (offline, 100% public data) — v108 SLIM
===========================================================
v108: is file me pehle 5 tools the (vehicle RTO, IFSC, pincode, area search,
WHOIS). Wo saare tools bot se PERMANENTLY delete ho gaye, isliye unka code
bhi yahan se hata diya gaya — ab sirf 📱 NUMBER INFO ka offline parser
bacha hai (`lookup_phone_info`), bilkul pehle jaisa.

Fayda: ab ye file na `requests` uthati hai, na `api_hub`, na hub cache —
Render par boot RAM aur bhi kam.
"""

# v107 RAM-SAVER-II — phonenumbers boot par +112 MB RSS khaata tha
# (core 3 MB + carrier 10 MB + GEOCODER 95 MB!). Boot 224 MB → Render free
# 512 MB plan par watchdog thrash + OOM risk. Ab LAZY import: pehli phone
# lookup par ek baar (~1s), output bilkul SAME. Emergency me guard.free_memory
# geocoder wapas drop kar sakta hai (drop_geocoder) — 95 MB turant wapas.
import re
import threading as _thd
_PN_LOCK = _thd.Lock()
phonenumbers = None
geocoder = None
carrier = None
timezone = None
number_type = None
PhoneNumberType = None
PN_LOADED = False


def _pn_load(heavy: bool = True):
    """Lazy loader — core+carrier+timezone ek baar, geocoder (95 MB) bhi ek baar."""
    global phonenumbers, carrier, timezone, number_type, PhoneNumberType
    global geocoder, PN_LOADED
    with _PN_LOCK:
        if phonenumbers is None:
            import phonenumbers as _p
            from phonenumbers import carrier as _ca, timezone as _tz
            phonenumbers = _p
            carrier, timezone = _ca, _tz
            number_type = _p.number_type
            PhoneNumberType = _p.PhoneNumberType
        if heavy and geocoder is None:
            try:
                from phonenumbers import geocoder as _gc
                geocoder = _gc
            except Exception:                                      # noqa: BLE001
                geocoder = None
        PN_LOADED = phonenumbers is not None
    return phonenumbers


def drop_geocoder() -> bool:
    """ Emergency RAM valve: geocoder module (~95 MB) wapas OS ko lautaao.

    guard.free_memory(aggressive) ise tab call karta hai jab safai ke baad bhi
    RAM hard limit ke paas ho. Agli phone lookup par geocoder dobara import
    ho jaata hai (~1s) — result par koi farq nahi (worst case: circle me
    'India' dikhta hai agar import usi din fail ho).
    """
    global geocoder
    import sys as _sys
    with _PN_LOCK:
        if geocoder is None:
            return False
        geocoder = None
        _sys.modules.pop("phonenumbers.geocoder", None)
        import gc as _gcmod
        _gcmod.collect()
        return True


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

    _pn_load()          # v107: lazy phonenumbers (boot RAM bachat)
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

    country = (geocoder.description_for_number(parsed, "en") if geocoder else "") or "India"
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
