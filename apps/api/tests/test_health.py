import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_general_health(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "Japanese Speaking AI Training OS" in data["app_name"]


@pytest.mark.asyncio
async def test_db_health(client: AsyncClient):
    response = await client.get("/api/v1/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["connected"] is True


@pytest.mark.asyncio
async def test_redis_health_graceful_handling(client: AsyncClient):
    # Redis might not be running in isolated unit test environments
    response = await client.get("/api/v1/health/redis")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "component" in data
    assert data["component"] == "redis"
