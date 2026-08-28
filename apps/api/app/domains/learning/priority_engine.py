import math
from datetime import datetime, timezone
from typing import Any

from app.domains.learning.contracts import (
    DifficultyLevel,
    ExerciseType,
    LearningGoalType,
    LearningItemType,
    PriorityScore,
)
from app.domains.learning.models import LearningGoal, LearningItem


class PriorityEngine:
    """Deterministic, explainable scoring engine for ranking learning priorities."""

    # Communication impact weights by skill category
    COMMUNICATION_IMPACT = {
        LearningItemType.GRAMMAR: 0.90,
        LearningItemType.PARTICLE: 0.95,
        LearningItemType.CONJUGATION: 0.85,
        LearningItemType.PRONUNCIATION: 0.85,
        LearningItemType.PITCH_ACCENT: 0.75,
        LearningItemType.POLITENESS: 0.80,
        LearningItemType.NATURALNESS: 0.75,
        LearningItemType.FLUENCY: 0.70,
        LearningItemType.FILLER: 0.60,
        LearningItemType.VOCABULARY: 0.70,
        LearningItemType.WORD_CHOICE: 0.65,
        LearningItemType.SENTENCE_PATTERN: 0.80,
    }

    # Exercise type recommendations by skill category
    RECOMMENDED_EXERCISES = {
        LearningItemType.GRAMMAR: ExerciseType.ROLEPLAY,
        LearningItemType.PARTICLE: ExerciseType.RAPID_RESPONSE,
        LearningItemType.CONJUGATION: ExerciseType.SENTENCE_TRANSFORMATION,
        LearningItemType.PRONUNCIATION: ExerciseType.PRONUNCIATION_REPEAT,
        LearningItemType.PITCH_ACCENT: ExerciseType.PRONUNCIATION_REPEAT,
        LearningItemType.POLITENESS: ExerciseType.ROLEPLAY,
        LearningItemType.NATURALNESS: ExerciseType.OPINION,
        LearningItemType.FLUENCY: ExerciseType.RAPID_RESPONSE,
        LearningItemType.FILLER: ExerciseType.RAPID_RESPONSE,
        LearningItemType.VOCABULARY: ExerciseType.SENTENCE_GENERATION,
        LearningItemType.WORD_CHOICE: ExerciseType.ROLEPLAY,
        LearningItemType.SENTENCE_PATTERN: ExerciseType.SCENARIO,
    }

    @classmethod
    def calculate_item_priority(
        cls,
        item: LearningItem,
        active_goals: list[LearningGoal],
        total_sessions_analyzed: int = 1,
        cooldown_hours: float = 2.0,
    ) -> PriorityScore:
        """
        Calculates normalized deterministic priority score in [0.05, 1.0].
        Provides transparent audit reasons and recommended exercise types.
        """
        try:
            item_type = LearningItemType(item.item_type)
        except ValueError:
            item_type = LearningItemType.GRAMMAR

        # 1. Severity weight
        sev_weight = 0.75
        if item.extra_metadata and "severity" in item.extra_metadata:
            sev = str(item.extra_metadata["severity"]).upper()
            if sev == "MUST_FIX":
                sev_weight = 1.00
            elif sev == "SHOULD_FIX":
                sev_weight = 0.75
            elif sev == "NATIVE_ALTERNATIVE":
                sev_weight = 0.45
            else:
                sev_weight = 0.35

        # 2. Recurrence factor across practice attempts
        attempts = item.attempt_count or 0
        recurrence = min(1.0, max(0.1, math.log2(1 + attempts) / 3.0))

        # 3. Recency factor
        now = datetime.now(timezone.utc)
        if item.last_practiced_at:
            dt = item.last_practiced_at if item.last_practiced_at.tzinfo else item.last_practiced_at.replace(tzinfo=timezone.utc)
            hours_since = (now - dt).total_seconds() / 3600.0
            days_since = hours_since / 24.0

            if hours_since < cooldown_hours:
                # Active cooldown dampener to prevent rapid re-drill fatigue
                recency_factor = 0.30
            elif days_since <= 2:
                recency_factor = 1.00
            elif days_since <= 7:
                recency_factor = 0.85
            elif days_since <= 21:
                recency_factor = 0.70
            else:
                recency_factor = 0.50
        else:
            recency_factor = 1.00  # Brand new item -> high urgency

        # 4. Mastery gap
        mastery = item.overall_mastery if item.overall_mastery is not None else 0.0
        mastery_gap = max(0.05, 1.0 - mastery)

        # 5. Goal relevance matching
        goal_rel = cls.calculate_goal_relevance(item, active_goals)

        # 6. Communication impact
        comm_impact = cls.COMMUNICATION_IMPACT.get(item_type, 0.75)

        # 7. Regression boost
        reg_boost = 0.25 if item.lifecycle == "regressed" else 0.0

        # 8. Uncertainty boost (items with low confidence get higher exploration priority)
        conf = item.confidence if item.confidence is not None else 0.5
        uncertainty_boost = max(0.0, (0.7 - conf) * 0.25)

        # Composite priority formula
        base_priority = (
            (sev_weight * 0.25)
            + (recurrence * 0.15)
            + (recency_factor * 0.15)
            + (mastery_gap * 0.25)
            + (goal_rel * 0.15)
            + (comm_impact * 0.05)
        )

        # Cap boost to 0.3 to avoid ceiling at 1.0 for top 20% (forward fix)
        boost = min(0.30, reg_boost + uncertainty_boost)
        final_score = base_priority * (1.0 + boost)
        final_score = max(0.05, min(1.0, round(final_score, 3)))

        # Recommended exercise type
        rec_exercise = cls.RECOMMENDED_EXERCISES.get(item_type, ExerciseType.ROLEPLAY)

        # Determine difficulty based on mastery
        if item.overall_mastery < 0.35:
            difficulty = DifficultyLevel.EASY
        elif item.overall_mastery < 0.70:
            difficulty = DifficultyLevel.NORMAL
        elif item.overall_mastery < 0.88:
            difficulty = DifficultyLevel.HARD
        else:
            difficulty = DifficultyLevel.CHALLENGE

        # Transparent explanation reason
        reason = cls._build_reason(item, goal_rel, reg_boost > 0)

        return PriorityScore(
            key=item.key,
            item_type=item_type,
            title=item.title,
            priority_score=final_score,
            reason=reason,
            goal_relevance=goal_rel,
            recommended_exercise_type=rec_exercise,
            estimated_minutes=5 if difficulty in (DifficultyLevel.EASY, DifficultyLevel.NORMAL) else 8,
            difficulty=difficulty,
            weakness_factor=sev_weight,
            recurrence_factor=recurrence,
            recency_factor=recency_factor,
            mastery_gap=mastery_gap,
            learning_value=comm_impact,
            uncertainty_boost=uncertainty_boost,
            regression_boost=reg_boost,
        )

    @classmethod
    def calculate_goal_relevance(
        cls,
        item: LearningItem,
        goals: list[LearningGoal],
    ) -> float:
        """Computes matching relevance between item and active user goals."""
        if not goals:
            return 0.60  # Default balanced baseline

        max_rel = 0.40
        key_lower = item.key.lower()
        title_lower = item.title.lower()
        item_type = item.item_type.lower()

        for g in goals:
            if g.status != "active":
                continue
            gt = g.goal_type.lower()

            if gt in ("workplace", "interview"):
                if any(w in key_lower or w in title_lower for w in ("keigo", "polite", "business", "desu", "itadaku", "shite")):
                    max_rel = max(max_rel, 0.95)
                elif item_type in ("politeness", "naturalness"):
                    max_rel = max(max_rel, 0.85)

            elif gt == "pronunciation":
                if item_type in ("pronunciation", "pitch_accent"):
                    max_rel = max(max_rel, 0.95)

            elif gt in ("speaking", "conversation", "fluency"):
                if item_type in ("grammar", "particle", "fluency", "naturalness"):
                    max_rel = max(max_rel, 0.90)

            elif gt == "travel":
                if any(w in key_lower or w in title_lower for w in ("travel", "direction", "hotel", "order", "kudasai")):
                    max_rel = max(max_rel, 0.95)

        return round(max_rel, 2)

    @classmethod
    def _build_reason(cls, item: LearningItem, goal_relevance: float, is_regression: bool) -> str:
        """Generates deterministic, factual reason string for user transparency."""
        mastery_pct = int((item.overall_mastery or 0.0) * 100)
        attempts = item.attempt_count or 0

        if is_regression:
            return f"Lỗi có dấu hiệu tái phát sau khi đã thuần thục (Độ thuần thục hiện tại: {mastery_pct}%)"

        if goal_relevance >= 0.85:
            return f"Trọng tâm trực tiếp cho mục tiêu giao tiếp hiện tại của bạn (Độ thuần thục: {mastery_pct}%)"

        if attempts > 0:
            successes = item.success_count or 0
            return f"Tỷ lệ thành công {successes}/{attempts} lần qua các bài luyện gần đây (Độ thuần thục: {mastery_pct}%)"

        return f"Kỹ năng mới được phát hiện cần củng cố phản xạ tự nhiên (Độ thuần thục: {mastery_pct}%)"

    @classmethod
    def rank_and_balance_priorities(
        cls,
        scores: list[PriorityScore],
        limit: int = 5,
    ) -> list[PriorityScore]:
        """
        Ranks priorities with diversity balancing (avoids recommending only 1 skill type).
        Ensures max 60% of top recommendations are the same item_type.
        """
        sorted_scores = sorted(scores, key=lambda s: s.priority_score, reverse=True)
        balanced: list[PriorityScore] = []
        type_counts: dict[LearningItemType, int] = {}
        max_per_type = max(2, int(limit * 0.60))

        remaining: list[PriorityScore] = []

        for s in sorted_scores:
            cnt = type_counts.get(s.item_type, 0)
            if cnt < max_per_type and len(balanced) < limit:
                balanced.append(s)
                type_counts[s.item_type] = cnt + 1
            else:
                remaining.append(s)

        # Fill remaining slots respecting cap (strict 60%)
        for s in list(remaining):
            if len(balanced) >= limit:
                break
            cnt = type_counts.get(s.item_type, 0)
            if cnt < max_per_type:
                balanced.append(s)
                type_counts[s.item_type] = cnt + 1
                remaining.remove(s)

        return balanced
