import asyncio
import logging
import sys
import os

# إضافة مسار المجلد الحالي لضمان رؤية جميع الملفات والمجلدات
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# تعديل مسار الاستيراد ليطابق هيكلة مشروعك الداخلي
from bot.app.config import settings
from bot.app.loader import create_bot_and_dispatcher, on_startup, on_shutdown, logger

async def main():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    
    bot, dp = await create_bot_and_dispatcher()
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    logger.info("🚀 Starting Bot Polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
