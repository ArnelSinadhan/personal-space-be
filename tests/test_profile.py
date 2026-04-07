import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_profile_empty(client: AsyncClient):
    response = await client.get("/api/v1/profile")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["skills"] == []
    assert data["work_experience"] == []
    assert data["education"] == []


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
async def test_social_links_update(client: AsyncClient):
    response = await client.put("/api/v1/profile/social-links", json={
        "links": [
            {"label": "GitHub", "url": "https://github.com/arnel"},
            {"label": "LinkedIn", "url": "https://linkedin.com/in/arnel"},
        ],
        "resume_url": "/resume.pdf",
    })
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["social_links"]) == 2
    assert data["resume_url"] == "/resume.pdf"
