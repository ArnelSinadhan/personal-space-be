import pytest
from httpx import AsyncClient

from app.services.storage_service import StorageService


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
        "github_url": "https://github.com/example/cms",
        "live_url": "https://cms.example.com",
        "tech_stack": ["Next.js", "TypeScript", "FastAPI"],
    })
    assert response.status_code == 201
    project = response.json()["data"]
    project_id = project["id"]
    assert project["name"] == "Client Management System"
    assert project["github_url"] == "https://github.com/example/cms"
    assert project["live_url"] == "https://cms.example.com"
    assert "Next.js" in project["tech_stack"]
    assert project["lifecycle_status"] == "active"
    assert project["completed_at"] is None
    assert project["archived_at"] is None

    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={
            "name": "Client Management System",
            "description": "Updated internal tool",
            "github_url": "https://github.com/example/cms-v2",
            "live_url": "https://cms-v2.example.com",
            "tech_stack": ["Next.js", "TypeScript", "FastAPI", "PostgreSQL"],
            "is_public": True,
            "lifecycle_status": "maintenance",
            "outcome_summary": "Supporting the shipped product with iterative updates.",
        },
    )
    assert response.status_code == 200
    updated_project = response.json()["data"]
    assert updated_project["github_url"] == "https://github.com/example/cms-v2"
    assert updated_project["live_url"] == "https://cms-v2.example.com"
    assert updated_project["is_public"] is True
    assert updated_project["lifecycle_status"] == "maintenance"
    assert (
        updated_project["outcome_summary"]
        == "Supporting the shipped product with iterative updates."
    )

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
async def test_project_update_can_clear_existing_image_and_delete_storage_file(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    deleted: list[tuple[str, str | None]] = []

    async def fake_delete_file(self, *, bucket: str, path: str | None):
        deleted.append((bucket, path))
        return None

    monkeypatch.setattr(StorageService, "delete_file", fake_delete_file)

    workspace = await client.post(
        "/api/v1/profile/work-experience",
        json={
            "title": "Engineer",
            "company": "Test Co",
            "start_date": "2024",
        },
    )
    work_experience_id = workspace.json()["id"]

    create_response = await client.post(
        f"/api/v1/work-experiences/{work_experience_id}/projects",
        json={
            "name": "Client Management System",
            "description": "Internal tool",
            "image_url": "stored/project.png",
            "tech_stack": ["Next.js", "TypeScript"],
        },
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["data"]["id"]

    update_response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={
            "name": "Client Management System",
            "description": "Internal tool",
            "image_url": None,
            "tech_stack": ["Next.js", "TypeScript"],
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["data"]["image_url"] is None
    assert deleted == [("project-images", "stored/project.png")]


@pytest.mark.asyncio
async def test_project_testimonial_owner_can_approve_and_delete(client: AsyncClient):
    workspace = await client.post(
        "/api/v1/profile/work-experience",
        json={
            "title": "Engineer",
            "company": "Test Co",
            "start_date": "2024",
        },
    )
    work_experience_id = workspace.json()["id"]

    project_response = await client.post(
        f"/api/v1/work-experiences/{work_experience_id}/projects",
        json={
            "name": "Client Portal",
            "description": "Portal",
            "tech_stack": ["Next.js"],
            "is_public": True,
        },
    )
    project_id = project_response.json()["data"]["id"]

    submit_response = await client.post(
        f"/api/v1/public/portfolio/test/projects/{project_id}/testimonial",
        json={
            "name": "Jane Reviewer",
            "role": "Product Manager",
            "message": "Arnel shipped the portal reliably, communicated clearly, and delivered polished product work end to end.",
        },
    )
    assert submit_response.status_code == 404

    await client.put(
        "/api/v1/profile/personal",
        json={"email": "test@example.com"},
    )
    await client.put(
        "/api/v1/profile/public-settings",
        json={"is_public_profile_enabled": True},
    )
    profile_response = await client.get("/api/v1/profile")
    slug = profile_response.json()["data"]["public_slug"]

    submit_response = await client.post(
        f"/api/v1/public/portfolio/{slug}/projects/{project_id}/testimonial",
        json={
            "name": "Jane Reviewer",
            "role": "Product Manager",
            "message": "Arnel shipped the portal reliably, communicated clearly, and delivered polished product work end to end.",
        },
    )
    assert submit_response.status_code == 201

    approve_response = await client.put(
        f"/api/v1/projects/{project_id}/testimonial",
        json={"status": "approved"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["data"]["testimonial"]["status"] == "approved"

    delete_response = await client.delete(f"/api/v1/projects/{project_id}/testimonial")
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["testimonial"] is None


@pytest.mark.asyncio
async def test_completed_project_disables_todo_mutations(client: AsyncClient):
    workspace = await client.post(
        "/api/v1/profile/work-experience",
        json={
            "title": "Engineer",
            "company": "Test Co",
            "start_date": "2024",
        },
    )
    work_experience_id = workspace.json()["id"]

    project_response = await client.post(
        f"/api/v1/work-experiences/{work_experience_id}/projects",
        json={
            "name": "Legacy Client Portal",
            "description": "Completed historical delivery.",
            "tech_stack": ["Next.js", "FastAPI"],
            "lifecycle_status": "completed",
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()["data"]
    project_id = project["id"]
    assert project["lifecycle_status"] == "completed"
    assert project["completed_at"] is not None

    create_todo_response = await client.post(
        f"/api/v1/projects/{project_id}/todos",
        json={
            "title": "Backfill docs",
            "status": "todo",
        },
    )
    assert create_todo_response.status_code == 409
    assert "Todos are disabled" in create_todo_response.json()["detail"]

    active_project_response = await client.post(
        f"/api/v1/work-experiences/{work_experience_id}/projects",
        json={
            "name": "Ops Dashboard",
            "description": "Operational dashboard",
            "tech_stack": ["React"],
        },
    )
    active_project_id = active_project_response.json()["data"]["id"]

    todo_response = await client.post(
        f"/api/v1/projects/{active_project_id}/todos",
        json={
            "title": "Ship release checklist",
            "status": "todo",
        },
    )
    todo_id = todo_response.json()["id"]

    complete_response = await client.put(
        f"/api/v1/projects/{active_project_id}",
        json={"lifecycle_status": "completed"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["data"]["completed_at"] is not None

    update_todo_response = await client.patch(
        f"/api/v1/todos/{todo_id}",
        json={"status": "done"},
    )
    assert update_todo_response.status_code == 409

    delete_todo_response = await client.delete(f"/api/v1/todos/{todo_id}")
    assert delete_todo_response.status_code == 409


@pytest.mark.asyncio
async def test_personal_project_crud_flow(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/personal-projects",
        json={
            "name": "Budget Tracker",
            "description": "A personal budgeting app.",
            "github_url": "https://github.com/example/budget-tracker",
            "live_url": "https://budget.example.com",
            "tech_stack": ["Next.js", "TypeScript"],
            "is_public": True,
            "is_featured": True,
        },
    )
    assert create_response.status_code == 201
    project = create_response.json()["data"]
    project_id = project["id"]
    assert project["is_featured"] is True
    assert project["lifecycle_status"] == "active"

    list_response = await client.get("/api/v1/personal-projects")
    assert list_response.status_code == 200
    assert any(item["id"] == project_id for item in list_response.json()["data"])

    update_response = await client.put(
        f"/api/v1/personal-projects/{project_id}",
        json={
            "name": "Budget Tracker",
            "description": "Updated budget app.",
            "tech_stack": ["Next.js", "TypeScript", "TailwindCSS"],
            "is_public": True,
            "is_featured": False,
            "lifecycle_status": "archived",
            "outcome_summary": "Kept as historical reference after wrapping active development.",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["is_featured"] is False
    assert update_response.json()["data"]["lifecycle_status"] == "archived"
    assert update_response.json()["data"]["archived_at"] is not None

    delete_response = await client.delete(f"/api/v1/personal-projects/{project_id}")
    assert delete_response.status_code == 200
