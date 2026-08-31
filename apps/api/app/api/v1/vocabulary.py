from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.users.service import UserService
from app.domains.vocabulary.schemas import (
    SaveVocabularyNotebookRequest,
    SaveVocabularyNotebookResponse,
    VocabularyLookupRequest,
    VocabularyLookupResponse,
)
from app.domains.vocabulary.service import VocabularyService
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/vocabulary", tags=["Context-Aware AI Vocabulary Lookup"])


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    """Resolves current active user."""
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    return user.id


@router.post(
    "/ai-lookup",
    response_model=VocabularyLookupResponse,
    summary="Context-Aware Highlight & AI Vocabulary Lookup",
    status_code=status.HTTP_200_OK,
)
async def ai_lookup_vocabulary(
    payload: VocabularyLookupRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> VocabularyLookupResponse:
    """
    Performs multidimensional, context-aware Japanese vocabulary analysis using AI.
    Analyzes nuance, register, JLPT level, natural collocations, situation examples, and alternatives.
    """
    service = VocabularyService(db)
    return await service.lookup_contextual_vocabulary(payload=payload, user_id=user_id)


@router.post(
    "/save-notebook",
    response_model=SaveVocabularyNotebookResponse,
    summary="Save Looked-up Vocabulary to Learner Memory & Learning Items Notebook",
    status_code=status.HTTP_200_OK,
)
async def save_vocabulary_notebook(
    payload: SaveVocabularyNotebookRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> SaveVocabularyNotebookResponse:
    """
    Persists the vocabulary item into the user's notebook and learning training plan.
    """
    service = VocabularyService(db)
    return await service.save_to_notebook(payload=payload, user_id=user_id)
