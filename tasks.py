from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.services.user_service import get_user_by_telegram_id
from bot.app.services.task_service import get_active_tasks, get_user_completed_task_ids, complete_task
from bot.app.keyboards.inline import tasks_list_kb, task_kb
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "📋 المهام")
async def list_tasks(message: Message, session: AsyncSession):
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("❌ أرسل /start")
        return
    tasks = await get_active_tasks(session)
    completed = await get_user_completed_task_ids(session, user.id)
    available = [t for t in tasks if t.id not in completed]
    if not available:
        await message.answer("📭 لا توجد مهام متاحة حالياً. عد لاحقاً!")
        return
    # Pagination 10 per page
    page = 0
    total_pages = (len(available) + 9)//10
    page_items = available[page*10:(page+1)*10]
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="🔍 بحث", callback_data="tasks_search")
    b.button(text="💰 الأعلى ربحاً", callback_data="tasks_sort_reward")
    b.button(text="🆕 الأحدث", callback_data="tasks_sort_new")
    b.adjust(2)
    kb = tasks_list_kb(page_items, prefix="task_view:")
    # add paginator
    if total_pages > 1:
        from aiogram.utils.keyboard import InlineKeyboardButton
        # append nav
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"1/{total_pages} ▶️", callback_data=f"tasks_page:1")])
    await message.answer(
        f"📋 <b>المهام المتاحة</b> ({len(available)}) صفحة 1/{total_pages}\nاختر مهمة:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await message.answer("🔍 <b>فرز وبحث:</b>", reply_markup=b.as_markup())

@router.callback_query(F.data == "tasks_sort_reward")
async def tasks_sort_reward(callback: CallbackQuery, session: AsyncSession):
    from bot.app.services.user_service import get_user_by_telegram_id as g
    user = await g(session, callback.from_user.id)
    tasks = await get_active_tasks(session)
    completed = await get_user_completed_task_ids(session, user.id)
    available = sorted([t for t in tasks if t.id not in completed], key=lambda x: x.reward_points, reverse=True)
    await callback.message.edit_text(f"💰 <b>الأعلى ربحاً</b> ({len(available)})", reply_markup=tasks_list_kb(available, prefix="task_view:"), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "tasks_sort_new")
async def tasks_sort_new(callback: CallbackQuery, session: AsyncSession):
    await tasks_back(callback, session)

@router.callback_query(F.data.startswith("tasks_page:"))
async def tasks_page(callback: CallbackQuery, session: AsyncSession):
    page = int(callback.data.split(":")[1])
    from bot.app.services.user_service import get_user_by_telegram_id as g
    user = await g(session, callback.from_user.id)
    tasks = await get_active_tasks(session)
    completed = await get_user_completed_task_ids(session, user.id)
    available = [t for t in tasks if t.id not in completed]
    total_pages = (len(available)+9)//10
    page = max(0, min(page, total_pages-1))
    items = available[page*10:(page+1)*10]
    kb = tasks_list_kb(items, prefix="task_view:")
    if total_pages>1:
        from aiogram.types import InlineKeyboardButton
        nav = []
        if page>0:
            nav.append(InlineKeyboardButton(text="◀️", callback_data=f"tasks_page:{page-1}"))
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages-1:
            nav.append(InlineKeyboardButton(text="▶️", callback_data=f"tasks_page:{page+1}"))
        kb.inline_keyboard.append(nav)
    await callback.message.edit_text(f"📋 <b>المهام</b> صفحة {page+1}/{total_pages}", reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(F.data == "tasks_search")
async def tasks_search(callback: CallbackQuery):
    await callback.answer("🔍 أرسل كلمة البحث كرسالة (مثال: قناة)", show_alert=True)

@router.message(F.text.regexp(r"^بحث:"))
async def tasks_search_text(message: Message, session: AsyncSession):
    q = message.text.replace("بحث:", "").strip().lower()
    user = await get_user_by_telegram_id(session, message.from_user.id)
    tasks = await get_active_tasks(session)
    completed = await get_user_completed_task_ids(session, user.id)
    filtered = [t for t in tasks if t.id not in completed and q in t.title.lower()]
    if not filtered:
        await message.answer("❌ لا نتائج")
        return
    await message.answer(f"🔍 نتائج '{q}' ({len(filtered)}):", reply_markup=tasks_list_kb(filtered, prefix="task_view:"), parse_mode="HTML")

@router.callback_query(F.data.startswith("task_view:"))
async def view_task(callback: CallbackQuery, session: AsyncSession):
    task_id = int(callback.data.split(":")[1])
    from sqlalchemy import select
    from bot.app.models.task import Task
    res = await session.execute(select(Task).where(Task.id==task_id))
    task = res.scalar_one_or_none()
    if not task:
        await callback.answer("المهمة غير موجودة", show_alert=True)
        return
    is_channel = task.type in ("channel_join","group_join")
    text = f"📋 <b>{task.title}</b>\n\n{task.description or ''}\n\n💰 المكافأة: <b>{task.reward_points} نقطة</b>\n📊 التقدم: {task.current_completions}/{task.max_completions}"
    await callback.message.edit_text(text, reply_markup=task_kb(task.id, task.url or task.channel_username or "", is_channel, task.channel_username), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("task_check:"))
async def check_task(callback: CallbackQuery, session: AsyncSession):
    task_id = int(callback.data.split(":")[1])
    from sqlalchemy import select
    from bot.app.models.task import Task
    res = await session.execute(select(Task).where(Task.id==task_id))
    task = res.scalar_one_or_none()
    if not task:
        await callback.answer("المهمة غير موجودة", show_alert=True)
        return
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        await callback.answer("أرسل /start", show_alert=True)
        return
    if user.is_banned:
        await callback.answer("حسابك محظور", show_alert=True)
        return

    # Verify membership if channel task
    is_member = None
    verify = False
    if task.type in ("channel_join", "group_join") and task.channel_username:
        verify = True
        try:
            chan = task.channel_username
            if chan.startswith("@"):
                chan_id = chan
            elif chan.startswith("https://t.me/"):
                chan_id = "@" + chan.split("/")[-1]
            else:
                chan_id = chan
            member = await callback.bot.get_chat_member(chat_id=chan_id, user_id=callback.from_user.id)
            if member.status in ("member", "administrator", "creator"):
                is_member = True
            else:
                is_member = False
        except Exception as e:
            logger.warning(f"get_chat_member failed {e}")
            # If bot is not admin, Telegram may fail. We show error and don't grant reward automatically.
            await callback.answer("⚠️ تعذر التحقق تلقائياً. تأكد من انضمامك وحاول مرة أخرى. إذا استمرت المشكلة تواصل مع الدعم.", show_alert=True)
            return

    # Premium multiplier
    from bot.app.services.premium_service import premium_multiplier
    mult = await premium_multiplier(session, user)
    if mult > 1:
        task.reward_points = int(task.reward_points * mult)
    success, code = await complete_task(session, user, task, verify_membership=verify, is_member=is_member)
    if success:
        await callback.message.edit_text(f"✅ <b>تم تنفيذ المهمة بنجاح!</b>\n💰 حصلت على <b>{task.reward_points} نقطة</b>{' 💎×2' if mult>1 else ''}", parse_mode="HTML")
        await callback.answer("✅ تمت المكافأة!")
    else:
        msgs = {
            "already_completed": "❌ لقد نفذت هذه المهمة مسبقاً",
            "limit_reached": "❌ انتهى الحد الأقصى لهذه المهمة",
            "not_member": "❌ لم يتم العثور على اشتراكك. انضم أولاً ثم اضغط تحقق.",
            "verification_failed": "⚠️ تعذر التحقق",
            "inactive": "❌ المهمة غير نشطة",
            "expired": "❌ المهمة منتهية",
            "error": "❌ حدث خطأ، حاول لاحقاً"
        }
        await callback.answer(msgs.get(code, "❌ فشل التنفيذ"), show_alert=True)

@router.callback_query(F.data == "tasks_back")
async def tasks_back(callback: CallbackQuery, session: AsyncSession):
    # re-list
    from bot.app.services.user_service import get_user_by_telegram_id as g
    user = await g(session, callback.from_user.id)
    tasks = await get_active_tasks(session)
    completed = await get_user_completed_task_ids(session, user.id)
    available = [t for t in tasks if t.id not in completed]
    if not available:
        await callback.message.edit_text("📭 لا توجد مهام متاحة حالياً.")
        await callback.answer()
        return
    await callback.message.edit_text(f"📋 <b>المهام المتاحة</b> ({len(available)})", reply_markup=tasks_list_kb(available, prefix="task_view:"), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "tasks_refresh")
async def tasks_refresh(callback: CallbackQuery, session: AsyncSession):
    await tasks_back(callback, session)
