from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resume import Resume, ResumeEducation, ResumeExperience, ResumeLink, ResumeProject
from app.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    def __init__(self, db: AsyncSession):
        super().__init__(Resume, db)

    async def get_by_user_id(self, user_id: UUID) -> Resume | None:
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .options(
                selectinload(Resume.experiences),
                selectinload(Resume.educations),
                selectinload(Resume.projects).selectinload(ResumeProject.tech_stack),
                selectinload(Resume.links),
                selectinload(Resume.skills),
            )
        )
        return result.scalar_one_or_none()

    async def delete_children(self, resume: Resume) -> None:
        """Remove all child rows before replacing them."""
        resume.experiences.clear()
        resume.educations.clear()
        resume.projects.clear()
        resume.links.clear()
        resume.skills.clear()
        await self.db.flush()
