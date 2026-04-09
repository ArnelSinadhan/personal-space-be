from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# PIN
# ---------------------------------------------------------------------------

class PinVerify(BaseModel):
    pin: str = Field(..., min_length=4, max_length=10)


class PinSet(BaseModel):
    pin: str = Field(..., min_length=4, max_length=10)


class PinVerifyResponse(BaseModel):
    success: bool
    vault_token: str | None = None


class PinStatusResponse(BaseModel):
    has_pin: bool


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class VaultCategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    icon_name: str = Field(..., max_length=50)


class VaultCategoryUpdate(VaultCategoryCreate):
    pass


class VaultCategoryOut(BaseModel):
    id: UUID
    name: str
    icon_name: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------

class VaultEntryCreate(BaseModel):
    title: str = Field(..., max_length=255)
    username: str = Field(..., max_length=255)
    password: str = Field(..., min_length=1)
    category_id: UUID | None = None
    icon_name: str | None = Field(None, max_length=50)


class VaultEntryUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    username: str | None = Field(None, max_length=255)
    password: str | None = None
    category_id: UUID | None = None
    icon_name: str | None = Field(None, max_length=50)


class VaultEntryOut(BaseModel):
    id: UUID
    title: str
    username: str
    password: str | None = None
    has_password: bool = True
    category_id: UUID | None = None
    icon_name: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class VaultEntryPasswordResponse(BaseModel):
    password: str


# ---------------------------------------------------------------------------
# List responses
# ---------------------------------------------------------------------------

class VaultCategoryListResponse(BaseModel):
    data: list[VaultCategoryOut]


class VaultEntryListResponse(BaseModel):
    data: list[VaultEntryOut]
