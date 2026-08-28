import uuid
from datetime import datetime, timezone
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.models import RecommendationRecord


class RecommendationTracker:
    """Tracks recommendation delivery and subsequent learner completion outcomes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_recommendation(
        self,
        user_id: str,
        action_type: str,
        target: str,
        reason: str,
        duration_minutes: int = 10,
        conversation_id: str | None = None,
    ) -> RecommendationRecord:
        record = RecommendationRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
            action_type=action_type,
            target=target,
            reason=reason,
            duration_minutes=duration_minutes,
            status="recommended",
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def update_status(
        self, recommendation_id: str, status: str
    ) -> RecommendationRecord | None:
        stmt = select(RecommendationRecord).where(RecommendationRecord.id == recommendation_id)
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            return None

        record.status = status
        if status == "completed":
            record.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(record)
        return record
