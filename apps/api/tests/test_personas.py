import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_and_seed_personas(client: AsyncClient):
    res = await client.get("/api/v1/personas")
    assert res.status_code == 200
    personas = res.json()
    assert len(personas) >= 4  # System seeds

    names = [p["name"] for p in personas]
    assert any("Yuki Senpai" in n for n in names)
    assert any("Takahashi" in n for n in names)
    assert any("Ren" in n for n in names)
    assert any("Tanaka" in n for n in names)


@pytest.mark.asyncio
async def test_create_and_delete_custom_persona(client: AsyncClient):
    # 1. Create custom persona
    create_res = await client.post(
        "/api/v1/personas",
        json={
            "name": "Sakura (桜)",
            "role": "Cafe Barista in Kyoto",
            "description": "A polite barista in a traditional Kyoto kissaten who loves discussing matcha and Japanese tea ceremonies.",
            "personality": "Gentle, calm, speaks with polite Kansai flair.",
            "speaking_style": "Kyoto polite Japanese",
            "difficulty": "N3",
            "system_prompt": "You are Sakura, a barista at a quiet Kyoto tea house.",
        },
    )
    assert create_res.status_code == 201
    persona = create_res.json()
    assert persona["name"] == "Sakura (桜)"
    assert persona["is_system"] is False
    persona_id = persona["id"]

    # 2. Get by ID
    get_res = await client.get(f"/api/v1/personas/{persona_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Sakura (桜)"

    # 3. Update custom persona
    patch_res = await client.patch(
        f"/api/v1/personas/{persona_id}",
        json={"difficulty": "N2"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["difficulty"] == "N2"

    # 4. Delete custom persona
    del_res = await client.delete(f"/api/v1/personas/{persona_id}")
    assert del_res.status_code == 204

    # 5. Verify 404 after deletion
    verify_res = await client.get(f"/api/v1/personas/{persona_id}")
    assert verify_res.status_code == 404


@pytest.mark.asyncio
async def test_can_delete_system_persona_and_restore_defaults(client: AsyncClient):
    # 1. Delete system persona
    del_res = await client.delete("/api/v1/personas/persona_senpai")
    assert del_res.status_code == 204

    # 2. Verify persona_senpai is gone
    get_res = await client.get("/api/v1/personas/persona_senpai")
    assert get_res.status_code == 404

    # 3. Restore default personas
    restore_res = await client.post("/api/v1/personas/restore-defaults")
    assert restore_res.status_code == 200
    restored_list = restore_res.json()
    assert any(p["id"] == "persona_senpai" for p in restored_list)

    # 4. Verify persona_senpai is accessible again
    get_again = await client.get("/api/v1/personas/persona_senpai")
    assert get_again.status_code == 200
    assert "Yuki Senpai" in get_again.json()["name"]


@pytest.mark.asyncio
async def test_generate_persona_ai_requires_provider_or_fails_cleanly(client: AsyncClient):
    # Without configured AI provider, generate should return 422 or error instead of silent mock
    res = await client.post(
        "/api/v1/personas/generate",
        json={"difficulty": "N2", "theme": "IT Developer"},
    )
    # Since no API key is set in test env, it should fail gracefully with ValidationException / 422
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert "message" in data["error"]

