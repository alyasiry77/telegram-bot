from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Text, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from bot.app.database.engine import Base


class Advertisement(Base):
    __tablename__ = "advertisements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    type: Mapped[str] = mapped_column(String(32), default="banner", nullable=False)  # banner/welcome/inter_tasks/pinned
    price: Mapped[float] = mapped_column(Integer, default=0, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_impressions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)  # active/inactive/expired
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_advertisements_status", "status"),
    )
