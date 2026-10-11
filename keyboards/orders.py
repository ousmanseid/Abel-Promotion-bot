"""
Keyboards for customer ordering and order tracking.
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Order
from utils.localization import t, get_status_display

def get_order_confirm_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Confirmation buttons before placing an order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_confirm_order", lang=lang), callback_data="ord_do_confirm"),
                InlineKeyboardButton(text=t("btn_cancel", lang=lang), callback_data="flow_cancel")
            ]
        ]
    )

def get_orders_list_keyboard(orders: List[Order], lang: str = "en") -> InlineKeyboardMarkup:
    """Generate keyboard for user's past/current orders."""
    buttons = []
    for ord_obj in orders:
        status_disp = get_status_display(ord_obj.status, lang=lang)
        label = f"#{ord_obj.order_code} - {ord_obj.total_price} ETB ({status_disp})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"ord_view:{ord_obj.id}")])

    buttons.append([
        InlineKeyboardButton(text=t("btn_main_menu", lang=lang), callback_data="nav_main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_order_detail_keyboard(order: Order, lang: str = "en") -> InlineKeyboardMarkup:
    """Action buttons on an order detail view."""
    buttons = []
    # If order is waiting for payment or rejected, allow submitting payment evidence
    if order.status in ("pending_payment", "Awaiting Payment", "rejected", "Payment Rejected"):
        buttons.append([
            InlineKeyboardButton(text=t("btn_submit_payment", lang=lang), callback_data=f"ord_pay:{order.id}")
        ])

    buttons.append([
        InlineKeyboardButton(text=t("btn_support", lang=lang), callback_data=f"ord_support:{order.id}")
    ])
    buttons.append([
        InlineKeyboardButton(text=t("btn_my_orders", lang=lang), callback_data="nav_my_orders"),
        InlineKeyboardButton(text=t("btn_main_menu", lang=lang), callback_data="nav_main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_customer_message_reply_keyboard(order_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """Button provided to customer to reply to an admin support message."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_reply_to_support", lang=lang), callback_data=f"cust_reply_msg:{order_id}")
            ],
            [
                InlineKeyboardButton(text=t("btn_my_orders", lang=lang), callback_data=f"ord_view:{order_id}")
            ]
        ]
    )
