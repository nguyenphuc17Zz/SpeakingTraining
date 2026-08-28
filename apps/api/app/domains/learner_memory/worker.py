import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.conversation.models import ConversationSession
from app.domains.conversation_intelligence.models import SessionAnalysis, TurnAnalysis
from app.domains.learner_memory.extractor import MemoryExtractor
from app.domains.learner_memory.merger import MemoryMerger
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.learner_memory.queue import learner_memory_job_queue
from app.infrastructure.database.session import AsyncSessionLocal


class LearnerMemoryWorker:
    """Background worker that continuously ingests session analysis results into long-term Learner Memory and recalculates Profiles."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self.jobs_processed: int = 0
        self.jobs_failed: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    async def execute_update(
        self,
        user_id: str,
        session_id: str,
        db_session: AsyncSession,
    ) -> None:
        """Executes a full memory extraction and profile recalculation for a session."""
        logger.info(f"[LearnerMemoryWorker] Processing memory update for session '{session_id}' (User: {user_id})")

        # 1. Load session with persona to determine context tag
        s_stmt = (
            select(ConversationSession)
            .where(ConversationSession.id == session_id)
            .options(selectinload(ConversationSession.persona))
        )
        s_res = await db_session.execute(s_stmt)
        conv_session = s_res.scalar_one_or_none()
        if not conv_session:
            logger.warning(f"[LearnerMemoryWorker] Session '{session_id}' not found.")
            return

        context_tag = "casual"
        if conv_session.persona:
            role_l = conv_session.persona.role.lower()
            if "boss" in role_l or "interview" in role_l or "colleague" in role_l or "work" in role_l:
                context_tag = "workplace"
            elif "travel" in role_l or "hotel" in role_l or "airport" in role_l or "restaurant" in role_l:
                context_tag = "travel"

        # 2. Fetch Turn Analyses
        ta_stmt = (
            select(TurnAnalysis)
            .where(TurnAnalysis.session_id == session_id)
            .options(
                selectinload(TurnAnalysis.corrections),
                selectinload(TurnAnalysis.grammar_notes),
                selectinload(TurnAnalysis.vocabulary_notes),
            )
        )
        ta_res = await db_session.execute(ta_stmt)
        turn_analyses = ta_res.scalars().all()

        # 3. Fetch Session Analysis
        sa_stmt = select(SessionAnalysis).where(SessionAnalysis.session_id == session_id)
        sa_res = await db_session.execute(sa_stmt)
        session_analysis = sa_res.scalar_one_or_none()

        # 4. Extract Candidates
        candidates = []
        for ta in turn_analyses:
            candidates.extend(
                MemoryExtractor.extract_from_turn_analysis(ta, context_tag=context_tag)
            )

        if session_analysis:
            candidates.extend(
                MemoryExtractor.extract_from_session_analysis(session_analysis, context_tag=context_tag)
            )

        logger.info(f"[LearnerMemoryWorker] Extracted {len(candidates)} memory candidates from session '{session_id}'")

        # 5. Merge Candidates into Persistent Memory
        merger = MemoryMerger(db_session)
        affected_memories = await merger.merge_candidates(user_id=user_id, candidates=candidates)
        logger.info(f"[LearnerMemoryWorker] Merged candidates into {len(affected_memories)} persistent memories.")

        # 6. Recalculate Long-Term Learner Profile
        profile_service = LearnerProfileService(db_session)
        await profile_service.recalculate_profile(user_id=user_id, generate_ai_summary=True)
        logger.info(f"[LearnerMemoryWorker] Completed memory & profile update for user '{user_id}'.")

    async def _worker_loop(self) -> None:
        """Continuous async worker loop."""
        logger.info("[LearnerMemoryWorker] Worker loop started.")
        while self._running:
            try:
                job_data = await learner_memory_job_queue.dequeue(timeout_seconds=2.0)
                if not job_data:
                    continue

                user_id = job_data.get("user_id")
                session_id = job_data.get("session_id")
                if not user_id or not session_id:
                    continue

                async with AsyncSessionLocal() as session:
                    await self.execute_update(user_id, session_id, session)
                self.jobs_processed += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.jobs_failed += 1
                logger.error(f"[LearnerMemoryWorker] Unexpected error in loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info("[LearnerMemoryWorker] Worker loop stopped.")

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None


# Global singleton instance
learner_memory_worker = LearnerMemoryWorker()
