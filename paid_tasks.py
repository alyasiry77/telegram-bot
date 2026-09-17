from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.services.user_service import get_user_by_telegram_id
from bot.app.services.task_service import get_active_campaigns, get_user_campaign_ids, complete_campaign
from bot.app.keyboards.inline import tasks_list_kb, campaign_kb
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "💰 المهام المدفوعة")
async def list_paid(message: Message, session: AsyncSession):
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ أرسل /start")
        return
    camps = await get_active_campaigns(session)
    done_ids = await get_user_campaign_ids(session, user.id)
    available = [c for c in camps if c.id not in done_ids]
    if not available:
        await message.answer("📭 لا توجد مهام مدفوعة متاحة حالياً.")
        return
    # Reuse tasks_list display but with campaign data
    # Build custom text
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    for c in available:
        b.button(text=f"{c.title} (+{c.reward_per_user})", callback_data=f"camp_view:{c.id}")
    b.button(text="🔄 تحديث", callback_data="camps_refresh")
    b.adjust(1)
    await message.answer(f"💰 <b>المهام المدفوعة</b> ({len(available)})\nهذه حملات مدفوعة من معلنين - مكافآت أعلى:", reply_markup=b.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("camp_view:"))
async def view_camp(callback: CallbackQuery, session: AsyncSession):
    cid = int(callback.data.split(":")[1])
    from sqlalchemy import select
    from bot.app.models.campaign import Campaign
    r = await session.execute(select(Campaign).where(Campaign.id==cid))
    c = r.scalar_one_or_none()
    if not c:
        await callback.answer("الحملة غير موجودة", show_alert=True)
        return
    text = f"💰 <b>{c.title}</b>\n\n{c.description or ''}\n\n🔗 {c.url}\n💰 المكافأة: <b>{c.reward_per_user} نقطة</b>\n📊 {c.current_completions}/{c.required_completions}"
    await callback.message.edit_text(text, reply_markup=campaign_kb(c.id, c.url), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("camp_check:"))
async def check_camp(callback: CallbackQuery, session: AsyncSession):
    cid = int(callback.data.split(":")[1])
    from sqlalchemy import select
    from bot.app.models.campaign import Campaign
    r = await session.execute(select(Campaign).where(Campaign.id==cid))
    c = r.scalar_one_or_none()
    if not c:
        await callback.answer("غير موجود", show_alert=True)
        return
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user or user.is_banned:
        await callback.answer("حسابك غير صالح", show_alert=True)
        return
    is_member = None
    verify = False
    if c.campaign_type in ("channel_join","group_join") and c.channel_username:
        verify = True
        try:
            chan = c.channel_username
            member = await callback.bot.get_chat_member(chat_id=chan, user_id=callback.from_user.id)
            is_member = member.status in ("member","administrator","creator")
        except Exception as e:
            logger.warning(e)
            await callback.answer("⚠️ تعذر التحقق، تأكد من الاشتراك", show_alert=True)
            return
    success, code = await complete_campaign(session, user, c, verify_membership=verify, is_member=is_member)
    if success:
        await callback.message.edit_text(f"✅ <b>تم تنفيذ الحملة!</b>\n💰 +{c.reward_per_user} نقطة", parse_mode="HTML")
        await callback.answer("✅ تمت المكافأة!")
    else:
        msgs = {"already_completed":"❌ نفذتها مسبقاً","limit_reached":"❌ اكتملت الحملة","not_member":"❌ اشترك أولاً","inactive":"❌ غير نشطة"}
        await callback.answer(msgs.get(code, "❌ فشل"), show_alert=True)

@router.callback_query(F.data == "camps_back")
async def camps_back(callback: CallbackQuery, session: AsyncSession):
    # re-list
    camps = await get_active_campaigns(session)
    from bot.app.services.user_service import get_user_by_telegram_id as g
    user = await g(session, callback.from_user.id)
    done_ids = await get_user_campaign_ids(session, user.id)
    available = [c for c in camps if c.id not in done_ids]
    if not available:
        await callback.message.edit_text("📭 لا توجد حملات متاحة.")
        await callback.answer()
        return
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    for c in available:
        b.button(text=f"{c.title} (+{c.reward_per_user})", callback_data=f"camp_view:{c.id}")
    b.button(text="🔄 تحديث", callback_data="camps_refresh")
    b.adjust(1)
    await callback.message.edit_text(f"💰 <b>المهام المدفوعة</b> ({len(available)})", reply_markup=b.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "camps_refresh")
async def camps_refresh(callback: CallbackQuery, session: AsyncSession):
    await camps_back(callback, session)
