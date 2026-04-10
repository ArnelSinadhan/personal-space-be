from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

# ---------------------------------------------------------------------------
# Join tables
# ---------------------------------------------------------------------------

profile_skills = Table(
    "profile_skills",
    Base.metadata,
    Column("profile_id", UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

# ---------------------------------------------------------------------------
# Skill (shared between profile & projects)
# ---------------------------------------------------------------------------


class Skill(Base, UUIDMixin):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Skill {self.name}>"


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class Profile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(String(255))
    about: Mapped[str | None] = mapped_column(Text)
    resume_url: Mapped[str | None] = mapped_column(Text)
    public_slug: Mapped[str | None] = mapped_column(String(100), unique=True)
    is_public_profile_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile")  # type: ignore[name-defined] # noqa: F821
    work_experiences: Mapped[list[WorkExperience]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="WorkExperience.sort_order", lazy="selectin"
    )
    education_entries: Mapped[list[EducationEntry]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="EducationEntry.sort_order", lazy="selectin"
    )
    certifications: Mapped[list["CertificationEntry"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="CertificationEntry.sort_order",
        lazy="selectin",
    )
    social_links: Mapped[list[SocialLink]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="SocialLink.sort_order", lazy="selectin"
    )
    personal_projects: Mapped[list["PersonalProject"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="PersonalProject.sort_order",
        lazy="selectin",
    )
    skills: Mapped[list[Skill]] = relationship(secondary=profile_skills, lazy="selectin")


# ---------------------------------------------------------------------------
# Work Experience
# ---------------------------------------------------------------------------


class WorkExperience(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "work_experiences"
    __table_args__ = (
        Index("ix_work_experiences_profile_current", "profile_id", "is_current"),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[str] = mapped_column(String(100), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(100))
    is_current: Mapped[bool] = mapped_column(default=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped[Profile] = relationship(back_populates="work_experiences")
    projects: Mapped[list["Project"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        back_populates="work_experience",
        cascade="all, delete-orphan",
        order_by="Project.sort_order",
        lazy="selectin",
    )


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------


class EducationEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "education_entries"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    school: Mapped[str] = mapped_column(String(255), nullable=False)
    years: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped[Profile] = relationship(back_populates="education_entries")


# ---------------------------------------------------------------------------
# Certifications
# ---------------------------------------------------------------------------


class CertificationEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "certification_entries"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_at: Mapped[str] = mapped_column(String(100), nullable=False)
    expires_at: Mapped[str | None] = mapped_column(String(100))
    credential_id: Mapped[str | None] = mapped_column(String(255))
    credential_url: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped[Profile] = relationship(back_populates="certifications")


# ---------------------------------------------------------------------------
# Social Links
# ---------------------------------------------------------------------------


class SocialLink(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "social_links"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped[Profile] = relationship(back_populates="social_links")
