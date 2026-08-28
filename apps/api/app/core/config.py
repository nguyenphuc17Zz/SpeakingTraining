import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Japanese Speaking AI Training OS"
    DEBUG: bool = True

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = "sqlite+aiosqlite:///./speaking_training.db"
    DATABASE_SYNC_URL: str = "sqlite:///./speaking_training.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    ENCRYPTION_KEY: str = "dGhpc19pc19hXzMyX2J5dGVfZmZXcm5ldF9rZXkxMjM0NTY="

    # Speech Configuration (Phase 3)
    VOICEVOX_ENGINE_URL: str = "http://127.0.0.1:50021"
    VOICEVOX_ENGINE_PATH: str = "E:\\VoiceVox"
    WHISPER_DEFAULT_MODEL: str = "base"
    WHISPER_DEVICE: str = "auto"
    WHISPER_COMPUTE_TYPE: str = "auto"

    NEXT_PUBLIC_API_URL: str = "http://localhost:8000/api/v1"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
