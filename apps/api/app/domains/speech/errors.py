from typing import Any

from app.shared.errors.exceptions import AppBaseException


class SpeechError(AppBaseException):
    """Base error for speech processing subsystem."""

    def __init__(self, message: str, provider_id: str, status_code: int = 500, raw_error: Any = None):
        super().__init__(
            message=message,
            code=f"SPEECH_ERROR_{provider_id.upper()}",
            status_code=status_code,
            details={"provider_id": provider_id, "raw_error": str(raw_error) if raw_error else None},
        )
        self.provider_id = provider_id
        self.raw_error = raw_error


class STTProviderError(SpeechError):
    """Speech-to-Text inference or execution failure."""

    def __init__(self, message: str, provider_id: str, raw_error: Any = None):
        super().__init__(message=message, provider_id=provider_id, status_code=502, raw_error=raw_error)


class STTUnavailableError(SpeechError):
    """Speech-to-Text provider or model offline/unavailable."""

    def __init__(self, message: str, provider_id: str, raw_error: Any = None):
        super().__init__(message=message, provider_id=provider_id, status_code=503, raw_error=raw_error)


class TTSProviderError(SpeechError):
    """Text-to-Speech synthesis failure."""

    def __init__(self, message: str, provider_id: str, raw_error: Any = None):
        super().__init__(message=message, provider_id=provider_id, status_code=502, raw_error=raw_error)


class TTSUnavailableError(SpeechError):
    """Text-to-Speech engine unreachable or offline (e.g. VOICEVOX offline)."""

    def __init__(self, message: str, provider_id: str, raw_error: Any = None):
        super().__init__(message=message, provider_id=provider_id, status_code=503, raw_error=raw_error)
