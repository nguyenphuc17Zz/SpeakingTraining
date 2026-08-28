from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domains.users.models import User


class GameProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Cached, fast-lookup progression profile for learner RPG stats.
    Total XP is backed by the immutable XPTransaction ledger.
    """
    __tablename__ = "game_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    rank: Mapped[str] = mapped_column(String(50), default="Beginner (初学者)", nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skill_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_freezes_available: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_active_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    current_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extra_stats: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")


class XPTransaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Immutable ledger of all XP changes.
    Never modify existing rows to reduce rewards — append negative correction transactions instead.
    """
    __tablename__ = "xp_transactions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reward_policy_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    meta_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")


class GameEventRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Outbox / audit log for normalized GameEvents.
    Enforces idempotency and event replay capabilities.
    """
    __tablename__ = "game_event_records"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="processed", nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")


class DailyQuestRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Personalized daily quest instances generated dynamically per user per calendar day.
    """
    __tablename__ = "daily_quest_records"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quest_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    quest_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="daily", nullable=False)
    target_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    objectives_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "quest_date", "quest_key", name="uq_user_daily_quest"),
    )


class WeeklyQuestRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Weekly challenge quests spanning Monday to Sunday based on user timezone.
    """
    __tablename__ = "weekly_quest_records"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    week_key: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-Www
    quest_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_count: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    current_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    objectives_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "week_key", "quest_key", name="uq_user_weekly_quest"),
    )


class AchievementDefinition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Declarative achievement templates.
    """
    __tablename__ = "achievement_definitions"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rarity: Mapped[str] = mapped_column(String(30), default="common", nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="speaking", nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="trophy", nullable=False)
    condition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)


class UserAchievement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User progress and unlock status for achievements.
    """
    __tablename__ = "user_achievements"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    achievement_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("achievement_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    achievement: Mapped["AchievementDefinition"] = relationship("AchievementDefinition", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )


class SkillNodeDefinition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Nodes in the Japanese Speaking Skill Tree.
    Does NOT store separate learner mastery — derives directly from LearningItems!
    """
    __tablename__ = "skill_node_definitions"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # fluency, naturalness, grammar, pronunciation
    icon: Mapped[str] = mapped_column(String(50), default="zap", nullable=False)
    prerequisites_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    linked_item_types_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class UnlockableDefinition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Progression unlocks: personas, voices, scenarios, titles, cosmetics.
    Never locks core AI models or basic learning mechanics.
    """
    __tablename__ = "unlockable_definitions"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    unlock_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    level_required: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    condition_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    asset_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class UserUnlock(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Records which unlockables a user has unlocked/equipped.
    """
    __tablename__ = "user_unlocks"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unlockable_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("unlockable_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
    unlockable: Mapped["UnlockableDefinition"] = relationship("UnlockableDefinition", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "unlockable_id", name="uq_user_unlockable"),
    )


class BossDefinition(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Specialized high-stakes conversation exercise challenge.
    Reuses existing Conversation/Exercise engines.
    """
    __tablename__ = "boss_definitions"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    persona_key: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(30), default="normal", nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    pass_score_threshold: Mapped[float] = mapped_column(Float, default=75.0, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    title_reward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    objectives_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    scenario_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_modifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class BossAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User attempt at a Boss Battle challenge.
    """
    __tablename__ = "boss_attempts"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    boss_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("boss_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_attempt_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    boss: Mapped["BossDefinition"] = relationship("BossDefinition", lazy="selectin")


class RewardNotification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Queued notifications for level up, achievements, quests, and XP gains.
    """
    __tablename__ = "reward_notifications"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    xp_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User")


class DailyStreakActivity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Audit log of qualifying meaningful daily activities for streak computation.
    """
    __tablename__ = "daily_streak_activities"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", "activity_type", "activity_id", name="uq_user_streak_act"),
    )


class GameSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User-configurable gamification preferences.
    """
    __tablename__ = "game_settings"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    gamification_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sound_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    animations_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quest_intensity: Mapped[str] = mapped_column(String(30), default="balanced", nullable=False)  # relaxed, balanced, hardcore
    difficulty_preference: Mapped[str] = mapped_column(String(30), default="balanced", nullable=False)
    show_xp_popups: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
