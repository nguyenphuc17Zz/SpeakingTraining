"""Mode 6 — Speaking Ramp API router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ramp.contracts import RampProgressSnapshot, RampSessionSummary
from app.domains.ramp.ramp_session_service import RampSessionService
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/ramp", tags=["Speaking Ramp — Mode 6"])


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    svc = UserService(db)
    user = await svc.get_or_create_default_user()
    return user.id


# ---------------------------------------------------------------------------
# Session Lifecycle
# ---------------------------------------------------------------------------

@router.post("/sessions")
async def create_session(
    payload: dict[str, Any] | None = None,
    desired_minutes: int = Query(default=15, ge=0, le=180),
    session_goal: str | None = Query(default=None),
    current_stage: int | None = Query(default=None, ge=0, le=10),
    support_level: int | None = Query(default=None, ge=0, le=7),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new Mode 6 Speaking Ramp session."""
    if payload:
        desired_minutes = int(payload.get("desired_minutes", desired_minutes))
        session_goal = payload.get("session_goal", session_goal)
        current_stage = payload.get("current_stage", current_stage)
        support_level = payload.get("support_level", support_level)

    svc = RampSessionService(db)
    session = await svc.create_session(
        user_id=user_id,
        desired_minutes=desired_minutes,
        session_goal=session_goal,
        current_stage=current_stage,
        support_level=support_level,
    )
    return {
        "id": session.id,
        "state": session.state,
        "stage": session.stage,
        "support_level": session.support_level,
        "desired_minutes": session.desired_minutes,
        "exercises_total": session.exercises_total,
        "started_at": session.started_at.isoformat() if session.started_at else None,
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current session state."""
    svc = RampSessionService(db)
    session = await svc.get_session(session_id, user_id)
    if not session:
        raise NotFoundException(f"Session '{session_id}' not found")
    return {
        "id": session.id,
        "state": session.state,
        "stage": session.stage,
        "support_level": session.support_level,
        "exercises_completed": session.exercises_completed,
        "exercises_total": session.exercises_total,
        "milestones_achieved": session.milestones_achieved or [],
    }


@router.post("/sessions/{session_id}/next-exercise")
async def generate_next_exercise(
    session_id: str,
    payload: dict[str, Any] | None = None,
    is_retry: bool = Query(default=False),
    force_followup: bool = Query(default=False),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate the next exercise for the session."""
    if payload:
        is_retry = bool(payload.get("is_retry", is_retry))
        force_followup = bool(payload.get("force_followup", force_followup))

    svc = RampSessionService(db)
    try:
        exercise, task_spec = await svc.generate_next_exercise(
            session_id=session_id,
            user_id=user_id,
            is_retry=is_retry,
            force_followup=force_followup,
        )
    except ValueError as e:
        raise NotFoundException(str(e))

    # Return exercise + task spec (richer than plain Exercise DTO)
    return {
        "exercise_id": exercise.id,
        "exercise_type": exercise.exercise_type,
        "title": exercise.title,
        "instructions": exercise.instructions,
        "ramp_config": (exercise.extra_metadata or {}).get("ramp_config", {}),
        "task_spec": {
            "exercise_type": task_spec.exercise_type.value,
            "stage": task_spec.stage,
            "topic": task_spec.topic,
            "topic_domain": task_spec.topic_domain.value,
            "prompt_jp": task_spec.prompt_jp,
            "prompt_vi": task_spec.prompt_vi,
            "target_duration_sec": task_spec.target_duration_sec,
            "support_level": task_spec.support_level,
            "scaffold": task_spec.scaffold.model_dump(),
            "echo_sentence": task_spec.echo_sentence,
            "template_sentence": task_spec.template_sentence,
            "substitution_variable": task_spec.substitution_variable,
            "seed_sentence": task_spec.seed_sentence,
            "expansion_dimension": task_spec.expansion_dimension,
            "keywords_for_production": task_spec.keywords_for_production,
            "previous_response": task_spec.previous_response,
            "is_retry": task_spec.is_retry,
        },
    }


@router.post("/sessions/{session_id}/exercises/{exercise_id}/submit")
async def submit_attempt(
    session_id: str,
    exercise_id: str,
    payload: dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a speaking attempt for evaluation.
    §37 Immediate feedback + §31 stage progression update.
    """
    user_transcript = payload.get("user_transcript", "").strip()
    audio_base64 = payload.get("audio_base64")
    support_level_used = payload.get("support_level_used")
    used_hint = bool(payload.get("used_hint", False))
    response_latency_ms = payload.get("response_latency_ms")

    if not user_transcript and not audio_base64:
        raise ValidationException("Either user_transcript or audio_base64 is required")

    svc = RampSessionService(db)
    try:
        result = await svc.submit_attempt(
            session_id=session_id,
            exercise_id=exercise_id,
            user_id=user_id,
            user_transcript=user_transcript,
            audio_base64=audio_base64,
            support_level_used=support_level_used,
            used_hint=used_hint,
            response_latency_ms=response_latency_ms,
        )
    except ValueError as e:
        raise NotFoundException(str(e))

    return result


@router.get("/sessions/{session_id}/progress")
async def get_session_progress(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> RampProgressSnapshot:
    """Get live progress snapshot for the session."""
    svc = RampSessionService(db)
    session = await svc.get_session(session_id, user_id)
    if not session:
        raise NotFoundException(f"Session '{session_id}' not found")
    return svc.get_progress_snapshot(session, user_id)


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> RampSessionSummary:
    """Finalize the session and return summary."""
    svc = RampSessionService(db)
    try:
        return await svc.complete_session(session_id, user_id)
    except ValueError as e:
        raise NotFoundException(str(e))


# ---------------------------------------------------------------------------
# Progress (historical, cross-session)
# ---------------------------------------------------------------------------

@router.get("/progress")
async def get_ramp_progress(
    period: str = Query(default="30d"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Historical Mode 6 progress across sessions.
    §58 Progress Visualization.
    """
    from sqlalchemy import select, desc
    from app.domains.ramp.models import RampSessionModel

    stmt = (
        select(RampSessionModel)
        .where(
            RampSessionModel.user_id == user_id,
            RampSessionModel.state == "completed",
        )
        .order_by(desc(RampSessionModel.completed_at))
        .limit(30)
    )
    res = await db.execute(stmt)
    sessions = list(res.scalars().all())

    if not sessions:
        return {
            "sessions_count": 0,
            "current_stage": 0,
            "current_support_level": 3,
            "max_independent_duration_ms": 0,
            "elaboration_trend": [],
            "duration_trend": [],
        }

    latest = sessions[0]
    duration_trend = [s.max_speech_duration_ms or 0 for s in reversed(sessions[:10])]
    elaboration_rates = []
    for s in reversed(sessions[:10]):
        completed = max(s.exercises_completed or 1, 1)
        elaboration_rates.append(round((s.elaboration_success_count or 0) / completed * 100, 1))

    return {
        "sessions_count": len(sessions),
        "current_stage": latest.stage,
        "current_support_level": latest.support_level,
        "max_independent_duration_ms": max(s.max_speech_duration_ms or 0 for s in sessions),
        "avg_elaboration_rate": round(sum(elaboration_rates) / len(elaboration_rates), 1) if elaboration_rates else 0,
        "duration_trend": duration_trend,
        "elaboration_trend": elaboration_rates,
        "milestones_total": len(set(m for s in sessions for m in (s.milestones_achieved or []))),
    }


# ---------------------------------------------------------------------------
# Utility / Info
# ---------------------------------------------------------------------------

@router.get("/stages")
async def get_stage_metadata():
    """Return stage descriptions for UI. §69"""
    from app.domains.ramp.contracts import STAGE_TARGET_DURATION_SEC, STAGE_EXERCISE_TYPE
    return {
        "stages": [
            {
                "stage": s,
                "name": [
                    "Echo", "Substitute", "Complete", "One Sentence",
                    "Expand", "Reason", "Example", "Keyword",
                    "Guided", "Spontaneous", "Independent"
                ][s],
                "target_duration_sec": STAGE_TARGET_DURATION_SEC.get(s, 0),
                "exercise_type": STAGE_EXERCISE_TYPE.get(s, "speak_spontaneous").value,
            }
            for s in range(11)
        ],
        "support_levels": [
            {"level": 0, "label": "No support", "is_answer_revealing": False},
            {"level": 1, "label": "Topic only", "is_answer_revealing": False},
            {"level": 2, "label": "Keywords", "is_answer_revealing": False},
            {"level": 3, "label": "Guided questions", "is_answer_revealing": False},
            {"level": 4, "label": "Sentence starter", "is_answer_revealing": False},
            {"level": 5, "label": "Structure outline", "is_answer_revealing": False},
            {"level": 6, "label": "Example response", "is_answer_revealing": True},
            {"level": 7, "label": "Translation reference", "is_answer_revealing": True},
        ],
    }
