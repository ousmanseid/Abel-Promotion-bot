"""
Tests for Support Tickets, Language updates, and Admin catalog actions.
"""

import pytest
from pathlib import Path
import config

@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path):
    config.DATABASE_PATH = tmp_path / "test_abel_admin.db"
    from database.connection import init_db
    await init_db()
    yield

@pytest.mark.asyncio
async def test_support_ticket_flow():
    from database.repositories import UserRepository, SupportTicketRepository

    user = await UserRepository.upsert_user(telegram_id=777001, username="helpmeplease", first_name="Help")
    ticket = await SupportTicketRepository.create_ticket(
        user_id=user.telegram_id,
        message="Need assistance regarding my order.",
        order_id=1001
    )

    assert ticket.id > 0
    assert ticket.ticket_code == f"TICKET-{100 + ticket.id}"
    assert ticket.status == "Open"

    # Admin responds
    success = await SupportTicketRepository.answer_ticket(ticket.id, "We have verified your details.")
    assert success is True

    updated_tkt = await SupportTicketRepository.get_ticket_by_id(ticket.id)
    assert updated_tkt.status == "Answered"
    assert updated_tkt.admin_response == "We have verified your details."

@pytest.mark.asyncio
async def test_language_switch_persistence():
    from database.repositories import UserRepository

    user = await UserRepository.upsert_user(telegram_id=777002, username="bilingual", first_name="Bi", language="en")
    assert user.language == "en"

    # Switch to Amharic
    await UserRepository.set_language(user.telegram_id, "am")
    reloaded = await UserRepository.get_user_by_telegram_id(user.telegram_id)
    assert reloaded.language == "am"

@pytest.mark.asyncio
async def test_admin_service_catalog_management():
    from database.repositories import ServiceRepository

    # Add custom service
    new_id = await ServiceRepository.add_service(
        name_en="TikTok Brand Consultation",
        name_am="የቲክቶክ ብራንድ ምክክር",
        platform="TikTok",
        description_en="Consultation on brand strategy",
        description_am="የብራንድ ስትራቴጂ ምክክር",
        price=600.0
    )
    assert new_id > 0

    svc = await ServiceRepository.get_service_by_id(new_id)
    assert svc is not None
    assert svc.price == 600.0
    assert svc.is_active is True

    # Deactivate
    is_active = await ServiceRepository.toggle_service_active(new_id)
    assert is_active is False

    # Price update
    await ServiceRepository.update_service_price(new_id, 750.0)
    updated_svc = await ServiceRepository.get_service_by_id(new_id)
    assert updated_svc.price == 750.0

@pytest.mark.asyncio
async def test_payment_rejection_flow():
    from database.repositories import UserRepository, ServiceRepository, OrderRepository, PaymentRepository

    user = await UserRepository.upsert_user(telegram_id=777003, username="reject_test", first_name="R")
    services = await ServiceRepository.get_active_by_platform("Facebook")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://facebook.com/r"
    )

    payment = await PaymentRepository.create_payment(
        order_id=order.id,
        payment_method="CBE",
        expected_amount=order.total_price,
        transaction_reference="INVALID_TXN_REF"
    )

    # Reject payment with reason
    reason = "Transaction reference was not found in CBE account records"
    success = await PaymentRepository.reject_payment(payment.id, admin_id=12345, reason=reason)
    assert success is True

    pay_reloaded = await PaymentRepository.get_payment_by_id(payment.id)
    assert pay_reloaded.status in ("rejected", "Payment Rejected")
    assert pay_reloaded.rejection_reason == reason

    ord_reloaded = await OrderRepository.get_order_by_id(order.id)
    assert ord_reloaded.status in ("pending_payment", "rejected", "Payment Rejected")
