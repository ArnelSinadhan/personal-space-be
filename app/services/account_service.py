from __future__ import annotations

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import firebase
from app.config import settings
from app.models.profile import Skill, profile_skills
from app.models.project import personal_project_tech_stacks, project_tech_stacks
from app.models.resume import resume_project_tech_stacks, resume_skills
from app.models.user import User
from app.services.storage_service import StorageService


class AccountService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.storage = StorageService()

    async def delete_account(self, user: User) -> None:
        await self._delete_storage_data(user)
        self._delete_firebase_account(user.firebase_uid)
        await self.db.execute(delete(User).where(User.id == user.id))
        await self._delete_orphaned_skills()
        await self.db.commit()

    async def update_password(self, user: User, new_password: str) -> None:
        firebase.update_firebase_user_password(user.firebase_uid, new_password)

    async def _delete_storage_data(self, user: User) -> None:
        prefix = str(user.id)
        await self.storage.delete_prefix(
            bucket=settings.supabase_profile_images_bucket,
            prefix=prefix,
        )
        await self.storage.delete_prefix(
            bucket=settings.supabase_company_images_bucket,
            prefix=prefix,
        )
        await self.storage.delete_prefix(
            bucket=settings.supabase_certification_images_bucket,
            prefix=prefix,
        )
        await self.storage.delete_prefix(
            bucket=settings.supabase_project_images_bucket,
            prefix=prefix,
        )
        await self.storage.delete_prefix(
            bucket=settings.supabase_resume_files_bucket,
            prefix=prefix,
        )

    def _delete_firebase_account(self, firebase_uid: str) -> None:
        firebase.delete_firebase_user(firebase_uid)

    async def _delete_orphaned_skills(self) -> None:
        await self.db.execute(
            delete(Skill).where(
                ~exists(
                    select(1).select_from(profile_skills).where(
                        profile_skills.c.skill_id == Skill.id
                    )
                ),
                ~exists(
                    select(1).select_from(project_tech_stacks).where(
                        project_tech_stacks.c.skill_id == Skill.id
                    )
                ),
                ~exists(
                    select(1).select_from(personal_project_tech_stacks).where(
                        personal_project_tech_stacks.c.skill_id == Skill.id
                    )
                ),
                ~exists(
                    select(1).select_from(resume_skills).where(
                        resume_skills.c.skill_id == Skill.id
                    )
                ),
                ~exists(
                    select(1).select_from(resume_project_tech_stacks).where(
                        resume_project_tech_stacks.c.skill_id == Skill.id
                    )
                ),
            )
        )
