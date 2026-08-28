import base64
import io
import wave
import numpy as np
import pytest
from httpx import AsyncClient


def generate_dummy_wav() -> str:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        samples = (0.2 * np.sin(np.linspace(0, 100, 16000)) * 32767.0).astype(np.int16)
        wf.writeframes(samples.tobytes())
    return base64.b64encode(buf.getvalue()).decode("ascii")


@pytest.mark.asyncio
async def test_audio_voices_and_health_endpoints(client: AsyncClient):
    # 1. Voices
    resp = await client.get("/api/v1/audio/voices?provider=voicevox")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "capabilities" in data[0]

    # 2. Providers health
    health_resp = await client.get("/api/v1/audio/providers/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert isinstance(health_data, list)
    assert len(health_data) >= 1
    assert health_data[0]["provider_id"] == "voicevox"


@pytest.mark.asyncio
async def test_audio_voice_profiles_crud(client: AsyncClient):
    # 1. Create Profile
    create_payload = {
        "name": "Senpai Friendly",
        "provider": "voicevox",
        "voice_id": "2",
        "description": "Zundamon friendly tone",
        "settings_json": {"speed": 0.95, "pitch": 0.0},
        "is_default": True,
        "is_favorite": True,
    }
    res = await client.post("/api/v1/audio/voice-profiles", json=create_payload)
    assert res.status_code == 200
    profile = res.json()
    assert profile["name"] == "Senpai Friendly"
    assert profile["is_default"] is True
    profile_id = profile["id"]

    # 2. List Profiles
    list_res = await client.get("/api/v1/audio/voice-profiles")
    assert list_res.status_code == 200
    profiles = list_res.json()
    assert any(p["id"] == profile_id for p in profiles)

    # 3. Patch Profile
    patch_res = await client.patch(
        f"/api/v1/audio/voice-profiles/{profile_id}",
        json={"name": "Senpai Super Friendly"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Senpai Super Friendly"

    # 4. Delete Profile
    del_res = await client.delete(f"/api/v1/audio/voice-profiles/{profile_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


@pytest.mark.asyncio
async def test_audio_presets_and_quality_check(client: AsyncClient):
    # 1. Presets list (system presets)
    res = await client.get("/api/v1/audio/presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 4
    assert any(p["name"] == "Japanese Natural" for p in presets)

    # 2. Create custom preset
    create_p_res = await client.post(
        "/api/v1/audio/presets",
        json={
            "name": "My Intensive Shadowing",
            "speed": 0.88,
            "volume": 0.9,
            "loop_count": 5,
            "pause_after_ms": 600,
        },
    )
    assert create_p_res.status_code == 200
    assert create_p_res.json()["loop_count"] == 5

    # 3. Quality Check
    dummy_b64 = generate_dummy_wav()
    qc_res = await client.post("/api/v1/audio/quality-check", json={"audio_base64": dummy_b64})
    assert qc_res.status_code == 200
    qc_data = qc_res.json()
    assert "quality" in qc_data
    assert "volume_db" in qc_data
    assert "has_clipping" in qc_data

    # 4. Settings
    set_res = await client.get("/api/v1/audio/settings")
    assert set_res.status_code == 200
    assert "default_tts_provider" in set_res.json()

    # 5. Diagnostics
    diag_res = await client.get("/api/v1/audio/diagnostics")
    assert diag_res.status_code == 200
    assert "tts_providers" in diag_res.json()
    assert "cache" in diag_res.json()

