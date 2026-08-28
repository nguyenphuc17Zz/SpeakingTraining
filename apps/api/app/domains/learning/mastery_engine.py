import math
from datetime import datetime, timezone
from typing import Any

from app.domains.learning.contracts import (
    ExerciseResult,
    IndependenceLevel,
    LearningItemLifecycle,
)
from app.domains.learning.models import LearningItem


class MasteryEngine:
    """Deterministic, pure-logic mathematical mastery engine for speaking-first multi-dimensional mastery tracking."""

    # Mastery threshold parameters
    MASTERY_THRESHOLD = 0.85
    MIN_ATTEMPTS_FOR_MASTERY = 5
    MIN_INDEPENDENT_RATE_FOR_MASTERY = 0.70
    MIN_CONTEXT_VARIETY_FOR_MASTERY = 2

    # Dimension weights for speaking-first philosophy
    WEIGHT_SPONTANEOUS = 0.45
    WEIGHT_PRODUCTION = 0.35
    WEIGHT_RECOGNITION = 0.10
    WEIGHT_CONTEXT_VARIETY = 0.10

    # Automaticity: separate dimension for retrieval speed under pressure (Mode 1)
    WEIGHT_AUTOMATICITY = 0.0  # not included in overall yet; tracked separately for analytics
    AUTOMATICITY_BASE_RATE = 0.08  # conservative vs 0.12 for spontaneous

    @classmethod
    def calculate_mastery_delta(
        cls,
        result: ExerciseResult,
        current_item: LearningItem,
        dimension: str = "spontaneous",
    ) -> float:
        """
        Calculates incremental mastery delta in [-0.25, +0.20].
        Incorporates saturation, independence weighting, confidence gating, and performance score.
        Supports 'automaticity' dimension for Reflex mode (conservative rate, speed-aware).
        """
        # Support automaticity as new dimension (fallback to overall if missing)
        if dimension == "automaticity":
            curr_mastery = getattr(current_item, "automaticity_mastery", current_item.overall_mastery)
        else:
            curr_mastery = getattr(current_item, f"{dimension}_mastery", current_item.overall_mastery)

        # 1. Independence multiplier
        if result.independence == IndependenceLevel.INDEPENDENT:
            indep_mult = 1.0
        elif result.independence == IndependenceLevel.ASSISTED_HINT:
            indep_mult = 0.60
        elif result.independence == IndependenceLevel.RETRY_SUCCESS:
            indep_mult = 0.40
        else:  # SCAFFOLDED
            indep_mult = 0.20

        # 2. Base performance signal [-1.0, 1.0] symmetric (forward fix 2026-08-26)
        # Score normalized around 70 as passing benchmark
        score_norm = (result.score - 70.0) / 30.0  # e.g. 100 -> +1.0, 70 -> 0.0, 40 -> -1.0
        score_norm = max(-1.0, min(1.0, score_norm))

        if not result.success:
            # ensure failure at least -0.4, but don't override strong positive if success=False due to AI inconsistency — validate
            if result.score >= 85 and not result.success:
                # suspicious AI inconsistency: keep score_norm as is, don't force -0.4
                pass
            else:
                score_norm = min(-0.4, score_norm)

        # 3. Saturation factor: delta shrinks as mastery reaches extremes
        # Automaticity uses more conservative base_rate (0.08) to prevent jumps like 0.42->1.0
        is_auto = dimension == "automaticity"
        # ensure curr_mastery is float
        if curr_mastery is None:
            curr_mastery = 0.5
        try:
            curr_mastery = float(curr_mastery)
        except Exception:
            curr_mastery = 0.5
        if score_norm >= 0:
            saturation = max(0.05, 1.0 - curr_mastery)
            base_rate = cls.AUTOMATICITY_BASE_RATE if is_auto else 0.12
            raw_delta = base_rate * score_norm * indep_mult * saturation
            # Automaticity bonus/penalty based on reaction speed if available
            if is_auto and result.response_speed_ms is not None:
                # Fast (<1500ms) adds +20% bonus, slow (>3000ms) dampens
                if result.response_speed_ms < 1500 and result.success:
                    raw_delta *= 1.2
                elif result.response_speed_ms > 3000:
                    raw_delta *= 0.7
        else:
            saturation = max(0.10, curr_mastery if curr_mastery is not None else 0.0)
            base_rate = cls.AUTOMATICITY_BASE_RATE if is_auto else 0.10
            raw_delta = base_rate * score_norm * saturation

        # 4. Confidence gating — handle None, clamp 0.2 floor
        conf = result.confidence if result.confidence is not None else 0.5
        try:
            conf = float(conf)
        except Exception:
            conf = 0.5
        confidence_factor = max(0.2, min(1.0, conf))
        final_delta = raw_delta * confidence_factor

        # Bound single step delta
        final_delta = max(-0.25, min(0.20, round(final_delta, 4)))
        return final_delta

    @classmethod
    def calculate_multidimensional_mastery(
        cls,
        recognition: float,
        production: float,
        spontaneous: float,
        context_variety_score: float,
    ) -> float:
        """
        Combines 4 dimensions into unified overall mastery [0.0, 1.0].
        Speaking-first weighted formula.
        """
        overall = (
            (spontaneous * cls.WEIGHT_SPONTANEOUS)
            + (production * cls.WEIGHT_PRODUCTION)
            + (recognition * cls.WEIGHT_RECOGNITION)
            + (context_variety_score * cls.WEIGHT_CONTEXT_VARIETY)
        )
        return max(0.0, min(1.0, round(overall, 3)))

    @classmethod
    def apply_decay(
        cls,
        current_mastery: float,
        days_since_practice: int,
        lifecycle: str = "active",
    ) -> float:
        """
        Applies smooth exponential forgetting decay based on inactivity days and lifecycle state.
        Maintenance and Mastered items decay significantly slower than freshly discovered items.
        """
        if days_since_practice <= 3:
            return current_mastery

        if lifecycle in ("mastered", "maintenance"):
            # Very slow decay: half-life ~ 180 days => rate = ln2/180
            decay_rate = 0.00385
        elif lifecycle in ("improving", "practicing"):
            # Moderate decay: half-life ~ 60 days => ln2/60
            decay_rate = 0.01155
        else:
            # Active/discovered: half-life ~ 30 days => ln2/30
            decay_rate = 0.0231

        effective_days = days_since_practice - 3
        decayed = current_mastery * math.exp(-decay_rate * effective_days)
        return max(0.0, min(1.0, round(decayed, 3)))

    @classmethod
    def evaluate_lifecycle_transition(
        cls,
        current_lifecycle: str,
        overall_mastery: float,
        spontaneous_mastery: float,
        attempt_count: int,
        independent_success_count: int,
        context_variety_count: int,
        recent_has_failure: bool = False,
    ) -> str:
        """
        Deterministic lifecycle state machine transitions:
        discovered -> active -> practicing -> improving -> mastered -> maintenance (or regressed).
        """
        curr = current_lifecycle.lower()
        indep_rate = independent_success_count / max(1, attempt_count)

        # Regression detection for mastered/maintenance
        if curr in ("mastered", "maintenance") and recent_has_failure and spontaneous_mastery < 0.65:
            return LearningItemLifecycle.REGRESSED.value

        # From regressed back to active/practicing
        if curr == "regressed":
            if overall_mastery >= 0.70:
                return LearningItemLifecycle.IMPROVING.value
            return LearningItemLifecycle.PRACTICING.value

        # Mastery criteria: overall mastery high AND spontaneous high AND independent success high AND context variety
        if (
            overall_mastery >= cls.MASTERY_THRESHOLD
            and spontaneous_mastery >= 0.75
            and attempt_count >= cls.MIN_ATTEMPTS_FOR_MASTERY
            and indep_rate >= cls.MIN_INDEPENDENT_RATE_FOR_MASTERY
            and context_variety_count >= cls.MIN_CONTEXT_VARIETY_FOR_MASTERY
        ):
            if curr == "mastered":
                return LearningItemLifecycle.MAINTENANCE.value
            return LearningItemLifecycle.MASTERED.value

        if overall_mastery >= 0.60 or (attempt_count >= 3 and indep_rate >= 0.5):
            return LearningItemLifecycle.IMPROVING.value

        if attempt_count >= 1:
            return LearningItemLifecycle.PRACTICING.value

        if curr == "discovered":
            return LearningItemLifecycle.ACTIVE.value

        return curr
