import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.learning.goal_service import GoalService
from app.domains.shadowing.analysis.candidate_selector import ShadowingCandidateSelector
from app.domains.shadowing.analysis.difficulty_analyzer import DifficultyAnalyzer
from app.domains.shadowing.analysis.expression_extractor import NaturalExpressionExtractor
from app.domains.shadowing.analysis.grammar_extractor import GrammarExtractor
from app.domains.shadowing.analysis.vocabulary_extractor import VocabularyExtractor
from app.domains.shadowing.contracts import (
    TranscriptQuality,
    TranscriptSource,
    VideoStatus,
)
from app.domains.shadowing.models import (
    ShadowingImportJob,
    ShadowingSegment,
    ShadowingTranscript,
    ShadowingVideo,
)
from app.domains.shadowing.pipeline.chunk_processor import ChunkProcessor
from app.domains.shadowing.processing.quality_evaluator import TranscriptQualityEvaluator
from app.domains.shadowing.processing.segmenter import SentenceSegmenter
from app.domains.shadowing.processing.speaker_segmenter import SpeakerSegmenter
from app.domains.shadowing.youtube.metadata_provider import YoutubeMetadataProvider
from app.domains.shadowing.youtube.transcript_provider import YouTubeTranscriptAdapter
from app.domains.shadowing.youtube.url_resolver import YoutubeUrlResolver
from app.domains.shadowing.youtube.whisper_adapter import WhisperFallbackAdapter


class ImportPipeline:
    """End-to-end import, transcription, segmentation, linguistic analysis, and candidate selection pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metadata_provider = YoutubeMetadataProvider()
        self.yt_transcript_provider = YouTubeTranscriptAdapter()
        self.whisper_adapter = WhisperFallbackAdapter()
        self.profile_service = LearnerProfileService(db)
        self.goal_service = GoalService(db)
        self.chunk_processor = ChunkProcessor(db)

    async def execute_import(
        self,
        video_id: str,
        user_id: str,
        custom_whisper_model: str | None = None,
        job_id: str | None = None,
    ) -> ShadowingVideo:
        """
        Executes full multi-stage ingestion pipeline with fault isolation and partial availability support.
        """
        stage_statuses: dict[str, str] = {}

        # 1. Check or load job record
        job: ShadowingImportJob | None = None
        if job_id:
            j_res = await self.db.execute(select(ShadowingImportJob).where(ShadowingImportJob.id == job_id))
            job = j_res.scalar_one_or_none()

        # 2. Check or create ShadowingVideo record
        v_res = await self.db.execute(select(ShadowingVideo).where(ShadowingVideo.video_id == video_id))
        video = v_res.scalar_one_or_none()

        if not video:
            canonical_url = YoutubeUrlResolver.get_canonical_url(video_id)
            video = ShadowingVideo(
                video_id=video_id,
                url=canonical_url,
                canonical_url=canonical_url,
                title=f"YouTube Video ({video_id})",
                channel_name="YouTube Creator",
                import_status=VideoStatus.FETCHING_METADATA.value,
            )
            self.db.add(video)
            await self.db.flush()

        video.import_status = VideoStatus.FETCHING_METADATA.value
        await self.db.commit()

        # -------------------------------------------------------------
        # Stage 1: Fetch Video Metadata
        # -------------------------------------------------------------
        if job:
            job.stage = "fetching_metadata"
            job.status = VideoStatus.FETCHING_METADATA.value
            job.stage_statuses_json = dict(stage_statuses)
            await self.db.commit()

        try:
            meta = await self.metadata_provider.get_metadata(video_id)
            video.title = meta.title
            video.channel_name = meta.channel_name
            video.thumbnail_url = meta.thumbnail_url
            video.source_status = meta.source_status
            video.metadata_fetched_at = datetime.now(timezone.utc)
            stage_statuses["metadata"] = "completed"
        except Exception as me:
            logger.warning(f"[ImportPipeline] Metadata fetch warning for {video_id}: {me}")
            stage_statuses["metadata"] = "partial"

        # -------------------------------------------------------------
        # Stage 2: Resolve Japanese Transcript
        # -------------------------------------------------------------
        video.import_status = VideoStatus.RESOLVING_TRANSCRIPT.value
        if job:
            job.stage = "resolving_transcript"
            job.status = VideoStatus.RESOLVING_TRANSCRIPT.value
            job.stage_statuses_json = dict(stage_statuses)
        await self.db.commit()

        raw_entries: list[dict[str, Any]] = []
        transcript_source = TranscriptSource.YOUTUBE.value
        transcript_model = None

        try:
            raw_entries = await self.yt_transcript_provider.get_transcript(video_id)
            if raw_entries:
                stage_statuses["transcript_resolution"] = "completed (youtube)"
        except Exception as te:
            logger.info(f"[ImportPipeline] YouTube transcript failed for {video_id}: {te}")

        # -------------------------------------------------------------
        # Stage 3: Faster-Whisper Fallback if YouTube captions absent
        # -------------------------------------------------------------
        if not raw_entries:
            video.import_status = VideoStatus.TRANSCRIBING.value
            if job:
                job.stage = "transcribing"
                job.status = VideoStatus.TRANSCRIBING.value
                job.stage_statuses_json = dict(stage_statuses)
            await self.db.commit()
            try:
                raw_entries = await self.whisper_adapter.get_transcript(
                    video_id, custom_model=custom_whisper_model
                )
                if raw_entries:
                    transcript_source = TranscriptSource.FASTER_WHISPER.value
                    transcript_model = custom_whisper_model or "base"
                    stage_statuses["transcript_resolution"] = "completed (whisper_fallback)"
            except Exception as we:
                logger.error(f"[ImportPipeline] Whisper fallback failed for {video_id}: {we}")
                stage_statuses["transcript_resolution"] = "failed"

        # If transcript cannot be resolved at all, mark partial/failed and stop gracefully
        if not raw_entries:
            video.import_status = VideoStatus.PARTIAL.value
            stage_statuses["pipeline"] = "partial_no_transcript"
            if job:
                job.status = VideoStatus.PARTIAL.value
                job.stage = "completed"
                job.stage_statuses_json = stage_statuses
                job.error_message = "Japanese transcript is unavailable and Whisper fallback could not process audio."
                job.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            return video

        # -------------------------------------------------------------
        # Stage 4: Normalization & Sentence Segmentation
        # -------------------------------------------------------------
        video.import_status = VideoStatus.SEGMENTING.value
        if job:
            job.stage = "segmenting"
            job.status = VideoStatus.SEGMENTING.value
            job.stage_statuses_json = dict(stage_statuses)
        await self.db.commit()

        segments = SentenceSegmenter.segment_transcript(raw_entries, video_id=video_id)
        segments = SpeakerSegmenter.segment_speakers(segments)
        quality_rep = TranscriptQualityEvaluator.evaluate_transcript(segments)
        stage_statuses["segmentation"] = f"completed ({len(segments)} segments)"

        # Update video duration from segments
        if segments:
            video.duration_seconds = int(max(s.end_time for s in segments))

        # -------------------------------------------------------------
        # Stage 5: Content Difficulty & Linguistic Analysis
        # -------------------------------------------------------------
        video.import_status = VideoStatus.ANALYZING.value
        if job:
            job.stage = "analyzing"
            job.status = VideoStatus.ANALYZING.value
            job.stage_statuses_json = dict(stage_statuses)
        await self.db.commit()

        for seg in segments:
            seg.difficulty = DifficultyAnalyzer.analyze_segment_difficulty(
                text=seg.normalized_text,
                duration_seconds=seg.duration or (seg.end_time - seg.start_time),
                reading=seg.reading,
            )

        video_diff, diff_summary = DifficultyAnalyzer.aggregate_video_difficulty(segments)
        video.overall_difficulty = video_diff.value

        # Fetch learner context
        profile = await self.profile_service.get_or_create_profile(user_id)
        goals = await self.goal_service.get_active_goals(user_id)
        goal_titles = [g.title for g in goals] or profile.learning_goals or ["Everyday Japanese"]
        weaknesses = profile.weaknesses or []

        # Run AI chunk extraction
        ai_extracted = {"vocabulary": [], "grammar": [], "expressions": []}
        try:
            ai_extracted = await self.chunk_processor.process_transcript_chunks(
                segments=segments,
                user_id=user_id,
                learner_goals=goal_titles,
                learner_weaknesses=[w.get("statement", "") if isinstance(w, dict) else str(w) for w in weaknesses],
            )
            stage_statuses["ai_analysis"] = "completed"
        except Exception as ae:
            logger.warning(f"[ImportPipeline] AI analysis warning: {ae}")
            stage_statuses["ai_analysis"] = "partial"

        # Map vocabulary, grammar, expressions to segments
        vocab_by_seg = VocabularyExtractor.extract_from_segments(segments, ai_extracted.get("vocabulary"))
        grammar_by_seg = GrammarExtractor.extract_from_segments(segments, ai_extracted.get("grammar"))
        expr_by_seg = NaturalExpressionExtractor.extract_from_segments(segments, ai_extracted.get("expressions"))

        for seg in segments:
            seg.vocabulary = vocab_by_seg.get(seg.id, [])
            seg.grammar = grammar_by_seg.get(seg.id, [])
            seg.expressions = expr_by_seg.get(seg.id, [])

        # -------------------------------------------------------------
        # Stage 6: Candidate Selection & Ranking
        # -------------------------------------------------------------
        if job:
            job.stage = "candidate_selection"
            job.status = VideoStatus.ANALYZING.value
            job.stage_statuses_json = dict(stage_statuses)
            await self.db.commit()

        candidates = ShadowingCandidateSelector.select_candidates(
            segments=segments,
            learner_goals=goal_titles,
            learner_weaknesses=weaknesses,
            max_recommendations=8,
        )
        stage_statuses["candidate_selection"] = f"completed ({len(candidates)} recommended)"

        # Video summary JSON
        video.summary_json = {
            "topic": video.title,
            "speaking_style": "Conversational Japanese",
            "difficulty_summary": diff_summary,
            "recommended_count": len(candidates),
            "total_segments": len(segments),
            "transcript_source": transcript_source,
            "quality": quality_rep.quality.value,
        }

        # -------------------------------------------------------------
        # Stage 7: Persist Transcripts and Segments to Database
        # -------------------------------------------------------------
        # Calculate transcript hash
        content_hash = hashlib.sha256(
            "".join(s.normalized_text for s in segments).encode("utf-8")
        ).hexdigest()
        video.content_hash = content_hash

        # Delete any prior transcript and segments for this video to ensure idempotent reload
        await self.db.execute(delete(ShadowingTranscript).where(ShadowingTranscript.video_id == video.id))
        await self.db.flush()

        db_transcript = ShadowingTranscript(
            video_id=video.id,
            source=transcript_source,
            source_version="v1",
            model=transcript_model,
            language="ja",
            quality=quality_rep.quality.value,
            is_active=True,
            transcript_hash=content_hash,
            raw_data_json=raw_entries[:50],  # sample raw data
        )
        self.db.add(db_transcript)
        await self.db.flush()

        for seg in segments:
            db_seg = ShadowingSegment(
                id=seg.id,
                transcript_id=db_transcript.id,
                video_id=video.id,
                sequence=seg.sequence,
                start_time=seg.start_time,
                end_time=seg.end_time,
                text=seg.text,
                normalized_text=seg.normalized_text,
                reading=seg.reading,
                language="ja",
                confidence=seg.confidence,
                speaker_id=seg.speaker_id,
                quality_score=1.0,
                difficulty_json=seg.difficulty.model_dump() if seg.difficulty else None,
                vocabulary_json=[v.model_dump() for v in seg.vocabulary],
                grammar_json=[g.model_dump() for g in seg.grammar],
                expressions_json=[e.model_dump() for e in seg.expressions],
                candidate_categories_json=[c.value for c in seg.candidate_categories],
                recommendation_score=seg.recommendation_score,
                recommendation_reason=seg.recommendation_reason,
            )
            self.db.add(db_seg)

        video.import_status = VideoStatus.READY.value

        # Update Job status
        if job:
            job.status = VideoStatus.READY.value
            job.stage = "done"
            job.stage_statuses_json = stage_statuses
            job.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        logger.info(f"[ImportPipeline] Video {video_id} successfully imported with {len(segments)} segments.")
        return video
