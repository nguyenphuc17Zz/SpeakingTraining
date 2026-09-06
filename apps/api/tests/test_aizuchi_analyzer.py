import pytest
from app.domains.conversation_intelligence.analyzers.aizuchi_analyzer import AizuchiAnalyzer
from app.domains.conversation_intelligence.analyzers.orchestrator import AnalysisOrchestrator
from app.domains.conversation_intelligence.contracts import (
    AizuchiCategory,
    AizuchiRegister,
    ConversationAnalysisInput,
    CorrectionCategory,
    CorrectionSeverity,
)


def test_aizuchi_taxonomy_classification():
    """Validates SLA classification across all backchannel taxonomies."""
    # Continuer
    cat, reg = AizuchiAnalyzer.classify_token("はい")
    assert cat == AizuchiCategory.CONTINUER
    assert reg == AizuchiRegister.POLITE

    cat, reg = AizuchiAnalyzer.classify_token("うん")
    assert cat == AizuchiCategory.CONTINUER
    assert reg == AizuchiRegister.CASUAL

    cat, reg = AizuchiAnalyzer.classify_token("ええ")
    assert cat == AizuchiCategory.CONTINUER
    assert reg == AizuchiRegister.FORMAL

    # Agreement
    cat, reg = AizuchiAnalyzer.classify_token("そうですね")
    assert cat == AizuchiCategory.AGREEMENT
    assert reg == AizuchiRegister.POLITE

    cat, reg = AizuchiAnalyzer.classify_token("だよね")
    assert cat == AizuchiCategory.AGREEMENT
    assert reg == AizuchiRegister.CASUAL

    cat, reg = AizuchiAnalyzer.classify_token("おっしゃる通りです")
    assert cat == AizuchiCategory.AGREEMENT
    assert reg == AizuchiRegister.FORMAL

    # Emotional Resonance
    cat, reg = AizuchiAnalyzer.classify_token("本当ですか")
    assert cat == AizuchiCategory.EMOTIONAL_RESONANCE
    assert reg == AizuchiRegister.POLITE

    cat, reg = AizuchiAnalyzer.classify_token("まじで")
    assert cat == AizuchiCategory.EMOTIONAL_RESONANCE
    assert reg == AizuchiRegister.CASUAL

    # Understanding
    cat, reg = AizuchiAnalyzer.classify_token("なるほど")
    assert cat == AizuchiCategory.UNDERSTANDING

    cat, reg = AizuchiAnalyzer.classify_token("理解いたしました")
    assert cat == AizuchiCategory.UNDERSTANDING
    assert reg == AizuchiRegister.FORMAL


def test_aizuchi_wakimae_formal_partner_violation():
    """Using casual backchannels with an interviewer or boss triggers politeness corrections."""
    # Saying "うん" to interviewer
    eval_result, corrections = AizuchiAnalyzer.evaluate(
        user_transcript="うん",
        persona_role="Interviewer (Tanaka-san)",
    )
    assert not eval_result.is_register_appropriate
    assert len(corrections) == 1
    assert corrections[0].severity == CorrectionSeverity.MUST_FIX
    assert corrections[0].category == CorrectionCategory.POLITENESS
    assert corrections[0].corrected == "はい"

    # Saying "なるほど" to interviewer / boss
    eval_result2, corrections2 = AizuchiAnalyzer.evaluate(
        user_transcript="なるほど",
        persona_role="Company Boss / Manager",
    )
    assert not eval_result2.is_register_appropriate
    assert len(corrections2) == 1
    assert corrections2[0].severity == CorrectionSeverity.SHOULD_FIX
    assert "おっしゃる通りです" in corrections2[0].corrected


def test_aizuchi_casual_partner_stiff_keigo():
    """Using stiff keigo backchannels with a friend generates a native alternative tip."""
    eval_result, corrections = AizuchiAnalyzer.evaluate(
        user_transcript="おっしゃる通りでございます",
        persona_role="Close Friend (Kenji)",
    )
    assert eval_result.is_register_appropriate
    assert len(corrections) == 1
    assert corrections[0].severity == CorrectionSeverity.NATIVE_ALTERNATIVE
    assert corrections[0].corrected == "うん"


def test_turn_initial_reactive_preface():
    """Detects turn-initial reactive prefaces and evaluates their flow and register."""
    # Appropriate preface in polite conversation
    eval_result, corrections = AizuchiAnalyzer.evaluate(
        user_transcript="そうですね、私も日本のアニメが好きです。",
        persona_role="Teacher",
    )
    assert eval_result.is_turn_initial_preface
    assert eval_result.category == AizuchiCategory.TURN_INITIAL_PREFACE
    assert eval_result.is_register_appropriate
    assert eval_result.naturalness_bonus > 0
    assert len(corrections) == 0

    # Inappropriate casual preface with interviewer
    eval_result2, corrections2 = AizuchiAnalyzer.evaluate(
        user_transcript="だよね、私の長所は忍耐力です。",
        persona_role="Interviewer",
    )
    assert eval_result2.is_turn_initial_preface
    assert not eval_result2.is_register_appropriate
    assert len(corrections2) == 1
    assert corrections2[0].corrected == "そうですね、"


def test_clause_boundary_sla_trigger():
    """Detects preceding partner clause-boundary triggers (e.g. 〜ね, 〜よね) and awards bonus."""
    prev_turns = [
        {"speaker": "assistant", "transcript": "東京の冬は結構寒いですよね？"}
    ]
    eval_result, _ = AizuchiAnalyzer.evaluate(
        user_transcript="そうですね",
        persona_role="Partner",
        previous_turns=prev_turns,
    )
    assert eval_result.clause_boundary_matched is True
    assert eval_result.naturalness_bonus == 8  # Matched clause boundary bonus


@pytest.mark.asyncio
async def test_orchestrator_integration_short_utterance_politeness(db_session):
    """Orchestrator accurately evaluates short utterances without naive blind passing."""
    orchestrator = AnalysisOrchestrator(db_session)

    # 1. Polite backchannel to partner -> High quality score and positive Aizuchi telemetry
    input_ok = ConversationAnalysisInput(
        session_id="test-session-aizuchi",
        current_turn_id="turn-ok",
        current_user_transcript="そうですね",
        persona_role="Colleague",
    )
    result_ok = await orchestrator.analyze_turn(input_ok)
    assert result_ok.overall_quality_score >= 95
    assert len(result_ok.corrections) == 0
    assert result_ok.aizuchi is not None
    assert result_ok.aizuchi.category == AizuchiCategory.AGREEMENT

    # 2. Impolite casual backchannel to interviewer -> Flagged with politeness correction
    input_bad = ConversationAnalysisInput(
        session_id="test-session-aizuchi",
        current_turn_id="turn-bad",
        current_user_transcript="うん",
        persona_role="Interviewer (Tanaka)",
    )
    result_bad = await orchestrator.analyze_turn(input_bad)
    assert result_bad.overall_quality_score <= 75
    assert len(result_bad.corrections) == 1
    assert result_bad.corrections[0].category == CorrectionCategory.POLITENESS
    assert result_bad.corrections[0].corrected == "はい"
    assert result_bad.context_notes[0].formality_level == "too_casual"
