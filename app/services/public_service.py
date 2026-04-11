from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.enums import ProjectTestimonialStatus
from app.models.portfolio import PortfolioView
from app.models.profile import Profile, WorkExperience
from app.models.project import (
    PersonalProject,
    Project,
    ProjectTestimonial,
    ProjectTestimonialSubmissionLog,
)
from app.schemas.public import (
    PortfolioViewCreate,
    PublicCertificationOut,
    PublicEducationOut,
    PublicPersonalProjectOut,
    PublicPortfolioOut,
    PublicPortfolioStatsOut,
    PublicProfileOut,
    PublicProjectOut,
    PublicProjectTestimonialCreate,
    PublicProjectTestimonialOut,
    PublicSocialLinkOut,
    PublicWorkExperienceOut,
)
from app.services.storage_service import StorageService


class PublicPortfolioNotFoundError(ValueError):
    pass


class PublicSubmissionValidationError(ValueError):
    pass


class PublicSubmissionRateLimitError(ValueError):
    pass


class PublicSubmissionConflictError(ValueError):
    pass


class PublicPortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = StorageService()

    async def get_portfolio(self, slug: str) -> PublicPortfolioOut:
        profile = await self._get_profile_by_slug(slug)
        profile_result = await self.db.execute(
            select(Profile)
            .where(Profile.id == profile.id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Profile.skills),
                selectinload(Profile.social_links),
                selectinload(Profile.education_entries),
                selectinload(Profile.certifications),
                selectinload(Profile.work_experiences)
                .selectinload(WorkExperience.projects)
                .selectinload(Project.tech_stack),
                selectinload(Profile.work_experiences)
                .selectinload(WorkExperience.projects)
                .selectinload(Project.testimonial),
                selectinload(Profile.personal_projects).selectinload(PersonalProject.tech_stack),
            )
        )
        hydrated_profile = profile_result.scalar_one_or_none()
        if hydrated_profile is None:
            raise PublicPortfolioNotFoundError("Portfolio not found")

        view_count_result = await self.db.execute(
            select(func.count(PortfolioView.id)).where(
                PortfolioView.user_id == hydrated_profile.user_id
            )
        )
        total_views = int(view_count_result.scalar() or 0)

        public_project_count = 0
        work_experience_out: list[PublicWorkExperienceOut] = []
        personal_projects_out: list[PublicPersonalProjectOut] = []

        for workspace in hydrated_profile.work_experiences:
            workspace_projects: list[PublicProjectOut] = []
            for project in workspace.projects:
                if not project.is_public:
                    continue
                project_out = await self._project_to_out(project, workspace.company)
                workspace_projects.append(project_out)
                public_project_count += 1

            work_experience_out.append(
                PublicWorkExperienceOut(
                    title=workspace.title,
                    company=workspace.company,
                    description=workspace.description,
                    start_date=workspace.start_date,
                    end_date=workspace.end_date,
                    is_current=workspace.is_current,
                    image_url=await self.storage.resolve_company_url(workspace.image_url),
                    projects=workspace_projects,
                )
            )

        for personal_project in hydrated_profile.personal_projects:
            if not personal_project.is_public:
                continue
            personal_projects_out.append(
                await self._personal_project_to_out(personal_project)
            )
            public_project_count += 1

        return PublicPortfolioOut(
            profile=PublicProfileOut(
                name=hydrated_profile.name,
                role=hydrated_profile.role,
                email=hydrated_profile.email,
                phone=hydrated_profile.phone,
                address=hydrated_profile.address,
                avatar=await self.storage.resolve_profile_url(hydrated_profile.avatar_url),
                about=hydrated_profile.about,
                skills=[skill.name for skill in hydrated_profile.skills],
                social_links=[
                    PublicSocialLinkOut(label=link.label, url=link.url)
                    for link in hydrated_profile.social_links
                ],
            ),
            work_experience=work_experience_out,
            personal_projects=personal_projects_out,
            education=[
                PublicEducationOut(
                    degree=education.degree,
                    school=education.school,
                    years=education.years,
                )
                for education in hydrated_profile.education_entries
            ],
            certifications=[
                PublicCertificationOut(
                    name=certification.name,
                    issuer=certification.issuer,
                    issued_at=certification.issued_at,
                    expires_at=certification.expires_at,
                    credential_id=certification.credential_id,
                    credential_url=certification.credential_url,
                    image_url=await self.storage.resolve_certification_url(
                        certification.image_url
                    ),
                )
                for certification in hydrated_profile.certifications
                if certification.is_public
            ],
            stats=PublicPortfolioStatsOut(
                company_count=len(hydrated_profile.work_experiences),
                public_project_count=public_project_count,
                skill_count=len(hydrated_profile.skills),
                total_views=total_views,
            ),
        )

    async def record_view(
        self,
        *,
        slug: str,
        payload: PortfolioViewCreate,
        request: Request,
    ) -> None:
        profile = await self._get_profile_by_slug(slug)

        forwarded_for = request.headers.get("x-forwarded-for")
        ip_address = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else request.client.host if request.client else None
        )

        self.db.add(
            PortfolioView(
                user_id=profile.user_id,
                path=(payload.path or "/")[:255],
                source=(payload.source or None),
                referrer=request.headers.get("referer"),
                user_agent=request.headers.get("user-agent"),
                ip_address=ip_address,
            )
        )
        await self.db.flush()

    async def submit_project_testimonial(
        self,
        *,
        slug: str,
        project_id,
        payload: PublicProjectTestimonialCreate,
        request: Request,
    ) -> None:
        project = await self._get_public_project(slug, project_id)
        ip_address = self._get_client_ip(request)

        await self._verify_captcha_token(payload.captcha_token, ip_address)
        await self._enforce_testimonial_rate_limit(project.id, ip_address)

        self.db.add(
            ProjectTestimonialSubmissionLog(
                project_id=project.id,
                ip_address=ip_address,
            )
        )
        await self.db.flush()

        if project.testimonial is not None:
            raise PublicSubmissionConflictError(
                "A testimonial has already been submitted for this project."
            )

        self.db.add(
            ProjectTestimonial(
                project_id=project.id,
                name=payload.name,
                role=payload.role,
                message=payload.message,
                status=ProjectTestimonialStatus.PENDING.value,
            )
        )
        await self.db.flush()

    async def _get_profile_by_slug(self, slug: str) -> Profile:
        normalized_slug = slug.strip().lower()
        result = await self.db.execute(
            select(Profile).where(Profile.public_slug == normalized_slug)
        )
        profile = result.scalar_one_or_none()
        if profile is None or not profile.is_public_profile_enabled:
            raise PublicPortfolioNotFoundError("Portfolio not found")
        return profile

    async def _get_public_project(self, slug: str, project_id) -> Project:
        profile = await self._get_profile_by_slug(slug)
        result = await self.db.execute(
            select(Project)
            .join(WorkExperience, Project.work_experience_id == WorkExperience.id)
            .where(
                Project.id == project_id,
                WorkExperience.profile_id == profile.id,
                Project.is_public.is_(True),
            )
            .options(
                selectinload(Project.tech_stack),
                selectinload(Project.testimonial),
            )
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise PublicPortfolioNotFoundError("Portfolio not found")
        return project

    async def _project_to_out(
        self, project: Project, company_name: str
    ) -> PublicProjectOut:
        return PublicProjectOut(
            id=str(project.id),
            name=project.name,
            description=project.description,
            image_url=await self.storage.resolve_project_url(project.image_url),
            github_url=project.github_url,
            live_url=project.live_url,
            company=company_name,
            tech_stack=[skill.name for skill in project.tech_stack],
            testimonial=(
                PublicProjectTestimonialOut(
                    name=project.testimonial.name,
                    role=project.testimonial.role,
                    message=project.testimonial.message,
                )
                if project.testimonial is not None
                and project.testimonial.status == ProjectTestimonialStatus.APPROVED.value
                else None
            ),
        )

    async def _personal_project_to_out(
        self, personal_project: PersonalProject
    ) -> PublicPersonalProjectOut:
        return PublicPersonalProjectOut(
            name=personal_project.name,
            description=personal_project.description,
            image_url=await self.storage.resolve_project_url(personal_project.image_url),
            github_url=personal_project.github_url,
            live_url=personal_project.live_url,
            tech_stack=[skill.name for skill in personal_project.tech_stack],
            is_featured=personal_project.is_featured,
        )

    def _get_client_ip(self, request: Request) -> str | None:
        forwarded_for = request.headers.get("x-forwarded-for")
        return (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else request.client.host if request.client else None
        )

    async def _enforce_testimonial_rate_limit(
        self, project_id, ip_address: str | None
    ) -> None:
        if settings.public_testimonial_rate_limit_max_attempts <= 0:
            return
        window_start = datetime.now(timezone.utc) - timedelta(
            minutes=settings.public_testimonial_rate_limit_window_minutes
        )
        query = select(func.count(ProjectTestimonialSubmissionLog.id)).where(
            ProjectTestimonialSubmissionLog.project_id == project_id,
            ProjectTestimonialSubmissionLog.created_at >= window_start,
        )
        if ip_address:
            query = query.where(ProjectTestimonialSubmissionLog.ip_address == ip_address)
        attempts = int((await self.db.execute(query)).scalar() or 0)
        if attempts >= settings.public_testimonial_rate_limit_max_attempts:
            raise PublicSubmissionRateLimitError(
                "Too many testimonial submissions. Please try again later."
            )

    async def _verify_captcha_token(
        self, captcha_token: str | None, ip_address: str | None
    ) -> None:
        if not settings.public_testimonial_captcha_secret:
            return
        if not captcha_token:
            raise PublicSubmissionValidationError("Captcha verification is required.")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.public_testimonial_captcha_verify_url,
                data={
                    "secret": settings.public_testimonial_captcha_secret,
                    "response": captcha_token,
                    "remoteip": ip_address or "",
                },
            )
        payload = response.json()
        if not response.is_success or not payload.get("success"):
            raise PublicSubmissionValidationError("Captcha verification failed.")
