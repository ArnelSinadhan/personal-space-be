from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile
from app.models.project import Project
from app.models.todo import Todo
from app.models.vault import VaultCategory, VaultEntry
from app.repositories.profile_repo import WorkExperienceRepository
from app.schemas.dashboard import (
    DashboardActiveTask,
    DashboardCompanyBarDatum,
    DashboardDonutDatum,
    DashboardOverviewOut,
    DashboardProfileCompleteness,
    DashboardProjectProgressDatum,
    DashboardStatusCounts,
    DashboardTechStackDatum,
    DashboardTimeDatum,
    DashboardVaultCategoryDatum,
)

STATUS_LABELS = {
    "todo": "To Do",
    "in_progress": "In Progress",
    "done": "Done",
    "blocked": "Blocked",
    "pending": "Pending",
}

STATUS_COLORS = {
    "todo": "#9ca3af",
    "in_progress": "#3b82f6",
    "done": "#22c55e",
    "blocked": "#f87171",
    "pending": "#fbbf24",
}

CHART_COLORS = [
    "#3b82f6",
    "#8b5cf6",
    "#06b6d4",
    "#f59e0b",
    "#ec4899",
    "#10b981",
    "#f97316",
    "#6366f1",
]

PROFILE_COMPLETENESS_FIELDS = [
    "Name",
    "Email",
    "Phone",
    "Address",
    "Avatar",
    "Role",
    "About",
    "Skills",
    "Work experience",
    "Education",
    "Social links",
]


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.work_repo = WorkExperienceRepository(db)

    async def get_overview(self, user_id: UUID) -> DashboardOverviewOut:
        profile = await self._get_profile_summary(user_id)
        work_experiences = await self.work_repo.get_all_for_user(user_id)
        vault_categories, vault_counts = await self._get_vault_summary(user_id)

        flat_tasks = self._flatten_tasks(work_experiences)
        status_counts = self._build_status_counts(flat_tasks)
        donut_data = self._build_donut_data(status_counts)
        daily_bar_data = self._build_daily_bar_data(flat_tasks)
        weekly_area_data = self._build_weekly_area_data(flat_tasks)
        company_bar_data = self._build_company_bar_data(work_experiences)
        project_radial_data = self._build_project_progress_data(work_experiences)
        tech_stack_data = self._build_tech_stack_data(work_experiences)
        active_tasks = self._build_active_tasks(flat_tasks)
        profile_completeness = self._build_profile_completeness(
            profile=profile,
            work_experience_count=len(work_experiences),
        )

        completed_today = sum(
            1 for task in flat_tasks if task["status"] == "done" and self._is_same_day(task["completed_at"])
        )
        completed_this_week = self._count_completed_this_week(flat_tasks)

        total_projects = sum(len(work.projects) for work in work_experiences)
        vault_entry_count = sum(vault_counts.values())

        return DashboardOverviewOut(
            first_name=(profile.name or "there").split(" ")[0] if profile and profile.name else "there",
            profile=profile_completeness,
            company_count=len(work_experiences),
            total_projects=total_projects,
            total_tasks=len(flat_tasks),
            completed_today=completed_today,
            completed_this_week=completed_this_week,
            streak=self._calculate_streak(flat_tasks),
            status_counts=DashboardStatusCounts(**status_counts),
            donut_data=donut_data,
            daily_bar_data=daily_bar_data,
            weekly_area_data=weekly_area_data,
            company_bar_data=company_bar_data,
            project_radial_data=project_radial_data,
            tech_stack_data=tech_stack_data,
            active_tasks=active_tasks,
            vault_entry_count=vault_entry_count,
            vault_category_count=len(vault_categories),
            vault_category_data=[
                DashboardVaultCategoryDatum(
                    name=category.name,
                    value=vault_counts.get(str(category.id), 0),
                    color=CHART_COLORS[index % len(CHART_COLORS)],
                )
                for index, category in enumerate(vault_categories)
            ],
            has_data=len(flat_tasks) > 0,
        )

    async def _get_profile_summary(self, user_id: UUID) -> Profile:
        result = await self.db.execute(
            select(Profile)
            .where(Profile.user_id == user_id)
            .options(
                selectinload(Profile.skills),
                selectinload(Profile.education_entries),
                selectinload(Profile.social_links),
            )
        )
        profile = result.scalar_one_or_none()
        if profile is not None:
            return profile

        profile = Profile(user_id=user_id)
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile, ["skills", "education_entries", "social_links"])
        return profile

    async def _get_vault_summary(
        self,
        user_id: UUID,
    ) -> tuple[list[VaultCategory], dict[str, int]]:
        category_result = await self.db.execute(
            select(VaultCategory)
            .where(VaultCategory.user_id == user_id)
            .order_by(VaultCategory.sort_order)
        )
        categories = list(category_result.scalars().all())

        count_result = await self.db.execute(
            select(VaultEntry.category_id, func.count(VaultEntry.id))
            .where(VaultEntry.user_id == user_id)
            .group_by(VaultEntry.category_id)
        )
        counts = {str(category_id): count for category_id, count in count_result.all() if category_id}
        return categories, counts

    def _flatten_tasks(self, work_experiences: list) -> list[dict[str, str | int | None]]:
        tasks: list[dict[str, str | int | None]] = []
        for work in work_experiences:
            for project in work.projects:
                for todo in project.todos:
                    tasks.append(
                        {
                            "id": str(todo.id),
                            "title": todo.title,
                            "status": todo.status,
                            "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
                            "sort_order": todo.sort_order,
                            "project_name": project.name,
                            "company_name": work.company,
                        }
                    )
        return tasks

    def _build_status_counts(self, tasks: list[dict[str, str | int | None]]) -> dict[str, int]:
        counts = {status: 0 for status in STATUS_LABELS}
        for task in tasks:
            status = str(task["status"])
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _build_donut_data(self, status_counts: dict[str, int]) -> list[DashboardDonutDatum]:
        return [
            DashboardDonutDatum(
                name=STATUS_LABELS[status],
                value=count,
                color=STATUS_COLORS[status],
            )
            for status, count in status_counts.items()
            if count > 0
        ]

    def _build_daily_bar_data(self, tasks: list[dict[str, str | int | None]], days: int = 14) -> list[DashboardTimeDatum]:
        now = datetime.now(timezone.utc)
        data: list[DashboardTimeDatum] = []
        for offset in range(days - 1, -1, -1):
            day = (now - timedelta(days=offset)).date()
            count = sum(
                1
                for task in tasks
                if task["status"] == "done"
                and task["completed_at"]
                and datetime.fromisoformat(str(task["completed_at"])).date() == day
            )
            label = datetime.combine(day, datetime.min.time()).strftime("%b %-d")
            data.append(DashboardTimeDatum(name=label, tasks=count))
        return data

    def _build_weekly_area_data(self, tasks: list[dict[str, str | int | None]], weeks: int = 8) -> list[DashboardTimeDatum]:
        now = datetime.now(timezone.utc)
        current_week_start = (now - timedelta(days=now.weekday())).date()
        data: list[DashboardTimeDatum] = []

        for offset in range(weeks - 1, -1, -1):
            week_start = current_week_start - timedelta(days=offset * 7)
            week_end = week_start + timedelta(days=7)
            count = sum(
                1
                for task in tasks
                if task["status"] == "done"
                and task["completed_at"]
                and week_start <= datetime.fromisoformat(str(task["completed_at"])).date() < week_end
            )
            data.append(DashboardTimeDatum(name=f"W{weeks - offset}", tasks=count))
        return data

    def _build_company_bar_data(self, work_experiences: list) -> list[DashboardCompanyBarDatum]:
        data: list[DashboardCompanyBarDatum] = []
        for work in work_experiences:
            todos = [todo for project in work.projects for todo in project.todos]
            data.append(
                DashboardCompanyBarDatum(
                    name=f"{work.company[:12]}..." if len(work.company) > 12 else work.company,
                    done=sum(1 for todo in todos if todo.status == "done"),
                    active=sum(1 for todo in todos if todo.status in {"todo", "in_progress", "pending"}),
                    blocked=sum(1 for todo in todos if todo.status == "blocked"),
                )
            )
        return data

    def _build_project_progress_data(self, work_experiences: list) -> list[DashboardProjectProgressDatum]:
        data: list[DashboardProjectProgressDatum] = []
        index = 0
        for work in work_experiences:
            for project in work.projects:
                total = len(project.todos)
                done = sum(1 for todo in project.todos if todo.status == "done")
                progress = round((done / total) * 100) if total else 0
                data.append(
                    DashboardProjectProgressDatum(
                        name=project.name,
                        progress=progress,
                        fill=CHART_COLORS[index % len(CHART_COLORS)],
                    )
                )
                index += 1
        return data

    def _build_tech_stack_data(self, work_experiences: list, limit: int = 8) -> list[DashboardTechStackDatum]:
        counter: Counter[str] = Counter()
        for work in work_experiences:
            for project in work.projects:
                counter.update(skill.name for skill in project.tech_stack)
        return [
            DashboardTechStackDatum(name=name, count=count)
            for name, count in counter.most_common(limit)
        ]

    def _build_active_tasks(self, tasks: list[dict[str, str | int | None]], limit: int = 5) -> list[DashboardActiveTask]:
        active_statuses = {"in_progress", "blocked", "pending"}
        active_tasks = [task for task in tasks if task["status"] in active_statuses]
        active_tasks.sort(key=lambda task: (str(task["status"]) != "in_progress", int(task["sort_order"] or 0)))
        return [
            DashboardActiveTask(
                id=str(task["id"]),
                title=str(task["title"]),
                status=str(task["status"]),
                completed_at=str(task["completed_at"]) if task["completed_at"] else None,
                sort_order=int(task["sort_order"] or 0),
                project_name=str(task["project_name"]),
                company_name=str(task["company_name"]),
            )
            for task in active_tasks[:limit]
        ]

    def _build_profile_completeness(
        self,
        *,
        profile: Profile,
        work_experience_count: int,
    ) -> DashboardProfileCompleteness:
        checks = [
            ("Name", bool(profile.name)),
            ("Email", bool(profile.email)),
            ("Phone", bool(profile.phone)),
            ("Address", bool(profile.address)),
            ("Avatar", bool(profile.avatar_url)),
            ("Role", bool(profile.role)),
            ("About", bool(profile.about)),
            ("Skills", len(profile.skills) > 0),
            ("Work experience", work_experience_count > 0),
            ("Education", len(profile.education_entries) > 0),
            ("Social links", len(profile.social_links) > 0),
        ]
        filled = sum(1 for _, value in checks if value)
        missing = [label for label, value in checks if not value]
        percent = round((filled / len(PROFILE_COMPLETENESS_FIELDS)) * 100)
        return DashboardProfileCompleteness(percent=percent, missing=missing)

    def _count_completed_this_week(self, tasks: list[dict[str, str | int | None]]) -> int:
        now = datetime.now(timezone.utc)
        week_start = (now - timedelta(days=now.weekday())).date()
        return sum(
            1
            for task in tasks
            if task["status"] == "done"
            and task["completed_at"]
            and datetime.fromisoformat(str(task["completed_at"])).date() >= week_start
        )

    def _calculate_streak(self, tasks: list[dict[str, str | int | None]]) -> int:
        completed_days = sorted(
            {
                datetime.fromisoformat(str(task["completed_at"])).date()
                for task in tasks
                if task["status"] == "done" and task["completed_at"]
            },
            reverse=True,
        )
        if not completed_days:
            return 0

        streak = 0
        check_day = datetime.now(timezone.utc).date()
        for completed_day in completed_days:
            if completed_day == check_day:
                streak += 1
                check_day -= timedelta(days=1)
            elif completed_day < check_day:
                break
        return streak

    def _is_same_day(self, completed_at: str | int | None) -> bool:
        if not completed_at:
            return False
        completed_date = datetime.fromisoformat(str(completed_at)).date()
        return completed_date == datetime.now(timezone.utc).date()
