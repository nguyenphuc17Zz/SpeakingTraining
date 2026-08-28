from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.domains.ai.contracts import AIResponse, AIUsage
from app.domains.ai.router import AIRouter
from app.domains.speech.contracts import STTResult, TTSAudioOutput
from app.domains.speech.stt_router import stt_router
from app.domains.speech.tts_router import tts_router


@pytest.mark.asyncio
async def test_conversation_session_lifecycle_and_turns(client: AsyncClient):
    # 1. Fetch personas to get a valid persona ID
    persona_resp = await client.get("/api/v1/personas")
    assert persona_resp.status_code == 200
    personas = persona_resp.json()
    assert len(personas) > 0
    persona_id = personas[0]["id"]

    # 2. Start a new conversation session
    start_payload = {
        "persona_id": persona_id,
        "mode": "conversation",
        "provider_preference": "gemini",
        "model_preference": "gemini-1.5-flash",
    }
    create_resp = await client.post("/api/v1/conversations", json=start_payload)
    assert create_resp.status_code == 201
    session_data = create_resp.json()
    session_id = session_data["id"]
    assert session_data["status"] == "active"
    assert session_data["persona_id"] == persona_id
    assert session_data["mode"] == "conversation"

    # 3. Get session by ID (includes initial AI opening turn)
    get_resp = await client.get(f"/api/v1/conversations/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == session_id
    assert len(get_resp.json()["turns"]) == 1
    assert get_resp.json()["turns"][0]["speaker"] == "assistant"

    # 4. Mock AI Router and TTS Router to test text turn
    fake_ai_resp = AIResponse(
        text="はじめまして！日本語の練習をしましょう。今日は何をしましたか？",
        provider="gemini",
        model="gemini-1.5-flash",
        usage=AIUsage(prompt_tokens=20, completion_tokens=15, total_tokens=35),
    )
    fake_tts_out = TTSAudioOutput(
        audio_bytes=b"RIFFdummywav",
        format="wav",
        duration_ms=2000,
        voice="1",
        provider="voicevox",
    )

    with (
        patch.object(AIRouter, "generate", new_callable=AsyncMock) as mock_ai,
        patch.object(tts_router, "synthesize", new_callable=AsyncMock) as mock_tts,
    ):
        mock_ai.return_value = fake_ai_resp
        mock_tts.return_value = fake_tts_out

        turn_resp = await client.post(
            f"/api/v1/conversations/{session_id}/turns",
            json={"transcript": "こんにちは！よろしくお願いします。"},
        )
        assert turn_resp.status_code == 200
        turn_data = turn_resp.json()
        assert turn_data["session_id"] == session_id
        assert turn_data["user_turn"]["transcript"] == "こんにちは！よろしくお願いします。"
        assert "日本語の練習をしましょう" in turn_data["assistant_turn"]["transcript"]
        assert turn_data["audio_base64"] is not None

    # 5. Mock audio turn
    fake_stt_result = STTResult(
        text="映画を見に行きました。",
        language="ja",
        duration_ms=1500,
        confidence=0.97,
        processing_time_ms=150,
        model="base",
        provider="faster_whisper",
    )

    with (
        patch.object(stt_router, "transcribe", new_callable=AsyncMock) as mock_stt,
        patch.object(AIRouter, "generate", new_callable=AsyncMock) as mock_ai,
        patch.object(tts_router, "synthesize", new_callable=AsyncMock) as mock_tts,
    ):
        mock_stt.return_value = fake_stt_result
        mock_ai.return_value = AIResponse(
            text="何の映画を見たんですか？面白かったですか？",
            provider="gemini",
            model="gemini-1.5-flash",
        )
        mock_tts.return_value = fake_tts_out

        files = {"audio_file": ("test.wav", b"fake_wav_bytes" * 50, "audio/wav")}
        data = {"client_turn_id": "client-turn-123"}
        audio_turn_resp = await client.post(
            f"/api/v1/conversations/{session_id}/audio-turn",
            files=files,
            data=data,
        )
        assert audio_turn_resp.status_code == 200
        audio_turn_data = audio_turn_resp.json()
        assert audio_turn_data["user_turn"]["transcript"] == "映画を見に行きました。"
        assert "何の映画を見たんですか" in audio_turn_data["assistant_turn"]["transcript"]

    # 6. Check full session history (Opening Assistant 1, User 1, Assistant 2, User 2, Assistant 3)
    session_with_turns = await client.get(f"/api/v1/conversations/{session_id}")
    assert session_with_turns.status_code == 200
    turns = session_with_turns.json()["turns"]
    assert len(turns) == 5

    # 7. End session
    end_resp = await client.post(f"/api/v1/conversations/{session_id}/end")
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == "completed"
    assert end_resp.json()["duration_seconds"] is not None

    # 8. Get session summary
    summary_resp = await client.get(f"/api/v1/conversations/{session_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["turn_count"] == 5
    assert summary["user_turns_count"] == 2
    assert summary["assistant_turns_count"] == 3
    assert summary["total_speaking_time_seconds"] >= 1.5
