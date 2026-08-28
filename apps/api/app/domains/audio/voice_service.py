from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.audio.contracts import VoiceCapability, VoiceProfileDTO
from app.domains.audio.models import VoiceProfileModel
from app.domains.personas.models import Persona
from app.domains.speech.tts_router import tts_router


class VoiceService:
    """
    Central Voice Management service for resolving persona voice mappings,
    custom voice profiles, and provider voice capabilities.
    """

    def __init__(self, session: AsyncSession | None = None):
        self.session = session

    async def list_available_voices(self, provider_id: str = "voicevox") -> list[VoiceProfileDTO]:
        """Lists voices from TTS provider formatted as VoiceProfileDTOs."""
        try:
            voices = await tts_router.get_available_voices(provider_id)
            profiles: list[VoiceProfileDTO] = []
            for v in voices:
                caps = [VoiceCapability.SPEED_CONTROL, VoiceCapability.PITCH_CONTROL, VoiceCapability.VOLUME_CONTROL]
                profiles.append(
                    VoiceProfileDTO(
                        id=f"{provider_id}:{v.id}",
                        provider=provider_id,
                        voice_id=v.id,
                        name=v.name,
                        display_name=v.name,
                        language="ja",
                        gender=v.gender if v.gender in ["female", "male"] else None,
                        default_speed=1.0,
                        default_pitch=0.0,
                        style=v.style or "normal",
                        capabilities=caps,
                        provider_metadata={"speaker_id": v.speaker_id},
                        is_favorite=False,
                        is_system=True,
                    )
                )
            return profiles
        except Exception as e:
            logger.warning(f"[VoiceService] Error listing voices for {provider_id}: {e}")
            return []

    async def resolve_voice_configuration(
        self,
        user_id: str | None = None,
        persona: Persona | None = None,
        session_override_provider: str | None = None,
        session_override_voice: str | None = None,
        session_override_speed: float | None = None,
        session_override_pitch: float | None = None,
    ) -> tuple[str, str, float, float]:
        """
        Deterministic hierarchy:
        1. Session explicit override
        2. Persona configured voice
        3. User default voice profile (if set)
        4. Default provider & voice fallback
        Returns: (provider_id, voice_id, speed, pitch)
        """
        # 1. Start with system defaults
        provider = "voicevox"
        voice_id = "1"
        speed = 1.0
        pitch = 0.0

        # 2. Check User default profile if session available
        if self.session and user_id:
            res = await self.session.execute(
                select(VoiceProfileModel).where(
                    VoiceProfileModel.user_id == user_id,
                    VoiceProfileModel.is_default.is_(True),
                )
            )
            user_default_profile = res.scalar_one_or_none()
            if user_default_profile:
                provider = user_default_profile.provider
                voice_id = user_default_profile.voice_id
                settings = user_default_profile.settings_json or {}
                speed = float(settings.get("speed", 1.0))
                pitch = float(settings.get("pitch", 0.0))

        # 3. Persona configured settings
        if persona:
            if getattr(persona, "tts_voice_id", None):
                voice_id = str(persona.tts_voice_id)
            if getattr(persona, "tts_speed", None) is not None:
                speed = float(persona.tts_speed)
            if getattr(persona, "tts_pitch", None) is not None:
                pitch = float(persona.tts_pitch)

        # 4. Session explicit overrides (highest priority)
        if session_override_provider:
            provider = session_override_provider
        if session_override_voice:
            voice_id = session_override_voice
        if session_override_speed is not None:
            speed = session_override_speed
        if session_override_pitch is not None:
            pitch = session_override_pitch

        return provider, voice_id, speed, pitch
