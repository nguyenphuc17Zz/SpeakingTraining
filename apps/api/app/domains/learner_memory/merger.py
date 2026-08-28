from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learner_memory.contracts import MemoryCandidate
from app.domains.learner_memory.models import LearnerMemory, MemoryEvidence


class MemoryMerger:
    """Handles memory deduplication, merging candidates into existing user memories and attaching evidence idempotently."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def merge_candidates(
        self,
        user_id: str,
        candidates: list[MemoryCandidate],
    ) -> list[LearnerMemory]:
        """Merges a list of extracted candidates into user's persistent memories."""
        if not candidates:
            return []

        affected_memories: dict[str, LearnerMemory] = {}

        for candidate in candidates:
            # 1. Look up existing memory by (user_id, key)
            stmt = select(LearnerMemory).where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.key == candidate.key,
            )
            res = await self.db.execute(stmt)
            memory = res.scalar_one_or_none()

            now_utc = datetime.now(timezone.utc)
            is_new = False

            if not memory:
                # Create new memory
                is_correct = candidate.evidence_type in ("correct_observation", "strength", "turn_strength", "session_strength")
                memory = LearnerMemory(
                    user_id=user_id,
                    memory_type=candidate.memory_type.value,
                    key=candidate.key,
                    statement=candidate.statement,
                    category=candidate.category,
                    evidence_count=1,
                    confidence=candidate.confidence,
                    severity=candidate.severity,
                    severity_score=candidate.severity_score,
                    priority_score=0.5,
                    mastery=0.7 if is_correct else 0.1,
                    attempt_count=1,
                    correct_count=1 if is_correct else 0,
                    error_count=0 if is_correct else 1,
                    first_seen=now_utc,
                    last_seen=now_utc,
                    trend="new",
                    status="new" if not is_correct else "stable",
                    is_regression=False,
                    contexts_used=[candidate.context_tag] if candidate.context_tag else [],
                    extra_metadata=candidate.metadata,
                )
                self.db.add(memory)
                await self.db.flush()
                is_new = True

            # 2. Check Idempotency: Has this evidence already been attached?
            ev_check_stmt = select(MemoryEvidence).where(
                MemoryEvidence.memory_id == memory.id,
                MemoryEvidence.session_id == candidate.session_id,
                MemoryEvidence.turn_id == candidate.turn_id,
                MemoryEvidence.correction_id == candidate.correction_id,
                MemoryEvidence.evidence_type == candidate.evidence_type,
            )
            ev_res = await self.db.execute(ev_check_stmt)
            existing_ev = ev_res.scalar_one_or_none()

            if not existing_ev:
                # Create and attach new evidence
                ev_time = candidate.created_at or now_utc
                evidence = MemoryEvidence(
                    memory_id=memory.id,
                    user_id=user_id,
                    session_id=candidate.session_id,
                    turn_id=candidate.turn_id,
                    turn_analysis_id=candidate.turn_analysis_id,
                    correction_id=candidate.correction_id,
                    evidence_type=candidate.evidence_type,
                    weight=candidate.evidence_weight,
                    original_snippet=candidate.original_snippet,
                    corrected_snippet=candidate.corrected_snippet,
                    context_tag=candidate.context_tag,
                    created_at=ev_time,
                )
                self.db.add(evidence)

                if not is_new:
                    # Update stats
                    memory.evidence_count += 1
                    memory.attempt_count += 1
                    is_correct = candidate.evidence_type in ("correct_observation", "strength", "turn_strength", "session_strength")
                    if is_correct:
                        memory.correct_count += 1
                    else:
                        memory.error_count += 1

                    ev_time_utc = ev_time if ev_time.tzinfo else ev_time.replace(tzinfo=timezone.utc)
                    last_seen_utc = memory.last_seen if memory.last_seen.tzinfo else memory.last_seen.replace(tzinfo=timezone.utc)

                    if ev_time_utc > last_seen_utc:
                        memory.last_seen = ev_time_utc

                    # Check for regression if previously resolved
                    if memory.status == "resolved" and not is_correct:
                        logger.info(f"[MemoryMerger] Regression detected for resolved memory '{memory.key}'")
                        memory.status = "active"
                        memory.is_regression = True

                    # Update context tags
                    current_contexts = list(memory.contexts_used or [])
                    if candidate.context_tag and candidate.context_tag not in current_contexts:
                        current_contexts.append(candidate.context_tag)
                        memory.contexts_used = list(current_contexts)

                    # Update statement if current is longer/richer
                    if len(candidate.statement) > len(memory.statement):
                        memory.statement = candidate.statement

            affected_memories[memory.id] = memory

        await self.db.flush()
        return list(affected_memories.values())
