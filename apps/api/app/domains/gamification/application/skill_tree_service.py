from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.models import SkillNodeDefinition
from app.domains.gamification.schemas import SkillNodeDTO, SkillTreeOverviewDTO
from app.domains.learning.models import LearningItem


class SkillTreeService:
    """
    Japanese Speaking RPG Skill Tree engine.
    Derives all node masteries dynamically from Phase 7 LearningItem state.
    Never duplicates mastery or creates separate learning truths!
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_skill_tree_overview(self, user_id: str) -> SkillTreeOverviewDTO:
        """
        Synthesizes the multi-branch Japanese Speaking Skill Tree from real LearningEngine data.
        Branches: Fluency, Naturalness, Grammar, Pronunciation.
        """
        # 1. Fetch Skill Node Definitions
        nodes_stmt = select(SkillNodeDefinition).order_by(SkillNodeDefinition.display_order.asc())
        nodes_res = await self.db.execute(nodes_stmt)
        node_defs = list(nodes_res.scalars().all())

        # 2. Fetch User's Learning Items
        items_stmt = select(LearningItem).where(LearningItem.user_id == user_id)
        items_res = await self.db.execute(items_stmt)
        user_items = list(items_res.scalars().all())

        # Index items by type
        items_by_type: dict[str, list[LearningItem]] = {}
        for it in user_items:
            t = it.item_type.lower()
            if t not in items_by_type:
                items_by_type[t] = []
            items_by_type[t].append(it)

        # 3. Compute Node Masteries
        node_dtos: list[SkillNodeDTO] = []
        mastery_map: dict[str, float] = {}
        categories = ["fluency", "naturalness", "grammar", "pronunciation"]

        for nd in node_defs:
            linked_types = nd.linked_item_types_json or []
            matched_items: list[LearningItem] = []
            for lt in linked_types:
                matched_items.extend(items_by_type.get(lt.lower(), []))

            if matched_items:
                avg_mastery = sum(it.overall_mastery for it in matched_items) / len(matched_items)
                total_attempts = sum(it.attempt_count for it in matched_items)
            else:
                avg_mastery = 0.0
                total_attempts = 0

            mastery_map[nd.key] = avg_mastery

            # Determine Status
            prereqs = nd.prerequisites_json or []
            is_locked = False
            for p in prereqs:
                if mastery_map.get(p, 0.0) < 0.35:
                    is_locked = True
                    break

            if is_locked:
                status = "locked"
            elif avg_mastery >= 0.85:
                status = "mastered"
            elif avg_mastery >= 0.60:
                status = "strong"
            elif avg_mastery >= 0.20 or total_attempts > 0:
                status = "developing"
            else:
                status = "available"

            linked_dtos = [
                {
                    "key": it.key,
                    "title": it.title,
                    "mastery": it.overall_mastery,
                    "lifecycle": it.lifecycle,
                }
                for it in matched_items[:5]
            ]

            rec_type = "roleplay"
            if nd.category == "pronunciation":
                rec_type = "pronunciation_repeat"
            elif nd.category == "fluency":
                rec_type = "rapid_response"

            node_dtos.append(
                SkillNodeDTO(
                    key=nd.key,
                    name=nd.name,
                    description=nd.description,
                    category=nd.category,
                    icon=nd.icon,
                    status=status,
                    current_mastery=round(avg_mastery, 2),
                    attempt_count=total_attempts,
                    prerequisites=prereqs,
                    linked_learning_items=linked_dtos,
                    recommended_exercise_type=rec_type,
                )
            )

        total_nodes = len(node_dtos)
        mastered_count = sum(1 for n in node_dtos if n.status == "mastered")
        overall_avg = sum(n.current_mastery for n in node_dtos) / max(1, total_nodes)

        return SkillTreeOverviewDTO(
            categories=categories,
            nodes=node_dtos,
            overall_mastery_average=round(overall_avg, 2),
            mastered_count=mastered_count,
            total_nodes=total_nodes,
        )
