from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ResumeTemplate
from app.models.resume import Resume, ResumeEducation, ResumeExperience, ResumeLink, ResumeProject
from app.repositories.profile_repo import ProfileRepository, SkillRepository
from app.repositories.resume_repo import ResumeRepository
from app.schemas.resume import (
    ResumeCreate,
    ResumeOut,
    ResumePersonalInput,
    ResumeUpdate,
    TemplateUpdate,
    ResumeExperienceOut,
    ResumeEducationOut,
    ResumeProjectOut,
    ResumeLinkOut,
)


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.skill_repo = SkillRepository(db)

    async def get_resume(self, user_id: UUID) -> ResumeOut | None:
        resume = await self.resume_repo.get_by_user_id(user_id)
        if resume is None:
            return None
        return self._to_out(resume)

    async def save_resume(self, user_id: UUID, data: ResumeUpdate) -> ResumeOut:
        resume = await self.resume_repo.get_by_user_id(user_id)

        if resume is None:
            resume = Resume(user_id=user_id)
            self.db.add(resume)
            await self.db.flush()
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

    async def delete_resume(self, user_id: UUID) -> None:
        resume = await self.resume_repo.get_by_user_id(user_id)
        if resume is None:
            raise ValueError("Resume not found")
        await self.resume_repo.delete(resume)

    async def change_template(self, user_id: UUID, data: TemplateUpdate) -> ResumeOut:
        resume = await self.resume_repo.get_by_user_id(user_id)
        if resume is None:
            raise ValueError("Resume not found")
        resume.template = data.template.value
        await self.db.flush()
        return self._to_out(resume)

    async def generate_from_profile(self, user_id: UUID) -> ResumeOut:
        """Auto-generate resume from profile data (mirrors frontend generateResumeFromProfile)."""
        profile = await self.profile_repo.get_or_create(user_id)

        data = ResumeUpdate(
            template=ResumeTemplate.CLASSIC,
            personal=ResumePersonalInput(
                name=profile.name,
                role=profile.role,
                email=profile.email,
                phone=profile.phone,
                address=profile.address,
                summary=profile.about,
            ),
            experience=[
                {
                    "title": w.title,
                    "company": w.company,
                    "start_date": w.start_date,
                    "end_date": "Present" if w.is_current else (w.end_date or ""),
                    "is_current": w.is_current,
                    "description": "",
                }
                for w in profile.work_experiences
            ],
            education=[
                {"degree": e.degree, "school": e.school, "years": e.years}
                for e in profile.education_entries
            ],
            skills=[s.name for s in profile.skills],
            projects=[],
            links=[
                {"label": l.label, "url": l.url}
                for l in profile.social_links
            ],
        )
        return await self.save_resume(user_id, data)

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
