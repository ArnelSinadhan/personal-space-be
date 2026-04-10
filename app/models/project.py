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

personal_project_tech_stacks = Table(
    "personal_project_tech_stacks",
    Base.metadata,
    Column(
        "personal_project_id",
        UUID(as_uuid=True),
        ForeignKey("personal_projects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "skill_id",
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    work_experience_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_experiences.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    live_url: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    work_experience: Mapped["WorkExperience"] = relationship(back_populates="projects")  # type: ignore[name-defined] # noqa: F821
    todos: Mapped[list["Todo"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        back_populates="project", cascade="all, delete-orphan", order_by="Todo.sort_order", lazy="selectin"
    )
    tech_stack: Mapped[list[Skill]] = relationship(secondary=project_tech_stacks, lazy="selectin")
    testimonial: Mapped["ProjectTestimonial | None"] = relationship(  # type: ignore[name-defined] # noqa: F821
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )


class ProjectTestimonial(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "project_testimonials"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str | None] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    project: Mapped["Project"] = relationship(back_populates="testimonial")


class ProjectTestimonialSubmissionLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "project_testimonial_submission_logs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(255), index=True)


class PersonalProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "personal_projects"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    live_url: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["Profile"] = relationship(back_populates="personal_projects")  # type: ignore[name-defined] # noqa: F821
    tech_stack: Mapped[list[Skill]] = relationship(
        secondary=personal_project_tech_stacks,
        lazy="selectin",
    )
