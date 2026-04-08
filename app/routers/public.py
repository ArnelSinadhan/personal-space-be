"""
Public portfolio endpoints — no authentication required.
These are consumed by the portfolio site.
Sensitive fields (phone, address) are excluded.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.profile import EducationEntry, Profile, WorkExperience
from app.models.project import Project
from app.models.user import User
from app.services.storage_service import StorageService

router = APIRouter(prefix="/api/v1/public", tags=["public"])


async def _get_first_user(db: AsyncSession) -> User:
    """Get the primary user. For a personal app there's only one."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="No user found")
    return user


@router.get("/profile")
async def public_profile(db: AsyncSession = Depends(get_db)):
    storage = StorageService()
    user = await _get_first_user(db)
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == user.id)
        .options(selectinload(Profile.skills), selectinload(Profile.social_links))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        return {"data": None}

    return {
        "data": {
            "name": profile.name,
            "role": profile.role,
            "avatar": await storage.resolve_profile_url(profile.avatar_url),
            "about": profile.about,
            "skills": [s.name for s in profile.skills],
            "social_links": [
                {"label": l.label, "url": l.url} for l in profile.social_links
            ],
        }
    }


@router.get("/work-experience")
async def public_work_experience(db: AsyncSession = Depends(get_db)):
    storage = StorageService()
    user = await _get_first_user(db)
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id).options(
            selectinload(Profile.work_experiences)
        )
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        return {"data": []}

    return {
        "data": [
            {
                "title": w.title,
                "company": w.company,
                "start_date": w.start_date,
                "end_date": w.end_date,
                "is_current": w.is_current,
                "image_url": await storage.resolve_company_url(w.image_url),
            }
            for w in profile.work_experiences
        ]
    }


@router.get("/projects")
async def public_projects(db: AsyncSession = Depends(get_db)):
    storage = StorageService()
    user = await _get_first_user(db)
    result = await db.execute(
        select(WorkExperience)
        .join(Profile, WorkExperience.profile_id == Profile.id)
        .where(Profile.user_id == user.id)
        .options(
            selectinload(WorkExperience.projects).selectinload(Project.tech_stack)
        )
    )
    work_experiences = result.scalars().all()

    projects = []
    for work_experience in work_experiences:
        for p in work_experience.projects:
            if not p.is_public:
                continue
            projects.append({
                "name": p.name,
                "description": p.description,
                "image_url": await storage.resolve_project_url(p.image_url),
                "company": work_experience.company,
                "tech_stack": [s.name for s in p.tech_stack],
            })

    return {"data": projects}


@router.get("/education")
async def public_education(db: AsyncSession = Depends(get_db)):
    user = await _get_first_user(db)
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id).options(
            selectinload(Profile.education_entries)
        )
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        return {"data": []}

    return {
        "data": [
            {"degree": e.degree, "school": e.school, "years": e.years}
            for e in profile.education_entries
        ]
    }
