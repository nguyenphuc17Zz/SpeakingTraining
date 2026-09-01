"""RampSessionService — orchestrates a complete Mode 6 session lifecycle.

§40 Session Structure, §41 Session Length, §42 User Goal,
§60 AI Coach Integration, §65 API.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.contracts import (
    DifficultyLevel,
    ExerciseType,
    IndependenceLevel,
    ScaffoldingLevel,
)
from app.domains.learning.models import Exercise, ExerciseAttempt
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.ramp.contracts import (
    RampAttemptFeedback,
    RampGenerationInput,
    RampProgressSnapshot,
    RampScore,
    RampSessionState,
    RampSessionSummary,
    RampTaskSpec,
)
from app.domains.ramp.followup_generator import FollowUpGenerator
from app.domains.ramp.models import RampSessionModel
from app.domains.ramp.ramp_evaluator import RampEvaluator
from app.domains.ramp.ramp_progression_engine import RampProgressionEngine
from app.domains.ramp.speaking_ramp_generator import SpeakingRampGenerator
from app.domains.ramp.stage_engine import RampStageEngine
from app.domains.users.service import UserService


class RampSessionService:
    """Orchestrates Mode 6 session lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.generator = SpeakingRampGenerator(db)
        self.evaluator = RampEvaluator(db)
        self.progression = RampProgressionEngine(db)
        self.followup_gen = FollowUpGenerator(db)
        self.stage_engine = RampStageEngine()

    # ---------------------------------------------------------------------------
    # Session Management
    # ---------------------------------------------------------------------------

    async def create_session(
        self,
        user_id: str,
        desired_minutes: int = 15,
        session_goal: str | None = None,
        current_stage: int | None = None,
        support_level: int | None = None,
    ) -> RampSessionModel:
        """Create and persist a new ramp session."""
        # Get learner state for defaults
        profile_svc = LearnerProfileService(self.db)
        profile = await profile_svc.get_or_create_profile(user_id)

        # Determine starting stage from profile or default based on session_goal
        if current_stage is not None:
            stage = current_stage
        elif session_goal == "fluency":
            stage = 1
        elif session_goal == "elaboration":
            stage = 4
        elif session_goal == "independence":
            stage = 7
        else:
            stage = 1

        if support_level is not None:
            sup_level = support_level
        elif session_goal == "independence":
            sup_level = 1
        elif session_goal in ("fluency", "elaboration"):
            sup_level = 2
        else:
            sup_level = 3

        session = RampSessionModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            state=RampSessionState.IDLE.value,
            stage=stage,
            stage_start=stage,
            support_level=sup_level,
            support_level_start=sup_level,
            desired_minutes=desired_minutes,
            session_goal=session_goal,
            exercises_completed=0,
            exercises_total=self._estimate_exercises(desired_minutes, stage),
            stage_attempt_buffer=[],
            attempt_results=[],
            milestones_achieved=[],
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        logger.info(f"[RampSessionService] Created session {session.id} for user {user_id}")
        return session

    async def get_session(self, session_id: str, user_id: str) -> RampSessionModel | None:
        stmt = select(RampSessionModel).where(
            RampSessionModel.id == session_id,
            RampSessionModel.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def generate_next_exercise(
        self,
        session_id: str,
        user_id: str,
        is_retry: bool = False,
        force_followup: bool = False,
    ) -> tuple[Exercise, RampTaskSpec]:
        """Generate next exercise for session, persist as Exercise, return both."""
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Build generation input from session state
        profile_svc = LearnerProfileService(self.db)
        profile = await profile_svc.get_or_create_profile(user_id)

        interests = []
        try:
            if hasattr(profile, "extra_metadata") and profile.extra_metadata:
                interests = profile.extra_metadata.get("interests", []) or []
        except Exception:
            pass

        target_sec = self.stage_engine.get_target_duration_sec(session.stage)
        last_response = None
        topic_context = session.topic_context

        # Get last response for follow-up generation
        attempts = session.attempt_results or []
        if attempts:
            last_attempt = attempts[-1]
            last_response = last_attempt.get("transcript")

        inp = RampGenerationInput(
            user_id=user_id,
            learner_level=getattr(profile, "overall_level", "N3") or "N3",
            measured_speaking_level=getattr(profile, "speaking_level", "N4") or "N4",
            current_stage=session.stage,
            support_level=session.support_level,
            interests=interests,
            topic_history=[a.get("topic", "") for a in attempts[-10:] if a.get("topic")],
            desired_duration_sec=target_sec,
            session_goal=session.session_goal,
            previous_response=last_response,
            session_topic_context=topic_context,
            is_retry=is_retry,
        )

        # Generate task spec
        from app.domains.ramp.contracts import RampExerciseType, STAGE_EXERCISE_TYPE
        force_type = None
        if force_followup and last_response:
            force_type = RampExerciseType.SPEAK_FOLLOWUP

        task_spec = await self.generator.generate(inp, force_exercise_type=force_type)

        # Sticky topic for follow-up continuity (§52)
        if session.stage >= 7 and not force_followup:
            if not session.topic_context:
                session.topic_context = task_spec.topic
        elif force_followup:
            task_spec.session_topic_context = session.topic_context

        # Build and persist Exercise record
        exercise = await self._persist_as_exercise(user_id, task_spec, session.stage, session.support_level)

        # Update session state
        session.state = RampSessionState.PROMPTING.value
        await self.db.commit()

        return exercise, task_spec

    async def submit_attempt(
        self,
        session_id: str,
        exercise_id: str,
        user_id: str,
        user_transcript: str,
        audio_base64: str | None = None,
        support_level_used: int | None = None,
        used_hint: bool = False,
        response_latency_ms: float | None = None,
    ) -> dict[str, Any]:
        """
        Submit an attempt, evaluate, update progression, return full result.
        §37 Immediate feedback + retry policy.
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Fetch exercise
        stmt = select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == user_id)
        res = await self.db.execute(stmt)
        exercise = res.scalar_one_or_none()
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")

        # Reconstruct task_spec from exercise metadata
        task_spec = self._task_spec_from_exercise(exercise)

        # Audio processing (if provided) via MonologuePipeline (§25 reuse)
        audio_metrics: dict[str, Any] | None = None
        if audio_base64 and user_transcript:
            try:
                audio_metrics = await self._process_audio_metrics(
                    audio_base64=audio_base64,
                    transcript=user_transcript,
                    target_duration_ms=task_spec.target_duration_sec * 1000,
                )
            except Exception as e:
                logger.warning(f"[RampSessionService] Audio processing failed: {e}")

        sup_level = support_level_used if support_level_used is not None else session.support_level

        # Evaluate
        score, feedback = await self.evaluator.evaluate(
            task_spec=task_spec,
            user_transcript=user_transcript,
            support_level_used=sup_level,
            audio_metrics=audio_metrics,
            response_latency_ms=response_latency_ms,
            used_hint=used_hint,
        )

        # Generate follow-up if appropriate (§19 Exercise K)
        followup = None
        if session.stage >= 5 and score.overall >= 60 and not feedback.incomplete_sentence:
            prev_followups_list = [
                a.get("followup_question", "") for a in (session.attempt_results or []) if a.get("followup_question")
            ]
            depth = min(5, len(prev_followups_list) + 1)
            try:
                followup = await self.followup_gen.generate(
                    user_response=user_transcript,
                    topic=task_spec.topic,
                    stage=session.stage,
                    previous_followups=prev_followups_list,
                    current_depth=depth,
                )
                feedback.followup = followup
            except Exception as e:
                logger.warning(f"[RampSessionService] FollowUp generation failed: {e}")

        # Update progression
        delta = await self.progression.process_attempt(
            session=session,
            score=score,
            feedback=feedback,
            task_spec_dict={"exercise_type": exercise.exercise_type, "topic": task_spec.topic},
        )

        # Record attempt in session
        attempt_entry: dict[str, Any] = {
            "exercise_id": exercise_id,
            "transcript": user_transcript,
            "topic": task_spec.topic,
            "score": score.overall,
            "success": delta["success"],
            "independence_level": score.independence_level,
            "speech_duration_ms": score.speech_duration_ms,
            "followup_question": followup.question_jp if followup else None,
            "support_level_used": sup_level,
        }
        results = list(session.attempt_results or [])
        results.append(attempt_entry)
        session.attempt_results = results[-50:]  # cap at 50

        # Persist exercise attempt
        await self._persist_exercise_attempt(exercise, user_id, score, user_transcript, sup_level, audio_metrics)

        # Mark exercise done
        exercise.status = "completed"
        session.state = RampSessionState.FEEDBACK.value

        await self.db.commit()

        return {
            "score": score.model_dump(),
            "feedback": feedback.model_dump(),
            "delta": delta,
            "new_stage": session.stage,
            "new_support_level": session.support_level,
            "followup": followup.model_dump() if followup else None,
            "session_state": session.state,
        }

    async def complete_session(self, session_id: str, user_id: str) -> RampSessionSummary:
        """Finalize session and build summary. §59"""
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.state = RampSessionState.COMPLETED.value
        now = datetime.now(timezone.utc)
        session.completed_at = now

        completed = max(session.exercises_completed or 1, 1)
        if session.started_at:
            started = session.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            elapsed_min = (now - started).total_seconds() / 60
        else:
            elapsed_min = float(session.desired_minutes)

        summary = RampSessionSummary(
            session_id=session_id,
            duration_minutes=round(elapsed_min, 1),
            exercises_completed=session.exercises_completed or 0,
            stage_start=session.stage_start,
            stage_end=session.stage,
            support_level_start=session.support_level_start,
            support_level_end=session.support_level,
            independent_speaking_pct=(session.independent_success_count or 0) / completed,
            avg_response_duration_ms=(session.total_speech_duration_ms or 0) / completed,
            full_sentence_rate=(session.full_sentence_count or 0) / completed,
            elaboration_success_rate=(session.elaboration_success_count or 0) / completed,
            reason_example_rate=(
                ((session.reason_success_count or 0) + (session.example_success_count or 0)) / 2 / completed
            ),
            strengths=self._derive_strengths(session),
            weaknesses=self._derive_weaknesses(session),
            next_recommendation=self._build_recommendation(session),
            milestones_achieved=list(session.milestones_achieved or []),
        )

        await self.db.commit()
        return summary

    def get_progress_snapshot(
        self,
        session: RampSessionModel,
        user_id: str,
    ) -> RampProgressSnapshot:
        return self.progression.build_progress_snapshot(session, user_id)

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    async def _persist_as_exercise(
        self,
        user_id: str,
        task_spec: RampTaskSpec,
        stage: int,
        support_level: int,
    ) -> Exercise:
        """Store RampTaskSpec as an Exercise record (§66 reuse Exercise model)."""
        import hashlib
        sig_raw = f"{task_spec.topic}:{stage}:{task_spec.exercise_type.value}"
        sig = hashlib.sha256(sig_raw.encode()).hexdigest()[:16]

        exercise = Exercise(
            id=str(uuid.uuid4()),
            user_id=user_id,
            exercise_type=task_spec.exercise_type.value,
            status="not_started",
            title=f"[Ramp S{stage}] {task_spec.topic}",
            objective=f"Speaking ramp stage {stage}: {task_spec.exercise_type.value}",
            scenario=task_spec.prompt_vi,
            instructions=task_spec.prompt_jp,
            difficulty=DifficultyLevel.NORMAL.value,
            scaffold_level=ScaffoldingLevel.NONE.value if support_level == 0 else ScaffoldingLevel.KEYWORD_HINT.value,
            scaffold_hint=task_spec.scaffold.sentence_starter,
            estimated_minutes=max(1, task_spec.target_duration_sec // 60 + 1),
            exercise_signature=sig,
            generator_version="ramp.v1",
            extra_metadata={
                "ramp_config": {
                    "stage": stage,
                    "support_level": support_level,
                    "target_duration_sec": task_spec.target_duration_sec,
                    "task_type": task_spec.exercise_type.value,
                    "learning_targets": task_spec.learning_targets,
                    "topic": task_spec.topic,
                    "topic_domain": task_spec.topic_domain.value,
                    "prompt_jp": task_spec.prompt_jp,
                    "echo_sentence": task_spec.echo_sentence,
                    "template_sentence": task_spec.template_sentence,
                    "substitution_variable": task_spec.substitution_variable,
                    "seed_sentence": task_spec.seed_sentence,
                    "expansion_dimension": task_spec.expansion_dimension,
                    "keywords_for_production": task_spec.keywords_for_production,
                    "guided_questions": task_spec.scaffold.guided_questions,
                    "scaffold_keywords": task_spec.scaffold.keywords,
                    "sentence_starter": task_spec.scaffold.sentence_starter,
                    "example_response": task_spec.scaffold.example_response,
                    "previous_response": task_spec.previous_response,
                },
            },
        )
        self.db.add(exercise)
        await self.db.flush()
        return exercise

    async def _persist_exercise_attempt(
        self,
        exercise: Exercise,
        user_id: str,
        score: RampScore,
        transcript: str,
        support_level: int,
        audio_metrics: dict[str, Any] | None,
    ) -> ExerciseAttempt:
        """Persist attempt with ramp metrics."""
        from app.domains.learning.contracts import IndependenceLevel as IL
        indep_map = {
            "independent": IL.INDEPENDENT.value,
            "assisted_hint": IL.ASSISTED_HINT.value,
            "scaffolded": IL.SCAFFOLDED.value,
        }
        indep = indep_map.get(score.independence_level, IL.INDEPENDENT.value)

        attempt = ExerciseAttempt(
            id=str(uuid.uuid4()),
            exercise_id=exercise.id,
            user_id=user_id,
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            independence_level=indep,
            response_speed_ms=score.response_latency_ms,
            score=score.overall,
            success=score.overall >= 60.0,
            assessment_confidence=0.85,
            feedback=f"Production: {score.production_accuracy:.0f} | Independence: {score.independence:.0f}",
            metrics_json={
                "ramp_score": score.model_dump(),
                "support_level_used": support_level,
                **(audio_metrics or {}),
            },
        )
        self.db.add(attempt)
        return attempt

    def _task_spec_from_exercise(self, exercise: Exercise) -> RampTaskSpec:
        """Reconstruct minimal RampTaskSpec from Exercise.extra_metadata."""
        from app.domains.ramp.contracts import RampExerciseType, RampScaffold, RampTopicDomain
        rc = (exercise.extra_metadata or {}).get("ramp_config", {})

        try:
            ex_type = RampExerciseType(exercise.exercise_type)
        except ValueError:
            ex_type = RampExerciseType.SPEAK_SPONTANEOUS

        try:
            topic_domain = RampTopicDomain(rc.get("topic_domain", "daily_life"))
        except ValueError:
            topic_domain = RampTopicDomain.DAILY_LIFE

        return RampTaskSpec(
            exercise_type=ex_type,
            stage=rc.get("stage", 0),
            topic=rc.get("topic", "一般"),
            topic_domain=topic_domain,
            prompt_jp=rc.get("prompt_jp", exercise.instructions or ""),
            target_duration_sec=rc.get("target_duration_sec", 15),
            support_level=rc.get("support_level", 0),
            scaffold=RampScaffold(
                keywords=rc.get("scaffold_keywords", []),
                guided_questions=rc.get("guided_questions", []),
                sentence_starter=rc.get("sentence_starter"),
                example_response=rc.get("example_response"),
            ),
            echo_sentence=rc.get("echo_sentence"),
            template_sentence=rc.get("template_sentence"),
            substitution_variable=rc.get("substitution_variable"),
            seed_sentence=rc.get("seed_sentence"),
            expansion_dimension=rc.get("expansion_dimension"),
            keywords_for_production=rc.get("keywords_for_production", []),
            previous_response=rc.get("previous_response"),
            learning_targets=rc.get("learning_targets", ["spontaneous_production"]),
        )

    async def _process_audio_metrics(
        self,
        audio_base64: str,
        transcript: str,
        target_duration_ms: int,
    ) -> dict[str, Any]:
        """Process audio through MonologuePipeline for speech metrics. Reuse §25."""
        import re
        b64 = audio_base64.strip()
        if "," in b64 and b64.startswith("data:"):
            b64 = b64.split(",", 1)[1]
        b64 = re.sub(r"\s", "", b64)
        audio_bytes = base64.b64decode(b64)

        from app.domains.monologue.analytics.pipeline import MonologuePipeline
        from app.domains.speech.stt_router import stt_router
        from app.domains.speech.contracts import STTOptions

        stt_res = await stt_router.transcribe(
            audio_bytes=audio_bytes,
            options=STTOptions(language="ja", model="base"),
        )
        words = [
            {"word": w.word, "start_ms": w.start_ms, "end_ms": w.end_ms}
            for w in (stt_res.words or [])
        ]
        duration_ms = stt_res.duration_ms or (
            max(w["end_ms"] for w in words if w.get("end_ms")) if words else target_duration_ms
        )

        pipeline = MonologuePipeline()
        result = await pipeline.analyze_transcript(
            transcript=transcript,
            words=words,
            speech_duration_ms=duration_ms,
            target_duration_ms=target_duration_ms,
            stt_confidence=stt_res.confidence,
        )

        return {
            "speech_duration_ms": duration_ms,
            "filler_count": result.get("filler_summary", {}).get("total_fillers", 0),
            "filler_rate": result.get("filler_summary", {}).get("filler_ratio", 0.0),
            "long_pause_count": result.get("pause_summary", {}).get("long_pause_count", 0),
            "self_repair_count": result.get("repair_summary", {}).get("total_repairs", 0),
        }

    def _estimate_exercises(self, desired_minutes: int, stage: int) -> int:
        """Estimate total exercises for session. §41"""
        if desired_minutes <= 0:
            return 999  # Infinite mode
        per_min = 2 if stage <= 3 else 1.5 if stage <= 7 else 1
        return max(3, int(desired_minutes * per_min))

    def _derive_strengths(self, session: RampSessionModel) -> list[str]:
        completed = max(session.exercises_completed or 1, 1)
        strengths = []
        if (session.full_sentence_count or 0) / completed >= 0.8:
            strengths.append("Full sentence production")
        if (session.reason_success_count or 0) / completed >= 0.7:
            strengths.append("Reason-giving")
        if (session.independent_success_count or 0) / completed >= 0.7:
            strengths.append("Independent production")
        return strengths or ["Consistent participation"]

    def _derive_weaknesses(self, session: RampSessionModel) -> list[str]:
        completed = max(session.exercises_completed or 1, 1)
        weaknesses = []
        if (session.elaboration_success_count or 0) / completed < 0.5:
            weaknesses.append("Spontaneous elaboration")
        if (session.example_success_count or 0) / completed < 0.5:
            weaknesses.append("Giving concrete examples")
        if (session.followup_success_count or 0) / completed < 0.4 and session.stage >= 5:
            weaknesses.append("Handling follow-up questions")
        return weaknesses or ["Continue building fluency"]

    def _build_recommendation(self, session: RampSessionModel) -> str:
        if session.stage >= 9:
            return "Ready for Mode 5 — 60-second sustained monologue"
        if session.stage >= 7:
            return f"Next: 30–45s guided speaking (Stage {session.stage + 1})"
        return f"Next: {self.stage_engine.get_target_duration_sec(session.stage + 1)}s elaboration exercises"
