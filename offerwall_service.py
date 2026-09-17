from datetime import datetime, timezone
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.task import Task

# Mock offerwall offers; in production call external API
MOCK_OFFERS = [
    {"title": "حمّل تطبيق X وجرّبه", "url": "https://example.com/offer1", "reward": 50, "provider": "cpx"},
    {"title": "أكمل استبيان 2 دقيقة", "url": "https://example.com/offer2", "reward": 30, "provider": "timewall"},
]

async def fetch_offers() -> List[dict]:
    return MOCK_OFFERS

async def sync_offerwall_tasks(session: AsyncSession):
    """Create/sync offerwall tasks into tasks table."""
    for o in MOCK_OFFERS:
        exists = await session.execute(select(Task).where(Task.title == o["title"]))
        if not exists.scalar_one_or_none():
            t = Task(title=o["title"], description=f"عبر {o['provider']} - Offerwall", url=o["url"], type="visit_link", reward_points=o["reward"], max_completions=10000, status="active")
            session.add(t)
    await session.commit()
