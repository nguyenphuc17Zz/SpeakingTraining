from collections.abc import AsyncIterator
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class ModelCapability(str, Enum):
    TEXT = "text"
    STREAMING = "streaming"
    VISION = "vision"
    AUDIO = "audio"
    REASONING = "reasoning"
    STRUCTURED_OUTPUT = "structured_output"


class ModelMetadata(BaseModel):
    id: str
    provider_id: str
    display_name: str
    context_window: int = 32000
    capabilities: list[ModelCapability] = Field(default_factory=list)
    is_recommended: bool = False
    is_enabled: bool = True


class ProviderMetadata(BaseModel):
    id: str
    display_name: str
    description: str
    default_model: str
    models: list[ModelMetadata] = Field(default_factory=list)
    is_configured: bool = False
    requires_api_key: bool = True
    documentation_url: str = ""


class ChatMessage(BaseModel):
    role: str  # 'system', 'user', 'assistant'
    content: str
    audio_bytes: bytes | None = None


class GenerateRequest(BaseModel):
    model_id: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int | None = None
    system_instruction: str | None = None
    response_schema: dict[str, Any] | None = None


class GenerateResponse(BaseModel):
    text: str
    model_id: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class GenerateChunk(BaseModel):
    text_delta: str
    is_last: bool = False


class AIProvider(Protocol):
    """Protocol contract for all AI LLM Providers (Gemini, Groq, OpenRouter)."""

    provider_id: str

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        ...

    async def stream(self, request: GenerateRequest) -> AsyncIterator[GenerateChunk]:
        ...

    def get_supported_models(self) -> list[ModelMetadata]:
        ...
