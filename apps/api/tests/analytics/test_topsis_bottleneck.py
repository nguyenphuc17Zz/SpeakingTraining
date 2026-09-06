import pytest
from app.domains.analytics.application.bottleneck_analyzer import BottleneckAnalyzer
from app.domains.analytics.domain.metric_definitions import ConfidenceLevel, MetricKey, MetricValue


def test_topsis_transfer_gap_primary():
    """Verify TOPSIS ranks Spontaneous Transfer Gap as #1 when drills are mastered but free transfer is low."""
    analyzer = BottleneckAnalyzer(None)

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
            value=82.0,
            sample_size=5,
            confidence=ConfidenceLevel.HIGH,
        ),
    }

    res = analyzer.analyze_bottleneck(metrics)

    assert "Transfer Gap" in res.candidate
    assert res.ranking_score is not None
    assert res.ranking_score > 0.40
    assert res.confidence == ConfidenceLevel.HIGH


def test_topsis_balanced_progression():
    """Verify TOPSIS detects Balanced Development when all dimensions are within target thresholds."""
    analyzer = BottleneckAnalyzer(None)

    healthy_metrics = {
        MetricKey.EXERCISE_SUCCESS_RATE.value: MetricValue(
            metric_key=MetricKey.EXERCISE_SUCCESS_RATE,
            value=80.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
        ),
        MetricKey.TRANSFER_RATE.value: MetricValue(
            metric_key=MetricKey.TRANSFER_RATE,
            value=76.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
        ),
        MetricKey.GRAMMAR_ACCURACY.value: MetricValue(
            metric_key=MetricKey.GRAMMAR_ACCURACY,
            value=82.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
        ),
        MetricKey.NATURALNESS.value: MetricValue(
            metric_key=MetricKey.NATURALNESS,
            value=78.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
        ),
        MetricKey.RESPONSE_SPEED.value: MetricValue(
            metric_key=MetricKey.RESPONSE_SPEED,
            value=1350.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
        ),
        MetricKey.MORA_TIMING.value: MetricValue(
            metric_key=MetricKey.MORA_TIMING,
            value=77.0,
            sample_size=6,
            confidence=ConfidenceLevel.HIGH,
        ),
    }

    res = analyzer.analyze_bottleneck(healthy_metrics)
    assert "Balanced Development" in res.candidate
    assert res.confidence == ConfidenceLevel.HIGH
