import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_overview(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200

    data = response.json()["data"]
    assert data["first_name"] == "there"
    assert data["company_count"] == 0
    assert data["total_projects"] == 0
    assert data["total_tasks"] == 0
    assert data["vault_entry_count"] == 0
    assert data["vault_category_count"] == 0
    assert data["status_counts"]["todo"] == 0
    assert data["profile"]["percent"] >= 0
