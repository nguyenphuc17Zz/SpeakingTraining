import base64
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.pronunciation.schemas import (
    PronunciationAnalyzeRequest,
    PronunciationAttemptResponse,
    PronunciationHistoryItemDTO,
    PronunciationPracticeTargetDTO,
    PronunciationSummaryStatsDTO,
)
from app.domains.pronunciation.service import PronunciationService
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import ValidationException

router = APIRouter(prefix="/pronunciation", tags=["Pronunciation"])


async def get_current_user_id(
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db),
) -> str:
    if x_user_id:
        return x_user_id
    user_service = UserService(db)
    default_user = await user_service.get_or_create_default_user()
    return default_user.id


@router.post("/analyze", response_model=PronunciationAttemptResponse)
async def analyze_pronunciation(
    request: PronunciationAnalyzeRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Performs comprehensive Japanese pronunciation analysis on base64-encoded audio.
    Analyzes phonemes, mora timing, pitch accent, rhythm, and intonation, saving learning signals to learner memory.
    """
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
    except Exception as e:
        raise ValidationException(f"Invalid base64 audio payload: {e}")

    service = PronunciationService(db)
    return await service.analyze_audio(
        user_id=user_id,
        audio_bytes=audio_bytes,
        target_text=request.target_text,
        expected_reading=request.expected_reading,
        target_type=request.target_type,
        reference_type=request.reference_type,
        voicevox_speaker_id=request.voicevox_speaker_id,
        session_id=request.session_id,
        turn_id=request.turn_id,
    )


@router.post("/enqueue")
async def enqueue_pronunciation_analysis(
    request: PronunciationAnalyzeRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Enqueues audio for background asynchronous pronunciation analysis."""
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
    except Exception as e:
        raise ValidationException(f"Invalid base64 audio payload: {e}")

    service = PronunciationService(db)
    attempt_id = await service.enqueue_analysis(
        user_id=user_id,
        audio_bytes=audio_bytes,
        target_text=request.target_text,
        expected_reading=request.expected_reading,
        target_type=request.target_type,
        reference_type=request.reference_type,
        session_id=request.session_id,
        turn_id=request.turn_id,
    )
    return {"attempt_id": attempt_id, "status": "queued"}


@router.get("/attempts/{attempt_id}", response_model=PronunciationAttemptResponse)
async def get_pronunciation_attempt(
    attempt_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full analysis results, pitch curves, and feedback for a specific attempt."""
    service = PronunciationService(db)
    return await service.get_attempt(attempt_id)


@router.get("/history", response_model=list[PronunciationHistoryItemDTO])
async def get_pronunciation_history(
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves recent pronunciation attempts for the current user."""
    service = PronunciationService(db)
    return await service.get_user_history(user_id=user_id, limit=limit)


@router.get("/stats", response_model=PronunciationSummaryStatsDTO)
async def get_pronunciation_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves aggregate pronunciation scores and top improvement areas."""
    service = PronunciationService(db)
    return await service.get_user_summary_stats(user_id=user_id)


@router.get("/targets", response_model=list[PronunciationPracticeTargetDTO])
async def get_practice_targets(
    limit: int = Query(6, ge=1, le=20),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves curated practice target words/sentences targeting common Japanese pronunciation difficulties."""
    service = PronunciationService(db)
    return await service.get_practice_targets(user_id=user_id, limit=limit)
