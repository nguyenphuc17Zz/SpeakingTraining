import pytest
from httpx import ASGITransport, AsyncClient

from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.conversation_intelligence.models import AnalysisCorrection, TurnAnalysis
from app.domains.conversation_intelligence.worker import AnalysisWorker
from app.domains.personas.models import Persona
from app.domains.users.models import User
from app.main import app


@pytest.mark.asyncio
async def test_analysis_api_flow(client: AsyncClient, db_session):
    # Seed user & persona
    user = User(display_name="Test Learner")
    db_session.add(user)
    persona = Persona(
        name="Takeshi-senpai",
        description="A friendly Japanese college senior.",
        role="Friendly Senpai",
        speaking_style="Casual Tameguchi",
        personality="Warm and supportive",
        difficulty="N3",
        is_system=True,
    )
    db_session.add(persona)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(persona)

    # Create session and user turn
    session = ConversationSession(
        user_id=user.id,
        persona_id=persona.id,
        mode="coaching",
        status="active",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    turn = ConversationTurn(
        session_id=session.id,
        sequence=1,
        speaker="user",
        transcript="昨日、友達と映画を見たです。",
        metrics={"confidence": 0.95},
    )
    db_session.add(turn)
    await db_session.commit()
    await db_session.refresh(turn)

    # 1. Trigger Turn Analysis
    resp = await client.post(f"/api/v1/conversations/{session.id}/turns/{turn.id}/analysis")
    assert resp.status_code == 200
    job_data = resp.json()
    assert job_data["type"] == "turn_analysis"
    assert job_data["status"] == "queued"
    job_id = job_data["id"]

    # 2. Check Job Status
    status_resp = await client.get(f"/api/v1/analyses/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == job_id

    # 3. Simulate Worker Execution
    worker = AnalysisWorker()
    await worker.execute_job(job_id, db_session)

    # 4. Get Turn Analysis Result
    analysis_resp = await client.get(f"/api/v1/conversations/{session.id}/turns/{turn.id}/analysis")
    assert analysis_resp.status_code == 200
    turn_analysis = analysis_resp.json()
    assert turn_analysis["turn_id"] == turn.id
    assert turn_analysis["session_id"] == session.id
    assert "overall_quality_score" in turn_analysis

    # 5. Trigger Session Analysis
    s_resp = await client.post(f"/api/v1/conversations/{session.id}/analysis")
    assert s_resp.status_code == 200
    s_job_id = s_resp.json()["id"]

    await worker.execute_job(s_job_id, db_session)

    # 6. Get Full Session Summary
    sum_resp = await client.get(f"/api/v1/conversations/{session.id}/analysis")
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    assert sum_data["session_id"] == session.id
    assert sum_data["session_analysis"] is not None
    assert len(sum_data["turn_analyses"]) >= 1

    # 7. Submit Feedback
    fb_payload = {
        "rating": "helpful",
        "reason": "Clear explanation of past tense polite form",
        "turn_analysis_id": turn_analysis["id"],
    }
    fb_resp = await client.post("/api/v1/analyses/feedback", json=fb_payload)
    assert fb_resp.status_code == 200
    fb_data = fb_resp.json()
    assert fb_data["rating"] == "helpful"
    assert fb_data["reason"] == "Clear explanation of past tense polite form"
