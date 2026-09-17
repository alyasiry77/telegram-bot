import sys
import os

# إضافة مجلد bot إلى مسار البحث الخاص ببايثون
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'bot')))

import asyncio
from bot.bot import main as bot_main

if __name__ == "__main__":
    try:
        asyncio.run(bot_main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")
