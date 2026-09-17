from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.services.user_service import get_user_by_telegram_id
from bot.app.services.premium_service import get_premium_price, activate_premium, is_premium
from bot.app.services.financial_service import debit

router = Router()

@router.message(F.text == "💎 بريميوم")
async def premium_menu(message: Message, session: AsyncSession):
    user = await get_user_by_telegram_id(session, message.from_user.id)
    price = await get_premium_price(session)
    is_p = await is_premium(user) if user else False
    status = f"✅ نشط حتى {user.premium_until.strftime('%Y-%m-%d')}" if is_p and user.premium_until else "❌ غير نشط"
    b = InlineKeyboardBuilder()
    if not is_p:
        b.button(text=f"💎 اشتراك 30 يوم - {price} نقطة", callback_data="premium_buy:30")
        b.button(text="💎 7 أيام تجريبي - 150 نقطة", callback_data="premium_buy:7")
    b.button(text="📋 المزايا", callback_data="premium_info")
    b.adjust(1)
    await message.answer(
        f"💎 <b>بريميوم</b>\n\n"
        f"الحالة: {status}\n"
        f"💰 رصيدك: {user.balance if user else 0} نقطة\n\n"
        f"✨ المزايا:\n"
        f"• مكافأة يومية ×2\n"
        f"• عجلة الحظ ×2\n"
        f"• أولوية سحب\n"
        f"• مهام حصرية\n",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("premium_buy:"))
async def premium_buy(callback: CallbackQuery, session: AsyncSession):
    days = int(callback.data.split(":")[1])
    price_map = {30: await get_premium_price(session), 7: 150}
    price = price_map.get(days, 500)
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if user.balance < price:
        await callback.answer(f"❌ رصيد غير كافٍ، تحتاج {price} نقطة", show_alert=True)
        return
    try:
        await debit(session, user, price, "premium_purchase", f"شراء بريميوم {days} يوم")
        await activate_premium(session, user, days)
        await callback.message.edit_text(f"✅ <b>تم تفعيل بريميوم لـ {days} يوم!</b>\nشكراً لدعمك 💎", parse_mode="HTML")
        await callback.answer("✅ تم التفعيل")
    except Exception as e:
        await callback.answer(f"❌ {e}", show_alert=True)

@router.callback_query(F.data == "premium_info")
async def premium_info(callback: CallbackQuery):
    await callback.answer("💎 بريميوم يضاعف أرباحك ويعطيك أولوية!", show_alert=True)
