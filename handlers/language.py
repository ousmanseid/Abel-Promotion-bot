"""
Language selection handler for Abel Promotion bot.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from database.repositories import UserRepository, AdminRepository
from database.models import User
from keyboards.language import get_language_keyboard
from keyboards.main_menu import get_main_menu_keyboard
from utils.localization import t

router = Router(name="language_router")

@router.message(Command("language"))
@router.message(F.text.in_(["🌐 Change Language", "🌐 ቋንቋ ቀይር"]))
async def cmd_language(message: types.Message, lang: str):
    """Prompt user to change language."""
    await message.answer(
        text=t("choose_language", lang=lang),
        reply_markup=get_language_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("set_lang:"))
async def callback_set_language(callback: types.CallbackQuery, user: User):
    """Handle language button click."""
    new_lang = callback.data.split(":")[1]
    if new_lang not in ("en", "am"):
        new_lang = "en"

    await UserRepository.set_language(callback.from_user.id, new_lang)
    is_adm = await AdminRepository.is_admin(callback.from_user.id)

    confirm_msg = t("language_changed", lang=new_lang)
    welcome_msg = t("welcome", lang=new_lang)
    main_kb = get_main_menu_keyboard(lang=new_lang, is_admin=is_adm)

    try:
        await callback.message.edit_text(confirm_msg, parse_mode="Markdown")
    except Exception:
        pass
    await callback.message.answer(welcome_msg, reply_markup=main_kb, parse_mode="Markdown")
    await callback.answer()
