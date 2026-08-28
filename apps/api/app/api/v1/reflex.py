"""Reflex Speaking API — Mode 1 integration (thin wrapper over Learning Engine)."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.contracts import ExerciseType, LearningItemType, PriorityScore
from app.domains.learning.exercise_generator import ExerciseGenerator
from app.domains.learning.exercise_session_service import ExerciseSessionService
from app.domains.learning.learner_state_service import LearnerStateService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.models import Exercise
from app.domains.learning.schemas import ExerciseDTO, ExerciseResultDTO
from app.domains.reflex.dynamic_generator import AIReflexGenerator
from app.domains.reflex.exercise_factory import ReflexExerciseFactory
from app.domains.reflex.pressure_profiles import PRESSURE_PROFILES, timer_for_level
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import ValidationException

router = APIRouter(prefix="/reflex", tags=["Reflex Speaking — Mode 1"])


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    svc = UserService(db)
    user = await svc.get_or_create_default_user()
    return user.id


# Factory singleton
_factory = ReflexExerciseFactory()


@router.get("/pressure-profiles")
async def list_pressure_profiles():
    """Returns available pressure profiles and timer configs."""
    return {
        "profiles": PRESSURE_PROFILES,
        "default": "normal",
        "recommended_order": ["relaxed", "normal", "fast", "reflex", "extreme"],
    }


@router.get("/exercises/generate", response_model=ExerciseDTO)
async def generate_reflex_exercise_get(
    sub_mode: str = Query(default="reflex_qna", description="reflex_conjugation|reflex_qna|reflex_transformation|reflex_context"),
    pressure_level: str = Query(default="normal"),
    difficulty: str | None = Query(default=None),
    verb: str | None = Query(default=None),
    conjugation_target: str | None = Query(default=None),
    timer_limit_ms: int | None = Query(default=None, ge=500, le=10000),
    learning_item_key: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await generate_reflex_exercise(sub_mode, pressure_level, difficulty, verb, conjugation_target, timer_limit_ms, learning_item_key, user_id, db)


@router.post("/exercises/generate", response_model=ExerciseDTO)
async def generate_reflex_exercise(
    sub_mode: str = Query(default="reflex_qna", description="reflex_conjugation|reflex_qna|reflex_transformation|reflex_context"),
    pressure_level: str = Query(default="normal"),
    difficulty: str | None = Query(default=None),
    verb: str | None = Query(default=None),
    conjugation_target: str | None = Query(default=None),
    timer_limit_ms: int | None = Query(default=None, ge=500, le=10000),
    learning_item_key: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Dynamic reflex exercise generation via Gemini AI and Sudachi Dictionary.

    100% on-the-fly, creative, infinite non-repeating scenarios.
    """
    valid_modes = {e.value for e in ExerciseType if e.value.startswith("reflex")}
    if sub_mode not in valid_modes:
        raise ValidationException(f"Invalid sub_mode '{sub_mode}'. Must be one of {sorted(valid_modes)}")
    if pressure_level not in PRESSURE_PROFILES:
        pressure_level = "normal"
    eff_timer = timer_limit_ms or timer_for_level(pressure_level)
    eff_diff = difficulty or PRESSURE_PROFILES[pressure_level]["difficulty"]

    # Generate dynamic payload via AIReflexGenerator
    ai_gen = AIReflexGenerator(db)
    data = await ai_gen.generate_dynamic_exercise(
        sub_mode=sub_mode,
        difficulty=eff_diff,
        pressure_level=pressure_level,
        verb=verb,
        conjugation_target=conjugation_target,
        user_id=user_id,
    )

    # Persist as Exercise row (reuse learning tables)
    from sqlalchemy import select

    # Resolve learning item key
    item_key = learning_item_key
    if not item_key:
        # Auto-create or find a learning item for reflex focus
        item_service = LearningItemService(db)
        # Try to find existing reflex item
        items = await item_service.list_items(user_id, limit=20)
        # Prefer item matching sub_mode affinity
        affinity_map = {
            "reflex_conjugation": "conjugation",
            "reflex_qna": "fluency",
            "reflex_transformation": "grammar",
            "reflex_context": "naturalness",
        }
        target_type = affinity_map.get(sub_mode, "grammar")
        match = next((i for i in items if i.item_type == target_type), None)
        if match:
            item_key = match.key
        else:
            # Create a generic reflex learning item on the fly
            from app.domains.learning.models import LearningItem
            import uuid

            key = f"reflex.{sub_mode}.{eff_diff}"
            existing = await item_service.get_item_by_key(key, user_id)
            if not existing:
                new_item = LearningItem(
                    user_id=user_id,
                    key=key,
                    item_type=target_type,
                    title=f"Reflex — {sub_mode.replace('reflex_', '').title()} ({eff_diff})",
                    description=f"Luyện phản xạ {sub_mode} ở mức {eff_diff} với áp lực {pressure_level}.",
                    difficulty=eff_diff,
                    lifecycle="active",
                    status="active",
                )
                db.add(new_item)
                await db.flush()
                item_key = key
            else:
                item_key = key

    # Determine prompt_version
    from app.domains.learning.prompts import LearningPrompts

    # Build signature
    from app.domains.learning.exercise_variety_policy import ExerciseVarietyPolicy

    sig = ExerciseVarietyPolicy.compute_exercise_signature(
        exercise_type=sub_mode,
        target_patterns=data.get("target_patterns", []),
        difficulty=eff_diff,
        scenario_topic=data.get("scenario"),
    )

    exercise = Exercise(
        user_id=user_id,
        exercise_type=sub_mode,
        status="not_started",
        title=data["title"],
        objective=data["objective"],
        scenario=data.get("scenario"),
        instructions=data["instructions"],
        constraints=data.get("constraints", []),
        target_patterns=data.get("target_patterns", []),
        learning_item_keys=[item_key],
        success_criteria=["Phản xạ đúng và tự nhiên trong thời gian cho phép."],
        acceptable_variants=data.get("acceptable_variants", []),
        difficulty=eff_diff,
        scaffold_level="none",
        scaffold_hint=None,
        estimated_minutes=data.get("estimated_minutes", 4),
        template_version="v1",
        generator_version="reflex.1.0.0",
        prompt_version=LearningPrompts.REFLEX_GEN_PROMPT_VERSION,
        provider="reflex_factory",
        model="deterministic_v1",
        exercise_signature=sig,
        extra_metadata={
            "reflex_config": {
                "sub_mode": sub_mode,
                "pressure_level": pressure_level,
                "timer_limit_ms": eff_timer,
                "verb": data.get("verb") or verb,
                "conjugation_target": data.get("form") or conjugation_target,
                "canonical": data.get("canonical") or data.get("expected"),
                "acceptable_variants": data.get("acceptable_variants", []),
                "prompt": data.get("prompt"),
                "task": data.get("task"),
                "intent": data.get("intent"),
            },
            "priority_score": 0.7,
            "item_type": "reflex",
        },
    )
    # Override timer if explicitly requested
    if timer_limit_ms:
        exercise.extra_metadata["reflex_config"]["timer_limit_ms"] = timer_limit_ms

    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@router.get("/exercises/{exercise_id}", response_model=ExerciseDTO)
async def get_reflex_exercise(
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


@router.post("/exercises/{exercise_id}/submit", response_model=ExerciseResultDTO)
async def submit_reflex_attempt(
    exercise_id: str,
    payload: dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit reflex attempt with timing metrics. Body supports both legacy and reflex_metrics."""
    session_svc = ExerciseSessionService(db)
    # Normalize payload
    transcript = payload.get("user_transcript") or payload.get("transcript") or ""
    result = await session_svc.submit_exercise_attempt(
        exercise_id=exercise_id,
        user_id=user_id,
        user_transcript=transcript,
        turn_analysis_score=payload.get("turn_analysis_score"),
        pronunciation_score=payload.get("pronunciation_score"),
        response_speed_ms=payload.get("response_speed_ms") or payload.get("reaction_latency_ms"),
        used_hint=payload.get("used_hint", False) or (payload.get("independence") != "independent" if payload.get("independence") else False),
        plan_item_id=payload.get("plan_item_id"),
        reflex_metrics=payload.get("reflex_metrics"),
        reaction_latency_ms=payload.get("reaction_latency_ms"),
        semantic_latency_ms=payload.get("semantic_latency_ms"),
        timer_limit_ms=payload.get("timer_limit_ms"),
        timed_out=payload.get("timed_out"),
        late_response=payload.get("late_response"),
        speech_confidence=payload.get("speech_confidence"),
    )
    return result


@router.get("/progress")
async def get_reflex_progress(
    period: str = Query(default="30d", description="7d|30d|all"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Returns reflex analytics derived from ExerciseAttempts."""
    from sqlalchemy import select

    from app.domains.learning.models import ExerciseAttempt

    # Determine days
    days_map = {"7d": 7, "30d": 30, "all": 3650}
    days = days_map.get(period, 30)

    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    from sqlalchemy.orm import selectinload

    stmt = (
        select(ExerciseAttempt)
        .options(selectinload(ExerciseAttempt.exercise))
        .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed", ExerciseAttempt.completed_at >= cutoff)
        .order_by(ExerciseAttempt.completed_at.desc())
        .limit(500)
    )
    res = await db.execute(stmt)
    attempts = res.scalars().all()

    # Filter reflex attempts
    reflex_attempts = [a for a in attempts if (a.metrics_json or {}).get("reflex") is not None or (a.exercise and a.exercise.exercise_type.startswith("reflex"))]

    # Fallback: also check exercise_type via join (need to fetch exercises)
    # For simplicity, count all where metrics_json has reflex
    total = len(reflex_attempts)
    if total == 0:
        return {
            "user_id": user_id,
            "period": period,
            "total_attempts": 0,
            "accuracy_rate": 0.0,
            "avg_reaction_ms": None,
            "p50_reaction_ms": None,
            "p90_reaction_ms": None,
            "timeout_rate": 0.0,
            "automaticity_avg": None,
            "pressure_threshold_ms": None,
            "comfort_window": None,
            "by_sub_mode": {},
        }

    # Accuracy
    successes = sum(1 for a in reflex_attempts if a.success)
    acc_rate = successes / total if total else 0.0

    # Latencies
    latencies = []
    for a in reflex_attempts:
        rm = (a.metrics_json or {}).get("reflex", {}) if a.metrics_json else {}
        lat = rm.get("reaction_latency_ms", a.response_speed_ms)
        if lat is not None:
            latencies.append(float(lat))
    latencies.sort()
    avg_lat = sum(latencies) / len(latencies) if latencies else None
    p50 = latencies[len(latencies) // 2] if latencies else None
    p90 = latencies[int(len(latencies) * 0.9)] if latencies else None

    timeouts = sum(1 for a in reflex_attempts if ((a.metrics_json or {}).get("reflex", {}) or {}).get("timed_out"))
    timeout_rate = timeouts / total if total else 0.0

    # Automaticity avg from learning items
    item_service = LearningItemService(db)
    items = await item_service.list_items(user_id, limit=50)
    reflex_items = [i for i in items if hasattr(i, "automaticity_mastery")]
    auto_vals = [float(getattr(i, "automaticity_mastery", 0) or 0) for i in reflex_items]
    auto_avg = sum(auto_vals) / len(auto_vals) if auto_vals else None

    # Pressure threshold estimation
    from app.domains.reflex.adaptive_pressure import estimate_pressure_threshold

    raw_attempts = []
    for a in reflex_attempts:
        rm = (a.metrics_json or {}).get("reflex", {}) if a.metrics_json else {}
        raw_attempts.append(
            {
                "success": a.success,
                "score": a.score or 0,
                "reaction_latency_ms": rm.get("reaction_latency_ms", a.response_speed_ms),
                "timer_limit_ms": rm.get("timer_limit_ms", 3000),
            }
        )
    thresh_info = estimate_pressure_threshold(raw_attempts) if len(raw_attempts) >= 8 else None

    # By sub_mode
    by_mode: dict[str, Any] = {}
    for a in reflex_attempts:
        mode = a.exercise.exercise_type if a.exercise else "unknown"
        by_mode.setdefault(mode, {"count": 0, "success": 0})
        by_mode[mode]["count"] += 1
        if a.success:
            by_mode[mode]["success"] += 1
    for k, v in by_mode.items():
        v["accuracy"] = v["success"] / v["count"] if v["count"] else 0

    return {
        "user_id": user_id,
        "period": period,
        "total_attempts": total,
        "accuracy_rate": round(acc_rate, 3),
        "avg_reaction_ms": round(avg_lat, 1) if avg_lat is not None else None,
        "p50_reaction_ms": round(p50, 1) if p50 is not None else None,
        "p90_reaction_ms": round(p90, 1) if p90 is not None else None,
        "timeout_rate": round(timeout_rate, 3),
        "automaticity_avg": round(auto_avg, 3) if auto_avg is not None else None,
        "pressure_threshold_ms": thresh_info["threshold_ms"] if thresh_info else None,
        "comfort_window": thresh_info["comfort_window"] if thresh_info else None,
        "by_sub_mode": by_mode,
    }
