# -*- coding: utf-8 -*-
"""
🇮🇳 INDIA BOARD REGISTRY (v74.1)
================================
User ka order (8 Oct 2026): "Result Check tool me India ke SAARE official
state boards ke alag-alag service banao — CBSE, BSEB, UP, Telangana...
aur har board ka OFFICIAL LOGO dikhe taaki users apna board pehchaan sake.
Bilkul advanced, koi galti nahi, 100% trusted."

Har board ka alag entry:
  • naam (English + short) + state
  • OFFICIAL result portal ka link
  • exam types (10th/12th/other)
  • kya chahiye (roll no / roll code / DOB / captcha)
  • status:
      "live"   → bot OFFICIAL server se seedha result laata hai (abhi BSEB)
      "portal" → official portal ka link + poore steps (login/captcha wahan)
  • logo: assets/logos/norm_*.jpg (official, unki hi website se) — jahan
    nahi mila wahan bot khud ka COLOR BADGE (initials) banata hai.

⚠️ Emaandari (user ka "life ka sawaal hai"):
  Jis board ka result bot seedha NAHI laa sakta, wahan hum JHOOTHA result
  kabhi nahi dikhayenge — sirf official portal ka link + sahi steps denge.
"""

import os
import re

_LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "assets", "logos")

# ─────────────────────────────────────────────────────── board registry
# status:  live = bot khud laata hai | portal = official portal link + steps
BOARDS = {
    # ---------------------------------------------------------- BIHAR (LIVE)
    "bseb": {
        "name": "Bihar School Examination Board",
        "short": "BSEB (Bihar Board)",
        "hi": "बिहार विद्यालय परीक्षा समिति",
        "state": "Bihar", "flag": "🟢",
        "portal": "https://result.biharboardonline.org/",
        "portal2": "https://biharboardonline.bihar.gov.in/",
        "exams": ["Matric (10th)", "Inter (12th)", "Inter Spl/Compartmental"],
        "need": ["Roll Code", "Roll Number"],
        "status": "live",
        "logo": "norm_bseb_live.jpg",
        "color": (139, 26, 26),
        "note": "LIVE ✅",
    },
    "bbose": {
        "name": "Bihar Board of Open Schooling & Examination",
        "short": "BBOSE (Bihar Open)",
        "hi": "बिहार मुक्त विद्यालयी शिक्षा परिषद",
        "state": "Bihar", "flag": "⚪",
        "portal": "https://bbose.org/",
        "portal2": "https://interbiharboard.com/BBOSE-26/",
        "exams": ["Secondary (10th)", "Senior Secondary (12th)"],
        "need": ["Roll Number", "Registration No"],
        "status": "portal",
        "logo": None, "color": (120, 53, 15),
    },
    # ---------------------------------------------------------- CENTRAL
    "cbse": {
        "name": "Central Board of Secondary Education",
        "short": "CBSE",
        "hi": "केंद्रीय माध्यमिक शिक्षा बोर्ड",
        "state": "All India", "flag": "🔵",
        "portal": "https://results.digilocker.gov.in/",
        "portal2": "https://cbse.gov.in/",
        "exams": ["Class 10", "Class 12"],
        "need": ["Mobile OTP", "Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (16, 88, 200),
        "note": "",
    },
    "cisce": {
        "name": "Council for Indian School Certificate Examinations",
        "short": "CISCE (ICSE / ISC)",
        "hi": "सी.आई.एस.सी.ई",
        "state": "All India", "flag": "🔵",
        "portal": "https://results.cisce.org/",
        "portal2": "https://cisce.org/",
        "exams": ["ICSE (10th)", "ISC (12th)"],
        "need": ["Unique ID", "Index Number"],
        "status": "portal",
        "logo": None, "color": (30, 58, 138),
    },
    "nios": {
        "name": "National Institute of Open Schooling",
        "short": "NIOS",
        "hi": "राष्ट्रीय मुक्त विद्यालयी शिक्षा संस्थान",
        "state": "All India", "flag": "🔵",
        "portal": "https://results.nios.ac.in/",
        "portal2": "https://www.nios.ac.in/",
        "exams": ["Secondary", "Senior Secondary"],
        "need": ["Enrollment Number"],
        "status": "portal",
        "logo": None, "color": (5, 90, 60),
    },
    # ---------------------------------------------------------- UP
    "upmsp": {
        "name": "Uttar Pradesh Madhyamik Shiksha Parishad",
        "short": "UP Board (UPMSP)",
        "hi": "माध्यमिक शिक्षा परिषद, उत्तर प्रदेश",
        "state": "Uttar Pradesh", "flag": "🟠",
        "portal": "https://results.upmsp.edu.in/",
        "portal2": "https://upmsp.edu.in/",
        "exams": ["High School (10th)", "Intermediate (12th)"],
        "need": ["Roll Number"],
        "status": "portal",
        "logo": "norm_up_live.jpg", "color": (180, 83, 9),
    },
    # ---------------------------------------------------------- EAST
    "jac": {
        "name": "Jharkhand Academic Council",
        "short": "JAC (Jharkhand)",
        "hi": "झारखंड अधिविद्य परिषद",
        "state": "Jharkhand", "flag": "🟡",
        "portal": "https://jac.jharkhand.gov.in/",
        "portal2": "https://jacresults.com/",
        "exams": ["Matric (10th)", "Inter (12th)"],
        "need": ["Roll Code", "Roll Number"],
        "status": "portal",
        "logo": "norm_jac_live.jpg", "color": (202, 138, 4),
    },
    "wbbse": {
        "name": "West Bengal Board of Secondary Education",
        "short": "WB Board (Madhyamik)",
        "hi": "पश्चिम बंगाल माध्यमिक शिक्षा बोर्ड",
        "state": "West Bengal", "flag": "🟡",
        "portal": "https://wbresults.nic.in/",
        "portal2": "https://wbbse.wb.gov.in/",
        "exams": ["Madhyamik (10th)", "Higher Secondary (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (161, 98, 7),
    },
    "odisha": {
        "name": "Board of Secondary Education, Odisha",
        "short": "BSE Odisha",
        "hi": "माध्यमिक शिक्षा बोर्ड, ओडिशा",
        "state": "Odisha", "flag": "🟤",
        "portal": "https://www.bseodisha.ac.in/",
        "portal2": "https://results.bseodisha.ac.in/",
        "exams": ["HSC (10th)", "CHSE (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": "norm_odisha_live.jpg", "color": (124, 45, 18),
    },
    "assam": {
        "name": "SEBA / AHSEC Assam",
        "short": "Assam (SEBA / AHSEC)",
        "hi": "असम माध्यमिक शिक्षा बोर्ड",
        "state": "Assam", "flag": "🟤",
        "portal": "https://resultsassam.nic.in/",
        "portal2": "https://sebaonline.org/",
        "exams": ["HSLC (10th)", "HS (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (21, 94, 117),
    },
    # ---------------------------------------------------------- NORTH
    "pseb": {
        "name": "Punjab School Education Board",
        "short": "PSEB (Punjab)",
        "hi": "पंजाब स्कूल शिक्षा बोर्ड",
        "state": "Punjab", "flag": "🟡",
        "portal": "https://www.pseb.ac.in/",
        "portal2": "https://results.pseb.ac.in/",
        "exams": ["Matric (10th)", "Sr. Secondary (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": "norm_pseb_live.jpg", "color": (180, 83, 9),
    },
    "bseh": {
        "name": "Board of School Education Haryana",
        "short": "BSEH (Haryana)",
        "hi": "हरियाणा विद्यालय शिक्षा बोर्ड",
        "state": "Haryana", "flag": "🟠",
        "portal": "https://bseh.org.in/",
        "portal2": "https://results.bseh.org.in/",
        "exams": ["Matric (10th)", "Sr. Secondary (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": "norm_bseh_live.jpg", "color": (194, 65, 12),
    },
    "hpbose": {
        "name": "Himachal Pradesh Board of School Education",
        "short": "HPBOSE (HP)",
        "hi": "हिमाचल प्रदेश विद्यालय शिक्षा बोर्ड",
        "state": "Himachal", "flag": "🔵",
        "portal": "https://hpbose.org/",
        "portal2": "https://results.hpbose.org/",
        "exams": ["Matric (10th)", "Plus Two (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": "norm_hpbose_live.jpg", "color": (30, 64, 175),
    },
    "ubse": {
        "name": "Uttarakhand Board of School Education",
        "short": "UBSE (Uttarakhand)",
        "hi": "उत्तराखंड विद्यालयी शिक्षा परिषद",
        "state": "Uttarakhand", "flag": "🔵",
        "portal": "https://ubse.uk.gov.in/",
        "portal2": "https://uaresults.nic.in/",
        "exams": ["High School (10th)", "Intermediate (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (17, 94, 89),
    },
    "jkbose": {
        "name": "Jammu & Kashmir Board of School Education",
        "short": "JKBOSE (J&K)",
        "hi": "जम्मू-कश्मीर विद्यालय शिक्षा बोर्ड",
        "state": "Jammu & Kashmir", "flag": "🔵",
        "portal": "https://jkbose.nic.in/",
        "portal2": "https://jkresults.nic.in/",
        "exams": ["Class 10", "Class 12"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (55, 65, 81),
    },
    "rbse": {
        "name": "Rajasthan Board of Secondary Education",
        "short": "RBSE (Rajasthan)",
        "hi": "माध्यमिक शिक्षा बोर्ड, राजस्थान",
        "state": "Rajasthan", "flag": "🟤",
        "portal": "https://rajresults.nic.in/",
        "portal2": "https://rajeduboard.rajasthan.gov.in/",
        "exams": ["Class 10", "Class 12 (Science/Arts/Commerce)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (154, 52, 18),
    },
    "mpbse": {
        "name": "Madhya Pradesh Board of Secondary Education",
        "short": "MPBSE (MP Board)",
        "hi": "माध्यमिक शिक्षा मंडल, मध्य प्रदेश",
        "state": "Madhya Pradesh", "flag": "🟢",
        "portal": "https://mpbse.nic.in/",
        "portal2": "https://mpresults.nic.in/",
        "exams": ["Class 10", "Class 12"],
        "need": ["Roll Number", "Application Number"],
        "status": "portal",
        "logo": None, "color": (22, 101, 52),
    },
    "cgbse": {
        "name": "Chhattisgarh Board of Secondary Education",
        "short": "CGBSE (Chhattisgarh)",
        "hi": "छत्तीसगढ़ माध्यमिक शिक्षा मंडल",
        "state": "Chhattisgarh", "flag": "🟢",
        "portal": "https://cgbse.nic.in/",
        "portal2": "https://cgresults.nic.in/",
        "exams": ["Class 10", "Class 12"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (15, 118, 110),
    },
    # ---------------------------------------------------------- WEST
    "gseb": {
        "name": "Gujarat Secondary & Higher Secondary Education Board",
        "short": "GSEB (Gujarat)",
        "hi": "ગુજરાત માધ્યમિક અને ઉચ્ચતર માધ્યમિક શિક્ષણ બોર્ડ",
        "state": "Gujarat", "flag": "🟠",
        "portal": "https://www.gseb.org/",
        "portal2": "https://gseb.org/home_new_result.php",
        "exams": ["SSC (10th)", "HSC (12th Science/Commerce)"],
        "need": ["Seat Number", "DOB"],
        "status": "portal",
        "logo": "norm_gseb_live.jpg", "color": (194, 65, 12),
    },
    "maharashtra": {
        "name": "Maharashtra State Board of Secondary & Higher Secondary Education",
        "short": "Maharashtra Board",
        "hi": "महाराष्ट्र राज्य माध्यमिक व उच्च माध्यमिक शिक्षण मंडळ",
        "state": "Maharashtra", "flag": "🟠",
        "portal": "https://mahresult.nic.in/",
        "portal2": "https://mahahsscboard.in/",
        "exams": ["SSC (10th)", "HSC (12th)"],
        "need": ["Roll Number", "Mother's First Name"],
        "status": "portal",
        "logo": None, "color": (153, 27, 27),
    },
    "goa": {
        "name": "Goa Board of Secondary & Higher Secondary Education",
        "short": "Goa Board (GBSHSE)",
        "hi": "गोवा माध्यमिक शिक्षा बोर्ड",
        "state": "Goa", "flag": "🔵",
        "portal": "https://gbshse.gov.in/",
        "portal2": "https://results.gbshse.gov.in/",
        "exams": ["SSC (10th)", "HSSC (12th)"],
        "need": ["Seat Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (30, 64, 175),
    },
    # ---------------------------------------------------------- SOUTH
    "telangana": {
        "name": "Board of Secondary Education Telangana",
        "short": "Telangana Board (BSE)",
        "hi": "తెలంగాణ మాధ్యమిక విద్యా మండలి",
        "state": "Telangana", "flag": "🟠",
        "portal": "https://bse.telangana.gov.in/",
        "portal2": "https://results.cgg.gov.in/",
        "exams": ["SSC (10th)", "Inter (12th, TSBIE)"],
        "need": ["Hall Ticket Number"],
        "status": "portal",
        "logo": None, "color": (194, 65, 12),
    },
    "ap": {
        "name": "Board of Intermediate Education & BSEAP",
        "short": "AP Board (BIEAP)",
        "hi": "ఆంధ్రప్రదేశ్ విద్యా మండలి",
        "state": "Andhra Pradesh", "flag": "🟠",
        "portal": "https://bse.ap.gov.in/",
        "portal2": "https://results.bse.ap.gov.in/",
        "exams": ["SSC (10th)", "Intermediate (12th)"],
        "need": ["Hall Ticket Number"],
        "status": "portal",
        "logo": None, "color": (180, 83, 9),
    },
    "karnataka": {
        "name": "Karnataka School Examination & Assessment Board",
        "short": "Karnataka (KSEAB)",
        "hi": "ಕರ್ನಾಟಕ ಶಾಲಾ ಪರೀಕ್ಷೆ ಮತ್ತು ಮೌಲ್ಯಮಾಪನ ಮಂಡಳಿ",
        "state": "Karnataka", "flag": "🟡",
        "portal": "https://karresults.nic.in/",
        "portal2": "https://kseab.karnataka.gov.in/",
        "exams": ["SSLC (10th)", "PUC (12th, PUE Board)"],
        "need": ["Register Number"],
        "status": "portal",
        "logo": None, "color": (161, 98, 7),
    },
    "tn": {
        "name": "Tamil Nadu Directorate of Government Examinations",
        "short": "Tamil Nadu (DGE)",
        "hi": "தமிழ்நாடு அரசுத் தேர்வுகள் இயக்ககம்",
        "state": "Tamil Nadu", "flag": "🔴",
        "portal": "https://tnresults.nic.in/",
        "portal2": "https://dge.tn.gov.in/",
        "exams": ["10th (SSLC)", "12th (HSC)"],
        "need": ["Register Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (153, 27, 27),
    },
    "kerala": {
        "name": "Kerala Pareeksha Bhavan",
        "short": "Kerala Board",
        "hi": "കേരള പരീക്ഷാ ഭവൻ",
        "state": "Kerala", "flag": "🟢",
        "portal": "https://keralaresults.nic.in/",
        "portal2": "https://pareekshabhavan.kerala.gov.in/",
        "exams": ["SSLC (10th)", "Plus Two (12th)"],
        "need": ["Register Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (20, 83, 45),
    },
    "puducherry": {
        "name": "Puducherry Board (CBSE / TN syllabus)",
        "short": "Puducherry",
        "hi": "पुदुचेरी",
        "state": "Puducherry", "flag": "🔵",
        "portal": "https://tnresults.nic.in/",
        "portal2": "https://www.py.gov.in/",
        "exams": ["10th", "12th"],
        "need": ["Register Number"],
        "status": "portal",
        "logo": None, "color": (30, 64, 175),
    },
    # ---------------------------------------------------------- NORTH-EAST
    "meghalaya": {
        "name": "Meghalaya Board of School Education",
        "short": "MBOSE (Meghalaya)",
        "hi": "मेघालय विद्यालय शिक्षा बोर्ड",
        "state": "Meghalaya", "flag": "🟢",
        "portal": "https://www.mbose.in/",
        "portal2": "https://results.mbose.in/",
        "exams": ["SSLC (10th)", "HSSLC (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": "norm_mbose_live.jpg", "color": (22, 101, 52),
    },
    "nagaland": {
        "name": "Nagaland Board of School Education",
        "short": "NBSE (Nagaland)",
        "hi": "नागालैंड विद्यालय शिक्षा बोर्ड",
        "state": "Nagaland", "flag": "🔵",
        "portal": "https://nbsenl.edu.in/",
        "portal2": "https://results.nbsenl.edu.in/",
        "exams": ["HSLC (10th)", "HSSLC (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (12, 74, 110),
    },
    "tripura": {
        "name": "Tripura Board of Secondary Education",
        "short": "TBSE (Tripura)",
        "hi": "त्रिपुरा माध्यमिक शिक्षा बोर्ड",
        "state": "Tripura", "flag": "🟢",
        "portal": "https://tbse.tripura.gov.in/",
        "portal2": "https://tbresults.tripura.gov.in/",
        "exams": ["Madhyamik (10th)", "HS (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (21, 128, 61),
    },
    "manipur": {
        "name": "Board of Secondary Education Manipur (BOSEM/COHSEM)",
        "short": "Manipur (BOSEM)",
        "hi": "मणिपुर माध्यमिक शिक्षा बोर्ड",
        "state": "Manipur", "flag": "🟢",
        "portal": "https://bsem.nic.in/",
        "portal2": "https://manresults.nic.in/",
        "exams": ["HSLC (10th)", "HSE (12th)"],
        "need": ["Roll Number"],
        "status": "portal",
        "logo": None, "color": (6, 95, 70),
    },
    "mizoram": {
        "name": "Mizoram Board of School Education",
        "short": "MBSE (Mizoram)",
        "hi": "मिज़ोरम विद्यालय शिक्षा बोर्ड",
        "state": "Mizoram", "flag": "🟢",
        "portal": "https://mbse.edu.in/",
        "portal2": "https://mbse.edu.in/results/",
        "exams": ["HSLC (10th)", "HSSLC (12th)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": "norm_mbse_live.jpg", "color": (22, 101, 52),
    },
    "sikkim": {
        "name": "Sikkim Board of Secondary Education",
        "short": "SBSE (Sikkim)",
        "hi": "सिक्किम माध्यमिक शिक्षा बोर्ड",
        "state": "Sikkim", "flag": "🔵",
        "portal": "https://sikkim.gov.in/",
        "portal2": "https://www.sikkimhrdd.org/",
        "exams": ["Class 10", "Class 12"],
        "need": ["Roll Number"],
        "status": "portal",
        "logo": None, "color": (30, 64, 175),
    },
    "arunachal": {
        "name": "Directorate of School Education, Arunachal Pradesh",
        "short": "Arunachal Pradesh",
        "hi": "अरुणाचल प्रदेश",
        "state": "Arunachal", "flag": "🟢",
        "portal": "https://education.arunachal.gov.in/",
        "portal2": "https://cbse.gov.in/",
        "exams": ["Class 10", "Class 12 (CBSE ke saath)"],
        "need": ["Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (21, 94, 117),
    },
}

# pagination order — sabse kaam ke board pehle
# ⚠️ RULE #1: portal/portal2 sirf INTERNAL reference hai — user ko kabhi nahi
# dikhaya jaata (na button me, na text me). User ko sirf bot ke andar ke cards.
ORDER = ["bseb", "cbse", "upmsp", "jac", "maharashtra", "telangana", "karnataka",
         "tn", "rbse", "mpbse", "gseb", "kerala", "wbbse", "odisha", "pseb",
         "bseh", "hpbose", "ubse", "jkbose", "cgbse", "assam", "meghalaya", "mizoram",
         "nagaland", "tripura", "manipur", "goa", "sikkim", "arunachal", "ap",
         "puducherry", "cisce", "nios", "bbose"]

PAGE_SIZE = 6


def total_pages() -> int:
    return (len(ORDER) + PAGE_SIZE - 1) // PAGE_SIZE


def page_boards(page: int):
    """(boards list, page, total_pages) — page 0-based."""
    try:
        page = max(0, min(int(page or 0), total_pages() - 1))
    except Exception:                                            # noqa: BLE001
        page = 0
    start = page * PAGE_SIZE
    keys = ORDER[start:start + PAGE_SIZE]
    return [(k, BOARDS[k]) for k in keys if k in BOARDS], page, total_pages()


def find(query: str):
    """Naam/short/state se board dhoondo (search)."""
    q = re.sub(r"[^a-z0-9]+", " ", str(query or "").lower()).strip()
    if not q:
        return []
    out = []
    for k in ORDER:
        b = BOARDS.get(k) or {}
        hay = " ".join([k, str(b.get("name", "")), str(b.get("short", "")),
                        str(b.get("state", "")), str(b.get("hi", ""))]).lower()
        hay = re.sub(r"[^a-z0-9\u0900-\u097F]+", " ", hay)
        if all(tok in hay for tok in q.split()):
            out.append((k, b))
    return out[:6]


# ─────────────────────────────────────────────────────── logos / badges
def logo_path(key: str):
    """Official logo ka path (mila ho to)."""
    b = BOARDS.get(str(key)) or {}
    lp = b.get("logo")
    if lp:
        full = os.path.join(_LOGO_DIR, lp)
        if os.path.isfile(full):
            return full
    return None


def badge_png(key: str):
    """Jo board ka official logo nahi mila — uske liye color badge banao
    (initials + state). Text hamesha circle ke andar fit hota hai. Fail par None."""
    b = BOARDS.get(str(key)) or {}
    try:
        from PIL import Image, ImageDraw
        from modules.business_tools import _font_obj
    except Exception:                                            # noqa: BLE001
        return None
    try:
        W = H = 512
        col = tuple(b.get("color") or (30, 64, 175))
        img = Image.new("RGB", (W, H), (255, 255, 255))
        dr = ImageDraw.Draw(img)
        dr.ellipse((18, 18, W - 18, H - 18), fill=col)
        dr.ellipse((46, 46, W - 46, H - 46), outline=(255, 255, 255), width=5)

        _short = str(b.get("short") or "")
        _acr = re.match(r"^([A-Z]{3,8})\b", _short.strip())           # JKBOSE / CBSE
        _par = re.search(r"\(([A-Za-z][A-Za-z&./ ]{1,14})\)", _short)  # (DGE) / (SEBA / AHSEC)
        if _acr:
            initials = _acr.group(1)
        elif _par:
            _tok = re.split(r"[^A-Za-z]+", _par.group(1))[0]
            initials = (_tok[:6] if len(_tok) >= 3 else _tok).upper()
        else:
            words = [w for w in re.split(r"[^A-Za-z]+", _short) if w]
            if len(words) >= 2:
                initials = "".join(w[0] for w in words[:4]).upper()
            elif words:
                initials = words[0][:4].upper()
            else:
                initials = "IND"
        if not initials:
            initials = "IND"
        inner = W - 150                                  # safe text area
        f_big = None
        for _sz in (150, 136, 122, 108, 96, 84, 72, 62):
            try:
                f = _font_obj("latin_b", _sz)
            except Exception:                                # noqa: BLE001
                f = None
            if not f:
                break
            try:
                _bb = dr.textbbox((0, 0), initials, font=f)
                if (_bb[2] - _bb[0]) <= inner:
                    f_big = f
                    break
            except Exception:                                # noqa: BLE001
                break
        if f_big:
            try:
                bb = dr.textbbox((0, 0), initials, font=f_big)
                dr.text(((W - (bb[2] - bb[0])) / 2 - bb[0],
                         (H - (bb[3] - bb[1])) / 2 - bb[1] - 46), initials,
                        font=f_big, fill=(255, 255, 255))
            except Exception:                                # noqa: BLE001
                pass
        st = str(b.get("state") or "").strip()[:22]
        if st:
            for _sz2 in (46, 40, 34, 30, 26, 22):
                try:
                    f2 = _font_obj("latin", _sz2)
                except Exception:                            # noqa: BLE001
                    f2 = None
                if not f2:
                    break
                try:
                    _bb2 = dr.textbbox((0, 0), st, font=f2)
                    if (_bb2[2] - _bb2[0]) <= inner:
                        bb2 = _bb2
                        dr.text(((W - (bb2[2] - bb2[0])) / 2 - bb2[0], H - 150),
                                st, font=f2, fill=(255, 255, 255))
                        break
                except Exception:                            # noqa: BLE001
                    break
        import io as _io
        out = _io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception:                                            # noqa: BLE001
        return None


def photo_bytes(key: str):
    """Board card ke liye photo bytes — official logo > badge. (None = text only)"""
    lp = logo_path(key)
    if lp:
        try:
            with open(lp, "rb") as f:
                return f.read()
        except Exception:                                        # noqa: BLE001
            pass
    return badge_png(key)
