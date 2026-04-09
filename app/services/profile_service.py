from uuid import UUID
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import EducationEntry, Profile, SocialLink, WorkExperience
from app.models.user import User
from app.repositories.profile_repo import (
    EducationRepository,
    ProfileRepository,
    SkillRepository,
    SocialLinkRepository,
    WorkExperienceRepository,
)
from app.schemas.profile import (
    AboutUpdate,
    EducationCreate,
    EducationOut,
    PersonalOut,
    PersonalUpdate,
    PublicProfileSettingsUpdate,
    ProfileOut,
    SocialLinkOut,
    SocialLinksUpdate,
    WorkExperienceCreate,
    WorkExperienceOut,
)
from app.services.storage_service import StorageService


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.work_repo = WorkExperienceRepository(db)
        self.edu_repo = EducationRepository(db)
        self.link_repo = SocialLinkRepository(db)
        self.skill_repo = SkillRepository(db)
        self.storage = StorageService()

    async def get_profile(self, user_id: UUID) -> ProfileOut:
        profile = await self.profile_repo.get_or_create(user_id)
        await self._ensure_public_slug(profile)
        return await self._to_profile_out(profile)

    async def update_personal(self, user_id: UUID, data: PersonalUpdate) -> ProfileOut:
        profile = await self.profile_repo.get_or_create(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self._ensure_public_slug(profile)
        await self.db.flush()
        return await self._to_profile_out(profile)

    async def update_about(self, user_id: UUID, data: AboutUpdate) -> ProfileOut:
        profile = await self.profile_repo.get_or_create(user_id)
        profile.about = data.about
        profile.skills = await self.skill_repo.get_or_create_many(data.skills)
        await self.db.flush()
        return await self._to_profile_out(profile)

    # -- Work Experience -----------------------------------------------------

    async def add_work_experience(
        self, user_id: UUID, data: WorkExperienceCreate
    ) -> WorkExperienceOut:
        profile = await self.profile_repo.get_or_create(user_id)
        entry = WorkExperience(
            profile_id=profile.id,
            sort_order=len(profile.work_experiences),
            **data.model_dump(),
        )
        self.db.add(entry)
        await self.db.flush()
        return await self._to_work_experience_out(entry)

    async def update_work_experience(
        self, entry_id: UUID, data: WorkExperienceCreate
    ) -> WorkExperienceOut:
        entry = await self.work_repo.get_by_id(entry_id)
        if entry is None:
            raise ValueError("Work experience not found")
        for field, value in data.model_dump().items():
            setattr(entry, field, value)
        await self.db.flush()
        return await self._to_work_experience_out(entry)

    async def delete_work_experience(self, entry_id: UUID) -> None:
        entry = await self.work_repo.get_by_id(entry_id)
        if entry is None:
            raise ValueError("Work experience not found")
        await self.work_repo.delete(entry)

    # -- Education -----------------------------------------------------------

    async def add_education(self, user_id: UUID, data: EducationCreate) -> EducationOut:
        profile = await self.profile_repo.get_or_create(user_id)
        entry = EducationEntry(
            profile_id=profile.id,
            sort_order=len(profile.education_entries),
            **data.model_dump(),
        )
        self.db.add(entry)
        await self.db.flush()
        return EducationOut.model_validate(entry)

    async def update_education(self, entry_id: UUID, data: EducationCreate) -> EducationOut:
        entry = await self.edu_repo.get_by_id(entry_id)
        if entry is None:
            raise ValueError("Education entry not found")
        for field, value in data.model_dump().items():
            setattr(entry, field, value)
        await self.db.flush()
        return EducationOut.model_validate(entry)

    async def delete_education(self, entry_id: UUID) -> None:
        entry = await self.edu_repo.get_by_id(entry_id)
        if entry is None:
            raise ValueError("Education entry not found")
        await self.edu_repo.delete(entry)

    # -- Social Links --------------------------------------------------------

    async def update_social_links(self, user_id: UUID, data: SocialLinksUpdate) -> ProfileOut:
        profile = await self.profile_repo.get_or_create(user_id)
        # Replace all links
        profile.social_links.clear()
        await self.db.flush()
        for i, link_data in enumerate(data.links):
            link = SocialLink(
                profile_id=profile.id,
                label=link_data.label,
                url=link_data.url,
                sort_order=i,
            )
            profile.social_links.append(link)
        await self.db.flush()
        return await self._to_profile_out(profile)

    async def update_public_profile_settings(
        self, user_id: UUID, data: PublicProfileSettingsUpdate
    ) -> ProfileOut:
        profile = await self.profile_repo.get_or_create(user_id)
        await self._ensure_public_slug(profile)
        profile.is_public_profile_enabled = data.is_public_profile_enabled
        await self.db.flush()
        return await self._to_profile_out(profile)

    # -- Serialization -------------------------------------------------------

    async def _to_work_experience_out(self, entry: WorkExperience) -> WorkExperienceOut:
        return WorkExperienceOut(
            id=entry.id,
            title=entry.title,
            company=entry.company,
            start_date=entry.start_date,
            end_date=entry.end_date,
            is_current=entry.is_current,
            image_url=await self.storage.resolve_company_url(entry.image_url),
        )

    async def _to_profile_out(self, profile: Profile) -> ProfileOut:
        personal = None
        avatar_url = await self.storage.resolve_profile_url(profile.avatar_url)
        if any(
            [
                profile.name,
                profile.email,
                profile.phone,
                profile.address,
                avatar_url,
                profile.role,
            ]
        ):
            personal = PersonalOut(
                name=profile.name,
                email=profile.email,
                phone=profile.phone,
                address=profile.address,
                avatar=avatar_url,
                role=profile.role,
            )
        return ProfileOut(
            personal=personal,
            about=profile.about,
            skills=[s.name for s in profile.skills],
            work_experience=[
                await self._to_work_experience_out(work_experience)
                for work_experience in profile.work_experiences
            ],
            education=[EducationOut.model_validate(e) for e in profile.education_entries],
            social_links=[SocialLinkOut.model_validate(l) for l in profile.social_links],
            public_slug=profile.public_slug,
            is_public_profile_enabled=profile.is_public_profile_enabled,
        )

    async def _ensure_public_slug(self, profile: Profile) -> None:
        if profile.public_slug:
            return

        email = profile.email or await self._get_user_email(profile.user_id)
        if not email:
            return

        profile.public_slug = await self._generate_unique_slug(email)
        await self.db.flush()

    async def _get_user_email(self, user_id: UUID) -> str | None:
        result = await self.db.execute(
            select(User.email).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _generate_unique_slug(self, email: str) -> str:
        local_part = email.split("@", 1)[0].strip().lower()
        base_slug = re.sub(r"[^a-z0-9]+", "-", local_part).strip("-")
        if not base_slug:
            base_slug = "user"

        candidate = base_slug
        suffix = 2
        while await self._slug_exists(candidate):
            candidate = f"{base_slug}-{suffix}"
            suffix += 1
        return candidate

    async def _slug_exists(self, slug: str) -> bool:
        result = await self.db.execute(
            select(Profile.id).where(Profile.public_slug == slug)
        )
        return result.scalar_one_or_none() is not None
