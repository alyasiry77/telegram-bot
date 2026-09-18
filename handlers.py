from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from messages import WELCOME

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    # تجهيز رسالة الترحيب مع اسم المستخدم
    text = WELCOME.format(
        name=message.from_user.full_name
    )
    await message.answer(text, parse_mode="HTML")
