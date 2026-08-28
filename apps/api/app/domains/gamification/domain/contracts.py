from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class GameEventType(str, Enum):
    EXERCISE_COMPLETED = "exercise.completed"
    CONVERSATION_COMPLETED = "conversation.completed"
    PRONUNCIATION_ATTEMPTED = "pronunciation.attempted"
    PRONUNCIATION_IMPROVED = "pronunciation.improved"
    SHADOWING_COMPLETED = "shadowing.completed"
    LEARNING_ITEM_MASTERED = "learning_item.mastered"
    LEARNING_ITEM_IMPROVED = "learning_item.improved"
    DAILY_PLAN_COMPLETED = "daily_plan.completed"
    GOAL_COMPLETED = "goal.completed"
    SESSION_STARTED = "session.started"
    SESSION_COMPLETED = "session.completed"
    REVIEW_COMPLETED = "review.completed"
    BOSS_ATTEMPTED = "boss.attempted"
    BOSS_CLEARED = "boss.cleared"


class GameEventSource(str, Enum):
    LEARNING = "learning"
    CONVERSATION = "conversation"
    PRONUNCIATION = "pronunciation"
    SHADOWING = "shadowing"
    GOAL = "goal"
    STREAK = "streak"
    ACHIEVEMENT = "achievement"
    BOSS = "boss"
    SYSTEM = "system"


class XPCategory(str, Enum):
    CONVERSATION = "conversation"
    EXERCISE = "exercise"
    PRONUNCIATION = "pronunciation"
    SHADOWING = "shadowing"
    MASTERY = "mastery"
    QUEST = "quest"
    ACHIEVEMENT = "achievement"
    STREAK = "streak"
    BOSS = "boss"
    CORRECTION = "correction"
    SPECIAL = "special"


class RankTier(str, Enum):
    BEGINNER = "Beginner (初学者)"
    BRONZE = "Bronze (銅侍)"
    SILVER = "Silver (銀侍)"
    GOLD = "Gold (金侍)"
    PLATINUM = "Platinum (白金達人)"
    DIAMOND = "Diamond (金剛指南役)"
    MASTER = "Master (伝説の師範)"


class AchievementRarity(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class QuestFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MILESTONE = "milestone"
    CHALLENGE = "challenge"
    BOSS = "boss"
    SPECIAL = "special"


class QuestStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CLAIMED = "claimed"
    EXPIRED = "expired"


class UnlockType(str, Enum):
    PERSONA = "persona"
    VOICE_PROFILE = "voice_profile"
    SCENARIO = "scenario"
    TITLE = "title"
    AVATAR_COSMETIC = "avatar_cosmetic"
    THEME = "theme"
    BOSS = "boss"
    SPECIAL_CHALLENGE = "special_challenge"


class NotificationPriority(str, Enum):
    LOW = "low"          # Batchable small XP toast
    NORMAL = "normal"    # Quest complete
    HIGH = "high"        # Level up, Achievement unlocked, Boss clear
