from __future__ import annotations

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portfolio import PortfolioView
from app.models.profile import Profile, WorkExperience
from app.models.project import Project
from app.schemas.public import (
    PortfolioViewCreate,
    PublicEducationOut,
    PublicPortfolioOut,
    PublicPortfolioStatsOut,
    PublicProfileOut,
    PublicProjectOut,
    PublicSocialLinkOut,
    PublicWorkExperienceOut,
)
from app.services.storage_service import StorageService


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
                selectinload(Profile.work_experiences)
                .selectinload(WorkExperience.projects)
                .selectinload(Project.tech_stack),
            )
        )
        hydrated_profile = profile_result.scalar_one_or_none()
        if hydrated_profile is None:
            raise ValueError("Portfolio not found")

        view_count_result = await self.db.execute(
            select(func.count(PortfolioView.id)).where(
                PortfolioView.user_id == hydrated_profile.user_id
            )
        )
        total_views = int(view_count_result.scalar() or 0)

        public_projects: list[PublicProjectOut] = []
        work_experience_out: list[PublicWorkExperienceOut] = []

        for workspace in hydrated_profile.work_experiences:
            workspace_projects: list[PublicProjectOut] = []
            for project in workspace.projects:
                if not project.is_public:
                    continue
                project_out = await self._project_to_out(project, workspace.company)
                workspace_projects.append(project_out)
                public_projects.append(project_out)

            work_experience_out.append(
                PublicWorkExperienceOut(
                    title=workspace.title,
                    company=workspace.company,
                    start_date=workspace.start_date,
                    end_date=workspace.end_date,
                    is_current=workspace.is_current,
                    image_url=await self.storage.resolve_company_url(workspace.image_url),
                    projects=workspace_projects,
                )
            )

        return PublicPortfolioOut(
            profile=PublicProfileOut(
                name=hydrated_profile.name,
                role=hydrated_profile.role,
                avatar=await self.storage.resolve_profile_url(hydrated_profile.avatar_url),
                about=hydrated_profile.about,
                skills=[skill.name for skill in hydrated_profile.skills],
                social_links=[
                    PublicSocialLinkOut(label=link.label, url=link.url)
                    for link in hydrated_profile.social_links
                ],
            ),
            work_experience=work_experience_out,
            education=[
                PublicEducationOut(
                    degree=education.degree,
                    school=education.school,
                    years=education.years,
                )
                for education in hydrated_profile.education_entries
            ],
            projects=public_projects,
            stats=PublicPortfolioStatsOut(
                company_count=len(hydrated_profile.work_experiences),
                public_project_count=len(public_projects),
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

    async def _get_profile_by_slug(self, slug: str) -> Profile:
        normalized_slug = slug.strip().lower()
        result = await self.db.execute(
            select(Profile).where(Profile.public_slug == normalized_slug)
        )
        profile = result.scalar_one_or_none()
        if profile is None or not profile.is_public_profile_enabled:
            raise ValueError("Portfolio not found")
        return profile

    async def _project_to_out(
        self, project: Project, company_name: str
    ) -> PublicProjectOut:
        return PublicProjectOut(
            name=project.name,
            description=project.description,
            image_url=await self.storage.resolve_project_url(project.image_url),
            github_url=project.github_url,
            live_url=project.live_url,
            company=company_name,
            tech_stack=[skill.name for skill in project.tech_stack],
        )
