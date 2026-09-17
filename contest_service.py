from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User
from bot.app.services.financial_service import credit

async def weekly_leaderboard(session: AsyncSession, limit: int = 10):
    since = datetime.now(timezone.utc) - timedelta(days=7)
    res = await session.execute(
        select(User).where(User.created_at >= since).order_by(desc(User.referral_count), desc(User.balance)).limit(limit)
    )
    return res.scalars().all()

async def distribute_weekly_prizes(session: AsyncSession, bot):
    """Call via scheduler every Monday."""
    top = await weekly_leaderboard(session, 3)
    prizes = [500, 300, 150]
    for i, u in enumerate(top):
        if i < len(prizes):
            await credit(session, u, prizes[i], "bonus", f"🏆 مسابقة أسبوعية المركز {i+1}")
            try:
                await bot.send_message(u.telegram_id, f"🏆 مبروك! فزت بالمركز {i+1} في المسابقة الأسبوعية +{prizes[i]} نقطة")
            except:
                pass
