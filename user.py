from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Integer, Float, Boolean, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.app.database.engine import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # points
    total_earnings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_withdrawals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    task_earnings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    referral_earnings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_earnings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    referral_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tasks_done: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    referrer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_daily_reward: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_daily_task: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    withdrawal_info: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    # --- New fields for upgrades ---
    language: Mapped[str] = mapped_column(String(5), default="ar", nullable=False)
    captcha_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    premium_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    kyc_status: Mapped[str] = mapped_column(String(16), default="none", nullable=False)  # none/pending/verified/rejected
    kyc_data: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    total_referral_volume: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # for tier calc
    last_spin: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    referrals_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    referrals_today_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    achievements: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # comma-separated

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    referrer: Mapped[Optional["User"]] = relationship("User", remote_side=[id], backref="referrals")

    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id"),
        Index("ix_users_referrer_id", "referrer_id"),
    )

    @property
    def full_name(self) -> str:
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p).strip() or f"User{self.telegram_id}"

    @property
    def cash_balance(self) -> float:
        # calculated via service with settings; placeholder
        return self.balance * 0.01
