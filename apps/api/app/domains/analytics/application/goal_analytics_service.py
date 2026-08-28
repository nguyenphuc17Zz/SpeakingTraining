from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.contracts import GoalProgressOverview
from app.domains.analytics.domain.metric_definitions import ConfidenceLevel
from app.domains.learning.models import LearningGoal, LearningItem


class GoalAnalyticsService:
    """Derives grounded goal progress from linked LearningItem masteries and attempt evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_goal_progress_overview(self, user_id: str) -> list[GoalProgressOverview]:
        """
        Calculates progress for all active goals tied to the learner.
        """
        # Fetch active goals
        goals_stmt = (
            select(LearningGoal)
            .where(
                LearningGoal.user_id == user_id,
                LearningGoal.status == "active",
            )
            .order_by(LearningGoal.priority.asc())
        )
        goals_res = await self.db.execute(goals_stmt)
        goals = list(goals_res.scalars().all())

        # Fetch active learning items
        items_stmt = select(LearningItem).where(
            LearningItem.user_id == user_id,
            LearningItem.status == "active",
        )
        items_res = await self.db.execute(items_stmt)
        items = list(items_res.scalars().all())

        overview_list: list[GoalProgressOverview] = []
        for g in goals:
            # Match items to goal based on goal_type and item affinity
            linked_items = []
            for it in items:
                if g.goal_type == "speaking":
                    linked_items.append(it)
                elif g.goal_type == "workplace" and it.item_type in ("politeness", "naturalness", "grammar"):
                    linked_items.append(it)
                elif g.goal_type == "pronunciation" and it.item_type in ("pronunciation", "pitch_accent"):
                    linked_items.append(it)
                elif g.title.lower() in it.title.lower():
                    linked_items.append(it)

            if not linked_items:
                # Fallback to general items
                linked_items = items[:5] if items else []

            total_attempts = sum(it.attempt_count for it in linked_items)
            avg_mastery = (
                sum(it.overall_mastery for it in linked_items) / len(linked_items)
                if linked_items
                else 0.0
            )

            # Confidence based on attempts
            if total_attempts >= 15:
                confidence = ConfidenceLevel.HIGH
            elif total_attempts >= 5:
                confidence = ConfidenceLevel.MEDIUM
            else:
                confidence = ConfidenceLevel.LOW

            # Blockers
            weak_items = [it for it in linked_items if it.overall_mastery < 0.5]
            blocked_by = f"Cần củng cố: {weak_items[0].title}" if weak_items else None

            overview_list.append(
                GoalProgressOverview(
                    goal_id=g.id,
                    title=g.title,
                    goal_type=g.goal_type,
                    progress_ratio=round(min(1.0, max(0.0, avg_mastery)), 2),
                    confidence=confidence,
                    recent_activity_count=total_attempts,
                    linked_items_count=len(linked_items),
                    blocked_by=blocked_by,
                    next_actions=[
                        f"Luyện tập 10 phút về {weak_items[0].title}" if weak_items else "Hội thoại tự do duy trì phong độ"
                    ],
                )
            )

        return overview_list
