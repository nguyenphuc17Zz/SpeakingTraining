from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.domains.gamification.domain.contracts import (
    AchievementRarity,
    NotificationPriority,
    QuestFrequency,
    QuestStatus,
    RankTier,
    UnlockType,
    XPCategory,
)


class GameProfileDTO(BaseModel):
    user_id: str
    total_xp: int
    level: int
    rank: str
    current_streak: int
    longest_streak: int
    skill_points: int
    streak_freezes_available: int
    current_title: str | None = None
    level_progress: dict[str, Any] = Field(default_factory=dict)
    today_xp: int = 0
    today_completed_quests: int = 0
    total_unlocked_achievements: int = 0
    last_active_date: str | None = None


class XPTransactionDTO(BaseModel):
    id: str
    amount: int
    category: str
    reason: str
    source_type: str
    source_id: str
    created_at: datetime
    reward_policy_version: str


class XPOverviewDTO(BaseModel):
    total_xp: int
    level: int
    today_xp: int
    week_xp: int
    category_breakdown: dict[str, int] = Field(default_factory=dict)
    recent_transactions: list[XPTransactionDTO] = Field(default_factory=list)


class QuestDTO(BaseModel):
    id: str
    quest_key: str
    title: str
    description: str
    frequency: str  # daily, weekly, challenge
    target_count: int
    current_count: int
    progress_ratio: float
    xp_reward: int
    status: str
    is_completed: bool
    expires_at: datetime | None = None
    category: str = "general"


class AchievementDTO(BaseModel):
    id: str
    key: str
    title: str
    description: str
    rarity: str
    category: str
    icon: str
    xp_reward: int
    is_unlocked: bool
    unlocked_at: datetime | None = None
    current_value: float
    target_value: float
    progress_ratio: float
    is_hidden: bool = False


class SkillNodeDTO(BaseModel):
    key: str
    name: str
    description: str
    category: str
    icon: str
    status: str  # locked, available, developing, strong, mastered
    current_mastery: float  # 0.0 - 1.0 derived from LearningEngine
    attempt_count: int
    prerequisites: list[str] = Field(default_factory=list)
    linked_learning_items: list[dict[str, Any]] = Field(default_factory=list)
    recommended_exercise_type: str | None = None


class SkillTreeOverviewDTO(BaseModel):
    categories: list[str]
    nodes: list[SkillNodeDTO]
    overall_mastery_average: float
    mastered_count: int
    total_nodes: int


class UnlockableDTO(BaseModel):
    id: str
    key: str
    unlock_type: str
    title: str
    description: str
    level_required: int
    is_unlocked: bool
    unlocked_at: datetime | None = None
    is_equipped: bool = False
    asset_reference: str | None = None


class BossDTO(BaseModel):
    id: str
    key: str
    name: str
    subtitle: str
    description: str
    difficulty: str
    required_level: int
    is_unlocked: bool
    pass_score_threshold: float
    xp_reward: int
    title_reward: str | None = None
    objectives: list[str] = Field(default_factory=list)
    personal_best_score: float | None = None
    cleared: bool = False
    total_attempts: int = 0


class BossStartResponseDTO(BaseModel):
    boss_id: str
    boss_name: str
    exercise_id: str
    session_id: str | None = None
    persona_key: str
    instructions: str
    objectives: list[str] = Field(default_factory=list)


class BossAttemptResultDTO(BaseModel):
    attempt_id: str
    boss_id: str
    score: float
    passed: bool
    xp_awarded: int
    title_awarded: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    feedback: str | None = None
    weak_points: list[str] = Field(default_factory=list)
    recommended_training: str | None = None


class RewardNotificationDTO(BaseModel):
    id: str
    notification_type: str
    priority: str
    title: str
    message: str
    xp_amount: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    is_read: bool
    created_at: datetime


class StreakOverviewDTO(BaseModel):
    current_streak: int
    longest_streak: int
    streak_freezes_available: int
    is_qualified_today: bool
    today_activities_count: int
    qualifying_threshold_met: bool
    last_active_date: str | None = None
    activity_history_last_7_days: list[dict[str, Any]] = Field(default_factory=list)


class GameSettingsDTO(BaseModel):
    gamification_enabled: bool
    sound_enabled: bool
    animations_enabled: bool
    quest_intensity: str
    difficulty_preference: str
    show_xp_popups: bool


class UpdateGameSettingsDTO(BaseModel):
    gamification_enabled: bool | None = None
    sound_enabled: bool | None = None
    animations_enabled: bool | None = None
    quest_intensity: str | None = None
    difficulty_preference: str | None = None
    show_xp_popups: bool | None = None
