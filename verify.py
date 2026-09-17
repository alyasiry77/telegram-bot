from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.services.security_service import generate_captcha, set_captcha, verify_captcha
from bot.app.services.user_service import get_user_by_telegram_id

router = Router()

@router.message(F.text.in_({"✅ تحقق", "🔐 تحقق"}))
async def send_captcha(message: Message):
    q, ans = generate_captcha()
    set_captcha(message.from_user.id, ans)
    await message.answer(f"🔐 <b>تحقق بشري</b>\nحل: <b>{q}</b>\nأرسل الإجابة رقمياً:", parse_mode="HTML")

@router.message(F.text.regexp(r"^\d+$"))
async def check_captcha(message: Message, session: AsyncSession):
    # Only if user not verified
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user or user.captcha_verified:
        return
    if verify_captcha(message.from_user.id, message.text.strip()):
        user.captcha_verified = True
        await session.commit()
        await message.answer("✅ تم التحقق بنجاح! يمكنك الآن استخدام البوت.")
    else:
        # Could be amount input, ignore if not captcha
        pass
