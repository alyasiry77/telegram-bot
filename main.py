import sys
import os
import asyncio

# إضافة المسارات لضمان رؤية جميع المجلدات
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'bot'))

from bot.bot import main as bot_main

if __name__ == "__main__":
    try:
        asyncio.run(bot_main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped safely.")
