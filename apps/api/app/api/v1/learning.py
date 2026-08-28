from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.curriculum_engine import CurriculumEngine
from app.domains.learning.daily_plan_generator import DailyPlanGenerator
from app.domains.learning.exercise_generator import ExerciseGenerator
from app.domains.learning.exercise_session_service import ExerciseSessionService
from app.domains.learning.goal_service import GoalService
from app.domains.learning.learner_state_service import LearnerStateService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.priority_engine import PriorityEngine
from app.domains.learning.queue import learning_job_queue
from app.domains.learning.recommendation_engine import RecommendationEngine
from app.domains.learning.review_scheduler import ReviewScheduler
from app.domains.learning.schemas import (
    CurriculumUnitDTO,
    DailyPlanDTO,
    DailyPlanRegenerateRequest,
    ExerciseDTO,
    ExerciseGenerateRequest,
    ExerciseResultDTO,
    ExerciseStartRequest,
    ExerciseStartResponse,
    ExerciseSubmitRequest,
    LearningGoalCreate,
    LearningGoalDTO,
    LearningGoalUpdate,
    LearningItemDTO,
    LearningRecommendationDTO,
)
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/learning", tags=["Learning Engine & Curriculum"])


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    return user.id


# 1. Daily Learning Plan
@router.get("/today", response_model=DailyPlanDTO)
async def get_today_plan(
    time_budget: int = Query(default=30, ge=5, le=90),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves today's personalized learning schedule (cached & stable across page reloads)."""
    generator = DailyPlanGenerator(db)
    plan = await generator.get_or_create_daily_plan(
        user_id=user_id,
        time_budget_minutes=time_budget,
        regenerate=False,
    )
    return plan


@router.post("/today/regenerate", response_model=DailyPlanDTO)
async def regenerate_today_plan(
    payload: DailyPlanRegenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Explicitly forces regeneration of today's learning plan with a new time budget."""
    generator = DailyPlanGenerator(db)
    plan = await generator.get_or_create_daily_plan(
        user_id=user_id,
        time_budget_minutes=payload.time_budget_minutes,
        regenerate=True,
    )
    return plan


# 2. Learning Priorities & Recommendations
@router.get("/priorities", response_model=list[LearningRecommendationDTO])
async def get_priorities(
    limit: int = Query(default=5, ge=1, le=20),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Returns top ranked, diversified learning recommendations with transparent Why/How context."""
    engine = RecommendationEngine(db)
    return await engine.get_actionable_recommendations(user_id=user_id, limit=limit)


# 3. Learning Items
@router.get("/items", response_model=list[LearningItemDTO])
async def list_learning_items(
    item_type: str | None = None,
    lifecycle: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Returns catalog of actively tracked linguistic learning items."""
    service = LearningItemService(db)
    return await service.list_items(user_id=user_id, item_type=item_type, lifecycle=lifecycle, limit=limit)


@router.get("/items/{item_id}", response_model=LearningItemDTO)
async def get_learning_item(
    item_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = LearningItemService(db)
    return await service.get_item_by_id(item_id=item_id, user_id=user_id)


@router.post("/items/{item_id}/practice", response_model=ExerciseDTO)
async def create_quick_practice_for_item(
    item_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generates an immediate targeted speaking drill for a specific learning item."""
    item_service = LearningItemService(db)
    item = await item_service.get_item_by_id(item_id, user_id)

    state_service = LearnerStateService(db)
    state = await state_service.build_learning_state(user_id)

    goal_service = GoalService(db)
    goals = await goal_service.get_active_goals(user_id)

    p_score = PriorityEngine.calculate_item_priority(item, goals)
    generator = ExerciseGenerator(db)
    exercise = await generator.generate_exercise(user_id=user_id, priority=p_score, state=state)
    await db.commit()
    return exercise


# 4. Spaced Reviews
@router.get("/reviews", response_model=list[LearningItemDTO])
async def get_due_reviews(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Returns learning items currently due for spaced repetition review."""
    service = LearningItemService(db)
    items = await service.list_items(user_id=user_id, limit=50)
    return ReviewScheduler.filter_due_items(items)


# 5. Goal System
@router.get("/goals", response_model=list[LearningGoalDTO])
async def list_goals(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = GoalService(db)
    return await service.get_or_create_default_goals(user_id)


@router.post("/goals", response_model=LearningGoalDTO, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: LearningGoalCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = GoalService(db)
    return await service.create_goal(
        user_id=user_id,
        title=payload.title,
        goal_type=payload.goal_type,
        description=payload.description,
        priority=payload.priority,
        target_date=payload.target_date,
    )


@router.patch("/goals/{goal_id}", response_model=LearningGoalDTO)
async def update_goal(
    goal_id: str,
    payload: LearningGoalUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = GoalService(db)
    return await service.update_goal(
        goal_id=goal_id,
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        target_date=payload.target_date,
    )


# 6. Exercises & Interactive Attempt Flow
@router.post("/exercises/generate", response_model=ExerciseDTO)
async def generate_custom_exercise(
    payload: ExerciseGenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Dynamically generates a new exercise for user. Supports reflex exercise_type."""
    state_service = LearnerStateService(db)
    state = await state_service.build_learning_state(user_id)

    item_service = LearningItemService(db)
    items = await item_service.list_items(user_id, limit=20)
    goal_service = GoalService(db)
    goals = await goal_service.get_active_goals(user_id)

    # Allow explicit exercise_type for reflex/keigo/pitch/situational/speech generation without requiring existing learning_item
    req_type = payload.exercise_type
    if req_type and (req_type.startswith(("reflex", "keigo", "pitch", "situational", "speech")) or req_type in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition", "situational_roleplay", "situational_scenario", "speech_monologue")):
        # Find or create suitable item for reflex type
        from app.domains.learning.contracts import ExerciseType as ET

        try:
            et = ET(req_type)
        except Exception:
            raise ValidationException(f"Invalid exercise_type '{req_type}'")
        # Build priority for reflex/keigo/pitch/situational/speech
        target_type_map = {
            "reflex_conjugation": "conjugation",
            "reflex_qna": "fluency",
            "reflex_transformation": "grammar",
            "reflex_context": "naturalness",
            "keigo_sonkeigo": "politeness",
            "keigo_kenjougo": "politeness",
            "keigo_teineigo": "politeness",
            "keigo_transformation": "politeness",
            "keigo_context": "politeness",
            "keigo_doctor": "politeness",
            "keigo_naturalness": "politeness",
            "pitch_minimal_pair": "pitch_accent",
            "mora_length": "pitch_accent",
            "vowel_devoicing": "pitch_accent",
            "pitch_contour": "pitch_accent",
            "pitch_recognition": "pitch_accent",
            "situational_roleplay": "naturalness",
            "situational_scenario": "conversation",
            "speech_monologue": "fluency",
        }
        target_item_type = target_type_map.get(req_type, "grammar")
        # Try to find existing item of target type
        candidate = next((i for i in items if i.item_type == target_item_type), None)
        if payload.learning_item_key:
            candidate = await item_service.get_item_by_key(payload.learning_item_key, user_id)
            if not candidate:
                raise NotFoundException(f"Learning item '{payload.learning_item_key}' not found.")
        if not candidate:
            if items:
                candidate = items[0]
            else:
                raise ValidationException("No learning items found to generate reflex exercise. Please run /learner sync first.")
        p_score = PriorityEngine.calculate_item_priority(candidate, goals)
        # Override exercise type to requested reflex type
        p_score.recommended_exercise_type = et
        if payload.difficulty:
            from app.domains.learning.contracts import DifficultyLevel

            try:
                p_score.difficulty = DifficultyLevel(payload.difficulty)
            except Exception:
                pass
        generator = ExerciseGenerator(db)
        exercise = await generator.generate_exercise(user_id=user_id, priority=p_score, state=state)
        await db.commit()
        return exercise

    if payload.learning_item_key:
        item = await item_service.get_item_by_key(payload.learning_item_key, user_id)
        if not item:
            raise NotFoundException(f"Learning item '{payload.learning_item_key}' not found.")
        p_score = PriorityEngine.calculate_item_priority(item, goals)
    elif items:
        p_score = PriorityEngine.calculate_item_priority(items[0], goals)
    else:
        raise ValidationException("No learning items found to generate exercise.")

    # Override type/difficulty if requested
    if req_type:
        from app.domains.learning.contracts import ExerciseType as ET

        try:
            p_score.recommended_exercise_type = ET(req_type)
        except Exception:
            pass
    if payload.difficulty:
        from app.domains.learning.contracts import DifficultyLevel

        try:
            p_score.difficulty = DifficultyLevel(payload.difficulty)
        except Exception:
            pass

    generator = ExerciseGenerator(db)
    exercise = await generator.generate_exercise(user_id=user_id, priority=p_score, state=state)
    await db.commit()
    return exercise


@router.get("/exercises/{exercise_id}", response_model=ExerciseDTO)
async def get_exercise(
    exercise_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session_svc = ExerciseSessionService(db)
    stmt = select(ExerciseSessionService).where()  # query exercise
    from app.domains.learning.models import Exercise
    ex_stmt = select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
    res = await db.execute(ex_stmt)
    ex = res.scalar_one_or_none()
    if not ex:
        raise NotFoundException(f"Exercise '{exercise_id}' not found.")
    return ex


@router.post("/exercises/{exercise_id}/start", response_model=ExerciseStartResponse)
async def start_exercise(
    exercise_id: str,
    payload: ExerciseStartRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Starts an exercise session and creates an attempt record."""
    session_svc = ExerciseSessionService(db)
    attempt = await session_svc.start_exercise(
        exercise_id=exercise_id,
        user_id=user_id,
        session_id=payload.session_id,
        pronunciation_attempt_id=payload.pronunciation_attempt_id,
    )
    return ExerciseStartResponse(
        attempt_id=attempt.id,
        exercise_id=exercise_id,
        status=attempt.status,
        started_at=attempt.started_at,
    )


@router.post("/exercises/{exercise_id}/submit", response_model=ExerciseResultDTO)
async def submit_exercise(
    exercise_id: str,
    payload: ExerciseSubmitRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submits transcript, evaluates response, and updates multi-dimensional mastery & review schedules."""
    # Speech monologue delegation: if exercise is speech_monologue and audio provided, route to MonologueService
    try:
        from sqlalchemy import select
        from app.domains.learning.models import Exercise

        _ex_stmt = select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
        _ex_res = await db.execute(_ex_stmt)
        _ex = _ex_res.scalar_one_or_none()
        if _ex and _ex.exercise_type.startswith("speech"):
            from app.domains.monologue.service import MonologueService

            mono = MonologueService(db)
            speech_metrics_dict = {}
            if payload.speech_metrics:
                speech_metrics_dict = payload.speech_metrics.model_dump()
            # merge flattened speech fields
            if payload.speech_duration_ms is not None:
                speech_metrics_dict["speech_duration_ms"] = payload.speech_duration_ms
            if payload.target_duration_ms is not None:
                speech_metrics_dict["target_duration_ms"] = payload.target_duration_ms
            if payload.timer_limit_ms is not None:
                speech_metrics_dict["timer_limit_ms"] = payload.timer_limit_ms
            mono_res = await mono.evaluate_exercise(
                exercise_id=exercise_id,
                user_id=user_id,
                user_transcript=payload.user_transcript,
                audio_base64=payload.audio_base64,
                speech_metrics=speech_metrics_dict,
                used_hint=payload.used_hint,
                plan_item_id=payload.plan_item_id,
            )
            # Map monologue result to ExerciseResultDTO shape
            if mono_res.get("status") == "RETRY_AUDIO":
                # Return low score but keep DTO shape
                return ExerciseResultDTO(
                    exercise_id=exercise_id,
                    score=0.0,
                    success=False,
                    confidence=0.3,
                    target_mastery_delta={},
                    feedback=mono_res.get("feedback", "Audio retry"),
                    evidence=mono_res.get("evidence", []),
                    metrics=mono_res.get("metrics", {}),
                    independence="independent" if not payload.used_hint else "assisted_hint",
                    response_speed_ms=payload.response_speed_ms,
                    target_usage="not_attempted",
                )
            return ExerciseResultDTO(
                exercise_id=exercise_id,
                score=float(mono_res.get("score", 0)),
                success=bool(mono_res.get("success", False)),
                confidence=float(mono_res.get("confidence", 0.8)),
                target_mastery_delta=mono_res.get("target_mastery_delta", {}),
                feedback=mono_res.get("feedback", ""),
                evidence=mono_res.get("evidence", []),
                metrics=mono_res.get("metrics", {}) or mono_res,
                independence="independent" if not payload.used_hint else "assisted_hint",
                response_speed_ms=payload.response_speed_ms or speech_metrics_dict.get("speech_duration_ms"),
                target_usage="correct" if mono_res.get("success") else "incorrect",
            )
    except Exception as e:
        # fall through to generic path if monologue delegation fails
        from app.core.logging import logger

        logger.warning(f"[Learning Submit] speech delegation fallback: {e}")

    session_svc = ExerciseSessionService(db)
    # Build reflex/keigo/pitch/situational metrics dict for evaluator (alias)
    reflex_metrics = None
    keigo_metrics = None
    pitch_metrics = None
    situational_metrics = None
    if payload.reflex_metrics:
        reflex_metrics = payload.reflex_metrics.model_dump()
    if payload.keigo_metrics:
        keigo_metrics = payload.keigo_metrics.model_dump()
    if payload.pitch_metrics:
        pitch_metrics = payload.pitch_metrics.model_dump()
    if payload.situational_metrics:
        situational_metrics = payload.situational_metrics.model_dump()
    elif payload.reflex_metrics is None and payload.keigo_metrics is None and payload.pitch_metrics is None and payload.situational_metrics is None and any(v is not None for v in [payload.reaction_latency_ms, payload.timer_limit_ms, payload.timed_out, payload.pitch_confidence, payload.audio_quality]):
        reflex_metrics = {
            "reaction_latency_ms": payload.reaction_latency_ms,
            "semantic_latency_ms": payload.semantic_latency_ms,
            "timer_limit_ms": payload.timer_limit_ms,
            "timed_out": payload.timed_out or False,
            "late_response": payload.late_response or False,
            "speech_confidence": payload.speech_confidence,
            "pitch_confidence": payload.pitch_confidence,
            "audio_quality": payload.audio_quality,
        }
        keigo_metrics = pitch_metrics = situational_metrics = reflex_metrics
    result = await session_svc.submit_exercise_attempt(
        exercise_id=exercise_id,
        user_id=user_id,
        user_transcript=payload.user_transcript,
        turn_analysis_score=payload.turn_analysis_score,
        pronunciation_score=payload.pronunciation_score,
        response_speed_ms=payload.response_speed_ms or payload.reaction_latency_ms,
        used_hint=payload.used_hint,
        plan_item_id=payload.plan_item_id,
        reflex_metrics=reflex_metrics,
        keigo_metrics=keigo_metrics,
        pitch_metrics=pitch_metrics,
        situational_metrics=situational_metrics,
        reaction_latency_ms=payload.reaction_latency_ms,
        semantic_latency_ms=payload.semantic_latency_ms,
        timer_limit_ms=payload.timer_limit_ms,
        timed_out=payload.timed_out,
        late_response=payload.late_response,
        speech_confidence=payload.speech_confidence,
        pitch_confidence=payload.pitch_confidence,
        audio_quality=payload.audio_quality,
    )
    return result


# 7. Adaptive Curriculum Units & Full Milestone Roadmap
@router.get("/curriculum", response_model=list[CurriculumUnitDTO])
async def get_dynamic_curriculum(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Synthesizes dynamic curriculum units based on active goals and mastery."""
    engine = CurriculumEngine(db)
    return await engine.generate_dynamic_curriculum(user_id=user_id)


@router.get("/roadmap")
async def get_curriculum_roadmap(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full 4-stage interactive milestone roadmap for the learner."""
    engine = CurriculumEngine(db)
    return await engine.get_curriculum_roadmap(user_id=user_id)


@router.post("/roadmap/generate")
async def generate_curriculum_roadmap(
    payload: dict[str, Any],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generates / regenerates a bespoke AI speaking curriculum roadmap."""
    engine = CurriculumEngine(db)
    return await engine.get_curriculum_roadmap(
        user_id=user_id,
        level=payload.get("level", "intermediate"),
        target_goal=payload.get("target_goal", "workplace"),
        daily_minutes=payload.get("daily_minutes", 30),
        custom_wish=payload.get("custom_wish"),
        force_regenerate=True,
    )


@router.post("/roadmap/nodes/{node_id}/toggle")
async def toggle_roadmap_node(
    node_id: str,
    payload: dict[str, Any] = {},
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Toggles completion status and score of a specific lesson node in the roadmap."""
    engine = CurriculumEngine(db)
    res = await engine.toggle_node_completion(
        user_id=user_id,
        node_id=node_id,
        is_completed=payload.get("is_completed"),
        score=payload.get("score"),
    )
    if not res:
        raise NotFoundException(f"Roadmap node '{node_id}' not found.")
    return res


# 8. Full Recalculation Trigger
@router.post("/recalculate", status_code=status.HTTP_202_ACCEPTED)
async def trigger_recalculation(
    user_id: str = Depends(get_current_user_id),
):
    """Enqueues full learning state and item recalculation in the background."""
    await learning_job_queue.enqueue({
        "task_type": "LEARNING_STATE_RECALCULATION",
        "user_id": user_id,
    })
    return {"status": "enqueued", "message": "Learning state recalculation initiated."}
