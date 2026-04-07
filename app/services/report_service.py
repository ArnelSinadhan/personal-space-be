from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ReportPeriod, TodoStatus
from app.models.profile import Profile, WorkExperience
from app.models.project import Project
from app.models.todo import Todo
from app.schemas.report import CompletedTaskOut, GroupedTasks, ReportSummary


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self, user_id: UUID) -> ReportSummary:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Monday of this week
        weekday = now.weekday()
        week_start = (today_start - timedelta(days=weekday))

        month_start = today_start.replace(day=1)

        base = (
            select(func.count())
            .select_from(Todo)
            .join(Project, Todo.project_id == Project.id)
            .join(WorkExperience, Project.work_experience_id == WorkExperience.id)
            .join(Profile, WorkExperience.profile_id == Profile.id)
            .where(Profile.user_id == user_id, Todo.status == TodoStatus.DONE.value)
        )

        today_q = base.where(Todo.completed_at >= today_start)
        week_q = base.where(Todo.completed_at >= week_start)
        month_q = base.where(Todo.completed_at >= month_start)

        today_count = (await self.db.execute(today_q)).scalar() or 0
        week_count = (await self.db.execute(week_q)).scalar() or 0
        month_count = (await self.db.execute(month_q)).scalar() or 0

        streak = await self._compute_streak(user_id)

        return ReportSummary(
            today=today_count,
            this_week=week_count,
            this_month=month_count,
            streak=streak,
        )

    async def get_completed(
        self, user_id: UUID, period: ReportPeriod
    ) -> list[GroupedTasks]:
        tasks = await self._fetch_completed_tasks(user_id)
        if not tasks:
            return []

        now = datetime.now(timezone.utc)

        if period == ReportPeriod.DAILY:
            return self._group_daily(tasks, now)
        elif period == ReportPeriod.WEEKLY:
            return self._group_weekly(tasks, now)
        else:
            return self._group_monthly(tasks, now)

    # -- Data fetching -------------------------------------------------------

    async def _fetch_completed_tasks(self, user_id: UUID) -> list[CompletedTaskOut]:
        result = await self.db.execute(
            select(
                Todo.id,
                Todo.title,
                Todo.completed_at,
                Project.name.label("project_name"),
                WorkExperience.company.label("company_name"),
            )
            .join(Project, Todo.project_id == Project.id)
            .join(WorkExperience, Project.work_experience_id == WorkExperience.id)
            .join(Profile, WorkExperience.profile_id == Profile.id)
            .where(
                Profile.user_id == user_id,
                Todo.status == TodoStatus.DONE.value,
                Todo.completed_at.isnot(None),
            )
            .order_by(Todo.completed_at.desc())
        )
        rows = result.all()
        return [
            CompletedTaskOut(
                id=str(r.id),
                title=r.title,
                project_name=r.project_name,
                company_name=r.company_name,
                completed_at=r.completed_at.isoformat(),
            )
            for r in rows
        ]

    # -- Streak --------------------------------------------------------------

    async def _compute_streak(self, user_id: UUID) -> int:
        """Count consecutive days with at least 1 completed task."""
        completed_day = func.date_trunc("day", Todo.completed_at)
        result = await self.db.execute(
            select(completed_day.label("day"))
            .join(Project, Todo.project_id == Project.id)
            .join(WorkExperience, Project.work_experience_id == WorkExperience.id)
            .join(Profile, WorkExperience.profile_id == Profile.id)
            .where(
                Profile.user_id == user_id,
                Todo.status == TodoStatus.DONE.value,
                Todo.completed_at.isnot(None),
            )
            .group_by(completed_day)
            .order_by(completed_day.desc())
        )
        days = [r.day.date() if hasattr(r.day, "date") else r.day for r in result.all()]

        if not days:
            return 0

        streak = 0
        check = date.today()
        for d in days:
            if d == check:
                streak += 1
                check -= timedelta(days=1)
            elif d < check:
                break
        return streak

    # -- Grouping helpers ----------------------------------------------------

    def _group_daily(
        self, tasks: list[CompletedTaskOut], now: datetime
    ) -> list[GroupedTasks]:
        groups: dict[str, list[CompletedTaskOut]] = {}
        for t in tasks:
            day_key = t.completed_at[:10]
            groups.setdefault(day_key, []).append(t)

        result = []
        today_str = now.strftime("%Y-%m-%d")
        yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

        for day_key, day_tasks in groups.items():
            if day_key == today_str:
                label = "Today"
            elif day_key == yesterday_str:
                label = "Yesterday"
            else:
                label = day_key
            result.append(GroupedTasks(label=label, tasks=day_tasks))
        return result

    def _group_weekly(
        self, tasks: list[CompletedTaskOut], now: datetime
    ) -> list[GroupedTasks]:
        groups: dict[str, list[CompletedTaskOut]] = {}
        for t in tasks:
            dt = datetime.fromisoformat(t.completed_at)
            week_start = dt - timedelta(days=dt.weekday())
            key = week_start.strftime("%Y-%m-%d")
            groups.setdefault(key, []).append(t)

        result = []
        current_week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")

        for key, week_tasks in groups.items():
            label = "This Week" if key == current_week_start else f"Week of {key}"
            sublabel = f"{len(week_tasks)} task{'s' if len(week_tasks) > 1 else ''} completed"
            result.append(GroupedTasks(label=label, sublabel=sublabel, tasks=week_tasks))
        return result

    def _group_monthly(
        self, tasks: list[CompletedTaskOut], now: datetime
    ) -> list[GroupedTasks]:
        groups: dict[str, list[CompletedTaskOut]] = {}
        for t in tasks:
            month_key = t.completed_at[:7]
            groups.setdefault(month_key, []).append(t)

        result = []
        current_month = now.strftime("%Y-%m")

        for key, month_tasks in groups.items():
            label = "This Month" if key == current_month else key
            sublabel = f"{len(month_tasks)} task{'s' if len(month_tasks) > 1 else ''} completed"
            result.append(GroupedTasks(label=label, sublabel=sublabel, tasks=month_tasks))
        return result
