from datetime import datetime, timedelta, timezone
import pytest

from app.domains.learning.contracts import ExerciseResult, IndependenceLevel
from app.domains.learning.models import LearningItem
from app.domains.learning.review_scheduler import ReviewScheduler


def test_review_schedule_on_strong_success():
    item = LearningItem(
        user_id="u1", key="k1", item_type="grammar", title="t1",
        review_streak=1, review_interval_days=2, overall_mastery=0.75
    )
    result = ExerciseResult(
        exercise_id="ex1", user_id="u1", score=90.0, success=True,
        confidence=0.9, feedback="Excellent", independence=IndependenceLevel.INDEPENDENT
    )

    decision = ReviewScheduler.schedule_next_review(item, result)

    assert decision.review_streak == 2
    assert decision.interval_days >= 3
    assert decision.next_review_at > datetime.now(timezone.utc)


def test_review_schedule_on_failure():
    item = LearningItem(
        user_id="u1", key="k1", item_type="grammar", title="t1",
        review_streak=3, review_interval_days=7, overall_mastery=0.75
    )
    result = ExerciseResult(
        exercise_id="ex1", user_id="u1", score=45.0, success=False,
        confidence=0.9, feedback="Needs work", independence=IndependenceLevel.INDEPENDENT
    )

    decision = ReviewScheduler.schedule_next_review(item, result)

    assert decision.review_streak == 0
    assert decision.interval_days == 1


def test_filter_due_items():
    now = datetime.now(timezone.utc)
    item_due = LearningItem(
        user_id="u1", key="due1", item_type="grammar", title="Due",
        next_review_at=now - timedelta(days=1), priority_score=0.8, overall_mastery=0.4
    )
    item_future = LearningItem(
        user_id="u1", key="fut1", item_type="grammar", title="Future",
        next_review_at=now + timedelta(days=3), priority_score=0.8, overall_mastery=0.4
    )

    due_list = ReviewScheduler.filter_due_items([item_due, item_future], reference_time=now)
    assert len(due_list) == 1
    assert due_list[0].key == "due1"
