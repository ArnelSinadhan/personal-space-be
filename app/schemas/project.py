from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.todo import TodoOut


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    image_url: str | None = None
    tech_stack: list[str] = []
    is_public: bool = False


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    image_url: str | None = None
    tech_stack: list[str] | None = None
    is_public: bool | None = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    image_url: str | None = None
    tech_stack: list[str] = []
    is_public: bool
    todos: list[TodoOut] = []

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    data: ProjectOut
