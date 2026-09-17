from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User
from bot.app.models.task import TaskCompletion
from bot.app.models.campaign import Campaign
from bot.app.models.withdrawal import Withdrawal
from bot.app.models.transaction import Transaction

async def get_dashboard_stats(session: AsyncSession, days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=days)

    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
    new_today = (await session.execute(select(func.count(User.id)).where(User.created_at >= today_start))).scalar_one()
    new_week = (await session.execute(select(func.count(User.id)).where(User.created_at >= week_start))).scalar_one()
    active_today = (await session.execute(select(func.count(User.id)).where(User.last_activity >= today_start))).scalar_one()
    banned = (await session.execute(select(func.count(User.id)).where(User.is_banned == True))).scalar_one()

    total_tasks_done = (await session.execute(select(func.count(TaskCompletion.id)))).scalar_one()
    total_referrals = (await session.execute(select(func.coalesce(func.sum(User.referral_count), 0)))).scalar_one()

    total_earnings = (await session.execute(select(func.coalesce(func.sum(User.total_earnings), 0)))).scalar_one()
    total_withdrawals_points = (await session.execute(select(func.coalesce(func.sum(Withdrawal.amount_points), 0)).where(Withdrawal.status.in_(["pending","approved","paid"])))).scalar_one()
    total_paid = (await session.execute(select(func.coalesce(func.sum(Withdrawal.amount_points), 0)).where(Withdrawal.status == "paid"))).scalar_one()

    # Platform profit from campaigns
    platform_profit = (await session.execute(select(func.coalesce(func.sum(Campaign.platform_profit), 0)))).scalar_one()
    # Bonus: fees
    fee_sum = (await session.execute(select(func.coalesce(func.sum(Withdrawal.fee_points), 0)).where(Withdrawal.status == "paid"))).scalar_one()

    # Recent transactions volume
    total_campaigns = (await session.execute(select(func.count(Campaign.id)))).scalar_one()
    active_campaigns = (await session.execute(select(func.count(Campaign.id)).where(Campaign.status == "active"))).scalar_one()

    net_profit = (platform_profit + fee_sum)  # simplified

    return {
        "total_users": total_users,
        "new_today": new_today,
        "new_week": new_week,
        "active_today": active_today,
        "banned": banned,
        "total_tasks_done": total_tasks_done,
        "total_referrals": int(total_referrals),
        "total_earnings": int(total_earnings),
        "total_withdrawals_points": int(total_withdrawals_points),
        "total_paid": int(total_paid),
        "platform_profit": int(platform_profit),
        "fee_sum": int(fee_sum),
        "net_profit": int(net_profit),
        "total_campaigns": total_campaigns,
        "active_campaigns": active_campaigns,
    }
