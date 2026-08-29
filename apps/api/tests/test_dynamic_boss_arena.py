import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_dynamic_boss_generation_and_arena():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List existing bosses
        resp = await client.get("/api/v1/game/bosses")
        assert resp.status_code == 200
        initial_bosses = resp.json()
        assert isinstance(initial_bosses, list)

        # 2. Generate a dynamic AI Boss
        gen_payload = {
            "topic": "Đàm Phán Dự Án Với Khách Hàng VIP Tokyo",
            "difficulty": "hard",
            "required_level": 5,
        }
        gen_resp = await client.post("/api/v1/game/bosses/generate", json=gen_payload)
        assert gen_resp.status_code == 200
        new_boss = gen_resp.json()
        assert "id" in new_boss
        assert new_boss["difficulty"] == "hard"
        assert new_boss["required_level"] == 5
        assert len(new_boss.get("objectives", [])) >= 1

        # 3. Evaluate arena battle turn
        turn_payload = {
            "round_index": 1,
            "user_speech": "本日の提案について、詳しくご説明申し上げます。",
            "latency_ms": 1500.0,
        }
        turn_resp = await client.post(f"/api/v1/game/bosses/{new_boss['id']}/evaluate-turn", json=turn_payload)
        assert turn_resp.status_code == 200
        turn_data = turn_resp.json()
        assert "turn_score" in turn_data
        assert "damage_dealt" in turn_data
        assert turn_data["damage_dealt"] > 0
        assert "feedback_vi" in turn_data
