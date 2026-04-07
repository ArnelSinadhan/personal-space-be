from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.resume import ResumeResponse, ResumeUpdate, TemplateUpdate
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/api/v1/resume", tags=["resume"])


@router.get("", response_model=ResumeResponse)
async def get_resume(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.get_resume(user.id)
    return ResumeResponse(data=resume)


@router.put("", response_model=ResumeResponse)
async def save_resume(
    payload: ResumeUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.save_resume(user.id, payload)
    return ResumeResponse(data=resume)


@router.delete("", response_model=MessageResponse)
async def delete_resume(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    try:
        await service.delete_resume(user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Resume not found")
    return MessageResponse(message="Deleted")


@router.post("/generate", response_model=ResumeResponse)
async def generate_from_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.generate_from_profile(user.id)
    return ResumeResponse(data=resume)


@router.patch("/template", response_model=ResumeResponse)
async def change_template(
    payload: TemplateUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    try:
        resume = await service.change_template(user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeResponse(data=resume)
