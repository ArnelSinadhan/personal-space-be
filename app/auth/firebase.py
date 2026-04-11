import json
from datetime import timedelta
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials

from app.config import settings

_app: firebase_admin.App | None = None


def init_firebase() -> firebase_admin.App:
    """Initialize Firebase Admin SDK once. Safe to call multiple times."""
    global _app
    if _app is not None:
        return _app

    if settings.firebase_service_account_key:
        cred_dict = json.loads(settings.firebase_service_account_key)
        cred = credentials.Certificate(cred_dict)
    elif settings.firebase_service_account_path:
        cred = credentials.Certificate(settings.firebase_service_account_path)
    else:
        raise RuntimeError(
            "Missing Firebase credentials. "
            "Set FIREBASE_SERVICE_ACCOUNT_KEY or FIREBASE_SERVICE_ACCOUNT_PATH."
        )

    _app = firebase_admin.initialize_app(cred, {
        "storageBucket": settings.firebase_storage_bucket,
    })
    return _app


def get_firebase_app() -> firebase_admin.App:
    if _app is None:
        return init_firebase()
    return _app


def verify_firebase_id_token(
    token: str,
    *,
    check_revoked: bool = False,
) -> dict[str, Any]:
    return auth.verify_id_token(
        token,
        check_revoked=check_revoked,
        app=get_firebase_app(),
    )


def create_firebase_session_cookie(
    id_token: str,
    *,
    expires_in: timedelta,
) -> str:
    return auth.create_session_cookie(
        id_token,
        expires_in=expires_in,
        app=get_firebase_app(),
    )


def verify_firebase_session_cookie(
    session_cookie: str,
    *,
    check_revoked: bool = True,
) -> dict[str, Any]:
    return auth.verify_session_cookie(
        session_cookie,
        check_revoked=check_revoked,
        app=get_firebase_app(),
    )


def revoke_firebase_refresh_tokens(uid: str) -> None:
    auth.revoke_refresh_tokens(uid, app=get_firebase_app())


def delete_firebase_user(uid: str) -> None:
    auth.delete_user(uid, app=get_firebase_app())


def update_firebase_user_password(uid: str, password: str) -> None:
    auth.update_user(uid, password=password, app=get_firebase_app())
