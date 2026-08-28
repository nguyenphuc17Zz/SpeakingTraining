from datetime import datetime, timedelta, timezone
from typing import Any
import zoneinfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import GameEventType, XPCategory
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.models import DailyQuestRecord, WeeklyQuestRecord
from app.domains.gamification.schemas import QuestDTO
from app.domains.learning.models import LearningGoal, LearningItem
from app.domains.settings.models import UserSettings


class QuestEngine:
    """
    Manages daily and weekly quest generation, event-driven objective tracking, and completion rewards.
    Quests are dynamically personalized based on active learning goals and weaknesses.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_timezone(self, user_id: str) -> str:
        stmt = select(UserSettings.timezone).where(UserSettings.user_id == user_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() or "Asia/Tokyo"

    def _resolve_tz(self, tz_name: str) -> timezone | zoneinfo.ZoneInfo:
        try:
            return zoneinfo.ZoneInfo(tz_name)
        except Exception:
            try:
                return zoneinfo.ZoneInfo("Asia/Tokyo")
            except Exception:
                # Fallback for Windows environments without tzdata package
                return timezone(timedelta(hours=9))

    def get_today_str(self, tz_name: str) -> str:
        tz = self._resolve_tz(tz_name)
        return datetime.now(tz).strftime("%Y-%m-%d")

    def get_current_week_key(self, tz_name: str) -> str:
        tz = self._resolve_tz(tz_name)
        dt = datetime.now(tz)
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"

    async def ensure_daily_quests(self, user_id: str) -> list[DailyQuestRecord]:
        """
        Ensures today's 3 personalized daily quests exist for the user.
        """
        tz_name = await self.get_user_timezone(user_id)
        today_str = self.get_today_str(tz_name)

        # Check existing
        stmt = select(DailyQuestRecord).where(
            DailyQuestRecord.user_id == user_id,
            DailyQuestRecord.quest_date == today_str,
        )
        res = await self.db.execute(stmt)
        existing = list(res.scalars().all())

        if len(existing) >= 3:
            return existing

        # Fetch learner context for personalization
        item_stmt = (
            select(LearningItem)
            .where(LearningItem.user_id == user_id, LearningItem.status == "active")
            .limit(3)
        )
        item_res = await self.db.execute(item_stmt)
        active_items = list(item_res.scalars().all())
        focus_title = active_items[0].title if active_items else "Japanese Daily Speaking"

        # Define 3 Standard / Personalized Daily Quests
        now_utc = datetime.now(timezone.utc)
        expires_at = now_utc + timedelta(hours=24)

        quest_defs = [
            {
                "key": "daily_speaking_duration",
                "title": "Natural Conversation (日常会話)",
                "description": "Engage in at least 5 minutes of spoken conversation with an AI partner.",
                "category": "conversation",
                "target_count": 5,  # 5 minutes
                "xp_reward": BALANCE_CONFIG.XP_DAILY_QUEST_DEFAULT,
                "objectives": {"event_type": "conversation.completed", "metric": "duration_minutes", "min_per_event": 1},
            },
            {
                "key": "daily_exercise_practice",
                "title": f"Target Practice: {focus_title}",
                "description": "Complete 2 interactive speaking drills or roleplays.",
                "category": "exercise",
                "target_count": 2,
                "xp_reward": BALANCE_CONFIG.XP_DAILY_QUEST_DEFAULT,
                "objectives": {"event_type": "exercise.completed", "metric": "count"},
            },
            {
                "key": "daily_pronunciation_drill",
                "title": "Pronunciation & Pitch (発音・アクセント)",
                "description": "Record and analyze at least 2 pronunciation or shadowing segments.",
                "category": "pronunciation",
                "target_count": 2,
                "xp_reward": BALANCE_CONFIG.XP_DAILY_QUEST_DEFAULT,
                "objectives": {"event_types": ["pronunciation.attempted", "shadowing.completed"], "metric": "count"},
            },
        ]

        created_quests = []
        existing_keys = {q.quest_key for q in existing}

        for qd in quest_defs:
            if qd["key"] not in existing_keys:
                quest = DailyQuestRecord(
                    user_id=user_id,
                    quest_date=today_str,
                    quest_key=qd["key"],
                    title=qd["title"],
                    description=qd["description"],
                    category=qd["category"],
                    target_count=qd["target_count"],
                    current_count=0,
                    xp_reward=qd["xp_reward"],
                    status="active",
                    expires_at=expires_at,
                    objectives_json=qd["objectives"],
                )
                self.db.add(quest)
                created_quests.append(quest)

        if created_quests:
            await self.db.commit()
            for q in created_quests:
                await self.db.refresh(q)

        return existing + created_quests

    async def ensure_weekly_quests(self, user_id: str) -> list[WeeklyQuestRecord]:
        """
        Ensures active weekly quests exist for the current ISO week.
        """
        tz_name = await self.get_user_timezone(user_id)
        week_key = self.get_current_week_key(tz_name)

        stmt = select(WeeklyQuestRecord).where(
            WeeklyQuestRecord.user_id == user_id,
            WeeklyQuestRecord.week_key == week_key,
        )
        res = await self.db.execute(stmt)
        existing = list(res.scalars().all())

        if len(existing) >= 2:
            return existing

        now_utc = datetime.now(timezone.utc)
        expires_at = now_utc + timedelta(days=7)

        weekly_defs = [
            {
                "key": "weekly_exercise_master",
                "title": "Weekly Speaking Mastery (週間スピーキング特訓)",
                "description": "Complete 10 speaking exercises or roleplays this week.",
                "target_count": 10,
                "xp_reward": BALANCE_CONFIG.XP_WEEKLY_QUEST_DEFAULT,
                "objectives": {"event_type": "exercise.completed", "metric": "count"},
            },
            {
                "key": "weekly_conversation_sessions",
                "title": "Conversation Marathon (会話マラソン)",
                "description": "Complete 5 distinct conversation sessions with AI personas.",
                "target_count": 5,
                "xp_reward": BALANCE_CONFIG.XP_WEEKLY_QUEST_DEFAULT,
                "objectives": {"event_type": "conversation.completed", "metric": "count"},
            },
        ]

        created_weekly = []
        existing_keys = {w.quest_key for w in existing}

        for wd in weekly_defs:
            if wd["key"] not in existing_keys:
                wquest = WeeklyQuestRecord(
                    user_id=user_id,
                    week_key=week_key,
                    quest_key=wd["key"],
                    title=wd["title"],
                    description=wd["description"],
                    target_count=wd["target_count"],
                    current_count=0,
                    xp_reward=wd["xp_reward"],
                    status="active",
                    expires_at=expires_at,
                    objectives_json=wd["objectives"],
                )
                self.db.add(wquest)
                created_weekly.append(wquest)

        if created_weekly:
            await self.db.commit()
            for w in created_weekly:
                await self.db.refresh(w)

        return existing + created_weekly

    async def process_event_for_quests(
        self,
        event: GameEvent,
    ) -> list[dict[str, Any]]:
        """
        Updates matching daily and weekly quests based on incoming GameEvent.
        Returns a list of newly completed quests: [{type, title, xp_reward, quest_id}]
        """
        user_id = event.user_id
        daily_quests = await self.ensure_daily_quests(user_id)
        weekly_quests = await self.ensure_weekly_quests(user_id)

        completed_notifications = []

        # 1. Update Daily Quests
        for quest in daily_quests:
            if quest.status != "active":
                continue

            obj = quest.objectives_json or {}
            event_type_match = False
            if "event_type" in obj and obj["event_type"] == event.type.value:
                event_type_match = True
            elif "event_types" in obj and event.type.value in obj["event_types"]:
                event_type_match = True

            if event_type_match:
                increment = 1
                if obj.get("metric") == "duration_minutes":
                    dur_secs = event.metadata.get("duration_seconds", 60)
                    increment = max(1, int(dur_secs // 60))

                quest.current_count = min(quest.target_count, quest.current_count + increment)

                if quest.current_count >= quest.target_count:
                    quest.status = "completed"
                    quest.completed_at = datetime.now(timezone.utc)
                    completed_notifications.append({
                        "quest_type": "daily",
                        "quest_id": quest.id,
                        "title": quest.title,
                        "xp_reward": quest.xp_reward,
                    })
                    logger.info(f"[QuestEngine] Daily quest '{quest.title}' completed by user {user_id}")

        # 2. Update Weekly Quests
        for wquest in weekly_quests:
            if wquest.status != "active":
                continue

            obj = wquest.objectives_json or {}
            if obj.get("event_type") == event.type.value:
                wquest.current_count = min(wquest.target_count, wquest.current_count + 1)
                if wquest.current_count >= wquest.target_count:
                    wquest.status = "completed"
                    wquest.completed_at = datetime.now(timezone.utc)
                    completed_notifications.append({
                        "quest_type": "weekly",
                        "quest_id": wquest.id,
                        "title": wquest.title,
                        "xp_reward": wquest.xp_reward,
                    })
                    logger.info(f"[QuestEngine] Weekly quest '{wquest.title}' completed by user {user_id}")

        await self.db.commit()
        return completed_notifications

    async def get_all_active_quests_dto(self, user_id: str) -> list[QuestDTO]:
        """Returns unified list of active/completed daily & weekly quests."""
        daily_quests = await self.ensure_daily_quests(user_id)
        weekly_quests = await self.ensure_weekly_quests(user_id)

        dtos = []
        for dq in daily_quests:
            ratio = min(1.0, dq.current_count / max(1, dq.target_count))
            dtos.append(
                QuestDTO(
                    id=dq.id,
                    quest_key=dq.quest_key,
                    title=dq.title,
                    description=dq.description,
                    frequency="daily",
                    target_count=dq.target_count,
                    current_count=dq.current_count,
                    progress_ratio=round(ratio, 2),
                    xp_reward=dq.xp_reward,
                    status=dq.status,
                    is_completed=dq.status in ("completed", "claimed"),
                    expires_at=dq.expires_at,
                    category=dq.category,
                )
            )

        for wq in weekly_quests:
            ratio = min(1.0, wq.current_count / max(1, wq.target_count))
            dtos.append(
                QuestDTO(
                    id=wq.id,
                    quest_key=wq.quest_key,
                    title=wq.title,
                    description=wq.description,
                    frequency="weekly",
                    target_count=wq.target_count,
                    current_count=wq.current_count,
                    progress_ratio=round(ratio, 2),
                    xp_reward=wq.xp_reward,
                    status=wq.status,
                    is_completed=wq.status in ("completed", "claimed"),
                    expires_at=wq.expires_at,
                    category="weekly",
                )
            )

        return dtos
