"""
Admin Authorization Middleware / Filter for Abel Promotion bot.
Ensures only verified administrators can access administrative handlers.
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.repositories import AdminRepository
from utils.localization import t

class AdminAuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("user")
        lang = data.get("lang", "en")
        user_id = user.telegram_id if user else (event.from_user.id if hasattr(event, "from_user") and event.from_user else 0)

        is_authorized = await AdminRepository.is_admin(user_id)
        if not is_authorized:
            denied_msg = t("unauthorized_admin", lang=lang)
            if isinstance(event, Message):
                await event.answer(denied_msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(denied_msg, show_alert=True)
            return

        return await handler(event, data)
