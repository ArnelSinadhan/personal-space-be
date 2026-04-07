from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile, WorkExperience
from app.models.project import Project
from app.models.todo import Todo
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_by_id_with_relations(self, project_id: UUID) -> Project | None:
        result = await self.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.todos),
                selectinload(Project.tech_stack),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, project_id: UUID, user_id: UUID) -> Project | None:
        result = await self.db.execute(
            select(Project)
            .join(WorkExperience, Project.work_experience_id == WorkExperience.id)
            .join(Profile, WorkExperience.profile_id == Profile.id)
            .where(Project.id == project_id, Profile.user_id == user_id)
            .options(
                selectinload(Project.todos),
                selectinload(Project.tech_stack),
            )
        )
        return result.scalar_one_or_none()
