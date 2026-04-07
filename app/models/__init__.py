# Import all models here so Alembic can discover them via Base.metadata
from app.models.base import Base
from app.models.company import Company
from app.models.profile import EducationEntry, Profile, Skill, SocialLink, WorkExperience
from app.models.project import Project
from app.models.resume import Resume, ResumeEducation, ResumeExperience, ResumeLink, ResumeProject
from app.models.todo import Todo
from app.models.user import User
from app.models.vault import VaultCategory, VaultEntry, VaultPin

__all__ = [
    "Base",
    "Company",
    "EducationEntry",
    "Profile",
    "Project",
    "Resume",
    "ResumeEducation",
    "ResumeExperience",
    "ResumeLink",
    "ResumeProject",
    "Skill",
    "SocialLink",
    "Todo",
    "User",
    "VaultCategory",
    "VaultEntry",
    "VaultPin",
    "WorkExperience",
]
