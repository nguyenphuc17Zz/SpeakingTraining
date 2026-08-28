import pytest
from datetime import datetime, timedelta, timezone

from app.domains.conversation_intelligence.contracts import CorrectionCategory, CorrectionSeverity
from app.domains.conversation_intelligence.models import (
    AnalysisCorrection,
    GrammarNote,
    SessionAnalysis,
    TurnAnalysis,
)
from app.domains.learner_memory.contracts import MemoryTrend, MemoryType
from app.domains.learner_memory.extractor import MemoryExtractor
from app.domains.learner_memory.key_resolver import MemoryKeyResolver
from app.domains.learner_memory.level_assessor import LevelAssessor
from app.domains.learner_memory.mastery import MasteryEstimator
from app.domains.learner_memory.merger import MemoryMerger
from app.domains.learner_memory.models import LearnerMemory, MemoryEvidence
from app.domains.learner_memory.scorer import MemoryScorer
from app.domains.learner_memory.trend_analyzer import TrendAnalyzer


def test_memory_key_resolver():
    # 1. Particles
    m_type, key, stmt = MemoryKeyResolver.resolve_key("particle", "は vs が", "私は猫が好き")
    assert m_type == MemoryType.PARTICLE
    assert key == "particle.ha_vs_ga"

    # 2. Grammar Point
    m_type, key, stmt = MemoryKeyResolver.resolve_key("grammar", "〜わけではない", "行くわけではない")
    assert m_type == MemoryType.GRAMMAR
    assert key == "grammar.wake_de_wa_nai"

    # 3. Filler
    m_type, key, stmt = MemoryKeyResolver.resolve_key("filler", "なんか", "なんかさ")
    assert m_type == MemoryType.FILLER
    assert key == "filler.excessive_nanka"

    # 4. Politeness
    m_type, key, stmt = MemoryKeyResolver.resolve_key("politeness", "keigo_avoidance")
    assert m_type == MemoryType.POLITENESS
    assert key == "politeness.keigo_avoidance"


def test_extractor_turn_and_session_analysis():
    # Turn Analysis
    corr1 = AnalysisCorrection(
        id="corr-1",
        category="particle",
        severity="MUST_FIX",
        severity_score=80,
        original="猫は好き",
        corrected="猫が好き",
        explanation="Dùng trợ từ が với tính từ 好き",
        confidence="high",
    )
    corr_ignore = AnalysisCorrection(
        id="corr-2",
        category="grammar",
        severity="IGNORE",
        original="テスト",
        corrected="テスト",
        explanation="Bỏ qua",
    )

    turn_analysis = TurnAnalysis(
        id="ta-1",
        turn_id="turn-1",
        session_id="sess-1",
        is_suspicious_transcript=False,
        strengths=["Phản xạ câu hỏi rất nhanh và tự nhiên"],
    )
    turn_analysis.corrections = [corr1, corr_ignore]
    turn_analysis.grammar_notes = [
        GrammarNote(
            id="gn-1",
            grammar_pattern="〜てしまう",
            user_usage="食べてしまった",
            correct_usage="食べてしまった",
            short_explanation="Sử dụng đúng cấu trúc lỡ/hoàn thành",
        )
    ]

    candidates = MemoryExtractor.extract_from_turn_analysis(turn_analysis, context_tag="casual")
    assert len(candidates) >= 2
    # corr_ignore should NOT be extracted
    assert not any(c.correction_id == "corr-2" for c in candidates)
    # corr1 must be extracted with MUST_FIX weight 1.0
    c1 = next(c for c in candidates if c.correction_id == "corr-1")
    assert c1.evidence_weight == 1.0
    assert c1.memory_type == MemoryType.PARTICLE


def test_memory_scorer_confidence_and_priority():
    # Confidence bounds
    conf1 = MemoryScorer.calculate_confidence(evidence_count=1, unique_sessions_count=1)
    assert 0.0 <= conf1 <= 1.0
    assert conf1 >= 0.35

    conf_high = MemoryScorer.calculate_confidence(evidence_count=20, unique_sessions_count=8)
    assert 0.8 <= conf_high <= 1.0

    # Weakness priority
    mem = LearnerMemory(
        id="mem-1",
        user_id="u-1",
        memory_type="particle",
        key="particle.ha_vs_ga",
        statement="は vs が",
        severity="MUST_FIX",
        confidence=0.85,
        mastery=0.3,
        last_seen=datetime.now(timezone.utc),
        is_regression=False,
    )
    priority = MemoryScorer.calculate_weakness_priority(mem, unique_sessions_count=4, total_user_sessions=5)
    assert 0.0 <= priority <= 1.0
    assert priority > 0.45


def test_trend_analyzer_transitions():
    now = datetime.now(timezone.utc)
    mem = LearnerMemory(
        id="mem-1",
        user_id="u-1",
        memory_type="grammar",
        key="grammar.te_shimau",
        statement="〜てしまう",
        correct_count=6,
        error_count=2,
        status="active",
        is_regression=False,
    )

    # 1. New trend (<= 2 evidences)
    evs_new = [
        MemoryEvidence(id="e1", memory_id="mem-1", user_id="u-1", session_id="s1", evidence_type="error_observation", created_at=now - timedelta(days=2)),
        MemoryEvidence(id="e2", memory_id="mem-1", user_id="u-1", session_id="s2", evidence_type="error_observation", created_at=now - timedelta(days=1)),
    ]
    trend, status = TrendAnalyzer.analyze_trend(mem, evs_new)
    assert trend == MemoryTrend.NEW

    # 2. Improving trend (old errors -> recent correct)
    evs_improving = [
        MemoryEvidence(id="e1", memory_id="mem-1", user_id="u-1", session_id="s1", evidence_type="error_observation", created_at=now - timedelta(days=10)),
        MemoryEvidence(id="e2", memory_id="mem-1", user_id="u-1", session_id="s2", evidence_type="error_observation", created_at=now - timedelta(days=8)),
        MemoryEvidence(id="e3", memory_id="mem-1", user_id="u-1", session_id="s3", evidence_type="correct_observation", created_at=now - timedelta(days=4)),
        MemoryEvidence(id="e4", memory_id="mem-1", user_id="u-1", session_id="s4", evidence_type="correct_observation", created_at=now - timedelta(days=1)),
    ]
    trend_imp, status_imp = TrendAnalyzer.analyze_trend(mem, evs_improving)
    assert trend_imp == MemoryTrend.IMPROVING

    # 3. Resolved trend (many attempts, recent zero errors, >= 5 correct)
    evs_resolved = [
        MemoryEvidence(id=f"e_{i}", memory_id="mem-1", user_id="u-1", session_id=f"s_{i}", evidence_type="correct_observation", created_at=now - timedelta(days=10 - i))
        for i in range(7)
    ]
    trend_res, status_res = TrendAnalyzer.analyze_trend(mem, evs_resolved)
    assert trend_res == MemoryTrend.RESOLVED
    assert status_res == "resolved"


def test_mastery_estimation_with_context_variety():
    now = datetime.now(timezone.utc)
    mem_single_context = LearnerMemory(
        id="mem-1",
        user_id="u-1",
        memory_type="grammar",
        key="grammar.sou_da",
        statement="〜そうだ",
        attempt_count=10,
        correct_count=9,
        last_seen=now,
        contexts_used=["casual"],
    )
    mastery_single = MasteryEstimator.estimate_mastery(mem_single_context)

    mem_multi_context = LearnerMemory(
        id="mem-2",
        user_id="u-1",
        memory_type="grammar",
        key="grammar.sou_da",
        statement="〜そうだ",
        attempt_count=10,
        correct_count=9,
        last_seen=now,
        contexts_used=["casual", "workplace", "travel", "interview"],
    )
    mastery_multi = MasteryEstimator.estimate_mastery(mem_multi_context)

    assert 0.0 <= mastery_single <= 1.0
    assert 0.0 <= mastery_multi <= 1.0
    # Multi-context variety must earn a higher mastery bonus!
    assert mastery_multi > mastery_single


def test_level_assessor_insufficient_evidence():
    # Less than 3 sessions -> Insufficient evidence
    lvl = LevelAssessor.assess_levels(
        total_sessions=1,
        total_turns=4,
        avg_session_score=80.0,
        must_fix_rate=0.2,
        total_corrections_rate=0.5,
    )
    assert lvl["level_confidence"] == "insufficient_evidence"
    assert lvl["confidence_score"] <= 0.40

    # Many sessions with low errors -> Intermediate / Upper Intermediate
    lvl_prof = LevelAssessor.assess_levels(
        total_sessions=16,
        total_turns=80,
        avg_session_score=88.0,
        must_fix_rate=0.04,
        total_corrections_rate=0.15,
        avg_response_speed_ms=1200.0,
    )
    assert lvl_prof["level_confidence"] == "high"
    assert lvl_prof["overall_level"] in ("intermediate", "upper_intermediate", "advanced")
