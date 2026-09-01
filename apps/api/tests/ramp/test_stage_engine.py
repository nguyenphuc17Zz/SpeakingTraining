"""Tests for RampStageEngine (deterministic progression and support fading)."""

import pytest
from app.domains.ramp.contracts import RampSupportLevel
from app.domains.ramp.stage_engine import RampStageEngine


def test_stage_advancement_requires_minimum_attempts():
    engine = RampStageEngine()
    # 4 attempts (less than window of 5)
    buffer = [
        {"success": True, "score": 85.0, "independence_level": "independent"},
        {"success": True, "score": 90.0, "independence_level": "independent"},
        {"success": True, "score": 80.0, "independence_level": "independent"},
        {"success": True, "score": 85.0, "independence_level": "independent"},
    ]
    new_stage, reason = engine.evaluate_stage_change(current_stage=2, stage_attempt_buffer=buffer)
    assert new_stage == 2
    assert reason == "insufficient_data"


def test_stage_advancement_on_high_success_rate():
    engine = RampStageEngine()
    # 5 attempts with 80% success (>= 75%)
    buffer = [
        {"success": True, "score": 80.0, "independence_level": "independent"},
        {"success": True, "score": 85.0, "independence_level": "independent"},
        {"success": True, "score": 75.0, "independence_level": "independent"},
        {"success": True, "score": 90.0, "independence_level": "independent"},
        {"success": False, "score": 40.0, "independence_level": "scaffolded"},
    ]
    new_stage, reason = engine.evaluate_stage_change(current_stage=2, stage_attempt_buffer=buffer)
    assert new_stage == 3
    assert "high_success_rate" in reason


def test_stage_retreat_on_low_success_rate():
    engine = RampStageEngine()
    # 5 attempts with 20% success (<= 35%)
    buffer = [
        {"success": False, "score": 30.0, "independence_level": "scaffolded"},
        {"success": False, "score": 40.0, "independence_level": "scaffolded"},
        {"success": False, "score": 35.0, "independence_level": "scaffolded"},
        {"success": True, "score": 65.0, "independence_level": "assisted_hint"},
        {"success": False, "score": 20.0, "independence_level": "scaffolded"},
    ]
    new_stage, reason = engine.evaluate_stage_change(current_stage=4, stage_attempt_buffer=buffer)
    assert new_stage == 3
    assert "low_success_rate" in reason


def test_stage_ceiling_and_floor():
    engine = RampStageEngine()
    high_success = [{"success": True, "score": 90.0, "independence_level": "independent"}] * 5
    low_success = [{"success": False, "score": 20.0, "independence_level": "scaffolded"}] * 5

    # Stage 10 cannot advance beyond 10
    stage, _ = engine.evaluate_stage_change(current_stage=10, stage_attempt_buffer=high_success)
    assert stage == 10

    # Stage 0 cannot retreat below 0
    stage, _ = engine.evaluate_stage_change(current_stage=0, stage_attempt_buffer=low_success)
    assert stage == 0


def test_support_fading_on_independent_success():
    engine = RampStageEngine()
    buffer = [
        {"success": True, "score": 85.0, "independence_level": "independent"},
        {"success": True, "score": 90.0, "independence_level": "independent"},
        {"success": True, "score": 80.0, "independence_level": "assisted_hint"},
        {"success": True, "score": 85.0, "independence_level": "independent"},
        {"success": True, "score": 95.0, "independence_level": "independent"},
    ]
    new_support, reason = engine.evaluate_support_change(
        current_support=RampSupportLevel.KEYWORDS.value,
        stage_attempt_buffer=buffer,
        current_stage=3,
    )
    # Fades from KEYWORDS (2) to TOPIC_ONLY (1)
    assert new_support == RampSupportLevel.TOPIC_ONLY.value
    assert "fade_support" in reason


def test_support_restoration_on_failure():
    engine = RampStageEngine()
    buffer = [
        {"success": False, "score": 30.0, "independence_level": "scaffolded"},
        {"success": False, "score": 40.0, "independence_level": "scaffolded"},
        {"success": False, "score": 35.0, "independence_level": "scaffolded"},
        {"success": False, "score": 25.0, "independence_level": "scaffolded"},
        {"success": True, "score": 60.0, "independence_level": "assisted_hint"},
    ]
    new_support, reason = engine.evaluate_support_change(
        current_support=RampSupportLevel.KEYWORDS.value,
        stage_attempt_buffer=buffer,
        current_stage=3,
    )
    # Restores from KEYWORDS (2) to GUIDED_QUESTION (3)
    assert new_support == RampSupportLevel.GUIDED_QUESTION.value
    assert "restore_support" in reason
