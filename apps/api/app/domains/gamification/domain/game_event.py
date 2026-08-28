import hashlib
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from app.domains.gamification.domain.contracts import GameEventSource, GameEventType


class GameEvent(BaseModel):
    """
    Normalized, immutable domain event emitted by learning, conversation, pronunciation, and shadowing systems.
    Has a deterministic or unique event_id for idempotency guarantees.
    """
    id: str | None = None
    user_id: str
    type: GameEventType
    source: GameEventSource
    source_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_id(self) -> str:
        """
        Derives an idempotent key from event attributes if explicit id is not provided.
        Ensures identical event submissions cannot award XP multiple times.
        """
        if self.id:
            return self.id
        raw_key = f"{self.user_id}:{self.type.value}:{self.source.value}:{self.source_id}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:36]
