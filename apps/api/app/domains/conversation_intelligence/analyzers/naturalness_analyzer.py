from app.domains.conversation_intelligence.contracts import (
    CorrectionCategory,
    CorrectionItem,
    CorrectionSeverity,
)


class NaturalnessAnalyzer:
    """Evaluates natural colloquial vs. rigid textbook speech in spoken Japanese."""

    # Patterns that are frequently valid informal speech (should not be marked as errors)
    VALID_INFORMAL_MARKERS = [
        "めっちゃ",
        "すごく",
        "やばい",
        "マジで",
        "〜じゃん",
        "〜だよね",
        "〜ね",
        "〜よ",
        "〜ちゃう",
        "〜てる",
    ]

    @staticmethod
    def evaluate_naturalness(
        corrections: list[CorrectionItem],
        persona_style: str = "casual",
    ) -> list[CorrectionItem]:
        """Ensures that valid informal expressions in friendly contexts are categorized as NATIVE_ALTERNATIVE or IGNORE."""
        processed = []
        is_casual_context = "casual" in persona_style.lower() or "friend" in persona_style.lower() or "tameguchi" in persona_style.lower()

        for item in corrections:
            # If user used a natural informal word in a casual context, ensure it is NOT marked MUST_FIX
            if is_casual_context and any(marker in item.original for marker in NaturalnessAnalyzer.VALID_INFORMAL_MARKERS):
                if item.severity in (CorrectionSeverity.MUST_FIX, CorrectionSeverity.SHOULD_FIX):
                    item.severity = CorrectionSeverity.NATIVE_ALTERNATIVE
                    item.category = CorrectionCategory.NATURALNESS

            processed.append(item)

        return processed
