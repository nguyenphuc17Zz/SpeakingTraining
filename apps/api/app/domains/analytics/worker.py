import asyncio
from app.core.logging import logger
from app.domains.analytics.application.analytics_snapshot_service import AnalyticsSnapshotService
from app.domains.analytics.application.session_analytics_service import SessionAnalyticsService
from app.domains.analytics.queue import AnalyticsJob, analytics_queue
from app.infrastructure.database.session import AsyncSessionLocal


class AnalyticsWorker:
    """Background worker consuming analytics jobs (session analytics, snapshots, weekly reviews)."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self.jobs_processed: int = 0
        self.jobs_failed: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("[AnalyticsWorker] Background worker started.")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[AnalyticsWorker] Background worker stopped.")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                job: AnalyticsJob = await analytics_queue.dequeue()
                await self._process_job(job)
                analytics_queue.task_done()
                self.jobs_processed += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.jobs_failed += 1
                logger.error(f"[AnalyticsWorker] Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_job(self, job: AnalyticsJob) -> None:
        async with AsyncSessionLocal() as db:
            if job.job_type == "calculate_session_analytics":
                session_id = job.payload.get("session_id")
                if session_id:
                    service = SessionAnalyticsService(db)
                    await service.calculate_session_analytics(session_id)
            elif job.job_type == "refresh_snapshot":
                user_id = job.payload.get("user_id")
                if user_id:
                    snap_service = AnalyticsSnapshotService(db)
                    await snap_service.refresh_snapshot(user_id)


analytics_worker = AnalyticsWorker()
