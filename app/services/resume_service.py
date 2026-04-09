from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ResumeTemplate
from app.models.resume import Resume, ResumeEducation, ResumeExperience, ResumeLink, ResumeProject
from app.repositories.profile_repo import SkillRepository
from app.repositories.resume_repo import ResumeRepository
from app.schemas.resume import (
    ResumeOut,
    ResumePersonalInput,
    ResumeUpdate,
    ResumeExperienceOut,
    ResumeEducationOut,
    ResumeProjectOut,
    ResumeLinkOut,
)


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.skill_repo = SkillRepository(db)

    async def get_resume(self, user_id: UUID) -> ResumeOut | None:
        resume = await self.resume_repo.get_by_user_id(user_id)
        if resume is None:
            return None
        return self._to_out(resume)

    async def save_resume(self, user_id: UUID, data: ResumeUpdate) -> ResumeOut:
        resume = await self.resume_repo.get_by_user_id(user_id)

        if resume is None:
            new_resume = Resume(user_id=user_id)
            self.db.add(new_resume)
            await self.db.flush()
            resume = await self.resume_repo.get_by_user_id(user_id)
            if resume is None:
                raise RuntimeError(f"Failed to load resume for user {user_id}")
        else:
            await self.resume_repo.delete_children(resume)

        # Set personal fields
        resume.template = data.template.value
        resume.name = data.personal.name
        resume.role = data.personal.role
        resume.email = data.personal.email
        resume.phone = data.personal.phone
        resume.address = data.personal.address
        resume.summary = data.personal.summary

        # Skills
        resume.skills = await self.skill_repo.get_or_create_many(data.skills)

        # Experiences
        for i, exp in enumerate(data.experience):
            resume.experiences.append(ResumeExperience(
                resume_id=resume.id, sort_order=i, **exp.model_dump(),
            ))

        # Education
        for i, edu in enumerate(data.education):
            resume.educations.append(ResumeEducation(
                resume_id=resume.id, sort_order=i, **edu.model_dump(),
            ))

        # Projects
        for i, proj in enumerate(data.projects):
            rp = ResumeProject(
                resume_id=resume.id,
                name=proj.name,
                description=proj.description,
                sort_order=i,
            )
            rp.tech_stack = await self.skill_repo.get_or_create_many(proj.tech_stack)
            resume.projects.append(rp)

        # Links
        for i, link in enumerate(data.links):
            resume.links.append(ResumeLink(
                resume_id=resume.id, sort_order=i, **link.model_dump(),
            ))

        await self.db.flush()
        refreshed = await self.resume_repo.get_by_user_id(user_id)
        return self._to_out(refreshed or resume)

    # -- Serialization -------------------------------------------------------

    def _to_out(self, resume: Resume) -> ResumeOut:
        return ResumeOut(
            id=resume.id,
            template=ResumeTemplate(resume.template),
            personal=ResumePersonalInput(
                name=resume.name,
                role=resume.role,
                email=resume.email,
                phone=resume.phone,
                address=resume.address,
                summary=resume.summary,
            ),
            experience=[ResumeExperienceOut.model_validate(e) for e in resume.experiences],
            education=[ResumeEducationOut.model_validate(e) for e in resume.educations],
            skills=[s.name for s in resume.skills],
            projects=[
                ResumeProjectOut(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    tech_stack=[s.name for s in p.tech_stack],
                )
                for p in resume.projects
            ],
            links=[ResumeLinkOut.model_validate(l) for l in resume.links],
            updated_at=resume.updated_at.isoformat() if resume.updated_at else None,
        )
