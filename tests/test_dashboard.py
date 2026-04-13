import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_overview(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200

    data = response.json()["data"]
    assert data["first_name"] == "there"
    assert data["company_count"] == 0
    assert data["total_projects"] == 0
    assert data["active_project_count"] == 0
    assert data["maintenance_project_count"] == 0
    assert data["completed_project_count"] == 0
    assert data["archived_project_count"] == 0
    assert data["total_tasks"] == 0
    assert data["vault_entry_count"] == 0
    assert data["vault_category_count"] == 0
    assert data["status_counts"]["todo"] == 0
    assert data["profile"]["percent"] >= 0


@pytest.mark.asyncio
async def test_dashboard_excludes_completed_project_todos_from_operational_metrics(
    client: AsyncClient,
):
    workspace = await client.post(
        "/api/v1/profile/work-experience",
        json={
            "title": "Engineer",
            "company": "Example Co",
            "start_date": "2024",
        },
    )
    workspace_id = workspace.json()["id"]

    active_project = await client.post(
        f"/api/v1/work-experiences/{workspace_id}/projects",
        json={
            "name": "Active Platform",
            "tech_stack": ["Next.js"],
            "lifecycle_status": "active",
        },
    )
    active_project_id = active_project.json()["data"]["id"]
    await client.post(
        f"/api/v1/projects/{active_project_id}/todos",
        json={"title": "Ship release", "status": "in_progress"},
    )

    completed_project = await client.post(
        f"/api/v1/work-experiences/{workspace_id}/projects",
        json={
            "name": "Historical Portal",
            "tech_stack": ["FastAPI"],
            "lifecycle_status": "completed",
        },
    )
    completed_project_data = completed_project.json()["data"]

    overview = await client.get("/api/v1/dashboard/overview")
    assert overview.status_code == 200
    data = overview.json()["data"]

    assert data["total_projects"] == 2
    assert data["active_project_count"] == 1
    assert data["completed_project_count"] == 1
    assert data["total_tasks"] == 1
    assert data["status_counts"]["in_progress"] == 1
    assert data["project_radial_data"][0]["name"] == "Active Platform"
    assert completed_project_data["completed_at"] is not None
