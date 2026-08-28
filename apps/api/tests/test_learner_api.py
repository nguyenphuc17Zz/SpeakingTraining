import pytest
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learner_memory.contracts import MemoryCandidate, MemoryType
from app.domains.learner_memory.merger import MemoryMerger


@pytest.mark.asyncio
async def test_learner_api_endpoints(client: AsyncClient, db_session: AsyncSession):
    # 1. Get Initial Profile
    resp = await client.get("/api/v1/learner/profile")
    assert resp.status_code == 200
    profile_data = resp.json()
    assert "overall_level" in profile_data
    assert "level_confidence" in profile_data
    user_id = profile_data["user_id"]

    # 2. Seed a candidate via domain merger to simulate session completion
    merger = MemoryMerger(db_session)
    candidate = MemoryCandidate(
        memory_type=MemoryType.PARTICLE,
        key="particle.ha_vs_ga",
        statement="Nhầm lẫn trợ từ は và が",
        category="particle",
        severity="MUST_FIX",
        confidence=0.9,
        evidence_weight=1.0,
        original_snippet="私は寿司が好き",
        corrected_snippet="私は寿司が好き",
        session_id="session-test-api",
    )
    await merger.merge_candidates(user_id=user_id, candidates=[candidate])
    await db_session.commit()

    # 3. List Memories
    m_resp = await client.get("/api/v1/learner/memories")
    assert m_resp.status_code == 200
    memories = m_resp.json()
    assert len(memories) >= 1
    mem_id = memories[0]["id"]

    # 4. Get Memory Detail & Evidence
    det_resp = await client.get(f"/api/v1/learner/memories/{mem_id}")
    assert det_resp.status_code == 200
    detail = det_resp.json()
    assert detail["key"] == "particle.ha_vs_ga"

    ev_resp = await client.get(f"/api/v1/learner/memories/{mem_id}/evidence")
    assert ev_resp.status_code == 200
    assert len(ev_resp.json()) >= 1

    # 5. Top Weaknesses & Priorities
    weak_resp = await client.get("/api/v1/learner/weaknesses")
    assert weak_resp.status_code == 200
    assert len(weak_resp.json()) >= 1

    prio_resp = await client.get("/api/v1/learner/priorities")
    assert prio_resp.status_code == 200
    assert len(prio_resp.json()) >= 1

    # 6. User Feedback / Dismiss Action
    fb_resp = await client.post(
        f"/api/v1/learner/memories/{mem_id}/feedback",
        json={"action": "dismiss", "feedback_text": "Tôi cố tình dùng"},
    )
    assert fb_resp.status_code == 200
    assert fb_resp.json()["action"] == "dismiss"

    # Verify dismissed memory is not in active weaknesses
    weak_after = await client.get("/api/v1/learner/weaknesses")
    assert not any(w["id"] == mem_id for w in weak_after.json())

    # 7. Recalculate Profile
    recalc_resp = await client.post("/api/v1/learner/profile/recalculate")
    assert recalc_resp.status_code == 200
    assert "last_recalculated_at" in recalc_resp.json()
