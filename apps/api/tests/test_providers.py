import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_providers_initially_unconfigured(client: AsyncClient):
    res = await client.get("/api/v1/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 3  # gemini, groq, openrouter
    gemini = next(p for p in providers if p["id"] == "gemini")
    assert gemini["display_name"] == "Google Gemini"
    assert len(gemini["models"]) >= 2
    assert gemini["is_configured"] is False


@pytest.mark.asyncio
async def test_create_and_delete_credential(client: AsyncClient):
    # 1. Create credential for Gemini
    create_res = await client.post(
        "/api/v1/providers/credentials",
        json={
            "provider": "gemini",
            "api_key": "AIzaSyTestApiKey1234567890",
            "is_enabled": True,
        },
    )
    assert create_res.status_code == 201
    cred = create_res.json()
    assert cred["provider"] == "gemini"
    assert cred["masked_secret"].endswith("7890")
    assert "AIzaSyTest" not in cred["masked_secret"]

    # 2. Check provider listing shows configured
    list_res = await client.get("/api/v1/providers")
    gemini = next(p for p in list_res.json() if p["id"] == "gemini")
    assert gemini["is_configured"] is True
    assert gemini["credential"] is not None

    # 3. Duplicate create should fail with 409 conflict
    dup_res = await client.post(
        "/api/v1/providers/credentials",
        json={
            "provider": "gemini",
            "api_key": "AIzaSyTestAnotherKey",
        },
    )
    assert dup_res.status_code == 409

    # 4. Update credential
    cred_id = cred["id"]
    patch_res = await client.patch(
        f"/api/v1/providers/credentials/{cred_id}",
        json={"api_key": "AIzaSyUpdatedKey9999"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["masked_secret"].endswith("9999")

    # 5. Delete credential
    del_res = await client.delete(f"/api/v1/providers/credentials/{cred_id}")
    assert del_res.status_code == 204

    # 6. Verify deleted
    verify_list = await client.get("/api/v1/providers")
    gemini_after = next(p for p in verify_list.json() if p["id"] == "gemini")
    assert gemini_after["is_configured"] is False
