import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.auth import firebase
from app.config import settings
from app.models import (
    EducationEntry,
    PortfolioView,
    Profile,
    Project,
    Resume,
    ResumeEducation,
    ResumeExperience,
    ResumeLink,
    ResumeProject,
    SocialLink,
    Todo,
    User,
    VaultCategory,
    VaultEntry,
    VaultPin,
    WorkExperience,
)
from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_delete_account_removes_firebase_storage_and_database_records(
    client: AsyncClient,
    db_session,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    profile = Profile(
        user_id=test_user.id,
        name="Test User",
        avatar_url=f"{test_user.id}/avatar.jpg",
        resume_url=f"{test_user.id}/resume.pdf",
    )
    db_session.add(profile)
    await db_session.flush()

    work_experience = WorkExperience(
        profile_id=profile.id,
        title="Engineer",
        company="Acme",
        start_date="2024",
        image_url=f"{test_user.id}/company-id/company.webp",
    )
    db_session.add(work_experience)
    await db_session.flush()

    project = Project(
        work_experience_id=work_experience.id,
        name="Project",
        image_url=f"{test_user.id}/project-id/project.png",
    )
    db_session.add(project)
    await db_session.flush()

    db_session.add(Todo(project_id=project.id, title="Todo"))
    db_session.add(EducationEntry(profile_id=profile.id, degree="BSIT", school="ICCT", years="2019-2023"))
    db_session.add(SocialLink(profile_id=profile.id, label="GitHub", url="https://example.com"))
    db_session.add(VaultPin(user_id=test_user.id, pin_hash="hash"))
    category = VaultCategory(user_id=test_user.id, name="General", icon_name="lock")
    db_session.add(category)
    await db_session.flush()
    db_session.add(VaultEntry(user_id=test_user.id, category_id=category.id, title="Vault", username="user", encrypted_password="secret"))
    resume = Resume(user_id=test_user.id, template="classic", name="Resume")
    db_session.add(resume)
    await db_session.flush()
    db_session.add(ResumeExperience(resume_id=resume.id, title="Engineer", company="Acme", start_date="2024", end_date=""))
    db_session.add(ResumeEducation(resume_id=resume.id, degree="BSIT", school="ICCT", years="2019-2023"))
    db_session.add(ResumeProject(resume_id=resume.id, name="Portfolio"))
    db_session.add(ResumeLink(resume_id=resume.id, label="GitHub", url="https://example.com"))
    db_session.add(PortfolioView(user_id=test_user.id, path="/portfolio"))
    await db_session.commit()

    deleted_prefixes: list[tuple[str, str]] = []
    deleted_firebase_uids: list[str] = []

    async def fake_delete_prefix(self, *, bucket: str, prefix: str | None):
        if prefix:
            deleted_prefixes.append((bucket, prefix))

    def fake_delete_firebase_user(uid: str):
        deleted_firebase_uids.append(uid)

    monkeypatch.setattr(StorageService, "delete_prefix", fake_delete_prefix)
    monkeypatch.setattr(firebase, "delete_firebase_user", fake_delete_firebase_user)

    response = await client.delete("/api/v1/account")

    assert response.status_code == 200
    assert response.json() == {"message": "Account deleted"}
    assert deleted_firebase_uids == [test_user.firebase_uid]
    assert deleted_prefixes == [
        (settings.supabase_profile_images_bucket, str(test_user.id)),
        (settings.supabase_company_images_bucket, str(test_user.id)),
        (settings.supabase_project_images_bucket, str(test_user.id)),
        (settings.supabase_resume_files_bucket, str(test_user.id)),
    ]

    remaining_user = await db_session.scalar(
        select(User).where(User.id == test_user.id)
    )
    assert remaining_user is None

    for model in (
        Profile,
        WorkExperience,
        Project,
        Todo,
        EducationEntry,
        SocialLink,
        VaultPin,
        VaultCategory,
        VaultEntry,
        Resume,
        ResumeExperience,
        ResumeEducation,
        ResumeProject,
        ResumeLink,
        PortfolioView,
    ):
        result = await db_session.execute(select(model))
        assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_update_account_password_updates_firebase_user(
    client: AsyncClient,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    updated_passwords: list[tuple[str, str]] = []

    def fake_update_firebase_user_password(uid: str, password: str):
        updated_passwords.append((uid, password))

    monkeypatch.setattr(firebase, "update_firebase_user_password", fake_update_firebase_user_password)

    response = await client.put(
        "/api/v1/account/password",
        json={"new_password": "new-password-123"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Password updated"}
    assert updated_passwords == [(test_user.firebase_uid, "new-password-123")]
