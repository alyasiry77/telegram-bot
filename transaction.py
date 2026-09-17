from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey, func, BigInteger, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON
from bot.app.database.engine import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # credit/debit type
    # e.g: daily_reward, daily_task, task_reward, referral_bonus, withdrawal_pending, withdrawal_fee, deposit, admin_adjustment, campaign_reward
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # points, can be negative for debit
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="completed", nullable=False)  # pending/completed/reversed/failed
    reference_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_transactions_user_id_created", "user_id", "created_at"),
        Index("ix_transactions_reference", "reference_type", "reference_id"),
    )
