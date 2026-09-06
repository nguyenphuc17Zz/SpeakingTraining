import pytest
from app.domains.situations.goal_engine import GoalEngine


def test_dag_parallel_goals_and_concurrent_firing():
    """Verify non-linear DAG allows parallel goals to complete in any order or simultaneously."""
    # Scenario: Restaurant order.
    # Goal 1: Ask recommendation (root)
    # Goal 2: Order drink (depends on Goal 1)
    # Goal 3: Order food (depends on Goal 1) -> Can be done parallel to Goal 2!
    # Goal 4: Checkout (depends on BOTH Goal 2 and Goal 3)
    goals = [
        {"id": "g_rec", "required_intent": "ASK_RECOMMENDATION", "depends_on": []},
        {"id": "g_drink", "required_intent": "ORDER_DRINK", "depends_on": ["g_rec"]},
        {"id": "g_food", "required_intent": "ORDER_FOOD", "depends_on": ["g_rec"]},
        {"id": "g_pay", "required_intent": "CONFIRM", "depends_on": ["g_drink", "g_food"]},
    ]

    engine = GoalEngine(goals)

    # Initial enabled goals: only g_rec
    enabled = [g["id"] for g in engine.get_enabled_goals()]
    assert enabled == ["g_rec"]

    # Step 1: Fire ASK_RECOMMENDATION
    engine.update({"intent": "ASK_RECOMMENDATION"}, [], "おすすめは何ですか")
    assert engine._find_goal("g_rec")["status"] == "COMPLETED"

    # Step 2: Now both g_drink AND g_food are enabled in parallel
    enabled = [g["id"] for g in engine.get_enabled_goals()]
    assert "g_drink" in enabled
    assert "g_food" in enabled
    assert "g_pay" not in enabled  # g_pay blocked until both completed

    # Step 3: Complete g_food first (order food before drink)
    engine.update({"intent": "ORDER_FOOD"}, [], "ラーメンをください")
    assert engine._find_goal("g_food")["status"] == "COMPLETED"
    assert engine._find_goal("g_drink")["status"] != "COMPLETED"
    assert "g_pay" not in [g["id"] for g in engine.get_enabled_goals()]

    # Step 4: Complete g_drink
    engine.update({"intent": "ORDER_DRINK"}, [], "緑茶をお願いします")
    assert engine._find_goal("g_drink")["status"] == "COMPLETED"

    # Step 5: Now g_pay is unlocked!
    assert "g_pay" in [g["id"] for g in engine.get_enabled_goals()]
    engine.update({"intent": "CONFIRM"}, [], "お会計をお願いします")
    assert engine.completion_rate() == 1.0


def test_deadlock_detection_and_recovery_guidance():
    """Verify engine flags deadlock after 3 unproductive turns and provides recovery hints."""
    goals = [
        {"id": "g1", "required_intent": "ASK_RECOMMENDATION", "required_entity": "メニュー", "depends_on": []}
    ]
    engine = GoalEngine(goals)

    assert not engine.is_deadlocked()

    # 3 off-topic turns
    engine.update({"intent": "GREETING"}, [], "こんにちは")
    engine.update({"intent": "SMALL_TALK"}, [], "今日はいい天気ですね")
    engine.update({"intent": "SMALL_TALK"}, [], "そうですね")

    assert engine.is_deadlocked()
    recs = engine.get_recovery_recommendations()
    assert len(recs) == 1
    assert recs[0]["goal_id"] == "g1"
    assert "メニュー" in recs[0]["scaffold_hint"]
