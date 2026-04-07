from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.company import CompanyCreate, CompanyListResponse, CompanyResponse, CompanyUpdate
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    companies = await service.get_companies_for_user(user.id)
    return CompanyListResponse(data=companies)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    company = await service.create_company(user.id, payload)
    return CompanyResponse(data=company)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        company = await service.update_company(company_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse(data=company)


@router.delete("/{company_id}", response_model=MessageResponse)
async def delete_company(
    company_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        await service.delete_company(company_id, user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Company not found")
    return MessageResponse(message="Deleted")


# -- Projects nested under companies ----------------------------------------

@router.post("/{company_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    company_id: UUID,
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        project = await service.create_project(company_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Company not found")
    return ProjectResponse(data=project)
