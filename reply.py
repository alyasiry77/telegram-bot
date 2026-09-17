from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏠 الرئيسية"))
    builder.add(KeyboardButton(text="🎁 المكافأة اليومية"))
    builder.add(KeyboardButton(text="📋 المهام"))
    builder.add(KeyboardButton(text="💰 المهام المدفوعة"))
    builder.add(KeyboardButton(text="👥 الإحالة"))
    builder.add(KeyboardButton(text="💸 سحب الأرباح"))
    builder.add(KeyboardButton(text="👤 ملفي وأرباحي"))
    builder.add(KeyboardButton(text="💳 الحساب المالي"))
    builder.add(KeyboardButton(text="📢 أعلن معنا"))
    builder.add(KeyboardButton(text="📣 قناتنا"))
    builder.add(KeyboardButton(text="ℹ️ عن البوت"))
    builder.add(KeyboardButton(text="📞 الدعم الفني"))
    builder.add(KeyboardButton(text="⚙️ الإعدادات"))
    builder.add(KeyboardButton(text="🏆 المتصدرون"))
    builder.add(KeyboardButton(text="🎡 عجلة الحظ"))
    builder.add(KeyboardButton(text="🌐 لوحة الويب"))
    builder.add(KeyboardButton(text="💎 بريميوم"))
    if is_admin:
        builder.add(KeyboardButton(text="🛡️ لوحة الإدارة"))
    builder.adjust(2, 2, 2, 2, 2, 2, 2, 2)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="اختر من القائمة...")

def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ إلغاء"), KeyboardButton(text="🏠 الرئيسية")]
        ],
        resize_keyboard=True
    )

def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ رجوع"), KeyboardButton(text="🏠 الرئيسية")]
        ],
        resize_keyboard=True
    )
