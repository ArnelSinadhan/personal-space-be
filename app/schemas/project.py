from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums import ProjectLifecycleStatus, ProjectTestimonialStatus
from app.schemas.todo import TodoOut


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] = []
    is_public: bool = False
    lifecycle_status: ProjectLifecycleStatus = ProjectLifecycleStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = Field(None, max_length=2000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] | None = None
    is_public: bool | None = None
    lifecycle_status: ProjectLifecycleStatus | None = None
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = Field(None, max_length=2000)


class PersonalProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] = []
    is_public: bool = False
    is_featured: bool = False
    lifecycle_status: ProjectLifecycleStatus = ProjectLifecycleStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = Field(None, max_length=2000)


class PersonalProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] | None = None
    is_public: bool | None = None
    is_featured: bool | None = None
    lifecycle_status: ProjectLifecycleStatus | None = None
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = Field(None, max_length=2000)


class ProjectTestimonialUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    role: str | None = Field(None, max_length=120)
    message: str | None = Field(None, min_length=20, max_length=1500)
    status: ProjectTestimonialStatus | None = None


class ProjectTestimonialOut(BaseModel):
    id: UUID
    name: str
    role: str | None = None
    message: str
    status: ProjectTestimonialStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] = []
    is_public: bool
    lifecycle_status: ProjectLifecycleStatus
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = None
    testimonial: ProjectTestimonialOut | None = None
    todos: list[TodoOut] = []

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    data: ProjectOut


class PersonalProjectOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] = []
    is_public: bool
    is_featured: bool = False
    lifecycle_status: ProjectLifecycleStatus
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = None

    model_config = {"from_attributes": True}


class PersonalProjectListResponse(BaseModel):
    data: list[PersonalProjectOut]


class PersonalProjectResponse(BaseModel):
    data: PersonalProjectOut


# ---------------------------------------------------------------------------
# Upwork projects
# ---------------------------------------------------------------------------


class UpworkProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    client_name: str | None = Field(None, max_length=255)
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] = []
    is_public: bool = False
    is_featured: bool = False
    lifecycle_status: ProjectLifecycleStatus = ProjectLifecycleStatus.ACTIVE
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = Field(None, max_length=2000)


class UpworkProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    client_name: str | None = Field(None, max_length=255)
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] | None = None
    is_public: bool | None = None
    is_featured: bool | None = None
    lifecycle_status: ProjectLifecycleStatus | None = None
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = Field(None, max_length=2000)


class UpworkProjectOut(BaseModel):
    id: UUID
    name: str
    client_name: str | None = None
    description: str | None = None
    image_url: str | None = None
    github_url: str | None = None
    live_url: str | None = None
    tech_stack: list[str] = []
    is_public: bool
    is_featured: bool = False
    lifecycle_status: ProjectLifecycleStatus
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    outcome_summary: str | None = None

    model_config = {"from_attributes": True}


class UpworkProjectListResponse(BaseModel):
    data: list[UpworkProjectOut]


class UpworkProjectResponse(BaseModel):
    data: UpworkProjectOut
