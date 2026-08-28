"""MonologueService — orchestration for generation + evaluation + persistence."""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.contracts import DifficultyLevel, ExerciseType, LearningItemType
from app.domains.learning.exercise_session_service import ExerciseSessionService
from app.domains.learning.models import Exercise
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.monologue.contracts import SpeechGenerationInput, SpeechTaskSpec
from app.domains.monologue.evaluator import MonologueEvaluator
from app.domains.monologue.generation.speech_topic_generator import SpeechTopicGenerator
from app.domains.users.service import UserService


class MonologueService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.generator = SpeechTopicGenerator(db)
        self.evaluator = MonologueEvaluator(db)

    async def generate_exercise(
        self,
        user_id: str,
        duration_sec: int = 60,
        prep_sec: int | None = None,
        difficulty: int | None = None,
        genre: str | None = None,
        support_level: int | None = None,
        topic_domain: str | None = None,
        seed: str | None = None,
    ) -> Exercise:
        # Build learner context
        profile_svc = LearnerProfileService(self.db)
        profile = await profile_svc.get_or_create_profile(user_id)

        # Get recent signatures/topics for variety
        from sqlalchemy import select, desc

        from app.domains.learning.models import Exercise as ExModel

        stmt = select(ExModel).where(ExModel.user_id == user_id, ExModel.exercise_type.like("speech%")).order_by(desc(ExModel.created_at)).limit(20)
        res = await self.db.execute(stmt)
        recent_ex = list(res.scalars().all())
        recent_sigs = [e.exercise_signature for e in recent_ex if e.exercise_signature]
        recent_topics = []
        recent_genres = []
        for e in recent_ex:
            if e.extra_metadata and isinstance(e.extra_metadata, dict):
                sc = e.extra_metadata.get("speech_config", {})
                if sc.get("topic"):
                    recent_topics.append(sc["topic"])
                if sc.get("genre"):
                    recent_genres.append(sc["genre"])

        # Interests/career from profile extra? fallback
        interests = []
        career_domain = None
        try:
            # profile may have interests in extra_metadata
            if hasattr(profile, "extra_metadata") and profile.extra_metadata:
                interests = profile.extra_metadata.get("interests", []) or []
                career_domain = profile.extra_metadata.get("career_domain")
        except Exception:
            pass

        weaknesses = profile.weaknesses or []  # list of dicts

        inp = SpeechGenerationInput(
            user_id=user_id,
            overall_level=getattr(profile, "overall_level", "N3") or "N3",
            speaking_level=getattr(profile, "speaking_level", "N3") or "N3",
            recent_signatures=recent_sigs,
            recent_topics=recent_topics,
            recent_genres=recent_genres,
            interests=interests,
            career_domain=career_domain,
            learning_targets=[],
            weaknesses=weaknesses,
            difficulty=difficulty,
            duration_sec=duration_sec,
            prep_sec=prep_sec or 30,
            genre=genre,
            support_level=support_level,
            topic_domain=topic_domain,
            seed=seed,
        )
        spec: SpeechTaskSpec = await self.generator.generate(inp.model_dump())

        # Persist as Exercise
        # Map difficulty 1-5 to DifficultyLevel
        diff_map = {1: "easy", 2: "easy", 3: "normal", 4: "hard", 5: "challenge"}
        diff_str = diff_map.get(spec.difficulty, "normal")

        # Determine exercise_type — keep as speech_monologue generic, genre in metadata
        ex_type = "speech_monologue"

        # Build scaffold hint (VI+JP hybrid: topic VI, instruction JP)
        scaffold_hint = None
        if spec.support_level.value == 1 and spec.support.keywords:
            scaffold_hint = "Keywords: " + ", ".join(spec.support.keywords)
        elif spec.support_level.value == 2 and spec.support.guided_questions:
            scaffold_hint = "Guided: " + " | ".join(spec.support.guided_questions)
        elif spec.support_level.value == 3 and spec.support.outline:
            scaffold_hint = "Outline: " + " → ".join(spec.support.outline)

        # Learning item keys — ensure at least one speech item exists
        from app.domains.learning.learning_item_service import LearningItemService

        item_svc = LearningItemService(self.db)
        # try to find existing speech learning item
        items = await item_svc.list_items(user_id, limit=10)
        # Prefer fluency/coherence item
        candidate = next((i for i in items if i.item_type in ("fluency", "naturalness", "vocabulary")), None)
        if candidate:
            lkey = candidate.key
        else:
            # create on fly
            from app.domains.learning.models import LearningItem
            import uuid

            lkey = f"speech.{spec.genre.value}.{diff_str}"
            existing = await item_svc.get_item_by_key(lkey, user_id)
            if not existing:
                new_item = LearningItem(
                    user_id=user_id,
                    key=lkey,
                    item_type="fluency",
                    title=f"Speech — {spec.genre.value.title()} ({diff_str})",
                    description=f"Monologue {spec.genre.value} {spec.expected_duration_sec}s",
                    difficulty=diff_str,
                    lifecycle="active",
                    status="active",
                )
                self.db.add(new_item)
                await self.db.flush()

        exercise = Exercise(
            user_id=user_id,
            exercise_type=ex_type,
            status="not_started",
            title=spec.topic,
            objective=f"Monologue {spec.genre.value} — {spec.instruction}",
            scenario=spec.instruction,
            instructions=spec.instruction,
            constraints=spec.constraints,
            target_patterns=[spec.topic, spec.genre.value] + spec.learning_targets,
            learning_item_keys=[lkey],
            success_criteria=["Nói liên tục, coherence, đúng genre, kết luận rõ"],
            acceptable_variants=[],
            difficulty=diff_str,
            scaffold_level={0:"none",1:"keyword_hint",2:"sentence_starter",3:"structured_options",4:"none"}.get(spec.support_level.value, "none"),
            scaffold_hint=scaffold_hint,
            estimated_minutes=max(1, spec.expected_duration_sec // 60 + 1),
            template_version="v1",
            generator_version=SpeechTopicGenerator.GENERATOR_VERSION,
            prompt_version="monologue.gen.v1",
            provider=spec.provider,
            model=spec.model,
            exercise_signature=spec.session_signature,
            extra_metadata={
                "speech_config": {
                    "genre": spec.genre.value,
                    "topic": spec.topic,
                    "instruction": spec.instruction,
                    "topic_domain": spec.topic_domain.value,
                    "difficulty": spec.difficulty,
                    "target_duration_sec": spec.expected_duration_sec,
                    "prep_duration_sec": spec.prep_duration_sec,
                    "support_level": spec.support_level.value,
                    "support": spec.support.model_dump(),
                    "constraints": spec.constraints,
                    "learning_targets": spec.learning_targets,
                    "outline_hint": spec.outline_hint,
                    "session_signature": spec.session_signature,
                },
                "priority_score": 0.75,
                "item_type": "speech",
            },
        )
        self.db.add(exercise)
        await self.db.commit()
        await self.db.refresh(exercise)
        logger.info(f"[MonologueService] Created speech exercise '{exercise.title}' ({exercise.id}) genre={spec.genre.value}")
        return exercise

    async def evaluate_exercise(
        self,
        exercise_id: str,
        user_id: str,
        user_transcript: str | None = None,
        audio_base64: str | None = None,
        speech_metrics: dict[str, Any] | None = None,
        used_hint: bool = False,
        plan_item_id: str | None = None,
    ) -> dict[str, Any]:
        from sqlalchemy import select

        from app.domains.learning.models import Exercise, ExerciseAttempt

        stmt = select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
        res = await self.db.execute(stmt)
        exercise = res.scalar_one_or_none()
        if not exercise:
            from app.shared.errors.exceptions import NotFoundException

            raise NotFoundException(f"Exercise '{exercise_id}' not found")

        sc = (exercise.extra_metadata or {}).get("speech_config", {}) if exercise.extra_metadata else {}
        target_sec = sc.get("target_duration_sec", 60)
        target_ms = int(target_sec * 1000)

        # Do NOT trust client target_duration_ms (spoofable) — use authoritative exercise config
        if speech_metrics and speech_metrics.get("target_duration_ms"):
            client_target = int(speech_metrics.get("target_duration_ms"))
            if abs(client_target - target_ms) > 5000:
                logger.warning(f"[MonologueService] client target_duration_ms {client_target} differs from authoritative {target_ms}, ignoring")

        eval_res = await self.evaluator.evaluate(
            exercise=exercise,
            user_transcript=user_transcript,
            audio_base64=audio_base64,
            speech_metrics=speech_metrics,
            target_duration_ms=target_ms,
            user_id=user_id,
        )

        # Handle RETRY_AUDIO
        if eval_res.get("status") == "RETRY_AUDIO":
            return eval_res

        # Persist via ExerciseSessionService (mastery, analytics, gamification)
        # Build attempt if not exists
        session_svc = ExerciseSessionService(self.db)
        # Find or create attempt
        from sqlalchemy import select as sel

        att_stmt = sel(ExerciseAttempt).where(
            ExerciseAttempt.exercise_id == exercise_id, ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "in_progress"
        ).order_by(ExerciseAttempt.started_at.desc())
        att_res = await self.db.execute(att_stmt)
        attempt = att_res.scalar_one_or_none()
        if not attempt:
            # create new attempt via start
            attempt = await session_svc.start_exercise(exercise_id, user_id)
        # Build ExerciseResult for mastery delta computation (reuse existing service's result mapping)
        from app.domains.learning.contracts import ExerciseResult, IndependenceLevel

        # Use evaluator's overall as score
        score = float(eval_res.get("score", 0))
        success = bool(eval_res.get("success", False))
        confidence = float(eval_res.get("confidence", 0.8))

        # Update attempt manually (bypass ExerciseEvaluator generic path but reuse mastery update)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        attempt.status = "completed"
        attempt.completed_at = now
        attempt.score = score
        attempt.success = success
        attempt.assessment_confidence = confidence
        attempt.independence_level = IndependenceLevel.ASSISTED_HINT.value if used_hint else IndependenceLevel.INDEPENDENT.value
        # Use server-derived duration (not client spoof)
        server_duration = eval_res.get("metrics", {}).get("speech_duration_ms") if eval_res.get("metrics") else None
        attempt.response_speed_ms = server_duration
        attempt.target_usage = "correct" if success else "incorrect"
        attempt.feedback = eval_res.get("feedback")
        attempt.metrics_json = eval_res.get("metrics")
        # store assessment separately in metrics_json.assessment
        if attempt.metrics_json is not None:
            attempt.metrics_json["assessment"] = eval_res.get("assessment")
            attempt.metrics_json["ai_result"] = eval_res.get("ai_result")
            attempt.metrics_json["upgrade"] = eval_res.get("upgrade")
            attempt.metrics_json["speech_config"] = sc
        attempt.mastery_deltas_json = {}

        exercise.status = "completed"

        # Mastery deltas for each learning_item_keys
        deltas_map: dict[str, float] = {}
        # Map speech assessment dimensions to learning items
        # We use a synthetic ExerciseResult to feed MasteryEngine
        result_for_mastery = ExerciseResult(
            exercise_id=exercise.id,
            user_id=user_id,
            score=score,
            success=success,
            confidence=confidence,
            target_mastery_delta={},
            feedback=eval_res.get("feedback", ""),
            evidence=eval_res.get("evidence", []),
            metrics=eval_res.get("metrics", {}),
            independence=IndependenceLevel.ASSISTED_HINT if used_hint else IndependenceLevel.INDEPENDENT,
            response_speed_ms=attempt.response_speed_ms,
            target_usage="correct" if success else "incorrect",
            pronunciation_score=eval_res.get("assessment", {}).get("pronunciation"),
            grammar_score=eval_res.get("assessment", {}).get("grammar"),
            naturalness_score=eval_res.get("assessment", {}).get("naturalness"),
            attempt_id=attempt.id,
        )
        from app.domains.learning.learning_item_service import LearningItemService

        item_svc = LearningItemService(self.db)
        for key in (exercise.learning_item_keys or []):
            upd = await item_svc.update_item_from_result(user_id=user_id, item_key=key, result=result_for_mastery, context_tag="speech_monologue")
            if upd and "delta" in upd:
                deltas_map[key] = upd["delta"]
        attempt.mastery_deltas_json = deltas_map

        # Plan item completion — IDOR fix: verify ownership via LearningPlan
        if plan_item_id:
            from app.domains.learning.models import LearningPlan, LearningPlanItem

            pi_stmt = (
                sel(LearningPlanItem)
                .join(LearningPlan, LearningPlanItem.plan_id == LearningPlan.id)
                .where(LearningPlanItem.id == plan_item_id, LearningPlan.user_id == user_id)
            )
            pi_res = await self.db.execute(pi_stmt)
            pi = pi_res.scalar_one_or_none()
            if pi:
                pi.status = "completed"
                pi.completed_at = now
            else:
                logger.warning(f"[MonologueService] plan_item {plan_item_id} not owned by {user_id} — 404")
                from app.shared.errors.exceptions import NotFoundException

                raise NotFoundException("Learning plan item not found")

        await self.db.commit()

        # Gamification event
        try:
            from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
            from app.domains.gamification.infrastructure.game_event_publisher import GameEventPublisher

            await GameEventPublisher.publish(
                user_id=user_id,
                event_type=GameEventType.EXERCISE_COMPLETED,
                source=GameEventSource.LEARNING,
                source_id=attempt.id,
                metadata={
                    "exercise_id": exercise.id,
                    "exercise_type": exercise.exercise_type,
                    "difficulty": exercise.difficulty,
                    "score": score,
                    "success": success,
                    "independence_level": attempt.independence_level,
                    "mastery_delta": sum(deltas_map.values()) if deltas_map else 0.0,
                    "genre": sc.get("genre"),
                    "duration_sec": target_sec,
                    "speech": True,
                },
            )
        except Exception as e:
            logger.warning(f"[MonologueService] game event failed: {e}")

        # Return combined
        return {
            **eval_res,
            "attempt_id": attempt.id,
            "exercise_id": exercise.id,
            "target_mastery_delta": deltas_map,
        }
