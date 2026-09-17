from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User
from bot.app.services.financial_service import credit
from bot.app.services.settings_service import get_int
from sqlalchemy import select

async def claim_daily_reward(session: AsyncSession, user: User) -> tuple[bool, str, int]:
    """
    Returns (success, message, remaining_seconds)
    """
    now = datetime.now(timezone.utc)
    reward = await get_int(session, "daily_reward", 5)

    # Need to lock user
    r = await session.execute(select(User).where(User.id == user.id).with_for_update())
    locked = r.scalar_one()

    if locked.last_daily_reward:
        last = locked.last_daily_reward
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = now - last
        if elapsed < timedelta(hours=24):
            remaining = timedelta(hours=24) - elapsed
            total_sec = int(remaining.total_seconds())
            return False, "wait", total_sec

    # Credit
    await credit(session, locked, reward, "daily_reward", "المكافأة اليومية", reference_type="daily_reward", reference_id=now.isoformat())
    # Update last claim
    locked.last_daily_reward = now
    await session.commit()
    await session.refresh(locked)
    return True, "ok", 0


async def claim_daily_task(session: AsyncSession, user: User) -> tuple[bool, str, int]:
    """Daily task is similar but separate timer — DAILY_TASK_POINTS."""
    now = datetime.now(timezone.utc)
    reward = await get_int(session, "daily_task_points", 10)
    r = await session.execute(select(User).where(User.id == user.id).with_for_update())
    locked = r.scalar_one()
    if locked.last_daily_task:
        last = locked.last_daily_task
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if now - last < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last)
            return False, "wait", int(remaining.total_seconds())
    await credit(session, locked, reward, "daily_task", "مكافأة المهمة اليومية", reference_type="daily_task", reference_id=now.isoformat())
    locked.last_daily_task = now
    await session.commit()
    await session.refresh(locked)
    return True, "ok", 0
