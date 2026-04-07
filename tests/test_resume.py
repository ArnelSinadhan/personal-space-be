import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_resume_empty(client: AsyncClient):
    response = await client.get("/api/v1/resume")
    assert response.status_code == 200
    assert response.json()["data"] is None


@pytest.mark.asyncio
async def test_save_and_get_resume(client: AsyncClient):
    payload = {
        "template": "classic",
        "personal": {
            "name": "Arnel Sinadhan",
            "role": "Software Engineer",
            "email": "arnel@example.com",
            "phone": "09150498926",
            "address": "Antipolo City",
            "summary": "Passionate engineer",
        },
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Hipe Japan Inc",
                "start_date": "September 2024",
                "end_date": "Present",
                "is_current": True,
                "description": "Building internal tools",
            }
        ],
        "education": [
            {"degree": "BS Computer Science", "school": "XYZ University", "years": "2017-2021"}
        ],
        "skills": ["React", "TypeScript", "FastAPI"],
        "projects": [
            {
                "name": "Client Management System",
                "description": "Internal tool",
                "tech_stack": ["Next.js", "TypeScript"],
            }
        ],
        "links": [
            {"label": "GitHub", "url": "https://github.com/arnel"},
        ],
    }

    # Save
    response = await client.put("/api/v1/resume", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["template"] == "classic"
    assert data["personal"]["name"] == "Arnel Sinadhan"
    assert len(data["experience"]) == 1
    assert len(data["skills"]) == 3

    # Get
    response = await client.get("/api/v1/resume")
    assert response.status_code == 200
    assert response.json()["data"] is not None


@pytest.mark.asyncio
async def test_change_template(client: AsyncClient):
    # Create resume first
    await client.put("/api/v1/resume", json={
        "template": "classic",
        "personal": {"name": "Test"},
    })

    # Change template
    response = await client.patch("/api/v1/resume/template", json={
        "template": "modern",
    })
    assert response.status_code == 200
    assert response.json()["data"]["template"] == "modern"


@pytest.mark.asyncio
async def test_generate_from_profile(client: AsyncClient):
    # Setup profile data first
    await client.put("/api/v1/profile/personal", json={
        "name": "Arnel Sinadhan",
        "role": "Software Engineer",
        "email": "arnel@example.com",
    })
    await client.put("/api/v1/profile/about", json={
        "about": "Passionate engineer",
        "skills": ["React", "TypeScript"],
    })

    # Generate
    response = await client.post("/api/v1/resume/generate")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["personal"]["name"] == "Arnel Sinadhan"
    assert "React" in data["skills"]


@pytest.mark.asyncio
async def test_delete_resume(client: AsyncClient):
    # Create then delete
    await client.put("/api/v1/resume", json={
        "template": "minimal",
        "personal": {"name": "Delete Me"},
    })
    response = await client.delete("/api/v1/resume")
    assert response.status_code == 200

    # Confirm gone
    response = await client.get("/api/v1/resume")
    assert response.json()["data"] is None
