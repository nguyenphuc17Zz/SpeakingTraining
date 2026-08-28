import base64
import pytest
from httpx import AsyncClient

from tests.unit.test_pronunciation_pipeline import create_synthetic_wav


@pytest.mark.asyncio
async def test_pronunciation_analyze_and_history_api(client: AsyncClient, db_session):
    # 1. Test Targets API
    resp_targets = await client.get("/api/v1/pronunciation/targets")
    assert resp_targets.status_code == 200
    targets = resp_targets.json()
    assert len(targets) > 0
    assert any("学校" in t["target_text"] or "おばあさん" in t["target_text"] for t in targets)

    # 2. Test Synchronous Analyze API
    wav_bytes = create_synthetic_wav(duration_sec=1.5, freq_hz=220.0, amplitude=0.4)
    audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")

    payload = {
        "audio_base64": audio_b64,
        "target_text": "がっこう",
        "expected_reading": "がっこう",
        "target_type": "word",
        "reference_type": "synthetic",
    }

    resp_analyze = await client.post("/api/v1/pronunciation/analyze", json=payload)
    assert resp_analyze.status_code == 200
    data = resp_analyze.json()
    assert data["analysis_status"] == "completed"
    assert data["overall_score"] is not None
    assert "result" in data
    assert data["result"]["mora_timing_score"] is not None

    attempt_id = data["id"]

    # 3. Test Get Attempt API
    resp_get = await client.get(f"/api/v1/pronunciation/attempts/{attempt_id}")
    assert resp_get.status_code == 200
    get_data = resp_get.json()
    assert get_data["id"] == attempt_id
    assert get_data["overall_score"] == data["overall_score"]

    # 4. Test History API
    resp_hist = await client.get("/api/v1/pronunciation/history")
    assert resp_hist.status_code == 200
    hist = resp_hist.json()
    assert len(hist) >= 1
    assert hist[0]["id"] == attempt_id

    # 5. Test Stats API
    resp_stats = await client.get("/api/v1/pronunciation/stats")
    assert resp_stats.status_code == 200
    stats = resp_stats.json()
    assert stats["total_attempts"] >= 1
    assert stats["avg_overall_score"] > 0.0

    # 6. Test Enqueue API
    resp_enqueue = await client.post("/api/v1/pronunciation/enqueue", json=payload)
    assert resp_enqueue.status_code == 200
    assert resp_enqueue.json()["status"] == "queued"
