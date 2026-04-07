import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_company_crud(client: AsyncClient):
    # Create
    response = await client.post("/api/v1/companies", json={
        "name": "Hipe Japan Inc",
        "role": "Software Engineer",
        "start_date": "September 2024",
        "is_current": True,
    })
    assert response.status_code == 201
    company = response.json()["data"]
    company_id = company["id"]
    assert company["name"] == "Hipe Japan Inc"

    # List
    response = await client.get("/api/v1/companies")
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1

    # Update
    response = await client.put(f"/api/v1/companies/{company_id}", json={
        "name": "Hipe Japan Inc (Updated)",
    })
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Hipe Japan Inc (Updated)"

    # Delete
    response = await client.delete(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_project_and_todo_flow(client: AsyncClient):
    # Create company first
    response = await client.post("/api/v1/companies", json={
        "name": "Test Co",
        "start_date": "2024",
    })
    company_id = response.json()["data"]["id"]

    # Create project
    response = await client.post(f"/api/v1/companies/{company_id}/projects", json={
        "name": "Client Management System",
        "description": "Internal tool",
        "tech_stack": ["Next.js", "TypeScript", "FastAPI"],
    })
    assert response.status_code == 201
    project = response.json()["data"]
    project_id = project["id"]
    assert project["name"] == "Client Management System"
    assert "Next.js" in project["tech_stack"]

    # Create todo
    response = await client.post(f"/api/v1/projects/{project_id}/todos", json={
        "title": "Setup authentication flow",
        "status": "todo",
    })
    assert response.status_code == 201
    todo = response.json()
    todo_id = todo["id"]
    assert todo["status"] == "todo"
    assert todo["completed_at"] is None

    # Update todo status to done — should set completed_at
    response = await client.patch(f"/api/v1/todos/{todo_id}", json={
        "status": "done",
    })
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "done"
    assert updated["completed_at"] is not None

    # Update back to in_progress — should clear completed_at
    response = await client.patch(f"/api/v1/todos/{todo_id}", json={
        "status": "in_progress",
    })
    assert response.status_code == 200
    assert response.json()["completed_at"] is None

    # Delete todo
    response = await client.delete(f"/api/v1/todos/{todo_id}")
    assert response.status_code == 200

    # Delete project
    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_bulk_update_todos(client: AsyncClient):
    # Setup: company → project → 2 todos
    resp = await client.post("/api/v1/companies", json={
        "name": "Bulk Co", "start_date": "2024",
    })
    company_id = resp.json()["data"]["id"]

    resp = await client.post(f"/api/v1/companies/{company_id}/projects", json={
        "name": "Bulk Project", "tech_stack": [],
    })
    project_id = resp.json()["data"]["id"]

    resp1 = await client.post(f"/api/v1/projects/{project_id}/todos", json={
        "title": "Task A", "status": "todo",
    })
    resp2 = await client.post(f"/api/v1/projects/{project_id}/todos", json={
        "title": "Task B", "status": "todo",
    })
    id_a = resp1.json()["id"]
    id_b = resp2.json()["id"]

    # Bulk update — simulate Kanban drag
    response = await client.patch("/api/v1/todos/bulk-update", json={
        "project_id": project_id,
        "todos": [
            {"id": id_a, "status": "done", "sort_order": 0},
            {"id": id_b, "status": "in_progress", "sort_order": 1},
        ],
    })
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
