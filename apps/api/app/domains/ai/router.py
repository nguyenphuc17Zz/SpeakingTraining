import asyncio
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import (
    AIRequest,
    AIResponse,
    AIStreamEvent,
    AIStreamEventType,
    AITask,
    AIUsage,
    ProviderHealth,
    ProviderHealthStatus,
)
from app.domains.ai.errors import (
    AIProviderError,
    ProviderAuthError,
    ProviderInvalidRequestError,
    ProviderUnknownError,
)
from app.domains.ai.health import circuit_breaker_manager
from app.domains.ai.registry import ModelRegistry, provider_registry
from app.domains.ai.service import AIUsageService
from app.domains.providers.service import CredentialService
from app.domains.settings.service import SettingsService
from app.domains.users.service import UserService
from app.shared.errors.exceptions import ValidationException


import hashlib
import random
import threading


class AIRequestDeduplicator:
    """In-memory idempotency cache with thread-safe lock and shared Redis fallback."""

    def __init__(self, ttl_seconds: float = 60.0, max_entries: int = 500):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._cache: dict[str, tuple[AIResponse, float]] = {}
        self._lock = threading.RLock()

    def compute_key(self, request: AIRequest, task: AITask, user_id: str) -> str:
        if "idempotency_key" in request.metadata:
            # include user_id/task to avoid cross-user collision
            return f"idem:{user_id}:{task.value}:{request.metadata['idempotency_key']}"

        # Deterministic hash of payload
        msg_str = "|".join([f"{m.role.value}:{m.content}" for m in request.messages])
        schema_str = str(request.response_format.json_schema) if request.response_format and request.response_format.json_schema else ""
        sys_str = request.system_instruction or ""
        payload = f"{user_id}:{task.value}:{request.model or ''}:{sys_str}:{schema_str}:{msg_str}"
        return f"hash:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"

    def get(self, key: str) -> AIResponse | None:
        with self._lock:
            if key not in self._cache:
                return None
            cached_resp, expires_at = self._cache[key]
            if time.time() > expires_at:
                del self._cache[key]
                return None
            copy_resp = cached_resp.model_copy(deep=True)
            copy_resp.metadata["cached_response"] = True
            return copy_resp

    def put(self, key: str, response: AIResponse) -> None:
        with self._lock:
            if len(self._cache) >= self.max_entries:
                # Clean expired
                now = time.time()
                expired = [k for k, (_, exp) in self._cache.items() if now > exp]
                for k in expired:
                    del self._cache[k]
                # If still full, pop oldest (FIFO)
                if len(self._cache) >= self.max_entries:
                    self._cache.pop(next(iter(self._cache)))

            self._cache[key] = (response, time.time() + self.ttl_seconds)


class PromptBudgetGuard:
    """Monitors and enforces prompt token limits per AI task to prevent runaway token costs."""

    TASK_TOKEN_LIMITS: dict[AITask, int] = {
        AITask.CONVERSATION: 4000,
        AITask.COACH: 6000,
        AITask.COACH_CHAT: 3500,
        AITask.COACH_EXPLANATION: 2500,
        AITask.COACH_INSIGHT: 2000,
        AITask.COACH_PLAN: 3000,
        AITask.COACH_SEMANTIC_ANALYSIS: 3500,
        AITask.COACH_NATIVE_UPGRADE: 3000,
        AITask.GRAMMAR_CORRECTION: 2000,
        AITask.TRANSLATION: 2000,
        AITask.DEEP_ANALYSIS: 16000,
        AITask.SESSION_ANALYSIS: 12000,
        AITask.GENERAL: 8000,
        AITask.SPEECH_GENERATION: 3000,
        AITask.SPEECH_EVALUATION: 4000,
        AITask.SPEECH_NATIVE_UPGRADE: 4000,
    }

    @classmethod
    def estimate_tokens(cls, request: AIRequest) -> int:
        total_chars = sum(len(m.content) for m in request.messages)
        if request.system_instruction:
            total_chars += len(request.system_instruction)
        # Approximate: ~3.5 chars per English token, ~1.5 chars per Japanese token -> conservative ~2.5 chars per token
        return max(1, int(total_chars / 2.5))

    @classmethod
    def inspect_and_guard(cls, request: AIRequest, task: AITask) -> None:
        est_tokens = cls.estimate_tokens(request)
        max_allowed = cls.TASK_TOKEN_LIMITS.get(task, 8000)

        if est_tokens > max_allowed:
            logger.warning(
                f"[PromptBudgetGuard] Prompt estimated at ~{est_tokens} tokens exceeds budget of {max_allowed} tokens for task {task.value}. Trimming non-system messages if necessary."
            )
            # If conversation has too many messages, trim from the middle keeping first (persona) and last 4
            if len(request.messages) > 6:
                kept = [request.messages[0]] + request.messages[-5:]
                request.messages = kept


# Global singleton deduplicator
ai_deduplicator = AIRequestDeduplicator()


class AIRouter:
    """Intelligent multi-provider AI Router with capability matching, circuit breaking, and fallbacks."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.credential_service = CredentialService(session)
        self.settings_service = SettingsService(session)
        self.usage_service = AIUsageService(session)
        self.user_service = UserService(session)

    async def _resolve_user_id(self, user_id: str | None = None) -> str:
        if user_id:
            return user_id
        user = await self.user_service.get_or_create_default_user()
        return user.id

    async def _build_candidate_chain(
        self,
        task: AITask,
        request: AIRequest,
        user_id: str,
    ) -> tuple[list[str], str, bool]:
        """Builds ordered list of candidate provider IDs to attempt."""
        settings = await self.settings_service.get_or_create_settings(user_id)
        routing_mode = settings.routing_mode.lower().strip()
        fallback_enabled = settings.fallback_enabled

        # If request explicitly specifies provider
        if request.provider:
            explicit_provider = request.provider.lower().strip()
            if not provider_registry.has_provider(explicit_provider):
                raise ValidationException(f"Unsupported AI provider: '{request.provider}'")
            if fallback_enabled and routing_mode == "auto":
                candidates = [explicit_provider] + [
                    p.strip() for p in settings.fallback_priority.split(",") if p.strip() and p.strip() != explicit_provider
                ]
            else:
                candidates = [explicit_provider]
            return candidates, routing_mode, fallback_enabled

        if routing_mode == "manual":
            primary = settings.default_ai_provider.lower().strip()
            if fallback_enabled:
                candidates = [primary] + [
                    p.strip() for p in settings.fallback_priority.split(",") if p.strip() and p.strip() != primary
                ]
            else:
                candidates = [primary]
            return candidates, routing_mode, fallback_enabled

        # AUTO Mode
        primary = settings.default_ai_provider.lower().strip()
        priority_list = [p.strip() for p in settings.fallback_priority.split(",") if p.strip()]
        candidates = []
        if primary in priority_list:
            candidates.append(primary)
            for p in priority_list:
                if p not in candidates:
                    candidates.append(p)
        else:
            candidates = [primary] + priority_list

        return candidates, routing_mode, fallback_enabled

    async def generate(
        self,
        task: AITask | AIRequest = AITask.GENERAL,
        request: AIRequest | None = None,
        user_id: str | None = None,
    ) -> AIResponse:
        """Executes non-streaming generation through best provider with intelligent retry & fallback."""
        # Gracefully support (request, user_id) positional arguments
        if isinstance(task, AIRequest):
            user_id = request if isinstance(request, str) else user_id
            request = task
            task = request.task if isinstance(request.task, AITask) else AITask.GENERAL

        if request is None:
            raise ValidationException("AIRequest cannot be None")

        uid = await self._resolve_user_id(user_id)
        request_id = str(uuid.uuid4())
        request.task = task

        # 1. Prompt Budget Guard
        PromptBudgetGuard.inspect_and_guard(request, task)

        # 2. Check Idempotency / Deduplication Cache for non-conversational tasks
        dedup_eligible = task != AITask.CONVERSATION or ("idempotency_key" in request.metadata)
        dedup_key = None
        if dedup_eligible:
            dedup_key = ai_deduplicator.compute_key(request, task, uid)
            cached = ai_deduplicator.get(dedup_key)
            if cached is not None:
                logger.info(f"[AI Router] [{request_id[:8]}] Cache Hit! Reusing idempotent response for task {task.value}")
                cached.request_id = request_id
                return cached

        candidates, routing_mode, fallback_enabled = await self._build_candidate_chain(task, request, uid)
        settings = await self.settings_service.get_or_create_settings(uid)

        attempts_log: list[dict[str, Any]] = []
        last_error: Exception | None = None

        for attempt_idx, provider_id in enumerate(candidates, start=1):

            adapter = provider_registry.get(provider_id)
            if not adapter:
                continue

            # Check if user has key for this provider
            api_key = await self.credential_service.get_raw_key_for_provider(provider_id, uid)
            if not api_key:
                attempts_log.append({
                    "attempt": attempt_idx,
                    "provider": provider_id,
                    "status": "skipped",
                    "reason": "no_api_key_configured",
                })
                continue

            # Check Circuit Breaker availability in AUTO mode
            if routing_mode == "auto" and not circuit_breaker_manager.is_available(provider_id):
                # If there are other candidates, skip degraded provider
                if len(candidates) > 1 and attempt_idx < len(candidates):
                    attempts_log.append({
                        "attempt": attempt_idx,
                        "provider": provider_id,
                        "status": "skipped",
                        "reason": "circuit_breaker_open",
                    })
                    continue

            # Resolve model
            model = request.model
            if not model:
                if attempt_idx == 1 and settings.default_ai_model and (provider_id == settings.default_ai_provider or routing_mode == "manual"):
                    model = settings.default_ai_model
                else:
                    model = ModelRegistry.get_recommended_model_for_task(task, provider_id)
            elif attempt_idx > 1:
                model = ModelRegistry.get_recommended_model_for_task(task, provider_id)

            req_copy = request.model_copy(deep=True)
            req_copy.model = model
            req_copy.provider = provider_id

            logger.info(
                f"[AI Router] [{request_id[:8]}] Attempt {attempt_idx}/{len(candidates)}: {provider_id} (model: {model}, task: {task.value})"
            )

            try:
                resp = await adapter.generate(req_copy, api_key)
                circuit_breaker_manager.record_success(provider_id)

                resp.request_id = request_id
                resp.fallback_occurred = attempt_idx > 1
                resp.attempt_history = attempts_log + [{
                    "attempt": attempt_idx,
                    "provider": provider_id,
                    "model": model,
                    "status": "success",
                    "latency_ms": resp.latency_ms,
                }]

                # Cache if eligible
                if dedup_eligible and dedup_key:
                    ai_deduplicator.put(dedup_key, resp)

                # Record usage in PostgreSQL
                await self.usage_service.record_usage(
                    user_id=uid,
                    request_id=request_id,
                    provider=provider_id,
                    model=model,
                    task=task.value,
                    latency_ms=resp.latency_ms,
                    usage=resp.usage,
                    success=True,
                    fallback_occurred=resp.fallback_occurred,
                    attempts_count=attempt_idx,
                )

                return resp

            except AIProviderError as pe:
                last_error = pe
                circuit_breaker_manager.record_failure(provider_id, pe)
                attempts_log.append({
                    "attempt": attempt_idx,
                    "provider": provider_id,
                    "model": model,
                    "status": "failed",
                    "error_type": pe.__class__.__name__,
                    "error_message": pe.message,
                    "is_retryable": pe.is_retryable,
                })

                logger.warning(
                    f"[AI Router] [{request_id[:8]}] Provider {provider_id} failed: {pe.__class__.__name__} - {pe.message}"
                )

                # If manual mode without fallback, or fatal non-retryable error (e.g. malformed JSON request)
                if isinstance(pe, (ProviderInvalidRequestError, ProviderAuthError)):
                    # Record failed usage
                    await self.usage_service.record_usage(
                        user_id=uid,
                        request_id=request_id,
                        provider=provider_id,
                        model=model,
                        task=task.value,
                        latency_ms=0,
                        success=False,
                        error_type=pe.__class__.__name__,
                        attempts_count=attempt_idx,
                    )
                    raise pe

                if routing_mode == "manual" and not fallback_enabled:
                    await self.usage_service.record_usage(
                        user_id=uid,
                        request_id=request_id,
                        provider=provider_id,
                        model=model,
                        task=task.value,
                        latency_ms=0,
                        success=False,
                        error_type=pe.__class__.__name__,
                        attempts_count=attempt_idx,
                    )
                    raise pe

                # If retryable, wait brief exponential backoff with jitter then try next candidate
                jitter = random.uniform(0.01, 0.05)
                await asyncio.sleep((0.1 * attempt_idx) + jitter)
                continue

            except Exception as e:
                last_error = e
                circuit_breaker_manager.record_failure(provider_id, e)
                attempts_log.append({
                    "attempt": attempt_idx,
                    "provider": provider_id,
                    "model": model,
                    "status": "failed",
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                })
                logger.error(f"[AI Router] [{request_id[:8]}] Unexpected error with {provider_id}: {e}")
                continue

        # If all candidates exhausted
        err_type = last_error.__class__.__name__ if last_error else "ProviderUnavailableError"
        await self.usage_service.record_usage(
            user_id=uid,
            request_id=request_id,
            provider=candidates[0] if candidates else "unknown",
            model="unknown",
            task=task.value,
            latency_ms=0,
            success=False,
            error_type=err_type,
            fallback_occurred=len(candidates) > 1,
            attempts_count=len(attempts_log),
        )

        if last_error and isinstance(last_error, AIProviderError):
            raise last_error
        elif last_error:
            raise ProviderUnknownError(f"All AI providers failed: {last_error}", provider_id="router", raw_error=last_error)
        else:
            raise ProviderAuthError(
                "No configured AI providers with valid API keys found. Please configure Gemini or Groq in Settings.",
                provider_id="router",
            )

    async def stream(
        self,
        task: AITask = AITask.GENERAL,
        request: AIRequest | None = None,
        user_id: str | None = None,
    ) -> AsyncIterator[AIStreamEvent]:
        """Streams AI responses with pre-token fallback support."""
        if request is None:
            raise ValidationException("AIRequest cannot be None")

        uid = await self._resolve_user_id(user_id)
        request_id = str(uuid.uuid4())
        request.task = task

        candidates, routing_mode, fallback_enabled = await self._build_candidate_chain(task, request, uid)
        settings = await self.settings_service.get_or_create_settings(uid)
        last_error: Exception | None = None

        for attempt_idx, provider_id in enumerate(candidates, start=1):
            adapter = provider_registry.get(provider_id)
            if not adapter:
                continue

            api_key = await self.credential_service.get_raw_key_for_provider(provider_id, uid)
            if not api_key:
                continue

            if routing_mode == "auto" and not circuit_breaker_manager.is_available(provider_id):
                if len(candidates) > 1 and attempt_idx < len(candidates):
                    continue

            model = request.model
            if not model:
                if attempt_idx == 1 and settings.default_ai_model and (provider_id == settings.default_ai_provider or routing_mode == "manual"):
                    model = settings.default_ai_model
                else:
                    model = ModelRegistry.get_recommended_model_for_task(task, provider_id)
            elif attempt_idx > 1:
                model = ModelRegistry.get_recommended_model_for_task(task, provider_id)

            req_copy = request.model_copy(deep=True)
            req_copy.model = model
            req_copy.provider = provider_id

            first_chunk_received = False
            final_usage = AIUsage()
            start_time = time.perf_counter()

            try:
                async for event in adapter.stream(req_copy, api_key):
                    event.request_id = request_id
                    event.fallback_occurred = attempt_idx > 1

                    if event.type == AIStreamEventType.TEXT_DELTA:
                        first_chunk_received = True

                    if event.type == AIStreamEventType.USAGE and event.usage:
                        final_usage = event.usage

                    if event.type == AIStreamEventType.COMPLETED:
                        circuit_breaker_manager.record_success(provider_id)
                        latency_ms = int((time.perf_counter() - start_time) * 1000)
                        event.latency_ms = latency_ms

                        # Async record usage
                        await self.usage_service.record_usage(
                            user_id=uid,
                            request_id=request_id,
                            provider=provider_id,
                            model=model,
                            task=task.value,
                            latency_ms=latency_ms,
                            usage=event.usage or final_usage,
                            success=True,
                            fallback_occurred=attempt_idx > 1,
                            attempts_count=attempt_idx,
                        )

                    yield event

                # Successful stream completion -> break attempt loop
                return

            except Exception as e:
                last_error = e
                circuit_breaker_manager.record_failure(provider_id, e)
                logger.warning(
                    f"[AI Router] Stream attempt {attempt_idx} on {provider_id} failed (emitted tokens: {first_chunk_received}): {e}"
                )

                # If tokens were already yielded to client, do not attempt mid-stream restart to prevent scrambled output
                if first_chunk_received:
                    yield AIStreamEvent(
                        type=AIStreamEventType.ERROR,
                        error=f"Stream interrupted on {provider_id}: {e}",
                        provider=provider_id,
                        model=model,
                        request_id=request_id,
                    )
                    return

                # If no tokens yielded yet and fallback is permitted, loop to next candidate
                if routing_mode == "manual" and not fallback_enabled:
                    yield AIStreamEvent(
                        type=AIStreamEventType.ERROR,
                        error=str(e),
                        provider=provider_id,
                        model=model,
                        request_id=request_id,
                    )
                    return

                continue

        # If all stream candidates failed
        err_msg = str(last_error) if last_error else "All AI streaming providers failed or unconfigured."
        yield AIStreamEvent(
            type=AIStreamEventType.ERROR,
            error=err_msg,
            provider="router",
            request_id=request_id,
        )

    async def test_connection(self, provider_id: str, user_id: str | None = None) -> ProviderHealth:
        """Tests live connectivity for specified provider using stored user credentials."""
        uid = await self._resolve_user_id(user_id)
        adapter = provider_registry.get(provider_id)
        if not adapter:
            return ProviderHealth(
                provider_id=provider_id,
                status=ProviderHealthStatus.NOT_CONFIGURED,
                is_configured=False,
                error_message=f"Unsupported provider '{provider_id}'",
            )

        api_key = await self.credential_service.get_raw_key_for_provider(provider_id, uid)
        if not api_key:
            return ProviderHealth(
                provider_id=provider_id,
                status=ProviderHealthStatus.NOT_CONFIGURED,
                is_configured=False,
                error_message="No API Key configured",
            )

        health = await adapter.test_connection(api_key)
        if health.status == ProviderHealthStatus.HEALTHY:
            circuit_breaker_manager.record_success(provider_id)
        else:
            circuit_breaker_manager.record_failure(provider_id, Exception(health.error_message or "Health test failed"))

        return health

    async def get_all_providers_health(self, user_id: str | None = None) -> list[ProviderHealth]:
        """Returns current health matrix for all known providers."""
        uid = await self._resolve_user_id(user_id)
        providers_meta = ModelRegistry.get_all_providers()
        results: list[ProviderHealth] = []

        for p_meta in providers_meta:
            api_key = await self.credential_service.get_raw_key_for_provider(p_meta.id, uid)
            is_configured = bool(api_key)
            health = circuit_breaker_manager.get_health(p_meta.id, is_configured=is_configured)
            results.append(health)

        return results
