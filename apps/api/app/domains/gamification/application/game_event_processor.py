from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.application.achievement_engine import AchievementEngine
from app.domains.gamification.application.anti_farming_service import AntiFarmingService
from app.domains.gamification.application.notification_service import GamificationNotificationService
from app.domains.gamification.application.quest_engine import QuestEngine
from app.domains.gamification.application.streak_service import StreakService
from app.domains.gamification.application.unlock_service import UnlockService
from app.domains.gamification.application.xp_service import XPService
from app.domains.gamification.domain.contracts import NotificationPriority, XPCategory
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.domain.reward_policy import RewardPolicy
from app.domains.gamification.models import GameEventRecord, GameSettings


class EventProcessingResult(BaseModel):
    is_duplicate: bool = False
    xp_awarded: int = 0
    xp_category: str | None = None
    reason: str | None = None
    did_level_up: bool = False
    new_level: int = 1
    completed_quests: list[dict[str, Any]] = Field(default_factory=list)
    unlocked_achievements: list[dict[str, Any]] = Field(default_factory=list)
    unlocked_items: list[dict[str, Any]] = Field(default_factory=list)
    current_streak: int = 0
    is_streak_incremented: bool = False


class GameEventProcessor:
    """
    Central, idempotent event processor.
    Subscribes to all normalized learning events, applies reward policies,
    updates quests, checks achievements & unlocks, and triggers notifications.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.xp_service = XPService(db)
        self.streak_service = StreakService(db)
        self.anti_farming = AntiFarmingService(db)
        self.quest_engine = QuestEngine(db)
        self.achievement_engine = AchievementEngine(db)
        self.unlock_service = UnlockService(db)
        self.notification_service = GamificationNotificationService(db)

    async def get_or_create_settings(self, user_id: str) -> GameSettings:
        stmt = select(GameSettings).where(GameSettings.user_id == user_id)
        res = await self.db.execute(stmt)
        settings = res.scalar_one_or_none()
        if not settings:
            settings = GameSettings(user_id=user_id, gamification_enabled=True)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
        return settings

    async def process_event(self, event: GameEvent) -> EventProcessingResult:
        """
        Idempotently processes a GameEvent.
        Guarantees that re-processing the same event will NOT award duplicate XP.
        """
        user_id = event.user_id
        event_key = event.event_id

        # 1. Idempotency Check
        stmt = select(GameEventRecord).where(GameEventRecord.event_key == event_key)
        res = await self.db.execute(stmt)
        existing_record = res.scalar_one_or_none()

        if existing_record:
            logger.info(f"[GameEventProcessor] Event '{event_key}' already processed. Skipping duplicate.")
            return EventProcessingResult(is_duplicate=True)

        # Record event in outbox
        record = GameEventRecord(
            user_id=user_id,
            event_key=event_key,
            event_type=event.type.value,
            source=event.source.value,
            source_id=event.source_id,
            status="processing",
            metadata_json=event.metadata,
            occurred_at=event.occurred_at,
        )
        self.db.add(record)
        await self.db.commit()

        # 2. Check Game Settings (Gamification ON/OFF)
        settings = await self.get_or_create_settings(user_id)
        gamification_enabled = settings.gamification_enabled

        # 3. Update Streak (Meaningful learning activities always qualify for streak)
        streak_val, streak_inc = await self.streak_service.record_qualifying_activity(
            user_id=user_id,
            activity_type=event.type.value,
            activity_id=event.source_id,
        )

        if not gamification_enabled:
            record.status = "processed_no_game"
            await self.db.commit()
            return EventProcessingResult(
                is_duplicate=False,
                current_streak=streak_val,
                is_streak_incremented=streak_inc,
            )

        # 4. Anti-Farming & XP Calculation
        tz_name = await self.streak_service.get_user_timezone(user_id)
        today_str = self.streak_service.get_current_date_in_tz(tz_name)

        repetition_count = await self.anti_farming.get_repetition_count_today(
            user_id=user_id,
            source_id=event.source_id,
            today_date_str=today_str,
        )

        category_guess = XPCategory.EXERCISE.value
        category_xp_today = await self.anti_farming.get_daily_category_xp(
            user_id=user_id,
            category=category_guess,
            today_date_str=today_str,
        )

        reward_calc = RewardPolicy.calculate_reward(
            event=event,
            repetition_count_today=repetition_count,
            daily_category_xp_so_far=category_xp_today,
        )

        # 5. Grant XP Transaction
        tx, did_level_up, old_lvl, new_lvl = await self.xp_service.grant_xp(
            user_id=user_id,
            amount=reward_calc.xp_amount,
            category=reward_calc.category,
            reason=reward_calc.reason,
            source_type=event.source.value,
            source_id=event.source_id,
            event_id=event_key,
            policy_version=reward_calc.policy_version,
            metadata=reward_calc.metadata,
        )

        # 6. Update Quests
        completed_quests = await self.quest_engine.process_event_for_quests(event)
        for q in completed_quests:
            # Award Quest completion XP
            await self.xp_service.grant_xp(
                user_id=user_id,
                amount=q["xp_reward"],
                category=XPCategory.QUEST,
                reason=f"Quest Complete: {q['title']}",
                source_type="quest",
                source_id=q["quest_id"],
                event_id=f"quest:{q['quest_id']}:{today_str}",
            )
            await self.notification_service.enqueue_notification(
                user_id=user_id,
                notification_type="quest_completed",
                title="Quest Completed! (クエスト達成)",
                message=f"You completed: {q['title']} (+{q['xp_reward']} XP)",
                priority=NotificationPriority.NORMAL,
                xp_amount=q["xp_reward"],
            )

        # 7. Evaluate Achievements
        unlocked_achievements = await self.achievement_engine.evaluate_achievements(user_id, event)
        for ach in unlocked_achievements:
            await self.xp_service.grant_xp(
                user_id=user_id,
                amount=ach["xp_reward"],
                category=XPCategory.ACHIEVEMENT,
                reason=f"Achievement Unlocked: {ach['title']}",
                source_type="achievement",
                source_id=ach["achievement_id"],
                event_id=f"ach:{ach['achievement_id']}",
            )
            await self.notification_service.enqueue_notification(
                user_id=user_id,
                notification_type="achievement_unlocked",
                title="Achievement Unlocked! 🏆",
                message=f"{ach['title']}: {ach['description']} (+{ach['xp_reward']} XP)",
                priority=NotificationPriority.HIGH,
                xp_amount=ach["xp_reward"],
                payload=ach,
            )

        # 8. Check Level-up & Unlocks
        unlocked_items = []
        if did_level_up:
            await self.notification_service.enqueue_notification(
                user_id=user_id,
                notification_type="level_up",
                title="🎉 LEVEL UP! (レベルアップ)",
                message=f"Congratulations! You reached RPG Level {new_lvl}! (+1 Skill Point)",
                priority=NotificationPriority.HIGH,
                payload={"old_level": old_lvl, "new_level": new_lvl},
            )
            unlocked_items = await self.unlock_service.evaluate_unlocks(user_id)
            for itm in unlocked_items:
                await self.notification_service.enqueue_notification(
                    user_id=user_id,
                    notification_type="item_unlocked",
                    title="New Unlock Available! 🎁",
                    message=f"Unlocked {itm['unlock_type']}: {itm['title']}",
                    priority=NotificationPriority.NORMAL,
                    payload=itm,
                )

        record.status = "processed"
        await self.db.commit()

        return EventProcessingResult(
            is_duplicate=False,
            xp_awarded=reward_calc.xp_amount,
            xp_category=reward_calc.category.value,
            reason=reward_calc.reason,
            did_level_up=did_level_up,
            new_level=new_lvl,
            completed_quests=completed_quests,
            unlocked_achievements=unlocked_achievements,
            unlocked_items=unlocked_items,
            current_streak=streak_val,
            is_streak_incremented=streak_inc,
        )
