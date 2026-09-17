import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from bot.app.database.engine import async_session
from bot.app.models.user import User

logger = logging.getLogger(__name__)

async def daily_reminder_loop(bot):
    """Smart: only users whose reward is actually ready and active in last 3 days."""
    while True:
        try:
            await asyncio.sleep(3600)
            async with async_session() as session:
                threshold = datetime.now(timezone.utc) - timedelta(hours=24)
                recent = datetime.now(timezone.utc) - timedelta(days=3)
                res = await session.execute(
                    select(User).where(
                        (User.last_daily_reward == None) | (User.last_daily_reward <= threshold),
                        User.is_banned == False,
                        User.last_activity >= recent,
                        User.captcha_verified == True
                    ).limit(100)
                )
                users = res.scalars().all()
                for u in users:
                    try:
                        await bot.send_message(u.telegram_id, "🎁 <b>مكافأتك اليومية جاهزة!</b>\nاضغط 🎁 المكافأة اليومية لاستلام 5 نقاط", parse_mode="HTML")
                        await asyncio.sleep(0.08)
                    except Exception as e:
                        if "blocked" in str(e).lower():
                            continue
                        pass
        except Exception as e:
            logger.warning(f"reminder loop error {e}")
            await asyncio.sleep(3600)

async def premium_expiry_loop():
    while True:
        try:
            await asyncio.sleep(86400)
            async with async_session() as session:
                now = datetime.now(timezone.utc)
                res = await session.execute(select(User).where(User.is_premium == True, User.premium_until != None, User.premium_until < now))
                for u in res.scalars().all():
                    u.is_premium = False
                await session.commit()
        except:
            await asyncio.sleep(86400)

async def weekly_contest_loop(bot):
    while True:
        try:
            await asyncio.sleep(86400)
            # Run Monday 00:00 UTC
            now = datetime.now(timezone.utc)
            if now.weekday() == 0:  # Monday
                async with async_session() as s:
                    from bot.app.services.contest_service import distribute_weekly_prizes
                    await distribute_weekly_prizes(s, bot)
                    await asyncio.sleep(86400)
            await asyncio.sleep(3600)
        except:
            await asyncio.sleep(3600)
