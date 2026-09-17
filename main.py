import sys
import os
import asyncio

# إضافة المجلد الحالي إلى مسار بايثون ليرى كل المجلدات (middlewares, handlers وغيرها)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from bot import create_bot_and_dispatcher

async def main():
    bot, dp = await create_bot_and_dispatcher()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
