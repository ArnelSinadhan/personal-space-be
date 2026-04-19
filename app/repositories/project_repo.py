from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile, WorkExperience
from app.models.project import PersonalProject, Project, UpworkProject
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
                selectinload(Project.testimonial),
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
                selectinload(Project.testimonial),
            )
        )
        return result.scalar_one_or_none()


class PersonalProjectRepository(BaseRepository[PersonalProject]):
    def __init__(self, db: AsyncSession):
        super().__init__(PersonalProject, db)

    async def get_all_for_user(self, user_id: UUID) -> list[PersonalProject]:
        result = await self.db.execute(
            select(PersonalProject)
            .join(Profile, PersonalProject.profile_id == Profile.id)
            .where(Profile.user_id == user_id)
            .options(selectinload(PersonalProject.tech_stack))
            .order_by(PersonalProject.completed_at.desc().nulls_last())
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(
        self, project_id: UUID, user_id: UUID
    ) -> PersonalProject | None:
        result = await self.db.execute(
            select(PersonalProject)
            .join(Profile, PersonalProject.profile_id == Profile.id)
            .where(PersonalProject.id == project_id, Profile.user_id == user_id)
            .options(selectinload(PersonalProject.tech_stack))
        )
        return result.scalar_one_or_none()


class UpworkProjectRepository(BaseRepository[UpworkProject]):
    def __init__(self, db: AsyncSession):
        super().__init__(UpworkProject, db)

    async def get_all_for_user(self, user_id: UUID) -> list[UpworkProject]:
        result = await self.db.execute(
            select(UpworkProject)
            .join(Profile, UpworkProject.profile_id == Profile.id)
            .where(Profile.user_id == user_id)
            .options(selectinload(UpworkProject.tech_stack))
            .order_by(UpworkProject.completed_at.desc().nulls_last())
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(
        self, project_id: UUID, user_id: UUID
    ) -> UpworkProject | None:
        result = await self.db.execute(
            select(UpworkProject)
            .join(Profile, UpworkProject.profile_id == Profile.id)
            .where(UpworkProject.id == project_id, Profile.user_id == user_id)
            .options(selectinload(UpworkProject.tech_stack))
        )
        return result.scalar_one_or_none()
