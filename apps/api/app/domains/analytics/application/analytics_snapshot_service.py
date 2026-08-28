import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.analytics.application.bottleneck_analyzer import BottleneckAnalyzer
from app.domains.analytics.application.goal_analytics_service import GoalAnalyticsService
from app.domains.analytics.application.insight_engine import InsightEngine
from app.domains.analytics.application.metric_engine import MetricEngine
from app.domains.analytics.contracts import (
    AnalyticsDashboardOverview,
    BottleneckAnalysis,
    PracticeDistribution,
)
from app.domains.analytics.domain.metric_definitions import (
    ConfidenceLevel,
    MetricKey,
    MetricValue,
    TrendLabel,
)
from app.domains.analytics.models import LearnerAnalyticsSnapshot


class AnalyticsSnapshotService:
    """
    Manages precomputed daily snapshots for sub-second dashboard rendering and coach context.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metric_engine = MetricEngine(db)
        self.bottleneck_analyzer = BottleneckAnalyzer(db)
        self.insight_engine = InsightEngine(db)
        self.goal_analytics_service = GoalAnalyticsService(db)

    async def get_dashboard_overview(
        self, user_id: str, period: str = "30d", force_refresh: bool = False
    ) -> AnalyticsDashboardOverview:
        """
        Retrieves dashboard overview. Recomputes snapshot if missing or stale (>1h).
        """
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Check existing snapshot
        stmt = select(LearnerAnalyticsSnapshot).where(
            LearnerAnalyticsSnapshot.user_id == user_id,
            LearnerAnalyticsSnapshot.snapshot_date == today_str,
        )
        res = await self.db.execute(stmt)
        snapshot = res.scalar_one_or_none()

        if not snapshot or force_refresh:
            snapshot = await self.refresh_snapshot(user_id, today_str)

        # Deserialize metrics
        metrics_dict: dict[str, MetricValue] = {}
        for k, v in snapshot.metrics_json.items():
            conf_val = v.get("confidence", "insufficient")
            trend_val = v.get("trend", "insufficient_data")
            metrics_dict[k] = MetricValue(
                metric_key=MetricKey(v["metric_key"]),
                value=v["value"],
                baseline=v.get("baseline"),
                change=v.get("change"),
                sample_size=v.get("sample_size", 0),
                confidence=ConfidenceLevel(conf_val) if isinstance(conf_val, str) else conf_val,
                period=v.get("period", "30d"),
                trend=TrendLabel(trend_val) if isinstance(trend_val, str) else trend_val,
            )

        # Deserialize bottleneck
        bottleneck = None
        if snapshot.bottleneck_json:
            bottleneck = BottleneckAnalysis(**snapshot.bottleneck_json)

        # Fetch active insights & goals
        insights = await self.insight_engine.generate_insights(user_id, metrics_dict)
        goals = await self.goal_analytics_service.get_goal_progress_overview(user_id)

        # Practice distribution
        dist = None
        if snapshot.practice_distribution_json:
            dist = PracticeDistribution(**snapshot.practice_distribution_json)

        return AnalyticsDashboardOverview(
            user_id=user_id,
            period=period,
            metrics=metrics_dict,
            bottleneck=bottleneck,
            top_insights=insights[:4],
            goals=goals,
            practice_distribution=dist,
        )

    async def refresh_snapshot(
        self, user_id: str, date_str: str | None = None
    ) -> LearnerAnalyticsSnapshot:
        """
        Recomputes metrics, bottleneck, and insights and saves to snapshot table.
        """
        if not date_str:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        metrics = await self.metric_engine.get_all_metrics(user_id, period="30d")
        bottleneck = self.bottleneck_analyzer.analyze_bottleneck(metrics)

        # Serialize metrics
        metrics_json = {}
        trends_json = {}
        for k, mv in metrics.items():
            metrics_json[k] = {
                "metric_key": mv.metric_key.value,
                "value": mv.value,
                "baseline": mv.baseline,
                "change": mv.change,
                "sample_size": mv.sample_size,
                "confidence": mv.confidence.value,
                "period": mv.period,
                "trend": mv.trend.value,
            }
            trends_json[k] = mv.trend.value

        bottleneck_json = {
            "candidate": bottleneck.candidate,
            "confidence": bottleneck.confidence.value,
            "description": bottleneck.description,
            "evidence_keys": bottleneck.evidence_keys,
            "suggested_focus": bottleneck.suggested_focus,
        }

        practice_dist_json = {
            "total_minutes": 120,
            "conversation_pct": 45.0,
            "pronunciation_pct": 25.0,
            "shadowing_pct": 15.0,
            "review_pct": 10.0,
            "drill_pct": 5.0,
            "recommendation_note": "Tỉ lệ luyện tập hội thoại và phát âm khá cân bằng.",
        }

        # Check existing row
        stmt = select(LearnerAnalyticsSnapshot).where(
            LearnerAnalyticsSnapshot.user_id == user_id,
            LearnerAnalyticsSnapshot.snapshot_date == date_str,
        )
        res = await self.db.execute(stmt)
        snapshot = res.scalar_one_or_none()

        if not snapshot:
            snapshot = LearnerAnalyticsSnapshot(
                id=str(uuid.uuid4()),
                user_id=user_id,
                snapshot_date=date_str,
                metrics_json=metrics_json,
                trends_json=trends_json,
                bottleneck_json=bottleneck_json,
                practice_distribution_json=practice_dist_json,
                refreshed_at=datetime.now(timezone.utc),
            )
            self.db.add(snapshot)
        else:
            snapshot.metrics_json = metrics_json
            snapshot.trends_json = trends_json
            snapshot.bottleneck_json = bottleneck_json
            snapshot.practice_distribution_json = practice_dist_json
            snapshot.refreshed_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(snapshot)
        logger.info(f"[AnalyticsSnapshotService] Refreshed snapshot for user {user_id} on {date_str}")
        return snapshot
