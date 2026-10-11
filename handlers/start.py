"""
Start handler for Abel Promotion bot.
Handles /start command, first-time user greeting, and language selection.
"""

from aiogram import Router, types
from aiogram.filters import CommandStart
from database.repositories import UserRepository, AdminRepository
from database.models import User
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.language import get_language_keyboard
from utils.localization import t

router = Router(name="start_router")

@router.message(CommandStart())
async def handle_start(message: types.Message, user: User, lang: str):
    """Handle /start command."""
    is_adm = await AdminRepository.is_admin(message.from_user.id)

    # If first time or language unchosen, prompt to pick language
    if not user.language:
        await message.answer(
            text=t("choose_language", lang="en"),
            reply_markup=get_language_keyboard(),
            parse_mode="Markdown"
        )
        return

    welcome_text = t("welcome", lang=lang)
    reply_kb = get_main_menu_keyboard(lang=lang, is_admin=is_adm)
    await message.answer(text=welcome_text, reply_markup=reply_kb, parse_mode="Markdown")
