from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import AchievementRarity, GameEventType
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.models import (
    AchievementDefinition,
    BossAttempt,
    GameProfile,
    UserAchievement,
    XPTransaction,
)
from app.domains.gamification.schemas import AchievementDTO
from app.domains.learning.models import LearningItem


class AchievementEngine:
    """
    Evaluates declarative achievement conditions against learner events, streaks, boss clears, and mastery.
    Achievements reward meaningful learning milestones, never superficial click farming.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_user_achievements(self, user_id: str) -> list[UserAchievement]:
        """Ensures user achievement tracking rows exist for all definitions."""
        defs_stmt = select(AchievementDefinition)
        defs_res = await self.db.execute(defs_stmt)
        definitions = list(defs_res.scalars().all())

        user_stmt = select(UserAchievement).where(UserAchievement.user_id == user_id)
        user_res = await self.db.execute(user_stmt)
        existing = {ua.achievement_id: ua for ua in user_res.scalars().all()}

        created = []
        for d in definitions:
            if d.id not in existing:
                ua = UserAchievement(
                    user_id=user_id,
                    achievement_id=d.id,
                    current_value=0.0,
                    is_unlocked=False,
                )
                self.db.add(ua)
                created.append(ua)

        if created:
            await self.db.commit()
            for ua in created:
                await self.db.refresh(ua)

        all_res = await self.db.execute(select(UserAchievement).where(UserAchievement.user_id == user_id))
        return list(all_res.scalars().all())

    async def evaluate_achievements(
        self,
        user_id: str,
        event: GameEvent | None = None,
    ) -> list[dict[str, Any]]:
        """
        Evaluates conditions for all locked achievements.
        Returns a list of newly unlocked achievements: [{achievement_id, title, xp_reward, rarity, icon}]
        """
        user_achievements = await self.ensure_user_achievements(user_id)
        prof_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()

        unlocked_list = []

        for ua in user_achievements:
            if ua.is_unlocked:
                continue

            definition = ua.achievement
            if not definition:
                continue

            cond_type = definition.condition_type
            target_val = definition.target_value
            current_val = ua.current_value

            # 1. Evaluate Condition Types
            if cond_type == "conversation_count":
                cnt_stmt = select(func.count(XPTransaction.id)).where(
                    XPTransaction.user_id == user_id,
                    XPTransaction.category == "conversation",
                )
                cnt_res = await self.db.execute(cnt_stmt)
                current_val = float(cnt_res.scalar() or 0)

            elif cond_type == "streak_days":
                current_val = float(profile.current_streak if profile else 0)

            elif cond_type == "shadowing_count":
                cnt_stmt = select(func.count(XPTransaction.id)).where(
                    XPTransaction.user_id == user_id,
                    XPTransaction.category == "shadowing",
                )
                cnt_res = await self.db.execute(cnt_stmt)
                current_val = float(cnt_res.scalar() or 0)

            elif cond_type == "pronunciation_count":
                cnt_stmt = select(func.count(XPTransaction.id)).where(
                    XPTransaction.user_id == user_id,
                    XPTransaction.category == "pronunciation",
                )
                cnt_res = await self.db.execute(cnt_stmt)
                current_val = float(cnt_res.scalar() or 0)

            elif cond_type == "mastered_items_count":
                m_stmt = select(func.count(LearningItem.id)).where(
                    LearningItem.user_id == user_id,
                    LearningItem.lifecycle.in_(["mastered", "maintenance"]),
                )
                m_res = await self.db.execute(m_stmt)
                current_val = float(m_res.scalar() or 0)

            elif cond_type == "boss_cleared_count":
                b_stmt = select(func.count(BossAttempt.id)).where(
                    BossAttempt.user_id == user_id,
                    BossAttempt.passed == True,
                )
                b_res = await self.db.execute(b_stmt)
                current_val = float(b_res.scalar() or 0)

            elif cond_type == "level_reached":
                current_val = float(profile.level if profile else 1)

            ua.current_value = current_val

            # Check Unlock Threshold
            if current_val >= target_val and not ua.is_unlocked:
                ua.is_unlocked = True
                ua.unlocked_at = datetime.now(timezone.utc)
                unlocked_list.append({
                    "achievement_id": definition.id,
                    "key": definition.key,
                    "title": definition.title,
                    "description": definition.description,
                    "rarity": definition.rarity,
                    "icon": definition.icon,
                    "xp_reward": definition.xp_reward,
                })
                logger.info(f"[AchievementEngine] Achievement '{definition.title}' unlocked by user {user_id}!")

        if unlocked_list:
            await self.db.commit()

        return unlocked_list

    async def get_achievements_dto(self, user_id: str) -> list[AchievementDTO]:
        """Returns structured achievement catalog with user progress ratios."""
        user_achievements = await self.ensure_user_achievements(user_id)
        dtos = []
        for ua in user_achievements:
            d = ua.achievement
            if not d:
                continue
            ratio = min(1.0, max(0.0, ua.current_value / max(0.001, d.target_value)))
            dtos.append(
                AchievementDTO(
                    id=d.id,
                    key=d.key,
                    title=d.title,
                    description=d.description if (ua.is_unlocked or not d.is_hidden) else "??? (Hidden Achievement)",
                    rarity=d.rarity,
                    category=d.category,
                    icon=d.icon,
                    xp_reward=d.xp_reward,
                    is_unlocked=ua.is_unlocked,
                    unlocked_at=ua.unlocked_at,
                    current_value=ua.current_value,
                    target_value=d.target_value,
                    progress_ratio=round(ratio, 2),
                    is_hidden=d.is_hidden,
                )
            )
        return dtos
