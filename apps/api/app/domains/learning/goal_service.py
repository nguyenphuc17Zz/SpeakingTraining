from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.models import LearningGoal
from app.shared.errors.exceptions import NotFoundException, ValidationException


class GoalService:
    """Service for managing learner goals and milestone alignments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_default_goals(self, user_id: str) -> list[LearningGoal]:
        """Ensures at least one default speaking goal exists for the user."""
        stmt = select(LearningGoal).where(
            LearningGoal.user_id == user_id,
            LearningGoal.status == "active",
        ).order_by(LearningGoal.priority)
        res = await self.db.execute(stmt)
        goals = res.scalars().all()

        if not goals:
            default_goal = LearningGoal(
                user_id=user_id,
                title="Giao tiếp tự nhiên trong công việc và đời sống",
                description="Tăng tốc độ phản xạ nói, kiểm soát trợ từ và ngữ điệu tự nhiên chuẩn người bản xứ.",
                goal_type="workplace",
                priority=1,
                status="active",
            )
            self.db.add(default_goal)
            await self.db.flush()
            return [default_goal]

        return list(goals)

    async def list_goals(self, user_id: str) -> list[LearningGoal]:
        stmt = select(LearningGoal).where(LearningGoal.user_id == user_id).order_by(LearningGoal.priority)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_active_goals(self, user_id: str) -> list[LearningGoal]:
        stmt = (
            select(LearningGoal)
            .where(LearningGoal.user_id == user_id, LearningGoal.status == "active")
            .order_by(LearningGoal.priority)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_goal(
        self,
        user_id: str,
        title: str,
        goal_type: str = "speaking",
        description: str | None = None,
        priority: int = 1,
        target_date: datetime | None = None,
    ) -> LearningGoal:
        if not title or not title.strip():
            raise ValidationException("Goal title cannot be empty.")

        goal = LearningGoal(
            user_id=user_id,
            title=title.strip(),
            goal_type=goal_type,
            description=description,
            priority=priority,
            status="active",
            target_date=target_date,
        )
        self.db.add(goal)
        await self.db.commit()
        await self.db.refresh(goal)
        return goal

    async def update_goal(
        self,
        goal_id: str,
        user_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: int | None = None,
        target_date: datetime | None = None,
    ) -> LearningGoal:
        stmt = select(LearningGoal).where(LearningGoal.id == goal_id, LearningGoal.user_id == user_id)
        res = await self.db.execute(stmt)
        goal = res.scalar_one_or_none()
        if not goal:
            raise NotFoundException(f"LearningGoal '{goal_id}' not found.")

        if title is not None:
            goal.title = title.strip()
        if description is not None:
            goal.description = description
        if status is not None:
            goal.status = status
        if priority is not None:
            goal.priority = priority
        if target_date is not None:
            goal.target_date = target_date

        await self.db.commit()
        await self.db.refresh(goal)
        return goal
