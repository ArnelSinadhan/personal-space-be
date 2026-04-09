from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.project import ProjectOut


# ---------------------------------------------------------------------------
# Nested sub-schemas
# ---------------------------------------------------------------------------

class WorkExperienceCreate(BaseModel):
    title: str = Field(..., max_length=255)
    company: str = Field(..., max_length=255)
    start_date: str = Field(..., max_length=100)
    end_date: str | None = None
    is_current: bool = False
    image_url: str | None = None


class WorkExperienceUpdate(WorkExperienceCreate):
    pass


class WorkExperienceOut(WorkExperienceCreate):
    id: UUID
    model_config = {"from_attributes": True}


class WorkExperienceWorkspaceOut(WorkExperienceOut):
    projects: list[ProjectOut] = []


class WorkExperienceListResponse(BaseModel):
    data: list[WorkExperienceWorkspaceOut]


class EducationCreate(BaseModel):
    degree: str = Field(..., max_length=255)
    school: str = Field(..., max_length=255)
    years: str = Field(..., max_length=100)


class EducationUpdate(EducationCreate):
    pass


class EducationOut(EducationCreate):
    id: UUID
    model_config = {"from_attributes": True}


class SocialLinkOut(BaseModel):
    id: UUID
    label: str
    url: str
    model_config = {"from_attributes": True}


class SocialLinkInput(BaseModel):
    label: str = Field(..., max_length=100)
    url: str


# ---------------------------------------------------------------------------
# Personal details
# ---------------------------------------------------------------------------

class PersonalUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    address: str | None = None
    avatar_url: str | None = None
    role: str | None = Field(None, max_length=255)


class PersonalOut(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    address: str | None
    avatar: str | None = None  # mapped from avatar_url
    role: str | None
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# About & Skills
# ---------------------------------------------------------------------------

class AboutUpdate(BaseModel):
    about: str | None = None
    skills: list[str] = []


# ---------------------------------------------------------------------------
# Social Links (bulk update)
# ---------------------------------------------------------------------------

class SocialLinksUpdate(BaseModel):
    links: list[SocialLinkInput] = []


class PublicProfileSettingsUpdate(BaseModel):
    is_public_profile_enabled: bool


# ---------------------------------------------------------------------------
# Full profile response (matches frontend ProfileData)
# ---------------------------------------------------------------------------

class ProfileOut(BaseModel):
    personal: PersonalOut | None = None
    about: str | None = None
    skills: list[str] = []
    work_experience: list[WorkExperienceOut] = []
    education: list[EducationOut] = []
    social_links: list[SocialLinkOut] = []
    public_slug: str | None = None
    is_public_profile_enabled: bool = False

    # Aliases to match frontend camelCase if needed via serialization_alias
    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    data: ProfileOut
