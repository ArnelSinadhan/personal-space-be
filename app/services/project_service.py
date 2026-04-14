from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enums import ProjectLifecycleStatus, ProjectTestimonialStatus, TodoStatus
from app.models.profile import Profile, WorkExperience
from app.models.project import PersonalProject, Project, ProjectTestimonial
from app.models.todo import Todo
from app.repositories.profile_repo import (
    ProfileRepository,
    SkillRepository,
    WorkExperienceRepository,
)
from app.repositories.project_repo import PersonalProjectRepository, ProjectRepository
from app.repositories.todo_repo import TodoRepository
from app.schemas.project import (
    PersonalProjectCreate,
    PersonalProjectOut,
    PersonalProjectUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectTestimonialOut,
    ProjectTestimonialUpdate,
    ProjectUpdate,
)
from app.schemas.profile import WorkExperienceWorkspaceOut
from app.schemas.todo import TodoCreate, TodoOut, TodoUpdate
from app.services.storage_service import StorageService


class ProjectLifecycleConflictError(Exception):
    pass


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.work_repo = WorkExperienceRepository(db)
        self.project_repo = ProjectRepository(db)
        self.personal_project_repo = PersonalProjectRepository(db)
        self.todo_repo = TodoRepository(db)
        self.skill_repo = SkillRepository(db)
        self.storage = StorageService()

    # -- Workspaces ----------------------------------------------------------

    async def get_workspaces_for_user(
        self, user_id: UUID, *, current_only: bool = False
    ) -> list[WorkExperienceWorkspaceOut]:
        workspaces = await self.work_repo.get_all_for_user(
            user_id, current_only=current_only
        )
        return [await self._workspace_to_out(workspace) for workspace in workspaces]

    async def get_personal_projects_for_user(
        self, user_id: UUID
    ) -> list[PersonalProjectOut]:
        projects = await self.personal_project_repo.get_all_for_user(user_id)
        return [await self._personal_project_to_out(project) for project in projects]

    # -- Projects ------------------------------------------------------------

    async def create_project(
        self, work_experience_id: UUID, user_id: UUID, data: ProjectCreate
    ) -> ProjectOut:
        workspace = await self.work_repo.get_by_id_for_user(work_experience_id, user_id)
        if workspace is None:
            raise ValueError("Work experience not found")
        skills = await self.skill_repo.get_or_create_many(data.tech_stack)
        lifecycle_fields = self._build_lifecycle_fields(
            lifecycle_status=data.lifecycle_status,
            completed_at=data.completed_at,
            archived_at=data.archived_at,
            outcome_summary=data.outcome_summary,
        )
        project = Project(
            work_experience_id=work_experience_id,
            name=data.name,
            description=data.description,
            image_url=data.image_url,
            github_url=data.github_url,
            live_url=data.live_url,
            is_public=data.is_public,
            **lifecycle_fields,
        )
        project.tech_stack = skills
        self.db.add(project)
        await self.db.flush()
        refreshed = await self.project_repo.get_by_id_for_user(project.id, user_id)
        return await self._project_to_out(refreshed or project)

    async def update_project(
        self, project_id: UUID, user_id: UUID, data: ProjectUpdate
    ) -> ProjectOut:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Project not found")
        updates = data.model_dump(exclude_unset=True)
        previous_image_path = project.image_url
        self._apply_lifecycle_updates(project, updates)

        for field, value in updates.items():
            if field == "tech_stack":
                project.tech_stack = await self.skill_repo.get_or_create_many(
                    value or []
                )
                continue
            setattr(project, field, value)

        await self.db.flush()

        if (
            "image_url" in updates
            and updates["image_url"] is None
            and previous_image_path is not None
        ):
            await self.storage.delete_file(
                bucket=settings.supabase_project_images_bucket,
                path=previous_image_path,
            )

        return await self._project_to_out(project)

    async def delete_project(self, project_id: UUID, user_id: UUID) -> None:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Project not found")
        image_path = project.image_url
        await self.project_repo.delete(project)
        await self.storage.delete_file(
            bucket=settings.supabase_project_images_bucket,
            path=image_path,
        )

    async def create_personal_project(
        self, user_id: UUID, data: PersonalProjectCreate
    ) -> PersonalProjectOut:
        profile = await self.profile_repo.get_or_create(user_id)

        skills = await self.skill_repo.get_or_create_many(data.tech_stack)
        existing = await self.personal_project_repo.get_all_for_user(user_id)
        lifecycle_fields = self._build_lifecycle_fields(
            lifecycle_status=data.lifecycle_status,
            completed_at=data.completed_at,
            archived_at=data.archived_at,
            outcome_summary=data.outcome_summary,
        )
        project = PersonalProject(
            profile_id=profile.id,
            name=data.name,
            description=data.description,
            image_url=data.image_url,
            github_url=data.github_url,
            live_url=data.live_url,
            is_public=data.is_public,
            is_featured=data.is_featured,
            sort_order=len(existing),
            **lifecycle_fields,
        )
        project.tech_stack = skills
        self.db.add(project)
        await self.db.flush()
        return await self._personal_project_to_out(project)

    async def update_personal_project(
        self, project_id: UUID, user_id: UUID, data: PersonalProjectUpdate
    ) -> PersonalProjectOut:
        project = await self.personal_project_repo.get_by_id_for_user(
            project_id, user_id
        )
        if project is None:
            raise ValueError("Personal project not found")
        updates = data.model_dump(exclude_unset=True)
        previous_image_path = project.image_url
        self._apply_lifecycle_updates(project, updates)

        for field, value in updates.items():
            if field == "tech_stack":
                project.tech_stack = await self.skill_repo.get_or_create_many(
                    value or []
                )
                continue
            setattr(project, field, value)

        await self.db.flush()

        if (
            "image_url" in updates
            and updates["image_url"] is None
            and previous_image_path is not None
        ):
            await self.storage.delete_file(
                bucket=settings.supabase_project_images_bucket,
                path=previous_image_path,
            )

        return await self._personal_project_to_out(project)

    async def delete_personal_project(self, project_id: UUID, user_id: UUID) -> None:
        project = await self.personal_project_repo.get_by_id_for_user(
            project_id, user_id
        )
        if project is None:
            raise ValueError("Personal project not found")
        image_path = project.image_url
        await self.personal_project_repo.delete(project)
        await self.storage.delete_file(
            bucket=settings.supabase_project_images_bucket,
            path=image_path,
        )

    async def update_testimonial(
        self, project_id: UUID, user_id: UUID, data: ProjectTestimonialUpdate
    ) -> ProjectOut:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise LookupError("Project not found")

        testimonial = project.testimonial
        if testimonial is None:
            if not data.name or not data.message:
                raise ValueError(
                    "Name and message are required to create a testimonial"
                )
            testimonial = ProjectTestimonial(
                project_id=project.id,
                name=data.name,
                role=data.role,
                message=data.message,
                status=(data.status or ProjectTestimonialStatus.PENDING).value,
            )
            self.db.add(testimonial)
            project.testimonial = testimonial
        else:
            if data.name is not None:
                testimonial.name = data.name
            if data.role is not None:
                testimonial.role = data.role
            if data.message is not None:
                testimonial.message = data.message
            if data.status is not None:
                testimonial.status = data.status.value

        await self.db.flush()
        return await self._project_to_out(project)

    async def delete_testimonial(self, project_id: UUID, user_id: UUID) -> ProjectOut:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise LookupError("Project not found")
        if project.testimonial is not None:
            await self.db.delete(project.testimonial)
            await self.db.flush()
            project.testimonial = None
        return await self._project_to_out(project)

    # -- Todos ---------------------------------------------------------------

    async def create_todo(
        self, project_id: UUID, user_id: UUID, data: TodoCreate
    ) -> TodoOut:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Project not found")
        self._ensure_todos_enabled(project)
        existing = await self.todo_repo.get_by_project(project_id)
        todo = Todo(
            project_id=project_id,
            title=data.title,
            status=data.status.value,
            sort_order=len(existing),
        )
        if data.status == TodoStatus.DONE:
            todo.completed_at = datetime.now(timezone.utc)
        self.db.add(todo)
        await self.db.flush()
        return TodoOut.model_validate(todo)

    async def update_todo(
        self, todo_id: UUID, user_id: UUID, data: TodoUpdate
    ) -> TodoOut:
        todo = await self.todo_repo.get_by_id_for_user(todo_id, user_id)
        if todo is None:
            raise ValueError("Todo not found")
        if todo.project is not None:
            self._ensure_todos_enabled(todo.project)
        if data.title is not None:
            todo.title = data.title
        if data.status is not None:
            old_status = todo.status
            todo.status = data.status.value
            # Auto-manage completed_at
            if data.status == TodoStatus.DONE and old_status != TodoStatus.DONE.value:
                todo.completed_at = datetime.now(timezone.utc)
            elif data.status != TodoStatus.DONE and old_status == TodoStatus.DONE.value:
                todo.completed_at = None
        await self.db.flush()
        return TodoOut.model_validate(todo)

    async def delete_todo(self, todo_id: UUID, user_id: UUID) -> None:
        todo = await self.todo_repo.get_by_id_for_user(todo_id, user_id)
        if todo is None:
            raise ValueError("Todo not found")
        if todo.project is not None:
            self._ensure_todos_enabled(todo.project)
        await self.todo_repo.delete(todo)

    # -- Serialization -------------------------------------------------------

    async def _workspace_to_out(
        self, workspace: WorkExperience
    ) -> WorkExperienceWorkspaceOut:
        sorted_projects = sorted(
            workspace.projects,
            key=lambda p: p.completed_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return WorkExperienceWorkspaceOut(
            id=workspace.id,
            title=workspace.title,
            company=workspace.company,
            start_date=workspace.start_date,
            end_date=workspace.end_date,
            is_current=workspace.is_current,
            image_url=await self.storage.resolve_company_url(workspace.image_url),
            projects=[
                await self._project_to_out(project) for project in sorted_projects
            ],
        )

    async def _project_to_out(self, project: Project) -> ProjectOut:
        return ProjectOut(
            id=project.id,
            name=project.name,
            description=project.description,
            image_url=await self.storage.resolve_project_url(project.image_url),
            github_url=project.github_url,
            live_url=project.live_url,
            tech_stack=[s.name for s in project.tech_stack],
            is_public=project.is_public,
            lifecycle_status=self._coerce_lifecycle_status(project.lifecycle_status),
            completed_at=project.completed_at,
            archived_at=project.archived_at,
            outcome_summary=project.outcome_summary,
            testimonial=(
                ProjectTestimonialOut.model_validate(project.testimonial)
                if project.testimonial is not None
                else None
            ),
            todos=[TodoOut.model_validate(t) for t in project.todos],
        )

    async def _personal_project_to_out(
        self, project: PersonalProject
    ) -> PersonalProjectOut:
        return PersonalProjectOut(
            id=project.id,
            name=project.name,
            description=project.description,
            image_url=await self.storage.resolve_project_url(project.image_url),
            github_url=project.github_url,
            live_url=project.live_url,
            tech_stack=[s.name for s in project.tech_stack],
            is_public=project.is_public,
            is_featured=project.is_featured,
            lifecycle_status=self._coerce_lifecycle_status(project.lifecycle_status),
            completed_at=project.completed_at,
            archived_at=project.archived_at,
            outcome_summary=project.outcome_summary,
        )

    def _build_lifecycle_fields(
        self,
        *,
        lifecycle_status: ProjectLifecycleStatus,
        completed_at: datetime | None,
        archived_at: datetime | None,
        outcome_summary: str | None,
    ) -> dict[str, object | None]:
        status = lifecycle_status.value
        now = datetime.now(timezone.utc)

        return {
            "lifecycle_status": status,
            "completed_at": (
                completed_at
                if status == ProjectLifecycleStatus.COMPLETED.value
                else None
            ),
            "archived_at": (
                archived_at if status == ProjectLifecycleStatus.ARCHIVED.value else None
            ),
            "outcome_summary": outcome_summary,
            **(
                {"completed_at": completed_at or now}
                if status == ProjectLifecycleStatus.COMPLETED.value
                else (
                    {"archived_at": archived_at or now}
                    if status == ProjectLifecycleStatus.ARCHIVED.value
                    else {}
                )
            ),
        }

    def _apply_lifecycle_updates(
        self,
        project: Project | PersonalProject,
        updates: dict[str, object | None],
    ) -> None:
        if not {
            "lifecycle_status",
            "completed_at",
            "archived_at",
            "outcome_summary",
        }.intersection(updates):
            return

        next_status = project.lifecycle_status
        raw_status = updates.get("lifecycle_status")
        if raw_status is None:
            updates.pop("lifecycle_status", None)
        elif isinstance(raw_status, ProjectLifecycleStatus):
            next_status = raw_status.value
            updates["lifecycle_status"] = next_status
        elif isinstance(raw_status, str):
            next_status = raw_status

        now = datetime.now(timezone.utc)
        if next_status == ProjectLifecycleStatus.COMPLETED.value:
            updates["completed_at"] = (
                updates.get("completed_at") or project.completed_at or now
            )
            updates["archived_at"] = None
        elif next_status == ProjectLifecycleStatus.ARCHIVED.value:
            updates["archived_at"] = (
                updates.get("archived_at") or project.archived_at or now
            )
            if "completed_at" not in updates:
                updates["completed_at"] = project.completed_at
        else:
            updates["completed_at"] = None
            updates["archived_at"] = None

    def _ensure_todos_enabled(self, project: Project) -> None:
        if project.lifecycle_status in {
            ProjectLifecycleStatus.COMPLETED.value,
            ProjectLifecycleStatus.ARCHIVED.value,
        }:
            raise ProjectLifecycleConflictError(
                f"Todos are disabled for projects with lifecycle_status '{project.lifecycle_status}'."
            )

    def _coerce_lifecycle_status(
        self,
        status: str | ProjectLifecycleStatus,
    ) -> ProjectLifecycleStatus:
        if isinstance(status, ProjectLifecycleStatus):
            return status
        return ProjectLifecycleStatus(status)
