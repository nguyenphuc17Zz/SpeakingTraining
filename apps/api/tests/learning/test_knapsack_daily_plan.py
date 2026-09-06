import pytest

from app.domains.learning.exercise_variety_policy import ExerciseVarietyPolicy
from app.domains.learning.mastery_engine import MasteryEngine
from app.domains.learning.contracts import IndependenceLevel


def test_knapsack_slot_allocation_various_budgets():
    """Verifies that Knapsack slot allocation works dynamically across different budgets."""
    for budget in [10, 15, 20, 25, 30, 45, 60]:
        slots = ExerciseVarietyPolicy.allocate_time_slots(budget)
        assert len(slots) >= 2
        total_time = sum(s["estimated_minutes"] for s in slots)
        assert total_time <= budget + 2  # Allow small slack
        # Speaking-first check: must contain conversation or drill
        types = {s["slot_type"] for s in slots}
        assert "conversation" in types or "targeted_drill" in types


def test_knapsack_slot_allocation_with_focus_bias():
    """Verifies that pronunciation bias yields dedicated pronunciation slots."""
    slots = ExerciseVarietyPolicy.allocate_time_slots(30, focus_bias="pronunciation")
    pron_slots = [s for s in slots if s["slot_type"] == "pronunciation"]
    assert len(pron_slots) >= 1


def test_bayesian_knowledge_tracing_progression():
    """Verifies BKT posterior updates correctly upon consecutive successes."""
    prior = 0.20
    # Success on independent attempt
    p1 = MasteryEngine.update_bkt_probability(prior, success=True, independence=IndependenceLevel.INDEPENDENT)
    assert p1 > prior

    # Another success
    p2 = MasteryEngine.update_bkt_probability(p1, success=True, independence=IndependenceLevel.INDEPENDENT)
    assert p2 > p1

    # Failure reduces probability
    p3 = MasteryEngine.update_bkt_probability(p2, success=False, independence=IndependenceLevel.INDEPENDENT)
    assert p3 < p2
