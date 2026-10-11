"""
Payment instructions and evidence submission handlers for Abel Promotion bot.
"""

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from database.repositories import OrderRepository, PaymentMethodRepository, PaymentRepository
from database.models import User
from handlers.states import PaymentSubmissionStates
from keyboards.payments import (
    get_payment_methods_keyboard,
    get_payment_instruction_keyboard
)
from keyboards.main_menu import get_cancel_keyboard, get_skip_and_cancel_keyboard
from services.notification_service import NotificationService
from utils.localization import t
from utils.validators import validate_transaction_reference

router = Router(name="payments_router")

@router.message(F.text.in_(["💳 Payment Methods", "💳 የክፍያ መንገዶች"]))
async def show_general_payment_methods(message: types.Message, lang: str):
    """Display information about supported payment channels (CBE and Telebirr)."""
    methods = await PaymentMethodRepository.get_active_methods()
    cbe = next((m for m in methods if m.method_code == "cbe"), None)
    telebirr = next((m for m in methods if m.method_code == "telebirr"), None)

    if lang == "am":
        text = (
            "💳 **የክፍያ መንገዶች (Payment Methods)**\n\n"
            "Abel Promotion የሚከተሉትን የክፍያ አማራጮች ይቀበላል:\n\n"
            "🏦 **የኢትዮጵያ ንግድ ባንክ (CBE)**\n"
            f"• የሂሳብ ስም: `{cbe.account_holder if cbe else 'Abel Promotion'}`\n"
            f"• የሂሳብ ቁጥር: `{cbe.account_number if cbe else '1000123456789'}`\n\n"
            "📱 **ቴሌብር (Telebirr)**\n"
            f"• የሂሳብ ስም: `{telebirr.account_holder if telebirr else 'Abel Promotion'}`\n"
            f"• የቴሌብር ቁጥር: `{telebirr.account_number if telebirr else '0911223344'}`\n\n"
            "📌 ትዕዛዝ በሚያስገቡበት ጊዜ ተገቢውን የክፍያ መንገድ መርጠው ደረሰኝ ማስገባት ይችላሉ።"
        )
    else:
        text = (
            "💳 **Payment Methods**\n\n"
            "Abel Promotion supports the following verified payment methods:\n\n"
            "🏦 **Commercial Bank of Ethiopia (CBE)**\n"
            f"• Account Holder: `{cbe.account_holder if cbe else 'Abel Promotion'}`\n"
            f"• Account Number: `{cbe.account_number if cbe else '1000123456789'}`\n\n"
            "📱 **Telebirr**\n"
            f"• Account Holder: `{telebirr.account_holder if telebirr else 'Abel Promotion'}`\n"
            f"• Telebirr Number: `{telebirr.account_number if telebirr else '0911223344'}`\n\n"
            "📌 When placing an order, select your preferred channel and upload your transaction receipt."
        )

    await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data.startswith("ord_pay:"))
async def callback_pay_for_order(callback: types.CallbackQuery, user: User, lang: str):
    """Prompt user to select payment channel for an existing order."""
    order_id = int(callback.data.split(":")[1])
    order = await OrderRepository.get_order_by_id(order_id)

    if not order or order.user_id != user.telegram_id:
        await callback.answer("Order not found or unauthorized.", show_alert=True)
        return

    methods = await PaymentMethodRepository.get_active_methods()
    text = t("select_payment_method", lang=lang, order_code=order.order_code)
    kb = get_payment_methods_keyboard(order.id, methods, lang=lang)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("pay_select:"))
async def callback_show_payment_instructions(callback: types.CallbackQuery, user: User, lang: str):
    """Show detailed payment transfer instructions for CBE or Telebirr."""
    parts = callback.data.split(":")
    method_code = parts[1]
    order_id = int(parts[2])

    order = await OrderRepository.get_order_by_id(order_id)
    if not order or order.user_id != user.telegram_id:
        await callback.answer("Order not found.", show_alert=True)
        return

    method = await PaymentMethodRepository.get_method_by_code(method_code)
    if not method:
        await callback.answer("Payment method unavailable.", show_alert=True)
        return

    template_key = "payment_instruction_cbe" if method_code == "cbe" else "payment_instruction_telebirr"
    text = t(
        template_key,
        lang=lang,
        order_code=order.order_code,
        amount=order.total_price,
        account_holder=method.account_holder,
        account_number=method.account_number
    )
    kb = get_payment_instruction_keyboard(order.id, method_code, lang=lang)

    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode=None)
    await callback.answer()

@router.callback_query(F.data.startswith("pay_submit:"))
async def callback_start_payment_submission(callback: types.CallbackQuery, state: FSMContext, user: User, lang: str):
    """Initiate evidence upload flow: request screenshot."""
    parts = callback.data.split(":")
    order_id = int(parts[1])
    method_code = parts[2]

    order = await OrderRepository.get_order_by_id(order_id)
    if not order or order.user_id != user.telegram_id:
        await callback.answer("Order not found.", show_alert=True)
        return

    await state.set_state(PaymentSubmissionStates.waiting_for_screenshot)
    await state.update_data(
        order_id=order.id,
        method_code=method_code,
        expected_amount=order.total_price
    )

    prompt = t("upload_screenshot_prompt", lang=lang)
    await callback.message.edit_text(prompt, reply_markup=get_cancel_keyboard(lang=lang), parse_mode="Markdown")
    await callback.answer()

@router.message(PaymentSubmissionStates.waiting_for_screenshot, F.photo)
async def process_payment_screenshot(message: types.Message, state: FSMContext, lang: str):
    """Handle uploaded screenshot photo."""
    # Take highest resolution photo
    photo_file_id = message.photo[-1].file_id
    await state.update_data(screenshot_file_id=photo_file_id)

    await state.set_state(PaymentSubmissionStates.waiting_for_reference)
    prompt = t("upload_reference_prompt", lang=lang)
    await message.answer(prompt, reply_markup=get_skip_and_cancel_keyboard(lang=lang), parse_mode="Markdown")

@router.message(PaymentSubmissionStates.waiting_for_screenshot)
async def invalid_screenshot_format(message: types.Message, lang: str):
    """Handle non-photo uploads."""
    await message.answer(
        "⚠️ Please upload the receipt as an image/photo.",
        reply_markup=get_cancel_keyboard(lang=lang)
    )

@router.callback_query(PaymentSubmissionStates.waiting_for_reference, F.data == "flow_skip")
async def skip_payment_reference(callback: types.CallbackQuery, state: FSMContext, bot: Bot, lang: str):
    """Skip transaction reference and finish submission."""
    await finalize_payment_submission(callback.message, state, bot, reference=None, lang=lang)
    await callback.answer()

@router.message(PaymentSubmissionStates.waiting_for_reference)
async def process_payment_reference(message: types.Message, state: FSMContext, bot: Bot, lang: str):
    """Validate and record transaction reference number."""
    raw_ref = message.text.strip() if message.text else ""
    is_valid, cleaned_ref = validate_transaction_reference(raw_ref)

    if not is_valid:
        await message.answer(
            f"⚠️ {cleaned_ref}\nPlease enter a valid reference or click 'Skip'.",
            reply_markup=get_skip_and_cancel_keyboard(lang=lang)
        )
        return

    # Check for duplicate references
    is_duplicate = await PaymentRepository.is_reference_used(cleaned_ref)
    if is_duplicate:
        await message.answer(
            t("duplicate_reference_error", lang=lang),
            reply_markup=get_cancel_keyboard(lang=lang),
            parse_mode="Markdown"
        )
        return

    await finalize_payment_submission(message, state, bot, reference=cleaned_ref, lang=lang)

async def finalize_payment_submission(
    message_or_target: types.Message,
    state: FSMContext,
    bot: Bot,
    reference: str = None,
    lang: str = "en"
):
    """Persist payment record, update order status, notify admins and user."""
    data = await state.get_data()
    order_id = data.get("order_id")
    method_code = data.get("method_code")
    expected_amount = data.get("expected_amount")
    screenshot_file_id = data.get("screenshot_file_id")

    order = await OrderRepository.get_order_by_id(order_id)
    if not order:
        await message_or_target.answer("Order not found.", parse_mode="Markdown")
        await state.clear()
        return

    method_name = "CBE" if method_code == "cbe" else "Telebirr"
    payment = await PaymentRepository.create_payment(
        order_id=order.id,
        payment_method=method_name,
        expected_amount=expected_amount,
        transaction_reference=reference,
        screenshot_file_id=screenshot_file_id
    )

    await state.clear()

    # Notify admins
    await NotificationService.notify_admins_new_payment(bot, order, payment)

    # Confirm to customer
    success_text = t(
        "payment_submitted_success",
        lang=lang,
        order_code=order.order_code,
        amount=expected_amount,
        method=method_name
    )
    await message_or_target.answer(success_text, parse_mode="Markdown")
