from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.project import ProjectOut


class CompanyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    logo_url: str | None = None
    role: str | None = Field(None, max_length=255)
    start_date: str = Field(..., max_length=100)
    end_date: str | None = None
    is_current: bool = False


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    logo_url: str | None = None
    role: str | None = Field(None, max_length=255)
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool | None = None


class CompanyOut(BaseModel):
    id: UUID
    name: str
    logo_url: str | None = None
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool
    projects: list[ProjectOut] = []

    model_config = {"from_attributes": True}


class CompanyResponse(BaseModel):
    data: CompanyOut


class CompanyListResponse(BaseModel):
    data: list[CompanyOut]
