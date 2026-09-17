from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User

router = Router()

@router.message(F.text == "🏆 المتصدرون")
async def leaderboard(message: Message, session: AsyncSession):
    # Top by balance + referrals
    res = await session.execute(select(User).order_by(User.balance.desc()).limit(10))
    users = res.scalars().all()
    text = "🏆 <b>المتصدرون - أعلى رصيد</b>\n\n"
    for i, u in enumerate(users, 1):
        name = u.full_name[:15]
        medal = ["🥇","🥈","🥉"][i-1] if i<=3 else f"{i}."
        text += f"{medal} {name} — {u.balance} نقطة | 👥{u.referral_count}\n"
    # weekly (created last 7 days earnings)
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🎡 عجلة الحظ")
async def spin_wheel(message: Message, session: AsyncSession):
    from datetime import datetime, timezone, timedelta
    from bot.app.services.user_service import get_user_by_telegram_id
    from bot.app.services.financial_service import credit
    from bot.app.services.premium_service import is_premium
    import random
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ أرسل /start"); return
    now = datetime.now(timezone.utc)
    if user.last_spin and user.last_spin.tzinfo is None:
        user.last_spin = user.last_spin.replace(tzinfo=timezone.utc)
    if user.last_spin and now - user.last_spin < timedelta(hours=24):
        rem = timedelta(hours=24) - (now - user.last_spin)
        h = int(rem.total_seconds() // 3600)
        await message.answer(f"⏳ يمكنك الدوران مرة كل 24 ساعة. متبقي {h} ساعة")
        return
    # cost 0 for first daily spin, premium free?
    cost = 0
    # Spin prizes weighted
    prizes = [0, 1, 2, 5, 10]
    weights = [30, 30, 20, 15, 5]
    prize = random.choices(prizes, weights=weights)[0]
    # premium doubles
    if await is_premium(user) and prize > 0:
        prize *= 2
    if prize > 0:
        await credit(session, user, prize, "bonus", f"عجلة الحظ +{prize}")
    user.last_spin = now
    await session.commit()
    if prize == 0:
        await message.answer("🎡 <b>عجلة الحظ</b>\nحظ أوفر! حاول غداً 🍀", parse_mode="HTML")
    else:
        await message.answer(f"🎡 <b>مبروك!</b>\n🎉 ربحت <b>{prize} نقطة</b> من العجلة!", parse_mode="HTML")
