"""Monologue — Mode 5 API (1-Minute Speech)."""

from typing import Any

import base64

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.models import Exercise
from app.domains.learning.schemas import ExerciseDTO, ExerciseResultDTO
from app.domains.monologue.service import MonologueService
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import ValidationException

router = APIRouter(prefix="/monologue", tags=["Monologue — Mode 5"])


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    svc = UserService(db)
    user = await svc.get_or_create_default_user()
    return user.id


@router.get("/genres")
async def list_genres():
    from app.domains.monologue.generation.genre_ontology import ALL_GENRES, GENRE_STRUCTURE

    return {
        "genres": [g.value for g in ALL_GENRES],
        "structures": {g.value: GENRE_STRUCTURE[g] for g in ALL_GENRES},
    }


@router.get("/domains")
async def list_domains():
    from app.domains.monologue.contracts import SpeechTopicDomain

    return {"domains": [d.value for d in SpeechTopicDomain]}


@router.get("/durations")
async def list_durations():
    return {"durations": [30, 45, 60, 90, 120, 180, 300], "default": 60, "prep_options": [0, 15, 30, 60]}


@router.post("/exercises/generate", response_model=ExerciseDTO)
async def generate_monologue_exercise(
    payload: dict[str, Any] | None = None,
    duration_sec: int = Query(default=60, ge=30, le=300),
    prep_sec: int | None = Query(default=None, ge=0, le=60),
    difficulty: int | None = Query(default=None, ge=1, le=5),
    genre: str | None = Query(default=None),
    support_level: int | None = Query(default=None, ge=0, le=4),
    topic_domain: str | None = Query(default=None),
    seed: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # payload overrides query
    if payload:
        duration_sec = int(payload.get("duration_sec") or payload.get("duration") or duration_sec)
        prep_sec = payload.get("prep_sec", prep_sec)
        difficulty = payload.get("difficulty", difficulty)
        genre = payload.get("genre", genre)
        support_level = payload.get("support_level", support_level)
        topic_domain = payload.get("topic_domain", topic_domain)
        seed = payload.get("seed", seed)

    # validate duration must be one of allowed
    allowed = {30, 45, 60, 90, 120, 180, 300}
    if duration_sec not in allowed:
        # snap to nearest
        duration_sec = min(allowed, key=lambda x: abs(x - duration_sec))

    svc = MonologueService(db)
    try:
        ex = await svc.generate_exercise(
            user_id=user_id,
            duration_sec=duration_sec,
            prep_sec=prep_sec,
            difficulty=difficulty,
            genre=genre,
            support_level=support_level,
            topic_domain=topic_domain,
            seed=seed,
        )
    except RuntimeError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Topic generation unavailable (AI down): {e}")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
    return ex


@router.get("/exercises/generate", response_model=ExerciseDTO)
async def generate_monologue_exercise_get(
    duration_sec: int = Query(default=60, ge=30, le=300),
    prep_sec: int | None = Query(default=None, ge=0, le=60),
    difficulty: int | None = Query(default=None, ge=1, le=5),
    genre: str | None = Query(default=None),
    support_level: int | None = Query(default=None, ge=0, le=4),
    topic_domain: str | None = Query(default=None),
    seed: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await generate_monologue_exercise(
        payload=None, duration_sec=duration_sec, prep_sec=prep_sec, difficulty=difficulty,
        genre=genre, support_level=support_level, topic_domain=topic_domain, seed=seed,
        user_id=user_id, db=db
    )


@router.get("/exercises/{exercise_id}", response_model=ExerciseDTO)
async def get_monologue_exercise(
    exercise_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    stmt = select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
    res = await db.execute(stmt)
    ex = res.scalar_one_or_none()
    if not ex:
        from app.shared.errors.exceptions import NotFoundException

        raise NotFoundException(f"Exercise '{exercise_id}' not found.")
    return ex


@router.post("/exercises/{exercise_id}/submit")
async def submit_monologue_exercise(
    exercise_id: str,
    payload: dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = MonologueService(db)
    transcript = payload.get("user_transcript") or payload.get("transcript") or payload.get("text")
    audio_b64 = payload.get("audio_base64") or payload.get("audio") or payload.get("audioBase64")
    # Enforce audio-only (hard error per user choice)
    if not audio_b64:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Audio is required for monologue evaluation — please record audio (transcript-only not allowed)")
    speech_metrics = payload.get("speech_metrics") or payload.get("speechMetrics") or {}
    if not speech_metrics and any(k in payload for k in ("speech_duration_ms", "target_duration_ms", "started_at", "ended_at")):
        speech_metrics = {k: payload.get(k) for k in ("speech_duration_ms", "target_duration_ms", "started_at", "ended_at", "audio_confidence") if payload.get(k) is not None}
    if not speech_metrics.get("target_duration_ms") and payload.get("target_duration_ms"):
        speech_metrics["target_duration_ms"] = payload["target_duration_ms"]
    used_hint = bool(payload.get("used_hint") or payload.get("usedHint"))
    plan_item_id = payload.get("plan_item_id") or payload.get("planItemId")

    try:
        result = await svc.evaluate_exercise(
            exercise_id=exercise_id,
            user_id=user_id,
            user_transcript=transcript,
            audio_base64=audio_b64,
            speech_metrics=speech_metrics,
            used_hint=used_hint,
            plan_item_id=plan_item_id,
        )
    except ValueError as ve:
        from fastapi import HTTPException
        # RETRY_AUDIO or validation
        if "Audio is required" in str(ve) or "STT failed" in str(ve):
            raise HTTPException(status_code=400, detail=str(ve))
        raise HTTPException(status_code=422, detail=str(ve))
    return result


@router.post("/exercises/{exercise_id}/submit_multipart")
async def submit_monologue_multipart(
    exercise_id: str,
    audio: UploadFile = File(..., description="Audio blob webm/opus"),
    user_transcript: str | None = Form(default=None),
    used_hint: bool = Form(default=False),
    plan_item_id: str | None = Form(default=None),
    speech_metrics_json: str | None = Form(default=None, alias="speech_metrics"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Multipart support (keep both per 2026-08-26): audio as binary, avoids 33% base64 overhead."""
    svc = MonologueService(db)
    audio_bytes = await audio.read()
    if not audio_bytes or len(audio_bytes) < 500:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Audio is required for monologue evaluation — please record audio (transcript-only not allowed)")
    if len(audio_bytes) > 10 * 1024 * 1024:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail="Audio too large (>10MB) — please use shorter duration")
    # pass as base64 internally to reuse evaluator (or directly as bytes if evaluator supports)
    audio_b64 = base64.b64encode(audio_bytes).decode()
    speech_metrics: dict = {}
    if speech_metrics_json:
        import json
        try:
            speech_metrics = json.loads(speech_metrics_json)
        except Exception:
            speech_metrics = {}
    try:
        result = await svc.evaluate_exercise(
            exercise_id=exercise_id,
            user_id=user_id,
            user_transcript=user_transcript,
            audio_base64=audio_b64,
            speech_metrics=speech_metrics,
            used_hint=used_hint,
            plan_item_id=plan_item_id,
        )
    except ValueError as ve:
        from fastapi import HTTPException
        if "Audio is required" in str(ve) or "STT failed" in str(ve):
            raise HTTPException(status_code=400, detail=str(ve))
        raise HTTPException(status_code=422, detail=str(ve))
    return result


@router.get("/progress")
async def get_monologue_progress(
    period: str = Query(default="30d", description="7d|30d|all"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.domains.learning.models import ExerciseAttempt

    days_map = {"7d": 7, "30d": 30, "all": 3650}
    days = days_map.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = (
        select(ExerciseAttempt)
        .options(selectinload(ExerciseAttempt.exercise))
        .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed", ExerciseAttempt.completed_at >= cutoff)
        .order_by(ExerciseAttempt.completed_at.desc())
        .limit(500)
    )
    res = await db.execute(stmt)
    attempts = res.scalars().all()
    speech_attempts = [a for a in attempts if a.exercise and a.exercise.exercise_type.startswith("speech")]

    total = len(speech_attempts)
    if total == 0:
        return {
            "user_id": user_id,
            "period": period,
            "total_attempts": 0,
            "accuracy_rate": 0.0,
            "avg_duration_ms": None,
            "avg_overall": None,
            "by_genre": {},
            "recent_scores": [],
        }

    successes = sum(1 for a in speech_attempts if a.success)
    acc = successes / total if total else 0
    durations = []
    scores = []
    by_genre: dict[str, dict] = {}
    for a in speech_attempts:
        sc = (a.metrics_json or {}).get("speech_config") or (a.exercise.extra_metadata or {}).get("speech_config", {}) if a.exercise and a.exercise.extra_metadata else {}
        # fallback metric duration
        dur = (a.metrics_json or {}).get("speech_duration_ms") or (a.metrics_json or {}).get("speech_metrics_core", {}).get("speech_duration_ms") if a.metrics_json else None
        if dur:
            durations.append(float(dur))
        if a.score is not None:
            scores.append(float(a.score))
        genre = sc.get("genre") or a.exercise.exercise_type
        by_genre.setdefault(genre, {"count": 0, "success": 0, "avg_score": []})
        by_genre[genre]["count"] += 1
        if a.success:
            by_genre[genre]["success"] += 1
        if a.score is not None:
            by_genre[genre]["avg_score"].append(float(a.score))

    for k, v in by_genre.items():
        v["accuracy"] = round(v["success"] / v["count"], 3) if v["count"] else 0
        v["avg_score"] = round(sum(v["avg_score"]) / len(v["avg_score"]), 1) if v["avg_score"] else None

    return {
        "user_id": user_id,
        "period": period,
        "total_attempts": total,
        "accuracy_rate": round(acc, 3),
        "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else None,
        "avg_overall": round(sum(scores) / len(scores), 1) if scores else None,
        "by_genre": by_genre,
        "recent_scores": scores[:10],
    }
