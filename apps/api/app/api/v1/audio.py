import base64
import os
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audio.contracts import (
    AudioQualityReport,
    PlaybackPreset,
    ProviderHealth,
    VoiceProfileDTO,
)
from app.domains.audio.recording_service import AudioQualityAnalyzer
from app.domains.audio.schemas import (
    AudioPresetCreateRequest,
    AudioPresetResponse,
    AudioQualityCheckRequest,
    AudioSettingsDTO,
    AudioSettingsUpdateRequest,
    TTSPreviewRequest,
    TTSPreviewResponse,
    VoiceProfileCreateRequest,
    VoiceProfileResponse,
    VoiceProfileUpdateRequest,
    VoicevoxEngineDTO,
)
from app.domains.audio.service import AudioService
from app.domains.audio.tts_service import tts_service
from app.domains.audio.voice_service import VoiceService
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/audio", tags=["audio"])


# 1. Voices & Health
@router.get("/voices", response_model=list[VoiceProfileDTO])
async def list_available_voices(
    provider: str = Query(default="voicevox"),
    db: AsyncSession = Depends(get_db),
):
    """Lists available voices with capabilities from the specified TTS provider."""
    voice_service = VoiceService(db)
    return await voice_service.list_available_voices(provider_id=provider)


@router.get("/providers/health", response_model=list[ProviderHealth])
async def get_providers_health():
    """Checks live status, version, and latency of registered speech providers."""
    return await tts_service.get_providers_health()


# 2. Voice Preview
@router.post("/tts/preview", response_model=TTSPreviewResponse)
async def preview_voice(payload: TTSPreviewRequest):
    """Synthesizes a short preview clip with in-memory caching."""
    result = await tts_service.preview_voice(
        text=payload.text,
        voice_id=payload.voice_id,
        provider=payload.provider,
        speed=payload.speed,
        pitch=payload.pitch,
        style=payload.style,
    )
    return TTSPreviewResponse(
        audio_base64=result.audio_base64 or "",
        format=result.format,
        duration_ms=result.duration_ms,
        provider=result.provider,
        voice_id=result.voice_id,
        processing_time_ms=result.processing_time_ms,
        is_cached=result.is_cached,
    )


# 3. Voice Profiles (CRUD)
@router.get("/voice-profiles", response_model=list[VoiceProfileResponse])
async def list_user_voice_profiles(db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    profiles = await service.list_user_voice_profiles(user.id)
    return [
        VoiceProfileResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            provider=p.provider,
            voice_id=p.voice_id,
            description=p.description,
            settings_json=p.settings_json or {},
            is_default=p.is_default,
            is_favorite=p.is_favorite,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in profiles
    ]


@router.post("/voice-profiles", response_model=VoiceProfileResponse)
async def create_voice_profile(
    payload: VoiceProfileCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    p = await service.create_voice_profile(user.id, payload)
    return VoiceProfileResponse(
        id=p.id,
        user_id=p.user_id,
        name=p.name,
        provider=p.provider,
        voice_id=p.voice_id,
        description=p.description,
        settings_json=p.settings_json or {},
        is_default=p.is_default,
        is_favorite=p.is_favorite,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.patch("/voice-profiles/{profile_id}", response_model=VoiceProfileResponse)
async def update_voice_profile(
    profile_id: str,
    payload: VoiceProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    p = await service.update_voice_profile(profile_id, user.id, payload)
    if not p:
        raise HTTPException(status_code=404, detail="Voice profile not found.")
    return VoiceProfileResponse(
        id=p.id,
        user_id=p.user_id,
        name=p.name,
        provider=p.provider,
        voice_id=p.voice_id,
        description=p.description,
        settings_json=p.settings_json or {},
        is_default=p.is_default,
        is_favorite=p.is_favorite,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


@router.delete("/voice-profiles/{profile_id}")
async def delete_voice_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    deleted = await service.delete_voice_profile(profile_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Voice profile not found.")
    return {"success": True}


# 4. Playback Presets
@router.get("/presets", response_model=list[PlaybackPreset])
async def list_presets(db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    return await service.list_presets(user.id)


@router.post("/presets", response_model=AudioPresetResponse)
async def create_preset(
    payload: AudioPresetCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    m = await service.create_preset(user.id, payload)
    return AudioPresetResponse(
        id=m.id,
        user_id=m.user_id,
        name=m.name,
        description=m.description,
        speed=m.speed,
        volume=m.volume,
        loop_count=m.loop_count,
        pause_after_ms=m.pause_after_ms,
        auto_play=m.auto_play,
        record_after=m.record_after,
        is_system=m.is_system,
        created_at=m.created_at.isoformat(),
    )


# 5. Microphone Calibration & Audio Quality Check
@router.post("/quality-check", response_model=AudioQualityReport)
async def check_audio_quality(payload: AudioQualityCheckRequest):
    """Analyzes audio recording for volume, noise floor, and clipping distortion."""
    try:
        raw_bytes = base64.b64decode(payload.audio_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 audio data.")
    return AudioQualityAnalyzer.analyze(raw_bytes)


# 6. Audio Settings
@router.get("/settings", response_model=AudioSettingsDTO)
async def get_audio_settings(db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    return await service.get_audio_settings(user.id)


@router.patch("/settings", response_model=AudioSettingsDTO)
async def update_audio_settings(
    payload: AudioSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    return await service.update_audio_settings(user.id, payload)


# 7. Diagnostics
@router.get("/diagnostics")
async def get_audio_diagnostics(db: AsyncSession = Depends(get_db)):
    service = AudioService(db)
    return await service.get_audio_diagnostics()


# 8. VOICEVOX Engine Path & URL (user-editable, default E:\VoiceVox)
class VoicevoxEngineUpdateRequest(BaseModel):
    path: str | None = None
    url: str | None = None

def _build_engine_dto(path: str, url: str, health: dict | None = None) -> VoicevoxEngineDTO:
    run_candidates = [
        os.path.join(path, "windows-nvidia", "run.exe"),
        os.path.join(path, "run.exe"),
        os.path.join(path, "voicevox_engine", "run.exe"),
    ]
    run_exe = next((p for p in run_candidates if os.path.exists(p)), run_candidates[0])
    return VoicevoxEngineDTO(
        url=url,
        path=path,
        path_exists=os.path.exists(path),
        run_exe_path=run_exe,
        run_exe_exists=os.path.exists(run_exe),
        is_available=bool(health and health.get("is_available")),
        status_message=health.get("status_message", "Unknown") if health else "Chưa kiểm tra",
        latency_ms=health.get("latency_ms") if health else None,
        available_voices_count=health.get("available_voices_count", 0) if health else 0,
    )

@router.get("/engine", response_model=VoicevoxEngineDTO)
async def get_voicevox_engine(db: AsyncSession = Depends(get_db)):
    from app.domains.speech.adapters.voicevox import VoicevoxAdapter
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    settings = await service.get_audio_settings(user.id)
    # Use user's URL for health check
    adapter = VoicevoxAdapter(engine_url=settings.voicevox_engine_url)
    health = await adapter.health_check()
    return _build_engine_dto(settings.voicevox_engine_path, settings.voicevox_engine_url, health)

@router.put("/engine", response_model=VoicevoxEngineDTO)
async def update_voicevox_engine(payload: VoicevoxEngineUpdateRequest, db: AsyncSession = Depends(get_db)):
    from app.domains.speech.adapters.voicevox import VoicevoxAdapter
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    # Update via AudioService (which proxies to UserSettings)
    update_data = {}
    if payload.path is not None:
        # Basic validation: must be absolute path like E:\...
        p = payload.path.strip()
        if not p:
            raise HTTPException(status_code=400, detail="Đường dẫn không được để trống")
        update_data["voicevox_engine_path"] = p
    if payload.url is not None:
        u = payload.url.strip()
        if not (u.startswith("http://") or u.startswith("https://")):
            raise HTTPException(status_code=400, detail="URL phải bắt đầu bằng http:// hoặc https://")
        update_data["voicevox_engine_url"] = u
    if update_data:
        await service.update_audio_settings(user.id, AudioSettingsUpdateRequest(**update_data))
    settings = await service.get_audio_settings(user.id)
    adapter = VoicevoxAdapter(engine_url=settings.voicevox_engine_url)
    health = await adapter.health_check()
    return _build_engine_dto(settings.voicevox_engine_path, settings.voicevox_engine_url, health)


@router.post("/engine/start", response_model=VoicevoxEngineDTO)
async def start_voicevox_engine(db: AsyncSession = Depends(get_db)):
    """Attempts to automatically launch VOICEVOX run.exe process in the background."""
    import asyncio
    import subprocess
    import sys
    from app.domains.speech.adapters.voicevox import VoicevoxAdapter

    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    service = AudioService(db)
    settings = await service.get_audio_settings(user.id)

    adapter = VoicevoxAdapter(engine_url=settings.voicevox_engine_url)
    health = await adapter.health_check()

    if health.get("is_available"):
        return _build_engine_dto(settings.voicevox_engine_path, settings.voicevox_engine_url, health)

    run_candidates = [
        os.path.join(settings.voicevox_engine_path, "windows-nvidia", "run.exe"),
        os.path.join(settings.voicevox_engine_path, "run.exe"),
        os.path.join(settings.voicevox_engine_path, "voicevox_engine", "run.exe"),
    ]
    run_exe = next((p for p in run_candidates if os.path.exists(p)), None)

    if not run_exe:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy file run.exe trong thư mục: {settings.voicevox_engine_path}",
        )

    try:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        flags = 0
        if sys.platform == "win32":
            flags = subprocess.CREATE_NO_WINDOW | getattr(subprocess, "DETACHED_PROCESS", 0x00000008)

        subprocess.Popen(
            [run_exe, "--host", "127.0.0.1", "--port", "50021"],
            cwd=os.path.dirname(run_exe),
            env=env,
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Poll for readiness
        for _ in range(12):
            await asyncio.sleep(0.5)
            health = await adapter.health_check()
            if health.get("is_available"):
                break
    except Exception as e:
        logger.error(f"[VOICEVOX] Failed to launch run.exe: {e}")
        raise HTTPException(status_code=500, detail=f"Không thể khởi động run.exe: {e}")

    return _build_engine_dto(settings.voicevox_engine_path, settings.voicevox_engine_url, health)

