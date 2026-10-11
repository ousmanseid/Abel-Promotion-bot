"""
Complete Telegram Administration Module for Abel Promotion bot.
Handles dashboard, service management, order status transitions,
payment review & verification, settings, reports, and support tickets.
"""

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database.repositories import (
    AdminRepository, ServiceRepository, OrderRepository,
    PaymentRepository, PaymentMethodRepository, UserRepository,
    SupportTicketRepository, AuditLogRepository, OrderMessageRepository
)
from database.models import User
from handlers.states import (
    AdminServiceCreateStates, AdminServicePriceStates,
    AdminPaymentRejectStates, AdminOrderRejectStates,
    AdminMessageCustomerStates, AdminPaymentSettingsStates,
    AdminSupportReplyStates
)
from keyboards.admin import (
    get_admin_main_keyboard,
    get_admin_services_menu,
    get_admin_service_item_keyboard,
    get_admin_order_filter_keyboard,
    get_admin_order_detail_keyboard,
    get_admin_order_notification_keyboard,
    get_admin_payment_review_keyboard,
    get_admin_payment_settings_keyboard,
    get_admin_ticket_detail_keyboard
)
from keyboards.main_menu import get_cancel_keyboard
from middlewares.admin_auth import AdminAuthMiddleware
from services.notification_service import NotificationService
from utils.localization import t, get_status_display
import config

router = Router(name="admin_router")
# Apply admin authorization middleware to all events in this router
router.message.middleware(AdminAuthMiddleware())
router.callback_query.middleware(AdminAuthMiddleware())

# ==========================================
# 1. Admin Entry Points & Dashboard
# ==========================================

@router.message(Command("admin"))
@router.message(F.text.in_(["⚙️ Admin Panel / አስተዳዳሪ", "/admin"]))
async def show_admin_panel(message: types.Message):
    """Show administrative control center."""
    text = (
        "👑 **Abel Promotion Admin Control Panel**\n\n"
        "Manage services, review customer payments, process orders, and view live metrics."
    )
    await message.answer(text, reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")

@router.callback_query(F.data == "adm_main")
async def callback_admin_main(callback: types.CallbackQuery, state: FSMContext):
    """Return to admin panel root."""
    await state.clear()
    text = (
        "👑 **Abel Promotion Admin Control Panel**\n\n"
        "Select an administrative module below:"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

@router.message(Command("stats"))
@router.callback_query(F.data == "adm_dashboard")
async def show_admin_dashboard(event: types.Message | types.CallbackQuery):
    """Display real-time statistics and revenue reports."""
    stats = await OrderRepository.get_dashboard_stats()

    text = (
        "📊 **Abel Promotion — Live Dashboard**\n\n"
        f"• 👥 **Total Registered Users:** `{stats['total_users']}`\n"
        f"• 📦 **Total Orders Placed:** `{stats['total_orders']}`\n"
        f"• 🔍 **Orders Under Payment Review:** `{stats['awaiting_review']}`\n"
        f"• 💳 **Verified Paid Orders:** `{stats['paid_approved']}`\n"
        f"• ⚙️ **Orders In Progress:** `{stats['in_progress']}`\n"
        f"• 🎉 **Completed Orders:** `{stats['completed']}`\n"
        f"• 🚫 **Cancelled Orders:** `{stats['cancelled']}`\n\n"
        f"💰 **Total Verified Revenue:** **{stats['total_revenue']:,.2f} ETB**\n"
        f"*(Calculated exclusively from verified orders)*"
    )

    kb = get_admin_main_keyboard()
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await event.answer()

# ==========================================
# 2. Service Management
# ==========================================

@router.callback_query(F.data == "adm_services")
async def show_admin_services(callback: types.CallbackQuery):
    """Services management menu."""
    text = "🛍️ **Service Catalog Management**\nAdd new promotional services or update prices and availability:"
    await callback.message.edit_text(text, reply_markup=get_admin_services_menu(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_svc_plat:"))
async def show_admin_services_by_platform(callback: types.CallbackQuery):
    """List services for a platform with admin actions."""
    platform = callback.data.split(":")[1]
    services = await ServiceRepository.get_all_services()
    filtered = [s for s in services if s.platform == platform]

    if not filtered:
        await callback.answer(f"No services found for {platform}.", show_alert=True)
        return

    buttons = []
    for s in filtered:
        status_dot = "🟢" if s.is_active else "🔴"
        label = f"{status_dot} {s.name_en} ({s.price} ETB)"
        buttons.append([types.InlineKeyboardButton(text=label, callback_data=f"adm_svc_detail:{s.id}")])

    buttons.append([types.InlineKeyboardButton(text="⬅️ Back", callback_data="adm_services")])
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(f"🛍️ **{platform} Services Management:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "adm_svc_list_all")
async def show_admin_all_services(callback: types.CallbackQuery):
    """List all catalog services."""
    services = await ServiceRepository.get_all_services()
    buttons = []
    for s in services:
        status_dot = "🟢" if s.is_active else "🔴"
        label = f"{status_dot} [{s.platform}] {s.name_en} ({s.price} ETB)"
        buttons.append([types.InlineKeyboardButton(text=label, callback_data=f"adm_svc_detail:{s.id}")])

    buttons.append([types.InlineKeyboardButton(text="⬅️ Back", callback_data="adm_services")])
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text("📋 **All Catalog Services:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_svc_detail:"))
async def show_admin_service_detail(callback: types.CallbackQuery):
    """View details and edit actions for a service."""
    service_id = int(callback.data.split(":")[1])
    service = await ServiceRepository.get_service_by_id(service_id)
    if not service:
        await callback.answer("Service not found.", show_alert=True)
        return

    status_str = "🟢 Active" if service.is_active else "🔴 Inactive"
    text = (
        f"📌 **Service #ID {service.id}**\n\n"
        f"• **Name (EN):** {service.name_en}\n"
        f"• **Name (AM):** {service.name_am}\n"
        f"• **Platform:** {service.platform}\n"
        f"• **Price:** {service.price} ETB\n"
        f"• **Type:** {service.pricing_type}\n"
        f"• **Estimated Duration:** {service.estimated_duration_en}\n"
        f"• **Status:** {status_str}\n\n"
        f"• **Description (EN):** {service.description_en}\n"
        f"• **Description (AM):** {service.description_am}\n"
    )
    kb = get_admin_service_item_keyboard(service)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_svc_toggle:"))
async def callback_admin_toggle_service(callback: types.CallbackQuery):
    """Activate or deactivate a service."""
    service_id = int(callback.data.split(":")[1])
    new_state = await ServiceRepository.toggle_service_active(service_id)
    await AuditLogRepository.log(
        admin_telegram_id=callback.from_user.id,
        action="TOGGLE_SERVICE_ACTIVE",
        entity_type="SERVICE",
        entity_id=str(service_id),
        details=f"New state: {'Active' if new_state else 'Inactive'}"
    )

    state_word = "Activated" if new_state else "Deactivated"
    await callback.answer(f"Service has been {state_word}!", show_alert=True)

    # Refresh detail view
    service = await ServiceRepository.get_service_by_id(service_id)
    kb = get_admin_service_item_keyboard(service)
    status_str = "🟢 Active" if service.is_active else "🔴 Inactive"
    text = (
        f"📌 **Service #ID {service.id}**\n\n"
        f"• **Name (EN):** {service.name_en}\n"
        f"• **Platform:** {service.platform}\n"
        f"• **Price:** {service.price} ETB\n"
        f"• **Status:** {status_str}\n"
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("adm_svc_price:"))
async def callback_admin_edit_price(callback: types.CallbackQuery, state: FSMContext):
    """Prompt for new price."""
    service_id = int(callback.data.split(":")[1])
    await state.set_state(AdminServicePriceStates.waiting_for_new_price)
    await state.update_data(service_id=service_id)
    await callback.message.answer(
        f"💰 Enter the new price in ETB for Service #{service_id}:",
        reply_markup=get_cancel_keyboard(lang="en")
    )
    await callback.answer()

@router.message(AdminServicePriceStates.waiting_for_new_price)
async def process_new_service_price(message: types.Message, state: FSMContext):
    """Save updated price."""
    try:
        new_price = float(message.text.strip())
        if new_price <= 0:
            raise ValueError()
    except Exception:
        await message.answer("⚠️ Please enter a valid positive number.")
        return

    data = await state.get_data()
    service_id = data.get("service_id")
    await ServiceRepository.update_service_price(service_id, new_price)

    await AuditLogRepository.log(
        admin_telegram_id=message.from_user.id,
        action="UPDATE_SERVICE_PRICE",
        entity_type="SERVICE",
        entity_id=str(service_id),
        details=f"Updated price to {new_price} ETB"
    )

    await state.clear()
    await message.answer(f"✅ Price for Service #{service_id} updated to {new_price} ETB!", reply_markup=get_admin_main_keyboard())

# Add service wizard
@router.callback_query(F.data == "adm_svc_add")
async def start_add_service_wizard(callback: types.CallbackQuery, state: FSMContext):
    """Start wizard to add a new service."""
    await state.set_state(AdminServiceCreateStates.waiting_for_platform)
    buttons = [
        [types.InlineKeyboardButton(text="Instagram", callback_data="adm_new_plat:Instagram")],
        [types.InlineKeyboardButton(text="Facebook", callback_data="adm_new_plat:Facebook")],
        [types.InlineKeyboardButton(text="YouTube", callback_data="adm_new_plat:YouTube")],
        [types.InlineKeyboardButton(text="❌ Cancel", callback_data="adm_main")]
    ]
    await callback.message.edit_text("Select platform for new service:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@router.callback_query(AdminServiceCreateStates.waiting_for_platform, F.data.startswith("adm_new_plat:"))
async def process_new_platform(callback: types.CallbackQuery, state: FSMContext):
    platform = callback.data.split(":")[1]
    await state.update_data(platform=platform)
    await state.set_state(AdminServiceCreateStates.waiting_for_name_en)
    await callback.message.edit_text(f"Selected: **{platform}**\n\nEnter the English name of the service:")
    await callback.answer()

@router.message(AdminServiceCreateStates.waiting_for_name_en)
async def process_new_name_en(message: types.Message, state: FSMContext):
    await state.update_data(name_en=message.text.strip())
    await state.set_state(AdminServiceCreateStates.waiting_for_name_am)
    await message.answer("Enter the Amharic name of the service (or type same as EN):")

@router.message(AdminServiceCreateStates.waiting_for_name_am)
async def process_new_name_am(message: types.Message, state: FSMContext):
    await state.update_data(name_am=message.text.strip())
    await state.set_state(AdminServiceCreateStates.waiting_for_description)
    await message.answer("Enter a brief service description:")

@router.message(AdminServiceCreateStates.waiting_for_description)
async def process_new_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminServiceCreateStates.waiting_for_price)
    await message.answer("Enter the price in ETB (e.g. 500):")

@router.message(AdminServiceCreateStates.waiting_for_price)
async def process_new_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError()
    except Exception:
        await message.answer("⚠️ Please enter a valid positive number.")
        return

    await state.update_data(price=price)
    await state.set_state(AdminServiceCreateStates.waiting_for_duration)
    await message.answer("Enter estimated duration (e.g., '1-2 business days'):")

@router.message(AdminServiceCreateStates.waiting_for_duration)
async def finalize_add_service(message: types.Message, state: FSMContext):
    duration = message.text.strip()
    data = await state.get_data()

    service_id = await ServiceRepository.add_service(
        name_en=data["name_en"],
        name_am=data["name_am"],
        platform=data["platform"],
        description_en=data["description"],
        description_am=data["description"],
        price=data["price"],
        pricing_type="fixed",
        minimum_quantity=1,
        maximum_quantity=1,
        estimated_duration_en=duration,
        estimated_duration_am=duration
    )

    await AuditLogRepository.log(
        admin_telegram_id=message.from_user.id,
        action="ADD_SERVICE",
        entity_type="SERVICE",
        entity_id=str(service_id),
        details=f"Created {data['name_en']} at {data['price']} ETB"
    )

    await state.clear()
    await message.answer(
        f"✅ Service **{data['name_en']}** added successfully with ID #{service_id}!",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="Markdown"
    )

# ==========================================
# 3. Order Management
# ==========================================

@router.message(Command("orders"))
@router.callback_query(F.data == "adm_orders_menu")
async def show_admin_orders_menu(event: types.Message | types.CallbackQuery):
    """Show order filters."""
    text = "📦 **Order Management**\nFilter orders by current status:"
    kb = get_admin_order_filter_keyboard()
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await event.answer()

@router.callback_query(F.data.startswith("adm_ord_filter:"))
async def show_filtered_orders(callback: types.CallbackQuery):
    """List orders matching the selected filter."""
    filter_val = callback.data.split(":")[1]
    status_filter = None if filter_val == "ALL" else filter_val

    orders = await OrderRepository.get_orders_by_status(status=status_filter, limit=20)
    if not orders:
        await callback.message.edit_text(
            f"No orders found with status: **{filter_val}**.",
            reply_markup=get_admin_order_filter_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    buttons = []
    for o in orders:
        label = f"#{o.order_code} - {o.total_price} ETB ({o.status})"
        buttons.append([types.InlineKeyboardButton(text=label, callback_data=f"adm_ord_view:{o.id}")])

    buttons.append([types.InlineKeyboardButton(text="⬅️ Back", callback_data="adm_orders_menu")])
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(f"📦 Orders ({filter_val}):", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_ord_view:"))
async def show_admin_order_detail(callback: types.CallbackQuery):
    """View order and customer details with status update controls."""
    order_id = int(callback.data.split(":")[1])
    order = await OrderRepository.get_order_by_id(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    payment = await PaymentRepository.get_latest_payment_for_order(order_id)
    user = await UserRepository.get_user_by_telegram_id(order.user_id)
    username = f"@{user.username}" if user and user.username else "No username"

    pay_status = payment.status if payment else "unpaid"
    pay_method = payment.payment_method if payment else "None"
    pay_ref = payment.transaction_reference if payment and payment.transaction_reference else "None"

    text = (
        f"🧾 **Order Details: #{order.order_code}**\n\n"
        f"• **Customer ID:** `{order.user_id}` ({username})\n"
        f"• **Service:** {order.service_name_snapshot}\n"
        f"• **Quantity:** {order.quantity}\n"
        f"• **Total Amount:** **{order.total_price} ETB**\n"
        f"• **Target Link:** `{order.target_link}`\n"
        f"• **Notes:** {order.customer_notes or 'None'}\n"
        f"• **Order Status:** **{order.status}**\n"
        f"• **Payment Status:** **{pay_status}** ({pay_method}, Ref: `{pay_ref}`)\n"
        f"• **Created:** {order.created_at[:16] if order.created_at else ''}\n"
    )
    if order.rejection_reason:
        text += f"• **Rejection Reason:** {order.rejection_reason}\n"
    if order.approved_by:
        text += f"• **Reviewed By Admin:** `{order.approved_by}`\n"

    kb = get_admin_order_detail_keyboard(order, payment)
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode="Markdown")
        else:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode=None)
        else:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode=None)
    await callback.answer()

@router.callback_query(F.data.startswith("adm_ord_approve:"))
async def callback_admin_approve_order(callback: types.CallbackQuery, bot: Bot):
    """Approve order after verifying payment."""
    order_id = int(callback.data.split(":")[1])
    success, msg, order = await OrderRepository.approve_order(order_id, callback.from_user.id)
    if not success:
        await callback.answer(f"⚠️ {msg}", show_alert=True)
        return

    await AuditLogRepository.log(
        admin_telegram_id=callback.from_user.id,
        action="APPROVE_ORDER",
        entity_type="ORDER",
        entity_id=str(order_id),
        details=f"Approved Order #{order.order_code}"
    )

    # Immediately notify customer
    await NotificationService.notify_user_order_approved(bot, order)

    await callback.answer(f"✅ Order #{order.order_code} APPROVED! Customer notified.", show_alert=True)

    payment = await PaymentRepository.get_latest_payment_for_order(order_id)
    kb = get_admin_order_detail_keyboard(order, payment)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass

@router.callback_query(F.data.startswith("adm_ord_reject:"))
async def callback_admin_reject_order_prompt(callback: types.CallbackQuery, state: FSMContext):
    """Prompt admin for rejection reason before rejecting an order."""
    order_id = int(callback.data.split(":")[1])
    order = await OrderRepository.get_order_by_id(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await state.set_state(AdminOrderRejectStates.waiting_for_reason)
    await state.update_data(order_id=order_id)

    await callback.message.answer(
        f"❌ Please enter the reason for rejecting Order `#{order.order_code}`:\n(This will be sent directly to the customer)",
        reply_markup=get_cancel_keyboard(lang="en")
    )
    await callback.answer()

@router.message(AdminOrderRejectStates.waiting_for_reason)
async def process_order_rejection(message: types.Message, state: FSMContext, bot: Bot):
    """Reject order and notify customer with the reason."""
    reason = message.text.strip()
    data = await state.get_data()
    order_id = data.get("order_id")

    payment = await PaymentRepository.get_latest_payment_for_order(order_id)
    was_paid = payment is not None and payment.status in ("verified", "Paid")

    success, msg, order = await OrderRepository.reject_order(order_id, message.from_user.id, reason)
    if not success:
        await message.answer(f"⚠️ {msg}", reply_markup=get_admin_main_keyboard())
        await state.clear()
        return

    await AuditLogRepository.log(
        admin_telegram_id=message.from_user.id,
        action="REJECT_ORDER",
        entity_type="ORDER",
        entity_id=str(order_id),
        details=f"Reason: {reason} (Was paid: {was_paid})"
    )

    # Immediately notify customer
    await NotificationService.notify_user_order_rejected(bot, order, reason, was_paid=was_paid)

    await state.clear()
    await message.answer(
        f"❌ Order `#{order.order_code}` has been REJECTED.\nCustomer has been notified.",
        reply_markup=get_admin_main_keyboard()
    )

@router.callback_query(F.data.startswith("adm_ord_start:"))
async def callback_admin_start_order(callback: types.CallbackQuery, bot: Bot):
    """Transition order to in_progress."""
    order_id = int(callback.data.split(":")[1])
    success, msg, order = await OrderRepository.start_order(order_id, callback.from_user.id)
    if not success:
        await callback.answer(f"⚠️ {msg}", show_alert=True)
        return

    await AuditLogRepository.log(
        admin_telegram_id=callback.from_user.id,
        action="START_ORDER",
        entity_type="ORDER",
        entity_id=str(order_id),
        details=f"Started work on #{order.order_code}"
    )

    await NotificationService.notify_user_order_status_update(
        bot, order, "in_progress", note="Work has officially started on your order!"
    )
    await callback.answer(f"⚙️ Order #{order.order_code} marked as In Progress!", show_alert=True)

    payment = await PaymentRepository.get_latest_payment_for_order(order_id)
    kb = get_admin_order_detail_keyboard(order, payment)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass

@router.callback_query(F.data.startswith("adm_ord_complete:"))
async def callback_admin_complete_order(callback: types.CallbackQuery, bot: Bot):
    """Transition order to completed."""
    order_id = int(callback.data.split(":")[1])
    success, msg, order = await OrderRepository.complete_order(order_id, callback.from_user.id)
    if not success:
        await callback.answer(f"⚠️ {msg}", show_alert=True)
        return

    await AuditLogRepository.log(
        admin_telegram_id=callback.from_user.id,
        action="COMPLETE_ORDER",
        entity_type="ORDER",
        entity_id=str(order_id),
        details=f"Completed #{order.order_code}"
    )

    await NotificationService.notify_user_order_status_update(
        bot, order, "completed", note="Your promotional campaign has been successfully completed! 🎉"
    )
    await callback.answer(f"🎉 Order #{order.order_code} marked as Completed!", show_alert=True)

    payment = await PaymentRepository.get_latest_payment_for_order(order_id)
    kb = get_admin_order_detail_keyboard(order, payment)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass

@router.callback_query(F.data.startswith("adm_ord_cancel:"))
async def callback_admin_cancel_order(callback: types.CallbackQuery, bot: Bot):
    """Cancel order and notify customer."""
    order_id = int(callback.data.split(":")[1])
    success, msg, order = await OrderRepository.cancel_order(order_id, callback.from_user.id, reason="Cancelled by Administrator")
    if not success:
        await callback.answer(f"⚠️ {msg}", show_alert=True)
        return

    await AuditLogRepository.log(
        admin_telegram_id=callback.from_user.id,
        action="CANCEL_ORDER",
        entity_type="ORDER",
        entity_id=str(order_id),
        details="Admin cancelled order"
    )

    await NotificationService.notify_user_order_status_update(
        bot, order, "cancelled", note="Order was cancelled by the administrator."
    )
    await callback.answer(f"🚫 Order #{order.order_code} cancelled.", show_alert=True)

    payment = await PaymentRepository.get_latest_payment_for_order(order_id)
    kb = get_admin_order_detail_keyboard(order, payment)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass

@router.callback_query(F.data.startswith("adm_msg_cust:"))
async def callback_admin_message_customer_start(callback: types.CallbackQuery, state: FSMContext):
    """Start workflow to send a direct message to customer regarding an order."""
    order_id = int(callback.data.split(":")[1])
    order = await OrderRepository.get_order_by_id(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await state.set_state(AdminMessageCustomerStates.waiting_for_message)
    await state.update_data(order_id=order_id)

    user = await UserRepository.get_user_by_telegram_id(order.user_id)
    user_str = f"@{user.username}" if user and user.username else str(order.user_id)

    prompt = (
        f"💬 **Send Message to Customer**\n\n"
        f"• **Order:** `#{order.order_code}`\n"
        f"• **Recipient:** {user_str} (ID: `{order.user_id}`)\n\n"
        f"Enter the message you want to deliver to the customer. They will receive it from the bot and will be able to reply."
    )
    await callback.message.answer(prompt, reply_markup=get_cancel_keyboard(lang="en"), parse_mode="Markdown")
    await callback.answer()

@router.message(AdminMessageCustomerStates.waiting_for_message)
async def process_admin_message_to_customer(message: types.Message, state: FSMContext, bot: Bot):
    """Send admin message to customer private chat and save to order_messages."""
    admin_msg = message.text.strip()
    data = await state.get_data()
    order_id = data.get("order_id")

    order = await OrderRepository.get_order_by_id(order_id)
    if not order:
        await message.answer("Order not found.", reply_markup=get_admin_main_keyboard())
        await state.clear()
        return

    # 1. Save in database
    await OrderMessageRepository.save_message(
        order_id=order.id,
        sender_id=message.from_user.id,
        sender_role="admin",
        message_text=admin_msg
    )

    # 2. Dispatch to customer via NotificationService
    delivered = await NotificationService.send_message_from_admin_to_customer(
        bot=bot,
        order=order,
        message_text=admin_msg
    )

    # 3. Log audit event
    await AuditLogRepository.log(
        admin_telegram_id=message.from_user.id,
        action="MESSAGE_CUSTOMER",
        entity_type="ORDER",
        entity_id=str(order.id),
        details=admin_msg[:120]
    )

    await state.clear()
    if delivered:
        await message.answer(
            f"✅ **Message delivered to customer!**\n\n"
            f"Order: `#{order.order_code}`\n"
            f"Recipient: `{order.user_id}`\n\n"
            f"When the customer replies, their response will be forwarded here directly.",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"⚠️ Could not deliver message to customer (they may have blocked the bot). Message was saved to database.",
            reply_markup=get_admin_main_keyboard()
        )

@router.callback_query(F.data.startswith("adm_ord_set:"))
async def callback_admin_set_order_status(callback: types.CallbackQuery, bot: Bot):
    """Update order status and notify customer."""
    parts = callback.data.split(":")
    order_id = int(parts[1])
    new_status = parts[2]

    order = await OrderRepository.get_order_by_id(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await OrderRepository.update_order_status(
        order_id=order.id,
        new_status=new_status,
        changed_by=callback.from_user.id,
        reason=f"Status updated by admin to {new_status}"
    )

    await AuditLogRepository.log(
        admin_telegram_id=callback.from_user.id,
        action="UPDATE_ORDER_STATUS",
        entity_type="ORDER",
        entity_id=str(order.id),
        details=f"Changed status to {new_status}"
    )

    # Notify customer
    await NotificationService.notify_user_order_status_update(bot, order, new_status)

    await callback.answer(f"Order #{order.order_code} status set to {new_status}!", show_alert=True)

    # Refresh order details
    order.status = new_status
    payment = await PaymentRepository.get_latest_payment_for_order(order_id)
    kb = get_admin_order_detail_keyboard(order, payment)
    await callback.message.edit_reply_markup(reply_markup=kb)

@router.callback_query(F.data.startswith("adm_ord_view_pay:"))
async def callback_admin_view_order_payment(callback: types.CallbackQuery):
    """View payment screenshot and reference for an order."""
    order_id = int(callback.data.split(":")[1])
    payment = await PaymentRepository.get_latest_payment_for_order(order_id)

    if not payment:
        await callback.answer("No payment record found for this order.", show_alert=True)
        return

    caption = (
        f"💳 **Payment Record for Order #{order_id}**\n\n"
        f"• **Method:** {payment.payment_method}\n"
        f"• **Expected Amount:** {payment.expected_amount} ETB\n"
        f"• **Reference:** `{payment.transaction_reference or 'None'}`\n"
        f"• **Status:** **{payment.status}**\n"
        f"• **Submitted:** {payment.submitted_at[:16] if payment.submitted_at else ''}\n"
    )
    if payment.rejection_reason:
        caption += f"• **Rejection Reason:** {payment.rejection_reason}\n"

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⬅️ Back to Order", callback_data=f"adm_ord_view:{order_id}")]
        ]
    )

    if payment.screenshot_file_id:
        await callback.message.answer_photo(
            photo=payment.screenshot_file_id,
            caption=caption,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(caption, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# ==========================================
# 4. Review Payments Queue
# ==========================================

@router.message(Command("payments"))
@router.callback_query(F.data == "adm_payments_queue")
async def show_payments_queue(event: types.Message | types.CallbackQuery):
    """Show pending payments awaiting verification."""
    pending = await PaymentRepository.get_pending_payments(limit=20)

    if not pending:
        text = "✅ **No Pending Payments!** All customer payments have been verified."
        kb = get_admin_main_keyboard()
        if isinstance(event, types.Message):
            await event.answer(text, reply_markup=kb, parse_mode="Markdown")
        else:
            await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
            await event.answer()
        return

    buttons = []
    for pay, ord_obj in pending:
        label = f"#{ord_obj.order_code} - {pay.expected_amount} ETB ({pay.payment_method})"
        buttons.append([types.InlineKeyboardButton(text=label, callback_data=f"adm_pay_inspect:{pay.id}")])

    buttons.append([types.InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="adm_main")])
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    text = f"💳 **Pending Payments Queue ({len(pending)}):**\nSelect a submission to review receipt and verify:"
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await event.answer()

@router.callback_query(F.data.startswith("adm_pay_inspect:"))
async def inspect_pending_payment(callback: types.CallbackQuery):
    """Inspect payment details and receipt photo."""
    payment_id = int(callback.data.split(":")[1])
    payment = await PaymentRepository.get_payment_by_id(payment_id)
    if not payment:
        await callback.answer("Payment not found.", show_alert=True)
        return

    order = await OrderRepository.get_order_by_id(payment.order_id)
    caption = (
        f"🔍 **Payment Review: #{order.order_code if order else 'N/A'}**\n\n"
        f"• **Amount:** **{payment.expected_amount} ETB**\n"
        f"• **Method:** {payment.payment_method}\n"
        f"• **Customer ID:** `{order.user_id if order else 'N/A'}`\n"
        f"• **Reference:** `{payment.transaction_reference or 'None'}`\n"
        f"• **Submitted:** {payment.submitted_at[:16] if payment.submitted_at else ''}\n\n"
        f"⚠️ Verify the transaction with your CBE/Telebirr account before approving."
    )
    kb = get_admin_payment_review_keyboard(payment.id)

    if payment.screenshot_file_id:
        await callback.message.answer_photo(
            photo=payment.screenshot_file_id,
            caption=caption,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(caption, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_pay_verify:"))
async def callback_admin_verify_payment(callback: types.CallbackQuery, bot: Bot):
    """Verify and approve payment."""
    payment_id = int(callback.data.split(":")[1])
    payment = await PaymentRepository.get_payment_by_id(payment_id)
    if not payment:
        await callback.answer("Payment not found.", show_alert=True)
        return

    order = await OrderRepository.get_order_by_id(payment.order_id)
    await PaymentRepository.verify_payment(payment_id, callback.from_user.id)

    await AuditLogRepository.log(
        admin_telegram_id=callback.from_user.id,
        action="VERIFY_PAYMENT",
        entity_type="PAYMENT",
        entity_id=str(payment_id),
        details=f"Verified {payment.expected_amount} ETB for Order #{order.order_code if order else payment.order_id}"
    )

    # Notify customer
    if order:
        await NotificationService.notify_user_order_status_update(
            bot, order, "Paid",
            note="Payment verified! Our team will begin processing your order shortly."
        )

    await callback.answer("✅ Payment verified and marked as Paid!", show_alert=True)
    reply_kb = get_admin_order_notification_keyboard(
        order_id=order.id,
        payment_id=payment.id,
        payment_status="verified",
        order_status="paid"
    ) if order else types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="💳 Back to Queue", callback_data="adm_payments_queue")]]
    )
    caption_text = f"✅ **Payment Verified!** Order #{order.order_code if order else ''} is now marked as Paid.\nYou can now review and Approve or Reject the order below:"
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=caption_text,
                reply_markup=reply_kb,
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                text=caption_text,
                reply_markup=reply_kb,
                parse_mode="Markdown"
            )
    except Exception:
        pass

@router.callback_query(F.data.startswith("adm_pay_reject:"))
async def callback_admin_reject_payment_prompt(callback: types.CallbackQuery, state: FSMContext):
    """Prompt admin for rejection reason."""
    payment_id = int(callback.data.split(":")[1])
    await state.set_state(AdminPaymentRejectStates.waiting_for_reason)
    await state.update_data(payment_id=payment_id)

    await callback.message.answer(
        "❌ Please enter the reason for rejecting this payment (e.g. 'Transaction not found', 'Amount mismatch'):",
        reply_markup=get_cancel_keyboard(lang="en")
    )
    await callback.answer()

@router.message(AdminPaymentRejectStates.waiting_for_reason)
async def process_payment_rejection(message: types.Message, state: FSMContext, bot: Bot):
    """Reject payment and notify customer with the reason."""
    reason = message.text.strip()
    data = await state.get_data()
    payment_id = data.get("payment_id")

    payment = await PaymentRepository.get_payment_by_id(payment_id)
    if not payment:
        await message.answer("Payment not found.")
        await state.clear()
        return

    order = await OrderRepository.get_order_by_id(payment.order_id)
    await PaymentRepository.reject_payment(payment_id, message.from_user.id, reason)

    await AuditLogRepository.log(
        admin_telegram_id=message.from_user.id,
        action="REJECT_PAYMENT",
        entity_type="PAYMENT",
        entity_id=str(payment_id),
        details=f"Reason: {reason}"
    )

    # Notify customer
    if order:
        await NotificationService.notify_user_order_status_update(
            bot, order, "Payment Rejected",
            note=f"Rejection reason: {reason}. You can submit updated proof under '📦 My Orders'."
        )

    await state.clear()
    await message.answer(
        f"❌ Payment for Order #{order.order_code if order else ''} was rejected.\nCustomer notified.",
        reply_markup=get_admin_main_keyboard()
    )

# ==========================================
# 5. Payment Settings
# ==========================================

@router.message(Command("payment_settings"))
@router.callback_query(F.data == "adm_pay_settings")
async def show_payment_settings(event: types.Message | types.CallbackQuery):
    """View and update payment account configuration."""
    methods = await PaymentMethodRepository.get_active_methods()
    cbe = next((m for m in methods if m.method_code == "cbe"), None)
    telebirr = next((m for m in methods if m.method_code == "telebirr"), None)

    text = (
        "💰 **Payment Account Settings**\n\n"
        "🏦 **Commercial Bank of Ethiopia (CBE):**\n"
        f"• Holder: `{cbe.account_holder if cbe else 'N/A'}`\n"
        f"• Number: `{cbe.account_number if cbe else 'N/A'}`\n\n"
        "📱 **Telebirr:**\n"
        f"• Holder: `{telebirr.account_holder if telebirr else 'N/A'}`\n"
        f"• Number: `{telebirr.account_number if telebirr else 'N/A'}`\n"
    )
    kb = get_admin_payment_settings_keyboard()

    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await event.answer()

@router.callback_query(F.data.startswith("adm_pay_set_edit:"))
async def callback_edit_payment_setting(callback: types.CallbackQuery, state: FSMContext):
    """Prompt for new account holder."""
    method_code = callback.data.split(":")[1]
    await state.set_state(AdminPaymentSettingsStates.waiting_for_holder)
    await state.update_data(method_code=method_code)

    name = "CBE" if method_code == "cbe" else "Telebirr"
    await callback.message.edit_text(
        f"Editing **{name}** details:\n\nPlease enter the new **Account Holder Name**:",
        reply_markup=get_cancel_keyboard(lang="en"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(AdminPaymentSettingsStates.waiting_for_holder)
async def process_new_account_holder(message: types.Message, state: FSMContext):
    holder = message.text.strip()
    await state.update_data(account_holder=holder)
    await state.set_state(AdminPaymentSettingsStates.waiting_for_number)
    await message.answer("Please enter the new **Account/Phone Number**:", reply_markup=get_cancel_keyboard(lang="en"), parse_mode="Markdown")

@router.message(AdminPaymentSettingsStates.waiting_for_number)
async def process_new_account_number(message: types.Message, state: FSMContext):
    number = message.text.strip()
    data = await state.get_data()
    method_code = data.get("method_code")
    holder = data.get("account_holder")

    await PaymentMethodRepository.update_method_details(
        method_code=method_code,
        account_holder=holder,
        account_number=number
    )

    await AuditLogRepository.log(
        admin_telegram_id=message.from_user.id,
        action="UPDATE_PAYMENT_METHOD",
        entity_type="PAYMENT_METHOD",
        entity_id=method_code,
        details=f"Holder: {holder}, Number: {number}"
    )

    await state.clear()
    await message.answer(f"✅ {method_code.upper()} payment details updated successfully!", reply_markup=get_admin_main_keyboard())

# ==========================================
# 6. Support Ticket Management
# ==========================================

@router.callback_query(F.data == "adm_tickets")
async def show_admin_tickets(callback: types.CallbackQuery):
    """List open support tickets."""
    tickets = await SupportTicketRepository.get_open_tickets(limit=20)
    if not tickets:
        await callback.message.edit_text("✅ No open support tickets.", reply_markup=get_admin_main_keyboard(), parse_mode="Markdown")
        await callback.answer()
        return

    buttons = []
    for tkt in tickets:
        preview = (tkt.message[:25] + "...") if len(tkt.message) > 25 else tkt.message
        buttons.append([types.InlineKeyboardButton(text=f"#{tkt.ticket_code}: {preview}", callback_data=f"adm_ticket_view:{tkt.id}")])

    buttons.append([types.InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="adm_main")])
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(f"🎫 **Open Support Tickets ({len(tickets)}):**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_ticket_view:"))
async def view_support_ticket(callback: types.CallbackQuery):
    """View details of a support ticket."""
    ticket_id = int(callback.data.split(":")[1])
    ticket = await SupportTicketRepository.get_ticket_by_id(ticket_id)
    if not ticket:
        await callback.answer("Ticket not found.", show_alert=True)
        return

    user = await UserRepository.get_user_by_telegram_id(ticket.user_id)
    user_str = f"@{user.username}" if user and user.username else str(ticket.user_id)

    text = (
        f"🎫 **Ticket #{ticket.ticket_code}**\n\n"
        f"• **Customer:** {user_str} (`{ticket.user_id}`)\n"
        f"• **Related Order:** #{ticket.order_id or 'None'}\n"
        f"• **Status:** {ticket.status}\n"
        f"• **Created:** {ticket.created_at[:16] if ticket.created_at else ''}\n\n"
        f"**Message:**\n{ticket.message}"
    )
    kb = get_admin_ticket_detail_keyboard(ticket.id)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_ticket_reply:"))
async def prompt_ticket_reply(callback: types.CallbackQuery, state: FSMContext):
    """Prompt admin to enter reply message."""
    ticket_id = int(callback.data.split(":")[1])
    await state.set_state(AdminSupportReplyStates.waiting_for_response)
    await state.update_data(ticket_id=ticket_id)

    await callback.message.answer(
        f"✍️ Enter your reply to Ticket #{ticket_id} (it will be delivered to the customer):",
        reply_markup=get_cancel_keyboard(lang="en")
    )
    await callback.answer()

@router.message(AdminSupportReplyStates.waiting_for_response)
async def process_ticket_reply(message: types.Message, state: FSMContext, bot: Bot):
    """Send reply to customer and mark ticket closed."""
    reply_text = message.text.strip()
    data = await state.get_data()
    ticket_id = data.get("ticket_id")

    ticket = await SupportTicketRepository.get_ticket_by_id(ticket_id)
    if not ticket:
        await message.answer("Ticket not found.")
        await state.clear()
        return

    await SupportTicketRepository.answer_ticket(ticket.id, reply_text)
    await NotificationService.notify_user_ticket_reply(bot, ticket, reply_text)

    await AuditLogRepository.log(
        admin_telegram_id=message.from_user.id,
        action="REPLY_SUPPORT_TICKET",
        entity_type="SUPPORT_TICKET",
        entity_id=str(ticket.id),
        details=reply_text[:100]
    )

    await state.clear()
    await message.answer(f"✅ Reply sent to customer for Ticket #{ticket.ticket_code}!", reply_markup=get_admin_main_keyboard())

# ==========================================
# 7. Customer Lookup & Reports
# ==========================================

@router.message(Command("users"))
@router.callback_query(F.data == "adm_customers")
async def show_customers(event: types.Message | types.CallbackQuery):
    """List recent customers."""
    users = await UserRepository.get_all_users(limit=20)
    lines = ["👥 **Registered Customers (Recent 20):**\n"]
    for u in users:
        uname = f"@{u.username}" if u.username else "No @"
        lines.append(f"• `{u.telegram_id}` | {u.first_name or 'N/A'} ({uname}) - Lang: {u.language}")

    text = "\n".join(lines)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="⬅️ Back", callback_data="adm_main")]]
    )
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await event.answer()

@router.callback_query(F.data == "adm_reports")
async def show_detailed_reports(callback: types.CallbackQuery):
    """Show detailed financial and operational reports."""
    stats = await OrderRepository.get_dashboard_stats()
    text = (
        "📈 **Abel Promotion — Detailed Reports**\n\n"
        f"• **Total Orders Recorded:** {stats['total_orders']}\n"
        f"• **Completed Orders:** {stats['completed']}\n"
        f"• **Pending Review:** {stats['awaiting_review']}\n"
        f"• **Cancelled Orders:** {stats['cancelled']}\n\n"
        f"💵 **Verified Revenue:** {stats['total_revenue']:,.2f} ETB\n"
        f"👥 **Customer Base:** {stats['total_users']} users\n\n"
        f"🔒 Duplicate checks and transaction references protect against fraudulent submissions."
    )
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="adm_main")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
