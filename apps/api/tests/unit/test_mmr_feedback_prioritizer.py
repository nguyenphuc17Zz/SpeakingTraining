import pytest

from app.domains.conversation_intelligence.analyzers.feedback_prioritizer import FeedbackPrioritizer
from app.domains.conversation_intelligence.contracts import (
    AnalysisConfidence,
    CorrectionCategory,
    CorrectionItem,
    CorrectionSeverity,
)


def test_mmr_prevents_repetitive_particle_overload():
    """Verify MMR suppresses redundant duplicates of the same category/token and promotes diverse high-impact errors."""
    # 3 duplicate particle errors with slight variations
    p1 = CorrectionItem(
        category=CorrectionCategory.PARTICLE,
        severity=CorrectionSeverity.MUST_FIX,
        original="私は",
        corrected="私が",
        explanation="Trợ từ は vs が",
        severity_score=95,
        confidence=AnalysisConfidence.HIGH,
    )
    p2 = CorrectionItem(
        category=CorrectionCategory.PARTICLE,
        severity=CorrectionSeverity.MUST_FIX,
        original="猫は",
        corrected="猫が",
        explanation="Trợ từ は vs が",
        severity_score=92,
        confidence=AnalysisConfidence.HIGH,
    )
    p3 = CorrectionItem(
        category=CorrectionCategory.PARTICLE,
        severity=CorrectionSeverity.MUST_FIX,
        original="犬は",
        corrected="犬が",
        explanation="Trợ từ は vs が",
        severity_score=90,
        confidence=AnalysisConfidence.HIGH,
    )

    # 1 critical verb conjugation error
    v1 = CorrectionItem(
        category=CorrectionCategory.GRAMMAR,
        severity=CorrectionSeverity.SHOULD_FIX,
        original="食べれる",
        corrected="食べられる",
        explanation="Lược bỏ ら (ら抜き言葉)",
        severity_score=78,
        confidence=AnalysisConfidence.HIGH,
    )

    # 1 vocabulary nuance error
    voc1 = CorrectionItem(
        category=CorrectionCategory.WORD_CHOICE,
        severity=CorrectionSeverity.SHOULD_FIX,
        original="風邪を受ける",
        corrected="風邪をひく",
        explanation="Collocation tự nhiên của người Nhật",
        severity_score=75,
        confidence=AnalysisConfidence.HIGH,
    )

    items = [p1, p2, p3, v1, voc1]

    # With MMR and max_budget = 3, learner should NOT receive 3 identical particle warnings
    selected = FeedbackPrioritizer.prioritize(items, max_budget=3, mode="coaching")
    assert len(selected) == 3

    categories = [c.category for c in selected]
    # At least 2 different categories must be represented
    assert len(set(categories)) >= 2
    # The verb conjugation error should be promoted into the top 3
    assert any(c.category == CorrectionCategory.GRAMMAR for c in selected)


def test_mmr_picks_all_when_within_budget():
    """Verify full list returned when candidate count <= max_budget."""
    items = [
        CorrectionItem(
            category=CorrectionCategory.POLITENESS,
            severity=CorrectionSeverity.MUST_FIX,
            original="だ",
            corrected="です",
            explanation="Politeness",
        ),
        CorrectionItem(
            category=CorrectionCategory.NATURALNESS,
            severity=CorrectionSeverity.SHOULD_FIX,
            original="とても",
            corrected="すごく",
            explanation="Naturalness",
        ),
    ]

    selected = FeedbackPrioritizer.prioritize(items, max_budget=4)
    assert len(selected) == 2
    assert selected[0].severity == CorrectionSeverity.MUST_FIX
