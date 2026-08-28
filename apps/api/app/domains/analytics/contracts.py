from typing import Any, Protocol
from pydantic import BaseModel, Field

from app.domains.analytics.domain.metric_definitions import (
    ConfidenceLevel,
    MetricDefinition,
    MetricKey,
    MetricValue,
    TrendLabel,
)
from app.domains.analytics.domain.insight_types import Insight, InsightType


class BottleneckAnalysis(BaseModel):
    candidate: str
    confidence: ConfidenceLevel
    description: str
    evidence_keys: list[str] = Field(default_factory=list)
    suggested_focus: str | None = None


class GoalProgressOverview(BaseModel):
    goal_id: str
    title: str
    goal_type: str
    progress_ratio: float  # 0.0 - 1.0
    confidence: ConfidenceLevel
    recent_activity_count: int
    linked_items_count: int
    blocked_by: str | None = None
    next_actions: list[str] = Field(default_factory=list)


class PracticeDistribution(BaseModel):
    total_minutes: int
    conversation_pct: float
    pronunciation_pct: float
    shadowing_pct: float
    review_pct: float
    drill_pct: float
    recommendation_note: str | None = None


class WeeklyFacts(BaseModel):
    week_start: str  # YYYY-MM-DD
    speaking_minutes: int
    session_count: int
    active_days_count: int
    metrics_summary: dict[str, Any] = Field(default_factory=dict)
    top_wins: list[str] = Field(default_factory=list)
    top_weaknesses: list[str] = Field(default_factory=list)
    goal_progress: list[dict[str, Any]] = Field(default_factory=list)
    practice_distribution: dict[str, float] = Field(default_factory=dict)


class AnalyticsDashboardOverview(BaseModel):
    user_id: str
    period: str
    metrics: dict[str, MetricValue]
    bottleneck: BottleneckAnalysis | None = None
    top_insights: list[Insight] = Field(default_factory=list)
    goals: list[GoalProgressOverview] = Field(default_factory=list)
    practice_distribution: PracticeDistribution | None = None


class AnalyticsEngineProtocol(Protocol):
    """Protocol for derived analytics, metric computations, and learner diagnostic intelligence."""

    async def get_dashboard(self, user_id: str, period: str = "30d") -> AnalyticsDashboardOverview:
        ...

    async def get_metric(self, user_id: str, key: MetricKey, period: str = "30d") -> MetricValue:
        ...


__all__ = [
    "MetricKey",
    "MetricValue",
    "MetricDefinition",
    "TrendLabel",
    "ConfidenceLevel",
    "Insight",
    "InsightType",
    "BottleneckAnalysis",
    "GoalProgressOverview",
    "PracticeDistribution",
    "WeeklyFacts",
    "AnalyticsDashboardOverview",
    "AnalyticsEngineProtocol",
]
