from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import BaseModel


class SpokenTurn(BaseModel):
    speaker: str  # 'user' or 'ai'
    transcript: str
    audio_url: str | None = None
    confidence: float | None = None
    duration_ms: int | None = None


class ConversationContext(BaseModel):
    session_id: str
    persona_id: str
    user_id: str
    difficulty: str
    history: list[SpokenTurn] = []


class ConversationEngine(Protocol):
    """Protocol for Phase 2 Realtime / Turn-based conversation orchestrator."""

    async def handle_turn(self, context: ConversationContext, user_audio_or_text: str | bytes) -> SpokenTurn:
        ...

    async def stream_turn(self, context: ConversationContext, user_text: str) -> AsyncIterator[str]:
        ...
