from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)  # type: ignore[name-defined] # noqa: F821
    resume: Mapped["Resume"] = relationship(back_populates="user", uselist=False)  # type: ignore[name-defined] # noqa: F821
    vault_pin: Mapped["VaultPin"] = relationship(back_populates="user", uselist=False)  # type: ignore[name-defined] # noqa: F821
    vault_categories: Mapped[list["VaultCategory"]] = relationship(back_populates="user")  # type: ignore[name-defined] # noqa: F821
    vault_entries: Mapped[list["VaultEntry"]] = relationship(back_populates="user")  # type: ignore[name-defined] # noqa: F821
