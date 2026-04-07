from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import TodoStatus
from app.models.company import Company
from app.models.project import Project
from app.models.todo import Todo
from app.repositories.company_repo import CompanyRepository
from app.repositories.profile_repo import SkillRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.todo_repo import TodoRepository
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.schemas.todo import TodoBulkUpdate, TodoCreate, TodoOut, TodoUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.company_repo = CompanyRepository(db)
        self.project_repo = ProjectRepository(db)
        self.todo_repo = TodoRepository(db)
        self.skill_repo = SkillRepository(db)

    # -- Companies -----------------------------------------------------------

    async def get_companies_for_user(self, user_id: UUID) -> list[CompanyOut]:
        companies = await self.company_repo.get_all_for_user(user_id)
        return [self._company_to_out(c) for c in companies]

    async def create_company(self, user_id: UUID, data: CompanyCreate) -> CompanyOut:
        company = Company(user_id=user_id, **data.model_dump())
        self.db.add(company)
        await self.db.flush()
        return self._company_to_out(company)

    async def update_company(
        self, company_id: UUID, user_id: UUID, data: CompanyUpdate
    ) -> CompanyOut:
        company = await self.company_repo.get_by_id_for_user(company_id, user_id)
        if company is None:
            raise ValueError("Company not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(company, field, value)
        await self.db.flush()
        return self._company_to_out(company)

    async def delete_company(self, company_id: UUID, user_id: UUID) -> None:
        company = await self.company_repo.get_by_id_for_user(company_id, user_id)
        if company is None:
            raise ValueError("Company not found")
        await self.company_repo.delete(company)

    # -- Projects ------------------------------------------------------------

    async def create_project(
        self, company_id: UUID, user_id: UUID, data: ProjectCreate
    ) -> ProjectOut:
        company = await self.company_repo.get_by_id_for_user(company_id, user_id)
        if company is None:
            raise ValueError("Company not found")
        skills = await self.skill_repo.get_or_create_many(data.tech_stack)
        project = Project(
            company_id=company_id,
            name=data.name,
            description=data.description,
            is_public=data.is_public,
        )
        project.tech_stack = skills
        self.db.add(project)
        await self.db.flush()
        return self._project_to_out(project)

    async def update_project(
        self, project_id: UUID, data: ProjectUpdate
    ) -> ProjectOut:
        project = await self.project_repo.get_by_id_with_relations(project_id)
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

    async def delete_project(self, project_id: UUID) -> None:
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise ValueError("Project not found")
        await self.project_repo.delete(project)

    # -- Todos ---------------------------------------------------------------

    async def create_todo(self, project_id: UUID, data: TodoCreate) -> TodoOut:
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

    async def update_todo(self, todo_id: UUID, data: TodoUpdate) -> TodoOut:
        todo = await self.todo_repo.get_by_id(todo_id)
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

    async def bulk_update_todos(self, data: TodoBulkUpdate) -> list[TodoOut]:
        results: list[TodoOut] = []
        for item in data.todos:
            todo = await self.todo_repo.get_by_id(item.id)
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

    async def delete_todo(self, todo_id: UUID) -> None:
        todo = await self.todo_repo.get_by_id(todo_id)
        if todo is None:
            raise ValueError("Todo not found")
        await self.todo_repo.delete(todo)

    # -- Serialization -------------------------------------------------------

    def _company_to_out(self, company: Company) -> CompanyOut:
        return CompanyOut(
            id=company.id,
            name=company.name,
            logo_url=company.logo_url,
            role=company.role,
            start_date=company.start_date,
            end_date=company.end_date,
            is_current=company.is_current,
            projects=[self._project_to_out(p) for p in company.projects],
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
