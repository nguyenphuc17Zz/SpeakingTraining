from datetime import datetime, timezone
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.learner_memory.contracts import LearningPriority
from app.domains.learner_memory.models import LearnerMemory, MemoryEvidence, MemoryFeedback
from app.domains.learner_memory.priority_service import LearningPriorityService
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.learner_memory.queue import learner_memory_job_queue
from app.domains.learner_memory.schemas import (
    LearnerMemoryDetailRead,
    LearnerMemoryRead,
    LearnerProfileRead,
    LearningPriorityRead,
    MemoryEvidenceRead,
    MemoryFeedbackCreate,
    MemoryFeedbackRead,
)
from app.shared.errors.exceptions import NotFoundException, ValidationException


class LearnerMemoryService:
    """Facade domain service for interacting with Learner Memory, Profiles, Evidences, and Priorities."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_service = LearnerProfileService(db)
        self.priority_service = LearningPriorityService(db)

    async def get_profile(self, user_id: str) -> LearnerProfileRead:
        """Retrieves or creates learner profile (auto-recalculates if empty)."""
        profile = await self.profile_service.get_or_create_profile(user_id)
        if profile.total_sessions_analyzed == 0:
            profile = await self.profile_service.recalculate_profile(user_id, generate_ai_summary=True)
        return LearnerProfileRead.model_validate(profile)

    async def recalculate_profile(self, user_id: str) -> LearnerProfileRead:
        """Explicitly triggers full recalculation of learner profile."""
        profile = await self.profile_service.recalculate_profile(user_id, generate_ai_summary=True)
        return LearnerProfileRead.model_validate(profile)

    async def list_memories(
        self,
        user_id: str,
        memory_type: str | None = None,
        status: str | None = None,
        trend: str | None = None,
        min_priority: float | None = None,
        limit: int = 50,
    ) -> list[LearnerMemoryRead]:
        """Lists user memories with optional filtering."""
        stmt = select(LearnerMemory).where(LearnerMemory.user_id == user_id)

        if memory_type:
            stmt = stmt.where(LearnerMemory.memory_type == memory_type)
        if status:
            stmt = stmt.where(LearnerMemory.status == status)
        if trend:
            stmt = stmt.where(LearnerMemory.trend == trend)
        if min_priority is not None:
            stmt = stmt.where(LearnerMemory.priority_score >= min_priority)

        stmt = stmt.order_by(desc(LearnerMemory.priority_score), desc(LearnerMemory.last_seen)).limit(limit)
        res = await self.db.execute(stmt)
        memories = res.scalars().all()
        return [LearnerMemoryRead.model_validate(m) for m in memories]

    async def get_memory_detail(self, user_id: str, memory_id: str) -> LearnerMemoryDetailRead:
        """Retrieves detailed memory with attached evidences."""
        stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.id == memory_id,
                LearnerMemory.user_id == user_id,
            )
            .options(selectinload(LearnerMemory.evidences))
        )
        res = await self.db.execute(stmt)
        mem = res.scalar_one_or_none()
        if not mem:
            raise NotFoundException(f"Learner memory with ID '{memory_id}' not found.")
        return LearnerMemoryDetailRead.model_validate(mem)

    async def get_memory_evidences(self, user_id: str, memory_id: str) -> list[MemoryEvidenceRead]:
        """Retrieves raw evidence items for a specific memory."""
        # Ensure memory belongs to user
        await self.get_memory_detail(user_id, memory_id)

        stmt = (
            select(MemoryEvidence)
            .where(
                MemoryEvidence.memory_id == memory_id,
                MemoryEvidence.user_id == user_id,
            )
            .order_by(desc(MemoryEvidence.created_at))
        )
        res = await self.db.execute(stmt)
        evs = res.scalars().all()
        return [MemoryEvidenceRead.model_validate(e) for e in evs]

    async def get_top_weaknesses(self, user_id: str, limit: int = 5) -> list[LearnerMemoryRead]:
        """Retrieves top prioritized weaknesses."""
        stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.memory_type.in_([
                    "grammar", "particle", "conjugation", "politeness", "filler", "word_choice", "vocabulary", "naturalness"
                ]),
                LearnerMemory.status.notin_(["dismissed", "archived"]),
            )
            .order_by(desc(LearnerMemory.priority_score), desc(LearnerMemory.last_seen))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        memories = res.scalars().all()
        return [LearnerMemoryRead.model_validate(m) for m in memories]

    async def get_top_strengths(self, user_id: str, limit: int = 5) -> list[LearnerMemoryRead]:
        """Retrieves confirmed speaking strengths."""
        stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.memory_type == "strength",
                LearnerMemory.status.notin_(["dismissed", "archived"]),
            )
            .order_by(desc(LearnerMemory.priority_score), desc(LearnerMemory.last_seen))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        memories = res.scalars().all()
        return [LearnerMemoryRead.model_validate(m) for m in memories]

    async def get_goals(self, user_id: str) -> list[LearnerMemoryRead]:
        """Retrieves user learning goals."""
        stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.memory_type == "goal",
            )
            .order_by(desc(LearnerMemory.created_at))
        )
        res = await self.db.execute(stmt)
        memories = res.scalars().all()
        return [LearnerMemoryRead.model_validate(m) for m in memories]

    async def get_learning_priorities(self, user_id: str, limit: int = 5) -> list[LearningPriorityRead]:
        """Retrieves adaptive curriculum priorities."""
        priorities: list[LearningPriority] = await self.priority_service.get_top_learning_priorities(user_id, limit)
        return [
            LearningPriorityRead(
                key=p.key,
                type=p.type.value,
                priority_score=p.priority_score,
                reason=p.reason,
                mastery=p.mastery,
                trend=p.trend.value,
                recommended_focus=p.recommended_focus,
                evidence_count=p.evidence_count,
                last_seen=p.last_seen,
            )
            for p in priorities
        ]

    async def submit_feedback(
        self,
        user_id: str,
        memory_id: str,
        payload: MemoryFeedbackCreate,
    ) -> MemoryFeedbackRead:
        """Applies user feedback / dismissal to a memory."""
        stmt = select(LearnerMemory).where(
            LearnerMemory.id == memory_id,
            LearnerMemory.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        mem = res.scalar_one_or_none()
        if not mem:
            raise NotFoundException(f"Memory with ID '{memory_id}' not found.")

        action = payload.action.strip().lower()
        if action == "dismiss":
            mem.status = "dismissed"
        elif action == "restore":
            mem.status = "active"
        elif action == "mark_inaccurate":
            # Reduce confidence
            mem.confidence = max(0.1, round(mem.confidence * 0.5, 2))
        else:
            raise ValidationException(f"Unsupported action '{payload.action}'. Supported: dismiss, mark_inaccurate, restore.")

        fb = MemoryFeedback(
            memory_id=mem.id,
            user_id=user_id,
            action=action,
            feedback_text=payload.feedback_text,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(fb)
        await self.db.commit()
        await self.db.refresh(fb)
        return MemoryFeedbackRead.model_validate(fb)

    async def enqueue_memory_update(self, user_id: str, session_id: str) -> None:
        """Enqueues async learner memory update job."""
        job_data = {
            "user_id": user_id,
            "session_id": session_id,
            "type": "session_memory_update",
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }
        await learner_memory_job_queue.enqueue(job_data)
        logger.info(f"[LearnerMemoryService] Enqueued memory update job for session '{session_id}' (User: {user_id})")
