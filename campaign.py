from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from bot.app.database.engine import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    advertiser_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(32), default="channel_join", nullable=False)
    required_completions: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_per_user: Mapped[int] = mapped_column(Integer, nullable=False)  # points
    total_budget: Mapped[int] = mapped_column(Integer, nullable=False)  # points (required * reward)
    platform_fee_percent: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    platform_profit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_completions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)  # pending/approved/active/rejected/completed/cancelled/paused
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel_username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_campaigns_status", "status"),
        Index("ix_campaigns_advertiser", "advertiser_id"),
    )


class CampaignCompletion(Base):
    __tablename__ = "campaign_completions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    reward_points: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="completed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_campaign_completions_user_campaign", "user_id", "campaign_id", unique=True),
    )
