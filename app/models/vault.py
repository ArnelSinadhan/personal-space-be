from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class VaultPin(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "vault_pins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped["User"] = relationship(back_populates="vault_pin")  # type: ignore[name-defined] # noqa: F821


class VaultCategory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "vault_categories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="vault_categories")  # type: ignore[name-defined] # noqa: F821
    entries: Mapped[list[VaultEntry]] = relationship(
        back_populates="category", cascade="all, delete-orphan", lazy="selectin"
    )


class VaultEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "vault_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vault_categories.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    icon_name: Mapped[str | None] = mapped_column(String(50))

    user: Mapped["User"] = relationship(back_populates="vault_entries")  # type: ignore[name-defined] # noqa: F821
    category: Mapped[VaultCategory | None] = relationship(back_populates="entries")
