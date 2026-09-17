from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.settings import Setting

DEFAULTS = {
    "daily_reward": "5",
    "daily_task_points": "10",
    "points_to_cash": "0.01",
    "min_withdrawal_balance": "100",
    "min_withdrawal_amount": "1.0",
    "min_withdrawal_referrals": "3",
    "referral_reward": "5",
    "campaign_profit_percent": "30",
    "withdrawal_fee_percent": "0",
    "channel_username": "@your_channel",
    "support_username": "@support",
    "maintenance_mode": "false",
    "premium_price": "100",
    "level_2_threshold": "10",
    "level_3_threshold": "50",
    "level_4_threshold": "200",
}


async def get_setting(session: AsyncSession, key: str, default: Optional[str] = None) -> str:
    res = await session.execute(select(Setting).where(Setting.key == key))
    obj = res.scalar_one_or_none()
    if obj:
        return obj.value
    if key in DEFAULTS:
        return DEFAULTS[key]
    if default is not None:
        return default
    return ""


async def get_int(session: AsyncSession, key: str, default: int = 0) -> int:
    v = await get_setting(session, key, str(default))
    try:
        return int(float(v))
    except:
        return default


async def get_float(session: AsyncSession, key: str, default: float = 0.0) -> float:
    v = await get_setting(session, key, str(default))
    try:
        return float(v)
    except:
        return default


async def get_bool(session: AsyncSession, key: str, default: bool = False) -> bool:
    v = await get_setting(session, key, str(default).lower())
    return v.lower() in ("true", "1", "yes", "on")


async def set_setting(session: AsyncSession, key: str, value: str, description: Optional[str] = None):
    res = await session.execute(select(Setting).where(Setting.key == key))
    obj = res.scalar_one_or_none()
    if obj:
        obj.value = value
    else:
        obj = Setting(key=key, value=value, description=description)
        session.add(obj)
    await session.commit()


async def get_all_settings(session: AsyncSession) -> dict:
    res = await session.execute(select(Setting))
    rows = res.scalars().all()
    data = {k: v for k, v in DEFAULTS.items()}
    for r in rows:
        data[r.key] = r.value
    return data
