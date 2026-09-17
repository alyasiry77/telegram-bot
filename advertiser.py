from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.states.campaign import CampaignCreate
from bot.app.keyboards.inline import advertiser_type_kb, confirm_kb
from bot.app.services.user_service import get_user_by_telegram_id
from bot.app.models.campaign import Campaign
from bot.app.services.settings_service import get_int
from bot.app.utils.helpers import sanitize, parse_int, is_valid_url

router = Router()

@router.message(F.text == "📢 أعلن معنا")
async def advertiser_start(message: Message, state: FSMContext):
    await state.set_state(CampaignCreate.type)
    await message.answer(
        "📢 <b>إنشاء حملة إعلانية</b>\n\nاختر نوع الحملة:",
        reply_markup=advertiser_type_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("adv_type:"), CampaignCreate.type)
async def adv_type(callback: CallbackQuery, state: FSMContext):
    ctype = callback.data.split(":")[1]
    await state.update_data(campaign_type=ctype)
    await state.set_state(CampaignCreate.title)
    await callback.message.edit_text("📝 أرسل <b>اسم الحملة</b> (مثال: زيادة مشتركي قناتي):", parse_mode="HTML")
    await callback.answer()

@router.message(CampaignCreate.title)
async def adv_title(message: Message, state: FSMContext):
    title = sanitize(message.text, 100)
    if len(title) < 3:
        await message.answer("❌ الاسم قصير جداً (3 أحرف على الأقل):")
        return
    await state.update_data(title=title)
    await state.set_state(CampaignCreate.description)
    await message.answer("📄 أرسل <b>وصف الحملة</b> (ما المطلوب من المستخدم؟):", parse_mode="HTML")

@router.message(CampaignCreate.description)
async def adv_desc(message: Message, state: FSMContext):
    desc = sanitize(message.text, 1000)
    if len(desc) < 5:
        await message.answer("❌ الوصف قصير:")
        return
    await state.update_data(description=desc)
    await state.set_state(CampaignCreate.url)
    await message.answer("🔗 أرسل <b>رابط الحملة</b> (https:// أو @username):", parse_mode="HTML")

@router.message(CampaignCreate.url)
async def adv_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if not is_valid_url(url):
        await message.answer("❌ رابط غير صالح. أرسل رابط يبدأ بـ https:// أو @ أو https://t.me/:")
        return
    # Extract channel username if channel_join type
    data = await state.get_data()
    chan = None
    if data.get("campaign_type") in ("channel_join",) or "@" in url or "t.me" in url:
        # try to extract
        if url.startswith("@"):
            chan = url
        elif "t.me/" in url:
            try:
                chan = "@" + url.split("t.me/")[-1].split("/")[0].split("?")[0]
            except:
                chan = url
    await state.update_data(url=url, channel_username=chan)
    await state.set_state(CampaignCreate.required)
    await message.answer("🔢 أرسل <b>عدد التنفيذات المطلوبة</b> (مثال: 1000):", parse_mode="HTML")

@router.message(CampaignCreate.required)
async def adv_required(message: Message, state: FSMContext):
    val = parse_int(message.text, 1, 1000000)
    if not val:
        await message.answer("❌ أرسل رقماً بين 1 و 1,000,000:")
        return
    await state.update_data(required=val)
    await state.set_state(CampaignCreate.reward)
    await message.answer("💰 أرسل <b>المكافأة لكل مستخدم</b> بالنقاط (مثال: 10):", parse_mode="HTML")

@router.message(CampaignCreate.reward)
async def adv_reward(message: Message, state: FSMContext, session: AsyncSession):
    val = parse_int(message.text, 1, 10000)
    if not val:
        await message.answer("❌ أرسل رقماً بين 1 و 10000:")
        return
    data = await state.get_data()
    required = data["required"]
    total = required * val
    profit_pct = await get_int(session, "campaign_profit_percent", 30)
    profit = int(total * profit_pct / 100)
    user_total = total  # points paid to users? Actually budget = total, platform keeps profit
    # Model: Advertiser pays total, users get total - profit? Or total is for users? Spec says 10k *0.01$ =100$ -> 70 for users, 30 profit. So total budget = required * reward, profit = percent, users share = total - profit?
    # We will store total_budget = total, platform_profit = profit, reward_per_user = val
    await state.update_data(reward=val, total=total, profit=profit)
    await state.set_state(CampaignCreate.confirm)
    await message.answer(
        f"📋 <b>ملخص الحملة</b>\n\n"
        f"📌 النوع: {data.get('campaign_type')}\n"
        f"📝 الاسم: {data.get('title')}\n"
        f"🔗 الرابط: {data.get('url')}\n"
        f"🔢 العدد: {required}\n"
        f"💰 لكل مستخدم: {val} نقطة\n"
        f"💵 الإجمالي: {total} نقطة\n"
        f"🏦 ربح المنصة ({profit_pct}%): {profit} نقطة\n"
        f"✅ للمستخدمين: {total - profit} نقطة\n\n"
        f"سيتم مراجعة حملتك من الإدارة قبل التفعيل.\n"
        f"هل تريد التأكيد؟",
        reply_markup=confirm_kb("adv_confirm", "adv_cancel"),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "adv_confirm", CampaignCreate.confirm)
async def adv_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("خطأ", show_alert=True)
        return
    profit_pct = await get_int(session, "campaign_profit_percent", 30)
    camp = Campaign(
        advertiser_id=user.id,
        title=data["title"],
        description=data["description"],
        url=data["url"],
        campaign_type=data["campaign_type"],
        required_completions=data["required"],
        reward_per_user=data["reward"],
        total_budget=data["total"],
        platform_fee_percent=profit_pct,
        platform_profit=data["profit"],
        status="pending",
        channel_username=data.get("channel_username"),
    )
    session.add(camp)
    await session.commit()
    await session.refresh(camp)
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>تم إنشاء حملتك بنجاح!</b>\n🆔 رقم الحملة: <code>{camp.id}</code>\n📊 الحالة: قيد المراجعة\nسيتم إشعارك عند الموافقة.",
        parse_mode="HTML"
    )
    await callback.answer("✅ تم الإنشاء")
    # Notify admins
    from bot.app.config import settings
    for aid in settings.admins:
        try:
            await callback.bot.send_message(
                aid,
                f"📢 <b>حملة جديدة بانتظار المراجعة</b>\n🆔 #{camp.id}\n👤 {user.telegram_id} (@{user.username or '-'})\n📌 {camp.title}\n🔢 {camp.required_completions} × {camp.reward_per_user} = {camp.total_budget}\n🔗 {camp.url}",
                parse_mode="HTML"
            )
        except:
            pass

@router.callback_query(F.data == "adv_cancel")
async def adv_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ تم إلغاء إنشاء الحملة.")
    await callback.answer()
