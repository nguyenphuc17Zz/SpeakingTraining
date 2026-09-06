"""Adaptive pressure — SOTA Item Response Theory (IRT) Elo and ZPD Flow State Engine.

Replaces legacy crude rule tables with:
1. Continuous Reflex Elo Rating (θ) with dynamic K-factor and latency-weighted performance.
2. Vygotsky Zone of Proximal Development (ZPD) & Csíkszentmihályi Flow State Engine targeting 76% optimal success probability.
3. Continuous millisecond reaction timer adaptation mapped to standard pressure profiles.
4. Cognitive state diagnosis: Flow, Comfort Plateau, Cognitive Overload, Speed-Inaccuracy Trap, Reaction Hesitation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.domains.reflex.pressure_profiles import ADAPTIVE_PRESSURE_ORDER, PressureLevel, timer_for_level


class CognitiveFlowState(str, Enum):
    """Cognitive processing state during speed reflex speaking."""

    FLOW = "flow"
    COMFORT_PLATEAU = "comfort_plateau"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    SPEED_INACCURACY_TRAP = "speed_inaccuracy_trap"
    REACTION_HESITATION = "reaction_hesitation"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class FlowAssessment:
    """Comprehensive cognitive flow & Elo assessment telemetry."""

    current_rating: float
    rating_deviation: float
    cognitive_state: CognitiveFlowState
    recommended_level: str
    recommended_timer_ms: int
    exact_target_timer_ms: float
    flow_probability: float
    reason: str
    comfort_window: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_rating": round(self.current_rating, 1),
            "rating_deviation": round(self.rating_deviation, 1),
            "cognitive_state": self.cognitive_state.value,
            "recommended_level": self.recommended_level,
            "recommended_timer_ms": self.recommended_timer_ms,
            "exact_target_timer_ms": round(self.exact_target_timer_ms, 1),
            "flow_probability": round(self.flow_probability, 3),
            "reason": self.reason,
            "comfort_window": self.comfort_window,
        }


class ReflexEloEngine:
    """Psychometric Item Response Theory (IRT) & Elo rating engine for speech reflex automaticity."""

    DEFAULT_RATING: float = 1200.0
    DEFAULT_RD: float = 350.0
    MIN_RATING: float = 600.0
    MAX_RATING: float = 2600.0
    REFERENCE_TIMER_MS: float = 4000.0
    REFERENCE_DIFFICULTY: float = 1200.0
    DIFFICULTY_SLOPE: float = 400.0

    @classmethod
    def timer_to_difficulty(cls, timer_limit_ms: float) -> float:
        """Maps millisecond timer limit to continuous item difficulty rating β(T)."""
        if timer_limit_ms <= 0:
            return 800.0  # Infinite timer = low constraint
        clamped_t = max(1000.0, min(10000.0, float(timer_limit_ms)))
        return cls.REFERENCE_DIFFICULTY + cls.DIFFICULTY_SLOPE * math.log2(cls.REFERENCE_TIMER_MS / clamped_t)

    @classmethod
    def expected_success_probability(cls, rating: float, difficulty: float) -> float:
        """Logistic Rasch/Elo model: P(success | θ, β)."""
        exponent = (difficulty - rating) / 400.0
        # Prevent numerical overflow
        clamped_exp = max(-20.0, min(20.0, exponent))
        return 1.0 / (1.0 + math.pow(10.0, clamped_exp))

    @classmethod
    def effective_performance(
        cls,
        success: bool,
        score: float,
        reaction_latency_ms: float | None,
        timer_limit_ms: float,
    ) -> float:
        """Computes latency-weighted performance S_effective ∈ [0.0, 1.15]."""
        norm_score = max(0.0, min(1.0, float(score) / 100.0))
        if not success:
            return max(0.0, norm_score * 0.15)

        base = 1.0
        if reaction_latency_ms is not None and timer_limit_ms > 0:
            ratio = reaction_latency_ms / timer_limit_ms
            if ratio < 0.50:
                # Sub-second reflex automaticity bonus up to +0.15
                bonus = 0.15 * (1.0 - 2.0 * ratio)
                return min(1.15, base + bonus)
            if ratio > 0.85:
                # Near-deadline hesitation discount
                return 0.85
        return base

    @classmethod
    def estimate_rating(
        cls,
        attempts: list[dict[str, Any]],
        initial_rating: float = DEFAULT_RATING,
    ) -> tuple[float, float]:
        """Calculates current continuous skill rating θ and rating deviation RD."""
        rating = initial_rating
        count = 0

        for a in attempts:
            count += 1
            t_ms = float(a.get("timer_limit_ms") or 3000.0)
            beta = cls.timer_to_difficulty(t_ms)
            expected = cls.expected_success_probability(rating, beta)
            actual = cls.effective_performance(
                bool(a.get("success")),
                float(a.get("score") or 0.0),
                a.get("reaction_latency_ms"),
                t_ms,
            )
            # Dynamic K-factor: higher adaptation early, stabilizes over time
            k_factor = max(16.0, 48.0 * math.pow(0.95, count))
            delta = k_factor * (actual - expected)
            rating = max(cls.MIN_RATING, min(cls.MAX_RATING, rating + delta))

        rd = max(60.0, cls.DEFAULT_RD * math.pow(0.93, count))
        return rating, rd


class ZPDFlowEngine:
    """Vygotsky Zone of Proximal Development (ZPD) & Csíkszentmihályi Flow State Engine."""

    TARGET_FLOW_PROBABILITY: float = 0.76  # 76% optimal learning challenge

    @classmethod
    def calculate_target_timer_ms(cls, rating: float) -> float:
        """Derives exact optimal millisecond timer T* producing 76% expected success."""
        # For P* = 0.76, β* = θ - 400 * log10((1 - 0.76) / 0.76) ≈ θ + 200.2
        # T* = 4000 * 2^(-(θ - 1000) / 400)
        power = -(rating - 1000.0) / 400.0
        clamped_power = max(-2.5, min(1.5, power))
        target_t = 4000.0 * math.pow(2.0, clamped_power)
        return max(1500.0, min(6500.0, target_t))

    @classmethod
    def map_timer_to_level(cls, target_timer_ms: float) -> str:
        """Maps millisecond target to the nearest discrete ADAPTIVE_PRESSURE_ORDER tier."""
        standard_tiers = [
            PressureLevel.RELAXED.value,
            PressureLevel.NORMAL.value,
            PressureLevel.FAST.value,
            PressureLevel.REFLEX.value,
            PressureLevel.EXTREME.value,
        ]
        best_level = PressureLevel.NORMAL.value
        min_diff = float("inf")
        for lvl in standard_tiers:
            t = timer_for_level(lvl)
            diff = abs(t - target_timer_ms)
            if diff < min_diff:
                min_diff = diff
                best_level = lvl
        return best_level

    @classmethod
    def evaluate_flow(
        cls,
        current_level: str,
        attempts: list[dict[str, Any]],
        *,
        sub_mode: str | None = None,
        min_samples: int = 5,
    ) -> FlowAssessment:
        """Performs full psychometric and cognitive state evaluation."""
        comparable = _filter_comparable(attempts, sub_mode)
        rating, rd = ReflexEloEngine.estimate_rating(comparable)
        target_timer_ms = cls.calculate_target_timer_ms(rating)
        nearest_level = cls.map_timer_to_level(target_timer_ms)
        curr_timer = timer_for_level(current_level) if current_level != PressureLevel.INFINITE.value else 6000
        curr_difficulty = ReflexEloEngine.timer_to_difficulty(curr_timer)
        p_success = ReflexEloEngine.expected_success_probability(rating, curr_difficulty)

        if len(comparable) < min_samples:
            return FlowAssessment(
                current_rating=rating,
                rating_deviation=rd,
                cognitive_state=CognitiveFlowState.INSUFFICIENT_DATA,
                recommended_level=current_level,
                recommended_timer_ms=curr_timer,
                exact_target_timer_ms=target_timer_ms,
                flow_probability=p_success,
                reason=f"Cần thêm dữ liệu ({len(comparable)}/{min_samples} lượt) để xác định Flow State chính xác.",
            )

        window = comparable[-min_samples:]
        successes = sum(1 for a in window if a.get("success"))
        acc = successes / len(window)
        avg_score = sum(float(a.get("score", 0)) for a in window) / len(window)
        latencies = [a.get("reaction_latency_ms") for a in window if a.get("reaction_latency_ms") is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        avg_timer = sum(float(a.get("timer_limit_ms", 3000)) for a in window) / len(window)
        reaction_ratio = (avg_latency / avg_timer) if (avg_latency and avg_timer) else 0.75

        # Cognitive State Diagnostics
        # 1. Speed-Inaccuracy Trap: fast clicking/guessing blindly without accurate processing
        if (acc < 0.60 or avg_score < 55) and reaction_ratio < 0.60:
            state = CognitiveFlowState.SPEED_INACCURACY_TRAP
            rec_level = _step_level(current_level, harder=False)
            reason = (
                f"Tốc độ nhanh ({avg_latency:.0f}ms) nhưng độ chính xác thấp ({acc*100:.0f}%) — "
                f"cần giảm áp lực để tái củng cố độ chuẩn xác phát âm."
            )

        # 2. Cognitive Overload: low accuracy / struggling
        elif acc < 0.60 or avg_score < 55:
            state = CognitiveFlowState.COGNITIVE_OVERLOAD
            rec_level = _step_level(current_level, harder=False)
            reason = (
                f"Quá tải nhận thức (độ chính xác {acc*100:.0f}%, điểm TB {avg_score:.0f}) — "
                f"tự động mở rộng thời gian phản xạ để ổn định nhịp nói."
            )

        # 3. Reaction Hesitation: high accuracy but slow reaction > 75% of timer
        elif acc >= 0.80 and reaction_ratio > 0.75:
            state = CognitiveFlowState.REACTION_HESITATION
            rec_level = current_level
            reason = (
                f"Độ chính xác cao ({acc*100:.0f}%) nhưng độ trễ phản xạ còn chậm ({avg_latency:.0f}ms) — "
                f"duy trì cấp độ hiện tại để rèn tính tự động hóa (Automaticity)."
            )

        # 4. Comfort Plateau: high accuracy and fast reaction — learner needs challenge
        elif acc >= 0.80 and avg_score >= 75 and reaction_ratio < 0.65:
            state = CognitiveFlowState.COMFORT_PLATEAU
            rec_level = _step_level(current_level, harder=True)
            reason = (
                f"Vùng an toàn (Độ chính xác {acc*100:.0f}%, phản xạ nhanh {avg_latency:.0f}ms, Elo {rating:.0f}) — "
                f"tăng áp lực thời gian để kích thích phát triển phản xạ sâu."
            )

        # 5. Optimal Flow State
        else:
            state = CognitiveFlowState.FLOW
            rec_level = nearest_level if nearest_level != current_level else current_level
            reason = (
                f"Trạng thái Flow tối ưu (Độ chính xác {acc*100:.0f}%, xác suất kỳ vọng {p_success*100:.0f}%, Elo {rating:.0f}) — "
                f"thời gian phản xạ mục tiêu lý tưởng là {target_timer_ms:.0f}ms."
            )

        # Derive comfort window string
        comfort_win = f"{target_timer_ms/1000:.1f}s (Elo: {rating:.0f})"

        return FlowAssessment(
            current_rating=rating,
            rating_deviation=rd,
            cognitive_state=state,
            recommended_level=rec_level,
            recommended_timer_ms=timer_for_level(rec_level),
            exact_target_timer_ms=target_timer_ms,
            flow_probability=p_success,
            reason=reason,
            comfort_window=comfort_win,
        )


def _filter_comparable(attempts: list[dict[str, Any]], sub_mode: str | None) -> list[dict[str, Any]]:
    if not sub_mode:
        return attempts
    return [a for a in attempts if a.get("sub_mode") == sub_mode or a.get("exercise_type") == sub_mode]


def _step_level(current_level: str, harder: bool) -> str:
    try:
        idx = ADAPTIVE_PRESSURE_ORDER.index(current_level)
    except ValueError:
        idx = 2  # normal
    if harder:
        return ADAPTIVE_PRESSURE_ORDER[min(len(ADAPTIVE_PRESSURE_ORDER) - 1, idx + 1)]
    return ADAPTIVE_PRESSURE_ORDER[max(0, idx - 1)]


def evaluate_flow_state(
    current_level: str,
    recent_attempts: list[dict[str, Any]],
    *,
    sub_mode: str | None = None,
    min_samples: int = 5,
) -> FlowAssessment:
    """Public helper returning structured FlowAssessment."""
    return ZPDFlowEngine.evaluate_flow(
        current_level,
        recent_attempts,
        sub_mode=sub_mode,
        min_samples=min_samples,
    )


def recommend_next_pressure(
    current_level: str,
    recent_attempts: list[dict[str, Any]],
    *,
    sub_mode: str | None = None,
    min_samples: int = 5,
) -> tuple[str, str]:
    """100% backward-compatible function returning (next_level, reason) powered by ZPD Flow Engine."""
    assessment = evaluate_flow_state(
        current_level,
        recent_attempts,
        sub_mode=sub_mode,
        min_samples=min_samples,
    )
    return assessment.recommended_level, assessment.reason


def estimate_pressure_threshold(
    attempts: list[dict[str, Any]],
    min_accuracy: float = 0.75,
) -> dict[str, Any] | None:
    """Derives personal pressure threshold: max pressure (smallest timer) where accuracy stays above min.

    Integrates empirical bucket stability with Elo psychometrics.
    Returns {threshold_level, threshold_ms, stable_until_ms, comfort_window, elo_rating}
    """
    if len(attempts) < 8:
        return None

    # Calculate Elo rating
    rating, _ = ReflexEloEngine.estimate_rating(attempts)
    target_timer_ms = ZPDFlowEngine.calculate_target_timer_ms(rating)

    # Group by timer level empirically
    from collections import defaultdict

    buckets: dict[int, list[dict]] = defaultdict(list)
    for a in attempts:
        tl = int(a.get("timer_limit_ms", 0))
        if tl:
            buckets[tl].append(a)

    sorted_timers = sorted(buckets.keys())
    stable_until = None
    for tl in sorted_timers:
        bucket = buckets[tl]
        if len(bucket) < 3:
            continue
        acc = sum(1 for x in bucket if x.get("success")) / len(bucket)
        if acc >= min_accuracy:
            stable_until = tl
        else:
            break

    if stable_until is None:
        # Fall back to psychometrically calculated target timer
        stable_until = int(round(target_timer_ms, -2))

    try:
        order_timers = [timer_for_level(lvl) for lvl in ADAPTIVE_PRESSURE_ORDER]
        idx = order_timers.index(stable_until) if stable_until in order_timers else -1
        if idx >= 0 and idx + 1 < len(order_timers):
            window = f"{stable_until/1000:.1f}–{order_timers[idx+1]/1000:.1f}s"
        else:
            window = f"~{stable_until/1000:.1f}s"
    except Exception:
        window = f"~{stable_until/1000:.1f}s"

    return {
        "threshold_ms": stable_until,
        "comfort_window": window,
        "stable_until_ms": stable_until,
        "elo_rating": round(rating, 1),
    }

