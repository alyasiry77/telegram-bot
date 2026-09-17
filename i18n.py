STRINGS = {
    "ar": {
        "welcome": "مرحباً",
        "balance": "رصيدك",
        "daily": "المكافأة اليومية",
        "level": "المستوى",
        "withdraw": "سحب الأرباح",
        "tasks": "المهام",
        "referral": "الإحالة",
        "premium": "بريميوم",
        "spin": "عجلة الحظ",
        "leaderboard": "المتصدرون",
    },
    "en": {
        "welcome": "Welcome",
        "balance": "Balance",
        "daily": "Daily Reward",
        "level": "Level",
        "withdraw": "Withdraw",
        "tasks": "Tasks",
        "referral": "Referral",
        "premium": "Premium",
        "spin": "Spin Wheel",
        "leaderboard": "Leaderboard",
    }
}

def t(user, key: str) -> str:
    lang = getattr(user, "language", "ar") if user else "ar"
    return STRINGS.get(lang, STRINGS["ar"]).get(key, key)
