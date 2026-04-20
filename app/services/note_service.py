from uuid import UUID

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.schemas.note import (
    NoteCreate,
    NoteOut,
    NotePaginationOut,
    NoteSummaryOut,
    NoteUpdate,
)


class NoteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_notes(
        self,
        user_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list[NoteSummaryOut], NotePaginationOut]:
        filters = [Note.user_id == user_id]
        normalized_search = (search or "").strip()
        if normalized_search:
            search_term = f"%{normalized_search}%"
            filters.append(
                or_(
                    func.coalesce(Note.title, "").ilike(search_term),
                    Note.content.ilike(search_term),
                )
            )

        total_items = int(
            (
                await self.db.execute(
                    select(func.count(Note.id)).where(*filters)
                )
            ).scalar()
            or 0
        )
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        current_page = min(page, total_pages)
        offset = (current_page - 1) * page_size

        result = await self.db.execute(
            select(
                Note.id,
                Note.title,
                func.substring(Note.content, 1, 320).label("preview_content"),
                Note.is_pinned,
                Note.created_at,
                Note.updated_at,
                (func.length(Note.content) > 320).label("has_more_content"),
            )
            .where(*filters)
            .order_by(desc(Note.is_pinned), desc(Note.updated_at), desc(Note.created_at))
            .offset(offset)
            .limit(page_size)
        )
        notes = [
            NoteSummaryOut(
                id=row.id,
                title=row.title,
                preview_content=row.preview_content or "",
                is_pinned=row.is_pinned,
                created_at=row.created_at,
                updated_at=row.updated_at,
                has_more_content=bool(row.has_more_content),
            )
            for row in result.all()
        ]
        pagination = NotePaginationOut(
            page=current_page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_previous_page=current_page > 1,
            has_next_page=current_page < total_pages,
        )
        return notes, pagination

    async def get_note(self, note_id: UUID, user_id: UUID) -> NoteOut:
        note = await self._get_note_for_user(note_id, user_id)
        if note is None:
            raise ValueError("Note not found")
        return NoteOut.model_validate(note)

    async def create_note(self, user_id: UUID, payload: NoteCreate) -> NoteOut:
        note = Note(
            user_id=user_id,
            title=self._normalize_title(payload.title),
            content=payload.content,
            is_pinned=payload.is_pinned,
        )
        self.db.add(note)
        await self.db.flush()
        await self.db.refresh(note)
        return NoteOut.model_validate(note)

    async def update_note(
        self,
        note_id: UUID,
        user_id: UUID,
        payload: NoteUpdate,
    ) -> NoteOut:
        note = await self._get_note_for_user(note_id, user_id)
        if note is None:
            raise ValueError("Note not found")

        if "title" in payload.model_fields_set:
            note.title = self._normalize_title(payload.title)
        if "content" in payload.model_fields_set:
            note.content = payload.content or note.content
        if "is_pinned" in payload.model_fields_set and payload.is_pinned is not None:
            note.is_pinned = payload.is_pinned

        await self.db.flush()
        await self.db.refresh(note)
        return NoteOut.model_validate(note)

    async def delete_note(self, note_id: UUID, user_id: UUID) -> None:
        note = await self._get_note_for_user(note_id, user_id)
        if note is None:
            raise ValueError("Note not found")
        await self.db.delete(note)
        await self.db.flush()

    async def _get_note_for_user(self, note_id: UUID, user_id: UUID) -> Note | None:
        result = await self.db.execute(
            select(Note).where(Note.id == note_id, Note.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def _normalize_title(self, title: str | None) -> str | None:
        if title is None:
            return None
        normalized_title = title.strip()
        return normalized_title or None
