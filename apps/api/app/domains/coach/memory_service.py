"""CoachMemoryService §10-12 + CoachLearningMemory semantic layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.coach.contracts import MemoryType
from app.domains.learner_memory.models import LearnerMemory, MemoryEvidence


class CoachMemoryService:
    """Dedicated semantic layer over existing learner data. §10."""

    # Thresholds §12
    SINGLE_OBSERVATION_MIN = 1
    CANDIDATE_MIN_EVIDENCE = 3
    PERSISTENT_MIN_EVIDENCE = 5
    PERSISTENT_MIN_CONFIDENCE = 0.75

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_memories(
        self, user_id: str, limit: int = 20, memory_type: str | None = None
    ) -> list[LearnerMemory]:
        stmt = (
            select(LearnerMemory)
            .where(LearnerMemory.user_id == user_id, LearnerMemory.status == "active")
            .order_by(desc(LearnerMemory.priority_score))
            .limit(limit)
        )
        if memory_type:
            stmt = stmt.where(LearnerMemory.memory_type == memory_type)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_persistent_errors(self, user_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.status == "active",
                LearnerMemory.error_count >= self.PERSISTENT_MIN_EVIDENCE,
                LearnerMemory.confidence >= self.PERSISTENT_MIN_CONFIDENCE,
            )
            .order_by(desc(LearnerMemory.priority_score))
            .limit(10)
        )
        res = await self.db.execute(stmt)
        mems = list(res.scalars().all())
        return [
            {
                "type": MemoryType.PERSISTENT_ERROR.value,
                "key": m.memory_key,
                "statement": m.statement,
                "confidence": m.confidence,
                "evidence_count": m.evidence_count,
                "error_count": m.error_count,
                "trend": m.trend,
                "mastery": m.mastery,
                "priority_score": m.priority_score,
            }
            for m in mems
        ]

    async def evaluate_memory_promotion(self, user_id: str, memory_key: str) -> dict[str, Any]:
        """Implements confidence governance §12: single → temporary, repeated → candidate, stable → persistent."""
        stmt = select(LearnerMemory).where(LearnerMemory.user_id == user_id, LearnerMemory.memory_key == memory_key)
        res = await self.db.execute(stmt)
        mem = res.scalar_one_or_none()
        if not mem:
            return {"status": "no_memory", "key": memory_key}
        cnt = mem.evidence_count or 1
        if cnt < self.CANDIDATE_MIN_EVIDENCE:
            return {"status": "temporary_insight", "key": memory_key, "evidence_count": cnt, "message": "Your recent attempts suggest... (need more evidence)"}
        if cnt < self.PERSISTENT_MIN_EVIDENCE or mem.confidence < self.PERSISTENT_MIN_CONFIDENCE:
            return {"status": "candidate_pattern", "key": memory_key, "evidence_count": cnt, "confidence": mem.confidence, "message": "Repeated comparable observations — candidate pattern."}
        return {"status": "persistent_learning_memory", "key": memory_key, "evidence_count": cnt, "confidence": mem.confidence, "statement": mem.statement}

    async def get_learner_summary(self, user_id: str) -> dict[str, Any]:
        """For Coach to retrieve profile without raw DB dump."""
        mems = await self.list_memories(user_id, limit=7)
        strengths = [m for m in mems if m.confidence > 0.8 and m.mastery > 0.6][:3]
        weaknesses = [m for m in mems if m.error_count >= 3][:4]
        return {
            "strengths": [{"key": m.memory_key, "statement": m.statement, "mastery": m.mastery} for m in strengths],
            "weaknesses": [{"key": m.memory_key, "statement": m.statement, "confidence": m.confidence, "evidence_count": m.evidence_count} for m in weaknesses],
            "total_memories": len(mems),
        }

    def to_memory_payload(self, mem: LearnerMemory) -> dict[str, Any]:
        return {
            "type": mem.memory_type,
            "skill": mem.memory_key,
            "statement": mem.statement,
            "confidence": mem.confidence,
            "evidence_count": mem.evidence_count,
            "error_count": mem.error_count,
            "mastery": mem.mastery,
            "trend": mem.trend,
            "created_at": mem.created_at.isoformat() if mem.created_at else None,
            "updated_at": mem.updated_at.isoformat() if mem.updated_at else None,
        }
