from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.models import DailyStreakActivity, XPTransaction


class AntiFarmingService:
    """
    Prevents XP farming and botting while protecting legitimate deliberate practice.
    Rule: Repetitive practice updates learning mastery normally, but XP returns diminish deterministically.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_repetition_count_today(
        self,
        user_id: str,
        source_id: str,
        today_date_str: str,
    ) -> int:
        """
        Counts how many times this specific source_id (e.g. same exercise or sentence target)
        has been awarded XP today.
        """
        stmt = (
            select(func.count(XPTransaction.id))
            .where(
                XPTransaction.user_id == user_id,
                XPTransaction.source_id == source_id,
                XPTransaction.created_at >= datetime.strptime(f"{today_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar() or 0

    async def get_daily_category_xp(
        self,
        user_id: str,
        category: str,
        today_date_str: str,
    ) -> int:
        """
        Calculates total XP earned in a specific category today to enforce soft caps.
        """
        stmt = (
            select(func.coalesce(func.sum(XPTransaction.amount), 0))
            .where(
                XPTransaction.user_id == user_id,
                XPTransaction.category == category,
                XPTransaction.created_at >= datetime.strptime(f"{today_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar() or 0
