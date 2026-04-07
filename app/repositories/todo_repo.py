from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo
from app.repositories.base import BaseRepository


class TodoRepository(BaseRepository[Todo]):
    def __init__(self, db: AsyncSession):
        super().__init__(Todo, db)

    async def get_by_project(self, project_id: UUID) -> list[Todo]:
        result = await self.db.execute(
            select(Todo).where(Todo.project_id == project_id).order_by(Todo.sort_order)
        )
        return list(result.scalars().all())

    async def get_completed_for_user_companies(self, company_ids: list[UUID]) -> list[Todo]:
        """Get all completed todos across multiple companies (for reports)."""
        from app.models.project import Project

        result = await self.db.execute(
            select(Todo, Project.name, Project.company_id)
            .join(Project, Todo.project_id == Project.id)
            .where(
                Project.company_id.in_(company_ids),
                Todo.status == "done",
                Todo.completed_at.isnot(None),
            )
            .order_by(Todo.completed_at.desc())
        )
        return list(result.all())
