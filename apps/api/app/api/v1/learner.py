from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learner_memory.schemas import (
    LearnerMemoryDetailRead,
    LearnerMemoryRead,
    LearnerProfileRead,
    LearningPriorityRead,
    MemoryEvidenceRead,
    MemoryFeedbackCreate,
    MemoryFeedbackRead,
)
from app.domains.learner_memory.service import LearnerMemoryService
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/learner", tags=["Learner Memory & Profile"])


async def get_current_user_id(
    db: AsyncSession = Depends(get_db),
) -> str:
    """Helper to resolve current user (or default user)."""
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    return user.id


@router.get("/profile", response_model=LearnerProfileRead)
async def get_learner_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the comprehensive long-term learner profile and skill levels."""
    service = LearnerMemoryService(db)
    return await service.get_profile(user_id)


@router.post("/profile/recalculate", response_model=LearnerProfileRead)
async def recalculate_learner_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Explicitly trigger full profile and memory recalculation."""
    service = LearnerMemoryService(db)
    return await service.recalculate_profile(user_id)


@router.get("/memories", response_model=list[LearnerMemoryRead])
async def list_learner_memories(
    type: str | None = Query(None, description="Filter by memory type (grammar, particle, filler, etc.)"),
    status: str | None = Query(None, description="Filter by status (new, active, improving, stable, resolved, dismissed)"),
    trend: str | None = Query(None, description="Filter by trend (improving, stable, worsening, new, resolved)"),
    min_priority: float | None = Query(None, description="Filter by minimum priority score (0.0 - 1.0)"),
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List persistent learner memories with rich filtering."""
    service = LearnerMemoryService(db)
    return await service.list_memories(
        user_id=user_id,
        memory_type=type,
        status=status,
        trend=trend,
        min_priority=min_priority,
        limit=limit,
    )


@router.get("/memories/{memory_id}", response_model=LearnerMemoryDetailRead)
async def get_learner_memory_detail(
    memory_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed memory record including all attached evidences."""
    service = LearnerMemoryService(db)
    return await service.get_memory_detail(user_id=user_id, memory_id=memory_id)


@router.get("/memories/{memory_id}/evidence", response_model=list[MemoryEvidenceRead])
async def get_memory_evidence(
    memory_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the chronological evidence trail for a specific memory item."""
    service = LearnerMemoryService(db)
    return await service.get_memory_evidences(user_id=user_id, memory_id=memory_id)


@router.get("/weaknesses", response_model=list[LearnerMemoryRead])
async def get_top_weaknesses(
    limit: int = Query(5, ge=1, le=20),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve top ranked linguistic weaknesses."""
    service = LearnerMemoryService(db)
    return await service.get_top_weaknesses(user_id=user_id, limit=limit)


@router.get("/strengths", response_model=list[LearnerMemoryRead])
async def get_top_strengths(
    limit: int = Query(5, ge=1, le=20),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve confirmed speaking strengths."""
    service = LearnerMemoryService(db)
    return await service.get_top_strengths(user_id=user_id, limit=limit)


@router.get("/goals", response_model=list[LearnerMemoryRead])
async def get_learner_goals(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve user learning goals."""
    service = LearnerMemoryService(db)
    return await service.get_goals(user_id=user_id)


@router.get("/priorities", response_model=list[LearningPriorityRead])
async def get_learning_priorities(
    limit: int = Query(5, ge=1, le=20),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve top learning priorities for adaptive recommendations (Phase 7 contract)."""
    service = LearnerMemoryService(db)
    return await service.get_learning_priorities(user_id=user_id, limit=limit)


@router.post("/memories/{memory_id}/feedback", response_model=MemoryFeedbackRead)
async def submit_memory_feedback(
    memory_id: str,
    payload: MemoryFeedbackCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit user control feedback (dismiss, mark inaccurate, restore)."""
    service = LearnerMemoryService(db)
    return await service.submit_feedback(user_id=user_id, memory_id=memory_id, payload=payload)
