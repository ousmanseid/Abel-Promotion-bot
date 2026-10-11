"""
Keyboards for browsing platforms and services.
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Service
from utils.localization import t

def get_platform_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Generate platform selection inline keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("platform_instagram", lang=lang), callback_data="svc_plat:Instagram"),
                InlineKeyboardButton(text=t("platform_facebook", lang=lang), callback_data="svc_plat:Facebook"),
            ],
            [
                InlineKeyboardButton(text=t("platform_youtube", lang=lang), callback_data="svc_plat:YouTube"),
            ],
            [
                InlineKeyboardButton(text=t("btn_main_menu", lang=lang), callback_data="nav_main_menu")
            ]
        ]
    )

def get_services_list_keyboard(services: List[Service], platform: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Generate inline buttons for each service under a platform."""
    buttons = []
    for svc in services:
        name = svc.get_name(lang)
        price_text = f"{int(svc.price) if svc.price.is_integer() else svc.price} ETB"
        label = f"{name} - {price_text}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"svc_view:{svc.id}")])

    # Navigation row
    nav_row = [
        InlineKeyboardButton(text=t("btn_back", lang=lang), callback_data="svc_platforms"),
        InlineKeyboardButton(text=t("btn_main_menu", lang=lang), callback_data="nav_main_menu")
    ]
    buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_service_detail_keyboard(service_id: int, platform: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Action buttons on viewing a specific service."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_select_service", lang=lang), callback_data=f"svc_order:{service_id}")
            ],
            [
                InlineKeyboardButton(text=t("btn_back", lang=lang), callback_data=f"svc_plat:{platform}"),
                InlineKeyboardButton(text=t("btn_main_menu", lang=lang), callback_data="nav_main_menu")
            ]
        ]
    )
