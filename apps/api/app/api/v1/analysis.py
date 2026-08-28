from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.conversation_intelligence.schemas import (
    AnalysisFeedbackCreate,
    AnalysisFeedbackRead,
    AnalysisJobRead,
    ConversationAnalysisSummaryRead,
    TurnAnalysisRead,
)
from app.domains.conversation_intelligence.service import ConversationIntelligenceService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import NotFoundException

router = APIRouter(tags=["Conversation Intelligence"])


@router.get("/conversations/{session_id}/analysis", response_model=ConversationAnalysisSummaryRead)
async def get_session_analysis_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full conversation intelligence summary, including session review and turn-by-turn analyses."""
    service = ConversationIntelligenceService(db)
    return await service.get_session_analysis_summary(session_id)


@router.get("/conversations/{session_id}/turns/{turn_id}/analysis", response_model=TurnAnalysisRead)
async def get_turn_analysis(
    session_id: str,
    turn_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve deep linguistic and correctness analysis for a specific spoken turn."""
    service = ConversationIntelligenceService(db)
    analysis = await service.get_turn_analysis(turn_id)
    if not analysis:
        raise NotFoundException(f"Analysis for turn '{turn_id}' not found or still processing.")
    return analysis


@router.post("/conversations/{session_id}/analysis", response_model=AnalysisJobRead)
async def trigger_session_analysis(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Trigger or re-run background whole-session holistic review."""
    service = ConversationIntelligenceService(db)
    return await service.enqueue_session_analysis(session_id)


@router.post("/conversations/{session_id}/turns/{turn_id}/analysis", response_model=AnalysisJobRead)
async def trigger_turn_analysis(
    session_id: str,
    turn_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Trigger or re-run background deep analysis for a specific user turn."""
    service = ConversationIntelligenceService(db)
    return await service.enqueue_turn_analysis(session_id=session_id, turn_id=turn_id)


@router.post("/analyses/feedback", response_model=AnalysisFeedbackRead)
async def submit_analysis_feedback(
    payload: AnalysisFeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit learner feedback (helpful / not helpful / wrong correction) for continual quality calibration."""
    service = ConversationIntelligenceService(db)
    return await service.submit_feedback(payload)


@router.get("/analyses/jobs/{job_id}", response_model=AnalysisJobRead)
async def get_analysis_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Check status of a background intelligence analysis job."""
    service = ConversationIntelligenceService(db)
    return await service.get_job_status(job_id)
