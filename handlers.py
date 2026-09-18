from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from messages import WELCOME
# استدعاء ملف القوائم والأزرار الموجود لديك menus.py
from menus import main_menu_keyboard  # أو اسم دالة الأزرار الموجودة في ملف menus.py

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    # تجهيز رسالة الترحيب مع اسم المستخدم
    text = WELCOME.format(
        name=message.from_user.full_name
    )
    # إرسال الرسالة مع الأزرار التفاعلية
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard)
