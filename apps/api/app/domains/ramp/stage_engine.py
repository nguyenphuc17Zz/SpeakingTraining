"""RampStageEngine — deterministic evidence-based progression logic.

§31 Adaptive Progression: requires comparable attempts before changing level.
§33 Automaticity: how quickly / independently / consistently.
§55 Support Fading: gradual, reversible.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import logger
from app.domains.ramp.contracts import (
    STAGE_MIN_ATTEMPTS_BEFORE_CHANGE,
    STAGE_TARGET_DURATION_SEC,
    RampSupportLevel,
)


class RampStageEngine:
    """Pure deterministic logic — no DB, no AI calls."""

    # Thresholds for stage transitions
    ADVANCE_SUCCESS_RATE = 0.75     # >= 75% in last N attempts → advance
    RETREAT_SUCCESS_RATE = 0.35     # <= 35% in last N attempts → retreat
    MIN_ATTEMPTS_WINDOW = STAGE_MIN_ATTEMPTS_BEFORE_CHANGE  # 5

    # Support-fading thresholds (§30)
    FADE_SUCCESS_RATE = 0.80        # >= 80% with independence → fade
    RESTORE_SUCCESS_RATE = 0.45     # <= 45% → restore one level

    # Duration ramp: each stage adds this many seconds before next stage
    DURATION_INCREMENT_SEC = 5

    def evaluate_stage_change(
        self,
        current_stage: int,
        stage_attempt_buffer: list[dict[str, Any]],
    ) -> tuple[int, str]:
        """
        Returns (new_stage, reason) after evaluating recent attempts.
        Only changes if enough comparable attempts have accumulated.
        Never jumps more than 1 stage in either direction. §31
        """
        if len(stage_attempt_buffer) < self.MIN_ATTEMPTS_WINDOW:
            return current_stage, "insufficient_data"

        recent = stage_attempt_buffer[-self.MIN_ATTEMPTS_WINDOW :]
        successes = sum(1 for a in recent if a.get("success"))
        rate = successes / len(recent)

        if rate >= self.ADVANCE_SUCCESS_RATE:
            new_stage = min(current_stage + 1, 10)
            reason = f"high_success_rate={rate:.2f}"
            logger.info(f"[RampStageEngine] Stage {current_stage} → {new_stage} ({reason})")
            return new_stage, reason

        if rate <= self.RETREAT_SUCCESS_RATE:
            new_stage = max(current_stage - 1, 0)
            reason = f"low_success_rate={rate:.2f}"
            logger.info(f"[RampStageEngine] Stage {current_stage} → {new_stage} ({reason})")
            return new_stage, reason

        return current_stage, f"stable_rate={rate:.2f}"

    def evaluate_support_change(
        self,
        current_support: int,
        stage_attempt_buffer: list[dict[str, Any]],
        current_stage: int,
    ) -> tuple[int, str]:
        """
        Returns (new_support_level, reason).
        Fades support on success, restores on failure. Never restores > 1 at a time.
        §30 §55 ScaffoldController decision boundary.
        """
        if len(stage_attempt_buffer) < 3:
            return current_support, "insufficient_data"

        recent = stage_attempt_buffer[-5:]
        independent_successes = sum(
            1 for a in recent
            if a.get("success") and a.get("independence_level") in ("independent", "assisted_hint")
        )
        rate = independent_successes / len(recent)

        if rate >= self.FADE_SUCCESS_RATE and current_support > RampSupportLevel.NONE.value:
            new_support = current_support - 1
            return new_support, f"fade_support rate={rate:.2f}"

        if rate <= self.RESTORE_SUCCESS_RATE and current_support < RampSupportLevel.TRANSLATION_REFERENCE.value:
            new_support = current_support + 1
            return new_support, f"restore_support rate={rate:.2f}"

        return current_support, f"stable rate={rate:.2f}"

    def get_target_duration_sec(self, stage: int) -> int:
        """Returns target speech duration for stage."""
        return STAGE_TARGET_DURATION_SEC.get(stage, 20)

    def get_elaboration_threshold(self, stage: int, measured_level: str) -> int:
        """
        Returns minimum word count for a 'complete enough' response.
        §21 — threshold varies by learner stage.
        """
        base_thresholds = {
            0: 3,   # echo: just needs to repeat
            1: 4,
            2: 6,
            3: 8,   # one sentence
            4: 12,  # two sentences
            5: 15,  # answer + reason
            6: 20,  # answer + reason + example
            7: 25,  # multi-idea
            8: 30,
            9: 40,
            10: 50,
        }
        base = base_thresholds.get(stage, 15)
        # Advanced learners get slightly higher threshold
        if measured_level in ("N1", "N2"):
            return int(base * 1.15)
        return base

    def build_stage_attempt_entry(
        self,
        success: bool,
        score: float,
        independence_level: str,
        speech_duration_ms: int | None,
        elaboration_ok: bool,
    ) -> dict[str, Any]:
        """Build a standardized attempt entry for the stage buffer."""
        return {
            "success": success,
            "score": score,
            "independence_level": independence_level,
            "speech_duration_ms": speech_duration_ms or 0,
            "elaboration_ok": elaboration_ok,
        }

    def get_session_structure(self, desired_minutes: int, current_stage: int) -> list[str]:
        """
        Returns the session exercise sequence. §40 Dynamic, not fixed.
        Returns exercise type names for the session.
        """
        structure_map: dict[tuple[int, int], list[str]] = {
            # (desired_minutes, stage_bucket) → exercise_types
            (5, 0): ["speak_echo", "speak_echo", "speak_substitute"],
            (10, 0): ["speak_echo", "speak_substitute", "speak_complete", "speak_one_sentence"],
            (15, 0): ["speak_echo", "speak_substitute", "speak_complete", "speak_one_sentence", "speak_expand"],
        }

        stage_bucket = min(current_stage // 3, 3)  # 0, 1, 2, 3+
        key = (min(desired_minutes, 15), stage_bucket)
        if key in structure_map:
            return structure_map[key]

        # Adaptive fallback: build from stage
        structure = []
        if current_stage <= 2:
            structure = ["speak_echo", "speak_substitute", "speak_complete", "speak_one_sentence"]
        elif current_stage <= 5:
            structure = ["speak_one_sentence", "speak_expand", "speak_reason", "speak_example"]
        elif current_stage <= 8:
            structure = ["speak_keyword", "speak_guided", "speak_spontaneous", "speak_followup"]
        else:
            structure = ["speak_guided", "speak_spontaneous", "speak_spontaneous", "speak_followup", "speak_followup"]

        # Scale to desired minutes
        rounds_per_15min = len(structure)
        extra_rounds = max(0, (desired_minutes - 15) // 5)
        structure += structure[-1:] * extra_rounds

        return structure
