import pytest
from httpx import AsyncClient

from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_upload_profile_image_persists_path_and_returns_signed_url(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_upload_file(self, *, bucket: str, path: str, content: bytes, content_type: str):
        return path

    async def fake_delete_file(self, *, bucket: str, path: str | None):
        return None

    async def fake_delete_files(self, *, bucket: str, paths: list[str]):
        return None

    async def fake_list_files(self, *, bucket: str, prefix: str):
        return []

    async def fake_resolve_profile_url(self, path: str | None):
        return f"https://signed.example/{path}" if path else None

    monkeypatch.setattr(StorageService, "upload_file", fake_upload_file)
    monkeypatch.setattr(StorageService, "delete_file", fake_delete_file)
    monkeypatch.setattr(StorageService, "delete_files", fake_delete_files)
    monkeypatch.setattr(StorageService, "list_files", fake_list_files)
    monkeypatch.setattr(StorageService, "resolve_profile_url", fake_resolve_profile_url)

    response = await client.post(
        "/api/v1/uploads/profile-image",
        files={"file": ("avatar.png", b"avatar-bytes", "image/png")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["path"].endswith("/avatar.png")
    assert data["url"] == f"https://signed.example/{data['path']}"

    profile_response = await client.get("/api/v1/profile")
    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["personal"]["avatar"] == data["url"]


@pytest.mark.asyncio
async def test_upload_profile_image_reuses_same_path_for_same_extension(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    deleted_path_batches: list[list[str]] = []

    async def fake_upload_file(self, *, bucket: str, path: str, content: bytes, content_type: str):
        return path

    async def fake_delete_file(self, *, bucket: str, path: str | None):
        return None

    async def fake_delete_files(self, *, bucket: str, paths: list[str]):
        deleted_path_batches.append(paths)
        return None

    async def fake_resolve_profile_url(self, path: str | None):
        return f"https://signed.example/{path}" if path else None

    listed_paths: list[str] = []

    async def fake_list_files(self, *, bucket: str, prefix: str):
        return [path for path in listed_paths if path.startswith(prefix)]

    monkeypatch.setattr(StorageService, "upload_file", fake_upload_file)
    monkeypatch.setattr(StorageService, "delete_file", fake_delete_file)
    monkeypatch.setattr(StorageService, "delete_files", fake_delete_files)
    monkeypatch.setattr(StorageService, "list_files", fake_list_files)
    monkeypatch.setattr(StorageService, "resolve_profile_url", fake_resolve_profile_url)

    first = await client.post(
        "/api/v1/uploads/profile-image",
        files={"file": ("avatar.png", b"avatar-bytes", "image/png")},
    )
    second = await client.post(
        "/api/v1/uploads/profile-image",
        files={"file": ("avatar.png", b"avatar-new", "image/png")},
    )

    assert first.status_code == 201
    listed_paths.append(first.json()["path"])
    assert second.status_code == 201
    assert first.json()["path"] == second.json()["path"]
    assert deleted_path_batches == [[], []]


@pytest.mark.asyncio
async def test_upload_profile_image_deletes_previous_file_when_extension_changes(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    deleted_path_batches: list[list[str]] = []

    async def fake_upload_file(self, *, bucket: str, path: str, content: bytes, content_type: str):
        return path

    async def fake_delete_file(self, *, bucket: str, path: str | None):
        return None

    async def fake_delete_files(self, *, bucket: str, paths: list[str]):
        deleted_path_batches.append(paths)
        return None

    async def fake_resolve_profile_url(self, path: str | None):
        return f"https://signed.example/{path}" if path else None

    listed_paths: list[str] = []

    async def fake_list_files(self, *, bucket: str, prefix: str):
        return [path for path in listed_paths if path.startswith(prefix)]

    monkeypatch.setattr(StorageService, "upload_file", fake_upload_file)
    monkeypatch.setattr(StorageService, "delete_file", fake_delete_file)
    monkeypatch.setattr(StorageService, "delete_files", fake_delete_files)
    monkeypatch.setattr(StorageService, "list_files", fake_list_files)
    monkeypatch.setattr(StorageService, "resolve_profile_url", fake_resolve_profile_url)

    first = await client.post(
        "/api/v1/uploads/profile-image",
        files={"file": ("avatar.png", b"avatar-bytes", "image/png")},
    )
    assert first.status_code == 201
    listed_paths.append(first.json()["path"])
    second = await client.post(
        "/api/v1/uploads/profile-image",
        files={"file": ("avatar.jpg", b"avatar-new", "image/jpeg")},
    )

    assert second.status_code == 201
    assert first.json()["path"].endswith("/avatar.png")
    assert second.json()["path"].endswith("/avatar.jpg")
    assert deleted_path_batches == [[], [first.json()["path"]]]


@pytest.mark.asyncio
async def test_upload_company_image_updates_workspace(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_upload_file(self, *, bucket: str, path: str, content: bytes, content_type: str):
        return path

    async def fake_delete_file(self, *, bucket: str, path: str | None):
        return None

    async def fake_delete_files(self, *, bucket: str, paths: list[str]):
        return None

    async def fake_list_files(self, *, bucket: str, prefix: str):
        return []

    async def fake_resolve_company_url(self, path: str | None):
        return f"https://signed.example/{path}" if path else None

    monkeypatch.setattr(StorageService, "upload_file", fake_upload_file)
    monkeypatch.setattr(StorageService, "delete_file", fake_delete_file)
    monkeypatch.setattr(StorageService, "delete_files", fake_delete_files)
    monkeypatch.setattr(StorageService, "list_files", fake_list_files)
    monkeypatch.setattr(StorageService, "resolve_company_url", fake_resolve_company_url)

    workspace = await client.post(
        "/api/v1/profile/work-experience",
        json={
            "title": "Engineer",
            "company": "Test Co",
            "start_date": "2024",
        },
    )
    workspace_id = workspace.json()["id"]

    response = await client.post(
        "/api/v1/uploads/company-image",
        data={"work_experience_id": workspace_id},
        files={"file": ("company.png", b"company-bytes", "image/png")},
    )
    assert response.status_code == 201
    upload_data = response.json()

    workspaces = await client.get("/api/v1/work-experiences")
    assert workspaces.status_code == 200
    matching = next(
        item for item in workspaces.json()["data"] if item["id"] == workspace_id
    )
    assert matching["image_url"] == upload_data["url"]


@pytest.mark.asyncio
async def test_upload_resume_updates_profile(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_upload_file(self, *, bucket: str, path: str, content: bytes, content_type: str):
        return path

    async def fake_delete_file(self, *, bucket: str, path: str | None):
        return None

    async def fake_delete_files(self, *, bucket: str, paths: list[str]):
        return None

    async def fake_list_files(self, *, bucket: str, prefix: str):
        return []

    async def fake_resolve_resume_url(self, path: str | None):
        return f"https://signed.example/{path}" if path else None

    monkeypatch.setattr(StorageService, "upload_file", fake_upload_file)
    monkeypatch.setattr(StorageService, "delete_file", fake_delete_file)
    monkeypatch.setattr(StorageService, "delete_files", fake_delete_files)
    monkeypatch.setattr(StorageService, "list_files", fake_list_files)
    monkeypatch.setattr(StorageService, "resolve_resume_url", fake_resolve_resume_url)

    response = await client.post(
        "/api/v1/uploads/resume",
        files={"file": ("resume.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 201
    upload_data = response.json()
    assert upload_data["path"].endswith("/resume.pdf")
    assert upload_data["url"] == f"https://signed.example/{upload_data['path']}"
