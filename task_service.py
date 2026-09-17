from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.task import Task, TaskCompletion
from bot.app.models.campaign import Campaign, CampaignCompletion
from bot.app.models.user import User
from bot.app.services.financial_service import credit
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

async def get_active_tasks(session: AsyncSession) -> List[Task]:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Task).where(
            Task.status == "active",
        ).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    # filter expired
    active = []
    for t in tasks:
        if t.expires_at and t.expires_at < now:
            continue
        if t.current_completions >= t.max_completions:
            continue
        active.append(t)
    return active

async def get_user_completed_task_ids(session: AsyncSession, user_id: int) -> set:
    r = await session.execute(select(TaskCompletion.task_id).where(TaskCompletion.user_id == user_id))
    return set(x for x in r.scalars().all())

async def complete_task(
    session: AsyncSession,
    user: User,
    task: Task,
    verify_membership: bool = False,
    is_member: Optional[bool] = None,
) -> tuple[bool, str]:
    """
    Attempt to complete task. Returns (success, code).
    Codes: ok, already_completed, limit_reached, not_member, expired, inactive, error
    """
    # Check already completed
    existing = await session.execute(
        select(TaskCompletion).where(TaskCompletion.user_id == user.id, TaskCompletion.task_id == task.id)
    )
    if existing.scalar_one_or_none():
        return False, "already_completed"

    if task.status != "active":
        return False, "inactive"
    if task.expires_at and task.expires_at < datetime.now(timezone.utc):
        return False, "expired"
    if task.current_completions >= task.max_completions:
        return False, "limit_reached"

    # Verify membership if required
    if task.type in ("channel_join", "group_join") and verify_membership:
        if is_member is False:
            return False, "not_member"
        if is_member is None:
            return False, "verification_failed"

    # Create completion + credit atomically
    try:
        # Lock task row
        locked_task_res = await session.execute(select(Task).where(Task.id == task.id).with_for_update())
        locked_task = locked_task_res.scalar_one()
        if locked_task.current_completions >= locked_task.max_completions:
            return False, "limit_reached"

        completion = TaskCompletion(
            user_id=user.id,
            task_id=task.id,
            reward_points=task.reward_points,
            status="completed"
        )
        session.add(completion)
        locked_task.current_completions += 1

        # Credit user
        await credit(session, user, task.reward_points, "task_reward", f"مكافأة مهمة: {task.title}", reference_type="task", reference_id=str(task.id))
        # Update tasks_done + XP
        r = await session.execute(select(User).where(User.id == user.id).with_for_update())
        locked_user = r.scalar_one()
        locked_user.tasks_done += 1
        # XP: 5 per task
        try:
            from bot.app.services.xp_service import add_xp
            await add_xp(session, locked_user, 5, "task")
        except:
            pass

        await session.commit()
        return True, "ok"
    except IntegrityError:
        await session.rollback()
        return False, "already_completed"
    except Exception as e:
        await session.rollback()
        logger.exception(f"complete_task error: {e}")
        return False, "error"


# Campaign helpers - similar
async def get_active_campaigns(session: AsyncSession) -> List[Campaign]:
    result = await session.execute(select(Campaign).where(Campaign.status == "active").order_by(Campaign.created_at.desc()))
    return list(result.scalars().all())

async def get_user_campaign_ids(session: AsyncSession, user_id: int) -> set:
    r = await session.execute(select(CampaignCompletion.campaign_id).where(CampaignCompletion.user_id == user_id))
    return set(r.scalars().all())

async def complete_campaign(
    session: AsyncSession,
    user: User,
    campaign: Campaign,
    verify_membership: bool = False,
    is_member: Optional[bool] = None,
) -> tuple[bool, str]:
    existing = await session.execute(select(CampaignCompletion).where(CampaignCompletion.user_id == user.id, CampaignCompletion.campaign_id == campaign.id))
    if existing.scalar_one_or_none():
        return False, "already_completed"
    if campaign.status != "active":
        return False, "inactive"
    if campaign.current_completions >= campaign.required_completions:
        return False, "limit_reached"
    if campaign.type_check_membership(verify_membership, is_member) is False:
        return False, "not_member"

    try:
        locked_res = await session.execute(select(Campaign).where(Campaign.id == campaign.id).with_for_update())
        locked = locked_res.scalar_one()
        if locked.current_completions >= locked.required_completions:
            return False, "limit_reached"

        comp = CampaignCompletion(user_id=user.id, campaign_id=campaign.id, reward_points=campaign.reward_per_user, status="completed")
        session.add(comp)
        locked.current_completions += 1
        if locked.current_completions >= locked.required_completions:
            locked.status = "completed"

        await credit(session, user, campaign.reward_per_user, "campaign_reward", f"مكافأة حملة: {campaign.title}", reference_type="campaign", reference_id=str(campaign.id))
        r = await session.execute(select(User).where(User.id == user.id).with_for_update())
        locked_user = r.scalar_one()
        locked_user.tasks_done += 1
        await session.commit()
        return True, "ok"
    except IntegrityError:
        await session.rollback()
        return False, "already_completed"
    except Exception as e:
        await session.rollback()
        logger.exception(e)
        return False, "error"

# Monkey patch helper for campaign membership check
def _campaign_type_check(self, verify, is_member):
    if self.campaign_type in ("channel_join", "group_join") and verify:
        if is_member is False:
            return False
        if is_member is None:
            return None
    return True

Campaign.type_check_membership = _campaign_type_check  # type: ignore
