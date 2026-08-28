from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learner_memory.models import LearnerMemory
from app.domains.learning.contracts import (
    ExerciseResult,
    IndependenceLevel,
    LearningItemLifecycle,
)
from app.domains.learning.goal_service import GoalService
from app.domains.learning.mastery_engine import MasteryEngine
from app.domains.learning.models import LearningItem
from app.domains.learning.priority_engine import PriorityEngine
from app.domains.learning.review_scheduler import ReviewScheduler
from app.shared.errors.exceptions import NotFoundException, ValidationException


class LearningItemService:
    """Service for managing the active learning item catalog, memory synchronization, and mastery updates."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.goal_service = GoalService(db)

    async def sync_from_memory(self, user_id: str) -> list[LearningItem]:
        """
        Synchronizes persistent LearnerMemory weaknesses into active LearningItem training targets.
        Ensures clear separation: Memory = what we know, LearningItem = what we are currently training.
        """
        # Fetch active memories
        mem_stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.status.in_(["new", "active", "improving"]),
                LearnerMemory.memory_type.in_([
                    "grammar", "particle", "conjugation", "politeness",
                    "filler", "word_choice", "vocabulary", "naturalness",
                    "pronunciation", "pitch_accent", "fluency"
                ]),
            )
        )
        mem_res = await self.db.execute(mem_stmt)
        memories = mem_res.scalars().all()

        active_goals = await self.goal_service.get_active_goals(user_id)
        synced_items: list[LearningItem] = []

        for mem in memories:
            item_stmt = select(LearningItem).where(
                LearningItem.user_id == user_id,
                LearningItem.key == mem.key,
            )
            item_res = await self.db.execute(item_stmt)
            item = item_res.scalar_one_or_none()

            if not item:
                # Create brand new training target
                recog_init = min(1.0, mem.mastery + 0.15)
                prod_init = mem.mastery
                spont_init = max(0.0, mem.mastery - 0.05)
                c_score = min(1.0, (len(mem.contexts_used or [])) * 0.25)
                overall_init = MasteryEngine.calculate_multidimensional_mastery(
                    recognition=recog_init,
                    production=prod_init,
                    spontaneous=spont_init,
                    context_variety_score=c_score,
                )

                item = LearningItem(
                    user_id=user_id,
                    memory_key=mem.key,
                    key=mem.key,
                    item_type=mem.memory_type,
                    title=mem.statement,
                    description=f"Luyện tập khắc phục lỗi {mem.statement} trong giao tiếp tự nhiên.",
                    difficulty="normal",
                    lifecycle=LearningItemLifecycle.ACTIVE.value,
                    status="active",
                    overall_mastery=overall_init,
                    recognition_mastery=recog_init,
                    production_mastery=prod_init,
                    spontaneous_mastery=spont_init,
                    context_variety_score=c_score,
                    confidence=mem.confidence,
                    priority_score=mem.priority_score,
                    attempt_count=mem.attempt_count,
                    success_count=mem.correct_count,
                    independent_success_count=max(0, mem.correct_count - 1),
                    assisted_success_count=1 if mem.correct_count > 0 else 0,
                    review_streak=1 if mem.correct_count > 0 else 0,
                    review_interval_days=1,
                    last_practiced_at=mem.last_seen,
                    contexts_used=mem.contexts_used,
                    extra_metadata={"severity": mem.severity, "category": mem.category},
                )
                self.db.add(item)
            else:
                # Update existing training target metadata if not yet mastered
                if item.lifecycle not in ("mastered", "maintenance"):
                    item.title = mem.statement
                    item.contexts_used = mem.contexts_used
                    item.extra_metadata = {"severity": mem.severity, "category": mem.category}

            # Recalculate priority
            p_score = PriorityEngine.calculate_item_priority(item, active_goals)
            item.priority_score = p_score.priority_score

            synced_items.append(item)

        await self.db.commit()
        logger.info(f"[LearningItemService] Synced {len(synced_items)} learning items for user '{user_id}'")
        return synced_items

    async def list_items(
        self,
        user_id: str,
        item_type: str | None = None,
        lifecycle: str | None = None,
        limit: int = 50,
    ) -> list[LearningItem]:
        stmt = select(LearningItem).where(LearningItem.user_id == user_id)
        if item_type:
            stmt = stmt.where(LearningItem.item_type == item_type)
        if lifecycle:
            stmt = stmt.where(LearningItem.lifecycle == lifecycle)
        stmt = stmt.order_by(desc(LearningItem.priority_score), desc(LearningItem.updated_at)).limit(limit)

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_item_by_id(self, item_id: str, user_id: str) -> LearningItem:
        stmt = select(LearningItem).where(LearningItem.id == item_id, LearningItem.user_id == user_id)
        res = await self.db.execute(stmt)
        item = res.scalar_one_or_none()
        if not item:
            raise NotFoundException(f"LearningItem '{item_id}' not found.")
        return item

    async def get_item_by_key(self, key: str, user_id: str) -> LearningItem | None:
        stmt = select(LearningItem).where(LearningItem.key == key, LearningItem.user_id == user_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def update_item_from_result(
        self,
        user_id: str,
        item_key: str,
        result: ExerciseResult,
        context_tag: str = "conversation",
    ) -> dict[str, Any]:
        """
        Applies completed exercise attempt outcomes to update multi-dimensional mastery,
        review schedule, lifecycle state, and priority.
        """
        item = await self.get_item_by_key(item_key, user_id)
        if not item:
            logger.warning(f"[LearningItemService] Cannot update mastery: item '{item_key}' not found.")
            return {}

        now = datetime.now(timezone.utc)

        # 1. Update attempt counters
        item.attempt_count += 1
        if result.success:
            item.success_count += 1
            if result.independence == IndependenceLevel.INDEPENDENT:
                item.independent_success_count += 1
            else:
                item.assisted_success_count += 1

        # 2. Contexts tracking
        contexts = list(item.contexts_used or [])
        if context_tag and context_tag not in contexts:
            contexts.append(context_tag)
            item.contexts_used = contexts
            item.context_variety_score = min(1.0, len(contexts) * 0.25)

        # 3. Calculate mastery deltas
        old_mastery = item.overall_mastery
        delta_spontaneous = MasteryEngine.calculate_mastery_delta(result, item, dimension="spontaneous")
        delta_production = MasteryEngine.calculate_mastery_delta(result, item, dimension="production")
        # Automaticity: only update for reflex/keigo/pitch/situational timed exercises or when response_speed is available
        is_timed = context_tag.startswith(("reflex", "keigo", "pitch", "mora", "vowel", "situational")) or (result.response_speed_ms is not None)
        delta_automaticity = 0.0
        if is_timed:
            delta_automaticity = MasteryEngine.calculate_mastery_delta(result, item, dimension="automaticity")
            # Ensure column exists (migration 010)
            if hasattr(item, "automaticity_mastery"):
                item.automaticity_mastery = max(0.0, min(1.0, round(float(item.automaticity_mastery or 0.0) + delta_automaticity, 3)))

        item.spontaneous_mastery = max(0.0, min(1.0, round(item.spontaneous_mastery + delta_spontaneous, 3)))
        item.production_mastery = max(0.0, min(1.0, round(item.production_mastery + delta_production, 3)))
        item.recognition_mastery = max(item.production_mastery, min(1.0, item.recognition_mastery + 0.05 if result.success else item.recognition_mastery))

        # Combined overall mastery
        item.overall_mastery = MasteryEngine.calculate_multidimensional_mastery(
            recognition=item.recognition_mastery,
            production=item.production_mastery,
            spontaneous=item.spontaneous_mastery,
            context_variety_score=item.context_variety_score,
        )
        total_delta = round(item.overall_mastery - old_mastery, 3)

        # 4. Lifecycle state machine evaluation
        new_lifecycle = MasteryEngine.evaluate_lifecycle_transition(
            current_lifecycle=item.lifecycle,
            overall_mastery=item.overall_mastery,
            spontaneous_mastery=item.spontaneous_mastery,
            attempt_count=item.attempt_count,
            independent_success_count=item.independent_success_count,
            context_variety_count=len(contexts),
            recent_has_failure=(not result.success),
        )
        item.lifecycle = new_lifecycle

        # 5. Spaced Review Scheduling
        review_decision = ReviewScheduler.schedule_next_review(item, result)
        item.review_streak = review_decision.review_streak
        item.review_interval_days = review_decision.interval_days
        item.next_review_at = review_decision.next_review_at
        item.last_practiced_at = now

        # 6. Recalculate Priority Score
        goals = await self.goal_service.get_active_goals(user_id)
        p_score = PriorityEngine.calculate_item_priority(item, goals)
        item.priority_score = p_score.priority_score

        await self.db.commit()
        await self.db.refresh(item)

        logger.info(
            f"[LearningItemService] Updated item '{item.key}': Mastery {old_mastery:.2f} -> {item.overall_mastery:.2f} (delta: {total_delta:+.2f}), Next review: {item.next_review_at.strftime('%Y-%m-%d')}"
        )

        return {
            "item_key": item.key,
            "old_mastery": old_mastery,
            "new_mastery": item.overall_mastery,
            "delta": total_delta,
            "delta_automaticity": delta_automaticity if is_timed else 0.0,
            "automaticity": float(getattr(item, "automaticity_mastery", 0.0)),
            "lifecycle": item.lifecycle,
            "next_review_at": item.next_review_at.isoformat() if item.next_review_at else None,
            "review_streak": item.review_streak,
        }
