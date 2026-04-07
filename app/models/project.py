from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.profile import Skill

# ---------------------------------------------------------------------------
# Join table: project ↔ skill (tech stack)
# ---------------------------------------------------------------------------

project_tech_stacks = Table(
    "project_tech_stacks",
    Base.metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    work_experience_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_experiences.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    work_experience: Mapped["WorkExperience"] = relationship(back_populates="projects")  # type: ignore[name-defined] # noqa: F821
    todos: Mapped[list["Todo"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        back_populates="project", cascade="all, delete-orphan", order_by="Todo.sort_order", lazy="selectin"
    )
    tech_stack: Mapped[list[Skill]] = relationship(secondary=project_tech_stacks, lazy="selectin")
