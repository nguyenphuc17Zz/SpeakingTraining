import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_activity_heatmap_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/activity-heatmap?weeks=14")
        assert resp.status_code == 200
        data = resp.json()
        assert data["weeks"] == 14
        assert data["total_days"] == 98
        assert "total_speaking_minutes" in data
        assert len(data["days"]) == 98
        for d in data["days"]:
            assert "date" in d
            assert "minutes" in d
            assert "level" in d
