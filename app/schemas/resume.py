from uuid import UUID

from pydantic import BaseModel, Field

from app.enums import ResumeTemplate


# ---------------------------------------------------------------------------
# Nested sub-schemas
# ---------------------------------------------------------------------------

class ResumeExperienceInput(BaseModel):
    title: str = Field(..., max_length=255)
    company: str = Field(..., max_length=255)
    start_date: str = Field(..., max_length=100)
    end_date: str = ""
    is_current: bool = False
    description: str | None = None


class ResumeExperienceOut(ResumeExperienceInput):
    id: UUID
    model_config = {"from_attributes": True}


class ResumeEducationInput(BaseModel):
    degree: str = Field(..., max_length=255)
    school: str = Field(..., max_length=255)
    years: str = Field(..., max_length=100)


class ResumeEducationOut(ResumeEducationInput):
    id: UUID
    model_config = {"from_attributes": True}


class ResumeProjectInput(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    tech_stack: list[str] = []


class ResumeProjectOut(ResumeProjectInput):
    id: UUID
    model_config = {"from_attributes": True}


class ResumeLinkInput(BaseModel):
    label: str = Field(..., max_length=100)
    url: str


class ResumeLinkOut(ResumeLinkInput):
    id: UUID
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Personal
# ---------------------------------------------------------------------------

class ResumePersonalInput(BaseModel):
    name: str | None = Field(None, max_length=255)
    role: str | None = Field(None, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    address: str | None = None
    summary: str | None = None


# ---------------------------------------------------------------------------
# Full resume
# ---------------------------------------------------------------------------

class ResumeCreate(BaseModel):
    template: ResumeTemplate = ResumeTemplate.CLASSIC
    personal: ResumePersonalInput = ResumePersonalInput()
    experience: list[ResumeExperienceInput] = []
    education: list[ResumeEducationInput] = []
    skills: list[str] = []
    projects: list[ResumeProjectInput] = []
    links: list[ResumeLinkInput] = []


class ResumeUpdate(ResumeCreate):
    pass


class ResumeOut(BaseModel):
    id: UUID
    template: ResumeTemplate
    personal: ResumePersonalInput
    experience: list[ResumeExperienceOut] = []
    education: list[ResumeEducationOut] = []
    skills: list[str] = []
    projects: list[ResumeProjectOut] = []
    links: list[ResumeLinkOut] = []
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class ResumeResponse(BaseModel):
    data: ResumeOut | None


class TemplateUpdate(BaseModel):
    template: ResumeTemplate
