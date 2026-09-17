from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.services.user_service import get_user_by_telegram_id
from bot.app.services.reward_service import claim_daily_reward, claim_daily_task
from bot.app.keyboards.inline import daily_reward_kb
from bot.app.messages import DAILY_REWARD_OK, DAILY_REWARD_WAIT
from bot.app.utils.helpers import format_remaining

router = Router()

@router.message(F.text == "🎁 المكافأة اليومية")
async def daily_menu(message: Message, session: AsyncSession):
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ أرسل /start أولاً")
        return
    await message.answer(
        "🎁 <b>المكافأة اليومية</b>\n\nاضغط لاستلام مكافأتك (+5 نقاط) أو المهمة اليومية (+10 نقاط):",
        reply_markup=daily_reward_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "daily_claim")
async def handle_daily_claim(callback: CallbackQuery, session: AsyncSession):
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("أرسل /start", show_alert=True)
        return
    success, code, remaining = await claim_daily_reward(session, user)
    if success:
        # refresh
        from bot.app.services.user_service import get_user_by_telegram_id as g
        user = await g(session, callback.from_user.id)
        await callback.message.edit_text(
            DAILY_REWARD_OK.format(amount=5, balance=user.balance),
            parse_mode="HTML"
        )
        await callback.answer("✅ تمت الإضافة!")
    else:
        h, m = format_remaining(remaining)
        await callback.answer(f"⏳ انتظر {h}س {m}د", show_alert=True)
        await callback.message.edit_text(
            DAILY_REWARD_WAIT.format(hours=h, minutes=m),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "daily_task_claim")
async def handle_daily_task(callback: CallbackQuery, session: AsyncSession):
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("أرسل /start", show_alert=True)
        return
    success, code, remaining = await claim_daily_task(session, user)
    if success:
        from bot.app.services.user_service import get_user_by_telegram_id as g
        user = await g(session, callback.from_user.id)
        await callback.message.edit_text(
            f"✅ <b>تم استلام مكافأة المهمة اليومية!</b>\n💰 +10 نقطة\n💳 رصيدك: {user.balance}",
            parse_mode="HTML"
        )
        await callback.answer("✅ تمت الإضافة!")
    else:
        h, m = format_remaining(remaining)
        await callback.answer(f"⏳ انتظر {h}س {m}د", show_alert=True)
        await callback.message.edit_text(
            DAILY_REWARD_WAIT.format(hours=h, minutes=m),
            parse_mode="HTML"
        )
