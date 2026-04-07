from pydantic import BaseModel


class CompletedTaskOut(BaseModel):
    id: str
    title: str
    project_name: str
    company_name: str
    completed_at: str


class GroupedTasks(BaseModel):
    label: str
    sublabel: str | None = None
    tasks: list[CompletedTaskOut]


class ReportSummary(BaseModel):
    today: int
    this_week: int
    this_month: int
    streak: int


class ReportSummaryResponse(BaseModel):
    data: ReportSummary


class ReportCompletedResponse(BaseModel):
    data: list[GroupedTasks]
