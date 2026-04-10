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

    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={
            "name": "Client Management System",
            "description": "Updated internal tool",
            "github_url": "https://github.com/example/cms-v2",
            "live_url": "https://cms-v2.example.com",
            "tech_stack": ["Next.js", "TypeScript", "FastAPI", "PostgreSQL"],
            "is_public": True,
        },
    )
    assert response.status_code == 200
    updated_project = response.json()["data"]
    assert updated_project["github_url"] == "https://github.com/example/cms-v2"
    assert updated_project["live_url"] == "https://cms-v2.example.com"
    assert updated_project["is_public"] is True

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
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["is_featured"] is False

    delete_response = await client.delete(f"/api/v1/personal-projects/{project_id}")
    assert delete_response.status_code == 200
