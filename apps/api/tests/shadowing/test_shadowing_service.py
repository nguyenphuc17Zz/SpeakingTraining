import base64
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.pronunciation.schemas import PronunciationAttemptResponse
from app.domains.shadowing.contracts import ShadowingVideoMetadata, VideoStatus
from app.domains.shadowing.service import ShadowingService
from app.domains.users.service import UserService


@pytest.mark.asyncio
async def test_duplicate_video_import_reuses_existing(db_session: AsyncSession):
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db_session)

    mock_entries = [
        {"text": "これはテストのシャドーイングです。", "start": 0.0, "duration": 3.0, "end": 3.0},
        {"text": "日本語の発音をしっかり練習しましょう。", "start": 3.5, "duration": 4.0, "end": 7.5},
    ]

    mock_meta = ShadowingVideoMetadata(
        video_id="12345678901",
        url="https://www.youtube.com/watch?v=12345678901",
        canonical_url="https://www.youtube.com/watch?v=12345678901",
        title="Test Japanese Video",
        channel_name="Test Channel",
        thumbnail_url="https://img.youtube.com/vi/12345678901/hqdefault.jpg",
        source_status="available",
    )

    with patch("app.domains.shadowing.pipeline.import_pipeline.YouTubeTranscriptAdapter.get_transcript", AsyncMock(return_value=mock_entries)), \
         patch("app.domains.shadowing.pipeline.import_pipeline.YoutubeMetadataProvider.get_metadata", AsyncMock(return_value=mock_meta)):

        # First import (run sync)
        res1 = await service.import_video("https://www.youtube.com/watch?v=12345678901", user_id=user.id, run_sync=True)
        assert res1.status == VideoStatus.READY
        assert res1.is_existing is False

        # Second import with same URL -> should reuse existing
        res2 = await service.import_video("https://www.youtube.com/watch?v=12345678901", user_id=user.id)
        assert res2.is_existing is True
        assert res2.status == VideoStatus.READY


@pytest.mark.asyncio
async def test_start_and_complete_shadowing_practice(db_session: AsyncSession):
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db_session)

    mock_entries = [
        {"text": "お疲れ様でした。", "start": 0.0, "duration": 2.5, "end": 2.5},
    ]

    mock_meta = ShadowingVideoMetadata(
        video_id="98765432109",
        url="https://www.youtube.com/watch?v=98765432109",
        canonical_url="https://www.youtube.com/watch?v=98765432109",
        title="Workplace Japanese Video",
        channel_name="Work Channel",
        thumbnail_url="https://img.youtube.com/vi/98765432109/hqdefault.jpg",
        source_status="available",
    )

    with patch("app.domains.shadowing.pipeline.import_pipeline.YouTubeTranscriptAdapter.get_transcript", AsyncMock(return_value=mock_entries)), \
         patch("app.domains.shadowing.pipeline.import_pipeline.YoutubeMetadataProvider.get_metadata", AsyncMock(return_value=mock_meta)):
        await service.import_video("https://www.youtube.com/watch?v=98765432109", user_id=user.id, run_sync=True)

    # Fetch video and segment
    video_detail = await service.get_video("98765432109", user_id=user.id)
    assert len(video_detail.segments) >= 1
    segment = video_detail.segments[0]

    # 1. Start segment practice (instantiates Phase 7 Exercise)
    start_resp = await service.start_segment_practice(
        segment_id=segment.id,
        user_id=user.id,
        shadowing_mode="shadow",
    )
    assert start_resp.exercise_id is not None
    assert start_resp.attempt_id is not None

    # 2. Complete practice with mock PronunciationService response
    mock_pron_res = PronunciationAttemptResponse(
        id="pron_attempt_1",
        user_id=user.id,
        reference_text=segment.normalized_text,
        target_text=segment.normalized_text,
        user_text="お疲れ様でした",
        target_type="sentence",
        reference_type="youtube",
        analysis_status="completed",
        overall_score=88.5,
        overall_confidence="high",
        score_interpretation="Very Good",
        top_issues=[],
        strengths=["Tốt"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    fake_audio_base64 = base64.b64encode(b"RIFFdummywavdata").decode("ascii")

    with patch.object(service.pronunciation_service, "analyze_audio", AsyncMock(return_value=mock_pron_res)):
        complete_resp = await service.complete_segment_practice(
            exercise_id=start_resp.exercise_id,
            attempt_id=start_resp.attempt_id,
            audio_base64=fake_audio_base64,
            user_id=user.id,
            shadowing_mode="shadow",
        )

    assert complete_resp.score >= 70.0
    assert complete_resp.timing_score >= 80.0
    assert complete_resp.pronunciation_score >= 80.0
    assert complete_resp.mastery in ("comfortable", "practicing")


@pytest.mark.asyncio
async def test_bookmark_and_translate_segment(db_session: AsyncSession):
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db_session)

    mock_entries = [
        {"text": "本当にありがとうございます。", "start": 0.0, "duration": 3.0, "end": 3.0},
    ]

    mock_meta = ShadowingVideoMetadata(
        video_id="55555555555",
        url="https://www.youtube.com/watch?v=55555555555",
        canonical_url="https://www.youtube.com/watch?v=55555555555",
        title="Thank you video",
        channel_name="Gratitude Channel",
        thumbnail_url="https://img.youtube.com/vi/55555555555/hqdefault.jpg",
        source_status="available",
    )

    with patch("app.domains.shadowing.pipeline.import_pipeline.YouTubeTranscriptAdapter.get_transcript", AsyncMock(return_value=mock_entries)), \
         patch("app.domains.shadowing.pipeline.import_pipeline.YoutubeMetadataProvider.get_metadata", AsyncMock(return_value=mock_meta)):
        await service.import_video("https://www.youtube.com/watch?v=55555555555", user_id=user.id, run_sync=True)

    video_detail = await service.get_video("55555555555", user_id=user.id)
    segment = video_detail.segments[0]

    # Bookmark
    bm = await service.bookmark_segment(segment.id, user.id, note="Luyện phát âm câu này")
    assert bm.segment_id == segment.id
    assert bm.note == "Luyện phát âm câu này"

    # Remove Bookmark
    removed = await service.remove_bookmark(segment.id, user.id)
    assert removed is True


@pytest.mark.asyncio
async def test_complete_shadowing_practice_silent_speech_strict_zero_score(db_session: AsyncSession):
    """Verifies that when user audio contains no recognizable speech, the system returns strictly 0.0 with NO fallbacks."""
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db_session)

    mock_entries = [
        {"text": "はじめまして。", "start": 0.0, "duration": 2.0, "end": 2.0},
    ]
    mock_meta = ShadowingVideoMetadata(
        video_id="11122233344",
        url="https://www.youtube.com/watch?v=11122233344",
        canonical_url="https://www.youtube.com/watch?v=11122233344",
        title="Intro Video",
        channel_name="Intro Channel",
        thumbnail_url="https://img.youtube.com/vi/11122233344/hqdefault.jpg",
        source_status="available",
    )

    with patch("app.domains.shadowing.pipeline.import_pipeline.YouTubeTranscriptAdapter.get_transcript", AsyncMock(return_value=mock_entries)), \
         patch("app.domains.shadowing.pipeline.import_pipeline.YoutubeMetadataProvider.get_metadata", AsyncMock(return_value=mock_meta)):
        await service.import_video("https://www.youtube.com/watch?v=11122233344", user_id=user.id, run_sync=True)

    video_detail = await service.get_video("11122233344", user_id=user.id)
    segment = video_detail.segments[0]

    start_resp = await service.start_segment_practice(
        segment_id=segment.id,
        user_id=user.id,
        shadowing_mode="shadow",
    )

    # Empty speech recognition response (user didn't speak or Whisper heard nothing)
    mock_silent_pron_res = PronunciationAttemptResponse(
        id="pron_attempt_silent",
        user_id=user.id,
        reference_text=segment.normalized_text,
        target_text=segment.normalized_text,
        user_text=None,
        target_type="sentence",
        reference_type="youtube",
        analysis_status="completed",
        overall_score=0.0,
        overall_confidence="high",
        score_interpretation="No speech detected",
        top_issues=[],
        strengths=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    fake_audio_base64 = base64.b64encode(b"RIFFsilentaudiodata").decode("ascii")

    with patch.object(service.pronunciation_service, "analyze_audio", AsyncMock(return_value=mock_silent_pron_res)):
        complete_resp = await service.complete_segment_practice(
            exercise_id=start_resp.exercise_id,
            attempt_id=start_resp.attempt_id,
            audio_base64=fake_audio_base64,
            user_id=user.id,
            shadowing_mode="shadow",
        )

    # Strict assertion: Must be 0.0, no fake 75% or 93% fallback
    assert complete_resp.score == 0.0
    assert complete_resp.accuracy_score == 0.0
    assert complete_resp.pronunciation_score == 0.0
    assert complete_resp.user_transcript is None
    assert "Không nhận diện được giọng nói" in complete_resp.feedback


@pytest.mark.asyncio
async def test_shadowing_worker_recover_stale_jobs(db_session: AsyncSession):
    from app.domains.shadowing.worker import ShadowingImportWorker
    from app.domains.shadowing.models import ShadowingVideo, ShadowingImportJob
    from tests.conftest import TestAsyncSessionLocal

    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()

    # Create dummy video and stale job
    video = ShadowingVideo(
        video_id="stale_vid_123",
        url="https://youtube.com/watch?v=stale_vid_123",
        canonical_url="https://youtube.com/watch?v=stale_vid_123",
        title="Stale Test",
        channel_name="Test Channel",
        import_status=VideoStatus.PROCESSING.value,
    )
    db_session.add(video)
    await db_session.flush()

    job = ShadowingImportJob(
        video_id=video.id,
        user_id=user.id,
        status=VideoStatus.PROCESSING.value,
        stage="transcribing",
    )
    db_session.add(job)
    await db_session.commit()

    session_factory = async_sessionmaker(bind=db_session.bind, class_=AsyncSession, expire_on_commit=False)
    with patch("app.domains.shadowing.worker.AsyncSessionLocal", session_factory):
        worker = ShadowingImportWorker()
        recovered = await worker.recover_stale_jobs()
        assert recovered >= 1

    await db_session.refresh(job)
    assert job.status == VideoStatus.QUEUED.value

