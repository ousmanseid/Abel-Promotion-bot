"""
Customer order creation and tracking handlers for Abel Promotion bot.
"""

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.repositories import (
    ServiceRepository, OrderRepository, PaymentMethodRepository,
    PaymentRepository, OrderMessageRepository
)
from database.models import User
from handlers.states import OrderCreationStates, CustomerReplyMessageStates
from keyboards.services import get_platform_keyboard
from keyboards.orders import (
    get_order_confirm_keyboard,
    get_orders_list_keyboard,
    get_order_detail_keyboard
)
from keyboards.payments import get_payment_methods_keyboard
from keyboards.main_menu import get_cancel_keyboard, get_skip_and_cancel_keyboard
from services.notification_service import NotificationService
from utils.localization import t, get_status_display
from utils.validators import validate_social_media_link, validate_quantity

router = Router(name="orders_router")

@router.message(Command("orders"))
@router.message(F.text.in_(["📦 My Orders", "📦 ትዕዛዞቼ"]))
async def show_my_orders(message: types.Message, user: User, lang: str):
    """Display user's order history."""
    orders = await OrderRepository.get_user_orders(user.telegram_id, limit=20)
    if not orders:
        await message.answer(t("no_orders_found", lang=lang), parse_mode="Markdown")
        return

    text = t("my_orders_title", lang=lang)
    kb = get_orders_list_keyboard(orders, lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "nav_my_orders")
async def callback_nav_my_orders(callback: types.CallbackQuery, user: User, lang: str):
    """View orders list via callback."""
    orders = await OrderRepository.get_user_orders(user.telegram_id, limit=20)
    if not orders:
        await callback.message.edit_text(t("no_orders_found", lang=lang), parse_mode="Markdown")
        await callback.answer()
        return

    text = t("my_orders_title", lang=lang)
    kb = get_orders_list_keyboard(orders, lang=lang)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text.in_(["📝 Place an Order", "📝 ትዕዛዝ አስገባ"]))
async def start_order_placement(message: types.Message, lang: str):
    """Start order flow by presenting platform choices."""
    text = t("select_platform", lang=lang)
    kb = get_platform_keyboard(lang=lang)
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("svc_order:"))
async def callback_start_service_order(callback: types.CallbackQuery, state: FSMContext, lang: str):
    """Initiate order process for a chosen service."""
    service_id = int(callback.data.split(":")[1])
    service = await ServiceRepository.get_service_by_id(service_id)

    if not service or not service.is_active:
        await callback.answer("This service is currently unavailable.", show_alert=True)
        return

    await state.set_state(OrderCreationStates.waiting_for_link)
    await state.update_data(
        service_id=service.id,
        service_name=service.get_name(lang),
        platform=service.platform,
        unit_price=service.price,
        pricing_type=service.pricing_type,
        min_qty=service.minimum_quantity,
        max_qty=service.maximum_quantity
    )

    prompt = t("enter_target_link", lang=lang, platform=service.platform)
    await callback.message.edit_text(prompt, reply_markup=get_cancel_keyboard(lang=lang), parse_mode="Markdown")
    await callback.answer()

@router.message(OrderCreationStates.waiting_for_link)
async def process_target_link(message: types.Message, state: FSMContext, lang: str):
    """Process and validate target social media link."""
    data = await state.get_data()
    platform = data.get("platform", "")

    is_valid, cleaned_link = validate_social_media_link(platform, message.text)
    if not is_valid:
        await message.answer(
            t("invalid_link", lang=lang, platform=platform),
            reply_markup=get_cancel_keyboard(lang=lang),
            parse_mode="Markdown"
        )
        return

    await state.update_data(target_link=cleaned_link)

    pricing_type = data.get("pricing_type", "fixed")
    if pricing_type == "per_unit":
        await state.set_state(OrderCreationStates.waiting_for_quantity)
        prompt = t(
            "enter_quantity",
            lang=lang,
            min_qty=data.get("min_qty", 1),
            max_qty=data.get("max_qty", 100000),
            unit_price=data.get("unit_price", 0.0)
        )
        await message.answer(prompt, reply_markup=get_cancel_keyboard(lang=lang), parse_mode="Markdown")
    else:
        # Fixed pricing has quantity = 1
        await state.update_data(quantity=1)
        await state.set_state(OrderCreationStates.waiting_for_notes)
        prompt = t("enter_customer_notes", lang=lang)
        await message.answer(prompt, reply_markup=get_skip_and_cancel_keyboard(lang=lang), parse_mode="Markdown")

@router.message(OrderCreationStates.waiting_for_quantity)
async def process_quantity(message: types.Message, state: FSMContext, lang: str):
    """Validate quantity input for per-unit services."""
    data = await state.get_data()
    min_qty = data.get("min_qty", 1)
    max_qty = data.get("max_qty", 100000)

    is_valid, qty = validate_quantity(message.text, min_qty=min_qty, max_qty=max_qty)
    if not is_valid or qty is None:
        await message.answer(
            t("invalid_quantity", lang=lang, min_qty=min_qty, max_qty=max_qty),
            reply_markup=get_cancel_keyboard(lang=lang),
            parse_mode="Markdown"
        )
        return

    await state.update_data(quantity=qty)
    await state.set_state(OrderCreationStates.waiting_for_notes)
    prompt = t("enter_customer_notes", lang=lang)
    await message.answer(prompt, reply_markup=get_skip_and_cancel_keyboard(lang=lang), parse_mode="Markdown")

@router.callback_query(OrderCreationStates.waiting_for_notes, F.data == "flow_skip")
async def skip_order_notes(callback: types.CallbackQuery, state: FSMContext, lang: str):
    """Skip optional notes and show order summary."""
    await state.update_data(notes="None")
    await show_order_summary(callback.message, state, lang)
    await callback.answer()

@router.message(OrderCreationStates.waiting_for_notes)
async def process_order_notes(message: types.Message, state: FSMContext, lang: str):
    """Capture optional customer notes and show order summary."""
    notes = message.text.strip() if message.text else "None"
    await state.update_data(notes=notes)
    await show_order_summary(message, state, lang)

async def show_order_summary(message_or_target: types.Message, state: FSMContext, lang: str):
    """Calculate price and present order summary."""
    data = await state.get_data()
    service_id = data.get("service_id")

    # Re-verify latest price directly from database
    service = await ServiceRepository.get_service_by_id(service_id)
    if not service or not service.is_active:
        await message_or_target.answer("Service is no longer available.", parse_mode="Markdown")
        await state.clear()
        return

    quantity = data.get("quantity", 1)
    unit_price = service.price
    total_price = round(unit_price * quantity, 2)

    await state.update_data(
        unit_price=unit_price,
        total_price=total_price,
        service_name=service.get_name(lang)
    )
    await state.set_state(OrderCreationStates.confirm_order)

    summary = t(
        "order_summary",
        lang=lang,
        service_name=service.get_name(lang),
        platform=service.platform,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        target_link=data.get("target_link", ""),
        notes=data.get("notes", "None")
    )
    kb = get_order_confirm_keyboard(lang=lang)
    await message_or_target.answer(summary, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(OrderCreationStates.confirm_order, F.data == "ord_do_confirm")
async def callback_confirm_order(callback: types.CallbackQuery, state: FSMContext, user: User, lang: str):
    """Save order to database and present payment instructions."""
    data = await state.get_data()
    service_id = data.get("service_id")

    # Fetch service snapshot details
    service = await ServiceRepository.get_service_by_id(service_id)
    if not service:
        await callback.answer("Error creating order.", show_alert=True)
        await state.clear()
        return

    quantity = data.get("quantity", 1)
    unit_price = service.price
    total_price = round(unit_price * quantity, 2)

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.get_name(lang),
        unit_price_snapshot=unit_price,
        quantity=quantity,
        total_price=total_price,
        target_link=data.get("target_link", ""),
        customer_notes=data.get("notes", "")
    )

    await state.clear()

    # Success message
    text = t("order_created", lang=lang, order_code=order.order_code, total_price=order.total_price)
    methods = await PaymentMethodRepository.get_active_methods()
    kb = get_payment_methods_keyboard(order.id, methods, lang=lang)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("ord_view:"))
async def callback_view_order(callback: types.CallbackQuery, user: User, lang: str):
    """View details of a specific order."""
    order_id = int(callback.data.split(":")[1])
    order = await OrderRepository.get_order_by_id(order_id)

    # Security: Validate ownership
    if not order or order.user_id != user.telegram_id:
        await callback.answer("Order not found or unauthorized.", show_alert=True)
        return

    latest_pay = await PaymentRepository.get_latest_payment_for_order(order.id)
    pay_info = ""
    if latest_pay:
        pay_info = f"\n• **Payment:** {latest_pay.payment_method} ({latest_pay.status})"
        if latest_pay.transaction_reference:
            pay_info += f"\n• **Reference:** `{latest_pay.transaction_reference}`"
        if latest_pay.rejection_reason and order.status == "Payment Rejected":
            pay_info += f"\n• **Rejection Reason:** {latest_pay.rejection_reason}"

    status_disp = get_status_display(order.status, lang=lang)
    detail_text = t(
        "order_detail_view",
        lang=lang,
        order_code=order.order_code,
        service_name=order.service_name_snapshot,
        platform="Social Media",
        quantity=order.quantity,
        total_price=order.total_price,
        target_link=order.target_link,
        status_text=status_disp,
        date=order.created_at[:16] if order.created_at else "",
        payment_info=pay_info
    )

    kb = get_order_detail_keyboard(order, lang=lang)
    await callback.message.edit_text(detail_text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("cust_reply_msg:"))
async def callback_customer_start_reply(callback: types.CallbackQuery, state: FSMContext, user: User, lang: str):
    """Start workflow for customer to reply to an admin support message."""
    order_id = int(callback.data.split(":")[1])
    order = await OrderRepository.get_order_by_id(order_id)

    # Security check: customer must own this order
    if not order or order.user_id != user.telegram_id:
        await callback.answer("Order not found or unauthorized.", show_alert=True)
        return

    await state.set_state(CustomerReplyMessageStates.waiting_for_message)
    await state.update_data(order_id=order_id)

    prompt = (
        f"✍️ **ለ Abel Promotion ድጋፍ ሰጪ ምላሽ ይስጡ (ትዕዛዝ `#{order.order_code}`)**\n\n"
        f"መልእክትዎን ከታች ይፃፉ። መልዕክትዎ በቀጥታ ለአስተዳዳሪው ይደርሳል።"
        if lang == "am" else
        f"✍️ **Reply to Abel Promotion Support (Order `#{order.order_code}`)**\n\n"
        f"Please type your message below. It will be forwarded directly to the administrator."
    )

    await callback.message.answer(prompt, reply_markup=get_cancel_keyboard(lang=lang), parse_mode="Markdown")
    await callback.answer()

@router.message(CustomerReplyMessageStates.waiting_for_message)
async def process_customer_reply_message(message: types.Message, state: FSMContext, user: User, bot: Bot, lang: str):
    """Receive customer reply, persist to database, and forward to admins."""
    reply_text = message.text.strip() if message.text else ""
    if not reply_text:
        await message.answer(
            "⚠️ Please enter a text message." if lang != "am" else "⚠️ እባክዎ የጽሑፍ መልዕክት ያስገቡ።",
            reply_markup=get_cancel_keyboard(lang=lang)
        )
        return

    data = await state.get_data()
    order_id = data.get("order_id")

    order = await OrderRepository.get_order_by_id(order_id)
    if not order or order.user_id != user.telegram_id:
        await message.answer("Error: Order not found or unauthorized.", parse_mode="Markdown")
        await state.clear()
        return

    # 1. Save in database
    await OrderMessageRepository.save_message(
        order_id=order.id,
        sender_id=user.telegram_id,
        sender_role="customer",
        message_text=reply_text
    )

    # 2. Forward to administrators
    await NotificationService.notify_admins_customer_reply(
        bot=bot,
        order=order,
        customer=user,
        message_text=reply_text
    )

    await state.clear()

    confirm_msg = (
        f"✅ **መልዕክትዎ ለድጋፍ ሰጪ ቡድናችን ተልኳል!**\n\n"
        f"የትዕዛዝ ቁጥር: `#{order.order_code}`\n"
        f"ቡድናችን በቅርቡ መልስ ይሰጥዎታል።"
        if lang == "am" else
        f"✅ **Your message has been sent to Abel Promotion Support!**\n\n"
        f"Order ID: `#{order.order_code}`\n"
        f"Our team will review your response shortly."
    )
    from keyboards.main_menu import get_main_menu_keyboard
    await message.answer(confirm_msg, reply_markup=get_main_menu_keyboard(lang=lang), parse_mode="Markdown")
