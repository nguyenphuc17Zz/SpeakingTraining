import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_furigana_resolver_single():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"text": "明日、日本語の勉強を始めます。"}
        resp = await client.post("/api/v1/speech/furigana", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == "明日、日本語の勉強を始めます。"
        assert "hiragana" in data
        assert "ruby" in data
        assert len(data["ruby"]) >= 1

        # Verify ruby chunk structure
        has_kanji_reading = any(c.get("reading") is not None for c in data["ruby"])
        assert has_kanji_reading is True


@pytest.mark.asyncio
async def test_furigana_resolver_batch():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "texts": [
                "部長はお帰りになりました。",
                "週末は映画を見に行きます。",
            ]
        }
        resp = await client.post("/api/v1/speech/furigana/batch", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert len(data["results"]) == 2
        for item in data["results"]:
            assert "text" in item
            assert "hiragana" in item
            assert "ruby" in item
