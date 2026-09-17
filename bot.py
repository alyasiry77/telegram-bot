import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from engine import async_session, init_db, engine

logger = logging.getLogger(__name__)

async def create_bot_and_dispatcher():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # استيراد آمن للهاندلرز لتجنب أي خطأ مفقود
    try:
        from handlers import start, menu
        dp.include_router(start.router)
        dp.include_router(menu.router)
    except Exception as e:
        logger.warning(f"Routers load warning: {e}")

    @dp.error()
    async def error_handler(event, exception):
        logger.exception(f"Error: {exception}")
        return True

    return bot, dp

async def on_startup(bot: Bot):
    logger.info("🚀 Bot starting...")
    await init_db()
    logger.info("✅ Database initialized")

async def on_shutdown(bot: Bot):
    logger.info("🛑 Bot shutting down...")
    await engine.dispose()
