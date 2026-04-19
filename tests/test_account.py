import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.auth import firebase
from app.config import settings
from app.models import (
    EducationEntry,
    PortfolioVisitor,
    Profile,
    Project,
    Skill,
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
    shared_skill = Skill(name="Shared Skill")
    orphan_profile_skill = Skill(name="Orphan Profile Skill")
    orphan_project_skill = Skill(name="Orphan Project Skill")
    orphan_resume_skill = Skill(name="Orphan Resume Skill")
    orphan_resume_project_skill = Skill(name="Orphan Resume Project Skill")

    profile = Profile(
        user_id=test_user.id,
        name="Test User",
        avatar_url=f"{test_user.id}/avatar.jpg",
        resume_url=f"{test_user.id}/resume.pdf",
        skills=[shared_skill, orphan_profile_skill],
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
        tech_stack=[shared_skill, orphan_project_skill],
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
    resume = Resume(
        user_id=test_user.id,
        template="classic",
        name="Resume",
        skills=[shared_skill, orphan_resume_skill],
    )
    db_session.add(resume)
    await db_session.flush()
    db_session.add(ResumeExperience(resume_id=resume.id, title="Engineer", company="Acme", start_date="2024", end_date=""))
    db_session.add(ResumeEducation(resume_id=resume.id, degree="BSIT", school="ICCT", years="2019-2023"))
    resume_project = ResumeProject(
        resume_id=resume.id,
        name="Portfolio",
        tech_stack=[shared_skill, orphan_resume_project_skill],
    )
    db_session.add(resume_project)
    await db_session.flush()
    db_session.add(ResumeLink(resume_id=resume.id, label="GitHub", url="https://example.com"))
    db_session.add(
        PortfolioVisitor(
            user_id=test_user.id,
            visitor_id="visitor-1",
            visit_count=1,
            first_visited_at=resume.created_at,
            last_visited_at=resume.created_at,
            last_path="/portfolio",
        )
    )
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
        (settings.supabase_certification_images_bucket, str(test_user.id)),
        (settings.supabase_project_images_bucket, str(test_user.id)),
        (settings.supabase_resume_files_bucket, str(test_user.id)),
    ]

    remaining_user = await db_session.scalar(
        select(User).where(User.id == test_user.id)
    )
    assert remaining_user is None

    remaining_skill_names = (
        await db_session.execute(select(Skill.name).order_by(Skill.name))
    ).scalars().all()
    assert remaining_skill_names == []

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
        PortfolioVisitor,
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
