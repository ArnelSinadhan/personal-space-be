from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile, WorkExperience
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

    async def get_by_id_for_user(self, todo_id: UUID, user_id: UUID) -> Todo | None:
        from app.models.project import Project

        result = await self.db.execute(
            select(Todo)
            .join(Project, Todo.project_id == Project.id)
            .join(WorkExperience, Project.work_experience_id == WorkExperience.id)
            .join(Profile, WorkExperience.profile_id == Profile.id)
            .where(Todo.id == todo_id, Profile.user_id == user_id)
            .options(selectinload(Todo.project))
        )
        return result.scalar_one_or_none()
