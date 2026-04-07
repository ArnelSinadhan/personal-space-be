from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.enums import ReportPeriod
from app.models.user import User
from app.schemas.report import ReportCompletedResponse, ReportSummaryResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/summary", response_model=ReportSummaryResponse)
async def get_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    summary = await service.get_summary(user.id)
    return ReportSummaryResponse(data=summary)


@router.get("/completed", response_model=ReportCompletedResponse)
async def get_completed(
    period: ReportPeriod = Query(ReportPeriod.DAILY),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    groups = await service.get_completed(user.id, period)
    return ReportCompletedResponse(data=groups)
