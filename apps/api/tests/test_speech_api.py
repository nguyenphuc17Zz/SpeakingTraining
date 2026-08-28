from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.domains.speech.contracts import STTResult, TTSAudioOutput
from app.domains.speech.stt_router import stt_router
from app.domains.speech.tts_router import tts_router


@pytest.mark.asyncio
async def test_speech_api_endpoints(client: AsyncClient):
    # 1. Get available STT models
    models_resp = await client.get("/api/v1/speech/stt-models")
    assert models_resp.status_code == 200
    models = models_resp.json()
    assert len(models) >= 5

    # 2. Get available TTS voices
    voices_resp = await client.get("/api/v1/speech/voices")
    assert voices_resp.status_code == 200
    voices = voices_resp.json()
    assert len(voices) > 0

    # 3. Transcribe audio with mocked STTRouter
    fake_stt_result = STTResult(
        text="テスト音声です",
        language="ja",
        duration_ms=1000,
        confidence=0.99,
        processing_time_ms=80,
        model="base",
        provider="faster_whisper",
    )

    with patch.object(stt_router, "transcribe", new_callable=AsyncMock) as mock_stt:
        mock_stt.return_value = fake_stt_result

        files = {"audio_file": ("test.wav", b"fake_wav_data", "audio/wav")}
        data = {"model": "base", "language": "ja"}
        transcribe_resp = await client.post("/api/v1/speech/transcribe", files=files, data=data)
        assert transcribe_resp.status_code == 200
        assert transcribe_resp.json()["text"] == "テスト音声です"

    # 4. Synthesize speech with mocked TTSRouter
    fake_tts_out = TTSAudioOutput(
        audio_bytes=b"RIFFfakeaudiobytes",
        format="wav",
        duration_ms=800,
        voice="1",
        provider="voicevox",
    )

    with patch.object(tts_router, "synthesize", new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = fake_tts_out

        synth_resp = await client.post(
            "/api/v1/speech/synthesize",
            json={"text": "こんにちは", "voice_id": "1", "return_base64": True},
        )
        assert synth_resp.status_code == 200
        data = synth_resp.json()
        assert data["audio_base64"] is not None
        assert data["format"] == "wav"
