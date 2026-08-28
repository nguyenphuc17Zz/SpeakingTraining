import uuid
from typing import Any
from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.audio.cache import tts_cache
from app.domains.audio.contracts import PlaybackPreset, ProviderHealth
from app.domains.audio.models import AudioPresetModel, VoiceProfileModel
from app.domains.audio.schemas import (
    AudioPresetCreateRequest,
    AudioSettingsDTO,
    AudioSettingsUpdateRequest,
    VoiceProfileCreateRequest,
    VoiceProfileUpdateRequest,
)
from app.domains.audio.tts_service import tts_service
from app.domains.settings.models import UserSettings
from app.domains.settings.service import SettingsService
from app.domains.speech.stt_router import stt_router


SYSTEM_PRESETS = [
    PlaybackPreset(
        id="preset_natural",
        name="Japanese Natural",
        description="Tốc độ tự nhiên 1.0x của người bản xứ.",
        speed=1.0,
        volume=1.0,
        loop=False,
        loop_count=1,
        pause_after_ms=0,
        auto_play=True,
        record_after=False,
        is_system=True,
    ),
    PlaybackPreset(
        id="preset_slow",
        name="Learner Slow",
        description="Tốc độ chậm 0.85x hỗ trợ người mới nghe rõ từng âm.",
        speed=0.85,
        volume=1.0,
        loop=False,
        loop_count=1,
        pause_after_ms=400,
        auto_play=True,
        record_after=False,
        is_system=True,
    ),
    PlaybackPreset(
        id="preset_shadowing",
        name="Shadowing Focus",
        description="Tốc độ 0.9x với lặp lại 3 lần và nghỉ 800ms giữa các lần.",
        speed=0.9,
        volume=1.0,
        loop=True,
        loop_count=3,
        pause_after_ms=800,
        auto_play=True,
        record_after=False,
        is_system=True,
    ),
    PlaybackPreset(
        id="preset_pronunciation",
        name="Pronunciation Practice",
        description="Nghe câu mẫu và tự động kích hoạt ghi âm thu giọng người học.",
        speed=1.0,
        volume=1.0,
        loop=False,
        loop_count=1,
        pause_after_ms=500,
        auto_play=False,
        record_after=True,
        is_system=True,
    ),
    PlaybackPreset(
        id="preset_fast",
        name="Fast Challenge",
        description="Thử thách phản xạ với tốc độ nói nhanh 1.1x - 1.25x.",
        speed=1.1,
        volume=1.0,
        loop=False,
        loop_count=1,
        pause_after_ms=0,
        auto_play=True,
        record_after=False,
        is_system=True,
    ),
]


class AudioService:
    """
    Primary domain service managing user voice profiles, custom audio presets,
    audio settings, and system-wide audio diagnostics.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings_service = SettingsService(session)

    # 1. Voice Profiles CRUD
    async def list_user_voice_profiles(self, user_id: str) -> list[VoiceProfileModel]:
        res = await self.session.execute(
            select(VoiceProfileModel)
            .where(VoiceProfileModel.user_id == user_id)
            .order_by(VoiceProfileModel.is_favorite.desc(), VoiceProfileModel.created_at.desc())
        )
        return list(res.scalars().all())

    async def create_voice_profile(
        self, user_id: str, payload: VoiceProfileCreateRequest
    ) -> VoiceProfileModel:
        if payload.is_default:
            # Unset existing defaults
            existing = await self.list_user_voice_profiles(user_id)
            for p in existing:
                if p.is_default:
                    p.is_default = False

        profile = VoiceProfileModel(
            user_id=user_id,
            name=payload.name,
            provider=payload.provider,
            voice_id=payload.voice_id,
            description=payload.description,
            settings_json=payload.settings_json or {},
            is_default=payload.is_default,
            is_favorite=payload.is_favorite,
        )
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def update_voice_profile(
        self, profile_id: str, user_id: str, payload: VoiceProfileUpdateRequest
    ) -> VoiceProfileModel | None:
        res = await self.session.execute(
            select(VoiceProfileModel).where(
                VoiceProfileModel.id == profile_id,
                VoiceProfileModel.user_id == user_id,
            )
        )
        profile = res.scalar_one_or_none()
        if not profile:
            return None

        if payload.is_default:
            existing = await self.list_user_voice_profiles(user_id)
            for p in existing:
                if p.id != profile_id and p.is_default:
                    p.is_default = False

        update_dict = payload.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            if v is not None:
                setattr(profile, k, v)

        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def delete_voice_profile(self, profile_id: str, user_id: str) -> bool:
        res = await self.session.execute(
            delete(VoiceProfileModel).where(
                VoiceProfileModel.id == profile_id,
                VoiceProfileModel.user_id == user_id,
            )
        )
        await self.session.commit()
        return (res.rowcount or 0) > 0

    # 2. Playback Presets
    async def list_presets(self, user_id: str | None = None) -> list[PlaybackPreset]:
        presets = list(SYSTEM_PRESETS)
        if user_id:
            res = await self.session.execute(
                select(AudioPresetModel).where(AudioPresetModel.user_id == user_id)
            )
            for m in res.scalars().all():
                presets.append(
                    PlaybackPreset(
                        id=m.id,
                        name=m.name,
                        description=m.description,
                        speed=m.speed,
                        volume=m.volume,
                        loop=m.loop_count > 1,
                        loop_count=m.loop_count,
                        pause_after_ms=m.pause_after_ms,
                        auto_play=m.auto_play,
                        record_after=m.record_after,
                        is_system=False,
                    )
                )
        return presets

    async def create_preset(
        self, user_id: str, payload: AudioPresetCreateRequest
    ) -> AudioPresetModel:
        preset = AudioPresetModel(
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            speed=payload.speed,
            volume=payload.volume,
            loop_count=payload.loop_count,
            pause_after_ms=payload.pause_after_ms,
            auto_play=payload.auto_play,
            record_after=payload.record_after,
            is_system=False,
        )
        self.session.add(preset)
        await self.session.commit()
        await self.session.refresh(preset)
        return preset

    # 3. Audio Settings
    async def get_audio_settings(self, user_id: str) -> AudioSettingsDTO:
        user_settings = await self.settings_service.get_or_create_settings(user_id)
        # Backfill for existing rows created before voicevox columns
        if not getattr(user_settings, "voicevox_engine_path", None):
            user_settings.voicevox_engine_path = "E:\\VoiceVox"
        if not getattr(user_settings, "voicevox_engine_url", None):
            user_settings.voicevox_engine_url = "http://127.0.0.1:50021"
        return AudioSettingsDTO(
            default_tts_provider=getattr(user_settings, "default_tts_provider", "voicevox"),
            default_stt_provider=getattr(user_settings, "default_stt_provider", "faster_whisper"),
            default_voice_profile_id=getattr(user_settings, "default_voice_profile_id", None),
            default_tts_speed=getattr(user_settings, "default_tts_speed", 1.0),
            default_tts_pitch=getattr(user_settings, "default_tts_pitch", 0.0),
            tts_fallback_enabled=getattr(user_settings, "tts_fallback_enabled", True),
            tts_fallback_provider=getattr(user_settings, "tts_fallback_provider", "voicevox"),
            tts_fallback_voice_id=getattr(user_settings, "tts_fallback_voice_id", "1"),
            auto_play_ai_response=getattr(user_settings, "auto_play_ai_response", True),
            auto_play_references=getattr(user_settings, "auto_play_references", True),
            voicevox_engine_url=getattr(user_settings, "voicevox_engine_url", "http://127.0.0.1:50021"),
            voicevox_engine_path=getattr(user_settings, "voicevox_engine_path", "E:\\VoiceVox"),
        )

    async def update_audio_settings(
        self, user_id: str, payload: AudioSettingsUpdateRequest
    ) -> AudioSettingsDTO:
        user_settings = await self.settings_service.get_or_create_settings(user_id)
        for k, v in payload.model_dump(exclude_unset=True).items():
            if hasattr(user_settings, k) and v is not None:
                setattr(user_settings, k, v)
        await self.session.commit()
        await self.session.refresh(user_settings)
        return await self.get_audio_settings(user_id)

    # 4. Diagnostics
    async def get_audio_diagnostics(self) -> dict[str, Any]:
        tts_health = await tts_service.get_providers_health()
        stt_models = stt_router.get_available_models()
        cache_stats = tts_cache.get_stats()

        return {
            "tts_providers": [h.model_dump() for h in tts_health],
            "stt_providers": [
                {
                    "provider_id": "faster_whisper",
                    "name": "Faster-Whisper (Local CT2/VAD)",
                    "is_available": True,
                    "available_models_count": len(stt_models),
                }
            ],
            "cache": cache_stats,
            "system_presets_count": len(SYSTEM_PRESETS),
            "status": "healthy" if any(h.is_available for h in tts_health) else "degraded",
        }
