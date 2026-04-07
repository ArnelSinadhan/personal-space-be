import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_set_and_verify_pin(client: AsyncClient):
    # Set PIN
    response = await client.post("/api/v1/vault/set-pin", json={"pin": "123456"})
    assert response.status_code == 200

    # Verify correct PIN
    response = await client.post("/api/v1/vault/verify-pin", json={"pin": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["vault_token"] is not None

    # Verify wrong PIN
    response = await client.post("/api/v1/vault/verify-pin", json={"pin": "000000"})
    assert response.status_code == 200
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_vault_category_crud(client: AsyncClient):
    # Create
    response = await client.post("/api/v1/vault/categories", json={
        "name": "Social",
        "icon_name": "Users",
    })
    assert response.status_code == 201
    cat_id = response.json()["id"]

    # List
    response = await client.get("/api/v1/vault/categories")
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1

    # Update
    response = await client.put(f"/api/v1/vault/categories/{cat_id}", json={
        "name": "Social Media",
        "icon_name": "Users",
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Social Media"

    # Delete
    response = await client.delete(f"/api/v1/vault/categories/{cat_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_vault_entry_crud(client: AsyncClient):
    # Create category first
    response = await client.post("/api/v1/vault/categories", json={
        "name": "Work", "icon_name": "Laptop",
    })
    cat_id = response.json()["id"]

    # Create entry — password should be encrypted/decrypted transparently
    response = await client.post("/api/v1/vault/entries", json={
        "title": "Gmail",
        "username": "john@example.com",
        "password": "SuperSecret123!",
        "category_id": cat_id,
        "icon_name": "Mail",
    })
    assert response.status_code == 201
    entry = response.json()
    entry_id = entry["id"]
    assert entry["password"] is None
    assert entry["has_password"] is True

    verify = await client.post("/api/v1/vault/verify-pin", json={"pin": "123456"})
    if verify.status_code != 200 or not verify.json()["success"]:
        await client.post("/api/v1/vault/set-pin", json={"pin": "123456"})
        verify = await client.post("/api/v1/vault/verify-pin", json={"pin": "123456"})
    vault_token = verify.json()["vault_token"]

    response = await client.get(
        f"/api/v1/vault/entries/{entry_id}/password",
        headers={"Authorization": f"Bearer {vault_token}"},
    )
    assert response.status_code == 200
    assert response.json()["password"] == "SuperSecret123!"

    # List entries
    response = await client.get("/api/v1/vault/entries")
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1
    assert response.json()["data"][0]["password"] is None

    # Update
    response = await client.put(f"/api/v1/vault/entries/{entry_id}", json={
        "password": "NewPassword456!",
    })
    assert response.status_code == 200
    assert response.json()["password"] is None

    response = await client.get(
        f"/api/v1/vault/entries/{entry_id}/password",
        headers={"Authorization": f"Bearer {vault_token}"},
    )
    assert response.status_code == 200
    assert response.json()["password"] == "NewPassword456!"

    # Delete
    response = await client.delete(f"/api/v1/vault/entries/{entry_id}")
    assert response.status_code == 200
