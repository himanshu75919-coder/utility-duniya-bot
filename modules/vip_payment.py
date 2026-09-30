# -*- coding: utf-8 -*-
"""
VIP Premium & Automated UPI Payment System
Dynamic QR generation, plan selection, payment proof submission, and 1-tap admin approval.
"""

import io
from urllib.parse import quote
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.general_tools import make_qr_bytes, build_upi_link

VIP_PLANS = {
    "plan_19": {"name": "🎫 Exam & Fast Pass (3 Days)", "days": 3, "price": 19},
    "plan_49": {"name": "💎 Monthly Super VIP (30 Days)", "days": 30, "price": 49},
    "plan_99": {"name": "👑 Lifetime All-Access VIP", "days": 99999, "price": 99},
}


def get_premium_plans_kb():
    buttons = [
        [InlineKeyboardButton("🎫 Exam Pass (3 Days) — ₹19", callback_data="buy_plan_19")],
        [InlineKeyboardButton("💎 Monthly VIP (30 Days) — ₹49", callback_data="buy_plan_49")],
        [InlineKeyboardButton("👑 Lifetime VIP — ₹99", callback_data="buy_plan_99")],
        [InlineKeyboardButton("🎁 Refer Friends = 30 Days Free", callback_data="open_refer_menu")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(buttons)


def generate_plan_payment_qr(upi_id: str, upi_name: str, plan_key: str, uid: int) -> tuple[io.BytesIO, str, int]:
    plan = VIP_PLANS.get(plan_key, VIP_PLANS["plan_49"])
    amt = plan["price"]
    note = f"VIP-{uid}-{plan_key}"
    upi_link = build_upi_link(upi_id, upi_name, amt=amt, note=note)
    qr_buf = make_qr_bytes(upi_link)
    return qr_buf, plan["name"], amt


def get_payment_admin_kb(uid: int, plan_key: str):
    buttons = [
        [
            InlineKeyboardButton("✅ Approve (30 Days)", callback_data=f"adm_appr_{uid}_30"),
            InlineKeyboardButton("👑 Approve (Lifetime)", callback_data=f"adm_appr_{uid}_99999"),
        ],
        [
            InlineKeyboardButton("❌ Reject Payment", callback_data=f"adm_rej_{uid}"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)
