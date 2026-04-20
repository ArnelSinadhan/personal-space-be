import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notes_crud_flow(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/notes",
        json={
            "title": "Portfolio ideas",
            "content": "Add a cleaner notes experience to Personal Space.",
            "is_pinned": True,
        },
    )
    assert create_response.status_code == 201
    created_note = create_response.json()
    assert created_note["title"] == "Portfolio ideas"
    assert created_note["is_pinned"] is True

    list_response = await client.get("/api/v1/notes")
    assert list_response.status_code == 200
    notes = list_response.json()["items"]
    assert len(notes) == 1
    assert notes[0]["id"] == created_note["id"]
    assert notes[0]["preview_content"].startswith("Add a cleaner")

    update_response = await client.put(
        f"/api/v1/notes/{created_note['id']}",
        json={
            "content": "Add a cleaner notes experience to Personal Space dashboard.",
            "is_pinned": False,
        },
    )
    assert update_response.status_code == 200
    updated_note = update_response.json()
    assert updated_note["content"].endswith("dashboard.")
    assert updated_note["is_pinned"] is False

    delete_response = await client.delete(f"/api/v1/notes/{created_note['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Deleted"

    final_list_response = await client.get("/api/v1/notes")
    assert final_list_response.status_code == 200
    assert final_list_response.json()["items"] == []


@pytest.mark.asyncio
async def test_notes_are_sorted_with_pinned_first(client: AsyncClient):
    await client.post(
        "/api/v1/notes",
        json={"title": "Second", "content": "Unpinned note", "is_pinned": False},
    )
    await client.post(
        "/api/v1/notes",
        json={"title": "First", "content": "Pinned note", "is_pinned": True},
    )

    response = await client.get("/api/v1/notes")
    assert response.status_code == 200
    notes = response.json()["items"]
    assert len(notes) == 2
    assert notes[0]["title"] == "First"
    assert notes[0]["is_pinned"] is True


@pytest.mark.asyncio
async def test_note_update_returns_404_for_missing_note(client: AsyncClient):
    response = await client.put(
        "/api/v1/notes/00000000-0000-0000-0000-000000000000",
        json={"content": "Missing note"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


@pytest.mark.asyncio
async def test_note_title_can_be_cleared(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/notes",
        json={"title": "Temporary title", "content": "Body"},
    )
    note_id = create_response.json()["id"]

    update_response = await client.put(
        f"/api/v1/notes/{note_id}",
        json={"title": None},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] is None


@pytest.mark.asyncio
async def test_note_content_preserves_markdown_whitespace(client: AsyncClient):
    markdown_content = "  indented line\nline with two spaces  \n- [ ] checklist"
    create_response = await client.post(
        "/api/v1/notes",
        json={"title": "Markdown", "content": markdown_content},
    )
    assert create_response.status_code == 201
    note_id = create_response.json()["id"]

    detail_response = await client.get(f"/api/v1/notes/{note_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["content"] == markdown_content


@pytest.mark.asyncio
async def test_notes_list_is_paginated_and_supports_detail_fetch(client: AsyncClient):
    for index in range(14):
        response = await client.post(
            "/api/v1/notes",
            json={
                "title": f"Note {index}",
                "content": f"Content for note {index}",
                "is_pinned": index == 13,
            },
        )
        assert response.status_code == 201

    page_one_response = await client.get("/api/v1/notes?page=1&page_size=12")
    assert page_one_response.status_code == 200
    payload = page_one_response.json()
    assert len(payload["items"]) == 12
    assert payload["pagination"]["total_items"] == 14
    assert payload["pagination"]["has_next_page"] is True
    assert payload["items"][0]["title"] == "Note 13"

    note_id = payload["items"][0]["id"]
    detail_response = await client.get(f"/api/v1/notes/{note_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["content"] == "Content for note 13"
