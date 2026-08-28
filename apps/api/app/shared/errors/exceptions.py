from typing import Any


class AppBaseException(Exception):
    """Base exception for all application domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundException(AppBaseException):
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(message=message, code="NOT_FOUND", status_code=404, details=details)


class ValidationException(AppBaseException):
    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class ConflictException(AppBaseException):
    def __init__(self, message: str = "Resource already exists", details: dict[str, Any] | None = None):
        super().__init__(message=message, code="RESOURCE_CONFLICT", status_code=409, details=details)


class UnauthorizedException(AppBaseException):
    def __init__(self, message: str = "Unauthorized", details: dict[str, Any] | None = None):
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401, details=details)


class ProviderException(AppBaseException):
    def __init__(self, message: str = "Provider error", details: dict[str, Any] | None = None):
        super().__init__(message=message, code="PROVIDER_ERROR", status_code=502, details=details)
