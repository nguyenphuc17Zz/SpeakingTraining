"""Unit tests for Reflex Arena SOTA Dynamic Difficulty Adaptation (Elo/Glicko-2 & ZPD Flow Engine)."""

from app.domains.reflex.adaptive_pressure import (
    CognitiveFlowState,
    ReflexEloEngine,
    ZPDFlowEngine,
    estimate_pressure_threshold,
    evaluate_flow_state,
    recommend_next_pressure,
)
from app.domains.reflex.pressure_profiles import PressureLevel


def test_timer_to_difficulty_monotonicity():
    """Shorter timer limits should yield strictly higher difficulty ratings."""
    diff_extreme = ReflexEloEngine.timer_to_difficulty(1800)
    diff_reflex = ReflexEloEngine.timer_to_difficulty(2500)
    diff_fast = ReflexEloEngine.timer_to_difficulty(3000)
    diff_normal = ReflexEloEngine.timer_to_difficulty(4000)
    diff_relaxed = ReflexEloEngine.timer_to_difficulty(6000)

    assert diff_extreme > diff_reflex > diff_fast > diff_normal > diff_relaxed
    assert diff_normal == 1200.0  # reference calibration


def test_elo_rating_growth_with_speed_and_accuracy():
    """Consistent rapid, accurate answers should significantly increase Elo rating."""
    fast_success_attempts = [
        {"success": True, "score": 95, "reaction_latency_ms": 1100, "timer_limit_ms": 3000}
        for _ in range(10)
    ]
    rating, rd = ReflexEloEngine.estimate_rating(fast_success_attempts)
    assert rating > 1300.0
    assert rd < 350.0  # uncertainty decreased


def test_elo_rating_drop_with_repeated_failures():
    """Repeated failures on standard tasks should decrease Elo rating."""
    failed_attempts = [
        {"success": False, "score": 20, "reaction_latency_ms": 4000, "timer_limit_ms": 4000}
        for _ in range(8)
    ]
    rating, rd = ReflexEloEngine.estimate_rating(failed_attempts)
    assert rating < 1100.0
    assert rd < 350.0


def test_target_timer_scaling():
    """High Elo learner should receive tighter millisecond limits than a novice."""
    timer_novice = ZPDFlowEngine.calculate_target_timer_ms(1000.0)
    timer_intermediate = ZPDFlowEngine.calculate_target_timer_ms(1400.0)
    timer_expert = ZPDFlowEngine.calculate_target_timer_ms(1800.0)

    assert timer_novice > timer_intermediate > timer_expert
    assert 1500.0 <= timer_expert <= 2500.0
    assert 3500.0 <= timer_novice <= 6500.0


def test_flow_state_comfort_plateau():
    """Learners breezing through exercises should be diagnosed in Comfort Plateau and pushed harder."""
    mastered_attempts = [
        {"success": True, "score": 92, "reaction_latency_ms": 1200, "timer_limit_ms": 3000}
        for _ in range(6)
    ]
    assessment = evaluate_flow_state(PressureLevel.FAST.value, mastered_attempts)

    assert assessment.cognitive_state == CognitiveFlowState.COMFORT_PLATEAU
    assert assessment.recommended_level in (PressureLevel.REFLEX.value, PressureLevel.EXTREME.value)
    assert "Vùng an toàn" in assessment.reason
    assert assessment.current_rating > 1250.0


def test_flow_state_cognitive_overload():
    """Learners struggling with high error rate should receive timer expansion."""
    overloaded_attempts = [
        {"success": False, "score": 40, "reaction_latency_ms": 2800, "timer_limit_ms": 2500}
        for _ in range(6)
    ]
    assessment = evaluate_flow_state(PressureLevel.REFLEX.value, overloaded_attempts)

    assert assessment.cognitive_state == CognitiveFlowState.COGNITIVE_OVERLOAD
    assert assessment.recommended_level in (PressureLevel.FAST.value, PressureLevel.NORMAL.value)
    assert "Quá tải nhận thức" in assessment.reason


def test_speed_inaccuracy_trap():
    """Rushing and answering incorrectly must NOT reward speed; it should slow the timer down."""
    blind_rushing_attempts = [
        {"success": False, "score": 30, "reaction_latency_ms": 800, "timer_limit_ms": 3000}
        for _ in range(6)
    ]
    assessment = evaluate_flow_state(PressureLevel.FAST.value, blind_rushing_attempts)

    assert assessment.cognitive_state == CognitiveFlowState.SPEED_INACCURACY_TRAP
    assert assessment.recommended_level == PressureLevel.NORMAL.value
    assert "nhanh" in assessment.reason and "thấp" in assessment.reason


def test_reaction_hesitation():
    """High accuracy with sluggish reaction should maintain current tier to drill automaticity."""
    hesitant_attempts = [
        {"success": True, "score": 85, "reaction_latency_ms": 2600, "timer_limit_ms": 3000}
        for _ in range(6)
    ]
    assessment = evaluate_flow_state(PressureLevel.FAST.value, hesitant_attempts)

    assert assessment.cognitive_state == CognitiveFlowState.REACTION_HESITATION
    assert assessment.recommended_level == PressureLevel.FAST.value
    assert "chậm" in assessment.reason or "Automaticity" in assessment.reason


def test_recommend_next_pressure_backward_compatibility():
    """Legacy recommend_next_pressure interface returns valid tuple[str, str]."""
    attempts = [
        {"success": True, "score": 88, "reaction_latency_ms": 1300, "timer_limit_ms": 3000}
        for _ in range(6)
    ]
    next_level, reason = recommend_next_pressure(PressureLevel.NORMAL.value, attempts)

    assert isinstance(next_level, str)
    assert isinstance(reason, str)
    assert len(reason) > 10


def test_estimate_pressure_threshold():
    """Legacy estimate_pressure_threshold derives stable timer and includes Elo rating."""
    varied_attempts = [
        {"success": True, "score": 85, "timer_limit_ms": 4000} for _ in range(5)
    ] + [
        {"success": True, "score": 80, "timer_limit_ms": 3000} for _ in range(4)
    ] + [
        {"success": False, "score": 40, "timer_limit_ms": 1800} for _ in range(3)
    ]

    threshold = estimate_pressure_threshold(varied_attempts)
    assert threshold is not None
    assert "threshold_ms" in threshold
    assert "comfort_window" in threshold
    assert "elo_rating" in threshold
    assert threshold["elo_rating"] > 0


def test_insufficient_samples():
    """Fewer than min_samples returns INSUFFICIENT_DATA and preserves current level."""
    few_attempts = [
        {"success": True, "score": 90, "reaction_latency_ms": 1200, "timer_limit_ms": 3000}
        for _ in range(2)
    ]
    assessment = evaluate_flow_state(PressureLevel.NORMAL.value, few_attempts, min_samples=5)

    assert assessment.cognitive_state == CognitiveFlowState.INSUFFICIENT_DATA
    assert assessment.recommended_level == PressureLevel.NORMAL.value
    assert "thêm dữ liệu" in assessment.reason
