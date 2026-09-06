"""Shadowing Acoustic Lag Profiler & Intonation DTW Engine.

Implements cognitive SLA shadowing science (Lambert 1992; Kadota 2007; Tamai 1997):
- Optimal cognitive shadowing lag τ ∈ [150ms, 400ms] (sweet spot ~250ms).
- Penalizes concurrent talking over (< 100ms) and trailing into delayed repeat (> 700ms).
- Dynamic Time Warping (DTW) intonation contour evaluation.
"""

from __future__ import annotations

import math
from typing import Any

from app.domains.pitch.acoustic.dtw_pitch import DTWPitchEngine


class ShadowingLagProfiler:
    """Acoustic lag and intonation contour profiler for Japanese shadowing."""

    OPTIMAL_LAG_MIN_MS: float = 150.0
    OPTIMAL_LAG_MAX_MS: float = 400.0
    SWEET_SPOT_MS: float = 250.0
    TALKING_OVER_LIMIT_MS: float = 100.0
    TRAILING_LIMIT_MS: float = 700.0

    @classmethod
    def classify_lag(cls, lag_ms: float) -> str:
        """Classifies auditory-vocal shadowing lag into discrete cognitive tiers.

        - 'optimal': 150ms - 400ms (ideal cognitive tracking window)
        - 'too_fast': < 100ms (talking over / concurrent auditory interference)
        - 'hesitant': 100ms - 149ms or 401ms - 700ms (mild hesitation / lag)
        - 'trailing': > 700ms (dropped out of shadowing into sequential repeating)
        """
        if lag_ms < cls.TALKING_OVER_LIMIT_MS:
            return "too_fast"
        if cls.OPTIMAL_LAG_MIN_MS <= lag_ms <= cls.OPTIMAL_LAG_MAX_MS:
            return "optimal"
        if lag_ms <= cls.TRAILING_LIMIT_MS:
            return "hesitant"
        return "trailing"

    @classmethod
    def compute_lag_score(cls, lag_ms: float) -> float:
        """Calculates psychometric lag score [0.0 - 100.0].

        Peak performance at 250ms with a broad plateau over [150ms, 400ms].
        """
        if cls.OPTIMAL_LAG_MIN_MS <= lag_ms <= cls.OPTIMAL_LAG_MAX_MS:
            # Inside optimal plateau: scores 92 - 100
            diff = abs(lag_ms - cls.SWEET_SPOT_MS)
            score = 100.0 - (diff / 150.0) * 8.0
            return round(max(92.0, min(100.0, score)), 1)

        if lag_ms < cls.OPTIMAL_LAG_MIN_MS:
            # Talking over: rapid decay down to ~35% at 0ms
            ratio = max(0.0, lag_ms) / cls.OPTIMAL_LAG_MIN_MS
            score = 35.0 + ratio * 57.0
            return round(max(30.0, min(92.0, score)), 1)

        # Trailing lag > 400ms: Gaussian decay
        delta = lag_ms - cls.OPTIMAL_LAG_MAX_MS
        decay = math.exp(-((delta) ** 2) / (2 * (280.0 ** 2)))
        score = 40.0 + decay * 52.0
        return round(max(25.0, min(92.0, score)), 1)

    @classmethod
    def evaluate_pitch_contour(
        cls,
        user_pitch_curve: Any | None,
        reference_semitones: list[float] | None = None,
    ) -> float | None:
        """Evaluates intonation contour similarity using DTW with Semitone Normalization."""
        if not user_pitch_curve:
            return None

        points = getattr(user_pitch_curve, "points", None)
        if not points:
            return None

        # Extract voiced semitone values
        voiced_semitones = [
            float(p.normalized_semitones)
            for p in points
            if getattr(p, "is_voiced", True) and getattr(p, "normalized_semitones", None) is not None
        ]
        if len(voiced_semitones) < 3:
            return None

        # If explicit reference is provided, run full DTW
        if reference_semitones and len(reference_semitones) >= 3:
            distance, _ = DTWPitchEngine.compute_dtw_distance(voiced_semitones, reference_semitones)
            similarity = round(100.0 * math.exp(-0.45 * distance), 1)
            return max(0.0, min(100.0, similarity))

        # Intonation contour dynamism / stability heuristic: rewards natural pitch fluctuations
        diffs = [abs(voiced_semitones[i] - voiced_semitones[i - 1]) for i in range(1, len(voiced_semitones))]
        avg_diff = sum(diffs) / len(diffs) if diffs else 0.0
        # Natural Japanese sentence intonation has mean frame-to-frame delta ~0.3 - 1.2 semitones
        if 0.25 <= avg_diff <= 1.5:
            dynamic_score = 90.0 + min(10.0, (avg_diff - 0.25) * 8.0)
        else:
            dynamic_score = max(55.0, 90.0 - abs(avg_diff - 0.8) * 25.0)
        return round(dynamic_score, 1)

    @classmethod
    def generate_lag_issue(cls, lag_ms: float, rating: str) -> dict[str, Any] | None:
        """Generates targeted pedagogical recommendation based on cognitive shadowing lag."""
        if rating == "too_fast":
            return {
                "title": "Nói đè lên giọng mẫu (Concurrent Interference)",
                "category": "Độ trễ Shadowing",
                "explanation": (
                    f"Độ trễ phản xạ chỉ {lag_ms:.0f}ms (< 100ms). Bạn đang bắt đầu phát âm gần như đồng thời, "
                    f"dẫn đến việc cơ quan thính giác bị nhiễu và không nghe trọn vẹn được sắc thái bản ngữ."
                ),
                "practice_tip": "Hãy giữ độ trễ tối ưu 150–400ms (khoảng 1/4 nhịp mora). Để tai nghe từ đầu tiên trước khi miệng cất lời.",
            }

        if rating == "trailing":
            return {
                "title": "Bị tụt nhịp Shadowing (Trailing)",
                "category": "Độ trễ Shadowing",
                "explanation": (
                    f"Độ trễ phản xạ đạt {lag_ms:.0f}ms (> 700ms). Bạn đang rơi vào thói quen nghe hết câu rồi mới lặp lại (Repeat) "
                    f"thay vì duy trì phản xạ đuổi bóng (Shadowing) tức thì."
                ),
                "practice_tip": "Nói đuổi sát theo giọng mẫu hơn, phát âm ngay khi người nói vừa dứt âm tiết đầu tiên.",
            }

        if rating == "hesitant":
            return {
                "title": "Độ trễ Shadowing hơi chậm",
                "category": "Độ trễ Shadowing",
                "explanation": f"Độ trễ phản xạ đạt {lag_ms:.0f}ms. Bạn bám sát nội dung tốt nhưng nhịp đuổi bóng còn hơi dè dặt.",
                "practice_tip": "Thả lỏng cơ hàm và tự tin bật âm sớm hơn để đưa độ trễ về vùng vàng 250ms.",
            }

        return None
