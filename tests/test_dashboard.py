import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_overview(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200

    data = response.json()
    assert data["first_name"] == "there"

    # Flat summary fields are now nested under `summary`
    assert data["summary"]["company_count"] == 0
    assert data["summary"]["total_projects"] == 0
    assert data["summary"]["active_project_count"] == 0
    assert data["summary"]["maintenance_project_count"] == 0
    assert data["summary"]["completed_project_count"] == 0
    assert data["summary"]["archived_project_count"] == 0
    assert data["summary"]["total_tasks"] == 0

    # Vault data is now nested under `vault`
    assert data["vault"]["entry_count"] == 0
    assert data["vault"]["category_count"] == 0

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
    data = overview.json()

    # Summary fields live under `summary`
    assert data["summary"]["total_projects"] == 2
    assert data["summary"]["active_project_count"] == 1
    assert data["summary"]["completed_project_count"] == 1
    assert data["summary"]["total_tasks"] == 1

    assert data["status_counts"]["in_progress"] == 1

    # project_health replaces project_radial_data; only operational projects appear
    assert len(data["project_health"]) == 1
    assert data["project_health"][0]["name"] == "Active Platform"
    assert data["project_health"][0]["lifecycle_status"] == "active"

    assert completed_project_data["completed_at"] is not None


@pytest.mark.asyncio
async def test_dashboard_portfolio_insights_aggregates_unique_visitors(
    client: AsyncClient,
):
    await client.put(
        "/api/v1/profile/personal",
        json={"email": "owner@example.com"},
    )
    await client.put(
        "/api/v1/profile/public-settings",
        json={"is_public_profile_enabled": True},
    )
    profile_response = await client.get("/api/v1/profile")
    slug = profile_response.json()["data"]["public_slug"]

    first_visit = await client.post(
        f"/api/v1/public/portfolio/{slug}/view",
        json={"path": "/", "source": "portfolio-site", "visitor_id": "visitor-1"},
        headers={
            "x-forwarded-for": "203.0.113.10",
            "user-agent": "pytest-agent",
            "x-vercel-ip-country": "PH",
            "x-vercel-ip-country-region": "Metro Manila",
            "x-vercel-ip-city": "Pasig",
        },
    )
    assert first_visit.status_code == 201

    second_visit = await client.post(
        f"/api/v1/public/portfolio/{slug}/view",
        json={
            "path": "/projects",
            "source": "portfolio-site",
            "visitor_id": "visitor-1",
        },
        headers={
            "x-forwarded-for": "203.0.113.10",
            "user-agent": "pytest-agent",
            "x-vercel-ip-country": "PH",
            "x-vercel-ip-country-region": "Metro Manila",
            "x-vercel-ip-city": "Pasig",
        },
    )
    assert second_visit.status_code == 201

    third_visit = await client.post(
        f"/api/v1/public/portfolio/{slug}/view",
        json={"path": "/", "source": "direct", "visitor_id": "visitor-2"},
        headers={
            "x-forwarded-for": "203.0.113.11",
            "user-agent": "pytest-agent-2",
            "x-vercel-ip-country": "US",
            "x-vercel-ip-country-region": "California",
            "x-vercel-ip-city": "San Francisco",
        },
    )
    assert third_visit.status_code == 201

    response = await client.get("/api/v1/dashboard/portfolio-insights")
    assert response.status_code == 200

    data = response.json()
    assert data["pagination"] == {
        "page": 1,
        "page_size": 10,
        "total_items": 2,
        "total_pages": 1,
        "has_previous_page": False,
        "has_next_page": False,
    }
    assert data["items"][0]["visitor_id"] == "visitor-2"
    assert data["items"][0]["ip_address"] == "203.0.113.11"
    assert data["items"][1]["visitor_id"] == "visitor-1"
    assert data["items"][1]["visit_count"] == 2
    assert data["items"][1]["ip_address"] == "203.0.113.10"
    assert data["items"][1]["last_path"] == "/projects"


@pytest.mark.asyncio
async def test_dashboard_portfolio_insights_is_paginated(
    client: AsyncClient,
):
    await client.put(
        "/api/v1/profile/personal",
        json={"email": "owner@example.com"},
    )
    await client.put(
        "/api/v1/profile/public-settings",
        json={"is_public_profile_enabled": True},
    )
    profile_response = await client.get("/api/v1/profile")
    slug = profile_response.json()["data"]["public_slug"]

    for index in range(3):
        visit = await client.post(
            f"/api/v1/public/portfolio/{slug}/view",
            json={
                "path": f"/page-{index}",
                "source": "portfolio-site",
                "visitor_id": f"visitor-{index}",
            },
            headers={
                "x-forwarded-for": f"203.0.113.{30 + index}",
                "user-agent": f"pytest-agent-{index}",
            },
        )
        assert visit.status_code == 201

    response = await client.get(
        "/api/v1/dashboard/portfolio-insights",
        params={"page": 2, "page_size": 2},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["pagination"] == {
        "page": 2,
        "page_size": 2,
        "total_items": 3,
        "total_pages": 2,
        "has_previous_page": True,
        "has_next_page": False,
    }
    assert len(data["items"]) == 1
    assert data["items"][0]["visitor_id"] == "visitor-0"


@pytest.mark.asyncio
async def test_dashboard_can_decrement_portfolio_visitor_by_visitor_id_and_ip(
    client: AsyncClient,
):
    await client.put(
        "/api/v1/profile/personal",
        json={"email": "owner@example.com"},
    )
    await client.put(
        "/api/v1/profile/public-settings",
        json={"is_public_profile_enabled": True},
    )
    profile_response = await client.get("/api/v1/profile")
    slug = profile_response.json()["data"]["public_slug"]

    first_visit = await client.post(
        f"/api/v1/public/portfolio/{slug}/view",
        json={"path": "/", "source": "portfolio-site", "visitor_id": "visitor-delete"},
        headers={
            "x-forwarded-for": "203.0.113.20",
            "user-agent": "pytest-agent",
        },
    )
    assert first_visit.status_code == 201

    second_visit = await client.post(
        f"/api/v1/public/portfolio/{slug}/view",
        json={"path": "/projects", "source": "portfolio-site", "visitor_id": "visitor-delete"},
        headers={
            "x-forwarded-for": "203.0.113.20",
            "user-agent": "pytest-agent",
        },
    )
    assert second_visit.status_code == 201

    decrement_response = await client.post(
        "/api/v1/dashboard/portfolio-insights/visitors/visitor-delete/decrement",
        params={"ip_address": "203.0.113.20"},
    )
    assert decrement_response.status_code == 200
    assert decrement_response.json()["message"] == "Visit count decremented"

    insights_response = await client.get("/api/v1/dashboard/portfolio-insights")
    assert insights_response.status_code == 200
    insights_data = insights_response.json()
    assert insights_data["items"][0]["visitor_id"] == "visitor-delete"
    assert insights_data["items"][0]["visit_count"] == 1

    final_decrement_response = await client.post(
        "/api/v1/dashboard/portfolio-insights/visitors/visitor-delete/decrement",
        params={"ip_address": "203.0.113.20"},
    )
    assert final_decrement_response.status_code == 200

    final_insights_response = await client.get("/api/v1/dashboard/portfolio-insights")
    assert final_insights_response.status_code == 200
    assert final_insights_response.json()["items"] == []
