from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import EducationEntry, Profile, Skill, SocialLink, WorkExperience
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, db: AsyncSession):
        super().__init__(Profile, db)

    async def get_by_user_id(self, user_id: UUID) -> Profile | None:
        result = await self.db.execute(
            select(Profile)
            .where(Profile.user_id == user_id)
            .options(
                selectinload(Profile.work_experiences),
                selectinload(Profile.education_entries),
                selectinload(Profile.social_links),
                selectinload(Profile.skills),
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: UUID) -> Profile:
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            profile = await self.create(user_id=user_id)
        return profile


class WorkExperienceRepository(BaseRepository[WorkExperience]):
    def __init__(self, db: AsyncSession):
        super().__init__(WorkExperience, db)


class EducationRepository(BaseRepository[EducationEntry]):
    def __init__(self, db: AsyncSession):
        super().__init__(EducationEntry, db)


class SocialLinkRepository(BaseRepository[SocialLink]):
    def __init__(self, db: AsyncSession):
        super().__init__(SocialLink, db)


class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, name: str) -> Skill:
        result = await self.db.execute(select(Skill).where(Skill.name == name))
        skill = result.scalar_one_or_none()
        if skill is None:
            skill = Skill(name=name)
            self.db.add(skill)
            await self.db.flush()
        return skill

    async def get_or_create_many(self, names: list[str]) -> list[Skill]:
        return [await self.get_or_create(name) for name in names]
