from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.vault import VaultCategory, VaultEntry
from app.repositories.vault_repo import VaultCategoryRepository, VaultEntryRepository, VaultPinRepository
from app.schemas.vault import (
    VaultCategoryCreate,
    VaultCategoryOut,
    VaultEntryCreate,
    VaultEntryOut,
    VaultEntryUpdate,
)
from app.utils.encryption import decrypt_password, encrypt_password


class VaultService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pin_repo = VaultPinRepository(db)
        self.cat_repo = VaultCategoryRepository(db)
        self.entry_repo = VaultEntryRepository(db)

    # -- PIN -----------------------------------------------------------------

    async def set_pin(self, user_id: UUID, pin: str) -> None:
        pin_hash = bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
        await self.pin_repo.upsert(user_id, pin_hash)

    async def verify_pin(self, user_id: UUID, pin: str) -> str | None:
        """Returns a vault session JWT if PIN is correct, None otherwise."""
        vault_pin = await self.pin_repo.get_by_user_id(user_id)
        if vault_pin is None:
            return None
        if not bcrypt.checkpw(pin.encode("utf-8"), vault_pin.pin_hash.encode("utf-8")):
            return None
        # Issue short-lived vault token
        payload = {
            "sub": str(user_id),
            "type": "vault_session",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.vault_session_expire_minutes),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    async def has_pin(self, user_id: UUID) -> bool:
        vault_pin = await self.pin_repo.get_by_user_id(user_id)
        return vault_pin is not None

    # -- Categories ----------------------------------------------------------

    async def get_categories(self, user_id: UUID) -> list[VaultCategoryOut]:
        cats = await self.cat_repo.get_all_for_user(user_id)
        return [VaultCategoryOut.model_validate(c) for c in cats]

    async def create_category(self, user_id: UUID, data: VaultCategoryCreate) -> VaultCategoryOut:
        cat = VaultCategory(user_id=user_id, **data.model_dump())
        self.db.add(cat)
        await self.db.flush()
        return VaultCategoryOut.model_validate(cat)

    async def update_category(
        self, cat_id: UUID, user_id: UUID, data: VaultCategoryCreate
    ) -> VaultCategoryOut:
        cat = await self.cat_repo.get_by_id_for_user(cat_id, user_id)
        if cat is None:
            raise ValueError("Category not found")
        cat.name = data.name
        cat.icon_name = data.icon_name
        await self.db.flush()
        return VaultCategoryOut.model_validate(cat)

    async def delete_category(self, cat_id: UUID, user_id: UUID) -> None:
        cat = await self.cat_repo.get_by_id_for_user(cat_id, user_id)
        if cat is None:
            raise ValueError("Category not found")
        await self.cat_repo.delete(cat)

    # -- Entries -------------------------------------------------------------

    async def get_entries(self, user_id: UUID) -> list[VaultEntryOut]:
        entries = await self.entry_repo.get_all_for_user(user_id)
        return [self._entry_to_out(e) for e in entries]

    async def create_entry(self, user_id: UUID, data: VaultEntryCreate) -> VaultEntryOut:
        entry = VaultEntry(
            user_id=user_id,
            title=data.title,
            username=data.username,
            encrypted_password=encrypt_password(data.password),
            category_id=data.category_id,
            icon_name=data.icon_name,
        )
        self.db.add(entry)
        await self.db.flush()
        return self._entry_to_out(entry)

    async def update_entry(
        self, entry_id: UUID, user_id: UUID, data: VaultEntryUpdate
    ) -> VaultEntryOut:
        entry = await self.entry_repo.get_by_id_for_user(entry_id, user_id)
        if entry is None:
            raise ValueError("Entry not found")
        if data.title is not None:
            entry.title = data.title
        if data.username is not None:
            entry.username = data.username
        if data.password is not None:
            entry.encrypted_password = encrypt_password(data.password)
        if data.category_id is not None:
            entry.category_id = data.category_id
        if data.icon_name is not None:
            entry.icon_name = data.icon_name
        await self.db.flush()
        return self._entry_to_out(entry)

    async def delete_entry(self, entry_id: UUID, user_id: UUID) -> None:
        entry = await self.entry_repo.get_by_id_for_user(entry_id, user_id)
        if entry is None:
            raise ValueError("Entry not found")
        await self.entry_repo.delete(entry)

    async def reveal_password(self, entry_id: UUID, user_id: UUID) -> str:
        entry = await self.entry_repo.get_by_id_for_user(entry_id, user_id)
        if entry is None:
            raise ValueError("Entry not found")
        return decrypt_password(entry.encrypted_password)

    # -- Serialization -------------------------------------------------------

    def _entry_to_out(self, entry: VaultEntry) -> VaultEntryOut:
        return VaultEntryOut(
            id=entry.id,
            title=entry.title,
            username=entry.username,
            password=None,
            has_password=bool(entry.encrypted_password),
            category_id=entry.category_id,
            icon_name=entry.icon_name,
            created_at=entry.created_at.isoformat() if entry.created_at else None,
        )
