from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.app.models.withdrawal import Withdrawal
from bot.app.models.user import User
from bot.app.services.settings_service import get_int, get_float
from bot.app.services.financial_service import reserve_for_withdrawal, refund_withdrawal

async def can_withdraw(session: AsyncSession, user: User) -> tuple[bool, str]:
    min_bal = await get_int(session, "min_withdrawal_balance", 100)
    min_ref = await get_int(session, "min_withdrawal_referrals", 3)
    if user.balance < min_bal:
        return False, f"رصيدك {user.balance} أقل من الحد الأدنى {min_bal} نقطة"
    if user.referral_count < min_ref:
        return False, f"تحتاج {min_ref} إحالات على الأقل (لديك {user.referral_count})"
    if user.is_banned:
        return False, "حسابك محظور"
    return True, "ok"

async def create_withdrawal(
    session: AsyncSession,
    user: User,
    amount_points: int,
    method: str,
    account_info: str,
) -> tuple[bool, str, Withdrawal | None]:
    min_bal = await get_int(session, "min_withdrawal_balance", 100)
    min_cash = await get_float(session, "min_withdrawal_amount", 1.0)
    rate = await get_float(session, "points_to_cash", 0.01)
    fee_pct = await get_float(session, "withdrawal_fee_percent", 0)
    min_ref = await get_int(session, "min_withdrawal_referrals", 3)

    if amount_points < min_bal:
        return False, f"الحد الأدنى {min_bal} نقطة", None
    if user.balance < amount_points:
        return False, "رصيد غير كافٍ", None
    if user.referral_count < min_ref:
        return False, f"تحتاج {min_ref} إحالات", None
    cash = amount_points * rate
    if cash < min_cash:
        return False, f"الحد الأدنى للسحب ${min_cash:.2f} (رصيدك ${cash:.2f})", None
    if not account_info or len(account_info.strip()) < 4:
        return False, "بيانات المحفظة/الحساب غير صحيحة", None

    fee_points = int(amount_points * fee_pct / 100)
    net_points = amount_points - fee_points
    net_cash = net_points * rate

    # Check duplicate pending?
    res = await session.execute(select(Withdrawal).where(Withdrawal.user_id == user.id, Withdrawal.status == "pending"))
    if res.scalars().first():
        return False, "لديك طلب سحب معلق بالفعل، انتظر معالجته", None

    # Reserve balance
    # Need fresh user lock inside financial service
    withdrawal = Withdrawal(
        user_id=user.id,
        amount_points=amount_points,
        amount_cash=cash,
        fee_points=fee_points,
        net_points=net_points,
        method=method,
        account_info=account_info.strip(),
        status="pending",
    )
    session.add(withdrawal)
    await session.flush()  # get id

    try:
        # reserve_for_withdrawal does commit internally (adds Transaction and updates balance)
        # withdrawal row is already flushed, so commit will persist both
        await reserve_for_withdrawal(session, user, amount_points, str(withdrawal.id))
    except ValueError as e:
        await session.rollback()
        return False, str(e), None
    except Exception as e:
        await session.rollback()
        return False, f"خطأ: {e}", None

    # Re-fetch (already committed inside reserve)
    # Need to ensure withdrawal still exists after commit
    await session.refresh(withdrawal)
    return True, "ok", withdrawal

async def process_withdrawal_admin(
    session: AsyncSession,
    withdrawal_id: int,
    action: str,  # approve/paid/reject/cancel
    admin_note: str = "",
) -> tuple[bool, str]:
    res = await session.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id).with_for_update())
    w = res.scalar_one_or_none()
    if not w:
        return False, "الطلب غير موجود"
    if w.status not in ("pending", "approved"):
        return False, f"حالة الطلب {w.status} لا تسمح بهذا الإجراء"

    from sqlalchemy import select as sel
    from bot.app.models.user import User

    if action == "approve":
        w.status = "approved"
        w.admin_note = admin_note
        w.processed_at = datetime.now(timezone.utc)
    elif action == "paid":
        w.status = "paid"
        w.admin_note = admin_note
        w.processed_at = datetime.now(timezone.utc)
        # Update user total_withdrawals
        ures = await session.execute(sel(User).where(User.id == w.user_id).with_for_update())
        u = ures.scalar_one()
        u.total_withdrawals += w.amount_points
    elif action == "reject":
        # refund
        ures = await session.execute(sel(User).where(User.id == w.user_id).with_for_update())
        u = ures.scalar_one()
        await refund_withdrawal(session, u, w.amount_points, str(w.id), "استرداد سحب مرفوض")
        w.status = "rejected"
        w.admin_note = admin_note
        w.processed_at = datetime.now(timezone.utc)
    elif action == "cancel":
        ures = await session.execute(sel(User).where(User.id == w.user_id).with_for_update())
        u = ures.scalar_one()
        await refund_withdrawal(session, u, w.amount_points, str(w.id), "إلغاء سحب")
        w.status = "cancelled"
        w.admin_note = admin_note
        w.processed_at = datetime.now(timezone.utc)
    else:
        return False, "إجراء غير معروف"

    await session.commit()
    return True, "ok"

async def get_pending_withdrawals(session: AsyncSession):
    res = await session.execute(select(Withdrawal).where(Withdrawal.status == "pending").order_by(Withdrawal.created_at.asc()))
    return res.scalars().all()
