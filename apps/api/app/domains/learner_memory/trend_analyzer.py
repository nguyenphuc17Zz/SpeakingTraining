from app.domains.learner_memory.contracts import MemoryTrend
from app.domains.learner_memory.models import LearnerMemory, MemoryEvidence


class TrendAnalyzer:
    """Deterministic, code-driven trend analyzer for detecting improvement, regression, stability, or resolution."""

    @classmethod
    def analyze_trend(
        cls,
        memory: LearnerMemory,
        evidences: list[MemoryEvidence],
    ) -> tuple[MemoryTrend, str]:
        """
        Analyzes chronological evidence and returns (MemoryTrend, new_lifecycle_status).
        """
        if not evidences or len(evidences) <= 2:
            return MemoryTrend.NEW, "new"

        from datetime import timezone
        # Chronological sort (oldest to newest)
        sorted_ev = sorted(
            evidences,
            key=lambda e: (e.created_at if e.created_at.tzinfo else e.created_at.replace(tzinfo=timezone.utc), str(e.id))
        )

        # Check total attempts and recent performance
        total_ev = len(sorted_ev)
        recent_window_size = max(2, total_ev // 2)
        old_window = sorted_ev[:-recent_window_size]
        recent_window = sorted_ev[-recent_window_size:]

        # Count errors in windows
        old_errors = sum(1 for e in old_window if e.evidence_type in ("error_observation", "session_repeated_pattern"))
        old_total = len(old_window)
        old_error_rate = (old_errors / old_total) if old_total > 0 else 1.0

        recent_errors = sum(1 for e in recent_window if e.evidence_type in ("error_observation", "session_repeated_pattern"))
        recent_total = len(recent_window)
        recent_error_rate = (recent_errors / recent_total) if recent_total > 0 else 0.0

        delta = recent_error_rate - old_error_rate

        # 1. Resolution Check: High attempts + zero recent errors + strong mastery (>= 5 correct)
        if total_ev >= 6 and recent_errors == 0 and memory.correct_count >= 5:
            return MemoryTrend.RESOLVED, "resolved"

        # 2. Regression Check: Was resolved, but recent evidence has an error
        if memory.is_regression or (memory.status == "resolved" and recent_errors > 0):
            return MemoryTrend.WORSENING, "active"

        # 3. Improvement Check: Significant reduction in error rate or recent streak of correct attempts
        recent_correct_streak = all(e.evidence_type in ("correct_observation", "strength", "turn_strength", "session_strength") for e in recent_window[-2:])
        if delta <= -0.15 or (recent_errors == 0 and memory.correct_count >= 2) or recent_correct_streak:
            return MemoryTrend.IMPROVING, "improving"

        # 4. Worsening Check
        if delta >= 0.25:
            return MemoryTrend.WORSENING, "active"

        # 5. Stable default
        return MemoryTrend.STABLE, "active"
