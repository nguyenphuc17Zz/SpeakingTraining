from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domains.ai.contracts import (
    AIMessage,
    AITask,
    AIUsage,
    ProviderHealthStatus,
    ResponseFormat,
)


class GenerateRequestInput(BaseModel):
    messages: list[AIMessage]
    task: AITask = AITask.GENERAL
    model: str | None = None
    provider: str | None = None
    temperature: float = 0.7
    max_output_tokens: int | None = None
    system_instruction: str | None = None
    response_format: ResponseFormat | None = None
    stream: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIResponseRead(BaseModel):
    text: str
    model: str
    provider: str
    usage: AIUsage
    finish_reason: str | None = "stop"
    latency_ms: int = 0
    fallback_occurred: bool = False
    attempt_history: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestConnectionRequest(BaseModel):
    provider: str


class TestConnectionResponse(BaseModel):
    provider_id: str
    status: ProviderHealthStatus
    is_configured: bool
    latency_ms: int | None = None
    last_checked_at: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIUsageRecordRead(BaseModel):
    id: str
    user_id: str
    request_id: str
    provider: str
    model: str
    task: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int
    success: bool
    error_type: str | None = None
    fallback_occurred: bool
    attempts_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIUsageSummaryRead(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    avg_latency_ms: float
    recent_records: list[AIUsageRecordRead] = Field(default_factory=list)


class AIRoutingPolicyRead(BaseModel):
    routing_mode: str  # 'auto' | 'manual'
    preferred_provider: str
    default_model: str
    fallback_enabled: bool
    fallback_priority: list[str]


class AIRoutingPolicyUpdate(BaseModel):
    routing_mode: str | None = None
    preferred_provider: str | None = None
    default_model: str | None = None
    fallback_enabled: bool | None = None
    fallback_priority: list[str] | None = None
