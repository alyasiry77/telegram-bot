from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.app.models.user import User
from bot.app.models.transaction import Transaction
import logging

logger = logging.getLogger(__name__)


async def add_transaction(
    session: AsyncSession,
    user: User,
    amount: int,
    type_: str,
    description: str = "",
    status: str = "completed",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    extra_data: Optional[dict] = None,
    commit: bool = True,
) -> Transaction:
    """
    Ledger-safe transaction.
    Uses SELECT FOR UPDATE on user row if postgres (via with_for_update).
    Must be called inside a transaction context.
    """
    # Lock user row for financial consistency
    # Re-fetch with lock
    result = await session.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = result.scalar_one()

    new_balance = locked_user.balance + amount
    if new_balance < 0:
        raise ValueError("Insufficient balance")

    locked_user.balance = new_balance
    if amount > 0:
        locked_user.total_earnings += amount
        if type_ in ("task_reward", "daily_task", "campaign_reward"):
            locked_user.task_earnings += amount
        elif type_ == "referral_bonus":
            locked_user.referral_earnings += amount
        elif type_ in ("daily_reward", "bonus"):
            locked_user.bonus_earnings += amount
    else:
        # debit, track withdrawals separately if needed handled elsewhere
        pass

    txn = Transaction(
        user_id=locked_user.id,
        type=type_,
        amount=amount,
        balance_after=new_balance,
        description=description,
        status=status,
        reference_type=reference_type,
        reference_id=reference_id,
        extra_data=extra_data,
    )
    session.add(txn)
    if commit:
        await session.commit()
        await session.refresh(locked_user)
        await session.refresh(txn)
    else:
        await session.flush()
    logger.info(f"Transaction {type_} {amount} for user {locked_user.telegram_id} balance {new_balance}")
    return txn


async def credit(
    session: AsyncSession,
    user: User,
    amount: int,
    type_: str,
    description: str = "",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> Transaction:
    if amount <= 0:
        raise ValueError("Credit amount must be positive")
    return await add_transaction(session, user, amount, type_, description, "completed", reference_type, reference_id)


async def debit(
    session: AsyncSession,
    user: User,
    amount: int,
    type_: str,
    description: str = "",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> Transaction:
    if amount <= 0:
        raise ValueError("Debit amount must be positive")
    return await add_transaction(session, user, -amount, type_, description, "completed", reference_type, reference_id)


async def reserve_for_withdrawal(
    session: AsyncSession,
    user: User,
    amount: int,
    reference_id: str,
) -> Transaction:
    """Reserve amount for pending withdrawal (hold)."""
    return await add_transaction(session, user, -amount, "withdrawal_pending", f"حجز سحب #{reference_id}", "pending", "withdrawal", reference_id)


async def refund_withdrawal(
    session: AsyncSession,
    user: User,
    amount: int,
    reference_id: str,
    reason: str = "رفض السحب",
) -> Transaction:
    return await add_transaction(session, user, amount, "withdrawal_refund", reason, "completed", "withdrawal", reference_id)
