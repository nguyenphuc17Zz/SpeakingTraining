import pytest
from httpx import AsyncClient

from app.domains.vocabulary.schemas import (
    SaveVocabularyNotebookRequest,
    VocabularyLookupRequest,
)


@pytest.mark.asyncio
async def test_vocabulary_ai_lookup_endpoint(client: AsyncClient):
    """Test AI lookup endpoint returns structured context-aware Japanese response."""
    payload = {
        "query": "申し訳ございません",
        "context": "本日の会議に遅れてしまい、誠に申し訳ございません。",
        "target_level": "N2",
        "register_preference": "business",
    }
    response = await client.post("/api/v1/vocabulary/ai-lookup", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "best_match" in data
    bm = data["best_match"]
    assert "expression" in bm
    assert "reading" in bm
    assert "meaning_vi" in bm
    assert "nuance_explanation" in bm
    assert "examples" in bm
    assert len(bm["examples"]) >= 1

    assert "alternatives" in data
    assert "original_query" in data
    assert data["original_query"] == "申し訳ございません"


@pytest.mark.asyncio
async def test_vocabulary_save_notebook_endpoint(client: AsyncClient):
    """Test saving a looked-up vocabulary word into the learner's notebook and training catalog."""
    payload = {
        "expression": "恐縮ですが",
        "reading": "きょうしゅくですが",
        "meaning_vi": "Tôi rất ngại / xin phép làm phiền nhưng mà...",
        "nuance_explanation": "Dùng để mở lời khi nhờ vả một cách lịch sự, nhún nhường trong công việc.",
        "context": "大変恐縮ですが、こちらの資料をご確認いただけますでしょうか。",
        "jlpt_level": "N2",
        "part_of_speech": "Liên từ / Kính ngữ",
        "register": "Business Keigo",
        "tags": ["business", "keigo", "polite"],
    }
    response = await client.post("/api/v1/vocabulary/save-notebook", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "item_id" in data
    assert "message" in data
