import json
from pathlib import Path

import pytest

from app.domains.conversation_intelligence.analyzers.orchestrator import AnalysisOrchestrator
from app.domains.conversation_intelligence.contracts import (
    ConversationAnalysisInput,
    CorrectionCategory,
    CorrectionSeverity,
)

FIXTURES_PATH = Path(__file__).parent / "evaluations" / "fixtures" / "speaking_evaluation_cases.json"


def load_fixtures():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_evaluation_benchmark_suite(db_session):
    cases = load_fixtures()
    assert len(cases) >= 10

    orchestrator = AnalysisOrchestrator(db_session)

    for tc in cases:
        tc_id = tc["id"]
        input_data = ConversationAnalysisInput(
            session_id="benchmark-sess-1",
            current_turn_id=tc_id,
            current_user_transcript=tc["input_transcript"],
            stt_confidence=tc.get("stt_confidence", 0.95),
            persona_role=tc.get("persona_role", "Partner"),
            persona_style=tc.get("persona_style", "Natural"),
            conversation_mode=tc.get("mode", "conversation"),
        )

        result = await orchestrator.analyze_turn(input_data)
        assert result.turn_id == tc_id
        assert result.overall_quality_score >= 0
        assert len(result.strengths) >= 1, f"Test case {tc_id} missing mandatory positive strengths"

        # Check Specific Case Constraints
        if tc_id == "tc_02_natural_informal_meccha":
            # Must NOT produce MUST_FIX error for natural casual slang in friendly context
            for corr in result.corrections:
                assert (
                    corr.severity != CorrectionSeverity.MUST_FIX
                ), f"{tc_id}: 'めっちゃ' should not be marked MUST_FIX"

        elif tc_id == "tc_08_whisper_uncertainty_guard":
            # Low confidence Whisper STT must not yield MUST_FIX
            for corr in result.corrections:
                assert (
                    corr.severity != CorrectionSeverity.MUST_FIX
                ), f"{tc_id}: Low STT confidence should not yield MUST_FIX"

        elif tc_id == "tc_10_short_acknowledgement_bypass":
            # Short acknowledgement returns 95+ score without corrections
            assert result.overall_quality_score >= 90
            assert len(result.corrections) == 0
