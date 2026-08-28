import pytest

from app.domains.learning.exercise_variety_policy import ExerciseVarietyPolicy


def test_time_slot_allocation():
    # 10 min session -> 2 slots
    slots_10 = ExerciseVarietyPolicy.allocate_time_slots(10)
    assert len(slots_10) == 2
    assert sum(s["estimated_minutes"] for s in slots_10) == 10

    # 30 min session -> 5 slots (conversation, drill, pronunciation, review, exploration)
    slots_30 = ExerciseVarietyPolicy.allocate_time_slots(30)
    assert len(slots_30) == 5
    assert sum(s["estimated_minutes"] for s in slots_30) == 30

    slot_types = [s["slot_type"] for s in slots_30]
    assert "conversation" in slot_types
    assert "pronunciation" in slot_types
    assert "review" in slot_types


def test_exercise_signature_and_deduplication():
    sig1 = ExerciseVarietyPolicy.compute_exercise_signature(
        exercise_type="roleplay",
        target_patterns=["わけではない"],
        difficulty="normal",
        scenario_topic="workplace meeting",
    )
    sig2 = ExerciseVarietyPolicy.compute_exercise_signature(
        exercise_type="roleplay",
        target_patterns=["わけではない"],
        difficulty="normal",
        scenario_topic="workplace meeting",
    )
    sig_diff = ExerciseVarietyPolicy.compute_exercise_signature(
        exercise_type="roleplay",
        target_patterns=["わけではない"],
        difficulty="hard",
        scenario_topic="weekend plan",
    )

    assert sig1 == sig2
    assert sig1 != sig_diff
    assert ExerciseVarietyPolicy.is_duplicate(sig1, [sig2, "other_sig"]) is True
