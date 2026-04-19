from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardPortfolioInsightsResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_overview(user.id)


@router.get("/portfolio-insights", response_model=DashboardPortfolioInsightsResponse)
async def get_portfolio_insights(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_portfolio_insights(
        user.id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/portfolio-insights/visitors/{visitor_id}/decrement",
    response_model=MessageResponse,
)
async def decrement_portfolio_visitor(
    visitor_id: str,
    ip_address: str = Query(..., min_length=1, max_length=255),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    try:
        await service.decrement_portfolio_visitor_visit_count(
            user_id=user.id,
            visitor_id=visitor_id,
            ip_address=ip_address,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return MessageResponse(message="Visit count decremented")
