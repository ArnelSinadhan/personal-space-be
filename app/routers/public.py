from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import MessageResponse
from app.schemas.public import (
    PortfolioViewCreate,
    PublicPortfolioResponse,
    PublicProjectTestimonialCreate,
)
from app.services.public_service import (
    PublicPortfolioNotFoundError,
    PublicPortfolioService,
    PublicSubmissionConflictError,
    PublicSubmissionRateLimitError,
    PublicSubmissionValidationError,
)

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/portfolio/{slug}", response_model=PublicPortfolioResponse)
async def get_public_portfolio(slug: str, db: AsyncSession = Depends(get_db)):
    service = PublicPortfolioService(db)
    try:
        portfolio = await service.get_portfolio(slug)
    except PublicPortfolioNotFoundError as exc:
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
    except PublicPortfolioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return MessageResponse(message="Recorded")


@router.post(
    "/portfolio/{slug}/projects/{project_id}/testimonial",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_project_testimonial(
    slug: str,
    project_id: UUID,
    payload: PublicProjectTestimonialCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    service = PublicPortfolioService(db)
    try:
        await service.submit_project_testimonial(
            slug=slug,
            project_id=project_id,
            payload=payload,
            request=request,
        )
    except PublicPortfolioNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PublicSubmissionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PublicSubmissionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PublicSubmissionRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    return MessageResponse(message="Submitted for review")
