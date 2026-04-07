import json

import firebase_admin
from firebase_admin import credentials

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
