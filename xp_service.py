from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User

ACHIEVEMENTS = {
    "first_task": ("🎯 أول مهمة", 10),
    "tasks_10": ("📋 10 مهام", 20),
    "tasks_50": ("🏆 50 مهمة", 50),
    "refs_5": ("👥 5 إحالات", 15),
    "refs_20": ("👑 20 إحالة", 40),
    "withdraw_1": ("💸 أول سحب", 30),
}

def xp_for_level(xp: int) -> int:
    # every 100 xp = 1 level
    return xp // 100 + 1

async def add_xp(session: AsyncSession, user: User, amount: int, reason: str = ""):
    res = await session.execute(select(User).where(User.id == user.id).with_for_update())
    u = res.scalar_one()
    u.xp += amount
    # check achievements
    cur = set((u.achievements or "").split(",")) if u.achievements else set()
    new = []
    if u.tasks_done >= 1 and "first_task" not in cur:
        new.append("first_task")
    if u.tasks_done >= 10 and "tasks_10" not in cur:
        new.append("tasks_10")
    if u.tasks_done >= 50 and "tasks_50" not in cur:
        new.append("tasks_50")
    if u.referral_count >= 5 and "refs_5" not in cur:
        new.append("refs_5")
    if u.referral_count >= 20 and "refs_20" not in cur:
        new.append("refs_20")
    for a in new:
        cur.add(a)
        # bonus xp already counted? give extra
        bonus = ACHIEVEMENTS[a][1]
        u.xp += bonus
    u.achievements = ",".join(cur) if cur else None
    await session.commit()
    return new
