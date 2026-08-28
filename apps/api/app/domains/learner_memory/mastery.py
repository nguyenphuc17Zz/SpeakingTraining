from datetime import datetime
from app.domains.learner_memory.models import LearnerMemory
from app.domains.learner_memory.scorer import MemoryScorer


class MasteryEstimator:
    """Estimates linguistic pattern mastery [0.0, 1.0] based on accuracy, context variety, and recency."""

    @classmethod
    def estimate_mastery(
        cls,
        memory: LearnerMemory,
    ) -> float:
        """Calculates mastery score bounded in [0.0, 1.0]."""
        # Strengths start high
        if memory.memory_type == "strength":
            recency = MemoryScorer.calculate_recency_factor(memory.last_seen)
            return min(1.0, round(0.85 * recency, 2))

        # Goals / preferences don't have linguistic mastery
        if memory.memory_type in ("goal", "preference"):
            return 1.0

        total_attempts = memory.attempt_count
        if total_attempts <= 0:
            return 0.0

        # Base correct ratio
        correct_ratio = memory.correct_count / float(total_attempts)

        # Context variety bonus (up to +0.20 for 4+ contexts)
        contexts = memory.contexts_used or []
        context_bonus = min(0.20, len(contexts) * 0.05)

        # Recency decay
        recency = MemoryScorer.calculate_recency_factor(memory.last_seen)

        # Attempt volume dampener (low attempts can't have 1.0 mastery immediately)
        volume_factor = min(1.0, total_attempts / 5.0)

        raw_mastery = ((correct_ratio * 0.80) + context_bonus) * recency * volume_factor
        return min(1.0, max(0.0, round(raw_mastery, 2)))
