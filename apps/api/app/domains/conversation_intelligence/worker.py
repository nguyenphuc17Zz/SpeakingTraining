import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.conversation_intelligence.analyzers.orchestrator import AnalysisOrchestrator
from app.domains.conversation_intelligence.contracts import ConversationAnalysisInput
from app.domains.conversation_intelligence.models import (
    AnalysisCorrection,
    AnalysisJob,
    GrammarNote,
    SessionAnalysis,
    TurnAnalysis,
    VocabularyNote,
)
from app.domains.conversation_intelligence.queue import analysis_job_queue
from app.infrastructure.database.session import AsyncSessionLocal


class AnalysisWorker:
    """Processes background conversation intelligence jobs."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self.jobs_processed: int = 0
        self.jobs_failed: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    async def recover_stale_jobs(self) -> int:
        """Recovers any jobs left in 'processing' state from an unexpected worker restart."""
        recovered = 0
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(AnalysisJob).where(AnalysisJob.status == "processing")
                res = await session.execute(stmt)
                stale_jobs = res.scalars().all()
                for job in stale_jobs:
                    if job.attempts >= job.max_attempts:
                        job.status = "failed"
                        job.error = "Failed permanently: worker restarted during maximum attempt"
                    else:
                        job.status = "queued"
                    recovered += 1
                if recovered > 0:
                    await session.commit()
                    logger.info(f"[AnalysisWorker] Recovered {recovered} stale analysis jobs on startup.")
        except Exception as e:
            logger.warning(f"[AnalysisWorker] Stale job recovery encountered an error: {e}")
        return recovered

    async def execute_job(self, job_id: str, db_session: AsyncSession) -> None:
        """Executes a single analysis job in a database transaction."""
        stmt = select(AnalysisJob).where(AnalysisJob.id == job_id)
        res = await db_session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            logger.warning(f"[AnalysisWorker] Job '{job_id}' not found.")
            return

        if job.status == "completed":
            logger.info(f"[AnalysisWorker] Job '{job_id}' is already completed.")
            return

        job.status = "processing"
        job.attempts += 1
        job.started_at = datetime.now(timezone.utc)
        await db_session.commit()

        orchestrator = AnalysisOrchestrator(db_session)

        try:
            if job.type == "turn_analysis" and job.turn_id:
                await self._process_turn_analysis(job, orchestrator, db_session)
            elif job.type == "session_analysis":
                await self._process_session_analysis(job, orchestrator, db_session)
            else:
                raise ValueError(f"Unknown or invalid job type: {job.type}")

            job.status = "completed"
            job.error = None
            job.completed_at = datetime.now(timezone.utc)
            await db_session.commit()
            self.jobs_processed += 1
            logger.info(f"[AnalysisWorker] Job '{job_id}' ({job.type}) completed successfully.")

        except Exception as e:
            logger.error(f"[AnalysisWorker] Job '{job_id}' failed on attempt {job.attempts}: {e}", exc_info=True)
            self.jobs_failed += 1
            job.error = str(e)
            job.status = "failed" if job.attempts >= job.max_attempts else "queued"
            await db_session.commit()

    async def _process_turn_analysis(
        self,
        job: AnalysisJob,
        orchestrator: AnalysisOrchestrator,
        db_session: AsyncSession,
    ) -> None:
        # Load turn with session and persona
        stmt = (
            select(ConversationTurn)
            .where(ConversationTurn.id == job.turn_id)
            .options(
                selectinload(ConversationTurn.session).selectinload(ConversationSession.persona),
                selectinload(ConversationTurn.session).selectinload(ConversationSession.turns),
            )
        )
        res = await db_session.execute(stmt)
        turn = res.scalar_one_or_none()
        if not turn or not turn.session:
            raise ValueError(f"Turn '{job.turn_id}' or associated session not found.")

        # Check if TurnAnalysis already exists
        exist_stmt = select(TurnAnalysis).where(TurnAnalysis.turn_id == turn.id)
        exist_res = await db_session.execute(exist_stmt)
        existing_analysis = exist_res.scalar_one_or_none()
        if existing_analysis:
            # Delete old analysis if re-running
            await db_session.delete(existing_analysis)
            await db_session.flush()

        session_obj = turn.session
        persona = session_obj.persona
        stt_metrics = turn.metrics or {}

        previous_turns = [
            {"speaker": t.speaker, "transcript": t.transcript}
            for t in session_obj.turns
            if t.sequence < turn.sequence
        ]

        analysis_input = ConversationAnalysisInput(
            session_id=session_obj.id,
            current_turn_id=turn.id,
            current_user_transcript=turn.transcript,
            stt_confidence=stt_metrics.get("confidence"),
            speech_duration_ms=stt_metrics.get("speech_duration_ms"),
            conversation_mode=session_obj.mode,
            persona_name=persona.name if persona else "Assistant",
            persona_role=persona.role if persona else "Partner",
            persona_difficulty=persona.difficulty if persona else "N3",
            persona_style=persona.speaking_style if persona else "Natural",
            learner_level=persona.difficulty if persona else "N3",
            previous_turns=previous_turns,
        )

        result = await orchestrator.analyze_turn(analysis_input, user_id=session_obj.user_id)

        input_hash = orchestrator.compute_input_hash(
            turn.transcript,
            persona.role if persona else "Partner",
            session_obj.mode,
        )

        turn_analysis_record = TurnAnalysis(
            turn_id=turn.id,
            session_id=session_obj.id,
            overall_quality_score=result.overall_quality_score,
            communicative_success=result.communicative_success,
            is_suspicious_transcript=result.is_suspicious_transcript,
            strengths=result.strengths,
            context_notes=[cn.model_dump() for cn in result.context_notes],
            input_hash=input_hash,
            analyzer_version=result.analyzer_version,
            prompt_version=result.prompt_version,
            ai_provider=result.provider,
            ai_model=result.model,
        )
        db_session.add(turn_analysis_record)
        await db_session.flush()

        # Persist corrections
        for corr in result.corrections:
            c_model = AnalysisCorrection(
                turn_analysis_id=turn_analysis_record.id,
                category=corr.category.value,
                severity=corr.severity.value,
                severity_score=corr.severity_score,
                original=corr.original,
                corrected=corr.corrected,
                explanation=corr.explanation,
                native_alternative=corr.native_alternative,
                acceptable_alternatives=corr.acceptable_alternatives,
                context_note=corr.context_note,
                confidence=corr.confidence.value,
            )
            db_session.add(c_model)

        # Persist grammar notes
        for gp in result.grammar_points:
            g_model = GrammarNote(
                turn_analysis_id=turn_analysis_record.id,
                grammar_pattern=gp.grammar_pattern,
                user_usage=gp.user_usage,
                correct_usage=gp.correct_usage,
                short_explanation=gp.short_explanation,
                example_sentence=gp.example_sentence,
            )
            db_session.add(g_model)

        # Persist vocabulary notes
        for vn in result.vocabulary_notes:
            v_model = VocabularyNote(
                turn_analysis_id=turn_analysis_record.id,
                original_word=vn.original_word,
                suggested_alternatives=vn.suggested_alternatives,
                nuance_explanation=vn.nuance_explanation,
                jlpt_level=vn.jlpt_level,
            )
            db_session.add(v_model)

    async def _process_session_analysis(
        self,
        job: AnalysisJob,
        orchestrator: AnalysisOrchestrator,
        db_session: AsyncSession,
    ) -> None:
        stmt = (
            select(ConversationSession)
            .where(ConversationSession.id == job.session_id)
            .options(
                selectinload(ConversationSession.persona),
                selectinload(ConversationSession.turns),
            )
        )
        res = await db_session.execute(stmt)
        session_obj = res.scalar_one_or_none()
        if not session_obj:
            raise ValueError(f"Session '{job.session_id}' not found.")

        # Check existing session analysis
        sa_stmt = select(SessionAnalysis).where(SessionAnalysis.session_id == session_obj.id)
        sa_res = await db_session.execute(sa_stmt)
        existing_sa = sa_res.scalar_one_or_none()
        if existing_sa:
            await db_session.delete(existing_sa)
            await db_session.flush()

        # Gather corrections from turn analyses
        ta_stmt = (
            select(TurnAnalysis)
            .where(TurnAnalysis.session_id == session_obj.id)
            .options(selectinload(TurnAnalysis.corrections))
        )
        ta_res = await db_session.execute(ta_stmt)
        turn_analyses = ta_res.scalars().all()

        corrections_summary = []
        for ta in turn_analyses:
            for c in ta.corrections:
                corrections_summary.append({
                    "original": c.original,
                    "corrected": c.corrected,
                    "category": c.category,
                    "severity": c.severity,
                    "explanation": c.explanation,
                })

        turns_summary = [{"speaker": t.speaker, "transcript": t.transcript} for t in session_obj.turns]

        result = await orchestrator.analyze_session(
            session_id=session_obj.id,
            persona_name=session_obj.persona.name if session_obj.persona else "Assistant",
            mode=session_obj.mode,
            turns_summary=turns_summary,
            corrections_summary=corrections_summary,
            user_id=session_obj.user_id,
        )

        session_analysis_record = SessionAnalysis(
            session_id=session_obj.id,
            overall_score=result.overall_score,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            repeated_issues=result.repeated_issues,
            top_recommendations=result.top_recommendations,
            total_user_turns_analyzed=result.total_user_turns_analyzed,
            total_corrections_count=result.total_corrections_count,
            must_fix_count=result.must_fix_count,
            should_fix_count=result.should_fix_count,
            native_alt_count=result.native_alt_count,
            grammar_summary=result.grammar_summary,
            vocabulary_summary=result.vocabulary_summary,
            analyzer_version=result.analyzer_version,
            prompt_version=result.prompt_version,
            ai_provider=result.provider,
            ai_model=result.model,
        )
        db_session.add(session_analysis_record)
        await db_session.flush()

        # Enqueue long-term Learner Memory & Profile update
        try:
            from app.domains.learner_memory.queue import learner_memory_job_queue
            await learner_memory_job_queue.enqueue({
                "user_id": session_obj.user_id,
                "session_id": session_obj.id,
                "type": "session_memory_update",
            })
            logger.info(f"[AnalysisWorker] Enqueued learner memory update for session '{session_obj.id}'")
        except Exception as lme:
            logger.warning(f"[AnalysisWorker] Failed to enqueue learner memory update: {lme}")

    async def _worker_loop(self) -> None:
        """Background continuous worker loop polling jobs from queue."""
        logger.info("[AnalysisWorker] Background worker loop started.")
        while self._running:
            try:
                job_data = await analysis_job_queue.dequeue(timeout_seconds=2.0)
                if not job_data:
                    continue

                job_id = job_data.get("job_id")
                if not job_id:
                    continue

                async with AsyncSessionLocal() as session:
                    await self.execute_job(job_id, session)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[AnalysisWorker] Unexpected error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info("[AnalysisWorker] Background worker loop stopped.")

    def start(self) -> None:
        if not self._running:
            self._running = True
            asyncio.create_task(self.recover_stale_jobs())
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


# Global singleton worker instance
analysis_worker = AnalysisWorker()
