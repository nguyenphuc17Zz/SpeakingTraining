from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PersonaBase(BaseModel):
    name: str
    description: str
    role: str
    personality: str
    speaking_style: str
    difficulty: str = "N3"
    avatar_url: str | None = None
    system_prompt: str | None = None


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    role: str | None = None
    personality: str | None = None
    speaking_style: str | None = None
    difficulty: str | None = None
    avatar_url: str | None = None
    system_prompt: str | None = None


class PersonaRead(PersonaBase):
    id: str
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonaGenerateRequest(BaseModel):
    theme: str | None = None
    difficulty: str | None = None
    language: str = "vi"


class PersonaGenerateResponse(PersonaCreate):
    reasoning: str | None = None


class PersonaPreferenceBase(BaseModel):
    custom_prompt_addon: str | None = None
    voice_pitch: float = 1.0
    voice_speed: float = 1.0


class PersonaPreferenceUpdate(PersonaPreferenceBase):
    pass


class PersonaPreferenceRead(PersonaPreferenceBase):
    id: str
    user_id: str
    persona_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
