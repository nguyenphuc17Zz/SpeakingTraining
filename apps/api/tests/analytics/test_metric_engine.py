import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.application.metric_engine import MetricEngine
from app.domains.analytics.domain.metric_definitions import ConfidenceLevel, MetricKey, TrendLabel
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.learning.models import Exercise, ExerciseAttempt, LearningItem
from app.domains.pronunciation.models import PronunciationAttempt


@pytest.mark.asyncio
async def test_metric_engine_empty_data(db_session: AsyncSession):
    """Verify that when no data exists, MetricEngine returns insufficient data safely without errors or hallucinations."""
    engine = MetricEngine(db_session)
    user_id = "test_empty_user"

    metrics = await engine.get_all_metrics(user_id, period="30d")
    assert len(metrics) > 0

    # Pronunciation overall should be insufficient
    pron_m = metrics[MetricKey.PRONUNCIATION_OVERALL.value]
    assert pron_m.sample_size == 0
    assert pron_m.confidence == ConfidenceLevel.INSUFFICIENT
    assert pron_m.trend == TrendLabel.INSUFFICIENT_DATA
    assert pron_m.value == 0.0


@pytest.mark.asyncio
async def test_metric_engine_with_sample_data(db_session: AsyncSession):
    """Verify MetricEngine aggregates pronunciation attempts and conversation turns correctly."""
    user_id = "test_learner_metrics_1"

    # 1. Seed pronunciation attempts
    for i, score in enumerate([70.0, 75.0, 80.0, 85.0, 90.0]):
        att = PronunciationAttempt(
            id=str(uuid.uuid4()),
            user_id=user_id,
            reference_text="こんにちは",
            target_type="sentence",
            analysis_status="completed",
            overall_score=score,
            scores_json={
                "pitch_accent": {"pitch_accuracy": score - 2},
                "mora_timing": {"mora_accuracy": score + 1},
                "sentence_intonation": {"intonation_score": score},
            },
        )
        db_session.add(att)

    # 2. Seed an exercise and completed attempts
    ex = Exercise(
        id=str(uuid.uuid4()),
        user_id=user_id,
        exercise_type="targeted_drill",
        title="Particle Ni Drill",
        objective="Use に accurately",
        instructions="Complete the sentence",
    )
    db_session.add(ex)
    await db_session.flush()

    for succ in [True, True, True, False]:
        attempt = ExerciseAttempt(
            id=str(uuid.uuid4()),
            exercise_id=ex.id,
            user_id=user_id,
            status="completed",
            success=succ,
        )
        db_session.add(attempt)

    await db_session.commit()

    engine = MetricEngine(db_session)
    metrics = await engine.get_all_metrics(user_id, period="30d")

    # Pronunciation
    pron = metrics[MetricKey.PRONUNCIATION_OVERALL.value]
    assert pron.sample_size == 5
    assert pron.value == 80.0
    assert pron.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)
    assert pron.trend in (TrendLabel.IMPROVING, TrendLabel.STRONGLY_IMPROVING)

    # Exercise success
    ex_succ = metrics[MetricKey.EXERCISE_SUCCESS_RATE.value]
    assert ex_succ.sample_size == 4
    assert ex_succ.value == 75.0  # 3/4 = 75%
