"""Centralized security input limits and validation guards."""

from app.shared.errors.exceptions import ValidationException

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB maximum audio payload
MAX_TEXT_INPUT_CHARS = 4000         # 4,000 characters maximum user text input
MAX_PROMPT_CHARS = 4000             # 4,000 characters maximum prompt length
MAX_VIDEO_DURATION_SECONDS = 3600   # 1 hour maximum YouTube shadowing video


def validate_audio_payload(audio_bytes: bytes) -> None:
    if not audio_bytes:
        raise ValidationException("Audio payload cannot be empty.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValidationException(
            f"Audio payload size ({len(audio_bytes)} bytes) exceeds maximum limit of {MAX_AUDIO_BYTES} bytes (10MB)."
        )


def validate_text_input(text: str, field_name: str = "text") -> str:
    if not text:
        raise ValidationException(f"{field_name} cannot be empty.")
    cleaned = text.strip()
    if len(cleaned) > MAX_TEXT_INPUT_CHARS:
        raise ValidationException(
            f"{field_name} length ({len(cleaned)} chars) exceeds maximum allowed {MAX_TEXT_INPUT_CHARS} characters."
        )
    return cleaned
