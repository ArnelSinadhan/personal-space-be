import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workspace_list(client: AsyncClient):
    response = await client.post("/api/v1/profile/work-experience", json={
        "title": "Software Engineer",
        "company": "Hipe Japan Inc",
        "start_date": "September 2024",
        "is_current": True,
    })
    assert response.status_code == 201
    workspace = response.json()
    workspace_id = workspace["id"]
    assert workspace["company"] == "Hipe Japan Inc"

    response = await client.get("/api/v1/work-experiences")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1
    assert any(item["id"] == workspace_id for item in data)

    response = await client.get("/api/v1/work-experiences", params={"current_only": "true"})
    assert response.status_code == 200
    assert any(item["id"] == workspace_id for item in response.json()["data"])


@pytest.mark.asyncio
async def test_project_and_todo_flow(client: AsyncClient):
    response = await client.post("/api/v1/profile/work-experience", json={
        "title": "Engineer",
        "company": "Test Co",
        "start_date": "2024",
    })
    work_experience_id = response.json()["id"]

    # Create project
    response = await client.post(f"/api/v1/work-experiences/{work_experience_id}/projects", json={
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
