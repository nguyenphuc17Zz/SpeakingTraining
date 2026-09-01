"""RampProgressionEngine — updates stage, support, mastery after each attempt.

§31 Adaptive Progression, §32 Independence Score, §56 Progress Model,
§57 Milestones, §62 Mastery Integration, §63 Gamification.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.contracts import ExerciseResult, IndependenceLevel
from app.domains.learning.mastery_engine import MasteryEngine
from app.domains.ramp.contracts import (
    RampAttemptFeedback,
    RampProgressSnapshot,
    RampScore,
)
from app.domains.ramp.models import RampSessionModel
from app.domains.ramp.stage_engine import RampStageEngine


# ---------------------------------------------------------------------------
# Derived skill keys tracked in MasteryEngine (§62)
# ---------------------------------------------------------------------------
RAMP_SKILL_KEYS = [
    "spontaneous_production",
    "sentence_expansion",
    "elaboration",
    "independent_speaking",
    "speaking_endurance",
    "followup_handling",
]

# ---------------------------------------------------------------------------
# Milestone thresholds (§57) — configurable via data, not hard-coded targets
# ---------------------------------------------------------------------------
MILESTONES: list[dict[str, Any]] = [
    {"id": "10_sentences", "label": "10 independent sentences", "metric": "independent_success_count", "threshold": 10},
    {"id": "20s_speech", "label": "20-second independent speech", "metric": "max_speech_duration_ms", "threshold": 20000},
    {"id": "reason_success", "label": "Reason-giving mastered", "metric": "reason_success_count", "threshold": 5},
    {"id": "example_success", "label": "Example-giving mastered", "metric": "example_success_count", "threshold": 5},
    {"id": "3_followups", "label": "3 follow-ups handled", "metric": "followup_success_count", "threshold": 3},
    {"id": "30s_speech", "label": "30-second spontaneous response", "metric": "max_speech_duration_ms", "threshold": 30000},
    {"id": "60s_speech", "label": "60-second independent speech", "metric": "max_speech_duration_ms", "threshold": 60000},
    {"id": "elaboration_5", "label": "Elaboration success 5 times", "metric": "elaboration_success_count", "threshold": 5},
]


class RampProgressionEngine:
    """
    Reads attempt result → updates session model → computes stage/support changes
    → triggers mastery updates + gamification events.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stage_engine = RampStageEngine()
        self.mastery_engine = MasteryEngine()

    async def process_attempt(
        self,
        session: RampSessionModel,
        score: RampScore,
        feedback: RampAttemptFeedback,
        task_spec_dict: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update session after an attempt. Returns delta dict.
        """
        stage = session.stage
        success = score.overall >= 60.0
        is_independent = score.independence_level in ("independent", "assisted_hint")

        # Build stage attempt entry
        entry = self.stage_engine.build_stage_attempt_entry(
            success=success,
            score=score.overall,
            independence_level=score.independence_level,
            speech_duration_ms=score.speech_duration_ms,
            elaboration_ok=not feedback.too_short and not feedback.missing_reason,
        )

        # Update buffer
        buffer = list(session.stage_attempt_buffer or [])
        buffer.append(entry)
        session.stage_attempt_buffer = buffer[-20:]  # keep last 20

        # Update counters
        session.exercises_completed = (session.exercises_completed or 0) + 1
        if is_independent and success:
            session.independent_success_count = (session.independent_success_count or 0) + 1
        if feedback.meaning_clear and not feedback.incomplete_sentence:
            session.full_sentence_count = (session.full_sentence_count or 0) + 1
        if not feedback.too_short and not feedback.missing_reason:
            session.elaboration_success_count = (session.elaboration_success_count or 0) + 1
        if not feedback.missing_reason:
            session.reason_success_count = (session.reason_success_count or 0) + 1
        if not feedback.missing_example:
            session.example_success_count = (session.example_success_count or 0) + 1
        ex_type = task_spec_dict.get("exercise_type", "")
        if "followup" in ex_type and success:
            session.followup_success_count = (session.followup_success_count or 0) + 1
        if score.speech_duration_ms:
            session.total_speech_duration_ms = (session.total_speech_duration_ms or 0) + score.speech_duration_ms
            session.max_speech_duration_ms = max(
                session.max_speech_duration_ms or 0, score.speech_duration_ms
            )

        # Evaluate stage change
        new_stage, stage_reason = self.stage_engine.evaluate_stage_change(
            current_stage=stage,
            stage_attempt_buffer=session.stage_attempt_buffer,
        )
        stage_changed = new_stage != stage
        if stage_changed:
            session.stage = new_stage
            session.stage_attempt_buffer = []  # reset buffer after stage change

        # Evaluate support change
        new_support, support_reason = self.stage_engine.evaluate_support_change(
            current_support=session.support_level,
            stage_attempt_buffer=buffer,
            current_stage=session.stage,
        )
        support_changed = new_support != session.support_level
        session.support_level = new_support

        # Check milestones
        new_milestones = self._check_milestones(session)

        # Gamification events
        events = self._build_gamification_events(
            score=score,
            stage_changed=stage_changed,
            new_stage=new_stage,
            support_changed=support_changed,
            milestones=new_milestones,
            session=session,
        )

        return {
            "stage_changed": stage_changed,
            "new_stage": new_stage,
            "stage_reason": stage_reason,
            "support_changed": support_changed,
            "new_support": new_support,
            "support_reason": support_reason,
            "new_milestones": new_milestones,
            "gamification_events": events,
            "success": success,
        }

    def _check_milestones(self, session: RampSessionModel) -> list[str]:
        """§57 Check which new milestones have been reached."""
        achieved = set(session.milestones_achieved or [])
        new_ones = []
        for m in MILESTONES:
            if m["id"] in achieved:
                continue
            val = getattr(session, m["metric"], 0) or 0
            if val >= m["threshold"]:
                achieved.add(m["id"])
                new_ones.append(m["label"])
        session.milestones_achieved = list(achieved)
        return new_ones

    def _build_gamification_events(
        self,
        score: RampScore,
        stage_changed: bool,
        new_stage: int,
        support_changed: bool,
        milestones: list[str],
        session: RampSessionModel,
    ) -> list[dict[str, Any]]:
        """§63 Gamification events."""
        events: list[dict[str, Any]] = []

        events.append({
            "event": "ramp.exercise_completed",
            "score": score.overall,
            "independence": score.independence_level,
        })

        if stage_changed:
            events.append({
                "event": "ramp.stage_up" if new_stage > (session.stage - 1) else "ramp.stage_stable",
                "new_stage": new_stage,
            })

        for milestone in milestones:
            events.append({"event": "ramp.independent_milestone", "milestone": milestone})

        if score.speech_duration_ms and score.speech_duration_ms > (session.max_speech_duration_ms or 0):
            events.append({
                "event": "ramp.duration_record",
                "duration_ms": score.speech_duration_ms,
            })

        return events

    def build_progress_snapshot(
        self,
        session: RampSessionModel,
        user_id: str,
    ) -> RampProgressSnapshot:
        """§56 Build current progress snapshot from session counters."""
        completed = max(session.exercises_completed or 1, 1)

        return RampProgressSnapshot(
            user_id=user_id,
            current_stage=session.stage,
            current_support_level=session.support_level,
            max_independent_duration_ms=session.max_speech_duration_ms or 0,
            avg_independent_duration_ms=(
                (session.total_speech_duration_ms or 0) / completed
            ),
            sentence_completeness_rate=(session.full_sentence_count or 0) / completed,
            elaboration_success_rate=(session.elaboration_success_count or 0) / completed,
            reason_success_rate=(session.reason_success_count or 0) / completed,
            example_success_rate=(session.example_success_count or 0) / completed,
            followup_success_rate=(session.followup_success_count or 0) / completed,
            independent_success_rate=(session.independent_success_count or 0) / completed,
            total_attempts=completed,
        )
