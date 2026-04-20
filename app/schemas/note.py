from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class NoteCreate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: str = Field(..., min_length=1, max_length=10000)
    is_pinned: bool = False

    @field_validator("content")
    @classmethod
    def ensure_content_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Note content is required.")
        return value


class NoteUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: str | None = Field(None, min_length=1, max_length=10000)
    is_pinned: bool | None = None

    @field_validator("content")
    @classmethod
    def ensure_updated_content_is_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Note content is required.")
        return value

    @model_validator(mode="after")
    def ensure_any_field_present(self) -> "NoteUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field is required.")
        return self


class NoteOut(BaseModel):
    id: UUID
    title: str | None = None
    content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteSummaryOut(BaseModel):
    id: UUID
    title: str | None = None
    preview_content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    has_more_content: bool


class NotePaginationOut(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_previous_page: bool
    has_next_page: bool


class NoteListResponse(BaseModel):
    items: list[NoteSummaryOut]
    pagination: NotePaginationOut
