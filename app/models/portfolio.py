from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PortfolioVisitor(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "portfolio_visitors"
    __table_args__ = (
        UniqueConstraint("user_id", "visitor_id", name="uq_portfolio_visitors_user_visitor"),
        Index("ix_portfolio_visitors_user_last_visited_at", "user_id", "last_visited_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    visitor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    first_visited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_visited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    visit_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_path: Mapped[str] = mapped_column(String(255), default="/", nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    referrer: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(255))
    country_code: Mapped[str | None] = mapped_column(String(16))
    region: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str | None] = mapped_column(String(120))

    user: Mapped["User"] = relationship(back_populates="portfolio_visitors")  # type: ignore[name-defined] # noqa: F821
