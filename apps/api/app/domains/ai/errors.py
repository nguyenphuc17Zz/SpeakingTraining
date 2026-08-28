from typing import Any


class AIProviderError(Exception):
    """Base exception for all AI provider interactions."""

    def __init__(
        self,
        message: str,
        provider_id: str,
        status_code: int | None = None,
        is_retryable: bool = False,
        raw_error: Any | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.provider_id = provider_id
        self.status_code = status_code
        self.is_retryable = is_retryable
        self.raw_error = raw_error

    def __str__(self) -> str:
        return f"[{self.provider_id.upper()}] {self.message} (status: {self.status_code}, retryable: {self.is_retryable})"


class ProviderAuthError(AIProviderError):
    """Raised when provider API key is invalid, missing, or lacks permissions."""

    def __init__(self, message: str, provider_id: str, raw_error: Any | None = None):
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=401,
            is_retryable=False,
            raw_error=raw_error,
        )


class ProviderRateLimitError(AIProviderError):
    """Raised when provider returns HTTP 429 (RPM / TPM exceeded)."""

    def __init__(self, message: str, provider_id: str, retry_after_seconds: float | None = None, raw_error: Any | None = None):
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=429,
            is_retryable=True,
            raw_error=raw_error,
        )
        self.retry_after_seconds = retry_after_seconds


class ProviderQuotaError(AIProviderError):
    """Raised when account balance or monthly billing quota is exhausted."""

    def __init__(self, message: str, provider_id: str, raw_error: Any | None = None):
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=402,
            is_retryable=True,  # Retryable via fallback to another provider
            raw_error=raw_error,
        )


class ProviderTimeoutError(AIProviderError):
    """Raised when an API request times out."""

    def __init__(self, message: str, provider_id: str, raw_error: Any | None = None):
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=408,
            is_retryable=True,
            raw_error=raw_error,
        )


class ProviderUnavailableError(AIProviderError):
    """Raised when the provider service is temporarily unavailable (HTTP 500, 502, 503, 504)."""

    def __init__(self, message: str, provider_id: str, status_code: int = 503, raw_error: Any | None = None):
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=status_code,
            is_retryable=True,
            raw_error=raw_error,
        )


class ProviderInvalidRequestError(AIProviderError):
    """Raised when the request parameters are invalid or malformed."""

    def __init__(self, message: str, provider_id: str, raw_error: Any | None = None):
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=400,
            is_retryable=False,
            raw_error=raw_error,
        )


class ProviderModelUnavailableError(AIProviderError):
    """Raised when the requested model does not exist or is deprecated on this provider."""

    def __init__(self, message: str, provider_id: str, model_id: str, raw_error: Any | None = None):
        super().__init__(
            message=f"Model '{model_id}' unavailable on {provider_id}: {message}",
            provider_id=provider_id,
            status_code=404,
            is_retryable=False,
            raw_error=raw_error,
        )
        self.model_id = model_id


class ProviderUnknownError(AIProviderError):
    """Fallback error for unclassified provider errors."""

    def __init__(self, message: str, provider_id: str, raw_error: Any | None = None):
        super().__init__(
            message=message,
            provider_id=provider_id,
            status_code=500,
            is_retryable=False,
            raw_error=raw_error,
        )
