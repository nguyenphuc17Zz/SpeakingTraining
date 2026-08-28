import pytest

from app.domains.learning.contracts import ExerciseResult, IndependenceLevel, LearningItemLifecycle
from app.domains.learning.mastery_engine import MasteryEngine
from app.domains.learning.models import LearningItem


def test_mastery_delta_saturation():
    # Low initial mastery gets healthy gain
    item_low = LearningItem(
        user_id="u1", key="k1", item_type="grammar", title="t1",
        overall_mastery=0.20, spontaneous_mastery=0.20, production_mastery=0.20
    )
    res_success = ExerciseResult(
        exercise_id="ex1", user_id="u1", score=90.0, success=True,
        confidence=0.9, feedback="Good", independence=IndependenceLevel.INDEPENDENT
    )
    delta_low = MasteryEngine.calculate_mastery_delta(res_success, item_low, dimension="spontaneous")

    # High initial mastery gets smaller saturated gain
    item_high = LearningItem(
        user_id="u1", key="k1", item_type="grammar", title="t1",
        overall_mastery=0.88, spontaneous_mastery=0.88, production_mastery=0.88
    )
    delta_high = MasteryEngine.calculate_mastery_delta(res_success, item_high, dimension="spontaneous")

    assert delta_low > 0
    assert delta_high > 0
    assert delta_low > delta_high


def test_mastery_independence_weighting():
    item = LearningItem(
        user_id="u1", key="k1", item_type="grammar", title="t1",
        overall_mastery=0.40, spontaneous_mastery=0.40
    )

    res_indep = ExerciseResult(
        exercise_id="ex1", user_id="u1", score=85.0, success=True,
        confidence=0.9, feedback="Good", independence=IndependenceLevel.INDEPENDENT
    )
    res_scaffold = ExerciseResult(
        exercise_id="ex1", user_id="u1", score=85.0, success=True,
        confidence=0.9, feedback="Good", independence=IndependenceLevel.SCAFFOLDED
    )

    d_indep = MasteryEngine.calculate_mastery_delta(res_indep, item, dimension="spontaneous")
    d_scaffold = MasteryEngine.calculate_mastery_delta(res_scaffold, item, dimension="spontaneous")

    assert d_indep > d_scaffold


def test_multidimensional_mastery_calculation():
    overall = MasteryEngine.calculate_multidimensional_mastery(
        recognition=0.90,
        production=0.80,
        spontaneous=0.70,
        context_variety_score=0.75,
    )
    assert 0.70 <= overall <= 0.85


def test_mastery_decay():
    # Fresh item <= 3 days -> no decay
    assert MasteryEngine.apply_decay(0.80, days_since_practice=2, lifecycle="active") == 0.80

    # Active item 20 days -> moderate decay
    decayed_active = MasteryEngine.apply_decay(0.80, days_since_practice=20, lifecycle="active")
    assert decayed_active < 0.80

    # Maintenance item 20 days -> slower decay
    decayed_maint = MasteryEngine.apply_decay(0.80, days_since_practice=20, lifecycle="maintenance")
    assert decayed_maint > decayed_active


def test_lifecycle_state_transitions():
    # Progressing to mastered
    state = MasteryEngine.evaluate_lifecycle_transition(
        current_lifecycle="improving",
        overall_mastery=0.88,
        spontaneous_mastery=0.82,
        attempt_count=6,
        independent_success_count=5,
        context_variety_count=3,
        recent_has_failure=False,
    )
    assert state == LearningItemLifecycle.MASTERED.value

    # Mastered with regression
    state_reg = MasteryEngine.evaluate_lifecycle_transition(
        current_lifecycle="mastered",
        overall_mastery=0.60,
        spontaneous_mastery=0.55,
        attempt_count=7,
        independent_success_count=5,
        context_variety_count=3,
        recent_has_failure=True,
    )
    assert state_reg == LearningItemLifecycle.REGRESSED.value
