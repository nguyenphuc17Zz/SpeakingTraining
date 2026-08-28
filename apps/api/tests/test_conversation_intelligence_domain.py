import pytest
from app.domains.conversation_intelligence.analyzers.context_analyzer import ContextAnalyzer
from app.domains.conversation_intelligence.analyzers.correction_analyzer import CorrectionAnalyzer
from app.domains.conversation_intelligence.analyzers.feedback_prioritizer import FeedbackPrioritizer
from app.domains.conversation_intelligence.analyzers.grammar_analyzer import GrammarAnalyzer
from app.domains.conversation_intelligence.analyzers.naturalness_analyzer import NaturalnessAnalyzer
from app.domains.conversation_intelligence.analyzers.orchestrator import AnalysisOrchestrator
from app.domains.conversation_intelligence.analyzers.session_analyzer import SessionAnalyzer
from app.domains.conversation_intelligence.analyzers.vocabulary_analyzer import VocabularyAnalyzer
from app.domains.conversation_intelligence.contracts import (
    AnalysisConfidence,
    AnalysisPolicyConfig,
    ConversationAnalysisInput,
    CorrectionCategory,
    CorrectionItem,
    CorrectionSeverity,
    GrammarPointNote,
    SessionAnalysisResult,
    VocabularyNote,
)
from app.domains.conversation_intelligence.queue import AnalysisJobQueue


@pytest.mark.asyncio
async def test_short_utterance_cost_aware_bypass(db_session):
    orchestrator = AnalysisOrchestrator(db_session)
    input_data = ConversationAnalysisInput(
        session_id="test-session-1",
        current_turn_id="turn-1",
        current_user_transcript="なるほど",
        conversation_mode="conversation",
    )
    result = await orchestrator.analyze_turn(input_data)
    assert result.overall_quality_score == 95
    assert len(result.corrections) == 0
    assert len(result.strengths) >= 1


def test_correction_analyzer_guardrails():
    # Test Rule 1: Suspicious transcript demotes MUST_FIX
    item = CorrectionItem(
        category=CorrectionCategory.GRAMMAR,
        severity=CorrectionSeverity.MUST_FIX,
        original="見たです",
        corrected="見ました",
        explanation="Test explanation",
        confidence=AnalysisConfidence.HIGH,
    )
    sanitized = CorrectionAnalyzer.sanitize_correction(item, is_suspicious_transcript=True)
    assert sanitized.confidence == AnalysisConfidence.LOW
    assert sanitized.severity == CorrectionSeverity.SHOULD_FIX

    # Test Rule 2: Low confidence never allows MUST_FIX
    item2 = CorrectionItem(
        category=CorrectionCategory.GRAMMAR,
        severity=CorrectionSeverity.MUST_FIX,
        original="食べた",
        corrected="食べました",
        explanation="Test",
        confidence=AnalysisConfidence.LOW,
    )
    sanitized2 = CorrectionAnalyzer.sanitize_correction(item2, is_suspicious_transcript=False)
    assert sanitized2.severity == CorrectionSeverity.SHOULD_FIX


def test_naturalness_analyzer_casual_expression():
    # Expression with natural casual word (めっちゃ) in friendly context should not be MUST_FIX
    item = CorrectionItem(
        category=CorrectionCategory.WORD_CHOICE,
        severity=CorrectionSeverity.MUST_FIX,
        original="めっちゃ楽しかった",
        corrected="とても楽しかったです",
        explanation="Formal version",
        confidence=AnalysisConfidence.HIGH,
    )
    evaluated = NaturalnessAnalyzer.evaluate_naturalness([item], persona_style="Casual Friend")
    assert evaluated[0].severity == CorrectionSeverity.NATIVE_ALTERNATIVE
    assert evaluated[0].category == CorrectionCategory.NATURALNESS


def test_context_analyzer_formality():
    notes, _ = ContextAnalyzer.evaluate_context_appropriateness(
        persona_role="Interviewer (Tanaka-san)",
        user_transcript="どうも",
        corrections=[],
    )
    assert len(notes) >= 1
    assert notes[0].formality_level == "too_casual"


def test_feedback_prioritizer_budget():
    items = [
        CorrectionItem(
            category=CorrectionCategory.WORD_CHOICE,
            severity=CorrectionSeverity.IGNORE,
            original="A",
            corrected="A1",
            explanation="Ignore item",
            confidence=AnalysisConfidence.LOW,
        ),
        CorrectionItem(
            category=CorrectionCategory.GRAMMAR,
            severity=CorrectionSeverity.MUST_FIX,
            original="見たです",
            corrected="見ました",
            explanation="Must fix grammar",
            confidence=AnalysisConfidence.HIGH,
        ),
        CorrectionItem(
            category=CorrectionCategory.POLITENESS,
            severity=CorrectionSeverity.SHOULD_FIX,
            original="うん",
            corrected="はい",
            explanation="Should fix politeness",
            confidence=AnalysisConfidence.MEDIUM,
        ),
        CorrectionItem(
            category=CorrectionCategory.NATURALNESS,
            severity=CorrectionSeverity.NATIVE_ALTERNATIVE,
            original="知っています",
            corrected="知ってるよ",
            explanation="Native alt",
            confidence=AnalysisConfidence.HIGH,
        ),
    ]

    prioritized = FeedbackPrioritizer.prioritize(items, max_budget=2)
    assert len(prioritized) == 2
    assert prioritized[0].severity == CorrectionSeverity.MUST_FIX
    assert prioritized[1].severity == CorrectionSeverity.SHOULD_FIX


def test_session_analyzer_repeated_patterns_and_strengths():
    turns = [
        {"speaker": "user", "transcript": "日本語が難しいと思います"},
        {"speaker": "user", "transcript": "明日も雨だと思います"},
        {"speaker": "user", "transcript": "映画は面白いと思います"},
    ]
    corrections = [
        {"original": "は", "corrected": "が", "severity": "MUST_FIX", "category": "particle"},
        {"original": "は", "corrected": "が", "severity": "MUST_FIX", "category": "particle"},
    ]

    repeated = SessionAnalyzer.detect_repeated_patterns(turns, corrections)
    assert any("と思います" in r["pattern"] for r in repeated)
    assert any("は" in r["pattern"] for r in repeated)

    empty_result = SessionAnalysisResult(
        session_id="test-session",
        overall_score=80,
        strengths=[],
    )
    guaranteed = SessionAnalyzer.ensure_strengths(empty_result, user_turns_count=3)
    assert len(guaranteed.strengths) >= 2


@pytest.mark.asyncio
async def test_job_queue_memory_fallback():
    queue = AnalysisJobQueue()
    job_payload = {"job_id": "test-job-99", "type": "turn_analysis"}
    await queue.enqueue(job_payload)
    dequeued = await queue.dequeue(timeout_seconds=0.5)
    assert dequeued is not None
    assert dequeued["job_id"] == "test-job-99"
