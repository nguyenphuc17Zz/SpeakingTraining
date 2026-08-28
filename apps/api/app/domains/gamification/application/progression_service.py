from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gamification.application.achievement_engine import AchievementEngine
from app.domains.gamification.application.anti_farming_service import AntiFarmingService
from app.domains.gamification.application.quest_engine import QuestEngine
from app.domains.gamification.application.streak_service import StreakService
from app.domains.gamification.application.xp_service import XPService
from app.domains.gamification.domain.level_curve import LevelCurve
from app.domains.gamification.models import DailyQuestRecord, GameProfile, UserAchievement, XPTransaction
from app.domains.gamification.schemas import GameProfileDTO, XPOverviewDTO, XPTransactionDTO


class ProgressionService:
    """
    High-level facade for aggregated learner progression and RPG dashboard metrics.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.xp_service = XPService(db)
        self.streak_service = StreakService(db)
        self.quest_engine = QuestEngine(db)
        self.achievement_engine = AchievementEngine(db)

    async def get_game_profile_dto(self, user_id: str) -> GameProfileDTO:
        """Returns comprehensive GameProfile with level progress and today's activity stats."""
        profile = await self.xp_service.get_or_create_profile(user_id)
        tz_name = await self.streak_service.get_user_timezone(user_id)
        today_str = self.streak_service.get_current_date_in_tz(tz_name)

        # Level progress calculation
        level_info = LevelCurve.level_progress_info(profile.total_xp)

        # Today's XP earned
        today_xp_stmt = (
            select(func.coalesce(func.sum(XPTransaction.amount), 0))
            .where(
                XPTransaction.user_id == user_id,
                XPTransaction.created_at >= datetime.strptime(f"{today_str} 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
            )
        )
        today_xp_res = await self.db.execute(today_xp_stmt)
        today_xp = int(today_xp_res.scalar() or 0)

        # Today's completed quests count
        quests = await self.quest_engine.ensure_daily_quests(user_id)
        completed_quests_count = sum(1 for q in quests if q.status in ("completed", "claimed"))

        # Total unlocked achievements count
        ach_stmt = (
            select(func.count(UserAchievement.id))
            .where(UserAchievement.user_id == user_id, UserAchievement.is_unlocked == True)
        )
        ach_res = await self.db.execute(ach_stmt)
        ach_count = int(ach_res.scalar() or 0)

        return GameProfileDTO(
            user_id=profile.user_id,
            total_xp=profile.total_xp,
            level=profile.level,
            rank=profile.rank,
            current_streak=profile.current_streak,
            longest_streak=profile.longest_streak,
            skill_points=profile.skill_points,
            streak_freezes_available=profile.streak_freezes_available,
            current_title=profile.current_title,
            level_progress=level_info,
            today_xp=today_xp,
            today_completed_quests=completed_quests_count,
            total_unlocked_achievements=ach_count,
            last_active_date=profile.last_active_date,
        )

    async def get_xp_overview(self, user_id: str) -> XPOverviewDTO:
        """Returns breakdown of XP earned across categories and recent transactions."""
        profile = await self.xp_service.get_or_create_profile(user_id)
        tz_name = await self.streak_service.get_user_timezone(user_id)
        today_str = self.streak_service.get_current_date_in_tz(tz_name)

        # Today's XP
        today_xp_stmt = (
            select(func.coalesce(func.sum(XPTransaction.amount), 0))
            .where(
                XPTransaction.user_id == user_id,
                XPTransaction.created_at >= datetime.strptime(f"{today_str} 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
            )
        )
        today_xp_res = await self.db.execute(today_xp_stmt)
        today_xp = int(today_xp_res.scalar() or 0)

        # Category Breakdown
        breakdown = await self.xp_service.get_category_breakdown(user_id)

        # Recent Transactions
        txs = await self.xp_service.get_xp_history(user_id, limit=20)
        tx_dtos = [
            XPTransactionDTO(
                id=tx.id,
                amount=tx.amount,
                category=tx.category,
                reason=tx.reason,
                source_type=tx.source_type,
                source_id=tx.source_id,
                created_at=tx.created_at,
                reward_policy_version=tx.reward_policy_version,
            )
            for tx in txs
        ]

        return XPOverviewDTO(
            total_xp=profile.total_xp,
            level=profile.level,
            today_xp=today_xp,
            week_xp=sum(breakdown.values()),
            category_breakdown=breakdown,
            recent_transactions=tx_dtos,
        )
