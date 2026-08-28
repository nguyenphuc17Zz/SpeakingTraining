from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import (
    get_ai_router,
    get_ai_routing_service,
    get_ai_usage_service,
    get_credential_service,
    get_current_user,
)
from app.domains.ai.contracts import (
    AIRequest,
    ModelMetadata,
    ProviderHealth,
    ProviderMetadata,
)
from app.domains.ai.discovery import model_discovery_service
from app.domains.ai.registry import ModelRegistry, provider_registry
from app.domains.ai.router import AIRouter
from app.domains.ai.schemas import (
    AIResponseRead,
    AIRoutingPolicyRead,
    AIRoutingPolicyUpdate,
    AIUsageSummaryRead,
    GenerateRequestInput,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.domains.ai.service import AIRoutingService, AIUsageService
from app.domains.providers.service import CredentialService
from app.domains.users.models import User

from app.domains.providers.schemas import ProviderDetailRead

router = APIRouter(prefix="/ai", tags=["AI Router & Models"])


@router.get("/providers", response_model=list[ProviderDetailRead], summary="List Supported AI Providers with Status")
async def list_ai_providers(
    current_user: User = Depends(get_current_user),
    credential_service: CredentialService = Depends(get_credential_service),
):
    return await credential_service.list_providers_with_status(user_id=current_user.id)


@router.get("/models", response_model=list[ModelMetadata], summary="List AI Models & Capabilities (Dynamic Discovery)")
async def list_ai_models(
    provider: str | None = Query(None, description="Filter by provider"),
    refresh: bool = Query(False, description="Force refresh models from upstream AI provider APIs"),
    current_user: User = Depends(get_current_user),
    credential_service: CredentialService = Depends(get_credential_service),
):
    if provider:
        pid = provider.lower().strip()
        api_key = await credential_service.get_raw_key_for_provider(pid, user_id=current_user.id)
        return await model_discovery_service.get_models_for_provider(
            provider_id=pid,
            api_key=api_key,
            force_refresh=refresh,
        )

    # Build creds map for all providers
    creds_map: dict[str, str] = {}
    for pid in provider_registry.list_providers():
        key = await credential_service.get_raw_key_for_provider(pid, user_id=current_user.id)
        if key:
            creds_map[pid] = key

    return await model_discovery_service.get_all_models(
        credentials_map=creds_map,
        force_refresh=refresh,
    )


@router.post("/models/refresh", response_model=list[ModelMetadata], summary="Force Refresh AI Models from Upstream APIs")
async def refresh_ai_models(
    provider: str | None = Query(None, description="Optional provider ID to refresh"),
    current_user: User = Depends(get_current_user),
    credential_service: CredentialService = Depends(get_credential_service),
):
    if provider:
        pid = provider.lower().strip()
        api_key = await credential_service.get_raw_key_for_provider(pid, user_id=current_user.id)
        return await model_discovery_service.get_models_for_provider(
            provider_id=pid,
            api_key=api_key,
            force_refresh=True,
        )

    creds_map: dict[str, str] = {}
    for pid in provider_registry.list_providers():
        key = await credential_service.get_raw_key_for_provider(pid, user_id=current_user.id)
        if key:
            creds_map[pid] = key

    return await model_discovery_service.get_all_models(
        credentials_map=creds_map,
        force_refresh=True,
    )


@router.get("/health", response_model=list[ProviderHealth], summary="Get Real-time Provider Health & Circuit Breakers")
async def get_providers_health(
    current_user: User = Depends(get_current_user),
    ai_router: AIRouter = Depends(get_ai_router),
):
    return await ai_router.get_all_providers_health(user_id=current_user.id)


@router.post("/test-connection", response_model=TestConnectionResponse, summary="Test Live Connection to AI Provider")
async def test_provider_connection(
    payload: TestConnectionRequest,
    current_user: User = Depends(get_current_user),
    ai_router: AIRouter = Depends(get_ai_router),
):
    health = await ai_router.test_connection(payload.provider, user_id=current_user.id)
    return TestConnectionResponse(
        provider_id=health.provider_id,
        status=health.status,
        is_configured=health.is_configured,
        latency_ms=health.latency_ms,
        last_checked_at=health.last_checked_at,
        error_message=health.error_message,
        metadata=health.metadata,
    )


@router.post("/generate", response_model=AIResponseRead, summary="Execute AI Turn Generation via AI Router")
async def generate_ai_turn(
    payload: GenerateRequestInput,
    current_user: User = Depends(get_current_user),
    ai_router: AIRouter = Depends(get_ai_router),
):
    request = AIRequest(
        messages=payload.messages,
        task=payload.task,
        model=payload.model,
        provider=payload.provider,
        temperature=payload.temperature,
        max_output_tokens=payload.max_output_tokens,
        system_instruction=payload.system_instruction,
        response_format=payload.response_format,
        stream=False,
        metadata=payload.metadata,
    )
    resp = await ai_router.generate(task=payload.task, request=request, user_id=current_user.id)
    return AIResponseRead(
        text=resp.text,
        model=resp.model,
        provider=resp.provider,
        usage=resp.usage,
        finish_reason=resp.finish_reason,
        latency_ms=resp.latency_ms,
        fallback_occurred=resp.fallback_occurred,
        attempt_history=resp.attempt_history,
        request_id=resp.request_id,
        metadata=resp.metadata,
    )


@router.post("/stream", summary="Stream AI Turn Generation via Server-Sent Events (SSE)")
async def stream_ai_turn(
    payload: GenerateRequestInput,
    current_user: User = Depends(get_current_user),
    ai_router: AIRouter = Depends(get_ai_router),
):
    request = AIRequest(
        messages=payload.messages,
        task=payload.task,
        model=payload.model,
        provider=payload.provider,
        temperature=payload.temperature,
        max_output_tokens=payload.max_output_tokens,
        system_instruction=payload.system_instruction,
        response_format=payload.response_format,
        stream=True,
        metadata=payload.metadata,
    )

    async def event_generator():
        async for event in ai_router.stream(task=payload.task, request=request, user_id=current_user.id):
            yield f"data: {event.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/usage", response_model=AIUsageSummaryRead, summary="Get AI Token Usage & Latency Telemetry")
async def get_ai_usage(
    provider: str | None = Query(None),
    task: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    usage_service: AIUsageService = Depends(get_ai_usage_service),
):
    return await usage_service.get_usage_summary(
        user_id=current_user.id,
        provider=provider,
        task=task,
        limit=limit,
        offset=offset,
    )


@router.get("/routing", response_model=AIRoutingPolicyRead, summary="Get Current AI Routing Policy")
async def get_routing_policy(
    current_user: User = Depends(get_current_user),
    routing_service: AIRoutingService = Depends(get_ai_routing_service),
):
    return await routing_service.get_routing_policy(user_id=current_user.id)


@router.put("/routing", response_model=AIRoutingPolicyRead, summary="Update AI Routing Policy")
async def update_routing_policy(
    payload: AIRoutingPolicyUpdate,
    current_user: User = Depends(get_current_user),
    routing_service: AIRoutingService = Depends(get_ai_routing_service),
):
    return await routing_service.update_routing_policy(payload=payload, user_id=current_user.id)
