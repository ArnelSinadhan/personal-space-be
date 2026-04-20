from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.note import NoteCreate, NoteListResponse, NoteOut, NoteUpdate
from app.services.note_service import NoteService

router = APIRouter(prefix="/api/v1/notes", tags=["notes"])


@router.get("", response_model=NoteListResponse)
async def list_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    search: str | None = Query(None, max_length=255),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NoteService(db)
    notes, pagination = await service.get_notes(
        user.id,
        page=page,
        page_size=page_size,
        search=search,
    )
    return NoteListResponse(items=notes, pagination=pagination)


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NoteService(db)
    try:
        return await service.get_note(note_id, user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Note not found")


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NoteService(db)
    return await service.create_note(user.id, payload)


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: UUID,
    payload: NoteUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NoteService(db)
    try:
        return await service.update_note(note_id, user.id, payload)
    except ValueError:
        raise HTTPException(status_code=404, detail="Note not found")


@router.delete("/{note_id}", response_model=MessageResponse)
async def delete_note(
    note_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NoteService(db)
    try:
        await service.delete_note(note_id, user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Note not found")
    return MessageResponse(message="Deleted")
