"""
Database migrations module for Abel Promotion bot.
Safely upgrades SQLite schema, preserves existing records, and normalizes statuses.
"""

import logging
import aiosqlite

logger = logging.getLogger(__name__)

async def run_migrations(db: aiosqlite.Connection) -> None:
    """Run incremental migrations on SQLite database without data loss."""
    logger.info("Running database migrations...")

    # 1. Ensure order_messages table exists
    await db.execute("""
        CREATE TABLE IF NOT EXISTS order_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            sender_role TEXT NOT NULL,
            message_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_order_messages_order_id ON order_messages(order_id);")

    # 2. Check and add columns to orders table if missing
    async with db.execute("PRAGMA table_info(orders);") as cursor:
        columns = [row[1] for row in await cursor.fetchall()]

    if "approved_by" not in columns:
        await db.execute("ALTER TABLE orders ADD COLUMN approved_by INTEGER;")
        logger.info("Added approved_by column to orders table.")

    if "approved_at" not in columns:
        await db.execute("ALTER TABLE orders ADD COLUMN approved_at TIMESTAMP;")
        logger.info("Added approved_at column to orders table.")

    if "rejection_reason" not in columns:
        await db.execute("ALTER TABLE orders ADD COLUMN rejection_reason TEXT;")
        logger.info("Added rejection_reason column to orders table.")

    # 3. Check and add columns to payments table if missing
    async with db.execute("PRAGMA table_info(payments);") as cursor:
        pay_columns = [row[1] for row in await cursor.fetchall()]

    if "verification_notes" not in pay_columns:
        await db.execute("ALTER TABLE payments ADD COLUMN verification_notes TEXT;")
        logger.info("Added verification_notes column to payments table.")

    # 4. Normalize legacy status values to standardized lowercase keys
    status_order_map = {
        "Awaiting Payment": "pending_payment",
        "Payment Under Review": "payment_under_review",
        "Paid": "paid",
        "Approved": "approved",
        "In Progress": "in_progress",
        "Completed": "completed",
        "Cancelled": "cancelled",
        "Payment Rejected": "rejected",
        "Refund Review": "refund_pending",
        "Refunded": "refunded",
    }
    for old_s, new_s in status_order_map.items():
        await db.execute("UPDATE orders SET status = ? WHERE status = ?;", (new_s, old_s))

    status_pay_map = {
        "Payment Under Review": "submitted",
        "Paid": "verified",
        "Payment Rejected": "rejected",
        "Refund Review": "refund_pending",
        "Refunded": "refunded",
    }
    for old_s, new_s in status_pay_map.items():
        await db.execute("UPDATE payments SET status = ? WHERE status = ?;", (new_s, old_s))

    await db.commit()
    logger.info("Database migrations completed successfully.")
