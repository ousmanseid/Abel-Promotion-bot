"""
Main menu command and navigation handlers for Abel Promotion bot.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.repositories import AdminRepository
from keyboards.main_menu import get_main_menu_keyboard
from utils.localization import t

router = Router(name="menu_router")

@router.message(Command("menu"))
async def cmd_menu(message: types.Message, lang: str):
    """Show the main menu."""
    is_adm = await AdminRepository.is_admin(message.from_user.id)
    await message.answer(
        text=t("welcome", lang=lang),
        reply_markup=get_main_menu_keyboard(lang=lang, is_admin=is_adm),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "nav_main_menu")
async def callback_nav_main_menu(callback: types.CallbackQuery, state: FSMContext, lang: str):
    """Return to main menu from inline button navigation."""
    await state.clear()
    is_adm = await AdminRepository.is_admin(callback.from_user.id)
    await callback.message.answer(
        text=t("welcome", lang=lang),
        reply_markup=get_main_menu_keyboard(lang=lang, is_admin=is_adm),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "flow_cancel")
async def callback_flow_cancel(callback: types.CallbackQuery, state: FSMContext, lang: str):
    """Cancel any active process and return to clean state."""
    await state.clear()
    await callback.message.edit_text(t("order_cancelled", lang=lang), parse_mode="Markdown")
    await callback.answer()
