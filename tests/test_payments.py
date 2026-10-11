"""
Integration and security tests for Payment processing and duplicate detection.
"""

import pytest
from pathlib import Path
import config

@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path):
    config.DATABASE_PATH = tmp_path / "test_abel_payments.db"
    from database.connection import init_db
    await init_db()
    yield

@pytest.mark.asyncio
async def test_payment_submission_and_duplicate_prevention():
    from database.repositories import UserRepository, ServiceRepository, OrderRepository, PaymentRepository

    user = await UserRepository.upsert_user(telegram_id=888001, username="payer", first_name="Payer")
    services = await ServiceRepository.get_active_by_platform("YouTube")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://youtube.com/c/test"
    )

    # Submit payment with reference FT998877
    payment = await PaymentRepository.create_payment(
        order_id=order.id,
        payment_method="CBE",
        expected_amount=order.total_price,
        transaction_reference="FT998877",
        screenshot_file_id="photo_file_123"
    )

    assert payment.id > 0
    assert payment.status in ("submitted", "Payment Under Review")

    # Verify order status transitioned to Payment Under Review
    order_updated = await OrderRepository.get_order_by_id(order.id)
    assert order_updated.status in ("payment_under_review", "Payment Under Review")

    # Security check: reference FT998877 is now flagged as used
    is_duplicate = await PaymentRepository.is_reference_used("FT998877")
    assert is_duplicate is True

    # Case-insensitive check
    assert await PaymentRepository.is_reference_used("ft998877") is True

    # Check unused reference
    assert await PaymentRepository.is_reference_used("NEW_REF_123") is False

@pytest.mark.asyncio
async def test_admin_payment_verification():
    from database.repositories import UserRepository, ServiceRepository, OrderRepository, PaymentRepository

    user = await UserRepository.upsert_user(telegram_id=888002, username="payer2", first_name="Payer2")
    services = await ServiceRepository.get_active_by_platform("Instagram")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/p/test"
    )

    payment = await PaymentRepository.create_payment(
        order_id=order.id,
        payment_method="Telebirr",
        expected_amount=order.total_price,
        transaction_reference="TB112233"
    )

    # Admin verifies payment
    admin_id = 999999
    success = await PaymentRepository.verify_payment(payment.id, admin_id)
    assert success is True

    # Check payment and order updated
    verified_pay = await PaymentRepository.get_payment_by_id(payment.id)
    assert verified_pay.status in ("verified", "Paid")
    assert verified_pay.verified_by == admin_id

    verified_ord = await OrderRepository.get_order_by_id(order.id)
    assert verified_ord.status in ("paid", "Paid")
