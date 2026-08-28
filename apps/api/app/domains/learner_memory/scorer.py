import math
from datetime import datetime, timezone

from app.domains.learner_memory.models import LearnerMemory


class MemoryScorer:
    """Centralized deterministic scoring algorithms for Confidence, Recency, Weakness Priority, and Strength Scores."""

    @classmethod
    def calculate_confidence(cls, evidence_count: int, unique_sessions_count: int) -> float:
        """
        Calculates confidence bounded strictly in [0.0, 1.0].
        Scales with evidence count and presence across distinct sessions.
        """
        if evidence_count <= 0:
            return 0.0

        # Base confidence: 0.35 for 1 item
        log_scale = 0.15 * math.log2(1 + evidence_count)
        session_bonus = 0.20 * (min(4, unique_sessions_count) / 4.0)

        raw = 0.35 + log_scale + session_bonus
        return min(1.0, max(0.1, round(raw, 3)))

    @classmethod
    def calculate_recency_factor(cls, last_seen: datetime) -> float:
        """
        Computes recency weight decaying smoothly with age.
        """
        now = datetime.now(timezone.utc)
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        days_ago = max(0.0, (now - last_seen).total_seconds() / 86400.0)

        if days_ago <= 3:
            return 1.0
        elif days_ago <= 14:
            return 0.90
        elif days_ago <= 30:
            return 0.75
        elif days_ago <= 90:
            return 0.55
        return 0.35

    @classmethod
    def calculate_weakness_priority(
        cls,
        memory: LearnerMemory,
        unique_sessions_count: int,
        total_user_sessions: int = 1,
    ) -> float:
        """
        Calculates deterministic weakness priority score bounded in [0.0, 1.0].
        """
        # 1. Severity weight
        sev = memory.severity.upper()
        if sev == "MUST_FIX":
            sev_weight = 1.0
        elif sev == "SHOULD_FIX":
            sev_weight = 0.70
        elif sev == "NATIVE_ALTERNATIVE":
            sev_weight = 0.40
        else:
            sev_weight = 0.30

        # 2. Recurrence rate across recent sessions
        safe_total = max(1, total_user_sessions)
        recurrence_rate = min(1.0, unique_sessions_count / min(safe_total, 10))

        # 3. Recency
        recency = cls.calculate_recency_factor(memory.last_seen)

        # 4. Mastery gap
        mastery_gap = max(0.0, 1.0 - memory.mastery)

        # 5. Regression booster
        regression_boost = 0.15 if memory.is_regression else 0.0

        # Weighted combination
        raw_score = (
            (sev_weight * 0.35)
            + (recurrence_rate * 0.25)
            + (recency * 0.20)
            + (mastery_gap * 0.20)
            + regression_boost
        ) * memory.confidence

        return min(1.0, max(0.05, round(raw_score, 3)))

    @classmethod
    def calculate_strength_score(
        cls,
        memory: LearnerMemory,
        unique_sessions_count: int,
        total_user_sessions: int = 1,
    ) -> float:
        """
        Calculates speaking strength score bounded in [0.0, 1.0].
        """
        safe_total = max(1, total_user_sessions)
        consistency = min(1.0, unique_sessions_count / min(safe_total, 10))
        recency = cls.calculate_recency_factor(memory.last_seen)
        mastery = max(0.5, memory.mastery)

        raw_score = (
            (consistency * 0.40)
            + (recency * 0.30)
            + (mastery * 0.30)
        ) * memory.confidence

        return min(1.0, max(0.05, round(raw_score, 3)))
