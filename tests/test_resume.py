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
async def test_save_resume_with_professional_template(client: AsyncClient):
    response = await client.put("/api/v1/resume", json={
        "template": "professional",
        "personal": {"name": "Template Test"},
    })
    assert response.status_code == 200
    assert response.json()["data"]["template"] == "professional"
