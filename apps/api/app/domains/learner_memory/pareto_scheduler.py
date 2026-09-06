"""Multi-Objective Pareto Frontier Spaced Repetition Review Scheduler.

Mathematical Foundations:
- Deb et al. (2002): A fast and elitist multiobjective genetic algorithm: NSGA-II (Non-dominated Sorting & Crowding Distance).
- Settles & Meeder (2016): A trainable spaced repetition model for language learning (Duolingo Half-Life Regression).
- Shannon (1948): Information entropy for category diversity balance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReviewCandidateItem:
    """Individual candidate memory item available for review."""

    item_id: str
    category: str  # e.g., "grammar", "pitch", "keigo", "pronunciation", "vocabulary"
    forgetting_risk: float  # [0.0, 1.0]: 1.0 - R(t), urgency to review
    difficulty: float       # [0.0, 1.0]: cognitive difficulty load
    mastery: float          # [0.0, 1.0]: current mastery level
    metadata: dict[str, Any] = field(default_factory=dict)

    # Multi-objective metrics populated during evaluation
    rank: int = 0
    crowding_distance: float = 0.0


@dataclass
class ParetoReviewPlan:
    """Optimal multi-objective review curriculum."""

    selected_items: list[ReviewCandidateItem]
    total_items: int
    mean_forgetting_risk: float
    category_diversity_entropy: float
    total_cognitive_load: float
    pareto_front_count: int
    category_distribution: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_items": self.total_items,
            "mean_forgetting_risk": round(self.mean_forgetting_risk, 3),
            "category_diversity_entropy": round(self.category_diversity_entropy, 3),
            "total_cognitive_load": round(self.total_cognitive_load, 2),
            "pareto_front_count": self.pareto_front_count,
            "category_distribution": self.category_distribution,
            "item_ids": [item.item_id for item in self.selected_items],
        }


class ParetoReviewScheduler:
    """Multi-objective Pareto optimization engine for spaced repetition review schedules."""

    @classmethod
    def calculate_shannon_entropy(cls, categories: list[str]) -> float:
        """Calculates Shannon diversity entropy H across item categories."""
        if not categories:
            return 0.0

        n = len(categories)
        counts: dict[str, int] = {}
        for cat in categories:
            counts[cat] = counts.get(cat, 0) + 1

        entropy = 0.0
        for count in counts.values():
            p = count / n
            if p > 0:
                entropy -= p * math.log(p)

        return float(entropy)

    @classmethod
    def dominates(cls, a: ReviewCandidateItem, b: ReviewCandidateItem) -> bool:
        """Determines if candidate item `a` Pareto-dominates item `b`.

        Objectives to maximize:
        1. Forgetting Risk (urgency to prevent memory loss).
        2. Mastery Gap (1.0 - mastery, prioritizing unmastered items).
        Objective to minimize (or balanced cognitive load):
        3. Cognitive Fatigue / Overload (preferring manageable difficulty unless high risk).
        """
        # We define 3 maximization criteria for individual item utility:
        # f1: Urgency (forgetting_risk) -> higher is better
        # f2: Mastery Gap (1.0 - mastery) -> higher is better
        # f3: Efficiency-to-load ratio: (forgetting_risk / max(0.1, difficulty)) -> higher is better

        f1_a, f1_b = a.forgetting_risk, b.forgetting_risk
        f2_a, f2_b = 1.0 - a.mastery, 1.0 - b.mastery
        f3_a = a.forgetting_risk / max(0.1, a.difficulty)
        f3_b = b.forgetting_risk / max(0.1, b.difficulty)

        not_worse = (f1_a >= f1_b and f2_a >= f2_b and f3_a >= f3_b)
        strictly_better = (f1_a > f1_b or f2_a > f2_b or f3_a > f3_b)

        return not_worse and strictly_better

    @classmethod
    def fast_non_dominated_sort(
        cls, items: list[ReviewCandidateItem]
    ) -> list[list[ReviewCandidateItem]]:
        """Executes Deb et al.'s Fast Non-dominated Sorting algorithm.

        Returns:
            List of Pareto fronts [Front_0, Front_1, Front_2, ...].
        """
        n = len(items)
        if n == 0:
            return []

        domination_counts = [0] * n
        dominated_items: list[list[int]] = [[] for _ in range(n)]
        fronts: list[list[int]] = [[]]

        for p in range(n):
            for q in range(n):
                if p == q:
                    continue
                if cls.dominates(items[p], items[q]):
                    dominated_items[p].append(q)
                elif cls.dominates(items[q], items[p]):
                    domination_counts[p] += 1

            if domination_counts[p] == 0:
                items[p].rank = 0
                fronts[0].append(p)

        i = 0
        while i < len(fronts) and fronts[i]:
            next_front: list[int] = []
            for p in fronts[i]:
                for q in dominated_items[p]:
                    domination_counts[q] -= 1
                    if domination_counts[q] == 0:
                        items[q].rank = i + 1
                        next_front.append(q)
            i += 1
            if next_front:
                fronts.append(next_front)

        result_fronts: list[list[ReviewCandidateItem]] = []
        for front in fronts:
            if front:
                result_fronts.append([items[idx] for idx in front])

        return result_fronts

    @classmethod
    def calculate_crowding_distance(cls, front: list[ReviewCandidateItem]) -> None:
        """Assigns NSGA-II crowding distance to preserve diversity along the Pareto front."""
        m = len(front)
        if m == 0:
            return
        if m <= 2:
            for item in front:
                item.crowding_distance = float("inf")
            return

        for item in front:
            item.crowding_distance = 0.0

        # Objective 1: Forgetting Risk
        front.sort(key=lambda x: x.forgetting_risk)
        front[0].crowding_distance = float("inf")
        front[-1].crowding_distance = float("inf")
        r_range = max(1e-6, front[-1].forgetting_risk - front[0].forgetting_risk)
        for i in range(1, m - 1):
            front[i].crowding_distance += (front[i + 1].forgetting_risk - front[i - 1].forgetting_risk) / r_range

        # Objective 2: Difficulty
        front.sort(key=lambda x: x.difficulty)
        front[0].crowding_distance = float("inf")
        front[-1].crowding_distance = float("inf")
        d_range = max(1e-6, front[-1].difficulty - front[0].difficulty)
        for i in range(1, m - 1):
            front[i].crowding_distance += (front[i + 1].difficulty - front[i - 1].difficulty) / d_range

    @classmethod
    def schedule_optimal_review(
        cls,
        candidates: list[ReviewCandidateItem],
        budget_k: int = 5,
    ) -> ParetoReviewPlan:
        """Selects the Pareto-optimal subset of review items within budget K."""
        if not candidates or budget_k <= 0:
            return ParetoReviewPlan(
                selected_items=[],
                total_items=0,
                mean_forgetting_risk=0.0,
                category_diversity_entropy=0.0,
                total_cognitive_load=0.0,
                pareto_front_count=0,
                category_distribution={},
            )

        if len(candidates) <= budget_k:
            selected = list(candidates)
        else:
            fronts = cls.fast_non_dominated_sort(candidates)
            selected: list[ReviewCandidateItem] = []

            for front in fronts:
                if len(selected) + len(front) <= budget_k:
                    selected.extend(front)
                else:
                    # Partial front: sort by crowding distance to preserve diversity
                    cls.calculate_crowding_distance(front)
                    front.sort(key=lambda x: x.crowding_distance, reverse=True)
                    needed = budget_k - len(selected)
                    selected.extend(front[:needed])
                    break

        # Compute summary telemetry
        cats = [item.category for item in selected]
        entropy = cls.calculate_shannon_entropy(cats)
        mean_risk = sum(item.forgetting_risk for item in selected) / max(1, len(selected))
        total_load = sum(item.difficulty for item in selected)

        cat_dist: dict[str, int] = {}
        for c in cats:
            cat_dist[c] = cat_dist.get(c, 0) + 1

        return ParetoReviewPlan(
            selected_items=selected,
            total_items=len(selected),
            mean_forgetting_risk=mean_risk,
            category_diversity_entropy=entropy,
            total_cognitive_load=total_load,
            pareto_front_count=len(set(it.rank for it in candidates)),
            category_distribution=cat_dist,
        )
