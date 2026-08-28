from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.domains.analytics.domain.metric_definitions import ConfidenceLevel, MetricKey


class InsightType(str, Enum):
    IMPROVEMENT = "improvement"
    REGRESSION = "regression"
    PLATEAU = "plateau"
    STRENGTH = "strength"
    RISK = "risk"
    MILESTONE = "milestone"
    OPPORTUNITY = "opportunity"
    CONSISTENCY = "consistency"
    GOAL_STALLED = "goal_stalled"
    TRANSFER_GAP = "transfer_gap"
    STUCK_PATTERN = "stuck_pattern"


class InsightLifecycle(str, Enum):
    NEW = "new"
    SEEN = "seen"
    ACTED_ON = "acted_on"
    EXPIRED = "expired"


@dataclass
class Insight:
    id: str
    user_id: str
    insight_type: InsightType
    title: str
    description: str
    confidence: ConfidenceLevel
    metric_key: MetricKey | None = None
    metric_value: float | None = None
    action_hint: str | None = None
    action_target_type: str | None = None  # conversation, drill, shadowing, pronunciation
    action_target_key: str | None = None
    evidence_keys: list[str] = field(default_factory=list)
    source_metrics: dict[str, Any] = field(default_factory=dict)
    source_period: str = "30d"
    lifecycle: InsightLifecycle = InsightLifecycle.NEW
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
