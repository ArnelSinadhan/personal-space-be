from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PortfolioView(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "portfolio_views"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    path: Mapped[str] = mapped_column(String(255), default="/", nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    referrer: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="portfolio_views")  # type: ignore[name-defined] # noqa: F821
