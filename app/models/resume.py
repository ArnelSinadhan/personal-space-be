from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import ResumeTemplate
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.profile import Skill

# ---------------------------------------------------------------------------
# Join tables
# ---------------------------------------------------------------------------

resume_skills = Table(
    "resume_skills",
    Base.metadata,
    Column("resume_id", UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

resume_project_tech_stacks = Table(
    "resume_project_tech_stacks",
    Base.metadata,
    Column("resume_project_id", UUID(as_uuid=True), ForeignKey("resume_projects.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------


class Resume(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    template: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ResumeTemplate.CLASSIC.value
    )
    name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="resume")  # type: ignore[name-defined] # noqa: F821
    experiences: Mapped[list[ResumeExperience]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeExperience.sort_order", lazy="selectin"
    )
    educations: Mapped[list[ResumeEducation]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeEducation.sort_order", lazy="selectin"
    )
    projects: Mapped[list[ResumeProject]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeProject.sort_order", lazy="selectin"
    )
    links: Mapped[list[ResumeLink]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeLink.sort_order", lazy="selectin"
    )
    skills: Mapped[list[Skill]] = relationship(secondary=resume_skills, lazy="selectin")


class ResumeExperience(Base, UUIDMixin):
    __tablename__ = "resume_experiences"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[str] = mapped_column(String(100), nullable=False)
    end_date: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    resume: Mapped[Resume] = relationship(back_populates="experiences")


class ResumeEducation(Base, UUIDMixin):
    __tablename__ = "resume_educations"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    school: Mapped[str] = mapped_column(String(255), nullable=False)
    years: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    resume: Mapped[Resume] = relationship(back_populates="educations")


class ResumeProject(Base, UUIDMixin):
    __tablename__ = "resume_projects"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    resume: Mapped[Resume] = relationship(back_populates="projects")
    tech_stack: Mapped[list[Skill]] = relationship(secondary=resume_project_tech_stacks, lazy="selectin")


class ResumeLink(Base, UUIDMixin):
    __tablename__ = "resume_links"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    resume: Mapped[Resume] = relationship(back_populates="links")
