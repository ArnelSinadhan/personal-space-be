import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.config import settings
from app.models.profile import Profile
from app.models.project import PersonalProject


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
    await client.post(
        "/api/v1/profile/certifications",
        json={
            "name": "AWS Certified Cloud Practitioner",
            "issuer": "Amazon Web Services",
            "issued_at": "2026-03-15",
            "credential_id": "AWS-123456",
            "credential_url": "https://www.credly.com/badges/example",
            "is_public": True,
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
            "lifecycle_status": "completed",
            "outcome_summary": "Delivered successfully and handed off.",
        },
    )

    profile = await db_session.scalar(select(Profile))
    assert profile is not None
    profile.personal_projects.append(
        PersonalProject(
            name="Personal Finance Tracker",
            description="A budgeting app for personal expense tracking.",
            github_url="https://github.com/example/personal-finance-tracker",
            live_url="https://finance-tracker.example.com",
            is_public=True,
            is_featured=True,
        )
    )
    profile.is_public_profile_enabled = True
    await db_session.commit()

    response = await client.get("/api/v1/public/portfolio/owner")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["profile"]["name"] == "Portfolio Owner"
    assert data["profile"]["role"] == "Full Stack Developer"
    assert data["profile"]["email"] == "owner@example.com"
    assert data["profile"]["phone"] == "123456789"
    assert data["profile"]["address"] == "Manila"
    assert len(data["profile"]["social_links"]) == 2
    assert len(data["education"]) == 1
    assert len(data["certifications"]) == 1
    assert len(data["work_experience"]) == 1
    assert len(data["work_experience"][0]["projects"]) == 1
    assert len(data["personal_projects"]) == 1
    assert (
        data["work_experience"][0]["projects"][0]["github_url"]
        == "https://github.com/example/portfolio-project"
    )
    assert (
        data["work_experience"][0]["projects"][0]["live_url"]
        == "https://portfolio-project.example.com"
    )
    assert data["work_experience"][0]["projects"][0]["lifecycle_status"] == "completed"
    assert data["work_experience"][0]["projects"][0]["completed_at"] is not None
    assert (
        data["work_experience"][0]["projects"][0]["outcome_summary"]
        == "Delivered successfully and handed off."
    )
    assert (
        data["personal_projects"][0]["github_url"]
        == "https://github.com/example/personal-finance-tracker"
    )
    assert data["personal_projects"][0]["is_featured"] is True
    assert data["personal_projects"][0]["id"] is not None
    assert data["certifications"][0]["issuer"] == "Amazon Web Services"
    assert data["stats"]["public_project_count"] == 2
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
        json={"path": "/", "source": "portfolio-site", "visitor_id": "visitor-123"},
        headers={
            "referer": "https://portfolio.example.com",
            "user-agent": "pytest-agent",
            "x-forwarded-for": "203.0.113.10",
            "x-vercel-ip-country": "PH",
            "x-vercel-ip-country-region": "Metro Manila",
            "x-vercel-ip-city": "Pasig",
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


@pytest.mark.asyncio
async def test_public_project_testimonial_submission_requires_approval_before_showing(
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
    project = await client.post(
        f"/api/v1/work-experiences/{workspace_id}/projects",
        json={
            "name": "Portfolio Project",
            "description": "Public portfolio project",
            "tech_stack": ["Next.js", "FastAPI"],
            "is_public": True,
        },
    )
    project_id = project.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/public/portfolio/{slug}/projects/{project_id}/testimonial",
        json={
            "name": "Jane Reviewer",
            "role": "Product Manager",
            "message": "Arnel shipped the portal reliably, communicated clearly, and delivered polished product work end to end.",
        },
    )
    assert response.status_code == 201

    portfolio_response = await client.get(f"/api/v1/public/portfolio/{slug}")
    assert portfolio_response.status_code == 200
    assert (
        portfolio_response.json()["data"]["work_experience"][0]["projects"][0]["testimonial"]
        is None
    )

    approve_response = await client.put(
        f"/api/v1/projects/{project_id}/testimonial",
        json={"status": "approved"},
    )
    assert approve_response.status_code == 200

    portfolio_response = await client.get(f"/api/v1/public/portfolio/{slug}")
    assert portfolio_response.status_code == 200
    assert (
        portfolio_response.json()["data"]["work_experience"][0]["projects"][0]["testimonial"]["name"]
        == "Jane Reviewer"
    )


@pytest.mark.asyncio
async def test_public_project_testimonial_rate_limit_is_enforced(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "public_testimonial_rate_limit_max_attempts", 1)

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
    project = await client.post(
        f"/api/v1/work-experiences/{workspace_id}/projects",
        json={
            "name": "Portfolio Project",
            "description": "Public portfolio project",
            "tech_stack": ["Next.js", "FastAPI"],
            "is_public": True,
        },
    )
    project_id = project.json()["data"]["id"]

    payload = {
        "name": "Jane Reviewer",
        "role": "Product Manager",
        "message": "Arnel shipped the portal reliably, communicated clearly, and delivered polished product work end to end.",
    }

    first = await client.post(
        f"/api/v1/public/portfolio/{slug}/projects/{project_id}/testimonial",
        json=payload,
        headers={"x-forwarded-for": "203.0.113.10"},
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/v1/public/portfolio/{slug}/projects/{project_id}/testimonial",
        json=payload,
        headers={"x-forwarded-for": "203.0.113.10"},
    )
    assert second.status_code == 429
    assert "Too many testimonial submissions" in second.json()["detail"]


@pytest.mark.asyncio
async def test_public_project_testimonial_can_require_captcha(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "public_testimonial_captcha_secret", "required-secret")

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
    project = await client.post(
        f"/api/v1/work-experiences/{workspace_id}/projects",
        json={
            "name": "Portfolio Project",
            "description": "Public portfolio project",
            "tech_stack": ["Next.js", "FastAPI"],
            "is_public": True,
        },
    )
    project_id = project.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/public/portfolio/{slug}/projects/{project_id}/testimonial",
        json={
            "name": "Jane Reviewer",
            "role": "Product Manager",
            "message": "Arnel shipped the portal reliably, communicated clearly, and delivered polished product work end to end.",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Captcha verification is required."
