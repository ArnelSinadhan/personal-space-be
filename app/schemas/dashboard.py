from pydantic import BaseModel


class DashboardProfileCompleteness(BaseModel):
    percent: int
    missing: list[str]


class DashboardVaultCategoryDatum(BaseModel):
    name: str
    value: int
    color: str


class DashboardStatusCounts(BaseModel):
    todo: int
    in_progress: int
    done: int
    blocked: int
    pending: int


class DashboardDonutDatum(BaseModel):
    name: str
    value: int
    color: str


class DashboardTimeDatum(BaseModel):
    name: str
    tasks: int


class DashboardCompanyBarDatum(BaseModel):
    name: str
    done: int
    active: int
    blocked: int


class DashboardProjectProgressDatum(BaseModel):
    name: str
    progress: int
    fill: str


class DashboardTechStackDatum(BaseModel):
    name: str
    count: int


class DashboardActiveTask(BaseModel):
    id: str
    title: str
    status: str
    completed_at: str | None = None
    sort_order: int = 0
    project_name: str
    company_name: str


class DashboardOverviewOut(BaseModel):
    first_name: str
    profile: DashboardProfileCompleteness
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
    status_counts: DashboardStatusCounts
    donut_data: list[DashboardDonutDatum]
    daily_bar_data: list[DashboardTimeDatum]
    weekly_area_data: list[DashboardTimeDatum]
    company_bar_data: list[DashboardCompanyBarDatum]
    project_radial_data: list[DashboardProjectProgressDatum]
    tech_stack_data: list[DashboardTechStackDatum]
    active_tasks: list[DashboardActiveTask]
    vault_entry_count: int
    vault_category_count: int
    vault_category_data: list[DashboardVaultCategoryDatum]
    has_data: bool


class DashboardOverviewResponse(BaseModel):
    data: DashboardOverviewOut
