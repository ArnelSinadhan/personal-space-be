from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import ProjectResponse, ProjectUpdate
from app.schemas.todo import TodoCreate, TodoOut, TodoUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1", tags=["projects & todos"])


# -- Projects ----------------------------------------------------------------

@router.post("/projects/{project_id}/todos", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
async def create_todo(
    project_id: UUID,
    payload: TodoCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        return await service.create_todo(project_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        project = await service.update_project(project_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(data=project)


@router.patch("/todos/{todo_id}", response_model=TodoOut)
async def update_todo(
    todo_id: UUID,
    payload: TodoUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        return await service.update_todo(todo_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Todo not found")


@router.delete("/todos/{todo_id}", response_model=MessageResponse)
async def delete_todo(
    todo_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        await service.delete_todo(todo_id, user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Todo not found")
    return MessageResponse(message="Deleted")


@router.delete("/projects/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    try:
        await service.delete_project(project_id, user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")
    return MessageResponse(message="Deleted")
