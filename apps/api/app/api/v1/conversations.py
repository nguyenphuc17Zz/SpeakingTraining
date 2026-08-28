from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.conversation.schemas import (
    AudioTurnResponse,
    ConversationRecentSessionRead,
    ConversationSessionCreate,
    ConversationSessionRead,
    ConversationSessionSummary,
    ConversationTurnCreate,
)
from app.domains.conversation.service import ConversationService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import ValidationException

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/recent", response_model=list[ConversationRecentSessionRead])
async def list_recent_conversations(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve recent conversation sessions with duration, turns, and persona metadata."""
    service = ConversationService(db)
    return await service.list_recent_sessions(limit=limit)


@router.post("", response_model=ConversationSessionRead, status_code=201)
async def start_conversation_session(
    create_dto: ConversationSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Start a new speaking conversation session with selected persona and config snapshot."""
    service = ConversationService(db)
    return await service.start_session(create_dto)


@router.get("/{session_id}", response_model=ConversationSessionRead)
async def get_conversation_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get conversation session details and full turn history."""
    service = ConversationService(db)
    return await service.get_session(session_id)


from app.shared.validation.limits import validate_audio_payload, validate_text_input


@router.post("/{session_id}/audio-turn", response_model=AudioTurnResponse)
async def process_audio_turn(
    session_id: str,
    audio_file: UploadFile = File(...),
    client_turn_id: str | None = Form(None),
    browser_transcript: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Process an audio utterance from browser mic: STT -> AI Context -> LLM -> TTS -> Audio playback."""
    if not audio_file:
        raise ValidationException("Audio file is required.")

    audio_bytes = await audio_file.read()
    validate_audio_payload(audio_bytes)

    service = ConversationService(db)
    return await service.process_audio_turn(
        session_id=session_id,
        audio_bytes=audio_bytes,
        client_turn_id=client_turn_id,
        browser_transcript=browser_transcript,
    )


@router.post("/{session_id}/turns", response_model=AudioTurnResponse)
async def process_text_turn(
    session_id: str,
    turn_dto: ConversationTurnCreate,
    db: AsyncSession = Depends(get_db),
):
    """Send text turn into active conversation session."""
    validated_text = validate_text_input(turn_dto.transcript, field_name="transcript")
    service = ConversationService(db)
    return await service.process_text_turn(
        session_id=session_id,
        user_text=validated_text,
        client_turn_id=turn_dto.client_turn_id,
    )


@router.post("/{session_id}/end", response_model=ConversationSessionRead)
async def end_conversation_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Conclude an active conversation session and compute duration."""
    service = ConversationService(db)
    return await service.end_session(session_id)


@router.get("/{session_id}/summary", response_model=ConversationSessionSummary)
async def get_conversation_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive statistics and summary for a finished conversation session."""
    service = ConversationService(db)
    return await service.get_session_summary(session_id)
