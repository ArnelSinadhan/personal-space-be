import pytest
from httpx import AsyncClient

from app.models.user import User
from app.services.profile_service import ProfileService


@pytest.mark.asyncio
async def test_get_profile_empty(client: AsyncClient):
    response = await client.get("/api/v1/profile")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["skills"] == []
    assert data["work_experience"] == []
    assert data["education"] == []
    assert data["certifications"] == []
    assert data["public_slug"] == "test"
    assert data["is_public_profile_enabled"] is False


@pytest.mark.asyncio
async def test_update_personal(client: AsyncClient):
    response = await client.put("/api/v1/profile/personal", json={
        "name": "Arnel Sinadhan",
        "email": "arnel@example.com",
        "role": "Software Engineer",
    })
    assert response.status_code == 200
    personal = response.json()["data"]["personal"]
    assert personal["name"] == "Arnel Sinadhan"
    assert personal["role"] == "Software Engineer"
    assert response.json()["data"]["public_slug"] == "arnel"


@pytest.mark.asyncio
async def test_update_about_and_skills(client: AsyncClient):
    response = await client.put("/api/v1/profile/about", json={
        "about": "Passionate engineer",
        "skills": ["React", "TypeScript", "FastAPI"],
    })
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["about"] == "Passionate engineer"
    assert set(data["skills"]) == {"React", "TypeScript", "FastAPI"}


@pytest.mark.asyncio
async def test_update_public_profile_settings(client: AsyncClient):
    await client.put(
        "/api/v1/profile/personal",
        json={"email": "public@example.com"},
    )
    response = await client.put(
        "/api/v1/profile/public-settings",
        json={"is_public_profile_enabled": True},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["public_slug"] == "public"
    assert data["is_public_profile_enabled"] is True


@pytest.mark.asyncio
async def test_work_experience_crud(client: AsyncClient):
    # Create
    response = await client.post("/api/v1/profile/work-experience", json={
        "title": "Software Engineer",
        "company": "Hipe Japan Inc",
        "start_date": "September 2024",
        "is_current": True,
    })
    assert response.status_code == 201
    entry_id = response.json()["id"]

    # Update
    response = await client.put(f"/api/v1/profile/work-experience/{entry_id}", json={
        "title": "Senior Software Engineer",
        "company": "Hipe Japan Inc",
        "start_date": "September 2024",
        "is_current": True,
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Senior Software Engineer"

    # Delete
    response = await client.delete(f"/api/v1/profile/work-experience/{entry_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_education_crud(client: AsyncClient):
    # Create
    response = await client.post("/api/v1/profile/education", json={
        "degree": "BS Computer Science",
        "school": "XYZ University",
        "years": "2017-2021",
    })
    assert response.status_code == 201
    entry_id = response.json()["id"]

    # Delete
    response = await client.delete(f"/api/v1/profile/education/{entry_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_certification_crud(client: AsyncClient):
    response = await client.post(
        "/api/v1/profile/certifications",
        json={
            "name": "AWS Certified Cloud Practitioner",
            "issuer": "Amazon Web Services",
            "issued_at": "2026-03-15",
            "expires_at": "2029-03-15",
            "credential_id": "AWS-123456",
            "credential_url": "https://www.credly.com/badges/example",
            "is_public": True,
        },
    )
    assert response.status_code == 201
    entry_id = response.json()["id"]
    assert response.json()["issuer"] == "Amazon Web Services"

    update_response = await client.put(
        f"/api/v1/profile/certifications/{entry_id}",
        json={
            "name": "AWS Certified Cloud Practitioner",
            "issuer": "AWS",
            "issued_at": "2026-03-15",
            "expires_at": "2029-03-15",
            "credential_id": "AWS-654321",
            "credential_url": "https://www.credly.com/badges/example-2",
            "is_public": False,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["issuer"] == "AWS"
    assert update_response.json()["is_public"] is False

    profile_response = await client.get("/api/v1/profile")
    assert profile_response.status_code == 200
    assert len(profile_response.json()["data"]["certifications"]) == 1

    delete_response = await client.delete(f"/api/v1/profile/certifications/{entry_id}")
    assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_social_links_update(client: AsyncClient):
    response = await client.put("/api/v1/profile/social-links", json={
        "links": [
            {"label": "GitHub", "url": "https://github.com/arnel"},
            {"label": "LinkedIn", "url": "https://linkedin.com/in/arnel"},
        ],
    })
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["social_links"]) == 2


@pytest.mark.asyncio
async def test_public_slug_stays_unique_between_users(
    db_session,
    test_user: User,
):
    second_user = User(
        firebase_uid="second-user",
        email="test@other.com",
    )
    db_session.add(second_user)
    await db_session.flush()

    service = ProfileService(db_session)

    first_profile = await service.get_profile(test_user.id)
    second_profile = await service.get_profile(second_user.id)

    assert first_profile.public_slug == "test"
    assert second_profile.public_slug == "test-2"
