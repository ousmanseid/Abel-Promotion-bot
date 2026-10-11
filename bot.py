"""
Main entry point for Abel Promotion Telegram Bot.
Initializes aiogram 3 Bot, Dispatcher, SQLite database, middlewares, and routers.
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database.connection import init_db
from middlewares.user_context import UserContextMiddleware

# Import handlers
from handlers.start import router as start_router
from handlers.language import router as language_router
from handlers.menu import router as menu_router
from handlers.services import router as services_router
from handlers.orders import router as orders_router
from handlers.payments import router as payments_router
from handlers.profile import router as profile_router
from handlers.support import router as support_router
from handlers.admin import router as admin_router

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("abel_promotion")

async def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_bot_token_here":
        logger.error(
            "\n"
            "===============================================================\n"
            "❌ BOT_TOKEN is missing or not configured!\n"
            "Please create a `.env` file or export BOT_TOKEN with your\n"
            "Telegram bot token from @BotFather.\n"
            "Example in .env:\n"
            "BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ\n"
            "ADMIN_IDS=123456789\n"
            "==============================================================="
        )
        sys.exit(1)

    logger.info("Initializing SQLite database...")
    await init_db()
    logger.info("Database initialized successfully.")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register global UserContextMiddleware
    dp.message.outer_middleware(UserContextMiddleware())
    dp.callback_query.outer_middleware(UserContextMiddleware())

    # Include routers in order
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(language_router)
    dp.include_router(menu_router)
    dp.include_router(services_router)
    dp.include_router(orders_router)
    dp.include_router(payments_router)
    dp.include_router(profile_router)
    dp.include_router(support_router)

    logger.info("Starting Abel Promotion bot long polling...")
    try:
        # Delete webhook if previously set to ensure polling operates cleanly
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
