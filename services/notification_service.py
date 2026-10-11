"""
Notification Service for notifying users and administrators of orders, payments,
state transitions, and direct messages.
"""

import logging
from aiogram import Bot
from database.models import Order, Payment, SupportTicket, User
from database.repositories import UserRepository, AdminRepository
from keyboards.admin import get_admin_order_notification_keyboard
from keyboards.orders import get_customer_message_reply_keyboard
from utils.localization import t, get_status_display
import config

logger = logging.getLogger(__name__)
 
class NotificationService:
    @staticmethod
    async def _get_admin_chat_ids(bot: Bot) -> set[int]:
        bot_id = getattr(bot, "id", None)
        admins = await AdminRepository.get_all_admins()
        admin_ids = {a.telegram_id for a in admins}.union(config.ADMIN_IDS)
        if bot_id:
            admin_ids = {aid for aid in admin_ids if aid != bot_id}
        return admin_ids

    @staticmethod
    async def notify_admins_new_payment(bot: Bot, order: Order, payment: Payment):
        """
        Notify all active administrators when a customer submits payment evidence.
        Includes complete order & customer info and state-aware inline action buttons.
        """
        admin_ids = await NotificationService._get_admin_chat_ids(bot)

        customer = await UserRepository.get_user_by_telegram_id(order.user_id)
        cust_name = customer.first_name if customer and customer.first_name else "N/A"
        cust_username = f"@{customer.username}" if customer and customer.username else "No @"

        msg = (
            f"🔔 **New Payment Submission Received!**\n\n"
            f"• **Order Code:** `#{order.order_code}`\n"
            f"• **Customer:** {cust_name} ({cust_username}, ID: `{order.user_id}`)\n"
            f"• **Service:** {order.service_name_snapshot}\n"
            f"• **Target Link:** `{order.target_link}`\n"
            f"• **Amount:** **{payment.expected_amount} ETB**\n"
            f"• **Method:** {payment.payment_method}\n"
            f"• **Reference / FT:** `{payment.transaction_reference or 'None'}`\n"
            f"• **Order Status:** {order.status}\n"
            f"• **Payment Status:** {payment.status}\n\n"
            f"⚠️ Verify the actual transaction with your banking records before approving."
        )

        kb = get_admin_order_notification_keyboard(
            order_id=order.id,
            payment_id=payment.id,
            payment_status=payment.status,
            order_status=order.status
        )

        for admin_id in admin_ids:
            try:
                if payment.screenshot_file_id:
                    await bot.send_photo(
                        chat_id=admin_id,
                        photo=payment.screenshot_file_id,
                        caption=msg,
                        reply_markup=kb,
                        parse_mode="Markdown"
                    )
                else:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=msg,
                        reply_markup=kb,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.warning(f"Failed to notify admin {admin_id}: {e}")

    @staticmethod
    async def notify_user_order_approved(bot: Bot, order: Order):
        """Notify customer immediately that their order has been accepted and approved."""
        user = await UserRepository.get_user_by_telegram_id(order.user_id)
        lang = user.language if user else "en"

        text = t(
            "order_approved_notify",
            lang=lang,
            order_code=order.order_code,
            service_name=order.service_name_snapshot,
            total_price=order.total_price
        )

        try:
            await bot.send_message(chat_id=order.user_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Failed to notify customer {order.user_id} of approval: {e}")

    @staticmethod
    async def notify_user_order_rejected(bot: Bot, order: Order, reason: str, was_paid: bool = False):
        """Notify customer immediately that their order was not approved."""
        user = await UserRepository.get_user_by_telegram_id(order.user_id)
        lang = user.language if user else "en"

        refund_note = ""
        if was_paid:
            if lang == "am":
                refund_note = "📌 ማሳሰቢያ፦ ክፍያ ተቀብለን ስለነበር፣ የክፍያ ተመላሽ ሂደቱ በመመሪያችን መሰረት በግምገማ ላይ ነው።\n\n"
            else:
                refund_note = "📌 Note: Because payment was received, your refund review has been initiated in accordance with our refund policy.\n\n"

        text = t(
            "order_rejected_notify",
            lang=lang,
            order_code=order.order_code,
            reason=reason,
            refund_note=refund_note
        )

        try:
            await bot.send_message(chat_id=order.user_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Failed to notify customer {order.user_id} of rejection: {e}")

    @staticmethod
    async def send_message_from_admin_to_customer(bot: Bot, order: Order, message_text: str) -> bool:
        """Send a direct message from administrator to customer for an order."""
        user = await UserRepository.get_user_by_telegram_id(order.user_id)
        lang = user.language if user else "en"

        text = t(
            "order_support_message_received",
            lang=lang,
            order_code=order.order_code,
            message_text=message_text
        )
        kb = get_customer_message_reply_keyboard(order.id, lang=lang)

        try:
            await bot.send_message(chat_id=order.user_id, text=text, reply_markup=kb, parse_mode="Markdown")
            return True
        except Exception as e:
            logger.error(f"Failed to deliver message to customer {order.user_id}: {e}")
            return False

    @staticmethod
    async def notify_admins_customer_reply(bot: Bot, order: Order, customer: User, message_text: str):
        """Deliver customer's response to all administrators."""
        admin_ids = await NotificationService._get_admin_chat_ids(bot)

        cust_username = f"@{customer.username}" if customer.username else "No @"
        msg = (
            f"💬 **Message from Customer (Order #{order.order_code})**\n\n"
            f"• **Customer:** {customer.first_name or 'N/A'} ({cust_username}, ID: `{customer.telegram_id}`)\n"
            f"• **Service:** {order.service_name_snapshot}\n"
            f"• **Status:** {order.status}\n\n"
            f"**Customer's Message:**\n"
            f"\"{message_text}\""
        )

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="💬 Reply to Customer", callback_data=f"adm_msg_cust:{order.id}"),
                    InlineKeyboardButton(text="🔍 View Order", callback_data=f"adm_ord_view:{order.id}")
                ]
            ]
        )

        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=msg, reply_markup=kb, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Failed to deliver customer reply to admin {admin_id}: {e}")

    @staticmethod
    async def notify_admins_new_ticket(bot: Bot, ticket: SupportTicket):
        """Notify admins of a newly submitted support ticket."""
        admin_ids = await NotificationService._get_admin_chat_ids(bot)

        msg = (
            f"🎫 **New Support Ticket: #{ticket.ticket_code}**\n\n"
            f"• **Customer:** `{ticket.user_id}`\n"
            f"• **Message:** {ticket.message}\n\n"
            f"Use `/admin` -> Support Tickets to reply."
        )

        for admin_id in admin_ids:
            try:
                await bot.send_message(chat_id=admin_id, text=msg, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Failed to notify admin {admin_id}: {e}")

    @staticmethod
    async def notify_user_order_status_update(bot: Bot, order: Order, new_status: str, note: str = ""):
        """Send notification to customer in their selected language about order progress."""
        user = await UserRepository.get_user_by_telegram_id(order.user_id)
        lang = user.language if user else "en"
        status_text = get_status_display(new_status, lang=lang)

        if lang == "am":
            msg = (
                f"📢 **የትዕዛዝ ሁኔታ ማሻሻያ!**\n\n"
                f"የትዕዛዝ ቁጥር: `#{order.order_code}`\n"
                f"አገልግሎት: **{order.service_name_snapshot}**\n"
                f"አዲስ ሁኔታ: **{status_text}**\n"
            )
            if note:
                msg += f"\nማስታወሻ: {note}\n"
            msg += "\nበትዕዛዞቼ (My Orders) ገጽ ላይ ዝርዝሩን መከታተል ይችላሉ።"
        else:
            msg = (
                f"📢 **Order Status Update!**\n\n"
                f"Order Code: `#{order.order_code}`\n"
                f"Service: **{order.service_name_snapshot}**\n"
                f"New Status: **{status_text}**\n"
            )
            if note:
                msg += f"\nNote: {note}\n"
            msg += "\nYou can track full progress anytime under '📦 My Orders'."

        try:
            await bot.send_message(chat_id=order.user_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Failed to notify customer {order.user_id}: {e}")

    @staticmethod
    async def notify_user_ticket_reply(bot: Bot, ticket: SupportTicket, reply_text: str):
        """Send admin response back to customer's chat."""
        user = await UserRepository.get_user_by_telegram_id(ticket.user_id)
        lang = user.language if user else "en"

        if lang == "am":
            msg = (
                f"💬 **የድጋፍ ጥያቄዎ (#{ticket.ticket_code}) ምላሽ ተሰጥቶታል!**\n\n"
                f"**የአስተዳዳሪ ምላሽ:**\n{reply_text}\n\n"
                f"ተጨማሪ እገዛ ካስፈለገዎት እንደገና መልዕክት መላክ ይችላሉ።"
            )
        else:
            msg = (
                f"💬 **Response to your Support Ticket (#{ticket.ticket_code})!**\n\n"
                f"**Admin Response:**\n{reply_text}\n\n"
                f"If you have further questions, feel free to submit another ticket."
            )

        try:
            await bot.send_message(chat_id=ticket.user_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Failed to send ticket response to {ticket.user_id}: {e}")
