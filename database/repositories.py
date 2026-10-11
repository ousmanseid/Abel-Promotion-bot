"""
Database repositories handling CRUD operations for Abel Promotion bot.
"""

from typing import List, Optional, Dict, Any, Tuple
from database.connection import get_db_connection
from database.models import (
    User, Admin, Service, Order, Payment, PaymentMethod,
    OrderStatusHistory, SupportTicket, AuditLog, OrderMessage
)
from utils.order_codes import format_order_code, format_ticket_code
import config

class OrderMessageRepository:
    @staticmethod
    async def save_message(order_id: int, sender_id: int, sender_role: str, message_text: str) -> OrderMessage:
        async with get_db_connection() as db:
            cursor = await db.execute("""
                INSERT INTO order_messages (order_id, sender_id, sender_role, message_text)
                VALUES (?, ?, ?, ?)
            """, (order_id, sender_id, sender_role, message_text))
            msg_id = cursor.lastrowid
            await db.commit()
            return OrderMessage(
                id=msg_id,
                order_id=order_id,
                sender_id=sender_id,
                sender_role=sender_role,
                message_text=message_text
            )

    @staticmethod
    async def get_order_messages(order_id: int, limit: int = 50) -> List[OrderMessage]:
        async with get_db_connection() as db:
            async with db.execute("""
                SELECT * FROM order_messages WHERE order_id = ? ORDER BY created_at ASC LIMIT ?
            """, (order_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [OrderMessage(**dict(r)) for r in rows]

class OrderRepository:
    @staticmethod
    def _row_to_order(r) -> Order:
        d = dict(r)
        return Order(
            id=d["id"],
            order_code=d["order_code"],
            user_id=d["user_id"],
            service_id=d["service_id"],
            service_name_snapshot=d["service_name_snapshot"],
            unit_price_snapshot=d["unit_price_snapshot"],
            quantity=d["quantity"],
            total_price=d["total_price"],
            target_link=d["target_link"],
            customer_notes=d.get("customer_notes"),
            status=d.get("status", "pending_payment"),
            approved_by=d.get("approved_by"),
            approved_at=d.get("approved_at"),
            rejection_reason=d.get("rejection_reason"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at")
        )

    @staticmethod
    async def create_order(
        user_id: int,
        service_id: int,
        service_name_snapshot: str,
        unit_price_snapshot: float,
        quantity: int,
        total_price: float,
        target_link: str,
        customer_notes: Optional[str] = None
    ) -> Order:
        async with get_db_connection() as db:
            cursor = await db.execute("""
                INSERT INTO orders (
                    user_id, service_id, service_name_snapshot, unit_price_snapshot,
                    quantity, total_price, target_link, customer_notes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending_payment')
            """, (
                user_id, service_id, service_name_snapshot, unit_price_snapshot,
                quantity, total_price, target_link, customer_notes
            ))
            order_id = cursor.lastrowid
            order_code = format_order_code(order_id)
            await db.execute("UPDATE orders SET order_code = ? WHERE id = ?", (order_code, order_id))

            # Record initial history
            await db.execute("""
                INSERT INTO order_status_history (order_id, previous_status, new_status, reason)
                VALUES (?, NULL, 'pending_payment', 'Order created')
            """, (order_id,))

            await db.commit()

            return Order(
                id=order_id,
                order_code=order_code,
                user_id=user_id,
                service_id=service_id,
                service_name_snapshot=service_name_snapshot,
                unit_price_snapshot=unit_price_snapshot,
                quantity=quantity,
                total_price=total_price,
                target_link=target_link,
                customer_notes=customer_notes,
                status="pending_payment"
            )

    @staticmethod
    async def get_order_by_id(order_id: int) -> Optional[Order]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
                return OrderRepository._row_to_order(row) if row else None

    @staticmethod
    async def get_order_by_code(order_code: str) -> Optional[Order]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM orders WHERE order_code = ?", (order_code.strip().upper(),)) as cursor:
                row = await cursor.fetchone()
                return OrderRepository._row_to_order(row) if row else None

    @staticmethod
    async def get_user_orders(user_id: int, limit: int = 20) -> List[Order]:
        async with get_db_connection() as db:
            async with db.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [OrderRepository._row_to_order(r) for r in rows]

    @staticmethod
    async def get_orders_by_status(status: Optional[str] = None, limit: int = 50) -> List[Order]:
        async with get_db_connection() as db:
            if status and status != "ALL":
                # Support both new and legacy values
                query = "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC LIMIT ?"
                params = (status, limit)
            else:
                query = "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?"
                params = (limit,)
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [OrderRepository._row_to_order(r) for r in rows]

    @staticmethod
    async def update_order_status(
        order_id: int,
        new_status: str,
        changed_by: Optional[int] = None,
        reason: Optional[str] = None
    ) -> bool:
        async with get_db_connection() as db:
            async with db.execute("SELECT status FROM orders WHERE id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False
                prev_status = row["status"]

            await db.execute("""
                UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (new_status, order_id))

            await db.execute("""
                INSERT INTO order_status_history (order_id, previous_status, new_status, changed_by, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, prev_status, new_status, changed_by, reason))

            await db.commit()
            return True

    @staticmethod
    async def approve_order(order_id: int, admin_id: int) -> Tuple[bool, str, Optional[Order]]:
        """
        Approve an order after confirming that payment has been verified.
        State guard: Order must have verified payment and be in 'paid' status.
        """
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False, "Order not found.", None
                order = OrderRepository._row_to_order(row)

            # Check payment verification guard
            async with db.execute("SELECT status FROM payments WHERE order_id = ? ORDER BY submitted_at DESC LIMIT 1", (order_id,)) as cursor:
                pay_row = await cursor.fetchone()
                if not pay_row or pay_row["status"] not in ("verified", "Paid"):
                    return False, "Cannot approve order before payment is verified.", order

            if order.status not in ("paid", "Paid"):
                return False, f"Order status is '{order.status}'. Only paid orders can be approved.", order

            await db.execute("""
                UPDATE orders SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (admin_id, order_id))

            await db.execute("""
                INSERT INTO order_status_history (order_id, previous_status, new_status, changed_by, reason)
                VALUES (?, ?, 'approved', ?, 'Order approved by administrator')
            """, (order_id, order.status, admin_id))

            await db.commit()

        updated = await OrderRepository.get_order_by_id(order_id)
        return True, "Order approved successfully.", updated

    @staticmethod
    async def reject_order(order_id: int, admin_id: int, reason: str) -> Tuple[bool, str, Optional[Order]]:
        """
        Reject an order. If payment was verified, flags payment for refund review.
        """
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False, "Order not found.", None
                order = OrderRepository._row_to_order(row)

            if order.status in ("completed", "Completed"):
                return False, "Completed orders cannot be rejected.", order

            # Check if customer had already paid
            async with db.execute("SELECT id, status FROM payments WHERE order_id = ? ORDER BY submitted_at DESC LIMIT 1", (order_id,)) as cursor:
                pay_row = await cursor.fetchone()
                if pay_row and pay_row["status"] in ("verified", "Paid"):
                    # Record refund pending on payment
                    await db.execute("UPDATE payments SET status = 'refund_pending' WHERE id = ?", (pay_row["id"],))

            await db.execute("""
                UPDATE orders SET status = 'rejected', rejection_reason = ?, approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reason, admin_id, order_id))

            await db.execute("""
                INSERT INTO order_status_history (order_id, previous_status, new_status, changed_by, reason)
                VALUES (?, ?, 'rejected', ?, ?)
            """, (order_id, order.status, admin_id, f"Order rejected: {reason}"))

            await db.commit()

        updated = await OrderRepository.get_order_by_id(order_id)
        return True, "Order rejected.", updated

    @staticmethod
    async def start_order(order_id: int, admin_id: int) -> Tuple[bool, str, Optional[Order]]:
        """Transition order to in_progress. Guard: Order must be approved first."""
        order = await OrderRepository.get_order_by_id(order_id)
        if not order:
            return False, "Order not found.", None
        if order.status not in ("approved", "Approved"):
            return False, "Order must be approved before work can start.", order

        await OrderRepository.update_order_status(
            order_id=order_id,
            new_status="in_progress",
            changed_by=admin_id,
            reason="Work started by administrator"
        )
        updated = await OrderRepository.get_order_by_id(order_id)
        return True, "Work started.", updated

    @staticmethod
    async def complete_order(order_id: int, admin_id: int) -> Tuple[bool, str, Optional[Order]]:
        """Transition order to completed. Guard: Order must be in_progress."""
        order = await OrderRepository.get_order_by_id(order_id)
        if not order:
            return False, "Order not found.", None
        if order.status not in ("in_progress", "In Progress"):
            return False, "Order must be In Progress before it can be marked completed.", order

        await OrderRepository.update_order_status(
            order_id=order_id,
            new_status="completed",
            changed_by=admin_id,
            reason="Work completed by administrator"
        )
        updated = await OrderRepository.get_order_by_id(order_id)
        return True, "Order marked as completed.", updated

    @staticmethod
    async def cancel_order(order_id: int, admin_id: int, reason: str = "Cancelled by administrator") -> Tuple[bool, str, Optional[Order]]:
        """Cancel an order."""
        order = await OrderRepository.get_order_by_id(order_id)
        if not order:
            return False, "Order not found.", None
        if order.status in ("completed", "Completed"):
            return False, "Completed orders cannot be cancelled.", order

        async with get_db_connection() as db:
            async with db.execute("SELECT id, status FROM payments WHERE order_id = ? ORDER BY submitted_at DESC LIMIT 1", (order_id,)) as cursor:
                pay_row = await cursor.fetchone()
                if pay_row and pay_row["status"] in ("verified", "Paid"):
                    await db.execute("UPDATE payments SET status = 'refund_pending' WHERE id = ?", (pay_row["id"],))

            await db.execute("""
                UPDATE orders SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (order_id,))

            await db.execute("""
                INSERT INTO order_status_history (order_id, previous_status, new_status, changed_by, reason)
                VALUES (?, ?, 'cancelled', ?, ?)
            """, (order_id, order.status, admin_id, reason))

            await db.commit()

        updated = await OrderRepository.get_order_by_id(order_id)
        return True, "Order cancelled.", updated

    @staticmethod
    async def count_user_orders(user_id: int) -> Tuple[int, int]:
        """Return (total_orders, completed_orders) for a user."""
        async with get_db_connection() as db:
            async with db.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,)) as c1:
                total = (await c1.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND status IN ('completed', 'Completed')", (user_id,)) as c2:
                completed = (await c2.fetchone())[0]
            return total, completed

    @staticmethod
    async def get_dashboard_stats() -> Dict[str, Any]:
        async with get_db_connection() as db:
            async with db.execute("SELECT COUNT(*) FROM users") as c_users:
                total_users = (await c_users.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM orders") as c_orders:
                total_orders = (await c_orders.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM orders WHERE status IN ('payment_under_review', 'Payment Under Review')") as c_review:
                review_count = (await c_review.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM orders WHERE status IN ('paid', 'Paid', 'approved', 'Approved')") as c_paid:
                paid_count = (await c_paid.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM orders WHERE status IN ('in_progress', 'In Progress')") as c_prog:
                in_prog_count = (await c_prog.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM orders WHERE status IN ('completed', 'Completed')") as c_comp:
                comp_count = (await c_comp.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM orders WHERE status IN ('cancelled', 'Cancelled')") as c_canc:
                canc_count = (await c_canc.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM orders WHERE status IN ('rejected', 'Payment Rejected')") as c_rej:
                rej_count = (await c_rej.fetchone())[0]

            async with db.execute("SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE status IN ('paid', 'Paid', 'approved', 'Approved', 'in_progress', 'In Progress', 'completed', 'Completed')") as c_rev:
                total_revenue = (await c_rev.fetchone())[0]

            return {
                "total_users": total_users,
                "total_orders": total_orders,
                "awaiting_review": review_count,
                "paid_approved": paid_count,
                "in_progress": in_prog_count,
                "completed": comp_count,
                "cancelled": canc_count,
                "rejected": rej_count,
                "total_revenue": total_revenue
            }

class PaymentRepository:
    @staticmethod
    def _row_to_payment(r) -> Payment:
        d = dict(r)
        return Payment(
            id=d["id"],
            order_id=d["order_id"],
            payment_method=d["payment_method"],
            expected_amount=d["expected_amount"],
            transaction_reference=d.get("transaction_reference"),
            screenshot_file_id=d.get("screenshot_file_id"),
            status=d.get("status", "submitted"),
            submitted_at=d.get("submitted_at"),
            verified_by=d.get("verified_by"),
            verified_at=d.get("verified_at"),
            verification_notes=d.get("verification_notes"),
            rejection_reason=d.get("rejection_reason")
        )

    @staticmethod
    async def create_payment(
        order_id: int,
        payment_method: str,
        expected_amount: float,
        transaction_reference: Optional[str] = None,
        screenshot_file_id: Optional[str] = None
    ) -> Payment:
        async with get_db_connection() as db:
            cursor = await db.execute("""
                INSERT INTO payments (
                    order_id, payment_method, expected_amount,
                    transaction_reference, screenshot_file_id, status
                ) VALUES (?, ?, ?, ?, ?, 'submitted')
            """, (order_id, payment_method, expected_amount, transaction_reference, screenshot_file_id))
            payment_id = cursor.lastrowid

            # Also update order status to 'payment_under_review'
            await db.execute("""
                UPDATE orders SET status = 'payment_under_review', updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (order_id,))

            await db.execute("""
                INSERT INTO order_status_history (order_id, previous_status, new_status, reason)
                VALUES (?, 'pending_payment', 'payment_under_review', 'Customer submitted payment evidence')
            """, (order_id,))

            await db.commit()

            return Payment(
                id=payment_id,
                order_id=order_id,
                payment_method=payment_method,
                expected_amount=expected_amount,
                transaction_reference=transaction_reference,
                screenshot_file_id=screenshot_file_id,
                status="submitted"
            )

    @staticmethod
    async def is_reference_used(reference: str, exclude_payment_id: Optional[int] = None) -> bool:
        if not reference:
            return False
        async with get_db_connection() as db:
            query = "SELECT id FROM payments WHERE UPPER(transaction_reference) = ? AND status NOT IN ('rejected', 'Payment Rejected')"
            params = [reference.strip().upper()]
            if exclude_payment_id:
                query += " AND id != ?"
                params.append(exclude_payment_id)
            async with db.execute(query, params) as cursor:
                return (await cursor.fetchone()) is not None

    @staticmethod
    async def get_payment_by_id(payment_id: int) -> Optional[Payment]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)) as cursor:
                row = await cursor.fetchone()
                return PaymentRepository._row_to_payment(row) if row else None

    @staticmethod
    async def get_latest_payment_for_order(order_id: int) -> Optional[Payment]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM payments WHERE order_id = ? ORDER BY submitted_at DESC LIMIT 1", (order_id,)) as cursor:
                row = await cursor.fetchone()
                return PaymentRepository._row_to_payment(row) if row else None

    @staticmethod
    async def get_pending_payments(limit: int = 20) -> List[Tuple[Payment, Order]]:
        async with get_db_connection() as db:
            async with db.execute("""
                SELECT p.*, o.order_code, o.user_id, o.service_name_snapshot, o.quantity, o.total_price, o.target_link
                FROM payments p
                JOIN orders o ON p.order_id = o.id
                WHERE p.status IN ('submitted', 'Payment Under Review')
                ORDER BY p.submitted_at ASC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                results = []
                for r in rows:
                    pay = PaymentRepository._row_to_payment(r)
                    ord_obj = Order(
                        id=r["order_id"],
                        order_code=r["order_code"],
                        user_id=r["user_id"],
                        service_id=0,
                        service_name_snapshot=r["service_name_snapshot"],
                        unit_price_snapshot=0.0,
                        quantity=r["quantity"],
                        total_price=r["total_price"],
                        target_link=r["target_link"],
                        customer_notes=None,
                        status="payment_under_review"
                    )
                    results.append((pay, ord_obj))
                return results

    @staticmethod
    async def verify_payment(payment_id: int, admin_id: int, verification_notes: Optional[str] = None) -> bool:
        async with get_db_connection() as db:
            async with db.execute("SELECT order_id FROM payments WHERE id = ?", (payment_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False
                order_id = row["order_id"]

            await db.execute("""
                UPDATE payments SET status = 'verified', verified_by = ?, verified_at = CURRENT_TIMESTAMP, verification_notes = ?
                WHERE id = ?
            """, (admin_id, verification_notes, payment_id))

            await db.execute("""
                UPDATE orders SET status = 'paid', updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (order_id,))

            await db.execute("""
                INSERT INTO order_status_history (order_id, previous_status, new_status, changed_by, reason)
                VALUES (?, 'payment_under_review', 'paid', ?, ?)
            """, (order_id, admin_id, f"Payment verified: {verification_notes or 'Confirmed via transaction records'}"))

            await db.commit()
            return True

    @staticmethod
    async def reject_payment(payment_id: int, admin_id: int, reason: str) -> bool:
        async with get_db_connection() as db:
            async with db.execute("SELECT order_id FROM payments WHERE id = ?", (payment_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False
                order_id = row["order_id"]

            await db.execute("""
                UPDATE payments SET status = 'rejected', verified_by = ?, verified_at = CURRENT_TIMESTAMP, rejection_reason = ?
                WHERE id = ?
            """, (admin_id, reason, payment_id))

            await db.execute("""
                UPDATE orders SET status = 'pending_payment', updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (order_id,))

            await db.execute("""
                INSERT INTO order_status_history (order_id, previous_status, new_status, changed_by, reason)
                VALUES (?, 'payment_under_review', 'pending_payment', ?, ?)
            """, (order_id, admin_id, f"Payment rejected: {reason}"))

            await db.commit()
            return True

class UserRepository:
    @staticmethod
    async def upsert_user(telegram_id: int, username: Optional[str], first_name: Optional[str], language: Optional[str] = None) -> User:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    user_lang = language if language else row["language"]
                    await db.execute("""
                        UPDATE users SET username = ?, first_name = ?, language = ?
                        WHERE telegram_id = ?
                    """, (username, first_name, user_lang, telegram_id))
                    await db.commit()
                    return User(
                        id=row["id"],
                        telegram_id=telegram_id,
                        username=username,
                        first_name=first_name,
                        language=user_lang,
                        created_at=row["created_at"],
                        is_blocked=bool(row["is_blocked"])
                    )
                else:
                    user_lang = language or config.DEFAULT_LANGUAGE
                    cursor = await db.execute("""
                        INSERT INTO users (telegram_id, username, first_name, language)
                        VALUES (?, ?, ?, ?)
                    """, (telegram_id, username, first_name, user_lang))
                    user_id = cursor.lastrowid
                    await db.commit()
                    return User(
                        id=user_id,
                        telegram_id=telegram_id,
                        username=username,
                        first_name=first_name,
                        language=user_lang,
                        is_blocked=False
                    )

    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        id=row["id"],
                        telegram_id=row["telegram_id"],
                        username=row["username"],
                        first_name=row["first_name"],
                        language=row["language"],
                        created_at=row["created_at"],
                        is_blocked=bool(row["is_blocked"])
                    )
        return None

    @staticmethod
    async def set_language(telegram_id: int, language: str) -> bool:
        async with get_db_connection() as db:
            await db.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, telegram_id))
            await db.commit()
            return True

    @staticmethod
    async def count_users() -> int:
        async with get_db_connection() as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    @staticmethod
    async def get_all_users(limit: int = 50) -> List[User]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [
                    User(
                        id=r["id"],
                        telegram_id=r["telegram_id"],
                        username=r["username"],
                        first_name=r["first_name"],
                        language=r["language"],
                        created_at=r["created_at"],
                        is_blocked=bool(r["is_blocked"])
                    ) for r in rows
                ]


class AdminRepository:
    @staticmethod
    async def is_admin(telegram_id: int) -> bool:
        if config.is_admin(telegram_id):
            return True
        async with get_db_connection() as db:
            async with db.execute("SELECT 1 FROM admins WHERE telegram_id = ? AND is_active = 1", (telegram_id,)) as cursor:
                return (await cursor.fetchone()) is not None

    @staticmethod
    async def is_owner(telegram_id: int) -> bool:
        if config.is_owner(telegram_id):
            return True
        async with get_db_connection() as db:
            async with db.execute("SELECT 1 FROM admins WHERE telegram_id = ? AND role = 'owner' AND is_active = 1", (telegram_id,)) as cursor:
                return (await cursor.fetchone()) is not None

    @staticmethod
    async def get_all_admins() -> List[Admin]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM admins WHERE is_active = 1") as cursor:
                rows = await cursor.fetchall()
                return [
                    Admin(
                        id=r["id"],
                        telegram_id=r["telegram_id"],
                        role=r["role"],
                        created_at=r["created_at"],
                        is_active=bool(r["is_active"])
                    ) for r in rows
                ]


class ServiceRepository:
    @staticmethod
    def _row_to_service(r) -> Service:
        d = dict(r)
        d["is_active"] = bool(d.get("is_active", 1))
        return Service(**d)

    @staticmethod
    async def get_active_by_platform(platform: str) -> List[Service]:
        async with get_db_connection() as db:
            async with db.execute(
                "SELECT * FROM services WHERE platform = ? AND is_active = 1 ORDER BY price ASC",
                (platform,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [ServiceRepository._row_to_service(r) for r in rows]

    @staticmethod
    async def get_service_by_id(service_id: int) -> Optional[Service]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM services WHERE id = ?", (service_id,)) as cursor:
                row = await cursor.fetchone()
                return ServiceRepository._row_to_service(row) if row else None

    @staticmethod
    async def get_all_services() -> List[Service]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM services ORDER BY platform ASC, price ASC") as cursor:
                rows = await cursor.fetchall()
                return [ServiceRepository._row_to_service(r) for r in rows]

    @staticmethod
    async def add_service(
        name_en: str, name_am: str, platform: str,
        description_en: str, description_am: str,
        price: float, pricing_type: str = "fixed",
        minimum_quantity: int = 1, maximum_quantity: int = 100000,
        estimated_duration_en: str = "1-2 business days",
        estimated_duration_am: str = "1-2 የሥራ ቀናት"
    ) -> int:
        async with get_db_connection() as db:
            cursor = await db.execute("""
                INSERT INTO services (
                    name_en, name_am, platform, description_en, description_am,
                    price, pricing_type, minimum_quantity, maximum_quantity,
                    estimated_duration_en, estimated_duration_am, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                name_en, name_am, platform, description_en, description_am,
                price, pricing_type, minimum_quantity, maximum_quantity,
                estimated_duration_en, estimated_duration_am
            ))
            service_id = cursor.lastrowid
            await db.commit()
            return service_id

    @staticmethod
    async def update_service_price(service_id: int, new_price: float) -> bool:
        async with get_db_connection() as db:
            await db.execute(
                "UPDATE services SET price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_price, service_id)
            )
            await db.commit()
            return True

    @staticmethod
    async def toggle_service_active(service_id: int) -> bool:
        async with get_db_connection() as db:
            async with db.execute("SELECT is_active FROM services WHERE id = ?", (service_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False
                new_state = 0 if row["is_active"] else 1
            await db.execute(
                "UPDATE services SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_state, service_id)
            )
            await db.commit()
            return bool(new_state)


class PaymentMethodRepository:
    @staticmethod
    async def get_active_methods() -> List[PaymentMethod]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM payment_methods WHERE is_active = 1") as cursor:
                rows = await cursor.fetchall()
                return [PaymentMethod(**dict(r)) for r in rows]

    @staticmethod
    async def get_method_by_code(method_code: str) -> Optional[PaymentMethod]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM payment_methods WHERE method_code = ?", (method_code.lower(),)) as cursor:
                row = await cursor.fetchone()
                return PaymentMethod(**dict(row)) if row else None

    @staticmethod
    async def update_method_details(
        method_code: str,
        account_holder: str,
        account_number: str
    ) -> bool:
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE payment_methods SET account_holder = ?, account_number = ? WHERE method_code = ?
            """, (account_holder, account_number, method_code.lower()))
            await db.commit()
            return True


class SupportTicketRepository:
    @staticmethod
    async def create_ticket(user_id: int, message: str, order_id: Optional[int] = None) -> SupportTicket:
        async with get_db_connection() as db:
            cursor = await db.execute("""
                INSERT INTO support_tickets (user_id, order_id, message, status)
                VALUES (?, ?, ?, 'Open')
            """, (user_id, order_id, message))
            ticket_id = cursor.lastrowid
            ticket_code = format_ticket_code(ticket_id)
            await db.execute("UPDATE support_tickets SET ticket_code = ? WHERE id = ?", (ticket_code, ticket_id))
            await db.commit()
            return SupportTicket(
                id=ticket_id,
                ticket_code=ticket_code,
                user_id=user_id,
                order_id=order_id,
                message=message,
                admin_response=None,
                status="Open"
            )

    @staticmethod
    async def get_open_tickets(limit: int = 20) -> List[SupportTicket]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM support_tickets WHERE status = 'Open' ORDER BY created_at ASC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [SupportTicket(**dict(r)) for r in rows]

    @staticmethod
    async def get_ticket_by_code(ticket_code: str) -> Optional[SupportTicket]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM support_tickets WHERE ticket_code = ?", (ticket_code.strip().upper(),)) as cursor:
                row = await cursor.fetchone()
                return SupportTicket(**dict(row)) if row else None

    @staticmethod
    async def get_ticket_by_id(ticket_id: int) -> Optional[SupportTicket]:
        async with get_db_connection() as db:
            async with db.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,)) as cursor:
                row = await cursor.fetchone()
                return SupportTicket(**dict(row)) if row else None

    @staticmethod
    async def answer_ticket(ticket_id: int, response: str) -> bool:
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE support_tickets SET admin_response = ?, status = 'Answered', closed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (response, ticket_id))
            await db.commit()
            return True


class AuditLogRepository:
    @staticmethod
    async def log(admin_telegram_id: int, action: str, entity_type: Optional[str] = None, entity_id: Optional[str] = None, details: Optional[str] = None):
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO audit_logs (admin_telegram_id, action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (admin_telegram_id, action, entity_type, entity_id, details))
            await db.commit()
