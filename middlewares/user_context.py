"""
User context middleware for aiogram 3.
Ensures every incoming event registers or retrieves the user and sets the user's preferred language.
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery
from database.repositories import UserRepository
from database.models import User
import config

class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        tg_user: TgUser = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        # Upsert or fetch user
        user = await UserRepository.get_user_by_telegram_id(tg_user.id)
        if not user:
            user = await UserRepository.upsert_user(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                language=config.DEFAULT_LANGUAGE
            )
        else:
            # Sync any username/first_name changes silently
            if user.username != tg_user.username or user.first_name != tg_user.first_name:
                user = await UserRepository.upsert_user(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    language=user.language
                )

        if user.is_blocked:
            if isinstance(event, Message):
                await event.answer("⛔ Your account has been suspended. Please contact support.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Your account has been suspended.", show_alert=True)
            return

        data["user"] = user
        data["lang"] = user.language or config.DEFAULT_LANGUAGE
        return await handler(event, data)
