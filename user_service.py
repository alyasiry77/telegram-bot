from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    referrer: Optional[User] = None,
) -> tuple[User, bool]:
    """Returns (user, is_new). Handles referral linking safely."""
    existing = await get_user_by_telegram_id(session, telegram_id)
    if existing:
        # update info & activity
        existing.username = username
        existing.first_name = first_name
        existing.last_name = last_name
        existing.last_activity = datetime.now(timezone.utc)
        await session.commit()
        return existing, False

    # Prevent self-referral: caller must ensure referrer.telegram_id != telegram_id
    referrer_id = None
    if referrer and referrer.telegram_id != telegram_id:
        referrer_id = referrer.id

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        referrer_id=referrer_id,
        balance=0,
    )
    session.add(user)
    await session.flush()  # get id

    # If referred, increment referrer count will be handled via referral service (to add bonus)
    await session.commit()
    await session.refresh(user)
    return user, True

async def update_activity(session: AsyncSession, user: User):
    user.last_activity = datetime.now(timezone.utc)
    await session.commit()

async def count_users(session: AsyncSession) -> int:
    r = await session.execute(select(func.count(User.id)))
    return r.scalar_one()

async def is_banned(user: User) -> bool:
    return user.is_banned
