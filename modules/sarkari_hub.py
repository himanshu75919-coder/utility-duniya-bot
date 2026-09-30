# -*- coding: utf-8 -*-
"""
Sarkari Seva & Student Exam Hub
Verified 100% Direct Official Government Portals & Student Exam Links.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 🏛️ CITIZEN SERVICES
SARKARI_CITIZEN_TEXT = (
    "🏛️ <b>OFFICIAL GOVERNMENT SERVICES HUB</b> 🏛️\n"
    "<blockquote>Saare 100% verified official Sarkari portals — bina fake ads ke direct link!</blockquote>\n\n"
    "📌 <b>Available Services:</b>\n"
    "• 💳 <b>Aadhaar:</b> Download, PVC Card, Mobile Link & Lock\n"
    "• 🪪 <b>PAN Card:</b> 10-Min Free e-PAN, Link Status & Apply\n"
    "• 🍚 <b>Ration & Ayushman:</b> NFSA Portal & ABHA Health Card\n"
    "• 🚗 <b>Parivahan:</b> Driving License, RC & e-Challan\n"
    "• 🎓 <b>APAAR ID:</b> One Nation One Student ID Portal\n"
    "• 📜 <b>State Portals:</b> RTPS Bihar, UP e-District, Jharsewa\n"
    "• 💼 <b>EPFO / PF:</b> UAN Passbook & Online Claim\n\n"
    "👉 Neeche button dabakar direct official portal kholein:"
)

def get_sarkari_citizen_kb():
    buttons = [
        [
            InlineKeyboardButton("💳 e-Aadhaar Download", url="https://myaadhaar.uidai.gov.in/"),
            InlineKeyboardButton("🪪 Order PVC Aadhaar", url="https://myaadhaar.uidai.gov.in/genricPVC"),
        ],
        [
            InlineKeyboardButton("🆓 10-Min Instant e-PAN", url="https://eportal.incometax.gov.in/iec/foservices/#/pre-login/instant-e-pan"),
            InlineKeyboardButton("🔗 PAN-Aadhaar Link Status", url="https://eportal.incometax.gov.in/iec/foservices/#/pre-login/link-aadhaar-status"),
        ],
        [
            InlineKeyboardButton("🍚 Ration Card (NFSA)", url="https://nfsa.gov.in/portal/ration_card_state_portals_aa"),
            InlineKeyboardButton("🏥 Ayushman / ABHA Card", url="https://abha.abdm.gov.in/abha/v3/"),
        ],
        [
            InlineKeyboardButton("🎓 APAAR Student ID Card", url="https://apaar.education.gov.in/"),
            InlineKeyboardButton("🚗 Parivahan & DL Services", url="https://parivahan.gov.in/parivahan/"),
        ],
        [
            InlineKeyboardButton("🚦 Check e-Challan Status", url="https://echallan.parivahan.gov.in/"),
            InlineKeyboardButton("💼 EPFO Passbook & Claim", url="https://passbook.epfindia.gov.in/MemberPassBook/Login"),
        ],
        [
            InlineKeyboardButton("🌾 PM Kisan Status & KYC", url="https://pmkisan.gov.in/"),
            InlineKeyboardButton("📜 State e-District Portals", callback_data="sarkari_state_list"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_home"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


# 🎓 STUDENT EXAM HUB
STUDENT_EXAM_TEXT = (
    "🎓 <b>STUDENT EXAM & SARKARI RESULT HUB</b> 🎓\n"
    "<blockquote>Har govt exam ka official notification, live admit card aur answer keys!</blockquote>\n\n"
    "📌 <b>Major Portals:</b>\n"
    "• 🏛️ <b>SSC:</b> CGL, CHSL, MTS, GD, CPO, Steno\n"
    "• 🚂 <b>Railway RRB:</b> NTPC, Group D, ALP, Tech\n"
    "• 🎖️ <b>Defence:</b> Army Agniveer, NDA, CDS, Airforce\n"
    "• 👮 <b>State Police & SSC:</b> Bihar, UP, MP, Rajasthan\n"
    "• 🏦 <b>Banking:</b> IBPS PO/Clerk, SBI, RBI\n"
    "• 👨‍🏫 <b>Teaching:</b> CTET, State TET, KVS, NVS\n\n"
    "👉 Direct official board portals 👇"
)

def get_student_exam_kb():
    buttons = [
        [
            InlineKeyboardButton("🏛️ SSC Official Portal", url="https://ssc.gov.in/"),
            InlineKeyboardButton("🚂 Railway RRB Portal", url="https://www.rrbapply.gov.in/"),
        ],
        [
            InlineKeyboardButton("🎖️ Army Agniveer Join", url="https://joinindianarmy.nic.in/"),
            InlineKeyboardButton("⚔️ UPSC Official Portal", url="https://upsc.gov.in/"),
        ],
        [
            InlineKeyboardButton("🏦 IBPS Banking Portal", url="https://ibps.in/"),
            InlineKeyboardButton("👨‍🏫 CTET Exam Portal", url="https://ctet.nic.in/"),
        ],
        [
            InlineKeyboardButton("📊 Sarkari Result Official", url="https://www.sarkariresult.com/"),
            InlineKeyboardButton("📋 Official Answer Keys", url="https://www.sarkariresult.com/answerkey/"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_home"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


STATE_PORTALS_TEXT = (
    "📜 <b>STATE-WISE CASTE, INCOME & RESIDENCE CERTIFICATE PORTALS</b>\n\n"
    "• <b>Bihar:</b> RTPS Service Plus (rtps.bihar.gov.in)\n"
    "• <b>Uttar Pradesh:</b> eDistrict UP (edistrict.up.gov.in)\n"
    "• <b>Jharkhand:</b> Jharsewa (jharsewa.jharkhand.gov.in)\n"
    "• <b>Madhya Pradesh:</b> MP e-District / Lok Seva Kendra\n"
    "• <b>Rajasthan:</b> E-Mitra Rajasthan\n"
    "• <b>Maharashtra:</b> Aaple Sarkar Portal\n\n"
    "👉 Select your state:"
)

def get_state_portals_kb():
    buttons = [
        [
            InlineKeyboardButton("🔴 Bihar RTPS", url="https://serviceonline.bihar.gov.in/"),
            InlineKeyboardButton("🟢 UP e-District", url="https://edistrict.up.gov.in/"),
        ],
        [
            InlineKeyboardButton("🔵 Jharkhand Jharsewa", url="https://jharsewa.jharkhand.gov.in/"),
            InlineKeyboardButton("🟡 MP Lok Seva", url="http://mpedistrict.gov.in/"),
        ],
        [
            InlineKeyboardButton("🟣 Rajasthan E-Mitra", url="https://emitra.rajasthan.gov.in/"),
            InlineKeyboardButton("🟠 Maharashtra Aaple", url="https://aaplesarkar.mahaonline.gov.in/"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Citizen Hub", callback_data="sarkari_citizen"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)
