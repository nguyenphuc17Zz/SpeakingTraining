import pytest
from app.domains.ramp.scaffold_controller import ScaffoldController


def test_pid_scaffold_fading_on_consecutive_success():
    """Verify PID controller fades scaffolding smoothly upon consistent high scores."""
    # Current level 5 (Structure outline). Learner scores 90%, 92%, 95%
    history = [90.0, 92.0, 95.0]
    decision = ScaffoldController.calculate_pid_support(current_level=5, performance_history=history)

    assert decision.recommended_level < 5
    assert decision.control_signal < 0  # Negative error -> reduce support
    assert "Fading scaffold" in decision.reason


def test_pid_scaffold_restore_on_consecutive_struggle():
    """Verify PID controller increases scaffolding support when learner struggles (<60%)."""
    # Current level 2 (Keywords). Learner struggles with 45%, 50%
    history = [45.0, 50.0]
    decision = ScaffoldController.calculate_pid_support(current_level=2, performance_history=history)

    assert decision.recommended_level > 2
    assert decision.control_signal > 0  # Positive error -> increase support
    assert "Cognitive strain detected" in decision.reason


def test_pid_scaffold_stability_in_zpd_flow():
    """Verify PID controller maintains current level when performance is near target (75%)."""
    # Current level 3 (Guided questions). Learner scores 74%, 76%, 75%
    history = [74.0, 76.0, 75.0]
    decision = ScaffoldController.calculate_pid_support(current_level=3, performance_history=history)

    assert decision.recommended_level == 3
    assert abs(decision.control_signal) < 0.35
    assert "ZPD flow state" in decision.reason
