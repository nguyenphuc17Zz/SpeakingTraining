import json
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

import httpx

from app.domains.ai.adapters.base import BaseHTTPAdapter
from app.domains.ai.contracts import (
    AIMessageRole,
    AIProvider,
    AIRequest,
    AIResponse,
    AIStreamEvent,
    AIStreamEventType,
    AIUsage,
    ModelCapability,
    ModelMetadata,
    ProviderHealth,
    ProviderHealthStatus,
    ResponseFormatType,
)
from app.domains.ai.errors import (
    ProviderAuthError,
    ProviderTimeoutError,
    ProviderUnknownError,
)


class OpenRouterAdapter(BaseHTTPAdapter, AIProvider):
    """Adapter for OpenRouter gateway API."""

    provider_id: str = "openrouter"
    DEFAULT_MODEL: str = "anthropic/claude-3.5-sonnet"
    BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, timeout_seconds: float = 60.0, transport: httpx.AsyncBaseTransport | None = None):
        super().__init__(provider_id="openrouter", timeout_seconds=timeout_seconds)
        self._transport = transport

    def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
            follow_redirects=True,
            transport=self._transport,
        )

    def _build_payload(self, request: AIRequest, stream: bool = False) -> dict[str, Any]:
        messages: list[dict[str, str]] = []

        if request.system_instruction:
            messages.append({"role": "system", "content": request.system_instruction})

        for msg in request.messages:
            role = msg.role.value if isinstance(msg.role, AIMessageRole) else str(msg.role)
            messages.append({"role": role, "content": msg.content})

        if not messages:
            messages = [{"role": "user", "content": "Hello"}]

        payload: dict[str, Any] = {
            "model": request.model or self.DEFAULT_MODEL,
            "messages": messages,
            "temperature": request.temperature,
            "stream": stream,
        }

        if request.max_output_tokens:
            payload["max_tokens"] = request.max_output_tokens

        if request.response_format and request.response_format.type in (
            ResponseFormatType.JSON_OBJECT,
            ResponseFormatType.JSON_SCHEMA,
        ):
            payload["response_format"] = {"type": "json_object"}

        return payload

    def _extract_usage(self, data: dict[str, Any]) -> AIUsage:
        usage = data.get("usage", {})
        return AIUsage(
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )

    async def generate(self, request: AIRequest, api_key: str) -> AIResponse:
        if not api_key:
            raise ProviderAuthError("OpenRouter API key is required", provider_id=self.provider_id)

        model = request.model or self.DEFAULT_MODEL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://speaking-training.local",
            "X-Title": "Japanese Speaking Training OS",
        }
        payload = self._build_payload(request, stream=False)

        start_time = time.perf_counter()
        async with self._build_client() as client:
            try:
                response = await client.post(self.BASE_URL, headers=headers, json=payload)
            except httpx.TimeoutException as te:
                raise ProviderTimeoutError(f"OpenRouter request timed out after {self.timeout_seconds}s", provider_id=self.provider_id, raw_error=te)
            except httpx.RequestError as re:
                raise ProviderUnknownError(f"Network error connecting to OpenRouter: {re}", provider_id=self.provider_id, raw_error=re)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if response.status_code != 200:
            try:
                err_data = response.json()
            except Exception:
                err_data = response.text
            self._handle_http_error(response.status_code, err_data, default_msg=f"OpenRouter API returned status {response.status_code}")

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return AIResponse(
                text="",
                model=model,
                provider=self.provider_id,
                usage=self._extract_usage(data),
                finish_reason="empty",
                latency_ms=latency_ms,
            )

        choice = choices[0]
        text = choice.get("message", {}).get("content", "")
        finish_reason = choice.get("finish_reason", "stop")

        return AIResponse(
            text=text,
            model=model,
            provider=self.provider_id,
            usage=self._extract_usage(data),
            finish_reason=finish_reason,
            latency_ms=latency_ms,
        )

    async def stream(self, request: AIRequest, api_key: str) -> AsyncIterator[AIStreamEvent]:
        if not api_key:
            raise ProviderAuthError("OpenRouter API key is required", provider_id=self.provider_id)

        model = request.model or self.DEFAULT_MODEL
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = self._build_payload(request, stream=True)

        yield AIStreamEvent(
            type=AIStreamEventType.STARTED,
            provider=self.provider_id,
            model=model,
        )

        start_time = time.perf_counter()
        final_usage = AIUsage()

        try:
            async with self._build_client() as client:
                async with client.stream("POST", self.BASE_URL, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        try:
                            err_data = json.loads(err_bytes.decode())
                        except Exception:
                            err_data = err_bytes.decode()
                        self._handle_http_error(response.status_code, err_data, default_msg=f"OpenRouter streaming failed with status {response.status_code}")

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            json_str = line[6:].strip()
                            if not json_str or json_str == "[DONE]":
                                continue
                            try:
                                chunk_data = json.loads(json_str)
                            except Exception:
                                continue

                            choices = chunk_data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                t = delta.get("content", "")
                                if t:
                                    yield AIStreamEvent(
                                        type=AIStreamEventType.TEXT_DELTA,
                                        text_delta=t,
                                        provider=self.provider_id,
                                        model=model,
                                    )

                            if chunk_data.get("usage"):
                                final_usage = self._extract_usage(chunk_data)

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            if final_usage.total_tokens:
                yield AIStreamEvent(
                    type=AIStreamEventType.USAGE,
                    usage=final_usage,
                    provider=self.provider_id,
                    model=model,
                )

            yield AIStreamEvent(
                type=AIStreamEventType.COMPLETED,
                provider=self.provider_id,
                model=model,
                finish_reason="stop",
                latency_ms=latency_ms,
                usage=final_usage,
            )

        except Exception as e:
            if isinstance(e, (ProviderAuthError, ProviderTimeoutError)):
                raise e
            yield AIStreamEvent(
                type=AIStreamEventType.ERROR,
                error=str(e),
                provider=self.provider_id,
                model=model,
            )

    async def list_models(self, api_key: str) -> list[ModelMetadata]:
        """Dynamically fetch all available models from OpenRouter API."""
        url = "https://openrouter.ai/api/v1/models"
        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with self._build_client() as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return self._fallback_models()
                data = response.json()
        except Exception:
            return self._fallback_models()

        raw_models = data.get("data", [])
        result: list[ModelMetadata] = []

        for m in raw_models:
            model_id = m.get("id", "").strip()
            if not model_id:
                continue

            display_name = m.get("name") or model_id
            context_window = m.get("context_length") or 128000

            caps = [
                ModelCapability.TEXT,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            ]
            lower_id = model_id.lower()
            if "claude" in lower_id or "gpt-4" in lower_id or "gemini" in lower_id or "vision" in lower_id:
                caps.append(ModelCapability.VISION)
            if "r1" in lower_id or "o1" in lower_id or "o3" in lower_id or "sonnet" in lower_id:
                caps.append(ModelCapability.REASONING)

            is_rec = any(rec in lower_id for rec in ("claude-3.5-sonnet", "deepseek-chat", "llama-3.3-70b"))

            result.append(
                ModelMetadata(
                    id=model_id,
                    provider_id=self.provider_id,
                    display_name=display_name,
                    context_window=context_window,
                    capabilities=list(set(caps)),
                    is_recommended=is_rec,
                    is_enabled=True,
                )
            )

        return result if result else self._fallback_models()

    def _fallback_models(self) -> list[ModelMetadata]:
        return [
            ModelMetadata(
                id="anthropic/claude-3.5-sonnet",
                provider_id=self.provider_id,
                display_name="Claude 3.5 Sonnet",
                context_window=200000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.REASONING,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=True,
            ),
            ModelMetadata(
                id="deepseek/deepseek-chat",
                provider_id=self.provider_id,
                display_name="DeepSeek V3",
                context_window=64000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=True,
            ),
            ModelMetadata(
                id="meta-llama/llama-3.3-70b-instruct",
                provider_id=self.provider_id,
                display_name="Llama 3.3 70B Instruct",
                context_window=128000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=False,
            ),
        ]

    async def test_connection(self, api_key: str) -> ProviderHealth:
        if not api_key:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderHealthStatus.NOT_CONFIGURED,
                is_configured=False,
                error_message="No API Key configured",
            )

        start_time = time.perf_counter()
        req = AIRequest(
            messages=[{"role": AIMessageRole.USER, "content": "Ping test: Reply with 'OK'"}],
            max_output_tokens=5,
            temperature=0.0,
        )
        try:
            resp = await self.generate(req, api_key)
            latency = int((time.perf_counter() - start_time) * 1000)
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderHealthStatus.HEALTHY,
                is_configured=True,
                latency_ms=latency,
                last_checked_at=datetime.now(timezone.utc),
                metadata={"reply": resp.text[:20]},
            )
        except Exception as e:
            latency = int((time.perf_counter() - start_time) * 1000)
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderHealthStatus.UNAVAILABLE,
                is_configured=True,
                latency_ms=latency,
                last_checked_at=datetime.now(timezone.utc),
                error_message=str(e),
            )
