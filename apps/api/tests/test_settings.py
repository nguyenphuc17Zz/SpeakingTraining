import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_and_patch_settings(client: AsyncClient):
    # 1. Get initial settings
    get_res = await client.get("/api/v1/settings")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["default_ai_provider"] == "gemini"
    assert data["default_tts_provider"] == "voicevox"
    assert data["theme"] == "system"

    # 2. Patch settings
    patch_res = await client.patch(
        "/api/v1/settings",
        json={
            "theme": "dark",
            "default_ai_provider": "groq",
            "default_ai_model": "llama-3.3-70b-versatile",
        },
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["theme"] == "dark"
    assert patched_data["default_ai_provider"] == "groq"
    assert patched_data["default_ai_model"] == "llama-3.3-70b-versatile"

    # 3. Verify changes persisted
    verify_res = await client.get("/api/v1/settings")
    assert verify_res.json()["theme"] == "dark"
