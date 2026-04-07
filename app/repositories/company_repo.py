from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.project import Project
from app.models.todo import Todo
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: AsyncSession):
        super().__init__(Company, db)

    async def get_all_for_user(self, user_id: UUID) -> list[Company]:
        """Get all companies with nested projects and todos (eager loaded)."""
        result = await self.db.execute(
            select(Company)
            .where(Company.user_id == user_id)
            .options(
                selectinload(Company.projects)
                .selectinload(Project.todos),
                selectinload(Company.projects)
                .selectinload(Project.tech_stack),
            )
            .order_by(Company.sort_order)
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, company_id: UUID, user_id: UUID) -> Company | None:
        result = await self.db.execute(
            select(Company)
            .where(Company.id == company_id, Company.user_id == user_id)
            .options(
                selectinload(Company.projects)
                .selectinload(Project.todos),
                selectinload(Company.projects)
                .selectinload(Project.tech_stack),
            )
        )
        return result.scalar_one_or_none()
