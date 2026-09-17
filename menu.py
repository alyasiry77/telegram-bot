from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.services.user_service import get_user_by_telegram_id
from bot.app.services.settings_service import get_float, get_int
from bot.app.keyboards.reply import main_menu
from bot.app.messages import PROFILE_TEMPLATE, FINANCE_TEMPLATE, REFERRAL_TEMPLATE, ABOUT_TEXT, SUPPORT_INTRO, get_level
from bot.app.keyboards.inline import daily_reward_kb, support_kb, channel_kb
from bot.app.config import settings

router = Router()

@router.message(F.text == "🏠 الرئيسية")
async def main_home(message: Message, session: AsyncSession):
    is_admin = settings.is_admin(message.from_user.id)
    await message.answer("🏠 <b>القائمة الرئيسية</b>\nاختر من الأزرار أدناه:", reply_markup=main_menu(is_admin), parse_mode="HTML")

@router.message(F.text == "👤 ملفي وأرباحي")
async def profile(message: Message, session: AsyncSession):
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ لم يتم العثور على حسابك. أرسل /start")
        return
    rate = await get_float(session, "points_to_cash", 0.01)
    _, lvl_name = get_level(user.referral_count)
    # Get thresholds for accurate level
    t2 = await get_int(session, "level_2_threshold", 10)
    t3 = await get_int(session, "level_3_threshold", 50)
    t4 = await get_int(session, "level_4_threshold", 200)
    _, lvl_name = get_level(user.referral_count, {1:0,2:t2,3:t3,4:t4})
    status = "🚫 محظور" if user.is_banned else "✅ نشط"
    created = user.created_at.strftime("%Y-%m-%d") if user.created_at else "-"
    username = f"@{user.username}" if user.username else "—"
    text = PROFILE_TEMPLATE.format(
        user_id=user.telegram_id,
        full_name=user.full_name,
        username=username,
        balance=user.balance,
        cash=user.balance*rate,
        total_earnings=user.total_earnings,
        total_withdrawals=user.total_withdrawals,
        tasks_done=user.tasks_done,
        referrals=user.referral_count,
        level=lvl_name,
        created=created,
        status=status,
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "💳 الحساب المالي")
async def finance(message: Message, session: AsyncSession):
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ أرسل /start أولاً")
        return
    rate = await get_float(session, "points_to_cash", 0.01)
    min_bal = await get_int(session, "min_withdrawal_balance", 100)
    text = FINANCE_TEMPLATE.format(
        balance=user.balance,
        cash=user.balance*rate,
        total_earnings=user.total_earnings,
        total_withdrawals=user.total_withdrawals,
        task_earnings=user.task_earnings,
        referral_earnings=user.referral_earnings,
        bonus=user.bonus_earnings,
        rate=rate,
        min_bal=min_bal,
    )
    # Show recent transactions
    from sqlalchemy import select
    from bot.app.models.transaction import Transaction
    res = await session.execute(select(Transaction).where(Transaction.user_id==user.id).order_by(Transaction.created_at.desc()).limit(5))
    txns = res.scalars().all()
    if txns:
        text += "\n\n📜 <b>آخر العمليات:</b>\n"
        for t in txns:
            sign = "+" if t.amount>0 else ""
            text += f"• {t.type}: {sign}{t.amount} | {t.description or ''}\n"
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "👥 الإحالة")
async def referral(message: Message, session: AsyncSession):
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ أرسل /start")
        return
    bot_username = settings.bot_username.lstrip("@")
    if not bot_username or bot_username == "your_bot":
        try:
            me = await message.bot.get_me()
            bot_username = me.username
        except:
            bot_username = "your_bot"
    reward = await get_int(session, "referral_reward", 5)
    t2 = await get_int(session, "level_2_threshold", 10)
    t3 = await get_int(session, "level_3_threshold", 50)
    t4 = await get_int(session, "level_4_threshold", 200)
    _, lvl = get_level(user.referral_count, {1:0,2:t2,3:t3,4:t4})
    text = REFERRAL_TEMPLATE.format(
        bot_username=bot_username,
        ref_code=user.telegram_id,
        count=user.referral_count,
        earnings=user.referral_earnings,
        level=lvl,
        reward=reward,
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📣 قناتنا")
async def channel(message: Message, session: AsyncSession):
    chan = await get_int(session, "channel_username", 0)  # mistaken, get string
    from bot.app.services.settings_service import get_setting
    chan = await get_setting(session, "channel_username", "@your_channel")
    await message.answer(f"📣 <b>قناتنا الرسمية</b>\n{chan}\nانضم لتصلك الأخبار والعروض!", reply_markup=channel_kb(chan), parse_mode="HTML")

@router.message(F.text == "ℹ️ عن البوت")
async def about(message: Message, session: AsyncSession):
    from bot.app.services.settings_service import get_setting, get_float as gf, get_int as gi
    min_bal = await gi(session, "min_withdrawal_balance", 100)
    min_ref = await gi(session, "min_withdrawal_referrals", 3)
    profit = await gi(session, "campaign_profit_percent", 30)
    chan = await get_setting(session, "channel_username", "@your_channel")
    sup = await get_setting(session, "support_username", "@support")
    await message.answer(ABOUT_TEXT.format(min_bal=min_bal, min_ref=min_ref, profit=profit, channel=chan, support=sup), parse_mode="HTML")

@router.message(F.text == "📞 الدعم الفني")
async def support(message: Message):
    await message.answer(SUPPORT_INTRO, reply_markup=support_kb(), parse_mode="HTML")

@router.message(F.text == "⚙️ الإعدادات")
async def settings_menu(message: Message, session: AsyncSession):
    from bot.app.services.settings_service import get_setting
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    chan = await get_setting(session, "channel_username", "@your_channel")
    sup = await get_setting(session, "support_username", "@support")
    b = InlineKeyboardBuilder()
    b.button(text="🇸🇦 عربي", callback_data="lang:ar")
    b.button(text="🇬🇧 English", callback_data="lang:en")
    b.adjust(2)
    # progress bar
    user = await get_user_by_telegram_id(session, message.from_user.id)
    rate = await get_float(session, "points_to_cash", 0.01)
    min_bal = await get_int(session, "min_withdrawal_balance", 100)
    pct = min(100, int(user.balance / max(1, min_bal) * 100)) if user else 0
    bar = "▓" * (pct // 10) + "░" * (10 - pct // 10)
    await message.answer(
        f"⚙️ <b>الإعدادات</b>\n\n📣 القناة: {chan}\n📞 الدعم: {sup}\n\n"
        f"💰 تقدم السحب: [{bar}] {pct}% ({user.balance if user else 0}/{min_bal})\n"
        f"اختر اللغة:",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("lang:"))
async def set_lang(callback: CallbackQuery, session: AsyncSession):
    lang = callback.data.split(":")[1]
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if user:
        user.language = lang
        await session.commit()
    await callback.answer("✅ تم التغيير" if lang=="ar" else "✅ Changed")
    await callback.message.edit_text(f"✅ اللغة: {lang}")

@router.message(F.text == "🛡️ لوحة الإدارة")
async def admin_entry(message: Message):
    if not settings.is_admin(message.from_user.id):
        await message.answer("🚫 ليس لديك صلاحية.")
        return
    from bot.app.keyboards.inline import admin_main_kb
    await message.answer("🛡️ <b>لوحة الإدارة</b>\nاختر القسم:", reply_markup=admin_main_kb(), parse_mode="HTML")
