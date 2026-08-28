from datetime import datetime, timezone
import pytest

from app.domains.learning.contracts import DifficultyLevel, ExerciseType, LearningGoalType, LearningItemType, PriorityScore
from app.domains.learning.models import LearningGoal, LearningItem
from app.domains.learning.priority_engine import PriorityEngine


def test_priority_calculation_severity_and_mastery_gap():
    item_urgent = LearningItem(
        user_id="user_1",
        key="grammar.わけではない",
        item_type="grammar",
        title="〜わけではない",
        overall_mastery=0.25,
        confidence=0.8,
        attempt_count=6,
        extra_metadata={"severity": "MUST_FIX"},
    )
    goals = [LearningGoal(user_id="user_1", title="Workplace Japanese", goal_type="workplace", status="active")]

    score_urgent = PriorityEngine.calculate_item_priority(item_urgent, goals)

    item_mastered = LearningItem(
        user_id="user_1",
        key="grammar.desu_masu",
        item_type="grammar",
        title="です・ます",
        overall_mastery=0.92,
        confidence=0.9,
        attempt_count=15,
        extra_metadata={"severity": "NATIVE_ALTERNATIVE"},
    )
    score_mastered = PriorityEngine.calculate_item_priority(item_mastered, goals)

    assert score_urgent.priority_score > score_mastered.priority_score
    assert score_urgent.priority_score >= 0.50


def test_priority_goal_relevance_boost():
    goals = [LearningGoal(user_id="user_1", title="Keigo and Workplace", goal_type="workplace", status="active")]

    item_keigo = LearningItem(
        user_id="user_1",
        key="politeness.keigo_switching",
        item_type="politeness",
        title="Kính ngữ công sở",
        overall_mastery=0.40,
        confidence=0.7,
        attempt_count=2,
    )
    score_keigo = PriorityEngine.calculate_item_priority(item_keigo, goals)

    item_travel = LearningItem(
        user_id="user_1",
        key="vocabulary.airport_terms",
        item_type="vocabulary",
        title="Từ vựng sân bay",
        overall_mastery=0.40,
        confidence=0.7,
        attempt_count=2,
    )
    score_travel = PriorityEngine.calculate_item_priority(item_travel, goals)

    assert score_keigo.goal_relevance > score_travel.goal_relevance
    assert score_keigo.priority_score > score_travel.priority_score


def test_priority_regression_boost():
    goals = []
    item_normal = LearningItem(
        user_id="user_1",
        key="particle.ha_vs_ga",
        item_type="particle",
        title="は vs が",
        overall_mastery=0.50,
        confidence=0.8,
        lifecycle="improving",
    )
    item_regressed = LearningItem(
        user_id="user_1",
        key="particle.ha_vs_ga",
        item_type="particle",
        title="は vs が",
        overall_mastery=0.50,
        confidence=0.8,
        lifecycle="regressed",
    )

    s_normal = PriorityEngine.calculate_item_priority(item_normal, goals)
    s_reg = PriorityEngine.calculate_item_priority(item_regressed, goals)

    assert s_reg.priority_score > s_normal.priority_score
    assert s_reg.regression_boost > 0


def test_rank_and_balance_diversity():
    scores = [
        PriorityScore(key=f"grammar.{i}", item_type=LearningItemType.GRAMMAR, title=f"G{i}", priority_score=0.90 - i*0.01, reason="")
        for i in range(6)
    ]
    scores.append(PriorityScore(key="pron.1", item_type=LearningItemType.PRONUNCIATION, title="P1", priority_score=0.75, reason=""))
    scores.append(PriorityScore(key="fluency.1", item_type=LearningItemType.FLUENCY, title="F1", priority_score=0.70, reason=""))

    balanced = PriorityEngine.rank_and_balance_priorities(scores, limit=5)
    types_in_top5 = [s.item_type for s in balanced]

    assert len(balanced) == 5
    assert LearningItemType.PRONUNCIATION in types_in_top5
