from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Profile completeness
# ---------------------------------------------------------------------------


class DashboardProfileCompleteness(BaseModel):
    percent: int
    missing: list[str]


# ---------------------------------------------------------------------------
# Flat summary counters (project + task counts, streak)
# ---------------------------------------------------------------------------


class DashboardSummary(BaseModel):
    company_count: int
    total_projects: int
    active_project_count: int
    maintenance_project_count: int
    completed_project_count: int
    archived_project_count: int
    total_tasks: int
    completed_today: int
    completed_this_week: int
    streak: int


# ---------------------------------------------------------------------------
# Status counts (raw numbers per status key)
# ---------------------------------------------------------------------------


class DashboardStatusCounts(BaseModel):
    todo: int
    in_progress: int
    done: int
    blocked: int
    pending: int


# ---------------------------------------------------------------------------
# Task distribution (horizontal bar / pie chart)
# Keeps `status` as the raw key so the frontend can drive colour/icon logic
# without re-parsing the human-readable `name`.
# ---------------------------------------------------------------------------


class DashboardTaskDistributionItem(BaseModel):
    name: str   # human label, e.g. "In Progress"
    value: int
    color: str
    status: str  # raw key: "todo" | "in_progress" | "done" | "blocked" | "pending"


# ---------------------------------------------------------------------------
# Time-series trend data (daily / weekly)
# ---------------------------------------------------------------------------


class DashboardTimeDatum(BaseModel):
    name: str
    tasks: int


# ---------------------------------------------------------------------------
# Project health
# Carries full per-status task breakdown so the frontend can render progress
# bars, warning badges, and navigate directly to the project detail page.
# ---------------------------------------------------------------------------


class DashboardProjectHealth(BaseModel):
    id: str
    name: str
    lifecycle_status: str  # "active" | "maintenance"
    progress: int          # done_tasks / total_tasks * 100, rounded
    total_tasks: int
    done_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    pending_tasks: int
    todo_tasks: int
    color: str             # backend-assigned chart colour


# ---------------------------------------------------------------------------
# Tech stack
# ---------------------------------------------------------------------------


class DashboardTechStackDatum(BaseModel):
    name: str
    count: int


# ---------------------------------------------------------------------------
# Vault summary (nested)
# ---------------------------------------------------------------------------


class DashboardVaultCategoryDatum(BaseModel):
    name: str
    value: int
    color: str


class DashboardVaultSummary(BaseModel):
    entry_count: int
    category_count: int
    categories: list[DashboardVaultCategoryDatum]


# ---------------------------------------------------------------------------
# Top-level response
#
# Metadata field:
#   project_health_total_count  — explicit count so the frontend never needs
#                                  to call .length on the list; also makes a
#                                  future pagination upgrade non-breaking.
# ---------------------------------------------------------------------------


class DashboardOverviewResponse(BaseModel):
    first_name: str

    profile: DashboardProfileCompleteness
    summary: DashboardSummary
    status_counts: DashboardStatusCounts

    task_distribution: list[DashboardTaskDistributionItem]
    weekly_trend: list[DashboardTimeDatum]
    daily_trend: list[DashboardTimeDatum]

    project_health: list[DashboardProjectHealth]
    project_health_total_count: int

    tech_stack: list[DashboardTechStackDatum]
    vault: DashboardVaultSummary

    has_data: bool


class DashboardPortfolioBreakdownItem(BaseModel):
    name: str
    value: int


class DashboardPortfolioInsightsSummary(BaseModel):
    unique_visitors: int
    total_visits: int
    returning_visitors: int
    recent_visitors: int


class DashboardPortfolioVisitor(BaseModel):
    visitor_id: str
    first_visited_at: datetime
    last_visited_at: datetime
    visit_count: int
    last_path: str
    source: str | None = None
    referrer: str | None = None
    country_code: str | None = None
    region: str | None = None
    city: str | None = None
    user_agent: str | None = None


class DashboardPortfolioInsightsResponse(BaseModel):
    summary: DashboardPortfolioInsightsSummary
    top_locations: list[DashboardPortfolioBreakdownItem]
    top_sources: list[DashboardPortfolioBreakdownItem]
    visitors: list[DashboardPortfolioVisitor]
