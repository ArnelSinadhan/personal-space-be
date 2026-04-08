from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import DashboardOverviewResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    overview = await service.get_overview(user.id)
    return DashboardOverviewResponse(data=overview)
