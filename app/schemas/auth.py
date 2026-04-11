from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    id_token: str = Field(..., min_length=1, max_length=4096)


class SessionCreateResponse(BaseModel):
    session_cookie: str
    expires_in_seconds: int


class SessionVerifyRequest(BaseModel):
    session_cookie: str = Field(..., min_length=1, max_length=8192)


class SessionVerifyResponse(BaseModel):
    authenticated: bool
    uid: str | None = None
    email: str | None = None

