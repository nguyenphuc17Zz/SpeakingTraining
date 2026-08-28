"""CoachProactiveTriggerEngine §27-28 — thresholded insights, not spam."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.analytics.application.bottleneck_analyzer import BottleneckAnalyzer
from app.domains.analytics.application.metric_engine import MetricEngine
from app.domains.analytics.domain.metric_definitions import ConfidenceLevel
from app.domains.coach.contracts import ProactiveThresholds
from app.domains.coach.insight_deduper import CoachInsightDeduper
from app.domains.learning.models import ExerciseAttempt


class CoachProactiveTriggerEngine:
    """Evaluates triggers after exercise attempts; respects thresholds §28."""

    def __init__(self, db: AsyncSession, thresholds: ProactiveThresholds | None = None):
        self.db = db
        self.thresholds = thresholds or ProactiveThresholds()
        self.metric_engine = MetricEngine(db)
        self.bottleneck = BottleneckAnalyzer(db)
        self.deduper = CoachInsightDeduper(db, cooldown_hours=self.thresholds.cooldown_hours)

    async def evaluate_for_user(self, user_id: str) -> list[dict[str, Any]]:
        """Returns list of proactive insight candidates (not yet persisted)."""
        insights: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # fetch recent attempts (last 30 days, up to 50)
        cutoff = now - timedelta(days=30)
        stmt = (
            select(ExerciseAttempt)
            .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed", ExerciseAttempt.completed_at >= cutoff)
            .order_by(desc(ExerciseAttempt.completed_at))
            .limit(50)
        )
        res = await self.db.execute(stmt)
        attempts = list(res.scalars().all())
        if len(attempts) < self.thresholds.minimum_attempts:
            return []

        # Trigger 1: repeated identical mistake (5 similar failures)
        failed = [a for a in attempts[:10] if not a.success]
        if len(failed) >= 5:
            # group by exercise_type prefix
            from collections import Counter
            types = Counter((a.metrics_json or {}).get("reflex", {}).get("sub_mode") or a.feedback[:30] if a.feedback else "unknown" for a in failed)
            for t, cnt in types.items():
                if cnt >= 5:
                    ok, _ = await self.deduper.should_surface(user_id, "REPEATED_MISTAKE", t, evidence_delta=cnt)
                    if ok:
                        insights.append({
                            "insight_type": "REPEATED_MISTAKE",
                            "severity": "MEDIUM",
                            "confidence": 0.88,
                            "description": f"Bạn đã gặp lỗi tương tự {cnt} lần gần đây ({t}). Thử một drill tập trung 5 phút?",
                            "recommended_action": "REFLEX_CONJUGATION" if "reflex" in t.lower() else "PRACTICE",
                            "evidence": {"fail_count": cnt, "sample": t},
                        })
                    break

        # Fetch metrics once for triggers 2 & 3 (reduce N+1)
        metrics_cache = None
        try:
            metrics_cache = await self.metric_engine.get_all_metrics(user_id, period="30d")
        except Exception as e:
            logger.warning(f"[CoachProactive] metric fetch failed: {e}")

        # Trigger 2: mastery threshold / personal best via metrics
        try:
            if metrics_cache:
                for mv in metrics_cache.values():
                    if mv.trend.value in ("strongly_improving", "improving") and mv.sample_size >= 8 and mv.confidence == ConfidenceLevel.HIGH:
                        ok, _ = await self.deduper.should_surface(user_id, "STRONG_PROGRESS", mv.metric_key.value, evidence_delta=mv.sample_size)
                        if ok:
                            insights.append({
                                "insight_type": "STRONG_PROGRESS",
                                "severity": "LOW",
                                "confidence": 0.82,
                                "description": f"Bạn đang tiến bộ rõ ở {mv.metric_key.value} (+{mv.change:.1f}) — duy trì đà này!",
                                "evidence": {"metric": mv.metric_key.value, "value": mv.value, "change": mv.change, "sample_count": mv.sample_size},
                            })
                        break
        except Exception as e:
            logger.warning(f"[CoachProactive] metric check failed: {e}")

        # Trigger 3: bottleneck new weakness via bottleneck analyzer
        try:
            if metrics_cache:
                bottleneck = self.bottleneck.analyze_bottleneck(metrics_cache)
                if bottleneck.confidence == ConfidenceLevel.HIGH and bottleneck.candidate != "Balanced Development (バランス良好)":
                    ok, _ = await self.deduper.should_surface(user_id, "BOTTLENECK", bottleneck.candidate)
                    if ok:
                        insights.append({
                            "insight_type": "BOTTLENECK",
                            "severity": "HIGH",
                            "confidence": 0.90,
                            "description": bottleneck.description,
                            "recommended_action": bottleneck.suggested_focus,
                            "evidence": {"candidate": bottleneck.candidate, "evidence_keys": bottleneck.evidence_keys},
                        })
        except Exception:
            pass

        # Persist insights as InsightRecord for dedup + audit (§6 persist)
        if insights:
            try:
                import uuid
                from app.domains.analytics.models import InsightRecord
                now2 = datetime.now(timezone.utc)
                for ins in insights:
                    rec = InsightRecord(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        insight_type=ins["insight_type"],
                        title=ins["insight_type"],
                        description=ins["description"],
                        confidence=str(ins.get("confidence", "medium")),
                        metric_key=ins.get("evidence", {}).get("metric"),
                        metric_value=ins.get("evidence", {}).get("value") if isinstance(ins.get("evidence", {}).get("value"), (int, float)) else None,
                        evidence_keys_json=list(ins.get("evidence", {}).keys()) if isinstance(ins.get("evidence"), dict) else [],
                        source_metrics_json=ins.get("evidence"),
                        source_period="30d",
                        lifecycle="new",
                        expires_at=now2 + timedelta(days=self.thresholds.insight_ttl_days),
                    )
                    self.db.add(rec)
                await self.db.commit()
            except Exception as e:
                logger.warning(f"[CoachProactive] persist failed: {e}")
                await self.db.rollback()

        return insights
