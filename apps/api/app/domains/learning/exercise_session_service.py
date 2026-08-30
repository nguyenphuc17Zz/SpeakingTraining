from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.contracts import ExerciseResult, IndependenceLevel
from app.domains.learning.exercise_evaluator import ExerciseEvaluator
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.models import Exercise, ExerciseAttempt, LearningPlanItem
from app.shared.errors.exceptions import NotFoundException, ValidationException


class ExerciseSessionService:
    """Orchestrates interactive exercise session lifecycle, audio/text submissions, and closed-loop mastery updates."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.evaluator = ExerciseEvaluator(db)
        self.item_service = LearningItemService(db)

    async def start_exercise(
        self,
        exercise_id: str,
        user_id: str,
        session_id: str | None = None,
        pronunciation_attempt_id: str | None = None,
    ) -> ExerciseAttempt:
        """Initializes a new user attempt on an exercise."""
        stmt = select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
        res = await self.db.execute(stmt)
        exercise = res.scalar_one_or_none()
        if not exercise:
            raise NotFoundException(f"Exercise '{exercise_id}' not found.")

        exercise.status = "in_progress"

        attempt = ExerciseAttempt(
            exercise_id=exercise.id,
            user_id=user_id,
            session_id=session_id,
            pronunciation_attempt_id=pronunciation_attempt_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            independence_level="independent",
        )
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        logger.info(f"[ExerciseSessionService] Started attempt '{attempt.id}' for exercise '{exercise.id}'")
        return attempt

    async def submit_exercise_attempt(
        self,
        exercise_id: str,
        user_id: str,
        user_transcript: str,
        turn_analysis_score: float | None = None,
        pronunciation_score: float | None = None,
        response_speed_ms: float | None = None,
        used_hint: bool = False,
        plan_item_id: str | None = None,
        reflex_metrics: dict[str, Any] | None = None,
        keigo_metrics: dict[str, Any] | None = None,
        pitch_metrics: dict[str, Any] | None = None,
        situational_metrics: dict[str, Any] | None = None,
        # Flattened reflex/keigo/pitch/situational timing (alternative to reflex_metrics)
        reaction_latency_ms: float | None = None,
        semantic_latency_ms: float | None = None,
        timer_limit_ms: int | None = None,
        timed_out: bool | None = None,
        late_response: bool | None = None,
        speech_confidence: float | None = None,
        pitch_confidence: float | None = None,
        audio_quality: float | None = None,
    ) -> ExerciseResult:
        """
        Submits learner response for evaluation and immediately triggers closed-loop mastery updates.
        """
        stmt = select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
        res = await self.db.execute(stmt)
        exercise = res.scalar_one_or_none()
        if not exercise:
            raise NotFoundException(f"Exercise '{exercise_id}' not found.")

        # Find or create active attempt
        att_stmt = (
            select(ExerciseAttempt)
            .where(
                ExerciseAttempt.exercise_id == exercise_id,
                ExerciseAttempt.user_id == user_id,
                ExerciseAttempt.status == "in_progress",
            )
            .order_by(ExerciseAttempt.started_at.desc())
        )
        att_res = await self.db.execute(att_stmt)
        attempt = att_res.scalar_one_or_none()

        if not attempt:
            attempt = await self.start_exercise(exercise_id, user_id)

        # Build normalized reflex/keigo/pitch/situational metrics dict from either nested or flattened inputs (alias)
        _reflex_metrics: dict[str, Any] = {}
        if situational_metrics:
            _reflex_metrics.update(situational_metrics)
        if pitch_metrics:
            _reflex_metrics.update(pitch_metrics)
        if keigo_metrics:
            _reflex_metrics.update(keigo_metrics)
        if reflex_metrics:
            _reflex_metrics.update(reflex_metrics)
        # Flattened overrides
        if reaction_latency_ms is not None:
            _reflex_metrics["reaction_latency_ms"] = reaction_latency_ms
        if semantic_latency_ms is not None:
            _reflex_metrics["semantic_latency_ms"] = semantic_latency_ms
        if timer_limit_ms is not None:
            _reflex_metrics["timer_limit_ms"] = timer_limit_ms
        if timed_out is not None:
            _reflex_metrics["timed_out"] = bool(timed_out)
        if late_response is not None:
            _reflex_metrics["late_response"] = bool(late_response)
        if speech_confidence is not None:
            _reflex_metrics["speech_confidence"] = speech_confidence
        if pitch_confidence is not None:
            _reflex_metrics["pitch_confidence"] = pitch_confidence
        if audio_quality is not None:
            _reflex_metrics["audio_quality"] = audio_quality
        if user_transcript:
            _reflex_metrics["transcript"] = user_transcript
        # Ensure response_speed_ms is synced with reaction_latency if not explicitly set
        if response_speed_ms is None and _reflex_metrics.get("reaction_latency_ms") is not None:
            response_speed_ms = float(_reflex_metrics["reaction_latency_ms"])
        _has_metrics = bool(_reflex_metrics)
        if not _reflex_metrics:
            _reflex_metrics = None  # type: ignore

        # 1. Run Evaluation
        result = await self.evaluator.evaluate_attempt(
            exercise=exercise,
            attempt=attempt,
            user_transcript=user_transcript,
            turn_analysis_score=turn_analysis_score,
            pronunciation_score=pronunciation_score,
            response_speed_ms=response_speed_ms,
            used_hint=used_hint,
            reflex_metrics=_reflex_metrics,
            keigo_metrics=_reflex_metrics,
            pitch_metrics=_reflex_metrics,
            situational_metrics=_reflex_metrics,
        )

        # 2. Update Learning Item Masteries
        deltas_map: dict[str, float] = {}
        for key in (exercise.learning_item_keys or []):
            update_info = await self.item_service.update_item_from_result(
                user_id=user_id,
                item_key=key,
                result=result,
                context_tag=exercise.exercise_type,
            )
            if update_info and "delta" in update_info:
                deltas_map[key] = update_info["delta"]

        result.target_mastery_delta = deltas_map

        # 3. Update Attempt and Exercise records
        now = datetime.now(timezone.utc)
        attempt.status = "completed"
        attempt.completed_at = now
        attempt.score = result.score
        attempt.success = result.success
        attempt.assessment_confidence = result.confidence
        attempt.independence_level = result.independence.value
        attempt.response_speed_ms = response_speed_ms
        attempt.target_usage = result.target_usage
        attempt.feedback = result.feedback
        attempt.metrics_json = result.metrics
        # Merge reflex/keigo/pitch/situational timing into metrics if present (already in result.metrics.*)
        if _has_metrics and _reflex_metrics is not None:
            if attempt.metrics_json is None:
                attempt.metrics_json = {}
            if exercise.exercise_type.startswith("keigo"):
                attempt.metrics_json.setdefault("keigo", _reflex_metrics)
                attempt.metrics_json.setdefault("reflex", _reflex_metrics)
            elif exercise.exercise_type.startswith("pitch") or exercise.exercise_type in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition"):
                attempt.metrics_json.setdefault("pitch", _reflex_metrics)
                attempt.metrics_json.setdefault("reflex", _reflex_metrics)
            elif exercise.exercise_type.startswith("situational"):
                attempt.metrics_json.setdefault("situational", _reflex_metrics)
                attempt.metrics_json.setdefault("reflex", _reflex_metrics)
            else:
                attempt.metrics_json.setdefault("reflex", _reflex_metrics)
        attempt.mastery_deltas_json = deltas_map

        exercise.status = "completed"

        # 4. Mark linked Daily Plan Item as completed
        if plan_item_id:
            pi_stmt = select(LearningPlanItem).where(LearningPlanItem.id == plan_item_id)
            pi_res = await self.db.execute(pi_stmt)
            plan_item = pi_res.scalar_one_or_none()
            if plan_item:
                plan_item.status = "completed"
                plan_item.completed_at = now

        await self.db.commit()
        logger.info(f"[ExerciseSessionService] Completed exercise '{exercise.id}' attempt '{attempt.id}' (Score: {result.score})")

        # 5. Emit GameEvent to Gamification Engine
        try:
            from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
            from app.domains.gamification.infrastructure.game_event_publisher import GameEventPublisher

            # Enrich game event with reflex metadata for quest/personal best detection
            _game_meta: dict[str, Any] = {
                "exercise_id": exercise.id,
                "exercise_type": exercise.exercise_type,
                "difficulty": exercise.difficulty,
                "score": result.score,
                "success": result.success,
                "independence_level": result.independence.value,
                "mastery_delta": sum(deltas_map.values()) if deltas_map else 0.0,
            }
            if _reflex_metrics:
                _game_meta["reflex"] = _reflex_metrics
                if _reflex_metrics.get("timed_out"):
                    _game_meta["timed_out"] = True
                if _reflex_metrics.get("reaction_latency_ms") is not None:
                    _game_meta["reaction_latency_ms"] = _reflex_metrics["reaction_latency_ms"]
            await GameEventPublisher.publish(
                user_id=user_id,
                event_type=GameEventType.EXERCISE_COMPLETED,
                source=GameEventSource.LEARNING,
                source_id=attempt.id,
                metadata=_game_meta,
            )
        except Exception as e:
            logger.warning(f"[ExerciseSessionService] Non-critical error emitting game event: {e}")

        return result
