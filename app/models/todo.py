from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import TodoStatus
from app.models.base import Base, TimestampMixin, UUIDMixin


class Todo(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "todos"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TodoStatus.TODO.value
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="todos")  # type: ignore[name-defined] # noqa: F821

    # Composite index for report queries
    __table_args__ = (
        Index("ix_todos_status_completed", "status", "completed_at"),
    )
