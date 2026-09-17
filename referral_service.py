from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.user import User
from bot.app.services.financial_service import credit
from bot.app.services.settings_service import get_int
import logging

logger = logging.getLogger(__name__)

async def process_referral(session: AsyncSession, new_user: User, referrer: User) -> bool:
    """
    Apply referral reward if valid.
    Returns True if reward given.
    Prevents: self, duplicate, existing user.
    new_user must be newly created and already linked via referrer_id.
    """
    if not referrer or not new_user:
        return False
    if referrer.id == new_user.id:
        return False
    if referrer.telegram_id == new_user.telegram_id:
        return False
    if new_user.referrer_id != referrer.id:
        return False
    # Check if this new_user already counted? new_user is_new so ok
    # But prevent if referrer already rewarded for this user via transaction check
    from sqlalchemy import select
    from bot.app.models.transaction import Transaction
    existing = await session.execute(
        select(Transaction).where(
            Transaction.user_id == referrer.id,
            Transaction.reference_type == "referral",
            Transaction.reference_id == str(new_user.id)
        )
    )
    if existing.scalar_one_or_none():
        logger.warning(f"Duplicate referral bonus attempt: {referrer.id} -> {new_user.id}")
        return False

    # Anti-fraud: daily limit & farming
    from bot.app.services.security_service import check_referral_limit, increment_referral_today
    ok_lim, msg = await check_referral_limit(session, referrer)
    if not ok_lim:
        logger.warning(f"Referral blocked {referrer.telegram_id}: {msg}")
        return False
    reward = await get_int(session, "referral_reward", 5)
    tier2_pct = await get_int(session, "referral_tier2_percent", 10)
    tier3_pct = await get_int(session, "referral_tier3_percent", 5)
    if reward <= 0:
        return False

    # Credit referrer L1
    await credit(
        session, referrer, reward, "referral_bonus",
        f"مكافأة إحالة L1 مستخدم {new_user.telegram_id}",
        reference_type="referral",
        reference_id=str(new_user.id)
    )
    await increment_referral_today(session, referrer)
    # Tier2: referrer's referrer
    if referrer.referrer_id and tier2_pct > 0:
        from sqlalchemy import select as sel2
        r2 = await session.execute(sel2(User).where(User.id == referrer.referrer_id))
        upline = r2.scalar_one_or_none()
        if upline:
            bonus2 = int(reward * tier2_pct / 100)
            if bonus2 > 0:
                await credit(session, upline, bonus2, "referral_bonus", f"مكافأة إحالة L2 من {new_user.telegram_id}", reference_type="referral_t2", reference_id=str(new_user.id))
    # Tier3
    if referrer.referrer_id and tier3_pct > 0:
        # get L2's referrer
        try:
            r2 = await session.execute(sel2(User).where(User.id == referrer.referrer_id))
            l2 = r2.scalar_one_or_none()
            if l2 and l2.referrer_id:
                r3 = await session.execute(sel2(User).where(User.id == l2.referrer_id))
                upline3 = r3.scalar_one_or_none()
                if upline3:
                    bonus3 = int(reward * tier3_pct / 100)
                    if bonus3 > 0:
                        await credit(session, upline3, bonus3, "referral_bonus", f"L3 {new_user.telegram_id}", reference_type="referral_t3", reference_id=str(new_user.id))
        except:
            pass
    # Update counts
    # Reload referrer to ensure balance updated (credit did)
    # Need to update referral_count and level
    from sqlalchemy import select as sel
    r = await session.execute(sel(User).where(User.id == referrer.id).with_for_update())
    locked = r.scalar_one()
    locked.referral_count += 1
    # Update level
    from bot.app.messages import get_level
    lvl_thresholds = {
        1: await get_int(session, "level_2_threshold", 10) and 0 or 0,
    }
    # Actually get levels properly
    t2 = await get_int(session, "level_2_threshold", 10)
    t3 = await get_int(session, "level_3_threshold", 50)
    t4 = await get_int(session, "level_4_threshold", 200)
    thresholds = {1: 0, 2: t2, 3: t3, 4: t4}
    lvl, _ = get_level(locked.referral_count, thresholds)
    locked.level = lvl
    await session.commit()
    logger.info(f"Referral reward {reward} given to {referrer.telegram_id} for {new_user.telegram_id}")
    return True
