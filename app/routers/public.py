from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import MessageResponse
from app.schemas.public import PortfolioViewCreate, PublicPortfolioResponse
from app.services.public_service import PublicPortfolioService

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/portfolio/{slug}", response_model=PublicPortfolioResponse)
async def get_public_portfolio(slug: str, db: AsyncSession = Depends(get_db)):
    service = PublicPortfolioService(db)
    try:
        portfolio = await service.get_portfolio(slug)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return PublicPortfolioResponse(data=portfolio)


@router.post(
    "/portfolio/{slug}/view",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_portfolio_view(
    slug: str,
    payload: PortfolioViewCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    service = PublicPortfolioService(db)
    try:
        await service.record_view(slug=slug, payload=payload, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return MessageResponse(message="Recorded")
