from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.profile import WorkExperienceListResponse
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/work-experiences", tags=["workspaces"])


@router.get("", response_model=WorkExperienceListResponse)
async def list_workspaces(
    current_only: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    workspaces = await service.get_workspaces_for_user(user.id, current_only=current_only)
    return WorkExperienceListResponse(data=workspaces)


@router.post("/{work_experience_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    work_experience_id: UUID,
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        project = await service.create_project(work_experience_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Work experience not found")
    return ProjectResponse(data=project)
