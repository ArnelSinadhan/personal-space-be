from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.vault import (
    PinSet,
    PinVerify,
    PinVerifyResponse,
    VaultCategoryCreate,
    VaultCategoryListResponse,
    VaultCategoryOut,
    VaultEntryCreate,
    VaultEntryListResponse,
    VaultEntryOut,
    VaultEntryUpdate,
)
from app.services.vault_service import VaultService

router = APIRouter(prefix="/api/v1/vault", tags=["vault"])


# -- PIN ---------------------------------------------------------------------

@router.post("/set-pin", response_model=MessageResponse)
async def set_pin(
    payload: PinSet,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    await service.set_pin(user.id, payload.pin)
    return MessageResponse(message="PIN set successfully")


@router.post("/verify-pin", response_model=PinVerifyResponse)
async def verify_pin(
    payload: PinVerify,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    token = await service.verify_pin(user.id, payload.pin)
    if token is None:
        return PinVerifyResponse(success=False)
    return PinVerifyResponse(success=True, vault_token=token)


# -- Categories --------------------------------------------------------------

@router.get("/categories", response_model=VaultCategoryListResponse)
async def list_categories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    cats = await service.get_categories(user.id)
    return VaultCategoryListResponse(data=cats)


@router.post("/categories", response_model=VaultCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: VaultCategoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    return await service.create_category(user.id, payload)


@router.put("/categories/{cat_id}", response_model=VaultCategoryOut)
async def update_category(
    cat_id: UUID,
    payload: VaultCategoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    try:
        return await service.update_category(cat_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found")


@router.delete("/categories/{cat_id}", response_model=MessageResponse)
async def delete_category(
    cat_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    try:
        await service.delete_category(cat_id, user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found")
    return MessageResponse(message="Deleted")


# -- Entries -----------------------------------------------------------------

@router.get("/entries", response_model=VaultEntryListResponse)
async def list_entries(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    entries = await service.get_entries(user.id)
    return VaultEntryListResponse(data=entries)


@router.post("/entries", response_model=VaultEntryOut, status_code=status.HTTP_201_CREATED)
async def create_entry(
    payload: VaultEntryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    return await service.create_entry(user.id, payload)


@router.put("/entries/{entry_id}", response_model=VaultEntryOut)
async def update_entry(
    entry_id: UUID,
    payload: VaultEntryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    try:
        return await service.update_entry(entry_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Entry not found")


@router.delete("/entries/{entry_id}", response_model=MessageResponse)
async def delete_entry(
    entry_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = VaultService(db)
    try:
        await service.delete_entry(entry_id, user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Entry not found")
    return MessageResponse(message="Deleted")
