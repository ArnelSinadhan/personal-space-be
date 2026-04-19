from __future__ import annotations

import mimetypes
import posixpath
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

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

        segments = [str(owner_id)]
        if related_id is not None:
            segments.append(str(related_id))
        segments.append(f"{folder}{extension}")
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
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = ""
                try:
                    detail = exc.response.json().get("message", "")
                except Exception:
                    pass
                raise RuntimeError(
                    f"Storage upload failed ({exc.response.status_code})"
                    + (f": {detail}" if detail else "")
                ) from exc
        return path

    async def delete_file(self, *, bucket: str, path: str | None) -> None:
        if not path or not self.enabled or self.is_external_url(path):
            return

        await self.delete_files(bucket=bucket, paths=[path])

    async def delete_files(self, *, bucket: str, paths: list[str]) -> None:
        valid_paths = [
            path for path in paths if path and not self.is_external_url(path)
        ]
        if not valid_paths or not self.enabled:
            return

        delete_url = f"{self.base_url}/storage/v1/object/{quote(bucket)}"
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                "DELETE",
                delete_url,
                headers=headers,
                json={"prefixes": valid_paths},
            )
            if response.status_code not in {200, 204, 404}:
                response.raise_for_status()

    async def list_files(self, *, bucket: str, prefix: str) -> list[str]:
        if not prefix or not self.enabled:
            return []

        list_url = f"{self.base_url}/storage/v1/object/list/{quote(bucket)}"
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "Content-Type": "application/json",
        }
        payload = {
            "prefix": prefix.rstrip("/") + "/",
            "limit": 100,
            "offset": 0,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(list_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        files: list[str] = []
        for item in data:
            name = item.get("name")
            if not name or not isinstance(name, str):
                continue
            files.append(posixpath.join(prefix, name))
        return files

    async def list_all_files(self, *, bucket: str, prefix: str) -> list[str]:
        if not prefix or not self.enabled:
            return []

        list_url = f"{self.base_url}/storage/v1/object/list/{quote(bucket)}"
        headers = {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "Content-Type": "application/json",
        }

        async def walk(current_prefix: str) -> list[str]:
            payload = {
                "prefix": current_prefix.rstrip("/") + "/",
                "limit": 100,
                "offset": 0,
            }

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(list_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            files: list[str] = []
            for item in data:
                name = item.get("name")
                if not name or not isinstance(name, str):
                    continue

                item_path = posixpath.join(current_prefix, name)
                is_file = bool(item.get("id")) or item.get("metadata") is not None
                if is_file:
                    files.append(item_path)
                    continue

                files.extend(await walk(item_path))
            return files

        return await walk(prefix.rstrip("/"))

    async def delete_prefix(self, *, bucket: str, prefix: str | None) -> None:
        if not prefix or not self.enabled:
            return

        paths = await self.list_all_files(bucket=bucket, prefix=prefix)
        await self.delete_files(bucket=bucket, paths=paths)

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
            try:
                response = await client.post(sign_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError:
                return path

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

    async def resolve_certification_url(self, path: str | None) -> str | None:
        return await self.create_signed_url(
            bucket=settings.supabase_certification_images_bucket,
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
