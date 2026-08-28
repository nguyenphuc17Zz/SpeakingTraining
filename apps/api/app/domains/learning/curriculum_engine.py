from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.contracts import CurriculumUnit, ExerciseType
from app.domains.learning.dynamic_curriculum import AICurriculumGenerator
from app.domains.learning.goal_service import GoalService
from app.domains.learning.learner_state_service import LearnerStateService
from app.domains.learning.learning_item_service import LearningItemService


class CurriculumEngine:
    """Dynamic, AI-powered goal-aligned curriculum engine that maps long-term speaking milestones to active practice units."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_service = LearnerStateService(db)
        self.item_service = LearningItemService(db)
        self.goal_service = GoalService(db)
        self.ai_generator = AICurriculumGenerator(db)

    async def get_curriculum_roadmap(
        self,
        user_id: str,
        level: str = "intermediate",
        target_goal: str = "workplace",
        daily_minutes: int = 30,
        custom_wish: str | None = None,
        force_regenerate: bool = False,
    ) -> dict[str, Any]:
        """Returns the full 4-stage interactive milestone roadmap for the user."""
        return await self.ai_generator.get_or_generate_user_curriculum(
            user_id=user_id,
            level=level,
            target_goal=target_goal,
            daily_minutes=daily_minutes,
            custom_wish=custom_wish,
            force_regenerate=force_regenerate,
        )

    async def toggle_node_completion(
        self,
        user_id: str,
        node_id: str,
        is_completed: bool | None = None,
        score: float | None = None,
    ) -> dict[str, Any] | None:
        """Toggles the completion status of a lesson node in the roadmap."""
        return await self.ai_generator.toggle_node_completion(
            user_id=user_id,
            node_id=node_id,
            is_completed=is_completed,
            score=score,
        )

    async def generate_dynamic_curriculum(self, user_id: str) -> list[CurriculumUnit]:
        """
        Synthesizes adaptive curriculum units from the active AI roadmap.
        Maintains backward compatibility with legacy endpoints.
        """
        roadmap = await self.get_curriculum_roadmap(user_id=user_id)
        units: list[CurriculumUnit] = []

        for stage in roadmap.get("stages", []):
            for node in stage.get("nodes", []):
                mode_str = node.get("target_mode", "/speaking").replace("/", "")
                ex_type = ExerciseType.CONVERSATION
                if mode_str == "keigo":
                    ex_type = ExerciseType.KEIGO_SONKEIGO
                elif mode_str == "pitch":
                    ex_type = ExerciseType.PITCH_MINIMAL_PAIR
                elif mode_str == "situations":
                    ex_type = ExerciseType.ROLEPLAY
                elif mode_str == "shadowing":
                    ex_type = ExerciseType.SHADOWING

                units.append(
                    CurriculumUnit(
                        id=node["id"],
                        title=node["title"],
                        objective=node["description"],
                        target_learning_items=node.get("key_patterns", []),
                        recommended_exercise_types=[ex_type],
                        completion_criteria=f"Hoàn thành bài tập tại phòng {node.get('mode_label', 'Luyện tập')}",
                        estimated_sessions=1,
                        is_completed=node.get("is_completed", False),
                        progress_ratio=1.0 if node.get("is_completed", False) else 0.0,
                    )
                )

        return units
