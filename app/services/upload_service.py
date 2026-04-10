from __future__ import annotations

import posixpath
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.repositories.profile_repo import ProfileRepository, WorkExperienceRepository
from app.repositories.project_repo import PersonalProjectRepository, ProjectRepository
from app.services.storage_service import StorageService


class UploadService:
    IMAGE_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/svg+xml",
        "image/jpg",
    }
    RESUME_CONTENT_TYPES = {"application/pdf"}

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.work_repo = WorkExperienceRepository(db)
        self.project_repo = ProjectRepository(db)
        self.personal_project_repo = PersonalProjectRepository(db)
        self.storage = StorageService()

    async def _delete_previous_if_replaced(
        self,
        *,
        bucket: str,
        previous_path: str | None,
        current_path: str,
    ) -> None:
        if not previous_path or previous_path == current_path:
            return

        await self.storage.delete_file(
            bucket=bucket,
            path=previous_path,
        )

    async def _cleanup_resource_folder(
        self,
        *,
        bucket: str,
        current_path: str,
    ) -> None:
        prefix = posixpath.dirname(current_path)
        existing_paths = await self.storage.list_files(
            bucket=bucket,
            prefix=prefix,
        )
        stale_paths = [path for path in existing_paths if path != current_path]
        await self.storage.delete_files(bucket=bucket, paths=stale_paths)

    async def upload_profile_image(
        self,
        *,
        user_id: UUID,
        file: UploadFile,
    ) -> tuple[str, str | None]:
        content = await self._read_and_validate(
            file=file,
            allowed_content_types=self.IMAGE_CONTENT_TYPES,
            max_bytes=settings.max_image_upload_bytes,
            label="profile image",
        )
        profile = await self.profile_repo.get_or_create(user_id)
        previous_path = profile.avatar_url
        path = self.storage.build_object_path(
            owner_id=user_id,
            folder="avatar",
            filename=file.filename,
            content_type=file.content_type,
        )
        await self.storage.upload_file(
            bucket=settings.supabase_profile_images_bucket,
            path=path,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        profile.avatar_url = path
        await self.db.flush()
        await self._cleanup_resource_folder(
            bucket=settings.supabase_profile_images_bucket,
            current_path=path,
        )
        await self._delete_previous_if_replaced(
            bucket=settings.supabase_profile_images_bucket,
            previous_path=previous_path,
            current_path=path,
        )
        url = await self.storage.resolve_profile_url(path)
        return path, url

    async def upload_company_image(
        self,
        *,
        user_id: UUID,
        work_experience_id: UUID,
        file: UploadFile,
    ) -> tuple[str, str | None]:
        content = await self._read_and_validate(
            file=file,
            allowed_content_types=self.IMAGE_CONTENT_TYPES,
            max_bytes=settings.max_image_upload_bytes,
            label="company image",
        )
        workspace = await self.work_repo.get_by_id_for_user(work_experience_id, user_id)
        if workspace is None:
            raise ValueError("Work experience not found")

        previous_path = workspace.image_url
        path = self.storage.build_object_path(
            owner_id=user_id,
            related_id=work_experience_id,
            folder="company",
            filename=file.filename,
            content_type=file.content_type,
        )
        await self.storage.upload_file(
            bucket=settings.supabase_company_images_bucket,
            path=path,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        workspace.image_url = path
        await self.db.flush()
        await self._cleanup_resource_folder(
            bucket=settings.supabase_company_images_bucket,
            current_path=path,
        )
        await self._delete_previous_if_replaced(
            bucket=settings.supabase_company_images_bucket,
            previous_path=previous_path,
            current_path=path,
        )
        url = await self.storage.resolve_company_url(path)
        return path, url

    async def upload_project_image(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        file: UploadFile,
    ) -> tuple[str, str | None]:
        content = await self._read_and_validate(
            file=file,
            allowed_content_types=self.IMAGE_CONTENT_TYPES,
            max_bytes=settings.max_image_upload_bytes,
            label="project image",
        )
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Project not found")

        previous_path = project.image_url
        path = self.storage.build_object_path(
            owner_id=user_id,
            related_id=project_id,
            folder="project",
            filename=file.filename,
            content_type=file.content_type,
        )
        await self.storage.upload_file(
            bucket=settings.supabase_project_images_bucket,
            path=path,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        project.image_url = path
        await self.db.flush()
        await self._cleanup_resource_folder(
            bucket=settings.supabase_project_images_bucket,
            current_path=path,
        )
        await self._delete_previous_if_replaced(
            bucket=settings.supabase_project_images_bucket,
            previous_path=previous_path,
            current_path=path,
        )
        url = await self.storage.resolve_project_url(path)
        return path, url

    async def upload_personal_project_image(
        self,
        *,
        user_id: UUID,
        personal_project_id: UUID,
        file: UploadFile,
    ) -> tuple[str, str | None]:
        content = await self._read_and_validate(
            file=file,
            allowed_content_types=self.IMAGE_CONTENT_TYPES,
            max_bytes=settings.max_image_upload_bytes,
            label="personal project image",
        )
        project = await self.personal_project_repo.get_by_id_for_user(
            personal_project_id, user_id
        )
        if project is None:
            raise ValueError("Personal project not found")

        previous_path = project.image_url
        path = self.storage.build_object_path(
            owner_id=user_id,
            related_id=personal_project_id,
            folder="personal-project",
            filename=file.filename,
            content_type=file.content_type,
        )
        await self.storage.upload_file(
            bucket=settings.supabase_project_images_bucket,
            path=path,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        project.image_url = path
        await self.db.flush()
        await self._cleanup_resource_folder(
            bucket=settings.supabase_project_images_bucket,
            current_path=path,
        )
        await self._delete_previous_if_replaced(
            bucket=settings.supabase_project_images_bucket,
            previous_path=previous_path,
            current_path=path,
        )
        url = await self.storage.resolve_project_url(path)
        return path, url

    async def upload_resume(
        self,
        *,
        user_id: UUID,
        file: UploadFile,
    ) -> tuple[str, str | None]:
        content = await self._read_and_validate(
            file=file,
            allowed_content_types=self.RESUME_CONTENT_TYPES,
            max_bytes=settings.max_resume_upload_bytes,
            label="resume",
        )
        profile = await self.profile_repo.get_or_create(user_id)
        previous_path = profile.resume_url
        path = self.storage.build_object_path(
            owner_id=user_id,
            folder="resume",
            filename=file.filename,
            content_type=file.content_type,
        )
        await self.storage.upload_file(
            bucket=settings.supabase_resume_files_bucket,
            path=path,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        profile.resume_url = path
        await self.db.flush()
        await self._cleanup_resource_folder(
            bucket=settings.supabase_resume_files_bucket,
            current_path=path,
        )
        await self._delete_previous_if_replaced(
            bucket=settings.supabase_resume_files_bucket,
            previous_path=previous_path,
            current_path=path,
        )
        url = await self.storage.resolve_resume_url(path)
        return path, url

    async def _read_and_validate(
        self,
        *,
        file: UploadFile,
        allowed_content_types: set[str],
        max_bytes: int,
        label: str,
    ) -> bytes:
        if not file.filename:
            raise ValueError(f"{label.capitalize()} filename is required")
        if (file.content_type or "").lower() not in allowed_content_types:
            raise ValueError(f"Unsupported {label} type")

        content = await file.read()
        if not content:
            raise ValueError(f"{label.capitalize()} file is empty")
        if len(content) > max_bytes:
            raise ValueError(f"{label.capitalize()} exceeds the allowed size")
        return content
