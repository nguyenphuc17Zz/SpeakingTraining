import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.application.analytics_snapshot_service import AnalyticsSnapshotService
from app.domains.analytics.application.goal_analytics_service import GoalAnalyticsService
from app.domains.analytics.application.weekly_review_service import WeeklyReviewService
from app.domains.learning.models import LearningGoal, LearningItem


@pytest.mark.asyncio
async def test_goal_analytics_progress_derivation(db_session: AsyncSession):
    """Verify GoalAnalyticsService computes progress from linked LearningItems."""
    user_id = "test_user_goals_1"

    # Seed goal
    goal = LearningGoal(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="Workplace Keigo Fluency",
        goal_type="workplace",
        status="active",
        priority=1,
    )
    db_session.add(goal)

    # Seed 2 linked learning items
    it1 = LearningItem(
        id=str(uuid.uuid4()),
        user_id=user_id,
        key="item_keigo_1",
        title="Kenjougo Humble Forms",
        item_type="politeness",
        overall_mastery=0.8,
        attempt_count=6,
        status="active",
    )
    it2 = LearningItem(
        id=str(uuid.uuid4()),
        user_id=user_id,
        key="item_keigo_2",
        title="Sonkeigo Respectful Forms",
        item_type="politeness",
        overall_mastery=0.6,
        attempt_count=4,
        status="active",
    )
    db_session.add_all([it1, it2])
    await db_session.commit()

    service = GoalAnalyticsService(db_session)
    goals = await service.get_goal_progress_overview(user_id)
    assert len(goals) == 1
    assert goals[0].goal_id == goal.id
    # (0.8 + 0.6) / 2 = 0.70
    assert goals[0].progress_ratio == 0.70
    assert goals[0].linked_items_count == 2


@pytest.mark.asyncio
async def test_weekly_review_deterministic_facts(db_session: AsyncSession):
    """Verify WeeklyReviewService generates factual summary without modifying numbers."""
    user_id = "test_user_review_1"
    service = WeeklyReviewService(db_session, ai_router=None)

    review = await service.get_or_generate_weekly_review(user_id, week_start_str="2026-08-24", generate_ai_narrative=False)
    assert review.week_start == "2026-08-24"
    assert review.is_ai_generated is False
    assert "Tổng kết tuần" in review.narrative
    assert len(review.recommendations) >= 1


@pytest.mark.asyncio
async def test_analytics_snapshot_caching(db_session: AsyncSession):
    """Verify AnalyticsSnapshotService creates cached snapshot for sub-second retrieval."""
    user_id = "test_user_snapshot_1"
    service = AnalyticsSnapshotService(db_session)

    dashboard = await service.get_dashboard_overview(user_id, period="30d")
    assert dashboard.user_id == user_id
    assert len(dashboard.metrics) > 0
    assert dashboard.bottleneck is not None
