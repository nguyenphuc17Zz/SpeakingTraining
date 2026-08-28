"""Situations API — Mode 4: Situational Roleplay & Hands-Free Simulation (thin wrapper)."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.contracts import ExerciseType
from app.domains.learning.exercise_session_service import ExerciseSessionService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.models import Exercise
from app.domains.learning.schemas import ExerciseDTO, ExerciseResultDTO
from app.domains.situations.dynamic_generator import AISituationsGenerator
from app.domains.situations.scenario_generator import ScenarioGenerator
from app.domains.reflex.pressure_profiles import PRESSURE_PROFILES, timer_for_level
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import ValidationException

router = APIRouter(prefix="/situations", tags=["Situations — Mode 4"])


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    svc = UserService(db)
    user = await svc.get_or_create_default_user()
    return user.id


_factory = ScenarioGenerator()


@router.get("/pressure-profiles")
async def list_pressure_profiles():
    return {"profiles": PRESSURE_PROFILES, "default": "normal"}


@router.get("/exercises/generate", response_model=ExerciseDTO)
async def generate_situational_exercise_get(
    sub_mode: str = Query(default="situational_roleplay", description="situational_roleplay|situational_scenario"),
    category: str | None = Query(default=None),
    custom_topic: str | None = Query(default=None),
    pressure_level: str = Query(default="normal"),
    difficulty: str | None = Query(default=None),
    duration: int = Query(default=5, ge=3, le=30),
    mode: str = Query(default="standard", description="guided|standard|challenge|blind"),
    timer_limit_ms: int | None = Query(default=None, ge=500, le=15000),
    seed: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await generate_situational_exercise(sub_mode, category, custom_topic, pressure_level, difficulty, duration, mode, timer_limit_ms, seed, user_id, db)


@router.post("/exercises/generate", response_model=ExerciseDTO)
async def generate_situational_exercise(
    sub_mode: str = Query(default="situational_roleplay", description="situational_roleplay|situational_scenario"),
    category: str | None = Query(default=None),
    custom_topic: str | None = Query(default=None),
    pressure_level: str = Query(default="normal"),
    difficulty: str | None = Query(default=None),
    duration: int = Query(default=5, ge=3, le=30),
    mode: str = Query(default="standard", description="guided|standard|challenge|blind"),
    timer_limit_ms: int | None = Query(default=None, ge=500, le=15000),
    seed: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    valid_modes = {e.value for e in ExerciseType if e.value.startswith("situational")}
    if sub_mode not in valid_modes:
        if sub_mode not in ("situational_roleplay", "situational_scenario"):
            raise ValidationException(f"Invalid sub_mode '{sub_mode}'. Must be one of {sorted(valid_modes)}")
    if pressure_level not in PRESSURE_PROFILES:
        pressure_level = "normal"
    eff_diff = difficulty or PRESSURE_PROFILES[pressure_level]["difficulty"]
    eff_timer = timer_limit_ms or timer_for_level(pressure_level) or 6000

    # Generate 100% on-the-fly dynamic situational roleplay via AISituationsGenerator
    ai_gen = AISituationsGenerator(db)
    data = await ai_gen.generate_dynamic_exercise(
        category=category,
        custom_topic=custom_topic,
        difficulty=eff_diff,
        pressure_level=pressure_level,
        duration=duration,
        mode=mode,
        user_id=user_id,
    )

    from app.domains.learning.prompts import LearningPrompts
    from app.domains.learning.exercise_variety_policy import ExerciseVarietyPolicy

    item_key = None
    item_service = LearningItemService(db)
    items = await item_service.list_items(user_id, limit=20)
    match = next((i for i in items if i.item_type in ("naturalness", "conversation", "fluency")), None)
    if match:
        item_key = match.key
    else:
        from app.domains.learning.models import LearningItem

        key = f"situational.{sub_mode}.{eff_diff}"
        existing = await item_service.get_item_by_key(key, user_id)
        if not existing:
            new_item = LearningItem(
                user_id=user_id,
                key=key,
                item_type="naturalness",
                title=f"Situational — {sub_mode} ({eff_diff})",
                description=f"Tình huống {sub_mode} mức {eff_diff}",
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
        target_patterns=data.get("target_patterns", ["situational"]),
        difficulty=eff_diff,
        scenario_topic=data.get("title"),
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
        success_criteria=["Giao tiếp tự nhiên, hoàn thành mục tiêu tình huống"],
        acceptable_variants=data.get("acceptable_variants", []),
        difficulty=eff_diff,
        scaffold_level="none",
        scaffold_hint=None,
        estimated_minutes=duration,
        template_version="v1",
        generator_version="situational.1.0.0",
        prompt_version=LearningPrompts.SITUATIONAL_GEN_PROMPT_VERSION,
        provider="situational_ai_factory",
        model="gemini_v1",
        exercise_signature=sig,
        extra_metadata={
            "situational_config": {
                "sub_mode": sub_mode,
                "category": category,
                "pressure_level": pressure_level,
                "timer_limit_ms": eff_timer,
                "canonical": data.get("canonical"),
                "accepted": data.get("acceptable_variants", []),
                "prompt": data.get("prompt"),
                "translation": data.get("translation"),
                "situational_data": data.get("situational_data", {}),
                "mode": mode,
                "duration_minutes": duration,
            },
            "priority_score": 0.7,
            "item_type": "situational",
        },
    )
    if timer_limit_ms:
        exercise.extra_metadata["situational_config"]["timer_limit_ms"] = timer_limit_ms
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return exercise


@router.get("/exercises/{exercise_id}", response_model=ExerciseDTO)
async def get_situational_exercise(
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
async def submit_situational_attempt(
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
        situational_metrics=payload.get("situational_metrics") or payload.get("reflex_metrics") or payload.get("pitch_metrics"),
        reflex_metrics=payload.get("situational_metrics") or payload.get("reflex_metrics"),
        reaction_latency_ms=payload.get("reaction_latency_ms"),
        semantic_latency_ms=payload.get("semantic_latency_ms"),
        timer_limit_ms=payload.get("timer_limit_ms"),
        timed_out=payload.get("timed_out"),
        late_response=payload.get("late_response"),
        speech_confidence=payload.get("speech_confidence"),
    )
    return result


@router.get("/progress")
async def get_situational_progress(
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
    situ_attempts = [a for a in attempts if (a.metrics_json or {}).get("situational") is not None or (a.exercise and a.exercise.exercise_type.startswith("situational"))]
    total = len(situ_attempts)
    if total == 0:
        return {"user_id": user_id, "period": period, "total_attempts": 0, "accuracy_rate": 0.0, "by_sub_mode": {}}
    successes = sum(1 for a in situ_attempts if a.success)
    acc = successes / total if total else 0
    by_mode: dict[str, Any] = {}
    for a in situ_attempts:
        mode = a.exercise.exercise_type if a.exercise else "unknown"
        by_mode.setdefault(mode, {"count": 0, "success": 0})
        by_mode[mode]["count"] += 1
        if a.success:
            by_mode[mode]["success"] += 1
    for k, v in by_mode.items():
        v["accuracy"] = v["success"]/v["count"] if v["count"] else 0
    return {"user_id": user_id, "period": period, "total_attempts": total, "accuracy_rate": round(acc,3), "by_sub_mode": by_mode}


@router.post("/session")
async def create_situational_session(
    payload: dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Thin wrapper for hands-free session creation — generates scenario and returns session config
    duration = payload.get("duration", 5)
    difficulty = payload.get("difficulty", "normal")
    category = payload.get("category")
    mode = payload.get("mode", "standard")
    seed = payload.get("seed")
    scenario = _factory.generate(category=category, difficulty=difficulty, seed=seed, duration_minutes=duration, mode=mode)
    return {"scenario": scenario, "hands_free": payload.get("hands_free", True), "duration": duration, "difficulty": difficulty, "mode": mode}
