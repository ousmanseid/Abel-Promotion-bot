"""
Integration and database tests for Order management.
"""

import pytest
from pathlib import Path
import config

@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path):
    config.DATABASE_PATH = tmp_path / "test_abel.db"
    from database.connection import init_db
    await init_db()
    yield

@pytest.mark.asyncio
async def test_order_creation_and_snapshot():
    from database.repositories import UserRepository, ServiceRepository, OrderRepository
    from utils.order_codes import format_order_code

    # Create user
    user = await UserRepository.upsert_user(telegram_id=999001, username="test_client", first_name="Test")
    assert user.telegram_id == 999001

    # Fetch active services
    services = await ServiceRepository.get_active_by_platform("Instagram")
    assert len(services) > 0
    service = services[0]

    # Create order
    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/my_business_page",
        customer_notes="Please optimize bio"
    )

    assert order.id > 0
    assert order.order_code == format_order_code(order.id)
    assert order.status in ("pending_payment", "Awaiting Payment")
    assert order.service_name_snapshot == service.name_en
    assert order.unit_price_snapshot == service.price

    # Verify order retrieval by code
    retrieved = await OrderRepository.get_order_by_code(order.order_code)
    assert retrieved is not None
    assert retrieved.id == order.id

    # Verify changing catalog price does not affect snapshot of existing order
    await ServiceRepository.update_service_price(service.id, 9999.0)
    order_after_price_change = await OrderRepository.get_order_by_id(order.id)
    assert order_after_price_change.unit_price_snapshot == service.price
    assert order_after_price_change.total_price == service.price

@pytest.mark.asyncio
async def test_order_status_transitions():
    from database.repositories import UserRepository, ServiceRepository, OrderRepository

    user = await UserRepository.upsert_user(telegram_id=999002, username="test_client2", first_name="Test2")
    services = await ServiceRepository.get_active_by_platform("Facebook")
    service = services[0]

    order = await OrderRepository.create_order(
        user_id=user.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=2,
        total_price=service.price * 2,
        target_link="https://facebook.com/my_page"
    )

    # Transition to In Progress
    success = await OrderRepository.update_order_status(order.id, "In Progress", changed_by=12345, reason="Started work")
    assert success is True

    updated_order = await OrderRepository.get_order_by_id(order.id)
    assert updated_order.status == "In Progress"

    # Transition to Completed
    await OrderRepository.update_order_status(order.id, "Completed", changed_by=12345, reason="Delivered")
    completed_order = await OrderRepository.get_order_by_id(order.id)
    assert completed_order.status == "Completed"
