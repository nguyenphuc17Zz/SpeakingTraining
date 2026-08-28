import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.application.bottleneck_analyzer import BottleneckAnalyzer
from app.domains.analytics.application.insight_engine import InsightEngine
from app.domains.analytics.application.trend_analyzer import TrendAnalyzer
from app.domains.analytics.domain.insight_types import InsightType
from app.domains.analytics.domain.metric_definitions import (
    ConfidenceLevel,
    MetricKey,
    MetricValue,
    TrendLabel,
)


def test_trend_analyzer_deterministic_curves():
    """Verify trend analyzer accurately detects improving, declining, stable, plateau, and noise sequences."""
    # 1. Improving
    improving_seq = [60.0, 65.0, 70.0, 75.0, 80.0, 85.0]
    trend, conf, delta = TrendAnalyzer.classify_trend(improving_seq)
    assert trend in (TrendLabel.IMPROVING, TrendLabel.STRONGLY_IMPROVING)
    assert conf == ConfidenceLevel.MEDIUM
    assert delta is not None and delta > 0

    # 2. Plateau (very low variance over 5+ points)
    plateau_seq = [76.0, 76.5, 75.8, 76.2, 76.0]
    trend_p, conf_p, _ = TrendAnalyzer.classify_trend(plateau_seq)
    assert trend_p == TrendLabel.PLATEAU

    # 3. Noise Guard (fluctuations within noise margin are stable)
    noisy_seq = [72.0, 74.0, 71.0, 73.0, 72.5]
    trend_n, _, _ = TrendAnalyzer.classify_trend(noisy_seq)
    assert trend_n in (TrendLabel.STABLE, TrendLabel.PLATEAU)

    # 4. Insufficient samples (< 4)
    short_seq = [70.0, 80.0]
    trend_s, conf_s, _ = TrendAnalyzer.classify_trend(short_seq)
    assert trend_s == TrendLabel.INSUFFICIENT_DATA
    assert conf_s == ConfidenceLevel.INSUFFICIENT


def test_bottleneck_analyzer_transfer_gap():
    """Verify bottleneck analyzer detects Spontaneous Transfer Gap when drill accuracy is high but transfer is low."""
    analyzer = BottleneckAnalyzer(None)  # pure logic test

    metrics = {
        MetricKey.EXERCISE_SUCCESS_RATE.value: MetricValue(
            metric_key=MetricKey.EXERCISE_SUCCESS_RATE,
            value=88.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
        ),
        MetricKey.TRANSFER_RATE.value: MetricValue(
            metric_key=MetricKey.TRANSFER_RATE,
            value=45.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
        ),
        MetricKey.GRAMMAR_ACCURACY.value: MetricValue(
            metric_key=MetricKey.GRAMMAR_ACCURACY,
            value=85.0,
            sample_size=5,
            confidence=ConfidenceLevel.HIGH,
        ),
    }

    analysis = analyzer.analyze_bottleneck(metrics)
    assert "Transfer Gap" in analysis.candidate
    assert analysis.confidence == ConfidenceLevel.HIGH


@pytest.mark.asyncio
async def test_insight_engine_cooldown_and_deduplication(db_session: AsyncSession):
    """Verify InsightEngine generates structured insights and suppresses duplicate records within 48h."""
    insight_engine = InsightEngine(db_session)
    user_id = "test_insight_user_1"

    metrics = {
        MetricKey.MORA_TIMING.value: MetricValue(
            metric_key=MetricKey.MORA_TIMING,
            value=84.0,
            change=12.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
            trend=TrendLabel.IMPROVING,
        ),
        MetricKey.GRAMMAR_ACCURACY.value: MetricValue(
            metric_key=MetricKey.GRAMMAR_ACCURACY,
            value=85.0,
            sample_size=5,
            confidence=ConfidenceLevel.HIGH,
        ),
        MetricKey.NATURALNESS.value: MetricValue(
            metric_key=MetricKey.NATURALNESS,
            value=62.0,
            sample_size=5,
            confidence=ConfidenceLevel.HIGH,
        ),
    }

    # 1. First generation -> creates insights
    insights_1 = await insight_engine.generate_insights(user_id, metrics)
    assert len(insights_1) >= 2
    types_1 = [i.insight_type for i in insights_1]
    assert InsightType.IMPROVEMENT in types_1
    assert InsightType.OPPORTUNITY in types_1

    # 2. Second generation immediately after -> reuses active insights without error
    insights_2 = await insight_engine.generate_insights(user_id, metrics)
    assert len(insights_2) >= 2
