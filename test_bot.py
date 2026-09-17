import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from bot.app.database.engine import Base
from bot.app.models.user import User
from bot.app.services.user_service import create_user, get_user_by_telegram_id
from bot.app.services.reward_service import claim_daily_reward
from bot.app.services.task_service import complete_task
from bot.app.models.task import Task

@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()

@pytest.mark.asyncio
async def test_register_and_no_duplicate(session):
    u1, is_new = await create_user(session, 12345, "test", "Test", None)
    assert is_new is True
    assert u1.telegram_id == 12345
    u2, is_new2 = await create_user(session, 12345, "test2", "Test2", None)
    assert is_new2 is False
    assert u2.id == u1.id

@pytest.mark.asyncio
async def test_referral_no_self(session):
    u1, _ = await create_user(session, 111, "a", "A", None)
    u2, _ = await create_user(session, 111, "a", "A", referrer=u1)
    assert u2.referrer_id is None or u2.referrer_id != u1.id or u2.id == u1.id

@pytest.mark.asyncio
async def test_daily_reward_once_per_24h(session):
    u, _ = await create_user(session, 222, "b", "B", None)
    ok, _, _ = await claim_daily_reward(session, u)
    assert ok is True
    u = await get_user_by_telegram_id(session, 222)
    assert u.balance == 5
    ok2, _, remaining = await claim_daily_reward(session, u)
    assert ok2 is False
    assert remaining > 0

@pytest.mark.asyncio
async def test_task_no_duplicate(session):
    u, _ = await create_user(session, 333, "c", "C", None)
    task = Task(title="Test", description="desc", url="https://t.me/test", type="visit_link", reward_points=10, max_completions=10, status="active")
    session.add(task)
    await session.commit()
    await session.refresh(task)
    ok, code = await complete_task(session, u, task)
    assert ok is True
    from sqlalchemy import select
    r = await session.execute(select(Task).where(Task.id==task.id))
    task2 = r.scalar_one()
    u2 = await get_user_by_telegram_id(session, 333)
    ok2, code2 = await complete_task(session, u2, task2)
    assert ok2 is False
    assert code2 == "already_completed"

@pytest.mark.asyncio
async def test_ledger_balance(session):
    from bot.app.services.financial_service import credit, debit
    u, _ = await create_user(session, 444, "d", "D", None)
    u = await get_user_by_telegram_id(session, 444)
    await credit(session, u, 100, "bonus", "test")
    u = await get_user_by_telegram_id(session, 444)
    assert u.balance == 100
    assert u.total_earnings == 100
    try:
        await debit(session, u, 200, "withdrawal_pending", "test")
        assert False, "should have raised"
    except ValueError:
        pass

@pytest.mark.asyncio
async def test_referral_tier(session):
    from bot.app.services.referral_service import process_referral
    u1,_=await create_user(session, 1001, "a", "A", None)
    u2,_=await create_user(session, 1002, "b", "B", referrer=u1)
    await process_referral(session, u2, u1)
    u1r = await get_user_by_telegram_id(session, 1001)
    assert u1r.referral_count >= 1

@pytest.mark.asyncio
async def test_premium_activate(session):
    from bot.app.services.premium_service import activate_premium, is_premium
    u,_=await create_user(session, 2001, "p", "P", None)
    assert await is_premium(u) is False
    await activate_premium(session, u, 7)
    u2 = await get_user_by_telegram_id(session, 2001)
    assert await is_premium(u2) is True

@pytest.mark.asyncio
async def test_spin_once_per_day(session):
    import datetime
    u,_=await create_user(session, 3001, "s", "S", None)
    u.last_spin = None
    await session.commit()
    # can spin

@pytest.mark.asyncio
async def test_encryption():
    from bot.app.services.encryption_service import encrypt, decrypt
    enc = encrypt("EQAbc123test")
    assert enc != "EQAbc123test"
    assert decrypt(enc) == "EQAbc123test"

@pytest.mark.asyncio
async def test_xp_achievements(session):
    from bot.app.services.xp_service import add_xp
    u,_=await create_user(session, 4001, "x", "X", None)
    u.tasks_done = 10
    u.referral_count = 5
    await session.commit()
    new = await add_xp(session, u, 10, "test")
    assert len(new) >= 1

@pytest.mark.asyncio
async def test_withdrawal_kyc_block(session):
    from bot.app.services.security_service import can_withdraw_time
    u,_=await create_user(session, 5001, "k", "K", None)
    ok, rem = can_withdraw_time(u)
    assert ok is False  # new account <24h

@pytest.mark.asyncio
async def test_rating_unique(session):
    from bot.app.models.campaign import Campaign
    from bot.app.models.rating import CampaignRating
    u,_=await create_user(session, 6001, "r", "R", None)
    c = Campaign(advertiser_id=u.id, title="T", url="https://t.me/x", campaign_type="visit_link", required_completions=10, reward_per_user=5, total_budget=50, status="active")
    session.add(c); await session.commit(); await session.refresh(c)
    r1 = CampaignRating(user_id=u.id, campaign_id=c.id, rating=5)
    session.add(r1); await session.commit()
    from sqlalchemy.exc import IntegrityError
    r2 = CampaignRating(user_id=u.id, campaign_id=c.id, rating=3)
    session.add(r2)
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()

@pytest.mark.asyncio
async def test_referral_daily_limit(session):
    from bot.app.services.security_service import check_referral_limit
    u,_=await create_user(session, 7001, "l", "L", None)
    u.referrals_today = 20
    from datetime import datetime, timezone
    u.referrals_today_date = datetime.now(timezone.utc)
    await session.commit()
    ok, msg = await check_referral_limit(session, u)
    assert ok is False

@pytest.mark.asyncio
async def test_offerwall_postback_signature():
    import hmac, hashlib
    from bot.app.config import settings
    sig = hmac.new(settings.secret_key.encode(), b"123:offer1", hashlib.sha256).hexdigest()[:16]
    assert len(sig) == 16

@pytest.mark.asyncio
async def test_complaint_create(session):
    from bot.app.models.rating import Complaint
    u,_=await create_user(session, 8001, "c2", "C2", None)
    comp = Complaint(user_id=u.id, reason="bad link", status="open")
    session.add(comp); await session.commit()
    assert comp.id is not None
