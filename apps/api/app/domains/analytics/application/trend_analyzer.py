import math
from typing import Sequence

from app.domains.analytics.domain.metric_definitions import ConfidenceLevel, TrendLabel


class TrendAnalyzer:
    """
    Deterministic statistical trend detector.
    Never uses AI/LLMs to compute statistical trends.
    Uses smoothing, noise guards, plateau detection, and sample size checks.
    """

    @staticmethod
    def classify_trend(
        data_points: Sequence[float],
        min_samples: int = 4,
        plateau_threshold_cv: float = 0.04,  # Coefficient of variation < 4% = plateau
        noise_margin: float = 3.0,          # Noise margin in absolute units
    ) -> tuple[TrendLabel, ConfidenceLevel, float | None]:
        """
        Takes a time-ordered sequence of values (oldest to newest).
        Returns (TrendLabel, ConfidenceLevel, calculated_change).
        """
        n = len(data_points)
        if n < min_samples:
            return TrendLabel.INSUFFICIENT_DATA, ConfidenceLevel.INSUFFICIENT, None

        # 1. Determine Confidence Level based on sample size
        if n >= 8:
            confidence = ConfidenceLevel.HIGH
        elif n >= 5:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        # 2. Check for Plateau (low variance over at least 5 points)
        if n >= 5:
            mean = sum(data_points) / n
            if mean > 0:
                variance = sum((x - mean) ** 2 for x in data_points) / n
                std_dev = math.sqrt(variance)
                cv = std_dev / mean
                if cv <= plateau_threshold_cv:
                    return TrendLabel.PLATEAU, confidence, 0.0

        # 3. Smoothed trend calculation using Exponential Moving Average (EMA)
        alpha = 0.35
        smoothed = []
        cur_ema = data_points[0]
        for val in data_points:
            cur_ema = alpha * val + (1 - alpha) * cur_ema
            smoothed.append(cur_ema)

        # Compare first third vs last third of smoothed history
        split_idx = max(1, n // 3)
        baseline_avg = sum(smoothed[:split_idx]) / split_idx
        recent_avg = sum(smoothed[-split_idx:]) / split_idx
        delta = recent_avg - baseline_avg

        # Noise guard: fluctuations within noise margin are considered stable
        if abs(delta) < noise_margin:
            return TrendLabel.STABLE, confidence, round(delta, 2)

        if delta >= 10.0:
            return TrendLabel.STRONGLY_IMPROVING, confidence, round(delta, 2)
        elif delta > 0:
            return TrendLabel.IMPROVING, confidence, round(delta, 2)
        elif delta <= -10.0:
            return TrendLabel.STRONGLY_DECLINING, confidence, round(delta, 2)
        else:
            return TrendLabel.DECLINING, confidence, round(delta, 2)
