from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.shadowing.contracts import ShadowingCandidate, ShadowingLesson
from app.domains.shadowing.schemas import (
    BookmarkDTO,
    BookmarkRequest,
    CreateLessonRequest,
    SegmentPracticeCompleteRequest,
    SegmentPracticeCompleteResponse,
    SegmentPracticeStartRequest,
    SegmentPracticeStartResponse,
    SegmentTranslateRequest,
    SegmentTranslateResponse,
    ShadowingJobStatusDTO,
    ShadowingVideoDetailDTO,
    ShadowingVideoDTO,
    ShadowingVideoListResponse,
    VideoImportRequest,
    VideoImportResponse,
)
from app.domains.shadowing.service import ShadowingService
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/shadowing", tags=["shadowing"])


@router.post("/videos/import", response_model=VideoImportResponse)
async def import_video(
    req: VideoImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Imports a YouTube video via URL for sentence segmentation, linguistic analysis, and personalized shadowing practice.
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    return await service.import_video(
        url=req.url,
        user_id=user.id,
        custom_whisper_model=req.custom_whisper_model,
        run_sync=False,
    )


@router.get("/videos", response_model=ShadowingVideoListResponse)
async def list_videos(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists recently imported YouTube videos with speaking difficulty and metadata.
    """
    service = ShadowingService(db)
    videos = await service.get_videos(limit=limit, offset=offset)
    return ShadowingVideoListResponse(videos=videos, total=len(videos))


@router.get("/videos/{video_id}", response_model=ShadowingVideoDetailDTO)
async def get_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves full video details, timestamped transcript segments, vocabulary, grammar, and recommendations.
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    return await service.get_video(video_id=video_id, user_id=user.id)


@router.delete("/videos/{video_id}")
async def delete_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a shadowing video along with its transcripts, segments, bookmarks, and exercises.
    """
    service = ShadowingService(db)
    return await service.delete_video(video_id=video_id)


@router.get("/videos/{video_id}/recommendations", response_model=list[ShadowingCandidate])
async def get_video_recommendations(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculates top recommended clips matching learner profile, goals, and pronunciation weaknesses.
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    return await service.get_recommendations(video_id=video_id, user_id=user.id)


@router.post("/videos/{video_id}/lesson", response_model=ShadowingLesson)
async def create_lesson(
    video_id: str,
    req: CreateLessonRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a structured shadowing lesson fitting target time budget (10/15/20/30 min).
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    return await service.create_lesson(
        video_id=video_id,
        user_id=user.id,
        time_budget_minutes=req.time_budget_minutes,
        mode=req.mode,
    )


@router.post("/segments/{segment_id}/practice/start", response_model=SegmentPracticeStartResponse)
async def start_practice(
    segment_id: str,
    req: SegmentPracticeStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates shadowing practice for a segment, creating a formal Phase 7 Exercise and ExerciseAttempt.
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    return await service.start_segment_practice(
        segment_id=segment_id,
        user_id=user.id,
        shadowing_mode=req.shadowing_mode,
    )


@router.post("/segments/{segment_id}/practice/complete", response_model=SegmentPracticeCompleteResponse)
async def complete_practice(
    segment_id: str,
    req: SegmentPracticeCompleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates learner audio using Phase 6 Pronunciation Engine and updates Phase 7 Mastery and spaced reviews.
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    return await service.complete_segment_practice(
        exercise_id=req.exercise_id,
        attempt_id=req.attempt_id,
        audio_base64=req.audio_base64,
        user_id=user.id,
        shadowing_mode=req.shadowing_mode,
        playback_speed=req.playback_speed,
        client_transcript=req.client_transcript,
    )


@router.post("/segments/{segment_id}/bookmark", response_model=BookmarkDTO)
async def bookmark_segment(
    segment_id: str,
    req: BookmarkRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Saves a segment to bookmarks with user personal study note.
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    return await service.bookmark_segment(
        segment_id=segment_id,
        user_id=user.id,
        note=req.note,
    )


@router.delete("/segments/{segment_id}/bookmark")
async def delete_bookmark(
    segment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Removes a segment bookmark.
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    success = await service.remove_bookmark(segment_id=segment_id, user_id=user.id)
    return {"success": success}


@router.post("/segments/{segment_id}/translate", response_model=SegmentTranslateResponse)
async def translate_segment(
    segment_id: str,
    req: SegmentTranslateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Translates spoken segment into nuanced Vietnamese or English with spoken idiom explanations.
    """
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = ShadowingService(db)

    return await service.translate_segment(
        segment_id=segment_id,
        user_id=user.id,
        target_language=req.target_language,
    )


@router.get("/jobs/{job_id}", response_model=ShadowingJobStatusDTO)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves progress status of an active YouTube import job.
    """
    service = ShadowingService(db)
    return await service.get_job_status(job_id=job_id)
