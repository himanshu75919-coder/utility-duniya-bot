# -*- coding: utf-8 -*-
"""
Sarkari Seva & Student Exam Hub
Verified 100% Direct Official Government Portals & Student Exam Links.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 🏛️ CITIZEN SERVICES
SARKARI_CITIZEN_TEXT = (
    "🏛️ <b>SARKARI SEVA PORTAL HUB</b> 🏛️\n"
    "<blockquote>100% verified official government portal — direct link, no fake ads.</blockquote>\n\n"
    "📌 <b>Kaun si service chahiye:</b>\n"
    "• 💳 <b>Aadhaar:</b> Download, PVC Card, Mobile link & lock\n"
    "• 🪪 <b>PAN Card:</b> 10-Min Free e-PAN, Link Status & Apply\n"
    "• 🍚 <b>Ration & Ayushman:</b> NFSA Portal & ABHA Health Card\n"
    "• 🚗 <b>Parivahan:</b> Driving License, RC & e-Challan\n"
    "• 🎓 <b>APAAR ID:</b> One Nation One Student ID Portal\n"
    "• 📜 <b>State Portals:</b> RTPS Bihar, UP e-District, Jharsewa\n"
    "• 💼 <b>EPFO / PF:</b> UAN Passbook & Online Claim\n\n"
    "👉 Tap a button below to open the official portal:"
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


STATE_PORTALS_TEXT = (
    "📜 <b>RAJYA-WISE JAATI, AAY AUR NIVAS Praman-Patra PORTAL</b>\n\n"
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
