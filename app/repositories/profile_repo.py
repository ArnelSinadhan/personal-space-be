from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import (
    CertificationEntry,
    EducationEntry,
    Profile,
    Skill,
    SocialLink,
    WorkExperience,
)
from app.models.project import PersonalProject, Project
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
                selectinload(Profile.certifications),
                selectinload(Profile.social_links),
                selectinload(Profile.skills),
                selectinload(Profile.personal_projects).selectinload(PersonalProject.tech_stack),
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: UUID) -> Profile:
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            await self.create(user_id=user_id)
            profile = await self.get_by_user_id(user_id)
        if profile is None:
            raise RuntimeError(f"Failed to load profile for user {user_id}")
        return profile


class WorkExperienceRepository(BaseRepository[WorkExperience]):
    def __init__(self, db: AsyncSession):
        super().__init__(WorkExperience, db)

    async def get_all_for_user(self, user_id: UUID, *, current_only: bool = False) -> list[WorkExperience]:
        stmt = (
            select(WorkExperience)
            .join(Profile, WorkExperience.profile_id == Profile.id)
            .where(Profile.user_id == user_id)
            .options(
                selectinload(WorkExperience.projects).selectinload(Project.todos),
                selectinload(WorkExperience.projects).selectinload(Project.tech_stack),
            )
            .order_by(WorkExperience.sort_order)
        )
        if current_only:
            stmt = stmt.where(WorkExperience.is_current.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_for_user(self, entry_id: UUID, user_id: UUID) -> WorkExperience | None:
        result = await self.db.execute(
            select(WorkExperience)
            .join(Profile, WorkExperience.profile_id == Profile.id)
            .where(WorkExperience.id == entry_id, Profile.user_id == user_id)
            .options(
                selectinload(WorkExperience.projects).selectinload(Project.todos),
                selectinload(WorkExperience.projects).selectinload(Project.tech_stack),
            )
        )
        return result.scalar_one_or_none()


class EducationRepository(BaseRepository[EducationEntry]):
    def __init__(self, db: AsyncSession):
        super().__init__(EducationEntry, db)

    async def get_by_id_for_user(
        self, entry_id: UUID, user_id: UUID
    ) -> EducationEntry | None:
        result = await self.db.execute(
            select(EducationEntry)
            .join(Profile, EducationEntry.profile_id == Profile.id)
            .where(EducationEntry.id == entry_id, Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()


class CertificationRepository(BaseRepository[CertificationEntry]):
    def __init__(self, db: AsyncSession):
        super().__init__(CertificationEntry, db)

    async def get_by_id_for_user(
        self, entry_id: UUID, user_id: UUID
    ) -> CertificationEntry | None:
        result = await self.db.execute(
            select(CertificationEntry)
            .join(Profile, CertificationEntry.profile_id == Profile.id)
            .where(CertificationEntry.id == entry_id, Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()


class SocialLinkRepository(BaseRepository[SocialLink]):
    def __init__(self, db: AsyncSession):
        super().__init__(SocialLink, db)


class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, name: str) -> Skill:
        normalized = name.strip()
        result = await self.db.execute(select(Skill).where(Skill.name == normalized))
        skill = result.scalar_one_or_none()
        if skill is None:
            skill = Skill(name=normalized)
            self.db.add(skill)
            await self.db.flush()
        return skill

    async def get_or_create_many(self, names: list[str]) -> list[Skill]:
        ordered_names: list[str] = []
        seen: set[str] = set()
        for name in names:
            normalized = name.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered_names.append(normalized)

        if not ordered_names:
            return []

        result = await self.db.execute(
            select(Skill).where(Skill.name.in_(ordered_names))
        )
        existing_skills = {skill.name: skill for skill in result.scalars().all()}

        missing_names = [
            name for name in ordered_names if name not in existing_skills
        ]
        new_skills = [Skill(name=name) for name in missing_names]
        if new_skills:
            self.db.add_all(new_skills)
            await self.db.flush()
            existing_skills.update({skill.name: skill for skill in new_skills})

        return [existing_skills[name] for name in ordered_names]
