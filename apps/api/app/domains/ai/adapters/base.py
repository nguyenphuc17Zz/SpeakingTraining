import json
from typing import Any

import httpx

from app.domains.ai.errors import (
    ProviderAuthError,
    ProviderInvalidRequestError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ProviderUnknownError,
)


class BaseHTTPAdapter:
    """Base helper for HTTP-based AI Provider Adapters."""

    def __init__(self, provider_id: str, timeout_seconds: float = 60.0):
        self.provider_id = provider_id
        self.timeout_seconds = timeout_seconds

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
            follow_redirects=True,
        )

    def _handle_http_error(self, status_code: int, error_body: Any, default_msg: str) -> None:
        """Map HTTP error status codes and response bodies to standard AIProviderError hierarchy."""
        err_text = ""
        if isinstance(error_body, dict):
            # OpenAI / Groq format: {"error": {"message": "...", "type": "...", "code": "..."}}
            # Google Gemini format: {"error": {"code": 400, "message": "...", "status": "INVALID_ARGUMENT"}}
            err_dict = error_body.get("error", {})
            if isinstance(err_dict, dict):
                err_text = err_dict.get("message") or err_dict.get("status") or str(error_body)
            else:
                err_text = str(err_dict or error_body)
        elif isinstance(error_body, str):
            try:
                parsed = json.loads(error_body)
                if isinstance(parsed, dict) and "error" in parsed:
                    err_text = parsed["error"].get("message", error_body)
                else:
                    err_text = error_body
            except Exception:
                err_text = error_body
        else:
            err_text = str(error_body)

        msg = err_text or default_msg

        if status_code in (401, 403):
            raise ProviderAuthError(
                message=f"Authentication failed: {msg}",
                provider_id=self.provider_id,
                raw_error=error_body,
            )
        elif status_code == 429:
            # Check if it's quota or rate limit
            lower_msg = msg.lower()
            if "quota" in lower_msg or "billing" in lower_msg or "insufficient_quota" in lower_msg:
                raise ProviderQuotaError(
                    message=f"Quota exhausted: {msg}",
                    provider_id=self.provider_id,
                    raw_error=error_body,
                )
            raise ProviderRateLimitError(
                message=f"Rate limit exceeded: {msg}",
                provider_id=self.provider_id,
                raw_error=error_body,
            )
        elif status_code == 400:
            raise ProviderInvalidRequestError(
                message=f"Invalid request: {msg}",
                provider_id=self.provider_id,
                raw_error=error_body,
            )
        elif status_code in (500, 502, 503, 504):
            raise ProviderUnavailableError(
                message=f"Provider unavailable ({status_code}): {msg}",
                provider_id=self.provider_id,
                status_code=status_code,
                raw_error=error_body,
            )
        else:
            raise ProviderUnknownError(
                message=f"Error ({status_code}): {msg}",
                provider_id=self.provider_id,
                raw_error=error_body,
            )
