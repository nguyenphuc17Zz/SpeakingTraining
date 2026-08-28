from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domains.providers.contracts import ModelMetadata


class CredentialCreate(BaseModel):
    provider: str  # 'gemini', 'groq', 'openrouter'
    api_key: str
    is_enabled: bool = True


class CredentialUpdate(BaseModel):
    api_key: str | None = None
    is_enabled: bool | None = None


class CredentialRead(BaseModel):
    id: str
    user_id: str
    provider: str
    masked_secret: str
    is_enabled: bool
    is_configured: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderDetailRead(BaseModel):
    id: str
    display_name: str
    description: str
    default_model: str
    models: list[ModelMetadata]
    is_configured: bool
    requires_api_key: bool
    documentation_url: str
    credential: CredentialRead | None = None
