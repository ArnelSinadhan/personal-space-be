from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import EducationEntry, Profile, SocialLink, WorkExperience
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
    ProfileOut,
    SocialLinkOut,
    SocialLinksUpdate,
    WorkExperienceCreate,
    WorkExperienceOut,
)


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.work_repo = WorkExperienceRepository(db)
        self.edu_repo = EducationRepository(db)
        self.link_repo = SocialLinkRepository(db)
        self.skill_repo = SkillRepository(db)

    async def get_profile(self, user_id: UUID) -> ProfileOut:
        profile = await self.profile_repo.get_or_create(user_id)
        return self._to_profile_out(profile)

    async def update_personal(self, user_id: UUID, data: PersonalUpdate) -> ProfileOut:
        profile = await self.profile_repo.get_or_create(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self.db.flush()
        return self._to_profile_out(profile)

    async def update_about(self, user_id: UUID, data: AboutUpdate) -> ProfileOut:
        profile = await self.profile_repo.get_or_create(user_id)
        profile.about = data.about
        profile.skills = await self.skill_repo.get_or_create_many(data.skills)
        await self.db.flush()
        return self._to_profile_out(profile)

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
        return WorkExperienceOut.model_validate(entry)

    async def update_work_experience(
        self, entry_id: UUID, data: WorkExperienceCreate
    ) -> WorkExperienceOut:
        entry = await self.work_repo.get_by_id(entry_id)
        if entry is None:
            raise ValueError("Work experience not found")
        for field, value in data.model_dump().items():
            setattr(entry, field, value)
        await self.db.flush()
        return WorkExperienceOut.model_validate(entry)

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
            self.db.add(link)
        profile.resume_url = data.resume_url
        await self.db.flush()
        # Reload
        refreshed = await self.profile_repo.get_by_user_id(user_id)
        return self._to_profile_out(refreshed or profile)

    # -- Serialization -------------------------------------------------------

    def _to_profile_out(self, profile: Profile) -> ProfileOut:
        personal = None
        if profile.name or profile.email or profile.role:
            personal = PersonalOut(
                name=profile.name,
                email=profile.email,
                phone=profile.phone,
                address=profile.address,
                avatar=profile.avatar_url,
                role=profile.role,
            )
        return ProfileOut(
            personal=personal,
            about=profile.about,
            skills=[s.name for s in profile.skills],
            work_experience=[WorkExperienceOut.model_validate(w) for w in profile.work_experiences],
            education=[EducationOut.model_validate(e) for e in profile.education_entries],
            social_links=[SocialLinkOut.model_validate(l) for l in profile.social_links],
            resume_url=profile.resume_url,
        )
