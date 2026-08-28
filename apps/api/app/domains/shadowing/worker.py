import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.shadowing.contracts import VideoStatus
from app.domains.shadowing.models import ShadowingImportJob, ShadowingVideo
from app.domains.shadowing.pipeline.import_pipeline import ImportPipeline
from app.domains.shadowing.queue import shadowing_job_queue
from app.infrastructure.database.session import AsyncSessionLocal


class ShadowingImportWorker:
    """Processes background YouTube video ingestion and analysis jobs."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self.jobs_processed: int = 0
        self.jobs_failed: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    async def recover_stale_jobs(self) -> int:
        """Recovers any shadowing import jobs left in 'processing' or in-progress state from an unexpected worker restart."""
        recovered = 0
        try:
            async with AsyncSessionLocal() as session:
                in_progress_statuses = [
                    VideoStatus.QUEUED.value,
                    VideoStatus.PROCESSING.value,
                    VideoStatus.FETCHING_METADATA.value,
                    VideoStatus.RESOLVING_TRANSCRIPT.value,
                    VideoStatus.TRANSCRIBING.value,
                    VideoStatus.SEGMENTING.value,
                    VideoStatus.ANALYZING.value,
                ]
                stmt = (
                    select(ShadowingImportJob, ShadowingVideo)
                    .join(ShadowingVideo, ShadowingImportJob.video_id == ShadowingVideo.id)
                    .where(ShadowingImportJob.status.in_(in_progress_statuses))
                )
                res = await session.execute(stmt)
                stale_pairs = res.all()
                for job, video in stale_pairs:
                    job.status = VideoStatus.QUEUED.value
                    job.stage = "queued"
                    await shadowing_job_queue.enqueue({
                        "job_id": job.id,
                        "video_id": video.video_id,
                        "user_id": job.user_id,
                        "custom_whisper_model": None,
                    })
                    recovered += 1
                if recovered > 0:
                    await session.commit()
                    logger.info(f"[ShadowingWorker] Recovered and re-enqueued {recovered} stale shadowing import jobs on startup.")
        except Exception as e:
            logger.warning(f"[ShadowingWorker] Stale job recovery encountered an error: {e}")
        return recovered

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        asyncio.create_task(self.recover_stale_jobs())
        self._task = asyncio.create_task(self._run_loop())
        logger.info("[ShadowingWorker] Background worker started.")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[ShadowingWorker] Background worker stopped.")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                job_data = await shadowing_job_queue.dequeue(timeout_seconds=2.0)
                if not job_data:
                    continue

                job_id = job_data.get("job_id")
                video_id = job_data.get("video_id")
                user_id = job_data.get("user_id")
                custom_model = job_data.get("custom_whisper_model")

                if not video_id or not user_id:
                    continue

                logger.info(f"[ShadowingWorker] Processing import job '{job_id}' for video '{video_id}'...")
                async with AsyncSessionLocal() as session:
                    await self._execute_job(
                        session=session,
                        job_id=job_id,
                        video_id=video_id,
                        user_id=user_id,
                        custom_whisper_model=custom_model,
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ShadowingWorker] Unexpected loop error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def _execute_job(
        self,
        session: AsyncSession,
        job_id: str | None,
        video_id: str,
        user_id: str,
        custom_whisper_model: str | None,
    ) -> None:
        pipeline = ImportPipeline(session)
        try:
            await pipeline.execute_import(
                video_id=video_id,
                user_id=user_id,
                custom_whisper_model=custom_whisper_model,
                job_id=job_id,
            )
            self.jobs_processed += 1
        except Exception as e:
            self.jobs_failed += 1
            logger.error(f"[ShadowingWorker] Pipeline execution failed for {video_id}: {e}", exc_info=True)
            if job_id:
                j_res = await session.execute(select(ShadowingImportJob).where(ShadowingImportJob.id == job_id))
                job = j_res.scalar_one_or_none()
                if job:
                    job.status = VideoStatus.FAILED.value
                    job.error_type = type(e).__name__
                    job.error_message = str(e)
                    job.completed_at = datetime.now(timezone.utc)

            v_res = await session.execute(select(ShadowingVideo).where(ShadowingVideo.video_id == video_id))
            video = v_res.scalar_one_or_none()
            if video and video.import_status != VideoStatus.READY.value:
                video.import_status = VideoStatus.FAILED.value

            await session.commit()


shadowing_worker = ShadowingImportWorker()
