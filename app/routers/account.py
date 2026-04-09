from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.account import PasswordUpdate
from app.schemas.common import MessageResponse
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/v1/account", tags=["account"])


@router.put("/password", response_model=MessageResponse)
async def update_password(
    payload: PasswordUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    try:
        await service.update_password(user, payload.new_password)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Password update failed: {exc}")
    return MessageResponse(message="Password updated")


@router.delete("", response_model=MessageResponse)
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    try:
        await service.delete_account(user)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Account deletion failed: {exc}")
    return MessageResponse(message="Account deleted")
