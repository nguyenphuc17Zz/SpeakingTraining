from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class MetricValueDTO(BaseModel):
    metric_key: str
    name: str
    ja_name: str
    unit: str
    category: str
    value: float
    baseline: float | None = None
    change: float | None = None
    sample_size: int = 0
    confidence: str = "insufficient"
    period: str = "30d"
    trend: str = "insufficient_data"
    metric_version: str = "1.0.0"
    description: str = ""
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class GoalProgressDTO(BaseModel):
    goal_id: str
    title: str
    goal_type: str
    progress_ratio: float
    confidence: str
    recent_activity_count: int
    linked_items_count: int
    blocked_by: str | None = None
    next_actions: list[str] = Field(default_factory=list)


class PracticeDistributionDTO(BaseModel):
    total_minutes: int
    conversation_pct: float
    pronunciation_pct: float
    shadowing_pct: float
    review_pct: float
    drill_pct: float
    recommendation_note: str | None = None


class BottleneckDTO(BaseModel):
    candidate: str
    confidence: str
    description: str
    evidence_keys: list[str] = Field(default_factory=list)
    suggested_focus: str | None = None


class InsightDTO(BaseModel):
    id: str
    insight_type: str
    title: str
    description: str
    confidence: str
    metric_key: str | None = None
    metric_value: float | None = None
    action_hint: str | None = None
    action_target_type: str | None = None
    action_target_key: str | None = None
    evidence_keys: list[str] = Field(default_factory=list)
    lifecycle: str = "new"
    generated_at: datetime | None = None


class WeeklyReviewDTO(BaseModel):
    week_start: str
    speaking_minutes: int
    session_count: int
    active_days_count: int
    metrics_summary: dict[str, Any] = Field(default_factory=dict)
    top_wins: list[str] = Field(default_factory=list)
    top_weaknesses: list[str] = Field(default_factory=list)
    goal_progress: list[dict[str, Any]] = Field(default_factory=list)
    practice_distribution: dict[str, float] = Field(default_factory=dict)
    narrative: str | None = None
    is_ai_generated: bool = False
    recommendations: list[dict[str, Any]] = Field(default_factory=list)


class AnalyticsDashboardDTO(BaseModel):
    user_id: str
    period: str
    metrics: dict[str, MetricValueDTO]
    bottleneck: BottleneckDTO | None = None
    top_insights: list[InsightDTO] = Field(default_factory=list)
    goals: list[GoalProgressDTO] = Field(default_factory=list)
    practice_distribution: PracticeDistributionDTO | None = None


class CoachAskRequest(BaseModel):
    question: str
    session_context_id: str | None = None


class CoachRecommendationDTO(BaseModel):
    id: str | None = None
    action_type: str  # conversation, drill, shadowing, pronunciation
    target: str
    reason: str
    duration_minutes: int = 10
    expected_signal: str | None = None
    practice_url: str | None = None


class CoachAnswerDTO(BaseModel):
    answer: str
    intent_type: str
    key_points: list[str] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[CoachRecommendationDTO] = Field(default_factory=list)
    confidence: str = "medium"
    is_deterministic: bool = False
    context_hash: str | None = None
    generated_at: datetime | None = None


class CoachFeedbackRequest(BaseModel):
    conversation_id: str
    rating: str  # helpful, not_helpful, incorrect
    feedback_text: str | None = None


class DailyBriefingDTO(BaseModel):
    date: str
    yesterday_summary: str
    today_focus_title: str
    today_focus_reason: str
    recommendation: CoachRecommendationDTO | None = None
    streak_status: str | None = None


class CoachQuickCardDTO(BaseModel):
    card_type: str  # progress, weakness, this_week, goals, what_to_practice
    title: str
    summary: str
    metrics_snippet: list[dict[str, Any]] = Field(default_factory=list)
    action_cta: str | None = None
    action_url: str | None = None
