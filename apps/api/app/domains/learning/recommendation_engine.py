from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.contracts import PriorityScore
from app.domains.learning.goal_service import GoalService
from app.domains.learning.learner_state_service import LearnerStateService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.priority_engine import PriorityEngine


class RecommendationEngine:
    """Provides transparent, explainable recommendations connecting weaknesses to active practice."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_service = LearnerStateService(db)
        self.item_service = LearningItemService(db)
        self.goal_service = GoalService(db)

    async def get_actionable_recommendations(
        self,
        user_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Computes prioritized actionable learning recommendations with transparent 'What', 'Why', and 'How'.
        """
        await self.item_service.sync_from_memory(user_id)
        active_goals = await self.goal_service.get_active_goals(user_id)
        items = await self.item_service.list_items(user_id, limit=30)

        scores: list[PriorityScore] = []
        for it in items:
            p_score = PriorityEngine.calculate_item_priority(it, active_goals)
            scores.append(p_score)

        balanced = PriorityEngine.rank_and_balance_priorities(scores, limit=limit)

        recommendations: list[dict[str, Any]] = []
        for s in balanced:
            # Match underlying item for accurate mastery and attempt counts
            it = next((i for i in items if i.key == s.key), None)
            mastery_pct = int(it.overall_mastery * 100) if it else 40
            attempts = it.attempt_count if it else 0
            successes = it.success_count if it else 0

            recommendations.append({
                "key": s.key,
                "item_type": s.item_type.value,
                "title": s.title,
                "priority_score": s.priority_score,
                "why": s.reason,
                "how": f"Luyện tập qua dạng bài {s.recommended_exercise_type.value.replace('_', ' ')}",
                "recommended_exercise_type": s.recommended_exercise_type.value,
                "estimated_minutes": s.estimated_minutes,
                "difficulty": s.difficulty.value,
                "mastery_percent": mastery_pct,
                "attempt_count": attempts,
                "success_count": successes,
                "goal_relevance": s.goal_relevance,
            })

        return recommendations
