"""
Security and permissions tests for Abel Promotion bot.
"""

import pytest
from pathlib import Path
import config

@pytest.fixture(autouse=True)
async def setup_test_db(tmp_path):
    config.DATABASE_PATH = tmp_path / "test_abel_permissions.db"
    config.ADMIN_IDS = {111222, 333444}
    config.OWNER_ID = 111222
    from database.connection import init_db
    await init_db()
    yield

@pytest.mark.asyncio
async def test_admin_and_owner_permissions():
    from database.repositories import AdminRepository

    assert await AdminRepository.is_admin(111222) is True
    assert await AdminRepository.is_admin(333444) is True
    assert await AdminRepository.is_admin(999999) is False

    assert await AdminRepository.is_owner(111222) is True
    assert await AdminRepository.is_owner(333444) is False

@pytest.mark.asyncio
async def test_order_privacy_isolation():
    from database.repositories import UserRepository, ServiceRepository, OrderRepository

    user_a = await UserRepository.upsert_user(telegram_id=1001, username="usera", first_name="A")
    user_b = await UserRepository.upsert_user(telegram_id=1002, username="userb", first_name="B")

    services = await ServiceRepository.get_active_by_platform("Instagram")
    service = services[0]

    order_a = await OrderRepository.create_order(
        user_id=user_a.telegram_id,
        service_id=service.id,
        service_name_snapshot=service.name_en,
        unit_price_snapshot=service.price,
        quantity=1,
        total_price=service.price,
        target_link="https://instagram.com/a"
    )

    # Customer A orders list contains order_a
    orders_a = await OrderRepository.get_user_orders(user_a.telegram_id)
    assert any(o.id == order_a.id for o in orders_a)

    # Customer B orders list must NOT contain order_a
    orders_b = await OrderRepository.get_user_orders(user_b.telegram_id)
    assert not any(o.id == order_a.id for o in orders_b)
