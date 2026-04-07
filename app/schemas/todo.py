from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums import TodoStatus


class TodoCreate(BaseModel):
    title: str = Field(..., max_length=500)
    status: TodoStatus = TodoStatus.TODO


class TodoUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    status: TodoStatus | None = None


class TodoBulkItem(BaseModel):
    id: UUID
    status: TodoStatus
    sort_order: int = 0


class TodoBulkUpdate(BaseModel):
    project_id: UUID
    todos: list[TodoBulkItem]


class TodoOut(BaseModel):
    id: UUID
    title: str
    status: TodoStatus
    completed_at: datetime | None = None
    sort_order: int = 0

    model_config = {"from_attributes": True}
