from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import ProjectLifecycleStatus
from app.models.profile import Profile
from app.models.project import Project
from app.models.vault import VaultCategory, VaultEntry
from app.repositories.profile_repo import WorkExperienceRepository
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardProfileCompleteness,
    DashboardProjectHealth,
    DashboardStatusCounts,
    DashboardSummary,
    DashboardTaskDistributionItem,
    DashboardTechStackDatum,
    DashboardTimeDatum,
    DashboardVaultCategoryDatum,
    DashboardVaultSummary,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATUS_LABELS: dict[str, str] = {
    "todo": "To Do",
    "in_progress": "In Progress",
    "done": "Done",
    "blocked": "Blocked",
    "pending": "Pending",
}

STATUS_COLORS: dict[str, str] = {
    "todo": "#9ca3af",
    "in_progress": "#3b82f6",
    "done": "#22c55e",
    "blocked": "#f87171",
    "pending": "#fbbf24",
}

CHART_COLORS: list[str] = [
    "#3b82f6",
    "#8b5cf6",
    "#06b6d4",
    "#f59e0b",
    "#ec4899",
    "#10b981",
    "#f97316",
    "#6366f1",
]

PROFILE_COMPLETENESS_FIELDS: list[str] = [
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


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.work_repo = WorkExperienceRepository(db)

    async def get_overview(self, user_id: UUID) -> DashboardOverviewResponse:
        profile = await self._get_profile_summary(user_id)
        work_experiences = await self.work_repo.get_all_for_user(user_id)
        vault_categories, vault_counts = await self._get_vault_summary(user_id)

        flat_tasks = self._flatten_tasks(work_experiences)
        status_counts = self._build_status_counts(flat_tasks)
        task_distribution = self._build_task_distribution(status_counts)
        daily_trend = self._build_daily_trend(flat_tasks)
        weekly_trend = self._build_weekly_trend(flat_tasks)
        project_health = self._build_project_health(work_experiences)
        tech_stack = self._build_tech_stack(work_experiences)
        profile_completeness = self._build_profile_completeness(
            profile=profile,
            work_experience_count=len(work_experiences),
        )

        completed_today = sum(
            1
            for task in flat_tasks
            if task["status"] == "done" and self._is_same_day(task["completed_at"])
        )
        completed_this_week = self._count_completed_this_week(flat_tasks)

        total_projects = sum(len(work.projects) for work in work_experiences)
        (
            active_project_count,
            maintenance_project_count,
            completed_project_count,
            archived_project_count,
        ) = self._count_projects_by_lifecycle(work_experiences)

        vault_entry_count = sum(vault_counts.values())

        return DashboardOverviewResponse(
            first_name=(profile.name or "there").split(" ")[0] if profile and profile.name else "there",
            profile=profile_completeness,
            summary=DashboardSummary(
                company_count=len(work_experiences),
                total_projects=total_projects,
                active_project_count=active_project_count,
                maintenance_project_count=maintenance_project_count,
                completed_project_count=completed_project_count,
                archived_project_count=archived_project_count,
                total_tasks=len(flat_tasks),
                completed_today=completed_today,
                completed_this_week=completed_this_week,
                streak=self._calculate_streak(flat_tasks),
            ),
            status_counts=DashboardStatusCounts(**status_counts),
            task_distribution=task_distribution,
            daily_trend=daily_trend,
            weekly_trend=weekly_trend,
            project_health=project_health,
            project_health_total_count=len(project_health),
            tech_stack=tech_stack,
            vault=DashboardVaultSummary(
                entry_count=vault_entry_count,
                category_count=len(vault_categories),
                categories=[
                    DashboardVaultCategoryDatum(
                        name=category.name,
                        value=vault_counts.get(str(category.id), 0),
                        color=CHART_COLORS[index % len(CHART_COLORS)],
                    )
                    for index, category in enumerate(vault_categories)
                ],
            ),
            has_data=len(flat_tasks) > 0,
        )

    # -----------------------------------------------------------------------
    # Database helpers
    # -----------------------------------------------------------------------

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
        counts = {
            str(category_id): count
            for category_id, count in count_result.all()
            if category_id
        }
        return categories, counts

    # -----------------------------------------------------------------------
    # Task flattening
    # -----------------------------------------------------------------------

    def _flatten_tasks(self, work_experiences: list) -> list[dict[str, str | int | None]]:
        """Return every todo across all operational projects as a flat list of dicts."""
        tasks: list[dict[str, str | int | None]] = []
        for work in work_experiences:
            for project in work.projects:
                if not self._is_operational_project(project):
                    continue
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

    # -----------------------------------------------------------------------
    # Chart builders
    # -----------------------------------------------------------------------

    def _build_status_counts(self, tasks: list[dict[str, str | int | None]]) -> dict[str, int]:
        counts: dict[str, int] = {status: 0 for status in STATUS_LABELS}
        for task in tasks:
            status = str(task["status"])
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _build_task_distribution(
        self, status_counts: dict[str, int]
    ) -> list[DashboardTaskDistributionItem]:
        """Horizontal bar / status chart data. Includes `status` key so the
        frontend can drive colour and icon logic without re-parsing the label."""
        return [
            DashboardTaskDistributionItem(
                name=STATUS_LABELS[status],
                value=count,
                color=STATUS_COLORS[status],
                status=status,
            )
            for status, count in status_counts.items()
            if count > 0
        ]

    def _build_daily_trend(
        self, tasks: list[dict[str, str | int | None]], days: int = 14
    ) -> list[DashboardTimeDatum]:
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

    def _build_weekly_trend(
        self, tasks: list[dict[str, str | int | None]], weeks: int = 8
    ) -> list[DashboardTimeDatum]:
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

    def _build_project_health(self, work_experiences: list) -> list[DashboardProjectHealth]:
        """Build the project health list for operational (active + maintenance) projects.

        Sorted for dashboard display priority:
          1. active  before maintenance
          2. projects with blocked tasks first (attention needed)
          3. higher progress first (nearly-done projects are motivating)
          4. stable alphabetical fallback by name

        The full list is always returned. `project_health_total_count` on the
        response lets the frontend paginate or truncate without losing the
        total for UI labels.
        """
        items: list[DashboardProjectHealth] = []
        color_index = 0

        for work in work_experiences:
            for project in work.projects:
                if not self._is_operational_project(project):
                    continue

                todos = project.todos
                total = len(todos)
                done_tasks = sum(1 for t in todos if t.status == "done")
                in_progress_tasks = sum(1 for t in todos if t.status == "in_progress")
                blocked_tasks = sum(1 for t in todos if t.status == "blocked")
                pending_tasks = sum(1 for t in todos if t.status == "pending")
                todo_tasks = sum(1 for t in todos if t.status == "todo")
                progress = round((done_tasks / total) * 100) if total else 0

                items.append(
                    DashboardProjectHealth(
                        id=str(project.id),
                        name=project.name,
                        lifecycle_status=project.lifecycle_status,
                        progress=progress,
                        total_tasks=total,
                        done_tasks=done_tasks,
                        in_progress_tasks=in_progress_tasks,
                        blocked_tasks=blocked_tasks,
                        pending_tasks=pending_tasks,
                        todo_tasks=todo_tasks,
                        color=CHART_COLORS[color_index % len(CHART_COLORS)],
                    )
                )
                color_index += 1

        items.sort(
            key=lambda p: (
                0 if p.lifecycle_status == ProjectLifecycleStatus.ACTIVE.value else 1,
                -p.blocked_tasks,   # more blocked tasks = needs attention first
                -p.progress,        # higher progress = show first within same tier
                p.name.lower(),     # stable alphabetical fallback
            )
        )
        return items

    def _build_tech_stack(
        self, work_experiences: list, limit: int = 8
    ) -> list[DashboardTechStackDatum]:
        counter: Counter[str] = Counter()
        for work in work_experiences:
            for project in work.projects:
                counter.update(skill.name for skill in project.tech_stack)
        return [
            DashboardTechStackDatum(name=name, count=count)
            for name, count in counter.most_common(limit)
        ]

    # -----------------------------------------------------------------------
    # Profile completeness
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Project lifecycle helpers
    # -----------------------------------------------------------------------

    def _count_projects_by_lifecycle(self, work_experiences: list) -> tuple[int, int, int, int]:
        counts: Counter[str] = Counter(
            project.lifecycle_status
            for work in work_experiences
            for project in work.projects
        )
        return (
            counts.get(ProjectLifecycleStatus.ACTIVE.value, 0),
            counts.get(ProjectLifecycleStatus.MAINTENANCE.value, 0),
            counts.get(ProjectLifecycleStatus.COMPLETED.value, 0),
            counts.get(ProjectLifecycleStatus.ARCHIVED.value, 0),
        )

    def _is_operational_project(self, project: Project) -> bool:
        return project.lifecycle_status in {
            ProjectLifecycleStatus.ACTIVE.value,
            ProjectLifecycleStatus.MAINTENANCE.value,
        }

    # -----------------------------------------------------------------------
    # Date / streak helpers
    # -----------------------------------------------------------------------

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
