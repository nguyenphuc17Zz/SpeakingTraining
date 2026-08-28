from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.conversation_intelligence.contracts import AnalysisJobStatus
from app.domains.conversation_intelligence.models import (
    AnalysisJob,
    AnalysisUserFeedback,
    SessionAnalysis,
    TurnAnalysis,
)
from app.domains.conversation_intelligence.queue import analysis_job_queue
from app.domains.conversation_intelligence.schemas import (
    AnalysisFeedbackCreate,
    AnalysisFeedbackRead,
    AnalysisJobRead,
    ConversationAnalysisSummaryRead,
    SessionAnalysisRead,
    TurnAnalysisRead,
)
from app.domains.users.service import UserService
from app.shared.errors.exceptions import NotFoundException


class ConversationIntelligenceService:
    """Domain service managing conversation intelligence analysis, jobs, and learner feedback."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)

    async def enqueue_turn_analysis(self, session_id: str, turn_id: str) -> AnalysisJobRead:
        """Creates and enqueues a background turn analysis job."""
        job = AnalysisJob(
            type="turn_analysis",
            status=AnalysisJobStatus.QUEUED.value,
            session_id=session_id,
            turn_id=turn_id,
            attempts=0,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)

        await analysis_job_queue.enqueue({
            "job_id": job.id,
            "type": "turn_analysis",
            "session_id": session_id,
            "turn_id": turn_id,
        })
        logger.info(f"[IntelligenceService] Enqueued turn analysis job '{job.id}' for turn '{turn_id}'")
        return AnalysisJobRead.model_validate(job)

    async def enqueue_session_analysis(self, session_id: str) -> AnalysisJobRead:
        """Creates and enqueues a background session analysis job."""
        job = AnalysisJob(
            type="session_analysis",
            status=AnalysisJobStatus.QUEUED.value,
            session_id=session_id,
            attempts=0,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)

        await analysis_job_queue.enqueue({
            "job_id": job.id,
            "type": "session_analysis",
            "session_id": session_id,
        })
        logger.info(f"[IntelligenceService] Enqueued session analysis job '{job.id}' for session '{session_id}'")
        return AnalysisJobRead.model_validate(job)

    async def get_turn_analysis(self, turn_id: str) -> TurnAnalysisRead | None:
        """Retrieves deep analysis for a specific turn."""
        stmt = (
            select(TurnAnalysis)
            .where(TurnAnalysis.turn_id == turn_id)
            .options(
                selectinload(TurnAnalysis.corrections),
                selectinload(TurnAnalysis.grammar_notes),
                selectinload(TurnAnalysis.vocabulary_notes),
            )
        )
        res = await self.session.execute(stmt)
        analysis = res.scalar_one_or_none()
        if not analysis:
            return None
        return TurnAnalysisRead.model_validate(analysis)

    async def get_session_analysis(self, session_id: str) -> SessionAnalysisRead | None:
        """Retrieves session-level analysis."""
        stmt = select(SessionAnalysis).where(SessionAnalysis.session_id == session_id)
        res = await self.session.execute(stmt)
        analysis = res.scalar_one_or_none()
        if not analysis:
            return None
        return SessionAnalysisRead.model_validate(analysis)

    async def get_session_turn_analyses(self, session_id: str) -> list[TurnAnalysisRead]:
        """Retrieves all turn analyses for a session in sequence."""
        stmt = (
            select(TurnAnalysis)
            .where(TurnAnalysis.session_id == session_id)
            .options(
                selectinload(TurnAnalysis.corrections),
                selectinload(TurnAnalysis.grammar_notes),
                selectinload(TurnAnalysis.vocabulary_notes),
            )
            .order_by(TurnAnalysis.created_at.asc())
        )
        res = await self.session.execute(stmt)
        analyses = res.scalars().all()
        return [TurnAnalysisRead.model_validate(a) for a in analyses]

    async def get_session_analysis_summary(self, session_id: str) -> ConversationAnalysisSummaryRead:
        """Retrieves full intelligence summary for a session."""
        session_analysis = await self.get_session_analysis(session_id)
        turn_analyses = await self.get_session_turn_analyses(session_id)

        # Count active/queued jobs
        job_stmt = (
            select(AnalysisJob)
            .where(
                AnalysisJob.session_id == session_id,
                AnalysisJob.status.in_(["queued", "processing"]),
            )
        )
        job_res = await self.session.execute(job_stmt)
        pending_jobs = job_res.scalars().all()

        return ConversationAnalysisSummaryRead(
            session_id=session_id,
            session_analysis=session_analysis,
            turn_analyses=turn_analyses,
            pending_jobs_count=len(pending_jobs),
        )

    async def submit_feedback(
        self,
        feedback_dto: AnalysisFeedbackCreate,
        user_id: str | None = None,
    ) -> AnalysisFeedbackRead:
        """Submits learner feedback on analysis corrections."""
        resolved_user_id = user_id or (await self.user_service.get_or_create_default_user()).id

        feedback = AnalysisUserFeedback(
            user_id=resolved_user_id,
            turn_analysis_id=feedback_dto.turn_analysis_id,
            correction_id=feedback_dto.correction_id,
            rating=feedback_dto.rating.value,
            reason=feedback_dto.reason,
        )
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        return AnalysisFeedbackRead.model_validate(feedback)

    async def get_job_status(self, job_id: str) -> AnalysisJobRead:
        """Retrieves status of a background analysis job."""
        stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
        res = await self.session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise NotFoundException(f"Analysis job '{job_id}' not found.")
        return AnalysisJobRead.model_validate(job)
