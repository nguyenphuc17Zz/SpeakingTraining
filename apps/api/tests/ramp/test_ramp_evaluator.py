"""Tests for RampEvaluator scoring and feedback generation."""

import pytest
from unittest.mock import AsyncMock, patch
from app.domains.ramp.contracts import (
    RampExerciseType,
    RampScaffold,
    RampTaskSpec,
    RampTopicDomain,
)
from app.domains.ramp.ramp_evaluator import RampEvaluator


@pytest.mark.asyncio
async def test_ramp_evaluator_deterministic_scoring(db_session):
    evaluator = RampEvaluator(db_session)

    task_spec = RampTaskSpec(
        exercise_type=RampExerciseType.SPEAK_REASON,
        stage=5,
        topic="週末の予定",
        topic_domain=RampTopicDomain.DAILY_LIFE,
        prompt_jp="週末は何をしますか？理由も教えてください。",
        target_duration_sec=15,
        support_level=0,
        scaffold=RampScaffold(),
    )

    # User gives full sentence with reason, support level 0 (independent)
    transcript = "週末は家で読書をします。最近忙しかったから、ゆっくり休みたいです。"

    with patch.object(evaluator, "_evaluate_with_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "semantic_relevance": 90.0,
            "naturalness": 85.0,
            "grammar_score": 90.0,
            "completeness": 90.0,
            "idea_quality": 85.0,
            "has_reason": True,
            "has_example": False,
            "sentence_complete": True,
            "errors": [],
            "correction_jp": None,
            "feedback_jp": "よくできました！",
        }

        score, feedback = await evaluator.evaluate(
            task_spec=task_spec,
            user_transcript=transcript,
            support_level_used=0,
            audio_metrics={"speech_duration_ms": 12000, "filler_rate": 0.02, "long_pause_count": 0},
            response_latency_ms=1500,
            used_hint=False,
        )

        assert score.overall >= 75.0
        assert score.independence >= 90.0
        assert score.production_accuracy >= 80.0
        assert feedback.meaning_clear is True
        assert feedback.grammar_ok is True
        assert feedback.missing_reason is False
        assert "✅ 意味が伝わった" in feedback.badges


@pytest.mark.asyncio
async def test_ramp_evaluator_penalizes_incomplete_sentence(db_session):
    evaluator = RampEvaluator(db_session)

    task_spec = RampTaskSpec(
        exercise_type=RampExerciseType.SPEAK_ONE_SENTENCE,
        stage=3,
        topic="映画",
        topic_domain=RampTopicDomain.PERSONAL,
        prompt_jp="好きな映画について教えてください。",
        target_duration_sec=5,
        support_level=0,
        scaffold=RampScaffold(),
    )

    transcript = "映画。"

    with patch.object(evaluator, "_evaluate_with_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "semantic_relevance": 40.0,
            "naturalness": 30.0,
            "grammar_score": 40.0,
            "completeness": 20.0,
            "idea_quality": 20.0,
            "has_reason": False,
            "has_example": False,
            "sentence_complete": False,
            "errors": [{"fragment": "映画。", "correction": "映画が好きです。", "note": "単語のみ"}],
            "correction_jp": "映画を見るのが好きです。",
            "feedback_jp": "文の形で話してみましょう。",
        }

        score, feedback = await evaluator.evaluate(
            task_spec=task_spec,
            user_transcript=transcript,
            support_level_used=0,
            response_latency_ms=3000,
            used_hint=False,
        )

        assert score.overall < 60.0
        assert feedback.incomplete_sentence is True
        assert feedback.next_action in ("retry", "elaborate")
