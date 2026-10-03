# -*- coding: utf-8 -*-
"""
VIP Premium & Automated UPI Payment System
Dynamic QR generation, plan selection, payment proof submission, and 1-tap admin approval with multi-duration plans.
"""

import io
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.general_tools import make_qr_bytes, build_upi_link

VIP_PLANS = {
    "plan_30": {"name": "💎 30 Days VIP (1 Month)", "days": 30, "price": 49},
    "plan_60": {"name": "⚡ 60 Days VIP (2 Months)", "days": 60, "price": 89},
    "plan_90": {"name": "🚀 90 Days VIP (3 Months)", "days": 90, "price": 129},
    "plan_120": {"name": "🔥 120 Days VIP (4 Months)", "days": 120, "price": 169},
    "plan_life": {"name": "👑 Lifetime All-Access VIP", "days": 99999, "price": 199},
}


def get_premium_plans_kb():
    buttons = [
        [InlineKeyboardButton("💎 30 Days (1 Month) — ₹49", callback_data="buy_plan_30")],
        [InlineKeyboardButton("⚡ 60 Days (2 Months) — ₹89", callback_data="buy_plan_60")],
        [InlineKeyboardButton("🚀 90 Days (3 Months) — ₹129", callback_data="buy_plan_90")],
        [InlineKeyboardButton("🔥 120 Days (4 Months) — ₹169", callback_data="buy_plan_120")],
        [InlineKeyboardButton("👑 Lifetime VIP — ₹199", callback_data="buy_plan_life")],
        [InlineKeyboardButton("🎁 Refer Friends = 30 Days Free", callback_data="open_refer_menu")],
        [InlineKeyboardButton("💬 Contact Support (@Supermannn_x)", url="https://t.me/Supermannn_x")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(buttons)


def generate_plan_payment_qr(upi_id: str, upi_name: str, plan_key: str, uid: int) -> tuple[io.BytesIO, str, int]:
    plan = VIP_PLANS.get(plan_key, VIP_PLANS["plan_30"])
    amt = plan["price"]
    note = f"VIP-{uid}-{plan_key}"
    upi_link = build_upi_link(upi_id, upi_name, amt=amt, note=note)
    qr_buf = make_qr_bytes(upi_link)
    return qr_buf, plan["name"], amt


def get_payment_admin_kb(uid: int, plan_key: str):
    buttons = [
        [
            InlineKeyboardButton("✅ 30 Days", callback_data=f"adm_appr_{uid}_30"),
            InlineKeyboardButton("✅ 60 Days", callback_data=f"adm_appr_{uid}_60"),
        ],
        [
            InlineKeyboardButton("✅ 90 Days", callback_data=f"adm_appr_{uid}_90"),
            InlineKeyboardButton("✅ 120 Days", callback_data=f"adm_appr_{uid}_120"),
        ],
        [
            InlineKeyboardButton("👑 Lifetime", callback_data=f"adm_appr_{uid}_99999"),
            InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{uid}"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)
