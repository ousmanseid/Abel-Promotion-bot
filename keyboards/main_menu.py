"""
Main menu keyboards for Abel Promotion bot.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.localization import t

def get_main_menu_keyboard(lang: str = "en", is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Generate reply keyboard for the main menu based on language and admin status."""
    keyboard = [
        [
            KeyboardButton(text=t("btn_services", lang=lang)),
            KeyboardButton(text=t("btn_place_order", lang=lang))
        ],
        [
            KeyboardButton(text=t("btn_my_orders", lang=lang)),
            KeyboardButton(text=t("btn_payment_methods", lang=lang))
        ],
        [
            KeyboardButton(text=t("btn_my_profile", lang=lang)),
            KeyboardButton(text=t("btn_help", lang=lang))
        ],
        [
            KeyboardButton(text=t("btn_support", lang=lang)),
            KeyboardButton(text=t("btn_change_language", lang=lang))
        ]
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin Panel / አስተዳዳሪ")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )

def get_cancel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Simple inline cancel button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_cancel", lang=lang), callback_data="flow_cancel")]
        ]
    )

def get_skip_and_cancel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Inline keyboard with Skip and Cancel."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_skip", lang=lang), callback_data="flow_skip"),
                InlineKeyboardButton(text=t("btn_cancel", lang=lang), callback_data="flow_cancel")
            ]
        ]
    )
