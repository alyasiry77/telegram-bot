from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, ForeignKey, func, Float, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from bot.app.database.engine import Base


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_points: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_cash: Mapped[float] = mapped_column(Float, nullable=False)
    fee_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_points: Mapped[int] = mapped_column(Integer, nullable=False)  # amount - fee
    method: Mapped[str] = mapped_column(String(32), default="wallet", nullable=False)
    account_info: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)  # pending/approved/paid/rejected/cancelled
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proof_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_withdrawals_status", "status"),
        Index("ix_withdrawals_user_status", "user_id", "status"),
    )
