from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.profile import (
    AboutUpdate,
    EducationCreate,
    EducationOut,
    PersonalUpdate,
    PublicProfileSettingsUpdate,
    ProfileResponse,
    SocialLinksUpdate,
    WorkExperienceCreate,
    WorkExperienceOut,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    profile = await service.get_profile(user.id)
    return ProfileResponse(data=profile)


@router.post(
    "/education", response_model=EducationOut, status_code=status.HTTP_201_CREATED
)
async def add_education(
    payload: EducationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.add_education(user.id, payload)


@router.post(
    "/work-experience",
    response_model=WorkExperienceOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_work_experience(
    payload: WorkExperienceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return await service.add_work_experience(user.id, payload)


@router.put("/about", response_model=ProfileResponse)
async def update_about(
    payload: AboutUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    profile = await service.update_about(user.id, payload)
    return ProfileResponse(data=profile)


@router.put("/education/{entry_id}", response_model=EducationOut)
async def update_education(
    entry_id: UUID,
    payload: EducationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    try:
        return await service.update_education(entry_id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Education entry not found")


@router.put("/personal", response_model=ProfileResponse)
async def update_personal(
    payload: PersonalUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    profile = await service.update_personal(user.id, payload)
    return ProfileResponse(data=profile)


@router.put("/public-settings", response_model=ProfileResponse)
async def update_public_profile_settings(
    payload: PublicProfileSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    profile = await service.update_public_profile_settings(user.id, payload)
    return ProfileResponse(data=profile)


@router.put("/social-links", response_model=ProfileResponse)
async def update_social_links(
    payload: SocialLinksUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    profile = await service.update_social_links(user.id, payload)
    return ProfileResponse(data=profile)


@router.put("/work-experience/{entry_id}", response_model=WorkExperienceOut)
async def update_work_experience(
    entry_id: UUID,
    payload: WorkExperienceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    try:
        return await service.update_work_experience(entry_id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Work experience not found")


@router.delete("/education/{entry_id}", response_model=MessageResponse)
async def delete_education(
    entry_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    try:
        await service.delete_education(entry_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Education entry not found")
    return MessageResponse(message="Deleted")


@router.delete("/work-experience/{entry_id}", response_model=MessageResponse)
async def delete_work_experience(
    entry_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    try:
        await service.delete_work_experience(entry_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Work experience not found")
    return MessageResponse(message="Deleted")
