from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ProjectTestimonialStatus, TodoStatus
from app.models.profile import Profile, WorkExperience
from app.models.project import PersonalProject, Project, ProjectTestimonial
from app.models.todo import Todo
from app.repositories.profile_repo import ProfileRepository, SkillRepository, WorkExperienceRepository
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
        workspaces = await self.work_repo.get_all_for_user(user_id, current_only=current_only)
        return [await self._workspace_to_out(workspace) for workspace in workspaces]

    async def get_personal_projects_for_user(self, user_id: UUID) -> list[PersonalProjectOut]:
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
        project = Project(
            work_experience_id=work_experience_id,
            name=data.name,
            description=data.description,
            image_url=data.image_url,
            github_url=data.github_url,
            live_url=data.live_url,
            is_public=data.is_public,
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
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        if data.image_url is not None:
            project.image_url = data.image_url
        if data.github_url is not None:
            project.github_url = data.github_url
        if data.live_url is not None:
            project.live_url = data.live_url
        if data.is_public is not None:
            project.is_public = data.is_public
        if data.tech_stack is not None:
            project.tech_stack = await self.skill_repo.get_or_create_many(data.tech_stack)
        await self.db.flush()
        return await self._project_to_out(project)

    async def delete_project(self, project_id: UUID, user_id: UUID) -> None:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Project not found")
        await self.project_repo.delete(project)

    async def create_personal_project(
        self, user_id: UUID, data: PersonalProjectCreate
    ) -> PersonalProjectOut:
        profile = await self.profile_repo.get_or_create(user_id)

        skills = await self.skill_repo.get_or_create_many(data.tech_stack)
        existing = await self.personal_project_repo.get_all_for_user(user_id)
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
        )
        project.tech_stack = skills
        self.db.add(project)
        await self.db.flush()
        return await self._personal_project_to_out(project)

    async def update_personal_project(
        self, project_id: UUID, user_id: UUID, data: PersonalProjectUpdate
    ) -> PersonalProjectOut:
        project = await self.personal_project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Personal project not found")
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        if data.image_url is not None:
            project.image_url = data.image_url
        if data.github_url is not None:
            project.github_url = data.github_url
        if data.live_url is not None:
            project.live_url = data.live_url
        if data.is_public is not None:
            project.is_public = data.is_public
        if data.is_featured is not None:
            project.is_featured = data.is_featured
        if data.tech_stack is not None:
            project.tech_stack = await self.skill_repo.get_or_create_many(data.tech_stack)
        await self.db.flush()
        return await self._personal_project_to_out(project)

    async def delete_personal_project(self, project_id: UUID, user_id: UUID) -> None:
        project = await self.personal_project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Personal project not found")
        await self.personal_project_repo.delete(project)

    async def update_testimonial(
        self, project_id: UUID, user_id: UUID, data: ProjectTestimonialUpdate
    ) -> ProjectOut:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise LookupError("Project not found")

        testimonial = project.testimonial
        if testimonial is None:
            if not data.name or not data.message:
                raise ValueError("Name and message are required to create a testimonial")
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

    async def create_todo(self, project_id: UUID, user_id: UUID, data: TodoCreate) -> TodoOut:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Project not found")
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

    async def update_todo(self, todo_id: UUID, user_id: UUID, data: TodoUpdate) -> TodoOut:
        todo = await self.todo_repo.get_by_id_for_user(todo_id, user_id)
        if todo is None:
            raise ValueError("Todo not found")
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
        await self.todo_repo.delete(todo)

    # -- Serialization -------------------------------------------------------

    async def _workspace_to_out(self, workspace: WorkExperience) -> WorkExperienceWorkspaceOut:
        return WorkExperienceWorkspaceOut(
            id=workspace.id,
            title=workspace.title,
            company=workspace.company,
            start_date=workspace.start_date,
            end_date=workspace.end_date,
            is_current=workspace.is_current,
            image_url=await self.storage.resolve_company_url(workspace.image_url),
            projects=[await self._project_to_out(project) for project in workspace.projects],
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
        )
