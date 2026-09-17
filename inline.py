from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def daily_reward_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🎁 استلام المكافأة اليومية", callback_data="daily_claim")
    b.button(text="✅ المهمة اليومية (+10)", callback_data="daily_task_claim")
    b.adjust(1)
    return b.as_markup()

def task_kb(task_id: int, url: str, is_channel: bool = False, channel_username: str = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if url:
        # Use URL button if provided
        if url.startswith("http"):
            b.button(text="🔗 فتح الرابط", url=url)
        elif url.startswith("@") or url.startswith("https://t.me"):
            b.button(text="📢 الانضمام", url=url if url.startswith("http") else f"https://t.me/{url.lstrip('@')}")
    if is_channel or channel_username:
        chan = channel_username or url
        if chan:
            link = chan if chan.startswith("http") else f"https://t.me/{chan.lstrip('@')}"
            # avoid duplicate if already added
            try:
                b.button(text="📢 انضم للقناة", url=link)
            except:
                pass
    b.button(text="✅ تحقق من التنفيذ", callback_data=f"task_check:{task_id}")
    b.button(text="⬅️ رجوع", callback_data="tasks_back")
    b.adjust(1)
    return b.as_markup()

def campaign_kb(campaign_id: int, url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if url:
        link = url if url.startswith("http") else f"https://t.me/{url.lstrip('@')}"
        b.button(text="🔗 فتح الرابط", url=link)
    b.button(text="✅ تحقق من التنفيذ", callback_data=f"camp_check:{campaign_id}")
    b.button(text="⬅️ رجوع", callback_data="camps_back")
    b.adjust(1)
    return b.as_markup()

def tasks_list_kb(tasks, prefix="task_view:") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for t in tasks:
        b.button(text=f"{t.title} (+{t.reward_points})", callback_data=f"{prefix}{t.id}")
    b.button(text="🔄 تحديث", callback_data="tasks_refresh")
    b.adjust(1)
    return b.as_markup()

def withdrawal_methods_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💳 محفظة إلكترونية", callback_data="wd_method:wallet")
    b.button(text="₿ كريبتو", callback_data="wd_method:crypto")
    b.button(text="🏦 بنك", callback_data="wd_method:bank")
    b.button(text="💵 بايير / بايبال", callback_data="wd_method:payeer")
    b.adjust(2)
    return b.as_markup()

def withdrawal_confirm_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ تأكيد السحب", callback_data="wd_confirm")
    b.button(text="❌ إلغاء", callback_data="wd_cancel")
    b.adjust(2)
    return b.as_markup()

def admin_withdrawal_kb(wd_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ موافقة", callback_data=f"adm_wd_approve:{wd_id}")
    b.button(text="💸 تم الدفع", callback_data=f"adm_wd_paid:{wd_id}")
    b.button(text="❌ رفض", callback_data=f"adm_wd_reject:{wd_id}")
    b.button(text="⬅️ رجوع", callback_data="adm_wd_list")
    b.adjust(2, 2)
    return b.as_markup()

def admin_campaign_kb(camp_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ قبول", callback_data=f"adm_camp_approve:{camp_id}")
    b.button(text="❌ رفض", callback_data=f"adm_camp_reject:{camp_id}")
    b.button(text="⏸️ إيقاف", callback_data=f"adm_camp_pause:{camp_id}")
    b.button(text="▶️ تفعيل", callback_data=f"adm_camp_activate:{camp_id}")
    b.button(text="⬅️ رجوع", callback_data="adm_camp_list")
    b.adjust(2, 2, 1)
    return b.as_markup()

def admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👥 المستخدمون", callback_data="adm_users")
    b.button(text="📋 المهام", callback_data="adm_tasks")
    b.button(text="💰 الحملات", callback_data="adm_camps")
    b.button(text="💸 السحوبات", callback_data="adm_withdrawals")
    b.button(text="📣 الإعلانات", callback_data="adm_ads")
    b.button(text="📊 الإحصائيات", callback_data="adm_stats")
    b.button(text="⚙️ الإعدادات", callback_data="adm_settings")
    b.button(text="📢 إذاعة", callback_data="adm_broadcast")
    b.button(text="📞 الدعم", callback_data="adm_support")
    b.button(text="🛡️ السجلات", callback_data="adm_logs")
    b.adjust(2, 2, 2, 2)
    return b.as_markup()

def support_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💸 مشكلة سحب", callback_data="support:withdrawal")
    b.button(text="📋 مشكلة مهمة", callback_data="support:task")
    b.button(text="👥 مشكلة إحالة", callback_data="support:referral")
    b.button(text="💬 أخرى", callback_data="support:general")
    b.adjust(2)
    return b.as_markup()

def channel_kb(channel_username: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    link = f"https://t.me/{channel_username.lstrip('@')}" if channel_username else "https://t.me/telegram"
    b.button(text="📣 فتح القناة", url=link)
    return b.as_markup()

def advertiser_type_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📢 قناة / مجموعة", callback_data="adv_type:channel_join")
    b.button(text="🔗 زيارة رابط", callback_data="adv_type:visit_link")
    b.button(text="👁️ مشاهدة محتوى", callback_data="adv_type:interaction")
    b.button(text="⚙️ مخصص", callback_data="adv_type:custom")
    b.adjust(2)
    return b.as_markup()

def confirm_kb(yes_data: str, no_data: str = "cancel") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ تأكيد", callback_data=yes_data)
    b.button(text="❌ إلغاء", callback_data=no_data)
    b.adjust(2)
    return b.as_markup()
