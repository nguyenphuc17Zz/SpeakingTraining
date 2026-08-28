from app.domains.conversation_intelligence.contracts import (
    AnalysisConfidence,
    CorrectionItem,
    CorrectionSeverity,
)


class FeedbackPrioritizer:
    """Ranks and budgets linguistic feedback items to prevent cognitive overload."""

    SEVERITY_WEIGHTS = {
        CorrectionSeverity.MUST_FIX: 100,
        CorrectionSeverity.SHOULD_FIX: 70,
        CorrectionSeverity.NATIVE_ALTERNATIVE: 40,
        CorrectionSeverity.IGNORE: 10,
    }

    CONFIDENCE_WEIGHTS = {
        AnalysisConfidence.HIGH: 1.0,
        AnalysisConfidence.MEDIUM: 0.75,
        AnalysisConfidence.LOW: 0.4,
    }

    @classmethod
    def calculate_priority_score(cls, item: CorrectionItem) -> float:
        base_sev = cls.SEVERITY_WEIGHTS.get(item.severity, 30)
        conf_multiplier = cls.CONFIDENCE_WEIGHTS.get(item.confidence, 0.75)
        # Use internal severity score if present as subtle tiebreaker
        return (base_sev * 0.8 + item.severity_score * 0.2) * conf_multiplier

    @classmethod
    def prioritize(
        cls,
        corrections: list[CorrectionItem],
        max_budget: int = 3,
        mode: str = "coaching",
    ) -> list[CorrectionItem]:
        """Ranks corrections and selects top N items according to mode and budget."""
        # Filter out IGNORE items from immediate priority
        eligible = [c for c in corrections if c.severity != CorrectionSeverity.IGNORE]

        # Sort descending by priority score
        ranked = sorted(eligible, key=cls.calculate_priority_score, reverse=True)

        return ranked[:max_budget]
