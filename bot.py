import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
# For persistence after restart, states are not critical but DB persists.
# Optionally use Redis storage if REDIS_URL set.
from bot.app.config import settings
from bot.app.database.engine import async_session, init_db, engine
from bot.app.middlewares.throttling import ThrottlingMiddleware
from bot.app.middlewares.user import MaintenanceMiddleware

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    # Hide token
    logging.getLogger("aiogram").setLevel(logging.INFO)

async def create_bot_and_dispatcher():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    # Redis FSM if available, fallback Memory
    try:
        from aiogram.fsm.storage.redis import RedisStorage
        from redis.asyncio import Redis
        if settings.redis_url and "redis" in settings.redis_url:
            redis = Redis.from_url(settings.redis_url)
            storage = RedisStorage(redis)
        else:
            storage = MemoryStorage()
    except Exception:
        storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(ThrottlingMiddleware(rate=0.4))
    dp.callback_query.middleware(ThrottlingMiddleware(rate=0.2))
    dp.message.middleware(MaintenanceMiddleware(async_session))
    dp.callback_query.middleware(MaintenanceMiddleware(async_session))

    # Inject session into handlers via middleware-like dependency
    # Use aiogram's dependency: we will use a simple middleware to provide session
    from aiogram import BaseMiddleware
    from typing import Callable, Dict, Any, Awaitable
    from aiogram.types import TelegramObject

    class DBSessionMiddleware(BaseMiddleware):
        async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: Dict[str, Any]) -> Any:
            async with async_session() as session:
                data["session"] = session
                return await handler(event, data)

    dp.message.middleware(DBSessionMiddleware())
    dp.callback_query.middleware(DBSessionMiddleware())

    # Routers
    from bot.app.handlers import start, menu, daily, tasks, paid_tasks, withdrawal, advertiser, support, admin, verify, leaderboard, webapp, premium, rating

    dp.include_router(verify.router)
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(daily.router)
    dp.include_router(tasks.router)
    dp.include_router(paid_tasks.router)
    dp.include_router(withdrawal.router)
    dp.include_router(advertiser.router)
    dp.include_router(support.router)
    dp.include_router(leaderboard.router)
    dp.include_router(premium.router)
    dp.include_router(webapp.router)
    dp.include_router(rating.router)
    dp.include_router(admin.router)

    # Global error handler
    @dp.error()
    async def error_handler(event, exception):
        logger.exception(f"Unhandled error: {exception} | event: {event}")
        return True

    return bot, dp

async def on_startup(bot: Bot):
    logger.info("🚀 Bot starting...")
    await init_db()
    logger.info("✅ Database ready")
    # Sync offerwall
    try:
        async with async_session() as s:
            from bot.app.services.offerwall_service import sync_offerwall_tasks
            await sync_offerwall_tasks(s)
    except Exception as e:
        logger.warning(f"offerwall sync fail {e}")
    # Scheduler
    try:
        from bot.app.utils.scheduler import daily_reminder_loop, premium_expiry_loop, weekly_contest_loop
        import asyncio as _asyncio
        _asyncio.create_task(daily_reminder_loop(bot))
        _asyncio.create_task(premium_expiry_loop())
        _asyncio.create_task(weekly_contest_loop(bot))
    except Exception as e:
        logger.warning(f"scheduler fail {e}")
    # Set commands
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 البداية"),
        BotCommand(command="help", description="ℹ️ المساعدة"),
        BotCommand(command="my_withdrawals", description="💸 سحوباتي"),
        BotCommand(command="kyc", description="🪪 توثيق"),
    ])

async def on_shutdown(bot: Bot):
    logger.info("🛑 Bot shutting down...")
    await engine.dispose()

async def main():
    setup_logging()
    if not settings.bot_token or settings.bot_token == "1234567890:AAH_YOUR_BOT_TOKEN_HERE":
        logger.warning("⚠️ BOT_TOKEN not set! Set it in .env")
    bot, dp = await create_bot_and_dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
