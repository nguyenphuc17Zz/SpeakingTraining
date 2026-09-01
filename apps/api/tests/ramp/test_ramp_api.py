"""End-to-end API tests for Mode 6 (Speaking Ramp /api/v1/ramp/*)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ramp_api_session_lifecycle(client: AsyncClient):
    # 1. Get stages metadata
    stages_resp = await client.get("/api/v1/ramp/stages")
    assert stages_resp.status_code == 200
    stages_data = stages_resp.json()
    assert len(stages_data["stages"]) == 11
    assert len(stages_data["support_levels"]) == 8

    # 2. Create a session
    create_resp = await client.post(
        "/api/v1/ramp/sessions",
        json={
            "desired_minutes": 15,
            "session_goal": "fluency",
            "current_stage": 2,
            "support_level": 3,
        },
    )
    assert create_resp.status_code == 200
    session_data = create_resp.json()
    session_id = session_data["id"]
    assert session_data["stage"] == 2
    assert session_data["support_level"] == 3

    # 3. Get session state
    get_resp = await client.get(f"/api/v1/ramp/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == session_id

    # 4. Generate next exercise
    next_ex_resp = await client.post(f"/api/v1/ramp/sessions/{session_id}/next-exercise")
    assert next_ex_resp.status_code == 200
    ex_data = next_ex_resp.json()
    exercise_id = ex_data["exercise_id"]
    assert ex_data["task_spec"]["stage"] == 2

    # 5. Submit an attempt
    submit_resp = await client.post(
        f"/api/v1/ramp/sessions/{session_id}/exercises/{exercise_id}/submit",
        json={
            "user_transcript": "昨日は仕事が終わってから、日本語の勉強をしました。",
            "support_level_used": 2,
            "used_hint": False,
            "response_latency_ms": 1200,
        },
    )
    assert submit_resp.status_code == 200
    result_data = submit_resp.json()
    assert "score" in result_data
    assert "feedback" in result_data
    assert "delta" in result_data

    # 6. Complete session
    comp_resp = await client.post(f"/api/v1/ramp/sessions/{session_id}/complete")
    assert comp_resp.status_code == 200
    summary = comp_resp.json()
    assert summary["exercises_completed"] == 1


@pytest.mark.asyncio
async def test_ramp_api_infinite_session(client: AsyncClient):
    """Verify session creation with desired_minutes=0 (infinite mode)."""
    resp = await client.post(
        "/api/v1/ramp/sessions",
        json={
            "desired_minutes": 0,
            "session_goal": "general",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["desired_minutes"] == 0
    assert data["exercises_total"] == 999


@pytest.mark.asyncio
async def test_ramp_api_session_goals_stages(client: AsyncClient):
    """Verify session creation with different session goals maps to appropriate starting stages."""
    goals_and_stages = [
        ("fluency", 1, 2),
        ("elaboration", 4, 2),
        ("independence", 7, 1),
    ]
    for goal, expected_stage, expected_support in goals_and_stages:
        resp = await client.post(
            "/api/v1/ramp/sessions",
            json={
                "desired_minutes": 10,
                "session_goal": goal,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == expected_stage, f"Goal {goal} should start at stage {expected_stage}"
        assert data["support_level"] == expected_support
