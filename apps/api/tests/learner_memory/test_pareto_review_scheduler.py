import pytest

from app.domains.learner_memory.pareto_scheduler import (
    ParetoReviewScheduler,
    ReviewCandidateItem,
)


def test_pareto_domination_and_sorting():
    # Item A: High urgency (0.9), low mastery (0.2), low difficulty (0.3) -> very attractive
    item_a = ReviewCandidateItem("item_a", "grammar", forgetting_risk=0.9, difficulty=0.3, mastery=0.2)
    # Item B: Low urgency (0.3), high mastery (0.8), high difficulty (0.8) -> clearly dominated by A
    item_b = ReviewCandidateItem("item_b", "grammar", forgetting_risk=0.3, difficulty=0.8, mastery=0.8)
    # Item C: Moderate urgency (0.6), moderate mastery (0.5), low difficulty (0.2)
    item_c = ReviewCandidateItem("item_c", "pitch", forgetting_risk=0.6, difficulty=0.2, mastery=0.5)

    assert ParetoReviewScheduler.dominates(item_a, item_b) is True
    assert ParetoReviewScheduler.dominates(item_b, item_a) is False

    fronts = ParetoReviewScheduler.fast_non_dominated_sort([item_a, item_b, item_c])
    assert len(fronts) >= 2
    # Front 0 should contain item_a
    front_0_ids = [it.item_id for it in fronts[0]]
    assert "item_a" in front_0_ids


def test_crowding_distance_and_entropy():
    # Single category: entropy should be 0.0
    h_single = ParetoReviewScheduler.calculate_shannon_entropy(["grammar", "grammar", "grammar"])
    assert h_single == 0.0

    # Multi-category uniform: entropy should be high
    h_multi = ParetoReviewScheduler.calculate_shannon_entropy(["grammar", "pitch", "keigo", "vocab"])
    assert h_multi > 1.2

    # Crowding distance boundary test
    items = [
        ReviewCandidateItem("1", "grammar", 0.1, 0.2, 0.5),
        ReviewCandidateItem("2", "pitch", 0.5, 0.5, 0.5),
        ReviewCandidateItem("3", "keigo", 0.9, 0.8, 0.5),
    ]
    ParetoReviewScheduler.calculate_crowding_distance(items)
    # Extremes should have infinite distance
    assert items[0].crowding_distance == float("inf")
    assert items[-1].crowding_distance == float("inf")
    assert items[1].crowding_distance > 0.0


def test_schedule_optimal_review_budget():
    candidates = [
        ReviewCandidateItem(f"item_{i}", cat, risk, diff, mastery)
        for i, (cat, risk, diff, mastery) in enumerate([
            ("grammar", 0.95, 0.4, 0.1),
            ("pitch", 0.88, 0.3, 0.2),
            ("keigo", 0.82, 0.5, 0.25),
            ("vocab", 0.75, 0.2, 0.3),
            ("situations", 0.70, 0.6, 0.4),
            ("grammar", 0.40, 0.7, 0.7),
            ("pitch", 0.30, 0.5, 0.8),
            ("keigo", 0.25, 0.6, 0.85),
            ("vocab", 0.20, 0.3, 0.9),
            ("grammar", 0.15, 0.8, 0.95),
        ])
    ]

    budget = 4
    plan = ParetoReviewScheduler.schedule_optimal_review(candidates, budget_k=budget)

    assert plan.total_items == budget
    assert len(plan.selected_items) == budget
    # The selected items should come from the top high-urgency/low-mastery items
    selected_ids = set(plan.to_dict()["item_ids"])
    assert "item_0" in selected_ids
    assert "item_1" in selected_ids
    assert plan.mean_forgetting_risk > 0.70
    assert plan.category_diversity_entropy > 0.5
