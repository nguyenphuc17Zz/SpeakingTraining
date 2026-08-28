import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.learning.contracts import ExerciseResult, ExerciseStatus, ExerciseType, IndependenceLevel
from app.domains.learning.exercise_evaluator import ExerciseEvaluator
from app.domains.learning.goal_service import GoalService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.mastery_engine import MasteryEngine
from app.domains.learning.models import Exercise, ExerciseAttempt
from app.domains.learning.review_scheduler import ReviewScheduler
from app.domains.pronunciation.contracts import ReferenceType, TargetType
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
from app.domains.pronunciation.service import PronunciationService
from app.domains.shadowing.analysis.candidate_selector import ShadowingCandidateSelector
from app.domains.shadowing.analysis.lesson_generator import ShadowingLessonGenerator
from app.domains.shadowing.contracts import (
    CandidateCategory,
    DifficultyReport,
    ExtractedGrammar,
    ExtractedVocabulary,
    NaturalExpression,
    ShadowingCandidate,
    ShadowingLesson,
    SpeakingDifficulty,
    TranscriptSegmentDTO,
    VideoStatus,
)
from app.domains.shadowing.models import (
    ShadowingBookmark,
    ShadowingImportJob,
    ShadowingSegment,
    ShadowingSegmentProgress,
    ShadowingTranscript,
    ShadowingVideo,
    ShadowingVideoProgress,
)
from app.domains.shadowing.pipeline.import_pipeline import ImportPipeline
from app.domains.shadowing.prompts import ShadowingPrompts
from app.domains.shadowing.queue import shadowing_job_queue
from app.domains.shadowing.scoring import ShadowingScorer
from app.domains.shadowing.schemas import (
    BookmarkDTO,
    SegmentPracticeCompleteResponse,
    SegmentPracticeStartResponse,
    SegmentTranslateResponse,
    ShadowingJobStatusDTO,
    ShadowingSegmentProgressDTO,
    ShadowingVideoDetailDTO,
    ShadowingVideoDTO,
    ShadowingVideoProgressDTO,
    VideoImportResponse,
)
from app.domains.shadowing.youtube.url_resolver import YoutubeUrlResolver
from app.domains.users.service import UserService
from app.shared.errors.exceptions import NotFoundException, ValidationException


class ShadowingService:
    """Core orchestrator for YouTube Shadowing, personalized recommendations, exercise execution, and mastery loop."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.profile_service = LearnerProfileService(db)
        self.goal_service = GoalService(db)
        self.pronunciation_service = PronunciationService(db)
        self.exercise_evaluator = ExerciseEvaluator(db)
        self.learning_item_service = LearningItemService(db)
        self.ai_router = AIRouter(db)

    async def import_video(
        self,
        url: str,
        user_id: str,
        custom_whisper_model: str | None = None,
        run_sync: bool = False,
    ) -> VideoImportResponse:
        """
        Validates URL, checks duplicate/existing video, creates background job, and returns immediate status.
        """
        video_id = YoutubeUrlResolver.extract_video_id(url)
        canonical_url = YoutubeUrlResolver.get_canonical_url(video_id)

        # 1. Duplicate detection: Check if video already exists and is READY
        v_res = await self.db.execute(select(ShadowingVideo).where(ShadowingVideo.video_id == video_id))
        video = v_res.scalar_one_or_none()

        if video and video.import_status == VideoStatus.READY.value:
            logger.info(f"[ShadowingService] Video '{video_id}' already exists in ready state. Reusing existing processing.")
            return VideoImportResponse(
                video_id=video.id,
                canonical_video_id=video_id,
                job_id="existing_job",
                status=VideoStatus.READY,
                message="Video already analyzed and ready for shadowing practice.",
                is_existing=True,
            )

        # Check if video is already queued or processing in background
        if video and video.import_status not in (VideoStatus.FAILED.value, VideoStatus.PARTIAL.value):
            job_stmt = (
                select(ShadowingImportJob)
                .where(ShadowingImportJob.video_id == video.id)
                .order_by(ShadowingImportJob.created_at.desc())
                .limit(1)
            )
            j_res = await self.db.execute(job_stmt)
            existing_job = j_res.scalar_one_or_none()
            if existing_job and existing_job.status not in (VideoStatus.FAILED.value, VideoStatus.PARTIAL.value):
                if not run_sync:
                    await shadowing_job_queue.enqueue({
                        "job_id": existing_job.id,
                        "video_id": video_id,
                        "user_id": user_id,
                        "custom_whisper_model": custom_whisper_model,
                    })
                logger.info(f"[ShadowingService] Video '{video_id}' is already processing with job '{existing_job.id}'. Re-enqueued job.")
                return VideoImportResponse(
                    video_id=video.id,
                    canonical_video_id=video_id,
                    job_id=existing_job.id,
                    status=VideoStatus(video.import_status) if video.import_status in VideoStatus._value2member_map_ else VideoStatus.PROCESSING,
                    message="Video is currently processing in the background.",
                    is_existing=False,
                )

        # 2. Create or reset Video record
        if not video:
            try:
                video = ShadowingVideo(
                    video_id=video_id,
                    url=canonical_url,
                    canonical_url=canonical_url,
                    title=f"YouTube Video ({video_id})",
                    channel_name="YouTube Creator",
                    import_status=VideoStatus.QUEUED.value,
                )
                self.db.add(video)
                await self.db.flush()
            except Exception as ex:
                await self.db.rollback()
                logger.warning(f"[ShadowingService] Video record insertion raced for '{video_id}': {ex}. Querying existing.")
                v_res = await self.db.execute(select(ShadowingVideo).where(ShadowingVideo.video_id == video_id))
                video = v_res.scalar_one_or_none()
                if not video:
                    raise ex
        else:
            video.import_status = VideoStatus.QUEUED.value

        # 3. Create Import Job
        job = ShadowingImportJob(
            video_id=video.id,
            user_id=user_id,
            stage="queued",
            status=VideoStatus.QUEUED.value,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.commit()

        # 4. Enqueue or run sync (for unit testing)
        if run_sync:
            pipeline = ImportPipeline(self.db)
            await pipeline.execute_import(
                video_id=video_id,
                user_id=user_id,
                custom_whisper_model=custom_whisper_model,
                job_id=job.id,
            )
            status = VideoStatus.READY
            msg = "Video analyzed synchronously and ready."
        else:
            await shadowing_job_queue.enqueue({
                "job_id": job.id,
                "video_id": video_id,
                "user_id": user_id,
                "custom_whisper_model": custom_whisper_model,
            })
            status = VideoStatus.QUEUED
            msg = "Video import queued for background metadata and transcript analysis."

        return VideoImportResponse(
            video_id=video.id,
            canonical_video_id=video_id,
            job_id=job.id,
            status=status,
            message=msg,
            is_existing=False,
        )

    async def get_video(self, video_id: str, user_id: str) -> ShadowingVideoDetailDTO:
        """Retrieves video detail, all segments, personalized recommendations, and user progress."""
        # Find by UUID or 11-char YouTube video ID
        stmt = (
            select(ShadowingVideo)
            .where(
                (ShadowingVideo.id == video_id) | (ShadowingVideo.video_id == video_id)
            )
            .options(
                selectinload(ShadowingVideo.transcripts),
                selectinload(ShadowingVideo.segments),
            )
        )
        res = await self.db.execute(stmt)
        video = res.scalar_one_or_none()
        if not video:
            raise NotFoundException(f"Shadowing video '{video_id}' not found.")

        # Convert segments to DTO
        segment_dtos = self._build_segment_dtos(video.segments)

        # Get personalized recommendations
        profile = await self.profile_service.get_or_create_profile(user_id)
        goals = await self.goal_service.get_active_goals(user_id)
        goal_titles = [g.title for g in goals] or profile.learning_goals or []

        recommendations = ShadowingCandidateSelector.select_candidates(
            segments=segment_dtos,
            learner_goals=goal_titles,
            learner_weaknesses=profile.weaknesses or [],
            max_recommendations=8,
        )

        # Fetch user video progress
        prog_res = await self.db.execute(
            select(ShadowingVideoProgress).where(
                ShadowingVideoProgress.user_id == user_id,
                ShadowingVideoProgress.video_id == video.id,
            )
        )
        progress = prog_res.scalar_one_or_none()
        progress_dto = None
        if progress:
            progress_dto = ShadowingVideoProgressDTO(
                watch_progress=progress.watch_progress,
                shadow_progress=progress.shadow_progress,
                mastery_progress=progress.mastery_progress,
                segments_completed=progress.segments_completed,
                total_practice_time_seconds=progress.total_practice_time_seconds,
                best_score=progress.best_score,
                last_position_seconds=progress.last_position_seconds,
                last_opened_at=progress.last_opened_at,
            )

        return ShadowingVideoDetailDTO(
            id=video.id,
            video_id=video.video_id,
            url=video.url,
            canonical_url=video.canonical_url,
            title=video.title,
            channel_name=video.channel_name,
            channel_id=video.channel_id,
            thumbnail_url=video.thumbnail_url,
            duration_seconds=video.duration_seconds,
            language=video.language,
            import_status=VideoStatus(video.import_status),
            overall_difficulty=SpeakingDifficulty(video.overall_difficulty),
            summary_json=video.summary_json,
            created_at=video.created_at,
            updated_at=video.updated_at,
            segments_count=len(segment_dtos),
            recommended_count=len(recommendations),
            segments=segment_dtos,
            recommended_segments=recommendations,
            progress=progress_dto,
        )

    async def get_videos(self, limit: int = 30, offset: int = 0) -> list[ShadowingVideoDTO]:
        """Lists imported YouTube videos with status and difficulty."""
        stmt = (
            select(ShadowingVideo)
            .order_by(desc(ShadowingVideo.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        videos = res.scalars().all()

        return [
            ShadowingVideoDTO(
                id=v.id,
                video_id=v.video_id,
                url=v.url,
                canonical_url=v.canonical_url,
                title=v.title,
                channel_name=v.channel_name,
                channel_id=v.channel_id,
                thumbnail_url=v.thumbnail_url,
                duration_seconds=v.duration_seconds,
                language=v.language,
                import_status=VideoStatus(v.import_status),
                overall_difficulty=SpeakingDifficulty(v.overall_difficulty),
                summary_json=v.summary_json,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
            for v in videos
        ]

    async def delete_video(self, video_id: str) -> dict[str, Any]:
        """Deletes a shadowing video along with its transcripts, segments, bookmarks, and progress records."""
        stmt = (
            select(ShadowingVideo)
            .where(
                (ShadowingVideo.id == video_id) | (ShadowingVideo.video_id == video_id)
            )
            .options(
                selectinload(ShadowingVideo.transcripts),
                selectinload(ShadowingVideo.segments),
            )
        )
        res = await self.db.execute(stmt)
        video = res.scalar_one_or_none()
        if not video:
            raise NotFoundException(f"Shadowing video '{video_id}' not found.")

        # Delete any associated video progress & bookmark records
        await self.db.execute(
            delete(ShadowingVideoProgress).where(ShadowingVideoProgress.video_id == video.id)
        )

        segment_ids = [s.id for s in video.segments]
        if segment_ids:
            await self.db.execute(
                delete(ShadowingBookmark).where(ShadowingBookmark.segment_id.in_(segment_ids))
            )
            await self.db.execute(
                delete(ShadowingSegmentProgress).where(ShadowingSegmentProgress.segment_id.in_(segment_ids))
            )

        # Delete the video (transcripts & segments will cascade delete)
        await self.db.delete(video)
        await self.db.commit()

        logger.info(f"[Shadowing] Deleted video '{video.title}' ({video.video_id})")
        return {"success": True, "deleted_id": video.video_id, "message": f"Video '{video.title}' đã được xóa thành công."}

    async def get_recommendations(self, video_id: str, user_id: str) -> list[ShadowingCandidate]:
        """Calculates current personalized shadowing candidate recommendations for a video."""
        video_detail = await self.get_video(video_id=video_id, user_id=user_id)
        return video_detail.recommended_segments

    async def create_lesson(
        self,
        video_id: str,
        user_id: str,
        time_budget_minutes: int = 15,
        mode: str = "quick_shadow",
    ) -> ShadowingLesson:
        """Assembles a tailored shadowing lesson based on time budget and skill focus."""
        detail = await self.get_video(video_id=video_id, user_id=user_id)
        return ShadowingLessonGenerator.generate_lesson(
            video_id=detail.id,
            video_title=detail.title,
            segments=detail.segments,
            recommended_candidates=detail.recommended_segments,
            time_budget_minutes=time_budget_minutes,
            mode=mode,
        )

    async def start_segment_practice(
        self,
        segment_id: str,
        user_id: str,
        shadowing_mode: str = "shadow",
    ) -> SegmentPracticeStartResponse:
        """
        Instantiates a canonical Phase 7 Exercise(type=shadowing) and ExerciseAttempt
        to ensure all shadowing activity feeds seamlessly into the core learning & mastery loop.
        """
        seg_res = await self.db.execute(select(ShadowingSegment).where(ShadowingSegment.id == segment_id))
        segment = seg_res.scalar_one_or_none()
        if not segment:
            raise NotFoundException(f"Shadowing segment '{segment_id}' not found.")

        # 1. Create or load standard Phase 7 Exercise
        exercise_title = f"Shadowing: {segment.normalized_text[:30]}"
        exercise = Exercise(
            user_id=user_id,
            exercise_type=ExerciseType.SHADOWING.value,
            status=ExerciseStatus.IN_PROGRESS.value,
            title=exercise_title,
            objective=f"Luyện tập ngữ điệu, nhịp điệu và phát âm chuẩn xác câu: '{segment.normalized_text}'",
            instructions="Nghe kỹ phát âm và ngữ điệu của người bản xứ, sau đó shadow lặp lại.",
            target_patterns=[segment.normalized_text],
            difficulty=segment.difficulty_json.get("overall_difficulty", "normal") if segment.difficulty_json else "normal",
            estimated_minutes=3,
            extra_metadata={
                "video_id": segment.video_id,
                "segment_id": segment.id,
                "shadowing_mode": shadowing_mode,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "speaker_id": segment.speaker_id,
            },
        )
        self.db.add(exercise)
        await self.db.flush()

        # 2. Create ExerciseAttempt
        attempt = ExerciseAttempt(
            exercise_id=exercise.id,
            user_id=user_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            independence_level=IndependenceLevel.INDEPENDENT.value,
        )
        self.db.add(attempt)
        await self.db.flush()

        # 3. Update ShadowingSegmentProgress
        prog_res = await self.db.execute(
            select(ShadowingSegmentProgress).where(
                ShadowingSegmentProgress.user_id == user_id,
                ShadowingSegmentProgress.segment_id == segment_id,
            )
        )
        seg_prog = prog_res.scalar_one_or_none()
        if not seg_prog:
            seg_prog = ShadowingSegmentProgress(
                user_id=user_id,
                video_id=segment.video_id,
                segment_id=segment.id,
                exercise_id=exercise.id,
                listen_count=1,
                shadow_attempts=1,
                mastery="practicing",
                last_practiced_at=datetime.now(timezone.utc),
            )
            self.db.add(seg_prog)
        else:
            seg_prog.shadow_attempts += 1
            seg_prog.exercise_id = exercise.id
            seg_prog.last_practiced_at = datetime.now(timezone.utc)

        await self.db.commit()

        return SegmentPracticeStartResponse(
            exercise_id=exercise.id,
            attempt_id=attempt.id,
            segment_id=segment.id,
            video_id=segment.video_id,
            reference_text=segment.normalized_text,
            expected_reading=segment.reading,
            start_time=segment.start_time,
            end_time=segment.end_time,
            speaker_id=segment.speaker_id,
        )

    async def complete_segment_practice(
        self,
        exercise_id: str,
        attempt_id: str,
        audio_base64: str,
        user_id: str,
        shadowing_mode: str = "shadow",
        playback_speed: float = 1.0,
        client_transcript: str | None = None,
    ) -> SegmentPracticeCompleteResponse:
        """
        Executes end-to-end attempt evaluation:
        1. Decode user audio
        2. PronunciationService (Phase 6) with ReferenceType.YOUTUBE
        3. ExerciseEvaluator (Phase 7)
        4. MasteryEngine & LearningItem updates
        5. Update Shadowing progress
        """
        att_res = await self.db.execute(
            select(ExerciseAttempt).where(
                ExerciseAttempt.id == attempt_id,
                ExerciseAttempt.exercise_id == exercise_id,
            )
        )
        attempt = att_res.scalar_one_or_none()

        ex_res = await self.db.execute(select(Exercise).where(Exercise.id == exercise_id))
        exercise = ex_res.scalar_one_or_none()
        if not exercise:
            raise NotFoundException(f"Exercise '{exercise_id}' not found.")

        # Self-healing attempt resolution: If attempt not found or already completed, spawn a fresh attempt
        if not attempt or attempt.status == "completed":
            attempt = ExerciseAttempt(
                exercise_id=exercise.id,
                user_id=user_id,
                status="in_progress",
                started_at=datetime.now(timezone.utc),
                independence_level=IndependenceLevel.INDEPENDENT.value,
            )
            self.db.add(attempt)
            await self.db.flush()

        segment_id = (exercise.extra_metadata or {}).get("segment_id")
        target_text = (exercise.target_patterns or [""])[0]

        # Decode user audio bytes
        try:
            audio_bytes = base64.b64decode(audio_base64)
            if len(audio_bytes) < 10:
                raise ValidationException("Bản thu âm quá ngắn hoặc không có tín hiệu âm thanh hợp lệ.")
        except ValidationException:
            raise
        except Exception as be:
            raise ValidationException(f"Invalid base64 audio payload: {be}")

        # 1. Run Phase 6 Pronunciation Service with ReferenceType.YOUTUBE
        pron_response = await self.pronunciation_service.analyze_audio(
            user_id=user_id,
            audio_bytes=audio_bytes,
            target_text=target_text,
            reference_type=ReferenceType.YOUTUBE,
            target_type=TargetType.SENTENCE,
        )

        user_spoken_text = (pron_response.user_text or "").strip()
        # Dual-Channel Fallback: If Whisper STT returned empty due to VAD/noise, use Live Speech Web Transcript
        if not user_spoken_text and client_transcript:
            user_spoken_text = client_transcript.strip()

        # Calculate target and user durations for tempo matching
        start_time = (exercise.extra_metadata or {}).get("start_time", 0.0)
        end_time = (exercise.extra_metadata or {}).get("end_time", 0.0)
        target_duration_sec = max(0.4, float(end_time - start_time)) if end_time > start_time else None
        user_duration_sec = (len(audio_bytes) / (2 * 16000)) if len(audio_bytes) > 0 else None

        # 2. Run Deterministic High-Precision ShadowingScorer (Local, < 200ms, no slow LLM call)
        shadow_eval = ShadowingScorer.evaluate(
            target_text=target_text,
            user_transcript=user_spoken_text,
            target_duration_sec=target_duration_sec,
            user_duration_sec=user_duration_sec,
            pron_result=pron_response.result,
            shadowing_mode=shadowing_mode,
            playback_speed=playback_speed,
            fallback_pron_score=pron_response.overall_score,
        )

        # 3. Update Attempt record
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.score = shadow_eval.score
        attempt.success = shadow_eval.success
        attempt.feedback = shadow_eval.feedback
        attempt.pronunciation_attempt_id = pron_response.id
        attempt.metrics_json = {
            "timing_score": shadow_eval.timing_score,
            "pronunciation_score": shadow_eval.pronunciation_score,
            "rhythm_score": shadow_eval.rhythm_score,
            "accuracy_score": shadow_eval.accuracy_score,
            "shadowing_mode": shadowing_mode,
            "playback_speed": playback_speed,
            "speech_rate_mora_sec": shadow_eval.metrics.speech_rate_mora_sec,
            "target_rate_mora_sec": shadow_eval.metrics.target_rate_mora_sec,
        }

        # 4. Synchronize Mastery & LearningItem delta
        mastery_delta = 0.05 if shadow_eval.success else -0.02
        new_mastery_state = shadow_eval.mastery_state

        # Update segment progress
        if segment_id:
            sp_res = await self.db.execute(
                select(ShadowingSegmentProgress).where(
                    ShadowingSegmentProgress.user_id == user_id,
                    ShadowingSegmentProgress.segment_id == segment_id,
                )
            )
            seg_prog = sp_res.scalar_one_or_none()
            if seg_prog:
                seg_prog.best_score = max(seg_prog.best_score or 0.0, shadow_eval.score)
                seg_prog.mastery = new_mastery_state
                seg_prog.last_practiced_at = datetime.now(timezone.utc)
                seg_prog.last_attempt_result_json = {
                    "score": shadow_eval.score,
                    "pronunciation_score": shadow_eval.pronunciation_score,
                    "feedback": shadow_eval.feedback,
                }

        # 5. Update overall Video Progress
        video_id = (exercise.extra_metadata or {}).get("video_id")
        if video_id:
            vp_res = await self.db.execute(
                select(ShadowingVideoProgress).where(
                    ShadowingVideoProgress.user_id == user_id,
                    ShadowingVideoProgress.video_id == video_id,
                )
            )
            vid_prog = vp_res.scalar_one_or_none()
            if not vid_prog:
                vid_prog = ShadowingVideoProgress(
                    user_id=user_id,
                    video_id=video_id,
                    segments_completed=1,
                    best_score=shadow_eval.score,
                    last_opened_at=datetime.now(timezone.utc),
                )
                self.db.add(vid_prog)
            else:
                vid_prog.segments_completed += 1
                vid_prog.best_score = max(vid_prog.best_score or 0.0, shadow_eval.score)
                vid_prog.last_opened_at = datetime.now(timezone.utc)

        await self.db.commit()

        # Emit GameEvent to Gamification Engine
        try:
            from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
            from app.domains.gamification.infrastructure.game_event_publisher import GameEventPublisher

            await GameEventPublisher.publish(
                user_id=user_id,
                event_type=GameEventType.SHADOWING_COMPLETED,
                source=GameEventSource.SHADOWING,
                source_id=attempt.id,
                metadata={
                    "segment_id": segment_id,
                    "video_id": video_id,
                    "score": shadow_eval.score,
                    "success": shadow_eval.success,
                    "timing_score": shadow_eval.timing_score,
                    "shadowing_mode": shadowing_mode,
                },
            )
        except Exception as ge:
            logger.warning(f"[ShadowingService] Error emitting shadowing.completed game event: {ge}")

        return SegmentPracticeCompleteResponse(
            exercise_id=exercise.id,
            attempt_id=attempt.id,
            segment_id=segment_id or "",
            target_text=target_text,
            user_transcript=user_spoken_text or None,
            score=shadow_eval.score,
            timing_score=shadow_eval.timing_score,
            pronunciation_score=shadow_eval.pronunciation_score,
            rhythm_score=shadow_eval.rhythm_score,
            accuracy_score=shadow_eval.accuracy_score,
            feedback=shadow_eval.feedback,
            strengths=shadow_eval.strengths,
            top_issues=shadow_eval.top_issues,
            mastery=new_mastery_state,
            mastery_delta=mastery_delta,
            review_scheduled_at=datetime.now(timezone.utc),
        )

    async def bookmark_segment(self, segment_id: str, user_id: str, note: str | None = None) -> BookmarkDTO:
        """Bookmarks a segment for quick access with personal study notes."""
        seg_res = await self.db.execute(select(ShadowingSegment).where(ShadowingSegment.id == segment_id))
        segment = seg_res.scalar_one_or_none()
        if not segment:
            raise NotFoundException(f"Segment '{segment_id}' not found.")

        bm_res = await self.db.execute(
            select(ShadowingBookmark).where(
                ShadowingBookmark.user_id == user_id,
                ShadowingBookmark.segment_id == segment_id,
            )
        )
        bm = bm_res.scalar_one_or_none()
        if bm:
            bm.note = note
        else:
            bm = ShadowingBookmark(
                user_id=user_id,
                video_id=segment.video_id,
                segment_id=segment_id,
                note=note,
            )
            self.db.add(bm)

        await self.db.commit()
        return BookmarkDTO(
            id=bm.id,
            user_id=bm.user_id,
            video_id=bm.video_id,
            segment_id=bm.segment_id,
            note=bm.note,
            created_at=bm.created_at,
        )

    async def remove_bookmark(self, segment_id: str, user_id: str) -> bool:
        """Deletes a segment bookmark."""
        await self.db.execute(
            delete(ShadowingBookmark).where(
                ShadowingBookmark.user_id == user_id,
                ShadowingBookmark.segment_id == segment_id,
            )
        )
        await self.db.commit()
        return True

    async def translate_segment(
        self,
        segment_id: str,
        user_id: str,
        target_language: str = "vi",
    ) -> SegmentTranslateResponse:
        """Translates segment text into nuanced Vietnamese/English with tone preservation."""
        seg_res = await self.db.execute(select(ShadowingSegment).where(ShadowingSegment.id == segment_id))
        segment = seg_res.scalar_one_or_none()
        if not segment:
            raise NotFoundException(f"Segment '{segment_id}' not found.")

        sys_inst, user_content = ShadowingPrompts.build_translation_prompt(
            text=segment.normalized_text,
            target_language=target_language,
        )

        req = AIRequest(
            task=AITask.TRANSLATION,
            system_instruction=sys_inst,
            messages=[
                AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst),
                AIMessage(role=AIMessageRole.USER, content=user_content),
            ],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.2,
            max_output_tokens=300,
            user_id=user_id,
        )

        try:
            resp = await self.ai_router.generate(task=AITask.TRANSLATION, request=req, user_id=user_id)
            clean_text = resp.text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text.replace("```json", "", 1).rstrip("```").strip()
            elif clean_text.startswith("```"):
                clean_text = clean_text.replace("```", "", 1).rstrip("```").strip()

            parsed = json.loads(clean_text)
            trans_text = parsed.get("translated_text", segment.normalized_text)
            nuance = parsed.get("nuance_note")
        except Exception as te:
            logger.warning(f"[ShadowingService] AI translation error: {te}")
            trans_text = segment.normalized_text
            nuance = "Bản dịch tự động tạm thời."

        return SegmentTranslateResponse(
            segment_id=segment.id,
            source_text=segment.normalized_text,
            target_language=target_language,
            translated_text=trans_text,
            explanation=nuance,
        )

    async def get_job_status(self, job_id: str) -> ShadowingJobStatusDTO:
        """Fetches background import job progression status."""
        j_res = await self.db.execute(select(ShadowingImportJob).where(ShadowingImportJob.id == job_id))
        job = j_res.scalar_one_or_none()
        if not job:
            raise NotFoundException(f"Job '{job_id}' not found.")

        return ShadowingJobStatusDTO(
            job_id=job.id,
            video_id=job.video_id,
            stage=job.stage,
            status=job.status,
            attempts=job.attempts,
            stage_statuses=job.stage_statuses_json,
            error_type=job.error_type,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    def _build_segment_dtos(self, db_segments: list[ShadowingSegment]) -> list[TranscriptSegmentDTO]:
        """Converts database segment records to domain DTOs."""
        dtos: list[TranscriptSegmentDTO] = []
        for s in db_segments:
            diff = None
            if s.difficulty_json:
                diff = DifficultyReport(**s.difficulty_json)

            vocab = [ExtractedVocabulary(**v) for v in (s.vocabulary_json or [])]
            grammar = [ExtractedGrammar(**g) for g in (s.grammar_json or [])]
            exprs = [NaturalExpression(**e) for e in (s.expressions_json or [])]
            cats = [CandidateCategory(c) for c in (s.candidate_categories_json or [])]

            dtos.append(
                TranscriptSegmentDTO(
                    id=s.id,
                    video_id=s.video_id,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    text=s.text,
                    normalized_text=s.normalized_text,
                    reading=s.reading,
                    ruby=JapaneseReadingResolver.to_ruby_chunks(s.normalized_text),
                    language=s.language,
                    confidence=s.confidence,
                    speaker_id=s.speaker_id,
                    sequence=s.sequence,
                    duration=round(s.end_time - s.start_time, 2),
                    difficulty=diff,
                    vocabulary=vocab,
                    grammar=grammar,
                    expressions=exprs,
                    candidate_categories=cats,
                    recommendation_score=s.recommendation_score,
                    recommendation_reason=s.recommendation_reason,
                )
            )
        return dtos
