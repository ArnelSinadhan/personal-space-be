import enum


class TodoStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    PENDING = "pending"


class ResumeTemplate(str, enum.Enum):
    CLASSIC = "classic"
    MODERN = "modern"
    MINIMAL = "minimal"
    PROFESSIONAL = "professional"


class ReportPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
