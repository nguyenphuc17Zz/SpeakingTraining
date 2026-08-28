import asyncio
import base64
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learner_memory.merger import MemoryMerger
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.pronunciation.contracts import (
    PronunciationAnalysisPolicy,
    PronunciationResult,
    PronunciationTarget,
    ReferenceType,
    TargetType,
)
from app.domains.pronunciation.learning_signal_extractor import PronunciationLearningSignalExtractor
from app.domains.pronunciation.models import PronunciationAttempt
from app.domains.pronunciation.pipeline import PronunciationPipeline
from app.domains.pronunciation.queue import pronunciation_job_queue
from app.domains.speech.contracts import STTOptions
from app.domains.speech.stt_router import stt_router
from app.infrastructure.database.session import AsyncSessionLocal


import os
import tempfile


class PronunciationWorker:
    """Continuous background worker for asynchronous Pronunciation analysis jobs."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self.jobs_processed: int = 0
        self.jobs_failed: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    async def recover_stale_jobs(self) -> int:
        """Recovers any pronunciation attempts left in 'processing' state from an unexpected worker restart."""
        recovered = 0
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(PronunciationAttempt).where(PronunciationAttempt.analysis_status == "processing")
                res = await session.execute(stmt)
                stale_attempts = res.scalars().all()
                for attempt in stale_attempts:
                    attempt.analysis_status = "pending"
                    recovered += 1
                if recovered > 0:
                    await session.commit()
                    logger.info(f"[PronunciationWorker] Recovered {recovered} stale pronunciation attempts on startup.")
        except Exception as e:
            logger.warning(f"[PronunciationWorker] Stale job recovery encountered an error: {e}")
        return recovered

    async def execute_job(self, job_data: dict[str, Any], db_session: AsyncSession) -> None:
        """Executes a single queued pronunciation analysis job."""
        attempt_id = job_data.get("attempt_id")
        user_id = job_data.get("user_id")
        target_text = job_data.get("target_text")
        expected_reading = job_data.get("expected_reading")
        audio_b64 = job_data.get("audio_base64")
        audio_path = job_data.get("audio_path")
        session_id = job_data.get("session_id")
        turn_id = job_data.get("turn_id")

        if not attempt_id or not user_id or not target_text or (not audio_b64 and not audio_path):
            logger.warning(f"[PronunciationWorker] Missing required fields in job: {job_data}")
            return

        logger.info(f"[PronunciationWorker] Processing pronunciation job for attempt '{attempt_id}' (User: {user_id})")

        # Load attempt from DB
        stmt = select(PronunciationAttempt).where(PronunciationAttempt.id == attempt_id)
        res = await db_session.execute(stmt)
        attempt = res.scalar_one_or_none()
        if not attempt:
            logger.warning(f"[PronunciationWorker] Attempt '{attempt_id}' not found.")
            return

        attempt.analysis_status = "processing"
        await db_session.commit()

        try:
            if audio_path and os.path.exists(audio_path):
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
            elif audio_b64:
                audio_bytes = base64.b64decode(audio_b64)
            else:
                raise ValueError("No valid audio source found")

            # 1. High-accuracy STT for word timestamps
            user_transcript = None
            word_timestamps = None
            try:
                from app.domains.speech.model_manager import whisper_model_manager
                active_model = whisper_model_manager.get_active_model_id()
                ref_clean = target_text.strip() if target_text else ""
                prompt = f"日本語のシャドーイング練習、発音評価。手本：「{ref_clean}」"
                stt_opts = STTOptions(
                    language="ja",
                    model=active_model,
                    beam_size=5,
                    vad_filter=True,
                    initial_prompt=prompt,
                )
                stt_res = await stt_router.transcribe(audio_bytes=audio_bytes, options=stt_opts)
                user_transcript = stt_res.text.strip()
                word_timestamps = stt_res.words
            except Exception as se:
                logger.warning(f"[PronunciationWorker] STT transcription failed: {se}")

            # 2. Run Pipeline
            target = PronunciationTarget(
                reference_text=target_text,
                expected_reading=expected_reading,
                target_type=TargetType(job_data.get("target_type", "sentence")),
                reference_type=ReferenceType(job_data.get("reference_type", "synthetic")),
            )

            pipeline_res: PronunciationResult = await PronunciationPipeline.run(
                audio_bytes=audio_bytes,
                target=target,
                user_transcript=user_transcript,
                word_timestamps=word_timestamps,
                policy=PronunciationAnalysisPolicy.DEEP,
            )

            # 3. Update DB Attempt
            attempt.user_text = user_transcript
            attempt.analysis_status = "completed"
            attempt.overall_score = pipeline_res.overall_score
            attempt.overall_confidence = pipeline_res.overall_confidence.value
            attempt.score_interpretation = pipeline_res.score_interpretation
            attempt.engine_version = pipeline_res.engine_version
            attempt.scores_json = {
                "overall": pipeline_res.overall_score,
                "phoneme": pipeline_res.phoneme_score.model_dump() if pipeline_res.phoneme_score else None,
                "mora": pipeline_res.mora_timing_score.model_dump() if pipeline_res.mora_timing_score else None,
                "pitch": pipeline_res.pitch_score.model_dump() if pipeline_res.pitch_score else None,
                "rhythm": pipeline_res.rhythm_score.model_dump() if pipeline_res.rhythm_score else None,
                "intonation": pipeline_res.intonation_score.model_dump() if pipeline_res.intonation_score else None,
            }
            attempt.feedback_json = {
                "top_issues": [i.model_dump() for i in pipeline_res.top_issues],
                "strengths": pipeline_res.strengths,
                "practice_recommendation": pipeline_res.practice_recommendation,
                "partial_reasons": pipeline_res.partial_reasons,
            }
            attempt.acoustic_metadata_json = {
                "phoneme_assessment": [p.model_dump() for p in (pipeline_res.phoneme_assessment or [])],
                "mora_assessment": pipeline_res.mora_assessment.model_dump() if pipeline_res.mora_assessment else None,
                "pitch_assessment": pipeline_res.pitch_assessment.model_dump() if pipeline_res.pitch_assessment else None,
                "rhythm_assessment": pipeline_res.rhythm_assessment.model_dump() if pipeline_res.rhythm_assessment else None,
                "intonation_assessment": pipeline_res.intonation_assessment.model_dump() if pipeline_res.intonation_assessment else None,
                "audio_quality": pipeline_res.audio_quality.model_dump() if pipeline_res.audio_quality else None,
            }
            await db_session.commit()

            # 4. Ingest into LearnerMemory (Phase 5)
            try:
                candidates = PronunciationLearningSignalExtractor.extract_from_pronunciation_result(
                    result=pipeline_res,
                    user_id=user_id,
                    session_id=session_id,
                    turn_id=turn_id,
                    context_tag="conversation_speech" if session_id else "pronunciation_practice",
                )
                if candidates:
                    merger = MemoryMerger(db_session)
                    await merger.merge_candidates(user_id=user_id, candidates=candidates)
                    profile_service = LearnerProfileService(db_session)
                    await profile_service.recalculate_profile(user_id=user_id, generate_ai_summary=False)
                    logger.info(f"[PronunciationWorker] Ingested {len(candidates)} memory signals for user {user_id}")
            except Exception as me:
                logger.warning(f"[PronunciationWorker] Learning signal extraction failed: {me}", exc_info=True)

            logger.info(f"[PronunciationWorker] Finished processing attempt '{attempt_id}' (Score: {pipeline_res.overall_score})")

            # 5. Emit GameEvent to Gamification Engine
            try:
                from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
                from app.domains.gamification.infrastructure.game_event_publisher import GameEventPublisher

                await GameEventPublisher.publish(
                    user_id=user_id,
                    event_type=GameEventType.PRONUNCIATION_ATTEMPTED,
                    source=GameEventSource.PRONUNCIATION,
                    source_id=attempt.id,
                    metadata={
                        "score": pipeline_res.overall_score,
                        "interpretation": pipeline_res.score_interpretation,
                        "session_id": session_id,
                        "turn_id": turn_id,
                    },
                )
            except Exception as ge:
                logger.warning(f"[PronunciationWorker] Error emitting pronunciation.attempted game event: {ge}")

            self.jobs_processed += 1
        except Exception as e:
            logger.error(f"[PronunciationWorker] Failed to process attempt '{attempt_id}': {e}", exc_info=True)
            self.jobs_failed += 1
            attempt.analysis_status = "failed"
            attempt.error_message = str(e)
            await db_session.commit()

    async def _worker_loop(self) -> None:
        """Continuous worker execution loop."""
        logger.info("[PronunciationWorker] Worker loop started.")
        while self._running:
            try:
                job_data = await pronunciation_job_queue.dequeue(timeout_seconds=2.0)
                if not job_data:
                    continue

                async with AsyncSessionLocal() as session:
                    await self.execute_job(job_data, session)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[PronunciationWorker] Unexpected error in loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info("[PronunciationWorker] Worker loop stopped.")

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


pronunciation_worker = PronunciationWorker()
