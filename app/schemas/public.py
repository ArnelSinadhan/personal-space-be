from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.enums import ProjectLifecycleStatus


class PublicSocialLinkOut(BaseModel):
    label: str
    url: str


class PublicProjectTestimonialOut(BaseModel):
    name: str
    role: str | None = None
    message: str


class PublicProjectOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    company: str
    tech_stack: list[str] = []
    lifecycle_status: ProjectLifecycleStatus = ProjectLifecycleStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = None
    testimonial: PublicProjectTestimonialOut | None = None


class PublicPersonalProjectOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] = []
    is_featured: bool = False
    lifecycle_status: ProjectLifecycleStatus = ProjectLifecycleStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = None


class PublicWorkExperienceOut(BaseModel):
    title: str
    company: str
    description: str | None = None
    start_date: str
    end_date: str | None = None
    is_current: bool
    image_url: str | None = None
    projects: list[PublicProjectOut] = []


class PublicEducationOut(BaseModel):
    degree: str
    school: str
    years: str


class PublicCertificationOut(BaseModel):
    name: str
    issuer: str
    issued_at: str
    expires_at: str | None = None
    credential_id: str | None = None
    credential_url: str | None = None
    image_url: str | None = None


class PublicProfileOut(BaseModel):
    name: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    avatar: str | None = None
    resume_url: str | None = None
    about: str | None = None
    skills: list[str] = []
    social_links: list[PublicSocialLinkOut] = []


class PublicPortfolioStatsOut(BaseModel):
    company_count: int = 0
    public_project_count: int = 0
    skill_count: int = 0
    total_views: int = 0


class PublicPortfolioOut(BaseModel):
    profile: PublicProfileOut | None = None
    work_experience: list[PublicWorkExperienceOut] = []
    personal_projects: list[PublicPersonalProjectOut] = []
    education: list[PublicEducationOut] = []
    certifications: list[PublicCertificationOut] = []
    stats: PublicPortfolioStatsOut


class PublicPortfolioResponse(BaseModel):
    data: PublicPortfolioOut


class PortfolioViewCreate(BaseModel):
    path: str | None = "/"
    source: str | None = None


class PublicProjectTestimonialCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    role: str | None = Field(None, max_length=120)
    message: str = Field(..., min_length=20, max_length=1500)
    captcha_token: str | None = Field(None, max_length=2048)

    @field_validator("name", "role", "message", "captcha_token", mode="before")
    @classmethod
    def strip_text(cls, value: str | None):
        if isinstance(value, str):
            value = value.strip()
        return value or None
