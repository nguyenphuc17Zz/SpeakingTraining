from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.learning.contracts import DifficultyLevel, ExerciseType, LearnerLearningState, LearningItemType, PriorityScore
from app.domains.learning.exercise_generator import ExerciseGenerator
from app.domains.learning.exercise_variety_policy import ExerciseVarietyPolicy
from app.domains.learning.goal_service import GoalService
from app.domains.learning.learner_state_service import LearnerStateService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.models import Exercise, LearningItem, LearningPlan, LearningPlanItem
from app.domains.learning.priority_engine import PriorityEngine
from app.domains.learning.review_scheduler import ReviewScheduler


class DailyPlanGenerator:
    """Orchestrates generation, persistence, and caching of daily adaptive learning schedules."""

    GENERATOR_VERSION = "1.0.0"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_service = LearnerStateService(db)
        self.item_service = LearningItemService(db)
        self.goal_service = GoalService(db)
        self.exercise_generator = ExerciseGenerator(db)

    async def get_or_create_daily_plan(
        self,
        user_id: str,
        plan_date: str | None = None,
        time_budget_minutes: int = 30,
        regenerate: bool = False,
    ) -> LearningPlan:
        """
        Retrieves today's persistent plan, or generates a new personalized plan if none exists or regeneration is requested.
        Guarantees stable daily plans upon page refresh. Handles concurrent create via ON CONFLICT retry.
        """
        # Validate time_budget to prevent cost explosion / empty plan
        if not isinstance(time_budget_minutes, int) or time_budget_minutes < 5 or time_budget_minutes > 120:
            from app.shared.errors.exceptions import ValidationException

            raise ValidationException(f"time_budget_minutes must be 5..120, got {time_budget_minutes}")
        # Validate plan_date format if provided
        if plan_date is not None:
            try:
                datetime.strptime(plan_date, "%Y-%m-%d")
            except Exception:
                from app.shared.errors.exceptions import ValidationException

                raise ValidationException(f"Invalid plan_date format, expected YYYY-MM-DD, got {plan_date}")
        date_str = plan_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 1. Check existing plan
        stmt = (
            select(LearningPlan)
            .where(
                LearningPlan.user_id == user_id,
                LearningPlan.plan_date == date_str,
            )
            .options(
                selectinload(LearningPlan.items).selectinload(LearningPlanItem.exercise)
            )
        )
        res = await self.db.execute(stmt)
        existing_plan = res.scalar_one_or_none()

        if existing_plan and not regenerate:
            return existing_plan

        if existing_plan and regenerate:
            # Delete old plan items and plan to regenerate fresh
            await self.db.delete(existing_plan)
            await self.db.flush()

        # 2. Build current learner state & sync items
        await self.item_service.sync_from_memory(user_id)
        state = await self.state_service.build_learning_state(user_id)
        active_goals = await self.goal_service.get_active_goals(user_id)
        items = await self.item_service.list_items(user_id, limit=30)

        # 3. Compute priority scores for all active items
        priority_scores: list[PriorityScore] = []
        for it in items:
            p_score = PriorityEngine.calculate_item_priority(it, active_goals)
            priority_scores.append(p_score)

        ranked_priorities = PriorityEngine.rank_and_balance_priorities(priority_scores, limit=8)

        # 4. Check due reviews
        due_items = ReviewScheduler.filter_due_items(items)

        # 5. Allocate time slots according to speaking-first variety policy
        slots = ExerciseVarietyPolicy.allocate_time_slots(time_budget_minutes)

        # Determine main daily focus title
        top_focus = ranked_priorities[0].title if ranked_priorities else "Luyện phản xạ giao tiếp tổng quát"
        top_reason = ranked_priorities[0].reason if ranked_priorities else "Duy trì thói quen luyện nói hàng ngày"

        # 6. Create LearningPlan container
        plan = LearningPlan(
            user_id=user_id,
            plan_date=date_str,
            time_budget_minutes=time_budget_minutes,
            status="active",
            focus_title=f"Trọng tâm: {top_focus}",
            focus_reason=top_reason,
            generator_version=self.GENERATOR_VERSION,
            generated_at=datetime.now(timezone.utc),
            extra_metadata={"slots_count": len(slots)},
        )
        self.db.add(plan)
        await self.db.flush()

        # 7. Generate or attach exercises for each allocated slot
        used_priority_indices = 0
        recent_signatures: list[str] = []

        for idx, slot in enumerate(slots):
            slot_type = slot["slot_type"]
            est_mins = slot["estimated_minutes"]
            slot_title = slot["title"]

            # Select target priority
            if slot_type == "review" and due_items:
                target_item = due_items.pop(0)
                p_score = PriorityEngine.calculate_item_priority(target_item, active_goals)
            elif slot_type == "pronunciation":
                # Find top pronunciation priority
                pron_p = next((p for p in ranked_priorities if p.item_type in (LearningItemType.PRONUNCIATION, LearningItemType.PITCH_ACCENT)), None)
                if pron_p:
                    p_score = pron_p
                else:
                    p_score = PriorityScore(
                        key="pronunciation.long_vowel",
                        item_type=LearningItemType.PRONUNCIATION,
                        title="Trường âm & Âm ngắt tiếng Nhật",
                        priority_score=0.75,
                        reason="Luyện độ đều đặn của phách và ngữ điệu tự nhiên.",
                        recommended_exercise_type=ExerciseType.PRONUNCIATION_REPEAT,
                        estimated_minutes=est_mins,
                        difficulty=DifficultyLevel.NORMAL,
                    )
            elif slot_type == "exploration":
                p_score = PriorityScore(
                    key="naturalness.casual_flow",
                    item_type=LearningItemType.NATURALNESS,
                    title="Hội thoại tự do mở rộng chủ đề",
                    priority_score=0.60,
                    reason="Khám phá các chủ đề giao tiếp mới không gò bó.",
                    recommended_exercise_type=ExerciseType.CONVERSATION,
                    estimated_minutes=est_mins,
                    difficulty=DifficultyLevel.NORMAL,
                )
            else:
                if used_priority_indices < len(ranked_priorities):
                    p_score = ranked_priorities[used_priority_indices]
                    used_priority_indices += 1
                else:
                    p_score = PriorityScore(
                        key="grammar.natural_speaking",
                        item_type=LearningItemType.GRAMMAR,
                        title="Phản xạ đối đáp hội thoại",
                        priority_score=0.65,
                        reason="Củng cố độ trôi chảy khi giao tiếp liên tục.",
                        recommended_exercise_type=ExerciseType.ROLEPLAY,
                        estimated_minutes=est_mins,
                        difficulty=DifficultyLevel.NORMAL,
                    )

            # Generate concrete exercise
            exercise = await self.exercise_generator.generate_exercise(
                user_id=user_id,
                priority=p_score,
                state=state,
                recent_signatures=recent_signatures,
            )
            if exercise.exercise_signature:
                recent_signatures.append(exercise.exercise_signature)

            # Create Plan Item
            plan_item = LearningPlanItem(
                plan_id=plan.id,
                exercise_id=exercise.id,
                order_index=idx,
                target_type=slot_type,
                title=f"{slot_title} — {exercise.title}",
                estimated_minutes=est_mins,
                status="pending",
            )
            self.db.add(plan_item)

        try:
            await self.db.commit()
        except Exception as e:
            # ON CONFLICT race: duplicate (user_id, plan_date) -> fetch existing
            from sqlalchemy.exc import IntegrityError

            if isinstance(e, IntegrityError) or "UNIQUE constraint" in str(e) or "uq_user_daily_plan_date" in str(e):
                await self.db.rollback()
                logger.warning(f"[DailyPlanGenerator] Concurrent plan create race for {user_id} {date_str}, re-fetching existing")
                res = await self.db.execute(stmt)
                existing = res.scalar_one_or_none()
                if existing:
                    return existing
            # Re-raise if not handled
            raise

        # Re-fetch with loaded relationships
        try:
            res = await self.db.execute(stmt)
            full_plan = res.scalar_one()
        except Exception:
            # scalar_one may fail if concurrent delete, fallback to scalar_one_or_none
            res = await self.db.execute(stmt)
            full_plan = res.scalar_one_or_none()
            if not full_plan:
                raise
        logger.info(f"[DailyPlanGenerator] Successfully generated and persisted plan for user '{user_id}' on '{date_str}' ({len(full_plan.items)} items)")
        return full_plan
