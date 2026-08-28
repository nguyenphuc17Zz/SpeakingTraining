from app.domains.conversation_intelligence.contracts import (
    AnalysisConfidence,
    CorrectionCategory,
    CorrectionItem,
    CorrectionSeverity,
)


class CorrectionAnalyzer:
    """Evaluates and validates correctness of grammatical units, particles, and conjugations."""

    @staticmethod
    def sanitize_correction(
        item: CorrectionItem,
        is_suspicious_transcript: bool = False,
    ) -> CorrectionItem:
        """Applies pedagogical rules to prevent false-positives and over-corrections."""
        # Rule 1: If Whisper transcript was suspicious, lower confidence and demote MUST_FIX to SHOULD_FIX or IGNORE
        if is_suspicious_transcript:
            item.confidence = AnalysisConfidence.LOW
            if item.severity == CorrectionSeverity.MUST_FIX:
                item.severity = CorrectionSeverity.SHOULD_FIX

        # Rule 2: If confidence is LOW, never allow MUST_FIX
        if item.confidence == AnalysisConfidence.LOW and item.severity == CorrectionSeverity.MUST_FIX:
            item.severity = CorrectionSeverity.SHOULD_FIX

        # Rule 3: Native alternatives must never have MUST_FIX or SHOULD_FIX severity
        if item.category == CorrectionCategory.NATURALNESS:
            if item.severity in (CorrectionSeverity.MUST_FIX, CorrectionSeverity.SHOULD_FIX):
                item.severity = CorrectionSeverity.NATIVE_ALTERNATIVE

        # Rule 4: Particle corrections default to PARTICLE category if classified generally
        if item.original in ("は", "が", "を", "に", "で", "へ", "と", "から", "まで"):
            item.category = CorrectionCategory.PARTICLE

        return item
