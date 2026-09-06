from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.contracts import GoalProgressOverview
from app.domains.analytics.domain.metric_definitions import ConfidenceLevel
from app.domains.learning.models import LearningGoal, LearningItem
from app.domains.learning.review_scheduler import FSRSEngine


class GoalAnalyticsService:
    """
    Derives grounded goal progress from linked LearningItem masteries, FSRS memory decay,
    and attempt evidence.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_goal_progress_overview(self, user_id: str) -> list[GoalProgressOverview]:
        """
        Calculates progress for all active goals tied to the learner with FSRS cognitive grounding.
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

        now = datetime.now(timezone.utc)
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
                elif it.title and g.title and g.title.lower() in it.title.lower():
                    linked_items.append(it)

            if not linked_items:
                # Fallback to general items
                linked_items = items[:5] if items else []

            total_attempts = sum(it.attempt_count for it in linked_items)

            # SOTA FSRS Memory Grounding:
            # An item's actual effective proficiency decays over time unless maintained.
            grounded_masteries: list[float] = []
            weak_items_with_retention: list[tuple[LearningItem, float, float]] = []

            for it in linked_items:
                elapsed_days = 0.0
                if it.last_practiced_at:
                    lp_dt = it.last_practiced_at if it.last_practiced_at.tzinfo else it.last_practiced_at.replace(tzinfo=timezone.utc)
                    elapsed_days = max(0.0, (now - lp_dt).total_seconds() / 86400.0)

                stability = float(it.review_interval_days) if it.review_interval_days > 0 else 2.0
                retrievability = FSRSEngine.calculate_retrievability(elapsed_days, stability)

                # Grounded mastery reflects true retained capacity
                grounded_m = it.overall_mastery * retrievability
                grounded_masteries.append(grounded_m)

                if grounded_m < 0.50:
                    weak_items_with_retention.append((it, grounded_m, retrievability))

            avg_mastery = (
                sum(grounded_masteries) / len(grounded_masteries)
                if grounded_masteries
                else 0.0
            )

            # Bayesian evidence confidence based on attempts volume
            if total_attempts >= 15:
                confidence = ConfidenceLevel.HIGH
            elif total_attempts >= 5:
                confidence = ConfidenceLevel.MEDIUM
            else:
                confidence = ConfidenceLevel.LOW

            # Cognitive Blockers: prioritize items with lowest grounded retention
            if weak_items_with_retention:
                weak_items_with_retention.sort(key=lambda x: x[1])
                weakest_it, weakest_m, weakest_r = weak_items_with_retention[0]
                retention_pct = int(round(weakest_r * 100))
                blocked_by = f"Cần củng cố: {weakest_it.title} (Khả năng nhớ: {retention_pct}%)"
                next_action = f"Luyện tập 10 phút về {weakest_it.title}"
            else:
                blocked_by = None
                next_action = "Hội thoại tự do duy trì phong độ"

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
                    next_actions=[next_action],
                )
            )

        return overview_list
