import pytest
from app.domains.analytics.application.trend_analyzer import TrendAnalyzer


def test_holt_winters_insufficient_samples_fallback():
    """Verify fallback when series has fewer than 4 points."""
    res = TrendAnalyzer.forecast_velocity_holt_winters([65.0, 70.0])
    assert res.model_type == "baseline_flat"
    assert len(res.forecast_points) == 7
    assert all(p == 70.0 for p in res.forecast_points)
    assert res.current_velocity == 0.0


def test_holt_linear_trend_forecasting():
    """Verify Double Exponential Smoothing accurately models linear velocity."""
    # Linear upward trend: 50, 55, 60, 65, 70, 75, 80, 85
    linear_series = [50.0 + 5.0 * i for i in range(8)]
    res = TrendAnalyzer.forecast_velocity_holt_winters(linear_series, forecast_horizon=5)

    assert res.model_type == "holt_linear_trend"
    assert res.current_velocity > 4.0  # Slope ~5.0
    assert len(res.forecast_points) == 5

    # Forecast points must strictly increase
    for i in range(len(res.forecast_points) - 1):
        assert res.forecast_points[i] < res.forecast_points[i + 1]

    # Confidence intervals integrity
    for interval in res.intervals:
        assert interval.lower_95 <= interval.lower_80
        assert interval.lower_80 <= interval.point
        assert interval.point <= interval.upper_80
        assert interval.upper_80 <= interval.upper_95


def test_additive_triple_holt_winters_seasonality():
    """Verify Triple Exponential Smoothing handles seasonal patterns with 2+ seasons."""
    # 2 weeks of daily practice data with weekly cycle (season length = 7)
    # Weekday baseline ~60, weekend spike ~85
    week_pattern = [60.0, 62.0, 61.0, 63.0, 65.0, 85.0, 90.0]
    series_2weeks = week_pattern + [x + 5.0 for x in week_pattern]  # With upward trend

    res = TrendAnalyzer.forecast_velocity_holt_winters(
        series_2weeks,
        forecast_horizon=7,
        season_length=7,
    )

    assert res.model_type == "additive_holt_winters"
    assert len(res.forecast_points) == 7
    assert res.current_velocity > 0.0

    # Weekend steps in forecast should show positive seasonal peak
    # (Steps 6 and 7 correspond to Saturday/Sunday)
    assert res.forecast_points[5] > res.forecast_points[0]
    assert res.forecast_points[6] > res.forecast_points[0]
