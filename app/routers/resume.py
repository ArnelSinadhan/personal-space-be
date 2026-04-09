from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.resume import ResumeResponse, ResumeUpdate
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
