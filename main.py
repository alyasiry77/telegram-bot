import sys
import os
import asyncio

# إضافة مسار المجلد الحالي ليقرأ كل الملفات والمجلدات بداخله تلقائياً
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from bot import main

if __name__ == "__main__":
    asyncio.run(main())
