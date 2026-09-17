from aiogram import Router, F
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.app.config import settings

router = Router()

def webapp_kb():
    # In production replace with your domain WebApp URL
    url = "https://your-domain.com/webapp"
    # For demo use channel link as placeholder
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 فتح لوحة الويب", web_app={"url": url})],
        [InlineKeyboardButton(text="📣 قناتنا", url=f"https://t.me/{settings.channel_username.lstrip('@')}")]
    ])

@router.message(F.text == "🌐 لوحة الويب")
async def webapp_menu(message: Message):
    await message.answer(
        "🌐 <b>لوحة الويب</b>\nافتح التطبيق المصغر لعرض مهامك وأرباحك بشكل عصري:",
        reply_markup=webapp_kb(),
        parse_mode="HTML"
    )
