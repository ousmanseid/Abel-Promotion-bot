"""
Keyboards for payment processing and evidence submission.
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import PaymentMethod
from utils.localization import t

def get_payment_methods_keyboard(order_id: int, methods: List[PaymentMethod], lang: str = "en") -> InlineKeyboardMarkup:
    """Buttons to choose payment method for a specific order."""
    buttons = []
    for m in methods:
        icon = "🏦" if m.method_code == "cbe" else "📱"
        label = f"{icon} {m.method_name}"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"pay_select:{m.method_code}:{order_id}")
        ])

    buttons.append([
        InlineKeyboardButton(text=t("btn_cancel", lang=lang), callback_data="flow_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_instruction_keyboard(order_id: int, method_code: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Action buttons after reading payment instructions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_submit_payment", lang=lang), callback_data=f"pay_submit:{order_id}:{method_code}")
            ],
            [
                InlineKeyboardButton(text=t("btn_back", lang=lang), callback_data=f"ord_pay:{order_id}"),
                InlineKeyboardButton(text=t("btn_main_menu", lang=lang), callback_data="nav_main_menu")
            ]
        ]
    )
