"""Pitch Accent & Minimal Pairs Lab API — Mode 3 (thin wrapper)."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.contracts import ExerciseType
from app.domains.learning.exercise_session_service import ExerciseSessionService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.models import Exercise
from app.domains.learning.schemas import ExerciseDTO, ExerciseResultDTO
from app.domains.pitch.dynamic_generator import AIPitchGenerator
from app.domains.pitch.exercise_factory import TIMER_DEFAULTS, PitchExerciseFactory
from app.domains.reflex.pressure_profiles import PRESSURE_PROFILES, timer_for_level
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import ValidationException

router = APIRouter(prefix="/pitch", tags=["Pitch Lab — Mode 3"])


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    svc = UserService(db)
    user = await svc.get_or_create_default_user()
    return user.id


_factory = PitchExerciseFactory()


@router.get("/pressure-profiles")
async def list_pressure_profiles():
    return {
        "profiles": PRESSURE_PROFILES,
        "defaults": TIMER_DEFAULTS,
        "default": "normal",
        "recommended_order": ["relaxed", "normal", "fast", "reflex", "extreme"],
    }


@router.get("/exercises/generate", response_model=ExerciseDTO)
async def generate_pitch_exercise_get(
    sub_mode: str = Query(default="pitch_minimal_pair", description="pitch_*"),
    pressure_level: str = Query(default="normal"),
    difficulty: str | None = Query(default=None),
    timer_limit_ms: int | None = Query(default=None, ge=500, le=10000),
    learning_item_key: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await generate_pitch_exercise(sub_mode, pressure_level, difficulty, timer_limit_ms, learning_item_key, user_id, db)


@router.post("/exercises/generate", response_model=ExerciseDTO)
async def generate_pitch_exercise(
    sub_mode: str = Query(default="pitch_minimal_pair", description="pitch_*"),
    pressure_level: str = Query(default="normal"),
    difficulty: str | None = Query(default=None),
    timer_limit_ms: int | None = Query(default=None, ge=500, le=10000),
    learning_item_key: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    valid_modes = {e.value for e in ExerciseType if e.value.startswith("pitch") or e.value in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition")}
    if sub_mode not in valid_modes:
        raise ValidationException(f"Invalid sub_mode '{sub_mode}'. Must be one of {sorted(valid_modes)}")
    if pressure_level not in PRESSURE_PROFILES:
        pressure_level = "normal"
    eff_diff = difficulty or PRESSURE_PROFILES[pressure_level]["difficulty"]
    eff_timer = timer_limit_ms or timer_for_level(pressure_level) or TIMER_DEFAULTS.get(sub_mode, 5000)

    # Generate 100% on-the-fly dynamic pitch exercise via AIPitchGenerator
    ai_gen = AIPitchGenerator(db)
    data = await ai_gen.generate_dynamic_exercise(
        sub_mode=sub_mode,
        difficulty=eff_diff,
        pressure_level=pressure_level,
        user_id=user_id,
    )

    from app.domains.learning.prompts import LearningPrompts
    from app.domains.learning.exercise_variety_policy import ExerciseVarietyPolicy

    item_key = learning_item_key
    if not item_key:
        item_service = LearningItemService(db)
        items = await item_service.list_items(user_id, limit=20)
        match = next((i for i in items if i.item_type == "pitch_accent"), None)
        if match:
            item_key = match.key
        else:
            from app.domains.learning.models import LearningItem

            key = f"pitch.{sub_mode}.{eff_diff}"
            existing = await item_service.get_item_by_key(key, user_id)
            if not existing:
                new_item = LearningItem(
                    user_id=user_id,
                    key=key,
                    item_type="pitch_accent",
                    title=f"Pitch — {sub_mode.replace('pitch_', '').replace('mora_length','Mora').title()} ({eff_diff})",
                    description=f"Luyện {sub_mode} ở mức {eff_diff} với áp lực {pressure_level}.",
                    difficulty=eff_diff,
                    lifecycle="active",
                    status="active",
                )
                db.add(new_item)
                await db.flush()
                item_key = key
            else:
                item_key = key

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
        success_criteria=["Đúng cao độ và mora, tự nhiên"],
        acceptable_variants=data.get("acceptable_variants") or data.get("accepted", []),
        difficulty=eff_diff,
        scaffold_level="none",
        scaffold_hint=None,
        estimated_minutes=data.get("estimated_minutes", 4),
        template_version="v1",
        generator_version="pitch.1.0.0",
        prompt_version=LearningPrompts.PITCH_GEN_PROMPT_VERSION,
        provider="pitch_factory",
        model="deterministic_v1",
        exercise_signature=sig,
        extra_metadata={
            "pitch_config": {
                "sub_mode": sub_mode,
                "pressure_level": pressure_level,
                "timer_limit_ms": eff_timer,
                "canonical": data.get("canonical") or data.get("target"),
                "accepted": data.get("acceptable_variants") or data.get("accepted", []),
                "prompt": data.get("prompt"),
                "reading": data.get("reading"),
                "translation": data.get("translation"),
                "pitch_pattern": data.get("pitch_pattern") or data.get("pattern"),
                "pair_info": data.get("pair_info") or data.get("pair"),
                "mora_info": data.get("mora_info"),
                "devoicing_info": data.get("devoicing_info"),
                "contour_info": data.get("contour_info"),
                "recognition_info": data.get("recognition_info"),
                "mora_count": data.get("mora_count"),
                "resource_source": data.get("resource_source"),
            },
            "priority_score": 0.7,
            "item_type": "pitch_accent",
        },
    )
    if timer_limit_ms:
        exercise.extra_metadata["pitch_config"]["timer_limit_ms"] = timer_limit_ms
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@router.get("/exercises/{exercise_id}", response_model=ExerciseDTO)
async def get_pitch_exercise(
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
async def submit_pitch_attempt(
    exercise_id: str,
    payload: dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session_svc = ExerciseSessionService(db)
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
        reflex_metrics=payload.get("pitch_metrics") or payload.get("reflex_metrics"),
        keigo_metrics=payload.get("pitch_metrics") or payload.get("reflex_metrics"),
        reaction_latency_ms=payload.get("reaction_latency_ms"),
        semantic_latency_ms=payload.get("semantic_latency_ms"),
        timer_limit_ms=payload.get("timer_limit_ms"),
        timed_out=payload.get("timed_out"),
        late_response=payload.get("late_response"),
        speech_confidence=payload.get("speech_confidence"),
    )
    # Also handle pitch_metrics alias via direct param (handled via reflex_metrics above, but ensure pitch_metrics passed)
    # The session service already merges, so we pass pitch_metrics explicitly via keigo_metrics/reflex_metrics
    return result


@router.get("/progress")
async def get_pitch_progress(
    period: str = Query(default="30d", description="7d|30d|all"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.domains.learning.models import ExerciseAttempt

    days_map = {"7d": 7, "30d": 30, "all": 3650}
    days = days_map.get(period, 30)
    from datetime import datetime, timedelta, timezone

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
    pitch_attempts = [a for a in attempts if (a.metrics_json or {}).get("pitch") is not None or (a.exercise and (a.exercise.exercise_type.startswith("pitch") or a.exercise.exercise_type in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition")))]
    total = len(pitch_attempts)
    if total == 0:
        return {"user_id": user_id, "period": period, "total_attempts": 0, "accuracy_rate": 0.0, "avg_reaction_ms": None, "by_sub_mode": {}}
    successes = sum(1 for a in pitch_attempts if a.success)
    acc = successes / total if total else 0
    latencies = []
    for a in pitch_attempts:
        rm = (a.metrics_json or {}).get("pitch", {}) if a.metrics_json else {}
        if not rm:
            rm = (a.metrics_json or {}).get("reflex", {}) if a.metrics_json else {}
        lat = rm.get("reaction_latency_ms", a.response_speed_ms)
        if lat is not None:
            latencies.append(float(lat))
    latencies.sort()
    avg = sum(latencies) / len(latencies) if latencies else None
    p50 = latencies[len(latencies)//2] if latencies else None
    by_mode: dict[str, Any] = {}
    for a in pitch_attempts:
        mode = a.exercise.exercise_type if a.exercise else "unknown"
        by_mode.setdefault(mode, {"count": 0, "success": 0})
        by_mode[mode]["count"] += 1
        if a.success:
            by_mode[mode]["success"] += 1
    for k, v in by_mode.items():
        v["accuracy"] = v["success"]/v["count"] if v["count"] else 0
    return {
        "user_id": user_id,
        "period": period,
        "total_attempts": total,
        "accuracy_rate": round(acc,3),
        "avg_reaction_ms": round(avg,1) if avg else None,
        "p50_reaction_ms": round(p50,1) if p50 else None,
        "by_sub_mode": by_mode,
    }
