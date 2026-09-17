from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User
from bot.app.services.settings_service import get_int, get_float

async def is_premium(user: User) -> bool:
    if not user.is_premium:
        return False
    if user.premium_until and user.premium_until < datetime.now(timezone.utc):
        return False
    return True

async def premium_multiplier(session: AsyncSession, user: User) -> float:
    if await is_premium(user):
        # e.g. 1.5x or 2x configurable
        try:
            from bot.app.services.settings_service import get_float as gf
            mult = await gf(session, "premium_multiplier", 2.0)
            return float(mult)
        except:
            return 2.0
    return 1.0

async def activate_premium(session: AsyncSession, user: User, days: int = 30):
    from sqlalchemy import select as sel
    res = await session.execute(sel(User).where(User.id == user.id).with_for_update())
    u = res.scalar_one()
    now = datetime.now(timezone.utc)
    base = u.premium_until if u.premium_until and u.premium_until > now else now
    u.premium_until = base + timedelta(days=days)
    u.is_premium = True
    await session.commit()

async def get_premium_price(session: AsyncSession) -> int:
    return await get_int(session, "premium_price", 500)  # points
