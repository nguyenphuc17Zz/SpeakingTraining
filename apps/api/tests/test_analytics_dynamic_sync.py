import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_analytics_dashboard_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/dashboard?period=30d")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert "metrics" in data
        assert "period" in data
        assert len(data["metrics"]) > 0


@pytest.mark.asyncio
async def test_analytics_diagnostic_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/diagnostic?period=30d")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_attempts" in data
        assert "pillars" in data
        assert "reflex" in data["pillars"]
        assert "keigo" in data["pillars"]
        assert "pitch" in data["pillars"]
        assert "situations" in data["pillars"]
        assert "diagnostic_report" in data
