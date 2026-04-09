import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.profile import Profile


@pytest.mark.asyncio
async def test_public_portfolio_returns_aggregated_data(
    client: AsyncClient,
    db_session,
):
    await client.put(
        "/api/v1/profile/personal",
        json={
            "name": "Portfolio Owner",
            "email": "owner@example.com",
            "phone": "123456789",
            "address": "Manila",
            "role": "Full Stack Developer",
        },
    )
    await client.put(
        "/api/v1/profile/about",
        json={
            "about": "Building useful products.",
            "skills": ["Next.js", "FastAPI", "TypeScript"],
        },
    )
    await client.put(
        "/api/v1/profile/social-links",
        json={
            "links": [
                {"label": "GitHub", "url": "https://github.com/example"},
                {"label": "LinkedIn", "url": "https://linkedin.com/in/example"},
            ]
        },
    )
    await client.post(
        "/api/v1/profile/education",
        json={
            "degree": "BS Computer Science",
            "school": "Example University",
            "years": "2018 - 2022",
        },
    )
    work_experience = await client.post(
        "/api/v1/profile/work-experience",
        json={
            "title": "Software Engineer",
            "company": "Example Co",
            "start_date": "2022",
            "is_current": True,
        },
    )
    workspace_id = work_experience.json()["id"]
    await client.post(
        f"/api/v1/work-experiences/{workspace_id}/projects",
        json={
            "name": "Portfolio Project",
            "description": "Public portfolio project",
            "github_url": "https://github.com/example/portfolio-project",
            "live_url": "https://portfolio-project.example.com",
            "tech_stack": ["Next.js", "FastAPI"],
            "is_public": True,
        },
    )

    profile = await db_session.scalar(select(Profile))
    assert profile is not None
    profile.is_public_profile_enabled = True
    await db_session.commit()

    response = await client.get("/api/v1/public/portfolio/owner")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["profile"]["name"] == "Portfolio Owner"
    assert data["profile"]["role"] == "Full Stack Developer"
    assert len(data["profile"]["social_links"]) == 2
    assert len(data["education"]) == 1
    assert len(data["work_experience"]) == 1
    assert len(data["projects"]) == 1
    assert data["projects"][0]["github_url"] == "https://github.com/example/portfolio-project"
    assert data["projects"][0]["live_url"] == "https://portfolio-project.example.com"
    assert data["stats"]["public_project_count"] == 1
    assert data["stats"]["company_count"] == 1


@pytest.mark.asyncio
async def test_public_portfolio_view_is_recorded(client: AsyncClient, db_session):
    await client.put(
        "/api/v1/profile/personal",
        json={"email": "owner@example.com"},
    )

    profile = await db_session.scalar(select(Profile))
    assert profile is not None
    profile.is_public_profile_enabled = True
    await db_session.commit()

    response = await client.post(
        "/api/v1/public/portfolio/owner/view",
        json={"path": "/", "source": "portfolio-site"},
        headers={
            "referer": "https://portfolio.example.com",
            "user-agent": "pytest-agent",
            "x-forwarded-for": "203.0.113.10",
        },
    )
    assert response.status_code == 201

    portfolio_response = await client.get("/api/v1/public/portfolio/owner")
    assert portfolio_response.status_code == 200
    assert portfolio_response.json()["data"]["stats"]["total_views"] == 1


@pytest.mark.asyncio
async def test_public_portfolio_returns_404_for_unknown_slug(client: AsyncClient):
    response = await client.get("/api/v1/public/portfolio/missing-user")
    assert response.status_code == 404
    assert response.json()["detail"] == "Portfolio not found"


@pytest.mark.asyncio
async def test_public_portfolio_returns_404_when_portfolio_is_not_public(
    client: AsyncClient,
):
    await client.put(
        "/api/v1/profile/personal",
        json={"email": "unpublished@example.com"},
    )

    response = await client.get("/api/v1/public/portfolio/unpublished")
    assert response.status_code == 404
    assert response.json()["detail"] == "Portfolio not found"
