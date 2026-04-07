from uuid import UUID

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class IDResponse(BaseModel):
    id: UUID


class HealthResponse(BaseModel):
    status: str
    db: str
