"""
Keyboards for the Administrator Panel in Abel Promotion bot.
"""

from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Service, Order, Payment, SupportTicket

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Main dashboard menu for authorized administrators."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Dashboard", callback_data="adm_dashboard"),
                InlineKeyboardButton(text="🛍️ Manage Services", callback_data="adm_services")
            ],
            [
                InlineKeyboardButton(text="📦 Manage Orders", callback_data="adm_orders_menu"),
                InlineKeyboardButton(text="💳 Review Payments", callback_data="adm_payments_queue")
            ],
            [
                InlineKeyboardButton(text="👥 View Customers", callback_data="adm_customers"),
                InlineKeyboardButton(text="💰 Payment Settings", callback_data="adm_pay_settings")
            ],
            [
                InlineKeyboardButton(text="📈 Reports", callback_data="adm_reports"),
                InlineKeyboardButton(text="🎫 Support Tickets", callback_data="adm_tickets")
            ],
            [
                InlineKeyboardButton(text="🏠 Exit to Main Menu", callback_data="nav_main_menu")
            ]
        ]
    )

def get_admin_services_menu() -> InlineKeyboardMarkup:
    """Service catalog management navigation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Add New Service", callback_data="adm_svc_add"),
                InlineKeyboardButton(text="📋 All Services", callback_data="adm_svc_list_all")
            ],
            [
                InlineKeyboardButton(text="📸 Instagram Services", callback_data="adm_svc_plat:Instagram"),
                InlineKeyboardButton(text="📘 Facebook Services", callback_data="adm_svc_plat:Facebook"),
            ],
            [
                InlineKeyboardButton(text="▶️ YouTube Services", callback_data="adm_svc_plat:YouTube"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="adm_main")
            ]
        ]
    )

def get_admin_service_item_keyboard(service: Service) -> InlineKeyboardMarkup:
    """Actions for managing a specific service."""
    status_label = "🔴 Deactivate" if service.is_active else "🟢 Activate"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=status_label, callback_data=f"adm_svc_toggle:{service.id}"),
                InlineKeyboardButton(text="✏️ Edit Price", callback_data=f"adm_svc_price:{service.id}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Services", callback_data="adm_services")
            ]
        ]
    )

def get_admin_order_filter_keyboard() -> InlineKeyboardMarkup:
    """Filter orders by lifecycle status."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Under Review", callback_data="adm_ord_filter:payment_under_review"),
                InlineKeyboardButton(text="💳 Paid", callback_data="adm_ord_filter:paid")
            ],
            [
                InlineKeyboardButton(text="✅ Approved", callback_data="adm_ord_filter:approved"),
                InlineKeyboardButton(text="⚙️ In Progress", callback_data="adm_ord_filter:in_progress")
            ],
            [
                InlineKeyboardButton(text="🎉 Completed", callback_data="adm_ord_filter:completed"),
                InlineKeyboardButton(text="❌ Rejected", callback_data="adm_ord_filter:rejected")
            ],
            [
                InlineKeyboardButton(text="⏳ Awaiting Payment", callback_data="adm_ord_filter:pending_payment"),
                InlineKeyboardButton(text="🚫 Cancelled", callback_data="adm_ord_filter:cancelled")
            ],
            [
                InlineKeyboardButton(text="📋 All Orders", callback_data="adm_ord_filter:ALL"),
                InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="adm_main")
            ]
        ]
    )

def get_admin_order_notification_keyboard(
    order_id: int,
    payment_id: Optional[int] = None,
    payment_status: str = "submitted",
    order_status: str = "payment_under_review"
) -> InlineKeyboardMarkup:
    """
    Inline buttons on push notifications sent to administrators.
    Displays only actions that are strictly valid for the current state.
    """
    buttons = []

    # 1. Payment Verification Actions (if payment submitted and unverified)
    if payment_id and payment_status in ("submitted", "Payment Under Review"):
        buttons.append([
            InlineKeyboardButton(text="✅ Verify Payment", callback_data=f"adm_pay_verify:{payment_id}"),
            InlineKeyboardButton(text="❌ Reject Payment", callback_data=f"adm_pay_reject:{payment_id}")
        ])

    # 2. Order Approval / Rejection Actions (if payment verified and order in paid/approved state)
    if payment_status in ("verified", "Paid") and order_status in ("paid", "Paid"):
        buttons.append([
            InlineKeyboardButton(text="✅ Approve Order", callback_data=f"adm_ord_approve:{order_id}"),
            InlineKeyboardButton(text="❌ Reject Order", callback_data=f"adm_ord_reject:{order_id}")
        ])

    # 3. Work Processing Actions
    if order_status in ("approved", "Approved"):
        buttons.append([
            InlineKeyboardButton(text="⚙️ Start Work", callback_data=f"adm_ord_start:{order_id}"),
            InlineKeyboardButton(text="❌ Reject Order", callback_data=f"adm_ord_reject:{order_id}")
        ])
    elif order_status in ("in_progress", "In Progress"):
        buttons.append([
            InlineKeyboardButton(text="🎉 Mark Completed", callback_data=f"adm_ord_complete:{order_id}")
        ])

    # 4. Direct Communication & Order Details
    buttons.append([
        InlineKeyboardButton(text="💬 Message Customer", callback_data=f"adm_msg_cust:{order_id}"),
        InlineKeyboardButton(text="🔍 View Order Details", callback_data=f"adm_ord_view:{order_id}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_order_detail_keyboard(order: Order, payment: Optional[Payment] = None) -> InlineKeyboardMarkup:
    """Action buttons to transition order status, review payments, or message customer."""
    buttons = []

    pay_status = payment.status if payment else "unpaid"
    ord_status = order.status

    # 1. Payment verification buttons
    if payment and pay_status in ("submitted", "Payment Under Review"):
        buttons.append([
            InlineKeyboardButton(text="✅ Verify Payment", callback_data=f"adm_pay_verify:{payment.id}"),
            InlineKeyboardButton(text="❌ Reject Payment", callback_data=f"adm_pay_reject:{payment.id}")
        ])

    # 2. Order approval buttons (guarded: payment must be verified!)
    if pay_status in ("verified", "Paid") and ord_status in ("paid", "Paid"):
        buttons.append([
            InlineKeyboardButton(text="✅ Approve Order", callback_data=f"adm_ord_approve:{order.id}"),
            InlineKeyboardButton(text="❌ Reject Order", callback_data=f"adm_ord_reject:{order.id}")
        ])

    # 3. Fulfillment progression
    if ord_status in ("approved", "Approved"):
        buttons.append([
            InlineKeyboardButton(text="⚙️ Start Work", callback_data=f"adm_ord_start:{order.id}"),
            InlineKeyboardButton(text="❌ Reject Order", callback_data=f"adm_ord_reject:{order.id}")
        ])
    elif ord_status in ("in_progress", "In Progress"):
        buttons.append([
            InlineKeyboardButton(text="🎉 Mark Completed", callback_data=f"adm_ord_complete:{order.id}")
        ])

    # 4. Cancellation option if not finished
    if ord_status not in ("completed", "Completed", "cancelled", "Cancelled", "rejected", "Payment Rejected"):
        buttons.append([
            InlineKeyboardButton(text="🚫 Cancel Order", callback_data=f"adm_ord_cancel:{order.id}")
        ])

    # 5. Direct messaging and payment evidence inspect
    action_row = [
        InlineKeyboardButton(text="💬 Message Customer", callback_data=f"adm_msg_cust:{order.id}")
    ]
    if payment or order.status not in ("pending_payment", "Awaiting Payment"):
        action_row.append(InlineKeyboardButton(text="💳 Payment Evidence", callback_data=f"adm_ord_view_pay:{order.id}"))
    buttons.append(action_row)

    # 6. Navigation
    buttons.append([
        InlineKeyboardButton(text="⬅️ Back to Orders", callback_data="adm_orders_menu"),
        InlineKeyboardButton(text="📊 Admin Panel", callback_data="adm_main")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_payment_review_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    """Decision buttons for a pending payment submission."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Verify & Mark Paid", callback_data=f"adm_pay_verify:{payment_id}"),
                InlineKeyboardButton(text="❌ Reject Payment", callback_data=f"adm_pay_reject:{payment_id}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Review Queue", callback_data="adm_payments_queue")
            ]
        ]
    )

def get_admin_payment_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings options for payment accounts."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏦 Edit CBE Account Info", callback_data="adm_pay_set_edit:cbe"),
                InlineKeyboardButton(text="📱 Edit Telebirr Info", callback_data="adm_pay_set_edit:telebirr")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Admin Panel", callback_data="adm_main")
            ]
        ]
    )

def get_admin_ticket_detail_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """Support ticket response keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ Reply to Ticket", callback_data=f"adm_ticket_reply:{ticket_id}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Back to Tickets", callback_data="adm_tickets")
            ]
        ]
    )
