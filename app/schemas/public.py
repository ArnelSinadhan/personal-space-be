from pydantic import BaseModel


class PublicSocialLinkOut(BaseModel):
    label: str
    url: str


class PublicProjectOut(BaseModel):
    name: str
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    company: str
    tech_stack: list[str] = []


class PublicWorkExperienceOut(BaseModel):
    title: str
    company: str
    start_date: str
    end_date: str | None = None
    is_current: bool
    image_url: str | None = None
    projects: list[PublicProjectOut] = []


class PublicEducationOut(BaseModel):
    degree: str
    school: str
    years: str


class PublicProfileOut(BaseModel):
    name: str | None = None
    role: str | None = None
    avatar: str | None = None
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
    education: list[PublicEducationOut] = []
    projects: list[PublicProjectOut] = []
    stats: PublicPortfolioStatsOut


class PublicPortfolioResponse(BaseModel):
    data: PublicPortfolioOut


class PortfolioViewCreate(BaseModel):
    path: str | None = "/"
    source: str | None = None
