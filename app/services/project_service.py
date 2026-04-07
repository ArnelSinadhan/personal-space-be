from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import TodoStatus
from app.models.profile import WorkExperience
from app.models.project import Project
from app.models.todo import Todo
from app.repositories.profile_repo import SkillRepository, WorkExperienceRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.todo_repo import TodoRepository
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.schemas.profile import WorkExperienceWorkspaceOut
from app.schemas.todo import TodoBulkUpdate, TodoCreate, TodoOut, TodoUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.work_repo = WorkExperienceRepository(db)
        self.project_repo = ProjectRepository(db)
        self.todo_repo = TodoRepository(db)
        self.skill_repo = SkillRepository(db)

    # -- Workspaces ----------------------------------------------------------

    async def get_workspaces_for_user(
        self, user_id: UUID, *, current_only: bool = False
    ) -> list[WorkExperienceWorkspaceOut]:
        workspaces = await self.work_repo.get_all_for_user(user_id, current_only=current_only)
        return [self._workspace_to_out(workspace) for workspace in workspaces]

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
            is_public=data.is_public,
        )
        project.tech_stack = skills
        self.db.add(project)
        await self.db.flush()
        refreshed = await self.project_repo.get_by_id_for_user(project.id, user_id)
        return self._project_to_out(refreshed or project)

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
        if data.is_public is not None:
            project.is_public = data.is_public
        if data.tech_stack is not None:
            project.tech_stack = await self.skill_repo.get_or_create_many(data.tech_stack)
        await self.db.flush()
        return self._project_to_out(project)

    async def delete_project(self, project_id: UUID, user_id: UUID) -> None:
        project = await self.project_repo.get_by_id_for_user(project_id, user_id)
        if project is None:
            raise ValueError("Project not found")
        await self.project_repo.delete(project)

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

    async def bulk_update_todos(self, user_id: UUID, data: TodoBulkUpdate) -> list[TodoOut]:
        results: list[TodoOut] = []
        for item in data.todos:
            todo = await self.todo_repo.get_by_id_for_user(item.id, user_id)
            if todo is None:
                continue
            old_status = todo.status
            todo.status = item.status.value
            todo.sort_order = item.sort_order
            if item.status == TodoStatus.DONE and old_status != TodoStatus.DONE.value:
                todo.completed_at = datetime.now(timezone.utc)
            elif item.status != TodoStatus.DONE and old_status == TodoStatus.DONE.value:
                todo.completed_at = None
            results.append(TodoOut.model_validate(todo))
        await self.db.flush()
        return results

    async def delete_todo(self, todo_id: UUID, user_id: UUID) -> None:
        todo = await self.todo_repo.get_by_id_for_user(todo_id, user_id)
        if todo is None:
            raise ValueError("Todo not found")
        await self.todo_repo.delete(todo)

    # -- Serialization -------------------------------------------------------

    def _workspace_to_out(self, workspace: WorkExperience) -> WorkExperienceWorkspaceOut:
        return WorkExperienceWorkspaceOut(
            id=workspace.id,
            title=workspace.title,
            company=workspace.company,
            start_date=workspace.start_date,
            end_date=workspace.end_date,
            is_current=workspace.is_current,
            image_url=workspace.image_url,
            projects=[self._project_to_out(project) for project in workspace.projects],
        )

    def _project_to_out(self, project: Project) -> ProjectOut:
        return ProjectOut(
            id=project.id,
            name=project.name,
            description=project.description,
            tech_stack=[s.name for s in project.tech_stack],
            is_public=project.is_public,
            todos=[TodoOut.model_validate(t) for t in project.todos],
        )
