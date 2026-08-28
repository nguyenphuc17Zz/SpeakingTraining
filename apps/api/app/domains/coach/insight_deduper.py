"""CoachInsightDeduper §26 — anti-spam cooldown."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.models import InsightRecord


class CoachInsightDeduper:
    """Dedup by insight_signature with cooldown + evidence delta."""

    def __init__(self, db: AsyncSession, cooldown_hours: int = 48):
        self.db = db
        self.cooldown_hours = cooldown_hours

    def signature(self, insight_type: str, metric_key: str | None, target: str | None = None) -> str:
        raw = f"{insight_type}:{metric_key or ''}:{target or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def should_surface(self, user_id: str, insight_type: str, metric_key: str | None, evidence_delta: int = 0) -> tuple[bool, str]:
        sig = self.signature(insight_type, metric_key)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.cooldown_hours)
        stmt = select(InsightRecord).where(
            InsightRecord.user_id == user_id,
            InsightRecord.insight_type == insight_type,
            InsightRecord.metric_key == metric_key,
            InsightRecord.created_at >= cutoff,
        ).limit(1)
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if not existing:
            return True, "no_recent_insight"
        # if new evidence materially larger, allow re-surface
        if evidence_delta and evidence_delta >= 3:
            return True, "material_new_evidence"
        return False, f"cooldown_active until {(existing.created_at + timedelta(hours=self.cooldown_hours)).isoformat()}"

    async def mark_shown(self, user_id: str, insight_type: str, metric_key: str | None) -> None:
        # InsightRecord creation is done by InsightEngine; deduper just checks.
        pass
