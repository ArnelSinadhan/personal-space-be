from __future__ import annotations

import mimetypes
import posixpath
from pathlib import Path
from urllib.parse import quote
from uuid import UUID, uuid4

import httpx

from app.config import settings


class StorageService:
    def __init__(self) -> None:
        self.base_url = (settings.supabase_url or "").rstrip("/")
        self.service_key = settings.supabase_service_role_key or ""

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.service_key)

    def is_external_url(self, value: str | None) -> bool:
        if not value:
            return False
        return value.startswith(("http://", "https://", "/"))

    def build_object_path(
        self,
        *,
        owner_id: UUID,
        folder: str,
        filename: str | None,
        content_type: str | None,
        related_id: UUID | None = None,
    ) -> str:
        extension = Path(filename or "").suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(content_type or "") or ""

        name = uuid4().hex
        segments = [str(owner_id)]
        if related_id is not None:
            segments.append(str(related_id))
        segments.append(f"{folder}-{name}{extension}")
        return posixpath.join(*segments)

    async def upload_file(
        self,
        *,
        bucket: str,
        path: str,
        content: bytes,
        content_type: str,
    ) -> str:
        if not self.enabled:
            raise RuntimeError("Supabase storage is not configured")

        upload_url = (
            f"{self.base_url}/storage/v1/object/{quote(bucket)}/{quote(path, safe='/')}"
        )
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(upload_url, headers=headers, content=content)
            response.raise_for_status()
        return path

    async def delete_file(self, *, bucket: str, path: str | None) -> None:
        if not path or not self.enabled or self.is_external_url(path):
            return

        delete_url = (
            f"{self.base_url}/storage/v1/object/{quote(bucket)}/{quote(path, safe='/')}"
        )
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(delete_url, headers=headers)
            if response.status_code not in {200, 204, 404}:
                response.raise_for_status()

    async def create_signed_url(
        self,
        *,
        bucket: str,
        path: str | None,
        expires_in: int | None = None,
    ) -> str | None:
        if not path:
            return None
        if self.is_external_url(path) or not self.enabled:
            return path

        sign_url = (
            f"{self.base_url}/storage/v1/object/sign/{quote(bucket)}/{quote(path, safe='/')}"
        )
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "Content-Type": "application/json",
        }
        payload = {"expiresIn": expires_in or settings.signed_url_expire_seconds}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(sign_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        signed_url = data.get("signedURL") or data.get("signedUrl") or data.get("signed_url")
        if not signed_url:
            return None
        if signed_url.startswith("http://") or signed_url.startswith("https://"):
            return signed_url
        if signed_url.startswith("/"):
            return f"{self.base_url}/storage/v1{signed_url}"
        return f"{self.base_url}/storage/v1/{signed_url.lstrip('/')}"

    async def resolve_profile_url(self, path: str | None) -> str | None:
        return await self.create_signed_url(
            bucket=settings.supabase_profile_images_bucket,
            path=path,
        )

    async def resolve_company_url(self, path: str | None) -> str | None:
        return await self.create_signed_url(
            bucket=settings.supabase_company_images_bucket,
            path=path,
        )

    async def resolve_project_url(self, path: str | None) -> str | None:
        return await self.create_signed_url(
            bucket=settings.supabase_project_images_bucket,
            path=path,
        )

    async def resolve_resume_url(self, path: str | None) -> str | None:
        return await self.create_signed_url(
            bucket=settings.supabase_resume_files_bucket,
            path=path,
        )
