from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


@router.post("/profile-image", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_profile_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UploadService(db)
    try:
        path, url = await service.upload_profile_image(user_id=user.id, file=file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return UploadResponse(path=path, url=url)


@router.post("/company-image", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_company_image(
    work_experience_id: UUID = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UploadService(db)
    try:
        path, url = await service.upload_company_image(
            user_id=user.id,
            work_experience_id=work_experience_id,
            file=file,
        )
    except ValueError as exc:
        status_code = 404 if str(exc) == "Work experience not found" else 400
        raise HTTPException(status_code=status_code, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return UploadResponse(path=path, url=url)


@router.post(
    "/certification-image",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_certification_image(
    certification_id: UUID = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UploadService(db)
    try:
        path, url = await service.upload_certification_image(
            user_id=user.id,
            certification_id=certification_id,
            file=file,
        )
    except ValueError as exc:
        status_code = 404 if str(exc) == "Certification not found" else 400
        raise HTTPException(status_code=status_code, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return UploadResponse(path=path, url=url)


@router.post("/project-image", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_project_image(
    project_id: UUID = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UploadService(db)
    try:
        path, url = await service.upload_project_image(
            user_id=user.id,
            project_id=project_id,
            file=file,
        )
    except ValueError as exc:
        status_code = 404 if str(exc) == "Project not found" else 400
        raise HTTPException(status_code=status_code, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return UploadResponse(path=path, url=url)


@router.post(
    "/personal-project-image",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_personal_project_image(
    personal_project_id: UUID = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UploadService(db)
    try:
        path, url = await service.upload_personal_project_image(
            user_id=user.id,
            personal_project_id=personal_project_id,
            file=file,
        )
    except ValueError as exc:
        status_code = 404 if str(exc) == "Personal project not found" else 400
        raise HTTPException(status_code=status_code, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return UploadResponse(path=path, url=url)


@router.post("/resume", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UploadService(db)
    try:
        path, url = await service.upload_resume(user_id=user.id, file=file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return UploadResponse(path=path, url=url)
