"""
Customer profile handler for Abel Promotion bot.
"""

from aiogram import Router, types, F
from database.models import User
from database.repositories import OrderRepository
from utils.localization import t

router = Router(name="profile_router")

@router.message(F.text.in_(["👤 My Profile", "👤 መለያዬ"]))
async def show_profile(message: types.Message, user: User, lang: str):
    """Display user profile details and statistics."""
    total_orders, completed_orders = await OrderRepository.count_user_orders(user.telegram_id)

    profile_text = t(
        "profile_text",
        lang=lang,
        telegram_id=user.telegram_id,
        name=user.first_name or "N/A",
        username=f"@{user.username}" if user.username else "None",
        language="English (EN)" if lang == "en" else "አማርኛ (AM)",
        total_orders=total_orders,
        completed_orders=completed_orders,
        joined_date=user.created_at[:10] if user.created_at else "Recently"
    )

    await message.answer(profile_text, parse_mode="Markdown")
