import random
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User

# In-memory captcha store (use Redis in production)
_captcha_store: dict[int, tuple[str, float]] = {}
_otp_store: dict[int, tuple[str, float]] = {}

def generate_captcha() -> tuple[str, str]:
    """Returns (question, answer). Simple math."""
    a, b = random.randint(2, 9), random.randint(2, 9)
    op = random.choice(["+", "×"])
    if op == "+":
        q = f"{a} + {b} = ?"
        ans = str(a + b)
    else:
        q = f"{a} × {b} = ?"
        ans = str(a * b)
    return q, ans

def set_captcha(user_id: int, answer: str):
    _captcha_store[user_id] = (answer, time.time() + 300)

def verify_captcha(user_id: int, text: str) -> bool:
    data = _captcha_store.get(user_id)
    if not data:
        return False
    ans, exp = data
    if time.time() > exp:
        _captcha_store.pop(user_id, None)
        return False
    if text.strip() == ans:
        _captcha_store.pop(user_id, None)
        return True
    return False

# 2FA OTP for admin sensitive actions
def generate_otp(admin_id: int) -> str:
    code = f"{random.randint(100000, 999999)}"
    _otp_store[admin_id] = (code, time.time() + 300)
    return code

def verify_otp(admin_id: int, code: str) -> bool:
    data = _otp_store.get(admin_id)
    if not data:
        return False
    exp_code, exp = data
    if time.time() > exp:
        _otp_store.pop(admin_id, None)
        return False
    if code == exp_code:
        _otp_store.pop(admin_id, None)
        return True
    return False

# Anti-fraud: referral farming detection
async def check_referral_limit(session: AsyncSession, referrer: User) -> tuple[bool, str]:
    from bot.app.services.settings_service import get_int
    max_per_day = await get_int(session, "max_referrals_per_day", 20)
    now = datetime.now(timezone.utc)
    # reset daily counter if date changed
    if referrer.referrals_today_date and referrer.referrals_today_date.date() != now.date():
        referrer.referrals_today = 0
        referrer.referrals_today_date = now
        await session.commit()
    if referrer.referrals_today >= max_per_day:
        return False, f"تجاوزت الحد اليومي {max_per_day} إحالة"
    # farming: too many referrals in last hour from same referrer with similar names?
    # simple: if >5 in last hour, flag
    one_hour_ago = now - timedelta(hours=1)
    cnt = (await session.execute(
        select(func.count(User.id)).where(User.referrer_id == referrer.id, User.created_at >= one_hour_ago)
    )).scalar_one()
    if cnt >= 5:
        return False, "نشاط إحالة مريب - تم التقييد مؤقتاً، حاول بعد ساعة"
    return True, "ok"

async def increment_referral_today(session: AsyncSession, referrer: User):
    now = datetime.now(timezone.utc)
    if not referrer.referrals_today_date or referrer.referrals_today_date.date() != now.date():
        referrer.referrals_today = 1
        referrer.referrals_today_date = now
    else:
        referrer.referrals_today += 1
    await session.commit()

# Withdrawal delay 24h for new accounts
def can_withdraw_time(user: User) -> tuple[bool, int]:
    now = datetime.now(timezone.utc)
    created = user.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if not created:
        return True, 0
    elapsed = now - created
    if elapsed < timedelta(hours=24):
        remaining = timedelta(hours=24) - elapsed
        return False, int(remaining.total_seconds())
    return True, 0
