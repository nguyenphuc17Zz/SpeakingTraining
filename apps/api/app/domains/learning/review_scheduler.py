from datetime import datetime, timedelta, timezone
from typing import Any

from app.domains.learning.contracts import (
    ExerciseResult,
    IndependenceLevel,
    LearningItemLifecycle,
    ReviewDecision,
)
from app.domains.learning.mastery_engine import MasteryEngine
from app.domains.learning.models import LearningItem


class ReviewScheduler:
    """Spaced repetition scheduler customized for speaking and spontaneous language production."""

    # Interval progression multipliers
    STREAK_INTERVAL_MAP = {
        0: 1,    # Day 1
        1: 2,    # Day 2
        2: 4,    # Day 4
        3: 7,    # 1 week
        4: 14,   # 2 weeks
        5: 28,   # 4 weeks
    }

    @classmethod
    def schedule_next_review(
        cls,
        item: LearningItem,
        result: ExerciseResult,
    ) -> ReviewDecision:
        """
        Computes next review timestamp and interval based on attempt performance and independence level.
        """
        now = datetime.now(timezone.utc)
        curr_streak = item.review_streak

        # 1. Evaluate success criteria
        is_independent = result.independence == IndependenceLevel.INDEPENDENT
        is_strong_success = result.success and result.score >= 80.0 and is_independent

        if not result.success or result.score < 60.0:
            # Failed or weak attempt -> Reset streak and schedule review tomorrow
            new_streak = 0
            interval_days = 1
            reason = "Lần luyện tập chưa đạt yêu cầu, cần ôn tập củng cố lại sớm."
            new_lifecycle = (
                LearningItemLifecycle.REGRESSED.value
                if item.lifecycle in ("mastered", "maintenance")
                else LearningItemLifecycle.PRACTICING.value
            )

        elif not is_independent:
            # Assisted success (used hint or starter) -> Keep or increment streak slowly
            new_streak = min(curr_streak + 1, 2)
            interval_days = cls.STREAK_INTERVAL_MAP.get(new_streak, 2)
            reason = "Đã sử dụng gợi ý hỗ trợ, cần thêm bài tập phản xạ độc lập."
            new_lifecycle = LearningItemLifecycle.IMPROVING.value

        elif is_strong_success:
            # Strong independent production -> Advance streak and extend interval
            new_streak = curr_streak + 1
            interval_days = cls.STREAK_INTERVAL_MAP.get(new_streak, min(30, int(item.review_interval_days * 1.8)))
            reason = f"Phản xạ tự nhiên xuất sắc! Giãn cách ôn tập lên {interval_days} ngày."
            new_lifecycle = (
                LearningItemLifecycle.MAINTENANCE.value
                if new_streak >= 4 and item.overall_mastery >= MasteryEngine.MASTERY_THRESHOLD
                else LearningItemLifecycle.IMPROVING.value
            )

        else:
            # Borderline pass
            new_streak = max(1, curr_streak)
            interval_days = max(2, item.review_interval_days)
            reason = f"Vượt qua ở mức khá, hẹn lịch ôn tập sau {interval_days} ngày."
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
