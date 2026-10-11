"""
Customer support and help handlers for Abel Promotion bot.
"""

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.models import User
from database.repositories import SupportTicketRepository
from handlers.states import SupportTicketStates
from keyboards.main_menu import get_cancel_keyboard
from services.notification_service import NotificationService
from utils.localization import t

router = Router(name="support_router")

@router.message(Command("help"))
@router.message(F.text.in_(["❓ Help", "❓ እርዳታ"]))
async def show_help(message: types.Message, lang: str):
    """Show help and guidelines."""
    text = t("help_text", lang=lang)
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("support"))
@router.message(F.text.in_(["📞 Contact Support", "📞 ድጋፍ ያግኙ"]))
async def start_support_ticket(message: types.Message, state: FSMContext, lang: str):
    """Prompt user to describe issue for support ticket."""
    await state.set_state(SupportTicketStates.waiting_for_message)
    await state.update_data(order_id=None)
    intro = t("support_intro", lang=lang)
    await message.answer(intro, reply_markup=get_cancel_keyboard(lang=lang), parse_mode="Markdown")

@router.callback_query(F.data.startswith("ord_support:"))
async def callback_order_support(callback: types.CallbackQuery, state: FSMContext, lang: str):
    """Start support ticket pre-linked to an order."""
    order_id = int(callback.data.split(":")[1])
    await state.set_state(SupportTicketStates.waiting_for_message)
    await state.update_data(order_id=order_id)

    intro = (
        f"📞 **Support for Order #{order_id}**\n\n"
        f"{t('support_intro', lang=lang)}"
    )
    await callback.message.edit_text(intro, reply_markup=get_cancel_keyboard(lang=lang), parse_mode="Markdown")
    await callback.answer()

@router.message(SupportTicketStates.waiting_for_message)
async def process_support_message(message: types.Message, state: FSMContext, user: User, bot: Bot, lang: str):
    """Save support ticket and alert admins."""
    text_content = message.text.strip() if message.text else "File/Media attached"
    data = await state.get_data()
    order_id = data.get("order_id")

    ticket = await SupportTicketRepository.create_ticket(
        user_id=user.telegram_id,
        message=text_content,
        order_id=order_id
    )

    await state.clear()

    # Notify admins
    await NotificationService.notify_admins_new_ticket(bot, ticket)

    confirm_text = t("ticket_created", lang=lang, ticket_code=ticket.ticket_code)
    await message.answer(confirm_text, parse_mode="Markdown")
