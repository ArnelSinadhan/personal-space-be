from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import auth as firebase_auth
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import firebase
from app.auth.middleware import get_or_create_user_from_claims
from app.config import settings
from app.database import get_db
from app.schemas.auth import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionVerifyRequest,
    SessionVerifyResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/session", response_model=SessionCreateResponse)
async def create_session(
    payload: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    expires_in = timedelta(days=settings.firebase_session_expire_days)

    try:
        decoded = firebase.verify_firebase_id_token(payload.id_token)
        session_cookie = firebase.create_firebase_session_cookie(
            payload.id_token,
            expires_in=expires_in,
        )
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not create session: {exc}",
        )

    await get_or_create_user_from_claims(decoded, db)

    return SessionCreateResponse(
        session_cookie=session_cookie,
        expires_in_seconds=int(expires_in.total_seconds()),
    )


@router.post("/session/verify", response_model=SessionVerifyResponse)
async def verify_session(
    payload: SessionVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        decoded = firebase.verify_firebase_session_cookie(payload.session_cookie)
    except Exception:
        return SessionVerifyResponse(authenticated=False)

    await get_or_create_user_from_claims(decoded, db)

    return SessionVerifyResponse(
        authenticated=True,
        uid=str(decoded.get("uid", "")) or None,
        email=str(decoded.get("email", "")) or None,
    )


@router.delete("/session", response_model=MessageResponse)
async def revoke_session(payload: SessionVerifyRequest):
    try:
        decoded = firebase.verify_firebase_session_cookie(payload.session_cookie)
        uid = decoded.get("uid")
        if not uid:
            raise ValueError("Missing uid in session cookie")
        firebase.revoke_firebase_refresh_tokens(str(uid))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not revoke session: {exc}",
        )

    return MessageResponse(message="Session revoked")
