import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.profile import CertificationEntry, EducationEntry, Profile, WorkExperience
from app.models.user import User
from app.services.storage_service import StorageService
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
async def test_work_experience_update_preserves_existing_image_when_not_provided(
    client: AsyncClient,
    db_session,
    test_user: User,
):
    bootstrap_response = await client.get("/api/v1/profile")
    assert bootstrap_response.status_code == 200

    profile = (
        await db_session.execute(select(Profile).where(Profile.user_id == test_user.id))
    ).scalar_one()

    entry = WorkExperience(
        profile_id=profile.id,
        title="Engineer",
        company="Test Co",
        start_date="2024-01-01",
        is_current=True,
        image_url="stored/company.png",
        sort_order=0,
    )
    db_session.add(entry)
    await db_session.commit()

    response = await client.put(
        f"/api/v1/profile/work-experience/{entry.id}",
        json={
            "title": "Senior Engineer",
            "company": "Test Co",
            "start_date": "2024-01-01",
            "is_current": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == "stored/company.png"

    await db_session.refresh(entry)
    assert entry.image_url == "stored/company.png"


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
async def test_work_experience_update_can_clear_existing_image_and_delete_storage_file(
    client: AsyncClient,
    db_session,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    deleted: list[tuple[str, str | None]] = []

    async def fake_delete_file(self, *, bucket: str, path: str | None):
        deleted.append((bucket, path))
        return None

    monkeypatch.setattr(StorageService, "delete_file", fake_delete_file)

    bootstrap_response = await client.get("/api/v1/profile")
    assert bootstrap_response.status_code == 200

    profile = (
        await db_session.execute(select(Profile).where(Profile.user_id == test_user.id))
    ).scalar_one()

    entry = WorkExperience(
        profile_id=profile.id,
        title="Engineer",
        company="Test Co",
        start_date="2024-01-01",
        is_current=True,
        image_url="stored/company.png",
        sort_order=0,
    )
    db_session.add(entry)
    await db_session.commit()

    response = await client.put(
        f"/api/v1/profile/work-experience/{entry.id}",
        json={
            "title": "Engineer",
            "company": "Test Co",
            "start_date": "2024-01-01",
            "is_current": True,
            "image_url": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["image_url"] is None

    await db_session.refresh(entry)
    assert entry.image_url is None
    assert deleted == [("company-images", "stored/company.png")]


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


@pytest.mark.asyncio
async def test_profile_entry_mutations_are_scoped_to_current_user(
    client: AsyncClient,
    db_session,
):
    other_user = User(firebase_uid="other-user", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    other_profile = Profile(user_id=other_user.id)
    db_session.add(other_profile)
    await db_session.flush()

    other_work = WorkExperience(
        profile_id=other_profile.id,
        title="Other Role",
        company="Other Co",
        start_date="01/01/2024",
        end_date=None,
        is_current=True,
        sort_order=0,
    )
    other_education = EducationEntry(
        profile_id=other_profile.id,
        degree="Other Degree",
        school="Other School",
        years="2020-2024",
        sort_order=0,
    )
    other_certification = CertificationEntry(
        profile_id=other_profile.id,
        name="Other Certification",
        issuer="Other Issuer",
        issued_at="2026-01-01",
        sort_order=0,
    )
    db_session.add_all([other_work, other_education, other_certification])
    await db_session.commit()

    work_update = await client.put(
        f"/api/v1/profile/work-experience/{other_work.id}",
        json={
            "title": "Hacked",
            "company": "Nope",
            "start_date": "01/01/2024",
            "is_current": True,
        },
    )
    education_delete = await client.delete(f"/api/v1/profile/education/{other_education.id}")
    certification_update = await client.put(
        f"/api/v1/profile/certifications/{other_certification.id}",
        json={
            "name": "Changed",
            "issuer": "Changed",
            "issued_at": "2026-01-01",
            "is_public": False,
        },
    )

    assert work_update.status_code == 404
    assert education_delete.status_code == 404
    assert certification_update.status_code == 404
