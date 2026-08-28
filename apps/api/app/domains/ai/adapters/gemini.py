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


class GeminiAdapter(BaseHTTPAdapter, AIProvider):
    """Production adapter for Google Gemini API (v1beta REST & SSE Streaming)."""

    provider_id: str = "gemini"
    DEFAULT_MODEL: str = "gemini-1.5-flash"
    BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, timeout_seconds: float = 60.0, transport: httpx.AsyncBaseTransport | None = None):
        super().__init__(provider_id="gemini", timeout_seconds=timeout_seconds)
        self._transport = transport

    def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
            follow_redirects=True,
            transport=self._transport,
        )

    def _build_payload(self, request: AIRequest) -> dict[str, Any]:
        """Convert normalized AIRequest to Gemini API payload."""
        contents: list[dict[str, Any]] = []
        system_instructions: list[str] = []

        if request.system_instruction:
            system_instructions.append(request.system_instruction)

        for msg in request.messages:
            if msg.role == AIMessageRole.SYSTEM:
                system_instructions.append(msg.content)
            else:
                role = "user" if msg.role == AIMessageRole.USER else "model"
                parts: list[dict[str, Any]] = [{"text": msg.content}]
                contents.append({"role": role, "parts": parts})

        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Hello"}]}]

        payload: dict[str, Any] = {"contents": contents}

        if system_instructions:
            payload["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_instructions)}]
            }

        generation_config: dict[str, Any] = {
            "temperature": request.temperature,
        }
        if request.max_output_tokens:
            generation_config["maxOutputTokens"] = request.max_output_tokens

        if request.response_format:
            if request.response_format.type in (ResponseFormatType.JSON_OBJECT, ResponseFormatType.JSON_SCHEMA):
                generation_config["responseMimeType"] = "application/json"
                if request.response_format.json_schema:
                    generation_config["responseSchema"] = request.response_format.json_schema

        payload["generationConfig"] = generation_config
        return payload

    def _extract_usage(self, data: dict[str, Any]) -> AIUsage:
        usage_meta = data.get("usageMetadata", {})
        prompt_tokens = usage_meta.get("promptTokenCount")
        completion_tokens = usage_meta.get("candidatesTokenCount")
        total_tokens = usage_meta.get("totalTokenCount")
        cached_tokens = usage_meta.get("cachedContentTokenCount")

        return AIUsage(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            total_tokens=total_tokens,
            cached_tokens=cached_tokens,
        )

    def _clean_model(self, model: str | None) -> str:
        """Sanitizes model name by removing any 'models/' prefix to avoid 404s."""
        m = (model or self.DEFAULT_MODEL).strip()
        return m.removeprefix("models/")

    async def generate(self, request: AIRequest, api_key: str) -> AIResponse:
        if not api_key:
            raise ProviderAuthError("Gemini API key is required", provider_id=self.provider_id)

        clean_model = self._clean_model(request.model)
        url = f"{self.BASE_URL}/{clean_model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        payload = self._build_payload(request)

        start_time = time.perf_counter()
        async with self._build_client() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.TimeoutException as te:
                raise ProviderTimeoutError(f"Gemini request timed out after {self.timeout_seconds}s", provider_id=self.provider_id, raw_error=te)
            except httpx.RequestError as re:
                raise ProviderUnknownError(f"Network error connecting to Gemini: {re}", provider_id=self.provider_id, raw_error=re)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if response.status_code != 200:
            try:
                err_data = response.json()
            except Exception:
                err_data = response.text
            self._handle_http_error(response.status_code, err_data, default_msg=f"Gemini API returned status {response.status_code}")

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return AIResponse(
                text="",
                model=clean_model,
                provider=self.provider_id,
                usage=self._extract_usage(data),
                finish_reason="empty",
                latency_ms=latency_ms,
            )

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        text = "".join(part.get("text", "") for part in parts)
        finish_reason = candidate.get("finishReason", "stop")

        return AIResponse(
            text=text,
            model=clean_model,
            provider=self.provider_id,
            usage=self._extract_usage(data),
            finish_reason=finish_reason,
            latency_ms=latency_ms,
        )

    async def stream(self, request: AIRequest, api_key: str) -> AsyncIterator[AIStreamEvent]:
        if not api_key:
            raise ProviderAuthError("Gemini API key is required", provider_id=self.provider_id)

        clean_model = self._clean_model(request.model)
        url = f"{self.BASE_URL}/{clean_model}:streamGenerateContent?alt=sse"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        payload = self._build_payload(request)

        yield AIStreamEvent(
            type=AIStreamEventType.STARTED,
            provider=self.provider_id,
            model=clean_model,
        )

        start_time = time.perf_counter()
        final_usage = AIUsage()
        accumulated_text = []

        try:
            async with self._build_client() as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        try:
                            err_data = json.loads(err_bytes.decode())
                        except Exception:
                            err_data = err_bytes.decode()
                        self._handle_http_error(response.status_code, err_data, default_msg=f"Gemini streaming failed with status {response.status_code}")

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

                            candidates = chunk_data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    t = p.get("text", "")
                                    if t:
                                        accumulated_text.append(t)
                                        yield AIStreamEvent(
                                            type=AIStreamEventType.TEXT_DELTA,
                                            text_delta=t,
                                            provider=self.provider_id,
                                            model=clean_model,
                                        )

                            if "usageMetadata" in chunk_data:
                                final_usage = self._extract_usage(chunk_data)

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            if final_usage.total_tokens:
                yield AIStreamEvent(
                    type=AIStreamEventType.USAGE,
                    usage=final_usage,
                    provider=self.provider_id,
                    model=clean_model,
                )

            yield AIStreamEvent(
                type=AIStreamEventType.COMPLETED,
                provider=self.provider_id,
                model=clean_model,
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
                model=clean_model,
            )

    async def list_models(self, api_key: str) -> list[ModelMetadata]:
        """Dynamically fetch all available models supported by Gemini API."""
        if not api_key:
            return self._fallback_models()

        url = "https://generativelanguage.googleapis.com/v1beta/models"
        headers = {
            "x-goog-api-key": api_key,
        }

        try:
            async with self._build_client() as client:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return self._fallback_models()
                data = response.json()
        except Exception:
            return self._fallback_models()

        raw_models = data.get("models", [])
        result: list[ModelMetadata] = []

        for m in raw_models:
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" not in methods:
                continue

            raw_name = m.get("name", "")
            model_id = raw_name.removeprefix("models/").strip()
            if not model_id:
                continue

            # Infer capabilities
            caps = [
                ModelCapability.TEXT,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            ]
            lower_id = model_id.lower()
            if "flash" in lower_id or "pro" in lower_id:
                caps.extend([ModelCapability.VISION, ModelCapability.AUDIO])
            if "pro" in lower_id or "thinking" in lower_id:
                caps.append(ModelCapability.REASONING)

            is_recommended = any(rec in lower_id for rec in ("gemini-2.0-flash", "gemini-1.5-flash"))

            result.append(
                ModelMetadata(
                    id=model_id,
                    provider_id=self.provider_id,
                    display_name=m.get("displayName") or model_id,
                    context_window=m.get("inputTokenLimit") or 1000000,
                    capabilities=list(set(caps)),
                    is_recommended=is_recommended,
                    is_enabled=True,
                )
            )

        return result if result else self._fallback_models()

    def _fallback_models(self) -> list[ModelMetadata]:
        return [
            ModelMetadata(
                id="gemini-2.0-flash",
                provider_id=self.provider_id,
                display_name="Gemini 2.0 Flash (Next-Gen Fast & Realtime)",
                context_window=1048576,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.AUDIO,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=True,
            ),
            ModelMetadata(
                id="gemini-1.5-flash",
                provider_id=self.provider_id,
                display_name="Gemini 1.5 Flash (Ultra Fast)",
                context_window=1000000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.AUDIO,
                    ModelCapability.STRUCTURED_OUTPUT,
                ],
                is_recommended=True,
            ),
            ModelMetadata(
                id="gemini-1.5-pro",
                provider_id=self.provider_id,
                display_name="Gemini 1.5 Pro (Deep Reasoning & Nuance)",
                context_window=2000000,
                capabilities=[
                    ModelCapability.TEXT,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.AUDIO,
                    ModelCapability.REASONING,
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
