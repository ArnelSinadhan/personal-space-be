from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vault import VaultCategory, VaultEntry, VaultPin
from app.repositories.base import BaseRepository


class VaultPinRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: UUID) -> VaultPin | None:
        result = await self.db.execute(
            select(VaultPin).where(VaultPin.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: UUID, pin_hash: str) -> VaultPin:
        pin = await self.get_by_user_id(user_id)
        if pin is None:
            pin = VaultPin(user_id=user_id, pin_hash=pin_hash)
            self.db.add(pin)
        else:
            pin.pin_hash = pin_hash
        await self.db.flush()
        return pin


class VaultCategoryRepository(BaseRepository[VaultCategory]):
    def __init__(self, db: AsyncSession):
        super().__init__(VaultCategory, db)

    async def get_all_for_user(self, user_id: UUID) -> list[VaultCategory]:
        result = await self.db.execute(
            select(VaultCategory)
            .where(VaultCategory.user_id == user_id)
            .order_by(VaultCategory.sort_order)
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, cat_id: UUID, user_id: UUID) -> VaultCategory | None:
        result = await self.db.execute(
            select(VaultCategory).where(
                VaultCategory.id == cat_id, VaultCategory.user_id == user_id
            )
        )
        return result.scalar_one_or_none()


class VaultEntryRepository(BaseRepository[VaultEntry]):
    def __init__(self, db: AsyncSession):
        super().__init__(VaultEntry, db)

    async def get_all_for_user(self, user_id: UUID) -> list[VaultEntry]:
        result = await self.db.execute(
            select(VaultEntry)
            .where(VaultEntry.user_id == user_id)
            .order_by(VaultEntry.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, entry_id: UUID, user_id: UUID) -> VaultEntry | None:
        result = await self.db.execute(
            select(VaultEntry).where(
                VaultEntry.id == entry_id, VaultEntry.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
