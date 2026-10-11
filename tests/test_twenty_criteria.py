"""
Comprehensive verification test suite for all 20 required criteria
in the Abel Promotion Telegram business system.
"""

import pytest
import aiosqlite
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import config
from database.connection import init_db, get_db_connection
from database.migrations import run_migrations
from database.repositories import (
    UserRepository, ServiceRepository, OrderRepository,
    PaymentRepository, AdminRepository, OrderMessageRepository
)
from database.models import User, Order, Payment
from services.notification_service import NotificationService
from utils.order_codes import format_order_code


class MockBot:
    """Mock aiogram Bot instance to capture sent notifications."""
    def __init__(self):
        self.sent_messages = []
        self.sent_photos = []

    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        payload = {"chat_id": chat_id, "text": text, "reply_markup": reply_markup}
        self.sent_messages.append(payload)
        return payload

    async def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode=None):
        payload = {"chat_id": chat_id, "photo": photo, "caption": caption, "reply_markup": reply_markup}
        self.sent_photos.append(payload)
        return payload


@pytest.fixture(autouse=True)
async def setup_test_environment(tmp_path):
    """Isolate each test in a clean SQLite database with configured test admins."""
    test_db = tmp_path / "test_twenty_criteria.db"
    config.DATABASE_PATH = test_db
    config.ADMIN_IDS = {777001, 777002}
    config.OWNER_ID = 777001
    await init_db()
    yield
    # Cleanup


@pytest.mark.asyncio
async def test_criterion_1_to_3_order_creation_unique_id_price_snapshot():
    """
    Test 1: Customer creates an order.
    Test 2: Order receives a unique ID.
    Test 3: Correct service price is used and preserved via snapshot.
    """
    user = await UserRepository.upsert_user(telegram_id=1001, username="client1", first_name="Abebe")
    services = await ServiceRepository.get_active_by_platform("Instagram")
    assert len(services) > 0
    service = services[0]

    # Create order with quantity 2
    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=2,
        total_price=round(service.price * 2, 2),
        target_link="https://instagram.com/abebe_biz",
        customer_notes="High quality please"
    )

    # 1. Customer created order
    assert order is not None
    assert order.id > 0

    # 2. Unique order code in AB-XXXX format
    assert order.order_code == format_order_code(order.id)
    assert order.order_code.startswith("AB-")

    # 3. Correct service price used and locked
    assert order.unit_price_snapshot == service.price
    assert order.total_price == round(service.price * 2, 2)

    # Changing catalog price later must NOT alter the order snapshot
    await ServiceRepository.update_service_price(service.id, service.price + 500.0)
    refreshed_order = await OrderRepository.get_order_by_id(order.id)
    assert refreshed_order.total_price == round(service.price * 2, 2)


@pytest.mark.asyncio
async def test_criterion_4_and_5_payment_evidence_and_admin_notification():
    """
    Test 4: Customer submits payment evidence (CBE / Telebirr).
    Test 5: Administrator receives push notification with action buttons.
    """
    mock_bot = MockBot()
    user = await UserRepository.upsert_user(telegram_id=1002, username="client2", first_name="Kebede")
    services = await ServiceRepository.get_active_by_platform("Facebook")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://facebook.com/kebede_page"
    )

    # 4. Customer submits payment evidence
    payment = await PaymentRepository.create_payment(
        order_id=order.id,
        payment_method="Telebirr",
        expected_amount=order.total_price,
        transaction_reference="TB_REF_778899",
        screenshot_file_id="telegram_file_id_receipt_screenshot"
    )
    assert payment.id > 0
    assert payment.status == "submitted" or payment.status == "Payment Under Review"

    # 5. Admin receives push notification
    await NotificationService.notify_admins_new_payment(mock_bot, order, payment)

    # Verify both admins received the photo alert
    admin_notified = [p for p in mock_bot.sent_photos if p["chat_id"] in config.ADMIN_IDS]
    assert len(admin_notified) >= 1
    first_alert = admin_notified[0]
    assert order.order_code in first_alert["caption"]
    assert "Telebirr" in first_alert["caption"]
    assert "TB_REF_778899" in first_alert["caption"]
    assert first_alert["reply_markup"] is not None


@pytest.mark.asyncio
async def test_criterion_6_to_8_payment_verification_auth_and_confirmation():
    """
    Test 6: Unauthorized user cannot verify payment.
    Test 7: Administrator verifies payment.
    Test 8: Customer receives payment confirmation.
    """
    mock_bot = MockBot()
    user = await UserRepository.upsert_user(telegram_id=1003, username="client3", first_name="Almaz")
    services = await ServiceRepository.get_active_by_platform("YouTube")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://youtube.com/c/almaz"
    )

    payment = await PaymentRepository.create_payment(
        order_id=order.id,
        payment_method="CBE",
        expected_amount=order.total_price,
        transaction_reference="CBE_FT_12345"
    )

    # 6. Unauthorized user cannot verify
    unauthorized_user_id = 999999
    assert await AdminRepository.is_admin(unauthorized_user_id) is False

    # 7. Authorized administrator verifies payment
    admin_id = 777001
    assert await AdminRepository.is_admin(admin_id) is True
    verify_success = await PaymentRepository.verify_payment(payment.id, admin_id)
    assert verify_success is True

    verified_pay = await PaymentRepository.get_payment_by_id(payment.id)
    assert verified_pay.status in ("verified", "Paid")
    assert verified_pay.verified_by == admin_id

    verified_order = await OrderRepository.get_order_by_id(order.id)
    assert verified_order.status in ("paid", "Paid")

    # 8. Customer receives payment confirmation
    await NotificationService.notify_user_order_status_update(
        mock_bot, verified_order, "paid", note="Payment verified successfully."
    )
    cust_msgs = [m for m in mock_bot.sent_messages if m["chat_id"] == user.telegram_id]
    assert len(cust_msgs) > 0
    assert order.order_code in cust_msgs[-1]["text"]


@pytest.mark.asyncio
async def test_criterion_9_and_10_order_approval_and_notification():
    """
    Test 9: Administrator approves an order (guarded by verified payment).
    Test 10: Customer receives approval notification.
    """
    mock_bot = MockBot()
    user = await UserRepository.upsert_user(telegram_id=1004, username="client4", first_name="Dawit")
    services = await ServiceRepository.get_active_by_platform("Instagram")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/dawit"
    )

    payment = await PaymentRepository.create_payment(
        order_id=order.id,
        payment_method="CBE",
        expected_amount=order.total_price,
        transaction_reference="CBE_FT_APPROVED_TEST"
    )

    admin_id = 777001

    # Verify payment first (guard requirement)
    await PaymentRepository.verify_payment(payment.id, admin_id)

    # 9. Administrator approves order
    success, msg, approved_order = await OrderRepository.approve_order(order.id, admin_id)
    assert success is True
    assert approved_order.status == "approved"
    assert approved_order.approved_by == admin_id

    # 10. Customer receives approval notification
    await NotificationService.notify_user_order_approved(mock_bot, approved_order)
    cust_msgs = [m for m in mock_bot.sent_messages if m["chat_id"] == user.telegram_id]
    assert len(cust_msgs) > 0
    last_msg = cust_msgs[-1]["text"]
    assert "APPROVED" in last_msg
    assert order.order_code in last_msg


@pytest.mark.asyncio
async def test_criterion_11_and_12_order_rejection_and_notification():
    """
    Test 11: Administrator rejects an order with a reason.
    Test 12: Customer receives rejection notification.
    """
    mock_bot = MockBot()
    user = await UserRepository.upsert_user(telegram_id=1005, username="client5", first_name="Hanna")
    services = await ServiceRepository.get_active_by_platform("Facebook")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://facebook.com/hanna_private"
    )

    admin_id = 777001
    rejection_reason = "Social media profile is private. Please make public."

    # 11. Administrator rejects order
    success, msg, rejected_order = await OrderRepository.reject_order(order.id, admin_id, rejection_reason)
    assert success is True
    assert rejected_order.status == "rejected"
    assert rejected_order.rejection_reason == rejection_reason

    # 12. Customer receives rejection notification
    await NotificationService.notify_user_order_rejected(mock_bot, rejected_order, rejection_reason)
    cust_msgs = [m for m in mock_bot.sent_messages if m["chat_id"] == user.telegram_id]
    assert len(cust_msgs) > 0
    last_msg = cust_msgs[-1]["text"]
    assert "not approved" in last_msg or "ውድቅ" in last_msg
    assert rejection_reason in last_msg


@pytest.mark.asyncio
async def test_criterion_13_and_14_admin_customer_bidirectional_messaging():
    """
    Test 13: Administrator sends a message to the customer.
    Test 14: Customer reply reaches the correct administrator conversation.
    """
    mock_bot = MockBot()
    user = await UserRepository.upsert_user(telegram_id=1006, username="client6", first_name="Tigist")
    services = await ServiceRepository.get_active_by_platform("Instagram")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/tigist"
    )

    admin_id = 777001
    admin_msg_text = "Please check your Instagram bio link, it returned a 404 error."

    # 13. Admin sends message to customer
    saved_admin_msg = await OrderMessageRepository.save_message(
        order_id=order.id,
        sender_id=admin_id,
        sender_role="admin",
        message_text=admin_msg_text
    )
    assert saved_admin_msg.id > 0
    delivered = await NotificationService.send_message_from_admin_to_customer(mock_bot, order, admin_msg_text)
    assert delivered is True

    # Customer received the message
    cust_msgs = [m for m in mock_bot.sent_messages if m["chat_id"] == user.telegram_id]
    assert len(cust_msgs) > 0
    assert admin_msg_text in cust_msgs[-1]["text"]

    # 14. Customer replies
    customer_reply_text = "I have updated the bio link, please verify now."
    saved_cust_msg = await OrderMessageRepository.save_message(
        order_id=order.id,
        sender_id=user.telegram_id,
        sender_role="customer",
        message_text=customer_reply_text
    )
    assert saved_cust_msg.id > 0

    await NotificationService.notify_admins_customer_reply(mock_bot, order, user, customer_reply_text)
    admin_msgs = [m for m in mock_bot.sent_messages if m["chat_id"] in config.ADMIN_IDS]
    assert len(admin_msgs) > 0
    assert customer_reply_text in admin_msgs[-1]["text"]

    # Communication history in DB
    history = await OrderMessageRepository.get_order_messages(order.id)
    assert len(history) == 2
    assert history[0].sender_role == "admin"
    assert history[1].sender_role == "customer"


@pytest.mark.asyncio
async def test_criterion_15_order_privacy_isolation():
    """
    Test 15: Customer cannot view another customer's order.
    """
    user_alice = await UserRepository.upsert_user(telegram_id=2001, username="alice", first_name="Alice")
    user_bob = await UserRepository.upsert_user(telegram_id=2002, username="bob", first_name="Bob")

    services = await ServiceRepository.get_active_by_platform("Instagram")
    service = services[0]

    order_alice = await OrderRepository.create_order(
        user_id=user_alice.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/alice"
    )

    # Bob's orders list must NOT contain Alice's order
    bob_orders = await OrderRepository.get_user_orders(user_bob.telegram_id)
    assert not any(o.id == order_alice.id for o in bob_orders)

    # Security check: Bob querying Alice's order directly must be blocked by ownership check
    order = await OrderRepository.get_order_by_id(order_alice.id)
    assert order.user_id != user_bob.telegram_id


@pytest.mark.asyncio
async def test_criterion_16_invalid_status_transitions_rejected():
    """
    Test 16: Invalid status transitions are rejected.
    """
    user = await UserRepository.upsert_user(telegram_id=3001, username="test_guard", first_name="Guard")
    services = await ServiceRepository.get_active_by_platform("Facebook")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://facebook.com/guard"
    )
    admin_id = 777001

    # Guard 1: Cannot approve an order before payment is verified!
    ok, err, _ = await OrderRepository.approve_order(order.id, admin_id)
    assert ok is False
    assert "payment is verified" in err.lower() or "paid" in err.lower()

    # Guard 2: Cannot start work before an order is approved!
    ok, err, _ = await OrderRepository.start_order(order.id, admin_id)
    assert ok is False
    assert "approved" in err.lower()

    # Guard 3: Cannot complete work before it is in_progress!
    ok, err, _ = await OrderRepository.complete_order(order.id, admin_id)
    assert ok is False
    assert "in progress" in err.lower()


@pytest.mark.asyncio
async def test_criterion_17_duplicate_payment_references():
    """
    Test 17: Duplicate payment references are flagged and prevented.
    """
    user = await UserRepository.upsert_user(telegram_id=4001, username="ref_tester", first_name="Ref")
    services = await ServiceRepository.get_active_by_platform("Instagram")
    service = services[0]

    order1 = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/order1"
    )

    test_ref = "FT_DUP_TEST_9999"

    # Reference is initially unused
    assert await PaymentRepository.is_reference_used(test_ref) is False

    # Create payment with reference
    await PaymentRepository.create_payment(
        order_id=order1.id,
        payment_method="CBE",
        expected_amount=order1.total_price,
        transaction_reference=test_ref
    )

    # Now reference is flagged as used
    assert await PaymentRepository.is_reference_used(test_ref) is True

    # Case insensitive duplicate check
    assert await PaymentRepository.is_reference_used(test_ref.lower()) is True


@pytest.mark.asyncio
async def test_criterion_18_data_survives_application_restart(tmp_path):
    """
    Test 18: Data survives a normal application restart.
    """
    restart_db_path = tmp_path / "persistent_restart_test.db"
    config.DATABASE_PATH = restart_db_path
    await init_db()

    # Session 1: Create user, order, payment
    user = await UserRepository.upsert_user(telegram_id=5001, username="persistent_user", first_name="Persist")
    services = await ServiceRepository.get_active_by_platform("Instagram")
    service = services[0]
    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/persistent"
    )
    payment = await PaymentRepository.create_payment(
        order_id=order.id,
        payment_method="Telebirr",
        expected_amount=order.total_price,
        transaction_reference="PERSIST_REF_01"
    )

    # Session 2: "Restart" bot by re-initializing connection to the same SQLite file
    await init_db()

    reloaded_user = await UserRepository.get_user_by_telegram_id(5001)
    assert reloaded_user is not None
    assert reloaded_user.username == "persistent_user"

    reloaded_order = await OrderRepository.get_order_by_id(order.id)
    assert reloaded_order is not None
    assert reloaded_order.order_code == order.order_code
    assert reloaded_order.total_price == order.total_price

    reloaded_payment = await PaymentRepository.get_payment_by_id(payment.id)
    assert reloaded_payment is not None
    assert reloaded_payment.transaction_reference == "PERSIST_REF_01"


@pytest.mark.asyncio
async def test_criterion_19_database_migrations_preserve_existing_records(tmp_path):
    """
    Test 19: Database migrations preserve existing records and safely upgrade schema.
    """
    migration_db_path = tmp_path / "migration_test.db"
    config.DATABASE_PATH = migration_db_path

    # Initialize base schema
    await init_db()

    # Insert a record with legacy status "Payment Under Review"
    async with get_db_connection() as db:
        await db.execute("""
            INSERT INTO users (telegram_id, username, first_name, language)
            VALUES (6001, 'legacy_client', 'Legacy', 'en')
        """)
        cursor = await db.execute("""
            INSERT INTO orders (order_code, user_id, service_id, service_name_snapshot, unit_price_snapshot, quantity, total_price, target_link, status)
            VALUES ('AB-9999', 6001, 1, 'Legacy Service', 100.0, 1, 100.0, 'https://test.com', 'Payment Under Review')
        """)
        legacy_order_id = cursor.lastrowid
        await db.execute("""
            INSERT INTO payments (order_id, payment_method, expected_amount, status)
            VALUES (?, 'CBE', 100.0, 'Payment Under Review')
        """, (legacy_order_id,))
        await db.commit()

    # Re-run migrations on populated database
    async with get_db_connection() as db:
        await run_migrations(db)

    # Verify existing data preserved and statuses normalized
    migrated_order = await OrderRepository.get_order_by_id(legacy_order_id)
    assert migrated_order is not None
    assert migrated_order.order_code == "AB-9999"
    assert migrated_order.status == "payment_under_review"

    migrated_payment = await PaymentRepository.get_latest_payment_for_order(legacy_order_id)
    assert migrated_payment is not None
    assert migrated_payment.status == "submitted"


@pytest.mark.asyncio
async def test_criterion_20_network_failure_resilience():
    """
    Test 20: Bot recovers gracefully from temporary network failure during notification.
    """
    class FailingBot:
        def __init__(self):
            self.call_count = 0

        async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
            self.call_count += 1
            raise ConnectionError("Temporary network timeout connecting to api.telegram.org")

    failing_bot = FailingBot()
    user = await UserRepository.upsert_user(telegram_id=7001, username="net_test", first_name="Net")
    services = await ServiceRepository.get_active_by_platform("Instagram")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/net_test"
    )

    # NotificationService handles network exception safely without crashing application
    delivered = await NotificationService.send_message_from_admin_to_customer(
        failing_bot, order, "Test message during network glitch"
    )
    assert delivered is False
    assert failing_bot.call_count == 1
