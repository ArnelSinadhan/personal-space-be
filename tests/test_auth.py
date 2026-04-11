import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.auth import firebase
from app.models.user import User


@pytest.mark.asyncio
async def test_create_session_exchanges_id_token_and_upserts_user(
    client: AsyncClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        firebase,
        "verify_firebase_id_token",
        lambda token, check_revoked=False: {
            "uid": "session-user-123",
            "email": "session@example.com",
        },
    )
    monkeypatch.setattr(
        firebase,
        "create_firebase_session_cookie",
        lambda id_token, expires_in: "session-cookie-value",
    )

    response = await client.post(
        "/api/v1/auth/session",
        json={"id_token": "firebase-id-token"},
    )

    assert response.status_code == 200
    assert response.json()["session_cookie"] == "session-cookie-value"
    assert response.json()["expires_in_seconds"] > 0

    created_user = await db_session.scalar(
        select(User).where(User.firebase_uid == "session-user-123")
    )
    assert created_user is not None
    assert created_user.email == "session@example.com"


@pytest.mark.asyncio
async def test_verify_session_returns_authenticated_user(
    client: AsyncClient,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        firebase,
        "verify_firebase_session_cookie",
        lambda session_cookie, check_revoked=True: {
            "uid": "verified-user-456",
            "email": "verified@example.com",
        },
    )

    response = await client.post(
        "/api/v1/auth/session/verify",
        json={"session_cookie": "session-cookie-value"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": True,
        "uid": "verified-user-456",
        "email": "verified@example.com",
    }

    created_user = await db_session.scalar(
        select(User).where(User.firebase_uid == "verified-user-456")
    )
    assert created_user is not None


@pytest.mark.asyncio
async def test_revoke_session_revokes_refresh_tokens(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    revoked_uids: list[str] = []

    monkeypatch.setattr(
        firebase,
        "verify_firebase_session_cookie",
        lambda session_cookie, check_revoked=True: {
            "uid": "revoked-user-789",
            "email": "revoked@example.com",
        },
    )
    monkeypatch.setattr(
        firebase,
        "revoke_firebase_refresh_tokens",
        lambda uid: revoked_uids.append(uid),
    )

    response = await client.request(
        "DELETE",
        "/api/v1/auth/session",
        json={"session_cookie": "session-cookie-value"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Session revoked"}
    assert revoked_uids == ["revoked-user-789"]
