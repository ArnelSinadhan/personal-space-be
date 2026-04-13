import enum


class TodoStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    PENDING = "pending"


class ProjectLifecycleStatus(str, enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ResumeTemplate(str, enum.Enum):
    CLASSIC = "classic"
    MODERN = "modern"
    MINIMAL = "minimal"
    PROFESSIONAL = "professional"


class ReportPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ProjectTestimonialStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
