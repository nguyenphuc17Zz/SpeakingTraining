import math
from datetime import datetime, timedelta, timezone

from app.domains.learning.contracts import (
    ExerciseResult,
    IndependenceLevel,
    LearningItemLifecycle,
    ReviewDecision,
)
from app.domains.learning.mastery_engine import MasteryEngine
from app.domains.learning.models import LearningItem


class FSRSEngine:
    """
    World SOTA Memory Engine: Free Spaced Repetition Scheduler (FSRS-5).
    Based on the DSR (Difficulty, Stability, Retrievability) cognitive memory model.
    References:
      - Jarrett Ye (2023-2024), FSRS algorithm adopted by Anki.
      - Bjork & Bjork (1994), Desirable Difficulty Principle.
    """

    REQUESTED_RETENTION: float = 0.90  # 90% target retention rate

    @staticmethod
    def calculate_retrievability(elapsed_days: float, stability: float) -> float:
        """
        Computes probability of successful recall/production R at elapsed time t.
        Exponential forgetting curve: R(t, S) = 0.9^(t / S)
        """
        if stability <= 0.05:
            return 0.10
        if elapsed_days <= 0.0:
            return 1.0
        power = elapsed_days / stability
        # Prevent numerical underflow
        if power > 30.0:
            return 0.01
        return min(1.0, max(0.01, round(math.pow(0.90, power), 4)))

    @staticmethod
    def calculate_next_difficulty(current_difficulty: float, grade: int) -> float:
        """
        Difficulty D in [1.0, 10.0]. Grade: 1 (Fail), 2 (Assisted), 3 (Good), 4 (Easy).
        Mean reversion prevents runaway difficulty extremes.
        """
        # Grade delta: Grade 3 -> delta 0, Grade 4 -> delta -0.6, Grade 1 -> delta +1.0
        delta = -0.6 * (grade - 3.0)
        updated = current_difficulty + delta
        # Slight mean reversion toward 5.0
        reverted = 0.85 * updated + 0.15 * 5.0
        return min(10.0, max(1.0, round(reverted, 2)))

    @classmethod
    def calculate_next_stability(
        cls,
        current_stability: float,
        difficulty: float,
        retrievability: float,
        grade: int,
    ) -> float:
        """
        Updates memory stability S based on attempt performance and retrievability.
        Incorporate Desirable Difficulty: reviewing when R is lower yields a larger stability boost!
        """
        # 1. Lapse / Failed review
        if grade <= 1:
            lapse_s = max(1.0, round(current_stability * 0.25, 1))
            return min(lapse_s, current_stability)

        # 2. Desirable difficulty multiplier
        # When R is lower, (1.0 - R) is higher, so exp factor > 1
        r_deficit = max(0.0, min(1.0, 1.0 - retrievability))
        desirable_factor = math.exp(0.85 * r_deficit) - 1.0

        # Difficulty resistance: easier items (low D) grow stability faster
        difficulty_weight = max(1.0, 11.0 - difficulty)

        # Scale by previous stability
        power_s = math.pow(max(0.5, current_stability), -0.22)

        boost = 1.0 + 0.35 * difficulty_weight * power_s * desirable_factor

        # Grade factor
        grade_multiplier = 0.80 if grade == 2 else 1.05 if grade == 3 else 1.45

        new_stability = max(current_stability + 1.0, current_stability * boost * grade_multiplier)
        return min(180.0, round(new_stability, 1))

    @classmethod
    def compute_optimal_interval(cls, stability: float) -> int:
        """Calculates optimal days until next review for requested retention rate."""
        if cls.REQUESTED_RETENTION == 0.90:
            return max(1, int(round(stability)))
        factor = math.log(cls.REQUESTED_RETENTION) / math.log(0.90)
        return max(1, int(round(stability * factor)))


class ReviewScheduler:
    """Spaced repetition scheduler customized for speaking and spontaneous language production with FSRS-5."""

    @classmethod
    def schedule_next_review(
        cls,
        item: LearningItem,
        result: ExerciseResult,
    ) -> ReviewDecision:
        """
        Computes next review timestamp and interval based on attempt performance,
        independence level, and FSRS-5 cognitive memory dynamics.
        """
        now = datetime.now(timezone.utc)
        curr_streak = item.review_streak

        # Derive initial stability and difficulty from item state
        current_stability = float(item.review_interval_days) if item.review_interval_days > 0 else 1.0
        current_difficulty = 5.0
        if item.extra_metadata and isinstance(item.extra_metadata, dict):
            current_difficulty = float(item.extra_metadata.get("fsrs_difficulty", 5.0))
            current_stability = float(item.extra_metadata.get("fsrs_stability", current_stability))

        # Elapsed days since last practice
        elapsed_days = 0.0
        if item.last_practiced_at:
            lp_dt = item.last_practiced_at if item.last_practiced_at.tzinfo else item.last_practiced_at.replace(tzinfo=timezone.utc)
            elapsed_days = max(0.0, (now - lp_dt).total_seconds() / 86400.0)

        # 1. Evaluate Grade (1=Fail, 2=Assisted, 3=Good, 4=Easy)
        is_independent = result.independence == IndependenceLevel.INDEPENDENT
        is_strong_success = result.success and result.score >= 80.0 and is_independent

        if not result.success or result.score < 60.0:
            grade = 1
        elif not is_independent:
            grade = 2
        elif is_strong_success and result.score >= 85.0:
            grade = 4
        else:
            grade = 3

        # 2. Compute FSRS Memory Metrics
        retrievability = FSRSEngine.calculate_retrievability(elapsed_days, current_stability)
        next_difficulty = FSRSEngine.calculate_next_difficulty(current_difficulty, grade)
        next_stability = FSRSEngine.calculate_next_stability(
            current_stability=current_stability,
            difficulty=next_difficulty,
            retrievability=retrievability,
            grade=grade,
        )

        # 3. Schedule next review interval
        if grade == 1:
            new_streak = 0
            interval_days = 1
            reason = "Lần luyện tập chưa đạt yêu cầu, FSRS hẹn lịch ôn tập củng cố lại sớm."
            new_lifecycle = (
                LearningItemLifecycle.REGRESSED.value
                if item.lifecycle in ("mastered", "maintenance")
                else LearningItemLifecycle.PRACTICING.value
            )
        elif grade == 2:
            new_streak = min(curr_streak + 1, 2)
            interval_days = max(2, min(4, FSRSEngine.compute_optimal_interval(next_stability)))
            reason = "Đã sử dụng gợi ý hỗ trợ, FSRS điều chỉnh độ khó và tăng tần suất ôn tập phản xạ."
            new_lifecycle = LearningItemLifecycle.IMPROVING.value
        elif grade == 4:
            new_streak = curr_streak + 1
            computed_days = FSRSEngine.compute_optimal_interval(next_stability)
            interval_days = max(3, computed_days)
            reason = f"Phản xạ tự nhiên xuất sắc! FSRS nâng độ ổn định trí nhớ lên {next_stability:.1f} ngày (giãn cách {interval_days} ngày)."
            new_lifecycle = (
                LearningItemLifecycle.MAINTENANCE.value
                if new_streak >= 4 and item.overall_mastery >= MasteryEngine.MASTERY_THRESHOLD
                else LearningItemLifecycle.IMPROVING.value
            )
        else:
            new_streak = max(1, curr_streak + 1)
            computed_days = FSRSEngine.compute_optimal_interval(next_stability)
            interval_days = max(2, computed_days)
            reason = f"Vượt qua tốt! FSRS hẹn lịch củng cố tối ưu sau {interval_days} ngày."
            new_lifecycle = LearningItemLifecycle.PRACTICING.value

        next_review_dt = now + timedelta(days=interval_days)

        try:
            lifecycle_enum = LearningItemLifecycle(new_lifecycle)
        except ValueError:
            lifecycle_enum = LearningItemLifecycle.ACTIVE

        return ReviewDecision(
            learning_item_key=item.key,
            next_review_at=next_review_dt,
            interval_days=interval_days,
            review_streak=new_streak,
            reason=reason,
            new_lifecycle=lifecycle_enum,
            retrievability=retrievability,
            stability=next_stability,
            difficulty=next_difficulty,
        )

    @classmethod
    def filter_due_items(
        cls,
        items: list[LearningItem],
        reference_time: datetime | None = None,
    ) -> list[LearningItem]:
        """Filters items that are due or overdue for review."""
        ref = reference_time or datetime.now(timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)

        due_items = []
        for it in items:
            if not it.next_review_at:
                continue
            item_dt = it.next_review_at if it.next_review_at.tzinfo else it.next_review_at.replace(tzinfo=timezone.utc)
            if item_dt <= ref:
                due_items.append(it)

        # Sort by urgency: highest priority and lowest mastery first
        due_items.sort(key=lambda it: (it.priority_score, 1.0 - it.overall_mastery), reverse=True)
        return due_items
