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

    @staticmethod
    def forecast_velocity_holt_winters(
        series: Sequence[float],
        forecast_horizon: int = 7,
        alpha: float = 0.3,
        beta: float = 0.1,
        gamma: float = 0.2,
        season_length: int = 7,
    ):
        """Computes deterministic forecasting and velocity tracking using Holt-Winters Exponential Smoothing.

        - If series < 4: fallback with flat projection.
        - If 4 <= series < 2 * season_length: Holt's Linear Trend (Double Exponential Smoothing).
        - If series >= 2 * season_length: Additive Triple Exponential Smoothing (Level, Trend, Seasonality).
        - Generates 80% and 95% confidence intervals from residual standard error.
        """
        from app.domains.analytics.schemas import ForecastConfidenceIntervalDTO, HoltWintersForecastDTO

        n = len(series)
        if n < 4:
            last_val = series[-1] if n > 0 else 0.0
            pts = [round(last_val, 2)] * forecast_horizon
            intervals = [
                ForecastConfidenceIntervalDTO(
                    step=h,
                    point=round(last_val, 2),
                    lower_80=round(last_val, 2),
                    upper_80=round(last_val, 2),
                    lower_95=round(last_val, 2),
                    upper_95=round(last_val, 2),
                )
                for h in range(1, forecast_horizon + 1)
            ]
            return HoltWintersForecastDTO(
                forecast_points=pts,
                current_level=round(last_val, 2),
                current_velocity=0.0,
                acceleration=0.0,
                intervals=intervals,
                residual_standard_error=0.0,
                model_type="baseline_flat",
            )

        # Case A: Holt's Linear Trend (Double Exponential Smoothing)
        if n < 2 * season_length:
            level = series[0]
            trend = (series[-1] - series[0]) / max(1, n - 1)
            residuals: list[float] = []
            prev_trend = trend

            for t in range(1, n):
                y = series[t]
                prev_level = level
                prev_trend = trend
                level = alpha * y + (1.0 - alpha) * (prev_level + prev_trend)
                trend = beta * (level - prev_level) + (1.0 - beta) * prev_trend
                fitted = prev_level + prev_trend
                residuals.append(y - fitted)

            acceleration = trend - prev_trend
            curr_level = level
            curr_trend = trend

            pts = []
            for h in range(1, forecast_horizon + 1):
                pts.append(round(curr_level + h * curr_trend, 2))

            mse = sum(r**2 for r in residuals) / max(1, len(residuals))
            rse = math.sqrt(mse)

            intervals = []
            for h in range(1, forecast_horizon + 1):
                sigma_h = rse * math.sqrt(1.0 + (h - 1) * (alpha**2))
                val = pts[h - 1]
                intervals.append(
                    ForecastConfidenceIntervalDTO(
                        step=h,
                        point=val,
                        lower_80=round(val - 1.282 * sigma_h, 2),
                        upper_80=round(val + 1.282 * sigma_h, 2),
                        lower_95=round(val - 1.960 * sigma_h, 2),
                        upper_95=round(val + 1.960 * sigma_h, 2),
                    )
                )

            return HoltWintersForecastDTO(
                forecast_points=pts,
                current_level=round(curr_level, 2),
                current_velocity=round(curr_trend, 3),
                acceleration=round(acceleration, 3),
                intervals=intervals,
                residual_standard_error=round(rse, 2),
                model_type="holt_linear_trend",
            )

        # Case B: Additive Holt-Winters (Triple Exponential Smoothing)
        m = season_length
        init_level = sum(series[:m]) / m
        init_trend = sum((series[i + m] - series[i]) / m for i in range(m)) / m
        seasonal = [series[i] - init_level for i in range(m)]

        level = init_level
        trend = init_trend
        residuals = []
        prev_trend = trend

        for t in range(m, n):
            y = series[t]
            prev_level = level
            prev_trend = trend
            s_prev = seasonal[t % m]

            level = alpha * (y - s_prev) + (1.0 - alpha) * (prev_level + prev_trend)
            trend = beta * (level - prev_level) + (1.0 - beta) * prev_trend
            seasonal[t % m] = gamma * (y - level) + (1.0 - gamma) * s_prev

            fitted = prev_level + prev_trend + s_prev
            residuals.append(y - fitted)

        acceleration = trend - prev_trend
        curr_level = level
        curr_trend = trend

        pts = []
        for h in range(1, forecast_horizon + 1):
            s_idx = (n + h - 1) % m
            forecast_val = curr_level + h * curr_trend + seasonal[s_idx]
            pts.append(round(forecast_val, 2))

        mse = sum(r**2 for r in residuals) / max(1, len(residuals))
        rse = math.sqrt(mse)

        intervals = []
        for h in range(1, forecast_horizon + 1):
            sigma_h = rse * math.sqrt(1.0 + (h - 1) * (alpha**2))
            val = pts[h - 1]
            intervals.append(
                ForecastConfidenceIntervalDTO(
                    step=h,
                    point=val,
                    lower_80=round(val - 1.282 * sigma_h, 2),
                    upper_80=round(val + 1.282 * sigma_h, 2),
                    lower_95=round(val - 1.960 * sigma_h, 2),
                    upper_95=round(val + 1.960 * sigma_h, 2),
                )
            )

        return HoltWintersForecastDTO(
            forecast_points=pts,
            current_level=round(curr_level, 2),
            current_velocity=round(curr_trend, 3),
            acceleration=round(acceleration, 3),
            intervals=intervals,
            residual_standard_error=round(rse, 2),
            model_type="additive_holt_winters",
        )

