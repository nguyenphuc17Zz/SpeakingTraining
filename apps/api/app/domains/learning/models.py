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
    from app.domains.conversation.models import ConversationSession
    from app.domains.pronunciation.models import PronunciationAttempt
    from app.domains.users.models import User


class LearningGoal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-level learning priorities and milestones."""
    __tablename__ = "learning_goals"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_type: Mapped[str] = mapped_column(String(50), default="speaking", nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")


class LearningItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stable linguistic unit actively tracked in the adaptive curriculum."""
    __tablename__ = "learning_items"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(30), default="normal", nullable=False)

    lifecycle: Mapped[str] = mapped_column(
        String(30), default="discovered", nullable=False, index=True
    )  # discovered, active, practicing, improving, mastered, maintenance, regressed
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)

    # Multi-dimensional mastery [0.0, 1.0]
    overall_mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recognition_mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    production_mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    spontaneous_mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    context_variety_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    automaticity_mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False, index=True)

    # Progress & Review Metrics
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    independent_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assisted_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    review_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    contexts_used: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_learning_item_user_key"),
    )


class ExerciseTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Curated blueprints for AI-assisted or template-only exercise synthesis."""
    __tablename__ = "exercise_templates"

    template_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_type_affinity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    template_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)

    title_template: Mapped[str] = mapped_column(String(255), nullable=False)
    objective_template: Mapped[str] = mapped_column(Text, nullable=False)
    scenario_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    instruction_template: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_frame: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_pattern_rules: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    default_estimated_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Exercise(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An instantiated learning exercise ready to be practiced by the user."""
    __tablename__ = "exercises"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(30), default="not_started", nullable=False, index=True
    )  # not_started, in_progress, completed, abandoned, expired

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    target_patterns: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    learning_item_keys: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    success_criteria: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    acceptable_variants: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    difficulty: Mapped[str] = mapped_column(String(30), default="normal", nullable=False)
    scaffold_level: Mapped[str] = mapped_column(String(30), default="none", nullable=False)
    scaffold_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    template_version: Mapped[str] = mapped_column(String(30), default="v1", nullable=False)
    generator_version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), default="exercise.gen.v1", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    exercise_signature: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    attempts: Mapped[list["ExerciseAttempt"]] = relationship(
        "ExerciseAttempt",
        back_populates="exercise",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ExerciseAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User attempt record for an exercise with performance measurement and mastery delta."""
    __tablename__ = "exercise_attempts"

    exercise_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    pronunciation_attempt_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("pronunciation_attempts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30), default="in_progress", nullable=False, index=True
    )  # in_progress, completed, abandoned
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    independence_level: Mapped[str] = mapped_column(
        String(30), default="independent", nullable=False
    )  # independent, assisted_hint, retry_success, scaffolded
    response_speed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    assessment_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_usage: Mapped[str | None] = mapped_column(String(30), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    mastery_deltas_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="attempts")
    user: Mapped["User"] = relationship("User")
    session: Mapped["ConversationSession | None"] = relationship("ConversationSession")
    pronunciation_attempt: Mapped["PronunciationAttempt | None"] = relationship("PronunciationAttempt")


class LearningPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Daily personalized learning schedule."""
    __tablename__ = "learning_plans"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    time_budget_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="active", nullable=False, index=True
    )  # active, completed, skipped

    focus_title: Mapped[str] = mapped_column(String(255), nullable=False)
    focus_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    generator_version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    items: Mapped[list["LearningPlanItem"]] = relationship(
        "LearningPlanItem",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="LearningPlanItem.order_index",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "plan_date", name="uq_user_daily_plan_date"),
    )


class LearningPlanItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An individual exercise entry within a daily plan."""
    __tablename__ = "learning_plan_items"

    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("learning_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_type: Mapped[str] = mapped_column(
        String(50), default="targeted_drill", nullable=False
    )  # conversation, targeted_drill, pronunciation, review, exploration
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False, index=True
    )  # pending, in_progress, completed, skipped
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    plan: Mapped["LearningPlan"] = relationship("LearningPlan", back_populates="items")
    exercise: Mapped["Exercise"] = relationship("Exercise", lazy="selectin")
